"""Build the 'Broadsheet' front page for Petworth from the nightly data file.

    python build.py            -> writes index.html next to this script

Every number on the page comes from site/src/data/petworth.json.
"""
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "site" / "src" / "data" / "petworth.json"
d = json.loads(DATA.read_text(encoding="utf-8"))

E = lambda s: escape(str(s), quote=True)
BASE = "/" + d["slug"]

# ---------------------------------------------------------------- formatting
AP_MONTH = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
FULL_MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
              "October", "November", "December"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def ap_date(dt, year=False):
    s = f"{AP_MONTH[dt.month - 1]} {dt.day}"
    return s + f", {dt.year}" if year else s


def n(x):
    return f"{x:,}"


def money_k(x):
    if x >= 1_000_000:
        return f"${x / 1_000_000:.2f}M".replace(".00M", "M")
    k = x / 1000
    return f"${k:,.0f}K" if abs(k - round(k)) < 0.05 else f"${k:,.1f}K"


def pct_ok(a, b):
    """Brief: percentages only when both counts are 100 or more."""
    return a >= 100 and b >= 100


def ap_time(s):
    def one(t):
        t = t.strip()
        m = re.match(r"(\d+):(\d+)\s*([AP])M", t, re.I)
        if not m:
            return t
        h, mi, ap = int(m[1]), m[2], m[3].lower()
        return f"{h}{'' if mi == '00' else ':' + mi} {ap}.m."
    parts = [one(p) for p in re.split(r"\s+-\s+", s or "")]
    if len(parts) == 2 and parts[0][-4:] == parts[1][-4:]:
        parts[0] = parts[0][:-5]
    return "–".join(parts)


def title_addr(a):
    a = re.sub(r"\s+\d{5}$", "", a.strip())
    out = []
    for w in a.split():
        if w in ("NW", "NE", "SW", "SE"):
            out.append(w)
        elif re.match(r"^\d+(ST|ND|RD|TH)$", w):
            out.append(w.lower())
        else:
            out.append(w.capitalize())
    s = " ".join(out)
    for full, short in (("Street", "St"), ("Avenue", "Ave"), ("Place", "Pl"), ("Road", "Rd")):
        s = re.sub(rf"\b{full}\b", short, s)
    return s


def title_block(b):
    m = re.match(r"(\d+ block of )(.*)", b)
    if not m:
        return b
    return m[1] + title_addr(m[2])


def clip(s, k):
    s = re.sub(r"\s+", " ", s or "").strip()
    if len(s) <= k:
        return s
    cut = s[:k].rsplit(" ", 1)[0].rstrip(",;:.")
    return cut + "…"


# ---------------------------------------------------------------- the edition date
gen = datetime.fromisoformat(d["generated_at"].replace("Z", "+00:00"))
# Eastern time: EDT through the first Sunday of November (the data is stamped 03:07Z Nov 1 = 11:07 p.m. Oct 31 EDT)
et = gen + timedelta(hours=-4 if gen < datetime(gen.year, 11, 1, 6, tzinfo=timezone.utc) else -5)
today = date.fromisoformat(d["events"]["today"])
edition_line = f"{DAYS[today.weekday()]}, {FULL_MONTH[today.month - 1]} {today.day}, {today.year}"
h12 = et.hour % 12 or 12
asof = f"{AP_MONTH[et.month - 1]} {et.day}, {h12}:{et.minute:02d} {'a.m.' if et.hour < 12 else 'p.m.'}"

# ---------------------------------------------------------------- news
items = sorted(d["news"]["items"], key=lambda x: x["published"], reverse=True)
for it in items:
    it["dt"] = datetime.fromisoformat(it["published"].replace("Z", "+00:00")).date()
recent = [it for it in items if (today - it["dt"]).days <= 30]
earlier = [it for it in items if (today - it["dt"]).days > 30]
outlets = d["news"]["outlets"]
outlets_ok = sum(1 for o in outlets if o["state"] == "ok")


def news_meta(it):
    return f'<span class="src">{E(it["source"])}</span> <span class="dot" aria-hidden="true">&middot;</span> <time datetime="{it["dt"].isoformat()}">{ap_date(it["dt"])}</time>'


def news_html():
    out = []
    pool = recent if recent else []
    lead, seconds, rest = (pool[0] if pool else None), pool[1:3], pool[3:]
    if lead:
        out.append(f'''<article class="lead-story">
  <h3 class="lead-hed"><a href="{E(lead["url"])}">{E(lead["title"])}</a></h3>
  <p class="meta">{news_meta(lead)}</p>
</article>''')
    else:
        out.append('<p class="empty">No local headlines mentioning Petworth in the last 30 days.</p>')
    if seconds:
        out.append('<div class="seconds">' + "".join(
            f'<article class="second"><h3 class="second-hed"><a href="{E(it["url"])}">{E(it["title"])}</a></h3><p class="meta">{news_meta(it)}</p></article>'
            for it in seconds) + "</div>")
    if rest:
        out.append('<ul class="briefs">' + "".join(
            f'<li><a href="{E(it["url"])}">{E(it["title"])}</a> <span class="meta">{news_meta(it)}</span></li>' for it in rest) + "</ul>")
    if earlier:
        out.append(f'<h3 class="subhead">Earlier this year</h3><ul class="briefs earlier">' + "".join(
            f'<li><a href="{E(it["url"])}">{E(it["title"])}</a> <span class="meta">{news_meta(it)}</span></li>' for it in earlier[:5]) + "</ul>")
    out.append(f'<p class="fine">Headlines that mention Petworth, from {outlets_ok} local outlets checked tonight. Each links to the outlet that published it; we never copy articles. <a href="{BASE}/news/">All news</a></p>')
    return "\n".join(out)


# ---------------------------------------------------------------- events
ev_end = today + timedelta(days=14)
events = [e for e in d["events"]["events"] if today <= date.fromisoformat(e["date"]) <= ev_end]
events.sort(key=lambda e: (e["date"], e.get("time") or ""))


def events_html():
    if not events:
        return '<p class="empty">Nothing on the calendars we read for the next two weeks.</p>'
    out = ['<ol class="cal">']
    for e in events:
        dt = date.fromisoformat(e["date"])
        rel = "Today" if dt == today else "Tomorrow" if dt == today + timedelta(days=1) else DAYS[dt.weekday()][:3]
        out.append(f'''<li class="cal-item">
  <p class="cal-date"><span class="cal-rel">{rel}</span><span class="cal-day">{AP_MONTH[dt.month - 1]} {dt.day}</span></p>
  <div class="cal-body"><h3 class="cal-hed"><a href="{E(e["url"])}">{E(e["title"])}</a></h3>
  <p class="meta">{E(ap_time(e.get("time") or ""))}<span class="dot" aria-hidden="true"> &middot; </span>{E(e["place"])}</p></div>
</li>''')
    out.append("</ol>")
    links = d["events"].get("links") or []
    if links:
        out.append('<p class="also"><span class="also-k">Also check</span> ' + ", ".join(
            f'<a href="{E(l["url"])}">{E(l["name"])}</a>' for l in links) + "</p>")
    return "\n".join(out)


# ---------------------------------------------------------------- 311 reading
LABEL = {
    "Bulk Collection": "Bulk trash pickups",
    "Scheduled Yard Waste": "Yard-waste pickups",
    "DC Health Rodent & Vector Control": "Rodent complaints",
    "Parking Enforcement": "Parking enforcement calls",
    "Illegal Dumping": "Illegal-dumping reports",
    "Trash Collection - Missed": "Missed-trash reports",
    "Sanitation Enforcement": "Sanitation enforcement calls",
    "DOEE - LIHEAP": "Heating-bill help (LIHEAP) requests",
    "Dead Animal Collection": "Dead-animal pickups",
    "Residential Parking Permit Violation": "Residential parking complaints",
    "Container Removal": "Container removals",
    "Recycling Collection - Missed": "Missed-recycling reports",
    "Public Space Litter Can-Collection": "Public litter-can requests",
    "Rat Replacement Containers": "Rat-proof can requests",
    "Tree Inspection": "Tree inspections",
    "Supercan - Delivery": "Supercan deliveries",
    "Trash Cart Repair": "Trash-cart repairs",
    "Alley Cleaning": "Alley cleanings",
}
SHORT = {
    "DC Health Rodent & Vector Control": "Rodents",
    "DOEE - LIHEAP": "Heating help (LIHEAP)",
    "Trash Collection - Missed": "Missed trash",
    "Recycling Collection - Missed": "Missed recycling",
    "Public Space Litter Can-Collection": "Litter cans",
    "Residential Parking Permit Violation": "Residential parking",
    "Rat Replacement Containers": "Rat-proof cans",
    "Supercan - Delivery": "Supercan delivery",
    "Scheduled Yard Waste": "Yard waste",
    "Bulk Collection": "Bulk trash",
}
label = lambda t: LABEL.get(t, t)
short = lambda t: SHORT.get(t, t)

req = d["requests"]
types = [t for t in req["by_type"] if max(t["count"], t["previous"]) >= 20]


def direction(c, p):
    if p == 0:
        return "rising" if c > 0 else "steady"
    ch = (c - p) / p
    return "steady" if abs(ch) <= 0.05 else "rising" if ch > 0 else "easing"


for t in types:
    t["dir"] = direction(t["count"], t["previous"])
    t["chg"] = t["count"] - t["previous"]
tally = {k: sum(1 for t in types if t["dir"] == k) for k in ("rising", "easing", "steady")}
risers = sorted([t for t in types if t["chg"] > 0 and t["previous"] >= 20], key=lambda t: -t["chg"])
fallers = sorted([t for t in types if t["chg"] < 0], key=lambda t: t["chg"])
newcomers = [t for t in types if t["previous"] == 0 and t["count"] > 0]
tot, ptot = req["total"], req["previous_total"]
days = d["windows"]["requests_days"]

if risers:
    lt = risers[0]
    if tot < ptot:
        reading_hed = f"{label(lt['type'])} climb as 311 calls fall"
        lede = (f"{label(lt['type'])} rose to {n(lt['count'])} in the past {days} days, up from {n(lt['previous'])}, "
                f"even as total 311 requests in Petworth fell from {n(ptot)} to {n(tot)}.")
    else:
        reading_hed = f"{label(lt['type'])} lead a rise in 311 calls"
        lede = (f"{label(lt['type'])} rose to {n(lt['count'])} in the past {days} days, up from {n(lt['previous'])}, "
                f"as total 311 requests in Petworth rose from {n(ptot)} to {n(tot)}.")
elif fallers:
    lt = fallers[0]
    reading_hed = f"{label(lt['type'])} ease"
    lede = (f"{label(lt['type'])} fell to {n(lt['count'])} in the past {days} days, down from {n(lt['previous'])}; "
            f"total 311 requests went from {n(ptot)} to {n(tot)}.")
else:
    reading_hed, lede = "A steady month for 311", f"Total 311 requests in Petworth: {n(tot)}, against {n(ptot)} the {days} days before."

second = []
if fallers:
    f0 = fallers[0]
    second.append(f"The biggest drop was in {label(f0['type']).lower()}, down to {n(f0['count'])} from {n(f0['previous'])}.")
for t in newcomers[:1]:
    second.append(f"{label(t['type'])} appeared this period: {n(t['count'])}, up from none.")


def arrow(dirn):
    return {"rising": "▲", "easing": "▼", "steady": "–"}[dirn]


def reading_html():
    rows = "".join(
        f'<li><span class="rt">{E(short(t["type"]))}</span><span class="rv num">{n(t["count"])}</span>'
        f'<span class="rd num {t["dir"]}"><span aria-hidden="true">{arrow(t["dir"])}</span> {"+" if t["chg"] > 0 else "−" if t["chg"] < 0 else ""}{n(abs(t["chg"]))}</span></li>'
        for t in sorted(types, key=lambda t: -abs(t["chg"]))[:6])
    return f'''<h3 class="reading-hed">{E(reading_hed)}</h3>
<p class="lede"><span class="dateline">Petworth, {ap_date(today)}&nbsp;&mdash;</span> {E(lede)}</p>
<p class="lede2">{E(" ".join(second))}</p>
<div class="tally" role="group" aria-label="Of the {len(types)} most common 311 request types: {tally['rising']} rising, {tally['easing']} easing, {tally['steady']} steady">
  <p class="tally-k">Of the {len(types)} most common request types</p>
  <p class="tally-v"><span><b class="num">{tally['rising']}</b> rising</span><span><b class="num">{tally['easing']}</b> easing</span><span><b class="num">{tally['steady']}</b> steady</span></p>
  <p class="tally-bar" aria-hidden="true">{''.join(f'<i class="{t["dir"]}"></i>' for t in sorted(types, key=lambda t: ("rising", "steady", "easing").index(t["dir"])))}</p>
</div>
<p class="tally-k">Largest moves, last {days} days</p>
<ul class="reading-list">{rows}</ul>
<p class="fine">Each type compares the last {days} days with the {days} days before; within 5% counts as steady. <a href="{BASE}/streets/#requests">All 311 types</a></p>'''


# ---------------------------------------------------------------- measures band
crime = d["crime"]
house = d["homes"]["house"]
permits_all = d["permits"]


def pair_bars(now, prev, lab_now, lab_prev, fmt=n):
    m = max(now, prev) or 1
    return f'''<div class="pair" aria-hidden="true">
  <div class="pb"><span class="pl">{lab_now}</span><span class="bar"><i style="width:{now / m * 100:.1f}%"></i></span><span class="pv num">{fmt(now)}</span></div>
  <div class="pb prev"><span class="pl">{lab_prev}</span><span class="bar"><i style="width:{prev / m * 100:.1f}%"></i></span><span class="pv num">{fmt(prev)}</span></div>
</div>'''


def change_txt(now, prev, unit=""):
    dlt = now - prev
    s = ("+" if dlt > 0 else "−" if dlt < 0 else "±") + n(abs(dlt)) + unit
    if pct_ok(now, prev) and prev:
        s += f" ({'+' if dlt > 0 else '−' if dlt < 0 else ''}{abs(dlt) / prev * 100:.0f}%)"
    return s


BIG_GROUPS = ("Demolition", "New construction", "Additions")


def inside(lon, lat, ring):
    c = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


rings = d["boundary"]["rings"]
permits = [p for p in permits_all if p.get("lat") and p.get("lon") and any(inside(p["lon"], p["lat"], r) for r in rings)]
big = sorted([p for p in permits if p["group"] in BIG_GROUPS], key=lambda p: p["issued"], reverse=True)
groups = {}
for p in permits:
    groups[p["group"]] = groups.get(p["group"], 0) + 1
GROUP_ORDER = ["Demolition", "New construction", "Additions", "Renovation & repair",
               "Electrical, plumbing & mechanical", "Home businesses", "Minor work"]
group_list = [(g, groups[g]) for g in GROUP_ORDER if g in groups] + [(g, c) for g, c in groups.items() if g not in GROUP_ORDER]
n_new = groups.get("New construction", 0)
pdays = d["windows"]["permits_days"]


def measures_html():
    hm, hp = house["median_12mo"], house["median_prev_12mo"]
    house_chg = hm - hp
    house_pct = f" ({'+' if house_chg > 0 else '−'}{abs(house_chg) / hp * 100:.0f}%)" if pct_ok(house["count_12mo"], house["count_prev_12mo"]) else ""
    big_n = len(big)
    seg = "".join(f'<i class="g{i}" style="flex:{c}" title="{E(g)}: {c}"></i>' for i, (g, c) in enumerate(group_list))
    return f'''<div class="measure">
  <h3 class="m-k">311 requests</h3>
  <p class="m-v num">{n(tot)}</p>
  <p class="m-c">{change_txt(tot, ptot)} vs. the {days} days before</p>
  {pair_bars(tot, ptot, f"Last {days} days", "Before")}
  <p class="m-n">{n(req["open"])} still open tonight.</p>
</div>
<div class="measure">
  <h3 class="m-k">Crime reports</h3>
  <p class="m-v num">{n(crime["total"])}</p>
  <p class="m-c">{n(crime["previous_total"])} in the {days} days before</p>
  {pair_bars(crime["total"], crime["previous_total"], f"Last {days} days", "Before")}
  <p class="m-n">Counts this small swing month to month. Counts only, never mapped. <a href="{BASE}/about/#crime">How we count</a></p>
</div>
<div class="measure">
  <h3 class="m-k">Median house price</h3>
  <p class="m-v num">{money_k(hm)}</p>
  <p class="m-c">{'−' if house_chg < 0 else '+'}{money_k(abs(house_chg))}{house_pct} vs. the year before</p>
  {pair_bars(hm, hp, "Last 12 mo.", "Year before", money_k)}
  <p class="m-n">From {n(house["count_12mo"])} house sales, against {n(house["count_prev_12mo"])} the year before.</p>
</div>
<div class="measure">
  <h3 class="m-k">Building permits</h3>
  <p class="m-v num">{n(len(permits))}</p>
  <p class="m-c">issued in the last {pdays} days</p>
  <p class="stack" role="img" aria-label="Permits by type: {E(', '.join(f'{g} {c}' for g, c in group_list))}">{seg}</p>
  <p class="m-n">{big_n} bigger project{'s' if big_n != 1 else ''} ({groups.get('Additions', 0)} additions, {groups.get('Demolition', 0)} demolition, {n_new} new buildings). No prior-period count in tonight&rsquo;s data.</p>
</div>'''


# ---------------------------------------------------------------- permit map
def map_svg():
    ring = rings[0]
    lons = [p[0] for r in rings for p in r]
    lats = [p[1] for r in rings for p in r]
    lon0, lon1, lat0, lat1 = min(lons), max(lons), min(lats), max(lats)
    k = math.cos(math.radians((lat0 + lat1) / 2))
    W = 640
    pad = 18
    sx = (W - 2 * pad) / ((lon1 - lon0) * k)
    H = round((lat1 - lat0) * sx + 2 * pad)

    def xy(lon, lat):
        return pad + (lon - lon0) * k * sx, pad + (lat1 - lat) * sx

    paths = []
    for r in rings:
        pts = [xy(*p) for p in r]
        paths.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    # scale bar: 500 m
    m_per_deg = 111_320
    bar_px = 500 / (m_per_deg) * sx
    small = []
    for p in permits:
        if p["group"] in BIG_GROUPS:
            continue
        x, y = xy(p["lon"], p["lat"])
        small.append(f'<g transform="translate({x:.1f},{y:.1f})"><circle r="3.6" class="pm"/><title>{E(title_addr(p["address"]))}: {E(p["group"])}</title></g>')
    bigm = []
    for i, p in enumerate(big, 1):
        x, y = xy(p["lon"], p["lat"])
        bigm.append(f'<g class="pb-m" transform="translate({x:.1f},{y:.1f})"><g class="mk"><circle r="11"/><text text-anchor="middle" dominant-baseline="central">{i}</text></g><title>{i}. {E(title_addr(p["address"]))}: {E(p["group"])}</title></g>')
    return f'''<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-labelledby="map-t map-d">
<title id="map-t">Map of building permits in Petworth, last {pdays} days</title>
<desc id="map-d">{len(permits)} permits inside the Petworth boundary. {len(big)} bigger projects are numbered to match the list beside the map.</desc>
<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" class="hatch"/></pattern></defs>
<path d="{' '.join(paths)}" class="bnd-fill"/>
<path d="{' '.join(paths)}" class="bnd"/>
{''.join(small)}
{''.join(bigm)}
<g class="scale" transform="translate({pad},{H - 10})"><line x1="0" y1="0" x2="{bar_px:.1f}" y2="0"/><line x1="0" y1="-4" x2="0" y2="0"/><line x1="{bar_px:.1f}" y1="-4" x2="{bar_px:.1f}" y2="0"/><text x="{bar_px + 6:.1f}" y="3">500 m</text></g>
<g class="north" transform="translate({W - pad - 6},{H - 30})"><path d="M0,-9 L5,5 L0,2 L-5,5Z"/><text y="18" text-anchor="middle">N</text></g>
</svg>'''


def projects_html():
    if not big:
        return '<p class="empty">No demolitions, new buildings or additions in the last 30 days.</p>'
    cutoff = today - timedelta(days=7)
    out = ['<ol class="projects">']
    for i, p in enumerate(big, 1):
        dt = datetime.fromisoformat(p["issued"].replace("Z", "+00:00")).date()
        new = ' <span class="flag">New this week</span>' if dt > cutoff else ""
        grp = {"Additions": "Addition", "Demolition": "Demolition", "New construction": "New building"}.get(p["group"], p["group"])
        out.append(f'''<li><span class="pn num" aria-hidden="true">{i}</span><div>
<h3 class="p-hed">{E(title_addr(p["address"]))}</h3>
<p class="p-k">{grp} &middot; {ap_date(dt)}{new}</p>
<p class="p-w">{E(clip(p["work"], 150)) or "No description filed."}</p></div></li>''')
    out.append("</ol>")
    return "\n".join(out)


def groups_html():
    m = max(c for _, c in group_list)
    return '<ul class="hbars">' + "".join(
        f'<li><span class="hl"><i class="sw g{i}" aria-hidden="true"></i>{E(g)}</span><span class="hb"><i style="width:{c / m * 100:.1f}%"></i></span><span class="hv num">{c}</span></li>'
        for i, (g, c) in enumerate(group_list)) + "</ul>"


# ---------------------------------------------------------------- curb
curb = d["streets"]["curb"]


def curb_html():
    up = curb["upcoming"]
    if not up:
        return '<p class="empty">No curb permits start in the next seven days.</p>'
    rows = "".join(
        f'<tr><td class="num">{ap_date(date.fromisoformat(c["start"]))}</td><td>{E(title_block(c["block"]))}</td><td>{E(c["type"])}</td><td class="num r">{n(c["ft"])} ft</td></tr>'
        for c in up[:7])
    more = len(up) - 7
    return f'''<table class="tbl curb">
<caption>Curb permits starting in the next 7 days</caption>
<thead><tr><th scope="col">Starts</th><th scope="col">Where</th><th scope="col">Why</th><th scope="col" class="r">Curb</th></tr></thead>
<tbody>{rows}</tbody></table>
{f'<p class="fine"><a href="{BASE}/streets/#curb">{more} more starting this week</a></p>' if more > 0 else ''}'''


# ---------------------------------------------------------------- homes
homes = d["homes"]


def months_svg():
    bm = homes["by_month"]
    vals = [m["median"] for m in bm if m["median"]]
    top = max(vals) if vals else 1
    W, H, gap = 300, 120, 4
    bw = (W - gap * (len(bm) - 1)) / len(bm)
    out = []
    for i, m in enumerate(bm):
        x = i * (bw + gap)
        mo = int(m["month"][5:])
        lab = FULL_MONTH[mo - 1][0]
        if m["median"]:
            h = m["median"] / top * (H - 34)
            out.append(f'<rect x="{x:.1f}" y="{H - 16 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" class="mb"><title>{FULL_MONTH[mo - 1]} {m["month"][:4]}: {money_k(m["median"])} median, {m["count"]} sales</title></rect>')
        else:
            out.append(f'<rect x="{x:.1f}" y="{H - 22:.1f}" width="{bw:.1f}" height="6" class="mb-na"><title>{FULL_MONTH[mo - 1]} {m["month"][:4]}: fewer than 3 sales so far</title></rect>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{H - 3}" text-anchor="middle" class="ml">{lab}</text>')
    hi = max(bm, key=lambda m: m["median"] or 0)
    lo = min((m for m in bm if m["median"]), key=lambda m: m["median"])
    first = bm[0]["month"]
    last = bm[-1]["month"]
    desc = (f"Monthly median house price, {FULL_MONTH[int(first[5:]) - 1]} {first[:4]} to {FULL_MONTH[int(last[5:]) - 1]} {last[:4]}. "
            f"High {money_k(hi['median'])} in {FULL_MONTH[int(hi['month'][5:]) - 1]}, low {money_k(lo['median'])} in {FULL_MONTH[int(lo['month'][5:]) - 1]}.")
    return f'<svg class="months" viewBox="0 0 {W} {H}" role="img" aria-label="{E(desc)}">{"".join(out)}</svg>', hi, lo


def homes_html():
    svg, hi, lo = months_svg()
    sales = sorted(homes["recent_sales"], key=lambda s: s["date"], reverse=True)[:5]
    rows = "".join(
        f'<tr><td>{E(s["address"])}<span class="sub">{s["beds"]} bd &middot; {n(s["sqft"])} sq ft</span></td><td class="num">{ap_date(date.fromisoformat(s["date"]))}</td><td class="num r">{money_k(s["price"])}</td></tr>'
        for s in sales)
    condo = homes["condo"]
    l60 = homes["last_60d"]
    aa = homes["above_assessment_12mo"]
    return f'''<p class="big-fig"><span class="num">{money_k(house["median_12mo"])}</span> median house price, last 12 months</p>
<figure class="fig">{svg}
<figcaption>Median by month, houses only. Months with fewer than 3 sales show a stub; {FULL_MONTH[int(homes["by_month"][-1]["month"][5:]) - 1]} is still in progress.</figcaption></figure>
<dl class="facts">
<div><dt>Last 60 days</dt><dd><span class="num">{money_k(l60["median"])}</span> from {l60["count"]} sales, {n(l60["median_ppsf"])} $/sq ft</dd></div>
<div><dt>Condos, 12 mo.</dt><dd><span class="num">{money_k(condo["median_12mo"])}</span> from {condo["count_12mo"]} sales</dd></div>
<div><dt>Above assessment</dt><dd>{aa["n"]} of {aa["of"]} sales</dd></div>
</dl>
<table class="tbl sales"><caption>Recent sales</caption>
<thead><tr><th scope="col">Address</th><th scope="col">Date</th><th scope="col" class="r">Price</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="fine"><a href="{BASE}/homes/#recent">Every recent sale</a></p>'''


# ---------------------------------------------------------------- streets
trees = d["streets"]["trees"]


def streets_html():
    sp = trees["top_species"][:5]
    m = sp[0]["count"]
    sp_rows = "".join(
        f'<li><span class="hl">{E(s["name"])}</span><span class="hb"><i style="width:{s["count"] / m * 100:.1f}%"></i></span><span class="hv num">{n(s["count"])}</span></li>' for s in sp)
    bigt = trees["biggest"][0]
    top311 = sorted(req["by_type"], key=lambda t: -t["count"])[:6]
    rows = "".join(
        f'<tr><td>{E(short(t["type"]))}</td><td class="num r">{n(t["count"])}</td><td class="num r muted">{n(t["previous"])}</td></tr>'
        for t in top311)
    return f'''<p class="big-fig"><span class="num">{n(trees["total"])}</span> street trees, {trees["species"]} species</p>
<p class="body">{n(trees["planted_5y"])} were planted in the last five years, and {trees["empty_boxes"]} tree boxes stand empty and ready to plant. The largest is a {E(bigt["species"].lower())} on the {E(title_block(bigt["block"]))}, {bigt["dbh_in"]:.0f} inches across the trunk.</p>
<h3 class="subhead">Most common</h3>
<ul class="hbars">{sp_rows}</ul>
<p class="fine"><a href="https://311.dc.gov/">Ask DC to plant a tree on your block</a> &middot; <a href="{BASE}/streets/#trees">Tree details</a></p>
<table class="tbl t311"><caption>Top 311 requests</caption>
<thead><tr><th scope="col">Type</th><th scope="col" class="r">Last {days} d</th><th scope="col" class="r">Before</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="fine"><a href="{BASE}/streets/#requests">All request types</a> &middot; <a href="{BASE}/streets/#service">How fast DC responds</a></p>'''


# ---------------------------------------------------------------- then
hist = d["history"]
fb = hist["buildings"]["featured_block"]
arch = hist["archive"]


def ocr_noise(t):
    toks = t.split()
    bad = sum(1 for w in toks if re.search(r"[a-z][A-Z]|\d[A-Za-z]|[A-Za-z]\d|[,.][a-z]{1,3}[,.]", w))
    return bad / max(1, len(toks))


def then_html():
    lp = fb["largest_permit"]
    fb_txt = (f"In {fb['year']}, {fb['builder']} built {fb['buildings']} buildings on the {fb['block']} under "
              f"{fb['permits']} permits. The largest permit covered {lp['buildings']} buildings at an estimated "
              f"${n(lp['cost'])} in total.")
    clips = sorted(arch["clips"], key=lambda c: ocr_noise(c["text"]))[:3]
    clips.sort(key=lambda c: c["date"])
    cl = "".join(
        f'<blockquote class="clip"><p>&ldquo;{E(c["text"])}&rdquo;</p><footer><a href="{E(c["url"])}">{E(arch["paper"])}, {ap_date(date.fromisoformat(c["date"]), True)}, page {c["page"]}</a></footer></blockquote>'
        for c in clips)
    wl = arch["week_label"].replace("�", "–")
    by_dec = hist["buildings"]["by_decade"]
    mx = max(x["count"] for x in by_dec)
    dec = "".join(
        f'<li><span class="hl num">{x["decade"]}s</span><span class="hb"><i style="width:{x["count"] / mx * 100:.1f}%"></i></span><span class="hv num">{n(x["count"])}</span></li>' for x in by_dec)
    return f'''<p class="then-year num">{fb["year"]}</p>
<h3 class="then-hed">{E(fb["block"])}: {fb["buildings"]} buildings, one builder</h3>
<p class="body">{E(fb_txt)}</p>
<h3 class="subhead">Petworth, built by decade</h3>
<ul class="hbars">{dec}</ul>
<p class="fine">{n(hist["buildings"]["records"])} building permits on record, {hist["buildings"]["year_min"]}&ndash;{hist["buildings"]["year_max"]}. <a href="{BASE}/then/">How Petworth was built</a></p>
<h3 class="subhead">This week, 100 years ago</h3>
<p class="fine">{E(wl)}, from the {E(arch["paper"])}</p>
{cl}
<p class="fine">Machine-read text from scanned pages at the Library of Congress; spelling errors are the scanner&rsquo;s. <a href="{BASE}/then/#archive">More clippings</a></p>'''


# ---------------------------------------------------------------- representatives
def reps_html():
    by = {}
    for s in d["smds"]:
        by.setdefault(s["anc"], {"url": s["url"], "smds": []})["smds"].append(s["smd"])
    return "".join(
        f'<div class="anc"><h3 class="anc-hed"><a href="{E(v["url"])}">ANC {E(a)}</a></h3><p class="smds">{" ".join(f"<span>{E(x)}</span>" for x in v["smds"])}</p></div>'
        for a, v in by.items())


SISTERS = [("Tenleytown", "tenleytown.org"), ("Adams Morgan", "adamsmorgan.org"), ("Friendship Heights", "friendshipheights.org"),
           ("Capitol Hill", "capitolhilldc.org"), ("Columbia Heights", "columbiaheights.net"), ("Georgetown", "georgetowndc.org"),
           ("Chevy Chase", "chevychasedc.net"), ("Anacostia", "anacostiadc.net"), ("Cleveland Park", "clevelandpark.org"),
           ("Dupont Circle", "dupontcircledc.net"), ("H Street NE", "hstreet.net"), ("Navy Yard", "navyyarddc.net")]

# ---------------------------------------------------------------- page
CSS = r"""
:root{
  --paper:#ffffff; --ink:#15171a; --ink2:#464c53; --ink3:#6b7178; --hair:#d9dcdf; --rule:#15171a;
  --tint:#f1f3f4; --accent:#a8261b; --accent-ink:#ffffff;
  --g0:#15171a; --g1:#a8261b; --g2:#5d6670; --g3:#8f979f; --g4:#b9bfc5; --g5:#d4d8dc; --g6:#e6e8ea;
  --serif:"Newsreader",Georgia,"Times New Roman",serif;
  --sans:"Archivo","Arial Narrow",Arial,sans-serif;
  --gut:clamp(16px,3vw,32px);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:18px;line-height:1.5;font-optical-sizing:auto}
a{color:inherit;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.18em;text-decoration-color:var(--ink3)}
a:hover{color:var(--accent);text-decoration-color:var(--accent)}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2,h3,p,ul,ol,dl,dd,figure,blockquote{margin:0;padding:0}
ul,ol{list-style:none}
.num{font-family:var(--sans);font-variant-numeric:tabular-nums lining-nums;font-stretch:90%}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:-999px;top:0;background:var(--ink);color:#fff;padding:8px 12px}
.skip:focus{left:8px;z-index:9}
.wrap{max-width:1240px;margin:0 auto;padding:0 var(--gut)}

/* top strip */
.strip{font-family:var(--sans);font-size:13px;color:var(--ink2);border-bottom:1px solid var(--hair)}
.strip .wrap{display:flex;justify-content:space-between;gap:8px 24px;flex-wrap:wrap;padding-top:8px;padding-bottom:8px}
.strip b{color:var(--ink);font-weight:600}

/* masthead */
.mast{text-align:center;padding-top:26px}
.mast-name{font-family:var(--serif);font-weight:700;font-size:clamp(58px,11vw,128px);line-height:.9;letter-spacing:-.025em;font-variation-settings:"opsz" 72}
.mast-name a{text-decoration:none}
.mast-tag{font-family:var(--serif);font-style:italic;font-size:clamp(16px,2vw,20px);color:var(--ink2);margin-top:10px}
.mast-rule{margin-top:18px;border-top:3px solid var(--rule);border-bottom:1px solid var(--rule);height:6px}
.mast-line{display:flex;justify-content:space-between;align-items:center;gap:8px 16px;flex-wrap:wrap;font-family:var(--sans);font-size:13px;letter-spacing:.06em;text-transform:uppercase;padding:9px 0;border-bottom:1px solid var(--rule)}
.mast-line nav ul{display:flex;flex-wrap:wrap;gap:4px 20px;justify-content:center}
.mast-line nav a{text-decoration:none;font-weight:600}
.mast-line nav a:hover{text-decoration:underline}

/* section heads */
.kicker{font-family:var(--sans);font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);display:flex;align-items:baseline;justify-content:space-between;gap:12px;padding-top:10px;border-top:2px solid var(--rule);margin-bottom:14px}
.kicker a{color:var(--ink2);font-weight:500;letter-spacing:.04em;text-transform:none;font-size:14px}
.sec-hed{font-family:var(--serif);font-weight:600;font-size:clamp(30px,4vw,44px);line-height:1.05;letter-spacing:-.015em;margin:0 0 6px;font-variation-settings:"opsz" 60}
.sec-dek{font-style:italic;color:var(--ink2);font-size:19px;margin-bottom:22px;max-width:60ch}
.subhead{font-family:var(--sans);font-size:12.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin:22px 0 8px;padding-bottom:5px;border-bottom:1px solid var(--hair)}
.meta{font-family:var(--sans);font-size:13.5px;color:var(--ink2);margin-top:6px}
.meta .src{font-weight:600;color:var(--ink)}
.fine{font-family:var(--sans);font-size:13px;color:var(--ink2);margin-top:12px;line-height:1.45}
.empty{font-style:italic;color:var(--ink2)}
.body{font-size:17px;line-height:1.55}

/* front */
.front{display:grid;grid-template-columns:minmax(0,6fr) minmax(0,3fr) minmax(0,3fr);gap:0;margin-top:26px}
.front>section{padding:0 24px}
.front>section:first-child{padding-left:0}
.front>section:last-child{padding-right:0}
.front>section+section{border-left:1px solid var(--hair)}
.lead-hed{font-family:var(--serif);font-weight:600;font-size:clamp(30px,3.6vw,46px);line-height:1.06;letter-spacing:-.018em;font-variation-settings:"opsz" 72;text-wrap:balance}
.lead-hed a,.second-hed a,.cal-hed a,.reading-hed{text-decoration:none}
.lead-hed a:hover,.second-hed a:hover,.cal-hed a:hover{text-decoration:underline;text-decoration-thickness:2px}
.lead-story{padding-bottom:18px;border-bottom:1px solid var(--hair)}
.lead-story .meta{font-size:14.5px;margin-top:12px}
.seconds{display:grid;grid-template-columns:1fr 1fr;gap:0;border-bottom:1px solid var(--hair)}
.second{padding:16px 0 18px}
.second+.second{padding-left:20px;border-left:1px solid var(--hair);margin-left:20px}
.second-hed{font-family:var(--serif);font-weight:600;font-size:22px;line-height:1.18;letter-spacing:-.005em;text-wrap:pretty}
.briefs li{padding:11px 0;border-bottom:1px solid var(--hair);font-size:17px;line-height:1.35}
.briefs li .meta{display:block;margin-top:3px}
.briefs a{text-decoration-color:var(--hair)}
.briefs.earlier li{font-size:16px}

.cal-item{display:grid;grid-template-columns:76px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--hair)}
.cal-item:first-child{padding-top:2px}
.cal-date{font-family:var(--sans);line-height:1.15}
.cal-rel{display:block;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.cal-day{display:block;font-size:15px;font-weight:600;font-stretch:90%}
.cal-hed{font-family:var(--serif);font-weight:600;font-size:18px;line-height:1.2}
.cal-item .meta{margin-top:3px;font-size:13px}
.also{font-family:var(--sans);font-size:14px;margin-top:14px;line-height:1.5}
.also-k{display:block;font-weight:700;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink)}

.reading-hed{font-family:var(--serif);font-weight:600;font-size:25px;line-height:1.12;letter-spacing:-.01em;text-wrap:balance}
.lede{font-size:17px;line-height:1.5;margin-top:10px}
.lede2{font-size:17px;line-height:1.5;margin-top:8px}
.dateline{font-family:var(--sans);font-weight:700;font-size:12.5px;letter-spacing:.08em;text-transform:uppercase}
.tally{margin:16px 0 4px;padding:12px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--hair)}
.tally-k{font-family:var(--sans);font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);margin-top:14px}
.tally .tally-k{margin-top:0}
.tally-v{display:flex;gap:14px;font-family:var(--sans);font-size:14px;margin-top:4px;flex-wrap:wrap}
.tally-v b{font-size:26px;font-weight:600;margin-right:3px}
.tally-bar{display:flex;gap:2px;margin-top:8px;height:10px}
.tally-bar i{flex:1}
.tally-bar .rising{background:var(--ink)}
.tally-bar .steady{background:var(--g4)}
.tally-bar .easing{background:transparent;border:1.5px solid var(--ink2)}
.reading-list li{display:grid;grid-template-columns:1fr auto 64px;gap:8px;font-family:var(--sans);font-size:14px;padding:6px 0;border-bottom:1px solid var(--hair);align-items:baseline}
.rd{text-align:right;color:var(--ink2);white-space:nowrap}
.rd.rising{color:var(--ink);font-weight:600}

/* numbers band */
.band{margin-top:44px}
.measures{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-bottom:1px solid var(--rule)}
.measure{padding:4px 22px 20px}
.measure:first-child{padding-left:0}
.measure:last-child{padding-right:0}
.measure+.measure{border-left:1px solid var(--hair)}
.m-k{font-family:var(--sans);font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.m-v{font-size:52px;font-weight:600;line-height:1;margin-top:8px;letter-spacing:-.02em;font-stretch:85%}
.m-c{font-family:var(--sans);font-size:14px;color:var(--ink2);margin-top:6px}
.m-n{font-family:var(--sans);font-size:13px;color:var(--ink2);margin-top:10px;line-height:1.4}
.pair{margin-top:12px;display:grid;gap:5px}
.pb{display:grid;grid-template-columns:78px 1fr 54px;gap:8px;align-items:center;font-family:var(--sans);font-size:12px;color:var(--ink2)}
.pb .bar{height:9px;background:var(--g6)}
.pb .bar i{display:block;height:100%;background:var(--ink)}
.pb.prev .bar i{background:var(--g3)}
.pv{text-align:right;color:var(--ink);font-size:13px}
.stack{display:flex;height:22px;margin-top:14px;gap:2px}
.stack i{display:block;min-width:3px}
.g0{background:var(--g0)}.g1{background:var(--accent)}.g2{background:var(--g2)}.g3{background:var(--g3)}.g4{background:var(--g4)}.g5{background:var(--g5)}.g6{background:var(--g6)}

/* block section */
.sec{margin-top:56px}
.block-grid{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:0 36px}
.map{display:block;width:100%;height:auto;background:var(--tint)}
.bnd-fill{fill:#fff}
.bnd{fill:none;stroke:var(--ink);stroke-width:1.6;stroke-linejoin:round}
.pm{fill:var(--g3);stroke:#fff;stroke-width:1}
.pb-m circle{fill:var(--accent);stroke:#fff;stroke-width:2}
.pb-m text{fill:#fff;font:700 12px var(--sans)}
.scale line{stroke:var(--ink);stroke-width:1.5}
.scale text,.north text{font:600 11px var(--sans);fill:var(--ink)}
.north path{fill:var(--ink)}
.map-key{display:flex;gap:18px;flex-wrap:wrap;font-family:var(--sans);font-size:13px;color:var(--ink2);margin-top:10px}
.map-key i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
.projects li{display:grid;grid-template-columns:30px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--hair)}
.projects li:first-child{padding-top:0}
.pn{display:inline-flex;width:24px;height:24px;border-radius:50%;background:var(--accent);color:#fff;font-size:13px;font-weight:700;align-items:center;justify-content:center}
.p-hed{font-family:var(--serif);font-weight:600;font-size:19px;line-height:1.2}
.p-k{font-family:var(--sans);font-size:12.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--ink2);margin-top:3px}
.flag{color:var(--accent);font-weight:700}
.p-w{font-size:15.5px;line-height:1.45;margin-top:5px;color:var(--ink)}
.under{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:0 36px;margin-top:36px}
.curb-lede{font-size:21px;line-height:1.4}
.curb caption{margin-top:22px}

.hbars li{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr) 40px;gap:10px;align-items:center;font-family:var(--sans);font-size:13.5px;padding:4px 0}
.hl{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hb{height:10px;background:var(--g6)}
.hb i{display:block;height:100%;background:var(--ink)}
.hv{text-align:right}
.sw{display:inline-block;width:10px;height:10px;margin-right:7px;vertical-align:-1px}

.tbl{width:100%;border-collapse:collapse;font-family:var(--sans);font-size:14px}
.tbl caption{text-align:left;font-size:12.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:0 0 5px;margin-top:22px;border-bottom:1px solid var(--rule)}
.tbl caption.sr{position:absolute}
.tbl th{font-size:11.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);text-align:left;padding:7px 8px 5px 0;border-bottom:1px solid var(--hair)}
.tbl td{padding:8px 8px 8px 0;border-bottom:1px solid var(--hair);vertical-align:top}
.tbl .r{text-align:right;padding-right:0}
.tbl .muted{color:var(--ink2)}
.tbl .sub{display:block;font-size:12.5px;color:var(--ink2)}
.curb td:first-child{white-space:nowrap}

/* three columns */
.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;margin-top:56px}
.three>section{padding:0 24px}
.three>section:first-child{padding-left:0}
.three>section:last-child{padding-right:0}
.three>section+section{border-left:1px solid var(--hair)}
.three .sec-hed{font-size:32px}
.big-fig{font-size:17px;line-height:1.35}
.big-fig .num{display:block;font-size:48px;font-weight:600;line-height:1;letter-spacing:-.02em;font-stretch:85%;margin-bottom:4px}
.fig{margin:16px 0 0}
.months{display:block;width:100%;height:auto}
.mb{fill:var(--ink)}
.mb-na{fill:none;stroke:var(--g3);stroke-dasharray:2 2}
.ml{font:600 10px var(--sans);fill:var(--ink2)}
.fig figcaption{font-family:var(--sans);font-size:12.5px;color:var(--ink2);margin-top:6px;line-height:1.4}
.facts{margin-top:14px;border-top:1px solid var(--hair)}
.facts div{display:grid;grid-template-columns:120px 1fr;gap:10px;padding:7px 0;border-bottom:1px solid var(--hair);font-family:var(--sans);font-size:14px}
.facts dt{color:var(--ink2)}
.facts dd .num{font-weight:600}
.then-year{font-size:76px;font-weight:300;line-height:.9;letter-spacing:-.03em;color:var(--accent);font-stretch:80%}
.then-hed{font-family:var(--serif);font-weight:600;font-size:22px;line-height:1.2;margin:8px 0 8px}
.clip{margin:14px 0 0;padding:12px 14px;background:var(--tint);border-left:3px solid var(--ink)}
.clip p{font-family:var(--serif);font-style:italic;font-size:16px;line-height:1.45}
.clip footer{font-family:var(--sans);font-size:12.5px;margin-top:7px;color:var(--ink2)}

/* bottom */
.civic{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:0 36px;margin-top:56px}
.ancs{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.anc-hed{font-family:var(--serif);font-size:24px;font-weight:600}
.smds{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.smds span{font-family:var(--sans);font-size:14px;font-weight:600;border:1px solid var(--ink);padding:2px 8px}
.email{background:var(--ink);color:#fff;padding:24px 26px}
.email .sec-hed{color:#fff}
.email p{color:#d7dadd;font-size:17px}
.email form{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
.email label{display:block;width:100%;font-family:var(--sans);font-size:13px;color:#d7dadd}
.email input{flex:1 1 220px;min-width:0;font:16px var(--sans);padding:11px 12px;border:1px solid #fff;background:#fff;color:var(--ink)}
.email button{font:700 15px var(--sans);letter-spacing:.04em;padding:11px 20px;border:1px solid #fff;background:var(--accent);color:#fff;cursor:pointer}
.email button:hover{background:#8a1e15}
.email a{color:#fff}

footer.site{margin-top:64px;border-top:3px solid var(--rule);padding:22px 0 40px;font-family:var(--sans);font-size:14px;color:var(--ink2)}
footer.site .indep{font-family:var(--serif);font-size:19px;color:var(--ink);font-weight:600;max-width:60ch}
footer.site p{margin-top:10px;max-width:80ch}
.sisters{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:14px}
.sisters li{white-space:nowrap}

/* tablet */
@media (max-width:1060px){
  .front{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
  .front>.news{grid-column:1/-1;padding:0 0 28px}
  .front>section+section{border-left:0}
  .front>.events{padding-left:0}
  .front>.reading{border-left:1px solid var(--hair)!important}
  .measures{grid-template-columns:1fr 1fr}
  .measure:nth-child(3){padding-left:0;border-left:0}
  .measure:nth-child(n+3){border-top:1px solid var(--hair);padding-top:14px}
  .measure:nth-child(2){padding-right:0}
  .three{grid-template-columns:1fr 1fr}
  .three>.then{grid-column:1/-1;border-left:0!important;padding:28px 0 0;margin-top:28px;border-top:2px solid var(--rule)}
  .three>.then .kicker{border-top:0;padding-top:0}
}
/* phone */
@media (max-width:720px){
  body{font-size:17px}
  .strip .wrap{flex-direction:column;gap:2px}
  .mast{padding-top:18px}
  .mast-line{justify-content:center;letter-spacing:.04em;font-size:12px}
  .mast-line .edition{display:none}
  .mast-line nav ul{gap:4px 14px}
  .front{display:block;margin-top:18px}
  .front>section,.front>.reading{padding:0!important;border-left:0!important}
  .front>section+section{margin-top:34px}
  .seconds{grid-template-columns:1fr}
  .second+.second{padding-left:0;margin-left:0;border-left:0;border-top:1px solid var(--hair)}
  .second-hed{font-size:20px}
  .measures{grid-template-columns:1fr 1fr}
  .measure{padding:4px 12px 16px}
  .measure:nth-child(odd){padding-left:0}
  .measure:nth-child(even){padding-right:0}
  .m-v{font-size:40px}
  .pb{grid-template-columns:1fr 46px;gap:2px 6px}
  .pb .pl{grid-column:1/-1}
  .block-grid,.under,.civic{display:block}
  .block-grid aside,.under>div+div{margin-top:28px}
  .three{display:block}
  .three>section{padding:0!important;border-left:0!important;border-top:0!important;margin-top:44px}
  .three>section:first-child{margin-top:0}
  .three>.then .kicker{border-top:2px solid var(--rule);padding-top:10px}
  .civic .email{margin-top:36px;padding:20px 18px}
  .ancs{grid-template-columns:1fr 1fr}
  .tbl{font-size:13.5px}
  .curb th:nth-child(3),.curb td:nth-child(3){display:none}
  .mk{transform:scale(1.55)}
  .pm{transform:scale(1.6)}
  .scale text,.north text{font-size:18px}
}
@media (max-width:380px){
  .m-v{font-size:34px}
  .measure{padding-left:8px;padding-right:8px}
}
"""


def page():
    mkey_big = len(big)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth: news, events and what&rsquo;s changing</title>
<meta name="description" content="Independent neighborhood news and public data for Petworth, Washington, DC. Updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..700&family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,400..600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to the news</a>
<div class="strip"><div class="wrap">
  <span><b>Independent.</b> Not affiliated with the DC Government.</span>
  <span>Updated nightly from public data &middot; as of {asof}</span>
</div></div>
<header class="wrap mast">
  <p class="mast-name"><a href="{BASE}/">Petworth</a></p>
  <p class="mast-tag">News, events and what&rsquo;s changing in the neighborhood, every night</p>
  <div class="mast-rule" aria-hidden="true"></div>
  <div class="mast-line">
    <span class="edition">Northwest Washington</span>
    <nav aria-label="Sections"><ul>
      <li><a href="#news">News</a></li><li><a href="#coming-up">Coming up</a></li><li><a href="#block">Your block</a></li>
      <li><a href="#homes">Homes</a></li><li><a href="#streets">Streets</a></li><li><a href="#then">Then</a></li><li><a href="#email">Weekly email</a></li>
    </ul></nav>
    <span class="edition">{edition_line}</span>
  </div>
</header>

<main id="main" class="wrap">
<h1 class="sr">Petworth front page, {edition_line}</h1>
<div class="front">
  <section class="news" id="news" aria-labelledby="h-news">
    <h2 class="kicker" id="h-news"><span>Latest from local outlets</span><a href="{BASE}/news/">All news</a></h2>
    {news_html()}
  </section>
  <section class="events" id="coming-up" aria-labelledby="h-events">
    <h2 class="kicker" id="h-events"><span>Coming up</span><a href="{BASE}/news/#events">Calendar</a></h2>
    {events_html()}
  </section>
  <section class="reading" aria-labelledby="h-reading">
    <h2 class="kicker" id="h-reading"><span>Tonight&rsquo;s reading</span></h2>
    {reading_html()}
  </section>
</div>

<section class="band" aria-labelledby="h-band">
  <h2 class="kicker" id="h-band"><span>By the numbers &middot; this period vs. the one before</span><a href="{BASE}/about/">About the data</a></h2>
  <div class="measures">{measures_html()}</div>
</section>

<section class="sec" id="block" aria-labelledby="h-block">
  <p class="kicker"><span>On the block</span><a href="{BASE}/projects/">All projects</a></p>
  <h2 class="sec-hed" id="h-block">What&rsquo;s changing</h2>
  <p class="sec-dek">{len(permits)} building permits issued inside Petworth in the last {pdays} days. The {mkey_big} bigger ones, additions and demolitions, are numbered.</p>
  <div class="block-grid">
    <div>
      <figure>{map_svg()}</figure>
      <p class="map-key"><span><i style="background:var(--accent)"></i>Bigger project, numbered</span><span><i style="background:var(--g3)"></i>Other permit</span></p>
      <h3 class="subhead">All {len(permits)} permits by type</h3>{groups_html()}
      <p class="fine"><a href="{BASE}/permits.xml">Permits RSS feed</a></p>
    </div>
    <aside aria-label="Bigger projects">{projects_html()}</aside>
  </div>
  <div class="under">
    <div><h3 class="subhead">Curb space</h3>
      <p class="curb-lede">{n(curb["active_this_week"])} curb permits are active this week, reserving {n(curb["reserved_ft"])} feet of curb; {curb["starting_next_7d"]} more start in the next seven days.</p>
</div>
    <div>{curb_html()}</div>
  </div>
</section>

<div class="three">
  <section id="homes" aria-labelledby="h-homes">
    <p class="kicker"><span>Homes</span><a href="{BASE}/homes/">Sales and prices</a></p>
    <h2 class="sec-hed" id="h-homes">What houses sell for</h2>
    {homes_html()}
  </section>
  <section id="streets" aria-labelledby="h-streets">
    <p class="kicker"><span>Streets</span><a href="{BASE}/streets/">Streets</a></p>
    <h2 class="sec-hed" id="h-streets">Trees and 311</h2>
    {streets_html()}
  </section>
  <section id="then" class="then" aria-labelledby="h-then">
    <p class="kicker"><span>Then</span><a href="{BASE}/then/">History</a></p>
    <h2 class="sec-hed" id="h-then">How these blocks were built</h2>
    {then_html()}
  </section>
</div>

<div class="civic">
  <section aria-labelledby="h-reps">
    <p class="kicker"><span>Who represents you</span><a href="{BASE}/representatives/">All {len(d["smds"])} districts</a></p>
    <h2 class="sec-hed" id="h-reps">Your ANC</h2>
    <p class="body" style="margin-bottom:16px">Petworth spans {len(d["smds"])} single-member districts in two Advisory Neighborhood Commissions. Each district elects one commissioner.</p>
    <div class="ancs">{reps_html()}</div>
    <p class="fine"><a href="{BASE}/representatives/">Find your district and commissioner</a> &middot; <a href="{BASE}/jobs/">Jobs nearby</a></p>
  </section>
  <section class="email" id="email" aria-labelledby="h-email">
    <h2 class="sec-hed" id="h-email">The week in Petworth, by email</h2>
    <p>Headlines, what&rsquo;s coming up and what changed on the blocks, once a week. No ads in the data.</p>
    <form action="{BASE}/subscribe/" method="get">
      <label for="em">Email address</label>
      <input id="em" name="email" type="email" autocomplete="email" required>
      <button type="submit">Subscribe</button>
    </form>
    <p class="fine" style="color:#d7dadd"><a href="{BASE}/subscribe/">What&rsquo;s in it</a></p>
  </section>
</div>
</main>

<footer class="site"><div class="wrap">
  <p class="indep">An independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission or any Business Improvement District.</p>
  <p>Data comes from Open Data DC ({E(d["sources"]["license"])}) and the Library of Congress, shown as published; it may lag or contain errors. Headlines and events link to whoever published them. Crime figures are preliminary counts. Check the official source before acting on anything here. Boundary: {E(d["boundary"]["source"])}.</p>
  <p><a href="{BASE}/about/">About the data, sources and privacy</a> &middot; <a href="{BASE}/permits.xml">Permits RSS</a></p>
  <nav aria-label="Other DC neighborhoods"><ul class="sisters"><li><b>More neighborhoods:</b></li>{"".join(f'<li><a href="https://{u}/">{E(nm)}</a></li>' for nm, u in SISTERS)}</ul></nav>
</div></footer>
</body>
</html>'''


(HERE / "index.html").write_text(page(), encoding="utf-8")
print("wrote", HERE / "index.html", f"({len(permits)} permits inside boundary, {len(big)} bigger, {len(events)} events)")
