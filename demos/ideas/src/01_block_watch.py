"""Demo #1: Block Watch for Tenleytown. Writes demos/ideas/01-block-watch.html.

A weekly "what changed" page: building permits, zoning cases, and DDOT
dumpster/crane/staging permits, grouped by week (Monday to Sunday), with a
numbered map per week. 311 appears only as weekly counts.
Never requested: owner/applicant/permittee names, zoning case names, 311 details.
"""

from __future__ import annotations

import html
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402
from run import PERMIT_FIELDS, hundred_block, permit_group, yearly_layers  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "01-block-watch.html"
HPN = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
ROADS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_WebMercator/MapServer/163"
ZONING_TITLE = "Zoning Cases"
OCC_TITLE = "Occupancy Permits (via DDOT TOPs)"
HOOD_KEY, HOOD = "TENLEYTOWN", "Tenleytown"
DAY = 86400
WEEKS = 5  # this week so far + 4 full weeks
ET = -4 * 3600  # display offset; dates only, so DST drift does not matter here
esc = html.escape

NOTABLE_GROUPS = ("New construction", "Demolition", "Additions", "Renovation & repair")
CAT = {  # category -> (label, color)
    "build": ("New construction & additions", "#245c4f"),
    "raze": ("Demolition / raze", "#a2412b"),
    "reno": ("Renovations", "#2f7dd1"),
    "zoning": ("Zoning relief requested", "#7a5bb5"),
    "curb": ("Dumpsters, cranes & street closures", "#c0602a"),
}


def find_layer(title: str) -> str:
    data = dcdata._request(dcdata.SEARCH_API, {"q": title, "limit": 10})
    for f in data.get("features", []):
        p = f.get("properties", {})
        if p.get("title", "").strip().lower() == title.lower() and p.get("url"):
            return p["url"]
    raise RuntimeError(f"layer not found: {title}")


def fetch_geoms(layer, where, fields, envelope):
    rows, offset = [], 0
    while True:
        data = dcdata._request(f"{layer}/query", {
            "where": where, "outFields": ",".join(fields), "returnGeometry": "true", "outSR": 4326,
            "geometry": json.dumps(envelope), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "maxAllowableOffset": 0.00003,
            "resultOffset": offset, "resultRecordCount": 1000, "f": "json"}, post=True)
        batch = data.get("features", [])
        rows += batch
        if not data.get("exceededTransferLimit") or not batch:
            return rows
        offset += len(batch)


class Proj:
    def __init__(self, bbox, width=640, pad=12):
        self.minx, self.miny, self.maxx, self.maxy = bbox
        self.k = math.cos(math.radians((self.miny + self.maxy) / 2))
        self.pad, self.w = pad, width
        self.s = (width - 2 * pad) / ((self.maxx - self.minx) * self.k)
        self.h = round((self.maxy - self.miny) * self.s + 2 * pad)

    def __call__(self, lon, lat):
        return self.pad + (lon - self.minx) * self.k * self.s, self.pad + (self.maxy - lat) * self.s


def path_d(proj, coords, close=False):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (proj(a, b) for a, b in coords)) + ("Z" if close else "")


def fmt_day(epoch: float, fmt="%b %d") -> str:
    s = time.strftime(fmt, time.gmtime(epoch))
    return re.sub(r"\b0(\d)", r"\1", s)


def summarize(work: str, group: str, subtype: str | None) -> str:
    """Rule-based one-liner standing in for the cached LLM summary."""
    w = re.sub(r"(?i)^\s*revision (?:under|to) (?:original )?permit\s*[-#:]?\s*\w*\s*[-:]?\s*", "Revision: ", work or "")
    w = re.sub(r"\s+", " ", w).strip(" .-")
    if not w:
        return (subtype or group).capitalize()
    first = re.split(r"(?<=[.;])\s", w)[0].strip(" \t .")
    if len(first) < 12:
        return (subtype or group).capitalize()
    if len(first) > 150:
        first = first[:147].rsplit(" ", 1)[0] + "…"
    if first.isupper() or sum(c.isupper() for c in first) > 0.6 * sum(c.isalpha() for c in first):
        first = first.lower()
    return first[0].upper() + first[1:]


def nice_addr(a: str) -> str:
    a = re.sub(r"\s+\d{5}$", "", (a or "").replace(", WASHINGTON, DC", "").strip())
    t = a.title()
    t = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), t)
    t = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), t).replace(" Block Of ", " block of ")
    return t if re.search(r"\d", t) else ""


def render(fields: dict) -> str:
    t = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    t = re.sub(r"<!--\s*\n\s*Template for idea demos.*?-->\n", "", t, flags=re.S)
    for k, v in fields.items():
        t = t.replace("{{" + k + "}}", v)
    if "{{" in t:
        raise RuntimeError("unfilled placeholder")
    return t


def main() -> None:
    now = time.time()
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    local = now + ET
    lt = time.gmtime(local)
    monday_local = (local // DAY - lt.tm_wday) * DAY  # 00:00 local on this Monday, as a UTC-epoch-ish day number
    week_starts = [monday_local - k * 7 * DAY for k in range(WEEKS)]  # newest first, local-time epochs
    start_utc = week_starts[-1] - ET

    def week_of(epoch_utc: float) -> int | None:
        loc = epoch_utc + ET
        for i, ws in enumerate(week_starts):
            if loc >= ws:
                return i
        return None

    geom = dcdata.boundary(HPN, f"DC_HPN_NAME='{HOOD_KEY}'")

    # Building permits.
    items: list[dict] = []
    minor = defaultdict(Counter)
    for layer in yearly_layers("Building Permits in {year}", start_utc, now):
        for r in dcdata.query_features(layer, geom, dcdata.date_where("ISSUE_DATE", start_utc), PERMIT_FIELDS, "ISSUE_DATE DESC"):
            wk = week_of(r["ISSUE_DATE"] / 1000)
            if wk is None:
                continue
            work = (r["DESC_OF_WORK"] or "").strip()
            if work.lower() in ("undefined", "null", "none", "n/a"):
                work = ""
            g = permit_group(r["PERMIT_TYPE_NAME"], r["PERMIT_SUBTYPE_NAME"], work)
            if g not in NOTABLE_GROUPS:
                minor[wk][g] += 1
                continue
            cat = {"New construction": "build", "Additions": "build", "Demolition": "raze"}.get(g, "reno")
            items.append({"week": wk, "cat": cat, "when": r["ISSUE_DATE"] / 1000, "addr": nice_addr(r["FULL_ADDRESS"]),
                          "ref": r["PERMIT_ID"], "line": summarize(work, g, r["PERMIT_SUBTYPE_NAME"]),
                          "kind": g, "lat": r["LATITUDE"], "lon": r["LONGITUDE"],
                          "link": "https://dob.dc.gov/page/permit-search"})

    # Zoning cases filed (BZA/ZC). Case names often carry applicant names, so they are not requested.
    zoning_url = find_layer(ZONING_TITLE)
    zrows = dcdata.query_features(zoning_url, geom, dcdata.date_where("DATEFILED", start_utc),
                                  ["CASE_NUMBER", "CASE_TYPE", "CASE_TYPE_RELIEF", "PREMISE_ADDRESS", "DATEFILED", "RELIEFSOUGHT", "CASEPOINT_URL", "URL"])
    zseen = set()
    for r in zrows:
        if r["CASE_NUMBER"] in zseen or not r["DATEFILED"]:
            continue
        zseen.add(r["CASE_NUMBER"])
        wk = week_of(r["DATEFILED"] / 1000)
        if wk is None:
            continue
        relief = (r["CASE_TYPE_RELIEF"] or r["RELIEFSOUGHT"] or "Zoning relief").strip()
        items.append({"week": wk, "cat": "zoning", "when": r["DATEFILED"] / 1000, "addr": nice_addr(r["PREMISE_ADDRESS"] or ""),
                      "ref": f"{r['CASE_TYPE'] or ''} {r['CASE_NUMBER']}".strip(), "line": relief[:150], "kind": "Zoning case",
                      "lat": None, "lon": None, "link": r["CASEPOINT_URL"] or r["URL"] or "https://app.dcoz.dc.gov/"})
    latest_zoning = None
    if not zseen:
        z = dcdata.query_features(zoning_url, geom, "DATEFILED IS NOT NULL", ["CASE_NUMBER", "CASE_TYPE", "DATEFILED"], "DATEFILED DESC")
        if z:
            latest_zoning = max(z, key=lambda r: r["DATEFILED"])

    # DDOT occupancy permits issued in the window: dumpsters, cranes, staging, closures listed; the rest counted.
    occ_url = find_layer(OCC_TITLE)
    orows = dcdata.query_features(occ_url, geom, f"{dcdata.date_where('IssueDate', start_utc)} AND Status IN ('ISSUED','APPROVED')",
                                  ["TrackingNumber", "EventTypeDescription", "IssueDate", "EffectiveDate", "ExpirationDate",
                                   "WorkLocationFullAddress", "IsRoadClosed", "Latitude", "Longitude"])
    oseen, curb_counts = set(), defaultdict(Counter)
    for r in orows:
        key = (r["TrackingNumber"], r["WorkLocationFullAddress"])
        if key in oseen:
            continue
        oseen.add(key)
        wk = week_of(r["IssueDate"] / 1000 - ET)  # TOPS stores DC local time
        if wk is None:
            continue
        ev = r["EventTypeDescription"] or "Other"
        closed = (r["IsRoadClosed"] or "").upper() == "Y"
        if not (closed or any(k in ev for k in ("Roll Off", "Crane", "Staging", "Storage Container"))):
            curb_counts[wk][ev] += 1
            continue
        span = f"{fmt_day(r['EffectiveDate'] / 1000)}–{fmt_day(r['ExpirationDate'] / 1000)}" if r["EffectiveDate"] and r["ExpirationDate"] else ""
        items.append({"week": wk, "cat": "curb", "when": r["IssueDate"] / 1000 - ET,
                      "addr": nice_addr(hundred_block(re.sub(r"\s+", " ", r["WorkLocationFullAddress"] or "")) or ""),
                      "ref": f"TOPS {r['TrackingNumber']}", "line": f"{ev}{' with road closure' if closed else ''}, {span}",
                      "kind": ev, "lat": r["Latitude"], "lon": r["Longitude"], "link": "https://tops.ddot.dc.gov"})

    # 311: weekly counts only (server-side).
    sr_counts: dict[int, Counter] = {}
    for i, ws in enumerate(week_starts):
        a, b = ws - ET, min(ws - ET + 7 * DAY, now)
        c = Counter()
        for layer in yearly_layers("311 City Service Requests in {year}", a, b):
            c.update(dcdata.count_by(layer, geom, dcdata.date_where("ADDDATE", a, b), "SERVICECODEDESCRIPTION"))
        sr_counts[i] = c

    # ---- Map pieces ----
    xs = [p[0] for ring in geom["rings"] for p in ring]
    ys = [p[1] for ring in geom["rings"] for p in ring]
    bbox = (min(xs) - 0.001, min(ys) - 0.001, max(xs) + 0.001, max(ys) + 0.001)
    proj = Proj(bbox, width=560)
    roads = fetch_geoms(ROADS, "1=1", ["DCFUNCTIONALCLASS"],
                        {"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3], "spatialReference": {"wkid": 4326}})
    minor_d = " ".join(path_d(proj, p) for f in roads if f["attributes"].get("DCFUNCTIONALCLASS") not in (11, 12, 14, 16) for p in f["geometry"]["paths"])
    major_d = " ".join(path_d(proj, p) for f in roads if f["attributes"].get("DCFUNCTIONALCLASS") in (11, 12, 14, 16) for p in f["geometry"]["paths"])
    base = (f'<path d="{minor_d}" class="r1"/><path d="{major_d}" class="r2"/>'
            + "".join(f'<path d="{path_d(proj, ring, True)}" class="hood"/>' for ring in geom["rings"]))

    order = ["build", "raze", "zoning", "curb", "reno"]
    weeks_html, tabs = [], []
    totals = []
    for i, ws in enumerate(week_starts):
        wk_items = sorted([it for it in items if it["week"] == i], key=lambda it: (order.index(it["cat"]), -it["when"]))
        totals.append(len(wk_items))
        label_range = f"{fmt_day(ws)} – {fmt_day(ws + 6 * DAY)}"
        tab_label = "This week" if i == 0 else ("Last week" if i == 1 else f"Week of {fmt_day(ws)}")
        tabs.append(f'<button type="button" role="tab" class="tab" aria-selected="{"true" if i == 0 else "false"}" data-w="{i}">{tab_label}<span>{len(wk_items)}</span></button>')
        pins, lists, n = [], [], 0
        for cat in order:
            cat_items = [it for it in wk_items if it["cat"] == cat]
            if not cat_items:
                continue
            lis = []
            for it in cat_items:
                n += 1
                it["n"] = n
                if it["lat"] and it["lon"]:
                    x, y = proj(it["lon"], it["lat"])
                    if 0 <= x <= proj.w and 0 <= y <= proj.h:
                        pins.append(f'<g class="pin"><circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{CAT[cat][1]}"/>'
                                    f'<text x="{x:.1f}" y="{y + 3.5:.1f}" text-anchor="middle">{n}</text><title>{esc(it["addr"])}</title></g>')
                lis.append(f'<li><span class="num" style="background:{CAT[cat][1]}">{n}</span><div><b>{esc(it["addr"]) or "Address not listed"}</b> '
                           f'<span class="muted">· {fmt_day(it["when"], "%a %b %d")}</span><br>{esc(it["line"])}<br>'
                           f'<a class="ref" href="{esc(it["link"])}">{esc(it["ref"])}</a></div></li>')
            lists.append(f'<h3><i class="sw" style="background:{CAT[cat][1]}"></i>{CAT[cat][0]} <span class="muted">({len(cat_items)})</span></h3><ul class="feed">{"".join(lis)}</ul>')
        if not lists:
            lists.append('<p class="muted">No new construction, demolition, zoning or curb permits this week.</p>')
        # Also-this-week roll-up of the small stuff.
        bits = []
        m = minor.get(i, Counter())
        if m:
            bits.append(", ".join(f"{v} {k.lower()}" for k, v in m.most_common()) + " permits")
        cc = curb_counts.get(i, Counter())
        if cc:
            bits.append(", ".join(f"{v} {k.lower()}" for k, v in cc.most_common(4)) + " (DDOT)")
        sc = sr_counts.get(i, Counter())
        if sc:
            top = ", ".join(f"{k.lower()} ({v})" for k, v in sc.most_common(3))
            bits.append(f"{sum(sc.values())} 311 requests, mostly {top}")
        also = f'<p class="also"><b>Also this week:</b> {esc("; ".join(bits))}.</p>' if bits else ""
        delta = ""
        if i + 1 < WEEKS:
            prev = len([it for it in items if it["week"] == i + 1])
            diff = len(wk_items) - prev
            delta = f' · <span class="{"up" if diff > 0 else "down" if diff < 0 else "muted"}">{"+" if diff > 0 else ""}{diff} vs. week before</span>' if diff else " · same as week before"
        status = " (so far)" if i == 0 else ""
        svg = (f'<svg viewBox="0 0 {proj.w} {proj.h}" class="map" role="img" aria-label="Map of items for the week of {fmt_day(ws)}">{base}{"".join(pins)}</svg>')
        weeks_html.append(
            f'<section class="week card" data-w="{i}"{"" if i == 0 else " hidden"}>'
            f'<p class="eyebrow">{esc(HOOD)} · {label_range}{status}</p>'
            f'<h2>{len(wk_items)} things changed{delta}</h2>'
            f'<div class="wk"><div class="wk-map">{svg}</div><div class="wk-list">{"".join(lists)}</div></div>{also}</section>'
        )

    # Spark bar of items per week (oldest -> newest).
    mx = max(totals + [1])
    bars = "".join(
        f'<rect x="{8 + k * 34}" y="{44 - 36 * v / mx:.1f}" width="24" height="{36 * v / mx:.1f}" rx="2" fill="{"var(--accent)" if k == WEEKS - 1 else "var(--line)"}"><title>{v}</title></rect>'
        f'<text x="{20 + k * 34}" y="58" text-anchor="middle">{v}</text>'
        for k, v in enumerate(reversed(totals))
    )
    zoning_note = ""
    if latest_zoning:
        zoning_note = (f'<p class="muted small">No zoning cases were filed in {esc(HOOD)} in these {WEEKS} weeks. The most recent was '
                       f'{esc(latest_zoning["CASE_TYPE"] or "")} case {esc(latest_zoning["CASE_NUMBER"])}, filed {fmt_day(latest_zoning["DATEFILED"] / 1000, "%b %d, %Y")}.</p>')

    legend = "".join(f'<span class="lg"><i class="sw" style="background:{c}"></i>{esc(lbl)}</span>' for lbl, c in CAT.values())
    body = f"""
<section class="card hero">
  <div class="tabs" role="tablist" aria-label="Choose a week">{''.join(tabs)}</div>
  <div class="trend"><svg viewBox="0 0 {8 + WEEKS * 34} 62" width="{8 + WEEKS * 34}" height="62" role="img" aria-label="Items per week, oldest to newest">{bars}</svg>
  <p class="small muted">Items per week, oldest to newest. Counts include new construction, additions, demolitions, renovations, zoning filings and dumpster/crane/staging/closure permits.</p></div>
  <div class="legend">{legend}</div>
</section>
{''.join(weeks_html)}
{zoning_note}
<section class="card sponsor">
  <span class="label">Every Monday</span>
  <p style="margin:.2rem 0 .5rem">Get last week's changes in your inbox. One email a week, nothing else.</p>
  <form class="sub" onsubmit="event.preventDefault();this.querySelector('output').textContent='Demo only: nothing was sent or stored.'">
    <label class="vh" for="em">Email</label><input id="em" type="email" placeholder="you@example.com" autocomplete="off"><button type="submit">Subscribe</button><output class="muted small"></output>
  </form>
  <p class="label" style="margin:.8rem 0 0">This week's issue presented by [Sponsor name], a local business</p>
</section>
<script>
(function(){{var tabs=document.querySelectorAll('.tab');tabs.forEach(function(t){{t.addEventListener('click',function(){{
tabs.forEach(function(o){{o.setAttribute('aria-selected',o===t)}});
document.querySelectorAll('.week').forEach(function(s){{s.hidden=s.dataset.w!==t.dataset.w}});}});}});}})();
</script>
"""

    extra_css = """
.small{font-size:.86rem}
.tabs{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px}
.tab{font:inherit;font-size:.85rem;white-space:nowrap;padding:5px 12px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.tab span{display:inline-block;margin-left:6px;font-weight:700;color:var(--muted)}
.tab[aria-selected=true]{background:var(--accent);color:var(--card);border-color:var(--accent)}
.tab[aria-selected=true] span{color:var(--card)}
.trend{display:flex;gap:12px;align-items:center;margin-top:10px}
.trend p{margin:0}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:.8rem}
.lg{display:inline-flex;align-items:center;gap:5px}
.sw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;flex:none}
.wk{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);gap:16px;align-items:start}
@media (max-width:640px){.wk{grid-template-columns:1fr}}
.wk-map{position:sticky;top:8px}
.map{width:100%;height:auto;background:var(--soft);border-radius:8px;display:block}
.r1{fill:none;stroke:var(--line);stroke-width:1.1}.r2{fill:none;stroke:var(--muted);stroke-width:2;opacity:.5}
.hood{fill:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:6 4}
.pin text{fill:#fff;font-size:9.5px;font-weight:700}
h3{font-size:.92rem;margin:.6rem 0 .2rem;display:flex;align-items:center}
ul.feed{list-style:none;margin:0;padding:0}
ul.feed li{display:flex;gap:10px;padding:.5rem 0;border-bottom:1px solid var(--line);font-size:.92rem;overflow-wrap:anywhere}
.num{flex:none;width:22px;height:22px;border-radius:50%;color:#fff;font-size:.72rem;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:2px}
.ref{font-size:.78rem}
.also{font-size:.88rem;color:var(--muted);border-top:1px solid var(--line);padding-top:.6rem;margin-bottom:0}
.sub{display:flex;flex-wrap:wrap;gap:8px}
.sub input{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);flex:1;min-width:0}
.sub button{font:inherit;padding:6px 14px;border-radius:6px;border:0;background:var(--accent);color:var(--card);cursor:pointer}
.sub output{flex-basis:100%}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
"""
    fields = {
        "IDEA_ID": "civic-data#1",
        "RANK": "1",
        "SCORE": "79.4",
        "SHORT_NAME": "Block Watch",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": f"{HOOD} &amp; Friendship Heights · Block Watch",
        "HEADLINE": f"What's changing in {HOOD} this week",
        "DECK": (f"New construction, demolitions, renovations, zoning filings and dumpster or crane permits, week by week. "
                 f"{sum(totals)} items over the last {WEEKS} weeks. Pick a week to see it on the map."),
        "BODY": body,
        "EXTRA_CSS": extra_css,
        "PITCH": "An automatic weekly page (plus a Monday email) listing every notable permit, zoning case and street-occupancy permit inside the neighborhood, in plain English, so neighbors know what's going on at that house before they have to ask.",
        "WHATS_REAL": (f"All items were pulled from Open Data DC on {pulled}: Building Permits (DOB yearly layer), Zoning Cases, DDOT TOPS Occupancy Permits, "
                       "and 311 City Service Requests (server-side counts only), clipped to the DC Health planning area for Tenleytown (which includes Friendship Heights). "
                       "Weeks run Monday to Sunday, Eastern time. Electrical, plumbing, minor and home-business permits are rolled up into the 'Also this week' line. "
                       "This differs from the existing digest demo, which is a 30-day summary: this page is a running weekly log with one map per week."),
        "WHATS_MOCKED": ("The one-line summaries are a rule-based cleanup of DOB's work description, standing in for the cached LLM summaries the idea proposes. "
                         "Liquor-license actions are left out: the ABCA layer on Open Data DC is a periodic snapshot of current licenses, and placard notices are PDFs that are not parsed yet. "
                         "The subscribe form and the sponsor line are mockups. Owner and applicant names, zoning case names and 311 details are never requested. "
                         "DDOT permit locations are shown to the hundred block."),
        "NEXT_STEPS": ("Store each night's items keyed by permit or case number so weeks freeze once they end, add per-street archive pages, "
                       "parse ABCA placard PDFs, cache an LLM summary per permit, and send the Monday email through Buttondown or Cloudflare Email."),
        "SOURCES": ('<a href="https://opendata.dc.gov/">Open Data DC</a>: Building Permits (DOB), Zoning Cases (DCOZ), DDOT TOPS Occupancy Permits, '
                    '311 City Service Requests (counts), Roadway Block, DC Health planning areas; CC BY 4.0'),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
    }
    OUT.write_text(render(fields), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: per-week items {totals}, zoning {len(zseen)}, occ rows {len(oseen)}")


if __name__ == "__main__":
    main()
