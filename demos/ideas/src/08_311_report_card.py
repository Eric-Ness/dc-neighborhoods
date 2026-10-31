"""Demo #8: 311 Report Card for Petworth. Writes demos/ideas/08-311-report-card.html.

Median days-to-close are computed server-side by DC's ArcGIS server
(percentile_cont on RESOLUTIONDATE - ADDDATE), so individual requests never
leave DC's servers for the medians. Only the "still open" list fetches rows,
and those are coarsened to the hundred block before use.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402
from run import hundred_block  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "08-311-report-card.html"
HPN = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
SR_TITLE = "311 City Service Requests in {year}"
DAY = 86400
WINDOW_START_DAYS = 210  # requests added 210..30 days ago, so every one had at least 30 days to close
WINDOW_END_DAYS = 30
MIN_N = 10
HOODS = [("PETWORTH", "Petworth"), ("TENLEYTOWN", "Tenleytown"), ("ADAMS MORGAN", "Adams Morgan")]
CLOSED = "SERVICEORDERSTATUS = 'Closed'"
OPEN = "SERVICEORDERSTATUS IN ('Open','In-Progress','In Progress')"
MED_STATS = [
    {"statisticType": "percentile_cont", "statisticParameters": {"value": 0.5},
     "onStatisticField": "RESOLUTIONDATE - ADDDATE", "outStatisticFieldName": "med"},
    {"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"},
]
COUNT_STATS = [{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]
esc = html.escape


def stats(layer: str, where: str, group: str, geom: dict | None, which=MED_STATS) -> list[dict]:
    params = {"where": where, "groupByFieldsForStatistics": group, "outStatistics": json.dumps(which), "f": "json"}
    if geom:
        params.update(dcdata._spatial(geom))
    data = dcdata._request(f"{layer}/query", params, post=True)
    return [{k.lower(): v for k, v in f["attributes"].items()} for f in data.get("features", [])]


def fmt_days(d: float | None) -> str:
    if d is None:
        return "—"
    if d < 1:
        return f"{max(1, round(d * 24))} hr"
    return f"{d:.1f} d" if d < 10 else f"{round(d)} d"


def title_type(t: str) -> str:
    return t.strip()


def render(fields: dict) -> str:
    t = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    t = re.sub(r"<!--\s*\n\s*Template for idea demos.*?-->\n", "", t, flags=re.S)
    for k, v in fields.items():
        t = t.replace("{{" + k + "}}", v)
    if "{{" in t:
        raise RuntimeError("unfilled placeholder: " + re.search(r"\{\{\w+\}\}", t).group(0))
    return t


def main() -> None:
    now = time.time()
    year = time.gmtime(now).tm_year
    layer = dcdata.resolve_yearly_layer(SR_TITLE, year)
    if not layer:
        raise RuntimeError("no 311 layer for this year")
    # Keep the window inside this year's layer; in early-year runs it simply gets shorter.
    jan1 = time.mktime((year, 1, 1, 0, 0, 0, 0, 0, 0)) - time.timezone
    w_start = max(now - WINDOW_START_DAYS * DAY, jan1)
    w_end = now - WINDOW_END_DAYS * DAY
    window = dcdata.date_where("ADDDATE", w_start, w_end)

    geoms = {key: dcdata.boundary(HPN, f"DC_HPN_NAME='{key}'") for key, _ in HOODS}
    pet = geoms["PETWORTH"]

    # 1. Medians per type: Petworth, the other two neighborhoods, and citywide. All server-side.
    def med_by_type(geom):
        rows = stats(layer, f"{window} AND {CLOSED} AND RESOLUTIONDATE >= ADDDATE", "SERVICECODEDESCRIPTION", geom)
        return {r["servicecodedescription"]: (r["med"], r["n"]) for r in rows}

    med = {key: med_by_type(g) for key, g in geoms.items()}
    city = med_by_type(None)
    # Requests in the window that are still open (any status other than closed/cancelled).
    open_in_window = {r["servicecodedescription"]: r["n"] for r in stats(layer, f"{window} AND {OPEN}", "SERVICECODEDESCRIPTION", pet, COUNT_STATS)}

    # 2. Monthly medians in Petworth for sparklines (one grouped call).
    monthly_rows = stats(layer, f"{CLOSED} AND RESOLUTIONDATE >= ADDDATE", "SERVICECODEDESCRIPTION,EXTRACT(MONTH FROM ADDDATE)", pet)
    monthly: dict[str, dict[int, tuple[float, int]]] = {}
    for r in monthly_rows:
        mkey = next(k for k in r if k.startswith("expr"))
        monthly.setdefault(r["servicecodedescription"], {})[int(r[mkey])] = (r["med"], r["n"])

    # 3. This month vs previous 30 days (counts only).
    last30 = {r["servicecodedescription"]: r["n"] for r in stats(layer, dcdata.date_where("ADDDATE", now - 30 * DAY), "SERVICECODEDESCRIPTION", pet, COUNT_STATS)}
    prev_start = max(now - 60 * DAY, jan1)
    prev30 = {r["servicecodedescription"]: r["n"] for r in stats(layer, dcdata.date_where("ADDDATE", prev_start, now - 30 * DAY), "SERVICECODEDESCRIPTION", pet, COUNT_STATS)}

    # 4. Still open after 30+ days, coarsened to the hundred block immediately.
    stale_rows = dcdata.query_features(
        layer, pet, f"{dcdata.date_where('ADDDATE', jan1, now - 30 * DAY)} AND {OPEN}",
        ["SERVICECODEDESCRIPTION", "STREETADDRESS", "ADDDATE"],
    )
    stale = [{"type": r["SERVICECODEDESCRIPTION"], "block": hundred_block(r["STREETADDRESS"]) or "Location not given",
              "age": (now * 1000 - (r["ADDDATE"] or now * 1000)) / 1000 / DAY} for r in stale_rows]
    stale_by_block = Counter(s["block"] for s in stale)
    stale_by_type = Counter(s["type"] for s in stale)
    oldest_by_block: dict[str, float] = {}
    for s in stale:
        oldest_by_block[s["block"]] = max(oldest_by_block.get(s["block"], 0), s["age"])

    # ---- Build the table rows ----
    pm = med["PETWORTH"]
    types = sorted((t for t, (m, n) in pm.items() if n >= MIN_N), key=lambda t: -pm[t][1])[:14]
    if not types:
        raise RuntimeError("no 311 types with enough closed requests in Petworth")
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    total_closed = sum(n for _, n in pm.values())
    faster = sum(1 for t in types if city.get(t) and pm[t][0] < city[t][0] * 0.9)
    slower = sum(1 for t in types if city.get(t) and pm[t][0] > city[t][0] * 1.1)

    # Dot plot: Petworth vs citywide median days, log-ish scale capped at 60 days.
    import math

    def xpos(d):
        d = max(d, 0.04)
        return 150 + (math.log10(d) - math.log10(0.04)) / (math.log10(90) - math.log10(0.04)) * 300

    rows_svg = []
    h = 26 * len(types) + 34
    for tick, label in [(0.0417, "1 hr"), (1, "1 day"), (7, "1 wk"), (30, "30 d"), (90, "90 d")]:
        x = xpos(tick)
        rows_svg.append(f'<line x1="{x:.1f}" y1="14" x2="{x:.1f}" y2="{h-16}" stroke="var(--line)"/>'
                        f'<text x="{x:.1f}" y="{h-3}" text-anchor="middle">{label}</text>')
    for i, t in enumerate(types):
        y = 26 + i * 26
        p = pm[t][0]
        c = city.get(t, (None, 0))[0]
        name = t if len(t) <= 24 else t[:23] + "…"
        rows_svg.append(f'<text x="144" y="{y+4}" text-anchor="end" class="lbl">{esc(name)}</text>')
        if c is not None:
            rows_svg.append(f'<line x1="{xpos(c):.1f}" y1="{y}" x2="{xpos(p):.1f}" y2="{y}" stroke="var(--muted)" stroke-width="2" opacity=".5"/>'
                            f'<circle cx="{xpos(c):.1f}" cy="{y}" r="5" fill="var(--card)" stroke="var(--muted)" stroke-width="2"><title>Citywide: {fmt_days(c)}</title></circle>')
        rows_svg.append(f'<circle cx="{xpos(p):.1f}" cy="{y}" r="5.5" fill="var(--accent)"><title>Petworth: {fmt_days(p)}</title></circle>')
    dotplot = (f'<svg viewBox="0 0 470 {h}" role="img" aria-label="Median days to close, Petworth versus citywide" style="width:100%;height:auto">'
               + "".join(rows_svg) + "</svg>")

    def spark(t: str) -> str:
        pts = monthly.get(t, {})
        months = [m for m in range(1, 13) if m in pts and pts[m][1] >= 3]
        if len(months) < 3:
            return '<span class="muted">—</span>'
        vals = [pts[m][0] for m in months]
        hi = max(vals) or 1
        coords = [(4 + (m - 1) * (92 / 11), 22 - 18 * v / hi) for m, v in zip(months, vals)]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
        lx, ly = coords[-1]
        return (f'<svg viewBox="0 0 100 26" width="100" height="26" aria-label="Monthly median, Jan to {time.strftime("%b", time.gmtime(now))}">'
                f'<polyline points="{path}" fill="none" stroke="var(--accent)" stroke-width="1.6"/>'
                f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.2" fill="var(--accent)"/></svg>')

    table_rows = []
    for t in types:
        p, n = pm[t]
        c, cn = city.get(t, (None, 0))
        cmp_ = ""
        if c:
            ratio = p / c if c else 1
            if ratio < 0.9:
                cmp_ = f'<span class="down">faster</span>'
            elif ratio > 1.1:
                cmp_ = f'<span class="up">slower</span>'
            else:
                cmp_ = '<span class="muted">about the same</span>'
        others = []
        for key, _ in HOODS[1:]:
            m2 = med[key].get(t)
            others.append(f'<td class="n">{fmt_days(m2[0]) if m2 and m2[1] >= MIN_N else "<span class=muted>few</span>"}</td>')
        still = open_in_window.get(t, 0)
        table_rows.append(
            f"<tr><td>{esc(t)}</td><td class='n'>{n:,}</td><td class='n'><b>{fmt_days(p)}</b></td>"
            f"<td class='n'>{fmt_days(c)}</td><td>{cmp_}</td>{''.join(others)}<td class='n'>{still}</td><td>{spark(t)}</td></tr>"
        )

    # Monthly paragraph: biggest movers in raw counts, no percentages under 100.
    movers = []
    for t in set(last30) | set(prev30):
        a, b = last30.get(t, 0), prev30.get(t, 0)
        if max(a, b) >= 15:
            movers.append((a - b, t, a, b))
    movers.sort(key=lambda x: -abs(x[0]))
    sentences = []
    for diff, t, a, b in movers[:3]:
        if diff == 0:
            continue
        word = "up" if diff > 0 else "down"
        if b >= 100:
            sentences.append(f"{esc(t)} requests were {word} {abs(round(100 * diff / b))}% ({b:,} → {a:,}).")
        else:
            sentences.append(f"{esc(t)} requests went from {b} to {a}.")
    tot_now, tot_prev = sum(last30.values()), sum(prev30.values())
    fastest = min(types, key=lambda t: pm[t][0])
    slowest = max(types, key=lambda t: pm[t][0])
    paragraph = (
        f"Neighbors filed <b>{tot_now:,}</b> requests in the last 30 days, compared with {tot_prev:,} in the 30 days before. "
        + " ".join(sentences)
        + f" Of the common request types, <b>{esc(fastest)}</b> closes fastest here (typically {fmt_days(pm[fastest][0])}), "
        f"and <b>{esc(slowest)}</b> takes longest ({fmt_days(pm[slowest][0])})."
    )

    top_types_rows = "".join(
        f"<tr><td>{esc(t)}</td><td class='n'>{last30.get(t, 0)}</td><td class='n'>{prev30.get(t, 0)}</td></tr>"
        for t, _ in Counter(last30).most_common(8)
    )
    stale_block_rows = "".join(
        f"<tr><td>{esc(re.sub(r'(?<=\d)(St|Nd|Rd|Th)', lambda m: m.group(1).lower(), re.sub(r'\b(Nw|Ne|Sw|Se)\b', lambda m: m.group(1).upper(), b.title())).replace(' Block Of ', ' block of ') if b else '')}</td><td class='n'>{n}</td><td class='n'>{round(oldest_by_block[b])} days</td></tr>"
        for b, n in stale_by_block.most_common(15)
    )
    stale_type_rows = "".join(f"<li>{esc(t)}: <b>{n}</b></li>" for t, n in stale_by_type.most_common(6))

    wstart_s = time.strftime("%b %-d" if sys.platform != "win32" else "%b %#d", time.gmtime(w_start))
    wend_s = time.strftime("%b %-d" if sys.platform != "win32" else "%b %#d", time.gmtime(w_end))

    body = f"""
<div class="grid">
  <div class="card stat"><b>{tot_now:,}</b>requests in the last 30 days</div>
  <div class="card stat"><b>{faster}</b>request types closing faster than citywide</div>
  <div class="card stat"><b>{slower}</b>request types closing slower than citywide</div>
  <div class="card stat"><b>{len(stale):,}</b>requests from this year still open after 30+ days</div>
</div>

<section class="card">
  <p class="eyebrow">This month in Petworth</p>
  <p style="margin:.3rem 0 0">{paragraph}</p>
</section>

<section class="card">
  <h2>How long until the city marks it closed?</h2>
  <p class="muted small">Median days from request to reported closure, for requests filed {wstart_s}–{wend_s} (each had at least 30 days to close).
  <span class="key"><i class="dot pet"></i>Petworth</span> <span class="key"><i class="dot cty"></i>Citywide</span></p>
  {dotplot}
</section>

<section class="card">
  <h2>Report card by request type</h2>
  <div class="scroll"><table>
    <thead><tr><th>Request type</th><th class="n">Closed here</th><th class="n">Petworth median</th><th class="n">Citywide</th><th>vs. city</th>
    <th class="n">Tenleytown</th><th class="n">Adams Morgan</th><th class="n">Still open</th><th>Monthly trend</th></tr></thead>
    <tbody>{''.join(table_rows)}</tbody>
  </table></div>
  <p class="muted small">"Faster" or "slower" means the Petworth median is more than 10% below or above citywide. "Few" means under {MIN_N} closed requests of that type there.
  "Still open" counts requests from the same window that are not yet closed. The trend line is the Petworth monthly median since January (higher means slower).</p>
</section>

<div class="two">
<section class="card">
  <h2>What people reported, last 30 days</h2>
  <div class="scroll"><table><thead><tr><th>Type</th><th class="n">Last 30 days</th><th class="n">30 days before</th></tr></thead>
  <tbody>{top_types_rows}</tbody></table></div>
</section>
<section class="card">
  <h2>Still open after 30 days</h2>
  <p class="muted small">Requests filed this year, open for more than 30 days. Most common types:</p>
  <ul class="tight">{stale_type_rows}</ul>
</section>
</div>

<section class="card">
  <h2>Blocks waiting longest</h2>
  <p class="muted small">Top 15 blocks by number of requests open more than 30 days. Addresses are shown to the hundred block only.</p>
  <div class="scroll"><table><thead><tr><th>Block</th><th class="n">Open 30+ days</th><th class="n">Oldest</th></tr></thead>
  <tbody>{stale_block_rows}</tbody></table></div>
</section>

<section class="card sponsor">
  <span class="label">Reading these numbers</span>
  <p style="margin:.2rem 0 0">This is <b>reported</b> closure: the date an agency marked the request closed in 311. A closed request is not always a fixed problem,
  and some types (bulk pickup, yard waste) close on a schedule rather than on demand. Use the numbers to ask questions, not to grade crews.</p>
</section>
"""

    extra_css = """
.small{font-size:.86rem}
.lbl{fill:var(--ink);font-size:11px}
.key{display:inline-flex;align-items:center;gap:4px;margin-left:10px;white-space:nowrap}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%}
.dot.pet{background:var(--accent)}.dot.cty{border:2px solid var(--muted);background:var(--card)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 14px}
ul.tight{margin:.3rem 0 0;padding-left:1.1rem}
td svg{display:block}
"""

    fields = {
        "IDEA_ID": "civic-data#4",
        "RANK": "8",
        "SCORE": "72.7",
        "SHORT_NAME": "311 Report Card",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "Petworth · 311 Report Card",
        "HEADLINE": "How fast does the city fix things in Petworth?",
        "DECK": (f"Typical days from a 311 request to reported closure, by request type, compared with all of DC. "
                 f"Based on {total_closed:,} closed Petworth requests. Updated nightly."),
        "BODY": body,
        "EXTRA_CSS": extra_css,
        "PITCH": "A live scoreboard of 311 requests per neighborhood: what people report, how long each type takes to close, and how that compares with the rest of DC.",
        "WHATS_REAL": (f"Everything on this page was pulled from Open Data DC's 311 City Service Requests layer on {pulled}. "
                       "Medians are computed <b>server-side</b> by DC's ArcGIS server (50th percentile of RESOLUTIONDATE − ADDDATE, status 'Closed' only, "
                       "duplicates and transfers excluded) over every closed request in the window, not a sample. Citywide uses the same query with no boundary. "
                       "Neighborhood boundaries are DC Health planning areas. The 'still open' list fetches only type, address and date, and coarsens addresses to the hundred block before use."),
        "WHATS_MOCKED": "Nothing in the numbers. The layout, the auto-written paragraph's wording and the 'faster/slower' threshold (10%) are design choices for the demo. Free-text details and exact addresses are never requested.",
        "NEXT_STEPS": ("Add the query to the nightly ingest (one grouped stats call per neighborhood plus one citywide), store monthly snapshots so trends survive the January layer rollover, "
                       "add a per-block map of open requests, and publish a printable one-pager for ANC meetings."),
        "SOURCES": '<a href="https://opendata.dc.gov/">Open Data DC</a>: 311 City Service Requests (OUC), DC Health planning areas; CC BY 4.0',
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
    }
    OUT.write_text(render(fields), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(types)} types, {total_closed} closed, {len(stale)} stale, citywide types {len(city)}")


if __name__ == "__main__":
    main()
