"""Demo #10: Address Watch. Writes demos/ideas/10-address-watch.html.

A sample subscriber watches a 500 ft radius around a street intersection
(Wisconsin Ave & Albemarle St NW, Tenleytown). Events inside the radius over the
last 30 days are live from Open Data DC. Crime appears only as server-side
counts by offense. 311 locations are coarsened to the hundred block.
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

OUT = ROOT / "demos" / "ideas" / "10-address-watch.html"
INTERSECTIONS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Location_WebMercator/FeatureServer/2"
ROADS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_WebMercator/MapServer/163"
STREET_1, STREET_2 = "WISCONSIN", "ALBEMARLE"
RADIUS_FT = 500
RADIUS_M = RADIUS_FT * 0.3048
DAYS = 30
DAY = 86400
FEED_CAP = 50
esc = html.escape

KINDS = {  # kind -> (label, color)
    "permit": ("Building permit", "#245c4f"),
    "curb": ("Street & curb permit", "#c0602a"),
    "311": ("311 request", "#2f7dd1"),
}


def find_layer(title: str) -> str:
    data = dcdata._request(dcdata.SEARCH_API, {"q": title, "limit": 10})
    for f in data.get("features", []):
        p = f.get("properties", {})
        if p.get("title", "").strip().lower() == title.lower() and p.get("url"):
            return p["url"]
    raise RuntimeError(f"layer not found: {title}")


def circle(lon: float, lat: float, meters: float, n: int = 72) -> dict:
    dlat = meters / 111320
    dlon = dlat / math.cos(math.radians(lat))
    ring = [[lon + dlon * math.cos(2 * math.pi * i / n), lat + dlat * math.sin(2 * math.pi * i / n)] for i in range(n)]
    ring.append(ring[0])
    return {"rings": [ring], "spatialReference": {"wkid": 4326}}


class Proj:
    def __init__(self, bbox, width=560, pad=8):
        self.minx, self.miny, self.maxx, self.maxy = bbox
        self.k = math.cos(math.radians((self.miny + self.maxy) / 2))
        self.pad, self.w = pad, width
        self.s = (width - 2 * pad) / ((self.maxx - self.minx) * self.k)
        self.h = round((self.maxy - self.miny) * self.s + 2 * pad)

    def __call__(self, lon, lat):
        return self.pad + (lon - self.minx) * self.k * self.s, self.pad + (self.maxy - lat) * self.s


def path_d(proj, coords):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (proj(a, b) for a, b in coords))


def tc(s: str) -> str:
    t = re.sub(r"\s+\d{5}$", "", (s or "").replace(", WASHINGTON, DC", "").strip()).title()
    t = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), t)
    return re.sub(r"(?<=\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1).lower(), t).replace(" Block Of ", " block of ")


def day_label(epoch: float) -> str:
    return re.sub(r"\b0(\d)", r"\1", time.strftime("%a, %b %d", time.gmtime(epoch)))


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
    start = now - DAYS * DAY
    et = -4 * 3600

    pt = dcdata._request(f"{INTERSECTIONS}/query", {"where": f"STREET_1_NAME='{STREET_1}' AND STREET_2_NAME='{STREET_2}'",
                                                    "outFields": "NAME,LATITUDE,LONGITUDE", "returnGeometry": "false", "f": "json"})["features"][0]["attributes"]
    lon, lat = pt["LONGITUDE"], pt["LATITUDE"]
    point_name = tc(pt["NAME"]).replace(" And ", " & ")
    geom = circle(lon, lat, RADIUS_M)

    events: list[dict] = []
    # Building permits.
    for layer in yearly_layers("Building Permits in {year}", start, now):
        for r in dcdata.query_features(layer, geom, dcdata.date_where("ISSUE_DATE", start), PERMIT_FIELDS, "ISSUE_DATE DESC"):
            work = (r["DESC_OF_WORK"] or "").strip()
            if work.lower() in ("undefined", "null", "none", "n/a"):
                work = ""
            g = permit_group(r["PERMIT_TYPE_NAME"], r["PERMIT_SUBTYPE_NAME"], work)
            line = re.split(r"(?<=[.;])\s", re.sub(r"\s+", " ", work))[0][:140] if len(work) > 10 else (r["PERMIT_SUBTYPE_NAME"] or g).capitalize()
            if len(line.strip()) < 4:
                line = ""
            events.append({"kind": "permit", "when": r["ISSUE_DATE"] / 1000, "where": tc(r["FULL_ADDRESS"]), "title": g,
                           "line": line, "ref": r["PERMIT_ID"], "lat": r["LATITUDE"], "lon": r["LONGITUDE"]})
    # DDOT occupancy permits issued (TOPS stores DC local time).
    occ_url = find_layer("Occupancy Permits (via DDOT TOPs)")
    seen = set()
    for r in dcdata.query_features(occ_url, geom, f"{dcdata.date_where('IssueDate', start + et)} AND Status IN ('ISSUED','APPROVED')",
                                   ["TrackingNumber", "EventTypeDescription", "IssueDate", "EffectiveDate", "ExpirationDate", "WorkLocationFullAddress", "Latitude", "Longitude"]):
        key = (r["TrackingNumber"], r["WorkLocationFullAddress"])
        if key in seen:
            continue
        seen.add(key)
        span = ""
        if r["EffectiveDate"] and r["ExpirationDate"]:
            span = f"{day_label(r['EffectiveDate'] / 1000)[5:]} – {day_label(r['ExpirationDate'] / 1000)[5:]}"
        events.append({"kind": "curb", "when": r["IssueDate"] / 1000 - et, "where": tc(hundred_block(re.sub(r"\s+", " ", r["WorkLocationFullAddress"] or ""))),
                       "title": r["EventTypeDescription"] or "Public space permit", "line": f"Reserved {span}" if span else "", "ref": f"TOPS {r['TrackingNumber']}",
                       "lat": r["Latitude"], "lon": r["Longitude"]})
    # 311 (type, date, hundred block only).
    for layer in yearly_layers("311 City Service Requests in {year}", start, now):
        for r in dcdata.query_features(layer, geom, dcdata.date_where("ADDDATE", start),
                                       ["SERVICECODEDESCRIPTION", "ADDDATE", "SERVICEORDERSTATUS", "STREETADDRESS"]):
            events.append({"kind": "311", "when": r["ADDDATE"] / 1000, "where": tc(hundred_block(r["STREETADDRESS"]) or "Near the intersection"),
                           "title": r["SERVICECODEDESCRIPTION"] or "Request", "line": f"Status: {r['SERVICEORDERSTATUS'] or 'unknown'}", "ref": "",
                           "lat": None, "lon": None})
    # Crime: counts only (opt-in alert type).
    crime = Counter()
    for layer in yearly_layers("Crime Incidents in {year}", start, now):
        crime.update(dcdata.count_by(layer, geom, dcdata.date_where("REPORT_DAT", start), "OFFENSE"))
    # Context: active ABC licensees inside the radius.
    lic_url = find_layer("Alcohol License Business Locations")
    lic = dcdata.query_features(lic_url, geom, "STATUS='ACTIVE'", ["TRADE_NAME", "TYPE"])

    events.sort(key=lambda e: -e["when"])
    by_kind = Counter(e["kind"] for e in events)

    # ---- Map ----
    pad_m = RADIUS_M * 1.35
    dlat = pad_m / 111320
    dlon = dlat / math.cos(math.radians(lat)) * 1.25
    bbox = (lon - dlon, lat - dlat, lon + dlon, lat + dlat)
    proj = Proj(bbox)
    env = {"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3], "spatialReference": {"wkid": 4326}}
    roads = dcdata._request(f"{ROADS}/query", {"where": "1=1", "outFields": "STREETNAME,STREETTYPE,DCFUNCTIONALCLASS,LENGTH", "returnGeometry": "true", "outSR": 4326,
                                               "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                                               "spatialRel": "esriSpatialRelIntersects", "f": "json"}, post=True)["features"]
    rp, labels, done = [], [], set()
    for f in sorted(roads, key=lambda f: -(f["attributes"].get("LENGTH") or 0)):
        major = f["attributes"].get("DCFUNCTIONALCLASS") in (11, 12, 14, 16)
        for p in f["geometry"]["paths"]:
            rp.append(f'<path d="{path_d(proj, p)}" class="{"rM" if major else "rm"}"/>')
        nm = tc(f"{f['attributes'].get('STREETNAME') or ''} {f['attributes'].get('STREETTYPE') or ''}")
        p = f["geometry"]["paths"][0]
        x, y = proj(*p[len(p) // 2])
        if nm and nm not in done and 40 < x < proj.w - 40 and 14 < y < proj.h - 8:
            done.add(nm)
            (x1, y1), (x2, y2) = proj(*p[0]), proj(*p[-1])
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
            ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
            labels.append(f'<text x="{x:.0f}" y="{y:.0f}" dy="-5" text-anchor="middle" transform="rotate({ang:.0f} {x:.0f} {y:.0f})" class="lbl">{esc(nm)}</text>')
    cx, cy = proj(lon, lat)
    r_px = RADIUS_M / 111320 * proj.s
    marks = []
    for e in events:
        if e["lat"] and e["lon"]:
            x, y = proj(e["lon"], e["lat"])
            marks.append(f'<circle data-k="{e["kind"]}" cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{KINDS[e["kind"]][1]}" stroke="var(--card)" stroke-width="1.2"><title>{esc(e["title"])} · {esc(e["where"])}</title></circle>')
    svg = (f'<svg viewBox="0 0 {proj.w} {proj.h}" class="map" role="img" aria-label="{RADIUS_FT} ft radius around {esc(point_name)}">'
           f'<defs><clipPath id="clip"><rect width="{proj.w}" height="{proj.h}" rx="8"/></clipPath></defs><g clip-path="url(#clip)">'
           f'{"".join(rp)}<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_px:.1f}" class="rad"/>{"".join(labels)}{"".join(marks)}'
           f'<path d="M{cx:.1f},{cy:.1f} l-7,-14 a8,8 0 1,1 14,0 z" class="pin"/><circle cx="{cx:.1f}" cy="{cy - 17:.1f}" r="3" fill="var(--card)"/>'
           f'<text x="{cx + r_px * .72:.0f}" y="{cy + r_px * .72 + 12:.0f}" class="rlbl">{RADIUS_FT} ft</text></g></svg>')

    # ---- Feed grouped by day, as the subscriber's inbox would show it ----
    feed_days = defaultdict(list)
    for e in events[:FEED_CAP]:
        feed_days[day_label(e["when"] + et)].append(e)
    feed_html = "".join(
        f'<h3>{esc(d)}</h3><ul class="feed">' + "".join(
            f'<li data-k="{e["kind"]}"><i style="background:{KINDS[e["kind"]][1]}"></i><div><b>{esc(e["title"])}</b> <span class="muted">· {esc(e["where"])}</span>'
            f'{"<br>" + esc(e["line"]) if e["line"] else ""}{" <span class=ref>" + esc(e["ref"]) + "</span>" if e["ref"] else ""}</div></li>' for e in es) + "</ul>"
        for d, es in feed_days.items())
    cap_note = f"Showing the newest {FEED_CAP} of {len(events)} alerts." if len(events) > FEED_CAP else f"All {len(events)} alerts."
    weeks = Counter(int((now - e["when"]) // (7 * DAY)) for e in events)
    week_rows = "".join(
        f"<tr><td>{'This week' if w == 0 else f'{w} week{'s' if w > 1 else ''} ago'}</td><td class='n'>{weeks.get(w, 0)}</td></tr>" for w in range(0, 5) if w * 7 < DAYS)
    chips = "".join(
        f'<button type="button" class="chip" aria-pressed="true" data-k="{k}"><i style="background:{c}"></i>{lbl} <b>{by_kind.get(k, 0)}</b></button>'
        for k, (lbl, c) in KINDS.items())
    crime_rows = "".join(f"<tr><td>{esc(o.title())}</td><td class='n'>{n}</td></tr>" for o, n in crime.most_common())
    lic_li = ", ".join(f"{esc(l['TRADE_NAME'] or '')} ({esc((l['TYPE'] or '').lower())})" for l in sorted(lic, key=lambda l: l["TRADE_NAME"] or "")) or "none"

    body = f"""
<section class="card sub-card">
  <div class="sub-head"><span class="badge sample" data-sample>Sample subscriber</span><span class="muted small">Not a real person; the point is a public intersection.</span></div>
  <div class="sub-grid">
    <div><span class="k">Watching</span><b>{esc(point_name)}</b></div>
    <div><span class="k">Radius</span><b>{RADIUS_FT} ft</b></div>
    <div><span class="k">Delivery</span><b>Daily email, 7 am</b></div>
    <div><span class="k">Alert types</span><b>Permits, curb, 311</b> <span class="muted small">(crime off)</span></div>
  </div>
</section>

<div class="grid">
  <div class="card stat"><b>{len(events)}</b>alerts in the last {DAYS} days</div>
  <div class="card stat"><b>{by_kind.get('permit', 0)}</b>building permits</div>
  <div class="card stat"><b>{by_kind.get('curb', 0)}</b>street &amp; curb permits</div>
  <div class="card stat"><b>{by_kind.get('311', 0)}</b>311 requests</div>
</div>

<section class="card">
  <h2>Inside your {RADIUS_FT} ft circle</h2>
  <div class="chips" role="group" aria-label="Filter alert types">{chips}</div>
  {svg}
  <p class="muted small">Building and curb permits are placed at DC's permit coordinates. 311 requests are listed by hundred block and not mapped.</p>
</section>

<div class="two">
<section class="card">
  <h2>Your alerts</h2>
  <p class="muted small">{cap_note} Each day's items would arrive in one email.</p>
  {feed_html}
</section>
<div>
<section class="card">
  <h2>Weekly roll-up</h2>
  <div class="scroll"><table><thead><tr><th>Week</th><th class="n">Alerts</th></tr></thead><tbody>{week_rows}</tbody></table></div>
</section>
<section class="card">
  <h2>Crime reports <span class="muted small">(opt-in)</span></h2>
  <p class="muted small" style="margin-top:0">Off by default. When turned on, subscribers get counts by offense, never individual incidents. Last {DAYS} days in this circle:</p>
  <div class="scroll"><table><thead><tr><th>Offense</th><th class="n">Reports</th></tr></thead><tbody>{crime_rows or "<tr><td colspan=2>None reported</td></tr>"}</tbody></table></div>
</section>
<section class="card">
  <h2>Also inside the circle</h2>
  <p class="small" style="margin-top:0">Licensed to sell alcohol: {lic_li}. You'd get an alert when ABCA posts a new application or renewal protest here.</p>
</section>
</div>
</div>

<section class="card">
  <h2>Plans</h2>
  <div class="tiers">
    <div class="tier"><h3>Block</h3><p class="price">Free</p><ul><li>1 address</li><li>300 ft radius</li><li>Weekly email</li><li>Permits, curb and 311</li></ul></div>
    <div class="tier hot"><h3>Neighbor</h3><p class="price">$4<span>/month</span></p><ul><li>Up to 3 addresses</li><li>Up to 1,000 ft</li><li>Daily or instant</li><li>Adds ABCA notices and opt-in crime counts</li></ul></div>
    <div class="tier"><h3>Pro</h3><p class="price">$29<span>/month</span></p><ul><li>Up to 25 properties</li><li>Up to ½ mile</li><li>CSV export and webhook</li><li>For landlords, condo boards and property managers</li></ul></div>
  </div>
  <p class="muted small">Proposed prices for the demo. Your address is never shown to anyone, and there is no public map of who watches what.</p>
</section>
<script>
(function(){{document.querySelectorAll('.chip').forEach(function(c){{c.addEventListener('click',function(){{
var on=c.getAttribute('aria-pressed')!=='true';c.setAttribute('aria-pressed',on);
document.querySelectorAll('li[data-k="'+c.dataset.k+'"],.map circle[data-k="'+c.dataset.k+'"]').forEach(function(el){{el.style.display=on?'':'none'}});}});}});}})();
</script>
"""
    extra_css = """
.small{font-size:.86rem}
.sub-card{border-color:var(--sample)}
.sub-head{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin-bottom:10px}
.sub-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.sub-grid .k{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.map{width:100%;height:auto;display:block;background:var(--soft);border-radius:8px;margin-top:8px}
.rm{fill:none;stroke:var(--line);stroke-width:6;stroke-linecap:round}.rM{fill:none;stroke:var(--line);stroke-width:11;stroke-linecap:round}
.rad{fill:var(--accent);fill-opacity:.07;stroke:var(--accent);stroke-width:2;stroke-dasharray:6 4}
.pin{fill:var(--brick);stroke:var(--card);stroke-width:1.5}
svg text.lbl{font-size:10px;fill:var(--ink);paint-order:stroke;stroke:var(--soft);stroke-width:3px}
svg text.rlbl{font-size:11px;fill:var(--accent);font-weight:700}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:inherit;font-size:.8rem;display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.chip i{display:inline-block;width:10px;height:10px;border-radius:50%}
.chip[aria-pressed=false]{opacity:.45;text-decoration:line-through}
.two{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:0 14px;align-items:start}
@media (max-width:700px){.two{grid-template-columns:1fr}}
h3{font-size:.85rem;margin:.9rem 0 .2rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
ul.feed{list-style:none;margin:0;padding:0}
ul.feed li{display:flex;gap:10px;padding:.4rem 0;border-bottom:1px solid var(--line);font-size:.9rem;overflow-wrap:anywhere}
ul.feed li>i{flex:none;width:10px;height:10px;border-radius:50%;margin-top:.45rem}
.ref{font-size:.75rem;color:var(--muted)}
.tiers{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.tier{border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.tier.hot{border:2px solid var(--accent)}
.tier h3{margin:0;color:var(--ink)}
.price{font-size:1.6rem;font-weight:700;margin:.2rem 0}.price span{font-size:.85rem;color:var(--muted);font-weight:400}
.tier ul{margin:0;padding-left:1.1rem;font-size:.88rem}
"""
    fields = {
        "IDEA_ID": "monetization#8",
        "RANK": "10",
        "SCORE": "72.7",
        "SHORT_NAME": "Address Watch",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "Address Watch · Tenleytown",
        "HEADLINE": f"What happened within {RADIUS_FT} ft this month",
        "DECK": f"Everything DC recorded in a {RADIUS_FT} ft circle around {esc(point_name)} over the last {DAYS} days, the way a subscriber's daily alerts would show it.",
        "BODY": body,
        "EXTRA_CSS": extra_css,
        "PITCH": "Enter your address and get an email the day a permit, curb reservation, 311 request or (opt-in) crime report appears within a chosen radius. One block is free; a few dollars a month covers more addresses, wider radii and instant delivery.",
        "WHATS_REAL": (f"Every alert was pulled from Open Data DC on {pulled} with a {RADIUS_FT} ft circle around DC's Intersection Points record for {esc(point_name)}: "
                       "Building Permits (DOB), DDOT TOPS Occupancy Permits, 311 City Service Requests (type, date, status and hundred block only), "
                       "Crime Incidents (server-side counts by offense, never incidents) and ABCA licensee locations (a periodic snapshot). Street lines are DDOT's Roadway Block layer."),
        "WHATS_MOCKED": ("The subscriber is a <b>sample</b>: a made-up account watching a public intersection, not anyone's home. The delivery settings, plan names and prices are proposals. "
                         "No ABCA notices are shown because placard PDFs are not parsed yet. Owner and applicant names, 311 details and individual crime incidents are never requested."),
        "NEXT_STEPS": ("Store watched points (encrypted) in Cloudflare D1, run each night's new records through a point-in-radius check, "
                       "send digests with Cloudflare Email Workers, take payments with Stripe, and add ABCA placard parsing."),
        "SOURCES": ('<a href="https://opendata.dc.gov/">Open Data DC</a>: Intersection Points, Building Permits (DOB), DDOT TOPS Occupancy Permits, 311 City Service Requests (OUC), '
                    'Crime Incidents (MPD, counts only), Alcohol License Business Locations (ABCA), Roadway Block; CC BY 4.0'),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
    }
    OUT.write_text(render(fields), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {dict(by_kind)}, crime {sum(crime.values())}, licensees {len(lic)}")


if __name__ == "__main__":
    main()
