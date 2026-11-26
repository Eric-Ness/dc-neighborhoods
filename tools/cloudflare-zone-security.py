"""Tighten TLS, DNSSEC and certificate settings for every neighborhood domain on Cloudflare.

For each domain in site/src/data/index.json (main and redirect domains) that is a zone in your
Cloudflare account, this:

  - sets the minimum TLS version to 1.2, so browsers can no longer connect with TLS 1.0 or 1.1
    (a zone already at 1.2 or 1.3 is left alone);
  - limits TLS 1.2 to forward-secret cipher suites (ECDHE with AES-GCM or ChaCha20), so a stolen
    key can't decrypt recorded traffic. TLS 1.3 is always forward-secret and isn't affected;
  - adds CAA records naming the certificate authorities Cloudflare uses, so no other authority
    may issue a certificate for the domain. Cloudflare also adds its own CAA entries for its
    certificates whenever a zone has any, so this can't block renewals;
  - turns on DNSSEC, so DNS answers for the domain are signed.

DNSSEC has a second half that this can't do everywhere: the domain's registrar must publish a DS
record. Cloudflare Registrar does that by itself. For a domain registered anywhere else, the
script prints the DS record to paste into that registrar, and the zone stays "pending" until it is
in place. Run the script again later to see which zones are still pending.

Dry run by default: it only reads and prints the plan. Add --apply to make the changes. A zone
already in the wanted state is left alone, so running it again is safe.

Token (Manage Account > Account API Tokens, or My Profile > API Tokens), for the zones you want:
  Zone > Zone > Read,  Zone > Zone Settings > Edit,  Zone > DNS Settings > Edit,  Zone > DNS > Edit
  PowerShell:  $env:CLOUDFLARE_API_TOKEN = Read-Host "Cloudflare token"

  python tools/cloudflare-zone-security.py                  # show the plan
  python tools/cloudflare-zone-security.py --apply          # make the changes
  python tools/cloudflare-zone-security.py --only georgetowndc.org --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.cloudflare.com/client/v4"
INDEX = Path(__file__).resolve().parent.parent / "site" / "src" / "data" / "index.json"
COMMENT = "Set by tools/cloudflare-zone-security.py"
MIN_TLS = "1.2"
TLS_ORDER = ["1.0", "1.1", "1.2", "1.3"]
# Cloudflare's "Modern" TLS 1.2 set: every suite uses ECDHE (forward secrecy) and an AEAD cipher.
CIPHERS = [
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-CHACHA20-POLY1305",
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES256-GCM-SHA384",
]
# The authorities Cloudflare issues its edge certificates from (the sites' current one is Google's).
CAA = [("issue", ca) for ca in ("pki.goog", "letsencrypt.org", "ssl.com", "sectigo.com")] + [
    ("issuewild", ca) for ca in ("pki.goog", "letsencrypt.org", "ssl.com", "sectigo.com")
]


class ApiError(Exception):
    pass


class PermissionMissing(Exception):
    pass


def call(token: str, method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        API + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "dc-neighborhoods-dns-tool",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            data = json.load(e)
        except ValueError:
            raise ApiError(f"HTTP {e.code}") from None
    if not data.get("success"):
        msgs = "; ".join(f"{x.get('code')}: {x.get('message')}" for x in data.get("errors") or [])
        raise ApiError(msgs or "request failed")
    return data


def zones(token: str) -> dict[str, dict]:
    out, page = {}, 1
    while True:
        data = call(token, "GET", "/zones?" + urllib.parse.urlencode({"page": page, "per_page": 50}))
        out.update({z["name"]: z for z in data["result"]})
        if page >= ((data.get("result_info") or {}).get("total_pages") or 1):
            return out
        page += 1


def our_domains() -> list[str]:
    hoods = json.loads(INDEX.read_text(encoding="utf-8"))
    return sorted({h for x in hoods for h in x["hosts"]} | {h for x in hoods for h in x["redirect_hosts"]})


def guarded(what: str, permission: str, fn):
    """Run one API call; a 10000 (authentication) answer means the token lacks this permission."""
    try:
        return fn()
    except ApiError as e:
        if "10000" in str(e):
            raise PermissionMissing(f"The token can't {what} ({e}). Add {permission} to it and run this again.") from None
        raise


def ds_line(d: dict) -> str:
    return d.get("ds") or f"key tag {d.get('key_tag')}, algorithm {d.get('algorithm')}, digest type {d.get('digest_type')}, digest {d.get('digest')}"


class Zone:
    """The four changes for one zone. Each returns a short note and counts what it changed."""

    def __init__(self, token: str, zid: str, domain: str, apply: bool):
        self.t, self.zid, self.domain, self.apply = token, zid, domain, apply
        self.changed = 0
        self.pending_ds: dict | None = None

    def get(self, path, what, perm):
        return guarded(what, perm, lambda: call(self.t, "GET", f"/zones/{self.zid}{path}"))["result"]

    def write(self, method, path, body, what, perm):
        guarded(what, perm, lambda: call(self.t, method, f"/zones/{self.zid}{path}", body))
        self.changed += 1

    def tls(self) -> str:
        perm = "Zone > Zone Settings > Edit"
        cur = self.get("/settings/min_tls_version", "read zone settings", perm)["value"]
        if cur in TLS_ORDER and TLS_ORDER.index(cur) >= TLS_ORDER.index(MIN_TLS):
            return f"TLS minimum already {cur}"
        if not self.apply:
            return f"would raise TLS minimum {cur} -> {MIN_TLS}"
        self.write("PATCH", "/settings/min_tls_version", {"value": MIN_TLS}, "change zone settings", perm)
        return f"raised TLS minimum {cur} -> {MIN_TLS}"

    def ciphers(self) -> str:
        perm = "Zone > Zone Settings > Edit"
        cur = self.get("/settings/ciphers", "read zone settings", perm)["value"] or []
        if cur and set(cur) <= set(CIPHERS):
            return "ciphers already forward-secret only"
        if not self.apply:
            return "would limit TLS 1.2 to forward-secret ciphers" + ("" if cur else " (now Cloudflare's default)")
        self.write("PATCH", "/settings/ciphers", {"value": CIPHERS}, "change zone settings", perm)
        return "limited TLS 1.2 to forward-secret ciphers"

    def caa(self) -> str:
        perm = "Zone > DNS > Edit"
        q = urllib.parse.urlencode({"type": "CAA", "name": self.domain, "per_page": 100})
        recs = self.get(f"/dns_records?{q}", "read DNS records", perm)
        have = {((r.get("data") or {}).get("tag"), (r.get("data") or {}).get("value")) for r in recs}
        missing = [(tag, ca) for tag, ca in CAA if (tag, ca) not in have]
        if not missing:
            return "CAA already set"
        if not self.apply:
            return f"would add {len(missing)} CAA records"
        for tag, ca in missing:
            body = {"type": "CAA", "name": self.domain, "ttl": 1, "comment": COMMENT,
                    "data": {"flags": 0, "tag": tag, "value": ca}}
            self.write("POST", "/dns_records", body, "add DNS records", perm)
        return f"added {len(missing)} CAA records"

    def dnssec(self) -> str:
        perm = "Zone > DNS Settings > Edit"
        d = self.get("/dnssec", "read DNSSEC", perm)
        status = d.get("status")
        if status == "active":
            return "DNSSEC active"
        if status == "pending":
            self.pending_ds = d
            return "DNSSEC waiting for the DS record at the registrar"
        if not self.apply:
            return f"would turn on DNSSEC (now {status})"
        self.write("PATCH", "/dnssec", {"status": "active"}, "change DNSSEC", perm)
        d = self.get("/dnssec", "read DNSSEC", perm)
        if d.get("status") != "active":
            self.pending_ds = d
        return f"turned on DNSSEC (now {d.get('status')})"


def main() -> int:
    ap = argparse.ArgumentParser(description="Tighten TLS, ciphers, CAA and DNSSEC for the neighborhood domains.")
    ap.add_argument("--apply", action="store_true", help="make the changes (default: dry run)")
    ap.add_argument("--only", nargs="+", metavar="DOMAIN", help="limit to these domains")
    args = ap.parse_args()

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        print("Set CLOUDFLARE_API_TOKEN first (see the top of this file).", file=sys.stderr)
        return 2

    wanted = our_domains()
    if args.only:
        unknown = sorted(set(args.only) - set(wanted))
        if unknown:
            print(f"Not one of the neighborhood domains: {', '.join(unknown)}", file=sys.stderr)
            return 2
        wanted = sorted(args.only)

    try:
        found = zones(token)
    except ApiError as e:
        print(f"Could not list zones: {e}", file=sys.stderr)
        return 1

    print(("Applying" if args.apply else "Dry run (add --apply to make these changes)") + f": {len(wanted)} domains\n")
    missing, pending = [], []
    failed = changed = 0
    try:
        for domain in wanted:
            zone = found.get(domain)
            if not zone:
                missing.append(domain)
                continue
            z = Zone(token, zone["id"], domain, args.apply)
            notes = []
            for name, step in (("TLS", z.tls), ("ciphers", z.ciphers), ("CAA", z.caa), ("DNSSEC", z.dnssec)):
                try:
                    notes.append(step())
                except ApiError as e:
                    notes.append(f"{name} FAILED: {e}")
                    failed += 1
            changed += z.changed
            if z.pending_ds:
                pending.append((domain, z.pending_ds))
            print(f"{domain}: " + "; ".join(notes))
    except PermissionMissing as e:
        print(f"\n{e}", file=sys.stderr)
        return 1

    print()
    if pending:
        print("DNSSEC is waiting on the registrar for these. Cloudflare Registrar adds the DS record by itself;")
        print("for a domain registered elsewhere, paste this DS record into that registrar's DNSSEC settings:")
        for domain, d in pending:
            print(f"  {domain}: {ds_line(d)}")
        print()
    if missing:
        print(f"Not zones in this account (or the token can't see them): {', '.join(missing)}")
    if args.apply:
        print(f"Changes made: {changed}. Failures: {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
