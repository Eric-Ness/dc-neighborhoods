"""Demo #26: Step-Free Status, elevator outage pages and alerts. Idea transit-tech#2.

Live this run: Metro station locations from DC GIS (Open Data DC) and the Adams Morgan boundary,
used to pick the nearer station for Adams Morgan and the "plan B" nearest station for each.
Sample: every elevator status, outage and uptime figure, because the WMATA ElevatorIncidents API needs a key.

Run from the repo root: python demos/ideas/src/26_step_free_status.py
"""

from __future__ import annotations

import hashlib
import html
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

RANK, IDEA_ID, SCORE = 26, "transit-tech#2", "66.1"
OUT = ROOT / "demos" / "ideas" / "26-step-free-status.html"
STATIONS_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_Rail_Bus_WebMercator/MapServer/51"
HOODS_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
ANCHOR_18TH = (38.9219, -77.0424)  # approx. 18th St & Columbia Rd NW
WP, CH = "Woodley Park-Zoo/Adams Morgan", "Columbia Heights"
# (neighborhood, station NAME in DC GIS, sample status: None = all working, else (elevator, days out, est. days left))
STATIONS = [
    ("Petworth", "Georgia Ave-Petworth", None),
    ("Tenleytown", "Tenleytown-AU", ("Street elevator", 4, 3)),
    ("Friendship Heights", "Friendship Heights", None),
    ("Adams Morgan", WP, None),
    ("Adams Morgan", CH, None),
    ("L'Enfant Plaza", "L'Enfant Plaza", ("A platform elevator", 1, 1)),
]
DAYS = 90


def meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat = math.radians((a[0] + b[0]) / 2)
    return math.hypot((a[0] - b[0]) * 111_320, (a[1] - b[1]) * 111_320 * math.cos(lat))


def centroid(ring: list) -> tuple[float, float]:
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    a *= 0.5
    return (cy / (6 * a), cx / (6 * a))


def fill(values: dict[str, str]) -> str:
    page = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    page = page.split("<!--", 1)[0] + page.split("-->", 1)[1]
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    assert "{{" not in page, "unfilled placeholder"
    return page


def sample_uptime(name: str, out_days: int) -> list[float]:
    """Made-up daily uptime share for the last DAYS days (oldest first). Seeded by name; NOT real."""
    h = hashlib.sha256(name.encode()).digest()
    days = []
    for i in range(DAYS):
        b = h[i % 32] ^ h[(i * 7) % 32]
        v = 1.0
        if b < 18:
            v = 0.35 + (b / 18) * 0.5
        elif b < 30:
            v = 0.9
        days.append(v)
    for i in range(out_days):
        days[DAYS - 1 - i] = 0.5 if i == out_days - 1 else 0.0
    return days


def uptime_svg(days: list[float]) -> str:
    w, gap, H = 4, 1, 34
    bars = []
    for i, v in enumerate(days):
        x = i * (w + gap)
        cls = "ok" if v >= 0.99 else ("part" if v >= 0.5 else "bad")
        hh = max(3, round(H * max(v, 0.1)))
        bars.append(f'<rect class="{cls}" x="{x}" y="{H - hh}" width="{w}" height="{hh}" rx="1"><title>{DAYS - i} days ago: {round(v * 24)} of 24 h working (sample)</title></rect>')
    W = DAYS * (w + gap)
    return f'<svg class="up" viewBox="0 0 {W} {H + 14}" preserveAspectRatio="none" role="img" aria-label="90-day elevator uptime, sample">{"".join(bars)}<text x="0" y="{H + 12}">90 days ago</text><text x="{W}" y="{H + 12}" text-anchor="end">today</text></svg>'


def main() -> None:
    now = time.gmtime()
    today = time.strftime("%Y-%m-%d", now)
    q = dcdata._request(f"{STATIONS_LAYER}/query", {"where": "1=1", "outFields": "NAME,LINE", "returnGeometry": "true", "outSR": 4326, "f": "json"})
    allst = {f["attributes"]["NAME"]: (f["geometry"]["y"], f["geometry"]["x"], f["attributes"]["LINE"] or "") for f in q["features"]}
    for _, n, _ in STATIONS:
        if n not in allst:
            raise RuntimeError(f"station {n!r} not in DC GIS layer")

    am_ring = max(dcdata.boundary(HOODS_LAYER, "DC_HPN_NAME='ADAMS MORGAN'")["rings"], key=len)
    am_c = centroid(am_ring)
    d = {n: (meters(am_c, allst[n][:2]), meters(ANCHOR_18TH, allst[n][:2])) for n in (WP, CH)}
    nearer_c = WP if d[WP][0] < d[CH][0] else CH
    nearer_a = WP if d[WP][1] < d[CH][1] else CH

    def short(n: str) -> str:
        return "Woodley Park" if n == WP else n.replace("-", "–")

    def plan_b(n: str) -> tuple[str, float]:
        here = allst[n][:2]
        best = min((meters(here, v[:2]), k) for k, v in allst.items() if k != n and meters(here, v[:2]) > 50)
        return best[1], best[0]

    weekday = lambda days_ago: time.strftime("%a", time.gmtime(time.time() - days_ago * 86400))  # noqa: E731
    cards, working, out = [], 0, 0
    for hood, n, st in STATIONS:
        days = sample_uptime(n, st[1] if st else 0)
        pct90 = sum(days) / len(days) * 100
        line = allst[n][2].replace(",", " ·").title()
        if st is None:
            working += 1
            status = '<p class="status ok"><span class="dot"></span>All elevators working</p>'
            plan = ""
        else:
            out += 1
            alt, alt_m = plan_b(n)
            status = f'<p class="status bad"><span class="dot"></span>{st[0]} out since {weekday(st[1])}</p><p class="small">Estimated back in about {st[2]} day{"s" if st[2] > 1 else ""}.</p>'
            plan = (
                f'<div class="planb"><b>Plan B:</b> nearest other station is <b>{html.escape(short(alt))}</b>, {alt_m / 1000:.1f} km away (check its status first). '
                "When Metro runs a shuttle for an elevator outage, the shuttle stop would be listed here.</div>"
            )
        note = ""
        if n in (WP, CH):
            note = '<p class="small muted">' + ("Nearer to the 18th St bars." if n == nearer_a else "Farther from 18th St, but on a different line.") + "</p>"
        cards.append(
            f'<article class="card st"><p class="tag sample-tag">Sample status</p>'
            f'<p class="eyebrow">{html.escape(hood)}</p><h2>{html.escape(short(n))} <span class="muted small">· {html.escape(line)}</span></h2>'
            f"{status}{plan}{note}"
            f'<p class="small muted">Last 90 days: <b>{pct90:.1f}%</b> uptime (sample)</p>{uptime_svg(days)}</article>'
        )

    am_text = (
        f"For Adams Morgan, {short(nearer_a)} is nearer to 18th St &amp; Columbia Rd "
        f"({d[nearer_a][1] / 1000:.2f} km vs {d[CH if nearer_a == WP else WP][1] / 1000:.2f} km, straight line)"
        + (f", and also nearer to the middle of the neighborhood ({d[nearer_c][0] / 1000:.2f} km vs {d[CH if nearer_c == WP else WP][0] / 1000:.2f} km)." if nearer_c == nearer_a
           else f". From the middle of the neighborhood, {short(nearer_c)} is nearer ({d[nearer_c][0] / 1000:.2f} km vs {d[CH if nearer_c == WP else WP][0] / 1000:.2f} km).")
        + " The page shows both, because they are on different lines."
    )

    body = f"""
  <section class="card summary">
    <p class="tag sample-tag">Sample status · updated every 5 minutes when live</p>
    <div class="grid">
      <div class="stat"><b>{working}</b>stations fully step-free right now</div>
      <div class="stat"><b>{out}</b>with an elevator out</div>
      <div class="stat"><b>{len(STATIONS)}</b>stations watched for five neighborhoods</div>
    </div>
    <p class="small">{am_text}</p>
  </section>

  <section class="cards">{''.join(cards)}</section>

  <section class="card">
    <h2>Get an alert when your elevator goes out</h2>
    <p>Pick your station once. We'll tell you when an elevator goes out and when it comes back.</p>
    <div class="alerts">
      <div><b>Push, free</b><br><span class="small muted">Subscribe in the ntfy app to topic <code>[neighborhood]-elevators</code>. No account, no phone number.</span></div>
      <div><b>Email</b><br><span class="small muted">One message per change, or a morning digest.</span>
        <form onsubmit="return false" class="mock"><input type="email" placeholder="you@example.com" aria-label="Email (demo, does nothing)" disabled> <button type="button" class="pill" disabled>Subscribe (demo)</button></form></div>
    </div>
    <p class="small muted">No text messages: SMS needs paid carrier registration. WMATA also runs its own ELstat alerts; see <a href="https://www.wmata.com/ride/elevators-escalators.html">wmata.com elevators and escalators</a>.</p>
  </section>

  <section class="card">
    <h2>Why not just use elevatoruptime.com?</h2>
    <p><a href="https://www.elevatoruptime.com/">Elevator Uptime</a> already publishes per-station elevator status and uptime history for Metro, with 30- and 90-day figures. It's good, and you should know about it. This version is different in where it lives and what it tells you to do next:</p>
    <div class="scroll"><table>
      <tr><th></th><th>elevatoruptime.com</th><th>This widget</th></tr>
      <tr><td>Where</td><td>Its own site, every station</td><td>On your neighborhood's home page, only your stations</td></tr>
      <tr><td>Out of service?</td><td>Status and history</td><td>Status plus a plan B: nearest other station and any shuttle</td></tr>
      <tr><td>Alerts</td><td>Not the focus</td><td>Free push or email for the stations you pick</td></tr>
      <tr><td>Adams Morgan</td><td>Two separate stations</td><td>Both shown together, with which is nearer to 18th St</td></tr>
    </table></div>
  </section>

  <section class="card">
    <h2>For other sites: embed it</h2>
    <pre><code>&lt;div data-step-free="petworth"&gt;&lt;/div&gt;
&lt;script src="https://[your-site]/step-free.js" defer&gt;&lt;/script&gt;</code></pre>
    <p class="small muted">Shown as text only. A one-line widget for ANC, library and church sites, served from the same cache.</p>
  </section>
"""

    extra_css = """
.small{font-size:.85rem}
.tag{display:inline-block;margin:0 0 6px;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:6px;border:1px solid currentColor}
.sample-tag{color:var(--sample)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 14px}
.st h2{font-size:1.1rem;margin:.1rem 0 .4rem}
.status{font-weight:700;margin:.3rem 0;display:flex;align-items:center;gap:8px}
.status .dot{width:12px;height:12px;border-radius:50%;flex:none}
.status.ok{color:var(--down)}.status.ok .dot{background:var(--down)}
.status.bad{color:var(--up)}.status.bad .dot{background:var(--up)}
.planb{background:var(--soft);border-left:3px solid var(--brick);padding:8px 10px;border-radius:6px;font-size:.9rem;margin:8px 0}
svg.up{width:100%;height:52px;display:block}
svg.up rect.ok{fill:var(--down)}svg.up rect.part{fill:var(--gold)}svg.up rect.bad{fill:var(--up)}
.alerts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:8px 0}
.mock{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.mock input{font:inherit;padding:4px 8px;border:1px solid var(--line);border-radius:6px;min-width:0;flex:1 1 150px;background:var(--card);color:var(--ink)}
.pill{font:inherit;font-size:.85rem;padding:5px 12px;border-radius:999px;border:1px solid var(--accent);background:var(--card);color:var(--accent)}
.pill[disabled]{opacity:.6}
pre{background:var(--soft);padding:10px;border-radius:6px;overflow-x:auto;font-size:.82rem;white-space:pre-wrap;word-break:break-all}
"""

    values = {
        "IDEA_ID": IDEA_ID, "RANK": str(RANK), "SCORE": SCORE,
        "SHORT_NAME": "Step-Free Status",
        "EXTRA_CSS": extra_css,
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": "Step-Free Status · Metro elevators",
        "HEADLINE": "Is the elevator working at your station?",
        "DECK": "Elevator status for the Metro stations that serve Petworth, Tenleytown, Friendship Heights, Adams Morgan and L'Enfant Plaza, with a plan B when one is out and free alerts.",
        "BODY": body,
        "PITCH": "A small status block on each neighborhood site for wheelchair users, parents with strollers, travelers with luggage and older residents: is the elevator working, since when has it been out, and where to go instead. Free push or email alerts, 90-day history.",
        "WHATS_REAL": (
            f"Station locations and lines come from DC GIS's Metro Stations layer, pulled {today}. From them the page computes each plan-B station (nearest other station) "
            f"and which station is nearer to Adams Morgan, using the neighborhood boundary from DC GIS. elevatoruptime.com was confirmed to exist and publish per-station uptime by a web search on {today}."
        ),
        "WHATS_MOCKED": (
            "Every elevator status, outage, estimated return, and uptime figure is sample data, including the two outages shown (Tenleytown–AU and L'Enfant Plaza). "
            "They are not real outages. Live status needs a WMATA API key we don't have. The alert sign-up, ntfy topic and embed snippet are mockups."
        ),
        "NEXT_STEPS": (
            "Register a WMATA developer key. A Cloudflare Worker calls the ElevatorIncidents endpoint (Incidents.svc/json/ElevatorIncidents) every 5 minutes, filters to these six stations by station code, "
            "and writes each change to D1. That table is the outage history, so the 90-day chart builds itself, and each new or cleared outage posts to the station's ntfy topic and email list. "
            "Serve every visitor from the cached JSON, as WMATA's terms require."
        ),
        "SOURCES": (
            f'<a href="{STATIONS_LAYER}">DC GIS Metro Stations</a>, '
            f'<a href="{HOODS_LAYER}">DC GIS neighborhood boundaries</a>, '
            '<a href="https://www.wmata.com/ride/elevators-escalators.html">WMATA elevators and escalators</a>, '
            '<a href="https://www.elevatoruptime.com/">elevatoruptime.com</a>; not affiliated with WMATA'
        ),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", now),
    }
    OUT.write_text(fill(values), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: nearer to 18th&Columbia = {nearer_a} {d}, centroid-nearer = {nearer_c}")


if __name__ == "__main__":
    main()
