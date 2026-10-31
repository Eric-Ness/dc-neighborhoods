"""Demo #30: Bus Report Card, reliability grades for neighborhood bus lines. Idea transit-tech#8.

Everything graded here is sample data: real grades need weeks of WMATA bus GTFS-RT snapshots and a key.
The only network call checks DC GIS's archived bus-stop layer, to show (live) why this demo does not
print route names: that layer was retired when the 2025 Better Bus network renamed routes and stops.

Run from the repo root: python demos/ideas/src/30_bus_report_card.py
"""

from __future__ import annotations

import hashlib
import html
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

RANK, IDEA_ID, SCORE = 30, "transit-tech#8", "63.6"
OUT = ROOT / "demos" / "ideas" / "30-bus-report-card.html"
OLD_STOPS = "https://services.arcgis.com/neT9SoYxizqTHZPH/arcgis/rest/services/Metro_Bus_Stops_2023_to_2025/FeatureServer"

# Sample routes, described by corridor only. (corridor, scheduled headway min, on-time %, adherence %, gaps>2x %, bunched %, ghost trips, trips observed)
HOODS = {
    "Petworth": [
        ("Georgia Ave north–south", 8, 71, 78, 9, 14, 41, 4820),
        ("East–west crosstown", 15, 79, 84, 6, 7, 18, 2210),
        ("Local neighborhood loop", 20, 66, 69, 15, 5, 33, 1390),
    ],
    "Adams Morgan": [
        ("Columbia Rd / 18th St", 10, 68, 72, 12, 16, 37, 3950),
        ("Crosstown to Woodley Park", 15, 81, 86, 5, 6, 12, 2140),
        ("Late-night downtown link", 20, 74, 77, 10, 4, 21, 1180),
    ],
    "Tenleytown": [
        ("Wisconsin Ave north–south", 10, 76, 82, 7, 11, 22, 4010),
        ("Nebraska Ave crosstown", 20, 84, 88, 4, 3, 9, 1260),
        ("Connecticut Ave link", 15, 72, 75, 11, 8, 26, 2050),
    ],
    "Friendship Heights": [
        ("Wisconsin Ave north–south", 10, 74, 80, 8, 12, 25, 3870),
        ("DC–Maryland border route", 20, 70, 71, 14, 4, 31, 1210),
        ("Western Ave local", 30, 82, 85, 6, 2, 8, 820),
    ],
}


def grade(adherence: int, gaps: int, ghosts_per_1000: float) -> str:
    score = adherence - gaps - 0.3 * ghosts_per_1000
    for cut, g in ((75, "A"), (65, "B"), (55, "C"), (45, "D")):
        if score >= cut:
            return g
    return "F"


def fill(values: dict[str, str]) -> str:
    page = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    page = page.split("<!--", 1)[0] + page.split("-->", 1)[1]
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    assert "{{" not in page, "unfilled placeholder"
    return page


def headway_svg(sched: int) -> str:
    """Sample: one weekday's observed gaps between buses at one stop, against the schedule."""
    h = hashlib.sha256(b"headways").digest()
    gaps, t = [], 6 * 60
    i = 0
    while t < 21 * 60:
        r = h[i % 32] / 255
        g = sched * (0.25 + r * 1.6) if i % 5 else sched * (2.1 + r)
        gaps.append((t, round(g, 1)))
        t += g
        i += 1
    W, H, L, B = 640, 180, 34, 22
    ymax = max(g for _, g in gaps) * 1.1
    x = lambda m: L + (m - 360) / (900) * (W - L - 6)  # noqa: E731
    y = lambda v: H - B - v / ymax * (H - B - 8)  # noqa: E731
    pts = []
    for m, g in gaps:
        cls = "big" if g > 2 * sched else ("bunch" if g < 0.25 * sched * 1.6 else "dotok")
        pts.append(f'<circle class="{cls}" cx="{x(m):.1f}" cy="{y(g):.1f}" r="3.2"><title>{int(m // 60)}:{int(m % 60):02d}, gap {g:.0f} min</title></circle>')
    grid = "".join(f'<line class="g" x1="{L}" x2="{W - 6}" y1="{y(v):.1f}" y2="{y(v):.1f}"/><text x="{L - 4}" y="{y(v) + 4:.1f}" text-anchor="end">{v}</text>' for v in range(0, int(ymax) + 1, 10))
    ticks = "".join(f'<text x="{x(hh * 60):.1f}" y="{H - 6}" text-anchor="middle">{hh if hh <= 12 else hh - 12}{"a" if hh < 12 else "p"}</text>' for hh in range(6, 22, 3))
    sline = f'<line class="sched" x1="{L}" x2="{W - 6}" y1="{y(sched):.1f}" y2="{y(sched):.1f}"/><line class="sched2" x1="{L}" x2="{W - 6}" y1="{y(2 * sched):.1f}" y2="{y(2 * sched):.1f}"/>'
    return (
        f'<svg viewBox="0 0 {W} {H}" class="hw" role="img" aria-label="Sample: minutes between buses at one stop over a weekday">{grid}{sline}{"".join(pts)}{ticks}'
        f'<text x="{W - 8}" y="{y(sched) - 4:.1f}" text-anchor="end">scheduled {sched} min</text><text x="{W - 8}" y="{y(2 * sched) - 4:.1f}" text-anchor="end">2× schedule</text></svg>'
    )


def trend_svg(vals: list[int]) -> str:
    W, H = 120, 30
    lo, hi = min(vals) - 3, max(vals) + 3
    pts = " ".join(f"{i * (W - 4) / (len(vals) - 1) + 2:.1f},{H - 2 - (v - lo) / (hi - lo) * (H - 4):.1f}" for i, v in enumerate(vals))
    return f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" class="spark" role="img" aria-label="6-month on-time trend, sample"><polyline points="{pts}"/></svg>'


def main() -> None:
    now = time.gmtime()
    today = time.strftime("%Y-%m-%d", now)
    req = urllib.request.Request(f"{OLD_STOPS}?f=json", headers={"User-Agent": dcdata.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        desc = json.load(r).get("serviceDescription", "")
    retired = "retired in June 2025" in desc
    print("archived bus-stop layer says retired June 2025:", retired)

    tabs, panels = [], []
    for k, (hood, routes) in enumerate(HOODS.items()):
        rows = []
        for j, (corr, sched, ontime, adh, gaps, bunch, ghosts, trips) in enumerate(routes):
            g = grade(adh, gaps, ghosts / trips * 1000)
            hsh = hashlib.sha256(f"{hood}{corr}".encode()).digest()
            trend = [ontime + (hsh[m] % 9) - 4 for m in range(5)] + [ontime]
            rows.append(
                f'<tr><td><span class="grade g{g}">{g}</span></td><td><b>Sample route {"ABC"[j]}</b><br><span class="small muted">{html.escape(corr)}</span></td>'
                f'<td class="n">{sched} min</td><td class="n">{ontime}%</td><td class="n">{adh}%</td><td class="n">{gaps}%</td><td class="n">{bunch}%</td>'
                f'<td class="n">{ghosts}</td><td class="n">{trips:,}</td><td>{trend_svg(trend)}</td></tr>'
            )
        tabs.append(f'<button type="button" class="tab{" on" if k == 0 else ""}" data-t="{k}">{html.escape(hood)}</button>')
        worst = min(routes, key=lambda r: r[3])
        summary = (
            f"In October, buses in {html.escape(hood)} ran close to schedule on {sum(r[7] * r[3] for r in routes) // sum(r[7] for r in routes)}% of observed gaps. "
            f"The weakest line was sample route {'ABC'[routes.index(worst)]} ({html.escape(worst[0])}): about 1 in {max(2, round(100 / worst[4]))} waits ran past twice the scheduled gap, "
            f"and {worst[6]} scheduled trips never showed up in the real-time feed."
        )
        panels.append(
            f'<div class="panel" data-p="{k}"{"" if k == 0 else " hidden"}><p class="auto">{summary} <span class="muted small">(auto-written, sample)</span></p>'
            '<div class="scroll"><table><tr><th>Grade</th><th>Line</th><th class=n>Scheduled gap</th><th class=n>On time</th><th class=n>Gaps on schedule</th>'
            f'<th class=n>Gaps over 2×</th><th class=n>Bunched</th><th class=n>Ghost trips</th><th class=n>Trips seen</th><th>6-month on time</th></tr>{"".join(rows)}</table></div></div>'
        )

    body = f"""
  <section class="card">
    <p class="tag sample-tag">Sample report card · October 2026</p>
    <div class="tabs" role="tablist">{''.join(tabs)}</div>
    {''.join(panels)}
    <p class="small muted">Lines are shown by corridor as "Sample route A/B/C". Metrobus routes and stops were renamed in the 2025 Better Bus network redesign
    {"(DC GIS's old bus-stop layer says it was retired in June 2025 for that reason)" if retired else ""}, so this demo names no routes rather than guess.</p>
  </section>

  <section class="card">
    <p class="tag sample-tag">Sample · one stop, one weekday</p>
    <h2>What riders actually waited</h2>
    <p class="small">Each dot is the gap between two buses at one stop on the Georgia Ave corridor. Red dots are waits over twice the schedule; gold dots are buses bunched right behind the one before.</p>
    <div class="scroll">{headway_svg(8)}</div>
  </section>

  <section class="card">
    <h2>How the grades are computed</h2>
    <ol class="method">
      <li><b>Collect.</b> Every 30-60 seconds a cron Worker reads WMATA's bus GTFS-RT trip-updates feed (<code>bus-gtfsrt-tripupdates.pb</code>) and keeps, for each trip and stop, the latest predicted or actual time once the bus has passed. GTFS static gives the schedule.</li>
      <li><b>Headways.</b> For each stop and route, sort observed arrivals and take the gap between consecutive buses. Compare it with the scheduled gap for that time of day.</li>
      <li><b>Gaps on schedule</b> = share of observed gaps no longer than 1.5× the scheduled gap. <b>Gaps over 2×</b> = share longer than twice the schedule (the long waits riders remember). <b>Bunched</b> = share under a quarter of the schedule.</li>
      <li><b>On time</b> = share of timepoint departures within a published window around the schedule (for example 2 minutes early to 7 minutes late). We would state the window on the page and keep it fixed.</li>
      <li><b>Ghost trips</b> = scheduled trips that never appear in the real-time feed that day.</li>
      <li><b>Grade</b> = gaps-on-schedule share, minus the gaps-over-2× share, minus 0.3 per ghost trip per 1,000 trips. A ≥ 75, B ≥ 65, C ≥ 55, D ≥ 45, else F. The formula is published so anyone can argue with it.</li>
    </ol>
    <p class="small muted">Only aggregate monthly statistics are published. WMATA's terms bar re-exposing its raw feed as an API, so there is no raw-data download.</p>
  </section>

  <section class="card sponsor">
    <p class="label">For ANC meetings</p>
    <p>Each month's card comes as a one-page chart image and a short summary you can paste into a resolution or a letter to WMATA.</p>
  </section>
"""

    script = """
<script>
(function(){
  var tabs=[].slice.call(document.querySelectorAll('.tab')),ps=[].slice.call(document.querySelectorAll('.panel'));
  tabs.forEach(function(t){t.addEventListener('click',function(){tabs.forEach(function(x){x.classList.toggle('on',x===t);});ps.forEach(function(p){p.hidden=p.dataset.p!==t.dataset.t;});});});
})();
</script>"""

    extra_css = """
.small{font-size:.85rem}
.tag{display:inline-block;margin:0 0 8px;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:6px;border:1px solid currentColor}
.sample-tag{color:var(--sample)}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 10px}
.tab{font:inherit;font-size:.88rem;padding:5px 12px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.tab.on{background:var(--accent);border-color:var(--accent);color:var(--card)}
.grade{display:inline-block;width:2rem;height:2rem;line-height:2rem;text-align:center;border-radius:6px;font-weight:800;font-size:1.1rem;color:#fff}
.gA,.gB{background:var(--down)}.gC{background:var(--gold)}.gD,.gF{background:var(--up)}
:root[data-theme=dark] .grade{color:#121715}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .grade{color:#121715}}
.auto{font-size:.95rem;border-left:3px solid var(--accent);padding-left:10px}
svg.hw{width:100%;min-width:480px;height:auto;display:block}
svg.hw line.g{stroke:var(--line)}
svg.hw line.sched{stroke:var(--accent);stroke-dasharray:4 3}
svg.hw line.sched2{stroke:var(--up);stroke-dasharray:2 3}
svg.hw circle.dotok{fill:var(--accent)}svg.hw circle.big{fill:var(--up)}svg.hw circle.bunch{fill:var(--gold)}
svg.spark polyline{fill:none;stroke:var(--accent);stroke-width:1.6}
.method li{margin:.35rem 0}
code{font-size:.85em;background:var(--soft);padding:0 4px;border-radius:4px;word-break:break-all}
"""

    values = {
        "IDEA_ID": IDEA_ID, "RANK": str(RANK), "SCORE": SCORE,
        "SHORT_NAME": "Bus Report Card",
        "EXTRA_CSS": extra_css,
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": "Bus Report Card · Petworth · Adams Morgan · Tenleytown · Friendship Heights",
        "HEADLINE": "How reliable are the buses on your street?",
        "DECK": "A monthly grade for every bus line that serves the neighborhood: how long riders really waited, how often buses bunched, and how many scheduled trips never came.",
        "BODY": body + script,
        "PITCH": "Monthly, automatically published reliability grades for the bus lines that serve each neighborhood, computed from WMATA's real-time GTFS-RT feed, with a plain-English summary and a chart residents can take to their ANC.",
        "WHATS_REAL": (
            "The method. The GTFS-RT trip-updates feed it relies on is documented by WMATA. "
            f"On {today} the generator {'confirmed' if retired else 'checked'} that DC GIS's old Metro bus-stop layer is marked retired as of June 2025, when the Better Bus network renamed routes and stops, which is why no route names appear."
        ),
        "WHATS_MOCKED": (
            "Every grade, percentage, ghost-trip count, trip count, trend line, summary and the headway chart is sample data. The lines are described by corridor only "
            "(\"Sample route A\") and do not correspond to real routes. Real figures need weeks of GTFS-RT snapshots and a WMATA API key we don't have."
        ),
        "NEXT_STEPS": (
            "Get a WMATA key; run a cron Worker that stores trip-update snapshots in D1 or R2; refresh GTFS static weekly so post-Better-Bus route names stay right; "
            "a monthly GitHub Action runs the Python analysis, commits the grades and chart images, and rebuilds the page. Test early whether the GTFS-RT 1.0 feed carries the fields headway analysis needs, "
            "and share the method with WMATA before the first publish."
        ),
        "SOURCES": (
            '<a href="https://developer.wmata.com/docs/services/gtfs/operations/5cdc51ea7a6be320cab064fe">WMATA GTFS / GTFS-RT docs</a>, '
            f'<a href="{OLD_STOPS}">DC GIS archived Metro bus stops</a>; not affiliated with WMATA'
        ),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", now),
    }
    OUT.write_text(fill(values), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
