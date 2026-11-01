"""Build porch/index.html from the live Petworth data. Usage: python build.py"""
import json, math, re
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / "site" / "src" / "data" / "petworth.json"
d = json.loads(DATA.read_text(encoding="utf-8"))

e = lambda s: escape(str(s), quote=True)
TODAY = date.fromisoformat(d["events"]["today"])


def pdate(s):
    return date.fromisoformat(s[:10])


def num(n):
    return f"{n:,}"


def money(n):
    return f"${n:,.0f}"


def mday(dt, weekday=False):
    s = f"{dt.strftime('%b')} {dt.day}"
    return (dt.strftime("%a, ") + s) if weekday else s


def pct_ok(a, b):
    return a >= 100 and b >= 100


def change_words(cur, prev, unit_more="more", unit_less="fewer"):
    if prev == cur:
        return "same as the period before"
    diff = cur - prev
    word = unit_more if diff > 0 else unit_less
    if pct_ok(cur, prev):
        return f"{abs(round(diff / prev * 100))}% {word} than the {num(prev)} before"
    return f"{abs(diff)} {word} than the {num(prev)} before"


FRIENDLY = {
    "DOEE - LIHEAP": "energy bill assistance (LIHEAP)",
    "DC Health Rodent & Vector Control": "rodent control",
    "Trash Collection - Missed": "missed trash",
    "Recycling Collection - Missed": "missed recycling",
}


def friendly(t):
    return FRIENDLY.get(t, t[0].upper() + t[1:].lower() if t.isupper() else t)


def street_title(addr):
    a = re.sub(r"\s+\d{5}$", "", addr.strip())
    words = []
    for w in a.split():
        words.append(w if w in ("NW", "NE", "SW", "SE") else (w.lower() if re.match(r"^\d+(st|nd|rd|th)$", w, re.I) else w.title()))
    return " ".join(words)


def block_of(addr):
    a = street_title(addr)
    m = re.match(r"^(\d+)\s+(.*)$", a)
    if not m:
        return a
    return f"{int(m.group(1)) // 100 * 100} block of {m.group(2)}"


def sentence(s, n=120):
    s = re.sub(r"\s+", " ", s or "").strip()
    if not s:
        return ""
    first = re.split(r"(?<=[.;])\s+", s)[0]
    if len(first) >= 40:
        s = first
    s = re.sub(r"[A-Z][A-Z0-9 ,\-+]{12,}[A-Z]", lambda m: m.group(0).lower(), s)
    if s.isupper():
        s = s.lower()
    s = s[0].upper() + s[1:]
    if len(s) > n:
        s = s[:n].rsplit(" ", 1)[0].rstrip(",.;:-") + "…"
    return s


# ---------- events ----------
events = sorted(d["events"]["events"], key=lambda x: x["date"])
horizon = TODAY + timedelta(days=14)
ev_today = [x for x in events if pdate(x["date"]) == TODAY]
ev_tmrw = [x for x in events if pdate(x["date"]) == TODAY + timedelta(days=1)]
ev_next = [x for x in events if TODAY + timedelta(days=1) < pdate(x["date"]) <= horizon]
ev_later = [x for x in events if pdate(x["date"]) > horizon]

# ---------- news ----------
news = sorted(d["news"]["items"], key=lambda x: x["published"], reverse=True)
news_week = [n for n in news if (TODAY - pdate(n["published"])).days <= 7]
news_older = [n for n in news if n not in news_week]

# ---------- 311 ----------
req = d["requests"]
types = req["by_type"]
rising = easing = steady = 0
for t in types:
    if t["count"] + t["previous"] < 10:
        continue
    diff = t["count"] - t["previous"]
    if abs(diff) <= max(2, 0.1 * t["previous"]):
        steady += 1
    elif diff > 0:
        rising += 1
    else:
        easing += 1
movers = sorted(types, key=lambda t: (abs(t["count"] - t["previous"]), max(t["count"], t["previous"])), reverse=True)
top_rise = max(types, key=lambda t: (t["count"] - t["previous"], t["count"]))
top_fall = min(types, key=lambda t: (t["count"] - t["previous"], -t["previous"]))
tot, ptot = req["total"], req["previous_total"]
direction = "eased" if tot < ptot else ("rose" if tot > ptot else "held steady")
lead = (
    f"311 requests {direction} this month: {num(tot)} in the last 30 days, "
    f"{change_words(tot, ptot)}. The biggest drop was {friendly(top_fall['type'])} "
    f"({top_fall['previous']} to {top_fall['count']}); the biggest rise, {friendly(top_rise['type'])} "
    f"({top_rise['previous']} to {top_rise['count']})."
)

# ---------- permits inside boundary ----------
ring = d["boundary"]["rings"][0]


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


BIG = ("Demolition", "New construction", "Additions")
permits = [p for p in d["permits"] if p.get("lat") and p.get("lon") and inside(p["lon"], p["lat"], ring)]
big = [p for p in permits if p["group"] in BIG]
big.sort(key=lambda p: (BIG.index(p["group"]), p["issued"]), reverse=False)
by_group = {}
for p in permits:
    by_group[p["group"]] = by_group.get(p["group"], 0) + 1
by_group = sorted(by_group.items(), key=lambda kv: -kv[1])

lons = [x for x, _ in ring]
lats = [y for _, y in ring]
lat0 = (min(lats) + max(lats)) / 2
kx = math.cos(math.radians(lat0))
W = 560
span_x = (max(lons) - min(lons)) * kx
span_y = max(lats) - min(lats)
s = (W - 20) / span_x
H = span_y * s + 20


def proj(lon, lat):
    return 10 + (lon - min(lons)) * kx * s, 10 + (max(lats) - lat) * s


path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (proj(*pt) for pt in ring)) + " Z"
dots = []
for p in permits:
    if p in big:
        continue
    x, y = proj(p["lon"], p["lat"])
    dots.append(f'<circle class="pm" cx="{x:.1f}" cy="{y:.1f}" r="4"><title>{e(p["group"])}: {e(block_of(p["address"]))}</title></circle>')
for i, p in enumerate(big, 1):
    x, y = proj(p["lon"], p["lat"])
    dots.append(
        f'<g class="pb"><circle cx="{x:.1f}" cy="{y:.1f}" r="10"/><text x="{x:.1f}" y="{y + 4:.1f}">{i}</text>'
        f'<title>{i}. {e(p["group"])}: {e(street_title(p["address"]))}</title></g>'
    )
map_svg = (
    f'<svg class="map" viewBox="0 0 {W} {H:.0f}" role="img" aria-labelledby="mapt mapd">'
    f'<title id="mapt">Map of building permits in Petworth, last 30 days</title>'
    f'<desc id="mapd">{len(permits)} permits inside the neighborhood boundary; {len(big)} bigger projects are numbered and listed beside the map.</desc>'
    f'<path class="bd" d="{path}"/>' + "".join(dots) +
    f'<g class="north" transform="translate({W - 30},26)"><path d="M0,-12 L6,6 L0,2 L-6,6 Z"/><text y="20">N</text></g></svg>'
)

# ---------- homes ----------
homes = d["homes"]
hh = homes["house"]
months = homes["by_month"]
mx = max(m["median"] or 0 for m in months)
bars = []
bw = 100 / len(months)
for i, m in enumerate(months):
    label = datetime.strptime(m["month"], "%Y-%m").strftime("%b %Y")
    if m["median"]:
        h = m["median"] / mx * 100
        bars.append(f'<span class="b" style="height:{h:.1f}%" title="{label}: median {money(m["median"])}, {m["count"]} sales"><i class="sr">{label}: {money(m["median"])}</i></span>')
    else:
        bars.append(f'<span class="b empty" title="{label}: no sales yet this month"><i class="sr">{label}: in progress</i></span>')
first_m = datetime.strptime(months[0]["month"], "%Y-%m").strftime("%b")
last_m = datetime.strptime(months[-1]["month"], "%Y-%m").strftime("%b")

# ---------- curb ----------
curb = d["streets"]["curb"]
curb_week = [c for c in curb["upcoming"] if pdate(c["start"]) <= TODAY + timedelta(days=7)]

# ---------- HTML pieces ----------
def ext(url, text, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{e(url)}" rel="noopener">{text}</a>'


def event_big(x, label):
    dt = pdate(x["date"])
    return (
        f'<article class="today-ev"><p class="when"><span class="tag">{label}</span> {dt.strftime("%A")}, {mday(dt)}</p>'
        f'<h3>{ext(x["url"], e(x["title"]))}</h3>'
        f'<p class="meta"><span class="time">{e(x["time"].replace(" - ", "–"))}</span> · {e(x["place"])}</p></article>'
    )


def event_row(x):
    dt = pdate(x["date"])
    return (
        f'<li><time class="dtile" datetime="{dt.isoformat()}"><b>{dt.strftime("%a")}</b><span>{dt.day}</span></time>'
        f'<div><h4>{ext(x["url"], e(x["title"]))}</h4><p class="meta">{e(x["time"].replace(" - ", "–"))} · {e(x["place"])}</p></div></li>'
    )


weekend_html = "".join(event_big(x, "Today") for x in ev_today) + "".join(event_big(x, "Tomorrow") for x in ev_tmrw)
if not weekend_html:
    weekend_html = '<p class="empty-note">Nothing on our calendars for today or tomorrow. The links below list more.</p>'
coming_html = "".join(event_row(x) for x in ev_next) or '<li class="empty-note">Nothing listed for the next two weeks yet.</li>'
later_note = ""
if ev_later:
    later_note = f'<p class="later">Later this month: {len(ev_later)} more market days ({", ".join(mday(pdate(x["date"])) for x in ev_later)}).</p>'
also = " ".join(f'<li>{ext(l["url"], e(l["name"]))}</li>' for l in d["events"]["links"])


def news_item(n, lead=False):
    dt = pdate(n["published"])
    ago = (TODAY - dt).days
    when = "Yesterday" if ago == 1 else ("Today" if ago == 0 else mday(dt, weekday=ago < 7))
    cls = "news lead" if lead else "news"
    return (
        f'<li class="{cls}"><p class="src">{e(n["source"])} <span>·</span> <time datetime="{dt.isoformat()}">{when}</time></p>'
        f'<h3>{ext(n["url"], e(n["title"]))}</h3></li>'
    )


news_week_html = "".join(news_item(n, i == 0) for i, n in enumerate(news_week)) or '<li class="empty-note">No local stories in the last seven days.</li>'
news_old_html = "".join(
    f'<li><time datetime="{pdate(n["published"]).isoformat()}">{mday(pdate(n["published"]))}</time><p>{ext(n["url"], e(n["title"]))} <span class="src-i">{e(n["source"])}</span></p></li>'
    for n in news_older[:6]
)
outlets_ok = sum(1 for o in d["news"]["outlets"] if o["state"] == "ok")

# measures
crime = d["crime"]
permit_total = len(permits)
measures = [
    ("311 requests", num(tot), (f"{abs(round((tot - ptot) / ptot * 100))}% {'fewer' if tot < ptot else 'more'} than the 30 days before ({num(ptot)})" if pct_ok(tot, ptot) else f"{num(ptot)} in the 30 days before"), "#requests"),
    ("Crime reports", num(crime["total"]), f"{crime['previous_total']} in the 30 days before. Counts only.", None),
    ("Median house price", money(hh["median_12mo"]), f"{money(hh['median_prev_12mo'])} the year before · {hh['count_12mo']} sales", "#homes"),
    ("Building permits", num(permit_total), "issued in the last 30 days. No earlier period in this data yet.", "#block"),
]
measures_html = "".join(
    f'<div class="ms"><h3>{a}</h3><p class="big">{b}</p><p class="sub">{c}</p>' + (f'<a class="more" href="{l}">Details</a>' if l else "") + "</div>"
    for a, b, c, l in measures
)

big_html = "".join(
    f'<li><span class="n" aria-hidden="true">{i}</span><div><p class="kind">{e(p["group"])} · {mday(pdate(p["issued"]))}</p>'
    f'<h4>{e(street_title(p["address"]))}</h4><p class="work">{e(sentence(p["work"]) or p["subtype"].title())}</p></div></li>'
    for i, p in enumerate(big, 1)
) or '<li class="empty-note">No demolitions, additions or new construction this month.</li>'
gmax = max(c for _, c in by_group)
groups_html = "".join(
    f'<li><span class="lbl">{e(g)}</span><span class="bar"><i style="width:{c / gmax * 100:.0f}%"></i></span><span class="v">{c}</span></li>'
    for g, c in by_group
)
curb_html = "".join(
    f'<li><time datetime="{c["start"]}">{mday(pdate(c["start"]), True)}</time><div><h4>{e(c["block"])}</h4>'
    f'<p class="meta">{e(c["type"])} · {c["ft"]} ft · until {mday(pdate(c["end"]))} · {e(c["hours"].replace("am", "a.m.").replace("pm", "p.m."))}</p></div></li>'
    for c in curb_week[:6]
)
curb_more = len(curb_week) - min(6, len(curb_week))

top311 = sorted(types, key=lambda t: -t["count"])[:8]
m311 = top311[0]["count"]
req_html = "".join(
    f'<li><span class="lbl">{e(friendly(t["type"])[0].upper() + friendly(t["type"])[1:])}</span>'
    f'<span class="bar"><i style="width:{t["count"] / m311 * 100:.0f}%"></i></span><span class="v">{t["count"]} <small>was {t["previous"]}</small></span></li>'
    for t in top311
)

sales_html = "".join(
    f'<li><span class="addr">{e(block_of(s["address"]))}</span><span class="v">{money(s["price"])}</span>'
    f'<small>{mday(pdate(s["date"]))} · {s["beds"]} bd · {num(s["sqft"])} sq ft</small></li>'
    for s in homes["recent_sales"][:4]
)

trees = d["streets"]["trees"]
tree_sp = "".join(f'<li><span>{e(t["name"])}</span><span class="v">{t["count"]}</span></li>' for t in trees["top_species"][:5])
bt = trees["biggest"][0]

hist = d["history"]
fb = hist["buildings"]["featured_block"]
arc = hist["archive"]
clips = [c for c in arc["clips"] if len(c["text"]) > 60][:3]
clips_html = "".join(
    f'<figure class="clip"><blockquote>{e(c["text"])}</blockquote><figcaption>{arc["paper"]}, {datetime.fromisoformat(c["date"]).strftime("%B")} {pdate(c["date"]).day}, 1926, page {c["page"]} · '
    f'{ext(c["url"], "See the page")}</figcaption></figure>'
    for c in clips
)

ancs = {}
for smd in d["smds"]:
    ancs.setdefault(smd["anc"], {"url": smd["url"], "smds": []})["smds"].append(smd["smd"])
reps_html = "".join(
    f'<li>{ext(v["url"], "ANC " + e(a))}<span>Districts {", ".join(v["smds"])}</span></li>' for a, v in sorted(ancs.items())
)

gen = datetime.fromisoformat(d["generated_at"].replace("Z", "+00:00"))
summary_bits = []
if ev_today:
    summary_bits.append(f"{'a market' if len(ev_today) == 1 else str(len(ev_today)) + ' events'} today")
if ev_tmrw:
    summary_bits.append(f"{'another' if ev_today else 'a market'} tomorrow")
summary_bits.append(f"{len(news_week)} local {'story' if len(news_week) == 1 else 'stories'} this week")
summary_bits.append(f"{curb['starting_next_7d']} curb reservations starting on our streets")
summary = ", ".join(summary_bits[:-1]) + ", and " + summary_bits[-1] + "."
summary = summary[0].upper() + summary[1:]

CSS = (HERE / "style.css").read_text(encoding="utf-8") if (HERE / "style.css").exists() else ""

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>This week in Petworth · petworth.org</title>
<meta name="description" content="What's happening in Petworth, Washington DC: local news, events, and what's changing on your block, updated every night from public data.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the week</a>
<header class="mast">
  <div class="wrap mast-in">
    <a class="logo" href="./" aria-label="petworth.org home">Petworth<span>.org</span></a>
    <nav aria-label="Sections"><ul>
      <li><a href="#week">This week</a></li><li><a href="#changed">What changed</a></li><li><a href="#block">Your block</a></li><li><a href="#then">Then</a></li><li><a class="nav-cta" href="#email">Weekly email</a></li>
    </ul></nav>
  </div>
</header>

<main id="main">
<section class="hero wrap" aria-labelledby="h-title">
  <p class="dateline"><time datetime="{TODAY.isoformat()}">{TODAY.strftime('%A')}, {TODAY.strftime('%B')} {TODAY.day}, {TODAY.year}</time></p>
  <h1 id="h-title">This week in <em>Petworth</em></h1>
  <p class="summary">{e(summary)}</p>
</section>

<div class="wrap board" id="week">
  <section class="weekend" aria-labelledby="h-weekend">
    <h2 class="label" id="h-weekend">Today &amp; tomorrow</h2>
    {weekend_html}
  </section>

  <section class="newscol" aria-labelledby="h-news">
    <h2 class="label" id="h-news">In the news this week</h2>
    <ul class="newslist">{news_week_html}</ul>
    <h3 class="sublabel">Earlier</h3>
    <ul class="older">{news_old_html}</ul>
    <p class="fine">Headlines link to the outlets; we never copy their stories. Watching {len(d['news']['outlets'])} local sources.</p>
  </section>

  <section class="coming" aria-labelledby="h-coming">
    <h2 class="label" id="h-coming">Coming up, next two weeks</h2>
    <ul class="evlist">{coming_html}</ul>
    {later_note}
    <div class="also"><h3 class="sublabel">Also check</h3><ul>{also}</ul></div>
  </section>
</div>

<section class="changed" id="changed" aria-labelledby="h-changed">
  <div class="wrap">
    <h2 class="label" id="h-changed">What changed this month</h2>
    <p class="leadline">{e(lead)}</p>
    <p class="tally" aria-label="311 request types compared with the 30 days before">
      <span><b>{rising}</b> kinds of request rising</span><span><b>{easing}</b> easing</span><span><b>{steady}</b> steady</span>
    </p>
    <div class="measures">{measures_html}</div>
    <p class="fine">Last 30 days compared with the 30 before, except house prices (last 12 months vs the 12 before). Percentages appear only when both counts are 100 or more. {e(crime['note'])}</p>
  </div>
</section>

<section class="wrap block" id="block" aria-labelledby="h-block">
  <h2 class="label" id="h-block">On your block</h2>
  <div class="block-grid">
    <figure class="mapfig">
      {map_svg}
      <figcaption><span class="key"><i class="k-small"></i>Permit, last 30 days</span><span class="key"><i class="k-big"></i>Bigger project, numbered</span></figcaption>
    </figure>
    <div class="bigproj">
      <h3 class="sublabel">Bigger projects</h3>
      <ol class="projects">{big_html}</ol>
    </div>
  </div>
  <div class="block-grid two">
    <div>
      <h3 class="sublabel">Curb space reserved this week</h3>
      <p class="note">{curb['starting_next_7d']} reservations start in the next seven days; {curb['active_this_week']} are active now.</p>
      <ul class="curb">{curb_html}</ul>
      {f'<p class="later">And {curb_more} more starting this week.</p>' if curb_more else ''}
    </div>
    <div>
      <h3 class="sublabel">All {permit_total} permits, by kind</h3>
      <ul class="hbars">{groups_html}</ul>
    </div>
  </div>
</section>

<section class="around" aria-labelledby="h-around">
  <div class="wrap">
  <h2 class="label" id="h-around">Around the neighborhood</h2>
  <div class="three">
    <div id="homes">
      <h3 class="sublabel">Homes</h3>
      <p class="big">{money(hh['median_12mo'])}</p>
      <p class="sub">Median house sale, last 12 months ({hh['count_12mo']} sales). The year before: {money(hh['median_prev_12mo'])}. Condos: {money(homes['condo']['median_12mo'])} ({homes['condo']['count_12mo']} sales).</p>
      <div class="spark" role="img" aria-label="Monthly median house price, {first_m} to {last_m}; highest {money(mx)}">{''.join(bars)}</div>
      <p class="axis"><span>{first_m}</span><span>{last_m}</span></p>
      <h4 class="mini">Recent sales</h4>
      <ul class="kv sales">{sales_html}</ul>
    </div>
    <div>
      <h3 class="sublabel">Street trees</h3>
      <p class="big">{num(trees['total'])}</p>
      <p class="sub">{trees['species']} species; {trees['planted_5y']} planted in the last five years; {trees['empty_boxes']} empty tree boxes ready to plant.</p>
      <h4 class="mini">Most common</h4>
      <ul class="kv">{tree_sp}</ul>
      <p class="note">The biggest: a {e(bt['species'].lower())} {bt['dbh_in']:.0f} inches across, on the {e(bt['block'])}.</p>
    </div>
    <div id="requests">
      <h3 class="sublabel">Top 311 requests</h3>
      <p class="sub">Last 30 days, with the 30 days before.</p>
      <ul class="hbars stack">{req_html}</ul>
      <p class="note">{req['open']} requests are still open.</p>
    </div>
  </div>
  </div>
</section>

<section class="then wrap" id="then" aria-labelledby="h-then">
  <h2 class="label" id="h-then">Then: this week in {arc['week_start'][:4]}</h2>
  <div class="then-grid">
    <div class="then-lead">
      <p class="then-range">{e(arc['week_label'].replace(' – ', '–'))}</p>
      <p class="then-block">{e(fb['sentence'])}</p>
      <p class="fine">From DC Historic Preservation Office building records ({num(hist['buildings']['records'])} Petworth buildings, {hist['buildings']['year_min']}–{hist['buildings']['year_max']}).</p>
    </div>
    <div class="clips">{clips_html}
      <p class="fine">Machine-read text from the {arc['paper']} on the Library of Congress's Chronicling America; misspellings are the scanner's.</p>
    </div>
  </div>
</section>
</main>

<footer class="foot">
  <div class="wrap foot-grid">
    <section id="email" aria-labelledby="h-email">
      <h2 id="h-email">The week in Petworth, every Friday</h2>
      <p>One short email: what's on this weekend, what changed, what's coming to your block.</p>
      <form class="sub-form" action="/petworth/subscribe/" method="get">
        <label for="em">Email address</label>
        <div class="row"><input id="em" name="email" type="email" autocomplete="email" required placeholder="you@example.com"><button type="submit">Sign up</button></div>
      </form>
    </section>
    <section aria-labelledby="h-reps">
      <h2 id="h-reps">Your neighborhood commissions</h2>
      <p>Petworth is split across {len(d['smds'])} single-member districts in two Advisory Neighborhood Commissions.</p>
      <ul class="reps">{reps_html}</ul>
      <p class="small">No ANC meetings on our calendars in the next 30 days; check the commission sites.</p>
    </section>
  </div>
  <div class="wrap foot-base"><div class="foot-rule">
    <p><strong>petworth.org is independent.</strong> It is not affiliated with the DC Government. Built every night from public data: {e(d['sources']['permits'])}; {e(d['sources']['requests'])}; {e(d['sources']['crime'])}; OTR sales; DDOT street data; Library of Congress. Data {e(d['sources']['license'])}.</p>
    <p>Updated {gen.strftime('%b')} {gen.day}, {gen.year}, {gen.strftime('%H:%M')} UTC.</p>
  </div></div>
</footer>
</body>
</html>
"""
(HERE / "index.html").write_text(html, encoding="utf-8")
print("wrote index.html", len(html), "bytes;", len(permits), "permits inside;", len(big), "big")
