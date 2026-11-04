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

CALENDARS = {"tenleytown": ["tms"], "petworth": [], "brookland": ["danceplace", "shrine"], "palisades": ["pca"],
             "chinatown": ["mvtcid"], "lenfantplaza": ["swbid"]}
# DC's Office of ANCs announces every ANC's public meetings in one feed (latest ~10 items only), so
# matches for this neighborhood's ANCs are archived run to run, like the headlines.
OANC_FEED = "https://oanc.dc.gov/rss.xml"
OANC_PAGE = "https://oanc.dc.gov/"
ANCS = {"petworth": ["4C", "4D"], "tenleytown": ["3E", "3F", "3/4G"], "adamsmorgan": ["1C", "2B"], "friendshipheights": ["3E"],
        # From ingest/setup_hood.py (SMD centroids inside each boundary), 2026-11-01.
        "capitolhill": ["6B", "6C"], "columbiaheights": ["1A", "1E", "1D"], "georgetown": ["2E"], "chevychase": ["3/4G"],
        "anacostia": ["8A", "8B"], "clevelandpark": ["3C"], "dupontcircle": ["2B"], "hstreet": ["6A", "6C"],
        "navyyard": ["8F", "6B", "6D"],
        "brookland": ["5B", "5F", "5A"], "chinatown": ["2C", "6E"], "gloverpark": ["3B"], "lenfantplaza": ["6D"], "noma": ["6E", "5F", "6C"],
        "palisades": ["3D"], "shaw": ["2G"], "logancircle": ["2F"], "ustreet": ["1B", "1E"], "vanness": ["3F"],
        "bloomingdale": ["5E", "5F"], "foggybottom": ["2A"], "hilleast": ["6B", "7D"], "kingmanpark": ["6A", "7D"], "mountpleasant": ["1D"],
        "stadiumarmory": ["7D", "6B", "7F"], "trinidad": ["5D"], "woodleypark": ["3C"]}
OANC_TITLE = re.compile(r"^([A-Z][a-z]+ \d{1,2}, \d{4}),?\s+(?:ANC\s+)?([0-9/]+[A-Z])\s+(?:In[-\s]Person\s+)?(Special\s+)?(?:(?:Public|Virtual|Regular)\s+)?Meeting", re.I)
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
    # Added 2026-11-01 (ingest/SOURCES-NORTHWEST.md): sources with no machine-readable calendar, linked instead.
    "brookland": [
        {"name": "Woodridge Library events", "url": "https://dclibrary.libnet.info/events?l=Woodridge%20Neighborhood%20Library"},
        {"name": "ANC 5B meetings", "url": "https://www.anc5b.org/meetings"},
        {"name": "Catholic University events", "url": "https://www.catholic.edu/event-calendar"},
    ],
    "gloverpark": [
        {"name": "ANC 3B meeting schedule", "url": "https://anc3b.org/meeting-schedule/"},
        {"name": "Glover Park Citizens' Association", "url": "https://gpcadc.org/"},
        {"name": "Georgetown Library events", "url": "https://dclibrary.libnet.info/events?l=Georgetown%20Neighborhood%20Library"},
    ],
    "palisades": [
        {"name": "Palisades Library events", "url": "https://dclibrary.libnet.info/events?l=Palisades%20Neighborhood%20Library"},
        {"name": "ANC 3D", "url": "https://www.anc3d.org/"},
    ],
    "vanness": [
        {"name": "Van Ness Main Street events", "url": "https://vannessmainstreet.org/events/"},
        {"name": "UDC events", "url": "https://www.udc.edu/"},
        {"name": "Cleveland Park Library events", "url": "https://dclibrary.libnet.info/events?l=Cleveland%20Park%20Neighborhood%20Library"},
    ],
    # (ingest/SOURCES-CENTRAL.md) The library location names in these links follow DCPL's pattern but weren't confirmed.
    "chinatown": [
        {"name": "MLK Library events", "url": "https://dclibrary.libnet.info/events?l=Martin%20Luther%20King%20Jr.%20Memorial%20Library"},
        {"name": "DowntownDC BID events", "url": "https://www.downtowndc.org/events/"},
        {"name": "ANC 2C", "url": "https://anc2c.dc.gov/"},
    ],
    "lenfantplaza": [
        {"name": "Southwest Library events", "url": "https://dclibrary.libnet.info/events?l=Southwest%20Neighborhood%20Library"},
        {"name": "The Wharf events", "url": "https://www.wharfdc.com/upcoming-events/"},
        {"name": "ANC 6D meeting schedule", "url": "https://www.anc6d.org/"},
    ],
    "noma": [
        {"name": "NoMa BID events", "url": "https://www.nomabid.org/events/"},
        {"name": "ANC 6E", "url": "https://anc6e.dc.gov/"},
    ],
    "shaw": [
        {"name": "Shaw Library events", "url": "https://dclibrary.libnet.info/events?l=Shaw%20(Watha%20T.%20Daniel)%20Neighborhood%20Library"},
        {"name": "Shaw Main Streets", "url": "https://www.shawmainstreets.org/"},
        {"name": "ANC 2G meetings", "url": "https://www.anc2g.org/meetings"},
    ],
    "logancircle": [
        {"name": "Logan Circle Community Association", "url": "https://www.logancircle.org/"},
        {"name": "ANC 2F", "url": "https://anc2f.org/"},
    ],
    "ustreet": [
        {"name": "ANC 1B meetings", "url": "https://www.anc1b.org/"},
        {"name": "District Bridges events (U Street Main Street)", "url": "https://districtbridges.org/events/"},
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
    if re.search(r"year.?round", f"{start or ''} {end or ''}", re.I):
        return True
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


# Calendars run on WordPress's "The Events Calendar" plugin publish a JSON API at /wp-json/tribe/events/v1/events.
# key -> (name, API url, page to link, titles to drop (regex or None), robots Crawl-delay in seconds). Researched in
# ingest/SOURCES-NORTHWEST.md and SOURCES-CENTRAL.md.
TRIBE: dict[str, tuple[str, str, str, str | None, int]] = {
    "danceplace": ("Dance Place", "https://www.danceplace.org/wp-json/tribe/events/v1/events", "https://www.danceplace.org/", None, 0),
    # Mostly the liturgical calendar and pilgrimages, so only concerts, recitals, lectures and exhibitions stay.
    "shrine": ("Basilica of the National Shrine", "https://www.nationalshrine.org/wp-json/tribe/events/v1/events",
               "https://www.nationalshrine.org/", r"^(?!.*\b(concerts?|recitals?|lectures?|choral|organ|choirs?|exhibits?|exhibitions?|festival)\b)", 0),
    # Its Sunday farmers market is kept: DC's market layer lists that market as "Sundays" with no season, so only
    # this calendar gives it dates.
    "pca": ("Palisades Citizens' Association", "https://palisadesdc.org/wp-json/tribe/events/v1/events", "https://palisadesdc.org/",
            None, 0),
    # Its FRESHFARM market is kept for the same reason as the Palisades one (the market layer can't date it).
    "mvtcid": ("Mount Vernon Triangle CID", "https://www.mvtcid.org/wp-json/tribe/events/v1/events", "https://www.mvtcid.org/",
               None, 10),
    "swbid": ("Southwest BID", "https://www.swbid.org/wp-json/tribe/events/v1/events", "https://www.swbid.org/", None, 0),
}

# Added 2026-11-02 (ingest/SOURCES-LATE.md). ANC 2A's meetings come through the OANC feed.
ANCS["bloomingdale"] = ["5E", "5F"]
LINKS["bloomingdale"] = [
    {"name": "Bloomingdale Civic Association calendar", "url": "https://bloomingdalecivicassociation.org/calendar-2/"},
    {"name": "Eckington Civic Association", "url": "https://eckingtoncivicassociation.com/"},
    {"name": "Shaw Library events", "url": "https://dclibrary.libnet.info/events?l=Shaw%20(Watha%20T.%20Daniel)%20Neighborhood%20Library"},
    {"name": "Northwest One Library events", "url": "https://dclibrary.libnet.info/events?l=Northwest%20One%20Neighborhood%20Library"},
]
ANCS["foggybottom"] = ["2A", "2B", "2C"]
LINKS["foggybottom"] = [
    {"name": "ANC 2A meetings", "url": "https://anc2a.org/meetings/"},
    {"name": "Foggy Bottom Association", "url": "https://www.foggybottomassociation.org/"},
    {"name": "Golden Triangle BID", "url": "https://goldentriangledc.com/"},
    {"name": "West End Library events", "url": "https://dclibrary.libnet.info/events?l=West%20End%20Neighborhood%20Library"},
]
ANCS["hilleast"] = ["6B", "7D"]
LINKS["hilleast"] = [
    {"name": "Southeast Library events", "url": "https://dclibrary.libnet.info/events?l=Southeast%20Neighborhood%20Library"},
    {"name": "ANC 6B calendar", "url": "https://anc6b.org/calendar/"},
    {"name": "ANC 7D", "url": "https://anc7d.dc.gov/"},
    {"name": "Hill East Civic Association", "url": "https://hilleastcivicassociation.org/"},
]
ANCS["kingmanpark"] = ["6A", "7D"]
LINKS["kingmanpark"] = [
    {"name": "Rosedale Library events", "url": "https://dclibrary.libnet.info/events?l=Rosedale%20Neighborhood%20Library"},
    {"name": "Kingman and Heritage Islands calendar", "url": "https://www.kingmanisland.com/calendar"},
    {"name": "ANC 7D", "url": "https://anc7d.dc.gov/"},
    {"name": "ANC 6A calendar", "url": "https://anc6a.org/community-calendar/"},
]
ANCS["mountpleasant"] = ["1D"]
LINKS["mountpleasant"] = [
    {"name": "Mt. Pleasant Library events", "url": "https://dclibrary.libnet.info/events?l=Mt.%20Pleasant%20Neighborhood%20Library"},
    {"name": "ANC 1D meetings", "url": "https://anc1d.org/meetingcalendar"},
    {"name": "District Bridges events", "url": "https://districtbridges.org/events/"},
    {"name": "Mount Pleasant Village", "url": "https://mountpleasantvillage.org/events/"},
]
TRIBE["congcem"] = ("Historic Congressional Cemetery", "https://www.congressionalcemetery.org/wp-json/tribe/events/v1/events",
                    "https://www.congressionalcemetery.org/", r"closed to dogs|private funeral|office closed|cemetery closed", 0)
CALENDARS["stadiumarmory"] = ["congcem"]
ANCS["stadiumarmory"] = ["7D", "7F", "6B"]
LINKS["stadiumarmory"] = [
    {"name": "ANC 7D", "url": "https://anc7d.dc.gov/"},
    {"name": "DC Office of ANCs calendar (ANC 7F)", "url": "https://oanc.dc.gov/"},
    {"name": "Events DC events", "url": "https://eventsdc.com/events"},
    {"name": "Kingman and Heritage Islands calendar", "url": "https://www.kingmanisland.com/calendar"},
]
TRIBE["unionmarket"] = ("Union Market District", "https://unionmarketdc.com/wp-json/tribe/events/v1/events", "https://unionmarketdc.com/events/",
                        r"freshfarm|cooking\s+class|making\s+class|mural\s+tour|gnocchi|pasta|dumpling|mozzarella|focaccia|tapas|tagliatelle|ravioli|run\s+club", 0)
CALENDARS["trinidad"] = ["unionmarket"]
ANCS["trinidad"] = ["5D", "5C"]
LINKS["trinidad"] = [
    {"name": "ANC 5D", "url": "https://www.anc5d.org/"},
    {"name": "Union Market District events", "url": "https://unionmarketdc.com/events/"},
    {"name": "Rosedale Library events", "url": "https://dclibrary.libnet.info/events?l=Rosedale%20Neighborhood%20Library"},
    {"name": "Gallaudet University", "url": "https://www.gallaudet.edu/"},
]
ANCS["woodleypark"] = ["3C"]
LINKS["woodleypark"] = [
    {"name": "ANC 3C calendar", "url": "https://anc3c.dc.gov/anc-calendar"},
    {"name": "Woodley Park Community Association", "url": "https://wpcaonline.org/"},
    {"name": "National Zoo events", "url": "https://nationalzoo.si.edu/events"},
    {"name": "Cleveland Park Library events", "url": "https://dclibrary.libnet.info/events?l=Cleveland%20Park%20Neighborhood%20Library"},
]


ANCS["brightwood"] = ["4A", "4B", "4D"]
LINKS["brightwood"] = [
    {"name": "ANC 4A", "url": "https://anc4a.dc.gov/"},
    {"name": "ANC 4D", "url": "https://anc4d.org/"},
    {"name": "Uptown Main Street (Kennedy Street)", "url": "https://www.uptownmainstreet.org/news-events"},
    {"name": "Petworth Library events", "url": "https://dclibrary.libnet.info/events?l=Petworth%20Neighborhood%20Library"},
]
ANCS["deanwood"] = ["7C"]
LINKS["deanwood"] = [
    {"name": "Deanwood Library events", "url": "https://dclibrary.libnet.info/events?l=Deanwood%20Neighborhood%20Library"},
    {"name": "DC Office of ANCs calendar (ANC 7C)", "url": "https://oanc.dc.gov/"},
]
ANCS["hillcrest"] = ["7B", "8B"]
LINKS["hillcrest"] = [
    {"name": "Francis A. Gregory Library events", "url": "https://dclibrary.libnet.info/events?l=Francis%20A.%20Gregory%20Neighborhood%20Library"},
    {"name": "ANC 8B", "url": "https://anc8b.dc.gov/"},
]
ANCS["bellevue"] = ["8D", "8E"]
LINKS["bellevue"] = [
    {"name": "Bellevue Library events", "url": "https://dclibrary.libnet.info/events?l=William%20O.%20Lockridge%2FBellevue%20Neighborhood%20Library"},
    {"name": "ANC 8E", "url": "https://anc8e.dc.gov/"},
    {"name": "DC Office of ANCs calendar", "url": "https://oanc.dc.gov/"},
]
ANCS["16thstreetheights"] = ["4E"]
LINKS["16thstreetheights"] = [
    {"name": "ANC 4E", "url": "https://anc4e.dc.gov/"},
    {"name": "DC Office of ANCs calendar", "url": "https://oanc.dc.gov/"},
]
ANCS["congressheights"] = ["8C", "8E"]
LINKS["congressheights"] = [
    {"name": "ANC 8C calendar", "url": "https://www.anc8c.org/calendar"},
    {"name": "ANC 8E", "url": "https://anc8e.dc.gov/"},
    {"name": "Parklands-Turner Library events", "url": "https://dclibrary.libnet.info/events?l=Parklands-Turner%20Neighborhood%20Library"},
    {"name": "Congress Heights on the Rise", "url": "https://www.congressheightsontherise.com/"},
]
ANCS["takoma"] = ["4A", "4B"]
LINKS["takoma"] = [
    {"name": "Takoma Library events", "url": "https://dclibrary.libnet.info/events?l=Takoma%20Park%20Neighborhood%20Library"},
    {"name": "The Parks at Walter Reed events", "url": "https://theparksdc.com/events/"},
    {"name": "ANC 4B", "url": "https://anc4b.com/"},
    {"name": "Shepherd Park Citizens Association", "url": "https://www.shepherdpark.org/"},
    {"name": "Historic Takoma", "url": "https://www.historictakoma.org/"},
]
TRIBE["bca"] = ("Brightwood Community Association", "https://brightwoodcommunity.org/wp-json/tribe/events/v1/events", "https://brightwoodcommunity.org/calendar/", None, 10)
CALENDARS["brightwood"] = ["bca"]
TRIBE["bbar"] = ("Building Bridges Across the River", "https://buildingbridgesdc.org/wp-json/tribe/events/v1/events", "https://buildingbridgesdc.org/",
                 r"^volunteer\b|union\s+temple|hopkins\s+garden", 0)
CALENDARS["congressheights"] = ["bbar"]
TRIBE["mainstreettakoma"] = ("Main Street Takoma", "https://mainstreettakoma.org/wp-json/tribe/events/v1/events", "https://mainstreettakoma.org/events/",
                             r"flatfoot|\btap\b|tap\s+class|woof\s+clinic|whittier\s+farm\s+stand|\bclass(es)?\b|pilates|workshop", 0)
CALENDARS["takoma"] = ["mainstreettakoma"]
# Calendars that straddle the DC line: keep only events at a DC venue.
TRIBE_DC_ONLY = {"mainstreettakoma"}
MAX_TRIBE_PAGES = 6


def dc_venue(v: dict) -> bool:
    """Venue data is typed in by hand, so any one of state, city or a DC quadrant in the address will do."""
    state = (v.get("state") or v.get("stateprovince") or "").strip().upper().replace(".", "")
    city = (v.get("city") or "").strip().lower()
    return state in ("DC", "DISTRICT OF COLUMBIA") or city == "washington" or bool(re.search(r"\b(NW|NE|SE|SW)\b\.?\s*$", news.plain(v.get("address")) or ""))


def tribe_time(s: str | None) -> str | None:
    """'2026-12-04 19:00:00' -> '7 PM'."""
    m = re.match(r"\d{4}-\d\d-\d\d (\d\d):(\d\d)", s or "")
    if not m:
        return None
    h, mi = int(m.group(1)), m.group(2)
    return f"{h % 12 or 12}{'' if mi == '00' else ':' + mi} {'AM' if h < 12 else 'PM'}"


def build_tribe(key: str, today: date) -> tuple[list[dict], str]:
    name, api, page, skip, delay = TRIBE[key]
    end = today + timedelta(days=DAYS_AHEAD - 1)
    url = f"{api}?start_date={today.isoformat()}&end_date={end.isoformat()}&per_page=50"
    if not news.allowed(url):
        return [], "skipped: robots.txt"
    rows, page_no, pages = [], 1, 1
    while page_no <= min(pages, MAX_TRIBE_PAGES):
        if delay:
            time.sleep(delay)
        try:
            data = json.loads(news.fetch(url + (f"&page={page_no}" if page_no > 1 else "")))
        except Exception as e:
            if rows:  # keep the pages we have
                break
            return [], f"error: {type(e).__name__}"
        rows += data.get("events") or []
        pages = data.get("total_pages") or 1
        page_no += 1
    out = []
    for r in rows:
        title = html.unescape(r.get("title") or "").strip()
        try:
            d = date.fromisoformat((r.get("start_date") or "")[:10])
        except ValueError:
            continue
        if not title or (skip and re.search(skip, title, re.I)) or not (today <= d <= end):
            continue
        v = r.get("venue") if isinstance(r.get("venue"), dict) else {}
        if key in TRIBE_DC_ONLY and not dc_venue(v):
            continue
        place = ", ".join(x for x in (news.plain(v.get("venue")), news.plain(v.get("address"))) if x) or None
        s, e = (None, None) if r.get("all_day") else (tribe_time(r.get("start_date")), tribe_time(r.get("end_date")))
        out.append({"title": title, "date": d.isoformat(), "time": f"{s} to {e}" if s and e and s != e else s,
                    "place": place, "url": r.get("url") or page, "source": name, "kind": "community"})
    return out, "ok"


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
    for key in CALENDARS.get(slug, []):
        if key in TRIBE:
            rows, st = build_tribe(key, today)
            community += rows
            calendars.append({"name": TRIBE[key][0], "url": TRIBE[key][2], "state": st})
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
