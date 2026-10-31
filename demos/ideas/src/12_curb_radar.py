"""Demo #12: Curb Radar for Petworth. Writes demos/ideas/12-curb-radar.html.

Uses DDOT's TOPS public-space permit layers (occupancy and construction), found
through the Open Data DC search API. Owner, applicant, permittee and contractor
names are never requested. Locations are shown to the hundred block.
"""

from __future__ import annotations

import html
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402
from run import hundred_block  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "12-curb-radar.html"
HPN = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
ROADS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_WebMercator/MapServer/163"
OCC_TITLE = "Occupancy Permits (via DDOT TOPs)"
CON_TITLE = "Construction Permits (via DDOT TOPs)"
DAY = 86400
AHEAD = 7
LONG_DAYS = 90
LIST_CAP = 50
esc = html.escape

OCC_FIELDS = ["TrackingNumber", "Status", "EventTypeDescription", "EffectiveDate", "ExpirationDate", "IssueDate",
              "WorkLocationFullAddress", "CurbLaneLength", "IsRoadClosed", "ParkingStartTime", "ParkingEndTime",
              "Latitude", "Longitude"]
CON_FIELDS = ["TrackingNumber", "Status", "TypeDetailNames", "EffectiveDate", "ExpirationDate", "IsOccupancy"]

# Event type -> (display group, color var/hex). Colors chosen to read in light and dark.
GROUPS = [
    ("Moving & storage", "#2f7dd1", ("Moving Truck", "Moving Storage Container")),
    ("Dumpsters", "#c0602a", ("Roll Off Debris Container",)),
    ("Construction staging", "#8a6a1f", ("Construction Staging Area", "Other Work Related Occupancy", "Steel plate")),
    ("Cranes", "#b8323a", ("Mobile Crane",)),
    ("Lead pipe replacement", "#2c8a6e", ("Lead Free DC",)),
    ("Utility & DDOT work", "#7a5bb5", ("ENP For DDOT", "Small Cell", "Manhole")),
    ("Events & reserved parking", "#5b6660", ()),
]


def group_of(event: str | None) -> str:
    e = event or ""
    for name, _, keys in GROUPS:
        if any(e.startswith(k) for k in keys):
            return name
    return GROUPS[-1][0]


COLOR = {name: color for name, color, _ in GROUPS}


def find_layer(title: str) -> tuple[str, int | None]:
    data = dcdata._request(dcdata.SEARCH_API, {"q": title, "limit": 10})
    for f in data.get("features", []):
        p = f.get("properties", {})
        if p.get("title", "").strip().lower() == title.lower() and p.get("url"):
            return p["url"], p.get("modified")
    raise RuntimeError(f"layer not found: {title}")


def fetch_geoms(layer: str, where: str, fields: list[str], envelope: dict) -> list[dict]:
    rows, offset = [], 0
    while True:
        data = dcdata._request(f"{layer}/query", {
            "where": where, "outFields": ",".join(fields), "returnGeometry": "true", "outSR": 4326,
            "geometry": json.dumps(envelope), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "maxAllowableOffset": 0.00003,
            "resultOffset": offset, "resultRecordCount": 1000, "f": "json"}, post=True)
        batch = data.get("features", [])
        rows += batch
        if not data.get("exceededTransferLimit") or not batch:
            return rows
        offset += len(batch)


class Proj:
    def __init__(self, bbox, width=640, pad=12):
        self.minx, self.miny, self.maxx, self.maxy = bbox
        self.k = math.cos(math.radians((self.miny + self.maxy) / 2))
        self.pad = pad
        self.s = (width - 2 * pad) / ((self.maxx - self.minx) * self.k)
        self.w = width
        self.h = round((self.maxy - self.miny) * self.s + 2 * pad)

    def __call__(self, lon, lat):
        return self.pad + (lon - self.minx) * self.k * self.s, self.pad + (self.maxy - lat) * self.s


def path_d(proj, coords, close=False) -> str:
    pts = [proj(x, y) for x, y in coords]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + ("Z" if close else "")


def street_of(addr: str) -> tuple[str, str]:
    """'4200 - 4299 BLOCK OF 3RD STREET NW' -> ('3rd Street NW', '4200 block of 3rd Street NW')."""
    hb = hundred_block(re.sub(r"\s+", " ", addr or "").strip()) or ""
    m = re.match(r"^(\S+) block of (.*)$", hb)
    street = (m.group(2) if m else hb).title()
    street = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda x: x.group(1).upper(), street)
    street = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda x: x.group(1) + x.group(2).lower(), street)
    block = f"{m.group(1)} block of {street}" if m else street
    return street, block


def clock(v: str | None) -> str | None:
    m = re.match(r"^\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*([AP]M)?", v or "", re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), m.group(2), (m.group(3) or "").lower()
    if not ap:
        ap = "am" if h < 12 else "pm"
        h = h % 12 or 12
    return f"{h}{'' if mi == '00' else ':' + mi} {ap}"


def hours(a: str | None, b: str | None) -> str:
    s, e = clock(a), clock(b)
    if not s or not e or s == e:
        return ""
    return f"{s}–{e}"


def d(ms: int | None) -> str:
    return time.strftime("%b %#d" if sys.platform == "win32" else "%b %-d", time.gmtime(ms / 1000)) if ms else "?"  # TOPS stores DC local time


def render(fields: dict) -> str:
    t = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    t = re.sub(r"<!--\s*\n\s*Template for idea demos.*?-->\n", "", t, flags=re.S)
    for k, v in fields.items():
        t = t.replace("{{" + k + "}}", v)
    if "{{" in t:
        raise RuntimeError("unfilled placeholder")
    return t


def main() -> None:
    now = time.time()
    now_ms = now * 1000
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    occ_url, occ_mod = find_layer(OCC_TITLE)
    con_url, con_mod = find_layer(CON_TITLE)
    geom = dcdata.boundary(HPN, "DC_HPN_NAME='PETWORTH'")

    # Freshness, citywide: latest issue/update dates and permits issued per day over the last 14 days.
    fresh = {}
    for key, url in (("occ", occ_url), ("con", con_url)):
        fresh[key] = {}
        for fld in ("IssueDate", "LastUpdateDate"):
            row = dcdata._request(f"{url}/query", {"where": f"{fld} IS NOT NULL", "orderByFields": f"{fld} DESC", "outFields": fld,
                                                   "resultRecordCount": 1, "returnGeometry": "false", "f": "json"})["features"][0]["attributes"]
            fresh[key][f"mx_{fld.lower()}"] = row[fld]
    per_day_rows = dcdata._request(f"{occ_url}/query", {
        "where": dcdata.date_where("IssueDate", now - 14 * DAY),
        "groupByFieldsForStatistics": "EXTRACT(MONTH FROM IssueDate),EXTRACT(DAY FROM IssueDate)",
        "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]),
        "f": "json"})["features"]
    per_day = {}
    for f in per_day_rows:
        a = {k.lower(): v for k, v in f["attributes"].items()}
        per_day[(int(a["expr1"]), int(a["expr2"]))] = a["n"]

    # Active in Petworth today through the next 7 days.
    horizon = time.strftime("%Y-%m-%d", time.gmtime(now + (AHEAD + 1) * DAY))
    where = f"{dcdata.date_where('ExpirationDate', now)} AND EffectiveDate < TIMESTAMP '{horizon} 00:00:00'"
    occ = dcdata.query_features(occ_url, geom, f"{where} AND Status IN ('ISSUED','APPROVED')", OCC_FIELDS)
    pending = dcdata.count_by(occ_url, geom, f"{where} AND Status IN ('ASSIGNED','RESUBMIT')", "Status")
    con = dcdata.query_features(con_url, geom, f"{where} AND Status = 9", CON_FIELDS)

    # One item per permit location; dedupe repeated rows.
    seen, items = set(), []
    for r in occ:
        key = (r["TrackingNumber"], r["WorkLocationFullAddress"], r["EventTypeDescription"])
        if key in seen:
            continue
        seen.add(key)
        street, block = street_of(r["WorkLocationFullAddress"])
        dur = ((r["ExpirationDate"] or 0) - (r["EffectiveDate"] or 0)) / 1000 / DAY
        items.append({
            "group": group_of(r["EventTypeDescription"]),
            "event": r["EventTypeDescription"] or "Other",
            "street": street, "block": block,
            "start": r["EffectiveDate"], "end": r["ExpirationDate"],
            "starts_soon": (r["EffectiveDate"] or 0) > now_ms,
            "long": dur > LONG_DAYS, "days": dur,
            "curb": r["CurbLaneLength"] or 0,
            "closed": (r["IsRoadClosed"] or "").upper() == "Y",
            "hours": hours(r["ParkingStartTime"], r["ParkingEndTime"]),
            "lat": r["Latitude"], "lon": r["Longitude"],
        })
    if not items:
        raise RuntimeError("no active occupancy permits found in Petworth")
    items.sort(key=lambda i: (i["start"] or 0))
    by_group = Counter(i["group"] for i in items)
    upcoming = [i for i in items if i["starts_soon"]]
    long_running = [i for i in items if i["long"]]
    curb_ft = sum(i["curb"] for i in items if i["curb"])
    streets = defaultdict(list)
    for i in items:
        streets[i["street"]].append(i)

    # ---- Map ----
    xs = [p[0] for ring in geom["rings"] for p in ring]
    ys = [p[1] for ring in geom["rings"] for p in ring]
    bbox = (min(xs) - 0.001, min(ys) - 0.001, max(xs) + 0.001, max(ys) + 0.001)
    proj = Proj(bbox)
    roads = fetch_geoms(ROADS, "1=1", ["STREETNAME", "STREETTYPE", "DCFUNCTIONALCLASS", "SHAPE.LEN"],
                        {"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3], "spatialReference": {"wkid": 4326}})
    road_minor, road_major, labels, labelled = [], [], [], set()
    for f in sorted(roads, key=lambda f: -(f["attributes"].get("SHAPE.LEN") or 0)):
        for p in f.get("geometry", {}).get("paths", []):
            dd = path_d(proj, p)
            cls = f["attributes"].get("DCFUNCTIONALCLASS")
            (road_major if cls in (11, 12, 14, 16) else road_minor).append(dd)
        a = f["attributes"]
        name = f"{(a.get('STREETNAME') or '').title()} {(a.get('STREETTYPE') or '').title()}".strip()
        if a.get("DCFUNCTIONALCLASS") in (14, 16) and name and name not in labelled and f.get("geometry", {}).get("paths"):
            path = f["geometry"]["paths"][0]
            mx, my = proj(*path[len(path) // 2])
            if 20 < mx < proj.w - 60 and 20 < my < proj.h - 10:
                labelled.add(name)
                labels.append(f'<text x="{mx:.0f}" y="{my - 4:.0f}" class="road-lbl">{esc(name)}</text>')
    outline = "".join(f'<path d="{path_d(proj, ring, True)}" class="hood"/>' for ring in geom["rings"])
    dots = []
    for n, i in enumerate(items):
        if not i["lat"] or not i["lon"]:
            continue
        x, y = proj(i["lon"], i["lat"])
        if not (0 <= x <= proj.w and 0 <= y <= proj.h):
            continue
        ring = ' stroke="var(--ink)" stroke-width="1.5"' if i["starts_soon"] else ' stroke="var(--card)" stroke-width="1"'
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6 if i["starts_soon"] else 4.5}" fill="{COLOR[i["group"]]}"{ring} '
                    f'data-g="{esc(i["group"])}"><title>{esc(i["event"])} · {esc(i["block"])} · {d(i["start"])}–{d(i["end"])}</title></circle>')
    svg_map = (f'<svg viewBox="0 0 {proj.w} {proj.h}" class="map" role="img" aria-label="Map of active DDOT occupancy permits in Petworth">'
               f'<g class="roads-minor"><path d="{" ".join(road_minor)}"/></g><g class="roads-major"><path d="{" ".join(road_major)}"/></g>'
               f'{outline}{"".join(labels)}<g id="dots">{"".join(dots)}</g></svg>')

    chips = "".join(
        f'<button type="button" class="chip" aria-pressed="true" data-g="{esc(name)}"><i style="background:{color}"></i>{esc(name)} <b>{by_group[name]}</b></button>'
        for name, color, _ in GROUPS if by_group.get(name)
    )

    def item_li(i) -> str:
        flags = []
        if i["starts_soon"]:
            flags.append('<span class="flag soon">starts ' + d(i["start"]) + "</span>")
        if i["long"]:
            flags.append(f'<span class="flag long">long-running · {round(i["days"])} days</span>')
        if i["closed"]:
            flags.append('<span class="flag closed">road closure</span>')
        curb = f" · {i['curb']} ft of curb" if i["curb"] else ""
        hrs = f" · {esc(i['hours'])}" if i["hours"] else ""
        return (f'<li data-g="{esc(i["group"])}"><i class="sw" style="background:{COLOR[i["group"]]}"></i>'
                f'<div><b>{esc(i["event"])}</b> {"".join(flags)}<br><span class="muted">{esc(i["block"])} · {d(i["start"])} – {d(i["end"])}{curb}{hrs}</span></div></li>')

    # Coming up: by start day.
    by_day = defaultdict(list)
    for i in upcoming:
        by_day[time.strftime("%A, %b %#d" if sys.platform == "win32" else "%A, %b %-d", time.gmtime(i["start"] / 1000))].append(i)
    coming = "".join(f'<h3>{esc(day)}</h3><ul class="items">{"".join(item_li(i) for i in its)}</ul>' for day, its in by_day.items()) \
        or '<p class="muted">Nothing new starts in the next 7 days.</p>'

    # By street, busiest first, capped.
    street_html, shown = [], 0
    for street, its in sorted(streets.items(), key=lambda kv: -len(kv[1])):
        if shown >= LIST_CAP:
            break
        its = its[: LIST_CAP - shown]
        shown += len(its)
        street_html.append(f'<details{" open" if len(street_html) < 3 else ""}><summary><b>{esc(street)}</b> <span class="muted">· {len(streets[street])} permit location{"s" if len(streets[street]) != 1 else ""}</span>'
                           f'<span class="follow">Follow this street</span></summary><ul class="items">{"".join(item_li(i) for i in its)}</ul></details>')
    cap_note = f"Showing the first {LIST_CAP} of {len(items)} permit locations." if len(items) > LIST_CAP else f"All {len(items)} permit locations."

    # Construction permits (excavation, poles etc.) summarized by work kind.
    con_seen, kinds = set(), Counter()
    for r in con:
        if r["TrackingNumber"] in con_seen:
            continue
        con_seen.add(r["TrackingNumber"])
        names = r["TypeDetailNames"] or ""
        if "Water Service Lateral" in names or "Boring Test Pit" in names:
            kinds["Water service line (incl. lead pipe) work"] += 1
        elif "Over Head Work" in names:
            kinds["Utility poles & overhead wires"] += 1
        elif "Gas" in names:
            kinds["Gas line work"] += 1
        elif "Electric" in names:
            kinds["Electric line work"] += 1
        elif "Paving" in names or "Leadwalk" in names or "Driveway" in names or "Curb" in names:
            kinds["Sidewalk, driveway & paving"] += 1
        else:
            kinds["Other public-space construction"] += 1
    con_rows = "".join(f"<tr><td>{esc(k)}</td><td class='n'>{n}</td></tr>" for k, n in kinds.most_common())

    # Freshness bars (last 14 days, citywide occupancy permits issued per day).
    bars, days = [], []
    for k in range(13, -1, -1):
        t = time.gmtime(now - k * DAY)
        days.append(((t.tm_mon, t.tm_mday), time.strftime("%a", t)[0], t.tm_mday))
    mx = max([per_day.get(k_, 0) for k_, _, _ in days] + [1])
    for n_, (key, wd, md) in enumerate(days):
        v = per_day.get(key, 0)
        h = 60 * v / mx
        x = 6 + n_ * 22
        bars.append(f'<rect x="{x}" y="{70 - h:.1f}" width="16" height="{h:.1f}" rx="2" fill="var(--accent)"><title>{v} issued</title></rect>'
                    f'<text x="{x + 8}" y="84" text-anchor="middle">{wd}</text>')
    fresh_svg = f'<svg viewBox="0 0 316 88" style="width:100%;max-width:420px;height:auto" role="img" aria-label="Occupancy permits issued per day citywide">{"".join(bars)}</svg>'
    occ_last = d(fresh["occ"]["mx_issuedate"])
    occ_upd = d(fresh["occ"]["mx_lastupdatedate"])
    con_last = d(fresh["con"]["mx_issuedate"])
    cat_mod = time.strftime("%B %Y", time.gmtime(occ_mod / 1000)) if occ_mod else "an earlier date"
    issued_7 = sum(per_day.get(k_, 0) for k_, _, _ in days[-7:])
    pend_n = sum(pending.values())

    body = f"""
<div class="grid">
  <div class="card stat"><b>{len(items)}</b>curb &amp; street permits active in Petworth this week</div>
  <div class="card stat"><b>{len(upcoming)}</b>start in the next 7 days</div>
  <div class="card stat"><b>{curb_ft:,} ft</b>of curb reserved (where DDOT lists a length)</div>
  <div class="card stat"><b>{len(long_running)}</b>long-running (over {LONG_DAYS} days)</div>
</div>

<section class="card">
  <h2>On the map: today through {time.strftime('%b %#d' if sys.platform == 'win32' else '%b %-d', time.gmtime(now + AHEAD * DAY))}</h2>
  <div class="chips" role="group" aria-label="Filter by type">{chips}</div>
  {svg_map}
  <p class="muted small">Dots with a dark ring start within the next 7 days. Tap a type above to hide or show it. Locations are DDOT's permit coordinates; the list shows them to the hundred block.</p>
</section>

<section class="card">
  <h2>Coming up this week</h2>
  <p class="muted small">Permits that are approved or issued and begin in the next 7 days. Plan your parking accordingly.</p>
  {coming}
</section>

<section class="card">
  <h2>By street</h2>
  <p class="muted small">{cap_note} Busiest streets first.</p>
  {''.join(street_html)}
</section>

<div class="two">
<section class="card">
  <h2>Digging &amp; utility work</h2>
  <p class="muted small">Active DDOT construction permits in Petworth this week (excavation, poles, paving). These often come with their own no-parking signs.</p>
  <div class="scroll"><table><thead><tr><th>Work</th><th class="n">Permits</th></tr></thead><tbody>{con_rows or '<tr><td colspan=2>None</td></tr>'}</tbody></table></div>
</section>
<section class="card">
  <h2>Is this data fresh?</h2>
  <p class="small" style="margin-top:0">Yes. DDOT's TOPS layers update daily. The newest occupancy permit was issued <b>{occ_last}</b> and the newest record update was <b>{occ_upd}</b>;
  the newest construction permit was issued <b>{con_last}</b>. Citywide, DDOT issued <b>{issued_7:,}</b> occupancy permits in the last 7 days:</p>
  {fresh_svg}
  <p class="muted small">The Open Data DC catalog entry still says the dataset was last modified in {cat_mod}; the live map service behind it is current. {pend_n} more Petworth applications for this week are still under review and not shown.</p>
</section>
</div>

<section class="card sponsor">
  <span class="label">Get alerts</span>
  <p style="margin:.2rem 0 .5rem">Follow a street and get an email the morning a new dumpster, moving truck or crane permit is approved on it.</p>
  <form class="sub" onsubmit="event.preventDefault();this.querySelector('output').textContent='Demo only: no email was sent or stored.'">
    <label class="vh" for="st">Street</label><input id="st" placeholder="e.g. Upshur Street NW" autocomplete="off">
    <button type="submit">Follow</button><output class="muted small"></output>
  </form>
</section>
"""

    script = """
<script>
(function(){
  var chips=document.querySelectorAll('.chip');
  chips.forEach(function(c){c.addEventListener('click',function(){
    var on=c.getAttribute('aria-pressed')!=='true';c.setAttribute('aria-pressed',on);
    var g=c.dataset.g;document.querySelectorAll('[data-g]').forEach(function(el){
      if(el.classList.contains('chip'))return;if(el.dataset.g===g)el.style.display=on?'':'none';});
  });});
})();
</script>"""

    extra_css = """
.small{font-size:.86rem}
.map{width:100%;height:auto;display:block;margin-top:8px;background:var(--soft);border-radius:8px}
.roads-minor path{fill:none;stroke:var(--line);stroke-width:1.2}
.roads-major path{fill:none;stroke:var(--muted);stroke-width:2.2;opacity:.55}
.hood{fill:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:6 4}
svg text.road-lbl{font-size:10px;fill:var(--muted);paint-order:stroke;stroke:var(--soft);stroke-width:3px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:inherit;font-size:.8rem;display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.chip i,.sw{display:inline-block;width:10px;height:10px;border-radius:50%;flex:none}
.chip[aria-pressed=false]{opacity:.45;text-decoration:line-through}
h3{font-size:.95rem;margin:1rem 0 .3rem}
ul.items{list-style:none;margin:0;padding:0}
ul.items li{display:flex;gap:10px;align-items:flex-start;padding:.45rem 0;border-bottom:1px solid var(--line);font-size:.92rem}
ul.items li .sw{margin-top:.4rem}
.flag{font-size:.7rem;font-weight:600;padding:1px 6px;border-radius:4px;margin-left:4px;white-space:nowrap}
.flag.soon{background:var(--soft);color:var(--accent)}.flag.long{background:var(--soft);color:var(--gold)}.flag.closed{background:var(--soft);color:var(--brick)}
details{border-top:1px solid var(--line);padding:.4rem 0}
summary{cursor:pointer;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline}
.follow{margin-left:auto;font-size:.75rem;color:var(--accent);border:1px solid var(--accent);border-radius:999px;padding:0 8px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 14px}
.sub{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.sub input{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);flex:1;min-width:0}
.sub button{font:inherit;padding:6px 14px;border-radius:6px;border:0;background:var(--accent);color:var(--card);cursor:pointer}
.sub output{flex-basis:100%}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
"""

    fields = {
        "IDEA_ID": "civic-data#6",
        "RANK": "12",
        "SCORE": "71.5",
        "SHORT_NAME": "Curb Radar",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "Petworth · Curb Radar",
        "HEADLINE": "Who has the curb in Petworth this week",
        "DECK": (f"Dumpsters, moving trucks, construction staging and DDOT no-parking zones from DDOT public-space permits, "
                 f"active today through the next {AHEAD} days. Updated every morning."),
        "BODY": body + script,
        "EXTRA_CSS": extra_css,
        "PITCH": "A daily map and alert feed of every DDOT public-space permit on the neighborhood's streets: who has reserved the curb, where a crane is going up, and which block loses parking next week.",
        "WHATS_REAL": (f"Every permit, date, curb length and map dot comes from DDOT's TOPS layers on Open Data DC, pulled {pulled}: "
                       f"<a href=\"{esc(occ_url)}\">Occupancy Permits (via DDOT TOPs)</a> and <a href=\"{esc(con_url)}\">Construction Permits (via DDOT TOPs)</a>, "
                       "both found through the Open Data DC search API. Only permits with status Issued or Approved whose dates overlap today–+7 days are shown. "
                       "The freshness panel is computed from the live layer (max issue and update dates, per-day counts). Street lines are DDOT's Roadway Block layer."),
        "WHATS_MOCKED": ("The 'Follow this street' buttons and the alert form are non-working mockups; nothing is sent or stored. "
                         "Type groupings and colors are my own. Permit holders' names (owner, applicant, permittee, contractor) are in the source data but are never requested or shown."),
        "NEXT_STEPS": ("Run the same two queries in the nightly ingest, keep yesterday's snapshot to detect newly approved permits, "
                       "send per-street alerts with Cloudflare Email Workers, and add an RSS feed per street. Watch the layer's update date and hide the page if it goes stale."),
        "SOURCES": ('<a href="https://opendata.dc.gov/">Open Data DC</a>: DDOT TOPS Occupancy Permits and Construction Permits, Roadway Block, DC Health planning areas; CC BY 4.0. '
                    'Permit lookup: <a href="https://tops.ddot.dc.gov">tops.ddot.dc.gov</a>'),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
    }
    OUT.write_text(render(fields), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(items)} items, {len(upcoming)} upcoming, {len(long_running)} long, {len(con_seen)} construction, roads {len(roads)}; "
          f"occ last issue {occ_last}, catalog modified {cat_mod}")


if __name__ == "__main__":
    main()
