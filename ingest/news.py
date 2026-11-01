"""`news` section: local headlines that mention the neighborhood, plus newly licensed bars and restaurants.

    python ingest/news.py petworth

Headlines come from local outlets' public RSS feeds. Only the headline, outlet, date and link are kept,
never article text: the site sends readers to the outlet. Each feed is fetched only if the outlet's
robots.txt allows it for our user agent (checked every run), and each item must mention one of the
neighborhood's terms in its headline, summary or tags, except outlets that cover only this
neighborhood (Petworth News), where every item counts.

Feeds hold only their latest 10-20 items, so matches are kept in an archive: the previous run's items
are read back from site/src/data/<slug>.json and merged, and anything older than ARCHIVE_DAYS drops off.

Openings and closings come from liquor licenses (restaurants, bars, shops). New ones come from DC ABCA's "Alcohol License Business Locations" layer: a license number
not in the previous run's list is new. The first run only records the list (nothing can be "new" yet).
Closings come from ABCA's cancellation list, minus places relicensed at the same address under a
similar name. DC publishes no cancellation dates for most, so new cancellations are dated by the night
we first see them. The applicant name is never requested; only the trade name, address and license type.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
from run import find_forbidden, iso  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = dcdata.USER_AGENT  # one honest project user agent for every request
DAY = 86400
ARCHIVE_DAYS = 180
MAX_ITEMS = 80

LICENSES = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer/5"
LICENSES_PAGE = "https://opendata.dc.gov/datasets/alcohol-license-business-locations"
# "APPLICANT" is deliberately absent.
LICENSE_FIELDS = ["LICENSE", "TRADE_NAME", "ADDRESS", "TYPE", "STATUS"]
CANCELLED = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer/42"
CANCELLED_PAGE = "https://opendata.dc.gov/datasets/abca-liquor-license-cancellation"
CANCELLED_FIELDS = ["LICENSE", "TRADE_NAME", "ADDRESS", "TYPE", "CANCELLATION_DATE"]

# (outlet, feed url, home page, mode). "all": the outlet covers only this neighborhood.
# "match": keep items whose headline, summary or tags mention a TERMS pattern.
# "search": a hyper-local outlet's own search feed; the article body counts too. (Washingtonian's search
# is "match": its passing body mentions, like a therapist listicle, aren't neighborhood news.)
WP_SEARCH = "{base}/?s={q}&feed=rss2&orderby=date&order=DESC"
SHARED = [
    ("Washington City Paper", "https://washingtoncitypaper.com/feed/", "https://washingtoncitypaper.com/", "match"),
    ("WTOP", "https://wtop.com/local/dc/feed/", "https://wtop.com/", "match"),
    ("WAMU", "https://wamu.org/feed/", "https://wamu.org/", "match"),
    ("51st", "https://51st.news/rss/", "https://51st.news/", "match"),
    ("Greater Greater Washington", "https://ggwash.org/rss", "https://ggwash.org/", "match"),
    ("Mayor's office", "https://mayor.dc.gov/rss.xml", "https://mayor.dc.gov/newsroom", "match"),
    ("DDOT", "https://ddot.dc.gov/rss.xml", "https://ddot.dc.gov/newsroom", "match"),
    ("DC Parks and Recreation", "https://dpr.dc.gov/rss.xml", "https://dpr.dc.gov/", "match"),
]
FEEDS = {
    "petworth": [
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        ("Petworth News", "https://www.petworthnews.org/blog?format=rss", "https://www.petworthnews.org/", "all"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="petworth"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="petworth"), "https://www.washingtonian.com/", "match"),
        *SHARED,
    ],
    "tenleytown": [
        ("ANC 3E", "https://anc3e.org/feed/", "https://anc3e.org/", "all"),
        ("Forest Hills Connection", "https://foresthillsconnection.com/feed/", "https://foresthillsconnection.com/", "match"),
        ("Forest Hills Connection", WP_SEARCH.format(base="https://foresthillsconnection.com", q="tenleytown"), "https://foresthillsconnection.com/", "search"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="tenleytown"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="tenleytown"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "adamsmorgan": [
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="adams+morgan"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="adams+morgan"), "https://www.washingtonian.com/", "match"),
        *SHARED,
    ],
    "friendshipheights": [
        ("ANC 3E", "https://anc3e.org/feed/", "https://anc3e.org/", "match"),  # also covers Tenleytown, so filtered
        ("Forest Hills Connection", WP_SEARCH.format(base="https://foresthillsconnection.com", q="friendship+heights"), "https://foresthillsconnection.com/", "search"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="friendship+heights"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="friendship+heights"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
}
TERMS = {
    "petworth": re.compile(r"\bpetworth\b|\bupshur st(reet)?\b|\bgrant circle\b|\bsherman circle\b", re.I),
    "adamsmorgan": re.compile(r"\badams[- ]morgan\b|\bkalorama park\b|\blanier heights\b|\bmarie reed\b|\bmintwood\b", re.I),
    # The Friendship Heights site covers both sides of the District line in news (stories about either side
    # matter to residents), so the name counts here, plus DC-side landmarks.
    "friendshipheights": re.compile(r"\bfriendship heights\b|\bmazza gallerie\b|\bchevy chase pavilion\b|\bjenifer st(reet)?\b", re.I),
    # "Friendship Heights" alone is left out: it also names the Maryland side of the line.
    "tenleytown": re.compile(r"\btenleytown\b|\btenley (circle|library)\b|\bfort reno\b|\bjackson[- ]reed\b|\btenley-friendship\b", re.I),
}

_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


def allowed(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    host = f"{parts.scheme}://{parts.netloc}"
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            req = urllib.request.Request(f"{host}/robots.txt", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as r:
                rp.parse(r.read().decode("utf-8", "replace").splitlines())
        except urllib.error.HTTPError as e:
            # Same rule as the stdlib: 401/403 means stay out, any other error means no robots.txt.
            rp.disallow_all = e.code in (401, 403)
            rp.allow_all = not rp.disallow_all
        except Exception:
            rp.allow_all = True
        _robots[host] = rp
    return _robots[host].can_fetch(USER_AGENT, url)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.5"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def plain(s: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s.strip())
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def clean_url(u: str) -> str:
    p = urllib.parse.urlsplit(u.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(("utm_", "mc_"))]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), ""))


XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}


def _fix_entities(raw: bytes) -> bytes:
    """Some feeds (Squarespace) use HTML entities like &nbsp; that XML doesn't define."""
    def sub(m: re.Match) -> bytes:
        name = m.group(1).decode()
        return m.group(0) if name in XML_ENTITIES else html.unescape(f"&{name};").encode("utf-8")
    return re.sub(rb"&([A-Za-z][A-Za-z0-9]*);", sub, raw)


def parse_feed(raw: bytes, body: bool = False) -> list[dict]:
    """RSS 2.0 or Atom -> [{title, url, published, text}] (text is for matching only, never stored).
    body=True also matches on the article body, for outlet search feeds where the outlet already did the search."""
    root = ET.fromstring(_fix_entities(raw))
    out = []
    for it in root.iter():
        tag = it.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        f: dict[str, str] = {}
        cats = []
        for ch in it:
            t = ch.tag.rsplit("}", 1)[-1]
            if t == "link" and ch.get("href"):
                f.setdefault("link", ch.get("href", ""))
            elif t == "category":
                cats.append(ch.text or ch.get("term") or "")
            elif ch.text:
                f.setdefault(t, ch.text)
        url = f.get("link", "")
        title = plain(f.get("title"))
        pub = parse_date(f.get("pubDate") or f.get("published") or f.get("updated") or f.get("date"))
        if url.startswith("http") and title and pub:
            out.append({"title": title, "url": clean_url(url), "published": pub,
                        "text": " ".join([title, plain(f.get("description") or f.get("summary")), " ".join(cats),
                              plain(f.get("encoded") or f.get("content")) if body else ""])})
    return out


def previous(slug: str) -> dict:
    path = ROOT / "site" / "src" / "data" / f"{slug}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("news") or {}
    except (OSError, ValueError):
        return {}


def build_headlines(slug: str, now: float, prev: dict) -> tuple[list[dict], list[dict]]:
    terms = TERMS[slug]
    cutoff = now - ARCHIVE_DAYS * DAY
    found: dict[str, dict] = {}
    status: dict[str, dict] = {}
    for name, url, home, mode in FEEDS[slug]:
        st = status.setdefault(name, {"name": name, "url": home, "state": "ok", "matched": 0})
        if not allowed(url):
            st["state"] = "skipped: robots.txt"
            continue
        try:
            items = parse_feed(fetch(url), body=mode == "search")
        except Exception as e:  # one outlet failing must not sink the others
            st["state"] = f"error: {type(e).__name__}" if st.get("fetched", 0) == 0 else "partial"
            st["failed"] = st.get("failed", 0) + 1
            continue
        st["fetched"] = st.get("fetched", 0) + 1
        if st["state"].startswith("error"):  # an earlier page of this outlet failed, this one worked
            st["state"] = "partial"
        for it in items:
            ts = it["published"].timestamp()
            if ts < cutoff or ts > now + DAY:
                continue
            if mode != "all" and not terms.search(it["text"]):
                continue
            if it["url"] not in found:
                st["matched"] += 1
            found[it["url"]] = {"title": it["title"], "url": it["url"], "source": name,
                                "published": iso(int(ts * 1000)), "first_seen": iso(int(now * 1000))}
        time.sleep(0.5)
    # Merge the archive. Items keep their first_seen; same headline from two feeds counts once.
    for old in prev.get("items", []):
        u = old.get("url")
        if not u or u in found:
            if u in found:
                found[u]["first_seen"] = old.get("first_seen", found[u]["first_seen"])
            continue
        ts = parse_date(old.get("published"))
        if ts and ts.timestamp() >= cutoff:
            found[u] = old
    seen_titles: set[str] = set()
    items = []
    for it in sorted(found.values(), key=lambda x: x["published"], reverse=True):
        key = re.sub(r"\W+", "", it["title"].lower())
        if key in seen_titles:
            continue
        seen_titles.add(key)
        items.append(it)
    return items[:MAX_ITEMS], list(status.values())


def build_licenses(geom: dict, now: float, prev: dict) -> dict:
    rows = dcdata.query_features(LICENSES, geom, "STATUS = 'ACTIVE'", LICENSE_FIELDS)
    current = {r["LICENSE"]: r for r in rows if r.get("LICENSE")}
    old = prev.get("licenses") or {}
    known = set(old.get("ids", []))
    stamp = iso(int(now * 1000))
    new = [n for n in old.get("new", []) if (parse_date(n.get("first_seen")) or datetime.now(timezone.utc)).timestamp() >= now - ARCHIVE_DAYS * DAY]
    if known:  # without a previous list, nothing can be called new
        for lic, r in sorted(current.items()):
            if lic not in known:
                new.append({"license": lic, "trade_name": plain(r.get("TRADE_NAME")) or None,
                            "address": plain(r.get("ADDRESS")), "type": plain(r.get("TYPE")), "first_seen": stamp})
    # Closings: cancelled licenses, minus places relicensed at the same address under a similar name
    # (a license change, like Whole Foods' new license, is not a closing).
    def words(n: str | None) -> set[str]:
        return {w for w in re.findall(r"[a-z]{4,}", (n or "").lower())} - {"restaurant", "market", "cafe", "grill", "kitchen", "lounge", "tavern", "the"}
    active_at: dict[str, set[str]] = {}
    for r in current.values():
        active_at.setdefault(plain(r.get("ADDRESS")).upper(), set()).update(words(r.get("TRADE_NAME")))
    gone_prev = {g["license"]: g for g in old.get("cancelled", [])}
    cancelled = []
    for r in dcdata.query_features(CANCELLED, geom, "1=1", CANCELLED_FIELDS):
        lic, a = r.get("LICENSE"), plain(r.get("ADDRESS"))
        if not lic or lic in current or words(r.get("TRADE_NAME")) & active_at.get(a.upper(), set()):
            continue
        when = r.get("CANCELLATION_DATE")
        cancelled.append({"license": lic, "trade_name": plain(r.get("TRADE_NAME")) or None, "address": a, "type": plain(r.get("TYPE")),
                          "cancelled": iso(when) if when else None,
                          # "first_seen" is the night we first saw it; null for the list as it stood when tracking began
                          "first_seen": gone_prev[lic]["first_seen"] if lic in gone_prev else (stamp if "cancelled" in old else None)})
    cancelled.sort(key=lambda c: (c["cancelled"] or c["first_seen"] or "", c["trade_name"] or ""), reverse=True)
    by_type: dict[str, int] = {}
    for r in current.values():
        t = plain(r.get("TYPE")) or "Other"
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "tracked_since": old.get("tracked_since") or stamp,
        "active": len(current),
        "by_type": [{"type": k, "count": v} for k, v in sorted(by_type.items(), key=lambda kv: -kv[1])],
        "ids": sorted(current),
        "new": sorted(new, key=lambda n: n["first_seen"], reverse=True),
        "cancelled": cancelled,
    }


def build(geom: dict, hood: dict, now: float) -> dict:
    slug = hood["slug"]
    prev = previous(slug)
    items, status = build_headlines(slug, now, prev)
    return {
        "generated_at": iso(int(now * 1000)),
        "archive_days": ARCHIVE_DAYS,
        "sources": [{"name": s["name"], "url": s["url"]} for s in status]
        + [{"name": "DC ABCA, Alcohol License Business Locations (Open Data DC)", "url": LICENSES_PAGE},
           {"name": "DC ABCA, Liquor License Cancellations (Open Data DC)", "url": CANCELLED_PAGE}],
        "outlets": status,
        "items": items,
        "licenses": build_licenses(geom, now, prev),
    }


def check(section: dict) -> list[str]:
    errors = []
    for key in ("generated_at", "sources", "outlets", "items", "licenses"):
        if key not in section:
            errors.append(f"news: missing {key}")
    if errors:
        return errors
    ok = [o for o in section["outlets"] if o["state"] in ("ok", "partial")]
    if len(ok) < len(section["outlets"]) / 2:
        errors.append(f"news: only {len(ok)} of {len(section['outlets'])} outlets fetched")
    if not section["items"]:
        errors.append("news: no headlines")
    for it in section["items"]:
        if not (it.get("url", "").startswith("http") and it.get("title") and it.get("source") and it.get("published")):
            errors.append(f"news: incomplete item {it.get('url')}")
        if set(it) - {"title", "url", "source", "published", "first_seen"}:
            errors.append(f"news: item carries extra fields {sorted(set(it))}")
    if not section["licenses"].get("active"):
        errors.append("news: no active liquor licenses found")
    errors += [f"news: forbidden field {h}" for h in find_forbidden(section)]
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
    (out_dir / f"news-{slug}.json").write_text(json.dumps(section, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{slug}: {len(section['items'])} headlines ({time.time() - t0:.0f}s)")
    for o in section["outlets"]:
        print(f"  {o['name']:24} {o['state']:22} {o['matched']}")
    for it in section["items"][:8]:
        print(f"  {it['published'][:10]} {it['source']:16} {it['title'][:80]}")
    lic = section["licenses"]
    print(f"  liquor licenses: {lic['active']} active, {len(lic['new'])} new")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("news ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
