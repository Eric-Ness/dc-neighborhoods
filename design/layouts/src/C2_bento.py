"""Layout C2: Bento. Reads design/layouts/facts.json, writes design/layouts/C2-bento.html.

An asymmetric bento grid: every tile is one self-contained fact, sized by importance.
6 columns at desktop, 4 at tablet, 2 at phone, each with explicit grid areas so no cell is empty.

Run from anywhere:  python design/layouts/src/C2_bento.py
Python 3 stdlib only.
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
OUT = LAYOUTS / "C2-bento.html"

e = html.escape


# ---------- helpers (adapted from C_civic_dashboard.py) ----------
def link(name: str) -> str:
    return "../../" + FACTS["demo_links"][name]


def fmt(n: int) -> str:
    return f"{n:,}"


def delta(cur: int, prev: int) -> dict:
    """Signed change. Percentages only when both counts are 100 or more."""
    d = cur - prev
    sign = "+" if d > 0 else ("−" if d < 0 else "±")
    pct = None
    if cur >= 100 and prev >= 100 and prev:
        pct = round(d / prev * 100)
    txt = f"{sign}{abs(d)}"
    if pct is not None:
        txt += f" ({sign}{abs(pct)}%)"
    return {"d": d, "txt": txt, "sign": sign, "cls": "up" if d > 0 else ("down" if d < 0 else "flat"), "pct": pct}


def title_case(s: str) -> str:
    keep = {"NW", "NE", "SW", "SE", "ADU"}
    return " ".join(w if w in keep or any(c.isdigit() for c in w) else w.capitalize() for w in s.split())


def addr(s: str) -> str:
    return title_case(re.sub(r"\s+\d{5}$", "", s.strip()))


def clean_work(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
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
        off = -4 if mar <= dt < nov else -5
        return dt.astimezone(timezone(timedelta(hours=off)))


# ---------- derived data ----------
gen = datetime.fromisoformat(FACTS["generated_at"].replace("Z", "+00:00"))
loc = to_eastern(gen)
asof = f"{loc.strftime('%b')} {loc.day}, {loc.year} · {loc.strftime('%I').lstrip('0')}:{loc.strftime('%M %p')} ET"

tm = FACTS["this_month"]
req = delta(tm["requests_30d"], tm["requests_prev_30d"])
crime = delta(tm["crime_30d"], tm["crime_prev_30d"])

movers = [dict(m, delta=delta(m["count"], m["previous"])) for m in tm["top_311_movers"]]
rises = sorted([m for m in movers if m["delta"]["d"] > 0], key=lambda m: -m["delta"]["d"])
lead = rises[0] if rises else max(movers, key=lambda m: abs(m["delta"]["d"]))
ld = lead["delta"]
lead_name = {"DC Health Rodent & Vector Control": "rodent complaints"}.get(lead["type"], lead["type"] + " requests")


def mini(cur: int, prev: int) -> str:
    """Two bars: last 30 days (solid) vs the 30 days before (outline)."""
    m = max(cur, prev) or 1
    return (f'<div class="mini" aria-hidden="true"><span>Now</span><i style="width:{100 * cur / m:.1f}%"></i>'
            f'<span>Before</span><i class="was" style="width:{100 * prev / m:.1f}%"></i></div>')


def short_type(t: str) -> str:
    return {"DC Health Rodent & Vector Control": "Rodent & vector control"}.get(t, t)


groups = FACTS["permit_groups"]
GROUP_ORDER = ["Demolition", "New construction", "Additions", "Renovation & repair",
               "Electrical, plumbing & mechanical", "Home businesses", "Minor work"]
GROUP_KEY = {"Demolition": "demo", "New construction": "newc", "Additions": "add",
             "Renovation & repair": "ren", "Electrical, plumbing & mechanical": "mep",
             "Home businesses": "home", "Minor work": "minor"}
GROUP_SHORT = {"Electrical, plumbing & mechanical": "Electrical, plumbing, mech."}
permits_total = tm["permits_30d"]
big_types = ["Demolition", "New construction", "Additions"]

projects = []
for p in FACTS["bigger_projects"]:
    issued = datetime.fromisoformat(p["issued"].replace("Z", "+00:00"))
    age = (gen.date() - issued.date()).days
    projects.append({
        "addr": addr(p["address"]), "group": p["group"], "issued": issued,
        "date": f"{issued.strftime('%b')} {issued.day}", "new": 0 <= age <= 7,
        "work": clean_work(p["work"]),
    })
new_count = sum(p["new"] for p in projects)

homes = FACTS["homes"]
streets = FACTS["streets"]
trees = FACTS["trees"]
hist = FACTS["history"]
reps = FACTS["representatives"]

# Pull the lead number out of the Delafield fact ("all 62 rowhouses in 1926").
m_rows = re.search(r"(\d+)\s+rowhouses\s+in\s+(\d{4})", hist["fact"])
rows_n, rows_year = (m_rows.group(1), m_rows.group(2)) if m_rows else ("", "")


# ---------- map ----------
def map_svg() -> str:
    rings = FACTS["boundary_rings"]
    pts = [p for r in rings for p in r]
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(lons), max(lons), min(lats), max(lats)
    k = math.cos(math.radians((miny + maxy) / 2))
    W, pad = 300, 8
    sc = (W - 2 * pad) / ((maxx - minx) * k)
    H = round((maxy - miny) * sc + 2 * pad)
    px = lambda lon: pad + (lon - minx) * k * sc
    py = lambda lat: pad + (maxy - lat) * sc
    d = " ".join("M" + "L".join(f"{px(x):.1f},{py(y):.1f}" for x, y in r) + "Z" for r in rings)
    small, big, seen = [], [], set()
    for p in FACTS["permit_points"]:
        key = (round(p["lon"], 5), round(p["lat"], 5), p["group"])
        if key in seen:
            continue
        seen.add(key)
        c = f'<circle cx="{px(p["lon"]):.1f}" cy="{py(p["lat"]):.1f}"'
        if p["group"] in big_types:
            big.append(c + f' r="6" class="pb {GROUP_KEY[p["group"]]}"><title>{e(p["group"])}</title></circle>')
        else:
            small.append(c + ' r="3" class="ps"/>')
    return (f'<svg class="map" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" role="img" '
            f'aria-label="Map of Petworth with this month\'s permit locations; large dots are additions and demolition">'
            f'<path d="{d}" class="bnd"/>{"".join(small)}{"".join(big)}</svg>')


# ---------- tiles ----------
ARROW = '<span class="go" aria-hidden="true">→</span>'

TREE_SVG = ('<svg class="tree" viewBox="0 0 24 32" aria-hidden="true">'
            '<circle cx="12" cy="10" r="9"/><circle cx="6.5" cy="15" r="5.5"/><circle cx="17.5" cy="15" r="5.5"/>'
            '<rect x="10.5" y="17" width="3" height="13" rx="1"/><rect x="5" y="29" width="14" height="2.4" rx="1.2"/></svg>')

ICON_SEARCH = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
               'stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>')

lead_max = max(lead["count"], lead["previous"])
t_lead = f"""
<a class="t lead" id="week" href="{link('311 report card')}" style="grid-area:lead">
  <div class="k"><span>This week's finding</span><span>311 · last 30 days</span></div>
  <h2 class="lead-s">{e(FACTS['lead_sentence'])}</h2>
  <div class="lead-nums">
    <div class="lead-now"><span class="n">{lead['count']}</span><span class="cap">{e(lead_name)}, last 30 days</span></div>
    <div class="lead-was">
      <span class="pill">{ld['txt']}</span>
      <span class="n">{lead['previous']}</span><span class="cap">the 30 days before</span>
    </div>
  </div>
  <div class="bars" aria-hidden="true">
    <i style="width:{100 * lead['count'] / lead_max:.1f}%"></i>
    <i class="was" style="width:{100 * lead['previous'] / lead_max:.1f}%"></i>
  </div>
  <div class="foot">{e(lead['type'])} requests filed through 311 <span class="more">311 report card {ARROW}</span></div>
</a>"""

t_hdr = f"""
<header class="t hdr" style="grid-area:hdr">
  <div class="k"><span>petworth.org</span><span>Independent · updated nightly</span></div>
  <h1 class="brand">Petworth</h1>
  <p class="desc">What's changing in Petworth, from DC's own data.</p>
  <p class="asof"><span class="dot" aria-hidden="true"></span>Data as of <time datetime="{FACTS['generated_at']}">{asof}</time></p>
</header>"""

t_srch = f"""
<div class="t srch" style="grid-area:srch">
  <label class="k" for="q"><span>Look up your block or building</span></label>
  <div class="sbox">{ICON_SEARCH}<input id="q" type="search" placeholder="e.g. 4400 Georgia Ave NW" autocomplete="off"><button type="button">Go</button></div>
  <div class="hint"><a href="{link('Block Watch')}">Block Watch {ARROW}</a><a href="{link('Building biography')}">Building biography {ARROW}</a></div>
</div>"""

t_req = f"""
<a class="t req" href="{link('311 report card')}" style="grid-area:req">
  <div class="k"><span>All 311 requests</span></div>
  <div class="n">{fmt(tm['requests_30d'])}</div>
  <div class="chg {req['cls']}">{req['txt']}</div>
  {mini(tm['requests_30d'], tm['requests_prev_30d'])}
  <div class="cap">last 30 days, vs {fmt(tm['requests_prev_30d'])} the 30 days before</div>
</a>"""

t_crime = f"""
<a class="t crime" href="{link('Block report card')}" style="grid-area:crime">
  <div class="k"><span>Crime reports</span></div>
  <div class="n">{tm['crime_30d']}</div>
  <div class="chg">{crime['txt']}</div>
  {mini(tm['crime_30d'], tm['crime_prev_30d'])}
  <div class="cap">last 30 days, vs {tm['crime_prev_30d']} the 30 days before. Counts only.</div>
</a>"""

segs, legend = [], []
for g in GROUP_ORDER:
    n = groups.get(g, 0)
    if not n:
        continue
    segs.append(f'<i class="{GROUP_KEY[g]}" style="flex:{n}" title="{e(g)}: {n}"></i>')
    legend.append(f'<li><i class="{GROUP_KEY[g]}"></i><span>{e(GROUP_SHORT.get(g, g))}</span><b>{n}</b></li>')
t_prm = f"""
<a class="t prm" href="#projects" style="grid-area:prm">
  <div class="k"><span>Building permits</span></div>
  <div class="n">{permits_total}</div>
  <div class="cap">issued in the last 30 days</div>
  <div class="stack" aria-hidden="true">{''.join(segs)}</div>
  <ul class="lgd">{''.join(legend)}</ul>
</a>"""

t_map = f"""
<a class="t mapt" href="{link('Block Watch')}" style="grid-area:map">
  <div class="k"><span>Where the permits are</span><span>30 days</span></div>
  {map_svg()}
  <div class="mlgd"><span><i class="ps"></i>Permit</span><span><i class="pb add"></i>Addition</span><span><i class="pb demo"></i>Demolition</span></div>
  <div class="foot">Block Watch {ARROW}</div>
</a>"""

proj_items = "".join(f"""
  <li>
    <div class="pmeta"><span class="tag {GROUP_KEY[p['group']]}">{'Addition' if p['group'] == 'Additions' else e(p['group'])}</span>{'<span class="new">New</span>' if p['new'] else ''}<time datetime="{p['issued'].date().isoformat()}">{p['date']}</time></div>
    <div class="paddr">{e(p['addr'])}</div>
    <p class="pwork">{e(p['work'])}</p>
  </li>""" for p in projects)
no_newc = "" if groups.get("New construction") else " · no new construction"
t_proj = f"""
<section class="t proj" id="projects" style="grid-area:proj" aria-labelledby="proj-h">
  <div class="k"><span id="proj-h">Bigger projects</span><a href="/petworth/permits.xml">RSS</a></div>
  <div class="proj-head"><span class="n">{len(projects)}</span><span class="cap">demolition and addition permits in the last 30 days · {new_count} new this week{no_newc}</span></div>
  <ul class="plist">{proj_items}</ul>
  <a class="foot" href="{link('Block Watch')}">All permits on Block Watch {ARROW}</a>
</section>"""

t_home = f"""
<section class="t home" id="homes" style="grid-area:home" aria-labelledby="home-h">
  <div class="k"><span id="home-h">Homes</span><span>12 months</span></div>
  <div class="n">{e(homes['median_house_price_12mo'])}</div>
  <div class="cap">median house price · {homes['house_sales_12mo']} house sales</div>
  <dl class="facts">
    <div><dt>Last 60 days</dt><dd>{e(homes['median_price_60d'])}</dd><span>median, {homes['market_sales_60d']} sales</span></div>
    <div><dt>Condos, 12 mo</dt><dd>{e(homes['median_condo_price_12mo'])}</dd><span>median, {homes['condo_sales_12mo']} sales</span></div>
    <div><dt>Per sq ft, 60 days</dt><dd>{e(homes['median_price_per_sqft_60d'])}</dd><span>median</span></div>
    <div><dt>Above assessment</dt><dd>{e(homes['sold_above_assessment_12mo'].split(' of ')[0])}<small> of {e(homes['sold_above_assessment_12mo'].split(' of ')[-1])}</small></dd><span>sales, 12 months</span></div>
  </dl>
  <div class="foot"><a href="{link('Assessment check')}">Check your assessment {ARROW}</a><a href="{link('Housing pulse')}">Housing pulse {ARROW}</a></div>
</section>"""

max311 = max(max(t["count"], t["previous"]) for t in tm["top_311_types"])
rk = ""
for i, t in enumerate(tm["top_311_types"], 1):
    d = delta(t["count"], t["previous"])
    hot = " hot" if t["type"] == lead["type"] else ""
    rk += (f'<li class="{hot.strip()}"><span class="rn">{i}</span><span class="rname">{e(short_type(t["type"]))}</span>'
           f'<span class="rc">{t["count"]}</span><span class="rd {d["cls"]}">{d["sign"]}{abs(d["d"])}</span>'
           f'<span class="rbar" aria-hidden="true"><i style="width:{100 * t["count"] / max311:.1f}%"></i>'
           f'<b style="left:{100 * t["previous"] / max311:.1f}%"></b></span></li>')
t_311 = f"""
<a class="t t311" href="{link('311 report card')}" style="grid-area:t311">
  <div class="k"><span>Top 311 requests</span><span>30 days</span></div>
  <ol class="rank">{rk}</ol>
  <div class="cap">Bar is the last 30 days; the tick is the 30 days before.</div>
  <div class="foot">311 report card {ARROW}</div>
</a>"""

t_curb = f"""
<a class="t curb" id="streets" href="{link('Curb radar')}" style="grid-area:curb">
  <div class="k"><span>Curb permits</span><span>this week</span></div>
  <div class="n">{streets['curb_permits_active_this_week']}</div>
  <div class="cap">active now, <b>{streets['curb_permits_starting_next_7d']}</b> more start in the next 7 days</div>
  <div class="paint" aria-hidden="true"></div>
  <div class="cap"><b>{fmt(streets['curb_reserved_ft'])} ft</b> of curb reserved</div>
  <div class="foot">Curb radar {ARROW}</div>
</a>"""

boxes = "".join("<i></i>" for _ in range(trees["empty_boxes_open"]))
t_trees = f"""
<a class="t trees" href="{link('Street trees')}" style="grid-area:trees">
  <div class="k"><span>Street trees</span>{TREE_SVG}</div>
  <div class="n">{fmt(trees['street_trees'])}</div>
  <div class="cap">trees, {trees['species']} species · {trees['planted_last_5y']} planted in 5 years</div>
  <div class="boxes" role="img" aria-label="{trees['empty_boxes_open']} empty tree boxes">{boxes}</div>
  <div class="cap"><b>{trees['empty_boxes_open']}</b> empty tree boxes open {ARROW}</div>
</a>"""

t_hist = f"""
<a class="t hist" id="history" href="{link('Building biography')}" style="grid-area:hist">
  <div class="k"><span>From the archives</span><span>{rows_year}</span></div>
  <div class="hrow"><span class="sn">{rows_n}</span><span class="hblock">rowhouses, one builder, {e(hist['block'])}</span></div>
  <p class="serif">{e(hist['fact'])}</p>
  <div class="foot">Building biography {ARROW}</div>
</a>"""

t_ocr = f"""
<a class="t ocr" href="{link('100 years ago')}" style="grid-area:ocr">
  <div class="k"><span>100 years ago this week</span><span class="badge">OCR text</span></div>
  <blockquote class="serif">“{e(hist['hundred_years_ago_excerpt_ocr'])}”</blockquote>
  <div class="src">{e(hist['hundred_years_ago_source'])}. Machine-read; may contain errors.</div>
  <div class="foot">100 years ago {ARROW}</div>
</a>"""

rep_html = ""
for anc in sorted({r["anc"] for r in reps}):
    rs = [r for r in reps if r["anc"] == anc]
    rep_html += (f'<div class="anc"><a class="anc-h" href="{e(rs[0]["url"])}">ANC {anc} ↗</a><ul>'
                 + "".join(f'<li><span class="smd">{r["smd"]}</span><span>{e(title_case(r["commissioner"]))}</span></li>' for r in rs)
                 + "</ul></div>")
t_reps = f"""
<section class="t reps" id="reps" style="grid-area:reps" aria-labelledby="reps-h">
  <div class="k"><span id="reps-h">Who represents you</span><span>{len(reps)} commissioners</span></div>
  <div class="ancs">{rep_html}</div>
  <div class="cap">Each Single Member District (SMD) elects one ANC commissioner.</div>
</section>"""

t_sub = f"""
<section class="t sub" id="subscribe" style="grid-area:sub" aria-labelledby="sub-h">
  <div class="k"><span id="sub-h">Weekly email</span><a href="{link('Weekly email')}">See a sample {ARROW}</a></div>
  <p class="sub-p">These numbers, once a week.</p>
  <form class="sub-row" onsubmit="return false"><input type="email" placeholder="you@example.com" aria-label="Email address"><button type="button">Subscribe</button></form>
  <div class="cap">Mock signup. Or follow the <a href="/petworth/permits.xml">permits RSS feed</a>.</div>
</section>"""

t_spon = """
<aside class="t spon" style="grid-area:spon">
  <div class="k"><span>Sponsor</span></div>
  <p>Presented by <b>[Local sponsor]</b></p>
</aside>"""

CSS = r"""
:root{
  --bg:#ebe8e1; --paper:#ffffff; --ink:#15130f; --ink-2:#47433b; --line:#d8d3c8;
  --tomato:#ff5b3a; --cobalt:#2340d8; --cobalt-ink:#ffffff; --cobalt-soft:#e5e9ff;
  --lemon:#ffd43b; --forest:#0f6b3e; --mint:#c8f2d6; --asphalt:#24272c; --cream:#f4ead6;
  --slate:#dfe3e8; --pink:#ffc9d9;
  --up:#b42318; --down:#0b6b3a;
  --r:22px; --gap:8px;
  --sans:"Archivo","Helvetica Neue",Arial,system-ui,sans-serif;
  --serif:"Instrument Serif",Georgia,"Times New Roman",serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--sans)}
a{color:inherit}
.tag-top{font:700 11px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;background:var(--ink);color:#fff;padding:7px 12px}
.bento{max-width:1400px;margin:0 auto;padding:var(--gap) 12px;display:grid;gap:var(--gap);
  grid-template-columns:repeat(2,minmax(0,1fr));
  grid-template-areas:
   "hdr hdr" "srch srch" "lead lead" "req crime" "prm map" "home home" "proj proj"
   "t311 t311" "curb trees" "hist hist" "ocr ocr" "reps reps" "sub sub" "spon spon"}

/* tile */
.t{border-radius:var(--r);padding:16px;display:flex;flex-direction:column;gap:8px;min-width:0;
  background:var(--paper);text-decoration:none;container-type:inline-size;position:relative;overflow:hidden}
a.t{transition:transform .15s ease}
a.t:hover{transform:translateY(-2px)}
a.t:focus-visible,.t a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid var(--ink);outline-offset:2px}
.k{display:flex;justify-content:space-between;align-items:center;gap:8px;font:700 11px/1.2 var(--sans);
  letter-spacing:.09em;text-transform:uppercase}
.k a{text-decoration:underline;text-underline-offset:2px}
.n{font-family:var(--sans);font-weight:800;font-stretch:125%;font-variant-numeric:tabular-nums lining-nums;
  line-height:.86;letter-spacing:-.035em;font-size:min(27cqi,104px)}
.cap{font-size:13px;line-height:1.35;color:inherit;opacity:.82}
.cap b{opacity:1;font-weight:700}
.foot{margin-top:auto;padding-top:6px;font-weight:700;font-size:13.5px;display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.foot a{text-decoration:none}
.go{display:inline-block;transition:transform .15s}
a.t:hover .go,.foot a:hover .go{transform:translateX(3px)}
.chg{font-weight:800;font-stretch:112%;font-size:17px;font-variant-numeric:tabular-nums}
.chg.up{color:var(--up)} .chg.down{color:var(--down)}

@container (max-width:220px){.k span+span{display:none}}
/* header */
.hdr{background:var(--ink);color:#fff;gap:6px}
.brand{margin:4px 0 0;font-weight:900;font-stretch:125%;letter-spacing:-.045em;line-height:.85;font-size:min(16cqi,128px)}
.desc{margin:4px 0 0;font-size:17px;font-weight:500;max-width:34ch}
.asof{margin:auto 0 0;padding-top:10px;font-size:12.5px;opacity:.85;font-variant-numeric:tabular-nums}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--lemon);margin-right:7px;vertical-align:1px}

/* search */
.srch{background:var(--paper);justify-content:center}
.sbox{display:flex;align-items:center;gap:8px;border:2px solid var(--ink);border-radius:14px;padding:0 5px 0 12px;height:52px;background:#fff}
.sbox input{flex:1;min-width:0;border:0;background:transparent;font:500 16px var(--sans);color:var(--ink);outline:none;height:100%}
.sbox input::placeholder{color:#6b665c}
.sbox button,.sub-row button{flex:none;border:0;background:var(--ink);color:#fff;font:700 14px var(--sans);border-radius:10px;padding:10px 16px;cursor:pointer}
.hint{display:flex;gap:6px;flex-wrap:wrap}
.hint a{font-size:13px;font-weight:600;text-decoration:none;background:var(--bg);border-radius:999px;padding:5px 11px}

/* lead */
.lead{background:var(--tomato);color:var(--ink);gap:12px}
.lead-s{margin:2px 0 0;font-weight:700;font-stretch:100%;font-size:clamp(19px,4.6cqi,34px);line-height:1.15;letter-spacing:-.015em;max-width:30ch}
.lead-nums{display:flex;align-items:flex-end;gap:5cqi}
.lead-now{display:flex;flex-direction:column;gap:8px}
.lead-now .n{font-size:min(31cqi,300px);letter-spacing:-.05em}
.lead-was{display:flex;flex-direction:column;gap:6px;padding-bottom:4px}
.lead-was .n{font-size:min(14cqi,104px);-webkit-text-stroke:2px var(--ink);color:transparent}
.lead .cap{font-weight:600;opacity:1}
.pill{align-self:flex-start;background:var(--ink);color:var(--tomato);font:800 15px/1 var(--sans);font-stretch:112%;padding:7px 10px;border-radius:999px;font-variant-numeric:tabular-nums}
.bars{display:grid;gap:4px}
.bars i{display:block;height:10px;border-radius:5px;background:var(--ink)}
.bars i.was{background:transparent;border:2px solid var(--ink)}
.lead .foot{font-weight:600;justify-content:space-between}
.more{font-weight:800;white-space:nowrap}

/* small stat tiles */
.req{background:var(--paper)}
.crime{background:var(--slate)}
.req .n,.crime .n{margin-top:6px}
.req .cap,.crime .cap{margin-top:auto}
.mini{display:grid;grid-template-columns:auto 1fr;gap:4px 8px;align-items:center;font-size:11px;font-weight:600;margin:4px 0 6px}
.mini i{display:block;height:9px;border-radius:5px;background:var(--ink)}
.mini i.was{background:transparent;border:2px solid var(--ink)}

/* permits */
.prm{background:var(--cobalt);color:var(--cobalt-ink)}
.prm .n{margin-top:2px}
.stack{display:flex;gap:2px;height:14px;border-radius:4px;overflow:hidden;margin-top:4px}
.stack i,.lgd i{display:block}
.lgd{list-style:none;margin:0;padding:0;display:grid;gap:3px;font-size:12px}
.lgd li{display:grid;grid-template-columns:10px 1fr auto;gap:6px;align-items:center}
.lgd i{width:10px;height:10px;border-radius:2px}
.lgd b{font-variant-numeric:tabular-nums}
.demo{background:var(--tomato)} .add{background:var(--lemon)} .newc{background:var(--mint)}
.ren{background:#9fb1ff} .mep{background:#ffffff} .home{background:var(--pink)} .minor{background:#6f84ea}

/* map */
.mapt{background:var(--paper)}
.map{flex:1 1 0;min-height:200px;width:100%;display:block}
.bnd{fill:var(--cobalt-soft);stroke:var(--cobalt);stroke-width:2;stroke-linejoin:round}
.ps{fill:var(--cobalt);opacity:.55}
.pb{stroke:var(--ink);stroke-width:1.6}
.pb.add{fill:var(--lemon)} .pb.demo{fill:var(--tomato)}
.mlgd{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:12px;font-weight:600}
.mlgd i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.mlgd i.ps{background:var(--cobalt);opacity:.55}
.mlgd i.pb{border:1.5px solid var(--ink)}

/* projects */
.proj{background:var(--cobalt-soft)}
.proj-head{display:flex;align-items:flex-end;gap:12px}
.proj-head .n{font-size:min(22cqi,96px);color:var(--cobalt)}
.proj-head .cap{max-width:36ch;padding-bottom:4px}
.plist{list-style:none;margin:4px 0 0;padding:0;display:grid;gap:6px}
.plist li{background:#fff;border-radius:14px;padding:10px 12px;min-width:0}
.pmeta{display:flex;gap:8px;align-items:center;font-size:12px;font-variant-numeric:tabular-nums}
.pmeta time{margin-left:auto;font-weight:600}
.tag{font:800 10.5px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;padding:4px 7px;border-radius:5px;color:var(--ink)}
.new{font:800 10.5px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;padding:4px 7px;border-radius:5px;background:var(--ink);color:#fff}
.paddr{font-weight:800;font-size:16px;margin-top:5px;letter-spacing:-.01em}
.pwork{margin:2px 0 0;font-size:13px;color:var(--ink-2);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.proj .foot{text-decoration:none}

/* homes */
.home{background:var(--lemon)}
.home .n{font-size:min(23cqi,132px)}
.facts{margin:6px 0 0;display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:2px solid var(--ink)}
.facts div{padding:9px 8px 9px 0;border-bottom:1px solid rgba(21,19,15,.35)}
.facts div:nth-child(even){padding-left:10px;border-left:1px solid rgba(21,19,15,.35)}
.facts dt{font:700 10.5px/1.2 var(--sans);letter-spacing:.07em;text-transform:uppercase}
.facts dd{margin:3px 0 1px;font-weight:800;font-stretch:118%;font-size:24px;line-height:1;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.facts dd small{font-size:14px;font-weight:700;letter-spacing:0}
.facts span{font-size:12px}

/* 311 ranking */
.t311{background:var(--paper)}
.rank{list-style:none;margin:2px 0 0;padding:0;display:grid;gap:9px}
.rank li{display:grid;grid-template-columns:18px 1fr auto 44px;gap:2px 8px;align-items:baseline;font-size:14px}
.rn{font-weight:800;font-variant-numeric:tabular-nums;opacity:.5}
.rname{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}
.rc{font-weight:800;font-stretch:118%;font-size:18px;font-variant-numeric:tabular-nums}
.rd{text-align:right;font-weight:700;font-size:12.5px;font-variant-numeric:tabular-nums}
.rd.up{color:var(--up)} .rd.down{color:var(--down)} .rd.flat{opacity:.7}
.rbar{grid-column:2/5;position:relative;height:8px;background:#f0ede6;border-radius:4px}
.rbar i{position:absolute;inset:0 auto 0 0;border-radius:4px;background:var(--ink)}
.rbar b{position:absolute;top:-3px;bottom:-3px;width:2px;margin-left:-1px;background:var(--ink-2)}
.rank li.hot .rbar i{background:var(--tomato)}
.rank li.hot .rname::after{content:" ●";color:var(--tomato)}
.t311 .cap{font-size:12px}
.t311 .rank{flex:1;align-content:space-evenly}

/* curb */
.curb{background:var(--asphalt);color:#fff}
.curb .n{color:var(--lemon)}
.paint{height:6px;margin:4px 0;background:repeating-linear-gradient(90deg,var(--lemon) 0 22px,transparent 22px 36px)}

/* trees */
.trees{background:var(--forest);color:#fff}
.tree{width:22px;height:30px;fill:var(--mint)}
.trees .n{color:var(--mint)}
.boxes{display:grid;grid-template-columns:repeat(auto-fill,minmax(11px,1fr));gap:4px;margin-top:4px;max-width:260px}
.boxes i{aspect-ratio:1;border:1.6px solid var(--mint);border-radius:2px}

/* archives */
.hist,.ocr{background:var(--cream)}
.serif{font-family:var(--serif)}
.hrow{display:flex;align-items:flex-end;gap:10px}
.sn{font-family:var(--serif);font-size:min(40cqi,120px);line-height:.8;font-variant-numeric:lining-nums;color:#8a2a14}
.hblock{font-family:var(--serif);font-style:italic;font-size:17px;line-height:1.15;padding-bottom:4px}
.hist p.serif{margin:0;font-size:17px;line-height:1.3}
.hblock{max-width:22ch}
.ocr blockquote{margin:0;font-style:italic;font-size:clamp(20px,6.4cqi,30px);line-height:1.2}
.badge{border:1.5px solid var(--ink);border-radius:5px;padding:3px 6px;font-size:10px}
.src{font-size:12px;opacity:.8}

/* reps */
.reps{background:var(--paper)}
.ancs{display:grid;grid-template-columns:1fr;gap:12px}
.anc-h{display:inline-block;font-weight:800;font-size:13px;text-decoration:none;background:var(--ink);color:#fff;border-radius:999px;padding:4px 10px}
.anc ul{list-style:none;margin:6px 0 0;padding:0}
.anc li{display:flex;gap:10px;align-items:baseline;padding:6px 0;border-bottom:1px solid #ece8df;font-size:14.5px;font-weight:600}
.smd{font-weight:800;font-stretch:118%;font-variant-numeric:tabular-nums;min-width:44px}

/* subscribe, sponsor */
.sub{background:var(--pink)}
.sub-p{margin:0;font-weight:800;font-stretch:112%;font-size:clamp(22px,8cqi,40px);line-height:1.05;letter-spacing:-.02em}
.sub-row{display:flex;gap:6px;margin-top:auto}
.sub-row input{flex:1;min-width:0;border:2px solid var(--ink);border-radius:12px;padding:0 12px;height:46px;font:500 16px var(--sans);background:#fff;color:var(--ink)}
.spon{background:transparent;border:2px dashed #a49d8f;justify-content:center}
.spon p{margin:0;font-size:15px}

footer{max-width:1400px;margin:0 auto;padding:10px 16px 40px;font-size:12.5px;color:var(--ink-2)}
footer p{margin:6px 0;max-width:80ch}
footer strong{color:var(--ink)}

/* tablet: 4 columns */
@media (min-width:640px){
  :root{--gap:10px}
  .bento{padding:var(--gap) 16px;grid-template-columns:repeat(4,minmax(0,1fr));grid-template-areas:
   "hdr hdr srch srch" "lead lead lead lead" "req crime prm prm" "map map home home" "map map curb curb"
   "proj proj proj proj" "t311 t311 trees trees" "t311 t311 hist hist" "ocr ocr ocr ocr"
   "reps reps sub sub" "spon spon spon spon"}
  .t{padding:20px}
  .plist{grid-template-columns:1fr 1fr}
  .ancs{grid-template-columns:1fr 1fr}
}
/* desktop: 6 columns */
@media (min-width:1100px){
  :root{--gap:12px;--r:26px}
  .bento{padding:var(--gap) 24px;grid-template-columns:repeat(6,minmax(0,1fr));grid-template-areas:
   "hdr hdr hdr hdr srch srch"
   "lead lead lead lead map map"
   "lead lead lead lead map map"
   "req crime prm prm map map"
   "proj proj proj proj home home"
   "proj proj proj proj curb curb"
   "t311 t311 trees trees hist hist"
   "t311 t311 sub sub ocr ocr"
   "reps reps reps reps spon spon"}
  .t{padding:22px}
  .lead{padding:28px}
  footer{padding:14px 24px 48px}
}
@media (prefers-reduced-motion:reduce){a.t,.go{transition:none}a.t:hover{transform:none}}
"""

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth Bento</title>
<meta name="description" content="What's changing in Petworth, Washington DC, from DC's own open data. Independent; updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="Petworth permits" href="/petworth/permits.xml">
<style>{CSS}</style>
</head>
<body>
<div class="tag-top">Layout C2: Bento</div>
<main class="bento">
{t_hdr}{t_srch}{t_lead}{t_map}{t_req}{t_crime}{t_prm}{t_proj}{t_home}{t_311}{t_trees}{t_curb}{t_hist}{t_ocr}{t_reps}{t_sub}{t_spon}
</main>
<footer>
  <p><strong>Independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission, or any Business Improvement District.</strong></p>
  <p>Sources: Open Data DC (CC BY 4.0); Library of Congress, Chronicling America. Crime figures are preliminary counts. Data as of {asof}.</p>
</footer>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
