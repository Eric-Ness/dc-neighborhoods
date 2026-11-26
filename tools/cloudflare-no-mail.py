"""Tell the world that the neighborhood domains send and receive no email.

For each domain in site/src/data/index.json (main and redirect domains) that is a zone in your
Cloudflare account, this adds the three DNS records that stop anyone forging mail "from" it:

  TXT  @       "v=spf1 -all"                                  no server may send mail as the domain
  TXT  _dmarc  "v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s" receivers reject mail that fails
  MX   @       0 .                                            the domain takes no mail (RFC 7505)

A zone that already has a real MX record (Email Routing, Google, Fastmail...) or an SPF record
other than "v=spf1 -all" uses email, so it is skipped entirely. Existing DMARC records are never
changed. Nothing is deleted.

Dry run by default: it only reads and prints the plan. Add --apply to create the records.

Token: create one at dash.cloudflare.com > My Profile > API Tokens with
  Zone > Zone > Read   and   Zone > DNS > Edit,  for the zones you want covered,
then set it for this shell only:
  PowerShell:  $env:CLOUDFLARE_API_TOKEN = "<token>"
  bash:        export CLOUDFLARE_API_TOKEN=<token>

  python tools/cloudflare-no-mail.py                 # show the plan
  python tools/cloudflare-no-mail.py --apply         # make the changes
  python tools/cloudflare-no-mail.py --only georgetowndc.org --apply
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
COMMENT = "No-mail policy, set by tools/cloudflare-no-mail.py"

SPF = "v=spf1 -all"
DMARC = "v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s"


class ApiError(Exception):
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


def paged(token: str, path: str, params: dict) -> list[dict]:
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode({**params, "page": page, "per_page": 100})
        data = call(token, "GET", f"{path}?{q}")
        out += data["result"]
        info = data.get("result_info") or {}
        if page >= (info.get("total_pages") or 1):
            return out
        page += 1


def txt(value: str) -> str:
    """TXT content as Cloudflare shows it: one quoted string, or several. Join and unquote."""
    v = value.strip()
    if v.startswith('"'):
        parts = [p for p in v.split('"')[1::2]]
        return "".join(parts)
    return v


def our_domains() -> list[str]:
    hoods = json.loads(INDEX.read_text(encoding="utf-8"))
    names = {h for x in hoods for h in x["hosts"]} | {h for x in hoods for h in x["redirect_hosts"]}
    return sorted(names)


def plan_zone(records: list[dict], domain: str) -> tuple[list[dict], list[str], str | None]:
    """Return (records to create, notes, reason to skip the whole zone)."""
    apex = [r for r in records if r["name"] == domain]
    mx = [r for r in apex if r["type"] == "MX"]
    real_mx = [r for r in mx if r["content"].strip().rstrip(".") != ""]
    if real_mx:
        return [], [], f"receives mail (MX {real_mx[0]['content']})"
    spf = [r for r in apex if r["type"] == "TXT" and txt(r["content"]).lower().startswith("v=spf1")]
    if any(txt(r["content"]).strip() != SPF for r in spf):
        return [], [], f"has its own SPF record ({txt(spf[0]['content'])})"

    create, notes = [], []
    if spf:
        notes.append("SPF already set")
    else:
        create.append({"type": "TXT", "name": domain, "content": f'"{SPF}"', "ttl": 1, "comment": COMMENT})

    dmarc = [r for r in records if r["name"] == f"_dmarc.{domain}" and r["type"] == "TXT"]
    if dmarc:
        current = txt(dmarc[0]["content"])
        notes.append("DMARC already set" if "p=reject" in current.replace(" ", "") else f"DMARC left as is ({current})")
    else:
        create.append({"type": "TXT", "name": f"_dmarc.{domain}", "content": f'"{DMARC}"', "ttl": 1, "comment": COMMENT})

    if mx:
        notes.append("null MX already set")
    else:
        create.append({"type": "MX", "name": domain, "content": ".", "priority": 0, "ttl": 1, "comment": COMMENT})
    return create, notes, None


def describe(r: dict) -> str:
    extra = f" {r['priority']}" if r["type"] == "MX" else ""
    return f"{r['type']:<3} {r['name']}{extra} {r['content']}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Add no-mail SPF, DMARC and null MX records to the neighborhood domains.")
    ap.add_argument("--apply", action="store_true", help="create the records (default: dry run)")
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
        zones = {z["name"]: z for z in paged(token, "/zones", {})}
    except ApiError as e:
        print(f"Could not list zones: {e}", file=sys.stderr)
        return 1

    print(("Applying" if args.apply else "Dry run (add --apply to make these changes)") + f": {len(wanted)} domains\n")
    created = failed = skipped = done = 0
    missing = []
    for domain in wanted:
        zone = zones.get(domain)
        if not zone:
            missing.append(domain)
            continue
        try:
            records = paged(token, f"/zones/{zone['id']}/dns_records", {})
        except ApiError as e:
            if "10000" in str(e):  # the same answer would come back for every zone
                print(f"{domain}: could not read DNS records ({e}).\n"
                      "The token can list zones but not their DNS records: add Zone > DNS > Edit to it "
                      "(Manage Account > Account API Tokens, or My Profile > API Tokens) and run this again.",
                      file=sys.stderr)
                return 1
            print(f"{domain}: could not read DNS records ({e})")
            failed += 1
            continue
        create, notes, skip = plan_zone(records, domain)
        if skip:
            print(f"{domain}: SKIPPED, {skip}")
            skipped += 1
            continue
        if not create:
            print(f"{domain}: nothing to do ({', '.join(notes)})")
            done += 1
            continue
        print(f"{domain}:" + (f" ({', '.join(notes)})" if notes else ""))
        for r in create:
            if not args.apply:
                print(f"  would add  {describe(r)}")
                continue
            try:
                call(token, "POST", f"/zones/{zone['id']}/dns_records", r)
                print(f"  added      {describe(r)}")
                created += 1
            except ApiError as e:
                print(f"  FAILED     {describe(r)}: {e}")
                failed += 1

    print()
    if missing:
        print(f"Not zones in this account (or the token can't see them): {', '.join(missing)}")
    print(f"Skipped because they use email: {skipped}. Already complete: {done}.")
    if args.apply:
        print(f"Records added: {created}. Failures: {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
