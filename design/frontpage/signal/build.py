"""Build the 'Signal' Petworth front page from the live data file.

Usage:  python build.py   (writes index.html next to this file)
"""
import html
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:  # tzdata missing: fall back to EDT
    ET = timezone(timedelta(hours=-4))

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / "site" / "src" / "data" / "petworth.json"
d = json.loads(DATA.read_text(encoding="utf-8"))
SLUG = d["slug"]
NAME = d["name"]
BASE = f"/{SLUG}"


def e(s):
    return html.escape(str(s), quote=True)


def n(x):
    return f"{x:,}"


def money(x):
    if x >= 1_000_000:
        return f"${x/1_000_000:.2f}M".replace(".00M", "M")
    return f"${round(x/1000):,}K"


def pct_ok(a, b):
    """Percentages only when both counts are 100 or more."""
    return a >= 100 and b >= 100


def pct(a, b):
    return round((a - b) / b * 100)


def minus(x):
    return str(x).replace("-", "−")


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


def sentence_case(s, limit=130):
    s = re.sub(r"\s+", " ", s.replace("\r", " ").replace("\n", " ")).strip()
    letters = [c for c in s if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        s = s.lower().capitalize()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return s


def parse_utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


gen = parse_utc(d["generated_at"]).astimezone(ET)
TODAY = date.fromisoformat(d["events"]["today"])
try:
    updated_label = gen.strftime("%a, %b %-d, %Y, %-I:%M %p")
except ValueError:  # Windows strftime lacks %-d
    updated_label = gen.strftime("%a, %b %#d, %Y, %#I:%M %p")
updated_label = updated_label.replace("AM", "am").replace("PM", "pm")


def day_label(dt: date, long=False):
    delta = (dt - TODAY).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    if delta == -1:
        return "Yesterday"
    fmt = "%a, %b %d" if long else "%b %d"
    return dt.strftime(fmt).replace(" 0", " ")


def short_date(iso):
    return date.fromisoformat(iso[:10]).strftime("%b %d").replace(" 0", " ")


# --------------------------------------------------------------------------- news
news = d["news"]["items"]
for it in news:
    it["_d"] = parse_utc(it["published"]).astimezone(ET).date()
recent = [it for it in news if (TODAY - it["_d"]).days <= 14]
earlier = [it for it in news if (TODAY - it["_d"]).days > 14]


def news_item(it, cls=""):
    return (
        f'<li class="{cls}"><a class="hl" href="{e(it["url"])}">{e(it["title"])}</a>'
        f'<span class="meta">{e(it["source"])} <span aria-hidden="true">/</span> '
        f'<time datetime="{it["_d"].isoformat()}">{day_label(it["_d"])}</time></span></li>'
    )


if news:
    lead, rest = (recent[0], recent[1:]) if recent else (None, [])
    news_html = ""
    if lead:
        news_html += f'<ol class="news-lead" role="list">{news_item(lead, "lead")}' + "".join(news_item(i) for i in rest) + "</ol>"
    else:
        news_html += '<p class="empty">No new Petworth headlines in the past two weeks.</p>'
    if earlier:
        news_html += (
            '<h3 class="minor">Earlier</h3><ol class="news-earlier" role="list">'
            + "".join(news_item(i) for i in earlier[:4])
            + "</ol>"
        )
else:
    news_html = '<p class="empty">No headlines from local outlets right now.</p>'

# --------------------------------------------------------------------------- events
ev_all = d["events"]["events"]
horizon = TODAY + timedelta(days=14)
events = [x for x in ev_all if TODAY <= date.fromisoformat(x["date"]) < horizon]
rows = []
for x in events:
    dt = date.fromisoformat(x["date"])
    rows.append(
        f'<li><span class="when"><strong>{day_label(dt)}</strong>'
        f'<span>{e(dt.strftime("%a %b %d").replace(" 0", " ") if (dt - TODAY).days < 2 else x["time"].replace(":00", "").replace(" - ", "–"))}</span></span>'
        f'<span class="what"><a href="{e(x["url"])}">{e(x["title"])}</a>'
        f'<span>{e(x["kind"].capitalize())} · {e(x["place"])}'
        + (f' · <span class="nw">{e(x["time"].replace(":00", "").replace(" - ", "–"))}</span>' if (dt - TODAY).days < 2 else "")
        + "</span></span></li>"
    )
events_html = (
    f'<ol class="board-list" role="list">{"".join(rows)}</ol>'
    if rows
    else '<p class="empty dark">Nothing on the machine-readable calendars for the next two weeks. Try the links below.</p>'
)
also = " ".join(f'<li><a href="{e(l["url"])}">{e(l["name"])}</a></li>' for l in d["events"]["links"])

# --------------------------------------------------------------------------- 311 condition
NICE = {
    "DC Health Rodent & Vector Control": "Rodent complaints",
    "DOEE - LIHEAP": "Energy-bill assistance (LIHEAP)",
    "Trash Collection - Missed": "Missed trash pickups",
    "Recycling Collection - Missed": "Missed recycling pickups",
    "Scheduled Yard Waste": "Scheduled yard waste",
    "Bulk Collection": "Bulk collection",
    "Illegal Dumping": "Illegal dumping",
    "Parking Enforcement": "Parking enforcement",
    "Sanitation Enforcement": "Sanitation enforcement",
    "Dead Animal Collection": "Dead animal collection",
    "Residential Parking Permit Violation": "Residential parking violations",
    "Container Removal": "Container removal",
}


def nice(t):
    return NICE.get(t, t)


req = d["requests"]
bt = req["by_type"]
sig = [t for t in bt if max(t["count"], t["previous"]) >= 10]


def trend(t):
    ch = t["count"] - t["previous"]
    if abs(ch) < max(3, 0.1 * t["previous"]):
        return "steady"
    return "rising" if ch > 0 else "easing"


tally = {"rising": 0, "easing": 0, "steady": 0}
for t in sig:
    tally[trend(t)] += 1
rises = sorted([t for t in sig if t["previous"] >= 10 and trend(t) == "rising"], key=lambda t: t["previous"] - t["count"])
falls = sorted([t for t in sig if t["previous"] >= 10 and trend(t) == "easing"], key=lambda t: t["count"] - t["previous"])
tot, ptot = req["total"], req["previous_total"]
if rises:
    big = rises[0]
    lead_sentence = (
        f'<strong>{e(nice(big["type"]))}</strong> rose to {n(big["count"])} in the past 30 days, up from {n(big["previous"])}, '
        + (f"even as all 311 requests fell from {n(ptot)} to {n(tot)}." if tot < ptot else f"as all 311 requests went from {n(ptot)} to {n(tot)}.")
    )
elif falls:
    big = falls[0]
    lead_sentence = f'<strong>{e(nice(big["type"]))}</strong> fell to {n(big["count"])} in the past 30 days, down from {n(big["previous"])}.'
else:
    big = None
    lead_sentence = f"311 requests held steady: {n(tot)} in the past 30 days against {n(ptot)} before."
n_sig = len(sig)
tally_bar = "".join(
    f'<span class="seg {k}" style="flex:{v}" title="{v} {k}"></span>' for k, v in tally.items() if v
)

# --------------------------------------------------------------------------- measures
def change_line(a, b, unit_more, unit_fewer, allow_pct):
    ch = a - b
    if ch == 0:
        return "Same as the period before"
    word = unit_more if ch > 0 else unit_fewer
    arrow = "↑" if ch > 0 else "↓"
    p = f" ({'+' if ch > 0 else minus('-')}{abs(pct(a, b))}%)" if allow_pct else ""
    return f'<span aria-hidden="true">{arrow}</span> {n(abs(ch))} {word}{p}'


crime = d["crime"]
house = d["homes"]["house"]
condo = d["homes"]["condo"]
permits = d["permits"]
BIG_GROUPS = ("Demolition", "New construction", "Additions")

hc = house["median_12mo"] - house["median_prev_12mo"]
house_line = (
    f'<span aria-hidden="true">{"↑" if hc > 0 else "↓"}</span> {money(abs(hc))} '
    + ("higher" if hc > 0 else "lower")
    + (f" ({'+' if hc > 0 else minus('-')}{abs(pct(house['median_12mo'], house['median_prev_12mo']))}%)" if pct_ok(house["count_12mo"], house["count_prev_12mo"]) else "")
)
big_permits = [p for p in permits if p["group"] in BIG_GROUPS]

measures = [
    ("311 requests", n(tot), "last 30 days", f"{n(ptot)} the 30 days before", change_line(tot, ptot, "more", "fewer", pct_ok(tot, ptot)), "#block"),
    ("Crime reports", n(crime["total"]), "last 30 days", f'{n(crime["previous_total"])} the 30 days before',
     change_line(crime["total"], crime["previous_total"], "more", "fewer", pct_ok(crime["total"], crime["previous_total"])) + ". Counts only, never mapped.", None),
    ("Median house price", money(house["median_12mo"]), "last 12 months", f'{money(house["median_prev_12mo"])} the 12 months before', house_line + f' · from {n(house["count_12mo"])} sales', "#homes"),
    ("Building permits", n(len(permits)), "last 30 days", f"{len(big_permits)} bigger projects, {len(permits) - len(big_permits)} smaller jobs", "No earlier period in this data to compare with.", "#map"),
]
measures_html = "".join(
    f'<div class="measure"><h3>{e(lbl)}</h3><p class="big">{val}</p><p class="per">{per}</p>'
    f'<p class="prev">{prev}</p><p class="chg">{chg}</p></div>'
    for lbl, val, per, prev, chg, _ in measures
)
crime_rows = "".join(
    f'<li><span>{e(o["offense"].title().replace("W/", "w/").replace("F/", "from "))}</span><span class="num">{o["count"]}</span><span class="num muted">{o["previous"]}</span></li>'
    for o in crime["by_offense"]
)

# --------------------------------------------------------------------------- map
ring = d["boundary"]["rings"][0]


def inside(lon, lat, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi:
            c = not c
        j = i
    return c


lons = [p[0] for p in ring]
lats = [p[1] for p in ring]
lat0 = (min(lats) + max(lats)) / 2
kx = math.cos(math.radians(lat0))
W = 600
pad = 14
span_x = (max(lons) - min(lons)) * kx
span_y = max(lats) - min(lats)
scale = (W - 2 * pad) / span_x
H = round(span_y * scale + 2 * pad)


def proj(lon, lat):
    return (pad + (lon - min(lons)) * kx * scale, pad + (max(lats) - lat) * scale)


path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (proj(*p) for p in ring)) + " Z"
mapped = [p for p in permits if p.get("lat") and p.get("lon") and inside(p["lon"], p["lat"], ring)]
small_dots, big_dots, big_list = [], [], []
seen = set()
k = 0
for p in mapped:
    x, y = proj(p["lon"], p["lat"])
    if p["group"] in BIG_GROUPS:
        key = (p["address"], p["group"])
        if key in seen:
            continue
        seen.add(key)
        k += 1
        big_dots.append(
            f'<g class="bigdot"><circle cx="{x:.1f}" cy="{y:.1f}" r="11"/><text x="{x:.1f}" y="{y:.1f}">{k}</text>'
            f'<title>{k}. {e(p["group"])}: {e(addr(p["address"]))}</title></g>'
        )
        big_list.append(
            f'<li><span class="num-badge">{k}</span><div><strong>{e(addr(p["address"]))}</strong>'
            f'<span class="tag">{e(p["group"])} · issued {short_date(p["issued"])}</span>'
            f'<span class="work">{e(sentence_case(p["work"]) or p["subtype"].capitalize())}</span></div></li>'
        )
    else:
        small_dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6"><title>{e(p["group"])}: {e(addr(p["address"]))}</title></circle>')
# big projects outside the boundary still belong in the list (no dot)
for p in permits:
    if p["group"] in BIG_GROUPS and p not in mapped and (p["address"], p["group"]) not in seen:
        seen.add((p["address"], p["group"]))
        big_list.append(
            f'<li><span class="num-badge off">–</span><div><strong>{e(addr(p["address"]))}</strong>'
            f'<span class="tag">{e(p["group"])} · issued {short_date(p["issued"])} · just outside the map boundary</span>'
            f'<span class="work">{e(sentence_case(p["work"]) or p["subtype"].capitalize())}</span></div></li>'
        )
map_svg = (
    f'<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-labelledby="map-t map-d">'
    f'<title id="map-t">Map of building permits in {NAME}, last 30 days</title>'
    f'<desc id="map-d">{len(mapped)} permits plotted inside the {NAME} boundary; {k} bigger projects are numbered and listed beside the map.</desc>'
    f'<path class="bound" d="{path}"/>'
    f'<g class="smalldots">{"".join(small_dots)}</g>{"".join(big_dots)}'
    f'<g class="northarrow" transform="translate({W - 34},{H - 46})"><path d="M10 0 L18 22 L10 17 L2 22 Z"/><text x="10" y="36">N</text></g>'
    "</svg>"
)
groups = {}
for p in permits:
    groups[p["group"]] = groups.get(p["group"], 0) + 1
gmax = max(groups.values()) if groups else 1
groups_html = "".join(
    f'<li><span class="lbl">{e(g)}</span><span class="bar"><span style="width:{c / gmax * 100:.1f}%"></span></span><span class="num">{c}</span></li>'
    for g, c in sorted(groups.items(), key=lambda kv: -kv[1])
)

# --------------------------------------------------------------------------- block: curb + top 311
curb = d["streets"]["curb"]
up = curb["upcoming"]
_prev = [None]


def _curb_date(c):
    lab = day_label(date.fromisoformat(c["start"]), long=True)
    same = lab == _prev[0]
    _prev[0] = lab
    return f'<span class="date{" same" if same else ""}">{"" if same else lab}</span>'


curb_rows = "".join(
    f'<li>{_curb_date(c)}'
    f'<span class="body"><strong>{e(c["block"])}</strong><span>{e(c["type"])} · {c["ft"]} ft · until {short_date(c["end"])}'
    + (f' · {e(c["hours"])}' if c["hours"] else "")
    + "</span></span></li>"
    for c in up[:7]
)
top = sorted(bt, key=lambda t: -t["count"])[:8]
tmax = max(max(t["count"], t["previous"]) for t in top) if top else 1
top_rows = "".join(
    f'<li><span class="lbl">{e(nice(t["type"]))}</span>'
    f'<span class="bar" aria-hidden="true"><span style="width:{t["count"] / tmax * 100:.1f}%"></span><i style="left:{t["previous"] / tmax * 100:.1f}%"></i></span>'
    f'<span class="num">{t["count"]}</span><span class="num muted">{t["previous"]}</span></li>'
    for t in top
)

# --------------------------------------------------------------------------- homes
months = d["homes"]["by_month"]
vals = [m["median"] for m in months if m["median"]]
vmax = max(vals) if vals else 1
bars = []
CH_W, CH_H = 360, 170
bw = CH_W / len(months)
for i, m in enumerate(months):
    x = i * bw
    lab = datetime.strptime(m["month"], "%Y-%m").strftime("%b")[0]
    if m["median"]:
        h = m["median"] / vmax * (CH_H - 34)
        bars.append(
            f'<g><rect x="{x + 3:.1f}" y="{CH_H - 18 - h:.1f}" width="{bw - 6:.1f}" height="{h:.1f}"/>'
            f'<title>{datetime.strptime(m["month"], "%Y-%m").strftime("%B %Y")}: median {money(m["median"])} from {m["count"]} sales</title></g>'
            f'<text class="v" x="{x + bw / 2:.1f}" y="{CH_H - 23 - h:.1f}">{round(m["median"] / 1000)}</text>'
        )
    else:
        bars.append(
            f'<g><rect class="none" x="{x + 3:.1f}" y="{CH_H - 22:.1f}" width="{bw - 6:.1f}" height="4"/>'
            f'<title>{datetime.strptime(m["month"], "%Y-%m").strftime("%B %Y")}: fewer than 3 sales, no median</title></g>'
        )
    bars.append(f'<text x="{x + bw / 2:.1f}" y="{CH_H - 3}">{lab}</text>')
chart = (
    f'<svg class="chart" viewBox="0 0 {CH_W} {CH_H}" role="img" aria-label="Median house sale price by month, '
    f'{datetime.strptime(months[0]["month"], "%Y-%m").strftime("%B %Y")} to {datetime.strptime(months[-1]["month"], "%Y-%m").strftime("%B %Y")}. '
    f'Highest {money(vmax)}, lowest {money(min(vals))}.">{"".join(bars)}</svg>'
)
chart_table = "".join(
    f'<tr><th scope="row">{datetime.strptime(m["month"], "%Y-%m").strftime("%b %Y")}</th><td>{money(m["median"]) if m["median"] else "–"}</td><td>{m["count"]}</td></tr>'
    for m in months
)
sales = d["homes"]["recent_sales"][:5]
sales_rows = "".join(
    f'<li><span class="body"><strong>{e(s["address"])}</strong><span>{short_date(s["date"])} · {e(s["kind"])}'
    + (f' · {s["beds"]} bed' if s.get("beds") else "")
    + (f' · {n(s["sqft"])} sq ft' if s.get("sqft") else "")
    + f'</span></span><span class="num">{money(s["price"])}</span></li>'
    for s in sales
)
l60 = d["homes"]["last_60d"]

# --------------------------------------------------------------------------- trees
trees = d["streets"]["trees"]
sp = trees["top_species"][:5]
spmax = sp[0]["count"] if sp else 1
species_rows = "".join(
    f'<li><span class="lbl">{e(s["name"])}</span><span class="bar"><span style="width:{s["count"] / spmax * 100:.1f}%"></span></span><span class="num">{s["count"]}</span></li>'
    for s in sp
)
bigtree = trees["biggest"][0] if trees["biggest"] else None

# --------------------------------------------------------------------------- then
hist = d["history"]
fb = hist["buildings"]["featured_block"]
then_sentence = (
    f'In {fb["year"]}, {e(fb["builder"])} built {fb["buildings"]} buildings on the {e(fb["block"])} under {fb["permits"]} permits. '
    f'The largest permit covered {fb["largest_permit"]["buildings"]} of them, at an estimated ${n(fb["largest_permit"]["cost"])} in total.'
)
arch = hist["archive"]
clips = [c for c in arch["clips"] if len(c["text"]) > 60][:3]
clips_html = "".join(
    f'<li><blockquote>{e(sentence_case(c["text"], 170))}</blockquote>'
    f'<a href="{e(c["url"])}">{e(arch["paper"])}, {date.fromisoformat(c["date"]).strftime("%b %d, %Y").replace(" 0", " ")}, page {c["page"]}</a></li>'
    for c in clips
)
week_label = arch["week_label"].replace("�", "–")

# --------------------------------------------------------------------------- reps (no person names)
ancs = {}
for s in d["smds"]:
    ancs.setdefault(s["anc"], {"url": s["url"], "smds": []})["smds"].append(s["smd"])
reps_html = "".join(
    f'<li><a href="{e(v["url"])}"><strong>ANC {e(a)}</strong></a><span>Districts {", ".join(e(x) for x in v["smds"])}</span></li>'
    for a, v in sorted(ancs.items())
)

# --------------------------------------------------------------------------- strip (the daily check-in)
nxt = events[0] if events else None
strip = []
if nxt:
    dt = date.fromisoformat(nxt["date"])
    strip.append(("Next up", f'{day_label(dt)}, {nxt["time"].replace(":00", "").replace(" - ", "–")}', nxt["title"], "#events"))
if news:
    strip.append(("Newest headline", f'{news[0]["source"]}, {day_label(news[0]["_d"]).lower() if day_label(news[0]["_d"]) in ("Today", "Yesterday") else day_label(news[0]["_d"])}', news[0]["title"], "#news"))
if big:
    strip.append(("311 this month", f'{nice(big["type"])} {"up" if big["count"] > big["previous"] else "down"}', f'{n(big["count"])}, from {n(big["previous"])}', "#condition"))
strip_html = "".join(
    f'<li><a href="{href}"><span class="k">{e(k_)}</span><span class="v">{e(v)}</span><span class="t">{e(t)}</span></a></li>'
    for k_, v, t, href in strip
)

OTHER = [
    ("Tenleytown", "https://tenleytown.org/"), ("Adams Morgan", "https://adamsmorgan.org/"),
    ("Friendship Heights", "https://friendshipheights.org/"), ("Capitol Hill", "https://capitolhilldc.org/"),
    ("Columbia Heights", "https://columbiaheights.net/"), ("Georgetown", "https://georgetowndc.org/"),
    ("Chevy Chase", "https://chevychasedc.net/"), ("Anacostia", "https://anacostiadc.net/"),
    ("Cleveland Park", "https://clevelandpark.org/"), ("Dupont Circle", "https://dupontcircledc.net/"),
    ("H Street NE", "https://hstreet.net/"), ("Navy Yard", "https://navyyarddc.net/"),
]
other_html = "".join(f'<li><a href="{u}">{e(nm)}</a></li>' for nm, u in OTHER)

CSS = (HERE / "style.css").read_text(encoding="utf-8")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NAME}: news, events and what's changing</title>
<meta name="description" content="Independent neighborhood site for {NAME}, Washington, DC. Local headlines, events and public data, updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Source+Serif+4:opsz,wght@8..60,400..700&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#news">Skip to the news</a>
<header class="mast">
  <div class="topline"><div class="wrap">
    <span>Independent neighborhood news · Washington, DC</span>
    <span>Updated <time datetime="{gen.isoformat()}">{updated_label}</time> · nightly from public data</span>
  </div></div>
  <div class="wrap brand">
    <a class="wordmark" href="{BASE}/" aria-label="{NAME} home">
      <span class="word">{NAME}</span>
      <span class="line" aria-hidden="true"><i></i><b></b><i></i></span>
    </a>
    <p class="tag">News, events and what's changing between Grant Circle and Sherman Circle.</p>
  </div>
  <nav class="wrap nav" aria-label="Sections">
    <a href="#news">News</a><a href="#events">Events</a><a href="#condition">Today</a><a href="#map">Permits</a><a href="#block">Your block</a><a href="#homes">Homes</a><a href="#then">Then</a><a href="#email">Weekly email</a>
  </nav>
</header>

<main>
  <section class="wrap strip" aria-label="Today at a glance">
    <ol role="list">{strip_html}</ol>
  </section>

  <div class="wrap lead-grid">
    <section id="news" class="stop" aria-labelledby="h-news">
      <h2 id="h-news"><span class="dot" aria-hidden="true"></span>Latest news</h2>
      {news_html}
      <p class="foot">Headlines from local outlets that mention {NAME}, linked to the outlet. We never copy articles. <a href="{BASE}/news/">All news</a></p>
    </section>

    <section id="events" class="board" aria-labelledby="h-events">
      <h2 id="h-events">Coming up <span>next 14 days</span></h2>
      {events_html}
      <div class="also"><h3>Also check</h3><ul role="list">{also}</ul></div>
    </section>
  </div>

  <section id="condition" class="band mist" aria-labelledby="h-cond">
    <div class="wrap">
      <h2 id="h-cond" class="eyebrow"><span class="dot" aria-hidden="true"></span>Today's condition · {TODAY.strftime("%A, %B %d").replace(" 0", " ")}</h2>
      <div class="cond-grid">
        <p class="cond-lead">{lead_sentence}</p>
        <div class="tally">
          <p class="tally-k">Of {n_sig} kinds of 311 request with 10 or more in either month</p>
          <dl>
            <div><dt>rising</dt><dd>{tally["rising"]}</dd></div>
            <div><dt>easing</dt><dd>{tally["easing"]}</dd></div>
            <div><dt>steady</dt><dd>{tally["steady"]}</dd></div>
          </dl>
          <div class="tbar" aria-hidden="true">{tally_bar}</div>
          <p class="note">Last 30 days against the 30 before. Steady means a change smaller than 3 requests or 10%.</p>
        </div>
      </div>
      <h3 class="sr-only">Measures</h3>
      <div class="measures">{measures_html}</div>
      <details class="crime-detail"><summary>Crime reports by offense</summary>
        <ul class="rowlist" role="list"><li class="head"><span>Offense</span><span class="num">Last 30 days</span><span class="num">30 days before</span></li>{crime_rows}</ul>
        <p class="note">{e(crime["note"])} Shown as counts only, never mapped or graded.</p>
      </details>
    </div>
  </section>

  <section id="map" class="wrap stop" aria-labelledby="h-map">
    <h2 id="h-map"><span class="dot" aria-hidden="true"></span>What's being built</h2>
    <p class="dek">{len(permits)} building permits issued in the last 30 days. The {len(big_list)} bigger projects (additions, demolition, new construction) are numbered.</p>
    <div class="map-grid">
      <figure class="map-fig">{map_svg}
        <figcaption><span class="nw"><span class="key k-big"></span> Bigger project</span> <span class="nw"><span class="key k-small"></span> Other permit</span> <span>{len(mapped)} of {len(permits)} permits fall inside the boundary</span></figcaption>
      </figure>
      <div>
        <ol class="projects" role="list">{"".join(big_list) or '<li class="empty">No bigger projects this month.</li>'}</ol>
        <h3 class="minor">All permits by type</h3>
        <ul class="bars" role="list">{groups_html}</ul>
        <p class="foot"><a href="{BASE}/projects/">Every project, with permit details</a></p>
      </div>
    </div>
  </section>

  <section id="block" class="wrap stop" aria-labelledby="h-block">
    <h2 id="h-block"><span class="dot" aria-hidden="true"></span>On your block</h2>
    <div class="two">
      <div>
        <h3 class="sub">Curb space reserved, starting soon</h3>
        <p class="dek small">{curb["starting_next_7d"]} permits start in the next 7 days; {curb["active_this_week"]} are active this week.</p>
        <ol class="curb" role="list">{curb_rows}</ol>
        <p class="foot"><a href="{BASE}/streets/">All {curb["starting_next_7d"]} upcoming curb permits</a></p>
      </div>
      <div>
        <h3 class="sub">Top 311 requests</h3>
        <p class="dek small">Last 30 days. The thin mark shows the 30 days before.</p>
        <ul class="bars b311" role="list"><li class="head"><span class="lbl">Request</span><span></span><span class="num">Now</span><span class="num">Before</span></li>{top_rows}</ul>
        <p class="foot">{n(req["open"])} requests still open. Locations are published only to the hundred block.</p>
      </div>
    </div>
  </section>

  <section id="homes" class="wrap stop" aria-labelledby="h-homes">
    <h2 id="h-homes"><span class="dot" aria-hidden="true"></span>Homes</h2>
    <div class="three">
      <div class="homes-k">
        <p class="big">{money(house["median_12mo"])}</p>
        <p class="per">median house, last 12 months · {n(house["count_12mo"])} sales</p>
        <p class="prev">{money(house["median_prev_12mo"])} the 12 months before ({n(house["count_prev_12mo"])} sales)</p>
        <p class="big b2">{money(condo["median_12mo"])}</p>
        <p class="per">median condo · {n(condo["count_12mo"])} sales</p>
        <p class="prev">{money(condo["median_prev_12mo"])} the 12 months before ({n(condo["count_prev_12mo"])} sales)</p>
      </div>
      <figure class="chart-fig">
        <figcaption>Median house price by month <span>in $ thousands</span></figcaption>
        {chart}
        <table class="sr-only"><caption>Median house price by month</caption><tr><th>Month</th><th>Median</th><th>Sales</th></tr>{chart_table}</table>
        <p class="note">Houses only. Months with fewer than 3 sales have no median. Last 60 days: {money(l60["median"])} median from {l60["count"]} sales, ${l60["median_ppsf"]} per sq ft.</p>
      </figure>
      <div>
        <h3 class="sub">Recent sales</h3>
        <ol class="sales" role="list">{sales_rows}</ol>
        <p class="foot"><a href="{BASE}/homes/">All sales and how we count them</a></p>
      </div>
    </div>
  </section>

  <div class="wrap two-wide">
    <section id="trees" class="stop" aria-labelledby="h-trees">
      <h2 id="h-trees"><span class="dot green" aria-hidden="true"></span>Street trees</h2>
      <p class="big green-t">{n(trees["total"])}</p>
      <p class="per">street trees in {trees["species"]} species · {trees["planted_5y"]} planted in the last 5 years · {trees["empty_boxes"]} empty boxes ready to plant</p>
      <ul class="bars green" role="list">{species_rows}</ul>
      {f'<p class="foot">Biggest: a {e(bigtree["species"].lower())} on the {e(bigtree["block"])}, {bigtree["dbh_in"]} inches across at chest height.</p>' if bigtree else ""}
    </section>

    <section id="then" class="stop then" aria-labelledby="h-then">
      <h2 id="h-then"><span class="dot" aria-hidden="true"></span>Then</h2>
      <p class="year" aria-hidden="true">{fb["year"]}</p>
      <p class="then-lead">{then_sentence}</p>
      <h3 class="minor">This week in {arch["week_start"][:4]}: the {e(arch["paper"])}, {e(week_label)}</h3>
      <ul class="clips" role="list">{clips_html}</ul>
      <p class="note">Machine-read text from scanned pages at the Library of Congress; misspellings are the scanner's.</p>
    </section>
  </div>

  <section id="reps" class="wrap stop" aria-labelledby="h-reps">
    <h2 id="h-reps"><span class="dot" aria-hidden="true"></span>Your representatives</h2>
    <p class="dek">{NAME} spans {len(d["smds"])} single-member districts in {len(ancs)} Advisory Neighborhood Commissions. Meetings and commissioners are on each commission's site.</p>
    <ul class="reps" role="list">{reps_html}</ul>
  </section>

  <section id="email" class="band brick" aria-labelledby="h-email">
    <div class="wrap email">
      <h2 id="h-email">{NAME}, once a week.</h2>
      <p>Headlines, what's coming up and what changed on the permits map. One email every week, no ads in the data.</p>
      <form action="{BASE}/subscribe/" method="get">
        <label for="em" class="sr-only">Email address</label>
        <input id="em" type="email" name="email" required placeholder="you@example.com" autocomplete="email">
        <button type="submit">Subscribe</button>
      </form>
    </div>
  </section>
</main>

<footer class="foot-site">
  <div class="wrap">
    <p class="indep"><strong>An independent project.</strong> Not affiliated with the DC Government, any Advisory Neighborhood Commission or any Business Improvement District.</p>
    <p>Data from Open Data DC (CC BY 4.0), the DC Office of Tax and Revenue, DDOT and the Library of Congress. Crime figures are preliminary MPD counts. <a href="{BASE}/about/">About the data</a> · <a href="{BASE}/permits.xml">Permits RSS</a></p>
    <nav aria-label="Other DC neighborhood sites"><h2>More DC neighborhoods</h2><ul role="list">{other_html}</ul></nav>
  </div>
</footer>
</body>
</html>
"""
(HERE / "index.html").write_text(page, encoding="utf-8")
print(f"wrote index.html ({len(page):,} bytes); {len(events)} events, {len(mapped)} mapped permits, tally {tally}")
