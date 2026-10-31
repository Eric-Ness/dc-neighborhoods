"""Layout C5: C3 layout + C4 data. Reads design/layouts/facts.json, writes design/layouts/C5-hybrid.html.

C3 ("Vital Signs") supplies the page: header, pill nav, the "Today's condition" card,
the two-column card composition, the soft palette and a plain-English reading under each
measure. C4 ("Map Console") supplies the data presentation: paired horizontal bars with
signed deltas, compact tabular rows, and the interactive gridded map with numbered
bigger-project markers that link to the project rows.

Run from anywhere:  python design/layouts/src/C5_hybrid.py
Python 3.13 stdlib only.
"""
from __future__ import annotations

import html
import itertools
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYOUTS = HERE.parent
FACTS = json.loads((LAYOUTS / "facts.json").read_text(encoding="utf-8"))
OUT = LAYOUTS / "C5-hybrid.html"

e = html.escape

STEADY_BAND = 0.05   # within ±5% of the comparison reads as "steady" (from C3)


# ---------- helpers (C3 + C4) ----------
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
        return dt.astimezone(timezone(timedelta(hours=-4 if mar <= dt < nov else -5)))


def price_k(s: str) -> int:
    return int(re.sub(r"[^\d]", "", s.split()[0]))


SIGN = lambda d: "+" if d > 0 else ("−" if d < 0 else "±")


def reading(cur: float, prev: float) -> dict:
    """C3 state + C4 signed delta. Percentages only when both counts are 100 or more."""
    d = cur - prev
    ratio = d / prev if prev else 0.0
    state = "steady" if abs(ratio) < STEADY_BAND else ("rising" if d > 0 else "easing")
    pct = round(ratio * 100) if (cur >= 100 and prev >= 100) else None
    txt = f"{SIGN(d)}{fmt(abs(d))}" + (f" ({SIGN(d)}{abs(pct)}%)" if pct is not None else "")
    return {"d": d, "state": state, "pct": pct, "txt": txt}


STATE_WORD = {"rising": "Rising", "easing": "Easing", "steady": "Steady"}


def icon(state: str, cls: str = "ic") -> str:
    """Shape-coded state glyph (▲ ▼ –), drawn as SVG so it aligns and inherits color."""
    shapes = {
        "rising": '<path d="M6 1.5 L11 10.5 H1 Z"/>',
        "easing": '<path d="M6 10.5 L11 1.5 H1 Z"/>',
        # Two bars ("equals"), so it never reads as a minus sign next to a negative number.
        "steady": '<rect x="1" y="2.5" width="10" height="2.2" rx="1.1"/><rect x="1" y="7.3" width="10" height="2.2" rx="1.1"/>',
    }
    return f'<svg class="{cls}" viewBox="0 0 12 12" aria-hidden="true">{shapes[state]}</svg>'


def state_tag(state: str) -> str:
    return f'<span class="tag s-{state}">{icon(state)}{STATE_WORD[state]}</span>'


def bar(cur: float, m: float, cls: str) -> str:
    return (f'<svg class="hb" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true">'
            f'<rect class="trk" width="100" height="8" rx="1"/><rect class="{cls}" width="{max(100 * cur / m, 0.6):.1f}" height="8" rx="1"/></svg>')


def pair(cur_lbl, cur, cur_txt, prev_lbl, prev, prev_txt, cur_cls) -> str:
    """C4's paired bars: the latest period over the earlier one, values right-aligned."""
    m = max(cur, prev) or 1
    return (f'<div class="cr-r"><span class="k">{cur_lbl}</span>{bar(cur, m, cur_cls)}<span class="v num">{cur_txt}</span></div>'
            f'<div class="cr-r"><span class="k">{prev_lbl}</span>{bar(prev, m, "prev")}<span class="v num">{prev_txt}</span></div>')


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

SHORT = {"DC Health Rodent & Vector Control": "Rodent & vector control"}
LEAD_NAME = {"DC Health Rodent & Vector Control": "Rodent complaints"}
short_type = lambda t: SHORT.get(t, t)

movers = [dict(m, r=reading(m["count"], m["previous"])) for m in tm["top_311_movers"]]
rises = sorted([m for m in movers if m["r"]["d"] > 0], key=lambda m: -m["r"]["d"])
lead = rises[0] if rises else max(movers, key=lambda m: abs(m["r"]["d"]))
others = [m for m in movers if m is not lead]
lr = lead["r"]

req_r = reading(tm["requests_30d"], tm["requests_prev_30d"])
crime_r = reading(tm["crime_30d"], tm["crime_prev_30d"])
med12 = price_k(homes["median_house_price_12mo"])
med60 = price_k(homes["median_price_60d"])
price_r = reading(med60, med12)
price_txt = f"{SIGN(med60 - med12)}${abs(med60 - med12)}K ({SIGN(med60 - med12)}{abs(price_r['pct'])}%)"

# permit categories (C4), coloured with C3's group palette
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
BIG = ["Demolition", "New construction", "Additions"]
permits_total = tm["permits_30d"]
big_count = sum(groups.get(g, 0) for g in BIG)
present = [(k, g, s, kind) for k, g, s, kind in CATS if groups.get(g)]


def glyph(kind: str, key: str = "") -> str:
    inner = {
        "num": f'<circle cx="7" cy="7" r="5.5" class="gl-{key or "add"}"/>',
        "numsq": '<rect x="2" y="2" width="10" height="10" rx="1" class="gl-demo"/>',
        "dot": '<circle cx="7" cy="7" r="3.2" class="gl-ink"/>',
        "ring": '<circle cx="7" cy="7" r="3" class="gl-ring"/>',
        "sq": '<rect x="4" y="4" width="6" height="6" class="gl-ink2"/>',
        "small": '<circle cx="7" cy="7" r="2" class="gl-mut"/>',
    }[kind]
    return f'<svg class="gl" viewBox="0 0 14 14" width="14" height="14" aria-hidden="true">{inner}</svg>'


# ---------- marker-to-project matching ----------
# permit_points carry no address, so C4 paired each bigger project with the next unused point
# of the same permit group, in file order. C5 keeps that as the tie-break but first checks
# every same-group assignment against what the address itself says about position on DC's
# grid: on Petworth's lettered east-west streets, a higher house number sits farther west,
# and a later street name (Delafield < Emerson < Farragut < Gallatin) sits farther north.
# The assignment with the fewest order contradictions wins.
pts = FACTS["permit_points"]
LETTERED = re.compile(r"^(\d+)\s+([A-Z]+)\s+(ST|PL|RD|TER|CT)\b")


def addr_hint(a: str):
    m = LETTERED.match(a.strip())
    return (int(m.group(1)), m.group(2)) if m else None


def inversions(projs, points) -> int:
    bad = 0
    for (pa, qa), (pb, qb) in itertools.combinations(zip(projs, points), 2):
        ha, hb = addr_hint(pa["address"]), addr_hint(pb["address"])
        if not ha or not hb:
            continue
        if ha[0] != hb[0] and (ha[0] > hb[0]) != (qa["lon"] < qb["lon"]):
            bad += 1   # house numbers say one is west of the other; the points disagree
        if ha[1] != hb[1] and (ha[1] > hb[1]) != (qa["lat"] > qb["lat"]):
            bad += 1   # street names say one is north of the other; the points disagree
    return bad


match: dict[int, int] = {}
match_report = []
for g in BIG:
    pidx = [i for i, p in enumerate(FACTS["bigger_projects"]) if p["group"] == g]
    cidx = [j for j, q in enumerate(pts) if q["group"] == g]
    if not pidx or not cidx:
        continue
    k = min(len(pidx), len(cidx))
    projs = [FACTS["bigger_projects"][i] for i in pidx[:k]]
    best, best_key = None, None
    perms = itertools.permutations(cidx, k) if math.perm(len(cidx), k) <= 200_000 else [tuple(cidx[:k])]
    for perm in perms:
        key = (inversions(projs, [pts[j] for j in perm]), sum(abs(a - b) for a, b in zip(perm, cidx)))
        if best_key is None or key < best_key:
            best, best_key = perm, key
    for i, j in zip(pidx, best):
        match[i] = j
    match_report.append(f"{g}: {k} matched, {best_key[0]} order contradictions"
                        + (" (same as C4's file-order pairing)" if tuple(best) == tuple(cidx[:k]) else " (reordered vs C4)"))
used = set(match.values())

projects = []
for i, p in enumerate(FACTS["bigger_projects"]):
    issued = datetime.fromisoformat(p["issued"].replace("Z", "+00:00"))
    age = (gen.date() - issued.date()).days
    projects.append({
        "n": i + 1, "id": f"p{i + 1}", "addr": addr(p["address"]), "group": p["group"], "key": GKEY[p["group"]],
        "issued": issued, "date": f"{issued.strftime('%b')} {issued.day}", "new": 0 <= age <= 7,
        "work": clean_work(p["work"]), "pt": pts[match[i]] if i in match else None,
    })
new_count = sum(p["new"] for p in projects)

# ---------- map (C4) ----------
rings = FACTS["boundary_rings"]
allp = [q for r in rings for q in r]
minx, maxx = min(q[0] for q in allp), max(q[0] for q in allp)
miny, maxy = min(q[1] for q in allp), max(q[1] for q in allp)
MARG = 0.0012
F_W, F_E = math.floor((minx - MARG) / 0.0005) * 0.0005, math.ceil((maxx + MARG) / 0.0005) * 0.0005
F_S, F_N = math.floor((miny - MARG) / 0.0005) * 0.0005, math.ceil((maxy + MARG) / 0.0005) * 0.0005
KLAT = math.cos(math.radians((miny + maxy) / 2))
VBW = 600.0
SC = VBW / ((F_E - F_W) * KLAT)
VBH = (F_N - F_S) * SC
X = lambda lon: (lon - F_W) * KLAT * SC
Y = lambda lat: (F_N - lat) * SC
M_PER_UNIT = 111_320 / SC
CENTER = ((miny + maxy) / 2, (minx + maxx) / 2)


def map_svg() -> str:
    out = []
    ext = 0.03   # faint grid continues past the frame into any letterbox space
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
    d = " ".join("M" + "L".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in r) + "Z" for r in rings)
    out.append(f'<path class="bnd-halo" d="{d}"/><path class="bnd" d="{d}"/>')
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
    sb = 500 / M_PER_UNIT
    out.append(f'<g transform="translate({VBW - 16 - sb:.1f},{VBH - 16:.1f})">'
               f'<path class="sb" d="M0,0H{sb:.1f}M0,-5V0M{sb / 2:.1f},-3V0M{sb:.1f},-5V0"/>'
               f'<g class="s"><text class="gt" x="0" y="-8">0</text></g>'
               f'<g transform="translate({sb:.1f},0)"><g class="s"><text class="gt" x="0" y="-8" text-anchor="end">500 m</text></g></g></g>')
    out.append(f'<g transform="translate({VBW - 22:.0f},24)"><g class="s"><path class="na" d="M0,-12L6,6L0,2L-6,6Z"/>'
               f'<text class="gt" x="0" y="18" text-anchor="middle">N</text></g></g>')
    small = []
    for j, q in enumerate(pts):
        if j in used:
            continue
        key = GKEY.get(q["group"], "minor")
        shape = {"mep": '<circle r="3"/>', "home": '<rect x="-3" y="-3" width="6" height="6"/>',
                 "minor": '<circle r="2.2"/>'}.get(key, '<circle r="3.4"/>')
        small.append(f'<g class="pt c-{key}" transform="translate({X(q["lon"]):.1f},{Y(q["lat"]):.1f})"><g class="s">{shape}</g>'
                     f'<title>{e(q["group"])}</title></g>')
    out.append(f'<g class="pts">{"".join(small)}</g>')
    bigm = []
    for p in reversed(projects):
        q = p["pt"]
        if not q:
            continue
        shape = ('<rect class="mk-b" x="-9" y="-9" width="18" height="18" rx="2"/>' if p["key"] == "demo"
                 else '<circle class="mk-b" r="9.5"/>')
        bigm.append(
            f'<g class="mk c-{p["key"]}" data-id="{p["id"]}" data-lat="{q["lat"]}" data-lon="{q["lon"]}" data-addr="{e(p["addr"])}" '
            f'tabindex="0" role="button" aria-label="Project {p["n"]}: {e(p["addr"])}, {e(p["group"])}. Go to its row." '
            f'transform="translate({X(q["lon"]):.1f},{Y(q["lat"]):.1f})"><g class="s ms">'
            f'<circle class="mk-halo" r="17"/>{shape}<text class="mk-t" y="3.6" text-anchor="middle">{p["n"]}</text></g></g>')
    out.append(f'<g class="mks">{"".join(bigm)}</g>')
    return (f'<svg id="map" class="map" viewBox="0 0 {VBW:.0f} {VBH:.1f}" preserveAspectRatio="xMidYMid meet" '
            f'data-w="{F_W}" data-n="{F_N}" data-k="{KLAT}" data-sc="{SC}" role="img" '
            f'aria-label="Map of Petworth: {permits_total} building permits from the last 30 days. Numbered markers are the {len(projects)} bigger projects listed beside the map.">'
            + "".join(out) + "</svg>")


chips = (f'<button type="button" class="chip all" data-all aria-pressed="true"><span class="cl">All</span><b class="num">{permits_total}</b></button>'
         + "".join(f'<button type="button" class="chip" data-g="{k}" aria-pressed="true">{glyph(kind, k)}'
                   f'<span class="cl">{e(s)}</span><b class="num">{groups[g]}</b></button>' for k, g, s, kind in present))

maxg = max(groups.values())
mix_rows = "".join(
    f'<li><button type="button" class="mixrow" data-g="{k}" aria-pressed="true">{glyph(kind, k)}'
    f'<span class="ml">{e(g)}</span>{bar(groups[g], maxg, "fill c-" + k if g in BIG else "fill")}'
    f'<b class="num">{groups[g]}</b></button></li>'
    for k, g, s, kind in present)

# ---------- measures (C3 vitals, C4 bars) ----------
def _biggest_drops() -> str:
    falls = sorted((t for t in tm["top_311_types"] if t["count"] < t["previous"]), key=lambda t: t["count"] - t["previous"])[:2]
    if not falls:
        return ""
    names = [f"{short_type(t['type']).lower()} (−{t['previous'] - t['count']})" for t in falls]
    return f"Biggest falls: {' and '.join(names)}."


crime_read = (f"Counts this small swing from month to month: {abs(crime_r['d'])} "
              f"{'more' if crime_r['d'] > 0 else 'fewer'} than the 30 days before. Shown as counts only.")
MEASURES = [
    {
        "name": "311 requests", "href": link("311 report card"), "state": req_r["state"], "chg": req_r["txt"],
        "bars": pair("Last 30 days", tm["requests_30d"], fmt(tm["requests_30d"]),
                     "30 days before", tm["requests_prev_30d"], fmt(tm["requests_prev_30d"]), "fill s-" + req_r["state"]),
        "read": (f"{fmt(abs(req_r['d']))} {'fewer' if req_r['d'] < 0 else 'more'} requests than the 30 days before. "
                 + _biggest_drops()),
    },
    {
        "name": "Crime reports", "href": link("Block report card"), "state": "neutral",
        "sub": f"{tm['crime_30d']} reports · {tm['crime_prev_30d']} the 30 days before",
        "glyph": crime_r["state"], "chg": crime_r["txt"],
        "bars": pair("Last 30 days", tm["crime_30d"], fmt(tm["crime_30d"]),
                     "30 days before", tm["crime_prev_30d"], fmt(tm["crime_prev_30d"]), "fill neutral"),
        "read": crime_read,
    },
    {
        "name": "Median house price", "href": "#homes", "state": price_r["state"], "chg": price_txt,
        "bars": pair("Last 60 days", med60, homes["median_price_60d"],
                     "12 months", med12, homes["median_house_price_12mo"], "fill s-" + price_r["state"]),
        "read": (f"The last 60 days' median sits ${abs(med12 - med60)}K "
                 f"{'under' if med60 < med12 else 'over'} the 12-month median, within 5%, so steady. "
                 f"Only {homes['market_sales_60d']} sales in 60 days."),
    },
    {
        "name": "Building permits", "href": "#projects", "state": "mix", "chg": f"{permits_total} issued",
        "bars": pair("Bigger projects", big_count, fmt(big_count),
                     "Smaller jobs", permits_total - big_count, fmt(permits_total - big_count), "fill c-add"),
        "read": (f"{groups.get('Additions', 0)} additions and {groups.get('Demolition', 0)} demolition; the rest are "
                 f"smaller jobs. No prior-month count in this feed, so this shows a mix, not a change."),
    },
]
MIX_ICON = '<svg class="ic" viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/></svg>'


def measure_html(m: dict) -> str:
    st = m["state"]
    if st == "neutral":
        tag = ""
        chg = f'<span class="chg s-neutral">{icon(m["glyph"])}{m["chg"]}</span>'
        sub = f'<div class="v-sub num">{e(m["sub"])}</div>'
    elif st == "mix":
        tag = f'<span class="tag s-mix">{MIX_ICON}Mix</span>'
        chg = f'<span class="chg s-mix">{m["chg"]}</span>'
        sub = ""
    else:
        tag = state_tag(st)
        chg = f'<span class="chg s-{st}">{icon(st)}{m["chg"]}</span>'
        sub = ""
    return f"""
<a class="vital" href="{m['href']}">
  <div class="v-top"><span class="v-name">{e(m['name'])}</span>{tag}</div>
  {sub}<div class="v-chg">{chg}</div>
  <div class="cmp">{m['bars']}</div>
  <p class="v-read">{e(m['read'])}</p>
</a>"""


measures_html = "".join(measure_html(m) for m in MEASURES)

# condition summary: graded readings only; crime is shown as counts, not graded
graded = [lr["state"]] + [m["r"]["state"] for m in others] + [req_r["state"], price_r["state"]]
counts = {s: graded.count(s) for s in ("rising", "easing", "steady")}
cond_strip = "".join(
    f'<li class="s-{s}">{icon(s)}<b class="num">{counts[s]}</b> {STATE_WORD[s].lower()}</li>' for s in ("rising", "easing", "steady")
)
cond_word = (("Mostly easing" if counts["easing"] > counts["rising"] else "Mixed")
             + f", with {counts['rising']} reading{'s' if counts['rising'] != 1 else ''} rising")

also = "".join(
    f'<li><span class="chg s-{m["r"]["state"]} ar">{icon(m["r"]["state"])}</span>'
    f'<span class="al">{e(short_type(m["type"]))}</span><span class="anum num"><b class="av">{m["count"]}</b> '
    f'<span class="ap">from {m["previous"]}</span></span><span class="chg s-{m["r"]["state"]} num ad">{m["r"]["txt"]}</span></li>'
    for m in others)

# ---------- projects (C4 rows, numbered to match the map) ----------
proj_rows = "".join(f"""
<li class="prow c-{p['key']}" data-id="{p['id']}" id="row-{p['id']}" tabindex="0" aria-label="Project {p['n']}, {e(p['addr'])}">
  <span class="pn {'sq' if p['key'] == 'demo' else ''} num" aria-hidden="true">{p['n']}</span>
  <div class="pb">
    <div class="pt1"><span class="paddr">{e(p['addr'])}</span><time class="pdate num" datetime="{p['issued'].date().isoformat()}">{p['date']}</time></div>
    <div class="pt2"><span class="ptype">{'Addition' if p['group'] == 'Additions' else e(p['group'])}</span>{'<span class="new">New this week</span>' if p['new'] else ''}{f'<span class="coord num">{p["pt"]["lat"]:.4f}°N {abs(p["pt"]["lon"]):.4f}°W</span>' if p['pt'] else ''}</div>
    <div class="pwork">{e(p['work'])}</div>
  </div>
</li>""" for p in projects)

# ---------- 311 ranked table (C4) ----------
max311 = max(max(t["count"], t["previous"]) for t in tm["top_311_types"])
rank_rows = ""
for i, t in enumerate(tm["top_311_types"], 1):
    r = reading(t["count"], t["previous"])
    rank_rows += f"""
<tr>
  <td class="ri num">{i:02d}</td>
  <td class="rn"><span>{e(short_type(t['type']))}</span>
    <svg class="rb" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="6"/><rect class="fill s-{r['state']}" width="{100 * t['count'] / max311:.1f}" height="6"/><rect class="tick" x="{100 * t['previous'] / max311 - 0.5:.1f}" y="-2" width="1" height="10"/></svg></td>
  <td class="rc num">{t['count']}</td>
  <td class="rp num">{t['previous']}</td>
  <td class="rd num"><span class="chg s-{r['state']}">{icon(r['state'])}{r['txt'].split(' ')[0]}</span></td>
</tr>"""

# ---------- homes as a tight table ----------
above, of_n = homes["sold_above_assessment_12mo"].split(" of ")
home_rows = [
    ("Median price", "last 60 days", homes["median_price_60d"], f"{homes['market_sales_60d']} sales"),
    ("Price per sq ft", "last 60 days", homes["median_price_per_sqft_60d"], "median"),
    ("Median condo", "12 months", homes["median_condo_price_12mo"], f"{homes['condo_sales_12mo']} sales"),
    ("Sold above assessment", "12 months", f"{above} <small>of {of_n}</small>", "sales"),
]
homes_tbl = "".join(
    f'<tr><th scope="row">{a}<span>{b}</span></th><td class="hv num">{v}</td><td class="hn num">{n}</td></tr>'
    for a, b, v, n in home_rows)

curb_mi = streets["curb_reserved_ft"] / 5280

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
  --track:#ebe8e1; --prevbar:#cbc7bd; --neutral:#4f5a5d;
  --grid-f:#e6e3db; --grid-m:#d5d1c7; --map-bg:#f3f1ec;
  --c-demo:#b05a36; --c-add:#466f60; --c-newc:#7a6a45; --on-mk:#ffffff;
  --sans:"Instrument Sans", "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, "Cascadia Mono", Consolas, Menlo, monospace;
  --r:16px;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#151b1d; --surface:#1d2528; --surface-2:#192023; --ink:#e8ebe8; --ink-2:#c3cac7; --muted:#8f9a97;
    --line:#2e383b; --line-2:#263033; --accent:#8fbfa9; --accent-soft:#22332d;
    --rising:#e39a76; --rising-soft:#3a2a22; --easing:#8fb6d3; --easing-soft:#1f2e39; --steady:#a3aca8; --steady-soft:#283033;
    --mix:#cdb886; --track:#263033; --prevbar:#4a5558; --neutral:#b9c1be;
    --grid-f:#232c2f; --grid-m:#30393c; --map-bg:#192023;
    --c-demo:#e39a76; --c-add:#8fbfa9; --c-newc:#cdb886; --on-mk:#151b1d;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.wrap{max-width:1240px;margin:0 auto;padding:0 16px}
.layout-tag{background:var(--ink);color:var(--bg);font:600 11px/1 var(--mono);letter-spacing:.06em;padding:7px 16px}

/* header (C3) */
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

/* panels */
main{padding:14px 0 28px}
.row{display:grid;gap:14px;margin-top:14px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px;min-width:0}
.ph{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin:0 0 12px}
.ph h2{margin:0;font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2)}
.ph a,.ph .sub{font-size:12.5px;color:var(--muted);text-decoration:none;white-space:nowrap}
.ph a{color:var(--accent);font-weight:600}
section,[id]{scroll-margin-top:14px}

/* state tokens: shape + colour */
.ic{width:10px;height:10px;flex:none;fill:currentColor}
.s-rising{color:var(--rising)} .s-easing{color:var(--easing)} .s-steady{color:var(--steady)} .s-mix{color:var(--mix)} .s-neutral{color:var(--muted)}
.tag{display:inline-flex;align-items:center;gap:5px;font:600 11px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;padding:5px 8px 5px 7px;border-radius:999px;white-space:nowrap}
.tag.s-rising{background:var(--rising-soft)} .tag.s-easing{background:var(--easing-soft)} .tag.s-steady{background:var(--steady-soft)} .tag.s-mix{background:var(--surface-2);border:1px solid var(--line)}
.chg{display:inline-flex;align-items:center;gap:4px;font:600 13px/1 var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
.chg.s-neutral{font-weight:500}

/* paired bars (C4) */
.cmp{display:grid;gap:3px}
.cr-r{display:grid;grid-template-columns:96px minmax(0,1fr) 56px;gap:10px;align-items:center;font-size:12px;color:var(--muted)}
.cr-r .v{text-align:right;color:var(--ink);font-weight:600;font-size:13.5px}
.cr-r+.cr-r .v{color:var(--ink-2);font-weight:500}
.hb{width:100%;height:9px;display:block}
svg .trk{fill:var(--track)}
svg .prev{fill:var(--prevbar)}
svg .fill{fill:var(--ink-2)}
svg .fill.s-rising{fill:var(--rising)} svg .fill.s-easing{fill:var(--easing)} svg .fill.s-steady{fill:var(--steady)}
svg .fill.neutral{fill:var(--neutral)}
svg .fill.c-add{fill:var(--c-add)} svg .fill.c-demo{fill:var(--c-demo)} svg .fill.c-newc{fill:var(--c-newc)}
svg .tick{fill:var(--ink)}

/* condition (C3) */
.cond{display:grid;gap:18px;padding:22px 18px;background:var(--surface);border:1px solid var(--line);border-radius:20px}
.c-kick{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font:600 12px/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.c-head{margin:10px 0 0;font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.015em;text-wrap:pretty}
.c-word{margin:12px 0 0;color:var(--ink-2);font-size:15px}
.c-strip{list-style:none;margin:14px 0 0;padding:0;display:flex;gap:8px;flex-wrap:wrap}
.c-strip li{display:inline-flex;align-items:center;gap:6px;font-size:13px;padding:6px 11px;border-radius:999px;border:1px solid var(--line);background:var(--surface-2)}
.c-strip li b{color:var(--ink)}
.c-box{background:var(--surface-2);border-radius:14px;padding:14px 16px;border:1px solid var(--line-2);min-width:0}
.c-box .ph{margin-bottom:10px}
.c-lead{display:block;color:inherit;text-decoration:none}
.c-lead .lh{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:8px}
.c-lead .lh b{font-size:15px}
.c-lead .chg{font-size:15px}
.also-h{font:600 11px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:16px 0 2px;padding-top:12px;border-top:1px solid var(--line)}
.also{list-style:none;margin:0;padding:0}
.also li{display:grid;grid-template-columns:12px minmax(0,1fr) auto;grid-template-areas:"ar al ad" "ar anum anum";gap:2px 8px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line-2);font-size:13.5px}
.also .ar{grid-area:ar} .also .al{grid-area:al} .also .anum{grid-area:anum;font-size:12.5px} .also .ad{grid-area:ad}
.av{font-weight:600}
.also li:first-child{border-top:0}
.also .ar{align-self:center}
.ap{color:var(--muted);font-size:12px}
.also .ad{justify-content:flex-end;font-size:12.5px}

/* measures: C3 vitals layout, C4 bars */
.vitals{padding:4px 0}
.vlist{display:block}
.vital{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"top chg" "sub sub" "cmp cmp" "read read";column-gap:12px;
  padding:14px 16px;border-top:1px solid var(--line-2);color:inherit;text-decoration:none}
.vital:first-child{border-top:0}
.v-top{grid-area:top;display:flex;align-items:center;gap:8px;min-width:0}
.v-name{font-weight:600;font-size:15px;line-height:1.25}
.v-top .tag{display:none}
.v-chg{grid-area:chg;align-self:center}
.v-sub{grid-area:sub;font-size:12.5px;color:var(--muted);margin-top:2px}
.vital .cmp{grid-area:cmp;margin-top:10px}
.v-read{grid-area:read;margin:8px 0 0;font-size:13px;line-height:1.4;color:var(--ink-2)}

/* map panel (C4 map in a C3 card) */
.mapgrid{display:grid;gap:14px;margin-top:14px;grid-template-areas:"meas" "map" "proj"}
.mapgrid>#vitals{grid-area:meas}
.mapcol{grid-area:map;min-width:0}
.projcol{grid-area:proj;display:grid;gap:14px;min-width:0}
.mappanel{display:flex;flex-direction:column}
.mbar{display:flex;align-items:baseline;justify-content:space-between;gap:8px;font:500 11px/1.3 var(--mono);color:var(--muted);margin:-4px 0 10px;text-transform:uppercase;letter-spacing:.04em}
.mbar b{color:var(--ink);font-weight:600}
.stage{position:relative;background:var(--map-bg);border:1px solid var(--line-2);border-radius:12px;overflow:hidden;cursor:crosshair}
.map{position:absolute;inset:8px;width:calc(100% - 16px);height:calc(100% - 16px);overflow:visible;display:block;--k:1;--ms:.85}
.s{transform:scale(calc(var(--k) * var(--ms)))}
.map text{font-family:var(--mono)}
.g-fine{stroke:var(--grid-f);stroke-width:.6;fill:none;vector-effect:non-scaling-stroke}
.g-major{stroke:var(--grid-m);stroke-width:1;fill:none;vector-effect:non-scaling-stroke}
.frame{fill:none;stroke:var(--line);stroke-width:1;vector-effect:non-scaling-stroke}
.bnd-halo{fill:var(--accent-soft);opacity:.55;stroke:none}
.bnd{fill:none;stroke:var(--accent);stroke-width:1.6;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.gt{font-size:9px;fill:var(--muted);letter-spacing:.02em}
.sb{stroke:var(--ink-2);stroke-width:1.2;fill:none;vector-effect:non-scaling-stroke}
.na{fill:var(--ink-2)}
.pt circle,.pt rect{fill:var(--ink-2);opacity:.7}
.pt.c-mep circle{fill:var(--surface);stroke:var(--ink-2);stroke-width:1.2;opacity:1}
.pt.c-minor circle{fill:var(--muted);opacity:.6}
.mk{cursor:pointer;outline:none}
.mk-b{fill:var(--c-add);stroke:var(--surface);stroke-width:1.6}
.mk.c-demo .mk-b{fill:var(--c-demo)}
.mk.c-newc .mk-b{fill:var(--c-newc)}
.mk-t{font:600 10.5px var(--mono);fill:var(--on-mk);pointer-events:none}
.mk-halo{fill:var(--accent);opacity:0;transition:opacity .15s}
.mk.c-demo .mk-halo{fill:var(--c-demo)}
.mk.hot .mk-halo,.mk:focus-visible .mk-halo{opacity:.28}
.ms{transition:transform .15s}
.mk.hot .ms{transform:scale(calc(var(--k) * var(--ms) * 1.3))}
.mks.dim .mk:not(.hot){opacity:.4}
.mk:focus-visible .mk-b{stroke:var(--ink);stroke-width:2.4}
body.hide-add .pt.c-add, body.hide-add .mk.c-add,
body.hide-demo .pt.c-demo, body.hide-demo .mk.c-demo,
body.hide-newc .pt.c-newc, body.hide-newc .mk.c-newc,
body.hide-ren .pt.c-ren, body.hide-mep .pt.c-mep, body.hide-home .pt.c-home, body.hide-minor .pt.c-minor{display:none}
body.hide-add .prow.c-add, body.hide-demo .prow.c-demo, body.hide-newc .prow.c-newc{opacity:.4}
.readout{position:absolute;left:8px;bottom:8px;z-index:2;font:500 10.5px/1.3 var(--mono);background:color-mix(in srgb,var(--surface) 90%,transparent);border:1px solid var(--line);border-radius:6px;padding:4px 7px;color:var(--ink-2);max-width:calc(100% - 16px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:none}
.readout b{color:var(--accent);font-weight:600}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin-top:10px}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:4px 9px 4px 7px;font-size:12px;cursor:pointer;white-space:nowrap;color:var(--ink-2)}
.chip b{font:600 11px var(--mono);color:var(--muted)}
.chip[aria-pressed="false"]{background:transparent;color:var(--muted);border-style:dashed}
.chip[aria-pressed="false"] .gl{opacity:.35}
.chip.all{padding-left:10px}
.chip.all[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.chip.all[aria-pressed="true"] b{color:var(--bg);opacity:.7}
.gl{flex:none;display:block}
.gl-add{fill:var(--c-add)} .gl-demo{fill:var(--c-demo)} .gl-newc{fill:var(--c-newc)} .gl-ink{fill:var(--ink-2)} .gl-ink2{fill:var(--ink-2)}
.gl-ring{fill:none;stroke:var(--ink-2);stroke-width:1.3} .gl-mut{fill:var(--muted)}
.mkey{display:flex;gap:4px 14px;flex-wrap:wrap;margin-top:9px;font-size:12px;color:var(--muted)}
.mkey span{display:inline-flex;align-items:center;gap:5px}

/* projects (C4 rows) */
.plist{list-style:none;margin:0 -16px;padding:0}
.prow{display:grid;grid-template-columns:26px minmax(0,1fr);gap:10px;padding:11px 16px;border-top:1px solid var(--line-2);outline:none;transition:background .12s;position:relative}
.prow:first-child{border-top:0;padding-top:4px}
.prow::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:transparent}
.prow.hot{background:var(--accent-soft)}
.prow.hot::before{background:var(--accent)}
.prow.c-demo.hot{background:var(--rising-soft)} .prow.c-demo.hot::before{background:var(--c-demo)}
.prow:focus-visible{box-shadow:inset 0 0 0 2px var(--accent)}
.pn{width:24px;height:24px;border-radius:50%;background:var(--c-add);color:var(--on-mk);display:grid;place-items:center;font:600 11.5px/1 var(--mono);margin-top:1px}
.pn.sq{border-radius:4px;background:var(--c-demo)}
.prow.c-newc .pn{background:var(--c-newc)}
.pt1{display:flex;gap:8px;align-items:baseline}
.paddr{font-weight:600;font-size:15px;min-width:0}
.pdate{margin-left:auto;font-size:12px;color:var(--muted);white-space:nowrap}
.pt2{display:flex;gap:4px 10px;flex-wrap:wrap;align-items:center;margin-top:2px;font-size:12.5px;color:var(--ink-2)}
.new{font:600 10px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--accent);background:var(--accent-soft);border-radius:999px;padding:4px 7px}
.coord{font-size:11px;color:var(--muted)}
.pwork{font-size:13px;color:var(--muted);margin-top:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
.pfoot{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line-2);padding-top:10px;margin-top:2px}
.mix ul{list-style:none;margin:0 -8px;padding:0}
.mixrow{width:100%;display:grid;grid-template-columns:14px minmax(0,1.25fr) minmax(0,1fr) 30px;gap:10px;align-items:center;border:0;background:none;padding:6px 8px;border-radius:8px;cursor:pointer;text-align:left;font-size:13.5px}
.mixrow:hover{background:var(--surface-2)}
.mixrow b{text-align:right;font-size:13px;font-weight:600}
.mixrow .ml{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mixrow[aria-pressed="false"]{color:var(--muted)}
.mixrow[aria-pressed="false"] svg{opacity:.3}
.mixrow[aria-pressed="false"] .ml{text-decoration:line-through}

/* stat readings (C3) */
.stats{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line-2);border:1px solid var(--line-2);border-radius:12px;overflow:hidden}
.stats>div{background:var(--surface);padding:12px 12px 11px}
.stats .v{font:600 20px/1.15 var(--mono)}
.stats .k{font-size:12.5px;color:var(--muted);margin-top:3px;line-height:1.35}
.stats.s3>div:last-child{grid-column:1/-1}
.hero{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.hero b{font:600 34px/1 var(--mono);letter-spacing:-.02em}
.hero span{font-size:13px;color:var(--muted)}
.cta{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:12px;padding:12px 14px;border-radius:12px;background:var(--accent-soft);color:var(--ink);text-decoration:none;font-size:14px}
.cta span{color:var(--accent);font-weight:600;white-space:nowrap}

/* homes table */
.htbl{width:100%;border-collapse:collapse}
.htbl th,.htbl td{padding:8px 0;border-top:1px solid var(--line-2);vertical-align:baseline}
.htbl tr:first-child th,.htbl tr:first-child td{border-top:0}
.htbl th{text-align:left;font-weight:500;font-size:14px}
.htbl th span{display:block;font-size:11.5px;color:var(--muted);font-weight:400}
.hv{text-align:right;font-size:16px;font-weight:600;white-space:nowrap}
.hv small{font-size:12px;color:var(--muted);font-weight:500}
.hn{text-align:right;font-size:12px;color:var(--muted);width:72px;white-space:nowrap}

/* 311 ranked table (C4) */
.tbl-wrap{overflow-x:auto;margin:0 -16px}
table.t311{border-collapse:collapse;width:100%}
.t311 th{font:500 10.5px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.05em;text-align:right;padding:0 6px 6px;border-bottom:1px solid var(--line)}
.t311 th:nth-child(2){text-align:left}
.t311 td{padding:8px 6px;border-bottom:1px solid var(--line-2);font-size:13.5px;vertical-align:middle}
.t311 tr:last-child td{border-bottom:0}
.ri{font-size:11px;color:var(--muted);width:28px;padding-left:16px!important}
.rn span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:170px}
.rb{display:block;width:100%;height:6px;margin-top:5px;overflow:visible}
.rc,.rp,.rd{text-align:right;font-size:13px;white-space:nowrap}
.rc{font-weight:600}.rp{color:var(--muted)}
.rd{padding-right:16px!important}
.rd .chg{font-size:12.5px}
.legend{display:flex;gap:6px 14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px;padding-top:10px;border-top:1px solid var(--line-2)}
.legend span{display:inline-flex;align-items:center;gap:5px}
.legend i{display:inline-block}

/* then (C3) */
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

/* reps (C3) */
.anc+.anc{margin-top:12px}
.anc-h{display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;color:var(--muted);margin-bottom:4px}
.anc-h a{text-decoration:none}
.anc ul{list-style:none;margin:0;padding:0}
.anc li{display:flex;gap:12px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line-2);font-size:14.5px}
.smd{font-size:12.5px;color:var(--muted);min-width:42px}
.repnote{font-size:12px;color:var(--muted);margin:10px 0 0}

/* subscribe + sponsor (C3) */
.subrow{display:flex;gap:8px;margin-top:10px;min-width:0}
.subrow input{flex:1;min-width:0;border:1px solid var(--line);background:var(--surface-2);border-radius:999px;padding:11px 16px;font:inherit;color:var(--ink)}
.subrow button{border:0;background:var(--ink);color:var(--bg);font:600 14px var(--sans);border-radius:999px;padding:0 18px}
.subnote{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin-top:9px}
.sponsor{display:flex;flex-direction:column;justify-content:center;gap:6px;border:1px dashed var(--muted);background:transparent}
.sponsor small{font:600 10.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.sponsor div{font-size:16px}
.stack{display:flex;flex-direction:column;gap:14px;min-width:0}

footer{border-top:1px solid var(--line);padding:20px 0 32px;font-size:12.5px;color:var(--muted)}
footer p{margin:0 0 8px;max-width:820px}
footer strong{color:var(--ink-2)}

@media (max-width:380px){
  .cr-r{grid-template-columns:86px minmax(0,1fr) 52px;gap:8px}
}

/* ---------- tablet & desktop ---------- */
@media (min-width:720px){
  .wrap{padding:0 28px}
  .brand h1{font-size:38px}
  .cond{grid-template-columns:1.25fr 1fr;align-items:center;padding:28px}
  .c-head{font-size:30px}
  .stats{grid-template-columns:repeat(3,1fr)}
  .stats.s3>div:last-child{grid-column:auto}
  .stats.s2{grid-template-columns:1fr 1fr}
  .then{grid-template-columns:1fr 1fr}
  .rn span{max-width:none}
  .also li{grid-template-columns:12px minmax(0,1fr) auto 92px;grid-template-areas:"ar al anum ad"}
  .also .anum{font-size:13.5px}
}
@media (min-width:1024px){
  header{padding-top:26px}
  .hd{align-items:center}
  .topbar{display:grid;grid-template-columns:1fr 460px;gap:28px;align-items:end}
  .search{margin-top:0}
  .row{grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:18px;margin-top:18px;align-items:stretch}
  .row.even{grid-template-columns:1fr 1fr}
  .row.one{grid-template-columns:1fr}
  .stack{gap:18px}
  .stack>:last-child{flex:1}
  .subband{display:grid;grid-template-columns:1fr 1.2fr;column-gap:28px;align-items:center}
  .subband .ph{grid-column:1/-1}
  .subband .subrow{margin:0}
  .subband .subnote{grid-column:2}
  .sponsor{flex:0 0 auto !important;padding:18px 16px}
  .c-head{font-size:34px}
  /* measures + projects on the left, the map sticky on the right */
  .mapgrid{grid-template-columns:minmax(0,7fr) minmax(0,5fr);grid-template-areas:"meas map" "proj map";gap:18px;margin-top:18px;align-items:start}
  .mapcol{align-self:stretch}
  .mappanel{position:sticky;top:16px;height:calc(100vh - 32px);height:calc(100svh - 32px);max-height:860px;min-height:560px}
  .stage{flex:1;min-height:0;aspect-ratio:auto !important}
  .map{inset:12px;width:calc(100% - 24px);height:calc(100% - 24px);--ms:1}
  .vitals{background:transparent;border:0;padding:0}
  .vitals>.ph{padding:0 2px !important}
  .vlist{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .vital{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px;transition:border-color .15s;
    grid-template-rows:auto auto auto 1fr}
  .vital:first-child{border-top:1px solid var(--line)}
  .vital:hover{border-color:var(--muted)}
  .v-top{justify-content:space-between}
  .v-top .tag{display:inline-flex}
  .vital{grid-template-areas:"top top" "chg sub" "cmp cmp" "read read"}
  .v-chg{justify-self:start;margin-top:8px}
  .v-chg .chg{font-size:18px;gap:6px}
  .v-chg .ic{width:12px;height:12px}
  .v-sub{justify-self:end;align-self:end;text-align:right;margin:0}
  .v-read{border-top:1px solid var(--line-2);padding-top:10px;margin-top:12px}
}
"""

JS = r"""
(function(){
  var map=document.getElementById('map'), stage=map.parentNode;
  var ro=document.getElementById('readout'), def=ro.innerHTML;
  var vb=map.viewBox.baseVal, W=+map.dataset.w, N=+map.dataset.n, K=+map.dataset.k, SC=+map.dataset.sc;
  function fit(){var r=map.getBoundingClientRect(); if(!r.width) return;
    var s=Math.min(r.width/vb.width,r.height/vb.height); map.style.setProperty('--k',(1/s).toFixed(4));}
  fit(); if(window.ResizeObserver){new ResizeObserver(fit).observe(map);} else {window.addEventListener('resize',fit);}
  function ll(lat,lon){return Math.abs(lat).toFixed(5)+'°N  '+Math.abs(lon).toFixed(5)+'°W';}
  map.addEventListener('mousemove',function(ev){ if(document.querySelector('.mk.hot')) return;
    var m=map.getScreenCTM(); if(!m) return; var p=new DOMPoint(ev.clientX,ev.clientY).matrixTransform(m.inverse());
    ro.innerHTML='Cursor  '+ll(N-p.y/SC, W+p.x/(K*SC));});
  map.addEventListener('mouseleave',function(){ if(!document.querySelector('.mk.hot')) ro.innerHTML=def;});
  // linked highlight: project row <-> numbered marker
  var mks=document.querySelector('.mks');
  function hot(id,on){
    document.querySelectorAll('[data-id="'+id+'"]').forEach(function(el){el.classList.toggle('hot',on);});
    mks.classList.toggle('dim',on);
    var mk=document.querySelector('.mk[data-id="'+id+'"]');
    if(on&&mk){ro.innerHTML='<b>'+id.slice(1)+'</b>  '+mk.dataset.addr+'  ·  '+ll(+mk.dataset.lat,+mk.dataset.lon);
      mk.parentNode.appendChild(mk);} else ro.innerHTML=def;
  }
  document.querySelectorAll('[data-id]').forEach(function(el){
    var id=el.dataset.id;
    el.addEventListener('mouseenter',function(){hot(id,true);});
    el.addEventListener('mouseleave',function(){hot(id,false);});
    el.addEventListener('focus',function(){hot(id,true);});
    el.addEventListener('blur',function(){hot(id,false);});
  });
  // marker -> its row
  document.querySelectorAll('.mk').forEach(function(mk){
    function go(ev){ev.stopPropagation();
      var row=document.querySelector('.prow[data-id="'+mk.dataset.id+'"]');
      row.scrollIntoView({behavior:'smooth',block:'center'}); row.focus({preventScroll:true});}
    mk.addEventListener('click',go);
    mk.addEventListener('keydown',function(ev){if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();go(ev);}});
  });
  // type filters: map chips and the permits-by-type rows stay in sync
  var keys=[].slice.call(document.querySelectorAll('.chips [data-g]')).map(function(b){return b.dataset.g;});
  var off={};
  function sync(){ keys.forEach(function(k){document.body.classList.toggle('hide-'+k,!!off[k]);
      document.querySelectorAll('[data-g="'+k+'"]').forEach(function(b){b.setAttribute('aria-pressed',!off[k]);});});
    document.querySelector('[data-all]').setAttribute('aria-pressed',!keys.some(function(k){return off[k];}));
    document.getElementById('shown').textContent=keys.reduce(function(s,k){
      return s+(off[k]?0:+document.querySelector('.chips [data-g="'+k+'"] b').textContent);},0);}
  document.querySelectorAll('[data-g]').forEach(function(b){b.addEventListener('click',function(){
    var k=b.dataset.g, all=keys.every(function(x){return !off[x];});
    if(all){keys.forEach(function(x){off[x]=x!==k;});} else {off[k]=!off[k]; if(keys.every(function(x){return off[x];})) off={};}
    sync();});});
  document.querySelector('[data-all]').addEventListener('click',function(){off={};sync();});
})();
"""

cx_lat, cx_lon = CENTER
default_readout = f"Center  {cx_lat:.5f}°N  {abs(cx_lon):.5f}°W"
lead_name = LEAD_NAME.get(lead["type"], short_type(lead["type"]))

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Petworth: what's changing, from DC's own data</title>
<meta name="description" content="What's changing in Petworth, Washington DC, from DC's own open data. Independent; updated nightly.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="Petworth permits" href="/petworth/permits.xml">
<style>{CSS}</style>
</head>
<body>
<div class="layout-tag">LAYOUT C5: C3 layout + C4 data</div>

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
    <li><a href="#condition">Condition</a></li><li><a href="#vitals">Measures</a></li><li><a href="#permit-map">Map</a></li><li><a href="#projects">Projects</a></li>
    <li><a href="#homes">Homes</a></li><li><a href="#streets">Streets</a></li><li><a href="#then">Then</a></li><li><a href="#reps">Representatives</a></li><li><a href="#subscribe">Weekly email</a></li>
  </ul></nav>
</div></header>

<main class="wrap">

<section id="condition" class="cond" aria-labelledby="c-h">
  <div>
    <div class="c-kick">Today's condition · {asof_day} {state_tag(lr['state'])}</div>
    <h2 class="c-head" id="c-h">{e(FACTS['lead_sentence'])}</h2>
    <p class="c-word">{e(cond_word)}. Each reading compares the last 30 days with the 30 days before; crime is shown as counts, not graded.</p>
    <ul class="c-strip" aria-label="Readings by state">{cond_strip}</ul>
  </div>
  <div class="c-box">
    <a class="c-lead" href="{link('311 report card')}">
      <div class="ph"><h2>Biggest change in 311</h2><span class="sub" style="color:var(--accent);font-weight:600">311 report card →</span></div>
      <div class="lh"><b>{e(lead_name)}</b><span class="chg s-{lr['state']}">{icon(lr['state'])}{lr['txt']}</span></div>
      <div class="cmp">{pair('Last 30 days', lead['count'], fmt(lead['count']), '30 days before', lead['previous'], fmt(lead['previous']), 'fill s-' + lr['state'])}</div>
    </a>
    <div class="also-h">Also in 311</div>
    <ul class="also">{also}</ul>
  </div>
</section>

<div class="mapgrid">
  <section id="vitals" class="panel vitals" aria-labelledby="v-h">
    <div class="ph" style="padding:12px 16px 0"><h2 id="v-h">Measures</h2><span class="sub">Latest period vs the one before</span></div>
    <div class="vlist">{measures_html}</div>
  </section>

  <div class="mapcol">
    <section id="permit-map" class="panel mappanel" aria-labelledby="m-h">
      <div class="ph"><h2 id="m-h">Permit map</h2><a href="{link('Block Watch')}">Block Watch →</a></div>
      <div class="mbar"><span><b id="shown">{permits_total}</b> permits shown · last 30 days</span><span>{len([p for p in projects if p['pt']])} numbered</span></div>
      <div class="stage" style="aspect-ratio:{VBW:.0f}/{VBH:.0f}">
        {map_svg()}
        <div class="readout" id="readout" aria-live="polite">{default_readout}</div>
      </div>
      <div class="chips" role="group" aria-label="Filter permits by type">{chips}</div>
      <div class="mkey"><span>{glyph('num')}Numbered: bigger project, matches the list</span><span>Grid 0.001°</span></div>
    </section>
  </div>

  <div class="projcol">
    <section id="projects" class="panel" aria-labelledby="p-h">
      <div class="ph"><h2 id="p-h">Bigger projects</h2><a href="{link('Block Watch')}">Block Watch →</a></div>
      <ol class="plist">{proj_rows}</ol>
      <div class="pfoot"><span><b class="num" style="color:var(--ink)">{len(projects)}</b> of {permits_total} permits · {new_count} new this week{'' if groups.get('New construction') else ' · no new construction'}</span><a href="/petworth/permits.xml">Permits RSS</a></div>
    </section>
    <section class="panel mix" aria-labelledby="mix-h">
      <div class="ph"><h2 id="mix-h">All {permits_total} permits by type</h2><span class="sub">Tap to filter the map</span></div>
      <ul>{mix_rows}</ul>
    </section>
  </div>
</div>

<div class="row">
  <section id="homes" class="panel" aria-labelledby="h-h">
    <div class="ph"><h2 id="h-h">Homes</h2><a href="{link('Housing pulse')}">Housing pulse →</a></div>
    <div class="hero"><b class="num">{homes['median_house_price_12mo']}</b><span>median house price, last 12 months, from {homes['house_sales_12mo']} house sales</span></div>
    <table class="htbl"><tbody>{homes_tbl}</tbody></table>
    <a class="cta" href="{link('Assessment check')}">Is your assessment in line with sales? <span>Assessment check →</span></a>
  </section>
  <section class="panel" aria-labelledby="tr-h">
    <div class="ph"><h2 id="tr-h">Street trees</h2><a href="{link('Street trees')}">Tree atlas →</a></div>
    <div class="hero"><b class="num">{fmt(trees['street_trees'])}</b><span>street trees, {trees['species']} species</span></div>
    <div class="stats s2">
      <div><div class="v">{trees['planted_last_5y']}</div><div class="k">planted in the last 5 years</div></div>
      <div><div class="v" style="color:var(--accent)">{trees['empty_boxes_open']}</div><div class="k">empty tree boxes open for planting</div></div>
    </div>
    <a class="cta" href="{link('Street trees')}">Find an empty tree box near you <span>Street trees →</span></a>
  </section>
</div>

<div class="row even" id="streets">
  <section class="panel" aria-labelledby="t-h">
    <div class="ph"><h2 id="t-h">Top 311 requests</h2><a href="{link('311 report card')}">All types →</a></div>
    <div class="tbl-wrap"><table class="t311">
      <thead><tr><th></th><th>Type · last 30 days</th><th>Now</th><th>Prior</th><th>Change</th></tr></thead>
      <tbody>{rank_rows}</tbody>
    </table></div>
    <div class="legend"><span><i style="width:12px;height:6px;background:var(--ink-2)"></i>Last 30 days</span><span><i style="width:1.5px;height:10px;background:var(--ink)"></i>30 days before</span><span>{icon('rising')}rising {icon('easing')}easing {icon('steady')}within 5%</span></div>
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
  <p>petworth.org · map: equirectangular, cos(lat) corrected · numbered markers matched to permits by type and address order</p>
</div></footer>
<script>{JS}</script>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
for line in match_report:
    print("  " + line)
