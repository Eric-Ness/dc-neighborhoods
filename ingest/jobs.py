"""`jobs` section: open jobs at employers in or near the neighborhood, from public career-site feeds.

    python ingest/jobs.py tenleytown

Only feeds that are machine-readable, allowed by robots.txt for our user agent, and not barred by the
employer's terms are used (research notes: ingest/JOBS-SOURCES.md, including the sources left out and why). Indeed, LinkedIn, Craigslist and
other boards that forbid automated use are not. We keep the title, employer, place, posted date and
link to apply; job descriptions are never stored.

Sources:
- Workday career sites (the JSON the employer's own careers page calls): American University and
  Children's National Hospital. Location filters are looked up by name every run, never hard-coded,
  because Workday's ids can change. Student-only postings are left out.
- Greenhouse's public job-board API (documented for third-party display), as a watch list of local
  employers, filtered by ZIP code.

"In" means the job is at a site inside the neighborhood; "nearby" means a named site within about a
mile, labeled with its distance on the page.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
import news  # noqa: E402  (robots check)
from run import find_forbidden, iso  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MAX_AGE_DAYS = 120  # every listing is open today; this only drops perpetual "pool" postings
NEARBY_CAP = 15  # newest N "nearby" jobs per employer, so one big campus can't flood the list

# Workday tenants: (employer, host, tenant, site). Sites: location name as Workday shows it -> (where, note)
WORKDAY = {
    "au": ("American University", "american.wd1.myworkdayjobs.com", "american", "AU"),
    "cn": ("Children's National Hospital", "childrensnational.wd108.myworkdayjobs.com", "childrensnational", "CN_Careers"),
    "gu": ("Georgetown University", "georgetown.wd1.myworkdayjobs.com", "georgetown", "Georgetown_Admin_Careers"),
}
SITES = {
    "tenleytown": [
        ("au", "Tenley Campus", "in", "4300 Nebraska Ave NW"),
        ("cn", "Friendship Heights", "in", "Friendship Heights"),
        ("au", "Main Campus", "nearby", "4400 Massachusetts Ave NW, about 0.8 mi"),
        ("au", "East Campus", "nearby", "about 0.7 mi"),
        ("au", "4401 Connecticut Campus", "nearby", "Van Ness, about 0.9 mi"),
        ("au", "Spring Valley Campus", "nearby", "about 1 mi"),
    ],
    "petworth": [
        ("cn", "Columbia Heights", "nearby", "about 1 mi south"),
    ],
    "adamsmorgan": [
        ("cn", "Columbia Heights", "nearby", "about 0.6 mi east"),
    ],
    "friendshipheights": [
        ("cn", "Friendship Heights", "in", "Friendship Heights"),
        ("au", "Tenley Campus", "nearby", "4300 Nebraska Ave NW, about 0.6 mi south"),
    ],
    "columbiaheights": [
        ("cn", "Columbia Heights", "in", "Columbia Heights"),
    ],
    "anacostia": [
        ("cn", "Anacostia", "in", "2101 Martin Luther King Jr Ave SE"),
    ],
    "chevychase": [
        ("cn", "Friendship Heights", "nearby", "Friendship Heights, about 0.8 mi west"),
    ],
    # Added 2026-11-01 (ingest/SOURCES-NORTHWEST.md). Location names are matched by prefix, so Georgetown's four
    # Wisconsin Avenue offices are each named in full.
    "brookland": [
        ("cn", "Rehabilitation and Specialized Care Bunker Hill Road", "nearby", "1731 Bunker Hill Rd NE, about 0.8 mi"),
    ],
    "gloverpark": [
        ("gu", "2115 Wisconsin Avenue", "in", "2115 Wisconsin Ave NW"),
        ("gu", "2115 Wisconsin Ave 3rd Floor", "in", "2115 Wisconsin Ave NW"),
        ("gu", "2115 Wisconsin Ave G1 Floor", "in", "2115 Wisconsin Ave NW"),
        ("gu", "2121 Wisconsin Avenue", "in", "2121 Wisconsin Ave NW"),
        ("au", "3201 New Mexico Campus", "in", "3201 New Mexico Ave NW"),
    ],
    "vanness": [
        ("au", "4401 Connecticut Campus", "in", "4401 Connecticut Ave NW"),
        ("au", "Tenley Campus", "nearby", "4300 Nebraska Ave NW, about 0.8 mi"),
    ],    # Children's National's "Shaw Metro" clinic is at 641 S St NW: inside U Street's planning area, just north of ANC 2G.
    "ustreet": [
        ("cn", "Shaw Metro", "in", "641 S St NW"),
    ],
    "shaw": [
        ("cn", "Shaw Metro", "nearby", "641 S St NW, just north of ANC 2G"),
    ],
    "logancircle": [
        ("cn", "Shaw Metro", "nearby", "641 S St NW, about 0.5 mi east"),
    ],
}
# Local employers on Greenhouse (board slug -> display name); extend as more are found. Monumental Sports is Capital One
# Arena, matched to Chinatown by ZIP 20004.
GREENHOUSE = {"sweetgreen": "Sweetgreen", "monumentalsports": "Monumental Sports & Entertainment"}
ZIPS = {"petworth": ("20011",), "tenleytown": ("20016", "20015"),  # no Adams Morgan: 20009 also covers Dupont, Logan, U St
        "friendshipheights": ("20015", "20016"), "brookland": ("20017",),
        "chinatown": ("20004",)}  # Penn Quarter; not 20001, which also covers Shaw, NoMa and Bloomingdale


def _json(url: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": dcdata.USER_AGENT, "Accept": "application/json", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * 2 ** attempt)
    raise AssertionError("unreachable")


def _posted(text: str | None, today: date) -> date | None:
    """Workday list pages say "Posted Today", "Posted Yesterday", "Posted 3 Days Ago", "Posted 30+ Days Ago"."""
    t = (text or "").lower()
    if "today" in t:
        return today
    if "yesterday" in t:
        return today - timedelta(days=1)
    m = re.search(r"(\d+)\+?\s+days", t)
    return today - timedelta(days=int(m.group(1))) if m else None


def _facets(tenant: tuple) -> tuple[dict[str, str], list[str]]:
    """Location name -> facet id, and the worker-subtype ids to keep (everything except student jobs)."""
    _, host, ten, site = tenant
    d = _json(f"https://{host}/wday/cxs/{ten}/{site}/jobs", {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
    locs: dict[str, str] = {}
    subtypes: list[str] = []

    def walk(fs):
        for f in fs or []:
            for v in f.get("values", []) or []:
                if v.get("id") and f.get("facetParameter") in ("locations", "locationMainGroup", "Location"):
                    locs[v["descriptor"]] = v["id"]
                if f.get("facetParameter") == "workerSubType" and v.get("id") and "student" not in v.get("descriptor", "").lower():
                    subtypes.append(v["id"])
                if v.get("facetParameter") or v.get("values"):
                    walk([v])
    walk(d.get("facets"))
    return locs, subtypes


def _workday(slug: str, today: date) -> tuple[list[dict], list[dict]]:
    jobs, status = [], []
    sites = SITES.get(slug, [])
    for key in dict.fromkeys(s[0] for s in sites):
        tenant = WORKDAY[key]
        employer, host, ten, site = tenant
        base = f"https://{host}/wday/cxs/{ten}/{site}"
        st = {"name": employer, "url": f"https://{host}/{site}", "state": "ok", "count": 0}
        status.append(st)
        if not news.allowed(f"{base}/jobs"):
            st["state"] = "skipped: robots.txt"
            continue
        try:
            locs, subtypes = _facets(tenant)
        except Exception as e:
            st["state"] = f"error: {type(e).__name__}"
            continue
        for k, loc_name, where, note in sites:
            if k != key:
                continue
            fid = next((v for n, v in locs.items() if n.lower().startswith(loc_name.lower())), None)
            if not fid:
                st["state"] = f"site not found: {loc_name}"
                continue
            found, offset = [], 0
            while True:
                facets = {"locations": [fid]}
                if subtypes:
                    facets["workerSubType"] = subtypes
                try:
                    d = _json(f"{base}/jobs", {"appliedFacets": facets, "limit": 20, "offset": offset, "searchText": ""})
                except Exception as e:
                    st["state"] = f"error: {type(e).__name__}"
                    break
                posts = d.get("jobPostings", [])
                for p in posts:
                    # A multi-site posting can match a site facet while its own location is elsewhere.
                    if not (p.get("locationsText") or "").lower().startswith(loc_name.lower()) and where == "in" and key == "cn":
                        continue
                    found.append((p, _posted(p.get("postedOn"), today)))
                offset += len(posts)
                if not posts or offset >= d.get("total", 0):
                    break
                time.sleep(0.5)
            found = [f for f in found if f[1] is None or f[1] >= today - timedelta(days=MAX_AGE_DAYS)]
            found.sort(key=lambda f: f[1] or date.min, reverse=True)
            if where == "nearby":
                found = found[:NEARBY_CAP]
            for p, posted in found:
                url = f"https://{host}/{site}{p['externalPath']}"
                try:  # the detail call gives the exact posting date; its description is dropped
                    info = _json(f"{base}{p['externalPath']}").get("jobPostingInfo", {})
                    posted = date.fromisoformat(info["startDate"][:10]) if info.get("startDate") else posted
                    url = info.get("externalUrl") or url
                except Exception:
                    pass
                time.sleep(0.3)
                if posted and posted < today - timedelta(days=MAX_AGE_DAYS):
                    continue  # "30+ Days Ago" in the list can hide a posting from months back
                jobs.append({"title": news.plain(p.get("title")), "employer": employer, "place": loc_name, "where": where,
                             "note": note, "posted": posted.isoformat() if posted else None,
                             "hours": p.get("timeType") or None, "url": url})
                st["count"] += 1
    return jobs, status


def _greenhouse(slug: str) -> tuple[list[dict], list[dict]]:
    jobs, status = [], []
    zips = ZIPS.get(slug, ())
    for board in GREENHOUSE:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        st = {"name": f"{GREENHOUSE[board]} (Greenhouse)", "url": f"https://boards.greenhouse.io/{board}", "state": "ok", "count": 0}
        status.append(st)
        if not news.allowed(url):
            st["state"] = "skipped: robots.txt"
            continue
        try:
            d = _json(url)
        except Exception as e:
            st["state"] = f"error: {type(e).__name__}"
            continue
        for j in d.get("jobs", []):
            loc = (j.get("location") or {}).get("name") or ""
            if not any(z in loc for z in zips):
                continue
            upd = (j.get("updated_at") or "")[:10]
            jobs.append({"title": news.plain(j.get("title")), "employer": GREENHOUSE[board], "place": loc, "where": "in",
                         "note": None, "posted": upd or None, "hours": None, "url": j.get("absolute_url")})
            st["count"] += 1
    return jobs, status


def build(geom: dict, hood: dict, now: float) -> dict:
    slug = hood["slug"]
    today = datetime.fromtimestamp(now, timezone.utc).date()
    wd, wd_status = _workday(slug, today)
    gh, gh_status = _greenhouse(slug)
    seen, jobs = set(), []
    for j in wd + gh:  # one posting can list several sites; keep it once
        if j["url"] not in seen:
            seen.add(j["url"])
            jobs.append(j)
    # in-neighborhood first, then newest first
    jobs.sort(key=lambda j: (j["where"] != "in", -(date.fromisoformat(j["posted"]).toordinal() if j["posted"] else 0)))
    status = wd_status + gh_status
    return {
        "generated_at": iso(int(now * 1000)),
        "max_age_days": MAX_AGE_DAYS,
        "sources": [{"name": s["name"], "url": s["url"]} for s in status],
        "employers": status,
        "jobs": jobs,
    }


def check(section: dict) -> list[str]:
    errors = []
    for key in ("generated_at", "sources", "employers", "jobs"):
        if key not in section:
            errors.append(f"jobs: missing {key}")
    if errors:
        return errors
    if not any(e["state"] == "ok" for e in section["employers"]):
        errors.append("jobs: no employer feed read")
    allowed = {"title", "employer", "place", "where", "note", "posted", "hours", "url"}
    for j in section["jobs"]:
        if set(j) - allowed:
            errors.append(f"jobs: extra fields {sorted(set(j) - allowed)}")  # never a description
        if not (j.get("title") and j.get("employer") and str(j.get("url", "")).startswith("https://")):
            errors.append(f"jobs: incomplete {j}")
        if j.get("where") not in ("in", "nearby"):
            errors.append(f"jobs: bad where {j.get('where')}")
    errors += [f"jobs: forbidden field {h}" for h in find_forbidden(section)]
    return errors


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    slug = sys.argv[1] if len(sys.argv) > 1 else "tenleytown"
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if not hood:
        print(f"unknown neighborhood {slug!r}", file=sys.stderr)
        return 2
    t0 = time.time()
    section = build({}, hood, time.time())
    out_dir = ROOT / "ingest" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"jobs-{slug}.json").write_text(json.dumps(section, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{slug}: {len(section['jobs'])} jobs ({time.time() - t0:.0f}s)")
    for e in section["employers"]:
        print(f"  {e['name']:32} {e['state']:24} {e['count']}")
    for j in section["jobs"][:12]:
        print(f"  {j['where']:6} {j['posted'] or '?':10} {j['employer'][:22]:22} {j['place'][:22]:22} {j['title'][:50]}")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("jobs ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
