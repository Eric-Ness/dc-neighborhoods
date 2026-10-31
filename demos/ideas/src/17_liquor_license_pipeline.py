"""Demo #17: Liquor License & Nightlife Pipeline (Adams Morgan).

Pulls ABCA liquor licensees and license cancellations inside DC Health's
ADAMS MORGAN planning neighborhood and writes demos/ideas/17-liquor-license-pipeline.html.

Run from the repo root:  python demos/ideas/src/17_liquor_license_pipeline.py
"""

from __future__ import annotations

import html
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "17-liquor-license-pipeline.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

BOUNDARY_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
BOUNDARY_WHERE = "DC_HPN_NAME='ADAMS MORGAN'"
LIC_BASE = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer"
LICENSES = f"{LIC_BASE}/5"
CANCELLATIONS = f"{LIC_BASE}/42"
MORATORIUM = f"{LIC_BASE}/35"

# Applicant (owner) names exist in both ABCA layers; we never request them.
LIC_FIELDS = [
    "LICENSE", "TRADE_NAME", "CLASS", "TYPE", "STATUS", "ADDRESS", "ENTERTAINMENT", "DANCING",
    "COVERCHARGE", "SIDEWALK_CAFE", "SUMMER_GARDEN", "TOTAL_CAPACITY", "EXPIRATION_DATE", "EDITED",
    "LATITUDE", "LONGITUDE",
]
CAN_FIELDS = ["LICENSE", "TRADE_NAME", "CLASS", "TYPE", "ADDRESS", "CANCELLATION_DATE", "REASON", "EDITED", "LATITUDE", "LONGITUDE"]

CLASS_GLOSS = {
    "A": "Liquor store: beer, wine and spirits to take home",
    "B": "Grocery or corner store: beer and wine to take home",
    "C": "Restaurant, tavern, nightclub, hotel or club: beer, wine and spirits served on site",
    "D": "Restaurant or tavern: beer and wine only, served on site",
    "Caterer": "Caterer: serves at events",
}

CATS = [
    ("bar", "Bars & nightclubs", "var(--brick)"),
    ("rest", "Restaurants", "var(--accent)"),
    ("store", "Stores", "var(--gold)"),
    ("other", "Hotels, clubs & other", "var(--muted)"),
]


def category(t: str | None) -> str:
    t = (t or "").lower()
    if t in ("tavern", "nightclub"):
        return "bar"
    if t == "restaurant":
        return "rest"
    if t.startswith("retail"):
        return "store"
    return "other"


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def day(ms: float | None) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ms / 1000)) if ms else ""


def nice_date(ms: float) -> str:
    t = time.gmtime(ms / 1000)
    return f"{time.strftime('%b', t)} {t.tm_mday}, {t.tm_year}"


def tidy_name(n: str | None) -> str:
    n = (n or "").strip()
    return n.title() if n.isupper() and len(n) > 4 else n


def tidy_addr(a: str | None) -> str:
    a = (a or "").strip()
    a = re.sub(r"\bSTREET\b", "ST", a)
    a = re.sub(r"\bAVENUE\b", "AVE", a)
    a = a.title().replace(" Nw", " NW").replace(" Ne", " NE").replace(" Sw", " SW").replace(" Se", " SE")
    return re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), a)


def addr_key(a: str | None) -> tuple:
    m = re.match(r"^\s*(\d+)\s+(.*)$", a or "")
    return (m.group(2), int(m.group(1))) if m else (a or "", 0)


def fnum(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- map
class Projector:
    def __init__(self, rings, width=760, pad=14):
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


def map_svg(rings, licensees, cancelled) -> str:
    pr = Projector(rings)
    paths = " ".join("M" + " L".join(f"{x},{y}" for x, y in (pr.xy(*p) for p in r)) + " Z" for r in rings)
    color = {c: col for c, _, col in CATS}
    dots = []
    for r in licensees:
        lon, lat = fnum(r["LONGITUDE"]), fnum(r["LATITUDE"])
        if lon is None or lat is None:
            continue
        x, y = pr.xy(lon, lat)
        dots.append(
            f'<circle cx="{x}" cy="{y}" r="5" fill="{color[category(r["TYPE"])]}" fill-opacity=".85" data-cat="{category(r["TYPE"])}">'
            f'<title>{esc(tidy_name(r["TRADE_NAME"]))} · {esc(r["TYPE"])} (Class {esc(r["CLASS"])})</title></circle>'
        )
    xs = []
    for r in cancelled:
        lon, lat = fnum(r["LONGITUDE"]), fnum(r["LATITUDE"])
        if lon is None or lat is None:
            continue
        x, y = pr.xy(lon, lat)
        xs.append(
            f'<path d="M{x-4},{y-4} L{x+4},{y+4} M{x-4},{y+4} L{x+4},{y-4}" stroke="var(--ink)" stroke-width="1.6">'
            f'<title>License cancelled: {esc(tidy_name(r["TRADE_NAME"]))}</title></path>'
        )
    return (
        f'<svg viewBox="0 0 {pr.w} {pr.h}" role="img" aria-label="Map of {len(dots)} liquor licensees and {len(xs)} cancelled licenses in Adams Morgan" class="map">'
        f'<path d="{paths}" fill="var(--soft)" stroke="var(--accent)" stroke-width="1.5"/>'
        + "".join(dots) + "".join(xs) + "</svg>"
    )


# ---------------------------------------------------------------- page
def main() -> int:
    now = time.time()
    geom = dcdata.boundary(BOUNDARY_LAYER, BOUNDARY_WHERE)
    lic = dcdata.query_features(LICENSES, geom, "1=1", LIC_FIELDS, "OBJECTID")
    can = dcdata.query_features(CANCELLATIONS, geom, "1=1", CAN_FIELDS, "OBJECTID")
    zones = dcdata._request(f"{MORATORIUM}/query", {"where": "NAME='Adams Morgan'", "outFields": "NAME,EDITED", "returnGeometry": "false", "f": "json"})
    zone_edit = max((f["attributes"].get("EDITED") or 0 for f in zones.get("features", [])), default=0)

    # Dedupe by license number (defensive; the layer is one row per license).
    lic = list({r["LICENSE"]: r for r in lic}.values())
    can = list({r["LICENSE"]: r for r in can}.values())
    if len(lic) < 20:
        raise RuntimeError(f"only {len(lic)} licensees came back; refusing to write a thin page")

    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    lic_loaded = max(r["EDITED"] or 0 for r in lic)
    can_loaded = max((r["EDITED"] or 0 for r in can), default=0)
    by_cat = Counter(category(r["TYPE"]) for r in lic)
    by_class = Counter((r["CLASS"] or "?").strip() for r in lic)
    by_type = Counter(r["TYPE"] or "Unknown" for r in lic)
    on_18th = sum(1 for r in lic if re.search(r"\b18TH ST", r["ADDRESS"] or "", re.I))
    ent = sum(1 for r in lic if r["ENTERTAINMENT"] == "CHECKED")
    dance = sum(1 for r in lic if r["DANCING"] == "CHECKED")
    sidewalk = sum(1 for r in lic if r["SIDEWALK_CAFE"] == "CHECKED" or r["SUMMER_GARDEN"] == "CHECKED")
    capacity = sum(int(fnum(r["TOTAL_CAPACITY"]) or 0) for r in lic)
    past_exp = [r for r in lic if r["EXPIRATION_DATE"] and r["EXPIRATION_DATE"] / 1000 < now]
    past_exp_dates = Counter(day(r["EXPIRATION_DATE"]) for r in past_exp)
    can_dated = sum(1 for r in can if r["CANCELLATION_DATE"])
    zone_current = bool(zone_edit) and (now - zone_edit / 1000) < 365 * 86400

    # ---- stat tiles
    stats = f"""
<section class="grid" aria-label="Headline numbers">
  <div class="card stat"><b>{len(lic)}</b>active liquor licenses</div>
  <div class="card stat"><b>{by_cat['bar']}</b>taverns &amp; nightclubs</div>
  <div class="card stat"><b>{on_18th}</b>on 18th Street alone</div>
  <div class="card stat"><b>{len(can)}</b>licenses cancelled (ABCA file)</div>
</section>"""

    # ---- map + legend
    legend = "".join(
        f'<span><i style="background:{col}"></i>{esc(lbl)} ({by_cat[c]})</span>' for c, lbl, col in CATS
    ) + f'<span><i class="x">×</i>License cancelled ({len(can)})</span>'
    map_card = f"""
<section class="card" id="map">
  <h2>Where the licenses are</h2>
  {map_svg(geom["rings"], lic, can)}
  <p class="legend">{legend}</p>
  <p class="muted small">Boundary: DC Health planning neighborhood "Adams Morgan", which also takes in Kalorama and reaches south to U Street and the Dupont Circle area. Hover or tap a dot for the name.</p>
</section>"""

    # ---- class explainer
    class_rows = "".join(
        f"<tr><td><b>{esc(c)}</b></td><td>{esc(CLASS_GLOSS.get(c, ''))}</td><td class='n'>{n}</td></tr>"
        for c, n in sorted(by_class.items(), key=lambda kv: -kv[1])
    )
    type_line = ", ".join(f"{esc(t)} {n}" for t, n in by_type.most_common())
    class_card = f"""
<section class="card" id="classes">
  <h2>What the license classes mean</h2>
  <div class="scroll"><table>
    <thead><tr><th>Class</th><th>What it allows</th><th class="n">Here</th></tr></thead>
    <tbody>{class_rows}</tbody>
  </table></div>
  <p class="muted small">By ABCA license type: {type_line}.</p>
</section>"""

    # ---- licensee table with filter
    def extras(r):
        tags = []
        if r["ENTERTAINMENT"] == "CHECKED":
            tags.append("Entertainment")
        if r["DANCING"] == "CHECKED":
            tags.append("Dancing")
        if r["COVERCHARGE"] == "CHECKED":
            tags.append("Cover charge")
        if r["SIDEWALK_CAFE"] == "CHECKED":
            tags.append("Sidewalk café")
        if r["SUMMER_GARDEN"] == "CHECKED":
            tags.append("Summer garden")
        return "".join(f'<span class="tag">{t}</span>' for t in tags) or '<span class="muted">—</span>'

    CAP = 50
    rows_html = []
    caps_note = []
    for c, lbl, col in CATS:
        group = [r for r in lic if category(r["TYPE"]) == c]
        group.sort(key=lambda r: -(fnum(r["TOTAL_CAPACITY"]) or 0))
        if len(group) > CAP:
            caps_note.append(f"{lbl}: showing the {CAP} largest by licensed capacity of {len(group)}.")
        for r in group[:CAP]:
            cap = fnum(r["TOTAL_CAPACITY"])
            rows_html.append(
                f'<tr data-cat="{c}"><td><span class="dot" style="background:{col}"></span><b>{esc(tidy_name(r["TRADE_NAME"]))}</b>'
                f'<br><span class="muted small">{esc(r["TYPE"])} · Class {esc(r["CLASS"])} · {esc(r["LICENSE"])}</span></td>'
                f'<td>{esc(tidy_addr(r["ADDRESS"]))}</td><td>{extras(r)}</td>'
                f'<td class="n">{int(cap) if cap else "—"}</td></tr>'
            )
    buttons = '<button type="button" data-f="all" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" data-f="{c}" aria-pressed="false">{esc(lbl)}</button>' for c, lbl, _ in CATS
    )
    table_card = f"""
<section class="card" id="licensees">
  <h2>Every licensee, by kind</h2>
  <div class="filters" role="group" aria-label="Filter licensees">{buttons}</div>
  <div class="scroll"><table class="lic">
    <thead><tr><th>Name</th><th>Address</th><th>Endorsements</th><th class="n">Capacity</th></tr></thead>
    <tbody>{''.join(rows_html)}</tbody>
  </table></div>
  <p class="muted small">{' '.join(caps_note)} Endorsements are add-ons the ABC Board approved for that license. Capacity is the licensed total occupancy where ABCA lists one.</p>
</section>"""

    # ---- cancellations
    can_sorted = sorted(can, key=lambda r: addr_key(r["ADDRESS"]))
    can_rows = "".join(
        f'<tr><td><b>{esc(tidy_name(r["TRADE_NAME"]))}</b><br><span class="muted small">{esc(r["TYPE"])} · Class {esc(r["CLASS"])} · {esc(r["LICENSE"])}</span></td>'
        f'<td>{esc(tidy_addr(r["ADDRESS"]))}</td>'
        f'<td><span class="chip">License cancelled</span>'
        f'{"<br><span class=small>" + esc(day(r["CANCELLATION_DATE"])) + "</span>" if r["CANCELLATION_DATE"] else ""}'
        f'{"<br><span class=small>" + esc(r["REASON"]) + "</span>" if r["REASON"] else ""}</td></tr>'
        for r in can_sorted[:50]
    )
    date_note = (
        f"ABCA's cancellations file gives a date for {can_dated} of these {len(can)}."
        if can_dated
        else f"ABCA's cancellations file leaves the cancellation date and reason blank for all {len(can)}, so we can't say when each happened; the file was last loaded {nice_date(can_loaded)}."
    )
    can_card = f"""
<section class="card" id="cancellations">
  <h2>Recently cancelled licenses</h2>
  <p>A cancelled license is not the same as a closed business. ABCA cancels a license when the holder asks (a sale, a change of owner, a switch to a different class) or when renewal fees go unpaid. Some of these places are still open under a new license.</p>
  <div class="scroll"><table>
    <thead><tr><th>Name on the license</th><th>Address</th><th>Status</th></tr></thead>
    <tbody>{can_rows}</tbody>
  </table></div>
  <p class="muted small">{date_note}{' Showing 50 of ' + str(len(can)) + '.' if len(can) > 50 else ''}</p>
</section>"""

    # ---- moratorium
    if zone_current:
        mor_text = f"ABCA's moratorium-zone layer was updated {nice_date(zone_edit)}."
    else:
        mor_text = (
            f"We left the moratorium-zone overlay off. ABCA's GIS layer still has an \"Adams Morgan\" zone, but it was last edited "
            f"{nice_date(zone_edit) if zone_edit else 'on an unknown date'}, and ABCA's own page lists a newer rulemaking for the zone, "
            "so we can't confirm the drawn boundary is the one in force. "
            '<a href="https://abca.dc.gov/page/adams-morgan-moratorium-zone">Read the current rule at ABCA</a>.'
        )

    # ---- coming soon (sample)
    pipeline_card = f"""
<section class="card sample-box" id="pipeline">
  <p class="eyebrow">Sample · not real applications</p>
  <h2>New applications &amp; protest deadlines</h2>
  <p class="muted small">In the full build this list would come from ABCA's public notices (placards). It's mocked here because those notices are PDFs we haven't parsed yet.</p>
  <ul class="pipe">
    <li><b>Sample Café</b> · new Class C restaurant · 2400 block of 18th St NW<br><span class="muted small">Placarded (sample date) · protest petitions due 45 days later</span></li>
    <li><b>Sample Tavern</b> · asking to add a summer garden · 1800 block of Columbia Rd NW<br><span class="muted small">Placarded (sample date) · ANC 1C liquor committee review</span></li>
  </ul>
  <p class="small"><a href="https://abca.dc.gov/page/public-notices">ABCA public notices</a> · <a href="https://abca.dc.gov/service/file-protest-alcohol">How to file a protest</a> · {mor_text}</p>
</section>"""

    exp_note = ""
    if past_exp:
        dates = ", ".join(f"{n} on {d}" for d, n in past_exp_dates.most_common())
        exp_note = (
            f"<p class='muted small'>Heads up: {len(past_exp)} licenses in this file show an expiration date that has already passed ({dates}). "
            f"ABCA last loaded the licensee file {nice_date(lic_loaded)}, so most of these were probably renewed after that; the file doesn't say.</p>"
        )

    body = f"""
{stats}
<p class="small muted">{ent} licenses carry an entertainment endorsement, {dance} allow dancing, {sidewalk} have a sidewalk café or summer garden. Licensed capacity adds up to about {capacity:,} people.</p>
{map_card}
{table_card}
{exp_note}
{can_card}
{pipeline_card}
{class_card}
<section class="card sponsor"><span class="label">Presented by</span><br><b>[Sponsor name]</b>: a local business could sponsor the weekly "who's opening" list here.</section>
"""

    extra_css = """
.map{width:100%;height:auto;display:block}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.85rem;margin:.6rem 0 .2rem}
.legend i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.legend i.x{background:none;width:auto;height:auto;font-style:normal;font-weight:700;color:var(--ink)}
.small{font-size:.84rem}
.filters{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.filters button{font:inherit;font-size:.85rem;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:3px 11px;cursor:pointer}
.filters button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--card)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
.tag{display:inline-block;font-size:.72rem;border:1px solid var(--line);border-radius:4px;padding:0 5px;margin:0 3px 3px 0;white-space:nowrap}
.chip{display:inline-block;font-size:.75rem;font-weight:600;color:var(--up);border:1px solid currentColor;border-radius:999px;padding:0 8px;white-space:nowrap}
table.lic td:first-child{min-width:170px}
.sample-box{border-style:dashed;border-color:var(--sample)}
.sample-box .eyebrow{color:var(--sample)}
.pipe{padding-left:1.1rem;margin:.4rem 0}
.pipe li{margin:.4rem 0}
"""
    script = """
<script>
(function(){var bs=document.querySelectorAll('.filters button');bs.forEach(function(b){b.addEventListener('click',function(){var f=b.getAttribute('data-f');bs.forEach(function(o){o.setAttribute('aria-pressed',o===b?'true':'false')});document.querySelectorAll('table.lic tbody tr').forEach(function(tr){tr.hidden=!(f==='all'||tr.getAttribute('data-cat')===f)});document.querySelectorAll('svg.map circle').forEach(function(c){c.style.opacity=(f==='all'||c.getAttribute('data-cat')===f)?'':'.12'})})})})();
</script>"""

    fill = {
        "IDEA_ID": "civic-data#7",
        "RANK": "17",
        "SCORE": "69.1",
        "SHORT_NAME": "Adams Morgan Liquor License Tracker",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "Adams Morgan · Nightlife pipeline",
        "HEADLINE": f"{len(lic)} liquor licenses. {by_cat['bar']} of them belong to bars and nightclubs.",
        "DECK": f"Every active ABCA liquor license in Adams Morgan, sorted by kind, plus {len(can)} licenses ABCA has cancelled. Licensee file loaded by ABCA {nice_date(lic_loaded)}.",
        "BODY": body + script,
        "PITCH": "A tracker of every alcohol licensee in the neighborhood: who holds a license, what kind, which ones were cancelled, and (in the full build) which new applications are open for protest. Written for nightlife fans and nervous neighbors alike.",
        "WHATS_REAL": (
            f"The licensee list, classes, endorsements, capacities and map come from ABCA's \"Alcohol License Business Locations\" layer, and the cancelled list from ABCA's \"Alcohol License Cancellations\" layer, both queried live inside the Adams Morgan boundary on {pulled}. "
            "License holder (applicant) names are never requested; only the public trade names are shown."
        ),
        "WHATS_MOCKED": (
            "The \"New applications &amp; protest deadlines\" box is sample data with placeholder names. "
            f"The moratorium-zone overlay is left off because the layer's Adams Morgan polygon was last edited {nice_date(zone_edit) if zone_edit else 'on an unknown date'}. "
            "Cancellation dates aren't in ABCA's file, so the cancelled list can't be sorted by recency."
        ),
        "NEXT_STEPS": (
            "Parse ABCA placard notices (PDF) weekly for new applications and protest deadlines; diff the licensee layer night to night to catch new and dropped licenses with real dates; "
            "add ANC 1C liquor-committee agendas; draw the moratorium zone once ABCA's layer matches the current rule."
        ),
        "SOURCES": (
            '<a href="https://catalog.data.gov/dataset/liquor-licenses-45a2f">Alcohol License Business Locations (ABCA)</a>, '
            '<a href="https://catalog.data.gov/dataset/alcohol-license-cancellations">Alcohol License Cancellations (ABCA)</a>, '
            "Alcohol License Moratorium Zones (checked, not drawn), DC Health Planning Neighborhoods; Open Data DC, CC BY 4.0"
        ),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    }
    page = render(fill)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(lic)} licensees, {len(can)} cancellations, {len(page)//1024} KB")
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
