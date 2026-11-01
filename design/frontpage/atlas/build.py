"""Build atlas/index.html from site/src/data/petworth.json.

Usage: python build.py   (writes index.html next to this file)

Everything on the page comes from the JSON. The street grid on the map is reconstructed from
geocoded addresses that appear in the data (permits and 311 blocks); a street the data never
touches is placed by DC's alphabetical street order between its neighbours.
"""
import datetime as dt
import html
import json
import math
import re
import statistics
from collections import defaultdict, OrderedDict
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
D = json.loads((REPO / "site/src/data/petworth.json").read_text(encoding="utf-8"))
ET = ZoneInfo("America/New_York")
esc = html.escape


# ----------------------------------------------------------------------------- helpers
def to_et(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ET)


def n(v):
    return f"{v:,}"


def money(v):
    if v is None:
        return "n/a"
    if v >= 1_000_000:
        return f"${v / 1e6:.2f}M".replace(".00M", "M")
    return f"${round(v / 1000):,}K"


def pct_ok(a, b):
    return a >= 100 and b >= 100


def pct(a, b):
    return f"{(a - b) / b * 100:+.0f}%".replace("-", "−")


def signed(v):
    return ("+" if v > 0 else "−" if v < 0 else "±") + f"{abs(v):,}"


def fmt_addr(a):
    a = re.sub(r"\s+\d{5}$", "", a.strip())
    t = a.title()
    t = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), t)
    t = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), t)
    return t


def clean_text(s, limit=150):
    s = re.sub(r"\s+", " ", (s or "").replace("\r", " ")).strip()
    if not s:
        return ""
    letters = [c for c in s if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:
        s = s.lower()
    s = s[0].upper() + s[1:]
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0].rstrip(",.;:-") + "…"
    return s


def day_label(date, today):
    delta = (date - today).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    if delta == -1:
        return "Yesterday"
    return date.strftime("%b %-d") if False else date.strftime("%b ") + str(date.day)


def short_date(date):
    return date.strftime("%b ") + str(date.day)


def range_label(a, b):
    if a == b:
        return short_date(a)
    if a.month == b.month and a.year == b.year:
        return f"{short_date(a)}–{b.day}"
    return f"{short_date(a)} – {short_date(b)}"


GEN = to_et(D["generated_at"])
TODAY = dt.date.fromisoformat(D["events"]["today"])
NAME = D["name"]

# ----------------------------------------------------------------------------- projection
RING = D["boundary"]["rings"][0]
LONS = [p[0] for p in RING]
LATS = [p[1] for p in RING]
PAD = 0.0007
LON0, LON1 = min(LONS) - PAD, max(LONS) + PAD
LAT0, LAT1 = min(LATS) - PAD, max(LATS) + PAD
COS = math.cos(math.radians((LAT0 + LAT1) / 2))
MW = 600.0
K = MW / ((LON1 - LON0) * COS)
MH = (LAT1 - LAT0) * K


def P(lat, lon):
    return ((lon - LON0) * COS * K, (LAT1 - lat) * K)


def inside(x, y, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


POLY = [P(lat, lon) for lon, lat in RING]
BOUNDARY_D = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in POLY) + " Z"
COLS, ROWS = 6, 6


def grid_ref(x, y):
    c = min(COLS - 1, max(0, int(x / (MW / COLS))))
    r = min(ROWS - 1, max(0, int(y / (MH / ROWS))))
    return "ABCDEF"[c] + str(r + 1)


# ----------------------------------------------------------------------------- street grid from data
def norm_street(s):
    s = s.upper()
    s = re.sub(r"\s+\d{5}$", "", s.strip())
    for a, b in (("STREET", "ST"), ("AVENUE", "AVE"), ("PLACE", "PL"), ("ROAD", "RD")):
        s = re.sub(rf"\b{a}\b", b, s)
    s = re.sub(r"\s+(NW|NE|SW|SE)$", "", s)
    return re.sub(r"\s+", " ", s).strip()


PTS = defaultdict(list)  # street -> [(num, lat, lon, precise)]
for p in D["permits"]:
    m = re.match(r"(\d+)\s+(.*)", norm_street(p["address"]))
    if m and p.get("lat"):
        PTS[m.group(2)].append((int(m.group(1)), p["lat"], p["lon"], True))
for r in D["requests"]["recent"]:
    b = r.get("block") or ""
    if not r.get("lat"):
        continue
    nb = norm_street(b)
    m = re.match(r"(\d+|UNIT) BLOCK OF (.*)", nb)
    if m:
        num = 0 if m.group(1) == "UNIT" else int(m.group(1))
        PTS[m.group(2)].append((num, r["lat"], r["lon"], False))
        continue
    m = re.match(r"(.*) AND (.*)", nb)
    if m:
        for s in (m.group(1), m.group(2)):
            PTS[norm_street(s)].append((None, r["lat"], r["lon"], False))


def linfit(xs, ys):
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return lambda x: my + b * (x - mx)


def kind_of(name):
    if re.match(r"^\d+(ST|ND|RD|TH) (ST|PL)$", name):
        return "ns"
    if re.search(r"\b(AVE|RD)$", name):
        return "ave"
    nums = [p[0] for p in PTS.get(name, []) if p[0] is not None]
    if nums and statistics.median(nums) >= 1500:
        return "ns"
    return "ew"


ns_pts = [(num, lat) for s, v in PTS.items() if kind_of(s) == "ns" for num, lat, lon, pr in v if num and pr]
ew_pts = [(num, lon) for s, v in PTS.items() if kind_of(s) == "ew" for num, lat, lon, pr in v if num is not None and pr]
LAT_OF = linfit([a for a, _ in ns_pts], [b for _, b in ns_pts])  # house number on a N-S street -> latitude
LON_OF = linfit([a for a, _ in ew_pts], [b for _, b in ew_pts])  # house number on an E-W street -> longitude


def med(vals):
    return statistics.median(vals) if vals else None


def street_coord(name, idx):
    v = PTS.get(name, [])
    pre = [p[idx] for p in v if p[3]]
    return med(pre) or med([p[idx] for p in v])


ORDER = ["QUINCY ST", "RANDOLPH ST", "SHEPHERD ST", "TAYLOR ST", "UPSHUR ST", "VARNUM ST", "WEBSTER ST",
         "ALLISON ST", "BUCHANAN ST", "CRITTENDEN ST", "DECATUR ST", "DELAFIELD PL", "EMERSON ST",
         "FARRAGUT ST", "GALLATIN ST"]
EW_LAT = {s: street_coord(s, 1) for s in PTS if kind_of(s) == "ew"}
for i, s in enumerate(ORDER):  # fill gaps by DC's alphabetical order
    if EW_LAT.get(s) is None:
        lo = next((EW_LAT[ORDER[j]] for j in range(i - 1, -1, -1) if EW_LAT.get(ORDER[j])), None)
        hi = next((EW_LAT[ORDER[j]] for j in range(i + 1, len(ORDER)) if EW_LAT.get(ORDER[j])), None)
        if lo and hi:
            EW_LAT[s] = (lo + hi) / 2
NS_LON = {s: street_coord(s, 2) for s in PTS if kind_of(s) == "ns"}


def fit_ave(name):
    seen = {(round(lat, 4), round(lon, 4)) for _, lat, lon, _ in PTS.get(name, [])}
    xy = [P(lat, lon) for lat, lon in seen]
    if len(xy) < 2:
        return None
    mx, my = statistics.fmean(x for x, _ in xy), statistics.fmean(y for _, y in xy)
    sxx = sum((x - mx) ** 2 for x, _ in xy)
    syy = sum((y - my) ** 2 for _, y in xy)
    sxy = sum((x - mx) * (y - my) for x, y in xy)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(ang), math.sin(ang)
    proj = [(x - mx) * ux + (y - my) * uy for x, y in xy]
    if max(proj) - min(proj) < 70:
        return None
    return (mx, my, ux, uy)


AVES = {s: fit_ave(s) for s in PTS if kind_of(s) == "ave"}
AVES = {s: v for s, v in AVES.items() if v}


def intersect(a, b):
    (x1, y1, u1, v1), (x2, y2, u2, v2) = a, b
    det = u1 * (-v2) - v1 * (-u2)
    if abs(det) < 1e-6:
        return None
    t = ((x2 - x1) * (-v2) - (y2 - y1) * (-u2)) / det
    return (x1 + t * u1, y1 + t * v1)


def label_name(s):
    t = s.title().replace(" St", " St").replace(" Ave", " Ave")
    t = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), t)
    return t


# Landmarks: circles where the fitted avenues cross (only if the fit is plausible).
LANDMARKS = []
for nm, a, b, near in (("Grant Circle", "NEW HAMPSHIRE AVE", "ILLINOIS AVE", ("VARNUM ST", "WEBSTER ST")),
                       ("Sherman Circle", "KANSAS AVE", "ILLINOIS AVE", ("CRITTENDEN ST", "DECATUR ST"))):
    if a in AVES and b in AVES:
        pt = intersect(AVES[a], AVES[b])
        if pt and all(EW_LAT.get(s) for s in near):
            ylo = P(max(EW_LAT[s] for s in near), LON0)[1] - 40
            yhi = P(min(EW_LAT[s] for s in near), LON0)[1] + 40
            if ylo <= pt[1] <= yhi and inside(pt[0], pt[1], POLY):
                LANDMARKS.append((nm, pt))


def in_plate(x, y, m=12):
    return m < x < MW - m and m < y < MH - m


def geo_block(num, street):
    """Centre and segment (projected) of a hundred-block, or None."""
    s = norm_street(street)
    k = kind_of(s)
    if k == "ns" and NS_LON.get(s):
        lon = NS_LON[s]
        a, b = P(LAT_OF(num + 5), lon), P(LAT_OF(num + 95), lon)
    elif k == "ew" and EW_LAT.get(s):
        lat = EW_LAT[s]
        a, b = P(lat, LON_OF(num + 5)), P(lat, LON_OF(num + 95))
    else:
        cands = [p for p in PTS.get(s, []) if p[0] is not None and abs(p[0] - num) < 150]
        if not cands:
            return None
        p = min(cands, key=lambda p: abs(p[0] - num))
        c = P(p[1], p[2])
        return {"c": c, "seg": None}
    c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if not in_plate(*c):
        return None
    return {"c": c, "seg": (a, b)}


def geo_place(place):
    m = re.match(r"(\d+)\s*-\s*(\d+)\s+Block\s+(?:of\s+)?(.+)", place, re.I)
    if m:
        return geo_block(min(int(m.group(1)), int(m.group(2))) // 100 * 100, m.group(3))
    m = re.match(r"(\d+)\s+block\s+of\s+(.+)", place, re.I)
    if m:
        return geo_block(int(m.group(1)), m.group(2))
    m = re.match(r"(.+?)\s*&\s*(.+)", place)
    if m:
        s1, s2 = norm_street(m.group(1)), norm_street(m.group(2))
        if kind_of(s1) == "ew":
            s1, s2 = s2, s1
        if NS_LON.get(s1) and EW_LAT.get(s2):
            c = P(EW_LAT[s2], NS_LON[s1])
            return {"c": c, "seg": None} if in_plate(*c) else None
    return None


# ----------------------------------------------------------------------------- content: events
events = sorted(D["events"]["events"], key=lambda e: (e["date"], e.get("time") or ""))
horizon = TODAY + dt.timedelta(days=14)
ev_soon = [e for e in events if TODAY <= dt.date.fromisoformat(e["date"]) <= horizon]
ev_later = [e for e in events if dt.date.fromisoformat(e["date"]) > horizon]
EV_PLACES = OrderedDict()
for e in ev_soon:
    if e["place"] not in EV_PLACES:
        g = geo_place(e["place"])
        EV_PLACES[e["place"]] = {"geo": g, "id": f"e{len(EV_PLACES) + 1}", "letter": "ABCDEFGH"[len(EV_PLACES)],
                                 "title": e["title"]}

# ----------------------------------------------------------------------------- content: curb
curb_groups = OrderedDict()
for c in D["streets"]["curb"]["upcoming"]:
    m = re.match(r"(\d+) block of (.+)", c["block"], re.I)
    street = m.group(2) if m else c["block"]
    key = (c["type"], street, c["start"], c["end"], c.get("hours") or "")
    g = curb_groups.setdefault(key, {"blocks": set(), "ft": 0})
    if m:
        g["blocks"].add(int(m.group(1)))
    g["ft"] += c.get("ft") or 0
CURB = []
for i, ((typ, street, s, e, hrs), g) in enumerate(curb_groups.items(), 1):
    blocks = sorted(g["blocks"])
    geos = [x for x in (geo_block(b, street) for b in blocks) if x]
    if blocks:
        bl = f"{blocks[0]}–{blocks[-1]} blocks" if len(blocks) > 1 else f"{blocks[0]} block"
        where = f"{bl} of {street.replace(' NW', '')}"
    else:
        where = street
    CURB.append({"id": f"c{i}", "type": typ, "where": where, "start": dt.date.fromisoformat(s),
                 "end": dt.date.fromisoformat(e), "hours": hrs, "ft": g["ft"], "geos": geos})

# ----------------------------------------------------------------------------- content: permits
BIG_GROUPS = ("Additions", "Demolition", "New construction", "New buildings")
by_addr = defaultdict(list)
for p in D["permits"]:
    by_addr[p["address"]].append(p)
big = [p for p in D["permits"] if p["group"] in BIG_GROUPS]
BIG = OrderedDict()
for p in sorted(big, key=lambda p: p["issued"], reverse=True):
    if p["address"] in BIG:
        continue
    BIG[p["address"]] = p
PROJECTS = []
for i, (addr, p) in enumerate(BIG.items(), 1):
    x, y = P(p["lat"], p["lon"])
    others = len(by_addr[addr]) - 1
    PROJECTS.append({"id": f"p{i}", "num": i, "addr": fmt_addr(addr), "group": p["group"],
                     "issued": to_et(p["issued"]).date(), "work": clean_text(p["work"]), "xy": (x, y),
                     "ref": grid_ref(x, y), "others": others, "permit": p["id"]})
big_addrs = set(BIG)
minor_spots = defaultdict(int)
for p in D["permits"]:
    if p["address"] in big_addrs or not p.get("lat"):
        continue
    if inside(*P(p["lat"], p["lon"]), POLY):
        minor_spots[(p["lat"], p["lon"])] += 1
permits_in = sum(1 for p in D["permits"] if p.get("lat") and inside(*P(p["lat"], p["lon"]), POLY))
group_counts = defaultdict(int)
for p in D["permits"]:
    group_counts[p["group"]] += 1
p_dates = sorted(to_et(p["issued"]).date() for p in D["permits"])

# 311 blocks layer (hundred-block points, as published)
req_spots = defaultdict(int)
for r in D["requests"]["recent"]:
    if r.get("lat") and inside(*P(r["lat"], r["lon"]), POLY):
        req_spots[(r["lat"], r["lon"])] += 1

# 1926 featured block
FB = D["history"]["buildings"]["featured_block"]
FB_GEO = None
m = re.match(r"(\d+) block of (.+)", FB["block"], re.I)
if m:
    FB_GEO = geo_block(int(m.group(1)), m.group(2))

# ----------------------------------------------------------------------------- the map (SVG)
ML, MT, MR, MB = 26.0, 26.0, 128.0, 70.0
VW, VH = ML + MW + MR, MT + MH + MB


def line_through(x, y, ux, uy, L=2000):
    return (x - ux * L, y - uy * L, x + ux * L, y + uy * L)


def build_svg():
    o = []
    o.append(f'<svg viewBox="0 0 {VW:.0f} {VH:.0f}" role="img" aria-labelledby="plate-t plate-d" '
             f'xmlns="http://www.w3.org/2000/svg">')
    o.append(f'<title id="plate-t">Map of {NAME}</title>')
    o.append(f'<desc id="plate-d">The {NAME} boundary with its street grid, {permits_in} building permits issued in the '
             f'last 30 days ({len(PROJECTS)} bigger projects numbered), this fortnight’s markets, and curb space '
             f'reserved starting this week. Crime is not mapped.</desc>')
    o.append('<defs>'
             f'<clipPath id="clip-b"><path d="{BOUNDARY_D}"/></clipPath>'
             f'<clipPath id="clip-m"><rect x="0" y="0" width="{MW:.0f}" height="{MH:.0f}"/></clipPath>'
             '<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<line x1="0" y1="0" x2="0" y2="7" class="hatch"/></pattern>'
             '</defs>')
    o.append(f'<g transform="translate({ML},{MT})">')
    # ground
    o.append(f'<rect class="outside" x="0" y="0" width="{MW:.0f}" height="{MH:.0f}"/>')
    o.append(f'<rect x="0" y="0" width="{MW:.0f}" height="{MH:.0f}" fill="url(#hatch)"/>')
    o.append(f'<path class="land" d="{BOUNDARY_D}"/>')
    # streets, clipped to the boundary
    o.append('<g clip-path="url(#clip-b)">')
    labels_ew, labels_ns = [], []
    for s, lat in EW_LAT.items():
        if lat is None or not (LAT0 < lat < LAT1):
            continue
        y = P(lat, LON0)[1]
        if s.endswith(" PL"):
            lons = [p[2] for p in PTS.get(s, [])]
            if not lons:
                continue
            x1, x2 = P(lat, min(lons) - 0.0012)[0], P(lat, max(lons) + 0.0012)[0]
        else:
            x1, x2 = -10, MW + 10
        o.append(f'<line class="st" x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}"/>')
        if not s.endswith(" PL") or s == "DELAFIELD PL":
            labels_ew.append((y, s))
    for s, lon in NS_LON.items():
        if lon is None:
            continue
        x = P(LAT0, lon)[0]
        if s.endswith(" PL"):
            lats = [p[1] for p in PTS.get(s, [])]
            y1, y2 = P(max(lats) + 0.0012, lon)[1], P(min(lats) - 0.0012, lon)[1]
        else:
            y1, y2 = -10, MH + 10
        o.append(f'<line class="st" x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}"/>')
        if re.match(r"^\d", s) and s.endswith(" ST"):
            labels_ns.append((x, s))
    for s, (x, y, ux, uy) in AVES.items():
        x1, y1, x2, y2 = line_through(x, y, ux, uy)
        o.append(f'<line class="ave" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    for nm, (x, y) in LANDMARKS:
        o.append(f'<circle class="circ" cx="{x:.1f}" cy="{y:.1f}" r="13"/>')
    o.append('</g><g>')
    for nm, (x, y) in LANDMARKS:
        o.append(f'<circle class="circ-hit mk" data-mk="{nm.split()[0].lower()}" cx="{x:.1f}" cy="{y:.1f}" r="13"><title>{esc(nm)}</title></circle>')
    o.append('</g>')
    # boundary ribbon + line
    o.append(f'<path class="ribbon" clip-path="url(#clip-b)" d="{BOUNDARY_D}"/>')
    o.append(f'<path class="bline" d="{BOUNDARY_D}"/>')
    # grid
    o.append('<g class="grid">')
    for c in range(1, COLS):
        x = MW / COLS * c
        o.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{MH:.1f}"/>')
    for r in range(1, ROWS):
        y = MH / ROWS * r
        o.append(f'<line x1="0" y1="{y:.1f}" x2="{MW:.1f}" y2="{y:.1f}"/>')
    o.append('</g>')
    # avenue labels along their line, inside the boundary
    for s, (x, y, ux, uy) in AVES.items():
        ins = []
        for t in range(-900, 900, 6):
            px, py = x + ux * t, y + uy * t
            if 20 < px < MW - 20 and 20 < py < MH - 20 and inside(px, py, POLY):
                ins.append((px, py))
        if not ins:
            continue
        frac = {"GEORGIA AVE": 0.5, "KANSAS AVE": 0.3, "ILLINOIS AVE": 0.84, "NEW HAMPSHIRE AVE": 0.7}.get(s, 0.6)
        px, py = ins[int(len(ins) * frac)]
        ang = math.degrees(math.atan2(uy, ux))
        if ang > 90:
            ang -= 180
        if ang <= -90:
            ang += 180
        o.append(f'<text class="avl" transform="translate({px:.1f},{py:.1f}) rotate({ang:.1f})" '
                 f'text-anchor="middle" dy="-5">{esc(label_name(s))}</text>')

    # --- layers
    # 311 blocks (off by default)
    o.append('<g class="layer L-req">')
    for (lat, lon), c in req_spots.items():
        x, y = P(lat, lon)
        o.append(f'<circle class="req" cx="{x:.1f}" cy="{y:.1f}" r="{3 + 1.6 * math.sqrt(c - 1):.1f}">'
                 f'<title>{c} recent 311 request{"s" if c > 1 else ""} on this block</title></circle>')
    o.append('</g>')
    # minor permits
    o.append('<g class="layer L-permits">')
    for (lat, lon), c in minor_spots.items():
        x, y = P(lat, lon)
        o.append(f'<circle class="pm" cx="{x:.1f}" cy="{y:.1f}" r="{2.8 + 1.5 * math.sqrt(c - 1):.1f}">'
                 f'<title>{c} smaller permit{"s" if c > 1 else ""}</title></circle>')
    o.append('</g>')
    # curb segments
    o.append('<g class="layer L-curb">')
    for c in CURB:
        for g in c["geos"]:
            if g["seg"]:
                (ax, ay), (bx, by) = g["seg"]
                o.append(f'<line class="curb mk" data-mk="{c["id"]}" x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" '
                         f'y2="{by:.1f}"><title>{esc(c["type"])}: {esc(c["where"])}</title></line>')
            else:
                x, y = g["c"]
                o.append(f'<circle class="curbdot mk" data-mk="{c["id"]}" cx="{x:.1f}" cy="{y:.1f}" r="4">'
                         f'<title>{esc(c["type"])}: {esc(c["where"])}</title></circle>')
    o.append('</g>')
    # 1926 block
    o.append('<g class="layer L-then">')
    if FB_GEO and FB_GEO["seg"]:
        (ax, ay), (bx, by) = FB_GEO["seg"]
        o.append(f'<line class="then mk" data-mk="h1" x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}">'
                 f'<title>{esc(FB["block"])}: {FB["buildings"]} buildings in {FB["year"]}</title></line>')
        o.append(f'<text class="thenl" x="{(ax + bx) / 2:.1f}" y="{ay - 8:.1f}" text-anchor="middle">{FB["year"]}</text>')
    o.append('</g>')
    # bigger projects
    o.append('<g class="layer L-permits">')
    for p in PROJECTS:
        x, y = p["xy"]
        o.append(f'<g class="proj mk" data-mk="{p["id"]}" transform="translate({x:.1f},{y:.1f})" tabindex="-1">'
                 f'<title>{p["num"]}. {esc(p["addr"])}: {esc(p["group"])}</title>'
                 f'<rect x="-8.5" y="-8.5" width="17" height="17"/><text y="4.2" text-anchor="middle">{p["num"]}</text></g>')
    o.append('</g>')
    # events
    o.append('<g class="layer L-events">')
    for place, ev in EV_PLACES.items():
        if not ev["geo"]:
            continue
        x, y = ev["geo"]["c"]
        o.append(f'<g class="evt mk" data-mk="{ev["id"]}" transform="translate({x:.1f},{y:.1f})">'
                 f'<title>{ev["letter"]}. {esc(ev["title"])}, {esc(place)}</title>'
                 f'<circle r="10"/><text y="4.3" text-anchor="middle">{ev["letter"]}</text></g>')
    o.append('</g>')
    for nm, (x, y) in LANDMARKS:
        if nm.startswith("Sherman"):
            o.append(f'<text class="lm" x="{x - 17:.1f}" y="{y - 8:.1f}" text-anchor="end">{esc(nm)}</text>')
        else:
            o.append(f'<text class="lm" x="{x + 17:.1f}" y="{y + 4:.1f}">{esc(nm)}</text>')
    o.append('</g>')  # translate

    # frame (neat line) and grid labels
    o.append(f'<rect class="neat" x="{ML:.1f}" y="{MT:.1f}" width="{MW:.1f}" height="{MH:.1f}"/>')
    o.append(f'<rect class="neat2" x="{ML - 5:.1f}" y="{MT - 5:.1f}" width="{MW + 10:.1f}" height="{MH + 10:.1f}"/>')
    for c in range(COLS):
        x = ML + MW / COLS * (c + 0.5)
        o.append(f'<text class="gl" x="{x:.1f}" y="{MT - 11:.1f}" text-anchor="middle">{"ABCDEF"[c]}</text>')
    for r in range(ROWS):
        y = MT + MH / ROWS * (r + 0.5)
        o.append(f'<text class="gl" x="{ML - 13:.1f}" y="{y + 4:.1f}" text-anchor="middle">{r + 1}</text>')

    # E-W street names in the right margin, de-collided, with leaders
    labels_ew.sort()
    GAP = 22.0
    ys = [MT + y for y, _ in labels_ew]
    pos = ys[:]
    for _ in range(60):
        for i in range(1, len(pos)):
            if pos[i] - pos[i - 1] < GAP:
                mid = (pos[i] + pos[i - 1]) / 2
                pos[i - 1], pos[i] = mid - GAP / 2, mid + GAP / 2
    xm = ML + MW + 5
    for (y0, s), y in zip(labels_ew, pos):
        yy = MT + y0
        o.append(f'<path class="lead" d="M{xm:.1f},{yy:.1f} L{xm + 10:.1f},{yy:.1f} L{xm + 18:.1f},{y:.1f} L{xm + 22:.1f},{y:.1f}"/>')
        o.append(f'<text class="sl" x="{xm + 25:.1f}" y="{y + 4:.1f}">{esc(label_name(s).replace(" St", "").replace(" Pl", ""))}</text>')
    # N-S numbered streets along the bottom margin
    labels_ns.sort()
    for x, s in labels_ns:
        o.append(f'<line class="lead" x1="{ML + x:.1f}" y1="{MT + MH + 5:.1f}" x2="{ML + x:.1f}" y2="{MT + MH + 11:.1f}"/>')
        o.append(f'<text class="sl" x="{ML + x:.1f}" y="{MT + MH + 26:.1f}" text-anchor="middle">'
                 f'{esc(label_name(s).replace(" St", ""))}</text>')
    # scale bar + north
    m_per_unit = 111320 / K
    bar_m = 400
    bl = bar_m / m_per_unit
    sx, sy = ML, MT + MH + 52
    o.append(f'<g class="scale"><line x1="{sx:.1f}" y1="{sy:.1f}" x2="{sx + bl:.1f}" y2="{sy:.1f}"/>'
             f'<line x1="{sx:.1f}" y1="{sy - 4:.1f}" x2="{sx:.1f}" y2="{sy + 4:.1f}"/>'
             f'<line x1="{sx + bl / 2:.1f}" y1="{sy - 3:.1f}" x2="{sx + bl / 2:.1f}" y2="{sy + 3:.1f}"/>'
             f'<line x1="{sx + bl:.1f}" y1="{sy - 4:.1f}" x2="{sx + bl:.1f}" y2="{sy + 4:.1f}"/>'
             f'<text x="{sx + bl + 8:.1f}" y="{sy + 4:.1f}">{bar_m} m</text></g>')
    nx = ML + MW - 8
    o.append(f'<g class="north" transform="translate({nx:.1f},{sy - 2:.1f})"><path d="M0,-14 L5,4 L0,0 L-5,4 Z"/>'
             f'<text x="12" y="3">N</text></g>')
    o.append('</svg>')
    return "".join(o)


SVG = build_svg()

# ----------------------------------------------------------------------------- 311 condition
LABELS = {
    "DC Health Rodent & Vector Control": "rodent complaints",
    "DOEE - LIHEAP": "heating-assistance (LIHEAP) requests",
    "Bulk Collection": "bulk trash pickups",
    "Scheduled Yard Waste": "yard-waste pickups",
    "Illegal Dumping": "illegal dumping reports",
    "Trash Collection - Missed": "missed trash pickups",
    "Recycling Collection - Missed": "missed recycling pickups",
    "Container Removal": "trash-can removals",
    "Parking Enforcement": "parking enforcement calls",
    "Sanitation Enforcement": "sanitation enforcement calls",
    "Dead Animal Collection": "dead animal pickups",
    "Residential Parking Permit Violation": "residential parking violations",
}


def lbl(t):
    return LABELS.get(t, t.lower())


def lbl_title(t):
    s = lbl(t)
    return s[0].upper() + s[1:]


REQ = D["requests"]
bt = REQ["by_type"]
deltas = sorted(bt, key=lambda r: (abs(r["count"] - r["previous"]), r["count"]), reverse=True)
rise = max(bt, key=lambda r: r["count"] - r["previous"])
fall = min(bt, key=lambda r: r["count"] - r["previous"])


def change_phrase(r):
    c, p = r["count"], r["previous"]
    d = c - p
    if p == 0:
        return f"{lbl(r['type'])} went from none to {n(c)}"
    word = "rose" if d > 0 else "fell"
    tail = f" ({pct(c, p)})" if pct_ok(c, p) else ""
    return f"{lbl(r['type'])} {word} to {n(c)} from {n(p)}{tail}"


tot, ptot = REQ["total"], REQ["previous_total"]
lead_total = (f"311 requests in {NAME} {'fell' if tot < ptot else 'rose' if tot > ptot else 'held'} to {n(tot)} "
              f"in the last 30 days, from {n(ptot)} the 30 days before")
lead_total += f" ({pct(tot, ptot)})." if pct_ok(tot, ptot) else "."
first = deltas[0]
second = rise if first is fall else fall
LEAD = (f"{lead_total} The biggest swing: {change_phrase(first)}. "
        f"{'Biggest rise' if second is rise else 'Biggest drop'}: {change_phrase(second)}.")
LEAD = LEAD[0].upper() + LEAD[1:]

tally = {"rising": 0, "easing": 0, "steady": 0}
considered = 0
for r in bt:
    c, p = r["count"], r["previous"]
    if max(c, p) < 10:
        continue
    considered += 1
    thr = max(2, 0.10 * p)
    if c - p > thr:
        tally["rising"] += 1
    elif p - c > thr:
        tally["easing"] += 1
    else:
        tally["steady"] += 1

# ----------------------------------------------------------------------------- HTML pieces
def chip(ref, rid, label=None):
    return (f'<a class="ref" href="#map" data-go="{rid}" aria-label="Show on map, square {ref}">'
            f'{esc(label) + " " if label else ""}<span>{ref}</span></a>')


def news_html():
    items = D["news"]["items"][:7]
    if not items:
        return '<p class="empty">No headlines from local outlets in the last 180 days.</p>'
    o = ['<ol class="news">']
    for it in items:
        d = to_et(it["published"]).date()
        o.append(f'<li><a class="hl" href="{esc(it["url"])}">{esc(it["title"])}</a>'
                 f'<span class="meta">{esc(it["source"])} <i aria-hidden="true">/</i> '
                 f'<time datetime="{d.isoformat()}">{day_label(d, TODAY)}</time></span></li>')
    o.append('</ol>')
    outlets = D["news"]["outlets"]
    o.append(f'<p class="fine">Headlines that mention {NAME}, from {len(outlets)} local outlets checked nightly. '
             f'Each links to the outlet; we never copy articles. <a href="/news/">All news &amp; events</a></p>')
    return "".join(o)


def events_html():
    if not ev_soon:
        o = ['<p class="empty">Nothing on the calendars we read for the next 14 days.</p>']
    else:
        o = ['<ol class="events">']
        by_day = OrderedDict()
        for e in ev_soon:
            by_day.setdefault(e["date"], []).append(e)
        for ds, evs in by_day.items():
            d = dt.date.fromisoformat(ds)
            rel = (d - TODAY).days
            tag = "Today" if rel == 0 else "Tomorrow" if rel == 1 else d.strftime("%a")
            o.append(f'<li class="day"><div class="date"><span class="dow">{tag}</span>'
                     f'<span class="dnum">{d.day}</span><span class="mon">{d.strftime("%b")}</span></div><ul>')
            for e in evs:
                ep = EV_PLACES[e["place"]]
                ref = grid_ref(*ep["geo"]["c"]) if ep["geo"] else None
                when = (e.get("time") or "").replace(":00", "").replace(" - ", "–")
                o.append(f'<li data-ref="{ep["id"]}" id="i-{ep["id"]}-{ds}">'
                         f'<span class="evkey" aria-hidden="true">{ep["letter"]}</span>'
                         f'<div><a class="et" href="{esc(e["url"])}">{esc(e["title"])}</a>'
                         f'<span class="meta">{esc(when)} <i aria-hidden="true">/</i> {esc(e["place"])}</span></div>'
                         f'{chip(ref, ep["id"]) if ref else ""}</li>')
            o.append('</ul></li>')
        o.append('</ol>')
        if ev_later:
            later = ", ".join(sorted({short_date(dt.date.fromisoformat(e["date"])) for e in ev_later},
                                     key=lambda s: dt.datetime.strptime(s + " 2026", "%b %d %Y")))
            o.append(f'<p class="fine">Further out on the market calendar: {later}.</p>')
    links = D["events"]["links"]
    anc = D["events"].get("anc_meetings") or []
    o.append('<p class="also"><span>Also check</span> ' + " ".join(
        f'<a href="{esc(l["url"])}">{esc(l["name"])}</a>' for l in links) + '</p>')
    if not anc:
        o.append('<p class="fine">No ANC meetings were posted for the next 30 days when we last looked.</p>')
    return "".join(o)


def curb_html():
    cu = D["streets"]["curb"]
    o = [f'<p class="dek">{cu["starting_next_7d"]} curb-space permits start in the next 7 days; '
         f'{cu["active_this_week"]} are active this week, reserving {n(cu["reserved_ft"])} ft of curb in all.</p>']
    if not CURB:
        o.append('<p class="empty">No curb permits start in the next 7 days.</p>')
        return "".join(o)
    o.append('<ul class="curb-list">')
    for c in CURB:
        ref = grid_ref(*c["geos"][0]["c"]) if c["geos"] else None
        hrs = f' <i aria-hidden="true">/</i> {esc(c["hours"])}' if c["hours"] else ""
        o.append(f'<li data-ref="{c["id"]}" id="i-{c["id"]}"><span class="when">{range_label(c["start"], c["end"])}</span>'
                 f'<div><strong>{esc(c["where"])}</strong><span class="meta">{esc(c["type"])}{hrs}</span></div>'
                 f'{chip(ref, c["id"]) if ref else "<span class=nomap>not mapped</span>"}</li>')
    o.append('</ul><p class="fine">From DDOT’s public-space occupancy permits. Blocks are placed on the map '
             'at hundred-block precision. <a href="/streets/">Streets</a></p>')
    return "".join(o)


def projects_html():
    o = [f'<p class="dek">{len(D["permits"])} permits were issued {short_date(p_dates[0])}–{short_date(p_dates[-1])}. '
         f'Most are trade work; these {len(PROJECTS)} are additions, demolitions or new buildings.</p>']
    if not PROJECTS:
        o.append('<p class="empty">No additions, demolitions or new buildings were permitted in the last 30 days.</p>')
        return "".join(o)
    o.append('<ol class="projects">')
    for p in PROJECTS:
        more = f' Plus {p["others"]} other permit{"s" if p["others"] > 1 else ""} at this address.' if p["others"] else ""
        o.append(f'<li data-ref="{p["id"]}" id="i-{p["id"]}"><span class="pnum" aria-hidden="true">{p["num"]}</span>'
                 f'<div><strong>{esc(p["addr"])}</strong><span class="meta">{esc(p["group"])} '
                 f'<i aria-hidden="true">/</i> issued {short_date(p["issued"])}</span>'
                 f'{f"<p>{esc(p["work"])}{esc(more)}</p>" if p["work"] or more else ""}</div>'
                 f'{chip(p["ref"], p["id"])}</li>')
    o.append('</ol><p class="fine"><a href="/projects/">All projects and permits</a></p>')
    return "".join(o)


def legend_html():
    items = [("permits", "Permits", f"{permits_in} in 30 days", True),
             ("events", "Markets", f"{sum(1 for v in EV_PLACES.values() if v['geo'])} places", True),
             ("curb", "Curb reserved", "starting this week", True),
             ("then", "1926", "featured block", True),
             ("req", "311 requests", "recent, by block", False)]
    o = ['<div class="legend" role="group" aria-label="Map layers">']
    for key, name, sub, on in items:
        o.append(f'<button type="button" class="lg lg-{key}" data-layer="{key}" aria-pressed="{"true" if on else "false"}">'
                 f'<span class="sw" aria-hidden="true"></span><span class="lt">{name}</span><span class="ls">{sub}</span></button>')
    o.append('</div>')
    return "".join(o)


def measures_html():
    homes = D["homes"]["house"]
    cr = D["crime"]
    rows = []
    d311 = tot - ptot
    rows.append(("311 requests", n(tot), f"{n(ptot)} the 30 days before",
                 f"{'Down' if d311 < 0 else 'Up'} {n(abs(d311))}" + (f" ({pct(tot, ptot)})" if pct_ok(tot, ptot) else ""),
                 "Last 30 days", "/streets/"))
    dc = cr["total"] - cr["previous_total"]
    rows.append(("Crime reports", n(cr["total"]), f"{n(cr['previous_total'])} the 30 days before",
                 f"{n(abs(dc))} {'more' if dc > 0 else 'fewer'}; small counts swing month to month",
                 "Last 30 days · counts only, never mapped", None))
    dh = homes["median_12mo"] - homes["median_prev_12mo"]
    hp = f" ({pct(homes['median_12mo'], homes['median_prev_12mo'])})" if pct_ok(homes["count_12mo"], homes["count_prev_12mo"]) else ""
    rows.append(("Median house price", money(homes["median_12mo"]), f"{money(homes['median_prev_12mo'])} the year before",
                 f"{'Down' if dh < 0 else 'Up'} {money(abs(dh))}{hp}",
                 f"Last 12 months · {homes['count_12mo']} sales vs {homes['count_prev_12mo']}", "/homes/"))
    rows.append(("Building permits", n(len(D["permits"])), "no prior-period count in this feed",
                 f"{len(big)} bigger, {len(D['permits']) - len(big)} smaller", "Last 30 days", "/projects/"))
    o = ['<dl class="measures">']
    for label, big_v, prev, delta, period, href in rows:
        o.append(f'<div class="ms"><dt>{label}</dt><dd class="mv">{big_v}</dd><dd class="md">{esc(delta)}</dd>'
                 f'<dd class="mp">{esc(prev)}</dd><dd class="mper">{esc(period)}</dd></div>')
    o.append('</dl>')
    return "".join(o)


def condition_html():
    total = sum(tally.values())
    segs = "".join(f'<span class="tb tb-{k}" style="flex:{v}" title="{v} {k}"></span>' for k, v in tally.items() if v)
    return (f'<p class="lead">{esc(LEAD)}</p>'
            f'<div class="tally"><div class="tbar" aria-hidden="true">{segs}</div>'
            f'<p><strong>{tally["rising"]}</strong> rising <i aria-hidden="true">/</i> <strong>{tally["easing"]}</strong> easing '
            f'<i aria-hidden="true">/</i> <strong>{tally["steady"]}</strong> steady, across the {total} kinds of 311 request '
            f'with at least 10 in either period. A change within 10% (or 2 requests) counts as steady.</p></div>')


def requests_html():
    top = sorted(bt, key=lambda r: r["count"], reverse=True)[:8]
    mx = max(max(r["count"], r["previous"]) for r in top)
    o = ['<ul class="bars">']
    for r in top:
        w = r["count"] / mx * 100
        pv = r["previous"] / mx * 100
        o.append(f'<li><span class="bl">{esc(lbl_title(r["type"]))}</span>'
                 f'<span class="bt"><span class="bf" style="width:{w:.1f}%"></span>'
                 f'<span class="bp" style="left:{pv:.1f}%" title="30 days before: {r["previous"]}"></span></span>'
                 f'<span class="bn">{n(r["count"])}<small> / {n(r["previous"])}</small></span></li>')
    o.append('</ul><p class="fine">Last 30 days, bar; the tick and small number are the 30 days before. '
             f'{REQ["open"]} requests are still open.</p>')
    return "".join(o)


def homes_html():
    h = D["homes"]
    hs, co, l60 = h["house"], h["condo"], h["last_60d"]
    months = h["by_month"]
    vals = [m["median"] for m in months if m["median"]]
    lo, hi = 0, max(vals)
    cols = []
    for m in months:
        mo = dt.date.fromisoformat(m["month"] + "-01")
        if m["median"]:
            ht = (m["median"] - lo) / (hi - lo) * 100
            cols.append(f'<span class="mc" title="{mo.strftime("%b %Y")}: {money(m["median"])}, {m["count"]} sales">'
                        f'<span style="height:{max(ht, 4):.0f}%"></span><b>{mo.strftime("%b")[0]}</b></span>')
        else:
            cols.append(f'<span class="mc na" title="{mo.strftime("%b %Y")}: under 3 sales"><span></span><b>{mo.strftime("%b")[0]}</b></span>')
    o = [f'<div class="kv"><div><span class="k">Houses</span><span class="v">{money(hs["median_12mo"])}</span>'
         f'<span class="s">median, {hs["count_12mo"]} sales in 12 months</span></div>'
         f'<div><span class="k">Condos</span><span class="v">{money(co["median_12mo"])}</span>'
         f'<span class="s">median, {co["count_12mo"]} sales; {money(co["median_prev_12mo"])} the year before ({co["count_prev_12mo"]} sales)</span></div></div>',
         f'<div class="months" role="img" aria-label="Monthly median house price, last 12 months, from {money(min(vals))} to {money(max(vals))}">{"".join(cols)}</div>',
         f'<p class="fine">Monthly median house price; blank months had under 3 sales. Last 60 days: {money(l60["median"])} '
         f'median, ${l60["median_ppsf"]} per sq ft, {l60["count"]} sales. {h["above_assessment_12mo"]["n"]} of '
         f'{h["above_assessment_12mo"]["of"]} sales in the past year closed above assessed value.</p>',
         '<table class="sales"><caption>Recent sales</caption><thead><tr><th scope="col">Address</th><th scope="col">Date</th>'
         '<th scope="col" class="num">Price</th></tr></thead><tbody>']
    for s in h["recent_sales"][:5]:
        d = dt.date.fromisoformat(s["date"])
        o.append(f'<tr><td>{esc(s["address"])}<small>{s["kind"]}, {s["beds"]} bd, {n(s["sqft"])} sq ft</small></td>'
                 f'<td>{short_date(d)}</td><td class="num">{money(s["price"])}</td></tr>')
    o.append('</tbody></table><p class="fine">Sales are matched by the tax office’s “Petworth” assessment '
             'area, which overlaps but does not match the map boundary. <a href="/homes/">Homes</a></p>')
    return "".join(o)


def trees_html():
    t = D["streets"]["trees"]
    top = t["top_species"][:5]
    o = [f'<div class="kv"><div><span class="k">Street trees</span><span class="v">{n(t["total"])}</span>'
         f'<span class="s">{t["species"]} species; {n(t["planted_5y"])} planted in the last 5 years</span></div>'
         f'<div><span class="k">Empty tree boxes</span><span class="v">{t["empty_boxes"]}</span>'
         f'<span class="s">ready to plant</span></div></div>',
         '<p class="sub">Most common</p><p class="plain">' +
         ", ".join(f'{esc(s["name"])} {s["count"]}' for s in top) + '</p>',
         '<p class="sub">Biggest trunks</p><ul class="plainlist">']
    for b in t["biggest"][:4]:
        o.append(f'<li>{esc(b["species"])}, {b["dbh_in"]:.0f} in across <span class="meta">{esc(b["block"])}</span></li>')
    o.append(f'</ul><p class="fine">DDOT urban forestry inventory, {short_date(dt.date.fromisoformat(t["inventory_date"]))}. '
             '<a href="/streets/">Streets</a></p>')
    return "".join(o)


def permit_types_html():
    rows = sorted(group_counts.items(), key=lambda kv: kv[1], reverse=True)
    mx = rows[0][1]
    o = ['<ul class="bars bars-p">']
    for g, c in rows:
        o.append(f'<li><span class="bl">{esc(g)}</span><span class="bt"><span class="bf{" bf-big" if g in BIG_GROUPS else ""}" '
                 f'style="width:{c / mx * 100:.1f}%"></span></span><span class="bn">{c}</span></li>')
    o.append('</ul>')
    return "".join(o)


def then_html():
    a = D["history"]["archive"]
    b = D["history"]["buildings"]
    ref = grid_ref(*FB_GEO["c"]) if FB_GEO else None
    decades = b["by_decade"]
    mx = max(x["count"] for x in decades)
    dec = "".join(f'<span class="dc" title="{x["decade"]}s: {n(x["count"])} buildings"><span style="height:{max(x["count"] / mx * 100, 2):.0f}%"></span>'
                  f'<b>{str(x["decade"])[2:]}s</b></span>' for x in decades)
    # People are not named: the sentence is rebuilt from the numbers only.
    lp = FB["largest_permit"]
    sentence = (f'In {FB["year"]}, one builder put up {FB["buildings"]} buildings on the {FB["block"]} under '
                f'{FB["permits"]} permits. The largest permit alone covered {lp["buildings"]} buildings at an '
                f'estimated ${n(lp["cost"])}.')
    def noise(c):  # prefer clips the scanner read cleanly
        toks = c["text"].split()
        bad = sum(1 for t in toks if re.search(r"[^A-Za-z,.;:'\-]", t) or re.search(r"[a-z][A-Z]", t))
        return bad / max(len(toks), 1)
    circ = [c for c in a["clips"] if "Circle" in c["text"]]
    picks = sorted(circ or a["clips"], key=noise)[:2]
    picks.sort(key=lambda c: (c["date"], c["page"]))
    o = [f'<div class="then-grid"><div><p class="then-lead" data-ref="h1" id="i-h1">{esc(sentence)} '
         f'{chip(ref, "h1") if ref else ""}</p>',
         f'<div class="decades" role="img" aria-label="Historic building permits by decade, peaking at {n(mx)} in the 1920s">{dec}</div>',
         f'<p class="fine">{n(b["records"])} building permits on record from {b["year_min"]} to {b["year_max"]}, '
         'by decade (DC Historic Preservation Office).</p></div><div>',
         f'<p class="sub">This week in {a["week_start"][:4]}: the {esc(a["paper"])}, {esc(a["week_label"].replace(chr(0x2013), "to").replace("  ", " "))}</p>']
    for c in picks:
        d = dt.date.fromisoformat(c["date"])
        lm = next(((nm, pt) for nm, pt in LANDMARKS if nm in c["text"]), None)
        attr = f' data-ref="{lm[0].split()[0].lower()}"' if lm else ""
        ch = " " + chip(grid_ref(*lm[1]), lm[0].split()[0].lower(), lm[0]) if lm else ""
        o.append(f'<blockquote{attr}><p>“{esc(c["text"])}”</p><a href="{esc(c["url"])}">{d.strftime("%b")} {d.day}, '
                 f'{d.year}, page {c["page"]}</a>{ch}</blockquote>')
    o.append('<p class="fine">Machine-read text from Library of Congress scans; misspellings are the scanner’s. '
             '<a href="/then/">More from the archive</a></p></div></div>')
    return "".join(o)


def reps_html():
    by_anc = OrderedDict()
    for s in D["smds"]:
        by_anc.setdefault(s["anc"], {"url": s["url"], "smds": []})["smds"].append(s["smd"])
    o = [f'<p class="dek">{NAME} overlaps {len(D["smds"])} single-member districts in {len(by_anc)} advisory '
         'neighborhood commissions.</p><ul class="ancs">']
    for anc, v in by_anc.items():
        o.append(f'<li><a href="{esc(v["url"])}">ANC {anc}</a><span class="meta">{", ".join(v["smds"])}</span></li>')
    o.append('</ul><p class="fine"><a href="/representatives/">Find your commissioner and council member</a></p>')
    return "".join(o)


centroid_lat = statistics.fmean(LATS)
centroid_lon = statistics.fmean(LONS)
gen_label = f'{GEN.strftime("%a, %b")} {GEN.day}, {GEN.year}, {GEN.strftime("%I:%M %p").lstrip("0")} ET'
wards = sorted({s["anc"][0] for s in D["smds"]})
sources = D["sources"]

CSS = r"""
:root{
  --paper:#ffffff; --ink:#14222c; --ink2:#3f4f5a; --ink3:#5f6d77; --rule:#d3dadf; --rule2:#e7ecef;
  --land:#f1f4f6; --outside:#e3e8ec; --street:#ffffff; --ave:#ffffff; --ribbon:#9cc6c9; --line:#14222c;
  --red:#b3361f; --green:#1c6e45; --ochre:#94570a; --sepia:#76563a; --blue:#2b609c; --link:#1c4e84;
  --serif:"Newsreader",Georgia,"Times New Roman",serif;
  --sans:"IBM Plex Sans Condensed","Arial Narrow",Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 17px/1.5 var(--serif);
  font-optical-sizing:auto;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px;
  text-decoration-color:color-mix(in srgb,var(--link) 45%,transparent)}
a:hover{text-decoration-color:currentColor}
a:focus-visible,button:focus-visible{outline:2px solid var(--link);outline-offset:2px}
i{font-style:normal;color:var(--rule)}
.wrap{max-width:1280px;margin:0 auto;padding:0 40px}
.skip{position:absolute;left:-999px}.skip:focus{left:12px;top:8px;background:#fff;padding:6px 10px;z-index:9}

/* masthead */
.topline{border-bottom:1px solid var(--rule);font:500 13px/1.3 var(--sans);letter-spacing:.02em;color:var(--ink2)}
.topline .wrap{display:flex;justify-content:space-between;gap:16px;padding-top:10px;padding-bottom:10px;flex-wrap:wrap}
.topline b{font-weight:600;color:var(--ink);letter-spacing:.06em;text-transform:uppercase}
.mast>.wrap{display:grid;grid-template-columns:auto 1fr;align-items:end;gap:8px 40px;padding-top:28px;padding-bottom:18px}
.mast h1{margin:0;font:500 112px/0.86 var(--serif);letter-spacing:-.035em;font-variation-settings:"opsz" 72}
.mast .about{font:400 19px/1.4 var(--serif);color:var(--ink2);max-width:36ch;padding-bottom:8px}
.mast .coords{display:block;margin-top:6px;font:500 12px/1.3 var(--mono);color:var(--ink3);letter-spacing:.02em}
nav.sections{border-top:3px solid var(--ink);border-bottom:1px solid var(--rule)}
nav.sections ul{list-style:none;margin:0;padding:0;display:flex;gap:4px 26px;flex-wrap:wrap}
nav.sections a{display:inline-block;padding:10px 0;font:500 14px/1.2 var(--sans);letter-spacing:.04em;
  text-transform:uppercase;color:var(--ink);text-decoration:none}
nav.sections a:hover{text-decoration:underline}

/* section heads */
.sh{display:flex;align-items:baseline;justify-content:space-between;gap:12px;border-top:1px solid var(--ink);
  padding-top:10px;margin:0 0 14px}
.sh h2{margin:0;font:600 13px/1.2 var(--sans);letter-spacing:.12em;text-transform:uppercase}
.sh .aside{font:400 13px/1.2 var(--sans);color:var(--ink3)}
.meta{display:block;font:400 14px/1.4 var(--sans);color:var(--ink3);margin-top:2px}
.fine{font:400 13.5px/1.45 var(--sans);color:var(--ink3);margin:12px 0 0}
.dek{font:400 16px/1.45 var(--serif);color:var(--ink2);margin:0 0 12px}
.empty{font:italic 400 16px/1.45 var(--serif);color:var(--ink2)}
.sub{font:600 12px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--ink2);margin:18px 0 6px}

/* spread: text column + map plate */
.spread{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);column-gap:48px;padding-top:30px;
  grid-template-areas:"news map" "events map" "street map" "projects map" "rest map"}
#news{grid-area:news}#events{grid-area:events}#street{grid-area:street}#projects{grid-area:projects}
#map{grid-area:map;align-self:start;position:sticky;top:10px}
.spread>section{margin-bottom:40px}

ol.news{list-style:none;margin:0;padding:0}
ol.news li{padding:11px 0 12px;border-bottom:1px solid var(--rule2)}
ol.news li:first-child{padding-top:2px}
ol.news a.hl{font:500 21px/1.22 var(--serif);color:var(--ink);text-decoration:none;letter-spacing:-.005em}
ol.news a.hl:hover{text-decoration:underline;text-decoration-color:var(--ink3)}

ol.events{list-style:none;margin:0;padding:0}
li.day{display:grid;grid-template-columns:58px 1fr;gap:14px;padding:10px 0;border-bottom:1px solid var(--rule2)}
.date{display:flex;flex-direction:column;align-items:flex-start;font-family:var(--sans);line-height:1}
.dow{font:600 11.5px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--green)}
.dnum{font:500 34px/1 var(--serif);margin-top:3px}
.mon{font:500 12px/1 var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-top:2px}
li.day ul{list-style:none;margin:0;padding:0}
li.day ul li{display:grid;grid-template-columns:26px 1fr auto;gap:10px;align-items:start;padding:2px 0}
.evkey{width:22px;height:22px;border-radius:50%;background:var(--green);color:#fff;font:600 12px/22px var(--sans);
  text-align:center;margin-top:3px}
a.et{font:500 19px/1.25 var(--serif);color:var(--ink)}
.also{font:400 15px/1.6 var(--sans);margin:14px 0 0}
.also span{font-weight:600;letter-spacing:.08em;text-transform:uppercase;font-size:12px;color:var(--ink2);margin-right:6px}
.also a{margin-right:14px;white-space:nowrap}

a.ref{display:inline-flex;align-items:center;gap:4px;font:500 12px/1 var(--mono);color:var(--ink2);text-decoration:none;
  border:1px solid var(--rule);padding:4px 6px;margin-top:3px;white-space:nowrap;background:#fff}
a.ref:hover,a.ref:focus-visible{border-color:var(--ink);color:var(--ink)}
a.ref::before{content:"";width:9px;height:9px;border:1.5px solid currentColor;border-radius:50% 50% 50% 0;transform:rotate(-45deg);
  margin-right:1px}
.nomap{font:400 12px/1 var(--sans);color:var(--ink3);margin-top:6px}

ul.curb-list{list-style:none;margin:0;padding:0}
ul.curb-list li{display:grid;grid-template-columns:96px 1fr auto;gap:12px;padding:9px 0;border-bottom:1px solid var(--rule2);align-items:start}
.when{font:500 14px/1.35 var(--sans);color:var(--ochre)}
ul.curb-list strong,ol.projects strong{font:500 17px/1.3 var(--serif)}
ol.projects{list-style:none;margin:0;padding:0}
ol.projects li{display:grid;grid-template-columns:26px 1fr auto;gap:12px;padding:11px 0;border-bottom:1px solid var(--rule2);align-items:start}
ol.projects p{margin:5px 0 0;font:400 15px/1.45 var(--serif);color:var(--ink2)}
.pnum{width:21px;height:21px;background:var(--red);color:#fff;font:600 12px/21px var(--sans);text-align:center;margin-top:2px}
[data-ref].on{background:linear-gradient(90deg,#eef4f7,transparent)}

/* the plate */
.plate{border-top:1px solid var(--ink);padding-top:10px}
.plate-h{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:8px}
.plate-h h2{margin:0;font:600 13px/1.2 var(--sans);letter-spacing:.12em;text-transform:uppercase}
.plate-h p{margin:0;font:400 13px/1.2 var(--sans);color:var(--ink3);text-align:right}
.plate svg{display:block;width:100%;height:auto;max-height:calc(100vh - 170px)}
.legend{display:flex;flex-wrap:wrap;gap:6px 6px;margin:0 0 8px}
.lg{display:grid;grid-template-columns:16px auto;column-gap:7px;align-items:center;text-align:left;cursor:pointer;
  background:#fff;border:1px solid var(--rule);padding:5px 9px 5px 7px;color:var(--ink);font-family:var(--sans)}
.lg .lt{font:500 13px/1.15 var(--sans)}
.lg .ls{grid-column:2;font:400 11.5px/1.15 var(--sans);color:var(--ink3)}
.lg .sw{grid-row:1/3;width:14px;height:14px;display:block}
.lg[aria-pressed="false"]{color:var(--ink3);background:var(--land);border-style:dashed}
.lg[aria-pressed="false"] .sw{opacity:.35}
.lg-permits .sw{background:var(--red);box-shadow:inset 0 0 0 3px #fff;outline:1px solid var(--red)}
.lg-events .sw{background:var(--green);border-radius:50%}
.lg-curb .sw{height:5px;background:var(--ochre)}
.lg-then .sw{height:0;border-top:3px dotted var(--sepia)}
.lg-req .sw{border:2px solid var(--blue);border-radius:50%}
.plate .fine{margin-top:6px}

svg .outside{fill:var(--outside)}
svg .hatch{stroke:#d3dbe1;stroke-width:1}
svg .land{fill:var(--land)}
svg .st{stroke:var(--street);stroke-width:4.5;stroke-linecap:round}
svg .ave{stroke:var(--ave);stroke-width:8}
svg .circ{fill:#dde9df;stroke:#fff;stroke-width:4}
svg .circ-hit{fill:transparent;stroke:transparent;stroke-width:2}
svg .circ-hit.hl{stroke:var(--green)!important;stroke-width:3!important}
svg .ribbon{fill:none;stroke:var(--ribbon);stroke-width:12;opacity:.55}
svg .bline{fill:none;stroke:var(--line);stroke-width:1.4;stroke-dasharray:9 3 2 3}
svg .grid line{stroke:#7d8b95;stroke-width:.6;stroke-dasharray:1 3;opacity:.7}
svg .neat{fill:none;stroke:var(--ink);stroke-width:1}
svg .neat2{fill:none;stroke:var(--ink);stroke-width:2.2}
svg text{font-family:var(--sans)}
svg .gl{font:600 12px var(--mono);fill:var(--ink2)}
svg .sl{font:500 12.5px var(--sans);fill:var(--ink2)}
svg .lead{fill:none;stroke:#9aa6ae;stroke-width:.8}
svg .avl{font:italic 500 12.5px var(--serif);fill:var(--ink2);letter-spacing:.03em;paint-order:stroke;stroke:#fff;stroke-width:3.5px}
svg .lm{font:italic 400 12px var(--serif);fill:#3d5a45;paint-order:stroke;stroke:var(--land);stroke-width:3px}
svg .scale line{stroke:var(--ink);stroke-width:1.4}
svg .scale text,svg .north text{font:500 12px var(--sans);fill:var(--ink2)}
svg .north path{fill:var(--ink)}
svg .pm{fill:var(--ink);fill-opacity:.62;stroke:#fff;stroke-width:1}
svg .req{fill:none;stroke:var(--blue);stroke-width:1.6}
svg .curb{stroke:var(--ochre);stroke-width:7;stroke-linecap:butt}
svg .curbdot{fill:var(--ochre)}
svg .then{stroke:var(--sepia);stroke-width:4;stroke-dasharray:1.5 4;stroke-linecap:round}
svg .thenl{font:italic 600 13px var(--serif);fill:var(--sepia);paint-order:stroke;stroke:var(--land);stroke-width:3px}
svg .proj rect{fill:var(--red);stroke:#fff;stroke-width:1.6}
svg .proj text{font:600 11.5px var(--sans);fill:#fff}
svg .evt circle{fill:var(--green);stroke:#fff;stroke-width:2}
svg .evt text{font:600 12px var(--sans);fill:#fff}
svg .mk{cursor:pointer;transition:opacity .2s}
svg .mk.hl rect,svg .mk.hl circle{stroke:var(--ink);stroke-width:3}
svg line.mk.hl{stroke-width:12}
svg.hide-permits .L-permits,svg.hide-events .L-events,svg.hide-curb .L-curb,svg.hide-then .L-then,svg.hide-req .L-req{display:none}
svg.dim .mk:not(.hl){opacity:.28}

/* numbers */
.band{border-top:3px solid var(--ink);margin-top:10px;padding-top:26px}
.band-grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:48px}
.lead{font:400 27px/1.32 var(--serif);margin:0;letter-spacing:-.005em;font-variation-settings:"opsz" 36}
.tally{margin-top:16px}
.tbar{display:flex;height:8px;gap:2px}
.tb-rising{background:var(--ink)}.tb-easing{background:#7e8e99}.tb-steady{background:#cfd7dc}
.tally p{font:400 14px/1.45 var(--sans);color:var(--ink2);margin:8px 0 0}
.measures{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin:0;border-left:1px solid var(--rule)}
.ms{padding:2px 16px 4px;border-right:1px solid var(--rule)}
.ms dt{font:600 12px/1.25 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);min-height:2.5em}
.ms dd{margin:0}
.mv{font:500 42px/1.05 var(--serif);letter-spacing:-.02em;margin-top:6px!important;font-variant-numeric:lining-nums tabular-nums}
.md{font:500 14px/1.35 var(--sans);margin-top:6px!important}
.mp,.mper{font:400 13px/1.35 var(--sans);color:var(--ink3)}
.mper{margin-top:8px!important;padding-top:6px!important;border-top:1px solid var(--rule2)}

/* ledger */
.ledger{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:40px 48px;padding-top:44px}
.ledger>section{min-width:0}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.kv .k{display:block;font:600 12px/1.2 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--ink2)}
.kv .v{display:block;font:500 34px/1.1 var(--serif);letter-spacing:-.02em;margin-top:4px}
.kv .s{display:block;font:400 13.5px/1.35 var(--sans);color:var(--ink3);margin-top:3px}
.months{display:grid;grid-template-columns:repeat(12,1fr);gap:3px;height:84px;margin-top:18px;align-items:end}
.mc{display:flex;flex-direction:column;justify-content:flex-end;height:100%}
.mc span{display:block;background:#8796a0}
.mc.na span{height:2px;background:repeating-linear-gradient(90deg,#b8c2c8 0 2px,transparent 2px 4px)}
.mc b{font:500 10.5px/1 var(--sans);color:var(--ink3);text-align:center;margin-top:4px}
table.sales{width:100%;border-collapse:collapse;margin-top:16px;font:400 14.5px/1.35 var(--sans)}
table.sales caption{text-align:left;font:600 12px/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--ink2);padding-bottom:6px}
table.sales th{font:500 12px/1.2 var(--sans);color:var(--ink3);text-align:left;border-bottom:1px solid var(--ink);padding:4px 0}
table.sales td{border-bottom:1px solid var(--rule2);padding:6px 6px 6px 0;vertical-align:top}
table.sales td small{display:block;color:var(--ink3);font-size:12.5px}
.num{text-align:right!important;font-variant-numeric:tabular-nums;white-space:nowrap}
ul.bars{list-style:none;margin:0;padding:0}
ul.bars li{display:grid;grid-template-columns:minmax(0,1fr) 84px;grid-template-areas:"l n" "t t";column-gap:10px;padding:5px 0}
.bl{grid-area:l;font:400 14.5px/1.3 var(--sans)}
.bn{grid-area:n;font:500 14.5px/1.3 var(--sans);text-align:right;font-variant-numeric:tabular-nums}
.bn small{color:var(--ink3);font-weight:400;font-size:12.5px}
.bt{grid-area:t;position:relative;height:7px;background:var(--rule2);margin-top:3px}
.bf{position:absolute;left:0;top:0;bottom:0;background:#56656f}
.bf-big{background:var(--red)}
.bp{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--ink);margin-left:-1px}
.bars-p li{grid-template-columns:minmax(0,1fr) 40px}
.plain{margin:0;font:400 15px/1.5 var(--serif)}
ul.plainlist{list-style:none;margin:0;padding:0;font:400 15px/1.4 var(--serif)}
ul.plainlist li{padding:4px 0;border-bottom:1px solid var(--rule2)}
ul.plainlist .meta{display:inline;margin-left:4px;font-size:13px}

.then{border-top:3px solid var(--ink);margin-top:48px;padding-top:26px}
.then-grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:48px}
.then-lead{font:400 24px/1.35 var(--serif);margin:0}
.decades{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;height:90px;margin-top:20px;align-items:end}
.dc{display:flex;flex-direction:column;justify-content:flex-end;height:100%}
.dc span{display:block;background:var(--sepia);opacity:.85}
.dc b{font:500 11px/1 var(--sans);color:var(--ink3);text-align:center;margin-top:4px}
blockquote{margin:0 0 16px;padding:0 0 0 18px;border-left:2px solid var(--sepia)}
blockquote p{margin:0;font:italic 400 19px/1.45 var(--serif);color:var(--ink)}
blockquote a{font:400 13px/1.3 var(--sans)}

.civic{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:48px;border-top:3px solid var(--ink);margin-top:48px;padding-top:26px}
ul.ancs{list-style:none;margin:0;padding:0}
ul.ancs li{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid var(--rule2);font:500 17px/1.3 var(--serif)}
ul.ancs .meta{margin:0;font-family:var(--mono);font-size:13px}
form.signup{display:flex;gap:0;max-width:520px;margin-top:4px}
form.signup label{position:absolute;left:-999px}
form.signup input{flex:1;min-width:0;font:400 17px/1.2 var(--sans);padding:12px 12px;border:1px solid var(--ink);border-right:0;background:#fff;color:var(--ink);border-radius:0}
form.signup button{font:600 14px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;padding:0 18px;border:1px solid var(--ink);background:var(--ink);color:#fff;cursor:pointer;border-radius:0}

footer{margin-top:56px;border-top:1px solid var(--ink);background:#f1f4f6}
footer .wrap{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:48px;padding-top:22px;padding-bottom:36px;font:400 14px/1.5 var(--sans);color:var(--ink2)}
footer strong{color:var(--ink)}
footer ul{margin:0;padding:0;list-style:none;columns:2;column-gap:28px}
footer li{margin-bottom:4px;break-inside:avoid}

/* tablet */
@media (max-width:1060px){
  .ledger{grid-template-columns:repeat(2,minmax(0,1fr))}
  .measures{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:22px}
  .band-grid{grid-template-columns:1fr;gap:24px}
}
/* phone */
@media (max-width:760px){
  body{font-size:16px}
  .wrap{padding:0 16px}
  .topline .wrap{font-size:12px;gap:2px 12px}
  .mast>.wrap{grid-template-columns:1fr;padding-top:18px;padding-bottom:14px;gap:10px}
  .mast h1{font-size:64px}
  .mast .about{font-size:17px;padding:0}
  nav.sections ul{gap:0 16px;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
  nav.sections a{font-size:13px;white-space:nowrap}
  .spread{grid-template-columns:minmax(0,1fr);grid-template-areas:"news" "events" "map" "street" "projects";padding-top:22px}
  #map{position:static;margin-bottom:36px}
  .spread>section{margin-bottom:32px}
  ol.news a.hl{font-size:19px}
  li.day{grid-template-columns:56px 1fr;gap:8px}
  .dow{font-size:10px;letter-spacing:.04em}
  .dnum{font-size:28px}
  li.day ul li{grid-template-columns:22px minmax(0,1fr);row-gap:4px}
  li.day ul li a.ref{grid-column:2;justify-self:start;margin-top:0}
  ul.curb-list li,ol.projects li{grid-template-columns:minmax(0,1fr) auto}
  ul.curb-list .when{grid-column:1/-1}
  ol.projects li{grid-template-columns:22px minmax(0,1fr)}
  ol.projects li a.ref{grid-column:2;justify-self:start}
  ul.curb-list li a.ref{align-self:start}
  .plate svg{max-height:none}
  .plate-h{flex-direction:column;gap:2px}.plate-h p{text-align:left}
  .lg{padding:4px 8px 4px 6px}.lg .ls{display:none}.lg{grid-template-columns:14px auto}
  svg .sl{font-size:19px}
  svg .gl{font-size:19px}
  svg .avl{font-size:18px;stroke-width:4px}
  svg .lm{font-size:17px}
  svg .scale text,svg .north text{font-size:18px}
  svg .proj rect{transform:scale(1.35)}
  svg .proj text{font-size:15px}
  svg .evt circle{r:13px}
  svg .evt text{font-size:15px}
  .lead{font-size:22px}
  .measures{grid-template-columns:repeat(2,minmax(0,1fr));border-left:0}
  .ms{padding:0 12px 0 0;border-right:0}
  .ms:nth-child(odd){border-right:1px solid var(--rule);margin-right:0}
  .ms:nth-child(even){padding-left:12px}
  .mv{font-size:32px}
  .ledger{grid-template-columns:minmax(0,1fr);padding-top:36px;gap:36px}
  .then-grid,.civic,footer .wrap{grid-template-columns:minmax(0,1fr);gap:24px}
  .then-lead{font-size:20px}
  blockquote p{font-size:17px}
  footer ul{columns:1}
}
"""

JS = r"""
(function(){
  var svg=document.querySelector('#map svg'); if(!svg) return;
  document.querySelectorAll('.lg').forEach(function(b){
    b.addEventListener('click',function(){
      var on=b.getAttribute('aria-pressed')!=='true';
      b.setAttribute('aria-pressed',String(on));
      svg.classList.toggle('hide-'+b.dataset.layer,!on);
    });
  });
  svg.classList.add('hide-req');
  var layerOf={p:'permits',e:'events',c:'curb',h:'then'};
  function mark(id,on){
    svg.querySelectorAll('[data-mk="'+id+'"]').forEach(function(m){m.classList.toggle('hl',on)});
    svg.classList.toggle('dim',on);
  }
  function ensureLayer(id){
    var l=layerOf[id.charAt(0)]; if(!l) return;
    var b=document.querySelector('.lg[data-layer="'+l+'"]');
    if(b && b.getAttribute('aria-pressed')!=='true'){b.click();}
  }
  document.querySelectorAll('[data-ref]').forEach(function(el){
    var id=el.dataset.ref;
    el.addEventListener('mouseenter',function(){mark(id,true)});
    el.addEventListener('mouseleave',function(){mark(id,false)});
    el.addEventListener('focusin',function(){mark(id,true)});
    el.addEventListener('focusout',function(){mark(id,false)});
  });
  var timer;
  document.querySelectorAll('a.ref').forEach(function(a){
    a.addEventListener('click',function(ev){
      var id=a.dataset.go; ensureLayer(id);
      var map=document.getElementById('map');
      var st=getComputedStyle(map).position==='sticky';
      if(st){ev.preventDefault();}
      else{ev.preventDefault();map.scrollIntoView({behavior:'smooth',block:'start'});}
      clearTimeout(timer); mark(id,true);
      timer=setTimeout(function(){mark(id,false)},2600);
    });
  });
  svg.querySelectorAll('.mk').forEach(function(m){
    m.addEventListener('click',function(){
      var id=m.dataset.mk;
      var t=document.querySelector('[data-ref="'+id+'"]'); if(!t) return;
      t.scrollIntoView({behavior:'smooth',block:'center'});
      t.classList.add('on'); setTimeout(function(){t.classList.remove('on')},2200);
    });
  });
})();
"""

window = f'{short_date(p_dates[0])}–{short_date(p_dates[-1])}'
src_list = "".join(f'<li>{esc(v)}</li>' for k, v in sources.items() if k != "license")

PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NAME}: news, events and what's changing</title>
<meta name="description" content="Independent neighborhood site for {NAME}, Washington, DC: local headlines, what's on, and a map of what's changing, updated nightly from public data.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans+Condensed:ital,wght@0,400;0,500;0,600;1,400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#news">Skip to the news</a>
<div class="topline"><div class="wrap"><span><b>{NAME.lower()}.org</b> &nbsp;An independent neighborhood site</span>
<span>Updated nightly from public data <i aria-hidden="true">/</i> as of {gen_label}</span></div></div>
<header class="mast"><div class="wrap">
<h1>{NAME}</h1>
<p class="about">News, what&rsquo;s on, and what&rsquo;s changing, block by block. Northwest Washington, Ward {", ".join(wards)}.
<span class="coords">{centroid_lat:.3f}&deg;N {abs(centroid_lon):.3f}&deg;W</span></p>
</div>
<nav class="sections" aria-label="Sections"><div class="wrap"><ul>
<li><a href="#news">News</a></li><li><a href="#events">Coming up</a></li><li><a href="#map">Map</a></li>
<li><a href="#numbers">Numbers</a></li><li><a href="#homes">Homes</a></li><li><a href="#streets">Streets</a></li>
<li><a href="#then">Then</a></li><li><a href="#civic">Representatives</a></li><li><a href="#email">Weekly email</a></li>
</ul></div></nav>
</header>

<main>
<div class="wrap spread">
<section id="news" aria-labelledby="h-news"><div class="sh"><h2 id="h-news">Latest news</h2><span class="aside">Local outlets</span></div>
{news_html()}</section>

<section id="events" aria-labelledby="h-events"><div class="sh"><h2 id="h-events">Coming up</h2><span class="aside">Next 14 days</span></div>
{events_html()}</section>

<aside id="map" class="plate" aria-labelledby="h-map">
<div class="plate-h"><h2 id="h-map">The map</h2><p>Permits issued {window} <i aria-hidden="true">/</i> this week on the street</p></div>
{legend_html()}
{SVG}
<p class="fine">Streets are drawn from addresses in the data, so positions are good to about a block; squares A&ndash;F, 1&ndash;6 match the references in the lists. Crime is never mapped.</p>
</aside>

<section id="street" aria-labelledby="h-street"><div class="sh"><h2 id="h-street">On the street this week</h2><span class="aside">Curb space reserved</span></div>
{curb_html()}</section>

<section id="projects" aria-labelledby="h-proj"><div class="sh"><h2 id="h-proj">Bigger projects</h2><span class="aside">Last 30 days</span></div>
{projects_html()}</section>
</div>

<div class="wrap">
<section id="numbers" class="band" aria-labelledby="h-num">
<div class="band-grid">
<div><div class="sh" style="border-top:0;padding-top:0"><h2 id="h-num">Today&rsquo;s condition</h2><span class="aside">{gen_label.split(",")[0]}, {short_date(TODAY)}</span></div>
{condition_html()}</div>
<div><div class="sh" style="border-top:0;padding-top:0"><h2>Measures</h2><span class="aside">Latest period vs the one before</span></div>
{measures_html()}</div>
</div>
</section>

<div class="ledger">
<section id="homes" aria-labelledby="h-homes"><div class="sh"><h2 id="h-homes">Homes</h2><span class="aside">Sales, OTR</span></div>{homes_html()}</section>
<section aria-labelledby="h-311"><div class="sh"><h2 id="h-311">Top 311 requests</h2><span class="aside">Last 30 days</span></div>{requests_html()}
<div class="sh" style="margin-top:28px"><h2>Permits by type</h2><span class="aside">{window}</span></div>{permit_types_html()}</section>
<section id="streets" aria-labelledby="h-streets"><div class="sh"><h2 id="h-streets">Street trees</h2><span class="aside">DDOT inventory</span></div>{trees_html()}</section>
</div>

<section id="then" class="then" aria-labelledby="h-then"><div class="sh" style="border-top:0;padding-top:0"><h2 id="h-then">Then</h2><span class="aside">{NAME} in the record</span></div>
{then_html()}</section>

<div class="civic">
<section id="civic" aria-labelledby="h-civic"><div class="sh" style="border-top:0;padding-top:0"><h2 id="h-civic">Representatives</h2></div>{reps_html()}</section>
<section id="email" aria-labelledby="h-email"><div class="sh" style="border-top:0;padding-top:0"><h2 id="h-email">The weekly email</h2></div>
<p class="dek">One email on Friday mornings: the week&rsquo;s headlines, what&rsquo;s on, and what changed on the map. No ads.</p>
<form class="signup" action="/subscribe/" method="get"><label for="em">Email address</label>
<input id="em" name="email" type="email" autocomplete="email" placeholder="you@example.com" required><button type="submit">Sign up</button></form>
<p class="fine">Also on this site: <a href="/jobs/">jobs near {NAME}</a> ({len(D["jobs"]["jobs"])} listed), <a href="/about/">about the data</a>.</p>
</section>
</div>
</div>
</main>

<footer><div class="wrap">
<div><p><strong>{NAME.lower()}.org is independent.</strong> It is not affiliated with the DC Government or any city agency. Built nightly from public records; nothing here is official.</p>
<p>Data licensed {esc(sources.get("license", ""))} where the source allows. Crime appears only as counts, never mapped or graded. 311 locations are shown no finer than the hundred block.</p></div>
<div><p><strong>Sources</strong></p><ul>{src_list}<li>{esc(D["boundary"]["source"])}</li><li>DDOT TOPS occupancy permits; DDOT urban forestry</li><li>OTR Integrated Tax System extract</li><li>Library of Congress, Chronicling America</li></ul></div>
</div></footer>
<script>{JS}</script>
</body>
</html>
"""

(HERE / "index.html").write_text(PAGE, encoding="utf-8")
print("wrote", HERE / "index.html", f"{len(PAGE) / 1024:.0f} KB")
print("streets EW", {k: round(v, 5) for k, v in EW_LAT.items() if v})
print("streets NS", {k: round(v, 5) for k, v in NS_LON.items() if v})
print("aves", list(AVES), "landmarks", [(nm, [round(c) for c in pt]) for nm, pt in LANDMARKS])
print("events", {k: (v["geo"] and grid_ref(*v["geo"]["c"])) for k, v in EV_PLACES.items()})
print("curb", [(c["where"], len(c["geos"])) for c in CURB])
print("fb", FB_GEO and grid_ref(*FB_GEO["c"]))
print("lead", LEAD, tally)
