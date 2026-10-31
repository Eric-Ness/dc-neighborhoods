"""Demo #19: Will There Be a Bike? Bikeshare dock reliability forecasts. Idea transit-tech#5.

Live this run: one Capital Bikeshare GBFS snapshot (station_information + station_status) for every
station in or within 250 m of the Petworth and Tenleytown boundaries (DC Health planning neighborhoods).
Sample: the hour-by-weekday odds, which need weeks of 5-minute snapshots we have not collected yet.

Run from the repo root: python demos/ideas/src/19_will_there_be_a_bike.py
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

RANK, IDEA_ID, SCORE = 19, "transit-tech#5", "69.1"
OUT = ROOT / "demos" / "ideas" / "19-will-there-be-a-bike.html"
GBFS_INFO = "https://gbfs.lyft.com/gbfs/1.1/dca-cabi/en/station_information.json"
GBFS_STATUS = "https://gbfs.lyft.com/gbfs/1.1/dca-cabi/en/station_status.json"
HOODS_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
STATIONS_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_Rail_Bus_WebMercator/MapServer/51"
HOODS = [("Petworth", "PETWORTH", "Georgia Ave-Petworth"), ("Tenleytown & Friendship Heights", "TENLEYTOWN", "Tenleytown-AU")]
BUFFER_M = 250
CAP_ROWS = 50
HOURS = list(range(5, 24))  # 5 am to 11 pm
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": dcdata.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat = math.radians((a[0] + b[0]) / 2)
    return math.hypot((a[0] - b[0]) * 111_320, (a[1] - b[1]) * 111_320 * math.cos(lat))


def in_ring(lat: float, lon: float, ring: list) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def seg_dist_m(p: tuple[float, float], a: list, b: list) -> float:
    k = math.cos(math.radians(p[0])) * 111_320
    px, py = p[1] * k, p[0] * 111_320
    ax, ay, bx, by = a[0] * k, a[1] * 111_320, b[0] * k, b[1] * 111_320
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def where(lat: float, lon: float, rings: list) -> str | None:
    """'in' if inside the polygon, 'near' if within BUFFER_M of its edge, else None."""
    if sum(in_ring(lat, lon, r) for r in rings) % 2:
        return "in"
    for r in rings:
        for a, b in zip(r, r[1:]):
            if seg_dist_m((lat, lon), a, b) <= BUFFER_M:
                return "near"
    return None


def fill(values: dict[str, str]) -> str:
    page = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    page = page.split("<!--", 1)[0] + page.split("-->", 1)[1]
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    assert "{{" not in page, "unfilled placeholder"
    return page


def sample_grid(station_id: str, near_metro: bool) -> tuple[list[list[int]], list[list[int]]]:
    """Plausible, deterministic, made-up odds (percent) of an empty and a full dock, [day][hour].

    Residential docks drain on weekday mornings and fill in the evening; docks by a Metro station do the
    reverse. Seeded by station id so the sample is stable between runs. This is NOT a forecast.
    """
    h = hashlib.sha256(station_id.encode()).digest()
    amp = 0.55 + h[0] / 255 * 0.4
    shift = (h[1] % 5 - 2) * 0.25
    base = 0.04 + h[2] / 255 * 0.08
    empty, full = [], []
    for d in range(7):
        weekday = d < 5
        er, fr = [], []
        for hr in HOURS:
            x = hr + shift
            am = math.exp(-((x - 8.6) ** 2) / 2.2) if weekday else math.exp(-((x - 11.5) ** 2) / 8) * 0.45
            pm = math.exp(-((x - 18.3) ** 2) / 3) if weekday else math.exp(-((x - 17) ** 2) / 8) * 0.4
            drain, fillup = (pm, am) if near_metro else (am, pm)
            jitter = ((h[(d * 24 + hr) % 32] / 255) - 0.5) * 0.06
            er.append(round(100 * min(0.95, max(0.01, base + amp * drain + jitter))))
            fr.append(round(100 * min(0.95, max(0.01, base * 0.6 + amp * 0.7 * fillup - jitter))))
        empty.append(er)
        full.append(fr)
    return empty, full


def advice(empty: list[list[int]]) -> str:
    wk = [sum(empty[d][i] for d in range(5)) / 5 for i in range(len(HOURS))]
    bad = [i for i in range(len(HOURS)) if HOURS[i] < 12 and wk[i] >= 40]
    if bad:
        hr = HOURS[bad[0]]
        return f"Weekdays: get here before {hr - 1 if hr > 5 else hr}:45 am or expect it empty."
    pm_bad = [i for i in range(len(HOURS)) if HOURS[i] >= 12 and wk[i] >= 40]
    if pm_bad:
        hr = HOURS[pm_bad[0]]
        return f"Weekdays: usually fine in the morning; often empty from about {hr - 12}:00 pm."
    return "Usually has a bike at most hours."


def main() -> None:
    now = time.gmtime()
    today = time.strftime("%Y-%m-%d", now)
    info = get_json(GBFS_INFO)["data"]["stations"]
    status_doc = get_json(GBFS_STATUS)
    status = {s["station_id"]: s for s in status_doc["data"]["stations"]}
    snap_utc = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(status_doc["last_updated"]))

    names = ", ".join(f"'{m}'" for _, _, m in HOODS)
    q = dcdata._request(f"{STATIONS_LAYER}/query", {"where": f"NAME IN ({names})", "outFields": "NAME", "returnGeometry": "true", "outSR": 4326, "f": "json"})
    metro = {f["attributes"]["NAME"]: (f["geometry"]["y"], f["geometry"]["x"]) for f in q["features"]}

    sections, grids, opts, hood_n = [], {}, [], {}
    totals = {"stations": 0, "bikes": 0, "ebikes": 0, "empty": 0, "full": 0}
    for label, hpn, metro_name in HOODS:
        rings = dcdata.boundary(HOODS_LAYER, f"DC_HPN_NAME='{hpn}'")["rings"]
        rows = []
        for s in info:
            w = where(s["lat"], s["lon"], rings)
            if not w:
                continue
            st = status.get(s["station_id"], {})
            bikes, eb, docks = st.get("num_bikes_available", 0), st.get("num_ebikes_available", 0), st.get("num_docks_available", 0)
            ok = bool(st.get("is_renting")) and bool(st.get("is_installed"))
            near_metro = metro_name in metro and meters((s["lat"], s["lon"]), metro[metro_name]) < 300
            rows.append({"id": s["station_id"], "name": s["name"], "w": w, "bikes": bikes, "eb": eb, "docks": docks, "cap": s.get("capacity", 0), "ok": ok, "metro": near_metro})
        rows.sort(key=lambda r: (r["w"] != "in", r["name"]))
        shown = rows[:CAP_ROWS]
        hood_n[label] = len(rows)
        trs = []
        for r in shown:
            totals["stations"] += 1
            if r["ok"]:
                totals["bikes"] += r["bikes"]
                totals["ebikes"] += r["eb"]
                totals["empty"] += r["bikes"] == 0
                totals["full"] += r["docks"] == 0
            cap = max(1, r["bikes"] + r["docks"])
            pct = round(100 * r["bikes"] / cap)
            bar = f'<span class="bar" title="{r["bikes"]} bikes, {r["docks"]} open docks"><i style="width:{pct}%"></i></span>'
            flag = ' <span class="chip">near</span>' if r["w"] == "near" else ""
            state = (
                '<td colspan="4" class="muted">Not renting right now</td>' if not r["ok"]
                else f'<td class="n">{r["bikes"] - r["eb"]}</td><td class="n">{r["eb"]}</td><td class="n">{r["docks"]}</td><td>{bar}</td>'
            )
            trs.append(f'<tr><td>{html.escape(r["name"])}{flag}</td>{state}</tr>')
            e, f_ = sample_grid(r["id"], r["metro"])
            grids[r["id"]] = {"n": r["name"], "e": e, "f": f_, "a": advice(e)}
            opts.append((label, r["id"], r["name"]))
        more = f'<p class="small muted">Showing the first {CAP_ROWS} of {len(rows)}.</p>' if len(rows) > CAP_ROWS else ""
        sections.append(
            f'<h3>{html.escape(label)} <span class="muted small">· {len(rows)} stations in or within {BUFFER_M} m</span></h3>'
            f'<div class="scroll"><table><tr><th>Station</th><th class=n>Bikes</th><th class=n>E-bikes</th><th class=n>Open docks</th><th>Fill</th></tr>{"".join(trs)}</table></div>{more}'
        )

    groups = {}
    for label, sid, name in opts:
        groups.setdefault(label, []).append(f'<option value="{sid}">{html.escape(name)}</option>')
    select = "".join(f'<optgroup label="{html.escape(g)}">{"".join(o)}</optgroup>' for g, o in groups.items())
    first_id = opts[0][1]

    pn = hood_n["Petworth"]
    report = [
        ("Docks that ran empty during the 7-9 am weekday rush on 10+ days", f"{max(1, pn // 5)} of {pn}"),
        ("Median minutes a dock sat empty before a rebalancing truck refilled it", "74"),
        ("Docks that were full at 6 pm on most weekdays", f"{max(1, pn // 8)} of {pn}"),
        ("Hours with zero e-bikes anywhere in the neighborhood", "38"),
    ]
    report_rows = "".join(f'<tr><td>{a}</td><td class="n"><b>{b}</b></td></tr>' for a, b in report)

    body = f"""
  <section class="card">
    <p class="tag live-tag">Live · Capital Bikeshare · snapshot {snap_utc}</p>
    <h2>Right now</h2>
    <div class="grid">
      <div class="stat"><b>{totals['stations']}</b>stations</div>
      <div class="stat"><b>{totals['bikes']}</b>bikes available ({totals['ebikes']} electric)</div>
      <div class="stat"><b>{totals['empty']}</b>with no bikes</div>
      <div class="stat"><b>{totals['full']}</b>with no open docks</div>
    </div>
    {''.join(sections)}
    <p class="small muted">"Near" means outside the neighborhood line but within {BUFFER_M} m of it. Bikes counts exclude e-bikes, which are listed separately.</p>
  </section>

  <section class="card">
    <p class="tag sample-tag">Sample forecast · not real odds yet</p>
    <h2>Odds by hour and weekday</h2>
    <label class="small" for="stationPick">Station</label>
    <select id="stationPick">{select}</select>
    <div class="toolbar" role="group" aria-label="Which odds">
      <button type="button" class="pill on" data-k="e">Chance it's empty</button>
      <button type="button" class="pill" data-k="f">Chance it's full</button>
    </div>
    <p id="advice" class="advice"></p>
    <div class="scroll"><div id="heat"></div></div>
    <p class="small muted">Darker means likelier. These figures are made up to show the layout. Real odds need four to six weeks of snapshots; see "About this demo".</p>
  </section>

  <section class="card">
    <p class="tag sample-tag">Sample · monthly rebalancing report card</p>
    <h2>Petworth, last month</h2>
    <div class="scroll"><table>{report_rows}</table></div>
    <p class="small muted">Written automatically on the 1st of each month from the snapshot history. Figures here are illustrative.</p>
  </section>

  <section class="card sponsor">
    <p class="label">Sponsor slot</p>
    <p>Flat tire on the way? <b>[Local bike shop name]</b> keeps this page free.</p>
  </section>
"""

    data_json = json.dumps({"h": HOURS, "d": DAYS, "s": grids}, separators=(",", ":"))
    script = f"""
<script>
var BIKE={data_json};
(function(){{
  var pick=document.getElementById('stationPick'),heat=document.getElementById('heat'),adv=document.getElementById('advice');
  var k='e';
  function lbl(h){{return h===12?'12p':h>12?(h-12)+'p':h+'a';}}
  function draw(){{
    var s=BIKE.s[pick.value],g=s[k],cw=30,ch=24,lw=40,th=20,W=lw+cw*BIKE.h.length,H=th+ch*7;
    var o='<svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" role="img" aria-label="'+(k==='e'?'Chance empty':'Chance full')+' by hour and weekday, sample">';
    BIKE.h.forEach(function(h,i){{if(i%2===0)o+='<text x="'+(lw+i*cw+cw/2)+'" y="13" text-anchor="middle">'+lbl(h)+'</text>';}});
    BIKE.d.forEach(function(d,r){{
      o+='<text x="0" y="'+(th+r*ch+16)+'">'+d+'</text>';
      g[r].forEach(function(v,i){{o+='<rect x="'+(lw+i*cw+1)+'" y="'+(th+r*ch+1)+'" width="'+(cw-2)+'" height="'+(ch-2)+'" rx="3" fill="var(--'+(k==='e'?'brick':'accent')+')" fill-opacity="'+(0.06+v/100*0.94).toFixed(2)+'"><title>'+d+' '+lbl(BIKE.h[i])+': '+v+'% (sample)</title></rect>';}});
    }});
    heat.innerHTML=o+'</svg>';
    adv.textContent=s.n+': '+s.a+' (sample)';
  }}
  pick.addEventListener('change',draw);
  [].forEach.call(document.querySelectorAll('.pill[data-k]'),function(b){{b.addEventListener('click',function(){{k=b.dataset.k;[].forEach.call(document.querySelectorAll('.pill[data-k]'),function(x){{x.classList.toggle('on',x===b);}});draw();}});}});
  pick.value='{first_id}';draw();
}})();
</script>"""

    extra_css = """
.small{font-size:.85rem}
.tag{display:inline-block;margin:0 0 8px;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:6px;border:1px solid currentColor}
.sample-tag{color:var(--sample)}.live-tag{color:var(--live)}
h3{font-size:1rem;margin:16px 0 4px}
.bar{display:inline-block;width:70px;height:10px;border-radius:5px;background:var(--soft);border:1px solid var(--line);vertical-align:middle;overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent)}
.chip{font-size:.7rem;padding:0 6px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
select{font:inherit;max-width:100%;margin:4px 0 8px;padding:4px 6px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--ink);display:block}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 8px}
.pill{font:inherit;font-size:.85rem;padding:5px 12px;border-radius:999px;border:1px solid var(--accent);background:var(--card);color:var(--accent);cursor:pointer}
.pill.on{background:var(--accent);color:var(--card)}
.advice{font-weight:600;margin:6px 0}
"""

    n_st = totals["stations"]
    values = {
        "IDEA_ID": IDEA_ID, "RANK": str(RANK), "SCORE": SCORE,
        "SHORT_NAME": "Will There Be a Bike?",
        "EXTRA_CSS": extra_css,
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative (current dock counts live)",
        "EYEBROW": "Petworth · Tenleytown · Capital Bikeshare",
        "HEADLINE": "Will there be a bike at 8:15 tomorrow?",
        "DECK": "Every app shows how many bikes are at a dock right now. This one tells you how often that dock is empty, or full, at the hour you actually leave.",
        "BODY": body + script,
        "PITCH": "Historical odds that each Capital Bikeshare dock in the neighborhood has a bike, or an open slot, at a given hour and weekday, with a plain-English tip per station and a monthly rebalancing report card.",
        "WHATS_REAL": (
            f"The \"Right now\" table: one live snapshot of Capital Bikeshare's public GBFS feed pulled {today} ({snap_utc}) for {n_st} stations inside or within {BUFFER_M} m of "
            "the Petworth and Tenleytown (which includes Friendship Heights) neighborhood boundaries from DC GIS. Station names, bikes, e-bikes and open docks are as reported by the feed."
        ),
        "WHATS_MOCKED": (
            "The hour-by-weekday odds, the per-station tips and the rebalancing report card are sample figures, generated from a simple made-up pattern "
            "(homes drain in the morning, docks by Metro fill). We have one snapshot, not the weeks of history real odds need. The sponsor is a placeholder."
        ),
        "NEXT_STEPS": (
            f"A Cloudflare Worker cron reads station_status every 5 minutes (288 snapshots a day; about {n_st * 288:,} rows a day for these {n_st} stations) into D1, "
            "with a nightly rollup to hour-by-weekday counts so the table stays small. After four to six weeks, each cell becomes the share of snapshots with zero bikes (or zero docks) in that hour. "
            "Capital Bikeshare's monthly trip-history files could backfill demand patterns. Check the GBFS license in system_information before launch."
        ),
        "SOURCES": (
            '<a href="https://gbfs.capitalbikeshare.com/gbfs/gbfs.json">Capital Bikeshare GBFS</a>, '
            f'<a href="{HOODS_LAYER}">DC GIS neighborhood boundaries</a>, '
            f'<a href="{STATIONS_LAYER}">DC GIS Metro Stations</a>; not affiliated with Capital Bikeshare or Lyft'
        ),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", now),
    }
    OUT.write_text(fill(values), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {n_st} stations, {totals['bikes']} bikes")


if __name__ == "__main__":
    main()
