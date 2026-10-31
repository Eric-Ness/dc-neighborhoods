"""Demo #13: Mall Day Planner from L'Enfant (transit-tech#7).

Writes demos/ideas/13-mall-day-planner.html.
Live: Capital Bikeshare GBFS docks near the station; NWS forecast for the station's grid point (both keyless).
Verified static: SW Shuttle schedule (wharfdc.com), Air and Space Museum hours (si.edu), station entrances (wmata.com).
Sample: NPS alerts and permitted events (NPS API key needed), elevator status (WMATA key needed).
Museum hours we could not verify are "Check hours" links, never invented.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "13-mall-day-planner.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

GBFS = "https://gbfs.capitalbikeshare.com/gbfs/gbfs.json"
NWS_POINT = "https://api.weather.gov/points/38.8849,-77.0219"
STATION = (38.8849, -77.0219)  # 650 Maryland Ave SW, approximate
WMATA_INFO = "https://www.wmata.com/ridertools/station/l'enfant-plaza/info"
SHUTTLE = "https://www.wharfdc.com/getting-here/the-wharf-shuttle/"
NPS_API = "https://www.nps.gov/subjects/developer/get-started.htm"

e = html.escape

# Places on and near the Mall. Coordinates are approximate building points used only for walk estimates.
# "hours" is filled only where we found the figure on the operator's own page; otherwise a link.
PLACES = [
    {"name": "National Air and Space Museum", "pt": (38.8882, -77.0199), "kind": "Smithsonian",
     "hours": "10 a.m.–5:30 p.m. daily; closed Dec. 25. Free timed-entry pass required.",
     "src": "https://www.si.edu/museums/air-and-space-museum", "stroller": True},
    {"name": "Hirshhorn Museum and Sculpture Garden", "pt": (38.8881, -77.0230), "kind": "Smithsonian",
     "src": "https://www.si.edu/museums/hirshhorn-museum"},
    {"name": "National Museum of the American Indian", "pt": (38.8881, -77.0165), "kind": "Smithsonian",
     "src": "https://www.si.edu/museums/american-indian-museum"},
    {"name": "National Museum of Natural History", "pt": (38.8913, -77.0261), "kind": "Smithsonian",
     "src": "https://www.si.edu/museums/natural-history-museum"},
    {"name": "National Museum of American History", "pt": (38.8913, -77.0300), "kind": "Smithsonian",
     "src": "https://www.si.edu/museums/american-history-museum"},
    {"name": "National Museum of African American History and Culture", "pt": (38.8911, -77.0326), "kind": "Smithsonian",
     "src": "https://www.si.edu/museums/african-american-museum"},
    {"name": "National Gallery of Art (West Building)", "pt": (38.8913, -77.0198), "kind": "Museum",
     "src": "https://www.nga.gov/visit"},
    {"name": "U.S. Holocaust Memorial Museum", "pt": (38.8867, -77.0326), "kind": "Museum",
     "src": "https://www.ushmm.org/information/visit-the-museum"},
    {"name": "U.S. Botanic Garden", "pt": (38.8881, -77.0129), "kind": "Garden",
     "src": "https://www.usbg.gov/visit"},
    {"name": "U.S. Capitol (Visitor Center)", "pt": (38.8899, -77.0091), "kind": "Landmark",
     "src": "https://www.visitthecapitol.gov/"},
    {"name": "Washington Monument", "pt": (38.8895, -77.0353), "kind": "NPS",
     "src": "https://www.nps.gov/wamo/"},
    {"name": "Lincoln Memorial", "pt": (38.8893, -77.0502), "kind": "NPS",
     "src": "https://www.nps.gov/linc/"},
    {"name": "International Spy Museum", "pt": (38.8840, -77.0254), "kind": "Museum",
     "src": "https://www.spymuseum.org/"},
    {"name": "The Wharf", "pt": (38.8786, -77.0233), "kind": "Waterfront",
     "src": "https://www.wharfdc.com/"},
    {"name": "Tidal Basin (Jefferson Memorial side)", "pt": (38.8814, -77.0365), "kind": "NPS",
     "src": "https://www.nps.gov/thje/"},
]


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": dcdata.USER_AGENT, "Accept": "application/geo+json, application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def meters(a, b) -> float:
    p = math.radians
    h = math.sin(p(b[0] - a[0]) / 2) ** 2 + math.cos(p(a[0])) * math.cos(p(b[0])) * math.sin(p(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def walk_min(m: float) -> int:
    return max(1, round(m * 1.3 / 80))  # street-grid factor, 80 m/min


def eastern(now_utc: dt.datetime) -> dt.datetime:
    y = now_utc.year
    mar = dt.datetime(y, 3, 8 + (6 - dt.date(y, 3, 8).weekday()) % 7, 7, tzinfo=dt.timezone.utc)
    nov = dt.datetime(y, 11, 1 + (6 - dt.date(y, 11, 1).weekday()) % 7, 6, tzinfo=dt.timezone.utc)
    return (now_utc + dt.timedelta(hours=-4 if mar <= now_utc < nov else -5)).replace(tzinfo=None)


def nearest_docks(n: int = 4):
    feeds = {f["name"]: f["url"] for f in get_json(GBFS)["data"]["en"]["feeds"]}
    info = get_json(feeds["station_information"])["data"]["stations"]
    status = {s["station_id"]: s for s in get_json(feeds["station_status"])["data"]["stations"]}
    rows = []
    for s in info:
        d = meters(STATION, (s["lat"], s["lon"]))
        st = status.get(s["station_id"])
        if st and d <= 700:
            rows.append({"name": s["name"], "m": round(d), "bikes": st.get("num_bikes_available", 0),
                         "ebikes": st.get("num_ebikes_available", 0), "docks": st.get("num_docks_available", 0)})
    rows.sort(key=lambda r: r["m"])
    return rows[:n], feeds["station_status"]


def forecast():
    """Two NWS calls: grid point lookup, then the 12-hour period forecast. Returns (periods, url) or (None, None)."""
    try:
        url = get_json(NWS_POINT)["properties"]["forecast"]
        periods = get_json(url)["properties"]["periods"][:3]
        return periods, url
    except Exception as exc:  # weather is a nice-to-have; the page still builds
        print(f"NWS forecast unavailable: {exc}")
        return None, None


def shuttle_status(local: dt.datetime) -> tuple[str, str]:
    """Schedule as published on wharfdc.com: Mon-Fri 7am-7pm; Sat 12pm-6pm Apr 1-Oct 31; no Sunday hours listed."""
    wd = local.weekday()
    if wd < 5:
        span = (7, 19, "Mon–Fri 7 a.m.–7 p.m.")
    elif wd == 5 and (4, 1) <= (local.month, local.day) <= (10, 31):
        span = (12, 18, "Saturdays 12–6 p.m., Apr. 1–Oct. 31")
    else:
        return "No service listed today", "The published schedule lists no hours for today. Event-day service is posted on the shuttle page."
    start, end, label = span
    h = local.hour + local.minute / 60
    if h < start:
        return f"Starts at {start if start <= 12 else start - 12} {'a.m.' if start < 12 else 'p.m.'}", label
    if h < end:
        return f"Running now until {end - 12} p.m.", label
    return "Done for today", label


def build() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    local = eastern(now)
    docks, gbfs_status = nearest_docks()
    periods, nws_url = forecast()
    shuttle_now, shuttle_hours = shuttle_status(local)
    last_sat = local.weekday() == 5 and (local.month, local.day) == (10, 31)

    # Weather banner
    if periods:
        p0 = periods[0]
        temp = p0.get("temperature")
        hot = isinstance(temp, (int, float)) and temp >= 88
        wet = bool(re.search(r"rain|showers|storm", p0.get("shortForecast", ""), re.I))
        tip = ("Hot one: refill bottles at museum fountains and take breaks indoors." if hot else
               "Rain likely: plan museum time first and keep the Mall walks short." if wet else
               "Good walking weather. Most Mall museums are a 5–15 minute walk from the station.")
        wx = (f'<div class="wx"><div class="wx-t"><b>{e(str(temp))}°{e(p0.get("temperatureUnit", "F"))}</b>'
              f'<span>{e(p0["name"])}: {e(p0.get("shortForecast", ""))}</span></div>'
              f'<p>{e(tip)}</p><p class="small"><span class="badge live">Live</span> National Weather Service forecast, pulled at build time.'
              + "".join(f' {e(p["name"])}: {e(str(p["temperature"]))}° {e(p["shortForecast"])}.' for p in periods[1:]) + "</p></div>")
    else:
        wx = '<div class="wx"><p>Forecast unavailable at build time. <a href="https://forecast.weather.gov/MapClick.php?lat=38.8849&lon=-77.0219">Check weather.gov</a>.</p></div>'

    rows = []
    for pl in sorted(PLACES, key=lambda p: meters(STATION, p["pt"])):
        w = walk_min(meters(STATION, pl["pt"]))
        if pl.get("hours"):
            hrs = f'{e(pl["hours"])} <a href="{pl["src"]}">si.edu</a>'
        else:
            hrs = f'<a class="chk" href="{pl["src"]}">Check hours</a>'
        rows.append(f'<tr><td><b>{e(pl["name"])}</b><br><span class="muted small">{e(pl["kind"])}</span></td>'
                    f'<td class="n">~{w} min</td><td>{hrs}</td></tr>')
    museum_table = ('<div class="scroll"><table><thead><tr><th>Place</th><th class="n">Walk (est.)</th><th>Hours today</th></tr></thead>'
                    f'<tbody>{"".join(rows)}</tbody></table></div>')

    dock_rows = "".join(f'<li><b>{d["bikes"]}</b> bikes{f" ({d["ebikes"]} e-bikes)" if d["ebikes"] else ""} · {d["docks"]} open docks — {e(d["name"])} <span class="muted">({d["m"]} m)</span></li>' for d in docks)

    body = f"""
<div class="today">
  <div class="date">{local:%A}, {local:%B} {local.day}</div>
  <button class="print" onclick="window.print()">Print for the front desk</button>
</div>

{wx}

<div class="card">
  <h2>On the Mall today <span class="badge sample">sample</span></h2>
  <ul class="alerts">
    <li><b>[Sample NPS alert]</b> A memorial area or path closure would appear here, from the National Park Service alerts feed.</li>
    <li><b>[Sample permitted event]</b> A permitted rally, festival or race would appear here with its location and time.</li>
  </ul>
  <p class="small muted">These two lines are placeholders. The real page pulls the <a href="{NPS_API}">NPS API</a> alerts and events each morning (free key, not yet registered).</p>
</div>

<div class="card">
  <h2>Where to go, and how far</h2>
  <p class="small muted">Walk times from the station's 7th St/Maryland Ave entrance area, estimated from map distance. We list hours only where the
  museum's own page states them; everything else links out so you never get a wrong time from us.</p>
  {museum_table}
</div>

<div class="grid two">
  <div class="card">
    <h2>Free SW Shuttle</h2>
    <p class="big">{e(shuttle_now)}</p>
    <p class="small">{e(shuttle_hours)}.{" Today is the last Saturday of the season." if last_sat else ""} Stops include L'Enfant Plaza Metro &amp; VRE
    (7th St at Maryland Ave SW) and the National Mall (Independence Ave at 7th St SW, near the Hirshhorn). Free.
    <a href="{SHUTTLE}">Schedule source</a>.</p>
  </div>
  <div class="card">
    <h2>Stroller route <span class="badge sample">sample status</span></h2>
    <p class="big ok">All 4 station elevators running</p>
    <p class="small">Use the 7th St/Maryland Ave · Smithsonian Museums entrance: WMATA lists an elevator from street to mezzanine there, and elevators
    from the mezzanine to both Green/Yellow platforms (<a href="{WMATA_INFO}">station page</a>). Status above is sample until the WMATA feed is connected.</p>
  </div>
</div>

<div class="card">
  <h2>Bike it <span class="badge live">live</span></h2>
  <ul class="docks">{dock_rows or "<li>No docks reported within 700 m.</li>"}</ul>
  <p class="small muted">Capital Bikeshare, as of {local:%I:%M %p} DC time when this page was built.</p>
</div>

<div class="sponsor card"><div class="label">Sponsor slot (lenfantplaza.net only)</div>[Hotel or tour sponsor] — the .org version stays ad-free.</div>
"""

    extra_css = """
.today{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;margin:6px 0}
.date{font-size:1.15rem;font-weight:700}
.print{font:inherit;font-size:.85rem;padding:6px 12px;border:1px solid var(--accent);background:var(--card);color:var(--accent);border-radius:999px;cursor:pointer}
.wx{background:linear-gradient(135deg,var(--soft),var(--card));border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:12px 0}
.wx-t{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline}.wx-t b{font-size:2rem}
.wx p{margin:.3rem 0}
.alerts{padding-left:1.1rem;margin:.2rem 0}.alerts li{margin:.3rem 0}
.two{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}.two .card{margin:0}
.big{font-size:1.25rem;font-weight:700;margin:.2rem 0}.ok{color:var(--down)}
.small{font-size:.86rem}
.docks{list-style:none;padding:0;margin:0}.docks li{padding:5px 0;border-bottom:1px solid var(--line);font-size:.92rem}
a.chk{font-weight:600;white-space:nowrap}
@media print{.demo-bar,.print,.sponsor,#about-demo{display:none}body{background:#fff;color:#000}.card,.wx{break-inside:avoid;border-color:#999}}
"""

    repl = {
        "IDEA_ID": "transit-tech#7", "RANK": "13", "SCORE": "71.5",
        "SHORT_NAME": "Mall Day Planner",
        "PROVENANCE_CLASS": "sample", "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": "lenfantplaza.org · Your Mall day",
        "HEADLINE": "Your Mall day, starting from L'Enfant Plaza",
        "DECK": "Weather, what's open, how far it is, the free shuttle and the step-free way in. One page, checked the morning of.",
        "BODY": body, "EXTRA_CSS": extra_css,
        "PITCH": "A one-page morning-of dashboard for visitors coming through L'Enfant Plaza: Mall closures and events, museum hours, weather tips, the free SW Shuttle, walking times and elevator status for strollers, printable for hotel front desks.",
        "WHATS_REAL": (
            "Live at build time: the National Weather Service forecast for the station's grid point and Capital Bikeshare dock counts within 700 m. "
            "Verified on the operators' pages: the SW Shuttle's hours and stops (wharfdc.com), the station's entrances and elevators (wmata.com), and the "
            "Air and Space Museum's hours (si.edu, read from search results because si.edu blocked our direct fetch; confirm before relying on it)."
        ),
        "WHATS_MOCKED": (
            "The NPS alert and permitted-event lines are placeholders, and elevator status is sample (no NPS or WMATA keys yet). "
            "Other museum hours are not shown at all, only \"Check hours\" links. Walk times are map-distance estimates (×1.3, 80 m/min) from approximate coordinates."
        ),
        "NEXT_STEPS": (
            "Register free NPS and WMATA keys. Run a 6 a.m. Worker cron that pulls NPS alerts and events for the Mall parks, NWS forecast and heat index, "
            "WMATA ElevatorIncidents, and the shuttle page, then re-renders this static page. Museum hours have no API, so scrape each si.edu museum page "
            "with a check that fails loudly when the layout changes, and fall back to \"Check hours\" links. Time the walks on foot once. Put ads and "
            "hotel sponsorship only on the lenfantplaza.net copy."
        ),
        "SOURCES": (
            f'<a href="{SHUTTLE}">Wharf Neighborhood Shuttle</a>, <a href="{WMATA_INFO}">WMATA station page</a>, '
            '<a href="https://www.si.edu/museums/air-and-space-museum">si.edu Air and Space Museum</a>, '
            f'<a href="{nws_url or "https://www.weather.gov/"}">National Weather Service</a> (live), '
            f'<a href="{gbfs_status}">Capital Bikeshare GBFS</a> (live)'
        ),
        "GENERATED_UTC": now.strftime("%Y-%m-%d %H:%M UTC"),
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    page = re.sub(r"<!--.*?-->\s*", "", page, count=1, flags=re.S)
    for k, v in repl.items():
        page = page.replace("{{" + k + "}}", v)
    page = page.replace("any ANC, BID or property owner.", "any ANC, BID or property owner. Not affiliated with WMATA, the Smithsonian or the National Park Service.")
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page) // 1024} KB, {len(docks)} docks, weather={'yes' if periods else 'no'})")


if __name__ == "__main__":
    build()
