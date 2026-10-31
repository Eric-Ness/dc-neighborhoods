"""Layout C1: Live Feed. Reads design/layouts/facts.json, writes design/layouts/C1-live-feed.html.

A variation on Layout C (Civic Dashboard): the page is a reverse-chronological feed of
what happened in Petworth, with sticky date headers and a slim sticky "vitals" bar.
Phone: single column plus a bottom tab bar. Desktop (>=1100px): three columns.

Run from anywhere:  python design/layouts/src/C1_live_feed.py
Python 3.13 stdlib only.
"""
from __future__ import annotations

import html
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYOUTS = HERE.parent
FACTS = json.loads((LAYOUTS / "facts.json").read_text(encoding="utf-8"))
OUT = LAYOUTS / "C1-live-feed.html"

e = html.escape


# ---------- helpers (shared with C) ----------
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
    return {"d": d, "abs": abs(d), "sign": sign, "pct": pct,
            "cls": "up" if d > 0 else ("down" if d < 0 else "flat"),
            "arrow": "▲" if d > 0 else ("▼" if d < 0 else "•"),
            "txt": f"{sign}{abs(d)}" + (f" ({sign}{abs(pct)}%)" if pct is not None else "")}


def title_case(s: str) -> str:
    keep = {"NW", "NE", "SW", "SE", "ADU"}
    return " ".join(w if w in keep or any(c.isdigit() for c in w) else w.capitalize() for w in s.split())


def addr(s: str) -> str:
    return title_case(re.sub(r"\s+\d{5}$", "", s.strip()))


def clean_work(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    # tame ALL-CAPS runs copied from permit forms
    s = re.sub(r"[A-Z0-9][A-Z0-9 ,.+\-]{24,}", lambda m: m.group(0)[0] + m.group(0)[1:].lower(), s)
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


def md(d: date) -> str:
    return f"{d.strftime('%b')} {d.day}"


def wmd(d: date) -> str:
    return f"{d.strftime('%a')}, {md(d)}"


def bars(cur: float, prev: float, cls: str, cur_lbl: str, prev_lbl: str) -> str:
    m = max(cur, prev) or 1
    return f"""<div class="bars">
  <div class="br"><span class="bk">{cur_lbl}</span><svg viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="8" rx="2"/><rect class="now {cls}" width="{100 * cur / m:.1f}" height="8" rx="2"/></svg><b class="num">{fmt(cur) if isinstance(cur, int) else cur}</b></div>
  <div class="br"><span class="bk">{prev_lbl}</span><svg viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="8" rx="2"/><rect class="prev" width="{100 * prev / m:.1f}" height="8" rx="2"/></svg><b class="num pv">{fmt(prev) if isinstance(prev, int) else prev}</b></div>
</div>"""


# ---------- derived data ----------
gen = datetime.fromisoformat(FACTS["generated_at"].replace("Z", "+00:00"))
gl = to_eastern(gen)
today = gl.date()
hour = gl.strftime("%I").lstrip("0")
clock = f"{hour}:{gl.strftime('%M')} {gl.strftime('%p')}"
asof_long = f"{wmd(today)}, {gl.year} · {clock} ET"

tm = FACTS["this_month"]
homes = FACTS["homes"]
streets = FACTS["streets"]
trees = FACTS["trees"]
hist = FACTS["history"]
reps = FACTS["representatives"]
groups = FACTS["permit_groups"]

req = delta(tm["requests_30d"], tm["requests_prev_30d"])
crime = delta(tm["crime_30d"], tm["crime_prev_30d"])

SHORT = {"DC Health Rodent & Vector Control": "Rodent & vector control"}
SENT = {"DC Health Rodent & Vector Control": "Rodent complaints"}


def short_type(t: str) -> str:
    return SHORT.get(t, t)


movers = [dict(m, delta=delta(m["count"], m["previous"])) for m in tm["top_311_movers"]]
rises = sorted([m for m in movers if m["delta"]["d"] > 0], key=lambda m: -m["delta"]["d"])
lead = rises[0] if rises else max(movers, key=lambda m: m["delta"]["abs"])
others = [m for m in movers if m is not lead]

GROUP_ORDER = ["Demolition", "New construction", "Additions", "Renovation & repair",
               "Electrical, plumbing & mechanical", "Home businesses", "Minor work"]
GKEY = {"Demolition": "demo", "New construction": "newc", "Additions": "add",
        "Renovation & repair": "ren", "Electrical, plumbing & mechanical": "mep",
        "Home businesses": "home", "Minor work": "minor"}
GSHORT = {"Electrical, plumbing & mechanical": "Electrical, plumbing, mech."}
big_types = ["Demolition", "New construction", "Additions"]
permits_total = tm["permits_30d"]

projects = []
for p in FACTS["bigger_projects"]:
    iss = datetime.fromisoformat(p["issued"].replace("Z", "+00:00"))
    d = to_eastern(iss).date()
    projects.append({"addr": addr(p["address"]), "group": p["group"], "day": d, "work": clean_work(p["work"]),
                     "street": " ".join(addr(p["address"]).split()[1:])})
projects.sort(key=lambda p: p["day"], reverse=True)


def price_k(s: str) -> int:
    return int(re.sub(r"[^\d]", "", s.split()[0]))


curb_mi = streets["curb_reserved_ft"] / 5280
hist_street = hist["block"].split()[3]  # "Delafield"


# ---------- feed items ----------
ICONS = {
    "permit": '<path d="M4 20h16M6 20V9l6-4 6 4v11M10 20v-5h4v5"/>',
    "311": '<path d="M5 5h14v10H9l-4 4z"/>',
    "crime": '<path d="M12 3l8 4v5c0 4.5-3.5 8-8 9-4.5-1-8-4.5-8-9V7z"/>',
    "streets": '<path d="M4 20 9 4M20 20 15 4M12 6v2M12 11v2M12 16v2"/>',
    "homes": '<path d="M3 11 12 4l9 7M6 9.5V20h12V9.5"/>',
    "history": '<path d="M5 4h11l3 3v13H5zM9 9h7M9 13h7M9 17h4"/>',
}


def icon(t: str, cls: str = "") -> str:
    return (f'<span class="ic {t} {cls}" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[t]}</svg></span>')


def item(t: str, kicker: str, head: str, body: str = "", href: str = "", go: str = "", extra: str = "",
         cls: str = "", sub_t: str = "", go_href: str = "") -> str:
    tag = "a" if href else "div"
    hattr = f' href="{href}"' if href else ""
    if go_href:
        go = f'<a class="go" href="{go_href}">{go} →</a>'
    elif go:
        go = f'<span class="go">{go} →</span>'
    return f"""
<li class="it {cls}" data-t="{t}{(' ' + sub_t) if sub_t else ''}">
  {icon(t)}
  <{tag} class="card"{hattr}>
    <div class="kick"><span class="kt {t}">{kicker}</span>{go}</div>
    <div class="hd">{head}</div>
    {f'<div class="bd">{body}</div>' if body else ''}
    {extra}
  </{tag}>
</li>"""


def day_group(label: str, rel: str, items: list[str], dt_attr: str = "", cls: str = "", count: str = "") -> str:
    return f"""
<section class="day {cls}" aria-label="{e(label)}">
  <h3 class="dh"><span class="dl">{label}</span><span class="dr">{rel}</span>{f'<span class="dc num">{count}</span>' if count else ''}</h3>
  <ol class="items">{''.join(items)}</ol>
</section>"""


def quiet(d1: date, d2: date) -> str:
    rng = md(d1) if d1 == d2 else (f"{md(d1)} – {d2.day}" if d1.month == d2.month else f"{md(d1)} – {md(d2)}")
    n = (d2 - d1).days + 1
    return (f'<div class="quiet" data-t="permit"><span class="qd num">{rng}</span>'
            f'<span>{"No" if n == 1 else f"{n} days, no"} demolition, addition or new-construction permits</span></div>')


feed: list[str] = []

# Coming up
feed.append(day_group(
    f"Next 7 days", f"{md(today + timedelta(days=1))} – {md(today + timedelta(days=7))}",
    [item("streets", "Curb · scheduled",
          f'<b class="num">{streets["curb_permits_starting_next_7d"]}</b> curb permits start this week',
          "Parking spaces reserved for moves, dumpsters and construction. Check your block before you park.",
          link("Curb radar"), "Curb radar")],
    cls="ahead"))

# Today
ld = lead["delta"]
lead_html = f"""
<li class="it lead" data-t="311">
  {icon("311", "big")}
  <a class="card" href="{link('311 report card')}">
    <div class="kick"><span class="flag">Top story</span><span class="kt 311">311 · last 30 days</span></div>
    <h2 class="lh">{e(FACTS['lead_sentence'])}</h2>
    {bars(lead['count'], lead['previous'], ld['cls'], 'Last 30 days', '30 days before')}
    <div class="lf"><span><span class="chg {ld['cls']}">{ld['arrow']} {ld['abs']}</span> {'more' if ld['d'] > 0 else 'fewer'} {e(SENT.get(lead['type'], lead['type']).lower())}</span><span class="go">311 report card →</span></div>
  </a>
</li>"""

mover_rows = "".join(
    f'<div class="mv"><span>{e(short_type(m["type"]))}</span><b class="num">{m["count"]}</b>'
    f'<span class="num pv">from {m["previous"]}</span><span class="chg num {m["delta"]["cls"]}">{m["delta"]["arrow"]} {m["delta"]["abs"]}'
    f'{"" if m["delta"]["pct"] is None else " (" + str(abs(m["delta"]["pct"])) + "%)"}</span></div>'
    for m in others)

today_items = [
    lead_html,
    item("history", "100 years ago today · OCR text",
         f'<q>{e(hist["hundred_years_ago_excerpt_ocr"])}</q>',
         f'{e(hist["hundred_years_ago_source"])}. Machine-read; may contain errors.',
         link("100 years ago"), "100 years ago", cls="arch"),
    item("311", "311 · all requests",
         f'<b class="num">{fmt(tm["requests_30d"])}</b> requests in 30 days, <span class="nw">{"down" if req["d"] < 0 else "up"} {req["abs"]}{"" if req["pct"] is None else " (" + str(abs(req["pct"])) + "%)"}</span>',
         "", link("311 report card"), "Report card",
         extra=bars(tm["requests_30d"], tm["requests_prev_30d"], req["cls"], "Last 30 days", "30 days before")),
    item("311", "311 · other big movers", "Fewer yard-waste and dumping calls", "", link("311 report card"), "",
         extra=f'<div class="mvs">{mover_rows}</div>'),
    item("crime", "Crime · counts only",
         f'<b class="num">{tm["crime_30d"]}</b> crime reports in 30 days; <span class="nw"><b class="num">{tm["crime_prev_30d"]}</b> the 30 days before</span>',
         "Preliminary counts from DC open data. Small numbers swing month to month.",
         link("Block report card"), "Block report card"),
    item("streets", "Curb · active now",
         f'<b class="num">{streets["curb_permits_active_this_week"]}</b> curb permits active this week',
         f'{fmt(streets["curb_reserved_ft"])} feet of curb reserved, about {curb_mi:.1f} miles.',
         link("Curb radar"), "Curb radar"),
    item("homes", "Homes · last 60 days",
         f'<b class="num">{homes["market_sales_60d"]}</b> sales, median <b class="num">{homes["median_price_60d"]}</b>',
         f'{homes["median_price_per_sqft_60d"]} per square foot. 12-month median house price: {homes["median_house_price_12mo"]}.',
         link("Housing pulse"), "Housing pulse"),
]
feed.append(day_group(f"Today · {wmd(today)}", f"Updated {clock} ET", today_items, cls="today",
                      count=""))

# Dated permits, grouped by day, with quiet stretches between
by_day: dict[date, list[dict]] = {}
for p in projects:
    by_day.setdefault(p["day"], []).append(p)
prev_day = today
for d in sorted(by_day, reverse=True):
    gap_hi, gap_lo = prev_day - timedelta(days=1), d + timedelta(days=1)
    if gap_lo <= gap_hi:
        feed.append(quiet(gap_lo, gap_hi))
    rows = []
    for p in by_day[d]:
        k = GKEY[p["group"]]
        label = "Addition" if p["group"] == "Additions" else p["group"]
        extra = ""
        if hist_street.lower() in p["street"].lower():
            extra = f"""<div class="aside" data-t="history">
  <span class="kt history">From the archives · same street</span>
  <p><b>{e(hist['block'])}.</b> {e(hist['fact'])}</p>
  <a class="go" href="{link('Building biography')}">Building biography →</a>
</div>"""
        rows.append(item("permit", f'Permit · <span class="pk {k}">{e(label)}</span>', e(p["addr"]), e(p["work"]),
                         "" if extra else link("Block Watch"), "Block Watch", extra=extra, cls=f"pm {k}",
                         sub_t="history" if extra else "", go_href=link("Block Watch") if extra else ""))
    ago = (today - d).days
    feed.append(day_group(wmd(d), f"{ago} days ago" if ago > 1 else "Yesterday", rows,
                          count=f"{len(rows)} permit{'s' if len(rows) > 1 else ''}"))
    prev_day = d

# End cap: the whole 30-day permit picture
segs, x = [], 0.0
for g in GROUP_ORDER:
    n = groups.get(g, 0)
    if not n:
        continue
    w = 100 * n / permits_total
    segs.append(f'<rect class="seg {GKEY[g]}" x="{x:.2f}" y="0" width="{max(w - 0.5, 0.4):.2f}" height="12"><title>{e(g)}: {n}</title></rect>')
    x += w
legend = "".join(f'<li><i class="sw {GKEY[g]}"></i>{e(GSHORT.get(g, g))}<b class="num">{groups[g]}</b></li>'
                 for g in GROUP_ORDER if g in groups)
endcap = f"""
<div class="endcap" data-t="permit">
  <div class="ec-h"><span class="dot"></span>That's every bigger permit from the last 30 days.</div>
  <p><b class="num">{permits_total}</b> building permits were issued in all. Most were small jobs:</p>
  <svg class="stack" viewBox="0 0 100 12" preserveAspectRatio="none" aria-hidden="true">{''.join(segs)}</svg>
  <ul class="glist">{legend}</ul>
  <a class="go" href="{link('Block Watch')}">See every permit on Block Watch →</a>
</div>"""

# ---------- filters ----------
def count_t(t: str) -> int:
    n = sum(1 for f in feed for _ in re.finditer(rf'class="it[^"]*" data-t="[^"]*\b{t}\b', f))
    return n


FILTERS = [("all", "Everything"), ("permit", "Permits"), ("311", "311"), ("crime", "Crime"),
           ("streets", "Curb & streets"), ("homes", "Homes"), ("history", "History")]
fcounts = {t: count_t(t) for t, _ in FILTERS[1:]}
fcounts["all"] = sum(1 for f in feed for _ in re.finditer(r'<li class="it', f))
filters_html = "".join(
    f'<button type="button" class="fb" data-f="{t}" aria-pressed="{"true" if t == "all" else "false"}">'
    f'{"" if t == "all" else icon(t, "sm")}<span>{lbl}</span><b class="num">{fcounts[t]}</b></button>'
    for t, lbl in FILTERS)

# ---------- vitals ----------
med12 = price_k(homes["median_house_price_12mo"])
med60 = price_k(homes["median_price_60d"])
VITALS = [
    ("311 requests", fmt(tm["requests_30d"]), req, f'vs {fmt(tm["requests_prev_30d"])}', "30d", link("311 report card"),
     (tm["requests_30d"], tm["requests_prev_30d"])),
    ("Crime reports", str(tm["crime_30d"]), crime, f'vs {tm["crime_prev_30d"]}', "30d", link("Block report card"),
     (tm["crime_30d"], tm["crime_prev_30d"])),
    ("Permits", str(permits_total), None, f'{sum(groups.get(g, 0) for g in big_types)} bigger', "30d", "#feed", None),
    ("Median house", homes["median_house_price_12mo"], None, f'{homes["house_sales_12mo"]} sales', "12 mo", "#homes",
     (med60, med12)),
    ("Curb permits", str(streets["curb_permits_active_this_week"]), None, f'+{streets["curb_permits_starting_next_7d"]} next 7d',
     "now", link("Curb radar"), None),
]


def vital(i, v) -> str:
    label, val, d, cmp_txt, per, href, pair = v
    dtxt = f'<span class="chg {d["cls"]}">{d["arrow"]}{d["abs"]}</span>' if d else ""
    spark = ""
    if pair:
        m = max(pair)
        spark = (f'<svg class="vs" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true">'
                 f'<rect class="trk" width="100" height="4" rx="1"/><rect class="now {d["cls"] if d else "neutral"}" width="{100 * pair[0] / m:.1f}" height="4" rx="1"/>'
                 f'<rect class="trk" y="6" width="100" height="4" rx="1"/><rect class="prev" y="6" width="{100 * pair[1] / m:.1f}" height="4" rx="1"/></svg>')
    short = {"311 requests": "311", "Crime reports": "Crime", "Median house": "Median"}.get(label, label)
    return (f'<a class="v v{i}" href="{href}"><span class="vl"><span class="lg">{label}</span><span class="st">{short}</span> <em>{per}</em></span>'
            f'<span class="vv"><b class="num">{val}</b>{dtxt}</span><span class="vc">{cmp_txt}</span>{spark}</a>')


vitals_html = "".join(vital(i, v) for i, v in enumerate(VITALS))

# ---------- ticker ----------
tick_bits = [
    f'<span><i class="chg {ld["cls"]}">{ld["arrow"]}</i> Rodent complaints <b>{lead["count"]}</b> <s>{lead["previous"]}</s></span>',
    f'<span><i class="chg {req["cls"]}">{req["arrow"]}</i> 311 requests <b>{fmt(tm["requests_30d"])}</b> <s>{fmt(tm["requests_prev_30d"])}</s></span>',
] + [f'<span><i class="chg {m["delta"]["cls"]}">{m["delta"]["arrow"]}</i> {e(short_type(m["type"]))} <b>{m["count"]}</b> <s>{m["previous"]}</s></span>' for m in others] + [
    f'<span><i class="chg {crime["cls"]}">{crime["arrow"]}</i> Crime reports <b>{tm["crime_30d"]}</b> <s>{tm["crime_prev_30d"]}</s></span>',
    f'<span><i class="nt">●</i> {len(projects)} bigger permits, latest {e(projects[0]["addr"])}</span>',
    f'<span><i class="nt">●</i> {streets["curb_permits_active_this_week"]} curb permits active</span>',
    f'<span><i class="nt">●</i> Median house {homes["median_house_price_12mo"]}</span>',
]
ticker_one = "".join(tick_bits)


# ---------- map ----------
def map_svg() -> str:
    rings = FACTS["boundary_rings"]
    pts = [p for r in rings for p in r]
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    minx, maxx, miny, maxy = min(lons), max(lons), min(lats), max(lats)
    k = math.cos(math.radians((miny + maxy) / 2))
    W, pad = 320, 10
    sc = (W - 2 * pad) / ((maxx - minx) * k)
    H = round((maxy - miny) * sc + 2 * pad)
    px = lambda lon: pad + (lon - minx) * k * sc
    py = lambda lat: pad + (maxy - lat) * sc
    d = " ".join("M" + "L".join(f"{px(x):.1f},{py(y):.1f}" for x, y in r) + "Z" for r in rings)
    small, big, seen = [], [], set()
    for p in FACTS["permit_points"]:
        isbig = p["group"] in big_types
        key = (round(p["lon"], 5), round(p["lat"], 5), isbig)
        if key in seen:
            continue
        seen.add(key)
        c = f'<circle cx="{px(p["lon"]):.1f}" cy="{py(p["lat"]):.1f}"'
        if isbig:
            big.append(f'<g class="bp {GKEY[p["group"]]}"><circle class="ring" cx="{px(p["lon"]):.1f}" cy="{py(p["lat"]):.1f}" r="5"/>'
                       + c + f' r="4.4" class="pt-big"><title>{e(p["group"])}</title></circle></g>')
        else:
            small.append(c + ' r="2.2" class="pt"/>')
    return (f'<svg class="map" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Map of Petworth with the last 30 days of permit locations; larger dots are demolition and addition permits">'
            f'<path d="{d}" class="bnd"/>{"".join(small)}{"".join(big)}</svg>')


# ---------- standing panels ----------
max311 = max(max(t["count"], t["previous"]) for t in tm["top_311_types"])
rank_rows = ""
for i, t in enumerate(tm["top_311_types"], 1):
    d = delta(t["count"], t["previous"])
    rank_rows += f"""
<li><span class="rn num">{i}</span><span class="rname">{e(short_type(t['type']))}</span><b class="num">{t['count']}</b><span class="chg num {d['cls']}">{d['arrow']}{d['abs']}</span>
<svg class="rbar" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="6" rx="1"/><rect class="fill" width="{100 * t['count'] / max311:.1f}" height="6" rx="1"/><rect class="tick" x="{100 * t['previous'] / max311 - 0.4:.1f}" y="-1.5" width="0.9" height="9"/></svg></li>"""

rep_rows = "".join(
    f'<li><span class="smd num">{r["smd"]}</span><span class="cname">{e(title_case(r["commissioner"]))}</span>'
    f'<a href="{e(r["url"])}" aria-label="ANC {r["anc"]} website">ANC {r["anc"]} ↗</a></li>' for r in reps)
ancs = sorted({r["anc"] for r in reps})

ICON_SEARCH = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
TAB_ICONS = {
    "feed": '<path d="M4 6h16M4 12h16M4 18h10"/>',
    "map": '<path d="M12 21s-6-5.4-6-10a6 6 0 0 1 12 0c0 4.6-6 10-6 10z"/><circle cx="12" cy="11" r="2"/>',
    "homes": ICONS["homes"],
    "streets": ICONS["streets"],
    "you": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4.5-6 8-6s7 2 8 6"/>',
}
tabs_html = "".join(
    f'<a href="#{k}" data-tab="{k}"{" aria-current=\"true\"" if k == "feed" else ""}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{TAB_ICONS[k]}</svg><span>{lbl}</span></a>'
    for k, lbl in [("feed", "Feed"), ("map", "Map"), ("homes", "Homes"), ("streets", "Streets"), ("you", "You")])

CSS = r"""
:root{
  --bg:#f2f1ed; --surface:#fff; --surface-2:#f7f6f2; --ink:#121519; --ink-2:#3a3f47; --muted:#6a6f78;
  --line:#e0ded7; --line-2:#ebe9e3;
  --accent:#0b6b70; --accent-ink:#fff; --accent-soft:#e1efee;
  --up:#c2410c; --up-soft:#fbe8dd; --down:#2f7a4a; --down-soft:#e0f0e5; --neutral:#4a5260;
  --t-permit:#0b6b70; --t-311:#9a6700; --t-crime:#6b4aa0; --t-streets:#4a5260; --t-homes:#a63d6e; --t-history:#7d6547;
  --c-demo:#c2410c; --c-add:#0b6b70; --c-newc:#9a6700; --c-ren:#6f8aa0; --c-mep:#9aa3ad; --c-home:#b49a5e; --c-minor:#cfd3d8;
  --font:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --vh:58px; --tabh:62px;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0f1113; --surface:#181b1e; --surface-2:#1e2226; --ink:#ecebe6; --ink-2:#c6c4bf; --muted:#959aa1;
  --line:#2b2f34; --line-2:#24282c; --accent:#4fb3b0; --accent-ink:#0c1214; --accent-soft:#16302f;
  --up:#f08a5d; --up-soft:#3a2219; --down:#6cc08a; --down-soft:#1a2e21; --neutral:#a7afba;
  --t-permit:#4fb3b0; --t-311:#e0a93a; --t-crime:#b39ae0; --t-streets:#a7afba; --t-homes:#e486b0; --t-history:#c9ae86;
  --c-demo:#f08a5d; --c-add:#4fb3b0; --c-ren:#7f9bb2; --c-mep:#5f6873; --c-home:#a58d55; --c-minor:#3d434a;
}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:calc(var(--vh) + 8px)}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font);font-feature-settings:"tnum" 1,"cv11" 1;padding-bottom:calc(var(--tabh) + env(safe-area-inset-bottom))}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.num{font-variant-numeric:tabular-nums}
.nw{white-space:nowrap}
h2,h3{margin:0}
.layout-tag{font:600 10.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;background:var(--ink);color:var(--bg);padding:6px 16px}
.chg{font-style:normal;font-weight:700}
.chg.up{color:var(--up)} .chg.down{color:var(--down)} .chg.flat{color:var(--muted)}
svg .trk{fill:var(--line-2)} svg .prev{fill:var(--c-minor)}
svg .now.up{fill:var(--up)} svg .now.down{fill:var(--down)} svg .now.neutral,svg .now.flat{fill:var(--neutral)}
@keyframes pulse{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--down) 55%,transparent)}70%{box-shadow:0 0 0 7px transparent}100%{box-shadow:0 0 0 0 transparent}}
.live{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--down);animation:pulse 2s infinite;flex:none}

/* header */
.top{background:var(--surface);border-bottom:1px solid var(--line)}
.top-in{max-width:1360px;margin:0 auto;padding:12px 16px 10px;display:grid;gap:10px}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.mark{flex:none;width:32px;height:32px;border-radius:8px;background:var(--ink);color:var(--bg);display:grid;place-items:center;font:700 16px/1 var(--mono)}
.brand h1{margin:0;font-size:20px;line-height:1.1;letter-spacing:-.01em}
.brand p{margin:1px 0 0;font-size:12.5px;color:var(--muted);line-height:1.3}
.status{display:flex;align-items:center;gap:8px;font:500 11.5px/1.3 var(--mono);color:var(--muted)}
.status b{color:var(--ink);font-weight:600}
@media (max-width:420px){.nx{display:none}}
.sbox{display:flex;align-items:center;gap:8px;background:var(--surface-2);border:1px solid var(--line);border-radius:11px;padding:0 5px 0 12px;height:44px}
.sbox svg{flex:none;color:var(--muted)}
.sbox input{flex:1;min-width:0;border:0;background:transparent;font:inherit;color:var(--ink);outline:none;height:100%}
.sbox input::placeholder{color:var(--muted)}
.sbox button{flex:none;border:0;background:var(--accent);color:var(--accent-ink);font:600 13px var(--font);border-radius:8px;padding:8px 12px;cursor:pointer}
.shint{font-size:12px;color:var(--muted);margin-top:6px}
.shint a{font-weight:500}

/* ticker */
.ticker{background:var(--ink);color:var(--bg);overflow:hidden;white-space:nowrap;font:500 12px/1 var(--mono);position:relative}
.ticker::before{content:"30 DAYS";position:absolute;left:0;top:0;bottom:0;z-index:1;display:flex;align-items:center;padding:0 10px 0 16px;background:var(--ink);font-weight:700;letter-spacing:.08em;color:#7fd3a0;box-shadow:8px 0 10px var(--ink)}
.tk-track{display:inline-flex;animation:tk 60s linear infinite;padding:9px 0}
.tk-track span{padding:0 18px;border-left:1px solid color-mix(in srgb,var(--bg) 22%,transparent)}
.tk-track b{font-weight:700}
.tk-track s{text-decoration:none;opacity:.55;margin-left:4px}
.tk-track i{font-style:normal;margin-right:4px}
.ticker .chg.up{color:#ff9a6a} .ticker .chg.down{color:#7fd3a0} .ticker .nt{color:#8fc9c7;font-size:8px;vertical-align:2px}
@keyframes tk{to{transform:translateX(-50%)}}
@media (prefers-reduced-motion:reduce){.tk-track{animation:none}.live{animation:none}}

/* app frame: phone = one column ordered by `order` */
.app{display:flex;flex-direction:column;max-width:680px;margin:0 auto}
.col,.stick,.standing{display:contents}
.vitals{order:1} .filters{order:2} #feed{order:3} #map{order:4} #homes{order:5} #streets{order:6} #you{order:7} #subscribe{order:8} .sponsor{order:9}
.blk{padding:0 16px}
.sh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin:22px 0 10px}
.sh h2{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase}
.sh a,.sh span{font-size:12.5px;white-space:nowrap}
.sh span{color:var(--muted)}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:12px}

/* vitals: sticky strip on phone */
.vitals{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--surface) 94%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);height:var(--vh);display:grid;grid-template-columns:repeat(4,minmax(0,1fr))}
.vh{display:none}
.v{display:flex;flex-direction:column;justify-content:center;padding:6px 8px 6px 10px;color:inherit;min-width:0;border-left:1px solid var(--line-2)}
.v:first-of-type{border-left:0;padding-left:16px}
.v:hover{text-decoration:none;background:var(--surface-2)}
.v4,.vc,.vs{display:none}
.vl{font:600 9.5px/1.2 var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vl em{font-style:normal;opacity:.7}
.vv{display:flex;align-items:baseline;gap:4px;margin-top:3px;white-space:nowrap}
.vv b{font-size:17px;font-weight:700;letter-spacing:-.02em;line-height:1}
.vv .chg{font-size:10.5px}
.vsub{display:none} .vl .lg{display:none}

/* filters */
.filters{padding:14px 16px 0}
.fh{display:none}
.fl{display:flex;flex-wrap:wrap;gap:6px}
.fb{display:inline-flex;align-items:center;gap:6px;font:500 12.5px var(--font);color:var(--ink-2);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:5px 10px 5px 8px;cursor:pointer}
.fb b{font:600 10.5px var(--mono);color:var(--muted)}
.fb[data-f="all"]{padding-left:11px}
.fb[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.fb[aria-pressed="true"] b{color:color-mix(in srgb,var(--bg) 70%,transparent)}
.fb[aria-pressed="true"] .ic{color:var(--bg)}

/* type icons */
.ic{display:grid;place-items:center;flex:none;width:26px;height:26px;border-radius:50%;background:var(--surface);border:1.5px solid currentColor}
.ic svg{width:14px;height:14px}
.ic.sm{width:auto;height:auto;border:0;background:none}
.ic.sm svg{width:14px;height:14px}
.ic.permit,.kt.permit{color:var(--t-permit)} .ic.\33 11,.kt.\33 11{color:var(--t-311)} .ic.crime,.kt.crime{color:var(--t-crime)}
.ic.streets,.kt.streets{color:var(--t-streets)} .ic.homes,.kt.homes{color:var(--t-homes)} .ic.history,.kt.history{color:var(--t-history)}
.ic.big{width:30px;height:30px;background:var(--t-311);color:var(--surface);border-color:var(--t-311)}

/* feed */
#feed{padding:0}
.feed-h{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:18px 16px 4px}
.feed-h h2{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;display:flex;align-items:center;gap:8px}
.feed-h a{font:600 11.5px var(--mono)}
.day{position:relative}
.day.empty{display:none}
.dh{position:sticky;top:var(--vh);z-index:10;display:flex;align-items:baseline;gap:8px;padding:9px 16px 8px;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(6px);border-bottom:1px solid var(--line-2);font-size:13px}
.dl{font-weight:700}
.dr{font:500 11.5px var(--mono);color:var(--muted)}
.dc{margin-left:auto;font:600 11px var(--mono);color:var(--muted)}
.today .dl{color:var(--ink)}
.today .dh::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--down);align-self:center;animation:pulse 2s infinite}
.ahead .dh{color:var(--muted)}
.ahead .dl{color:var(--ink-2)}
.items{list-style:none;margin:0;padding:6px 16px 4px;position:relative}
.items::before{content:"";position:absolute;left:28.5px;top:0;bottom:0;width:2px;background:var(--line)}
.ahead .items::before{background:repeating-linear-gradient(var(--line) 0 4px,transparent 4px 8px)}
.it{position:relative;display:grid;grid-template-columns:26px minmax(0,1fr);gap:10px;padding:6px 0}
.it[hidden]{display:none}
.it>.ic{margin-top:8px;position:relative;z-index:1}
.it.lead>.ic{margin-left:-2px}
.card{display:block;color:inherit;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 12px 11px;min-width:0}
a.card:hover{text-decoration:none;border-color:color-mix(in srgb,var(--ink) 40%,var(--line))}
.kick{display:flex;align-items:center;gap:8px;font:600 10.5px/1.2 var(--mono);letter-spacing:.04em;text-transform:uppercase}
.kick .go{margin-left:auto;text-transform:none;letter-spacing:0;font-family:var(--font);font-size:12px}
.go{color:var(--accent);font-weight:600;white-space:nowrap}
.pk.add{color:var(--c-add)} .pk.demo{color:var(--c-demo);}
.hd{font-size:15px;font-weight:600;line-height:1.3;margin-top:4px}
.hd b{font-weight:700}
.bd{font-size:12.5px;color:var(--muted);margin-top:3px;overflow-wrap:anywhere}
.pm .bd{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pm.demo .card{border-left:3px solid var(--c-demo)}
.pm.add .card{border-left:3px solid var(--c-add)}
.arch .card{background:var(--surface-2)}
.arch .hd q{font:italic 400 16px/1.4 Georgia,"Times New Roman",serif;color:var(--ink-2);quotes:"“" "”"}
.aside{margin-top:9px;padding:9px 10px;border-radius:8px;background:var(--surface-2);border:1px dashed var(--line)}
.aside .kt{font:600 10.5px var(--mono);letter-spacing:.04em;text-transform:uppercase}
.aside .go{font-size:12.5px}
.kick a.go:hover{text-decoration:underline}
.aside p{margin:4px 0;font-size:13px;color:var(--ink-2)}
/* lead */
.lead .card{border:1px solid var(--line);border-top:3px solid var(--t-311);padding:12px 13px 12px}
.flag{background:var(--ink);color:var(--bg);padding:3px 6px;border-radius:4px;letter-spacing:.06em}
.lh{font-size:19px;line-height:1.3;letter-spacing:-.01em;margin:8px 0 10px;font-weight:700}
.lf{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 6px;font-size:12px;color:var(--muted);margin-top:9px}
.lf .go{margin-left:auto}
.bars{display:grid;gap:4px;margin-top:8px}
.br{display:grid;grid-template-columns:92px 1fr 44px;gap:8px;align-items:center;font-size:11.5px;color:var(--muted)}
.br svg{width:100%;height:8px;display:block}
.br b{text-align:right;color:var(--ink);font-size:13px}
.br b.pv{color:var(--muted);font-weight:600}
.mvs{margin-top:6px;display:grid}
.mv{display:grid;grid-template-columns:minmax(0,1fr) auto auto 78px;gap:8px;align-items:baseline;font-size:13px;padding:5px 0;border-top:1px solid var(--line-2)}
.mv:first-child{border-top:0}
.mv b{font-weight:700}
.mv .pv{font-size:11.5px;color:var(--muted)}
.mv .chg{font-size:12px;text-align:right}
.quiet{display:flex;gap:10px;align-items:baseline;margin:0 16px;padding:7px 0 7px 38px;font-size:12px;color:var(--muted);position:relative;border-top:1px dashed var(--line);border-bottom:1px dashed var(--line);background:repeating-linear-gradient(135deg,transparent 0 6px,color-mix(in srgb,var(--line) 35%,transparent) 6px 7px)}
.quiet[hidden]{display:none}
.qd{font:600 11px var(--mono);color:var(--ink-2);white-space:nowrap}
.endcap{margin:10px 16px 0;padding:14px;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
.endcap[hidden]{display:none}
.ec-h{display:flex;gap:8px;align-items:center;font-weight:700;font-size:14px}
.ec-h .dot{width:8px;height:8px;border-radius:50%;background:var(--ink)}
.endcap p{margin:6px 0 10px;font-size:13px;color:var(--ink-2)}
.stack{width:100%;height:12px;display:block;border-radius:3px}
svg .seg.demo{fill:var(--c-demo)} svg .seg.add{fill:var(--c-add)} svg .seg.newc{fill:var(--c-newc)} svg .seg.ren{fill:var(--c-ren)}
svg .seg.mep{fill:var(--c-mep)} svg .seg.home{fill:var(--c-home)} svg .seg.minor{fill:var(--c-minor)}
.glist{list-style:none;margin:10px 0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:4px 14px;font-size:12px;color:var(--ink-2)}
.glist li{display:flex;align-items:center;gap:6px;min-width:0}
.glist b{margin-left:auto;font-weight:700}
.sw{width:9px;height:9px;border-radius:2px;flex:none;background:var(--c-minor)}
.sw.demo{background:var(--c-demo)} .sw.add{background:var(--c-add)} .sw.ren{background:var(--c-ren)} .sw.mep{background:var(--c-mep)} .sw.home{background:var(--c-home)}
.endcap .go{font-size:13px}

/* map */
.mapcard{padding:10px 10px 8px}
.map{width:100%;height:auto;display:block;max-height:400px}
.bnd{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.4;stroke-linejoin:round}
.pt{fill:var(--muted);opacity:.5}
.pt-big{stroke:var(--surface);stroke-width:1.4}
.bp.add .pt-big{fill:var(--c-add)} .bp.demo .pt-big{fill:var(--c-demo)}
.bp .ring{fill:none;stroke-width:1.2;opacity:.6;transform-box:fill-box;transform-origin:center;animation:ring 3s ease-out infinite}
.bp.add .ring{stroke:var(--c-add)} .bp.demo .ring{stroke:var(--c-demo)}
@keyframes ring{0%{transform:scale(1);opacity:.7}100%{transform:scale(2.6);opacity:0}}
@media (prefers-reduced-motion:reduce){.bp .ring{animation:none;opacity:0}}
.mapkey{display:flex;gap:12px;flex-wrap:wrap;font-size:11.5px;color:var(--muted);padding:6px 4px 0}
.mapkey i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}

/* standing panels */
.stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}
.stats>div{padding:11px 13px;border-top:1px solid var(--line-2);min-width:0}
.stats>div:nth-child(-n+2){border-top:0}
.stats>div:nth-child(even){border-left:1px solid var(--line-2)}
.stats.s3{grid-template-columns:repeat(3,minmax(0,1fr))}
.stats.s3>div{border-top:0;border-left:1px solid var(--line-2)}
.stats.s3>div:first-child{border-left:0}
.sv{font-size:21px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.sk{font-size:11.5px;color:var(--muted);line-height:1.3;margin-top:2px}
.hero{display:flex;justify-content:space-between;align-items:flex-end;gap:14px;padding:14px 13px 12px;border-bottom:1px solid var(--line-2)}
.hero .sv{font-size:32px}
.hero .bars{width:52%;margin:0}
.hero .br{grid-template-columns:44px 1fr 48px}
@media (max-width:520px){.hero{flex-direction:column;align-items:stretch}.hero .bars{width:100%}}
.cta{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 13px;border-top:1px solid var(--line);font-weight:600;font-size:13.5px;color:var(--ink)}
.cta:hover{text-decoration:none;background:var(--surface-2)}
.cta span{color:var(--accent);font-size:12.5px;white-space:nowrap}
.streets-g{display:grid;gap:10px}
.rank{list-style:none;margin:0;padding:6px 13px 4px}
.rank li{display:grid;grid-template-columns:16px minmax(0,1fr) 34px 40px;gap:6px;align-items:baseline;padding:6px 0 7px;border-top:1px solid var(--line-2);font-size:13.5px}
.rank li:first-child{border-top:0}
.rn{font:600 11px var(--mono);color:var(--muted)}
.rname{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rank b{text-align:right}
.rank .chg{font-size:11.5px;text-align:right}
.rbar{grid-column:2 / -1;width:100%;height:6px;display:block;overflow:visible}
.rbar .fill{fill:var(--t-311)} .rbar .tick{fill:var(--ink)}
.legend{display:flex;gap:12px;font-size:11px;color:var(--muted);padding:2px 13px 11px}
.legend i{display:inline-block;vertical-align:1px;margin-right:4px}
.ph{display:flex;justify-content:space-between;align-items:baseline;gap:8px;padding:11px 13px 0;font:600 11px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.ph a{text-transform:none;letter-spacing:0;font-family:var(--font);font-size:12px}

/* reps */
.reps{list-style:none;margin:0;padding:4px 13px}
.reps li{display:grid;grid-template-columns:44px minmax(0,1fr) auto;gap:8px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line-2);font-size:13.5px}
.reps li:first-child{border-top:0}
.smd{font:600 11.5px var(--mono);color:var(--accent)}
.reps a{font-size:11.5px;white-space:nowrap}
.repnote{font-size:11.5px;color:var(--muted);padding:0 13px 11px;margin:0}

/* subscribe + sponsor */
.subp{padding:14px}
.subp h3{font-size:16px;letter-spacing:-.01em}
.subp p{margin:3px 0 0;font-size:13px;color:var(--muted)}
.sub-row{display:flex;gap:8px;margin-top:10px}
.sub-row input{flex:1;min-width:0;height:42px;border:1px solid var(--line);border-radius:8px;padding:0 12px;font:inherit;background:var(--surface-2);color:var(--ink)}
.sub-row button{height:42px;border:0;border-radius:8px;background:var(--ink);color:var(--bg);font:600 14px var(--font);padding:0 16px;cursor:pointer}
.subnote{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px}
.sponsor{margin:16px 16px 0;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 13px;border:1px dashed var(--line);border-radius:10px;font-size:13px;color:var(--ink-2)}
.sponsor small{font:600 10px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}

footer{margin-top:24px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
.foot-in{max-width:1360px;margin:0 auto;padding:16px 16px 28px}
footer p{margin:0 0 6px}
footer strong{color:var(--ink-2)}

/* bottom tab bar (phone + tablet) */
.tabs{position:fixed;left:0;right:0;bottom:0;z-index:30;display:grid;grid-template-columns:repeat(5,1fr);height:calc(var(--tabh) + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom);background:color-mix(in srgb,var(--surface) 94%,transparent);backdrop-filter:blur(10px);border-top:1px solid var(--line)}
.tabs a{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;color:var(--muted);font-size:10.5px;font-weight:600;position:relative}
.tabs a:hover{text-decoration:none}
.tabs svg{width:22px;height:22px}
.tabs a[aria-current="true"]{color:var(--ink)}
.tabs a[aria-current="true"]::before{content:"";position:absolute;top:0;left:28%;right:28%;height:2.5px;border-radius:0 0 3px 3px;background:var(--accent)}
.tabs a[data-tab="feed"] .badge{position:absolute;top:8px;left:calc(50% + 6px);min-width:16px;height:16px;padding:0 4px;border-radius:8px;background:var(--up);color:#fff;font:700 9.5px/16px var(--mono);text-align:center}

/* ---------- desktop: three columns ---------- */
@media (min-width:1100px){
  body{padding-bottom:0;font-size:15.5px}
  html{scroll-padding-top:12px}
  :root{--vh:0px}
  .tabs{display:none}
  .top-in{grid-template-columns:auto 1fr auto;align-items:center;gap:28px;padding:14px 28px}
  .top-search{max-width:520px;width:100%;justify-self:center}
  .shint{display:none}
  .status{justify-self:end}
  .app{display:grid;grid-template-columns:280px minmax(0,1fr) 372px;gap:28px;max-width:1360px;padding:0 28px;align-items:start}
  .col,.stick{display:block;min-width:0}
  .col-l .stick,.col-r .stick{position:sticky;top:16px;padding-top:20px}
  .blk{padding:0}
  .vitals{position:static;height:auto;display:block;background:var(--surface);border:1px solid var(--line);border-radius:12px;backdrop-filter:none;overflow:hidden}
  .vh{display:flex;justify-content:space-between;align-items:center;padding:11px 14px 9px;font:600 11px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);border-bottom:1px solid var(--line-2)}
  .vh span{display:flex;align-items:center;gap:7px}
  .v,.v:first-of-type{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"l l" "v c" "s s";gap:2px 8px;padding:10px 14px;border-left:0;border-top:1px solid var(--line-2)}
  .vh+.v{border-top:0}
  .v4{display:grid}
  .vl{grid-area:l;font-size:10px} .vl .lg{display:inline} .vl .st{display:none}
  .vv{grid-area:v;margin-top:1px}
  .vv b{font-size:22px}
  .vv .chg{font-size:12px}
  .vc{display:block;grid-area:c;align-self:end;font:500 11.5px var(--mono);color:var(--muted);text-align:right}
  .vs{display:block;grid-area:s;width:100%;height:10px;margin-top:5px}
  .filters{padding:0;margin-top:14px}
  .fh{display:block;font:600 11px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 6px 2px}
  .fl{flex-direction:column;gap:2px}
  .fb,.fb[data-f="all"]{width:100%;border-radius:8px;border-color:transparent;background:transparent;padding:7px 10px;font-size:13.5px}
  .fb:hover{background:var(--surface)}
  .fb b{margin-left:auto}
  .fb[data-f="all"]::before{content:"";width:14px}
  .sponsor{margin:14px 0 0}
  #feed .feed-h{padding:22px 4px 6px}
  .dh{top:0;padding:10px 4px 8px;font-size:13.5px}
  .items{padding:8px 0 6px}
  .items::before{left:12.5px}
  .it{gap:14px;padding:7px 0}
  .card{padding:12px 14px 13px}
  .hd{font-size:16px}
  .bd{font-size:13px}
  .lh{font-size:23px;line-height:1.25}
  .lead .card{padding:15px 16px 14px}
  .quiet{margin:0;padding-left:40px}
  .endcap{margin:12px 0 0}
  .glist{grid-template-columns:repeat(3,minmax(0,1fr))}
  .standing{display:block}
  .fb[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
  .stats.s3 .sv{font-size:24px}
  #map .sh{margin-top:0}
  .map{max-height:330px}
  #you .sh{margin-top:18px}
  #feed,#homes,#streets,#subscribe{order:0}
}
@media (min-width:1100px) and (max-height:880px){
  .map{max-height:270px}
}
"""

JS = r"""
(function(){
  var btns=[].slice.call(document.querySelectorAll('.fb'));
  btns.forEach(function(b){b.addEventListener('click',function(){
    var f=b.getAttribute('data-f');
    btns.forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});
    document.querySelectorAll('.it,.quiet,.endcap').forEach(function(r){
      var t=(r.getAttribute('data-t')||'').split(' ');
      r.hidden=!(f==='all'||t.indexOf(f)>-1);
    });
    document.querySelectorAll('.day').forEach(function(d){d.classList.toggle('empty',!d.querySelector('.it:not([hidden])'))});
    var feed=document.getElementById('feed'); if(feed.getBoundingClientRect().top<0) feed.scrollIntoView();
  })});
  var tabs=[].slice.call(document.querySelectorAll('.tabs a'));
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(en){
      if(en.isIntersecting){tabs.forEach(function(t){t.setAttribute('aria-current',String(t.getAttribute('data-tab')===en.target.id))})}
    })},{rootMargin:'-45% 0px -50% 0px'});
    ['feed','map','homes','streets','you'].forEach(function(id){var el=document.getElementById(id); if(el) io.observe(el)});
  }
})();
"""

new_this_week = sum(1 for p in projects if (today - p["day"]).days <= 7)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Petworth Live</title>
<meta name="description" content="What's changing in Petworth, Washington DC, from DC's own open data. Independent; updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="Petworth feed" href="/petworth/permits.xml">
<style>{CSS}</style>
</head>
<body>
<div class="layout-tag">Layout C1: Live Feed</div>

<header class="top">
  <div class="top-in">
    <div class="brand">
      <div class="mark" aria-hidden="true">P</div>
      <div><h1>{e(FACTS['neighborhood'])}</h1><p>What's changing in Petworth, from DC's own data</p></div>
    </div>
    <div class="top-search">
      <label class="sbox" for="q">{ICON_SEARCH}<input id="q" type="search" placeholder="Look up your block or building" autocomplete="off"><button type="button">Go</button></label>
      <div class="shint">Opens your <a href="{link('Block report card')}">block report card</a> or <a href="{link('Building biography')}">building biography</a></div>
    </div>
    <div class="status"><span class="live" aria-hidden="true"></span><span>Data as of <b><time datetime="{FACTS['generated_at']}">{md(today)}, {clock} ET</time></b><span class="nx"> · next update tonight</span></span></div>
  </div>
</header>
<div class="ticker" aria-label="Latest changes"><div class="tk-track"><div style="display:inline-flex">{ticker_one}</div><div style="display:inline-flex" aria-hidden="true">{ticker_one}</div></div></div>

<div class="app">

  <aside class="col col-l"><div class="stick">
    <nav class="vitals" aria-label="Vitals">
      <div class="vh"><span><span class="live" aria-hidden="true"></span>Vitals</span><span>vs prior period</span></div>
      {vitals_html}
    </nav>
    <div class="filters">
      <div class="fh">Show in feed</div>
      <div class="fl" role="group" aria-label="Filter the feed">{filters_html}</div>
    </div>
    <div class="sponsor"><span>Presented by <b>[Local sponsor]</b></span><small>Sponsor</small></div>
  </div></aside>

  <main class="col col-c">
    <section id="feed" aria-label="Feed">
      <div class="feed-h"><h2><span class="live" aria-hidden="true"></span>Petworth feed</h2><a href="/petworth/permits.xml">RSS</a></div>
      {''.join(feed)}
      {endcap}
    </section>

    <div class="standing">
      <section id="homes" class="blk">
        <div class="sh"><h2>Homes</h2><a href="{link('Housing pulse')}">Housing pulse →</a></div>
        <div class="panel">
          <div class="hero">
            <div><div class="sv num">{homes['median_house_price_12mo']}</div><div class="sk">median house price, 12 months</div></div>
            {bars(med60, med12, "neutral", "60d", "12 mo").replace(f'>{med60}<', f'>{homes["median_price_60d"]}<').replace(f'>{med12}<', f'>{homes["median_house_price_12mo"]}<')}
          </div>
          <div class="stats">
            <div><div class="sv num">{homes['house_sales_12mo']}</div><div class="sk">house sales, 12 months</div></div>
            <div><div class="sv num">{homes['median_condo_price_12mo']}</div><div class="sk">median condo, {homes['condo_sales_12mo']} sales, 12 mo</div></div>
            <div><div class="sv num">{homes['market_sales_60d']}</div><div class="sk">sales, last 60 days</div></div>
            <div><div class="sv num">{homes['median_price_per_sqft_60d']}</div><div class="sk">median per sq ft, 60 days</div></div>
          </div>
          <a class="cta" href="{link('Assessment check')}">{homes['sold_above_assessment_12mo']} sales went above assessment. Yours? <span>Assessment check →</span></a>
        </div>
      </section>

      <section id="streets" class="blk">
        <div class="sh"><h2>Streets</h2><a href="{link('Curb radar')}">Curb radar →</a></div>
        <div class="streets-g">
          <div class="panel">
            <div class="stats s3">
              <div><div class="sv num">{streets['curb_permits_active_this_week']}</div><div class="sk">curb permits active this week</div></div>
              <div><div class="sv num">{streets['curb_permits_starting_next_7d']}</div><div class="sk">starting in the next 7 days</div></div>
              <div><div class="sv num">{fmt(streets['curb_reserved_ft'])}</div><div class="sk">feet of curb reserved</div></div>
            </div>
          </div>
          <div class="panel">
            <div class="ph"><span>Top 311 requests · 30 days</span><a href="{link('311 report card')}">All types →</a></div>
            <ol class="rank">{rank_rows}</ol>
            <div class="legend"><span><i style="width:10px;height:6px;background:var(--t-311)"></i>Last 30 days</span><span><i style="width:2px;height:9px;background:var(--ink)"></i>30 days before</span></div>
          </div>
          <div class="panel">
            <div class="stats s3">
              <div><div class="sv num">{fmt(trees['street_trees'])}</div><div class="sk">street trees, {trees['species']} species</div></div>
              <div><div class="sv num">{trees['planted_last_5y']}</div><div class="sk">planted in 5 years</div></div>
              <div><div class="sv num" style="color:var(--accent)">{trees['empty_boxes_open']}</div><div class="sk">empty tree boxes open</div></div>
            </div>
            <a class="cta" href="{link('Street trees')}">Find an empty tree box near you <span>Street trees →</span></a>
          </div>
        </div>
      </section>
    </div>

    <section id="subscribe" class="blk">
      <div class="sh"><h2>This feed, weekly</h2><a href="{link('Weekly email')}">See a sample →</a></div>
      <div class="panel subp">
        <h3>Get the week in Petworth by email</h3>
        <p>Every item above, once a week, with the numbers that changed.</p>
        <form class="sub-row" onsubmit="return false"><input type="email" placeholder="you@example.com" aria-label="Email address"><button type="button">Subscribe</button></form>
        <div class="subnote"><span>One email a week. Mock signup.</span><a href="/petworth/permits.xml">Or follow the RSS feed</a></div>
      </div>
    </section>
  </main>

  <aside class="col col-r"><div class="stick">
    <section id="map" class="blk">
      <div class="sh"><h2>Permits on the map</h2><span>last 30 days</span></div>
      <div class="panel mapcard">
        {map_svg()}
        <div class="mapkey"><span><i style="background:var(--c-add)"></i>Addition ({groups.get('Additions', 0)})</span><span><i style="background:var(--c-demo)"></i>Demolition ({groups.get('Demolition', 0)})</span><span><i style="background:var(--muted);opacity:.55"></i>Other permit</span></div>
      </div>
    </section>
    <section id="you" class="blk">
      <div class="sh"><h2>Your representatives</h2><span>{len(reps)} SMDs · ANC {' & '.join(ancs)}</span></div>
      <div class="panel">
        <ul class="reps">{rep_rows}</ul>
        <p class="repnote">Each Single Member District elects one commissioner. Names of elected officials are public record. <a href="{link('Block report card')}">Find your SMD by address →</a></p>
      </div>
    </section>
  </div></aside>

</div>

<footer><div class="foot-in">
  <p><strong>Independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission, or any Business Improvement District.</strong></p>
  <p>Sources: Open Data DC (CC BY 4.0); Library of Congress, Chronicling America. Crime figures are preliminary counts. Data as of {asof_long}.</p>
  <p>petworth.org</p>
</div></footer>

<nav class="tabs" aria-label="Sections">{tabs_html.replace('<span>Feed</span>', f'<span>Feed</span><b class="badge">{new_this_week}</b>', 1)}</nav>
<script>{JS}</script>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
