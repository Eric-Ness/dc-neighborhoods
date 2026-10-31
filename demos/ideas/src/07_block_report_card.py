"""Demo #7: Block Report Card for the 700 block of Shepherd Street NW (Petworth).
Writes demos/ideas/07-block-report-card.html.

Joins, for one block face: DDOT roadway attributes, DOB building permits, 311
requests (server-side counts), crashes within 150 m (counts only), street trees,
nearby ABC licensees (public trade names), school attendance zones and the SMD.
Never requested: owner/applicant names, 311 details, crash report numbers.
"""

from __future__ import annotations

import html
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402
from run import PERMIT_FIELDS, SMD_LAYER, permit_group, yearly_layers  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "07-block-report-card.html"
STREET, STREET_SHORT, LOW = "SHEPHERD STREET NW", "SHEPHERD ST", 700
BLOCK_TITLE = "700 block of Shepherd Street NW"
ROADS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_WebMercator/MapServer/163"
EDU = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Education_WebMercator/MapServer"
SCHOOL_LAYERS = [("Elementary", f"{EDU}/19"), ("Middle", f"{EDU}/17"), ("High", f"{EDU}/15")]
DAY = 86400
CRASH_M = 150
LIC_M = 250
TREE_M = 15
esc = html.escape


def find_layer(title: str) -> str:
    data = dcdata._request(dcdata.SEARCH_API, {"q": title, "limit": 10})
    for f in data.get("features", []):
        p = f.get("properties", {})
        if p.get("title", "").strip().lower() == title.lower() and p.get("url"):
            return p["url"]
    raise RuntimeError(f"layer not found: {title}")


def q(layer: str, params: dict) -> list[dict]:
    rows, offset = [], 0
    while True:
        data = dcdata._request(f"{layer}/query", {"f": "json", "outSR": 4326, "resultOffset": offset, "resultRecordCount": 1000, **params}, post=True)
        batch = data.get("features", [])
        rows += batch
        if not data.get("exceededTransferLimit") or not batch:
            return rows
        offset += len(batch)


def near(geom: dict, gtype: str, meters: float) -> dict:
    return {"geometry": json.dumps(geom), "geometryType": gtype, "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
            "distance": meters, "units": "esriSRUnit_Meter"}


def count_where(layer: str, where: str, field: str) -> Counter:
    data = dcdata._request(f"{layer}/query", {"where": where, "groupByFieldsForStatistics": field, "f": "json",
                                              "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}])}, post=True)
    out = Counter()
    for f in data.get("features", []):
        a = {k.lower(): v for k, v in f["attributes"].items()}
        out[a[field.lower()]] += a["n"]
    return out


class Proj:
    def __init__(self, bbox, width=640, pad=10):
        self.minx, self.miny, self.maxx, self.maxy = bbox
        self.k = math.cos(math.radians((self.miny + self.maxy) / 2))
        self.pad, self.w = pad, width
        self.s = (width - 2 * pad) / ((self.maxx - self.minx) * self.k)
        self.h = round((self.maxy - self.miny) * self.s + 2 * pad)

    def __call__(self, lon, lat):
        return self.pad + (lon - self.minx) * self.k * self.s, self.pad + (self.maxy - lat) * self.s


def path_d(proj, coords):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (proj(a, b) for a, b in coords))


def title_case(s: str) -> str:
    t = (s or "").title()
    t = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), t)
    return re.sub(r"(?<=\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1).lower(), t)


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
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    year_ago = now - 365 * DAY

    # 1. The block itself (DDOT Roadway Block).
    segs = q(ROADS, {"where": f"BLOCK_NAME LIKE '% BLOCK OF {STREET}' AND ADDRESS_RANGE_LOW >= {LOW} AND ADDRESS_RANGE_LOW < {LOW + 100}",
                     "outFields": "*", "returnGeometry": "true"})
    if not segs:
        raise RuntimeError("block not found in Roadway Block layer")
    seg = max(segs, key=lambda f: f["attributes"].get("LENGTH") or 0)
    a = seg["attributes"]
    line = [pt for p in seg["geometry"]["paths"] for pt in p]
    mid = line[len(line) // 2]
    line_geom = {"paths": seg["geometry"]["paths"], "spatialReference": {"wkid": 4326}}
    pt_geom = {"x": mid[0], "y": mid[1], "spatialReference": {"wkid": 4326}}

    # 2. Permits, last 12 months, by address on this block.
    permits = []
    for layer in yearly_layers("Building Permits in {year}", year_ago, now):
        for f in q(layer, {"where": f"FULL_ADDRESS LIKE '{str(LOW)[0]}__ {STREET_SHORT} NW%' AND {dcdata.date_where('ISSUE_DATE', year_ago)}",
                           "outFields": ",".join(PERMIT_FIELDS), "returnGeometry": "false", "orderByFields": "ISSUE_DATE DESC"}):
            r = f["attributes"]
            work = (r["DESC_OF_WORK"] or "").strip()
            if work.lower() in ("undefined", "null", "none", "n/a"):
                work = ""
            permits.append({"id": r["PERMIT_ID"], "issued": r["ISSUE_DATE"], "group": permit_group(r["PERMIT_TYPE_NAME"], r["PERMIT_SUBTYPE_NAME"], work),
                            "addr": title_case(re.sub(r",.*$", "", r["FULL_ADDRESS"] or "")), "work": work,
                            "lat": r["LATITUDE"], "lon": r["LONGITUDE"]})
    permits.sort(key=lambda p: -(p["issued"] or 0))
    pgroups = Counter(p["group"] for p in permits)

    # 3. 311, last 12 months, server-side counts by type (house numbers never leave DC's server).
    sr_where = (f"(STREETADDRESS LIKE '{str(LOW)[0]}__ {STREET}%' OR STREETADDRESS LIKE '{LOW} - {LOW + 99} BLOCK OF {STREET}%') "
                f"AND {dcdata.date_where('ADDDATE', year_ago)}")
    sr = Counter()
    sr_open = 0
    for layer in yearly_layers("311 City Service Requests in {year}", year_ago, now):
        sr.update(count_where(layer, sr_where, "SERVICECODEDESCRIPTION"))
        sr_open += sum(count_where(layer, f"{sr_where} AND SERVICEORDERSTATUS IN ('Open','In-Progress','In Progress')", "SERVICEORDERSTATUS").values())
    sr_total = sum(sr.values())

    # 4. Crashes within 150 m, last 3 years: counts only.
    crash_url = find_layer("Crashes in DC")
    three = now - 3 * 365 * DAY
    crashes = q(crash_url, {"where": dcdata.date_where("REPORTDATE", three), "returnGeometry": "false",
                            "outFields": "REPORTDATE,TOTAL_PEDESTRIANS,TOTAL_BICYCLES,MAJORINJURIES_PEDESTRIAN,MAJORINJURIES_BICYCLIST,MAJORINJURIES_DRIVER,MAJORINJURIESPASSENGER,FATAL_PEDESTRIAN,FATAL_BICYCLIST,FATAL_DRIVER,FATALPASSENGER,SPEEDING_INVOLVED",
                            **near(line_geom, "esriGeometryPolyline", CRASH_M)})
    cr = [c["attributes"] for c in crashes]
    by_year = Counter(time.gmtime(c["REPORTDATE"] / 1000).tm_year for c in cr if c["REPORTDATE"])
    ped = sum(1 for c in cr if (c["TOTAL_PEDESTRIANS"] or 0) > 0)
    bike = sum(1 for c in cr if (c["TOTAL_BICYCLES"] or 0) > 0)
    serious = sum(1 for c in cr if any((c[k] or 0) > 0 for k in ("MAJORINJURIES_PEDESTRIAN", "MAJORINJURIES_BICYCLIST", "MAJORINJURIES_DRIVER", "MAJORINJURIESPASSENGER",
                                                                 "FATAL_PEDESTRIAN", "FATAL_BICYCLIST", "FATAL_DRIVER", "FATALPASSENGER")))

    # 5. Street trees along the block.
    tree_url = find_layer("Urban Forestry Street Trees")
    trees = q(tree_url, {"where": "TBOX_STAT IN ('Plant','Open')", "outFields": "CMMN_NM,TBOX_STAT,CONDITION,DBH,DATE_PLANT", "returnGeometry": "true",
                         **near(line_geom, "esriGeometryPolyline", TREE_M)})
    planted = [t for t in trees if t["attributes"]["TBOX_STAT"] == "Plant"]
    empty_boxes = [t for t in trees if t["attributes"]["TBOX_STAT"] == "Open"]
    species = Counter((t["attributes"]["CMMN_NM"] or "Unknown").strip().title() for t in planted)
    cond = Counter((t["attributes"]["CONDITION"] or "Not rated") for t in planted)
    big = max((t["attributes"]["DBH"] or 0 for t in planted), default=0)

    # 6. ABC licensees nearby (public trade names; applicant names not requested).
    lic_url = find_layer("Alcohol License Business Locations")
    lic = q(lic_url, {"where": "STATUS='ACTIVE'", "outFields": "TRADE_NAME,TYPE,CLASS,ADDRESS", "returnGeometry": "true",
                      **near(pt_geom, "esriGeometryPoint", LIC_M)})

    # 7. Schools and SMD by point.
    schools = []
    for label, url in SCHOOL_LAYERS:
        rows = q(url, {"where": "1=1", "outFields": "NAME", "returnGeometry": "false", "geometry": json.dumps(pt_geom),
                       "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"})
        if rows:
            schools.append((label, rows[0]["attributes"]["NAME"]))
    smd = q(SMD_LAYER, {"where": "1=1", "outFields": "SMD_ID,ANC_ID,REP_NAME,WEB_URL", "returnGeometry": "false", "geometry": json.dumps(pt_geom),
                        "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"})
    smd_a = smd[0]["attributes"] if smd else {}

    # ---- Map: ~300 m around the block ----
    lon0, lat0 = mid
    dlat = 0.0024
    dlon = dlat / math.cos(math.radians(lat0)) * 1.5
    bbox = (lon0 - dlon, lat0 - dlat, lon0 + dlon, lat0 + dlat)
    proj = Proj(bbox)
    env = {"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3], "spatialReference": {"wkid": 4326}}
    roads = q(ROADS, {"where": "1=1", "outFields": "STREETNAME,STREETTYPE,DCFUNCTIONALCLASS,LENGTH", "returnGeometry": "true",
                      "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"})
    road_paths, labels, seen_lbl = [], [], set()
    for f in sorted(roads, key=lambda f: -(f["attributes"].get("LENGTH") or 0)):
        cls = f["attributes"].get("DCFUNCTIONALCLASS")
        for p in f["geometry"]["paths"]:
            road_paths.append(f'<path d="{path_d(proj, p)}" class="{"rM" if cls in (14, 16) else "rm"}"/>')
        nm = title_case(f"{f['attributes'].get('STREETNAME') or ''} {f['attributes'].get('STREETTYPE') or ''}".strip())
        if nm and nm not in seen_lbl:
            p = f["geometry"]["paths"][0]
            x, y = proj(*p[len(p) // 2])
            if 30 < x < proj.w - 50 and 15 < y < proj.h - 8:
                seen_lbl.add(nm)
                (x2, y2), (x1, y1) = proj(*p[-1]), proj(*p[0])
                ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
                if ang > 90:
                    ang -= 180
                if ang < -90:
                    ang += 180
                labels.append(f'<text x="{x:.0f}" y="{y:.0f}" transform="rotate({ang:.0f} {x:.0f} {y:.0f})" text-anchor="middle" dy="-4" class="lbl">{esc(nm)}</text>')
    hl = "".join(f'<path d="{path_d(proj, p)}" class="hl"/>' for p in seg["geometry"]["paths"])
    tree_dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3.5 if t["attributes"]["TBOX_STAT"] == "Plant" else 3}" class="{"tr" if t["attributes"]["TBOX_STAT"] == "Plant" else "tb"}"/>'
        for t in trees for x, y in [proj(t["geometry"]["x"], t["geometry"]["y"])])
    permit_dots = "".join(
        f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" class="pm"><title>{esc(p["addr"])}</title></rect>'
        for p in permits if p["lat"] and p["lon"] for x, y in [proj(p["lon"], p["lat"])])
    lic_dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="lc"><title>{esc(l["attributes"]["TRADE_NAME"] or "")}</title></circle>'
        for l in lic for x, y in [proj(l["geometry"]["x"], l["geometry"]["y"])] if 0 <= x <= proj.w and 0 <= y <= proj.h)
    radius_px = CRASH_M * proj.s / 111320
    cx, cy = proj(*mid)
    svg = (f'<svg viewBox="0 0 {proj.w} {proj.h}" class="map" role="img" aria-label="Map of the {BLOCK_TITLE}">'
           f'{"".join(road_paths)}<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius_px:.1f}" class="rad"/>{hl}{tree_dots}{permit_dots}{lic_dots}{"".join(labels)}</svg>')

    # ---- Sections ----
    from_to = f"between {title_case(a.get('FROMSTREET') or '?')} and {title_case(a.get('TOSTREET') or '?')}"
    pci = a.get("PCI_SCORE")
    pci_cat = (a.get("PCI_CONDCATEGORY") or "").title()
    pci_date = time.strftime("%b %Y", time.gmtime(a["PCI_LASTINSPECTED"] / 1000)) if a.get("PCI_LASTINSPECTED") else None
    speed = a.get("SPEEDLIMITS_IB") or a.get("SPEEDLIMITS_OB")
    facts = [
        ("Pavement condition", f"{pci_cat} ({pci:g}/100{', rated ' + pci_date if pci_date else ''})" if pci is not None else "Not rated"),
        ("Speed limit", f"{speed:g} mph" if speed else "Not listed"),
        ("Direction", "One-way" if (a.get("SUMMARYDIRECTION") or "").upper() in ("IB", "OB", "I", "O") else "Two-way" if a.get("SUMMARYDIRECTION") else "Not listed"),
        ("Parking lanes", str(a.get("TOTALPARKINGLANES") if a.get("TOTALPARKINGLANES") is not None else "Not listed")),
        ("Residential permit parking", f"Zone {a['PARKINGZONE_RPP']}" if a.get("PARKINGZONE_RPP") else ("Yes" if a.get("RPPSIDE") else "No")),
        ("Daily traffic", f"about {a['AADT']:,} vehicles ({a.get('AADT_YEAR') or 'year n/a'})" if a.get("AADT") else "Not counted (local street)"),
        ("Block length", f"{round((a.get('LENGTH') or 0) * 3.28084):,} ft" if a.get("LENGTH") else "Not listed"),
        ("Snow route", "Yes" if (a.get("SNOWROUTE_DPW") or "").upper() in ("Y", "YES") else "No"),
    ]
    facts_html = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in facts)

    def ago(ms):
        return re.sub(r"\b0(\d)", r"\1", time.strftime("%b %d, %Y", time.gmtime(ms / 1000))) if ms else ""

    trade = [p for p in permits if p["group"] == "Electrical, plumbing & mechanical"]
    shown_permits = [p for p in permits if p not in trade]
    trade_addrs = len({p["addr"] for p in trade})
    permit_rows = "".join(
        f"<tr><td>{ago(p['issued'])}</td><td>{esc(p['addr'])}</td><td>{esc(p['group'])}</td><td class='work'>{esc((p['work'] or '—')[:160])}{'…' if len(p['work']) > 160 else ''}</td><td>{esc(p['id'])}</td></tr>"
        for p in shown_permits[:25])
    sr_rows = "".join(f"<tr><td>{esc(t)}</td><td class='n'>{n}</td></tr>" for t, n in sr.most_common(8))
    years = sorted(by_year)
    crash_rows = "".join(f"<tr><td>{y}{' (so far)' if y == time.gmtime(now).tm_year else ' (from ' + time.strftime('%b', time.gmtime(three)) + ')' if y == time.gmtime(three).tm_year else ''}</td><td class='n'>{by_year[y]}</td></tr>" for y in years)
    species_li = "".join(f"<li>{esc(s)} <b>{n}</b></li>" for s, n in species.most_common(5))
    lic_li = "".join(
        f"<li><b>{esc(l['attributes']['TRADE_NAME'] or '')}</b> <span class='muted'>· {esc(l['attributes']['TYPE'] or '')} · {esc(title_case(l['attributes']['ADDRESS'] or ''))}</span></li>"
        for l in sorted(lic, key=lambda l: l["attributes"]["TRADE_NAME"] or "")[:12]) or "<li class='muted'>None within 250 m</li>"
    school_li = "".join(f"<li>{esc(lbl)}: <b>{esc(title_case(n))}</b></li>" for lbl, n in schools)

    body = f"""
<div class="grid">
  <div class="card stat"><b>{len(permits)}</b>building permits in the last 12 months</div>
  <div class="card stat"><b>{sr_total}</b>311 requests in the last 12 months</div>
  <div class="card stat"><b>{len(planted)}</b>street trees{f", plus {len(empty_boxes)} empty tree box{'es' if len(empty_boxes) != 1 else ''}" if empty_boxes else ""}</div>
  <div class="card stat"><b>{len(cr)}</b>reported crashes within {CRASH_M} m since {time.gmtime(three).tm_year}</div>
</div>

<section class="card">
  <h2>The block</h2>
  <p class="muted small" style="margin-top:0">{esc(title_case(STREET))}, {esc(from_to)}. Ward {esc(str(a.get('WARD_ID') or '4'))}, ANC {esc(str(smd_a.get('ANC_ID') or a.get('ANC_ID') or ''))}.</p>
  {svg}
  <p class="legend small"><span><i class="k hlk"></i>This block</span><span><i class="k trk"></i>Street tree</span><span><i class="k tbk"></i>Empty tree box</span><span><i class="k pmk"></i>Permit</span><span><i class="k lck"></i>ABC licensee</span><span><i class="k radk"></i>{CRASH_M} m</span></p>
  <dl class="facts">{facts_html}</dl>
</section>

<section class="card">
  <h2>Building permits, last 12 months</h2>
  <p class="muted small">{", ".join(f"{n} {g.lower()}" for g, n in pgroups.most_common()) or "None"}. {f" The {len(trade)} electrical, plumbing and mechanical permits cover {trade_addrs} houses and are summarized here rather than listed." if trade else ""} Other permits, newest first:</p>
  <div class="scroll"><table><thead><tr><th>Issued</th><th>Address</th><th>Kind</th><th>Work</th><th>Permit</th></tr></thead><tbody>{permit_rows or "<tr><td colspan=5>None besides trade permits</td></tr>"}</tbody></table></div>
</section>

<div class="two">
<section class="card">
  <h2>What neighbors report to 311</h2>
  <p class="muted small">Last 12 months. {sr_open} still open.</p>
  <div class="scroll"><table><thead><tr><th>Request type</th><th class="n">Count</th></tr></thead><tbody>{sr_rows}</tbody></table></div>
</section>
<section class="card">
  <h2>Street safety</h2>
  <p class="muted small">Reported crashes within {CRASH_M} m of the block (includes the corners), by year.</p>
  <div class="scroll"><table><thead><tr><th>Year</th><th class="n">Crashes</th></tr></thead><tbody>{crash_rows or "<tr><td colspan=2>None</td></tr>"}</tbody></table></div>
  <p class="small">{ped} involved a pedestrian, {bike} a bicyclist; {serious} had a major injury or death.</p>
</section>
</div>

<div class="two">
<section class="card">
  <h2>Trees</h2>
  <p class="small" style="margin-top:0">{len(planted)} trees in public tree boxes along this block{f"; the largest trunk is {big:g} inches across" if big else ""}.
  Condition: {", ".join(f"{n} {c.lower()}" for c, n in cond.most_common())}.</p>
  <ul class="tight">{species_li}</ul>
  {f'<p class="small">{len(empty_boxes)} empty box{"es" if len(empty_boxes) != 1 else ""} could be planted. <a href="https://caseytrees.org/">Request a tree</a> or call 311.</p>' if empty_boxes else ""}
</section>
<section class="card">
  <h2>Schools &amp; representation</h2>
  <p class="muted small" style="margin-top:0">DCPS in-boundary schools for the middle of the block. Check an exact address with DCPS's school finder.</p>
  <ul class="tight">{school_li}</ul>
  <p class="small">Commissioner for SMD {esc(smd_a.get('SMD_ID') or '')}: <b>{esc(title_case(smd_a.get('REP_NAME') or 'Vacant'))}</b>{f' · <a href="{esc(smd_a["WEB_URL"])}">ANC {esc(smd_a.get("ANC_ID") or "")}</a>' if smd_a.get("WEB_URL") else ""}</p>
  <p class="small"><b>Lead pipes:</b> look up each house's water service line on <a href="https://www.dcwater.com/service-line-materials-dashboard">DC Water's map</a>.</p>
</section>
</div>

<section class="card">
  <h2>Licensed to sell alcohol nearby</h2>
  <p class="muted small" style="margin-top:0">Active ABCA licensees within {LIC_M} m.</p>
  <ul class="tight lic">{lic_li}</ul>
</section>

<section class="card sponsor">
  <span class="label">Know your block</span>
  <p style="margin:.2rem 0 0">Every block in Petworth gets a page like this, rebuilt nightly. Share it with a new neighbor, or bring it to your next ANC meeting.
  Facts only: no ratings and no "best block" scores.</p>
</section>
"""
    extra_css = """
.small{font-size:.86rem}
.map{width:100%;height:auto;display:block;background:var(--soft);border-radius:8px}
.rm{fill:none;stroke:var(--line);stroke-width:5;stroke-linecap:round}
.rM{fill:none;stroke:var(--line);stroke-width:9;stroke-linecap:round}
.hl{fill:none;stroke:var(--brick);stroke-width:7;stroke-linecap:round;opacity:.85}
.rad{fill:none;stroke:var(--gold);stroke-width:1.2;stroke-dasharray:4 3}
.tr{fill:#3f8f4f;opacity:.85}.tb{fill:none;stroke:#3f8f4f;stroke-width:1.3}
.pm{fill:var(--accent);stroke:var(--card);stroke-width:1}
.lc{fill:#7a5bb5;stroke:var(--card);stroke-width:1}
svg text.lbl{font-size:10px;fill:var(--ink);paint-order:stroke;stroke:var(--soft);stroke-width:3px}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:5px}
.k{display:inline-block;width:12px;height:12px;border-radius:50%}
.hlk{background:var(--brick);border-radius:2px;height:5px}.trk{background:#3f8f4f}.tbk{border:1.5px solid #3f8f4f}
.pmk{background:var(--accent);border-radius:2px}.lck{background:#7a5bb5}.radk{border:1.5px dashed var(--gold)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px 16px;margin:12px 0 0}
.facts dt{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.facts dd{margin:0;font-weight:600}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 14px}
td.work{min-width:220px;font-size:.85rem}
td:first-child{white-space:nowrap}
ul.tight{margin:.3rem 0 0;padding-left:1.1rem}
ul.lic{columns:2 260px}
"""
    fields = {
        "IDEA_ID": "civic-data#9",
        "RANK": "7",
        "SCORE": "73.3",
        "SHORT_NAME": "Block Report Card",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "Petworth · Block Report Card",
        "HEADLINE": BLOCK_TITLE,
        "DECK": f"Everything public about one block {esc(from_to)}: permits, 311, street safety, trees, schools and who represents it.",
        "BODY": body,
        "EXTRA_CSS": extra_css,
        "PITCH": "A generated page for every block face that combines permits, 311, crashes, trees, liquor licenses, school boundaries and the SMD into one shareable 'know your block' card.",
        "WHATS_REAL": (f"Everything was pulled from Open Data DC on {pulled}: DDOT Roadway Block (street attributes and geometry), Building Permits (last 12 months, matched by address on the block), "
                       "311 City Service Requests (server-side counts by type, so house numbers never leave DC's server), Crashes in DC (counts within 150 m of the block line), "
                       "Urban Forestry Street Trees (within 15 m), ABCA licensee locations (within 250 m of mid-block; that layer is a periodic snapshot), "
                       "DCPS attendance zones and the 2023 SMD layer (point lookup at mid-block)."),
        "WHATS_MOCKED": ("Nothing in the data. Block choice (picked for having both permits and 311 activity) and the layout are design decisions. "
                         "Lead-pipe status is a link to DC Water, not ingested. Owner and applicant names, 311 details and crash report numbers are never requested; crashes are shown only as counts."),
        "NEXT_STEPS": ("Build one joined dataset per neighborhood in the nightly ingest, emit a static Astro page per Roadway Block segment, "
                       "add 'nearby blocks' links and sales history, and keep pages substantive enough to avoid looking like an SEO farm."),
        "SOURCES": ('<a href="https://opendata.dc.gov/">Open Data DC</a>: Roadway Block (DDOT), Building Permits (DOB), 311 City Service Requests (OUC), Crashes in DC (MPD/DDOT), '
                    'Urban Forestry Street Trees (DDOT UFD), Alcohol License Business Locations (ABCA), School Attendance Zones (DCPS), Single Member Districts 2023; CC BY 4.0'),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
    }
    OUT.write_text(render(fields), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(permits)} permits, {sr_total} 311, {len(cr)} crashes, {len(planted)} trees/{len(empty_boxes)} empty, {len(lic)} licensees, schools {schools}, smd {smd_a.get('SMD_ID')}")


if __name__ == "__main__":
    main()
