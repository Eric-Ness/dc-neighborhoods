"""Demo #2 (culture-content#1): a "biography" page for one building.

    python demos/ideas/src/02_building_biography.py

Pulls, live:
  - the building's original-permit record from DC HPO HistoryQuest (Historic Data on DC Buildings)
  - neighbouring HistoryQuest footprints, for a construction-era map of the block
  - other buildings by the same architect and builder (citywide counts + a short list)
  - historic district / landmark overlap (Open Data DC)
  - current building permits at the address (Open Data DC, last three calendar years)
Historic owner names are never requested.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "02-building-biography.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

HISTORIC = "https://services.arcgis.com/neT9SoYxizqTHZPH/arcgis/rest/services/DC_HistoricalBuildings2017/FeatureServer/0"
DISTRICTS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Historic_WebMercator/MapServer/6"
LANDMARKS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Planning_Landuse_and_Zoning_WebMercator/MapServer/23"

HQ_ADDRESS = "4920 43RD PLACE NW"
PERMIT_PREFIX = "4920 43RD PL NW"
NEIGHBORHOOD = "Tenleytown"
# Fields we ask HistoryQuest for. "Owner" is deliberately absent.
HQ_FIELDS = [
    "FULLADDRES", "Square", "Lot", "Date", "MapYear", "PermitNumber", "MicrofilmRoll", "Architect", "Builder",
    "EstimatedCost", "Material", "FrontMaterial", "FoundationMaterial", "StoneType", "RoofType", "RoofMaterial",
    "Heat", "Rooms", "Width", "Depth", "Stories", "Number_of_Families", "Purpose", "House_Type", "Quantity", "Extant",
]
PERMIT_FIELDS = ["PERMIT_ID", "ISSUE_DATE", "PERMIT_TYPE_NAME", "PERMIT_SUBTYPE_NAME", "DESC_OF_WORK", "ZONING"]

e = html.escape


def hq_date(ms):
    """HistoryQuest stores pre-1970 dates as negative epoch ms, which time.gmtime rejects on Windows."""
    if ms is None:
        return None
    return datetime(1970, 1, 1) + timedelta(milliseconds=ms)


def person(name: str | None) -> str:
    """'Finelli, R. W.' -> 'R. W. Finelli'. Company names pass through."""
    name = (name or "").strip()
    m = re.match(r"^([A-Z][A-Za-z'\-]+), ([A-Z]\.(?: ?[A-Z]\.)*)(, Jr\.)?$", name)
    return f"{m.group(2)} {m.group(1)}{m.group(3) or ''}" if m else name


def tc(s: str) -> str:
    t = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(0).upper(), (s or "").title())
    return re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), t)


def sql(s: str) -> str:
    return s.replace("'", "''")


def fetch_building() -> tuple[dict, list]:
    data = dcdata._request(
        f"{HISTORIC}/query",
        {"where": f"FULLADDRES = '{HQ_ADDRESS}'", "outFields": ",".join(HQ_FIELDS), "returnGeometry": "true", "outSR": 4326, "f": "json"},
    )
    feats = data["features"]
    if not feats:
        raise RuntimeError(f"no HistoryQuest record for {HQ_ADDRESS}")
    return feats[0]["attributes"], feats[0]["geometry"]["rings"]


def fetch_neighbors(cx: float, cy: float) -> list[dict]:
    dx, dy = 0.0016, 0.0011  # roughly 140 m x 120 m around the house
    env = {"xmin": cx - dx, "ymin": cy - dy, "xmax": cx + dx, "ymax": cy + dy, "spatialReference": {"wkid": 4326}}
    out, offset = [], 0
    while True:
        data = dcdata._request(
            f"{HISTORIC}/query",
            {
                "where": "1=1", "outFields": "FULLADDRES,Date,Extant", "returnGeometry": "true", "outSR": 4326,
                "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects", "resultOffset": offset, "f": "json",
            },
            post=True,
        )
        out += data.get("features", [])
        if not data.get("exceededTransferLimit") or not data.get("features"):
            return out
        offset += len(data["features"])


def same_maker(field: str, value: str) -> tuple[int, list[dict]]:
    where = f"{field} = '{sql(value)}'"
    n = dcdata._request(f"{HISTORIC}/query", {"where": where, "returnCountOnly": "true", "f": "json"})["count"]
    rows = dcdata._request(
        f"{HISTORIC}/query",
        {"where": where, "outFields": "FULLADDRES,Date,Purpose,Material", "orderByFields": "Date", "resultRecordCount": 40, "f": "json"},
    )["features"]
    return n, [r["attributes"] for r in rows]


def overlaps(layer: str, x: float, y: float) -> list[str]:
    data = dcdata._request(
        f"{layer}/query",
        {
            "where": "1=1", "outFields": "NAME", "returnGeometry": "false",
            "geometry": json.dumps({"x": x, "y": y, "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "f": "json",
        },
    )
    return [f["attributes"]["NAME"] for f in data.get("features", [])]


def fetch_permits(now: float) -> list[dict]:
    year = time.gmtime(now).tm_year
    rows = []
    for y in (year - 2, year - 1, year):
        layer = dcdata.resolve_yearly_layer("Building Permits in {year}", y)
        if layer:
            rows += dcdata._request(
                f"{layer}/query",
                {"where": f"FULL_ADDRESS LIKE '{PERMIT_PREFIX}%'", "outFields": ",".join(PERMIT_FIELDS), "f": "json"},
            )["features"]
    permits = [r["attributes"] for r in rows]
    permits.sort(key=lambda p: p["ISSUE_DATE"] or 0, reverse=True)
    return permits


# ---------------------------------------------------------------- drawing

ERAS = [
    ("before 1910", 0, 1909, "var(--era1)"),
    ("1910s", 1910, 1919, "var(--era2)"),
    ("1920s", 1920, 1929, "var(--era3)"),
    ("1930s", 1930, 1939, "var(--era4)"),
    ("1940s", 1940, 1949, "var(--era5)"),
]


def era_of(year: int | None):
    if year is None:
        return None
    for era in ERAS:
        if era[1] <= year <= era[2]:
            return era
    return None


def block_map(target_rings: list, neighbors: list, cx: float, cy: float) -> tuple[str, Counter]:
    import math

    W, H = 640, 420
    kx = math.cos(math.radians(cy))
    dx, dy = 0.0016, 0.0011
    sx = W / (2 * dx * kx)
    sy = H / (2 * dy)
    s = min(sx, sy)

    def pt(lon, lat):
        return (W / 2 + (lon - cx) * kx * s, H / 2 - (lat - cy) * s)

    def path(rings):
        d = ""
        for ring in rings:
            pts = [pt(*p) for p in ring]
            d += "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
        return d

    counts: Counter = Counter()
    shapes = []
    for f in neighbors:
        a = f["attributes"]
        if (a.get("FULLADDRES") or "").strip().upper() == HQ_ADDRESS:
            continue
        y = hq_date(a.get("Date")).year if a.get("Date") is not None else None
        era = era_of(y)
        counts[era[0] if era else "no permit year"] += 1
        fill = era[3] if era else "var(--era0)"
        title = f"{tc(a.get('FULLADDRES') or '')}: {y or 'year not recorded'}"
        shapes.append(f'<path d="{path(f["geometry"]["rings"])}" fill="{fill}" stroke="var(--card)" stroke-width=".6"><title>{e(title)}</title></path>')
    target = f'<path d="{path(target_rings)}" fill="var(--brick)" stroke="var(--ink)" stroke-width="2"><title>{e(tc(HQ_ADDRESS))}</title></path>'
    tx, ty = pt(*target_rings[0][0])
    label = f'<text x="{tx + 10:.0f}" y="{ty - 8:.0f}" style="fill:var(--ink);font-weight:700;font-size:13px">{HQ_ADDRESS.split()[0]}</text>'
    scale_m = 50
    px = scale_m / 111320 * s  # metres -> degrees lat -> px
    bar = (f'<g transform="translate(16,{H - 18})"><rect width="{px:.0f}" height="4" fill="var(--muted)"/>'
           f'<text x="{px + 6:.0f}" y="5">{scale_m} m</text></g>'
           f'<text x="{W - 16}" y="20" text-anchor="end">N ↑</text>')
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Map of buildings around {e(tc(HQ_ADDRESS))}, shaded by construction decade" '
           f'style="width:100%;height:auto;background:var(--soft);border-radius:8px">{"".join(shapes)}{target}{label}{bar}</svg>')
    return svg, counts


# ---------------------------------------------------------------- page

def render(fields: dict) -> str:
    out = TEMPLATE.read_text(encoding="utf-8")
    out = re.sub(r"<!--.*?-->\n", "", out, count=1, flags=re.S)
    for k, v in fields.items():
        out = out.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        raise RuntimeError(f"unfilled placeholders: {left}")
    return out


def main() -> None:
    now = time.time()
    today = time.strftime("%Y-%m-%d", time.gmtime(now))
    b, rings = fetch_building()
    ring = rings[0]
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    neighbors = fetch_neighbors(cx, cy)
    arch_n, arch_rows = same_maker("Architect", b["Architect"])
    build_n, build_rows = same_maker("Builder", b["Builder"])
    districts = overlaps(DISTRICTS, cx, cy)
    landmarks = overlaps(LANDMARKS, cx, cy)
    permits = fetch_permits(now)
    print(f"HistoryQuest record ok; {len(neighbors)} nearby footprints; architect {arch_n}, builder {build_n}; "
          f"{len(permits)} permits; districts {districts}; landmarks {landmarks}")

    built = hq_date(b["Date"])
    year = built.year if built else None
    built_txt = f"{built:%B} {built.day}, {built.year}" if built else "date not recorded"
    cost = int(b["EstimatedCost"]) if (b["EstimatedCost"] or "").isdigit() else None
    arch, builder = person(b["Architect"]), person(b["Builder"])
    stone = (b.get("StoneType") or "").replace("soft grnt", "soft granite")
    size = f"{b['Width']} × {b['Depth']} ft" if b.get("Width") and b.get("Depth") else "not recorded"

    svg, era_counts = block_map(rings, neighbors, cx, cy)
    nearby_total = sum(era_counts.values())
    same_decade = era_counts.get(era_of(year)[0], 0) if era_of(year) else 0
    legend = "".join(
        f'<span class="key"><i style="background:{fill}"></i>{label} <b>{era_counts.get(label, 0)}</b></span>' for label, _, _, fill in ERAS
    ) + f'<span class="key"><i style="background:var(--era0)"></i>no permit year <b>{era_counts.get("no permit year", 0)}</b></span>' \
      + '<span class="key"><i style="background:var(--brick)"></i>this house</span>'

    def maker_rows(rows):
        items = []
        for r in rows:
            if (r["FULLADDRES"] or "").strip().upper() == HQ_ADDRESS:
                continue
            y = hq_date(r["Date"]).year if r["Date"] is not None else ""
            items.append(f"<li><b>{e(tc(r['FULLADDRES'] or ''))}</b> <span class='muted'>· {y} · {e((r['Purpose'] or '').lower())} · {e(r['Material'] or '')}</span></li>")
            if len(items) == 8:
                break
        return "".join(items) or "<li class='muted'>No other records.</li>"

    def permit_li(p):
        when = time.strftime("%b %d, %Y", time.gmtime(p["ISSUE_DATE"] / 1000)) if p["ISSUE_DATE"] else ""
        kind = tc(p["PERMIT_SUBTYPE_NAME"] or p["PERMIT_TYPE_NAME"] or "")
        work = re.sub(r"\s+", " ", (p["DESC_OF_WORK"] or "").strip())
        if work.lower() in ("", "none", "null", "undefined", "n/a"):
            work = ""
        work = work[:320] + ("…" if len(work) > 320 else "")
        return (f"<li><span class='when'>{e(when)}</span><b>{e(kind)}</b> <span class='muted'>({e(tc(p['PERMIT_TYPE_NAME'] or ''))} · {e(p['PERMIT_ID'])})</span>"
                + (f"<br><span class='work'>{e(work)}</span>" if work else "") + "</li>")

    big = [p for p in permits if (p["PERMIT_TYPE_NAME"] or "").upper() == "CONSTRUCTION"]
    trades = Counter(tc(p["PERMIT_SUBTYPE_NAME"] or "") for p in permits if (p["PERMIT_TYPE_NAME"] or "").upper() != "CONSTRUCTION")
    headline_now = (
        "Addition permitted" if any("ADDITION" in (p["DESC_OF_WORK"] or "").upper() for p in big)
        else ("Construction permit on file" if big else "No major construction permits")
    )
    status_bits = []
    status_bits.append(f"Historic district: {e(', '.join(districts))}" if districts else "Not inside a DC historic district")
    status_bits.append(f"Landmark: {e(', '.join(landmarks))}" if landmarks else "Not a designated landmark")

    story = (
        f"{e(tc(HQ_ADDRESS))} was permitted in {year}. "
        f"The original permit (No. {e(b['PermitNumber'])}, issued {e(built_txt)}) names <b>{e(arch)}</b> as architect and "
        f"<b>{e(builder)}</b> as builder, and estimates the cost at <b>${cost:,}</b>. "
        f"It describes a {e((b['House_Type'] or '').lower())} {e((b['Purpose'] or '').lower())} of {e(b['Material'] or '')}"
        + (f" ({e(stone)})" if stone else "") +
        f", {b['Rooms']} rooms, on a {e((b['FoundationMaterial'] or '').lower())} foundation under a {e((b['RoofMaterial'] or '').lower())} "
        f"{e((b['RoofType'] or '').lower())} roof, heated by {e((b['Heat'] or '').lower())}. "
        f"Of the {nearby_total} other buildings mapped around it, {same_decade} date from the same decade."
    )

    sanborn = "https://www.loc.gov/collections/sanborn-maps/?fa=location:district+of+columbia"
    hq_link = "https://opendata.dc.gov/datasets/DCGIS::historic-data-on-dc-buildings"
    permit_link = "https://opendata.dc.gov/search?q=building%20permits"

    body = f"""
<div class="card hero">
  <div class="facts grid">
    <div class="stat"><span class="muted">Built</span><b>{year}</b>permit {e(built_txt)}</div>
    <div class="stat"><span class="muted">Architect</span><b class="nm">{e(arch)}</b>{arch_n:,} DC permits on record</div>
    <div class="stat"><span class="muted">Builder</span><b class="nm">{e(builder)}</b>{build_n:,} DC permits on record</div>
    <div class="stat"><span class="muted">Est. cost then</span><b>${cost:,}</b>as written on the permit</div>
  </div>
  <p class="chips"><span class="chip">{e(b['Material'] or '').capitalize()}{' · ' + e(stone) if stone else ''}</span><span class="chip">{e(b['House_Type'] or '')}</span><span class="chip">{b['Rooms']} rooms</span><span class="chip">{e(size)} footprint</span><span class="chip">Square {e(b['Square'])}, lot {e(b['Lot'])}</span>{''.join(f'<span class="chip">{s}</span>' for s in status_bits)}</p>
</div>

<section class="card">
  <h2>The house's story</h2>
  <p>{story}</p>
  <p class="muted small">Drafted automatically from the permit record; in the product an editor checks each draft before it goes live. Original owners' names are left out on purpose.</p>
</section>

<section class="card">
  <h2>As built: the original permit</h2>
  <div class="scroll"><table class="kv">
    <tr><th>Permit</th><td>No. {e(b['PermitNumber'])} · microfilm roll {e(b['MicrofilmRoll'] or '')}</td></tr>
    <tr><th>Issued</th><td>{e(built_txt)}</td></tr>
    <tr><th>Use</th><td>{e((b['Purpose'] or '').capitalize())}{f", {b['Number_of_Families']} family" if b['Number_of_Families'] else ''}</td></tr>
    <tr><th>Walls</th><td>{e(b['Material'] or '')}{'; front ' + e(b['FrontMaterial']) if b['FrontMaterial'] else ''}{'; ' + e(stone) if stone else ''}</td></tr>
    <tr><th>Foundation</th><td>{e(b['FoundationMaterial'] or '')}</td></tr>
    <tr><th>Roof</th><td>{e(b['RoofType'] or '')}, {e(b['RoofMaterial'] or '')}</td></tr>
    <tr><th>Heat</th><td>{e(b['Heat'] or '')}</td></tr>
    <tr><th>Size</th><td>{e(size)}, {b['Rooms']} rooms</td></tr>
  </table></div>
  <p class="muted small">Source: DC Historic Preservation Office, <a href="{hq_link}">Historic Data on DC Buildings</a> (HistoryQuest, CC BY 4.0). HistoryQuest transcribes the city's original building permits (1877–1949); spellings are as written.</p>
</section>

<section class="card">
  <h2>Its neighbors, by decade built</h2>
  {svg}
  <p class="legend">{legend}</p>
  <p class="muted small">Building footprints from HistoryQuest within about 150 m. Hover over a shape for its address and year. Grey shapes have no original-permit year on file (often post-1949 or unmatched).</p>
</section>

<section class="card">
  <h2>Now: permits at this address</h2>
  <p class="nowline"><b>{e(headline_now)}</b> · {len(permits)} permits since January {time.gmtime(now).tm_year - 2}{' (' + ', '.join(f'{n} {k.lower()}' for k, n in trades.most_common()) + ')' if trades else ''}.</p>
  <ul class="permits">{''.join(permit_li(p) for p in permits[:20]) or '<li>No permits since then.</li>'}</ul>
  <p class="muted small">Source: Open Data DC, <a href="{permit_link}">Building Permits</a> by year (DOB, CC BY 4.0). Applicant and owner fields are never requested.</p>
</section>

<div class="grid two">
<section class="card">
  <h2>More by {e(arch)}</h2>
  <p class="muted small">{arch_n:,} buildings citywide name this architect. Earliest first:</p>
  <ul class="tight">{maker_rows(arch_rows)}</ul>
</section>
<section class="card">
  <h2>More by {e(builder)}</h2>
  <p class="muted small">{build_n:,} buildings citywide name this builder. Earliest first:</p>
  <ul class="tight">{maker_rows(build_rows)}</ul>
</section>
</div>

<section class="card">
  <h2>See it on the old fire-insurance maps</h2>
  <p>Sanborn Company maps drew every building's outline, material and number of stories. The Library of Congress has the Washington volumes online, free and public domain. Look for square {e(b['Square'])} in the volume covering this part of {NEIGHBORHOOD}.</p>
  <p><a class="btn" href="{sanborn}">Browse DC Sanborn maps at the Library of Congress →</a></p>
</section>

<div class="card sponsor"><div class="label">Sponsor</div><b>[Sponsor name]</b>, a local real-estate or restoration business. One labeled slot on each building page; the history stays neutral.</div>

<section class="card"><h2>Know more about this house?</h2><p>Old photos, a renovation date, a correction to the permit transcription? <span class="btn ghost" aria-disabled="true">Suggest an edit</span> <span class="muted small">(button is inert in this demo)</span></p></section>
"""

    extra_css = """
:root{--era0:#cfd4cc;--era1:#d9c7a7;--era2:#c99b6a;--era3:#a8673f;--era4:#7c4a37;--era5:#4f3a33}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--era0:#39413c;--era1:#6d5f45;--era2:#8a6a46;--era3:#b07a52;--era4:#cf9f7c;--era5:#ecc9ad}}
:root[data-theme=dark]{--era0:#39413c;--era1:#6d5f45;--era2:#8a6a46;--era3:#b07a52;--era4:#cf9f7c;--era5:#ecc9ad}
.hero .stat span{display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em}
.hero .stat{font-size:.85rem;color:var(--muted)}
.hero .stat b{color:var(--ink)}.hero .stat b.nm{font-size:1.15rem;line-height:1.3;padding:.3rem 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0}
.chip{font-size:.8rem;background:var(--soft);border:1px solid var(--line);border-radius:999px;padding:2px 10px}
.small{font-size:.84rem}
table.kv th{width:7.5rem;text-transform:none;letter-spacing:0;font-size:.85rem}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.82rem;color:var(--muted);margin:.6rem 0 0}
.key i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:-1px;border:1px solid var(--line)}
.permits{list-style:none;padding:0;margin:.4rem 0}.permits li{padding:.55rem 0;border-bottom:1px solid var(--line)}
.permits .when{display:inline-block;min-width:7.2rem;font-variant-numeric:tabular-nums;color:var(--muted);font-size:.86rem}
.permits .work{font-size:.88rem}
.nowline{margin:.2rem 0 .4rem}
.tight{padding-left:1.1rem;margin:.3rem 0}.tight li{margin:.25rem 0;font-size:.92rem}
.two{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}.two .card{margin:0}
.btn{display:inline-block;background:var(--accent);color:var(--card);padding:.45rem .9rem;border-radius:8px;text-decoration:none;font-weight:600}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
"""

    page = render({
        "IDEA_ID": "culture-content#1",
        "RANK": "2",
        "SCORE": "79.4",
        "SHORT_NAME": f"{tc(HQ_ADDRESS)}: building biography",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC + DC HPO · pulled {today}",
        "EYEBROW": f"{NEIGHBORHOOD} · Building biography",
        "HEADLINE": e(tc(HQ_ADDRESS)),
        "DECK": e(f"A {b['Material']} house from {year}, designed by {arch} and built by {builder}. What the original permit says, who else they built for, and what is being done to it now."),
        "BODY": body,
        "PITCH": "A permanent page for every pre-1950 building in the neighborhood: who designed and built it, what it cost, what it was made of, its block's construction history, and today's permits. Pages like this rank for address searches and need almost no upkeep.",
        "WHATS_REAL": f"Everything on the page was queried by the generator on {today}: the HistoryQuest permit record and nearby footprints, citywide architect and builder counts, the historic-district and landmark check, and DOB building permits at the address. The story paragraph is filled in from those fields by a template.",
        "WHATS_MOCKED": "The sponsor slot and the \"Suggest an edit\" button. The page links to the Sanborn collection rather than embedding a cropped, georeferenced sheet of this exact block, which would need manual georeferencing.",
        "NEXT_STEPS": "Generate one page per HistoryQuest address in each neighborhood (Tenleytown alone has about 4,000 records with architect, builder, cost and material). Match permits by normalized address. Add Sanborn sheet crops once sheets are georeferenced (Allmaps or QGIS), a correction queue, and block pages that link to each house.",
        "SOURCES": f'<a href="{hq_link}">DC HPO Historic Data on DC Buildings (HistoryQuest, CC BY 4.0)</a>; Open Data DC Building Permits, Historic Districts and Historic Landmarks (CC BY 4.0); <a href="{sanborn}">Library of Congress Sanborn Maps</a> (public domain)',
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    })
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({len(page.encode()) // 1024} KB)")


if __name__ == "__main__":
    main()
