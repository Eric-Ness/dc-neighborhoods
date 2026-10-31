"""Layout C3: Vital Signs. Reads design/layouts/facts.json, writes design/layouts/C3-vital-signs.html.

The neighborhood as a calm instrument panel: each metric is a "vital" with a small
dial comparing the last 30 days with the 30 before (only those two data points).
State (rising / easing / steady) is carried by shape and icon as well as color.

Run from anywhere:  python design/layouts/src/C3_vital_signs.py
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
OUT = LAYOUTS / "C3-vital-signs.html"

e = html.escape

STEADY_BAND = 0.05   # within ±5% of the comparison reads as "steady"
DIAL_RANGE = 0.50    # dial ends sit at −50% / +50% of the comparison value


# ---------- helpers (adapted from C) ----------
def link(name: str) -> str:
    return "../../" + FACTS["demo_links"][name]


def fmt(n: int) -> str:
    return f"{n:,}"


def title_case(s: str) -> str:
    keep = {"NW", "NE", "SW", "SE", "ADU"}
    return " ".join(w if w in keep or any(c.isdigit() for c in w) else w.capitalize() for w in s.split())


def addr(s: str) -> str:
    return title_case(re.sub(r"\s+\d{5}$", "", s.strip()))


def clean_work(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"(?<=[a-z]\.)(?=[A-Z])", " ", s)          # "grade.Rear" -> "grade. Rear"
    s = re.sub(r"(?<=[A-Z]{3})(?=[A-Z][a-z])", " ", s)     # "ADUNew" -> "ADU New"
    return s + "…" if len(s) >= 150 else s


def to_eastern(dt: datetime) -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo("America/New_York"))
    except Exception:
        y = dt.year
        mar = datetime(y, 3, 8, 7, tzinfo=timezone.utc)
        mar += timedelta(days=(6 - mar.weekday()) % 7)
        nov = datetime(y, 11, 1, 6, tzinfo=timezone.utc)
        nov += timedelta(days=(6 - nov.weekday()) % 7)
        off = -4 if mar <= dt < nov else -5
        return dt.astimezone(timezone(timedelta(hours=off)))


def price_k(s: str) -> int:
    return int(re.sub(r"[^\d]", "", s.split()[0]))


def reading(cur: float, prev: float) -> dict:
    d = cur - prev
    ratio = d / prev if prev else 0.0
    state = "steady" if abs(ratio) < STEADY_BAND else ("rising" if d > 0 else "easing")
    pct = round(ratio * 100) if (cur >= 100 and prev >= 100) else None  # no % on small counts
    return {"d": d, "ratio": ratio, "state": state, "pct": pct}


STATE_WORD = {"rising": "Rising", "easing": "Easing", "steady": "Steady"}


def icon(state: str, cls: str = "ic") -> str:
    """State glyph: triangle up / triangle down / level bar. Shape carries meaning without color."""
    shapes = {
        "rising": '<path d="M6 1.5 L11 10.5 H1 Z"/>',
        "easing": '<path d="M6 10.5 L11 1.5 H1 Z"/>',
        "steady": '<rect x="1" y="4.5" width="10" height="3" rx="1.5"/>',
    }
    return f'<svg class="{cls} s-{state}" viewBox="0 0 12 12" aria-hidden="true">{shapes[state]}</svg>'


def state_tag(state: str) -> str:
    return f'<span class="tag s-{state}">{icon(state)}{STATE_WORD[state]}</span>'


# ---------- the dial ----------
CX, CY, R = 60.0, 58.0, 46.0


def _pt(theta_deg: float, r: float = R) -> tuple[float, float]:
    t = math.radians(theta_deg)
    return CX + r * math.cos(t), CY - r * math.sin(t)


def dial(cur: float, prev: float, state: str, label: str) -> str:
    """Half-circle dial. Top centre = the prior period. The marker swings right when the
    latest period is higher, left when lower; the dial ends are −50% and +50%."""
    ratio = max(-DIAL_RANGE, min(DIAL_RANGE, (cur - prev) / prev if prev else 0))
    theta = 90 - ratio / DIAL_RANGE * 90
    x0, y0 = _pt(180)
    x1, y1 = _pt(0)
    tx, ty = _pt(90)
    mx, my = _pt(theta)
    # steady band, drawn as a pale wedge either side of the top
    b = STEADY_BAND / DIAL_RANGE * 90
    bx0, by0 = _pt(90 + b)
    bx1, by1 = _pt(90 - b)
    sweep = 1 if theta < 90 else 0
    fill_arc = (f'<path class="d-fill s-{state}" d="M{tx:.1f},{ty:.1f} A{R},{R} 0 0 {sweep} {mx:.1f},{my:.1f}"/>'
                if abs(theta - 90) > 0.5 else "")
    # inner ticks every 10%
    ticks = []
    for i in range(-5, 6):
        a = 90 - i * 18
        ax, ay = _pt(a, R - 7)
        bx, by = _pt(a, R - (11 if i in (-5, 0, 5) else 9))
        ticks.append(f'<line class="d-tick{" maj" if i in (-5, 0, 5) else ""}" x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}"/>')
    # marker: shape follows state
    if state == "rising":
        mark = f'<path class="d-mark s-{state}" d="M{mx:.1f},{my - 6.5:.1f} L{mx + 6:.1f},{my + 4:.1f} L{mx - 6:.1f},{my + 4:.1f} Z"/>'
    elif state == "easing":
        mark = f'<path class="d-mark s-{state}" d="M{mx:.1f},{my + 6.5:.1f} L{mx + 6:.1f},{my - 4:.1f} L{mx - 6:.1f},{my - 4:.1f} Z"/>'
    else:
        mark = f'<circle class="d-mark s-{state}" cx="{mx:.1f}" cy="{my:.1f}" r="5"/>'
    return (
        f'<svg class="dial" viewBox="0 0 120 70" role="img" aria-label="{e(label)}">'
        f'<path class="d-track" d="M{x0:.1f},{y0:.1f} A{R},{R} 0 0 1 {x1:.1f},{y1:.1f}"/>'
        f'<path class="d-band" d="M{bx0:.1f},{by0:.1f} A{R},{R} 0 0 1 {bx1:.1f},{by1:.1f}"/>'
        f'{"".join(ticks)}{fill_arc}'
        f'<line class="d-prior" x1="{tx:.1f}" y1="{ty - 6:.1f}" x2="{tx:.1f}" y2="{ty + 6:.1f}"/>'
        f'{mark}'
        f'<text class="d-lbl" x="{x0 + 2:.1f}" y="68" text-anchor="middle">lower</text>'
        f'<text class="d-lbl" x="{x1 - 2:.1f}" y="68" text-anchor="middle">higher</text>'
        f'</svg>'
    )


# ---------- derived data ----------
gen = datetime.fromisoformat(FACTS["generated_at"].replace("Z", "+00:00"))
loc = to_eastern(gen)
hour = loc.strftime("%I").lstrip("0")
asof = f"{loc.strftime('%b')} {loc.day}, {loc.year}, {hour}:{loc.strftime('%M %p')} ET"
asof_day = f"{loc.strftime('%A, %B')} {loc.day}"

tm = FACTS["this_month"]
homes = FACTS["homes"]
streets = FACTS["streets"]
trees = FACTS["trees"]
hist = FACTS["history"]
reps = FACTS["representatives"]
groups = FACTS["permit_groups"]

RODENT = "DC Health Rodent & Vector Control"
by_type = {t["type"]: t for t in tm["top_311_types"]}
for m in tm["top_311_movers"]:
    by_type.setdefault(m["type"], m)

rod = by_type[RODENT]
rod_r = reading(rod["count"], rod["previous"])

med12 = price_k(homes["median_house_price_12mo"])
med60 = price_k(homes["median_price_60d"])


def more_fewer(d: int, noun: str) -> str:
    return f"{abs(d):,} {'more' if d > 0 else 'fewer'} {noun}"


def vital(name, cur, prev, unit_noun, href, note="", cur_txt=None, prev_txt=None, prev_lbl="prior 30 days",
          read_txt=None):
    r = reading(cur, prev)
    cur_txt = cur_txt or fmt(cur)
    prev_txt = prev_txt or fmt(prev)
    if read_txt is None:
        if r["state"] == "steady":
            read_txt = f"About level with the 30 days before ({prev_txt})."
        else:
            read_txt = f"{more_fewer(r['d'], unit_noun)} than the 30 days before"
            read_txt += f" ({'+' if r['d'] > 0 else '−'}{abs(r['pct'])}%)." if r["pct"] is not None else "."
            read_txt = read_txt[0].upper() + read_txt[1:]
        if note:
            read_txt += " " + note
    lbl = f"{name}: {cur_txt} in the last period against {prev_txt} in the {prev_lbl}. {STATE_WORD[r['state']]}."
    return {"name": name, "r": r, "cur": cur_txt, "prev": prev_txt, "prev_lbl": prev_lbl, "read": read_txt,
            "href": href, "gauge": dial(cur, prev, r["state"], lbl)}


VITALS = [
    vital("311 requests", tm["requests_30d"], tm["requests_prev_30d"], "requests", link("311 report card")),
    vital("Crime reports", tm["crime_30d"], tm["crime_prev_30d"], "reports", link("Block report card"),
          note="Shown as counts only."),
    vital("Illegal dumping", by_type["Illegal Dumping"]["count"], by_type["Illegal Dumping"]["previous"],
          "reports", link("311 report card")),
    vital("Yard waste pickups", by_type["Scheduled Yard Waste"]["count"], by_type["Scheduled Yard Waste"]["previous"],
          "requests", link("311 report card")),
    vital("Median house price", med60, med12, "", "#homes",
          cur_txt=homes["median_price_60d"], prev_txt=homes["median_house_price_12mo"], prev_lbl="12-month median",
          read_txt=(f"The last 60 days' median, {homes['median_price_60d']}, sits ${med12 - med60}K under the "
                    f"12-month median of {homes['median_house_price_12mo']}. Within the steady band."
                    if abs(med60 - med12) / med12 < STEADY_BAND else
                    f"The last 60 days' median is {homes['median_price_60d']}, against {homes['median_house_price_12mo']} over 12 months.")),
]

# permits: no prior-month figure exists, so its instrument is a composition ring instead of a dial
GROUP_ORDER = ["Demolition", "New construction", "Additions", "Renovation & repair",
               "Electrical, plumbing & mechanical", "Home businesses", "Minor work"]
GROUP_KEY = {"Demolition": "demo", "New construction": "newc", "Additions": "add",
             "Renovation & repair": "ren", "Electrical, plumbing & mechanical": "mep",
             "Home businesses": "home", "Minor work": "minor"}
GROUP_SHORT = {"Electrical, plumbing & mechanical": "Electrical, plumbing, mech."}
big_types = ["Demolition", "New construction", "Additions"]
permits_total = tm["permits_30d"]
big_count = sum(groups.get(g, 0) for g in big_types)


def ring() -> str:
    rr, c = 24.0, 2 * math.pi * 24.0
    segs, off = [], 0.0
    for g in GROUP_ORDER:
        n = groups.get(g, 0)
        if not n:
            continue
        L = c * n / permits_total
        segs.append(f'<circle class="rg {GROUP_KEY[g]}" cx="60" cy="38" r="{rr}" stroke-dasharray="{max(L - 1.2, 0.8):.2f} {c:.2f}" '
                     f'stroke-dashoffset="{-off:.2f}" transform="rotate(-90 60 38)"><title>{e(g)}: {n}</title></circle>')
        off += L
    return (f'<svg class="dial ringsvg" viewBox="0 0 120 70" role="img" aria-label="Building permits: {permits_total} in 30 days, '
            f'{big_count} of them demolition or additions">{"".join(segs)}'
            f'<text class="rg-n" x="60" y="42" text-anchor="middle">{big_count}</text></svg>')


demo_n, add_n = groups.get("Demolition", 0), groups.get("Additions", 0)
permit_vital = {
    "name": "Building permits", "cur": fmt(permits_total), "prev": "",
    "read": (f"{add_n} addition{'s' if add_n != 1 else ''} and {demo_n} demolition among them; "
             f"the rest are smaller jobs. No prior-month count in this feed, so this one shows a mix, not a change."),
    "href": "#projects", "gauge": ring(),
}


def vital_html(v: dict) -> str:
    if "r" in v:
        r = v["r"]
        st = r["state"]
        dtxt = f"{'+' if r['d'] > 0 else ('−' if r['d'] < 0 else '±')}"
        if v["name"] == "Median house price":
            dtxt += f"${abs(med12 - med60)}K"
        else:
            dtxt += fmt(abs(r["d"]))
        side = (f'<div class="v-num num">{v["cur"]}</div>'
                f'<div class="v-cmp"><span class="chg s-{st}">{icon(st)}{dtxt}</span>'
                f'<span class="v-prev">vs <b class="num">{v["prev"]}</b> {v["prev_lbl"]}</span></div>')
        tag = state_tag(st)
    else:
        side = (f'<div class="v-num num">{v["cur"]}</div>'
                f'<div class="v-cmp"><span class="chg s-mix">{big_count} larger</span>'
                f'<span class="v-prev">issued, last 30 days</span></div>')
        tag = '<span class="tag s-mix"><svg class="ic" viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/></svg>Mix</span>'
    return f"""
<a class="vital" href="{v['href']}">
  <div class="v-name">{e(v['name'])}{tag}</div>
  <div class="v-gauge">{v['gauge']}</div>
  <div class="v-side">{side}</div>
  <p class="v-read">{e(v['read'])}</p>
</a>"""


all_vitals = VITALS + [permit_vital]
vitals_html = "".join(vital_html(v) for v in all_vitals)

# condition summary counts include the lead (rodents)
states = [rod_r["state"]] + [v["r"]["state"] for v in VITALS]
counts = {s: states.count(s) for s in ("rising", "easing", "steady")}
cond_strip = "".join(
    f'<li class="s-{s}">{icon(s)}<b class="num">{counts[s]}</b> {STATE_WORD[s].lower()}</li>' for s in ("rising", "easing", "steady")
)
rising_names = ["Rodent complaints"] + [v["name"].lower() for v in VITALS if v["r"]["state"] == "rising"]
cond_word = ("Mostly easing" if counts["easing"] > counts["rising"] else "Mixed") + \
    f", with {len(rising_names)} reading{'s' if len(rising_names) != 1 else ''} rising"

lead_dial = dial(rod["count"], rod["previous"], rod_r["state"],
                 f"Rodent complaints: {rod['count']} in the last 30 days against {rod['previous']} in the 30 days before. Rising.")


# ---------- map ----------
def map_svg() -> str:
    rings_ = FACTS["boundary_rings"]
    pts = [p for r in rings_ for p in r]
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(lons), max(lons), min(lats), max(lats)
    k = math.cos(math.radians((miny + maxy) / 2))
    W, pad = 320, 12
    sc = (W - 2 * pad) / ((maxx - minx) * k)
    H = round((maxy - miny) * sc + 2 * pad)
    px = lambda lon: pad + (lon - minx) * k * sc
    py = lambda lat: pad + (maxy - lat) * sc
    d = " ".join("M" + "L".join(f"{px(x):.1f},{py(y):.1f}" for x, y in r) + "Z" for r in rings_)
    # faint contour-like grid for the instrument feel
    grid = "".join(f'<line class="mgrid" x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(20, H, 40))
    grid += "".join(f'<line class="mgrid" x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(20, W, 40))
    small, big, seen = [], [], set()
    for p in FACTS["permit_points"]:
        key = (round(p["lon"], 5), round(p["lat"], 5), p["group"] in big_types)
        if key in seen:
            continue
        seen.add(key)
        x, y = px(p["lon"]), py(p["lat"])
        if p["group"] in big_types:
            gk = GROUP_KEY[p["group"]]
            if gk == "demo":
                big.append(f'<rect class="pt-big demo" x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" transform="rotate(45 {x:.1f} {y:.1f})"><title>Demolition</title></rect>')
            else:
                big.append(f'<circle class="pt-big {gk}" cx="{x:.1f}" cy="{y:.1f}" r="5.2"><title>{e(p["group"])}</title></circle>')
        else:
            small.append(f'<circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="2.3"/>')
    return (f'<svg class="map" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Map of Petworth with permit locations from the last 30 days; larger marks are additions and demolition">'
            f'<defs><clipPath id="clipb"><path d="{d}"/></clipPath></defs>'
            f'<path d="{d}" class="bnd"/><g clip-path="url(#clipb)">{grid}</g>'
            f'{"".join(small)}{"".join(big)}</svg>')


def permit_bar() -> str:
    segs, x = [], 0.0
    for g in GROUP_ORDER:
        n = groups.get(g, 0)
        if not n:
            continue
        w = 100 * n / permits_total
        segs.append(f'<rect class="seg {GROUP_KEY[g]}" x="{x:.2f}" y="0" width="{max(w - 0.5, 0.4):.2f}" height="10"><title>{e(g)}: {n}</title></rect>')
        x += w
    return f'<svg class="pbar" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true">{"".join(segs)}</svg>'


group_legend = "".join(
    f'<li><i class="sw {GROUP_KEY[g]}"></i><span>{e(GROUP_SHORT.get(g, g))}</span><b class="num">{groups[g]}</b></li>'
    for g in GROUP_ORDER if g in groups
)

# ---------- projects ----------
projects = []
for p in FACTS["bigger_projects"]:
    issued = datetime.fromisoformat(p["issued"].replace("Z", "+00:00"))
    age = (gen.date() - issued.date()).days
    projects.append({"addr": addr(p["address"]), "group": p["group"], "issued": issued,
                     "date": f"{issued.strftime('%b')} {issued.day}", "new": 0 <= age <= 7,
                     "work": clean_work(p["work"])})
new_count = sum(p["new"] for p in projects)


def proj_mark(g: str) -> str:
    if g == "Demolition":
        return '<svg class="pm" viewBox="0 0 12 12" aria-hidden="true"><rect class="demo" x="2.5" y="2.5" width="7" height="7" transform="rotate(45 6 6)"/></svg>'
    return f'<svg class="pm" viewBox="0 0 12 12" aria-hidden="true"><circle class="{GROUP_KEY.get(g, "add")}" cx="6" cy="6" r="4.5"/></svg>'


proj_rows = "".join(f"""
<li class="prow">
  <div class="p-l">{proj_mark(p['group'])}</div>
  <div class="p-m">
    <div class="paddr">{e(p['addr'])}</div>
    <div class="pmeta"><span>{'Addition' if p['group'] == 'Additions' else e(p['group'])}</span><span aria-hidden="true">·</span><time class="num" datetime="{p['issued'].date().isoformat()}">{p['date']}</time>{'<span class="newb">New this week</span>' if p['new'] else ''}</div>
    <div class="pwork">{e(p['work'])}</div>
  </div>
</li>""" for p in projects)

# ---------- 311 types as compact readings ----------
t311 = ""
for t in tm["top_311_types"]:
    r = reading(t["count"], t["previous"])
    name = {"DC Health Rodent & Vector Control": "Rodent & vector control"}.get(t["type"], t["type"])
    dd = f"{'+' if r['d'] > 0 else ('−' if r['d'] < 0 else '±')}{abs(r['d'])}"
    t311 += (f'<li><span class="t-n">{e(name)}</span><span class="t-c num">{t["count"]}</span>'
             f'<span class="chg s-{r["state"]}">{icon(r["state"])}{dd}</span><span class="t-p num">was {t["previous"]}</span></li>')

curb_mi = streets["curb_reserved_ft"] / 5280

# ---------- reps ----------
rep_html = ""
for anc in sorted({r["anc"] for r in reps}):
    rs = [r for r in reps if r["anc"] == anc]
    rep_html += (f'<div class="anc"><div class="anc-h"><span>ANC {anc}</span><a href="{e(rs[0]["url"])}">ANC {anc} site ↗</a></div><ul>'
                 + "".join(f'<li><span class="smd num">{r["smd"]}</span><span>{e(title_case(r["commissioner"]))}</span></li>' for r in rs)
                 + "</ul></div>")

ICON_SEARCH = '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M13 13l4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'

CSS = r"""
:root{
  --bg:#f1efea; --surface:#fbfaf7; --surface-2:#f5f3ee; --ink:#1e2a2e; --ink-2:#3e4a4d; --muted:#6a7471;
  --line:#ddd9d0; --line-2:#e8e5de;
  --accent:#466f60; --accent-soft:#e2ebe5;
  --rising:#b05a36; --rising-soft:#f4e3d9;
  --easing:#3d6684; --easing-soft:#dfe8ef;
  --steady:#6f7a75; --steady-soft:#e7e9e6;
  --mix:#7a6a45;
  --track:#e3e0d8; --band:#d3d8d2;
  --c-demo:#b05a36; --c-add:#466f60; --c-newc:#7a6a45; --c-ren:#8fa3ae; --c-mep:#b4bab6; --c-home:#c4ac78; --c-minor:#d9dcd6;
  --sans:"Instrument Sans", "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, "Cascadia Mono", Consolas, Menlo, monospace;
  --r:16px;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#151b1d; --surface:#1d2528; --surface-2:#192023; --ink:#e8ebe8; --ink-2:#c3cac7; --muted:#8f9a97;
    --line:#2e383b; --line-2:#263033; --accent:#8fbfa9; --accent-soft:#22332d;
    --rising:#e39a76; --rising-soft:#3a2a22; --easing:#8fb6d3; --easing-soft:#1f2e39; --steady:#a3aca8; --steady-soft:#283033;
    --mix:#cdb886; --track:#2d3639; --band:#3a4645;
    --c-demo:#e39a76; --c-add:#8fbfa9; --c-ren:#6f8794; --c-mep:#56605e; --c-home:#a99464; --c-minor:#3c4648;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.wrap{max-width:1240px;margin:0 auto;padding:0 16px}
.layout-tag{background:var(--ink);color:var(--bg);font:600 11px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;padding:7px 16px}

/* header */
header{padding:18px 0 6px}
.hd{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}
.brand h1{margin:0;font-size:30px;line-height:1.05;letter-spacing:-.02em;font-weight:600}
.brand p{margin:4px 0 0;color:var(--muted);font-size:14px}
.asof{font:500 12px/1.4 var(--mono);color:var(--muted);text-align:right}
.asof b{color:var(--ink);font-weight:600}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);margin-right:6px;vertical-align:1px;box-shadow:0 0 0 3px var(--accent-soft)}
.search{margin-top:14px}
.sbox{display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:6px 6px 6px 16px;color:var(--muted)}
.sbox input{flex:1;min-width:0;border:0;background:transparent;font:inherit;color:var(--ink);padding:8px 0;outline:none}
.sbox button{border:0;background:var(--ink);color:var(--bg);font:600 14px var(--sans);border-radius:999px;padding:9px 18px}
.shint{font-size:12.5px;color:var(--muted);margin:7px 4px 0}
.shint a{margin-left:10px;text-decoration:none;font-weight:600}
nav.snav{margin-top:14px;overflow-x:auto;scrollbar-width:none}
nav.snav::-webkit-scrollbar{display:none}
nav.snav ul{list-style:none;margin:0;padding:0;display:flex;gap:6px;white-space:nowrap}
nav.snav a{display:block;text-decoration:none;color:var(--ink-2);font-size:13px;padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface)}

/* generic panels */
main{padding:14px 0 28px}
.row{display:grid;gap:14px;margin-top:14px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px}
.ph{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin:0 0 12px}
.ph h2{margin:0;font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2)}
.ph a,.ph .sub{font-size:12.5px;color:var(--muted);text-decoration:none;white-space:nowrap}
.ph a{color:var(--accent);font-weight:600}

/* state tokens: color + shape */
.ic{width:11px;height:11px;flex:none;fill:currentColor}
.s-rising{color:var(--rising)} .s-easing{color:var(--easing)} .s-steady{color:var(--steady)} .s-mix{color:var(--mix)}
.tag{display:inline-flex;align-items:center;gap:5px;font:600 11px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;padding:5px 8px 5px 7px;border-radius:999px;white-space:nowrap}
.tag.s-rising{background:var(--rising-soft)} .tag.s-easing{background:var(--easing-soft)} .tag.s-steady{background:var(--steady-soft)} .tag.s-mix{background:var(--surface-2);border:1px solid var(--line)}
.chg{display:inline-flex;align-items:center;gap:4px;font:600 13px/1 var(--mono);white-space:nowrap}

/* dial */
.dial{display:block;width:100%;height:auto;overflow:visible}
.d-track{fill:none;stroke:var(--track);stroke-width:9;stroke-linecap:round}
.d-band{fill:none;stroke:var(--band);stroke-width:9}
.d-fill{fill:none;stroke:currentColor;stroke-width:9;stroke-linecap:round;opacity:.85}
.d-tick{stroke:var(--muted);stroke-width:.8;opacity:.45}
.d-tick.maj{opacity:.8;stroke-width:1.1}
.d-prior{stroke:var(--ink);stroke-width:2;stroke-linecap:round}
.d-mark{fill:currentColor;stroke:var(--surface);stroke-width:2;stroke-linejoin:round}
.d-lbl{font:500 7.5px var(--mono);fill:var(--muted)}
.rg{fill:none;stroke-width:9}
.rg.demo{stroke:var(--c-demo)} .rg.add{stroke:var(--c-add)} .rg.newc{stroke:var(--c-newc)} .rg.ren{stroke:var(--c-ren)} .rg.mep{stroke:var(--c-mep)} .rg.home{stroke:var(--c-home)} .rg.minor{stroke:var(--c-minor)}
.rg-n{font:600 14px var(--mono);fill:var(--ink)}

/* condition */
.cond{display:grid;gap:18px;padding:22px 18px;background:var(--surface);border:1px solid var(--line);border-radius:20px}
.c-kick{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font:600 12px/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.c-kick .tag{letter-spacing:.04em}
.c-head{margin:10px 0 0;font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.015em;text-wrap:pretty}
.c-head .num{font-weight:600}
.c-word{margin:12px 0 0;color:var(--ink-2);font-size:15px}
.c-strip{list-style:none;margin:14px 0 0;padding:0;display:flex;gap:8px;flex-wrap:wrap}
.c-strip li{display:inline-flex;align-items:center;gap:6px;font-size:13px;padding:6px 11px;border-radius:999px;border:1px solid var(--line);background:var(--surface-2)}
.c-strip li b{color:var(--ink)}
.c-gauge{background:var(--surface-2);border-radius:14px;padding:14px 16px 12px;border:1px solid var(--line-2)}
.c-gauge .dial{max-width:300px;margin:0 auto}
.c-gauge .d-lbl{font-size:4.6px}
.c-gl{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-top:8px}
.c-gl div{font-size:12px;color:var(--muted)}
.c-gl b{display:block;font:600 22px/1.1 var(--mono);color:var(--ink)}
.c-gl .r b{color:var(--rising)}
.c-gl .r{text-align:right}
.c-how{font-size:12px;color:var(--muted);margin:10px 0 0;line-height:1.45}
.c-how .pk{display:inline-block;width:2px;height:11px;background:var(--ink);vertical-align:-1px;margin:0 3px}

/* vitals: phone = stacked compact rows inside one panel */
.vitals{padding:4px 0}
.vlist{display:block}
.vital{display:grid;grid-template-columns:72px 1fr auto;grid-template-areas:"g name side" "g read read";column-gap:12px;row-gap:2px;align-items:center;
  padding:12px 16px;border-top:1px solid var(--line-2);color:inherit;text-decoration:none}
.vital:first-child{border-top:0}
.v-gauge{grid-area:g;align-self:start;padding-top:2px}
.v-gauge .d-lbl{display:none}
.v-name{grid-area:name;display:flex;align-items:center;gap:8px;font-weight:600;font-size:15px;line-height:1.25;min-width:0;flex-wrap:wrap}
.v-name .tag{display:none}
.v-side{grid-area:side;text-align:right}
.v-num{font-size:19px;font-weight:600;line-height:1.1}
.v-cmp{display:flex;flex-direction:column;align-items:flex-end;gap:3px;margin-top:3px}
.v-cmp .chg{font-size:12px}
.v-prev{display:none;font-size:12px;color:var(--muted)}
.v-read{grid-area:read;margin:2px 0 0;font-size:13px;line-height:1.4;color:var(--ink-2)}

/* map panel */
.mapwrap{position:relative;background:var(--surface-2);border:1px solid var(--line-2);border-radius:12px;padding:10px}
.map{display:block;width:100%;height:auto;max-height:520px}
.bnd{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.4;stroke-linejoin:round}
.mgrid{stroke:var(--accent);stroke-width:.4;opacity:.25}
.pt{fill:var(--ink-2);opacity:.45}
.pt-big{stroke:var(--surface);stroke-width:1.6}
.pt-big.add{fill:var(--c-add)} .pt-big.demo{fill:var(--c-demo)} .pt-big.newc{fill:var(--c-newc)}
.mkey{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:10px 2px 0}
.mkey span{display:inline-flex;align-items:center;gap:5px}
.mkey svg{width:11px;height:11px}
.m-big{display:flex;align-items:baseline;gap:8px;margin:14px 0 8px}
.m-big b{font:600 26px/1 var(--mono)}
.m-big span{font-size:13px;color:var(--muted)}
.pbar{display:block;width:100%;height:10px;border-radius:5px;overflow:hidden}
.seg.demo{fill:var(--c-demo)} .seg.add{fill:var(--c-add)} .seg.newc{fill:var(--c-newc)} .seg.ren{fill:var(--c-ren)} .seg.mep{fill:var(--c-mep)} .seg.home{fill:var(--c-home)} .seg.minor{fill:var(--c-minor)}
.glist{list-style:none;margin:10px 0 0;padding:0;display:grid;grid-template-columns:1fr;gap:4px 18px;font-size:13px}
.glist li{display:flex;align-items:center;gap:8px}
.glist span{flex:1;color:var(--ink-2)}
.sw{width:10px;height:10px;border-radius:3px;flex:none}
.sw.demo{background:var(--c-demo)} .sw.add{background:var(--c-add)} .sw.newc{background:var(--c-newc)} .sw.ren{background:var(--c-ren)} .sw.mep{background:var(--c-mep)} .sw.home{background:var(--c-home)} .sw.minor{background:var(--c-minor)}

/* projects */
.plist{list-style:none;margin:0;padding:0}
.prow{display:grid;grid-template-columns:18px 1fr;gap:10px;padding:11px 0;border-top:1px solid var(--line-2)}
.prow:first-child{border-top:0;padding-top:2px}
.pm{width:12px;height:12px;margin-top:4px}
.pm .add{fill:var(--c-add)} .pm .demo{fill:var(--c-demo)} .pm .newc{fill:var(--c-newc)}
.paddr{font-weight:600;font-size:15px}
.pmeta{display:flex;gap:6px;flex-wrap:wrap;align-items:center;font-size:12.5px;color:var(--muted)}
.newb{font:600 10.5px/1 var(--sans);letter-spacing:.05em;text-transform:uppercase;color:var(--accent);background:var(--accent-soft);padding:4px 7px;border-radius:999px}
.pwork{font-size:13px;color:var(--ink-2);margin-top:3px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pfoot{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line-2);padding-top:10px;margin-top:4px}

/* stat readings */
.stats{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line-2);border:1px solid var(--line-2);border-radius:12px;overflow:hidden}
.stats>div{background:var(--surface);padding:12px 12px 11px}
.stats .v{font:600 20px/1.15 var(--mono)}
.stats .k{font-size:12.5px;color:var(--muted);margin-top:3px;line-height:1.35}
.stats .wide{grid-column:1/-1}
.stats.s3>div:last-child{grid-column:1/-1}
.hero{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.hero b{font:600 34px/1 var(--mono);letter-spacing:-.02em}
.hero span{font-size:13px;color:var(--muted)}
.cta{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:12px;padding:12px 14px;border-radius:12px;background:var(--accent-soft);color:var(--ink);text-decoration:none;font-size:14px}
.cta span{color:var(--accent);font-weight:600;white-space:nowrap}

.t311{list-style:none;margin:0;padding:0}
.t311 li{display:grid;grid-template-columns:1fr auto auto;grid-template-areas:"n c d" "n p p";column-gap:12px;align-items:center;padding:9px 0;border-top:1px solid var(--line-2)}
.t311 li:first-child{border-top:0;padding-top:0}
.t-n{grid-area:n;font-size:14px}
.t-c{grid-area:c;font-weight:600;text-align:right}
.t311 .chg{grid-area:d;font-size:12px;min-width:52px;justify-content:flex-end}
.t-p{grid-area:p;font-size:11.5px;color:var(--muted);text-align:right}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:10px;padding-top:10px;border-top:1px solid var(--line-2)}
.legend span{display:inline-flex;align-items:center;gap:5px}

/* then readings */
.then{display:grid;gap:12px}
.thencard{border-radius:12px;padding:14px;background:var(--surface-2);border:1px solid var(--line-2);color:inherit;text-decoration:none;display:block}
.th-k{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font:600 11px/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.th-yr{font:600 11px/1 var(--mono);color:var(--surface);background:var(--ink-2);padding:4px 7px;border-radius:999px;letter-spacing:.02em}
.ocr{font:600 10px/1 var(--mono);border:1px dashed var(--muted);padding:3px 6px;border-radius:4px;letter-spacing:.06em}
.th-big{font-size:21px;line-height:1.2;font-weight:600;letter-spacing:-.01em;margin:10px 0 6px}
.thencard p{margin:0;font-size:14px;color:var(--ink-2)}
.thencard blockquote{margin:10px 0 8px;font-size:18px;line-height:1.45;font-style:italic;color:var(--ink)}
.th-src{font-size:12px;color:var(--muted);margin-top:8px;line-height:1.4}
.th-go{font-size:13px;font-weight:600;color:var(--accent);margin-top:8px;display:inline-block}

/* reps */
.anc+.anc{margin-top:12px}
.anc-h{display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;color:var(--muted);margin-bottom:4px}
.anc-h a{text-decoration:none}
.anc ul{list-style:none;margin:0;padding:0}
.anc li{display:flex;gap:12px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line-2);font-size:14.5px}
.smd{font-size:12.5px;color:var(--muted);min-width:42px}
.repnote{font-size:12px;color:var(--muted);margin:10px 0 0}

/* subscribe + sponsor */
.subrow{display:flex;gap:8px;margin-top:10px;min-width:0}
.subrow input{flex:1;min-width:0;border:1px solid var(--line);background:var(--surface-2);border-radius:999px;padding:11px 16px;font:inherit;color:var(--ink)}
.subrow button{border:0;background:var(--ink);color:var(--bg);font:600 14px var(--sans);border-radius:999px;padding:0 18px}
.subnote{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin-top:9px}
.sponsor{display:flex;flex-direction:column;justify-content:center;gap:6px;border:1px dashed var(--muted);background:transparent}
.sponsor small{font:600 10.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.sponsor div{font-size:16px}

footer{border-top:1px solid var(--line);padding:20px 0 32px;font-size:12.5px;color:var(--muted)}
footer p{margin:0 0 8px;max-width:820px}
footer strong{color:var(--ink-2)}

/* ---------- tablet & desktop ---------- */
@media (min-width:720px){
  .wrap{padding:0 28px}
  .brand h1{font-size:38px}
  .cond{grid-template-columns:1.35fr 1fr;align-items:center;padding:28px}
  .c-head{font-size:30px}
  .stats{grid-template-columns:repeat(3,1fr)}
  .stats.s3>div:last-child{grid-column:auto}
  .stats.s2{grid-template-columns:1fr 1fr}
  .glist{grid-template-columns:1fr 1fr}
  .then{grid-template-columns:1fr 1fr}
}
@media (min-width:1024px){
  header{padding-top:26px}
  .hd{align-items:center}
  .topbar{display:grid;grid-template-columns:1fr 460px;gap:28px;align-items:end}
  .search{margin-top:0}
  .row{grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:18px;margin-top:18px;align-items:stretch}
  .row.even{grid-template-columns:1fr 1fr}
  .row.one{grid-template-columns:1fr}
  .subband{display:grid;grid-template-columns:1fr 1.2fr;column-gap:28px;align-items:center}
  .subband .ph{grid-column:1/-1}
  .subband .subrow{margin:0}
  .subband .subnote{grid-column:2}
  .sponsor{flex:0 0 auto !important;padding:18px 16px}
  .stack{display:flex;flex-direction:column;gap:18px}
  .stack>:last-child{flex:1}
  .p-m{display:grid;grid-template-columns:auto 1fr;column-gap:12px;align-items:baseline}
  .pwork{grid-column:1/-1}
  .c-head{font-size:34px}
  /* vitals become a 2-column instrument grid of cards */
  .vitals{background:transparent;border:0;padding:0}
  .vitals>.ph{padding:0 2px}
  .vlist{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .vital{grid-template-columns:1fr auto;grid-template-areas:"name name" "g side" "read read";row-gap:10px;column-gap:14px;
    background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px;align-items:end;transition:border-color .15s}
  .vital:first-child{border-top:1px solid var(--line)}
  .vital:hover{border-color:var(--muted)}
  .v-name{justify-content:space-between;flex-wrap:nowrap}
  .v-name .tag{display:inline-flex}
  .v-gauge{max-width:150px;width:100%}
  .v-gauge .d-lbl{display:block}
  .v-num{font-size:24px}
  .v-prev{display:block}
  .v-read{border-top:1px solid var(--line-2);padding-top:10px;margin:0}
  .t311 li{grid-template-areas:"n c d p";grid-template-columns:1fr auto auto 64px}
  .t-p{text-align:right}
  .then{grid-template-columns:1fr 1fr}
}
@media (min-width:1280px){
  .vital{grid-template-columns:150px 1fr}
}
"""

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth: vital signs, from DC's own data</title>
<meta name="description" content="What's changing in Petworth, Washington DC, from DC's own open data. Independent; updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="layout-tag">Layout C3: Vital Signs</div>

<header><div class="wrap">
  <div class="topbar">
    <div class="hd">
      <div class="brand"><h1>{e(FACTS['neighborhood'])}</h1><p>What's changing in Petworth, from DC's own data</p></div>
      <div class="asof"><span class="dot" aria-hidden="true"></span>Data as of <b><time datetime="{FACTS['generated_at']}">{asof}</time></b><br>Updated nightly</div>
    </div>
    <div class="search">
      <label class="sbox" for="q">{ICON_SEARCH}<input id="q" type="search" placeholder="Look up your block or building" autocomplete="off"><button type="button">Look up</button></label>
      <div class="shint">Opens<a href="{link('Block report card')}">Block report card</a><a href="{link('Building biography')}">Building biography</a></div>
    </div>
  </div>
  <nav class="snav" aria-label="Sections"><ul>
    <li><a href="#condition">Condition</a></li><li><a href="#vitals">Vitals</a></li><li><a href="#projects">Projects</a></li><li><a href="#homes">Homes</a></li>
    <li><a href="#streets">Streets</a></li><li><a href="#then">Then</a></li><li><a href="#reps">Representatives</a></li><li><a href="#subscribe">Weekly email</a></li>
  </ul></nav>
</div></header>

<main class="wrap">

<section id="condition" class="cond" aria-labelledby="c-h">
  <div>
    <div class="c-kick">Today's condition · {asof_day} {state_tag(rod_r['state'])}</div>
    <h2 class="c-head" id="c-h">{e(FACTS['lead_sentence'])}</h2>
    <p class="c-word">{e(cond_word)}. Each reading compares the last 30 days with the 30 days before.</p>
    <ul class="c-strip" aria-label="Readings by state">{cond_strip}</ul>
  </div>
  <a class="c-gauge" href="{link('311 report card')}" style="color:inherit;text-decoration:none">
    <div class="ph" style="margin-bottom:6px"><h2>Rodent complaints</h2><span class="sub" style="color:var(--accent);font-weight:600">311 report card →</span></div>
    <div class="s-{rod_r['state']}">{lead_dial}</div>
    <div class="c-gl"><div>30 days before<b class="num">{rod['previous']}</b></div><div class="r">Last 30 days<b class="num">{rod['count']}</b></div></div>
    <p class="c-how">How to read a dial: the <span class="pk"></span> mark at the top is the earlier period. The marker moves right when the latest reading is higher and left when it is lower; the pale band is "steady" (within 5%).</p>
  </a>
</section>

<div class="row">
  <section id="vitals" class="panel vitals" aria-labelledby="v-h">
    <div class="ph" style="padding:12px 16px 0"><h2 id="v-h">Vitals</h2><span class="sub">Last 30 days vs the 30 before</span></div>
    <div class="vlist">{vitals_html}</div>
  </section>

  <section id="projects-map" class="panel" aria-labelledby="m-h">
    <div class="ph"><h2 id="m-h">Permit map</h2><a href="{link('Block Watch')}">Block Watch →</a></div>
    <div class="mapwrap">{map_svg()}</div>
    <div class="mkey">
      <span><svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="5" fill="var(--c-add)"/></svg>Addition</span>
      <span><svg viewBox="0 0 12 12" aria-hidden="true"><rect x="2.5" y="2.5" width="7" height="7" transform="rotate(45 6 6)" fill="var(--c-demo)"/></svg>Demolition</span>
      <span><svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="2.6" fill="var(--ink-2)" opacity=".5"/></svg>Other permit</span>
    </div>
    <div class="m-big"><b>{permits_total}</b><span>permits issued in the last 30 days, by type</span></div>
    {permit_bar()}
    <ul class="glist">{group_legend}</ul>
  </section>
</div>

<div class="row">
  <section id="projects" class="panel" aria-labelledby="p-h">
    <div class="ph"><h2 id="p-h">Bigger projects</h2><a href="{link('Block Watch')}">Block Watch →</a></div>
    <ul class="plist">{proj_rows}</ul>
    <div class="pfoot"><span><b class="num" style="color:var(--ink)">{len(projects)}</b> projects · {new_count} new this week{'' if groups.get('New construction') else ' · no new construction'}</span><a href="/petworth/permits.xml">Permits RSS</a></div>
  </section>

  <div class="stack">
    <section id="homes" class="panel" aria-labelledby="h-h">
      <div class="ph"><h2 id="h-h">Homes</h2><a href="{link('Housing pulse')}">Housing pulse →</a></div>
      <div class="hero"><b>{homes['median_house_price_12mo']}</b><span>median house price, last 12 months, from {homes['house_sales_12mo']} house sales</span></div>
      <div class="stats">
        <div><div class="v">{homes['median_price_60d']}</div><div class="k">median price, last 60 days ({homes['market_sales_60d']} sales)</div></div>
        <div><div class="v">{homes['median_price_per_sqft_60d']}</div><div class="k">median per sq ft, last 60 days</div></div>
        <div><div class="v">{homes['median_condo_price_12mo']}</div><div class="k">median condo, 12 months ({homes['condo_sales_12mo']} sales)</div></div>
        <div class="wide"><div class="v">{homes['sold_above_assessment_12mo']}</div><div class="k">sales above the tax assessment, last 12 months</div></div>
      </div>
      <a class="cta" href="{link('Assessment check')}">Is your assessment in line with sales? <span>Assessment check →</span></a>
    </section>
    <section class="panel" aria-labelledby="tr-h">
      <div class="ph"><h2 id="tr-h">Street trees</h2><a href="{link('Street trees')}">Tree atlas →</a></div>
      <div class="hero"><b>{fmt(trees['street_trees'])}</b><span>street trees, {trees['species']} species</span></div>
      <div class="stats s2">
        <div><div class="v">{trees['planted_last_5y']}</div><div class="k">planted in the last 5 years</div></div>
        <div><div class="v" style="color:var(--accent)">{trees['empty_boxes_open']}</div><div class="k">empty tree boxes open for planting</div></div>
      </div>
      <a class="cta" href="{link('Street trees')}">Find an empty tree box near you <span>Street trees →</span></a>
    </section>

  </div>
</div>

<div class="row even" id="streets">
  <section class="panel" aria-labelledby="t-h">
    <div class="ph"><h2 id="t-h">Top 311 requests</h2><a href="{link('311 report card')}">All types →</a></div>
    <ul class="t311">{t311}</ul>
    <div class="legend"><span>{icon('rising')}Rising</span><span>{icon('easing')}Easing</span><span>{icon('steady')}Steady (within 5%)</span><span>vs prior 30 days</span></div>
  </section>
  <div class="stack">
    <section class="panel" aria-labelledby="curb-h">
      <div class="ph"><h2 id="curb-h">Curb space</h2><a href="{link('Curb radar')}">Curb radar →</a></div>
      <div class="stats s3">
        <div><div class="v">{streets['curb_permits_active_this_week']}</div><div class="k">curb permits active this week</div></div>
        <div><div class="v">{streets['curb_permits_starting_next_7d']}</div><div class="k">starting in the next 7 days</div></div>
        <div><div class="v">{fmt(streets['curb_reserved_ft'])} ft</div><div class="k">of curb reserved, about {curb_mi:.1f} miles</div></div>
      </div>
    </section>
    <aside class="panel sponsor" aria-label="Sponsor">
      <small>Sponsor</small>
      <div>Presented by <b>[Local sponsor]</b></div>
    </aside>
  </div>
</div>

<div class="row">
  <section id="then" class="panel" aria-labelledby="th-h">
    <div class="ph"><h2 id="th-h">Then</h2><a href="{link('100 years ago')}">100 years ago →</a></div>
    <div class="then">
      <a class="thencard" href="{link('Building biography')}">
        <div class="th-k"><span class="th-yr">1926</span>{e(hist['block'])}</div>
        <div class="th-big">62 rowhouses, one builder</div>
        <p>{e(hist['fact'])}</p>
        <span class="th-go">Building biography →</span>
      </a>
      <div class="thencard">
        <div class="th-k"><span class="th-yr">1926</span>A reading from 100 years ago <span class="ocr">OCR</span></div>
        <blockquote>“{e(hist['hundred_years_ago_excerpt_ocr'])}”</blockquote>
        <div class="th-src">{e(hist['hundred_years_ago_source'])}. Machine-read text; may contain errors.</div>
      </div>
    </div>
  </section>

  <section id="reps" class="panel" aria-labelledby="r-h">
    <div class="ph"><h2 id="r-h">Who represents you</h2><span class="sub">{len(reps)} SMDs</span></div>
    {rep_html}
    <p class="repnote">Each Single Member District elects one ANC commissioner. Names of elected officials are public record.</p>
  </section>
</div>

<div class="row one" id="subscribe">
  <section class="panel subband" aria-labelledby="s-h">
    <div class="ph"><h2 id="s-h">Weekly email</h2><a href="{link('Weekly email')}">See a sample →</a></div>
    <div style="font-size:15px">These readings in your inbox once a week.</div>
    <form class="subrow" onsubmit="return false"><input type="email" placeholder="you@example.com" aria-label="Email address"><button type="button">Subscribe</button></form>
    <div class="subnote"><span>One email a week. Mock signup.</span><a href="/petworth/permits.xml">Permits RSS feed</a></div>
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
