"""Layout A: "Neighborhood Paper" -- builds design/layouts/A-neighborhood-paper.html from facts.json.

Run:  python design/layouts/src/A_neighborhood_paper.py
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from html import escape
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:  # tzdata missing: fall back to UTC
    ET = None

HERE = Path(__file__).resolve().parent
LAYOUTS = HERE.parent
FACTS = json.loads((LAYOUTS / "facts.json").read_text(encoding="utf-8"))
OUT = LAYOUTS / "A-neighborhood-paper.html"


def e(s) -> str:
    return escape(str(s), quote=True)


def n(x: int) -> str:
    return f"{x:,}"


def link(name: str) -> str:
    """Demo path rewritten relative to design/layouts/."""
    return "../../" + FACTS["demo_links"][name]


def title_case_name(s: str) -> str:
    out = []
    for w in s.split():
        if w.upper() in ("JR.", "JR", "SR.", "SR"):
            out.append(w.capitalize())
        else:
            out.append("-".join(p.capitalize() for p in w.split("-")))
    return " ".join(out)


SUFFIX = {"PL": "Pl.", "ST": "St.", "AVE": "Ave.", "RD": "Rd.", "NW": "NW", "NE": "NE"}


def nice_address(a: str) -> str:
    parts = a.split()
    if parts and re.fullmatch(r"\d{5}", parts[-1]):
        parts = parts[:-1]
    words = []
    for p in parts:
        if p in SUFFIX:
            words.append(SUFFIX[p])
        elif p.isdigit():
            words.append(p)
        else:
            words.append(p.capitalize())
    return " ".join(words)


def clean_work(w: str, limit: int = 150) -> str:
    w = w.split("\r\n")[0].split("\n")[0]
    w = re.sub(r"([A-Z]{2,})([A-Z][a-z])", r"\1 \2", w)   # "ADUNew" -> "ADU New"
    w = re.sub(r"\.([A-Z])", r". \1", w)                   # "grade.Rear" -> "grade. Rear"
    w = re.sub(r"\s+", " ", w).strip()
    if len(w) > limit:
        w = w[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return w


def short_date(iso: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%b ") + str(d.day)


# --------------------------------------------------------------------------- dates
gen = datetime.fromisoformat(FACTS["generated_at"].replace("Z", "+00:00"))
local = gen.astimezone(ET) if ET else gen
tz_label = "ET" if ET else "UTC"
hour = local.hour % 12 or 12
ampm = "a.m." if local.hour < 12 else "p.m."
EDITION_DATE = f"{local.strftime('%A, %B')} {local.day}, {local.year}"
AS_OF = f"{local.strftime('%b')}. {local.day}, {local.year}, {hour}:{local.minute:02d} {ampm} {tz_label}"
ISSUE_NO = local.isocalendar().week

# --------------------------------------------------------------------------- data
tm = FACTS["this_month"]
rodent = next(m for m in tm["top_311_movers"] if "Rodent" in m["type"])
rod_diff = rodent["count"] - rodent["previous"]
req_diff = tm["requests_prev_30d"] - tm["requests_30d"]
movers = tm["top_311_movers"]
types = tm["top_311_types"]
projects = FACTS["bigger_projects"]
groups = FACTS["permit_groups"]
homes = FACTS["homes"]
streets = FACTS["streets"]
trees = FACTS["trees"]
hist = FACTS["history"]
reps = FACTS["representatives"]

n_add = groups.get("Additions", 0)
n_demo = groups.get("Demolition", 0)
n_new = groups.get("New construction", 0)
NUMWORD = {0: "No", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
           7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}


def word(k: int) -> str:
    return NUMWORD.get(k, n(k))


# --------------------------------------------------------------------------- map
def build_map(width: int = 360, pad: int = 10) -> tuple[str, int]:
    ring_pts = [pt for ring in FACTS["boundary_rings"] for pt in ring]
    xs = [p[0] for p in ring_pts]
    ys = [p[1] for p in ring_pts]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    k = math.cos(((min_y + max_y) / 2) * math.pi / 180)
    scale = (width - 2 * pad) / ((max_x - min_x) * k)
    height = round((max_y - min_y) * scale + 2 * pad)

    def px(lon):
        return pad + (lon - min_x) * k * scale

    def py(lat):
        return pad + (max_y - lat) * scale

    paths = []
    for ring in FACTS["boundary_rings"]:
        d = "M" + " L".join(f"{px(x):.1f},{py(y):.1f}" for x, y in ring) + " Z"
        paths.append(f'<path d="{d}" class="m-boundary"/>')
    big = {"Additions", "Demolition", "New construction"}
    small_dots, big_dots = [], []
    for p in FACTS["permit_points"]:
        cx, cy = px(p["lon"]), py(p["lat"])
        if p["group"] in big:
            big_dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.6" class="m-big"><title>{e(p["group"])}</title></circle>')
        else:
            small_dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.6" class="m-dot"><title>{e(p["group"])}</title></circle>')
    svg = (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="map-t" class="map">'
        f'<title id="map-t">Map of Petworth with a dot for each permit issued in the past 30 days</title>'
        + "".join(paths) + "".join(small_dots) + "".join(big_dots) + "</svg>"
    )
    return svg, len(FACTS["permit_points"])


MAP_SVG, N_POINTS = build_map()


# --------------------------------------------------------------------------- fragments
def change_row(label: str, now: int, prev: int, maxv: int, highlight: bool = False) -> str:
    diff = now - prev
    sign = "+" if diff > 0 else ("−" if diff < 0 else "±")
    w_now = now / maxv * 100
    w_prev = prev / maxv * 100
    return f"""
      <li class="chg{' is-hl' if highlight else ''}">
        <div class="chg-label">{e(label)}</div>
        <div class="chg-bars" aria-hidden="true">
          <span class="bar bar-prev" style="width:{w_prev:.1f}%"></span>
          <span class="bar bar-now" style="width:{w_now:.1f}%"></span>
        </div>
        <div class="chg-num"><b>{n(now)}</b> <span class="was">from {n(prev)}</span> <span class="delta">{sign}{abs(diff)}</span></div>
      </li>"""


maxv = max(max(m["count"], m["previous"]) for m in movers)
movers_html = "".join(change_row(m["type"], m["count"], m["previous"], maxv, m is rodent) for m in movers)

top_types_html = "".join(
    f'<li><span class="tt-name">{e(t["type"])}</span><span class="tt-dots"></span><span class="tt-n">{n(t["count"])}</span></li>'
    for t in types
)

groups_sorted = sorted(groups.items(), key=lambda kv: -kv[1])
groups_html = "".join(
    f'<li><span class="tt-name">{e(g)}</span><span class="tt-dots"></span><span class="tt-n">{c}</span></li>'
    for g, c in groups_sorted
)

projects_html = "".join(
    f"""
        <li class="proj">
          <div class="proj-meta"><span class="proj-tag{' is-demo' if p['group'] == 'Demolition' else ''}">{e(p['group'].rstrip('s') if p['group'] == 'Additions' else p['group'])}</span> <span class="proj-date">Issued {e(short_date(p['issued']))}</span></div>
          <h4 class="proj-addr"><a href="{e(link('Building biography'))}">{e(nice_address(p['address']))}</a></h4>
          <p class="proj-work">{e(clean_work(p['work']))}</p>
        </li>"""
    for p in projects
)

reps_html = "".join(
    f"""
          <tr><th scope="row">{e(r['smd'])}</th><td>{e(title_case_name(r['commissioner']))}</td><td><a href="{e(r['url'])}">ANC {e(r['anc'])}</a></td></tr>"""
    for r in reps
)

miles = streets["curb_reserved_ft"] / 5280
first_issued = short_date(min(p["issued"] for p in projects))
last_issued = short_date(max(p["issued"] for p in projects))

new_note = (
    f"{word(n_new)} new-construction permits"
    if n_new
    else "No new-construction permits were issued in this period"
)

# --------------------------------------------------------------------------- page
CSS = r"""
:root{
  --paper:#fbfaf8; --ink:#141414; --ink-2:#3d3d3b; --muted:#6b6a66; --rule:#141414; --hair:#d9d6cf;
  --tint:#f1efea; --accent:#0b6e4f; --accent-ink:#ffffff; --bar-prev:#c9c6be;
  --serif:"Newsreader", "Iowan Old Style", "Charter", "Georgia", "Times New Roman", serif;
  --sans:"Libre Franklin", "Franklin Gothic Medium", "Helvetica Neue", Arial, system-ui, sans-serif;
}
@media (prefers-color-scheme: dark){
  :root{
    --paper:#151514; --ink:#eeece6; --ink-2:#c9c6be; --muted:#9a978f; --rule:#eeece6; --hair:#3a3936;
    --tint:#1f1f1d; --accent:#4cc39a; --accent-ink:#0c1a14; --bar-prev:#4a4945;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:18px;line-height:1.5;
  font-optical-sizing:auto;text-rendering:optimizeLegibility}
a{color:inherit;text-decoration-thickness:1px;text-underline-offset:3px}
a:hover{color:var(--accent)}
h1,h2,h3,h4{margin:0;font-weight:inherit}
p{margin:0}
ul,ol{margin:0;padding:0;list-style:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}

.layout-label{font:600 11px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;background:var(--ink);color:var(--paper);
  padding:7px 16px;text-align:center}

/* masthead */
.mast{padding-top:18px;text-align:center}
.mast-top{display:flex;justify-content:space-between;gap:12px;font:500 11px/1.3 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.mast-name{font-family:var(--serif);font-weight:800;font-size:clamp(3.4rem,18.5vw,10.5rem);line-height:.86;letter-spacing:-.035em;
  margin:14px 0 8px;font-variation-settings:"opsz" 72}
.mast-desc{font-style:italic;font-size:clamp(1.05rem,3.6vw,1.35rem);color:var(--ink-2);margin-bottom:14px}
.edition{border-top:3px solid var(--rule);border-bottom:1px solid var(--rule);padding:8px 0 7px;margin-top:4px;
  display:flex;flex-direction:column;align-items:center;gap:2px;font:500 12px/1.35 var(--sans);letter-spacing:.04em}
.edition span+span::before{display:none;content:"";width:3px;height:3px;border-radius:50%;background:currentColor;vertical-align:middle;margin-right:14px;position:relative;top:-1px}
.edition .asof{color:var(--accent);font-weight:600}

/* index / search */
.lookup{margin:20px 0 4px;border-bottom:1px solid var(--hair);padding-bottom:20px}
.lookup label{display:block;font:700 12px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}
.lookup-row{display:flex;border:1.5px solid var(--ink);background:var(--paper)}
.lookup input{flex:1;min-width:0;border:0;background:transparent;font:400 17px/1.2 var(--serif);color:var(--ink);padding:13px 12px}
.lookup input::placeholder{color:var(--muted);font-style:italic}
.lookup button{border:0;background:var(--ink);color:var(--paper);font:600 14px/1 var(--sans);padding:0 18px;cursor:pointer}
.lookup-hint{font:400 13px/1.45 var(--sans);color:var(--muted);margin-top:8px}
.lookup-hint a{color:var(--ink-2)}

/* section heads */
.kicker{font:700 11.5px/1.2 var(--sans);letter-spacing:.13em;text-transform:uppercase;color:var(--accent)}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;border-top:3px solid var(--rule);padding-top:8px;margin:40px 0 18px}
.sec-head h2{font:700 13px/1.2 var(--sans);letter-spacing:.14em;text-transform:uppercase}
.sec-head a{font:500 13px/1.2 var(--sans);white-space:nowrap}
.more{display:inline-block;margin-top:14px;font:600 14px/1.3 var(--sans)}
.more::after{content:" \2192"}

/* front page grid */
.front{display:grid;gap:28px;margin-top:24px}
.lead .kicker{margin-bottom:10px}
.lead h2{font-weight:700;font-size:clamp(2.1rem,8.6vw,3.6rem);line-height:1.02;letter-spacing:-.022em;font-variation-settings:"opsz" 72}
.lead .dek{font-size:clamp(1.13rem,4vw,1.4rem);line-height:1.38;color:var(--ink-2);margin-top:14px;font-weight:400}
.byline{font:500 12px/1.4 var(--sans);color:var(--muted);margin-top:14px;text-transform:uppercase;letter-spacing:.07em}
.lead-body{margin-top:20px;columns:1;column-gap:32px}
.lead-body p{margin-bottom:12px}
.lead-body p:first-child::first-letter{float:left;font-weight:700;font-size:3.6em;line-height:.82;padding:5px 8px 0 0}
.chart-cap{font:700 12px/1.3 var(--sans);letter-spacing:.06em;text-transform:uppercase;margin:22px 0 4px}
.chart-note{font:400 12.5px/1.4 var(--sans);color:var(--muted);margin-bottom:10px}
.chart-note i{display:inline-block;width:14px;height:6px;vertical-align:middle;margin:0 4px 0 2px}
.chg{display:grid;grid-template-columns:1fr;gap:4px;padding:10px 0;border-top:1px solid var(--hair)}
.chg-label{font:500 14px/1.3 var(--sans)}
.chg-bars{display:grid;gap:3px}
.bar{display:block;height:7px;background:var(--bar-prev)}
.bar-now{background:var(--ink-2)}
.chg.is-hl .bar-now{background:var(--accent)}
.chg-num{font:400 13px/1.3 var(--sans);color:var(--muted)}
.chg-num b{font:700 17px/1 var(--serif);color:var(--ink)}
.chg .delta{font-weight:600;color:var(--ink-2);margin-left:4px}
.chg.is-hl .delta,.chg.is-hl .chg-num b{color:var(--accent)}

/* by the numbers */
.btn-box{border:1.5px solid var(--ink);padding:16px 16px 6px}
.btn-box h3{font:800 13px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;padding-bottom:10px;border-bottom:3px double var(--ink)}
.btn-list li{padding:13px 0;border-bottom:1px solid var(--hair)}
.btn-list li:last-child{border-bottom:0}
.btn-num{font-weight:700;font-size:2.5rem;line-height:1;letter-spacing:-.02em;font-variant-numeric:lining-nums tabular-nums;font-variation-settings:"opsz" 72}
.btn-lab{font:500 13.5px/1.35 var(--sans);margin-top:4px}
.btn-sub{font:400 12.5px/1.35 var(--sans);color:var(--muted);margin-top:2px}
.btn-foot{font:400 11.5px/1.4 var(--sans);color:var(--muted);padding:10px 0}
.sponsor{margin-top:18px;border-top:1px solid var(--hair);border-bottom:1px solid var(--hair);padding:12px 0;text-align:center;font:400 12px/1.3 var(--sans);color:var(--muted)}
.sponsor b{display:block;font:italic 600 18px/1.3 var(--serif);color:var(--ink);margin-top:3px}
.sponsor small{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:2px}

/* secondary stories */
.cols{display:grid;gap:0}
.story{padding:20px 0;border-top:1px solid var(--hair)}
.story:first-child{border-top:0;padding-top:0}
.story .kicker{margin-bottom:8px}
.story h3{font-weight:700;font-size:1.65rem;line-height:1.1;letter-spacing:-.012em;font-variation-settings:"opsz" 48}
.story .summary{margin-top:10px;color:var(--ink-2);font-size:17px}
.big-figure{display:flex;align-items:baseline;gap:10px;margin:14px 0 4px}
.big-figure .fig{font-weight:700;font-size:3.4rem;line-height:.9;letter-spacing:-.03em;font-variation-settings:"opsz" 72}
.big-figure .fig-lab{font:500 13px/1.3 var(--sans);color:var(--muted)}
.leaders li{display:flex;align-items:baseline;gap:6px;font:400 14.5px/1.35 var(--sans);padding:6px 0}
.tt-name{flex:0 1 auto}
.tt-dots{flex:1 1 20px;border-bottom:1px dotted var(--muted);transform:translateY(-4px);min-width:16px}
.tt-n{font-weight:700;font-variant-numeric:tabular-nums}
.facts2{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px;margin-top:14px}
.facts2 div{border-top:1px solid var(--ink);padding-top:6px}
.facts2 b{display:block;font-weight:700;font-size:1.6rem;line-height:1.1;font-variation-settings:"opsz" 48}
.facts2 span{font:400 12.5px/1.35 var(--sans);color:var(--muted)}

/* projects */
.projects-wrap{display:grid;gap:24px}
.proj{padding:14px 0;border-top:1px solid var(--hair)}
.proj:first-child{border-top:0;padding-top:0}
.proj-meta{font:500 11.5px/1.3 var(--sans);color:var(--muted);letter-spacing:.04em}
.proj-tag{font-weight:700;text-transform:uppercase;letter-spacing:.11em;color:var(--ink)}
.proj-tag.is-demo{color:var(--accent)}
.proj-addr{font-weight:700;font-size:1.3rem;line-height:1.2;margin-top:4px}
.proj-addr a{text-decoration:none}
.proj-addr a:hover{text-decoration:underline}
.proj-work{font-size:15.5px;line-height:1.45;color:var(--ink-2);margin-top:4px}
.map-fig{margin:0}
.map{display:block;width:100%;height:auto;max-width:440px;margin:0 auto}
.m-boundary{fill:var(--tint);stroke:var(--ink);stroke-width:1.4;stroke-linejoin:round}
.m-dot{fill:var(--ink);fill-opacity:.42}
.m-big{fill:var(--accent);stroke:var(--paper);stroke-width:1.5}
.map-fig figcaption{font:400 12.5px/1.45 var(--sans);color:var(--muted);margin-top:8px}
.map-fig figcaption i{display:inline-block;width:9px;height:9px;border-radius:50%;vertical-align:middle;margin:0 3px 0 0}
.groups-h{font:700 12px/1.3 var(--sans);letter-spacing:.06em;text-transform:uppercase;margin:20px 0 4px}

/* archives */
.archive{background:var(--tint);padding:24px 16px;margin:0 -16px}
.archive .inner{max-width:780px;margin:0 auto}
.archive h3{font-weight:700;font-size:clamp(1.8rem,7vw,2.6rem);line-height:1.05;letter-spacing:-.02em;margin-top:8px;font-variation-settings:"opsz" 72}
.archive .lede{margin-top:12px;font-size:18px}
.archive .lede strong{font-weight:700}
.clip{margin:26px 0 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);padding:18px 0}
.clip-label{font:700 11px/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.clip blockquote{margin:10px 0 0;font-style:italic;font-size:clamp(1.25rem,4.6vw,1.6rem);line-height:1.35}
.clip blockquote::before{content:"\201C"}
.clip blockquote::after{content:"\201D"}
.clip figcaption{font:400 12.5px/1.45 var(--sans);color:var(--muted);margin-top:10px}
.ocr{display:inline-block;border:1px solid var(--muted);padding:1px 5px;font:700 10px/1.3 var(--sans);letter-spacing:.1em;margin-right:6px;color:var(--ink-2)}

/* reps */
.reps-intro{font-size:17px;color:var(--ink-2);margin-bottom:12px}
.table-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table.reps{width:100%;border-collapse:collapse;font:400 15px/1.35 var(--sans);min-width:320px}
.reps th,.reps td{text-align:left;padding:10px 8px 10px 0;border-bottom:1px solid var(--hair);vertical-align:baseline}
.reps thead th{font:700 11px/1.2 var(--sans);letter-spacing:.11em;text-transform:uppercase;color:var(--muted);border-bottom:1.5px solid var(--ink)}
.reps tbody th{font:700 15px/1.2 var(--serif);font-variant-numeric:tabular-nums;width:4.5em}
.reps td:last-child{text-align:right;padding-right:0;white-space:nowrap}

/* subscribe */
.subscribe{border:3px solid var(--ink);padding:22px 18px;margin-top:44px;text-align:center}
.subscribe h2{font-weight:700;font-size:clamp(1.9rem,7.4vw,2.6rem);line-height:1.05;letter-spacing:-.02em;font-variation-settings:"opsz" 72}
.subscribe p{color:var(--ink-2);margin:10px auto 0;max-width:34em;font-size:17px}
.sub-form{display:flex;flex-wrap:wrap;gap:8px;max-width:460px;margin:18px auto 0}
.sub-form input{flex:1 1 200px;min-width:0;border:1.5px solid var(--ink);background:var(--paper);color:var(--ink);font:400 16px/1.2 var(--sans);padding:12px}
.sub-form button{flex:0 0 auto;border:0;background:var(--accent);color:var(--accent-ink);font:700 15px/1 var(--sans);padding:12px 18px;cursor:pointer}
.sub-links{font:400 13px/1.4 var(--sans);color:var(--muted);margin-top:12px}

/* footer */
footer.wrap{margin-top:48px;border-top:3px solid var(--rule);padding:16px 16px 40px;font:400 13px/1.55 var(--sans);color:var(--ink-2)}
footer .foot-name{font:800 1.6rem/1 var(--serif);color:var(--ink);letter-spacing:-.02em;margin-bottom:10px}
footer p+p{margin-top:8px}
.foot-grid>div+div{margin-top:10px}
@media (min-width:760px){.foot-grid>div+div{margin-top:0}}
footer .indep{font-weight:600;color:var(--ink)}

/* desktop */
@media (min-width:760px){
  body{font-size:19px}
  .wrap{padding:0 28px}
  footer.wrap{padding-left:28px;padding-right:28px}
  .edition{flex-direction:row;justify-content:center;gap:14px}
  .edition span+span::before{display:inline-block}
  .lookup{display:grid;grid-template-columns:auto 1fr;gap:4px 18px;align-items:center}
  .lookup label{margin:0}
  .lookup-hint{grid-column:2}
  .front{grid-template-columns:minmax(0,1fr) 300px;gap:40px}
  .lead{border-right:1px solid var(--hair);padding-right:40px}
  .lead-body{columns:2}
  .cols{grid-template-columns:repeat(3,minmax(0,1fr));gap:0}
  .story{border-top:0;padding:0 24px;border-left:1px solid var(--hair)}
  .story:first-child{padding-left:0;border-left:0}
  .story:last-child{padding-right:0}
  .projects-wrap{grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:40px}
  .proj-list{columns:2;column-gap:28px;column-rule:1px solid var(--hair)}
  .proj{break-inside:avoid}
  .proj:first-child{padding-top:14px;border-top:1px solid var(--hair)}
  .archive{margin:0 -28px;padding:40px 28px}
  .reps-grid{display:grid;grid-template-columns:1fr 1.4fr;gap:40px;align-items:start}
  .subscribe{padding:36px}
  .foot-grid{display:grid;grid-template-columns:1fr 1.4fr;gap:40px}
  .chg{grid-template-columns:minmax(0,13em) minmax(0,1fr) 11em;align-items:center;gap:14px}
}
@media (min-width:1100px){
  .front{grid-template-columns:minmax(0,1fr) 320px}
  .proj-list{columns:2}
}
"""

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth: the weekly edition</title>
<meta name="description" content="What's changing in Petworth, from DC's own data. Independent; updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;500;600;700;800&family=Newsreader:ital,opsz,wght@0,6..72,400..800;1,6..72,400..700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="layout-label">Layout A: Neighborhood Paper</div>

<header class="wrap mast">
  <div class="mast-top"><span>{e(FACTS['domain'])}</span><span>The weekly edition</span></div>
  <h1 class="mast-name">{e(FACTS['neighborhood'])}</h1>
  <p class="mast-desc">What&rsquo;s changing in Petworth, from DC&rsquo;s own data</p>
  <div class="edition">
    <span>{e(EDITION_DATE)}</span>
    <span class="asof">Data as of {e(AS_OF)}</span>
    <span>Updated nightly</span>
  </div>
</header>

<main class="wrap">

  <form class="lookup" role="search" action="{e(link('Block Watch'))}" onsubmit="return false">
    <label for="addr">Look up your block or building</label>
    <div class="lookup-row">
      <input id="addr" type="text" placeholder="e.g. 4400 block of 9th St. NW" autocomplete="street-address">
      <button type="submit">Look up</button>
    </div>
    <p class="lookup-hint">Opens <a href="{e(link('Block Watch'))}">Block Watch</a>, the <a href="{e(link('Block report card'))}">block report card</a> or a <a href="{e(link('Building biography'))}">building biography</a>.</p>
  </form>

  <!-- ===== Front page: lead + by the numbers ===== -->
  <section class="front" aria-labelledby="lead-h">
    <article class="lead">
      <p class="kicker">This week &middot; 311 requests</p>
      <h2 id="lead-h">Rodent complaints rose to {rodent['count']}, up from {rodent['previous']} the month before</h2>
      <p class="dek">Calls to DC Health&rsquo;s rodent and vector control line went up by {rod_diff} in the past 30 days, while total 311 requests in Petworth fell from {n(tm['requests_prev_30d'])} to {n(tm['requests_30d'])}.</p>
      <p class="byline">From DC 311 open data &middot; last 30 days vs. the 30 before</p>
      <div class="lead-body">
        <p>Rodent and vector control was the third most common 311 request in Petworth over the past 30 days, with {rodent['count']} requests. Only bulk collection ({types[0]['count']}) and scheduled yard waste ({types[1]['count']}) drew more.</p>
        <p>It was one of the few request types to go up. Overall, residents filed {n(req_diff)} fewer requests than in the previous 30 days. Illegal dumping reports fell from {movers[2]['previous']} to {movers[2]['count']}, and yard-waste pickups from {movers[0]['previous']} to {movers[0]['count']}.</p>
        <p>The 311 report card has the full breakdown by request type.</p>
      </div>
      <p class="chart-cap">Biggest changes in 311 requests</p>
      <p class="chart-note"><i style="background:var(--bar-prev)"></i>previous 30 days <i style="background:var(--ink-2)"></i>past 30 days</p>
      <ul class="changes">{movers_html}
      </ul>
      <a class="more" href="{e(link('311 report card'))}">Read the 311 report card</a>
    </article>

    <aside aria-label="By the numbers">
      <div class="btn-box">
        <h3>By the numbers</h3>
        <ul class="btn-list">
          <li><div class="btn-num">{n(tm['permits_30d'])}</div><div class="btn-lab">building permits issued</div><div class="btn-sub">{n_add} additions, {n_demo} demolition</div></li>
          <li><div class="btn-num">{n(tm['requests_30d'])}</div><div class="btn-lab">311 requests</div><div class="btn-sub">{n(tm['requests_prev_30d'])} in the 30 days before</div></li>
          <li><div class="btn-num">{tm['crime_30d']}</div><div class="btn-lab">reported crimes</div><div class="btn-sub">{tm['crime_prev_30d']} in the 30 days before</div></li>
          <li><div class="btn-num">{streets['curb_permits_active_this_week']}</div><div class="btn-lab">curb permits active this week</div><div class="btn-sub">{streets['curb_permits_starting_next_7d']} more start in the next 7 days</div></li>
          <li><div class="btn-num">{homes['median_house_price_12mo']}</div><div class="btn-lab">median house price</div><div class="btn-sub">{homes['house_sales_12mo']} sales in the past 12 months</div></li>
        </ul>
        <p class="btn-foot">Past 30 days unless noted. Crime shown as counts; small numbers move a lot from month to month.</p>
      </div>
      <div class="sponsor"><small>Sponsor</small><b>Presented by [Local sponsor]</b></div>
    </aside>
  </section>

  <!-- ===== Bigger projects ===== -->
  <div class="sec-head"><h2 id="proj-h">Bigger projects</h2><a href="{e(link('Block Watch'))}">All permits &rarr;</a></div>
  <section class="projects-wrap" aria-labelledby="proj-h">
    <div>
      <p class="kicker">Permits &middot; {e(first_issued)}&ndash;{e(last_issued)}</p>
      <h3 class="story-h" style="font-weight:700;font-size:clamp(1.7rem,6.4vw,2.3rem);line-height:1.06;letter-spacing:-.018em;margin:8px 0 10px">{word(n_add)} additions and {word(n_demo).lower()} partial demolition</h3>
      <p class="summary" style="color:var(--ink-2);margin-bottom:16px;font-size:17px">The larger jobs among {tm['permits_30d']} permits issued in the past 30 days. {e(new_note)}.</p>
      <ol class="proj-list">{projects_html}
      </ol>
    </div>
    <div>
      <figure class="map-fig">
        {MAP_SVG}
        <figcaption><i style="background:var(--accent)"></i>Additions and demolition &nbsp; <i style="background:var(--ink);opacity:.42"></i>Other work. {N_POINTS} permits with a mapped location.</figcaption>
      </figure>
      <p class="groups-h">All {tm['permits_30d']} permits by type</p>
      <ul class="leaders">{groups_html}</ul>
    </div>
  </section>

  <!-- ===== Secondary stories ===== -->
  <div class="sec-head"><h2>Homes, streets &amp; trees</h2></div>
  <section class="cols">
    <article class="story">
      <p class="kicker">Homes</p>
      <h3>Median Petworth house sold for {e(homes['median_house_price_12mo'])} over the past year</h3>
      <div class="big-figure"><span class="fig">{homes['house_sales_12mo']}</span><span class="fig-lab">house sales<br>in 12 months</span></div>
      <div class="facts2">
        <div><b>{homes['market_sales_60d']}</b><span>sales in the past 60 days</span></div>
        <div><b>{e(homes['median_price_60d'])}</b><span>median price, past 60 days</span></div>
        <div><b>{e(homes['median_price_per_sqft_60d'])}</b><span>median per square foot</span></div>
      </div>
      <p class="summary">Compare your assessment with what nearby homes sold for.</p>
      <a class="more" href="{e(link('Assessment check'))}">Check your assessment</a><br>
      <a class="more" style="margin-top:6px" href="{e(link('Housing pulse'))}">Housing pulse</a>
    </article>
    <article class="story">
      <p class="kicker">Streets</p>
      <h3>{streets['curb_permits_active_this_week']} curb permits are active this week</h3>
      <p class="summary">Together they reserve {n(streets['curb_reserved_ft'])} feet of curb, about {miles:.1f} miles. Another {streets['curb_permits_starting_next_7d']} start in the next seven days.</p>
      <p class="groups-h">Top 311 requests, past 30 days</p>
      <ul class="leaders">{top_types_html}</ul>
      <a class="more" href="{e(link('Curb radar'))}">Open curb radar</a>
    </article>
    <article class="story">
      <p class="kicker">Trees</p>
      <h3>{trees['empty_boxes_open']} empty tree boxes are waiting for a tree</h3>
      <div class="big-figure"><span class="fig">{n(trees['street_trees'])}</span><span class="fig-lab">street trees<br>in Petworth</span></div>
      <div class="facts2">
        <div><b>{trees['species']}</b><span>species</span></div>
        <div><b>{trees['planted_last_5y']}</b><span>planted in the past 5 years</span></div>
      </div>
      <p class="summary">Find the open boxes on your street, and what grows on the rest.</p>
      <a class="more" href="{e(link('Street trees'))}">See the street tree atlas</a>
    </article>
  </section>

  <!-- ===== From the archives ===== -->
  <div class="sec-head"><h2>From the archives</h2><a href="{e(link('100 years ago'))}">100 years ago &rarr;</a></div>
  <section class="archive">
    <div class="inner">
      <p class="kicker">{e(hist['block'])}</p>
      <h3>One builder, one year, 62 rowhouses</h3>
      <p class="lede">{e(hist['fact'])}</p>
      <figure class="clip">
        <p class="clip-label">This week in 1926 &middot; {e(hist['hundred_years_ago_week'])}</p>
        <blockquote>{e(hist['hundred_years_ago_excerpt_ocr'])}</blockquote>
        <figcaption><span class="ocr">OCR</span>Machine-read text, unedited; errors are possible. Source: {e(hist['hundred_years_ago_source'])}.</figcaption>
      </figure>
      <a class="more" href="{e(link('100 years ago'))}">Read this week&rsquo;s 1926 pages</a>
    </div>
  </section>

  <!-- ===== Who represents you ===== -->
  <div class="sec-head"><h2 id="reps-h">Who represents you</h2></div>
  <section class="reps-grid" aria-labelledby="reps-h">
    <div>
      <h3 style="font-weight:700;font-size:1.65rem;line-height:1.1;letter-spacing:-.012em;margin-bottom:10px">Six commissioners, two ANCs</h3>
      <p class="reps-intro">Petworth spans six single-member districts in ANCs 4C and 4D. Commissioners are elected officials; their names are public record. Your block page shows which district you are in.</p>
    </div>
    <div class="table-scroll">
      <table class="reps">
        <thead><tr><th scope="col">SMD</th><th scope="col">Commissioner</th><th scope="col" style="text-align:right">Commission</th></tr></thead>
        <tbody>{reps_html}
        </tbody>
      </table>
    </div>
  </section>

  <!-- ===== Subscribe ===== -->
  <section class="subscribe" aria-labelledby="sub-h">
    <p class="kicker">Free &middot; Every week</p>
    <h2 id="sub-h" style="margin-top:8px">Get the weekly edition</h2>
    <p>The numbers on this page, in your inbox once a week: permits, 311, crime counts, homes and what happened in 1926.</p>
    <form class="sub-form" onsubmit="return false">
      <label for="email" style="position:absolute;left:-9999px">Email address</label>
      <input id="email" type="email" placeholder="you@example.com">
      <button type="submit">Subscribe</button>
    </form>
    <p class="sub-links"><a href="{e(link('Weekly email'))}">See a sample edition</a> &middot; <a href="/rss.xml">RSS feed</a></p>
  </section>

</main>

<footer class="wrap">
  <div class="foot-grid">
    <div>
      <p class="foot-name">Petworth</p>
      <p class="indep">Independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission, or any Business Improvement District.</p>
    </div>
    <div>
      <p>Sources: <a href="https://opendata.dc.gov/">Open Data DC</a> (CC BY 4.0), including permits, 311 requests, crime incidents, property sales, public-space permits and street trees. Historical newspapers from the <a href="https://chroniclingamerica.loc.gov/">Library of Congress, Chronicling America</a>.</p>
      <p>Data as of {e(AS_OF)}. Numbers are recomputed nightly and may change as agencies update their records.</p>
    </div>
  </div>
</footer>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
