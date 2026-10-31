"""Layout C4: Map Console. Reads design/layouts/facts.json, writes design/layouts/C4-map-console.html.

Run from anywhere:  python design/layouts/src/C4_map_console.py
Python 3.13 stdlib only.

Idea: a split-screen console. Desktop: a sticky, gridded map fills the left half and the
dashboard scrolls on the right. Phone: the map is a ~200px sticky strip that expands on tap.
Project rows and numbered map markers highlight each other; category toggles filter the dots.
"""
from __future__ import annotations

import html
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYOUTS = HERE.parent
FACTS = json.loads((LAYOUTS / "facts.json").read_text(encoding="utf-8"))
OUT = LAYOUTS / "C4-map-console.html"

e = html.escape


# ---------- helpers ----------
def link(name: str) -> str:
    return "../../" + FACTS["demo_links"][name]


def fmt(n: int) -> str:
    return f"{n:,}"


def delta(cur: int, prev: int) -> dict:
    """Signed change. Percentages only when both counts are 100 or more."""
    d = cur - prev
    sign = "+" if d > 0 else ("−" if d < 0 else "±")
    pct = round(d / prev * 100) if cur >= 100 and prev >= 100 else None
    txt = f"{sign}{abs(d)}" + (f" ({sign}{abs(pct)}%)" if pct is not None else "")
    return {"d": d, "txt": txt, "cls": "up" if d > 0 else ("down" if d < 0 else "flat"), "pct": pct}


def title_case(s: str) -> str:
    keep = {"NW", "NE", "SW", "SE", "ADU"}
    return " ".join(w if w in keep or any(c.isdigit() for c in w) else w.capitalize() for w in s.split())


def addr(s: str) -> str:
    return title_case(re.sub(r"\s+\d{5}$", "", s.strip()))


def clean_work(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"([a-z])([A-Z][a-z])", r"\1 \2", s)  # "ADUNew" -> "ADU New" style run-ons
    return s + "…" if len(s) >= 150 else s


def to_eastern(dt: datetime) -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo("America/New_York"))
    except Exception:  # no tzdata: US DST rule by hand
        y = dt.year
        mar = datetime(y, 3, 8, 7, tzinfo=timezone.utc)
        mar += timedelta(days=(6 - mar.weekday()) % 7)
        nov = datetime(y, 11, 1, 6, tzinfo=timezone.utc)
        nov += timedelta(days=(6 - nov.weekday()) % 7)
        return dt.astimezone(timezone(timedelta(hours=-4 if mar <= dt < nov else -5)))


def bar(cur: float, m: float, cls: str) -> str:
    return (f'<svg class="hb" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true">'
            f'<rect class="trk" width="100" height="8"/><rect class="{cls}" width="{100 * cur / m:.1f}" height="8"/></svg>')


# ---------- derived data ----------
gen = datetime.fromisoformat(FACTS["generated_at"].replace("Z", "+00:00"))
gl = to_eastern(gen)
hour = gl.strftime("%I").lstrip("0")
asof = f"{gl.strftime('%b')} {gl.day}, {gl.year} · {hour}:{gl.strftime('%M %p')} ET"
asof_short = f"{gl.strftime('%b')} {gl.day}, {hour}:{gl.strftime('%M %p')} ET"

tm = FACTS["this_month"]
req = delta(tm["requests_30d"], tm["requests_prev_30d"])
crime = delta(tm["crime_30d"], tm["crime_prev_30d"])
movers = [dict(m, delta=delta(m["count"], m["previous"])) for m in tm["top_311_movers"]]
rises = sorted([m for m in movers if m["delta"]["d"] > 0], key=lambda m: -m["delta"]["d"])
lead = rises[0] if rises else max(movers, key=lambda m: abs(m["delta"]["d"]))
others = [m for m in movers if m is not lead]

SHORT = {"DC Health Rodent & Vector Control": "Rodent & vector control"}
LEAD_NAME = {"DC Health Rodent & Vector Control": "Rodent complaints"}


def short_type(t: str) -> str:
    return SHORT.get(t, t)


groups = FACTS["permit_groups"]
permits_total = tm["permits_30d"]
# key, label, glyph kind
CATS = [
    ("add", "Additions", "Additions", "num"),
    ("demo", "Demolition", "Demolition", "numsq"),
    ("newc", "New construction", "New construction", "num"),
    ("ren", "Renovation & repair", "Renovation & repair", "dot"),
    ("mep", "Electrical, plumbing & mechanical", "Electrical / plumbing", "ring"),
    ("home", "Home businesses", "Home businesses", "sq"),
    ("minor", "Minor work", "Minor work", "small"),
]
GKEY = {g: k for k, g, _, _ in CATS}
BIG = {"Additions", "Demolition", "New construction"}


def glyph(kind: str) -> str:
    """Small legend glyph matching the map symbol."""
    inner = {
        "num": '<circle cx="7" cy="7" r="5.5" class="gl-acc"/>',
        "numsq": '<rect x="1.5" y="1.5" width="11" height="11" class="gl-acc"/>',
        "dot": '<circle cx="7" cy="7" r="3.2" class="gl-ink"/>',
        "ring": '<circle cx="7" cy="7" r="3" class="gl-ring"/>',
        "sq": '<rect x="4" y="4" width="6" height="6" class="gl-ink"/>',
        "small": '<circle cx="7" cy="7" r="2" class="gl-mut"/>',
    }[kind]
    return f'<svg class="gl" viewBox="0 0 14 14" width="14" height="14" aria-hidden="true">{inner}</svg>'


# Projects, each matched to its permit point: same group, same order as in permit_points.
pts = FACTS["permit_points"]
used: set[int] = set()
projects = []
for i, p in enumerate(FACTS["bigger_projects"], 1):
    issued = datetime.fromisoformat(p["issued"].replace("Z", "+00:00"))
    age = (gen.date() - issued.date()).days
    idx = next((j for j, q in enumerate(pts) if j not in used and q["group"] == p["group"]), None)
    if idx is not None:
        used.add(idx)
    projects.append({
        "n": i, "id": f"p{i}", "addr": addr(p["address"]), "group": p["group"], "key": GKEY[p["group"]],
        "issued": issued, "date": f"{issued.strftime('%b')} {issued.day}", "new": 0 <= age <= 7,
        "work": clean_work(p["work"]), "pt": pts[idx] if idx is not None else None,
    })
new_count = sum(p["new"] for p in projects)

homes = FACTS["homes"]
streets = FACTS["streets"]
trees = FACTS["trees"]
hist = FACTS["history"]
reps = FACTS["representatives"]

# ---------- map ----------
rings = FACTS["boundary_rings"]
allp = [q for r in rings for q in r]
minx, maxx = min(q[0] for q in allp), max(q[0] for q in allp)
miny, maxy = min(q[1] for q in allp), max(q[1] for q in allp)
# Neatline frame: boundary bbox plus a margin, snapped to 0.0005 degrees.
M = 0.0012
F_W, F_E = math.floor((minx - M) / 0.0005) * 0.0005, math.ceil((maxx + M) / 0.0005) * 0.0005
F_S, F_N = math.floor((miny - M) / 0.0005) * 0.0005, math.ceil((maxy + M) / 0.0005) * 0.0005
KLAT = math.cos(math.radians((miny + maxy) / 2))
VBW = 600.0
SC = VBW / ((F_E - F_W) * KLAT)       # viewBox units per degree of latitude
VBH = (F_N - F_S) * SC
X = lambda lon: (lon - F_W) * KLAT * SC
Y = lambda lat: (F_N - lat) * SC
M_PER_UNIT = 111_320 / SC
CENTER = ((miny + maxy) / 2, (minx + maxx) / 2)


def map_svg() -> str:
    out = []
    # extended faint grid (shows beyond the frame when the strip is wider than the map)
    ext = 0.03
    lon = math.floor((F_W - ext) / 0.001) * 0.001
    fine, major = [], []
    while lon <= F_E + ext:
        x = X(lon)
        (major if abs(round(lon / 0.005) * 0.005 - lon) < 1e-9 else fine).append(f"M{x:.1f},{Y(F_N + ext):.0f}V{Y(F_S - ext):.0f}")
        lon += 0.001
    lat = math.floor((F_S - ext) / 0.001) * 0.001
    while lat <= F_N + ext:
        y = Y(lat)
        (major if abs(round(lat / 0.005) * 0.005 - lat) < 1e-9 else fine).append(f"M{X(F_W - ext):.0f},{y:.1f}H{X(F_E + ext):.0f}")
        lat += 0.001
    out.append(f'<path class="g-fine" d="{"".join(fine)}"/><path class="g-major" d="{"".join(major)}"/>')
    out.append(f'<rect class="frame" x="0" y="0" width="{VBW:.0f}" height="{VBH:.1f}"/>')
    # boundary
    d = " ".join("M" + "L".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in r) + "Z" for r in rings)
    out.append(f'<path class="bnd-halo" d="{d}"/><path class="bnd" d="{d}"/>')
    # graticule labels on the frame edges (scaled to screen size)
    lab = []
    v = math.ceil(F_W / 0.005) * 0.005
    while v < F_E - 1e-9:
        lab.append(f'<g transform="translate({X(v):.1f},0)"><g class="s"><text class="gt" x="3" y="11">{abs(v):.3f}°W</text></g></g>')
        v += 0.005
    v = math.ceil(F_S / 0.005) * 0.005
    while v < F_N - 1e-9:
        lab.append(f'<g transform="translate(0,{Y(v):.1f})"><g class="s"><text class="gt" x="4" y="-4">{v:.3f}°N</text></g></g>')
        v += 0.005
    out.append("".join(lab))
    # scale bar: 500 m, true length in viewBox units
    sb = 500 / M_PER_UNIT
    out.append(f'<g class="scale" transform="translate({VBW - 16 - sb:.1f},{VBH - 16:.1f})">'
               f'<path class="sb" d="M0,0H{sb:.1f}M0,-5V0M{sb / 2:.1f},-3V0M{sb:.1f},-5V0"/>'
               f'<g class="s"><text class="gt" x="0" y="-8">0</text></g>'
               f'<g transform="translate({sb:.1f},0)"><g class="s"><text class="gt" x="0" y="-8" text-anchor="end">500 m</text></g></g></g>')
    # north arrow
    out.append(f'<g transform="translate({VBW - 22:.0f},24)"><g class="s"><path class="na" d="M0,-12L6,6L0,2L-6,6Z"/>'
               f'<text class="gt" x="0" y="18" text-anchor="middle">N</text></g></g>')
    # small permits
    small = []
    for j, q in enumerate(pts):
        if j in used:
            continue
        key = GKEY.get(q["group"], "minor")
        shape = {"ren": '<circle r="3.4"/>', "mep": '<circle r="3"/>', "home": '<rect x="-3" y="-3" width="6" height="6"/>',
                 "minor": '<circle r="2.2"/>', "add": '<circle r="3.4"/>', "demo": '<circle r="3.4"/>', "newc": '<circle r="3.4"/>'}[key]
        small.append(f'<g class="pt c-{key}" transform="translate({X(q["lon"]):.1f},{Y(q["lat"]):.1f})"><g class="s">{shape}</g>'
                     f'<title>{e(q["group"])}</title></g>')
    out.append(f'<g class="pts">{"".join(small)}</g>')
    # big numbered markers, drawn last so they sit on top; later numbers first so 1 is topmost
    bigm = []
    for p in reversed(projects):
        q = p["pt"]
        if not q:
            continue
        shape = ('<rect class="mk-b" x="-9" y="-9" width="18" height="18"/>' if p["key"] == "demo"
                 else '<circle class="mk-b" r="9.5"/>')
        bigm.append(
            f'<g class="mk c-{p["key"]}" data-id="{p["id"]}" data-lat="{q["lat"]}" data-lon="{q["lon"]}" data-addr="{e(p["addr"])}" '
            f'tabindex="0" role="button" aria-label="Project {p["n"]}: {e(p["addr"])}, {e(p["group"])}" '
            f'transform="translate({X(q["lon"]):.1f},{Y(q["lat"]):.1f})"><g class="s ms">'
            f'<circle class="mk-halo" r="17"/>{shape}<text class="mk-t" y="3.6" text-anchor="middle">{p["n"]}</text></g></g>')
    out.append(f'<g class="mks">{"".join(bigm)}</g>')
    return (f'<svg id="map" class="map" viewBox="0 0 {VBW:.0f} {VBH:.1f}" preserveAspectRatio="xMidYMid meet" '
            f'data-w="{F_W}" data-n="{F_N}" data-k="{KLAT}" data-sc="{SC}" role="img" '
            f'aria-label="Map of Petworth: {permits_total} building permits from the last 30 days. Numbered markers are the {len(projects)} bigger projects listed beside the map.">'
            + "".join(out) + "</svg>")


# ---------- sections ----------
def toggle_btn(k: str, label: str, kind: str, n: int, cls: str = "chip") -> str:
    return (f'<button type="button" class="{cls}" data-g="{k}" aria-pressed="true">{glyph(kind)}'
            f'<span class="cl">{e(label)}</span><b class="num">{n}</b></button>')


present = [(k, g, s, kind) for k, g, s, kind in CATS if groups.get(g)]
chips = (f'<button type="button" class="chip all" data-all aria-pressed="true"><span class="cl">All</span><b class="num">{permits_total}</b></button>'
         + "".join(toggle_btn(k, s, kind, groups[g]) for k, g, s, kind in present))

maxg = max(groups.values())
mix_rows = "".join(
    f'<li><button type="button" class="mixrow" data-g="{k}" aria-pressed="true">{glyph(kind)}'
    f'<span class="ml">{e(g)}</span>{bar(groups[g], maxg, "fill" + (" acc" if g in BIG else ""))}'
    f'<b class="num">{groups[g]}</b></button></li>'
    for k, g, s, kind in present)

proj_rows = "".join(f"""
<li class="prow c-{p['key']}" data-id="{p['id']}" tabindex="0" aria-label="Project {p['n']}, {e(p['addr'])}">
  <span class="pn {'sq' if p['key'] == 'demo' else ''} num">{p['n']}</span>
  <div class="pb">
    <div class="pt1"><span class="paddr">{e(p['addr'])}</span><time class="pdate num" datetime="{p['issued'].date().isoformat()}">{p['date']}</time></div>
    <div class="pt2"><span class="ptype">{'Addition' if p['group'] == 'Additions' else e(p['group'])}</span>{'<span class="new">New this week</span>' if p['new'] else ''}{f'<span class="coord num">{p["pt"]["lat"]:.4f}°N {abs(p["pt"]["lon"]):.4f}°W</span>' if p['pt'] else ''}</div>
    <div class="pwork">{e(p['work'])}</div>
  </div>
</li>""" for p in projects)

ld = lead["delta"]
lm = max(lead["count"], lead["previous"])
rm = max(tm["requests_30d"], tm["requests_prev_30d"])


def cmp_rows(label, cur, prev, m, d, cls_cur):
    return f"""
<div class="cr">
  <div class="cr-h"><span>{label}</span><span class="chg {d['cls']} num">{d['txt']}</span></div>
  <div class="cr-r"><span class="k">Last 30 days</span>{bar(cur, m, cls_cur)}<span class="v num">{fmt(cur)}</span></div>
  <div class="cr-r"><span class="k">30 days before</span>{bar(prev, m, 'prev')}<span class="v num">{fmt(prev)}</span></div>
</div>"""


also = "".join(
    f'<li><span class="arw {m["delta"]["cls"]}" aria-hidden="true">{"▲" if m["delta"]["d"] > 0 else "▼"}</span>'
    f'<span class="al">{e(short_type(m["type"]))}</span><span class="num av">{m["count"]}</span>'
    f'<span class="num ap">from {m["previous"]}</span><span class="chg {m["delta"]["cls"]} num">{m["delta"]["txt"]}</span></li>'
    for m in others)

max311 = max(max(t["count"], t["previous"]) for t in tm["top_311_types"])
rank_rows = ""
for i, t in enumerate(tm["top_311_types"], 1):
    d = delta(t["count"], t["previous"])
    rank_rows += f"""
<tr>
  <td class="ri num">{i:02d}</td>
  <td class="rn"><span>{e(short_type(t['type']))}</span>
    <svg class="rb" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="6"/><rect class="{'fill acc' if t is lead or t['type'] == lead['type'] else 'fill'}" width="{100 * t['count'] / max311:.1f}" height="6"/><rect class="tick" x="{100 * t['previous'] / max311 - 0.5:.1f}" y="-2" width="1" height="10"/></svg></td>
  <td class="rc num">{t['count']}</td>
  <td class="rp num">{t['previous']}</td>
  <td class="rd num chg {d['cls']}">{d['txt'].split(' ')[0]}</td>
</tr>"""

curb_mi = streets["curb_reserved_ft"] / 5280

rep_rows = ""
for r in reps:
    rep_rows += (f'<tr><td class="smd num">{r["smd"]}</td><td class="cname">{e(title_case(r["commissioner"]))}</td>'
                 f'<td class="anc"><a href="{e(r["url"])}">ANC {r["anc"]} ↗</a></td></tr>')

ICON_SEARCH = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'


def sh(num: str, title: str, right: str = "") -> str:
    return f'<div class="sh"><span class="sn num">{num}</span><h2>{title}</h2><span class="sr">{right}</span></div>'


CSS = r"""
:root{
  --bg:#f4f4f1; --panel:#ffffff; --map-bg:#ecece7; --ink:#14161a; --ink-2:#3f444c; --muted:#757a82;
  --line:#dedfd9; --line-2:#ebebe6; --grid-f:#e0e0da; --grid-m:#cfd0c9;
  --acc:#ff5a1f; --acc-ink:#c43d0a; --acc-soft:#ffe7dc; --on-acc:#ffffff;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --hdr:0px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--sans)}
a{color:var(--acc-ink);text-decoration:none}
a:hover{text-decoration:underline}
.num{font-variant-numeric:tabular-nums}
.mono{font-family:var(--mono)}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}

.layout-tag{font:600 10.5px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;background:var(--ink);color:var(--bg);padding:6px 16px;display:flex;justify-content:space-between;gap:10px}
.layout-tag span:last-child{opacity:.6;white-space:nowrap}

/* header */
.top{background:var(--panel);border-bottom:1px solid var(--line)}
.top-in{padding:12px 16px;display:grid;gap:10px}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.brand>div{min-width:0}
.mark{flex:none;width:30px;height:30px;border:1.5px solid var(--ink);display:grid;place-items:center;position:relative}
.mark::before,.mark::after{content:"";position:absolute;background:var(--ink)}
.mark::before{width:1px;height:100%;left:50%}.mark::after{height:1px;width:100%;top:50%}
.mark i{position:relative;z-index:1;width:9px;height:9px;border-radius:50%;background:var(--acc);box-shadow:0 0 0 2px var(--panel)}
.brand h1{margin:0;font-size:20px;line-height:1.05;letter-spacing:-.01em;font-weight:700}
.brand p{margin:2px 0 0;font-size:12.5px;color:var(--muted);line-height:1.3}
.asof{margin-left:auto;flex:none;text-align:right;font:500 10.5px/1.35 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.asof b{display:block;color:var(--ink);font-weight:600;letter-spacing:0;text-transform:none;font-size:11.5px}
.live{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--acc);margin-right:5px;vertical-align:1px}
.sbox{display:flex;align-items:center;gap:8px;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:0 5px 0 11px;height:44px}
.sbox:focus-within{border-color:var(--ink)}
.sbox svg{flex:none;color:var(--muted)}
.sbox input{flex:1;min-width:0;border:0;background:transparent;font:inherit;font-size:15px;color:var(--ink);outline:none;height:100%}
.sbox input::placeholder{color:var(--muted)}
.sbox button{flex:none;border:0;background:var(--ink);color:var(--bg);font:600 13px var(--sans);border-radius:5px;padding:8px 12px;cursor:pointer}
.shint{display:flex;gap:4px 10px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:-2px}
.shint a{font-weight:500}

/* ===== console split ===== */
.console{position:relative}
.mapwrap{position:sticky;top:0;z-index:20;height:200px;background:var(--map-bg);border-bottom:1px solid var(--line);display:flex;flex-direction:column;transition:height .25s ease}
.mapwrap.open{height:min(78vh,640px);height:min(78svh,640px)}
.mbar{flex:none;display:flex;align-items:center;gap:8px;padding:0 8px 0 12px;height:32px;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--map-bg) 70%,var(--panel));font:500 10.5px/1 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink-2)}
.mbar .mt{font-weight:600;color:var(--ink);white-space:nowrap}
.mbar .mc{color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.xbtn{margin-left:auto;flex:none;border:1px solid var(--line);background:var(--panel);border-radius:5px;height:24px;padding:0 8px;font:600 10.5px/1 var(--mono);letter-spacing:.04em;text-transform:uppercase;cursor:pointer;display:flex;align-items:center;gap:5px}
.stage{position:relative;flex:1;min-height:0;overflow:hidden;cursor:crosshair}
.map{position:absolute;inset:8px 10px;width:calc(100% - 20px);height:calc(100% - 16px);overflow:visible;display:block;--k:1;--ms:1}
.mapwrap:not(.open) .map{--ms:.72}
.mapwrap:not(.open) .gt{display:none}
.mapwrap:not(.open) .readout:not(.on){display:none}
.s{transform:scale(calc(var(--k) * var(--ms)))}
.map text{font-family:var(--mono)}
.g-fine{stroke:var(--grid-f);stroke-width:.6;fill:none;vector-effect:non-scaling-stroke}
.g-major{stroke:var(--grid-m);stroke-width:1;fill:none;vector-effect:non-scaling-stroke}
.frame{fill:none;stroke:var(--ink-2);stroke-width:1;vector-effect:non-scaling-stroke}
.bnd-halo{fill:color-mix(in srgb,var(--panel) 72%,transparent);stroke:none}
.bnd{fill:none;stroke:var(--ink);stroke-width:1.6;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.gt{font-size:9px;fill:var(--muted);letter-spacing:.02em}
.sb,.na{stroke:var(--ink);stroke-width:1.2;fill:none;vector-effect:non-scaling-stroke}
.na{fill:var(--ink);stroke:none}
.pt circle,.pt rect{fill:var(--ink);opacity:.82}
.pt.c-mep circle{fill:var(--panel);stroke:var(--ink);stroke-width:1.3;opacity:1}
.pt.c-minor circle{fill:var(--muted);opacity:.75}
.pt.c-home rect{fill:var(--ink-2)}
.mk{cursor:pointer;outline:none}
.mk-b{fill:var(--acc);stroke:var(--panel);stroke-width:1.6}
.mk.c-demo .mk-b{fill:var(--ink);stroke:var(--acc);stroke-width:2}
.mk-t{font:700 10.5px var(--mono);fill:var(--on-acc);pointer-events:none}
.mk-halo{fill:var(--acc);opacity:0;transition:opacity .15s}
.mk.hot .mk-halo,.mk:focus-visible .mk-halo{opacity:.25}
.mk.hot .ms{transform:scale(calc(var(--k) * 1.25))}
.ms{transition:transform .15s}
.mks.dim .mk:not(.hot){opacity:.4}
.mk:focus-visible .mk-b{stroke:var(--ink);stroke-width:2.4}
/* filter: body.hide-<key> */
body.hide-add .c-add.pt, body.hide-add .mk.c-add,
body.hide-demo .c-demo.pt, body.hide-demo .mk.c-demo,
body.hide-ren .pt.c-ren, body.hide-mep .pt.c-mep, body.hide-home .pt.c-home, body.hide-minor .pt.c-minor{display:none}
body.hide-add .prow.c-add, body.hide-demo .prow.c-demo{opacity:.38}

.readout{position:absolute;left:10px;bottom:8px;z-index:2;font:500 10.5px/1.3 var(--mono);background:color-mix(in srgb,var(--panel) 90%,transparent);border:1px solid var(--line);border-radius:4px;padding:4px 7px;color:var(--ink-2);max-width:calc(100% - 20px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:none}
.readout b{color:var(--acc-ink);font-weight:600}
.mfoot{flex:none;border-top:1px solid var(--line);background:var(--panel);padding:8px 10px;display:none}
.mapwrap.open .mfoot{display:block}
.chips{display:flex;gap:5px;flex-wrap:wrap}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--panel);border-radius:5px;padding:4px 7px;font-size:12px;cursor:pointer;white-space:nowrap}
.chip b{font:600 11px var(--mono);color:var(--muted)}
.chip[aria-pressed="false"]{background:transparent;color:var(--muted);border-style:dashed}
.chip[aria-pressed="false"] .gl{opacity:.35}
.chip.all[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.chip.all[aria-pressed="true"] b{color:var(--bg);opacity:.7}
.gl{flex:none;display:block}
.gl-acc{fill:var(--acc)} .gl-ink{fill:var(--ink)} .gl-ring{fill:none;stroke:var(--ink);stroke-width:1.3} .gl-mut{fill:var(--muted)}
.mkey{display:flex;gap:4px 12px;flex-wrap:wrap;margin-top:7px;font:500 10.5px/1.3 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.mkey span{display:inline-flex;align-items:center;gap:5px}

/* ===== dashboard ===== */
.dash{padding:0 16px 8px;min-width:0}
section{padding:22px 0 6px;border-bottom:1px solid var(--line);scroll-margin-top:210px}
section:last-of-type{border-bottom:0}
.sh{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:baseline;margin-bottom:12px}
.sn{font:600 11px var(--mono);color:var(--acc-ink)}
.sh h2{margin:0;font:600 11.5px/1.2 var(--mono);letter-spacing:.1em;text-transform:uppercase}
.sr{font-size:12.5px;color:var(--muted);text-align:right}
.sr a{font-weight:600;white-space:nowrap}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px}
.chg{font-weight:600}
.chg.up{color:var(--acc-ink)} .chg.down{color:var(--ink-2)} .chg.flat{color:var(--muted)}

/* lead */
.kick{font:500 11px/1.3 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.tag-up{font:700 10.5px/1 var(--mono);background:var(--acc);color:var(--on-acc);padding:4px 6px;border-radius:3px;letter-spacing:.04em}
.lede{margin:10px 0 14px;font-size:22px;line-height:1.28;letter-spacing:-.012em;font-weight:600;text-wrap:pretty}
.lede em{font-style:normal;color:var(--acc-ink)}
.cmpgrid{display:grid;gap:10px}
.cr{padding:11px 12px 10px}
.cr-h{display:flex;justify-content:space-between;gap:8px;font-size:13px;font-weight:600;margin-bottom:6px}
.cr-r{display:grid;grid-template-columns:92px 1fr 46px;gap:8px;align-items:center;font-size:11.5px;color:var(--muted);padding:2px 0}
.cr-r .v{text-align:right;color:var(--ink);font:600 13px var(--mono)}
.hb{width:100%;height:8px;display:block}
svg .trk{fill:var(--line-2)}
svg .fill{fill:var(--ink-2)}
svg .fill.acc,svg .acc{fill:var(--acc)}
svg .prev{fill:#c4c6c0}
svg .tick{fill:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin-top:10px}
.stat{padding:11px 12px;border-left:1px solid var(--line-2);min-width:0;color:inherit;display:block}
.stat:first-child{border-left:0}
a.stat:hover{text-decoration:none;background:var(--bg)}
.stat .l{font:500 10.5px/1.2 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.stat .v{font-size:26px;font-weight:700;letter-spacing:-.02em;line-height:1.1;margin-top:5px}
.stat .c{font-size:11.5px;color:var(--muted);margin-top:3px;line-height:1.35}
.also{list-style:none;margin:10px 0 0;padding:0}
.also li{display:grid;grid-template-columns:12px 1fr auto auto auto;gap:8px;align-items:baseline;padding:7px 2px;border-top:1px solid var(--line-2);font-size:13px}
.also-h{font:500 10.5px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:12px}
.arw{font-size:9px}.arw.up{color:var(--acc-ink)}.arw.down{color:var(--muted)}
.av{font-weight:600}.ap{color:var(--muted);font-size:12px}
.also .chg{font-size:12px;min-width:66px;text-align:right}

/* projects */
.plist{list-style:none;margin:0;padding:0}
.prow{display:grid;grid-template-columns:28px 1fr;gap:10px;padding:11px 12px;border-top:1px solid var(--line-2);cursor:default;outline:none;transition:background .12s;position:relative}
.prow:first-child{border-top:0}
.prow::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:transparent}
.prow.hot{background:var(--acc-soft)}
.prow.hot::before{background:var(--acc)}
.prow:focus-visible{box-shadow:inset 0 0 0 2px var(--acc)}
.pn{width:24px;height:24px;border-radius:50%;background:var(--acc);color:var(--on-acc);display:grid;place-items:center;font:700 11.5px/1 var(--mono);margin-top:1px}
.pn.sq{border-radius:2px;background:var(--ink);box-shadow:inset 0 0 0 2px var(--acc)}
.pt1{display:flex;gap:8px;align-items:baseline}
.paddr{font-weight:600;font-size:15px;min-width:0}
.pdate{margin-left:auto;font:500 11.5px var(--mono);color:var(--muted);white-space:nowrap}
.pt2{display:flex;gap:4px 10px;flex-wrap:wrap;align-items:center;margin-top:2px;font-size:12px;color:var(--ink-2)}
.ptype{font-weight:500}
.new{font:700 9.5px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--acc-ink);border:1px solid var(--acc);border-radius:3px;padding:3px 5px}
.coord{font:400 10.5px var(--mono);color:var(--muted)}
.pwork{font-size:12.5px;color:var(--muted);margin-top:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
.pfoot{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;padding:9px 12px;border-top:1px solid var(--line);font:500 11px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.pfoot a{font-weight:600}
.mix{margin-top:10px}
.mix-h{display:flex;justify-content:space-between;gap:8px;padding:10px 12px 4px;font:500 10.5px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.mix ul{list-style:none;margin:0;padding:0 4px 6px}
.mixrow{width:100%;display:grid;grid-template-columns:14px minmax(0,1.3fr) minmax(0,1fr) 28px;gap:9px;align-items:center;border:0;background:none;padding:6px 8px;border-radius:5px;cursor:pointer;text-align:left;font-size:13px}
.mixrow:hover{background:var(--bg)}
.mixrow b{text-align:right;font:600 12.5px var(--mono)}
.mixrow .ml{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mixrow[aria-pressed="false"]{color:var(--muted)}
.mixrow[aria-pressed="false"] svg{opacity:.3}
.mixrow[aria-pressed="false"] .ml{text-decoration:line-through}

/* homes */
.homes{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line-2);overflow:hidden}
.homes>*{background:var(--panel);border:0!important}
.homes .hero{grid-column:1 / -1;padding:14px 12px}
.homes .hero .v{font-size:36px}
.homes .cta{grid-column:1 / -1;border-top:0}
.cta{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 12px;border-top:1px solid var(--line);font-weight:600;font-size:13.5px;color:var(--ink)}
.cta span{color:var(--acc-ink);font-size:12.5px;white-space:nowrap}
.cta:hover{text-decoration:none;background:var(--bg)}

/* streets */
.stack{display:grid;gap:10px}
.tbl-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%}
.t311 th{font:500 10px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em;text-align:right;padding:9px 6px 5px;border-bottom:1px solid var(--line)}
.t311 th:nth-child(2){text-align:left}
.t311 td{padding:7px 6px;border-bottom:1px solid var(--line-2);font-size:13px;vertical-align:middle}
.t311 tr:last-child td{border-bottom:0}
.ri{font:500 10.5px var(--mono);color:var(--muted);width:26px;padding-left:12px!important}
.rn span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:190px}
.rb{display:block;width:100%;height:6px;margin-top:4px;overflow:visible}
.rc,.rp,.rd{text-align:right;font-family:var(--mono);font-size:12.5px;white-space:nowrap}
.rc{font-weight:600}.rp{color:var(--muted)}
.rd{padding-right:12px!important}
.tlegend{display:flex;gap:14px;padding:8px 12px 10px;font:500 10px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.05em;border-top:1px solid var(--line-2)}
.tlegend i{display:inline-block;vertical-align:0;margin-right:5px}
.stats.s4{grid-template-columns:1fr 1fr}
.stats.s4 .stat:nth-child(odd){border-left:0}
.stats.s4 .stat:nth-child(n+3){border-top:1px solid var(--line-2)}
.stats.flush{margin-top:0}
.v.acc{color:var(--acc-ink)}

/* archives */
.arch{display:grid;gap:10px}
.acard{padding:14px 14px 12px}
.ak{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font:500 10.5px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.abig{display:flex;gap:18px;margin:10px 0 8px}
.abig div{font:700 26px/1 var(--sans);letter-spacing:-.02em}
.abig small{display:block;font:500 10.5px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:4px}
.acard p{margin:0;font-size:14px;color:var(--ink-2)}
.ocr{font:600 9.5px/1 var(--mono);border:1px solid var(--ink-2);color:var(--ink-2);padding:3px 5px;border-radius:3px;letter-spacing:.06em}
.clip{margin:10px 0 0;padding:12px 14px;background:#f6f3ea;border:1px solid #e6e0cf;font:17px/1.4 Georgia,"Times New Roman",serif;color:#2b2a26;position:relative}
.clip::before{content:"“";position:absolute;left:5px;top:-2px;font-size:28px;color:#b9b19a}
.src{font-size:11.5px;color:var(--muted);margin-top:8px;line-height:1.4}
.alink{display:inline-block;margin-top:8px;font-weight:600;font-size:13px}

/* reps */
.treps td{padding:9px 12px;border-top:1px solid var(--line-2);font-size:14px}
.treps tr:first-child td{border-top:0}
.smd{font:600 12px var(--mono);color:var(--acc-ink);width:56px}
.anc{text-align:right;font-size:12.5px;white-space:nowrap}
.note{font-size:12px;color:var(--muted);margin:8px 0 0}

/* subscribe */
.subc{padding:14px}
.subc h3{margin:0;font-size:16px}
.subc p{margin:3px 0 0;font-size:13px;color:var(--muted)}
.sub-row{display:flex;gap:8px;margin-top:10px}
.sub-row input{flex:1;min-width:0;height:42px;border:1px solid var(--line);border-radius:6px;padding:0 12px;font:inherit;background:var(--bg);color:var(--ink)}
.sub-row button{height:42px;border:0;border-radius:6px;background:var(--acc);color:var(--on-acc);font:600 14px var(--sans);padding:0 16px;cursor:pointer}
.subnote{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px}
.sponsor{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px;padding:12px 14px;border:1px dashed var(--grid-m);border-radius:8px;font-size:13px;color:var(--ink-2);background:repeating-linear-gradient(135deg,transparent 0 8px,rgba(0,0,0,.018) 8px 9px)}
.sponsor small{font:600 10px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}

footer{border-top:1px solid var(--line);padding:16px 0 28px;font-size:12px;color:var(--muted)}
footer p{margin:0 0 6px}
footer strong{color:var(--ink-2)}
footer .mono{font-size:11px}

/* ===== desktop split ===== */
@media (min-width:960px){
  body{font-size:15.5px}
  .top-in{grid-template-columns:auto minmax(320px,520px);justify-content:space-between;align-items:center;padding:12px 24px;gap:24px}
  .brand{gap:12px}
  .asof{margin-left:24px}
  .shint{grid-column:2;margin-top:-6px}
  .console{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
  .mapwrap,.mapwrap.open{height:100vh;height:100svh;border-bottom:0;border-right:1px solid var(--line);z-index:1}
  .mbar{height:38px;padding:0 14px}
  .xbtn{display:none}
  .map{inset:16px 18px;width:calc(100% - 36px);height:calc(100% - 32px);--ms:1}
  .mapwrap:not(.open) .map{--ms:1}
  .mapwrap:not(.open) .gt{display:inline}
  .mfoot{display:block;padding:10px 14px 12px}
  .readout{left:18px;bottom:14px}
  .dash{padding:0 32px 8px;max-width:760px}
  section{scroll-margin-top:12px;padding-top:28px}
  .lede{font-size:27px}
  .cmpgrid{grid-template-columns:1fr 1fr}
  .homes{grid-template-columns:1.2fr 1fr 1fr}
  .homes .hero{grid-column:1;grid-row:1 / span 2;display:flex;flex-direction:column;justify-content:center}
  .arch{grid-template-columns:1fr 1fr}
  .stats.s4{grid-template-columns:repeat(4,minmax(0,1fr))}
  .stats.s4 .stat:nth-child(n){border-left:1px solid var(--line-2);border-top:0}
  .stats.s4 .stat:first-child{border-left:0}
  .rn span{max-width:none}
}
@media (min-width:1280px){
  .console{grid-template-columns:minmax(0,1fr) minmax(600px,720px)}
  .dash{padding:0 40px 8px}
}
"""

JS = r"""
(function(){
  var map=document.getElementById('map'), wrap=document.getElementById('mapwrap'), stage=map.parentNode;
  var ro=document.getElementById('readout'), def=ro.innerHTML;
  var vb=map.viewBox.baseVal, W=+map.dataset.w, N=+map.dataset.n, K=+map.dataset.k, SC=+map.dataset.sc;
  function fit(){var r=map.getBoundingClientRect(); if(!r.width) return;
    var s=Math.min(r.width/vb.width,r.height/vb.height); map.style.setProperty('--k',(1/s).toFixed(4));}
  fit(); if(window.ResizeObserver){new ResizeObserver(fit).observe(map);} else {window.addEventListener('resize',fit);}
  map.addEventListener('transitionend',fit); wrap.addEventListener('transitionend',fit);
  function ll(lat,lon){return Math.abs(lat).toFixed(5)+'°N  '+Math.abs(lon).toFixed(5)+'°W';}
  // cursor readout
  map.addEventListener('mousemove',function(ev){ if(document.querySelector('.mk.hot')) return;
    var m=map.getScreenCTM(); if(!m) return; var p=new DOMPoint(ev.clientX,ev.clientY).matrixTransform(m.inverse());
    var lon=W+p.x/(K*SC), lat=N-p.y/SC; ro.innerHTML='Cursor  '+ll(lat,lon);});
  map.addEventListener('mouseleave',function(){ if(!document.querySelector('.mk.hot')) ro.innerHTML=def;});
  // linked highlight
  function hot(id,on){
    document.querySelectorAll('[data-id="'+id+'"]').forEach(function(el){el.classList.toggle('hot',on);});
    document.querySelector('.mks').classList.toggle('dim',on);
    var mk=document.querySelector('.mk[data-id="'+id+'"]');
    if(on&&mk){ro.innerHTML='<b>'+id.slice(1)+'</b>  '+mk.dataset.addr+'  ·  '+ll(+mk.dataset.lat,+mk.dataset.lon);
      mk.parentNode.appendChild(mk);}
    else ro.innerHTML=def;
    ro.classList.toggle('on',on);
  }
  document.querySelectorAll('[data-id]').forEach(function(el){
    var id=el.dataset.id;
    el.addEventListener('mouseenter',function(){hot(id,true);});
    el.addEventListener('mouseleave',function(){hot(id,false);});
    el.addEventListener('focus',function(){hot(id,true);});
    el.addEventListener('blur',function(){hot(id,false);});
  });
  // marker -> row
  document.querySelectorAll('.mk').forEach(function(mk){
    function go(ev){ ev.stopPropagation(); if(!wrap.classList.contains('open') && innerWidth<960){setOpen(true);return;}
      var row=document.querySelector('.prow[data-id="'+mk.dataset.id+'"]');
      if(innerWidth<960) setOpen(false);
      row.scrollIntoView({behavior:'smooth',block:'center'}); row.focus({preventScroll:true});}
    mk.addEventListener('click',go);
    mk.addEventListener('keydown',function(ev){if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();go(ev);}});
  });
  // phone strip expand
  var xb=document.getElementById('xbtn');
  function setOpen(o){wrap.classList.toggle('open',o); xb.setAttribute('aria-expanded',o);
    xb.querySelector('span').textContent=o?'Collapse':'Expand'; setTimeout(fit,280);}
  xb.addEventListener('click',function(){setOpen(!wrap.classList.contains('open'));});
  stage.addEventListener('click',function(){ if(innerWidth<960 && !wrap.classList.contains('open')) setOpen(true);});
  // category filters (map chips + permit-mix rows stay in sync)
  var keys=[].slice.call(document.querySelectorAll('.chips [data-g]')).map(function(b){return b.dataset.g;});
  var off={};
  function sync(){ keys.forEach(function(k){document.body.classList.toggle('hide-'+k,!!off[k]);
      document.querySelectorAll('[data-g="'+k+'"]').forEach(function(b){b.setAttribute('aria-pressed',!off[k]);});});
    var any=keys.some(function(k){return off[k];});
    document.querySelector('[data-all]').setAttribute('aria-pressed',!any);
    var shown=keys.reduce(function(s,k){return s+(off[k]?0:+document.querySelector('.chips [data-g="'+k+'"] b').textContent);},0);
    document.getElementById('shown').textContent=shown;}
  document.querySelectorAll('[data-g]').forEach(function(b){b.addEventListener('click',function(){
    var k=b.dataset.g, solo=keys.every(function(x){return !off[x];});
    if(solo){keys.forEach(function(x){off[x]=x!==k;});} else {off[k]=!off[k]; if(keys.every(function(x){return off[x];})) off={};}
    sync();});});
  document.querySelector('[data-all]').addEventListener('click',function(){off={};sync();});
})();
"""

lead_word = "up" if ld["d"] > 0 else "down"
lede = e(FACTS["lead_sentence"])
cx_lat, cx_lon = CENTER
default_readout = f"Center  {cx_lat:.5f}°N  {abs(cx_lon):.5f}°W"

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth Map Console</title>
<meta name="description" content="What's changing in Petworth, Washington DC, from DC's own open data. Independent; updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="Petworth permits" href="/petworth/permits.xml">
<style>{CSS}</style>
</head>
<body>
<div class="layout-tag"><span>Layout C4: Map Console</span><span>{CENTER[0]:.3f}°N {abs(CENTER[1]):.3f}°W</span></div>

<header class="top"><div class="top-in">
  <div class="brand">
    <div class="mark" aria-hidden="true"><i></i></div>
    <div><h1>{e(FACTS['neighborhood'])}</h1><p>What's changing in Petworth, from DC's own data</p></div>
    <div class="asof"><span class="live" aria-hidden="true"></span>Data as of<b><time datetime="{FACTS['generated_at']}">{asof_short}</time></b>nightly</div>
  </div>
  <label class="sbox" for="q">{ICON_SEARCH}<input id="q" type="search" placeholder="Look up your block or building" autocomplete="off"><button type="button">Go</button></label>
  <div class="shint">Opens <a href="{link('Block report card')}">Block report card</a><a href="{link('Building biography')}">Building biography</a><a href="{link('Block Watch')}">Block Watch</a></div>
</div></header>

<div class="console">
  <aside class="mapwrap" id="mapwrap" aria-label="Permit map">
    <div class="mbar">
      <span class="mt">Map</span><span class="mc"><span id="shown">{permits_total}</span> permits · 30 days · {len(projects)} numbered</span>
      <button type="button" class="xbtn" id="xbtn" aria-expanded="false" aria-controls="mapwrap"><span>Expand</span> ⤢</button>
    </div>
    <div class="stage">
      {map_svg()}
      <div class="readout" id="readout" aria-live="polite">{default_readout}</div>
    </div>
    <div class="mfoot">
      <div class="chips" role="group" aria-label="Filter permits by type">{chips}</div>
      <div class="mkey"><span>{glyph('num')}Numbered = bigger project</span><span>Grid 0.001°</span><span>Outline: Petworth</span></div>
    </div>
  </aside>

  <main class="dash">

<section id="week">
  {sh('01', 'This week', 'Last 30 days vs the 30 before')}
  <div class="kick"><span class="tag-up">{lead_word.upper()} {abs(ld['d'])}</span>Biggest change in 311</div>
  <h2 class="lede">{lede}</h2>
  <div class="cmpgrid">
    <a class="card" href="{link('311 report card')}" style="color:inherit;text-decoration:none">{cmp_rows(e(LEAD_NAME.get(lead['type'], short_type(lead['type']))), lead['count'], lead['previous'], lm, ld, 'acc')}</a>
    <a class="card" href="{link('311 report card')}" style="color:inherit;text-decoration:none">{cmp_rows('All 311 requests', tm['requests_30d'], tm['requests_prev_30d'], rm, req, 'fill')}</a>
  </div>
  <div class="card stats">
    <a class="stat" href="#projects"><div class="l">Permits</div><div class="v num">{permits_total}</div><div class="c">issued in 30 days · all on the map</div></a>
    <a class="stat" href="{link('311 report card')}"><div class="l">311 requests</div><div class="v num">{fmt(tm['requests_30d'])}</div><div class="c"><span class="chg {req['cls']}">{req['txt']}</span> vs {fmt(tm['requests_prev_30d'])}</div></a>
    <a class="stat" href="{link('Block report card')}"><div class="l">Crime reports</div><div class="v num">{tm['crime_30d']}</div><div class="c"><span class="chg {crime['cls']}">{crime['txt']}</span> vs {tm['crime_prev_30d']} · counts</div></a>
  </div>
  <div class="also-h">Also in 311</div>
  <ul class="also">{also}</ul>
</section>

<section id="projects">
  {sh('02', 'Bigger projects', f'<a href="{link("Block Watch")}">Block Watch →</a>')}
  <div class="card">
    <ol class="plist">{proj_rows}</ol>
    <div class="pfoot"><span>{len(projects)} of {permits_total} permits · {new_count} new this week{'' if groups.get('New construction') else ' · 0 new construction'}</span><a href="/petworth/permits.xml">RSS feed</a></div>
  </div>
  <div class="card mix">
    <div class="mix-h"><span>All {permits_total} permits by type</span><span>Tap to filter map</span></div>
    <ul>{mix_rows}</ul>
  </div>
</section>

<section id="homes">
  {sh('03', 'Homes', f'<a href="{link("Housing pulse")}">Housing pulse →</a>')}
  <div class="card homes">
    <div class="stat hero"><div class="l">Median house price · 12 mo</div><div class="v num">{homes['median_house_price_12mo']}</div><div class="c">{homes['house_sales_12mo']} house sales in 12 months</div></div>
    <div class="stat"><div class="l">Median · 60 days</div><div class="v num">{homes['median_price_60d']}</div><div class="c">{homes['market_sales_60d']} sales</div></div>
    <div class="stat"><div class="l">Per sq ft · 60 days</div><div class="v num">{homes['median_price_per_sqft_60d']}</div><div class="c">median</div></div>
    <div class="stat"><div class="l">Median condo · 12 mo</div><div class="v num">{homes['median_condo_price_12mo']}</div><div class="c">{homes['condo_sales_12mo']} condo sales</div></div>
    <div class="stat"><div class="l">Sold above assessment</div><div class="v num">{homes['sold_above_assessment_12mo'].split(' of ')[0]}<span style="font-size:15px;color:var(--muted);font-weight:500"> of {homes['sold_above_assessment_12mo'].split(' of ')[1]}</span></div><div class="c">sales, 12 months</div></div>
    <a class="cta" href="{link('Assessment check')}">Is your assessment in line with sales? <span>Assessment check →</span></a>
  </div>
</section>

<section id="streets">
  {sh('04', 'Streets', f'<a href="{link("Curb radar")}">Curb radar →</a>')}
  <div class="stack">
    <div class="card stats flush">
      <div class="stat"><div class="l">Curb permits</div><div class="v num">{streets['curb_permits_active_this_week']}</div><div class="c">active this week</div></div>
      <div class="stat"><div class="l">Next 7 days</div><div class="v num">{streets['curb_permits_starting_next_7d']}</div><div class="c">more starting</div></div>
      <div class="stat"><div class="l">Curb reserved</div><div class="v num">{curb_mi:.1f} mi</div><div class="c">{fmt(streets['curb_reserved_ft'])} ft</div></div>
    </div>
    <div class="card">
      <div class="tbl-wrap"><table class="t311">
        <thead><tr><th></th><th>Top 311 requests · 30 days</th><th>Now</th><th>Prior</th><th>Change</th></tr></thead>
        <tbody>{rank_rows}</tbody>
      </table></div>
      <div class="tlegend"><span><i style="width:12px;height:6px;background:var(--ink-2)"></i>Last 30 days</span><span><i style="width:1.5px;height:10px;background:var(--ink)"></i>Prior 30 days</span><a href="{link('311 report card')}" style="margin-left:auto">All types →</a></div>
    </div>
    <div class="card">
      <div class="stats flush">
        <div class="stat"><div class="l">Street trees</div><div class="v num">{fmt(trees['street_trees'])}</div><div class="c">{trees['species']} species</div></div>
        <div class="stat"><div class="l">Planted</div><div class="v num">{trees['planted_last_5y']}</div><div class="c">in the last 5 years</div></div>
        <div class="stat"><div class="l">Empty boxes</div><div class="v num acc">{trees['empty_boxes_open']}</div><div class="c">open tree boxes</div></div>
      </div>
      <a class="cta" href="{link('Street trees')}">Find an empty tree box near you <span>Street trees →</span></a>
    </div>
  </div>
</section>

<section id="history">
  {sh('05', 'From the archives', f'<a href="{link("100 years ago")}">100 years ago →</a>')}
  <div class="arch">
    <div class="card acard">
      <div class="ak">{e(hist['block'])}</div>
      <div class="abig"><div class="num">62<small>rowhouses</small></div><div class="num">1926<small>built</small></div><div class="num">4<small>permits</small></div></div>
      <p>{e(hist['fact'])}</p>
      <a class="alink" href="{link('Building biography')}">Building biography →</a>
    </div>
    <div class="card acard">
      <div class="ak">100 years ago this week <span class="ocr">OCR</span></div>
      <blockquote class="clip">{e(hist['hundred_years_ago_excerpt_ocr'])}</blockquote>
      <div class="src">{e(hist['hundred_years_ago_source'])}. Machine-read text; may contain errors.</div>
    </div>
  </div>
</section>

<section id="reps">
  {sh('06', 'Who represents you', f"{len(reps)} SMDs · ANC {' & '.join(sorted({r['anc'] for r in reps}))}")}
  <div class="card"><div class="tbl-wrap"><table class="treps"><tbody>{rep_rows}</tbody></table></div></div>
  <p class="note">Each Single Member District elects one commissioner. Names of elected officials are public record.</p>
</section>

<section id="subscribe">
  {sh('07', 'Weekly email', f'<a href="{link("Weekly email")}">See a sample →</a>')}
  <div class="card subc">
    <h3>These numbers, once a week</h3>
    <p>The week's changes and new permits, sent to your inbox.</p>
    <form class="sub-row" onsubmit="return false"><input type="email" placeholder="you@example.com" aria-label="Email address"><button type="button">Subscribe</button></form>
    <div class="subnote"><span>Mock signup.</span><a href="/petworth/permits.xml">Permits RSS feed</a></div>
  </div>
  <div class="sponsor"><span>Presented by <b>[Local sponsor]</b></span><small>Sponsor</small></div>
</section>

<footer>
  <p><strong>Independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission, or any Business Improvement District.</strong></p>
  <p>Sources: Open Data DC (CC BY 4.0); Library of Congress, Chronicling America. Crime figures are preliminary counts. Data as of {asof}.</p>
  <p class="mono">petworth.org · map: equirectangular, cos(lat) corrected · grid 0.001°</p>
</footer>

  </main>
</div>
<script>{JS}</script>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
