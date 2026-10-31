"""Demo #20: Street Tree Atlas & Empty-Box Finder (Petworth).

Pulls DDOT Urban Forestry street-tree records inside DC Health's PETWORTH planning
neighborhood and writes demos/ideas/20-street-tree-atlas.html.

Run from the repo root:  python demos/ideas/src/20_street_tree_atlas.py
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
from run import hundred_block  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "20-street-tree-atlas.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

BOUNDARY_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
BOUNDARY_WHERE = "DC_HPN_NAME='PETWORTH'"
TREES = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Urban_Tree_Canopy/MapServer/23"
# TREE_NOTES is free text written by arborists; we leave it out.
FIELDS = ["OBJECTID", "CMMN_NM", "SCI_NM", "GENUS_NAME", "DBH", "CONDITION", "TBOX_STAT", "VICINITY",
          "TBOX_L", "TBOX_W", "WIRES", "OWNERSHIP", "DATE_PLANT", "LAST_EDITED_DATE"]

GROUPS = [  # (key, label, colour, matcher on genus/common name)
    ("oak", "Oaks", "#8a6a1f", lambda g, c: g == "quercus" or "oak" in c),
    ("maple", "Maples", "#a2412b", lambda g, c: g == "acer" or "maple" in c),
    ("elm", "Elms & zelkovas", "#245c4f", lambda g, c: g in ("ulmus", "zelkova") or "elm" in c or "zelkova" in c),
    ("bloom", "Cherries, redbuds & crabapples", "#b5577f", lambda g, c: g in ("prunus", "cercis", "malus") or any(w in c for w in ("cherry", "redbud", "crabapple", "plum"))),
    ("other", "Everything else", "#6c7a89", lambda g, c: True),
]

DAY = 86400


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def group_of(r) -> str:
    g = (r.get("GENUS_NAME") or "").strip().lower()
    c = (r.get("CMMN_NM") or "").strip().lower()
    if not g and r.get("SCI_NM"):
        g = r["SCI_NM"].split()[0].lower()
    for key, _, _, match in GROUPS:
        if match(g, c):
            return key
    return "other"


def fetch_trees(geom: dict) -> list[dict]:
    """Page by OBJECTID order (stable) and keep point geometry for the map."""
    rows, offset = [], 0
    while True:
        data = dcdata._request(
            f"{TREES}/query",
            {
                "where": "1=1", "outFields": ",".join(FIELDS), "returnGeometry": "true",
                "orderByFields": "OBJECTID", "resultOffset": offset, "resultRecordCount": 2000, "f": "json",
                "geometry": json.dumps(geom), "geometryType": "esriGeometryPolygon", "inSR": 4326, "outSR": 4326,
                "spatialRel": "esriSpatialRelIntersects",
            },
            post=True,
        )
        feats = data.get("features", [])
        for f in feats:
            a = f["attributes"]
            g = f.get("geometry") or {}
            a["_x"], a["_y"] = g.get("x"), g.get("y")
            rows.append(a)
        if not data.get("exceededTransferLimit") or not feats:
            break
        offset += len(feats)
    return list({r["OBJECTID"]: r for r in rows}.values())


class Projector:
    def __init__(self, rings, width=760, pad=12):
        xs = [p[0] for r in rings for p in r]
        ys = [p[1] for r in rings for p in r]
        self.minx, self.maxx, self.miny, self.maxy = min(xs), max(xs), min(ys), max(ys)
        self.k = math.cos(math.radians((self.miny + self.maxy) / 2))
        self.pad = pad
        self.s = (width - 2 * pad) / ((self.maxx - self.minx) * self.k)
        self.w = width
        self.h = round((self.maxy - self.miny) * self.s + 2 * pad)

    def xy(self, lon, lat):
        return (round(self.pad + (lon - self.minx) * self.k * self.s, 1), round(self.pad + (self.maxy - lat) * self.s, 1))


def nice_date(ts: float) -> str:
    t = time.gmtime(ts)
    return f"{time.strftime('%b', t)} {t.tm_mday}, {t.tm_year}"


def title_addr(a: str | None) -> str:
    a = (a or "").strip()
    out = a.title()
    out = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), out)
    return re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), out).replace("Blk", "block")


def block_of(v: str | None) -> str:
    v = (v or "").strip()
    if not v:
        return "Location not listed"
    v = re.sub(r"^(OPP|REAR|NEAR|BEHIND)\s+", "", v, flags=re.I)
    m = re.match(r"^\s*(\d+)\s+BLK\s+(.*)$", v, re.I)
    if m:
        return title_addr(f"{int(m.group(1)) // 100 * 100} block of {m.group(2)}").replace("0 Block Of", "0 block of")
    v = re.sub(r"\s*\(.*?\)\s*", " ", v).strip()
    return title_addr(hundred_block(v)).replace(" Block Of ", " block of ")


def block_sort(kv):
    m = re.match(r"^(\d+|Unit) block of (.*)$", kv[0])
    return (m.group(2), 0 if m.group(1) == "Unit" else int(m.group(1))) if m else (kv[0], 0)


def main() -> int:
    now = time.time()
    geom = dcdata.boundary(BOUNDARY_LAYER, BOUNDARY_WHERE)
    rows = fetch_trees(geom)
    if len(rows) < 500:
        raise RuntimeError(f"only {len(rows)} tree records; refusing to write a thin page")
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))

    stat = Counter((r["TBOX_STAT"] or "Blank").strip() for r in rows)
    trees = [r for r in rows if (r["TBOX_STAT"] or "").strip() == "Plant"]
    live = [r for r in trees if (r["CONDITION"] or "") != "Dead"]
    dead = len(trees) - len(live)
    open_boxes = [r for r in rows if (r["TBOX_STAT"] or "").strip() == "Open"]
    proposed = stat.get("Proposed", 0)
    conflict = sum(n for k, n in stat.items() if k.startswith("Conflict") or k.startswith("Utility"))
    retired = stat.get("Retired", 0)

    named = [r for r in live if r["CMMN_NM"] and not r["CMMN_NM"].lower().startswith(("other", "unknown", "vacant"))]
    species = Counter(r["CMMN_NM"].strip() for r in named)
    groups = Counter(group_of(r) for r in live)
    planted_5y = sum(1 for r in live if r["DATE_PLANT"] and r["DATE_PLANT"] / 1000 > now - 5 * 365 * DAY)
    cond = Counter(r["CONDITION"] or "Not rated" for r in trees)
    last_edit = max((r["LAST_EDITED_DATE"] or 0) for r in rows) / 1000

    # ---- species bars
    top = species.most_common(12)
    maxn = top[0][1] if top else 1
    bars = "".join(
        f'<div class="bar"><span class="lbl">{esc(n)}</span><span class="track"><span style="width:{c / maxn * 100:.1f}%;background:{dict((k, col) for k, _, col, _ in GROUPS)[group_of({"CMMN_NM": n, "GENUS_NAME": ""})]}"></span></span><b>{c}</b></div>'
        for n, c in top
    )
    group_line = " · ".join(
        f'<span><i style="background:{col}"></i>{esc(lbl)} {groups[k]:,}</span>' for k, lbl, col, _ in GROUPS
    )
    species_card = f"""
<section class="card" id="species">
  <h2>What's growing on Petworth's sidewalks</h2>
  <p class="muted small">{len(species)} named species and varieties among {len(live):,} living street trees. Top 12:</p>
  <div class="bars">{bars}</div>
  <p class="legend">{group_line}</p>
</section>"""

    # ---- map
    pr = Projector(geom["rings"])
    colours = {k: col for k, _, col, _ in GROUPS}
    outline = " ".join("M" + " L".join(f"{x},{y}" for x, y in (pr.xy(*p) for p in r)) + " Z" for r in geom["rings"])
    dots = []
    for r in live:
        if r["_x"] is None:
            continue
        x, y = pr.xy(r["_x"], r["_y"])
        dots.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="{colours[group_of(r)]}"/>')
    rings = []
    for r in open_boxes:
        if r["_x"] is None:
            continue
        x, y = pr.xy(r["_x"], r["_y"])
        rings.append(f'<circle cx="{x}" cy="{y}" r="5" fill="none" stroke="var(--ink)" stroke-width="1.8"><title>Empty tree box: {esc(block_of(r["VICINITY"]))}</title></circle>')
    map_card = f"""
<section class="card" id="map">
  <h2>Every street tree, and the empty boxes</h2>
  <svg viewBox="0 0 {pr.w} {pr.h}" class="map" role="img" aria-label="Map of {len(dots):,} street trees and {len(rings)} empty tree boxes in Petworth">
    <path d="{outline}" fill="var(--soft)" stroke="var(--accent)" stroke-width="1.5"/>
    <g>{''.join(dots)}</g><g>{''.join(rings)}</g>
  </svg>
  <p class="legend">{group_line} · <span><i class="ring"></i>Empty box, ready to plant ({len(open_boxes)})</span></p>
  <p class="muted small">Boundary: DC Health planning neighborhood "Petworth". Dead trees are left off the map.</p>
</section>"""

    # ---- biggest trees
    big = sorted((r for r in live if r["DBH"] and 0 < r["DBH"] < 90), key=lambda r: -r["DBH"])[:15]
    big_rows = "".join(
        f'<tr><td class="n">{i}</td><td><b>{esc(r["CMMN_NM"] or "Unidentified")}</b><br><span class="muted small"><i>{esc(r["SCI_NM"] or "")}</i></span></td>'
        f'<td>{esc(block_of(r["VICINITY"]))}</td><td class="n">{r["DBH"]:.0f}″</td><td class="n">{math.pi * r["DBH"] / 12:.1f} ft</td><td>{esc(r["CONDITION"] or "Not rated")}</td></tr>'
        for i, r in enumerate(big, 1)
    )
    big_card = f"""
<section class="card" id="giants">
  <h2>The neighborhood's 15 biggest street trees</h2>
  <div class="scroll"><table>
    <thead><tr><th class="n">#</th><th>Species</th><th>Where</th><th class="n">Trunk width</th><th class="n">Around</th><th>Condition</th></tr></thead>
    <tbody>{big_rows}</tbody>
  </table></div>
  <p class="muted small">Trunk width is diameter at breast height (4.5 ft up), as measured by DDOT's Urban Forestry Division; "around" is the matching circumference. Locations are rounded to the hundred block.</p>
</section>"""

    # ---- empty boxes
    by_block = Counter(block_of(r["VICINITY"]) for r in open_boxes)
    wires = Counter((r["WIRES"] or "Unknown") for r in open_boxes)
    under_wires = sum(n for w, n in wires.items() if w not in ("None", "Unknown"))
    box_rows = "".join(
        f"<tr><td>{esc(b)}</td><td class='n'>{n}</td></tr>" for b, n in sorted(by_block.items(), key=block_sort)[:50]
    )
    box_card = f"""
<section class="card" id="empty-boxes">
  <h2>Empty tree boxes: {len(open_boxes)} spots waiting for a tree</h2>
  <p>Yes, the city's dataset tracks empty boxes. Each record has a tree-box status, and in Petworth it reads:
  <b>{stat.get('Plant', 0):,}</b> planted, <b>{len(open_boxes)}</b> "Open" (an empty box), <b>{proposed}</b> "Proposed" (a planting the city has scheduled),
  <b>{conflict}</b> "Conflict" (empty but blocked, often by a utility line or a stump that has to rot first) and <b>{retired}</b> "Retired" (a box taken out of service).</p>
  <p><a class="cta" href="https://311.dc.gov/">Ask for a free street tree on 311 →</a><br><span class="muted small">Choose the "Tree Planting" request type. DDOT plants street trees in public space at no cost to residents. You can also see the official map at <a href="https://trees.dc.gov/">trees.dc.gov</a>.</span></p>
  <div class="scroll"><table>
    <thead><tr><th>Block</th><th class="n">Empty boxes</th></tr></thead>
    <tbody>{box_rows}</tbody>
  </table></div>
  <p class="muted small">{under_wires} of the {len(open_boxes)} open boxes sit under overhead wires, which limits DDOT to smaller species there. Box addresses are rounded to the hundred block.</p>
</section>"""

    health = " · ".join(f"{k} {n:,}" for k, n in cond.most_common())
    stats = f"""
<section class="grid" aria-label="Headline numbers">
  <div class="card stat"><b>{len(live):,}</b>living street trees</div>
  <div class="card stat"><b>{len(species)}</b>species &amp; varieties</div>
  <div class="card stat"><b>{planted_5y:,}</b>planted in the last 5 years</div>
  <div class="card stat"><b>{len(open_boxes)}</b>empty boxes ready to plant</div>
</section>
<p class="muted small">Condition of trees in boxes, per DDOT's last inspection: {health}. {dead} are recorded as dead and waiting for removal.</p>"""

    body = f"""
{stats}
{map_card}
{species_card}
{big_card}
{box_card}
<section class="card sponsor"><span class="label">Presented by</span><br><b>[Sponsor name]</b>: a local garden center could sponsor the spring "what's blooming" page.</section>
"""

    extra_css = """
.map{width:100%;height:auto;display:block}
.small{font-size:.84rem}
.legend{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.84rem;margin:.6rem 0 .2rem}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.legend i.ring{background:none;border:2px solid var(--ink)}
.bars{display:grid;gap:5px}
.bar{display:grid;grid-template-columns:minmax(0,9.5rem) 1fr 2.6rem;gap:8px;align-items:center;font-size:.9rem}
.bar .lbl{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar .track{background:var(--soft);border-radius:3px;height:12px;overflow:hidden}
.bar .track span{display:block;height:100%;border-radius:3px}
.bar b{text-align:right;font-variant-numeric:tabular-nums}
.cta{display:inline-block;font-weight:700;background:var(--accent);color:var(--card);text-decoration:none;border-radius:8px;padding:8px 14px;margin:.2rem 0 .3rem}
"""

    fill = {
        "IDEA_ID": "civic-data#8",
        "RANK": "20",
        "SCORE": "68.5",
        "SHORT_NAME": "Petworth Street Tree Atlas",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "Petworth · Street trees",
        "HEADLINE": f"{len(live):,} street trees, and {len(open_boxes)} empty boxes waiting for one",
        "DECK": f"Every public street tree in Petworth from DDOT's Urban Forestry inventory: species, size, health and the open tree boxes you can ask the city to fill. Inventory last edited {nice_date(last_edit)}.",
        "BODY": body,
        "PITCH": "Every public street tree in the neighborhood, with species, size and health, plus a finder for empty tree boxes where residents can request a free DDOT planting.",
        "WHATS_REAL": (
            f"All counts, the species chart, the biggest-trees table, the map and the empty-box list come from DDOT's Urban Forestry Street Trees layer, "
            f"queried live inside the Petworth boundary on {pulled} ({len(rows):,} records). The empty-box finding is from the layer's own tree-box status field (TBOX_STAT)."
        ),
        "WHATS_MOCKED": (
            "Only the sponsor slot. Our reading of the status values (Open = empty and plantable, Proposed = scheduled, Conflict = blocked) is from the values and their notes, "
            "not from a published DDOT data dictionary, so treat it as our interpretation. Arborist notes are not shown."
        ),
        "NEXT_STEPS": (
            "Add the Street Tree Archive to show plantings and removals per year since 2014, a species filter on the map, a per-street \"biggest oak\" page, "
            "and a seasonal \"what's blooming\" page from species bloom months. Refresh monthly."
        ),
        "SOURCES": (
            '<a href="https://catalog.data.gov/dataset/urban-forestry-street-trees">Urban Forestry Street Trees (DDOT)</a>, '
            "DC Health Planning Neighborhoods; Open Data DC, CC BY 4.0"
        ),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    }
    page = render(fill)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} records, {len(live)} living trees, {len(open_boxes)} open boxes, {len(page)//1024} KB")
    return 0


def render(fill: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    tpl = re.sub(r"<!--\s*Template for idea demos.*?-->\s*", "", tpl, flags=re.S)
    for k, v in fill.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", tpl)
    if left:
        raise RuntimeError(f"unfilled placeholders: {sorted(set(left))}")
    return tpl


if __name__ == "__main__":
    sys.exit(main())
