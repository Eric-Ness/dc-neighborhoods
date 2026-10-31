"""Demo #09: Building Report Cards for Renters (idea monetization#5).

One large Petworth apartment building, shown as raw public records with no grade:
- Address Points (OCTO/MAR): unit count and location.
- Integrated Tax System Public Extract (OTR): property type, land area, assessment (owner fields never requested).
- 311 City Service Requests, yearly layers since 2019: requests logged at the building's address.
  Rows carry type, agency, dates and status only; no free-text details, no unit numbers, and a short
  list of person-related request types is withheld entirely.
- Building Permits (DOB), yearly layers since 2016, at the address.
- Crime Incidents (MPD): server-side counts by offense within ~150 m, last 12 months (no incidents).
- Metro station locations, for straight-line distance.

Run from the repo root: python demos/ideas/src/09_building_report_card.py
"""

from __future__ import annotations

import datetime
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propkit_shared as k  # noqa: E402

RANK, IDEA_ID, SCORE = 9, "monetization#5", "72.7"
OUT = k.ROOT / "demos" / "ideas" / "09-building-report-card.html"
MAR_ADDRESS = "3800 NEW HAMPSHIRE AVENUE NW"
PERMIT_PREFIX = "3800 NEW HAMPSHIRE AVE NW"
SR_FIRST_YEAR, PERMIT_FIRST_YEAR = 2019, 2016
METRO_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_Rail_Bus_WebMercator/MapServer/51"
WITHHELD = ("HOMELESS", "DRIVERS LICENSE", "ID ISSUES", "PROTECTIVE", "CHILD", "SENIOR", "WELFARE", "MENTAL", "DECEASED", "OVERDOSE")
HOUSING_WORDS = ("HOUSING", "RODENT", "INSECT", "BED BUG", "MOLD", "HEAT", "PROPERTY MAINT", "VACANT", "BUILDING", "INSPECTION")
CAP = 50


def meters(lat1, lon1, lat2, lon2) -> float:
    kx = math.cos(math.radians((lat1 + lat2) / 2)) * 111_320
    return math.hypot((lat1 - lat2) * 111_320, (lon1 - lon2) * kx)


def main() -> None:
    now = time.time()
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    this_year = time.gmtime(now).tm_year

    ap = k.resolve("Address Points")
    pt = k.query(ap, f"ADDRESS='{MAR_ADDRESS}'", ["ADDRESS", "SSL", "LATITUDE", "LONGITUDE", "HOUSING_UNIT_COUNT", "WARD", "ANC", "SMD"])
    if len(pt) != 1:
        raise RuntimeError(f"address lookup returned {len(pt)} rows")
    pt = pt[0]
    lat, lon = pt["LATITUDE"], pt["LONGITUDE"]

    itspe = k.resolve(k.ITSPE_TITLE)
    tax = k.query(itspe, f"SSL='{pt['SSL']}'", ["SSL", "PROPTYPE", "USECODE", "LANDAREA", "NEWTOTAL", "NBHDNAME", "CLASSTYPE"])
    tax = tax[0] if tax else {}

    # 311 at the address.
    sr_rows = []
    for y in range(SR_FIRST_YEAR, this_year + 1):
        layer = k.dcdata.resolve_yearly_layer("311 City Service Requests in {year}", y)
        if layer:
            sr_rows += k.query(layer, f"STREETADDRESS LIKE '{MAR_ADDRESS}%'",
                               ["SERVICEREQUESTID", "SERVICECODEDESCRIPTION", "ORGANIZATIONACRONYM", "ADDDATE", "RESOLUTIONDATE", "SERVICEORDERSTATUS"])
    seen = set()
    sr = []
    withheld = 0
    for r in sr_rows:
        if r["SERVICEREQUESTID"] in seen:
            continue
        seen.add(r["SERVICEREQUESTID"])
        t = (r["SERVICECODEDESCRIPTION"] or "Other").strip()
        if any(w in t.upper() for w in WITHHELD):
            withheld += 1
            continue
        days = None
        if r["RESOLUTIONDATE"] and r["ADDDATE"]:
            days = max(0, (r["RESOLUTIONDATE"] - r["ADDDATE"]) / 86_400_000)
        sr.append({"type": t, "agency": r["ORGANIZATIONACRONYM"] or "", "added": k.day(r["ADDDATE"]),
                   "status": r["SERVICEORDERSTATUS"] or "", "days": days,
                   "housing": any(w in t.upper() for w in HOUSING_WORDS)})
    sr.sort(key=lambda r: r["added"] or "", reverse=True)

    # Permits at the address.
    permits = []
    for y in range(PERMIT_FIRST_YEAR, this_year + 1):
        layer = k.dcdata.resolve_yearly_layer("Building Permits in {year}", y)
        if layer:
            permits += k.query(layer, f"FULL_ADDRESS LIKE '{PERMIT_PREFIX}%'",
                               ["PERMIT_ID", "ISSUE_DATE", "PERMIT_TYPE_NAME", "PERMIT_SUBTYPE_NAME", "DESC_OF_WORK"])
    pseen = set()
    plist = []
    for p in sorted(permits, key=lambda p: p["ISSUE_DATE"] or 0, reverse=True):
        if p["PERMIT_ID"] in pseen:
            continue
        pseen.add(p["PERMIT_ID"])
        work = (p["DESC_OF_WORK"] or "").strip()
        if work.lower() in ("undefined", "null", "none", "n/a"):
            work = ""
        plist.append({"id": p["PERMIT_ID"], "day": k.day(p["ISSUE_DATE"]), "group": k.permit_group(p["PERMIT_TYPE_NAME"], p["PERMIT_SUBTYPE_NAME"], work),
                      "sub": (p["PERMIT_SUBTYPE_NAME"] or p["PERMIT_TYPE_NAME"] or "").title(), "work": work[:220]})

    # Crime counts nearby (server-side), last 12 months.
    d_lat = 150 / 111_320
    d_lon = 150 / (111_320 * math.cos(math.radians(lat)))
    box = {"rings": [[[lon - d_lon, lat - d_lat], [lon + d_lon, lat - d_lat], [lon + d_lon, lat + d_lat], [lon - d_lon, lat + d_lat], [lon - d_lon, lat - d_lat]]],
           "spatialReference": {"wkid": 4326}}
    crime = Counter()
    start = now - 365 * k.DAY
    for y in sorted({time.gmtime(start).tm_year, this_year}):
        layer = k.dcdata.resolve_yearly_layer("Crime Incidents in {year}", y)
        if layer:
            crime.update(k.dcdata.count_by(layer, box, k.dcdata.date_where("REPORT_DAT", start), "OFFENSE"))

    # Nearest Metro station (straight line).
    mdata = k.dcdata._request(f"{METRO_LAYER}/query", {"where": "1=1", "outFields": "NAME", "returnGeometry": "true", "outSR": 4326, "f": "json"})
    stations = [(f["attributes"].get("NAME"), f["geometry"]["y"], f["geometry"]["x"]) for f in mdata.get("features", []) if f.get("geometry")]
    metro = min(stations, key=lambda s: meters(lat, lon, s[1], s[2])) if stations else None
    metro_m = meters(lat, lon, metro[1], metro[2]) if metro else None

    # ---- render
    years = list(range(SR_FIRST_YEAR, this_year + 1))
    per_year = Counter((r["added"] or "0000")[:4] for r in sr)
    year_svg = k.svg_columns([(str(y) if y != this_year else f"{y}*", per_year.get(str(y), 0)) for y in years], height=150,
                             title="311 requests at this address per year", highlight_last=True)
    by_type = Counter(r["type"] for r in sr).most_common(12)
    type_svg = k.svg_bars(by_type, label_w=230, title="311 requests by type, all years")
    housing_n = sum(1 for r in sr if r["housing"])
    res_days = [r["days"] for r in sr if r["days"] is not None]
    med_days = k.median(res_days)
    open_n = sum(1 for r in sr if r["status"].upper() not in ("CLOSED", "CLOSE"))
    last12 = sum(1 for r in sr if r["added"] and r["added"] >= time.strftime("%Y-%m-%d", time.gmtime(start)))

    def sr_tr(r):
        d = "—" if r["days"] is None else ("same day" if r["days"] < 1 else f"{r['days']:.0f} days")
        mark = ' class="hous"' if r["housing"] else ""
        return (f"<tr{mark}><td>{k.esc(k.nice_date(r['added']))}</td><td>{k.esc(r['type'])}</td><td>{k.esc(r['agency'])}</td>"
                f"<td>{k.esc(r['status'].title())}</td><td class=\"n\">{d}</td></tr>")

    sr_table = "".join(sr_tr(r) for r in sr[:CAP])
    p_table = "".join(
        f"<tr><td>{k.esc(k.nice_date(p['day']))}</td><td>{k.esc(p['group'])}</td><td>{k.esc(p['sub'])}</td><td class=\"work\">{k.esc(p['work'].capitalize()) or '—'}</td></tr>"
        for p in plist[:CAP])
    crime_rows = "".join(f'<tr><td>{k.esc(o.title())}</td><td class="n">{n}</td></tr>' for o, n in crime.most_common())
    addr_display = k.titleish(MAR_ADDRESS.replace("AVENUE", "AVE"))
    units = int(pt["HOUSING_UNIT_COUNT"] or 0)
    walk_min = metro_m * 1.3 / 80 if metro_m else None  # 1.3 detour factor, 80 m/min walking

    body = f"""
<div class="bldg card">
  <div><span class="muted">Building</span><b>{k.esc(addr_display)}</b><span class="muted">Washington, DC 20011 · {k.esc(pt.get("WARD") or "")} · {k.esc(pt.get("SMD") or "")}</span></div>
  <div><span class="muted">Units (DC address registry)</span><b>{units or "—"}</b></div>
  <div><span class="muted">Property type (OTR)</span><b class="sm">{k.esc((tax.get("PROPTYPE") or "—").replace("(Elevato", "(Elevator)"))}</b></div>
  <div><span class="muted">Nearest Metro</span><b class="sm">{k.esc((metro[0] or "").title()) if metro else "—"}</b><span class="muted">{f"{metro_m:,.0f} m straight line, about {walk_min:.0f} min walk" if metro_m else ""}</span></div>
</div>

<p class="nograde">No grade, no stars. This page shows public records exactly as DC publishes them, so you can judge for yourself. A request to 311 is a report, not a finding; many are routine (bulk pickup, parking) and some are made by the building's own staff.</p>

<div class="grid">
  <div class="card stat"><span class="muted">311 requests at this address since {SR_FIRST_YEAR}</span><b>{len(sr)}</b><span class="muted">{last12} in the last 12 months</span></div>
  <div class="card stat"><span class="muted">Housing-related</span><b>{housing_n}</b><span class="muted">rodents, insects, housing inspections and similar</span></div>
  <div class="card stat"><span class="muted">Median time to close</span><b>{"—" if med_days is None else f"{med_days:.0f} d"}</b><span class="muted">{open_n} still open</span></div>
  <div class="card stat"><span class="muted">Building permits since {PERMIT_FIRST_YEAR}</span><b>{len(plist)}</b><span class="muted">at this address</span></div>
</div>

<section class="card">
  <h2>311 requests per year</h2>
  {year_svg}
  <p class="muted" style="font-size:.8rem;margin:.3rem 0 0">* {this_year} to date.</p>
</section>

<section class="card">
  <h2>What people reported</h2>
  {type_svg}
</section>

<section class="card">
  <h2>311 timeline</h2>
  <p class="muted" style="margin-top:0">Newest first{f", latest {CAP} of {len(sr)}" if len(sr) > CAP else ""}. Housing-related rows are tinted. DC's free-text notes and unit numbers are never shown{f"; {withheld} request{'s' if withheld != 1 else ''} about an individual (e.g. DMV or welfare issues) {'are' if withheld != 1 else 'is'} withheld" if withheld else ""}.</p>
  <div class="scroll"><table>
    <thead><tr><th>Logged</th><th>Request type</th><th>Agency</th><th>Status</th><th class="n">Closed in</th></tr></thead>
    <tbody>{sr_table or '<tr><td colspan="5" class="muted">No 311 requests logged at this address.</td></tr>'}</tbody>
  </table></div>
</section>

<section class="card">
  <h2>Permit history</h2>
  <p class="muted" style="margin-top:0">Building permits DOB issued at this address since {PERMIT_FIRST_YEAR}, newest first. Applicant and owner names are not shown.</p>
  <div class="scroll"><table>
    <thead><tr><th>Issued</th><th>Kind</th><th>Permit type</th><th>Work described</th></tr></thead>
    <tbody>{p_table or '<tr><td colspan="4" class="muted">No permits found at this address.</td></tr>'}</tbody>
  </table></div>
</section>

<section class="card">
  <h2>Reported crime within about 150 m, last 12 months</h2>
  <p class="muted" style="margin-top:0">MPD counts by offense for the few blocks around the building, not incidents at the building. Preliminary data.</p>
  <div class="scroll"><table><thead><tr><th>Offense</th><th class="n">Reports</th></tr></thead>
  <tbody>{crime_rows or '<tr><td colspan="2" class="muted">No reports in this area.</td></tr>'}</tbody></table></div>
</section>

<section class="card sponsor">
  <span class="label">Moving here?</span>
  <p style="margin:.2rem 0 0">[Renters insurance partner] · [Moving company partner] · [Internet provider partner]. Affiliate links help pay for this site; partners never affect what records appear above.</p>
</section>
"""
    extra_css = """
.bldg{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.bldg b{display:block;font-size:1.35rem;line-height:1.2}.bldg b.sm{font-size:1rem}
.bldg span{display:block;font-size:.8rem}
.nograde{font-size:.88rem;background:var(--soft);border-left:4px solid var(--accent);padding:.6rem .8rem;border-radius:6px}
tr.hous td{background:var(--soft)}
td.work{font-size:.82rem;color:var(--muted);min-width:220px}
"""
    values = k.base_values(RANK, IDEA_ID, SCORE, "live", pulled)
    values.update({
        "SHORT_NAME": f"{addr_display}: building records",
        "EXTRA_CSS": extra_css,
        "EYEBROW": "Petworth · Apartment building records",
        "HEADLINE": f"{addr_display}: what the public record shows",
        "DECK": f"Every 311 request logged at this {units}-unit building since {SR_FIRST_YEAR}, every building permit since {PERMIT_FIRST_YEAR}, and reported crime nearby, straight from DC open data.",
        "BODY": body,
        "PITCH": "One page per large apartment building that puts its 311 history, permits and surroundings in one place for renters comparing buildings. Revenue comes from renters-insurance and moving affiliate links. Records are shown raw, with no grade, because a grade is an opinion that invites defamation claims.",
        "WHATS_REAL": f"All records. This run matched {len(sr) + withheld} 311 requests logged at {MAR_ADDRESS} in the {SR_FIRST_YEAR}–{this_year} yearly layers, {len(plist)} building permits at the address in the {PERMIT_FIRST_YEAR}–{this_year} layers, server-side crime counts in a 300 m box, the unit count from DC's Address Points and property type from OTR's tax extract. Owner names, applicant names and 311 free-text details were never requested.",
        "WHATS_MOCKED": "The affiliate card is a placeholder. The building was chosen as a large elevator building inside the Petworth boundary, with no judgment about it. Walk time is a straight-line estimate, not a routed walk.",
        "NEXT_STEPS": "Generate one page per building with 20+ units from Address Points; add DOB housing-code inspection and violation records where published; show a neighborhood baseline (requests per unit) so numbers have context; offer a landlord response box; keep any paid \"verified building\" profiles off the .org sites.",
        "SOURCES": "Address Points, Integrated Tax System Public Extract, 311 City Service Requests, Building Permits, Crime Incidents and Metro Stations via Open Data DC",
    })
    k.write(OUT, k.fill(values))
    print(f"{len(sr)} 311 (+{withheld} withheld), {len(plist)} permits, crime {sum(crime.values())}, metro {metro}")


if __name__ == "__main__":
    main()
