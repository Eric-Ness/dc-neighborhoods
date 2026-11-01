"""`events` section: what's happening in the neighborhood over the next 30 days.

    python ingest/events.py petworth

Three kinds of source, all automatic (nobody submits or moderates anything):

- Farmers markets inside the boundary, from DC's "Farmers Market Locations" layer. Its schedule is free
  text ("Saturdays", "1st, 2nd, & 4th Sundays") plus a season (STARTDATE/ENDDATE as a month name or
  YYYYMMDD); it's expanded into dated occurrences. A schedule that can't be read is listed as-is with no
  dates, never guessed.
- Community calendars that publish machine-readable listings: Tenleytown Main Street's event list
  (JSON its own calendar page uses; robots.txt asks for 10 seconds between requests, so we wait).
- ANC public meetings from DC's Office of ANCs feed (archived run to run, since the feed only holds the
  latest ~10 notices across all of DC), and from the commission's own posts: a post titled "October 8, 2026 Meeting
  Agenda" becomes a meeting on October 8 that links to the agenda.

DC Public Library's calendar refuses automated requests, so the library is linked, not listed.
Only titles, dates, times, places and links are kept; event descriptions and phone numbers are not.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
import news  # noqa: E402  (robots check, fetch and feed parsing)
from run import find_forbidden, iso  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DAYS_AHEAD = 30

MARKETS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Goods_and_Service_WebMercator/MapServer/2"
MARKETS_PAGE = "https://opendata.dc.gov/datasets/farmers-market-locations"
MARKET_FIELDS = ["NAME", "ADDRESS", "DAYS", "TIMES", "WEBSITE", "STARTDATE", "ENDDATE"]

TMS_LIST = "https://tenleytownmainstreet.org/wp-json/events/list/?period={period}"
TMS_PAGE = "https://tenleytownmainstreet.org/events/"
TMS_DELAY = 10  # robots.txt Crawl-delay

CALENDARS = {"tenleytown": ["tms"], "petworth": []}
# DC's Office of ANCs announces every ANC's public meetings in one feed (latest ~10 items only), so
# matches for this neighborhood's ANCs are archived run to run, like the headlines.
OANC_FEED = "https://oanc.dc.gov/rss.xml"
OANC_PAGE = "https://oanc.dc.gov/"
ANCS = {"petworth": ["4C", "4D"], "tenleytown": ["3E", "3F", "3/4G"], "adamsmorgan": ["1C", "2B"], "friendshipheights": ["3E"],
        # From ingest/setup_hood.py (SMD centroids inside each boundary), 2026-11-01.
        "capitolhill": ["6B", "6C"], "columbiaheights": ["1A", "1E", "1D"], "georgetown": ["2E"], "chevychase": ["3/4G"],
        "anacostia": ["8A", "8B"], "clevelandpark": ["3C"], "dupontcircle": ["2B"], "hstreet": ["6A", "6C"],
        "navyyard": ["8F", "6B", "6D"]}
OANC_TITLE = re.compile(r"^([A-Z][a-z]+ \d{1,2}, \d{4}),?\s+ANC\s+([0-9/]+[A-Z])\s+(Special\s+)?Public Meeting", re.I)
ANC_ARCHIVE_DAYS = 400
ANC_FEEDS = {"tenleytown": ("ANC 3E", "https://anc3e.org/feed/", "https://anc3e.org/"),
             "friendshipheights": ("ANC 3E", "https://anc3e.org/feed/", "https://anc3e.org/")}
LINKS = {  # calendars we point to but can't (or shouldn't) read
    "adamsmorgan": [
        {"name": "Mt. Pleasant Library events", "url": "https://dclibrary.libnet.info/events?l=Mt.%20Pleasant%20Neighborhood%20Library"},
        {"name": "Adams Morgan Partnership", "url": "https://www.adamsmorgandc.org/"},
    ],
    "friendshipheights": [
        {"name": "Tenley-Friendship Library events", "url": "https://dclibrary.libnet.info/events?l=Tenley-Friendship%20Neighborhood%20Library"},
        {"name": "Chevy Chase Library events", "url": "https://dclibrary.libnet.info/events?l=Chevy%20Chase%20Neighborhood%20Library"},
    ],
    "petworth": [
        {"name": "Petworth Library events", "url": "https://dclibrary.libnet.info/events?l=Petworth%20Neighborhood%20Library"},
        {"name": "ANC 4C meetings", "url": "https://www.anc4c.com/"},
        {"name": "Petworth Community Market", "url": "https://www.petworthcommunitymarket.org/"},
    ],
    "tenleytown": [
        {"name": "Tenley-Friendship Library events", "url": "https://dclibrary.libnet.info/events?l=Tenley-Friendship%20Neighborhood%20Library"},
        {"name": "Tenleytown Main Street calendar", "url": TMS_PAGE},
        {"name": "Fort Reno summer concerts", "url": "https://www.fortreno.com/"},
    ],
}

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def eastern_today(now: float) -> date:
    """Today's date in Washington. US DST: second Sunday of March to first Sunday of November, at 2 a.m."""
    utc = datetime.fromtimestamp(now, timezone.utc)
    y = utc.year
    mar1, nov1 = date(y, 3, 1), date(y, 11, 1)
    dst_start = datetime(y, 3, 1 + (6 - mar1.weekday()) % 7 + 7, 7, tzinfo=timezone.utc)  # 2 a.m. EST
    dst_end = datetime(y, 11, 1 + (6 - nov1.weekday()) % 7, 6, tzinfo=timezone.utc)  # 2 a.m. EDT
    offset = 4 if dst_start <= utc < dst_end else 5
    return (utc - timedelta(hours=offset)).date()


def season_bound(s: str | None, year: int, end: bool) -> date | None:
    s = (s or "").strip().lower()
    if re.fullmatch(r"\d{8}", s):
        return date(int(s[:4]), int(s[4:6]), int(s[6:]))
    m = MONTHS.get(s[:3])
    if not m:
        return None
    if not end:
        return date(year, m, 1)
    nxt = date(year + (m == 12), m % 12 + 1, 1)
    return nxt - timedelta(days=1)


def in_season(d: date, start: str | None, end: str | None) -> bool | None:
    """None when the season can't be read."""
    a, b = season_bound(start, d.year, False), season_bound(end, d.year, True)
    if a is None or b is None:
        return None
    if re.fullmatch(r"\d{8}", (end or "").strip()) or a <= b:
        return a <= d <= b
    return d >= a or d <= b  # wraps the new year ("May" to "March")


def market_dates(days_text: str, start: str | None, end: str | None, today: date) -> list[date] | None:
    """Dated occurrences in the next DAYS_AHEAD days, or None if the schedule isn't readable."""
    t = (days_text or "").lower()
    wds = sorted({WEEKDAYS[w[:3]] for w in re.findall(r"\b(mon|tues?|wed(?:nes)?|thu(?:rs)?|fri|sat(?:ur)?|sun)(?:day)?s?\b", t)})
    if not wds:
        return None
    nth = {int(n) for n in re.findall(r"\b([1-5])(?:st|nd|rd|th)\b", t)}
    last = "last" in t
    out = []
    for i in range(DAYS_AHEAD):
        d = today + timedelta(days=i)
        if d.weekday() not in wds:
            continue
        k = (d.day - 1) // 7 + 1
        is_last = (d + timedelta(days=7)).month != d.month
        if (nth or last) and not (k in nth or (last and is_last)):
            continue
        ok = in_season(d, start, end)
        if ok is None:
            return None
        if ok:
            out.append(d)
    return out


def build_markets(geom: dict, today: date) -> tuple[list[dict], list[dict]]:
    rows = dcdata.query_features(MARKETS, geom, "1=1", MARKET_FIELDS)
    events, unread = [], []
    for r in rows:
        name = news.plain(r.get("NAME"))
        site = (r.get("WEBSITE") or "").strip()
        if site and not re.match(r"https?://", site, re.I):  # DC's list sometimes omits the scheme ("www.dolgrocery.org")
            site = "https://" + site
        base = {"title": name, "place": news.plain(r.get("ADDRESS")), "time": news.plain(r.get("TIMES")) or None,
                "url": site or MARKETS_PAGE, "source": "DC farmers market list", "kind": "market"}
        dates = market_dates(r.get("DAYS") or "", r.get("STARTDATE"), r.get("ENDDATE"), today)
        if dates is None:
            unread.append({**base, "schedule": news.plain(r.get("DAYS"))})
            continue
        events += [{**base, "date": d.isoformat()} for d in dates]
    return events, unread


def parse_tms_time(s: str | None) -> str | None:
    m = re.search(r"(\d{1,2}):(\d{2}) ([AP]M)$", s or "")
    if not m:
        return None
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3).lower().replace("m", ".m.")
    return f"{h}:{mi} {ap}" if mi != "00" else f"{h} {ap}"


def build_tms(today: date) -> tuple[list[dict], str]:
    periods = sorted({today.strftime("%Y-%m"), (today + timedelta(days=DAYS_AHEAD)).strftime("%Y-%m")})
    out, state = [], "ok"
    for i, period in enumerate(periods):
        url = TMS_LIST.format(period=period)
        if not news.allowed(url):
            return [], "skipped: robots.txt"
        if i:
            time.sleep(TMS_DELAY)
        try:
            rows = json.loads(news.fetch(url))
        except Exception as e:
            state = f"error: {type(e).__name__}"
            continue
        for r in rows:
            try:
                d = date.fromisoformat(r["start"][:10])
            except (KeyError, ValueError):
                continue
            if not (today <= d < today + timedelta(days=DAYS_AHEAD)):
                continue
            x = r.get("extendedProps") or {}
            s, e = parse_tms_time(x.get("start")), parse_tms_time(x.get("end"))
            out.append({"title": html.unescape(r.get("title", "")).strip(), "date": d.isoformat(),
                        "time": f"{s} to {e}" if s and e and s != e else s, "place": news.plain(x.get("address")) or None,
                        "url": r.get("url") or TMS_PAGE, "source": "Tenleytown Main Street", "kind": "community"})
    return out, state


AGENDA = re.compile(r"^([A-Z][a-z]+ \d{1,2}, \d{4})\s+(?:Public\s+)?Meeting Agenda\b")


def build_anc(slug: str, today: date) -> tuple[list[dict], str]:
    if slug not in ANC_FEEDS:
        return [], "none"
    name, url, _home = ANC_FEEDS[slug]
    if not news.allowed(url):
        return [], "skipped: robots.txt"
    try:
        items = news.parse_feed(news.fetch(url))
    except Exception as e:
        return [], f"error: {type(e).__name__}"
    out = []
    for it in items:
        m = AGENDA.match(it["title"])
        if not m:
            continue
        d = datetime.strptime(m.group(1), "%B %d, %Y").date()
        if today <= d < today + timedelta(days=DAYS_AHEAD):
            out.append({"title": f"{name} public meeting", "date": d.isoformat(), "time": None, "place": None,
                        "url": it["url"], "source": name, "kind": "civic"})
    return out, "ok"


def previous(slug: str) -> dict:
    try:
        return json.loads((ROOT / "site" / "src" / "data" / f"{slug}.json").read_text(encoding="utf-8")).get("events") or {}
    except (OSError, ValueError):
        return {}


def build_oanc(slug: str, today: date, prev: dict) -> tuple[list[dict], str]:
    """Every public meeting of this neighborhood's ANCs seen in the OANC feed, past and upcoming."""
    mine = set(ANCS.get(slug, []))
    found = {m["url"]: m for m in prev.get("anc_meetings", [])
             if date.fromisoformat(m["date"]) >= today - timedelta(days=ANC_ARCHIVE_DAYS)}
    if not news.allowed(OANC_FEED):
        return sorted(found.values(), key=lambda m: m["date"], reverse=True), "skipped: robots.txt"
    try:
        items = news.parse_feed(news.fetch(OANC_FEED))
        state = "ok"
    except Exception as e:
        items, state = [], f"error: {type(e).__name__}"
    for it in items:
        m = OANC_TITLE.match(it["title"])
        if not m or m.group(2).upper() not in mine:
            continue
        d = datetime.strptime(m.group(1).replace(",", ""), "%B %d %Y").date()
        found[it["url"]] = {"anc": f"ANC {m.group(2).upper()}", "date": d.isoformat(), "special": bool(m.group(3)),
                            "title": it["title"], "url": it["url"]}
    return sorted(found.values(), key=lambda m: m["date"], reverse=True), state


def build(geom: dict, hood: dict, now: float) -> dict:
    slug = hood["slug"]
    today = eastern_today(now)
    markets, unread = build_markets(geom, today)
    calendars = [{"name": "DC farmers market list", "url": MARKETS_PAGE, "state": "ok"}]
    community: list[dict] = []
    if "tms" in CALENDARS.get(slug, []):
        tms, st = build_tms(today)
        community += tms
        calendars.append({"name": "Tenleytown Main Street", "url": TMS_PAGE, "state": st})
    anc, st = build_anc(slug, today)
    if slug in ANC_FEEDS:
        calendars.append({"name": f"{ANC_FEEDS[slug][0]} meeting agendas", "url": ANC_FEEDS[slug][2], "state": st})
    meetings, oanc_state = build_oanc(slug, today, previous(slug))
    calendars.append({"name": "DC Office of ANCs meeting notices", "url": OANC_PAGE, "state": oanc_state})
    agenda_days = {(e["source"], e["date"]) for e in anc}
    for m in meetings:
        d = date.fromisoformat(m["date"])
        if today <= d < today + timedelta(days=DAYS_AHEAD) and (m["anc"], m["date"]) not in agenda_days:
            anc.append({"title": f"{m['anc']} {'special ' if m['special'] else ''}public meeting", "date": m["date"], "time": None,
                        "place": None, "url": m["url"], "source": m["anc"], "kind": "civic"})
    events = sorted(markets + community + anc, key=lambda e: (e["date"], e.get("time") or "", e["title"]))
    return {
        "generated_at": iso(int(now * 1000)),
        "today": today.isoformat(),
        "days_ahead": DAYS_AHEAD,
        "sources": [{"name": c["name"], "url": c["url"]} for c in calendars],
        "calendars": calendars,
        "events": events,
        "unscheduled": unread,
        "links": LINKS.get(slug, []),
        "ancs": [f"ANC {a}" for a in ANCS.get(slug, [])],
        "anc_meetings": meetings,
    }


def check(section: dict) -> list[str]:
    errors = []
    for key in ("generated_at", "today", "sources", "calendars", "events", "unscheduled", "links"):
        if key not in section:
            errors.append(f"events: missing {key}")
    if errors:
        return errors
    # DC's own data must read; a community calendar being down for a night is shown on the page, not fatal.
    if any(c["name"] == "DC farmers market list" and c["state"] != "ok" for c in section["calendars"]):
        errors.append("events: DC farmers market list not read")
    today = date.fromisoformat(section["today"])
    for e in section["events"]:
        if not (e.get("title") and e.get("url", "").startswith("http") and e.get("source") and e.get("date")):
            errors.append(f"events: incomplete {e}")
            continue
        d = date.fromisoformat(e["date"])
        if not (today <= d < today + timedelta(days=section["days_ahead"])):
            errors.append(f"events: {e['title']} on {d} is outside the window")
        if set(e) - {"title", "date", "time", "place", "url", "source", "kind"}:
            errors.append(f"events: extra fields {sorted(set(e))}")
    errors += [f"events: forbidden field {h}" for h in find_forbidden(section)]
    return errors


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    slug = sys.argv[1] if len(sys.argv) > 1 else "petworth"
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if not hood:
        print(f"unknown neighborhood {slug!r}", file=sys.stderr)
        return 2
    t0 = time.time()
    geom = dcdata.hood_boundary(config, hood)
    section = build(geom, hood, time.time())
    out_dir = ROOT / "ingest" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"events-{slug}.json").write_text(json.dumps(section, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{slug}: {len(section['events'])} events from {section['today']} ({time.time() - t0:.0f}s)")
    for c in section["calendars"]:
        print(f"  {c['name']:32} {c['state']}")
    for e in section["events"][:12]:
        print(f"  {e['date']} {e.get('time') or '':22} {e['title'][:50]} [{e['source']}]")
    for u in section["unscheduled"]:
        print(f"  (schedule unread) {u['title']}: {u['schedule']}")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("events ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
