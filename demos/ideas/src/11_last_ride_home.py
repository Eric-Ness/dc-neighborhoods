"""Demo #11: Last Ride Home (Adams Morgan nightlife edition). Idea transit-tech#3.

Live this run: Capital Bikeshare GBFS (station_information + station_status, keyless) and
Metro station locations from DC GIS (Open Data DC). Sample: train countdowns and bus arrivals,
because we have no WMATA API key.

Run from the repo root: python demos/ideas/src/11_last_ride_home.py
"""

from __future__ import annotations

import html
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

RANK, IDEA_ID, SCORE = 11, "transit-tech#3", "72.1"
OUT = ROOT / "demos" / "ideas" / "11-last-ride-home.html"
GBFS_INFO = "https://gbfs.lyft.com/gbfs/1.1/dca-cabi/en/station_information.json"
GBFS_STATUS = "https://gbfs.lyft.com/gbfs/1.1/dca-cabi/en/station_status.json"
STATIONS_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_Rail_Bus_WebMercator/MapServer/51"
# Approximate corner of 18th St NW and Columbia Rd NW (center of the Adams Morgan bar strip).
ANCHOR = (38.9219, -77.0424)
ANCHOR_NAME = "18th St & Columbia Rd NW"
NEAR_M = 550
WALK_M_PER_MIN = 80  # about 3 mph
DETOUR = 1.3  # street grid vs straight line
STATION_PAGES = {
    "Woodley Park-Zoo/Adams Morgan": "https://www.wmata.com/ridertools/station/woodley-park",
    "Columbia Heights": "https://www.wmata.com/ridertools/station/columbia-heights",
}
DESTINATIONS = ["Georgia Ave-Petworth", "Columbia Heights", "Dupont Circle"]


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": dcdata.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat = math.radians((a[0] + b[0]) / 2)
    dy = (a[0] - b[0]) * 111_320
    dx = (a[1] - b[1]) * 111_320 * math.cos(lat)
    return math.hypot(dx, dy)


def walk_min(m: float) -> int:
    return max(1, round(m * DETOUR / WALK_M_PER_MIN))


def fill(values: dict[str, str]) -> str:
    page = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    page = page.split("-->", 1)[0].split("<!--")[0] + page.split("-->", 1)[1]  # drop template comment
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    assert "{{" not in page, "unfilled placeholder"
    return page


def main() -> None:
    now = time.gmtime()
    today = time.strftime("%Y-%m-%d", now)
    info = get_json(GBFS_INFO)["data"]["stations"]
    status_doc = get_json(GBFS_STATUS)
    status = {s["station_id"]: s for s in status_doc["data"]["stations"]}
    snap_utc = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(status_doc["last_updated"]))

    names = ", ".join(f"'{n}'" for n in [*STATION_PAGES, *DESTINATIONS])
    q = dcdata._request(f"{STATIONS_LAYER}/query", {"where": f"NAME IN ({names})", "outFields": "NAME,LINE", "returnGeometry": "true", "outSR": 4326, "f": "json"})
    metro = {f["attributes"]["NAME"]: (f["geometry"]["y"], f["geometry"]["x"], f["attributes"]["LINE"]) for f in q["features"]}
    missing = [n for n in [*STATION_PAGES, *DESTINATIONS] if n not in metro]
    if missing:
        raise RuntimeError(f"Metro stations not found in DC GIS: {missing}")

    def dock_row(s: dict, origin: tuple[float, float]) -> dict:
        st = status.get(s["station_id"], {})
        d = meters(origin, (s["lat"], s["lon"]))
        ebikes = st.get("num_ebikes_available", 0)
        bikes = st.get("num_bikes_available", 0)
        return {
            "name": s["name"], "m": d, "walk": walk_min(d), "classic": max(0, bikes - ebikes), "ebikes": ebikes,
            "docks": st.get("num_docks_available", 0), "cap": s.get("capacity", 0),
            "ok": bool(st.get("is_renting")) and bool(st.get("is_installed")),
        }

    near = sorted((dock_row(s, ANCHOR) for s in info if meters(ANCHOR, (s["lat"], s["lon"])) <= NEAR_M), key=lambda r: r["m"])
    if not near:
        raise RuntimeError("no bikeshare stations near the anchor; check GBFS")
    total_classic = sum(r["classic"] for r in near if r["ok"])
    total_e = sum(r["ebikes"] for r in near if r["ok"])

    dest_rows = []
    for dname in DESTINATIONS:
        lat, lon, _ = metro[dname]
        rows = sorted((dock_row(s, (lat, lon)) for s in info if meters((lat, lon), (s["lat"], s["lon"])) <= 450), key=lambda r: r["m"])[:3]
        dest_rows.append((dname, rows))

    # Train board: walk times are computed from real coordinates; the countdowns are sample.
    sample_trains = {
        "Woodley Park-Zoo/Adams Morgan": [("Toward Shady Grove", 71), ("Toward Glenmont", 64)],
        "Columbia Heights": [("Northbound, toward Greenbelt", 58), ("Southbound, toward Branch Ave", 52)],
    }
    train_cards = []
    for sname, dirs in sample_trains.items():
        lat, lon, line = metro[sname]
        d = meters(ANCHOR, (lat, lon))
        w = walk_min(d)
        rows = []
        for label, mins in dirs:
            leave = mins - w
            rows.append(
                f'<div class="dir"><span class="dlabel">{html.escape(label)}</span>'
                f'<span class="count" data-min="{leave}"><b>{leave // 60}:{leave % 60:02d}</b></span>'
                f'<span class="muted small">leave the bar within (h:mm) · last train {mins} min away</span></div>'
            )
        short = "Woodley Park" if sname.startswith("Woodley") else sname
        train_cards.append(
            f'<div class="card train"><p class="tag sample-tag">Sample countdown</p>'
            f'<h2>{html.escape(short)} <span class="muted small">· {html.escape(line.title())} line · {d/1000:.1f} km, about {w} min walk</span></h2>'
            + "".join(rows)
            + f'<p class="small">Real last-train times change with Metro\'s service plan: '
            f'<a href="{STATION_PAGES[sname]}">check tonight\'s first and last trains for {html.escape(short)} on wmata.com</a>.</p></div>'
        )

    def bike_table(rows: list[dict], show_bikes: bool) -> str:
        head = "<tr><th>Dock</th><th class=n>Walk</th>" + ("<th class=n>Bikes</th><th class=n>E-bikes</th>" if show_bikes else "") + "<th class=n>Open docks</th></tr>"
        body = []
        for r in rows:
            if not r["ok"]:
                cells = f'<td colspan="{3 if show_bikes else 1}" class="muted">Not renting right now</td>'
            else:
                cells = (f'<td class="n">{r["classic"]}</td><td class="n">{r["ebikes"]}</td>' if show_bikes else "") + f'<td class="n">{r["docks"]}</td>'
            body.append(f'<tr><td>{html.escape(r["name"])}</td><td class="n">{r["walk"]} min</td>{cells}</tr>')
        return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'

    dest_html = "".join(
        f'<h3>Near {html.escape(n.replace("-", "–"))} Metro</h3>' + (bike_table(rows, False) if rows else '<p class="muted">No dock within 450 m.</p>')
        for n, rows in dest_rows
    )

    sample_buses = [("[Route]", "toward Columbia Heights & Petworth", [6, 27]), ("[Route]", "toward Dupont Circle & downtown", [11, 41]), ("[Route]", "toward Woodley Park & upper Northwest", [19, 49])]
    bus_rows = "".join(
        f'<tr><td><span class="route">{r}</span></td><td>{html.escape(dest)}</td><td class="n"><b>{a[0]}</b> min</td><td class="n">{a[1]} min</td></tr>'
        for r, dest, a in sample_buses
    )

    body = f"""
  <div class="toolbar"><button type="button" id="themeBtn" class="pill">Night mode</button><span class="muted small" id="clock"></span></div>

  <section class="grid2">{''.join(train_cards)}</section>

  <section class="card">
    <p class="tag live-tag">Live · Capital Bikeshare · snapshot {snap_utc}</p>
    <h2>Bikes within a 7-minute walk of {ANCHOR_NAME}</h2>
    <div class="grid">
      <div class="stat"><b>{total_classic}</b>classic bikes</div>
      <div class="stat"><b>{total_e}</b>e-bikes</div>
      <div class="stat"><b>{len(near)}</b>docks nearby</div>
    </div>
    {bike_table(near, True)}
    <p class="small muted">Walk times are estimates from straight-line distance plus 30% for the street grid, at about 3 mph.</p>
  </section>

  <section class="card">
    <p class="tag live-tag">Live · same snapshot</p>
    <h2>Will there be a dock where you're going?</h2>
    {dest_html}
  </section>

  <section class="card">
    <p class="tag sample-tag">Sample arrivals · route names withheld</p>
    <h2>Late-night buses from 18th &amp; Columbia</h2>
    <div class="scroll"><table><tr><th>Route</th><th>Heading</th><th class=n>Next</th><th class=n>Then</th></tr>{bus_rows}</table></div>
    <p class="small muted">Metrobus routes were renamed in the 2025 Better Bus network redesign, so this demo shows "[Route]" instead of guessing names.
    The real board fills these rows from WMATA's bus GTFS static schedule plus its real-time trip-updates feed.</p>
  </section>

  <section class="grid2">
    <div class="card">
      <h2>Share my ETA</h2>
      <p>Send a friend a link that says which ride you picked and when you should be home.</p>
      <button type="button" class="pill" disabled>Share link (demo)</button>
      <p class="small muted">Nothing is tracked: the link carries only your chosen ride and an arrival estimate.</p>
    </div>
    <div class="card sponsor">
      <p class="label">Table tent · bars that opt in</p>
      <p><b>Scan for your last ride home.</b> One QR code on the table opens this board, already pointed at the nearest stations.</p>
      <p class="small">This board brought to you by <b>[Sponsor bar name]</b>. One clearly labeled sponsor at a time.</p>
    </div>
  </section>
"""

    extra_css = """
.toolbar{display:flex;gap:12px;align-items:center;margin:6px 0}
.pill{font:inherit;font-size:.85rem;padding:5px 12px;border-radius:999px;border:1px solid var(--accent);background:var(--card);color:var(--accent);cursor:pointer}
.pill[disabled]{opacity:.6;cursor:not-allowed}
.small{font-size:.85rem}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:0 14px}
.train h2{font-size:1.25rem}
.dir{display:grid;grid-template-columns:1fr auto;gap:0 10px;border-top:1px solid var(--line);padding:10px 0}
.dir .muted{grid-column:1/-1}
.dlabel{font-weight:600}
.count b{font-size:2.4rem;line-height:1;font-variant-numeric:tabular-nums;color:var(--brick)}
.tag{display:inline-block;margin:0 0 8px;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:6px;border:1px solid currentColor}
.sample-tag{color:var(--sample)}.live-tag{color:var(--live)}
.route{display:inline-block;padding:1px 7px;border-radius:5px;background:var(--soft);font-weight:700;font-size:.85rem}
h3{font-size:.95rem;margin:14px 0 4px}
"""
    script = """
<script>
(function(){
  var root=document.documentElement, btn=document.getElementById('themeBtn');
  var h=new Date().getHours();
  if(h>=22||h<5){root.setAttribute('data-theme','dark');}
  function label(){btn.textContent=root.getAttribute('data-theme')==='dark'?'Day mode':'Night mode';}
  btn.addEventListener('click',function(){root.setAttribute('data-theme',root.getAttribute('data-theme')==='dark'?'light':'dark');label();});
  label();
  document.getElementById('clock').textContent='Board switches to night mode after 10 pm. Sample countdowns tick down from page load.';
  var t0=Date.now();
  var els=[].slice.call(document.querySelectorAll('.count'));
  function tick(){var m=Math.floor((Date.now()-t0)/60000);els.forEach(function(e){var v=Math.max(0,+e.dataset.min-m);e.querySelector('b').textContent=Math.floor(v/60)+':'+String(v%60).padStart(2,'0');});}
  setInterval(tick,15000);
})();
</script>"""

    wp = metro["Woodley Park-Zoo/Adams Morgan"]
    ch = metro["Columbia Heights"]
    d_wp, d_ch = meters(ANCHOR, wp[:2]), meters(ANCHOR, ch[:2])
    values = {
        "IDEA_ID": IDEA_ID, "RANK": str(RANK), "SCORE": SCORE,
        "SHORT_NAME": "Last Ride Home",
        "EXTRA_CSS": extra_css,
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative (bike docks live)",
        "EYEBROW": "Adams Morgan · 18th St &amp; Columbia Rd NW",
        "HEADLINE": "Can you still catch a train home?",
        "DECK": "Last trains from the two nearest stations with your walk time already subtracted, the next late buses, and bikes and docks around 18th Street right now.",
        "BODY": body + script,
        "PITCH": "A late-night board for Adams Morgan bar-goers, restaurant staff and visitors that answers one question: can I still make the train, and if not, which bus or bike? Bars that opt in put a QR code on the table.",
        "WHATS_REAL": (
            f"Every bike, e-bike and open-dock count comes from Capital Bikeshare's public GBFS feed, pulled {today} (snapshot {snap_utc}). "
            f"Station locations come from DC GIS's Metro Stations layer, so the walk times are real estimates: Woodley Park is {d_wp/1000:.2f} km and Columbia Heights {d_ch/1000:.2f} km from 18th &amp; Columbia as the crow flies."
        ),
        "WHATS_MOCKED": (
            "The train countdowns and bus arrivals are sample values. We have no WMATA API key, and Metro's late-night closing times change, so this page states no real closing times; "
            "it links to each station's first-and-last-train page instead. Bus route names are placeholders because the 2025 Better Bus redesign renamed routes. "
            "The share link and the sponsor are mockups."
        ),
        "NEXT_STEPS": (
            "Register a free WMATA developer key. A Cloudflare Worker on a 30-60 second cron calls Rail Predictions for the two stations and bus GTFS-RT trip updates, merges GTFS static for last-trip times, "
            "and caches one JSON blob in KV that every visitor reads (WMATA's terms forbid one key per user and re-exposing the data as an API). GBFS is polled the same way. "
            "Refresh bus GTFS weekly with a GitHub Action so route renames flow through. Then print table tents for two or three bars."
        ),
        "SOURCES": (
            '<a href="https://gbfs.capitalbikeshare.com/gbfs/gbfs.json">Capital Bikeshare GBFS</a>, '
            f'<a href="{STATIONS_LAYER}">DC GIS Metro Stations</a>, '
            '<a href="https://www.wmata.com/ridertools/station/woodley-park">WMATA station pages</a>; '
            "not affiliated with WMATA or Capital Bikeshare"
        ),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", now),
    }
    OUT.write_text(fill(values), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(near)} docks near anchor, {total_classic} bikes, {total_e} e-bikes")


if __name__ == "__main__":
    main()
