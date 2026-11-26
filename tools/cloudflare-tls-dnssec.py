"""Turn off old TLS and turn on DNSSEC for every neighborhood domain on Cloudflare.

For each domain in site/src/data/index.json (main and redirect domains) that is a zone in your
Cloudflare account, this:

  - sets the minimum TLS version to 1.2, so browsers can no longer connect with TLS 1.0 or 1.1
    (a zone already at 1.2 or 1.3 is left alone);
  - turns on DNSSEC, so DNS answers for the domain are signed.

DNSSEC has a second half that this can't do everywhere: the domain's registrar must publish a DS
record. Cloudflare Registrar does that by itself. For a domain registered anywhere else, the
script prints the DS record to paste into that registrar, and the zone stays "pending" until it is
in place. Run the script again later to see which zones are still pending.

Dry run by default: it only reads and prints the plan. Add --apply to make the changes.

Token (Manage Account > Account API Tokens, or My Profile > API Tokens), for the zones you want:
  Zone > Zone > Read,  Zone > Zone Settings > Edit,  Zone > DNS Settings > Edit
  PowerShell:  $env:CLOUDFLARE_API_TOKEN = Read-Host "Cloudflare token"

  python tools/cloudflare-tls-dnssec.py                  # show the plan
  python tools/cloudflare-tls-dnssec.py --apply          # make the changes
  python tools/cloudflare-tls-dnssec.py --only georgetowndc.org --apply
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
MIN_TLS = "1.2"
TLS_ORDER = ["1.0", "1.1", "1.2", "1.3"]


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Set minimum TLS 1.2 and turn on DNSSEC for the neighborhood domains.")
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
    missing, failed, pending = [], 0, []
    tls_changed = dnssec_changed = 0
    try:
        for domain in wanted:
            zone = found.get(domain)
            if not zone:
                missing.append(domain)
                continue
            zid = zone["id"]
            lines = []

            # Minimum TLS version
            try:
                cur = guarded("read zone settings", "Zone > Zone Settings > Edit",
                              lambda: call(token, "GET", f"/zones/{zid}/settings/min_tls_version"))["result"]["value"]
                if cur in TLS_ORDER and TLS_ORDER.index(cur) >= TLS_ORDER.index(MIN_TLS):
                    lines.append(f"TLS minimum already {cur}")
                elif not args.apply:
                    lines.append(f"would raise TLS minimum {cur} -> {MIN_TLS}")
                else:
                    guarded("change zone settings", "Zone > Zone Settings > Edit",
                            lambda: call(token, "PATCH", f"/zones/{zid}/settings/min_tls_version", {"value": MIN_TLS}))
                    lines.append(f"raised TLS minimum {cur} -> {MIN_TLS}")
                    tls_changed += 1
            except ApiError as e:
                lines.append(f"TLS FAILED: {e}")
                failed += 1

            # DNSSEC
            try:
                d = guarded("read DNSSEC", "Zone > DNS Settings > Edit",
                            lambda: call(token, "GET", f"/zones/{zid}/dnssec"))["result"]
                status = d.get("status")
                if status == "active":
                    lines.append("DNSSEC already active")
                elif status == "pending":
                    lines.append("DNSSEC on, waiting for the DS record at the registrar")
                    pending.append((domain, d))
                elif not args.apply:
                    lines.append(f"would turn on DNSSEC (now {status})")
                else:
                    guarded("change DNSSEC", "Zone > DNS Settings > Edit",
                            lambda: call(token, "PATCH", f"/zones/{zid}/dnssec", {"status": "active"}))
                    d = call(token, "GET", f"/zones/{zid}/dnssec")["result"]
                    lines.append(f"turned on DNSSEC (now {d.get('status')})")
                    dnssec_changed += 1
                    if d.get("status") != "active":
                        pending.append((domain, d))
            except ApiError as e:
                lines.append(f"DNSSEC FAILED: {e}")
                failed += 1

            print(f"{domain}: " + "; ".join(lines))
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
        print(f"TLS minimums raised: {tls_changed}. DNSSEC turned on: {dnssec_changed}. Failures: {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
