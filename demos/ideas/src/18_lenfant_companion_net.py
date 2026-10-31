"""Demo #18: L'Enfant Plaza Transfer Companion, the commercial .net page (monetization#6).

Writes demos/ideas/18-lenfant-companion-net.html.
Live: Capital Bikeshare GBFS docks near the station (keyless).
Sample: arrival boards and elevator/escalator status (no WMATA key), "food open now" (placeholder names).
Affiliate: hotel and tour boxes are labeled "[Affiliate placement]" with no real hotel or tour names.
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

OUT = ROOT / "demos" / "ideas" / "18-lenfant-companion-net.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

GBFS = "https://gbfs.capitalbikeshare.com/gbfs/gbfs.json"
STATION = (38.8849, -77.0219)
WMATA_INFO = "https://www.wmata.com/ridertools/station/l'enfant-plaza/info"
WMATA_TERMS = "https://developer.wmata.com/license"
STAY22 = "https://stay22.com/faq"

e = html.escape

LINES = {"G": ("#00a650", "#fff"), "Y": ("#ffd200", "#111"), "O": ("#f7931d", "#111"),
         "B": ("#0076c0", "#fff"), "S": ("#a1a3a1", "#111")}

# Sample boards. Platform names follow WMATA's station page; destinations are the lines' terminals.
BOARDS = [
    ("Upper level · platform to Branch Ave/Huntington", [("G", "Branch Ave", 2), ("Y", "Huntington", 6), ("G", "Branch Ave", 10)]),
    ("Upper level · platform to Greenbelt/Mt Vernon Sq", [("Y", "Mt Vernon Sq", 1), ("G", "Greenbelt", 4), ("G", "Greenbelt", 12)]),
    ("Lower level · westbound side", [("S", "Ashburn", 3), ("O", "Vienna", 5), ("B", "Franconia-Spfld", 9)]),
    ("Lower level · eastbound side", [("O", "New Carrollton", 2), ("S", "Downtown Largo", 7), ("B", "Downtown Largo", 11)]),
]

DESTS = [
    ("National Air and Space Museum", (38.8882, -77.0199), "Museums"),
    ("International Spy Museum", (38.8840, -77.0254), "Museums"),
    ("Hirshhorn Museum", (38.8881, -77.0230), "Museums"),
    ("U.S. Holocaust Memorial Museum", (38.8867, -77.0326), "Museums"),
    ("The Wharf", (38.8786, -77.0233), "Waterfront"),
    ("Washington Monument", (38.8895, -77.0353), "Monuments"),
    ("U.S. Capitol", (38.8899, -77.0091), "Monuments"),
    ("Nationals Park", (38.8730, -77.0074), "Games"),
]


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": dcdata.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def meters(a, b) -> float:
    p = math.radians
    h = math.sin(p(b[0] - a[0]) / 2) ** 2 + math.cos(p(a[0])) * math.cos(p(b[0])) * math.sin(p(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def walk_min(m: float) -> int:
    return max(1, round(m * 1.3 / 80))


def eastern(now_utc: dt.datetime) -> dt.datetime:
    y = now_utc.year
    mar = dt.datetime(y, 3, 8 + (6 - dt.date(y, 3, 8).weekday()) % 7, 7, tzinfo=dt.timezone.utc)
    nov = dt.datetime(y, 11, 1 + (6 - dt.date(y, 11, 1).weekday()) % 7, 6, tzinfo=dt.timezone.utc)
    return (now_utc + dt.timedelta(hours=-4 if mar <= now_utc < nov else -5)).replace(tzinfo=None)


def nearest_docks(n: int = 3):
    feeds = {f["name"]: f["url"] for f in get_json(GBFS)["data"]["en"]["feeds"]}
    info = get_json(feeds["station_information"])["data"]["stations"]
    status = {s["station_id"]: s for s in get_json(feeds["station_status"])["data"]["stations"]}
    rows = []
    for s in info:
        d = meters(STATION, (s["lat"], s["lon"]))
        st = status.get(s["station_id"])
        if st and d <= 700:
            rows.append({"name": s["name"], "m": round(d), "bikes": st.get("num_bikes_available", 0),
                         "docks": st.get("num_docks_available", 0)})
    rows.sort(key=lambda r: r["m"])
    return rows[:n], feeds["station_status"]


def mini_map() -> str:
    """Schematic 'Stay nearby' map: the station plus three unnamed affiliate pins. Not to scale."""
    pins = [(70, 60, "A"), (250, 48, "B"), (200, 140, "C")]
    p = "".join(
        f'<g><circle cx="{x}" cy="{y}" r="13" class="pin"/><text x="{x}" y="{y + 4}" text-anchor="middle" class="pin-t">{t}</text></g>'
        for x, y, t in pins
    )
    return (
        '<svg viewBox="0 0 320 180" role="img" aria-label="Schematic map with the station and three placeholder hotel pins" class="map">'
        '<rect width="320" height="180" rx="8" class="map-bg"/>'
        '<path d="M0 120 L320 95" class="road"/><path d="M150 0 L165 180" class="road"/><path d="M0 30 L320 20" class="road"/>'
        '<text x="8" y="16">Mall ↑</text><text x="8" y="172">Wharf ↓</text>'
        '<rect x="148" y="98" width="26" height="18" rx="4" class="stn"/><text x="161" y="111" text-anchor="middle" class="stn-t">M</text>'
        f'{p}</svg>'
    )


def build() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    local = eastern(now)
    docks, gbfs_status = nearest_docks()

    boards = []
    for title, rows in BOARDS:
        trs = "".join(
            f'<tr><td><span class="ln" style="background:{LINES[c][0]};color:{LINES[c][1]}">{c}</span></td>'
            f'<td>{e(dest)}</td><td class="n">8</td><td class="n mm">{"ARR" if m <= 1 else m}</td></tr>'
            for c, dest, m in rows
        )
        boards.append(f'<div class="bd"><div class="bd-h">{e(title)}</div><table><thead><tr><th>Ln</th><th>Dest</th>'
                      f'<th class="n">Car</th><th class="n">Min</th></tr></thead><tbody>{trs}</tbody></table></div>')

    walk_cells = "".join(
        f'<div class="wk"><b>~{walk_min(meters(STATION, pt))}</b><span>min</span><div>{e(n)}</div><small>{e(cat)}</small></div>'
        for n, pt, cat in sorted(DESTS, key=lambda d: meters(STATION, d[1]))
    )

    dock_html = "".join(f'<li><b>{d["bikes"]}</b> bikes · {d["docks"]} docks — {e(d["name"])}</li>' for d in docks) or "<li>No docks within 700 m.</li>"

    body = f"""
<div class="strip" role="status">
  <span class="pill bad">1 escalator out</span><span class="pill ok">4/4 elevators</span>
  <span class="muted small">Sample status · updated every minute once live</span>
</div>

<div class="boards">
  <div class="boards-h"><h2>Next trains</h2><span class="badge sample">sample arrivals</span></div>
  <div class="bgrid">{"".join(boards)}</div>
  <p class="small muted">Boards are sample data. Live version: WMATA Rail Predictions for L'Enfant's upper and lower levels, polled once by our server
  and cached so every visitor shares one call (<a href="{WMATA_TERMS}">WMATA data terms</a>).</p>
</div>

<div class="card">
  <h2>Walk from the station</h2>
  <div class="wgrid">{walk_cells}</div>
  <p class="small muted">Estimated from map distance. Which street exit to use is coming after our on-site walk: [Exit for each place — verify on site].</p>
</div>

<div class="card aff">
  <div class="aff-l">[Affiliate placement] · Stay nearby</div>
  <div class="stay">
    {mini_map()}
    <ul class="hotels">
      <li><b>A</b> [Hotel name] · [distance] · from $[rate]/night <span class="cta">[Check dates]</span></li>
      <li><b>B</b> [Hotel name] · [distance] · from $[rate]/night <span class="cta">[Check dates]</span></li>
      <li><b>C</b> [Hotel name] · [distance] · from $[rate]/night <span class="cta">[Check dates]</span></li>
    </ul>
  </div>
  <p class="small muted">A hotel-map widget (for example <a href="{STAY22}">Stay22</a>) fills this box with real listings and pays a share of booking commission.</p>
</div>

<div class="card aff">
  <div class="aff-l">[Affiliate placement] · Tours &amp; tickets</div>
  <div class="tours">
    <div class="tour"><b>[Tour partner] Monuments at night</b><span>[time slots] · $[price]</span><span class="cta">[See times]</span></div>
    <div class="tour"><b>[Tour partner] Mall walking tour</b><span>[time slots] · $[price]</span><span class="cta">[See times]</span></div>
    <div class="tour"><b>[Ticket partner] Museum or game tickets</b><span>[date] · $[price]</span><span class="cta">[See times]</span></div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>Food open now <span class="badge sample">sample</span></h2>
    <ul class="food"><li>Sample Café · coffee, pastries · [hours]</li><li>Sample Deli · sandwiches · [hours]</li><li>Sample Noodle Bar · [hours]</li></ul>
  </div>
  <div class="card">
    <h2>Grab a bike <span class="badge live">live</span></h2>
    <ul class="food">{dock_html}</ul>
    <p class="small muted">Capital Bikeshare, {local:%I:%M %p} DC time at build.</p>
  </div>
</div>

<div class="ad">[Ad slot · 300×250 display]</div>
<p class="small muted disclose">Disclosure: lenfantplaza.net earns commission on some hotel and tour bookings. It does not change what the train boards show.</p>
"""

    extra_css = """
.strip{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;margin:10px 0}
.pill{font-size:.8rem;font-weight:700;padding:3px 10px;border-radius:999px;color:#fff}
.pill.bad{background:#a33a2c}.pill.ok{background:#2c6e49}
.small{font-size:.86rem}
.boards{background:#0f1412;color:#e6ebe7;border-radius:12px;padding:14px;margin:12px 0}
.boards a{color:#7dc3ac}.boards .muted{color:#9ba7a1}
.boards-h{display:flex;justify-content:space-between;align-items:center;gap:8px}.boards-h h2{margin:0}
.boards .badge.sample{color:#d8b25c}
.bgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px;margin-top:10px}
.bd{background:#000;border-radius:8px;padding:8px 10px;font-family:ui-monospace,Consolas,monospace}
.bd-h{font-size:.72rem;color:#9ba7a1;margin-bottom:4px}
.bd table{font-size:.95rem}.bd th{color:#6f7a74;border-color:#222}.bd td{border-color:#222;color:#f5c542;padding:.3rem .35rem}
.bd .mm{font-weight:700}
.ln{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;font-weight:700;font-size:.72rem;font-family:system-ui,sans-serif}
.wgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.wk{background:var(--soft);border-radius:8px;padding:8px 10px}
.wk b{font-size:1.5rem}.wk span{margin-left:3px;color:var(--muted);font-size:.8rem}.wk div{font-weight:600;font-size:.88rem;line-height:1.25}.wk small{color:var(--muted)}
.aff{border:2px dashed var(--gold);background:var(--soft)}
.aff-l{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;color:var(--gold);margin-bottom:8px}
.stay{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;align-items:start}
.map{width:100%;height:auto}.map-bg{fill:var(--card);stroke:var(--line)}.road{stroke:var(--line);stroke-width:6;fill:none}
.pin{fill:var(--gold)}.map text.pin-t{fill:#fff;font-weight:700}.stn{fill:var(--accent)}.map text.stn-t{fill:var(--card);font-weight:700}
.hotels{list-style:none;padding:0;margin:0}.hotels li{padding:7px 0;border-bottom:1px solid var(--line);font-size:.92rem}
.cta{display:inline-block;margin-left:4px;font-size:.78rem;font-weight:700;color:var(--accent);border:1px solid var(--accent);border-radius:999px;padding:1px 8px}
.tours{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px}
.tour{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;display:flex;flex-direction:column;gap:4px;font-size:.9rem}
.food{list-style:none;padding:0;margin:0}.food li{padding:5px 0;border-bottom:1px solid var(--line);font-size:.92rem}
.ad{border:1px dashed var(--line);color:var(--muted);text-align:center;padding:40px 10px;border-radius:8px;margin:14px auto;max-width:300px;font-size:.85rem}
.disclose{text-align:center}
"""

    repl = {
        "IDEA_ID": "monetization#6", "RANK": "18", "SCORE": "69.1",
        "SHORT_NAME": "L'Enfant Plaza Companion",
        "PROVENANCE_CLASS": "sample", "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": "lenfantplaza.net",
        "HEADLINE": "L'Enfant Plaza, right now",
        "DECK": "Trains on all four platforms, what's broken, how far everything is, and where to stay and what to book while you're here.",
        "BODY": body, "EXTRA_CSS": extra_css,
        "PITCH": "The commercial companion on lenfantplaza.net: a fast mobile page with arrival boards by platform, an outage strip, a walking-time grid, food open now, and paid hotel-map and tour placements for the tourists and conference-goers passing through. The ad-free how-to-transfer guide lives on the .org.",
        "WHATS_REAL": (
            "Capital Bikeshare dock counts near the station were pulled live from the public GBFS feed at build time. Platform names "
            "(upper-level platforms to Branch Ave/Huntington and Greenbelt/Mt Vernon Sq; lower-level Blue/Orange/Silver) and the four-elevator count "
            "follow WMATA's station page. Walk times are map-distance estimates."
        ),
        "WHATS_MOCKED": (
            "Arrival boards, car counts and the outage strip are sample data (no WMATA key). Every hotel, tour, ticket and ad box is an "
            "unfilled [Affiliate placement] with no real business named. Food spots use placeholder names (\"Sample Café\"). Exit-per-destination is unverified."
        ),
        "NEXT_STEPS": (
            "Register a WMATA key and serve predictions and ElevatorIncidents from one cached Worker; confirm WMATA's terms allow display on an ad-supported page "
            "and add the required non-endorsement line. Apply to Stay22 and a tour affiliate (GetYourGuide or Viator) and drop their widgets into the marked boxes. "
            "Pull food hours from a places source with a commercial license, or sell those slots to local spots. Walk the station to fill the exit-per-destination column."
        ),
        "SOURCES": (
            f'<a href="{WMATA_INFO}">WMATA station page</a>, <a href="{WMATA_TERMS}">WMATA data terms</a>, '
            f'<a href="{STAY22}">Stay22 FAQ</a>, <a href="{gbfs_status}">Capital Bikeshare GBFS</a> (live)'
        ),
        "GENERATED_UTC": now.strftime("%Y-%m-%d %H:%M UTC"),
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    page = re.sub(r"<!--.*?-->\s*", "", page, count=1, flags=re.S)
    for k, v in repl.items():
        page = page.replace("{{" + k + "}}", v)
    page = page.replace("any ANC, BID or property owner.", "any ANC, BID or property owner. Not affiliated with or endorsed by WMATA.")
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page) // 1024} KB, {len(docks)} docks)")


if __name__ == "__main__":
    build()
