"""Demo #15 (culture-content#3): Lost Southwest, a self-guided walk from L'Enfant Plaza.

    python demos/ideas/src/15_lost_southwest_walk.py

Live this run:
  - stop coordinates from Open Data DC (Address Points, Intersection Points, Historic Landmarks)
  - map layers: SW/Waterfront boundary, street centerlines, water (Open Data DC)
  - three Library of Congress photos, embedded only after the item record says "No known restrictions"
Stop text is editorial: every fact is written from, and linked to, a cited source. Facts we could not
source were left out.
"""

from __future__ import annotations

import base64
import html
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "15-lost-southwest-walk.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"
UA = "dc-neighborhoods-demo/0.1 (+https://lenfantplaza.org)"

HPN = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
ADDRESS_PTS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Location_WebMercator/FeatureServer/0"
INTERSECTIONS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Location_WebMercator/FeatureServer/2"
LANDMARKS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Planning_Landuse_and_Zoning_WebMercator/MapServer/23"
STREETS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Planimetrics_2013/MapServer/3"
WATER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Environment_Water_WebMercator/MapServer/24"

W_LENFANT = "https://en.wikipedia.org/wiki/L%27Enfant_Plaza"
W_BERMAN = "https://en.wikipedia.org/wiki/Berman_v._Parker"
W_WHEAT = "https://en.wikipedia.org/wiki/Wheat_Row"
W_LAW = "https://en.wikipedia.org/wiki/Thomas_Law_House"
W_ARENA = "https://en.wikipedia.org/wiki/Arena_Stage"
W_FISH = "https://en.wikipedia.org/wiki/Maine_Avenue_Fish_Market"
SWBID = "https://swbid.org/history/"
WETA = "https://blogs.weta.org/metromap/renewalcenter"
GHOSTS = "https://ghostsofdc.org/2026/04/12/before-fedlandia-lenfant-plaza-southwest-dc-history/"
LANDMARKS_PAGE = "https://opendata.dc.gov/datasets/DCGIS::historic-landmarks"

# LOC photos: item id -> how we use it. Embedded only if the live record says "No known restrictions".
PHOTOS = {
    "2017769571": "Southwest Washington, 1939",
    "2017776356": "Alley dwellings in the southwest section, 1937",
    "dc0401": "Wheat Row, 1315–1321 Fourth Street SW",
}


def src(url: str, label: str) -> str:
    return f'<a class="src" href="{url}">{label}</a>'


# Each stop: how to locate it (live), and text whose every claim links to a source.
STOPS = [
    {
        "id": "plaza", "short": True, "name": "L'Enfant Plaza", "where": "Start at the 7th & D St SW Metro exit",
        "locate": ("intersection", "7TH", "D"),
        "photo": "2017769571",
        "lede": "You're standing on the first urban-renewal project in Washington.",
        "facts": [
            f"L'Enfant Plaza was built as part of the Southwest urban renewal project, the first in D.C., and was dedicated in 1968. {src(W_LENFANT, 'Wikipedia: L’Enfant Plaza')}",
            f"In 1954 Southwest had about 3,900 buildings housing 4,500 families. About 60 percent of residents were African American, and only 20 percent owned their homes. {src(W_LENFANT, 'Wikipedia')}",
            f"The ground under the plaza was mostly Victorian townhouses, plus a shuttered slaughterhouse. {src(W_LENFANT, 'Wikipedia')}",
            f"The Southwest BID puts the toll at about 23,000 residents and 1,500 businesses displaced. {src(SWBID, 'SW BID history')}",
        ],
    },
    {
        "id": "berman", "short": False, "name": "The store that went to the Supreme Court",
        "where": "4th & G St SW (approximate: the old street grid is gone)",
        "locate": ("intersection", "4TH", "G"),
        "photo": "2017776356",
        "lede": "A department store on Fourth Street, taken for a plan it wasn't part of.",
        "facts": [
            f"A department store stood at 712 Fourth Street SW. It wasn't blighted, but it sat in Project Area B, the first project under the 1946 D.C. Redevelopment Act, and was slated for clearance. {src(W_BERMAN, 'Wikipedia: Berman v. Parker')}",
            f"The owner's estate sued and lost, 8–0, in Berman v. Parker (1954). The Court held that private property could be taken for a public purpose with just compensation, a ruling that laid the groundwork for Kelo v. City of New London (2005). {src(W_BERMAN, 'Wikipedia')}",
            f"The planners' 1950 survey of the area reported 57.8 percent of dwellings with outside toilets and 29.6 percent without electricity. {src(W_BERMAN, 'Wikipedia')}",
        ],
    },
    {
        "id": "wheat", "short": False, "name": "Wheat Row", "where": "1315–1321 4th St SW",
        "locate": ("landmark", "Wheat Row"),
        "photo": "dc0401",
        "lede": "Four rowhouses from 1794 that renewal kept.",
        "facts": [
            f"Begun in 1794 and finished in 1795, these are some of the oldest homes in D.C. and the city's first row houses. {src(W_WHEAT, 'Wikipedia: Wheat Row')}",
            f"They were folded into the new Harbour Square cooperative in 1963 and listed on the National Register in 1973. {src(W_WHEAT, 'Wikipedia')}",
            f"The Duncanson-Cranch House next door went up at about the same time, by the same speculators. {src(W_WHEAT, 'Wikipedia')}",
        ],
    },
    {
        "id": "law", "short": False, "name": "Thomas Law House", "where": "Near 6th & N St SW, inside Tiber Island",
        "locate": ("landmark", "Law, Thomas, House (Honeymoon House)"),
        "photo": None,
        "lede": "The \"Honeymoon House\" of Martha Washington's granddaughter.",
        "facts": [
            f"Built 1794–96. Thomas Law moved in in March 1796 after marrying Eliza Parke Custis, Martha Washington's eldest granddaughter. {src(W_LAW, 'Wikipedia: Thomas Law House')}",
            f"It was the Mt. Vernon Hotel during the Civil War and a medical clinic from 1923 to 1961. {src(W_LAW, 'Wikipedia')}",
        ],
    },
    {
        "id": "arena", "short": True, "name": "Arena Stage", "where": "1101 6th St SW",
        "locate": ("address", "1101 6TH STREET SW"),
        "photo": None,
        "lede": "A theater that chose the new Southwest in 1960.",
        "facts": [
            f"Founded in 1950, Arena was the first racially integrated theater in Washington. {src(W_ARENA, 'Wikipedia: Arena Stage')}",
            f"It moved into this Harry Weese-designed home on Sixth Street in 1960; the glass-walled Mead Center renovation came in 2008–2010. {src(W_ARENA, 'Wikipedia')}",
        ],
    },
    {
        "id": "fish", "short": True, "name": "Maine Avenue Fish Market", "where": "1100 Maine Ave SW",
        "locate": ("address", "1100 MAINE AVENUE SW"),
        "photo": None,
        "lede": "Older than anything else on this walk except Wheat Row and the Law House.",
        "facts": [
            f"Open since 1805, it is the oldest continuously operating fish market in the United States. {src(W_FISH, 'Wikipedia: Maine Avenue Fish Market')}",
            f"It moved a few blocks along the Washington Channel in the 1960s, and still sells from floating barges. {src(W_FISH, 'Wikipedia')}",
        ],
    },
]

e = html.escape


def http_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(4 * (attempt + 1))
    raise AssertionError


def locate(spec) -> tuple[float, float]:
    kind = spec[0]
    if kind == "address":
        d = dcdata._request(f"{ADDRESS_PTS}/query", {"where": f"ADDRESS='{spec[1]}'", "outFields": "ADDRESS", "returnGeometry": "true", "outSR": 4326, "f": "json"})
        g = d["features"][0]["geometry"]
        return g["x"], g["y"]
    if kind == "intersection":
        a, b = spec[1], spec[2]
        where = (f"STREET_1_QUADRANT='SW' AND ((STREET_1_NAME='{a}' AND STREET_2_NAME='{b}') OR "
                 f"(STREET_1_NAME='{b}' AND STREET_2_NAME='{a}'))")
        d = dcdata._request(f"{INTERSECTIONS}/query", {"where": where, "outFields": "LATITUDE,LONGITUDE", "f": "json"})
        at = d["features"][0]["attributes"]
        return at["LONGITUDE"], at["LATITUDE"]
    if kind == "landmark":
        name = spec[1].replace("'", "''")
        d = dcdata._request(f"{LANDMARKS}/query", {"where": f"NAME='{name}'", "outFields": "NAME", "returnGeometry": "true", "outSR": 4326, "f": "json"})
        ring = d["features"][0]["geometry"]["rings"][0]
        return sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)
    raise ValueError(kind)


def loc_photo(item_id: str) -> dict | None:
    rec = json.loads(http_bytes(f"https://www.loc.gov/item/{item_id}/?fo=json&at=item"))["item"]
    rights = rec.get("rights_advisory") or ""
    rights = rights if isinstance(rights, str) else " ".join(rights)
    if "no known restrictions" not in rights.lower():
        print(f"  skip {item_id}: rights say {rights[:80]!r}")
        return None
    big = next((u for u in rec.get("image_url", []) if re.search(r"v\.jpg|pv\.jpg", u)), None) or rec["image_url"][-1]
    path = big.split("#")[0].split("storage-services/")[1].rsplit(".", 1)[0]
    iiif = f"https://tile.loc.gov/image-services/iiif/{path.replace('/', ':')}/full/520,/0/default.jpg"
    time.sleep(2)
    data = http_bytes(iiif)
    if len(data) > 150 * 1024:
        data = http_bytes(iiif.replace("/full/520,/", "/full/380,/"))
    if len(data) > 150 * 1024:
        return None
    creator = (rec.get("contributor_names") or rec.get("creator") or ["Library of Congress"])[0]
    parts = [x.strip() for x in creator.split(",")]
    parts = [x for x in parts if x and not re.match(r"^(\d|approximately|photographer|creator)", x, re.I)]
    creator = f"{re.sub(r'\s*\(.*\)', '', parts[1])} {parts[0]}" if len(parts) >= 2 else (parts[0] if parts else "Unknown")
    time.sleep(2)
    return {
        "data": "data:image/jpeg;base64," + base64.b64encode(data).decode(),
        "kb": len(data) // 1024, "url": f"https://www.loc.gov/item/{item_id}/", "creator": creator,
        "rights": "No known restrictions (LOC)",
    }


def metres(a, b) -> float:
    """Grid (Manhattan) walking estimate between two lon/lat points."""
    lat = math.radians((a[1] + b[1]) / 2)
    dx = abs(a[0] - b[0]) * 111320 * math.cos(lat)
    dy = abs(a[1] - b[1]) * 110540
    return dx + dy


def fetch_layer(url: str, env: dict, fields: str, offset: float) -> list[dict]:
    d = dcdata._request(f"{url}/query", {
        "where": "1=1", "outFields": fields, "returnGeometry": "true", "outSR": 4326,
        "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "maxAllowableOffset": offset, "f": "json",
    }, post=True)
    return d.get("features", [])


def draw_map(points: list[tuple[float, float]], boundary: dict, streets: list, water: list, bbox) -> str:
    xmin, ymin, xmax, ymax = bbox
    kx = math.cos(math.radians((ymin + ymax) / 2))
    W = 360
    s = W / ((xmax - xmin) * kx)
    H = round((ymax - ymin) * s)

    def p(lon, lat):
        return (lon - xmin) * kx * s, (ymax - lat) * s

    def d_of(parts, close):
        out = ""
        for part in parts:
            pts = [p(*q) for q in part]
            out += "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + ("Z" if close else "")
        return out

    water_svg = "".join(f'<path d="{d_of(f["geometry"]["rings"], True)}" class="water"/>' for f in water)
    street_svg = "".join(
        f'<path d="{d_of(f["geometry"]["paths"], False)}" class="st{" major" if (f["attributes"].get("ROADTYPE") or "").lower().startswith(("interstate", "freeway")) else ""}"/>'
        for f in streets if "paths" in f["geometry"]
    )
    bound = f'<path d="{d_of(boundary["rings"], True)}" class="bound"/>'
    pts = [p(*q) for q in points]
    route_full = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts + [pts[0]])
    short_pts = [pts[i] for i, st in enumerate(STOPS) if st["short"]]
    route_short = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in short_pts + [short_pts[0]])
    markers = "".join(
        f'<a href="#stop-{st["id"]}" class="mk{" long" if not st["short"] else ""}"><circle cx="{x:.1f}" cy="{y:.1f}" r="9"/>'
        f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle">{i + 1}</text></a>'
        for i, (st, (x, y)) in enumerate(zip(STOPS, pts))
    )
    labels = (f'<text x="{p(-77.0285, 38.8752)[0]:.0f}" y="{p(-77.0285, 38.8752)[1]:.0f}" class="lbl">Washington Channel</text>'
              f'<text x="{W - 8}" y="16" text-anchor="end" class="lbl">N ↑</text>')
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Map of the walking route through Southwest" class="map">'
            f'<defs><clipPath id="clip"><rect width="{W}" height="{H}"/></clipPath></defs><g clip-path="url(#clip)">'
            f'{water_svg}{street_svg}{bound}<path d="{route_full}" class="route full"/><path d="{route_short}" class="route short"/>'
            f'{markers}{labels}</g></svg>')


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
    points = [locate(st["locate"]) for st in STOPS]
    xs, ys = [q[0] for q in points], [q[1] for q in points]
    pad = 0.0022
    bbox = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    env = {"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3], "spatialReference": {"wkid": 4326}}
    boundary = dcdata.boundary(HPN, "DC_HPN_NAME='SW/WATERFRONT'")
    streets = fetch_layer(STREETS, env, "ROADTYPE", 0.00002)
    water = fetch_layer(WATER, env, "DESCRIPTION", 0.00004)
    photos = {}
    for pid in PHOTOS:
        ph = loc_photo(pid)
        if ph:
            photos[pid] = ph
    print(f"{len(points)} stops located, {len(streets)} street segments, {len(water)} water polygons, "
          f"{len(photos)} photos ({sum(p['kb'] for p in photos.values())} KB)")

    legs = [metres(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]
    full_m = sum(legs)
    short_idx = [i for i, st in enumerate(STOPS) if st["short"]]
    short_m = sum(metres(points[short_idx[i]], points[short_idx[(i + 1) % len(short_idx)]]) for i in range(len(short_idx)))

    def mins(m):  # ~80 m per minute plus ~4 minutes per stop
        return round(m / 80)

    cards = []
    for i, st in enumerate(STOPS):
        nxt = (i + 1) % len(STOPS)
        leg = legs[i]
        ph = photos.get(st["photo"]) if st["photo"] else None
        fig = (f'<figure><img src="{ph["data"]}" alt="{e(PHOTOS[st["photo"]])}" width="520">'
               f'<figcaption>{e(PHOTOS[st["photo"]])}. {e(ph["creator"])}. <a href="{ph["url"]}">Library of Congress</a>, no known restrictions.</figcaption></figure>') if ph else ""
        nxt_txt = "back to the start" if nxt == 0 else f"stop {nxt + 1}, {STOPS[nxt]['name']}"
        cards.append(f"""<section class="card stop{' long' if not st['short'] else ''}" id="stop-{st['id']}">
  <p class="num">Stop {i + 1}{'' if st['short'] else ' · full walk only'}</p>
  <h2>{e(st['name'])}</h2>
  <p class="where">{e(st['where'])}</p>
  <p class="lede">{e(st['lede'])}</p>
  {fig}
  <ul class="facts">{''.join(f'<li>{f}</li>' for f in st['facts'])}</ul>
  <p class="audio"><span class="play" aria-hidden="true">▶</span> 90-second audio guide <span class="muted">(recording planned)</span></p>
  <p class="next">Next: {e(nxt_txt)} · about {round(leg / 10) * 10:,} m, {mins(leg)} min</p>
</section>""")

    gone = f"""<section class="card gone"><h2>Where did everyone go?</h2>
<p>The 1946 Redevelopment Act let a new land agency take property by eminent domain and hand it to private developers. {src(W_BERMAN, 'Wikipedia')} WETA's Boundary Stones says the project wiped out most of Southwest's buildings and many predominantly Black neighborhoods. {src(WETA, 'WETA')} Families were moved out with only a fraction of their homes' value in compensation. {src(W_LENFANT, 'Wikipedia')}</p>
<p class="muted small">This section will carry first-person accounts recorded with former residents and Southwest neighborhood groups. Until then we point to <a href="{GHOSTS}">Ghosts of DC</a> and <a href="{SWBID}">the Southwest BID's history page</a>.</p></section>"""

    body = f"""
<div class="card start">
  <div class="pick" role="group" aria-label="Choose a walk">
    <button type="button" data-route="full" aria-pressed="true">Full walk<br><b>{full_m / 1000:.1f} km · ~{mins(full_m) + 4 * len(STOPS)} min</b></button>
    <button type="button" data-route="short" aria-pressed="false">Short loop<br><b>{short_m / 1000:.1f} km · ~{mins(short_m) + 4 * len(short_idx)} min</b></button>
  </div>
  <div class="mapwrap">{draw_map(points, boundary, streets, water, bbox)}</div>
  <p class="muted small">Route lines are schematic: follow the sidewalks. Distances are grid estimates. Dashed line: Southwest/Waterfront neighborhood boundary. Tap a number to jump to that stop.</p>
  <p class="train"><b>12 minutes before your train?</b> Read stop 1 at the plaza, then look south. WETA puts the loss at 99 percent of Southwest's buildings. {src(WETA, 'WETA')}</p>
</div>
{''.join(cards)}
{gone}
<div class="card sponsor"><div class="label">Supported by</div><b>[Grant funder or sponsor name]</b>. This walk is meant to be free and grant-funded.</div>
<script>
(function(){{var b=document.querySelectorAll('.pick button');b.forEach(function(x){{x.addEventListener('click',function(){{var r=x.getAttribute('data-route');document.body.classList.toggle('short',r==='short');b.forEach(function(y){{y.setAttribute('aria-pressed',String(y===x));}});}});}});}})();
</script>
"""

    extra_css = """
.small{font-size:.84rem}
.pick{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.pick button{font:inherit;font-size:.85rem;text-align:left;padding:.55rem .7rem;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
.pick button[aria-pressed=true]{border-color:var(--accent);background:var(--soft);box-shadow:inset 0 0 0 1px var(--accent)}
.map{width:100%;height:auto;display:block;background:var(--card);border-radius:8px;border:1px solid var(--line)}
.map .water{fill:#cfe0ea}
.map .st{fill:none;stroke:var(--line);stroke-width:1.3}
.map .st.major{stroke:var(--muted);stroke-width:2.2;opacity:.5}
.map .bound{fill:none;stroke:var(--gold);stroke-width:1.5;stroke-dasharray:5 4}
.map .route{fill:none;stroke:var(--brick);stroke-width:3;stroke-linejoin:round;opacity:.85}
.map .route.short{display:none}
.map .mk circle{fill:var(--brick);stroke:var(--card);stroke-width:2}
.map .mk text{fill:#fff;font-size:11px;font-weight:700}
.map .lbl{font-size:10px;font-style:italic}
body.short .map .route.full{display:none}body.short .map .route.short{display:inline}
body.short .map .mk.long{opacity:.25}
body.short .stop.long{display:none}
body.short .next{display:none}
.stop .num{margin:0;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--brick)}
.stop h2{font-size:1.3rem;margin:.1rem 0 .1rem}
.stop .where{margin:0 0 .5rem;color:var(--muted);font-size:.9rem}
.stop .lede{font-weight:600;margin:.4rem 0}
.stop figure{margin:.6rem 0}.stop img{width:100%;height:auto;border-radius:6px;display:block;filter:grayscale(1)}
.stop figcaption{font-size:.78rem;color:var(--muted);margin-top:4px}
.facts{padding-left:1.1rem;margin:.4rem 0}.facts li{margin:.35rem 0}
a.src{font-size:.72rem;white-space:nowrap;color:var(--muted);text-decoration:underline dotted}
a.src::before{content:"["}a.src::after{content:"]"}
.audio{display:flex;align-items:center;gap:8px;font-size:.88rem;margin:.6rem 0}
.play{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--soft);color:var(--accent);border:1px solid var(--accent);font-size:.7rem}
.next{margin:.4rem 0 0;padding-top:.5rem;border-top:1px solid var(--line);font-size:.88rem;color:var(--muted)}
.train{background:var(--soft);border-radius:8px;padding:.6rem .8rem;margin:.8rem 0 0;font-size:.92rem}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .map .water{fill:#1f3340}}
:root[data-theme=dark] .map .water{fill:#1f3340}
"""

    page = render({
        "IDEA_ID": "culture-content#3",
        "RANK": "15",
        "SCORE": "70.9",
        "SHORT_NAME": "Lost Southwest walk",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC + Library of Congress · pulled {today}",
        "EYEBROW": "L'Enfant Plaza · Self-guided walk",
        "HEADLINE": "Lost Southwest",
        "DECK": e(f"A {len(STOPS)}-stop walk from the L'Enfant Plaza Metro through the neighborhood that urban renewal cleared in the 1950s, and the few things it kept."),
        "BODY": body,
        "PITCH": "A phone-first, grant-fundable walking tour for the people passing through L'Enfant Plaza: tourists, federal workers and Metro transfers. It tells the story of the Southwest neighborhood that renewal razed, stop by stop, with public-domain photos.",
        "WHATS_REAL": f"Fetched on {today}: stop locations (DC Address Points, Intersection Points and Historic Landmarks), the map's streets, water and neighborhood boundary (Open Data DC), and the Library of Congress photos, each embedded only after its record said \"No known restrictions\". Every fact in the stop text was written from the source linked beside it. Facts I couldn't source, such as when St. Dominic's Church was built, were left out.",
        "WHATS_MOCKED": "The audio guides (planned, not recorded), the sponsor slot and first-person accounts. Distances are straight grid estimates and the route line is schematic. The Fourth Street store's pin is approximate because the old street grid no longer exists.",
        "NEXT_STEPS": "Write 8–12 stops with SW neighborhood groups, record 90-second audio for each, add GPS \"you are here\" and a 15/30/45-minute chooser, route along real sidewalks, and apply for a HumanitiesDC grant. DCPL's Washington Star photos would need a license, so link to them instead.",
        "SOURCES": f'Open Data DC (Address Points, Intersection Points, Historic Landmarks, Street Centerlines 2013, Waterbodies, Neighborhood boundaries; CC BY 4.0); Library of Congress Prints &amp; Photographs (FSA/OWI, HABS); <a href="{SWBID}">SW BID</a>; <a href="{WETA}">WETA Boundary Stones</a>; Wikipedia (CC BY-SA)',
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    })
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({len(page.encode()) // 1024} KB); full {full_m:.0f} m, short {short_m:.0f} m")


if __name__ == "__main__":
    main()
