"""Layout B: "Field Guide" mockup for the petworth.org home page.

Map-first, place-based, wayfinding-sign visual language.
Reads design/layouts/facts.json and writes design/layouts/B-field-guide.html.

Run:  python design/layouts/src/B_field_guide.py
"""
from __future__ import annotations

import html
import json
import math
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYOUTS = HERE.parent
ROOT = LAYOUTS.parent.parent
FACTS = LAYOUTS / "facts.json"
OUT = LAYOUTS / "B-field-guide.html"
# Optional: the site's own nightly data, used ONLY to know which of the
# permit_points in facts.json belongs to which bigger-project address.
SITE_DATA = ROOT / "site" / "src" / "data" / "petworth.json"

f = json.loads(FACTS.read_text(encoding="utf-8"))
e = html.escape


# ---------- helpers ----------
def link(name: str) -> str:
    return "../../" + f["demo_links"][name]


def n(x: int) -> str:
    return f"{x:,}"


def title_addr(a: str) -> str:
    a = re.sub(r"\s+\d{5}$", "", a.strip())
    out = []
    for w in a.split():
        out.append(w if w in ("NW", "NE", "SW", "SE") or w[0].isdigit() else w.capitalize())
    return " ".join(out)


def title_name(s: str) -> str:
    return " ".join(w.capitalize() for w in s.split())


def clean_work(s: str) -> str:
    s = s.replace("\r", "\n").split("\n")[0].strip()
    s = re.sub(r"\.(?=[A-Z])", ". ", s)
    s = re.sub(r"\s+", " ", s)
    if len(s) >= 150:  # source text is truncated mid-word; end on a whole word
        s = s.rsplit(" ", 1)[0].rstrip(",;:-") + "…"
    return s


def short_date(iso: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%b ") + str(d.day)


def stamp(iso: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    try:
        from zoneinfo import ZoneInfo

        d = d.astimezone(ZoneInfo("America/New_York"))
        tz = d.tzname() or "ET"
    except Exception:  # no tz database: show UTC
        tz = "UTC"
    hour = d.strftime("%I").lstrip("0")
    return f"{d.strftime('%b')} {d.day}, {d.year} · {hour}:{d.strftime('%M')} {d.strftime('%p').lower()} {tz}"


# ---------- map projection (same approach as site/src/components/BoundaryMap.astro) ----------
rings = f["boundary_rings"]
pts = [p for r in rings for p in r]
minX, maxX = min(p[0] for p in pts), max(p[0] for p in pts)
minY, maxY = min(p[1] for p in pts), max(p[1] for p in pts)
k = math.cos(math.radians((minY + maxY) / 2))
W, PAD = 600, 26
scale = (W - 2 * PAD) / ((maxX - minX) * k)
H = round((maxY - minY) * scale + 2 * PAD)


def px(lon: float) -> float:
    return PAD + (lon - minX) * k * scale


def py(lat: float) -> float:
    return PAD + (maxY - lat) * scale


outline = " ".join(
    "M" + "L".join(f"{px(x):.1f},{py(y):.1f}" for x, y in r) + "Z" for r in rings
)

BIG = {"Demolition", "Additions", "New construction"}
points = f["permit_points"]

# Which permit point is which bigger project? Look the address up in the site's
# data, and accept it only if that exact coordinate+group is in facts.json.
addr_coord: dict[str, tuple[float, float]] = {}
if SITE_DATA.exists():
    try:
        site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
        fact_pts = {(p["lat"], p["lon"], p["group"]) for p in points}
        for p in site.get("permits", []):
            key = (p.get("lat"), p.get("lon"), p.get("group"))
            if key in fact_pts and p.get("group") in BIG:
                addr_coord.setdefault(p["address"], (p["lat"], p["lon"]))
    except Exception:
        addr_coord = {}

projects = []
for i, b in enumerate(f["bigger_projects"], 1):
    projects.append(
        {
            "num": i,
            "addr": title_addr(b["address"]),
            "group": "Demolition" if b["group"] == "Demolition" else b["group"].rstrip("s"),
            "kind": "demo" if b["group"] == "Demolition" else "add",
            "date": short_date(b["issued"]),
            "work": clean_work(b["work"]),
            "xy": addr_coord.get(b["address"]),
        }
    )

# small dots (everything not a bigger project), de-duplicated by position
seen = set()
dots = []
for p in points:
    if p["group"] in BIG:
        continue
    key = (round(px(p["lon"]), 1), round(py(p["lat"]), 1))
    if key in seen:
        continue
    seen.add(key)
    dots.append(key)

dot_svg = "".join(f'<circle class="m-dot" cx="{x}" cy="{y}" r="4"/>' for x, y in dots)

marker_svg = []
for pr in projects:
    if not pr["xy"]:
        continue
    lat, lon = pr["xy"]
    x, y = px(lon), py(lat)
    cls = "m-pin demo" if pr["kind"] == "demo" else "m-pin"
    marker_svg.append(
        f'<a href="#p{pr["num"]}" class="{cls}" aria-label="Project {pr["num"]}: {e(pr["addr"])}">'
        f'<title>{pr["num"]}. {e(pr["addr"])} · {pr["group"]}</title>'
        f'<rect x="{x - 15:.1f}" y="{y - 15:.1f}" width="30" height="30" rx="7"/>'
        f'<text x="{x:.1f}" y="{y + 6.5:.1f}">{pr["num"]}</text></a>'
    )
marker_svg = "".join(marker_svg)

# scale bar: 500 m
m_per_deg_lat = 111_320
bar_px = 500 / m_per_deg_lat * scale
sb_x, sb_y = PAD, H - 16
scale_svg = (
    f'<g class="m-scale"><rect x="{sb_x}" y="{sb_y - 5}" width="{bar_px / 2:.1f}" height="5"/>'
    f'<rect x="{sb_x + bar_px / 2:.1f}" y="{sb_y - 5}" width="{bar_px / 2:.1f}" height="5" class="alt"/>'
    f'<text x="{sb_x}" y="{sb_y - 10}">0</text>'
    f'<text x="{sb_x + bar_px:.1f}" y="{sb_y - 10}" text-anchor="end">500 m</text></g>'
)
north_svg = (
    f'<g class="m-north" transform="translate({W - 34},{H - 40})">'
    '<circle r="17"/><path d="M0,-11 L6,6 L0,2 L-6,6 Z"/><text y="-21">N</text></g>'
)
cx_label = px((minX + maxX) / 2) - 40
cy_label = py((minY + maxY) / 2) + 40

map_svg = f"""<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-label="Map of Petworth with {f['this_month']['permits_30d']} building permits from the last 30 days; the {len(projects)} bigger projects are numbered.">
<defs><pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" class="m-grid"/></pattern>
<clipPath id="clip"><path d="{outline}"/></clipPath></defs>
<rect width="{W}" height="{H}" class="m-bg"/><rect width="{W}" height="{H}" fill="url(#grid)"/>
<path d="{outline}" class="m-area"/>
<g clip-path="url(#clip)"><rect width="{W}" height="{H}" fill="url(#grid)" class="m-grid-in"/></g>
<path d="{outline}" class="m-edge"/>
{dot_svg}{marker_svg}{north_svg}{scale_svg}
</svg>"""

# ---------- permit legend ----------
pg = f["permit_groups"]
legend_rows = "".join(
    f'<li><span class="sw {"big" if g in BIG else ""}"></span>{e(g)}<b>{c}</b></li>'
    for g, c in sorted(pg.items(), key=lambda kv: -kv[1])
)

# ---------- pictograms (24x24, stroke) ----------
ICON = {
    "week": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/><circle cx="12" cy="15.5" r="2"/>',
    "build": '<path d="M4 21V9l8-5 8 5v12"/><path d="M4 21h16"/><path d="M9 21v-6h6v6"/><path d="M15 4h5v4"/>',
    "streets": '<path d="M7 21 10 3M17 21 14 3"/><path d="M12 5v2M12 10v3M12 16v4"/>',
    "homes": '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><rect x="10" y="14" width="4" height="6"/>',
    "trees": '<circle cx="12" cy="9" r="6"/><path d="M12 15v6M9 21h6M12 12l-2.5-2.5M12 11l2.5-2"/>',
    "history": '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3Z"/><path d="M5 17a3 3 0 0 1 3-3h11"/><path d="M9 7h6M9 10h4"/>',
    "people": '<circle cx="8" cy="8" r="3"/><circle cx="16.5" cy="9" r="2.5"/><path d="M2.5 20a5.5 5.5 0 0 1 11 0M13 20a4 4 0 0 1 8 0"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
    "rss": '<path d="M5 5a14 14 0 0 1 14 14M5 11a8 8 0 0 1 8 8"/><circle cx="6" cy="18" r="1.5"/>',
}


def icon(name: str, cls: str = "pict") -> str:
    return (
        f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICON[name]}</svg>'
    )


def blade(entry: str, label: str, ic: str, tone: str = "") -> str:
    return (
        f'<div class="entry-head"><span class="entry-no">{entry}</span>'
        f'<h2 class="blade {tone}">{icon(ic)}<span>{label}</span></h2></div>'
    )


# ---------- this week ----------
tm = f["this_month"]
movers = tm["top_311_movers"]
lead = max(movers, key=lambda m: m["count"] - m["previous"])
top_type = tm["top_311_types"][0]
req_diff = tm["requests_30d"] - tm["requests_prev_30d"]
req_word = "down" if req_diff < 0 else "up"

other_moves = "".join(
    f'<li><span>{e(m["type"])}</span><b>{m["count"]}</b><i>was {m["previous"]}</i></li>'
    for m in movers
    if m is not lead
)

# ---------- 311 top types ----------
max311 = max(t["count"] for t in tm["top_311_types"])
types_rows = "".join(
    f'<li><span class="lbl">{e(t["type"])}</span><span class="bar"><i style="width:{t["count"] / max311 * 100:.0f}%"></i></span><b>{t["count"]}</b></li>'
    for t in tm["top_311_types"]
)

# ---------- projects key ----------
key_rows = "".join(
    f'<li id="p{p["num"]}" class="kp {p["kind"]}"><span class="kn">{p["num"]}</span>'
    f'<div><h3>{e(p["addr"])}</h3>'
    f'<p class="kmeta"><span class="tag {p["kind"]}">{p["group"]}</span> issued {p["date"]}</p>'
    f'<p class="kwork">{e(p["work"])}</p></div></li>'
    for p in projects
)

# ---------- representatives ----------
reps = f["representatives"]
ancs: dict[str, list] = {}
for r in reps:
    ancs.setdefault(r["anc"], []).append(r)
rep_html = ""
for anc, rs in ancs.items():
    rows = "".join(
        f'<li><span class="smd">{r["smd"]}</span><span class="who">{e(title_name(r["commissioner"]))}</span></li>'
        for r in rs
    )
    rep_html += (
        f'<div class="anc"><p class="anc-h">ANC {anc} <a href="{e(rs[0]["url"])}">{e(rs[0]["url"].split("//")[1].strip("/"))} ↗</a></p>'
        f'<ul class="smds">{rows}</ul></div>'
    )

h = f["homes"]
s = f["streets"]
t = f["trees"]
hist = f["history"]

# ---------- page ----------
CSS = """
:root{
  --paper:#f3f1e7; --card:#fffdf6; --ink:#16231b; --muted:#56635a; --rule:#d8d5c4;
  --park:#1d5b3b; --park-2:#2f7a50; --park-soft:#dcebd9; --park-tint:#e9f2e3;
  --signal:#e2571e; --signal-soft:#fde3d4; --amber:#f2b630; --amber-soft:#fcefc7;
  --brown:#6b4528; --brown-soft:#efe2d4;
  --on-sign:#ffffff; --dot:#3c4d43; --map-bg:#ebe8da; --grid:#d9d5c3;
  --radius:14px;
  --sans:"Overpass","Highway Gothic","Helvetica Neue",Arial,sans-serif;
  --mono:"Overpass Mono",ui-monospace,"SFMono-Regular",Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root{
    --paper:#111a15; --card:#18241d; --ink:#eef0e6; --muted:#a6b2a8; --rule:#2c3b32;
    --park:#2f7a50; --park-2:#5fae7e; --park-soft:#1f3a2a; --park-tint:#1a2c21;
    --signal:#f07a42; --signal-soft:#3d2418; --amber:#f2b630; --amber-soft:#3a3018;
    --brown:#8a5d3a; --brown-soft:#33271d; --dot:#b9c6bc; --map-bg:#141f18; --grid:#22322a;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 16px/1.5 var(--sans);overflow-x:hidden}
a{color:var(--park-2);text-underline-offset:3px;text-decoration-thickness:2px}
h1,h2,h3{margin:0;line-height:1.1}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
.layout-tag{background:var(--ink);color:var(--paper);font:600 11px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;padding:7px 16px}

/* header: a street-name sign */
header.top{padding-top:18px;padding-bottom:14px}
.sign{display:inline-flex;align-items:center;gap:12px;background:var(--park);color:var(--on-sign);border-radius:10px;padding:8px 18px 6px;box-shadow:inset 0 0 0 3px var(--park),inset 0 0 0 5px var(--on-sign)}
.sign h1{font:900 44px/1 var(--sans);letter-spacing:.02em;text-transform:uppercase}
.sign small{white-space:nowrap;font:700 13px/1 var(--sans);border-left:2px solid currentColor;padding-left:10px;letter-spacing:.06em}
.dek{font:600 18px/1.3 var(--sans);margin:12px 0 6px;max-width:34ch}
.stamp{display:inline-flex;gap:8px;align-items:center;font:600 12px/1 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.stamp::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--park-2);box-shadow:0 0 0 3px var(--park-soft)}

/* hero map */
.hero{display:grid;gap:18px;padding-bottom:8px}
.mapcard{background:var(--card);border:2px solid var(--ink);border-radius:var(--radius);overflow:hidden}
.mapcap{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:10px 14px;border-bottom:2px solid var(--ink);font:800 13px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.06em}
.mapcap span{font:600 11px/1 var(--mono);color:var(--muted)}
svg.map{display:block;width:100%;height:auto}
.m-bg{fill:var(--map-bg)}
.m-grid{fill:none;stroke:var(--grid);stroke-width:1}
.m-area{fill:var(--park-tint)}
.m-grid-in{opacity:.6}
.m-edge{fill:none;stroke:var(--park);stroke-width:3.5;stroke-dasharray:14 5;stroke-linejoin:round}
.m-name{font:900 30px var(--sans);letter-spacing:.35em;fill:var(--park);opacity:.18}
.m-dot{fill:var(--dot);opacity:.55}
.m-pin rect{fill:var(--signal);stroke:var(--card);stroke-width:3}
.m-pin.demo rect{fill:var(--ink)}
.m-pin text{font:800 19px var(--sans);fill:#fff;text-anchor:middle}
.m-pin:hover rect,.m-pin:focus rect{stroke:var(--amber)}
.m-north circle{fill:var(--card);stroke:var(--ink);stroke-width:2}
.m-north path{fill:var(--ink)}
.m-north text{font:800 12px var(--sans);fill:var(--ink);text-anchor:middle}
.m-scale rect{fill:var(--ink)} .m-scale rect.alt{fill:var(--card);stroke:var(--ink);stroke-width:1}
.m-scale text{font:600 11px var(--mono);fill:var(--ink)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;padding:10px 14px 12px;border-top:1px solid var(--rule);font-size:13px;color:var(--muted)}
.legend .k{display:inline-flex;align-items:center;gap:6px}
.legend .d{width:9px;height:9px;border-radius:50%;background:var(--dot);opacity:.7}
.legend .p{width:16px;height:16px;border-radius:4px;background:var(--signal);color:#fff;font:800 10px/16px var(--sans);text-align:center}
.legend .p.dk{background:var(--ink);color:var(--card)}

/* find your block */
.finder{background:var(--amber);color:#1b1a10;border-radius:var(--radius);padding:16px;border:2px solid #1b1a10}
.finder label{display:flex;align-items:center;gap:8px;font:900 20px/1.1 var(--sans);text-transform:uppercase;letter-spacing:.02em;margin-bottom:10px}
.finder label svg{width:24px;height:24px}
.field{display:flex;background:#fff;border:2px solid #1b1a10;border-radius:10px;overflow:hidden}
.field input{flex:1;min-width:0;border:0;padding:14px 12px;font:600 17px var(--sans);color:#1b1a10;background:transparent}
.field input::placeholder{color:#6d6a58}
.field a{display:flex;align-items:center;padding:0 18px;background:#1b1a10;color:#fff;font:800 15px var(--sans);text-decoration:none;text-transform:uppercase;letter-spacing:.06em}
.finder p{margin:10px 0 0;font-size:14px}
.finder p a{color:#1b1a10;font-weight:700}

/* directional post */
.post{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 6px;padding:0;list-style:none}
.post a{display:inline-flex;align-items:center;gap:6px;background:var(--park);color:var(--on-sign);text-decoration:none;font:800 13px/1 var(--sans);text-transform:uppercase;letter-spacing:.05em;padding:8px 10px 7px;border-radius:6px;box-shadow:inset 0 0 0 1.5px var(--park),inset 0 0 0 3px rgba(255,255,255,.85)}
.post a.br{background:var(--brown);box-shadow:inset 0 0 0 1.5px var(--brown),inset 0 0 0 3px rgba(255,255,255,.85)}
.post a.or{background:var(--signal);box-shadow:inset 0 0 0 1.5px var(--signal),inset 0 0 0 3px rgba(255,255,255,.85)}
.post a.yl{background:var(--amber);color:#1b1a10;box-shadow:inset 0 0 0 1.5px var(--amber),inset 0 0 0 3px rgba(27,26,16,.85)}

/* key */
.key{background:var(--card);border:2px solid var(--ink);border-radius:var(--radius);overflow:hidden}
.key ol{list-style:none;margin:0;padding:0}
.kp{display:grid;grid-template-columns:34px 1fr;gap:12px;padding:12px 14px;border-top:1px solid var(--rule)}
.kp:first-child{border-top:0}
.kp:target{background:var(--signal-soft)}
.kn{width:30px;height:30px;border-radius:7px;background:var(--signal);color:#fff;font:800 17px/31px var(--sans);text-align:center}
.kp.demo .kn{background:var(--ink);color:var(--card)}
.kp h3{font:800 17px/1.2 var(--sans)}
.kmeta{margin:3px 0 4px;font:600 12px/1.3 var(--mono);color:var(--muted);text-transform:uppercase}
.tag{display:inline-block;padding:2px 6px 1px;border-radius:4px;background:var(--signal-soft);color:var(--ink);margin-right:4px}
.tag.demo{background:var(--ink);color:var(--card)}
.kwork{margin:0;font-size:14px;line-height:1.4;color:var(--muted)}
.more{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:12px 14px;border-top:2px solid var(--ink);font:800 14px var(--sans);text-transform:uppercase;letter-spacing:.04em}
.more a{text-decoration:none}

/* field-guide entries */
.entries{display:grid;gap:18px;margin:22px 0}
.entry{background:var(--card);border:2px solid var(--ink);border-radius:var(--radius);padding:0 0 4px;overflow:hidden}
.entry-head{display:flex;align-items:stretch;border-bottom:2px solid var(--ink)}
.entry-no{display:flex;align-items:center;justify-content:center;min-width:56px;font:700 12px/1.1 var(--mono);text-align:center;color:var(--muted);border-right:2px solid var(--ink);padding:0 6px;text-transform:uppercase}
.blade{flex:1;display:flex;align-items:center;gap:10px;margin:8px;padding:9px 12px 7px;background:var(--park);color:var(--on-sign);border-radius:8px;font:900 22px/1 var(--sans);text-transform:uppercase;letter-spacing:.03em;box-shadow:inset 0 0 0 2px var(--park),inset 0 0 0 4px rgba(255,255,255,.9)}
.blade.or{background:var(--signal);box-shadow:inset 0 0 0 2px var(--signal),inset 0 0 0 4px rgba(255,255,255,.9)}
.blade.br{background:var(--brown);box-shadow:inset 0 0 0 2px var(--brown),inset 0 0 0 4px rgba(255,255,255,.9)}
.blade.yl{background:var(--amber);color:#1b1a10;box-shadow:inset 0 0 0 2px var(--amber),inset 0 0 0 4px rgba(27,26,16,.9)}
.pict{width:26px;height:26px;flex:none;background:rgba(255,255,255,.95);color:var(--park);border-radius:5px;padding:3px}
.blade.or .pict{color:var(--signal)} .blade.br .pict{color:var(--brown)} .blade.yl .pict{background:#1b1a10;color:var(--amber)}
.body{padding:14px 16px 10px}
.lead{font:900 26px/1.1 var(--sans);margin:0 0 6px}
.lead em{font-style:normal;color:var(--signal)}
.body p{margin:0 0 10px}
.stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:12px 0}
.stat{background:var(--park-tint);border-radius:10px;padding:10px 12px}
.stat b{display:block;font:900 30px/1 var(--sans);letter-spacing:-.01em}
.stat span{display:block;font-size:13px;line-height:1.3;color:var(--muted);margin-top:4px}
.stats.three{grid-template-columns:repeat(3,minmax(0,1fr))}
.stats.three .stat b{font-size:26px}
.stat.or{background:var(--signal-soft)} .stat.yl{background:var(--amber-soft)} .stat.br{background:var(--brown-soft)}
.moves{list-style:none;margin:0 0 6px;padding:0;font-size:14px}
.moves li{display:flex;gap:8px;align-items:baseline;padding:6px 0;border-top:1px dashed var(--rule)}
.moves span{flex:1} .moves b{font-weight:800} .moves i{font-style:normal;color:var(--muted);font-size:12px;font-family:var(--mono)}
.sub{font:800 13px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px;color:var(--muted)}
.bars{list-style:none;margin:0 0 6px;padding:0;font-size:14px}
.bars li{display:grid;grid-template-columns:minmax(0,1fr) 70px 36px;gap:8px;align-items:center;padding:4px 0}
.bars .lbl{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bars .bar{height:10px;background:var(--park-soft);border-radius:3px;overflow:hidden}
.bars .bar i{display:block;height:100%;background:var(--park)}
.bars b{text-align:right;font-weight:800}
.go{display:flex;flex-wrap:wrap;gap:8px 16px;padding:10px 16px 12px;border-top:1px solid var(--rule);font:800 14px var(--sans)}
.go a{text-decoration:none}
.go a::after{content:" \\2192"}
.permit-groups{list-style:none;margin:0;padding:0;columns:1;font-size:14px}
.permit-groups li{display:flex;align-items:center;gap:8px;padding:3px 0}
.permit-groups b{margin-left:auto}
.permit-groups .sw{width:9px;height:9px;border-radius:50%;background:var(--dot);opacity:.7}
.permit-groups .sw.big{border-radius:2px;background:var(--signal);opacity:1}
blockquote{margin:12px 0;padding:12px 14px;background:var(--brown-soft);border-left:5px solid var(--brown);border-radius:0 10px 10px 0;font:italic 400 16px/1.45 Georgia,"Times New Roman",serif}
.ocr{display:inline-block;font:700 10px/1 var(--mono);letter-spacing:.1em;background:var(--brown);color:#fff;padding:4px 6px 3px;border-radius:3px;margin-bottom:6px;font-style:normal}
.src{font:400 12px/1.4 var(--mono);color:var(--muted)}
.anc{margin-bottom:10px}
.anc-h{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font:900 16px/1.2 var(--sans);text-transform:uppercase;margin:0 0 6px}
.anc-h a{font:600 13px var(--sans);text-transform:none}
.smds{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.smds li{display:flex;align-items:center;gap:10px;font-weight:600}
.smd{flex:none;font:800 13px/1 var(--mono);background:var(--ink);color:var(--card);border-radius:5px;padding:6px 7px 5px}
.note{font-size:13px;color:var(--muted)}

/* subscribe + sponsor */
.signup{background:var(--park);color:var(--on-sign);border-radius:var(--radius);padding:18px 16px;margin:0 0 18px}
.signup h2{display:flex;align-items:center;gap:10px;font:900 22px/1.1 var(--sans);text-transform:uppercase}
.signup h2 svg{width:26px;height:26px}
.signup p{margin:8px 0 12px}
.signup .field{border-color:var(--on-sign)}
.signup .field a{background:var(--amber);color:#1b1a10}
.signup .alt{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:12px;font:700 14px var(--sans)}
.signup .alt a{color:var(--on-sign);display:inline-flex;align-items:center;gap:6px}
.signup .alt svg{width:16px;height:16px}
.sponsor{display:flex;align-items:center;gap:12px;border:2px dashed var(--muted);border-radius:var(--radius);padding:14px 16px;margin-bottom:22px;color:var(--muted)}
.sponsor b{color:var(--ink);font:800 16px var(--sans)}
.sponsor small{display:block;font:600 11px/1 var(--mono);text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px}

footer{border-top:4px solid var(--ink);padding:18px 0 40px;font-size:13px;color:var(--muted)}
footer strong{color:var(--ink)}
footer p{margin:0 0 8px;max-width:70ch}

@media (min-width:760px){
  .entries{grid-template-columns:1fr 1fr}
  .entries .wide{grid-column:1/-1}
  .sign h1{font-size:56px}
}
@media (min-width:980px){
  .hero{grid-template-columns:minmax(0,7fr) minmax(0,5fr);align-items:start}
  .hero .key{position:sticky;top:12px}
  .dek{font-size:21px}
}
"""

stamp_txt = stamp(f["generated_at"])
demo_num = next((p['num'] for p in projects if p['kind'] == 'demo'), '')
n_pins = sum(1 for p in projects if p["xy"])

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth Field Guide</title>
<meta name="description" content="What's changing in Petworth, from DC's own data. An independent, automatically updated neighborhood guide.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;700;800;900&family=Overpass+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="layout-tag">LAYOUT B: Field Guide</div>

<header class="top wrap">
  <div class="sign"><h1>Petworth</h1><small>NW &middot; DC</small></div>
  <p class="dek">A field guide to what's changing in Petworth, from DC's own data.</p>
  <span class="stamp">Data as of {stamp_txt}</span>
</header>

<main class="wrap">
<section class="hero" aria-label="Map and bigger projects">
  <div>
    <figure class="mapcard" style="margin:0">
      <figcaption class="mapcap">Building permits, last 30 days <span>{tm['permits_30d']} permits</span></figcaption>
      {map_svg}
      <div class="legend">
        <span class="k"><span class="d"></span>Permit</span>
        <span class="k"><span class="p">1</span>Addition</span>
        <span class="k"><span class="p dk">{demo_num}</span>Demolition</span>
        <span class="k">Dashed line: Petworth boundary</span>
      </div>
    </figure>

    <div class="finder" style="margin-top:14px" role="search">
      <label for="q">{icon('search', '')}Find your block</label>
      <div class="field">
        <input id="q" type="text" placeholder="Look up your block or building" autocomplete="off">
        <a href="{link('Block Watch')}">Go</a>
      </div>
      <p>Try &ldquo;400 Delafield Pl NW&rdquo;. Opens <a href="{link('Block Watch')}">Block Watch</a>, your <a href="{link('Block report card')}">block report card</a>, or a <a href="{link('Building biography')}">building biography</a>.</p>
    </div>

    <ul class="post" aria-label="Jump to">
      <li><a class="yl" href="#week">This week</a></li>
      <li><a class="or" href="#projects">Projects</a></li>
      <li><a href="#streets">Streets</a></li>
      <li><a href="#homes">Homes</a></li>
      <li><a href="#trees">Trees</a></li>
      <li><a class="br" href="#history">History</a></li>
      <li><a href="#reps">Who represents you</a></li>
    </ul>
  </div>

  <aside class="key" id="projects" aria-label="Bigger projects">
    {blade('Map key', 'Bigger projects', 'build', 'or')}
    <ol>{key_rows}</ol>
    <div class="more"><span>{' &nbsp;&middot;&nbsp; '.join(f'<span style="white-space:nowrap">{c} {g.lower()}</span>' for g, c in pg.items() if g in BIG)}</span><a href="{link('Building biography')}">Look up a building &rarr;</a></div>
  </aside>
</section>

<div class="entries">

  <article class="entry wide" id="week">
    {blade('No. 01', 'This week', 'week', 'yl')}
    <div class="body">
      <p class="lead">Rodent complaints: <em>{lead['count']}</em>, up from {lead['previous']}</p>
      <p>DC Health rodent and vector control requests rose more than any other 311 type in the last 30 days. Bulk collection is still the most common request ({top_type['count']}).</p>
      <div class="stats three">
        <div class="stat or"><b>{tm['permits_30d']}</b><span>building permits issued</span></div>
        <div class="stat"><b>{n(tm['requests_30d'])}</b><span>311 requests, {req_word} from {n(tm['requests_prev_30d'])}</span></div>
        <div class="stat yl"><b>{tm['crime_30d']}</b><span>reported crimes, compared with {tm['crime_prev_30d']} the 30 days before</span></div>
      </div>
      <p class="sub">Other 311 changes</p>
      <ul class="moves">{other_moves}</ul>
      <p class="note">All counts cover the last 30 days, compared with the 30 days before.</p>
    </div>
    <div class="go"><a href="{link('311 report card')}">311 report card</a><a href="{link('Block Watch')}">Block Watch</a></div>
  </article>

  <article class="entry" id="streets">
    {blade('No. 02', 'Streets', 'streets')}
    <div class="body">
      <div class="stats">
        <div class="stat"><b>{s['curb_permits_active_this_week']}</b><span>curb permits active this week</span></div>
        <div class="stat yl"><b>{s['curb_permits_starting_next_7d']}</b><span>start in the next 7 days</span></div>
      </div>
      <p>{n(s['curb_reserved_ft'])} feet of curb are reserved under those permits.</p>
      <p class="sub">Top 311 requests, 30 days</p>
      <ul class="bars">{types_rows}</ul>
      <p class="sub">Permits by type, 30 days</p>
      <ul class="permit-groups">{legend_rows}</ul>
    </div>
    <div class="go"><a href="{link('Curb radar')}">Curb radar</a><a href="{link('311 report card')}">311 report card</a></div>
  </article>

  <article class="entry" id="homes">
    {blade('No. 03', 'Homes', 'homes')}
    <div class="body">
      <div class="stats">
        <div class="stat"><b>{h['median_house_price_12mo']}</b><span>median house price, last 12 months</span></div>
        <div class="stat"><b>{h['house_sales_12mo']}</b><span>house sales, last 12 months</span></div>
        <div class="stat or"><b>{h['median_price_60d']}</b><span>median price, last 60 days ({h['market_sales_60d']} sales)</span></div>
        <div class="stat"><b>{h['median_price_per_sqft_60d']}</b><span>per square foot, last 60 days</span></div>
      </div>
      <p>Is your assessment in line with what similar homes sold for? Compare it against nearby sales.</p>
    </div>
    <div class="go"><a href="{link('Assessment check')}">Check your assessment</a><a href="{link('Housing pulse')}">Housing pulse</a></div>
  </article>

  <article class="entry" id="trees">
    {blade('No. 04', 'Trees', 'trees')}
    <div class="body">
      <div class="stats">
        <div class="stat"><b>{n(t['street_trees'])}</b><span>street trees, {t['species']} species</span></div>
        <div class="stat"><b>{t['planted_last_5y']}</b><span>planted in the last 5 years</span></div>
      </div>
      <p><strong>{t['empty_boxes_open']} empty tree boxes</strong> are open, waiting for a tree.</p>
    </div>
    <div class="go"><a href="{link('Street trees')}">Street tree atlas</a></div>
  </article>

  <article class="entry" id="history">
    {blade('No. 05', 'History', 'history', 'br')}
    <div class="body">
      <p class="sub" style="margin-top:0">{e(hist['block'])}</p>
      <p>{e(hist['fact'])}</p>
      <p class="sub">100 years ago this week: {e(hist['hundred_years_ago_week'])}</p>
      <blockquote><span class="ocr">OCR TEXT</span><br>&ldquo;{e(hist['hundred_years_ago_excerpt_ocr'])}&rdquo;</blockquote>
      <p class="src">Source: {e(hist['hundred_years_ago_source'])}. Machine-read text; may contain errors.</p>
    </div>
    <div class="go"><a href="{link('100 years ago')}">100 years ago</a><a href="{link('Building biography')}">Building biography</a></div>
  </article>

  <article class="entry" id="reps">
    {blade('No. 06', 'Who represents you', 'people')}
    <div class="body">
      <p>Petworth spans {len(reps)} single-member districts (SMDs) in two Advisory Neighborhood Commissions. Your commissioner:</p>
      {rep_html}
      <p class="note">Commissioners are elected officials; names are public record. Find your SMD by looking up your block above.</p>
    </div>
  </article>

</div>

<section class="signup" aria-label="Subscribe">
  <h2>{icon('mail', '')}The weekly field notes</h2>
  <p>One email a week: new permits, 311 counts and curb permits for Petworth.</p>
  <div class="field"><input type="email" placeholder="you@example.com" aria-label="Email address"><a href="{link('Weekly email')}">Subscribe</a></div>
  <div class="alt"><a href="{link('Weekly email')}">See a sample issue &rarr;</a><a href="#rss">{icon('rss', '')}RSS feed</a></div>
</section>

<aside class="sponsor" aria-label="Sponsor"><div><small>Presented by</small><b>[Local sponsor]</b></div></aside>
</main>

<footer>
  <div class="wrap">
    <p><strong>Independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission, or any Business Improvement District.</strong></p>
    <p>Updated automatically every night. Sources: Open Data DC (CC BY 4.0); Library of Congress, Chronicling America.</p>
    <p>petworth.org &middot; data as of {stamp_txt}</p>
  </div>
</footer>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB), {n_pins}/{len(projects)} projects pinned")
