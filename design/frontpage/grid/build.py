"""Build index.html for the `grid` front-page design from petworth.json.

Usage: python build.py   (writes index.html next to this file)
"""
import json
import math
import re
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / "site" / "src" / "data" / "petworth.json"
d = json.loads(DATA.read_text(encoding="utf-8"))

ET = ZoneInfo("America/New_York")
gen = datetime.fromisoformat(d["generated_at"].replace("Z", "+00:00")).astimezone(ET)
today = date.fromisoformat(d["events"]["today"])
NAME = d["name"]


def e(s):
    return escape(str(s), quote=True)


def n(x):
    return f"{x:,}"


def signed(x):
    return ("+" if x > 0 else "−" if x < 0 else "±") + f"{abs(x):,}"


def pct(a, b):
    """Percent change, only when both counts are 100 or more (privacy/honesty rule)."""
    if a >= 100 and b >= 100 and b:
        p = round((a - b) / b * 100)
        return ("+" if p > 0 else "−" if p < 0 else "±") + f"{abs(p)}%"
    return None


def money_k(x):
    return f"${x / 1000:,.0f}K" if x < 1_000_000 else f"${x / 1_000_000:,.2f}M"


def mdy(dt):
    return f"{dt:%b} {dt.day}"


def iso_date(s):
    return date.fromisoformat(s[:10])


def addr(s):
    s = re.sub(r"\s+\d{5}$", "", s.strip())
    out = []
    for w in s.split():
        if w in ("NW", "NE", "SW", "SE"):
            out.append(w)
        elif re.match(r"^\d+(ST|ND|RD|TH)$", w):
            out.append(w.lower())
        else:
            out.append(w.capitalize())
    return " ".join(out)


def clip(s, k):
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= k:
        return s
    cut = s[:k].rsplit(" ", 1)[0].rstrip(",.;:")
    return cut + "…"


TYPE_LABEL = {
    "DC Health Rodent & Vector Control": "Rodent & vector control",
    "DOEE - LIHEAP": "Energy assistance (LIHEAP)",
    "Trash Collection - Missed": "Missed trash collection",
    "Recycling Collection - Missed": "Missed recycling collection",
    "Public Space Litter Can-Collection": "Public litter can collection",
}


def tlabel(t):
    return TYPE_LABEL.get(t, t[:1] + t[1:].lower() if t.isupper() else t)


# ---------------------------------------------------------------- 311 condition
req = d["requests"]
types = req["by_type"]
VOL = 20  # a "reading" is a request type with at least this many requests in either period


def direction(c, p):
    diff = c - p
    if abs(diff) <= max(2, 0.05 * p):
        return "steady"
    return "rising" if diff > 0 else "easing"


readings = [t for t in types if max(t["count"], t["previous"]) >= VOL]
tally = {"rising": 0, "easing": 0, "steady": 0}
for t in readings:
    tally[direction(t["count"], t["previous"])] += 1

# Lead: biggest rise among types with a real baseline (50+ the period before),
# otherwise the biggest absolute change.
based = [t for t in types if t["previous"] >= 50]
lead_t = max(based, key=lambda t: t["count"] - t["previous"]) if based else max(types, key=lambda t: abs(t["count"] - t["previous"]))
lt_name = tlabel(lead_t["type"])
lt_dir = "rose" if lead_t["count"] > lead_t["previous"] else "fell"
tot_dir = "fell" if req["total"] < req["previous_total"] else "rose"
tot_join = "even as" if (lt_dir != tot_dir) else "and"
lead_sentence = (
    f"{lt_name} requests {lt_dir} to <span class=\"num\">{n(lead_t['count'])}</span> in the last "
    f"{d['windows']['requests_days']} days, from <span class=\"num\">{n(lead_t['previous'])}</span>, "
    f"{tot_join} all 311 requests in {NAME} {tot_dir} from <span class=\"num\">{n(req['previous_total'])}</span> "
    f"to <span class=\"num\">{n(req['total'])}</span>."
)

# ---------------------------------------------------------------- permits + map
ring = d["boundary"]["rings"][0]  # [lon, lat]


def inside(lon, lat, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


permits = [p for p in d["permits"] if p.get("lat") and p.get("lon") and inside(p["lon"], p["lat"], ring)]
BIG = ("Demolition", "New construction", "Additions")
big = sorted([p for p in permits if p["group"] in BIG], key=lambda p: p["issued"], reverse=True)
big_ids = {p["id"]: i + 1 for i, p in enumerate(big)}
groups = {}
for p in d["permits"]:
    groups[p["group"]] = groups.get(p["group"], 0) + 1
group_order = sorted(groups.items(), key=lambda kv: (-kv[1], kv[0]))
GROUP_LABEL = {"Electrical, plumbing & mechanical": "Electrical, plumbing, mechanical"}

lons = [x for x, _ in ring]
lats = [y for _, y in ring]
lat0 = (min(lats) + max(lats)) / 2
kx = math.cos(math.radians(lat0))
W = 600
span_x = (max(lons) - min(lons)) * kx
span_y = max(lats) - min(lats)
s = (W - 40) / span_x
H = round(span_y * s + 40)


def proj(lon, lat):
    return (20 + (lon - min(lons)) * kx * s, 20 + (max(lats) - lat) * s)


path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (proj(*pt) for pt in ring)) + " Z"
# graticule every 0.005 degrees
grat = []
g = math.ceil(min(lons) / 0.005) * 0.005
while g < max(lons):
    x, _ = proj(g, lat0)
    grat.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{H}"/>')
    if x < W - 70:
        grat.append(f'<text x="{x + 3:.1f}" y="{H - 4}">{abs(g):.3f}°W</text>')
    g += 0.005
g = math.ceil(min(lats) / 0.005) * 0.005
while g < max(lats):
    _, y = proj(min(lons), g)
    grat.append(f'<line x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}"/>')
    grat.append(f'<text x="4" y="{y - 4:.1f}">{g:.3f}°N</text>')
    g += 0.005
dots = []
for p in permits:
    if p["id"] in big_ids:
        continue
    x, y = proj(p["lon"], p["lat"])
    dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2"/>')
marks = []
for p in reversed(big):
    x, y = proj(p["lon"], p["lat"])
    k = big_ids[p["id"]]
    marks.append(
        f'<g class="mk"><circle cx="{x:.1f}" cy="{y:.1f}" r="10"/>'
        f'<text x="{x:.1f}" y="{y + 4:.1f}">{k}</text><title>{k}. {e(addr(p["address"]))}, {e(p["group"].lower())}</title></g>'
    )
map_svg = f"""<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-labelledby="map-t map-d">
<title id="map-t">Map of building permits in {NAME}, last {d['windows']['permits_days']} days</title>
<desc id="map-d">{len(permits)} permits plotted inside the {NAME} boundary. {len(big)} bigger projects are numbered to match the list beside the map; the other {len(permits) - len(big)} are small gray dots.</desc>
<g class="grat">{''.join(grat)}</g>
<path class="bnd" d="{path}"/>
<g class="dots">{''.join(dots)}</g>
{''.join(marks)}
</svg>"""

# ---------------------------------------------------------------- homes
homes = d["homes"]
house = homes["house"]
hp_diff = house["median_12mo"] - house["median_prev_12mo"]
hp_pct = None
if house["count_12mo"] >= 100 and house["count_prev_12mo"] >= 100:
    p_ = round(hp_diff / house["median_prev_12mo"] * 100)
    hp_pct = ("+" if p_ > 0 else "−" if p_ < 0 else "±") + f"{abs(p_)}%"
hp_state = "steady" if abs(hp_diff) <= 0.05 * house["median_prev_12mo"] else ("rising" if hp_diff > 0 else "easing")
months = [m for m in homes["by_month"] if m["median"]]


def month_bars(ms, w=240, h=56, label=True):
    if not ms:
        return ""
    lo = min(m["median"] for m in ms)
    hi = max(m["median"] for m in ms)
    floor = lo * 0.8
    bw = w / len(ms)
    out = []
    for i, m in enumerate(ms):
        bh = (m["median"] - floor) / (hi - floor) * (h - 4) + 2
        mo = datetime.strptime(m["month"], "%Y-%m")
        out.append(
            f'<rect x="{i * bw + 1:.1f}" y="{h - bh:.1f}" width="{bw - 3:.1f}" height="{bh:.1f}">'
            f'<title>{mo:%b %Y}: median {money_k(m["median"])} from {m["count"]} sales</title></rect>'
        )
    first = datetime.strptime(ms[0]["month"], "%Y-%m")
    last = datetime.strptime(ms[-1]["month"], "%Y-%m")
    lab = ""
    if label:
        lab = (
            f'<text x="0" y="{h + 13}">{first:%b %Y}</text>'
            f'<text x="{w}" y="{h + 13}" text-anchor="end">{last:%b %Y}</text>'
        )
    return (
        f'<svg class="spark" viewBox="0 -2 {w} {h + 18}" role="img" aria-label="Monthly median house price, '
        f'{first:%b %Y} to {last:%b %Y}, ranging from {money_k(lo)} to {money_k(hi)}">{"".join(out)}{lab}</svg>'
    )


# ---------------------------------------------------------------- small helpers for bars
def pair_bar(a, b, label_a, label_b):
    m = max(a, b) or 1
    return (
        f'<div class="pair" role="img" aria-label="{e(label_a)} {n(a)}, {e(label_b)} {n(b)}">'
        f'<span class="pb now" style="width:{a / m * 100:.1f}%"></span>'
        f'<span class="pb prev" style="width:{b / m * 100:.1f}%"></span></div>'
    )


# ---------------------------------------------------------------- sections
news = d["news"]["items"]
news_rows = []
for it in news[:6]:
    pd_ = datetime.fromisoformat(it["published"].replace("Z", "+00:00")).astimezone(ET).date()
    age = (gen.date() - pd_).days
    when = "Today" if age == 0 else "Yesterday" if age == 1 else mdy(pd_)
    news_rows.append(
        f'<li><time datetime="{pd_.isoformat()}">{when}</time>'
        f'<div><a href="{e(it["url"])}" rel="noopener">{e(it["title"])}</a>'
        f'<span class="src">{e(it["source"])}</span></div></li>'
    )
newest_age = (gen.date() - datetime.fromisoformat(news[0]["published"].replace("Z", "+00:00")).astimezone(ET).date()).days if news else None

ev = d["events"]
horizon = today + timedelta(days=14)
upcoming = [x for x in ev["events"] if today <= iso_date(x["date"]) <= horizon]
by_day = {}
for x in upcoming:
    by_day.setdefault(x["date"], []).append(x)
ev_rows = []
for ds, xs in sorted(by_day.items()):
    dd = iso_date(ds)
    rel = "Today" if dd == today else "Tomorrow" if dd == today + timedelta(days=1) else f"{dd:%a}"
    items = "".join(
        f'<div class="ev"><a href="{e(x["url"])}" rel="noopener">{e(x["title"])}</a>'
        f'<span class="meta"><span class="num">{e(x["time"].replace(" - ", "–"))}</span> · {e(x["place"])}</span></div>'
        for x in xs
    )
    ev_rows.append(
        f'<li class="{"is-today" if dd == today else ""}"><div class="day"><span class="dnum">{dd.day}</span>'
        f'<span class="dlab">{rel}<br>{dd:%b}</span></div><div>{items}</div></li>'
    )
later = len(ev["events"]) - len(upcoming)
ev_links = " · ".join(f'<a href="{e(l["url"])}" rel="noopener">{e(l["name"])}</a>' for l in ev["links"])

# 311 table
top = sorted(types, key=lambda t: -t["count"])[:8]
tmax = max(max(t["count"], t["previous"]) for t in top)
rows_311 = []
for t in top:
    c, p = t["count"], t["previous"]
    dr = direction(c, p)
    arrow = {"rising": "↑", "easing": "↓", "steady": "→"}[dr]
    pc = pct(c, p)
    rows_311.append(
        f'<tr><th scope="row">{e(tlabel(t["type"]))}</th>'
        f'<td class="bar" aria-hidden="true"><span class="in"><span class="b" style="width:{c / tmax * 100:.1f}%"></span>'
        f'<span class="tick" style="left:{p / tmax * 100:.1f}%"></span></span></td>'
        f'<td class="num">{n(c)}</td><td class="num muted hide-s">{n(p)}</td>'
        f'<td class="num chg"><span class="arr" aria-label="{dr}">{arrow}</span> {signed(c - p)}'
        f'{f"<span class=pc> {pc}</span>" if pc else ""}</td></tr>'
    )

# measures
crime = d["crime"]
c_diff = crime["total"] - crime["previous_total"]
req_diff = req["total"] - req["previous_total"]
req_pc = pct(req["total"], req["previous_total"])
nbig = len([p for p in d["permits"] if p["group"] in BIG])
nper = len(d["permits"])
gcount = {k: v for k, v in groups.items()}

big_rows = []
for p in big:
    k = big_ids[p["id"]]
    dt = iso_date(p["issued"])
    work = clip(p["work"], 150) if p["work"] else "No description filed."
    big_rows.append(
        f'<li><span class="k">{k}</span><div><div class="bh"><strong>{e(addr(p["address"]))}</strong>'
        f'<span class="meta">{e(p["group"].rstrip("s") if p["group"] == "Additions" else p["group"])} · '
        f'<time datetime="{dt.isoformat()}">{mdy(dt)}</time></span></div>'
        f'<p>{e(work)}</p><span class="pid">{e(p["id"])}</span></div></li>'
    )

gmax = max(groups.values())
group_rows = "".join(
    f'<tr><th scope="row">{e(GROUP_LABEL.get(g_, g_))}{" <span class=hl>●</span>" if g_ in BIG else ""}</th>'
    f'<td class="bar" aria-hidden="true"><span class="b{" hl" if g_ in BIG else ""}" style="width:{c_ / gmax * 100:.1f}%"></span></td>'
    f'<td class="num">{c_}</td></tr>'
    for g_, c_ in group_order
)

# homes table
sales_rows = []
for s_ in homes["recent_sales"][:6]:
    dt = iso_date(s_["date"])
    vs = s_["price"] - s_["assessed"] if s_.get("assessed") else None
    sales_rows.append(
        f'<tr><td class="num first"><time datetime="{dt.isoformat()}">{mdy(dt)}</time></td>'
        f'<th scope="row">{e(s_["address"])}</th>'
        f'<td class="hide-s muted">{e(s_["kind"])}, {s_["beds"]} bd</td>'
        f'<td class="num">${n(s_["price"])}</td>'
        f'<td class="num muted hide-s">{"" if vs is None else signed(round(vs / 1000)) + "K"}</td></tr>'
    )
l60 = homes["last_60d"]
condo = homes["condo"]
above = homes["above_assessment_12mo"]

# streets: curb + trees
curb = d["streets"]["curb"]
curb_rows = []
for c_ in curb["upcoming"][:6]:
    a, b = iso_date(c_["start"]), iso_date(c_["end"])
    curb_rows.append(
        f'<tr><th scope="row">{e(c_["block"])}<span class="sub">{e(c_["type"])}</span></th>'
        f'<td class="num">{mdy(a)}–{mdy(b) if b.month != a.month else b.day}</td>'
        f'<td class="num">{c_["ft"]} ft</td></tr>'
    )
curb_more = len(curb["upcoming"]) - len(curb_rows)
trees = d["streets"]["trees"]
cond = trees["condition"]
cond_order = [("Excellent", "c1"), ("Good", "c2"), ("Fair", "c3"), ("Poor", "c4")]
rated = sum(cond.get(k, 0) for k, _ in cond_order)
cond_bar = "".join(
    f'<span class="{cls}" style="width:{cond.get(k, 0) / rated * 100:.2f}%" title="{k}: {n(cond.get(k, 0))}"></span>' for k, cls in cond_order
)
cond_leg = "".join(f'<li><i class="{cls}"></i>{k} <span class="num">{n(cond.get(k, 0))}</span></li>' for k, cls in cond_order)
sp_max = trees["top_species"][0]["count"]
species_rows = "".join(
    f'<tr><th scope="row">{e(t["name"])}</th><td class="bar" aria-hidden="true"><span class="b" style="width:{t["count"] / sp_max * 100:.1f}%"></span></td>'
    f'<td class="num">{n(t["count"])}</td></tr>'
    for t in trees["top_species"][:5]
)
bigtree = trees["biggest"][0]

# history
hist = d["history"]
fb = hist["buildings"]["featured_block"]
dec = hist["buildings"]["by_decade"]
dmax = max(x["count"] for x in dec)
dec_rows = "".join(
    f'<li><span class="dl num">{x["decade"]}s</span><span class="db"><span style="width:{x["count"] / dmax * 100:.1f}%"></span></span>'
    f'<span class="num">{n(x["count"])}</span></li>'
    for x in dec
)


def ocr_noise(t):
    """Rough OCR-garbage score: odd symbols, mixed-case words, digits glued to letters, short junk words."""
    bad = len(re.findall(r"[^A-Za-z0-9 ,.:;'\-$]", t))
    bad += 3 * len(re.findall(r"\b[a-z]+[A-Z]\w*|\b[A-Z]{2,}[a-z]+", t))
    bad += 3 * len(re.findall(r"\b\w*(?:[A-Za-z]\d|\d[A-Za-z])\w*", t))
    return bad / max(len(t), 1)


arch = hist["archive"]
clips = sorted(arch["clips"], key=lambda c: ocr_noise(c["text"]))[:3]
clips = sorted(clips, key=lambda c: (c["date"], c["page"]))
clip_rows = "".join(
    f'<li><blockquote>“{e(clip(c["text"], 220))}”</blockquote>'
    f'<a class="meta" href="{e(c["url"])}" rel="noopener">{e(arch["paper"])}, {mdy(iso_date(c["date"]))}, 1926, page {c["page"]}</a></li>'
    for c in clips
)

# representatives: SMD codes only, no names (privacy rule: no person names from data)
ancs = {}
for s_ in d["smds"]:
    ancs.setdefault(s_["anc"], {"url": s_["url"], "smds": []})["smds"].append(s_["smd"])
rep_rows = "".join(
    f'<li><span class="anc">ANC {e(a)}</span><span class="smds num">{" ".join(e(x) for x in v["smds"])}</span>'
    f'<a href="{e(v["url"])}" rel="noopener">{e(v["url"].split("//")[1].strip("/"))}</a></li>'
    for a, v in ancs.items()
)

sources = d["sources"]
asof = f"{gen:%a} {gen:%b} {gen.day}, {gen:%Y}, {gen:%I:%M %p}".replace(" 0", " ") + " ET"

# ---------------------------------------------------------------- page
CSS = r"""
:root{
  --ink:#111111; --ink-2:#5e5e5e; --rule:#111111; --hair:#d6d6d6; --fill:#f2f2f2;
  --accent:#c43a12; --bar:#111111; --bar-2:#bdbdbd; --bg:#ffffff;
  --gut:24px; --pad:32px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.5 "Archivo",system-ui,sans-serif;
  font-feature-settings:"tnum" 1,"lnum" 1}
a{color:inherit;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.18em;text-decoration-color:#9a9a9a}
a:hover{color:var(--accent);text-decoration-color:currentColor}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.num{font-variant-numeric:tabular-nums lining-nums}
.muted{color:var(--ink-2)}
.wrap{max-width:1280px;margin:0 auto;padding:0 var(--pad)}
.g{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:var(--gut)}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:6px 10px;z-index:9}

/* masthead */
.mast{border-top:8px solid var(--ink);padding-top:20px}
.mast .g{align-items:end}
.mast h1{grid-column:1/8;margin:0 0 -6px;font-size:128px;line-height:.86;font-weight:700;letter-spacing:-.045em}
.mast .tag{grid-column:8/13;max-width:30em;margin:0 0 6px;font-size:15px;line-height:1.4}
.mast .tag strong{display:block;font-weight:600}
.nav{margin-top:24px;border-top:1px solid var(--rule);border-bottom:1px solid var(--hair)}
.nav ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;column-gap:24px}
.nav a{display:inline-block;padding:10px 0;font-size:14px;font-weight:500;text-decoration:none}
.nav a:hover{text-decoration:underline}

/* sections */
section{margin-top:72px}
.sh{grid-column:1/-1;display:flex;align-items:baseline;gap:16px;border-top:2px solid var(--rule);padding-top:10px;margin-bottom:24px}
.sh .no{font-size:13px;font-weight:600;width:28px;flex:none}
.sh h2{margin:0;font-size:22px;line-height:1.2;font-weight:700;letter-spacing:-.01em}
.sh .more{margin-left:auto;font-size:14px;white-space:nowrap}
.sh .note{font-size:14px;color:var(--ink-2)}
.cap{font-size:13px;line-height:1.45;color:var(--ink-2);margin:14px 0 0}
h3{font-size:15px;font-weight:700;margin:0 0 12px;line-height:1.3}
.lab{font-size:13px;color:var(--ink-2);display:block}

/* news + events */
.news{grid-column:1/8}
.events{grid-column:9/13}
.newslist{list-style:none;margin:0;padding:0}
.newslist li{display:grid;grid-template-columns:92px 1fr;column-gap:var(--gut);padding:12px 0;border-bottom:1px solid var(--hair)}
.newslist li:first-child{padding-top:0}
.newslist time{font-size:14px;color:var(--ink-2);padding-top:3px}
.newslist a{font-size:19px;line-height:1.3;font-weight:500;text-decoration-color:#c4c4c4}
.newslist li:first-child a{font-size:24px;line-height:1.2;font-weight:600;letter-spacing:-.01em}
.src{display:block;font-size:13px;color:var(--ink-2);margin-top:4px}
.evlist{list-style:none;margin:0;padding:0}
.evlist li{display:grid;grid-template-columns:112px 1fr;column-gap:16px;padding:12px 0;border-bottom:1px solid var(--hair)}
.evlist li:first-child{padding-top:0}
.day{display:flex;gap:8px;align-items:flex-start}
.dnum{font-size:34px;line-height:.9;font-weight:600;letter-spacing:-.02em;min-width:1.25em}
.dlab{font-size:12px;line-height:1.3;color:var(--ink-2);padding-top:1px}
.is-today .dnum,.is-today .dlab{color:var(--accent)}
.ev+.ev{margin-top:8px}
.ev a{font-weight:600}
.meta{display:block;font-size:13px;color:var(--ink-2);line-height:1.4;margin-top:2px}
.also{font-size:14px;margin:16px 0 0;line-height:1.6}
.also b{font-weight:600;display:block;font-size:13px;color:var(--ink-2)}

/* condition */
.cond .lead{grid-column:1/10;margin:0;font-size:34px;line-height:1.22;font-weight:400;letter-spacing:-.015em}
.cond .lead .num{font-weight:600}
.tally{grid-column:10/13;align-self:end;margin:0;padding:0;list-style:none;border-left:1px solid var(--rule);padding-left:20px}
.tally .tl{font-size:13px;color:var(--ink-2);display:block;margin-bottom:4px}
.tally li{display:flex;align-items:baseline;gap:10px;font-size:15px}
thead th.first{padding-right:16px}
.tally .tn{font-size:30px;font-weight:600;min-width:1.4em;text-align:right;line-height:1.15}
.cond .cap{grid-column:1/10}

/* measures */
.measures .m{grid-column:span 3;border-left:1px solid var(--hair);padding-left:16px;min-width:0}
.measures .sh+.m{border-left:0;padding-left:0}
.m .big{font-size:52px;line-height:1;font-weight:600;letter-spacing:-.03em;margin:10px 0 6px;white-space:nowrap}
.m .big small{font-size:16px;font-weight:500;letter-spacing:0;margin-left:4px;color:var(--ink-2)}
.m .cmp{font-size:14px;margin:0 0 14px;line-height:1.45}
.m .cmp strong{font-weight:600}
.m .cap{margin-top:12px}
.state{display:inline-block;font-size:12px;font-weight:600;border:1px solid var(--ink);padding:0 6px;line-height:19px;margin-left:6px;vertical-align:1px}
.pair{display:grid;row-gap:4px}
.pb{display:block;height:8px;background:var(--bar)}
.pb.prev{background:var(--bar-2)}
.key{font-size:12px;color:var(--ink-2);margin-top:6px;display:flex;gap:14px;flex-wrap:wrap}
.key i{display:inline-block;width:10px;height:8px;margin-right:5px;background:var(--bar)}
.key i.p{background:var(--bar-2)}
.split{display:flex;height:8px;margin-top:2px}
.split span{display:block;height:8px}
.split .a{background:var(--accent)} .split .b2{background:var(--bar-2)}
.spark{display:block;width:100%;height:auto;max-width:280px}
.spark rect{fill:var(--bar)}
.spark text{font-size:11px;fill:var(--ink-2);font-family:inherit}

/* permits */
.mapcol{grid-column:1/8;min-width:0}
.bigcol{grid-column:8/13;min-width:0}
.map{display:block;width:100%;height:auto}
.map .grat line{stroke:#e6e6e6;stroke-width:1}
.map .grat text{font-size:10px;fill:#8a8a8a;font-family:inherit}
.map .bnd{fill:none;stroke:var(--ink);stroke-width:1.5}
.map .dots circle{fill:#8c8c8c}
.map .mk circle{fill:var(--accent);stroke:#fff;stroke-width:1.5}
.map .mk text{fill:#fff;font-size:11px;font-weight:700;text-anchor:middle;font-family:inherit}
.maplegend{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;color:var(--ink-2);margin-top:10px}
.maplegend i{display:inline-block;border-radius:50%;margin-right:6px;vertical-align:-1px}
.maplegend .d{width:7px;height:7px;background:#8c8c8c;vertical-align:1px}
.maplegend .k{width:14px;height:14px;background:var(--accent)}
.biglist{list-style:none;margin:0;padding:0}
.biglist li{display:grid;grid-template-columns:28px 1fr;column-gap:12px;padding:12px 0;border-bottom:1px solid var(--hair)}
.biglist li:first-child{padding-top:0}
.biglist .k{width:22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:1px}
.bh strong{font-weight:600}
.bh .meta{display:inline;margin-left:8px}
.biglist p{margin:4px 0 2px;font-size:14px;line-height:1.45}
.pid{font-size:12px;color:var(--ink-2)}
.bytype{grid-column:1/8;margin-top:40px}
.bytype-note{grid-column:9/13;margin-top:40px}

/* tables */
table{border-collapse:collapse;width:100%}
th,td{text-align:left;font-weight:400;padding:7px 0;border-bottom:1px solid var(--hair);vertical-align:baseline;font-size:15px}
thead th{font-size:12px;color:var(--ink-2);border-bottom:1px solid var(--rule);padding-top:0}
td.num,th.num{text-align:right;padding-left:14px;white-space:nowrap}
td.first{text-align:left;padding-left:0;padding-right:16px}
th+th,td+th{padding-left:0}
td.gap,th.gap{padding-left:16px}
td.bar{width:34%;padding-left:16px;vertical-align:middle}
td.bar .in{position:relative;display:block;height:16px}
td.bar .in .b{position:absolute;left:0;top:4px}
td.bar .b{display:block;height:8px;background:var(--bar)}
td.bar .b.hl{background:var(--accent)}
td.bar .tick{position:absolute;top:50%;width:2px;height:16px;margin-top:-8px;background:var(--bar-2)}
.chg .arr{display:inline-block;width:1em;text-align:center}
.pc{color:var(--ink-2)}
.hl{color:var(--accent);font-size:.8em}
.sub{display:block;font-size:12px;color:var(--ink-2)}

/* lower grid */
.half{grid-column:span 6;min-width:0}
.facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));column-gap:var(--gut);margin:0 0 24px;padding:0}
.facts div{border-top:1px solid var(--hair);padding-top:8px}
.facts dt{font-size:13px;color:var(--ink-2);line-height:1.35}
.facts dd{margin:4px 0 0;font-size:26px;font-weight:600;letter-spacing:-.02em;line-height:1.1}
.facts dd small{font-size:13px;font-weight:400;color:var(--ink-2);letter-spacing:0;display:block;margin-top:2px}
.hero{display:flex;align-items:flex-end;gap:var(--gut);margin-bottom:24px;flex-wrap:wrap}
.hero .big{font-size:52px;line-height:1;font-weight:600;letter-spacing:-.03em}
.hero p{margin:0;font-size:14px;line-height:1.45;max-width:24em}
.condbar{display:flex;height:12px;margin:6px 0 8px}
.condbar span{display:block;height:12px}
.c1{background:#111}.c2{background:#555}.c3{background:#a8a8a8}.c4{background:#dcdcdc}
.condleg{list-style:none;margin:0 0 24px;padding:0;display:flex;flex-wrap:wrap;gap:4px 16px;font-size:13px;color:var(--ink-2)}
.condleg i{display:inline-block;width:10px;height:10px;margin-right:6px;vertical-align:-1px}
.condleg .num{color:var(--ink)}
.subhead{display:flex;justify-content:space-between;align-items:baseline;gap:4px 12px;margin:0 0 10px;flex-wrap:wrap}
.subhead h3{margin:0}
.subhead a{font-size:14px;white-space:nowrap}

/* then */
.then .yr{grid-column:1/4;font-size:120px;line-height:.85;font-weight:700;letter-spacing:-.05em;margin:0}
.then .fb{grid-column:4/9;min-width:0}
.then .fb p.s{font-size:20px;line-height:1.35;margin:0 0 20px}
.then .decades{grid-column:9/13;min-width:0}
.declist{list-style:none;margin:0;padding:0}
.declist li{display:grid;grid-template-columns:56px 1fr 52px;align-items:center;column-gap:10px;font-size:14px;padding:3px 0}
.declist .db{display:block;height:8px}
.declist .db span{display:block;height:8px;background:var(--bar)}
.declist .num:last-child{text-align:right}
.clips{grid-column:1/-1;list-style:none;margin:40px 0 0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));column-gap:var(--gut)}
.clips li{border-top:1px solid var(--rule);padding-top:12px}
.clips blockquote{margin:0 0 10px;font-size:16px;line-height:1.5}
.clips .meta{display:inline}

/* reps + email */
.replist{list-style:none;margin:0;padding:0}
.replist li{display:grid;grid-template-columns:80px 1fr auto;column-gap:16px;padding:10px 0;border-bottom:1px solid var(--hair);align-items:baseline}
.replist .anc{font-weight:700}
.replist .smds{word-spacing:.5em}
form.mail{display:flex;gap:0;margin-top:4px;max-width:480px}
form.mail input{flex:1;min-width:0;font:inherit;font-size:16px;padding:11px 12px;border:1px solid var(--ink);border-right:0;border-radius:0;background:#fff;color:var(--ink)}
form.mail button{font:inherit;font-size:15px;font-weight:600;padding:0 20px;border:1px solid var(--ink);background:var(--ink);color:#fff;border-radius:0;cursor:pointer}
form.mail button:hover{background:var(--accent);border-color:var(--accent)}
form.mail input:focus-visible,form.mail button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

/* footer */
footer{margin-top:96px;border-top:8px solid var(--ink);padding:20px 0 48px;font-size:13px;line-height:1.55;color:var(--ink-2)}
footer .g>div{grid-column:span 4}
footer strong{color:var(--ink);font-weight:600}
footer p{margin:0 0 10px}

/* ---------- tablet */
@media (max-width:1040px){
  .mast h1{font-size:96px}
  .news{grid-column:1/-1}.events{grid-column:1/-1;margin-top:48px}
  .measures .m{grid-column:span 6;margin-bottom:32px}
  .measures .m:nth-child(4){border-left:0;padding-left:0}
  .mapcol,.bigcol,.bytype,.bytype-note{grid-column:1/-1}
  .bigcol{margin-top:32px}
  .half{grid-column:1/-1}
  .half+.half{margin-top:56px}
  .then .yr{grid-column:1/-1;font-size:96px;margin-bottom:16px}
  .then .fb{grid-column:1/8}.then .decades{grid-column:8/13}
  .cond .lead,.cond .cap{grid-column:1/-1}
  .tally{grid-column:1/-1;margin-top:24px;border-left:0;padding-left:0;display:flex;gap:28px;border-top:1px solid var(--hair);padding-top:12px}
}
/* ---------- phone */
@media (max-width:640px){
  :root{--pad:16px;--gut:16px}
  body{font-size:16px}
  .mast{padding-top:14px}
  .mast h1{grid-column:1/-1;font-size:64px;margin:0}
  .mast .tag{grid-column:1/-1;margin-top:12px;font-size:14px}
  .nav{margin-top:16px}
  .nav ul{flex-wrap:nowrap;overflow-x:auto;column-gap:18px;scrollbar-width:none}
  .nav ul::-webkit-scrollbar{display:none}
  .nav li{flex:none}
  section{margin-top:52px}
  .sh{flex-wrap:wrap;row-gap:2px;margin-bottom:18px}
  .sh h2{font-size:20px}
  .sh .no{width:22px}
  .sh .note{flex-basis:100%;padding-left:38px}
  .newslist li{grid-template-columns:1fr;row-gap:2px}
  .newslist time{padding-top:0;font-size:13px}
  .newslist a{font-size:17px}
  .newslist li:first-child a{font-size:20px}
  .evlist li{grid-template-columns:104px 1fr}
  .dnum{font-size:28px}
  .cond .lead{font-size:24px;line-height:1.28}
  .tally{gap:18px}
  .tally li{font-size:14px;gap:6px}
  .tally .tn{font-size:24px;min-width:0}
  .measures .m{grid-column:span 6;border-left:0;padding-left:0;border-top:1px solid var(--rule);padding-top:10px;margin-bottom:28px}
  .m .big{font-size:36px;margin:8px 0 4px}
  .m h3{font-size:14px;margin:0}
  .m .cmp{font-size:13px;margin-bottom:10px}
  .m .state{margin:4px 0 0}
  .m .key{font-size:11px;gap:2px 10px}
  .spark text{font-size:16px}
  .then .yr{font-size:72px}
  .then .fb,.then .decades{grid-column:1/-1}
  .then .decades{margin-top:28px}
  .then .fb p.s{font-size:18px}
  .clips{grid-template-columns:1fr;row-gap:24px;margin-top:32px}
  .facts{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:16px}
  .facts dd{font-size:22px}
  .hide-s{display:none}
  td.bar{width:26%;padding-left:10px}
  th,td{font-size:14px}
  .hero .big{font-size:44px}
  .replist li{grid-template-columns:64px 1fr;row-gap:2px}
  .replist li a{grid-column:2}
  footer .g>div{grid-column:1/-1}
  .map .mk circle{r:17px}
  .map .mk text{font-size:18px}
  .map .dots circle{r:5.5px}
  .map .grat text{font-size:17px}
  .map .bnd{stroke-width:2.5}
  .mast .tag{max-width:none}
  .tally .tl{flex-basis:100%;margin:0}
  .tally{flex-wrap:wrap;row-gap:4px}
}
"""

nav_items = [
    ("#news", "News"), ("#events", "Coming up"), ("#condition", "Condition"), ("#measures", "Measures"),
    ("#permits", "Permits"), ("#homes", "Homes"), ("#streets", "Streets"), ("#then", "Then"),
    ("#reps", "Representatives"), ("#email", "Weekly email"),
]
nav = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in nav_items)

news_note = ""
if newest_age is not None and newest_age > 14:
    news_note = '<span class="note">No new headlines in the past two weeks.</span>'

events_block = (
    f'<ul class="evlist">{"".join(ev_rows)}</ul>'
    if ev_rows
    else '<p>Nothing listed for the next 14 days in the calendars we read. Check the links below.</p>'
)

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NAME}: news, events and what's changing</title>
<meta name="description" content="Local headlines, events and nightly public data for {NAME}, Washington, DC. Independent; not affiliated with the DC Government.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="wrap mast">
  <div class="g">
    <h1>{NAME}</h1>
    <p class="tag"><strong>News, events and what's changing in {NAME}, Washington, DC.</strong>
    Updated nightly from public data. Data as of <time datetime="{gen.isoformat()}" class="num">{asof}</time>.</p>
  </div>
  <nav class="nav" aria-label="Sections"><ul>{nav}</ul></nav>
</header>

<main id="main" class="wrap">

<section class="g" aria-labelledby="h-news" style="margin-top:40px">
  <div class="news" id="news">
    <div class="sh"><span class="no num">01</span><h2 id="h-news">Latest news</h2><a class="more" href="#news">All news</a></div>
    <ol class="newslist">{"".join(news_rows)}</ol>
    <p class="cap">Headlines from local outlets that mention {NAME}. Each links to the outlet; we don't copy articles.</p>
  </div>
  <div class="events" id="events">
    <div class="sh"><span class="no num">02</span><h2>Coming up</h2><span class="note">Next 14 days</span></div>
    {events_block}
    <p class="also"><b>Also check</b>{ev_links}</p>
  </div>
</section>

<section class="g cond" id="condition" aria-labelledby="h-cond">
  <div class="sh"><span class="no num">03</span><h2 id="h-cond">Today's condition</h2><span class="note">311 requests, last {d['windows']['requests_days']} days vs the {d['windows']['requests_days']} before</span></div>
  <p class="lead">{lead_sentence}</p>
  <ul class="tally" aria-label="Request types by direction">
    <li class="tl">Of {len(readings)} request types</li>
    <li><span class="tn num">{tally['rising']}</span> rising</li>
    <li><span class="tn num">{tally['easing']}</span> easing</li>
    <li><span class="tn num">{tally['steady']}</span> steady</li>
  </ul>
  <p class="cap">Tally covers the {len(readings)} request types with at least {VOL} requests in either period. Steady means a change within 5% or within 2 requests.</p>
</section>

<section class="g measures" id="measures" aria-labelledby="h-meas">
  <div class="sh"><span class="no num">04</span><h2 id="h-meas">Measures</h2><span class="note">Latest period vs the one before</span></div>

  <div class="m">
    <h3>311 requests</h3>
    <div class="big num">{n(req['total'])}</div>
    <p class="cmp">from <span class="num">{n(req['previous_total'])}</span> &middot; <strong class="num">{signed(req_diff)}{f" ({req_pc})" if req_pc else ""}</strong></p>
    {pair_bar(req['total'], req['previous_total'], 'Last 30 days', '30 days before')}
    <div class="key"><span><i></i>Last 30 days</span><span><i class="p"></i>30 days before</span></div>
    <p class="cap"><span class="num">{n(req['open'])}</span> still open.</p>
  </div>

  <div class="m">
    <h3>Crime reports</h3>
    <div class="big num">{n(crime['total'])}</div>
    <p class="cmp">from <span class="num">{n(crime['previous_total'])}</span> &middot; <strong class="num">{signed(c_diff)}</strong></p>
    {pair_bar(crime['total'], crime['previous_total'], 'Last 30 days', '30 days before')}
    <div class="key"><span><i></i>Last 30 days</span><span><i class="p"></i>30 days before</span></div>
    <p class="cap">Counts only, never mapped or graded. Counts this small swing from month to month. {e(crime['note'])}</p>
  </div>

  <div class="m">
    <h3>Median house price</h3>
    <div class="big num">{money_k(house['median_12mo'])}</div>
    <p class="cmp">from <span class="num">{money_k(house['median_prev_12mo'])}</span> &middot; <strong class="num">{"−" if hp_diff < 0 else "+"}{money_k(abs(hp_diff))}{f" ({hp_pct})" if hp_pct else ""}</strong><span class="state">{hp_state}</span></p>
    {month_bars(months)}
    <p class="cap">Last 12 months vs the 12 before, from <span class="num">{house['count_12mo']}</span> and <span class="num">{house['count_prev_12mo']}</span> house sales. Bars: monthly medians, <span class="num">{min(m['count'] for m in months)}&ndash;{max(m['count'] for m in months)}</span> sales each, so they jump.</p>
  </div>

  <div class="m">
    <h3>Building permits</h3>
    <div class="big num">{nper}</div>
    <p class="cmp">issued, last {d['windows']['permits_days']} days &middot; <strong class="num">{nbig}</strong> bigger projects</p>
    <div class="split" role="img" aria-label="{nbig} bigger projects, {nper - nbig} smaller jobs"><span class="a" style="width:{nbig / nper * 100:.1f}%"></span><span class="b2" style="width:{(nper - nbig) / nper * 100:.1f}%"></span></div>
    <div class="key"><span><i style="background:var(--accent)"></i>Bigger <span class="num">{nbig}</span></span><span><i class="p"></i>Smaller <span class="num">{nper - nbig}</span></span></div>
    <p class="cap"><span class="num">{gcount.get('Additions', 0)}</span> additions, <span class="num">{gcount.get('Demolition', 0)}</span> demolition, <span class="num">{gcount.get('New construction', 0)}</span> new buildings. The permit feed carries no count for the period before.</p>
  </div>
</section>

<section class="g" id="permits" aria-labelledby="h-perm">
  <div class="sh"><span class="no num">05</span><h2 id="h-perm">What's being built</h2><span class="note">Permits issued, last {d['windows']['permits_days']} days</span><a class="more" href="#permits">All permits</a></div>
  <div class="mapcol">
    {map_svg}
    <div class="maplegend"><span><i class="k"></i>Bigger project (addition, demolition, new building), numbered</span><span><i class="d"></i>Other permit</span></div>
  </div>
  <div class="bigcol">
    <h3>Bigger projects <span class="muted num" style="font-weight:400">{len(big)}</span></h3>
    <ol class="biglist">{"".join(big_rows) or "<li><span></span><p>No additions, demolitions or new buildings this period.</p></li>"}</ol>
  </div>
  <div class="bytype">
    <h3>All {nper} permits by type</h3>
    <table><tbody>{group_rows}</tbody></table>
  </div>
  <p class="bytype-note cap">Map shows the {len(permits)} permits with coordinates inside the {NAME} boundary ({e(d['boundary']['source'])}). Grid lines every 0.005&deg;, about 550 m north&ndash;south.</p>
</section>

<section class="g" aria-label="Homes and 311">
  <div class="half" id="homes">
    <div class="sh"><span class="no num">06</span><h2>Homes</h2><a class="more" href="#homes">Sales and prices</a></div>
    <dl class="facts">
      <div><dt>Median house, last 60 days</dt><dd class="num">{money_k(l60['median'])}<small>{l60['count']} sales</small></dd></div>
      <div><dt>Price per sq ft, last 60 days</dt><dd class="num">${l60['median_ppsf']}<small>median</small></dd></div>
      <div><dt>Median condo, 12 months</dt><dd class="num">{money_k(condo['median_12mo'])}<small>{condo['count_12mo']} sales</small></dd></div>
    </dl>
    <div class="subhead"><h3>Recent sales</h3><span class="lab">Sold above assessment, 12 months: <span class="num">{above['n']}</span> of <span class="num">{above['of']}</span></span></div>
    <table>
      <thead><tr><th class="first">Date</th><th>Address</th><th class="hide-s">Type</th><th class="num">Price</th><th class="num hide-s">vs assessed</th></tr></thead>
      <tbody>{"".join(sales_rows)}</tbody>
    </table>
    <p class="cap">Sales from DC's tax records for the assessment neighborhood "{NAME}", which overlaps but does not exactly match the boundary used elsewhere on this page.</p>
  </div>
  <div class="half" id="streets">
    <div class="sh"><span class="no num">07</span><h2>Top 311 requests</h2><a class="more" href="#streets">All types</a></div>
    <table>
      <thead><tr><th>Type, last {d['windows']['requests_days']} days</th><th aria-hidden="true"></th><th class="num">Now</th><th class="num hide-s">Before</th><th class="num">Change</th></tr></thead>
      <tbody>{"".join(rows_311)}</tbody>
    </table>
    <div class="key" style="margin-top:10px"><span><i></i>Last {d['windows']['requests_days']} days</span><span><i class="p" style="width:2px;height:12px;vertical-align:-2px"></i>{d['windows']['requests_days']} days before</span><span>Percent shown only when both counts are 100 or more</span></div>
  </div>
</section>

<section class="g" aria-label="Streets">
  <div class="half">
    <div class="sh"><span class="no num">08</span><h2>Curb space</h2><a class="more" href="#streets">This week's curb permits</a></div>
    <dl class="facts">
      <div><dt>Active this week</dt><dd class="num">{curb['active_this_week']}</dd></div>
      <div><dt>Starting in the next 7 days</dt><dd class="num">{curb['starting_next_7d']}</dd></div>
      <div><dt>Curb reserved</dt><dd class="num">{n(curb['reserved_ft'])} ft<small>about {curb['reserved_ft'] / 5280:.1f} miles</small></dd></div>
    </dl>
    <h3>Starting soon</h3>
    <table><tbody>{"".join(curb_rows)}</tbody></table>
    {f'<p class="cap">and {curb_more} more starting in the next 7 days.</p>' if curb_more > 0 else ''}
  </div>
  <div class="half">
    <div class="sh"><span class="no num">09</span><h2>Street trees</h2><a class="more" href="#streets">Tree details</a></div>
    <div class="hero"><span class="big num">{n(trees['total'])}</span><p>street trees of <span class="num">{trees['species']}</span> species; <span class="num">{trees['planted_5y']}</span> planted in the last 5 years. <span class="num">{trees['empty_boxes']}</span> empty tree boxes are open for planting.</p></div>
    <span class="lab">Condition</span>
    <div class="condbar" role="img" aria-label="Condition: {', '.join(f'{k} {n(cond.get(k, 0))}' for k, _ in cond_order)}">{cond_bar}</div>
    <ul class="condleg">{cond_leg}</ul>
    <h3>Most common</h3>
    <table><tbody>{species_rows}</tbody></table>
    <p class="cap">Largest: a {e(bigtree['species'].lower())}, <span class="num">{bigtree['dbh_in']}</span> in across, on the {e(bigtree['block'])}. <a href="https://311.dc.gov/">Ask DC to plant a tree on your block</a>.</p>
  </div>
</section>

<section class="g then" id="then" aria-labelledby="h-then">
  <div class="sh"><span class="no num">10</span><h2 id="h-then">Then</h2><span class="note">How {NAME} was built</span><a class="more" href="#then">History</a></div>
  <p class="yr num" aria-hidden="true">{fb['year']}</p>
  <div class="fb">
    <h3>{e(fb['block'])}</h3>
    <p class="s">In {fb['year']}, {e(fb['builder'])} built <span class="num">{fb['buildings']}</span> buildings on this block under <span class="num">{fb['permits']}</span> permits. The largest permit covered <span class="num">{fb['largest_permit']['buildings']}</span> buildings at an estimated <span class="num">${n(fb['largest_permit']['cost'])}</span>.</p>
  </div>
  <div class="decades">
    <h3>Buildings by decade built</h3>
    <ul class="declist">{dec_rows}</ul>
    <p class="cap"><span class="num">{n(hist['buildings']['records'])}</span> historic building permit records, {hist['buildings']['year_min']}&ndash;{hist['buildings']['year_max']}.</p>
  </div>
  <ul class="clips" aria-label="Newspaper clips from {e(arch['week_label'])}">{clip_rows}</ul>
  <p class="cap" style="grid-column:1/-1">This week 100 years ago, {e(arch['week_label'])}. Machine-read text from scanned pages at the Library of Congress; errors are the scanner's.</p>
</section>

<section class="g" aria-label="Representatives and email">
  <div class="half" id="reps">
    <div class="sh"><span class="no num">11</span><h2>Who represents you</h2><span class="note">{len(d['smds'])} single member districts</span></div>
    <ul class="replist">{rep_rows}</ul>
    <p class="cap">Each single member district elects one Advisory Neighborhood Commissioner. Commissioners and meeting dates are on each ANC's site.</p>
  </div>
  <div class="half" id="email">
    <div class="sh"><span class="no num">12</span><h2>Weekly email</h2></div>
    <p style="margin:0 0 16px;font-size:18px;line-height:1.4">These readings in your inbox once a week: news, events, and what changed.</p>
    <form class="mail" action="#" onsubmit="return false">
      <label class="vh" for="em">Email address</label>
      <input id="em" type="email" name="email" placeholder="you@example.com" autocomplete="email" required>
      <button type="submit">Subscribe</button>
    </form>
    <p class="cap">One email a week. Unsubscribe in one click.</p>
  </div>
</section>
</main>

<footer>
  <div class="wrap g">
    <div><p><strong>{e(d['slug'])}.org is independent.</strong> It is not affiliated with, endorsed by, or speaking for the DC Government.</p>
    <p>Built every night from public data. Data as of <span class="num">{asof}</span>.</p></div>
    <div><p><strong>Sources</strong><br>Permits: {e(sources['permits'])}<br>311: {e(sources['requests'])}<br>Crime: {e(sources['crime'])}<br>Districts: {e(sources['smds'])}</p></div>
    <div><p><strong>Data license</strong> {e(sources['license'])}. Numbers are as published; where a feed is missing, we say so.</p>
    <p><a href="#">About the data</a> &middot; <a href="#">Permits RSS</a></p></div>
  </div>
</footer>
</body>
</html>
"""

(HERE / "index.html").write_text(html, encoding="utf-8")
print("wrote", HERE / "index.html", len(html), "bytes")
