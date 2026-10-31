"""Layout C: Civic Dashboard. Reads design/layouts/facts.json, writes design/layouts/C-civic-dashboard.html.

Run from anywhere:  python design/layouts/src/C_civic_dashboard.py
Python 3.13 stdlib only.
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
OUT = LAYOUTS / "C-civic-dashboard.html"

e = html.escape


# ---------- helpers ----------
def link(name: str) -> str:
    return "../../" + FACTS["demo_links"][name]


def fmt(n: int) -> str:
    return f"{n:,}"


def minus(s: str) -> str:
    return s.replace("-", "−")


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
    return {"d": d, "txt": txt, "cls": "up" if d > 0 else ("down" if d < 0 else "flat"), "pct": pct}


def title_case(s: str) -> str:
    keep = {"NW", "NE", "SW", "SE", "ADU"}
    out = []
    for w in s.split():
        out.append(w if w in keep or any(c.isdigit() for c in w) else w.capitalize())
    return " ".join(out)


def addr(s: str) -> str:
    return title_case(re.sub(r"\s+\d{5}$", "", s.strip()))


def clean_work(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s + "…" if len(s) >= 150 else s


def to_eastern(dt: datetime) -> tuple[datetime, str]:
    try:
        from zoneinfo import ZoneInfo

        loc = dt.astimezone(ZoneInfo("America/New_York"))
        return loc, "ET"
    except Exception:  # no tzdata on this machine: US DST rule by hand
        y = dt.year
        mar = datetime(y, 3, 8, 7, tzinfo=timezone.utc)
        mar += timedelta(days=(6 - mar.weekday()) % 7)
        nov = datetime(y, 11, 1, 6, tzinfo=timezone.utc)
        nov += timedelta(days=(6 - nov.weekday()) % 7)
        off = -4 if mar <= dt < nov else -5
        return dt.astimezone(timezone(timedelta(hours=off))), "ET"


def compare_svg(cur: float, prev: float, cls: str, max_v: float | None = None) -> str:
    """Two stacked bars: this period (colored) vs previous (grey). Only the two data points we have."""
    m = max_v or max(cur, prev) or 1
    w1, w0 = 100 * cur / m, 100 * prev / m
    return (
        f'<svg class="cmp" viewBox="0 0 100 18" preserveAspectRatio="none" aria-hidden="true">'
        f'<rect class="trk" x="0" y="1" width="100" height="7" rx="1.5"/>'
        f'<rect class="now {cls}" x="0" y="1" width="{w1:.1f}" height="7" rx="1.5"/>'
        f'<rect class="trk" x="0" y="10" width="100" height="7" rx="1.5"/>'
        f'<rect class="prev" x="0" y="10" width="{w0:.1f}" height="7" rx="1.5"/>'
        f"</svg>"
    )


# ---------- derived data ----------
gen = datetime.fromisoformat(FACTS["generated_at"].replace("Z", "+00:00"))
gen_local, tzname = to_eastern(gen)
hour = gen_local.strftime("%I").lstrip("0")
asof = f"{gen_local.strftime('%b')} {gen_local.day}, {gen_local.year} · {hour}:{gen_local.strftime('%M %p')} {tzname}"
asof_short = f"{gen_local.strftime('%b')} {gen_local.day}, {hour}:{gen_local.strftime('%M %p')}"

tm = FACTS["this_month"]
req = delta(tm["requests_30d"], tm["requests_prev_30d"])
crime = delta(tm["crime_30d"], tm["crime_prev_30d"])

movers = [dict(m, **{"delta": delta(m["count"], m["previous"])}) for m in tm["top_311_movers"]]
rises = sorted([m for m in movers if m["delta"]["d"] > 0], key=lambda m: -m["delta"]["d"])
lead = rises[0] if rises else max(movers, key=lambda m: abs(m["delta"]["d"]))
LEAD_NAMES = {"DC Health Rodent & Vector Control": "Rodent complaints"}
lead_name = LEAD_NAMES.get(lead["type"], lead["type"] + " requests")


def short_type(t: str) -> str:
    return {"DC Health Rodent & Vector Control": "Rodent & vector control"}.get(t, t)


def sentence_type(t: str) -> str:
    s = short_type(t)
    return s[0] + s[1:].lower() + " requests"


# "What changed": total 311 change + the movers not used as the lead, biggest first, max 3.
findings = []
findings.append((abs(req["d"]), req["cls"],
                 f"311 requests {'down' if req['d'] < 0 else 'up'} {abs(req['d'])}"
                 + (f" ({abs(req['pct'])}%)" if req["pct"] is not None else "")
                 + f", to {fmt(tm['requests_30d'])}"))
for m in movers:
    if m is lead:
        continue
    d = m["delta"]
    findings.append((abs(d["d"]), d["cls"],
                     f"{sentence_type(m['type'])} {'down' if d['d'] < 0 else 'up'} {abs(d['d'])}"
                     + (f" ({abs(d['pct'])}%)" if d["pct"] is not None else "")
                     + f", to {fmt(m['count'])}"))
findings.sort(key=lambda f: -f[0])
findings = findings[:3]

groups = FACTS["permit_groups"]
GROUP_ORDER = ["Demolition", "New construction", "Additions", "Renovation & repair",
               "Electrical, plumbing & mechanical", "Home businesses", "Minor work"]
GROUP_KEY = {"Demolition": "demo", "New construction": "newc", "Additions": "add",
             "Renovation & repair": "ren", "Electrical, plumbing & mechanical": "mep",
             "Home businesses": "home", "Minor work": "minor"}
GROUP_SHORT = {"Electrical, plumbing & mechanical": "Electrical / plumbing / mech."}
permits_total = tm["permits_30d"]
big_types = ["Demolition", "New construction", "Additions"]
big_count = sum(groups.get(g, 0) for g in big_types)

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


def price_k(s: str) -> int:
    return int(re.sub(r"[^\d]", "", s.split()[0]))


med12 = price_k(homes["median_house_price_12mo"])
med60 = price_k(homes["median_price_60d"])
condo = homes["median_condo_price_12mo"].split(" ")[0]


# ---------- map ----------
def map_svg() -> str:
    rings = FACTS["boundary_rings"]
    pts = [p for r in rings for p in r]
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(lons), max(lons), min(lats), max(lats)
    k = math.cos(math.radians((miny + maxy) / 2))
    W, pad = 320, 10
    sc = (W - 2 * pad) / ((maxx - minx) * k)
    H = round((maxy - miny) * sc + 2 * pad)
    px = lambda lon: pad + (lon - minx) * k * sc
    py = lambda lat: pad + (maxy - lat) * sc
    d = " ".join("M" + "L".join(f"{px(x):.1f},{py(y):.1f}" for x, y in r) + "Z" for r in rings)
    small, big = [], []
    seen = set()
    for p in FACTS["permit_points"]:
        key = (round(p["lon"], 5), round(p["lat"], 5), p["group"] in big_types)
        if key in seen:
            continue
        seen.add(key)
        c = f'<circle cx="{px(p["lon"]):.1f}" cy="{py(p["lat"]):.1f}"'
        if p["group"] in big_types:
            big.append(c + f' r="4.6" class="pt-big {GROUP_KEY[p["group"]]}"><title>{e(p["group"])}</title></circle>')
        else:
            small.append(c + ' r="2.4" class="pt"/>')
    return (f'<svg class="map" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Map of Petworth with permit locations; larger dots are demolition and addition permits">'
            f'<path d="{d}" class="bnd"/>{"".join(small)}{"".join(big)}</svg>')


# ---------- sections ----------
def kpi_tile(label, value, unit, cmp_html, foot, href, extra_cls=""):
    return f"""
<a class="tile {extra_cls}" href="{href}">
  <div class="t-label">{label}</div>
  <div class="t-value"><span class="num">{value}</span>{f'<span class="t-unit">{unit}</span>' if unit else ''}</div>
  {cmp_html}
  <div class="t-foot">{foot}</div>
</a>"""


def cmp_block(cur, prev, cls, cur_lbl, prev_lbl, max_v=None):
    return f"""<div class="cmpwrap">{compare_svg(cur, prev, cls, max_v)}
    <div class="cmplbl"><span class="{cls}-t">{cur_lbl}</span><span>{prev_lbl}</span></div></div>"""


def permit_stack():
    segs = []
    x = 0.0
    for g in GROUP_ORDER:
        n = groups.get(g, 0)
        if not n:
            continue
        w = 100 * n / permits_total
        segs.append(f'<rect class="seg {GROUP_KEY[g]}" x="{x:.2f}" y="1" width="{max(w - 0.6, 0.4):.2f}" height="16"><title>{e(g)}: {n}</title></rect>')
        x += w
    return (f'<div class="cmpwrap"><svg class="cmp" viewBox="0 0 100 18" preserveAspectRatio="none" aria-hidden="true">{"".join(segs)}</svg>'
            f'<div class="cmplbl"><span>{big_count} demolition / addition</span><span>{permits_total - big_count} other</span></div></div>')


tiles = "".join([
    kpi_tile("Building permits", fmt(permits_total), "issued",
             permit_stack(),
             "Last 30 days · split by type", "#projects"),
    kpi_tile("311 requests", fmt(tm["requests_30d"]), "",
             cmp_block(tm["requests_30d"], tm["requests_prev_30d"], req["cls"],
                       f"Last 30d {fmt(tm['requests_30d'])}", f"Prior {fmt(tm['requests_prev_30d'])}"),
             f'<span class="chg {req["cls"]}">{req["txt"]}</span> vs prior 30d', link("311 report card")),
    kpi_tile("Crime reports", fmt(tm["crime_30d"]), "",
             cmp_block(tm["crime_30d"], tm["crime_prev_30d"], crime["cls"],
                       f"Last 30d {tm['crime_30d']}", f"Prior {tm['crime_prev_30d']}"),
             f'<span class="chg {crime["cls"]}">{crime["txt"]}</span> vs prior 30d · counts only', link("Block report card")),
    kpi_tile("Median house price", homes["median_house_price_12mo"], "",
             cmp_block(med60, med12, "neutral", f"Last 60d {homes['median_price_60d']}", f"12 mo {homes['median_house_price_12mo']}"),
             f"{homes['house_sales_12mo']} house sales in 12 months", "#homes"),
])

lead_d = lead["delta"]
lead_html = f"""
<a class="lead" href="{link('311 report card')}">
  <div class="lead-top"><span class="pill {lead_d['cls']}">{'Up' if lead_d['d'] > 0 else 'Down'} {abs(lead_d['d'])}</span><span class="lead-kicker">Biggest change in 311 · last 30 days</span></div>
  <h3 class="lead-h">{e(lead_name)}: <span class="num">{lead['count']}</span>, <span class="nw">{'up' if lead_d['d'] > 0 else 'down'} from <span class="num">{lead['previous']}</span></span></h3>
  <div class="lead-bars">
    <div class="lb-row"><span class="lb-k">Last 30 days</span><svg class="lb" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="10" rx="2"/><rect class="now {lead_d['cls']}" width="{100 * lead['count'] / max(lead['count'], lead['previous']):.1f}" height="10" rx="2"/></svg><span class="lb-v num">{lead['count']}</span></div>
    <div class="lb-row"><span class="lb-k">30 days before</span><svg class="lb" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="10" rx="2"/><rect class="prev" width="{100 * lead['previous'] / max(lead['count'], lead['previous']):.1f}" height="10" rx="2"/></svg><span class="lb-v num">{lead['previous']}</span></div>
  </div>
  <p class="lead-note">{e(lead['type'])} requests filed through 311. <span class="more">311 report card →</span></p>
</a>"""

changed_html = "".join(
    f'<li><span class="arrow {cls}" aria-hidden="true">{"▲" if cls == "up" else "▼"}</span><span>{e(txt)}</span></li>'
    for _, cls, txt in findings
)

chips_html = "".join(
    f'<span class="chip {GROUP_KEY[g]}"><i></i>{e(GROUP_SHORT.get(g, g))} <b class="num">{groups.get(g, 0)}</b></span>'
    for g in GROUP_ORDER if g in groups
)

proj_rows = "".join(f"""
<li class="prow">
  <div class="prow-top">
    <span class="chip sm {GROUP_KEY[p['group']]}"><i></i>{'Addition' if p['group'] == 'Additions' else e(p['group'])}</span>
    {'<span class="badge-new">New this week</span>' if p['new'] else ''}
    <time class="pdate num" datetime="{p['issued'].date().isoformat()}">{p['date']}</time>
  </div>
  <div class="paddr">{e(p['addr'])}</div>
  <div class="pwork">{e(p['work'])}</div>
</li>""" for p in projects)

max311 = max(max(t["count"], t["previous"]) for t in tm["top_311_types"])
rank_rows = ""
for i, t in enumerate(tm["top_311_types"], 1):
    d = delta(t["count"], t["previous"])
    rank_rows += f"""
<li class="rk">
  <span class="rk-n num">{i}</span>
  <div class="rk-body">
    <div class="rk-line"><span class="rk-name">{e(short_type(t['type']))}</span><span class="rk-c num">{t['count']}</span><span class="rk-d num {d['cls']}">{d['txt'].split(' ')[0]}</span></div>
    <svg class="rk-bar" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="6" rx="1"/><rect class="fill" width="{100 * t['count'] / max311:.1f}" height="6" rx="1"/><rect class="tick" x="{100 * t['previous'] / max311 - 0.4:.1f}" y="-1" width="0.8" height="8"/></svg>
  </div>
</li>"""

curb_mi = streets["curb_reserved_ft"] / 5280

rep_rows = ""
for anc in sorted({r["anc"] for r in reps}):
    rs = [r for r in reps if r["anc"] == anc]
    rep_rows += f'<div class="anc"><div class="anc-h"><span>ANC {anc}</span><a href="{e(rs[0]["url"])}">ANC {anc} site ↗</a></div><ul>'
    rep_rows += "".join(
        f'<li><span class="smd num">{r["smd"]}</span><span class="cname">{e(title_case(r["commissioner"]))}</span></li>' for r in rs)
    rep_rows += "</ul></div>"


CSS = r"""
:root{
  --bg:#f3f2ee; --surface:#ffffff; --surface-2:#f8f7f4; --ink:#14171c; --ink-2:#3b4048; --muted:#6b7079;
  --line:#e2e0da; --line-2:#ecebe6;
  --accent:#0b6b70; --accent-ink:#ffffff; --accent-soft:#e3f0ef;
  --up:#c2410c; --up-soft:#fbe9df; --down:#2f7a4a; --down-soft:#e2f1e6; --neutral:#4a5260;
  --c-demo:#c2410c; --c-add:#0b6b70; --c-newc:#7a5a00; --c-ren:#6f8aa0; --c-mep:#9aa3ad; --c-home:#b49a5e; --c-minor:#cfd3d8;
  --r:10px; --font:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#111315; --surface:#1a1d20; --surface-2:#202428; --ink:#eceae5; --ink-2:#c5c3be; --muted:#959aa1;
  --line:#2c3035; --line-2:#262a2e; --accent:#4fb3b0; --accent-ink:#0d1214; --accent-soft:#18302f;
  --up:#f08a5d; --up-soft:#3a2219; --down:#6cc08a; --down-soft:#1b2f22; --neutral:#a7afba;
  --c-demo:#f08a5d; --c-add:#4fb3b0; --c-ren:#7f9bb2; --c-mep:#5f6873; --c-home:#a58d55; --c-minor:#3d434a;
}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font);font-feature-settings:"tnum" 1,"cv11" 1}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.num{font-variant-numeric:tabular-nums}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
.layout-tag{font:600 10.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;background:var(--ink);color:var(--bg);padding:6px 16px}

/* header */
.top{background:var(--surface);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding-top:14px;padding-bottom:12px}
.brand{display:flex;gap:10px;align-items:center;min-width:0}
.mark{flex:none;width:34px;height:34px;border-radius:9px;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;font:700 17px/1 var(--font)}
.brand h1{margin:0;font-size:21px;line-height:1.1;letter-spacing:-.01em}
.brand p{margin:2px 0 0;font-size:12.5px;color:var(--muted);line-height:1.3}
.asof{flex:none;text-align:right;font:500 11px/1.35 var(--mono);color:var(--muted)}
.asof b{display:block;color:var(--ink);font-weight:600}
.live{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--down);margin-right:5px;vertical-align:1px;box-shadow:0 0 0 3px var(--down-soft)}

/* search */
.search{padding-top:12px;padding-bottom:4px}
.sbox{display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:0 6px 0 12px;height:46px;box-shadow:0 1px 0 rgba(0,0,0,.02)}
.sbox svg{flex:none;color:var(--muted)}
.sbox input{flex:1;min-width:0;border:0;background:transparent;font:inherit;font-size:15px;color:var(--ink);outline:none;height:100%}
.sbox input::placeholder{color:var(--muted)}
.sbox button{flex:none;border:0;background:var(--accent);color:var(--accent-ink);font:600 13px var(--font);border-radius:8px;padding:8px 12px;cursor:pointer}
.shint{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;font-size:12.5px;color:var(--muted);align-items:center}
.shint a{border:1px solid var(--line);border-radius:999px;padding:3px 9px;background:var(--surface);color:var(--ink-2)}

/* section nav */
.snav{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);margin-top:10px}
.snav .wrap{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;padding-top:6px;padding-bottom:6px}
.snav .wrap::-webkit-scrollbar{display:none}
.snav a{flex:none;font-size:13px;font-weight:500;color:var(--ink-2);padding:6px 10px;border-radius:7px}
.snav a:first-child{background:var(--ink);color:var(--bg)}

/* section frame */
section{padding:18px 0 4px}
.sh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin:0 0 10px}
.sh h2{margin:0;font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.sh .sub{font-size:12px;color:var(--muted)}
.sh a{font-size:12.5px;font-weight:600;white-space:nowrap}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--r)}
.p-pad{padding:14px}

/* lead */
.lead{display:block;color:inherit;background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--up);border-radius:var(--r);padding:14px 14px 12px}
.lead:hover{text-decoration:none;border-color:var(--ink-2)}
.lead-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.lead-kicker{font-size:12px;color:var(--muted)}
.pill{font:700 11px/1 var(--font);padding:4px 7px;border-radius:5px;letter-spacing:.02em}
.pill.up{background:var(--up-soft);color:var(--up)}
.pill.down{background:var(--down-soft);color:var(--down)}
.nw{white-space:nowrap}
.lead-h{margin:8px 0 10px;font-size:20px;line-height:1.25;letter-spacing:-.01em}
.lead-bars{display:grid;gap:5px}
.lb-row{display:grid;grid-template-columns:96px 1fr 34px;gap:8px;align-items:center;font-size:12px;color:var(--muted)}
.lb{width:100%;height:10px;display:block}
.lb-v{text-align:right;color:var(--ink);font-weight:600;font-size:13px}
.lead-note{margin:10px 0 0;font-size:12.5px;color:var(--muted)}
.more{color:var(--accent);font-weight:600;white-space:nowrap}

/* KPI tiles */
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.tile{display:flex;flex-direction:column;gap:6px;color:inherit;background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:11px 12px 10px;min-width:0}
.tile:hover{text-decoration:none;border-color:var(--ink-2)}
.t-label{font-size:11.5px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.t-value{display:flex;align-items:baseline;gap:5px}
.t-value .num{font-size:28px;font-weight:700;letter-spacing:-.02em;line-height:1}
.t-unit{font-size:12px;color:var(--muted)}
.cmpwrap{display:grid;gap:3px}
.cmp{width:100%;height:18px;display:block}
.cmplbl{display:flex;justify-content:space-between;gap:6px;font-size:10.5px;color:var(--muted);white-space:nowrap}
.cmplbl span:first-child{font-weight:600}
.up-t{color:var(--up)} .down-t{color:var(--down)} .neutral-t{color:var(--neutral)}
.t-foot{font-size:11.5px;color:var(--muted);line-height:1.35;margin-top:auto}
.chg{font-weight:700}
.chg.up,.up{color:var(--up)} .chg.down,.down{color:var(--down)}
svg .trk{fill:var(--line-2)}
svg .prev{fill:var(--c-minor)}
svg .now.up{fill:var(--up)} svg .now.down{fill:var(--down)} svg .now.neutral{fill:var(--neutral)} svg .now.flat{fill:var(--neutral)}
svg .seg.demo{fill:var(--c-demo)} svg .seg.add{fill:var(--c-add)} svg .seg.newc{fill:var(--c-newc)} svg .seg.ren{fill:var(--c-ren)}
svg .seg.mep{fill:var(--c-mep)} svg .seg.home{fill:var(--c-home)} svg .seg.minor{fill:var(--c-minor)}

/* what changed */
.changed{margin:8px 0 0;padding:4px 12px;list-style:none;background:var(--surface-2);border:1px solid var(--line);border-radius:var(--r)}
.changed-h{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:8px 0 2px}
.changed li{display:flex;gap:9px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line-2);font-size:13.5px}
.changed li:first-of-type{border-top:0}
.arrow{font-size:9px;width:10px;flex:none}
.arrow.up{color:var(--up)} .arrow.down{color:var(--down)}

/* chips */
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:500;color:var(--ink-2);background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:4px 8px;white-space:nowrap}
.chip i{width:8px;height:8px;border-radius:2px;background:var(--c-minor);flex:none}
.chip b{font-weight:700;color:var(--ink)}
.chip.demo i{background:var(--c-demo)} .chip.add i{background:var(--c-add)} .chip.newc i{background:var(--c-newc)} .chip.ren i{background:var(--c-ren)}
.chip.mep i{background:var(--c-mep)} .chip.home i{background:var(--c-home)}
.chip.sm{font-size:11px;padding:2px 7px;font-weight:600}
.chip.sm.demo{color:var(--c-demo);border-color:color-mix(in srgb,var(--c-demo) 35%,var(--line))}
.chip.sm.add{color:var(--c-add);border-color:color-mix(in srgb,var(--c-add) 35%,var(--line))}
.badge-new{font:700 10px/1 var(--font);letter-spacing:.04em;text-transform:uppercase;background:var(--accent);color:var(--accent-ink);border-radius:4px;padding:4px 6px}

/* projects */
.proj{display:grid;gap:10px}
.mapcard{padding:10px}
.map{width:100%;height:auto;display:block;max-height:340px}
.bnd{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.4;stroke-linejoin:round}
.pt{fill:var(--muted);opacity:.55}
.pt-big{stroke:var(--surface);stroke-width:1.4}
.pt-big.add{fill:var(--c-add)} .pt-big.demo{fill:var(--c-demo)} .pt-big.newc{fill:var(--c-newc)}
.mapkey{display:flex;gap:12px;flex-wrap:wrap;font-size:11.5px;color:var(--muted);margin-top:6px}
.mapkey i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:0}
.plist{list-style:none;margin:0;padding:0}
.prow{padding:10px 14px;border-top:1px solid var(--line-2)}
.prow:first-child{border-top:0}
.prow-top{display:flex;align-items:center;gap:6px}
.pdate{margin-left:auto;font:500 11.5px var(--mono);color:var(--muted)}
.paddr{font-weight:600;font-size:15px;margin-top:5px}
.pwork{font-size:12.5px;color:var(--muted);margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
.pfoot{display:flex;justify-content:space-between;gap:8px;padding:10px 14px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted)}

/* mini stat grid */
.mini{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid var(--line-2)}
.mini>div{padding:10px 12px;border-left:1px solid var(--line-2);min-width:0}
.mini>div:first-child{border-left:0}
.mini.m2{grid-template-columns:1fr 1fr}
.mini.m2>div:nth-child(odd){border-left:0}
.mini.m2>div:nth-child(n+3){border-top:1px solid var(--line-2)}
.mini .v{font-size:19px;font-weight:700;letter-spacing:-.01em;line-height:1.1}
.mini .k{font-size:11px;color:var(--muted);line-height:1.3;margin-top:2px}
.hero-stat{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;padding:14px}
.hero-stat .v{font-size:32px;font-weight:700;letter-spacing:-.02em;line-height:1}
.hero-stat .k{font-size:12px;color:var(--muted);margin-top:4px}
.hero-stat .cmpwrap{width:44%;min-width:130px}
.cta{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 14px;border-top:1px solid var(--line);font-weight:600;font-size:13.5px}
.cta span{color:var(--muted);font-weight:400;font-size:12px}

/* ranked list */
.rank{list-style:none;margin:0;padding:4px 14px 8px}
.rk{display:grid;grid-template-columns:18px 1fr;gap:8px;padding:7px 0;border-top:1px solid var(--line-2)}
.rk:first-child{border-top:0}
.rk-n{font:600 11px/1.6 var(--mono);color:var(--muted)}
.rk-line{display:grid;grid-template-columns:1fr 38px 44px;gap:6px;align-items:baseline;font-size:13.5px}
.rk-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rk-c{text-align:right;font-weight:700}
.rk-d{text-align:right;font-size:12px;font-weight:600}
.rk-d.flat{color:var(--muted)}
.rk-bar{width:100%;height:6px;display:block;margin-top:4px;overflow:visible}
.rk-bar .fill{fill:var(--accent)}
.rk-bar .tick{fill:var(--ink)}
.legend{display:flex;gap:12px;font-size:11px;color:var(--muted);padding:0 14px 10px}
.legend i{display:inline-block;vertical-align:1px;margin-right:4px}

/* streets */
.streets{display:grid;gap:10px}

/* history */
.hist{display:grid;gap:10px}
.hcard{padding:14px}
.hk{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.hcard p{margin:6px 0 0;font-size:14px}
.hcard .big{font-size:26px;font-weight:700;letter-spacing:-.02em;margin:6px 0 0;line-height:1}
.ocr{font:600 10px/1 var(--mono);border:1px solid var(--line);color:var(--ink-2);padding:3px 5px;border-radius:4px;letter-spacing:.04em}
blockquote{margin:8px 0 0;padding:8px 12px;border-left:3px solid var(--line);background:var(--surface-2);font-family:Georgia,"Times New Roman",serif;font-size:14.5px;color:var(--ink-2)}
.src{font-size:11.5px;color:var(--muted);margin-top:8px}

/* reps */
.reps{display:grid;grid-template-columns:1fr 1fr}
.anc{padding:10px 14px 12px;min-width:0}
.anc+.anc{border-left:1px solid var(--line-2)}
.anc-h{display:flex;justify-content:space-between;align-items:baseline;gap:6px;font-size:12px;font-weight:700;margin-bottom:4px}
.anc-h a{font-weight:500;font-size:11.5px;white-space:nowrap}
.anc ul{list-style:none;margin:0;padding:0}
.anc li{display:flex;gap:8px;align-items:baseline;padding:5px 0;border-top:1px solid var(--line-2);font-size:13px;min-width:0}
.smd{font:600 11px var(--mono);color:var(--accent);flex:none}
.cname{overflow-wrap:anywhere}

/* subscribe + sponsor */
.sub-row{display:flex;gap:8px;margin-top:10px}
.sub-row input{flex:1;min-width:0;height:42px;border:1px solid var(--line);border-radius:8px;padding:0 12px;font:inherit;background:var(--surface-2);color:var(--ink)}
.sub-row button{height:42px;border:0;border-radius:8px;background:var(--ink);color:var(--bg);font:600 14px var(--font);padding:0 16px;cursor:pointer}
.subnote{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px}
.sponsor{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px;padding:11px 14px;border:1px dashed var(--line);border-radius:var(--r);font-size:13px;color:var(--ink-2)}
.sponsor small{font:600 10px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}

footer{margin-top:24px;border-top:1px solid var(--line);padding:16px 0 28px;font-size:12px;color:var(--muted)}
footer p{margin:0 0 6px}
footer strong{color:var(--ink-2)}

/* desktop */
@media (min-width:760px){
  body{font-size:15.5px}
  .tiles{grid-template-columns:repeat(4,minmax(0,1fr))}
  .week{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:10px;align-items:stretch}
  .week .changed{margin-top:0}
  .proj{grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);align-items:start}
  .two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;align-items:start}
  .streets{grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:start}
  .curbp{grid-column:1;grid-row:1} .treep{grid-column:1;grid-row:2} .rankp{grid-column:2;grid-row:1 / span 3}
  .homes{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr)}
  .homes .hero-stat{flex-direction:column;align-items:stretch;justify-content:center;gap:14px;border-right:1px solid var(--line-2)}
  .homes .hero-stat .cmpwrap{width:100%}
  .homes .m2{border-top:0}
  .homes .cta{grid-column:1 / -1}
  .mapcard{position:sticky;top:56px}
  .hist{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
  .t-value .num{font-size:32px}
  .snav a{font-size:13.5px}
}
"""

ICON_SEARCH = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth Dashboard</title>
<meta name="description" content="What's changing in Petworth, Washington DC, from DC's own open data. Independent; updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="Petworth permits" href="/petworth/permits.xml">
<style>{CSS}</style>
</head>
<body>
<div class="layout-tag">Layout C: Civic Dashboard</div>

<header class="top">
  <div class="wrap">
    <div class="brand">
      <div class="mark" aria-hidden="true">P</div>
      <div><h1>{e(FACTS['neighborhood'])}</h1><p>What's changing in Petworth, from DC's own data</p></div>
    </div>
    <div class="asof"><span class="live" aria-hidden="true"></span>Data as of<b><time datetime="{FACTS['generated_at']}">{asof_short}</time></b>updated nightly</div>
  </div>
</header>

<div class="wrap search">
  <label class="sbox" for="q">{ICON_SEARCH}<input id="q" type="search" placeholder="Look up your block or building" autocomplete="off"><button type="button">Go</button></label>
  <div class="shint">Opens <a href="{link('Block report card')}">Block report card</a><a href="{link('Building biography')}">Building biography</a><a href="{link('Block Watch')}">Block Watch</a></div>
</div>

<nav class="snav" aria-label="Sections"><div class="wrap">
  <a href="#week">This week</a><a href="#projects">Projects</a><a href="#homes">Homes</a><a href="#streets">Streets</a><a href="#history">History</a><a href="#reps">Representatives</a><a href="#subscribe">Subscribe</a>
</div></nav>

<main class="wrap">

<section id="week">
  <div class="sh"><h2>This week</h2><span class="sub">Last 30 days vs the 30 before</span></div>
  <div class="week">
    {lead_html}
    <div class="changed"><div class="changed-h">What changed</div><ul style="list-style:none;margin:0;padding:0">{changed_html}</ul></div>
  </div>
  <div class="tiles">{tiles}</div>
</section>

<section id="projects">
  <div class="sh"><h2>Bigger projects</h2><a href="{link('Block Watch')}">Block Watch →</a></div>
  <div class="chips" style="margin-bottom:10px">{chips_html}</div>
  <div class="proj">
    <div class="panel mapcard">
      {map_svg()}
      <div class="mapkey"><span><i style="background:var(--c-add)"></i>Addition</span><span><i style="background:var(--c-demo)"></i>Demolition</span><span><i style="background:var(--muted);opacity:.55"></i>Other permit</span></div>
    </div>
    <div class="panel">
      <ul class="plist">{proj_rows}</ul>
      <div class="pfoot"><span><b class="num" style="color:var(--ink)">{len(projects)}</b> projects · {new_count} new this week{'' if groups.get('New construction') else ' · no new construction'}</span><a href="/petworth/permits.xml">RSS</a></div>
    </div>
  </div>
</section>

<section id="homes">
  <div class="sh"><h2>Homes</h2><a href="{link('Housing pulse')}">Housing pulse →</a></div>
  <div class="panel homes">
    <div class="hero-stat">
      <div><div class="v num">{homes['median_house_price_12mo']}</div><div class="k">Median house price, last 12 months</div></div>
      {cmp_block(med60, med12, "neutral", f"60 days {homes['median_price_60d']}", f"12 mo {homes['median_house_price_12mo']}")}
    </div>
    <div class="mini m2">
      <div><div class="v num">{homes['house_sales_12mo']}</div><div class="k">house sales, 12 months</div></div>
      <div><div class="v num">{homes['market_sales_60d']}</div><div class="k">sales, last 60 days</div></div>
      <div><div class="v num">{homes['median_price_per_sqft_60d']}</div><div class="k">median per sq ft, 60 days</div></div>
      <div><div class="v num">~{condo}</div><div class="k">median condo, 12 mo (approx.)</div></div>
    </div>
    <a class="cta" href="{link('Assessment check')}">Is your assessment in line with sales? <span>Assessment check →</span></a>
  </div>
</section>

<section id="streets">
  <div class="sh"><h2>Streets</h2><a href="{link('Curb radar')}">Curb radar →</a></div>
  <div class="streets">
    <div class="panel curbp">
      <div class="mini" style="border-top:0">
        <div><div class="v num">{streets['curb_permits_active_this_week']}</div><div class="k">curb permits active this week</div></div>
        <div><div class="v num">{streets['curb_permits_starting_next_7d']}</div><div class="k">starting in the next 7 days</div></div>
        <div><div class="v num">{curb_mi:.1f} mi</div><div class="k">{fmt(streets['curb_reserved_ft'])} ft of curb reserved</div></div>
      </div>
    </div>
    <div class="panel rankp">
      <div class="sh" style="padding:12px 14px 0;margin:0"><h2 style="font-size:11.5px">Top 311 requests · 30 days</h2><a href="{link('311 report card')}">All types →</a></div>
      <ol class="rank">{rank_rows}</ol>
      <div class="legend"><span><i style="width:10px;height:6px;background:var(--accent)"></i>Last 30 days</span><span><i style="width:2px;height:9px;background:var(--ink)"></i>Prior 30 days</span></div>
    </div>
    <div class="panel treep">
      <div class="mini" style="border-top:0">
        <div><div class="v num">{fmt(trees['street_trees'])}</div><div class="k">street trees, {trees['species']} species</div></div>
        <div><div class="v num">{trees['planted_last_5y']}</div><div class="k">planted in the last 5 years</div></div>
        <div><div class="v num" style="color:var(--accent)">{trees['empty_boxes_open']}</div><div class="k">empty tree boxes open</div></div>
      </div>
      <a class="cta" href="{link('Street trees')}">Find an empty tree box near you <span>Street trees →</span></a>
    </div>
  </div>
</section>

<section id="history">
  <div class="sh"><h2>History</h2><a href="{link('100 years ago')}">100 years ago →</a></div>
  <div class="hist">
    <a class="panel hcard" href="{link('Building biography')}" style="color:inherit;text-decoration:none">
      <div class="hk">{e(hist['block'])}</div>
      <div class="big num">62 rowhouses · 1926</div>
      <p>{e(hist['fact'])}</p>
      <div class="src"><span style="color:var(--accent);font-weight:600">Building biography →</span></div>
    </a>
    <div class="panel hcard">
      <div class="hk">100 years ago this week <span class="ocr">OCR TEXT</span></div>
      <blockquote>“{e(hist['hundred_years_ago_excerpt_ocr'])}”</blockquote>
      <div class="src">{e(hist['hundred_years_ago_source'])}. Machine-read text; may contain errors.</div>
    </div>
  </div>
</section>

<div class="two">
<section id="reps">
  <div class="sh"><h2>Who represents you</h2><span class="sub">{len(reps)} SMDs · ANC {' & '.join(sorted({r['anc'] for r in reps}))}</span></div>
  <div class="panel reps">{rep_rows}</div>
  <p class="sub" style="font-size:12px;color:var(--muted);margin:8px 0 0">Each Single Member District elects one commissioner. Names of elected officials are public record.</p>
</section>

<section id="subscribe">
  <div class="sh"><h2>Get the weekly email</h2><a href="{link('Weekly email')}">See a sample →</a></div>
  <div class="panel p-pad">
    <div style="font-size:14px">These numbers in your inbox once a week.</div>
    <form class="sub-row" onsubmit="return false"><input type="email" placeholder="you@example.com" aria-label="Email address"><button type="button">Subscribe</button></form>
    <div class="subnote"><span>One email a week. Mock signup.</span><a href="/petworth/permits.xml">Permits RSS feed</a></div>
  </div>
  <div class="sponsor"><span>Presented by <b>[Local sponsor]</b></span><small>Sponsor</small></div>
</section>
</div>

</main>

<footer><div class="wrap">
  <p><strong>Independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission, or any Business Improvement District.</strong></p>
  <p>Sources: Open Data DC (CC BY 4.0); Library of Congress, Chronicling America. Crime figures are preliminary counts. Data as of {asof}.</p>
  <p>petworth.org</p>
</div></footer>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
