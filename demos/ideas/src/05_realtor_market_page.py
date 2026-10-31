"""Demo #05: Realtor Market Page, one exclusive agent sponsor per neighborhood (idea monetization#2).

Live this run:
- Integrated Tax System Public Extract (OTR): market-coded sales of Petworth houses and condos, 24 months.
- CAMA Residential (OTR): building area and bedrooms for recent house sales, joined by SSL.
- Building Permits (DOB, yearly layers) inside the Petworth boundary: new buildings and multi-unit work.
Sample: the sponsor card ("[Agent name]"). Rent data is not included (no open source).
Owner fields are never requested.

Run from the repo root: python demos/ideas/src/05_realtor_market_page.py
"""

from __future__ import annotations

import datetime
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propkit_shared as k  # noqa: E402

RANK, IDEA_ID, SCORE = 5, "monetization#2", "75.2"
OUT = k.ROOT / "demos" / "ideas" / "05-realtor-market-page.html"
NBHD = "Petworth"
TYPES = {"011": "Rowhouse", "013": "Semi-detached", "012": "Detached", "016": "Condo", "017": "Condo"}
GROUP = {"011": "Houses", "012": "Houses", "013": "Houses", "016": "Condos", "017": "Condos"}
CAP = 40


def quarter(d: str) -> str:
    y, m = int(d[:4]), int(d[5:7])
    return f"{y} Q{(m - 1) // 3 + 1}"


def main() -> None:
    now = time.time()
    today = datetime.date.fromtimestamp(now)
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    start = today - datetime.timedelta(days=730)

    itspe = k.resolve(k.ITSPE_TITLE)
    codes = ",".join(f"'{c}'" for c in TYPES)
    sales = k.query(itspe, f"NBHDNAME='{NBHD}' AND USECODE IN ({codes}) AND ACCEPTCODE='Market Sale' AND SALEDATE >= DATE '{start}' AND SALEPRICE >= 75000",
                    ["SSL", "PREMISEADD", "USECODE", "SALEPRICE", "SALEDATE", "NEWTOTAL"], order_by="SALEDATE DESC")
    for s in sales:
        s["day"] = k.day(s["SALEDATE"])
        s["group"] = GROUP[s["USECODE"]]
    if len(sales) < 50:
        raise RuntimeError(f"only {len(sales)} sales")

    def within(s, a_days, b_days=0):
        d = datetime.date.fromisoformat(s["day"])
        return today - datetime.timedelta(days=a_days) <= d < today - datetime.timedelta(days=b_days)

    last12 = [s for s in sales if within(s, 365)]
    prev12 = [s for s in sales if within(s, 730, 365)]
    recent = [s for s in sales if within(s, 60)]

    cama_url = k.resolve(k.CAMA_RES_TITLE)
    house_ssls = [s["SSL"] for s in recent if s["group"] == "Houses"]
    cama = {}
    if house_ssls:
        chunk = ",".join("'" + x + "'" for x in house_ssls)
        for r in k.query(cama_url, f"SSL IN ({chunk})", ["SSL", "BLDG_NUM", "GBA", "BEDRM"]):
            if r["SSL"] not in cama or (r["BLDG_NUM"] or 9) < (cama[r["SSL"]]["BLDG_NUM"] or 9):
                cama[r["SSL"]] = r

    def med(rows, group):
        return k.median([r["SALEPRICE"] for r in rows if r["group"] == group])

    def change(a, b):
        if not a or not b:
            return ""
        pct = (a - b) / b * 100
        cls = "up" if pct > 0 else "down"
        return f'<span class="{cls}">{"+" if pct > 0 else ""}{pct:.1f}%</span> vs prior 12 mo'

    n_h12 = sum(1 for s in last12 if s["group"] == "Houses")
    n_c12 = sum(1 for s in last12 if s["group"] == "Condos")
    stats = f"""
<div class="grid">
  <div class="card stat"><span class="muted">Median house price, 12 mo</span><b>{k.money(med(last12, "Houses"), True)}</b><span class="muted">{n_h12} sales · {change(med(last12, "Houses"), med(prev12, "Houses"))}</span></div>
  <div class="card stat"><span class="muted">Median condo price, 12 mo</span><b>{k.money(med(last12, "Condos"), True)}</b><span class="muted">{n_c12} sales · {change(med(last12, "Condos"), med(prev12, "Condos"))}</span></div>
  <div class="card stat"><span class="muted">Market sales, last 60 days</span><b>{len(recent)}</b><span class="muted">recorded deeds</span></div>
  <div class="card stat"><span class="muted">Sold above assessment</span><b>{sum(1 for s in last12 if s["NEWTOTAL"] and s["SALEPRICE"] > s["NEWTOTAL"])} of {len(last12)}</b><span class="muted">12-month sales</span></div>
</div>"""

    # Quarterly medians.
    qs = sorted({quarter(s["day"]) for s in sales})[-8:]
    series = {}
    for g in ("Houses", "Condos"):
        vals = []
        for q in qs:
            v = [s["SALEPRICE"] for s in sales if s["group"] == g and quarter(s["day"]) == q]
            vals.append(k.median(v) if len(v) >= 3 else None)
        series[f"{g} median"] = vals
    trend = k.svg_lines(series, [q.replace(" ", " ") for q in qs], title="Quarterly median sale price, houses and condos")
    vols = k.svg_columns([(q[2:], sum(1 for s in sales if quarter(s["day"]) == q)) for q in qs], height=120, title="Market sales per quarter",
                         highlight_last=True)

    # Price bands, last 12 months.
    bands = [(0, 400_000, "Under $400K"), (400_000, 600_000, "$400K–600K"), (600_000, 800_000, "$600K–800K"),
             (800_000, 1_000_000, "$800K–1M"), (1_000_000, 1_250_000, "$1M–1.25M"), (1_250_000, 10**9, "$1.25M+")]
    band_items = [(lab, sum(1 for s in last12 if lo <= s["SALEPRICE"] < hi)) for lo, hi, lab in bands]
    band_svg = k.svg_bars(band_items, label_w=120, title="Sales by price band, last 12 months")

    # Recent sales table.
    def tr(s):
        c = cama.get(s["SSL"], {})
        gba = c.get("GBA")
        ppsf = f"${s['SALEPRICE'] / gba:,.0f}" if gba else "—"
        beds = int(c["BEDRM"]) if c.get("BEDRM") else "—"
        return (f"<tr><td>{k.esc(k.clean_premise(s['PREMISEADD']))}</td><td>{k.esc(k.nice_date(s['day']))}</td><td>{TYPES[s['USECODE']]}</td>"
                f'<td class="n">{k.money(s["SALEPRICE"])}</td><td class="n">{ppsf}</td><td class="n">{beds}</td></tr>')
    table = "".join(tr(s) for s in recent[:CAP])

    # New housing from permits.
    geom = k.boundary("PETWORTH")
    since = now - 540 * k.DAY
    permits = []
    for y in sorted({time.gmtime(since).tm_year, time.gmtime(now).tm_year}):
        layer = dcdata_layer = k.dcdata.resolve_yearly_layer("Building Permits in {year}", y)
        if not dcdata_layer:
            continue
        where = (k.dcdata.date_where("ISSUE_DATE", since) +
                 " AND PERMIT_TYPE_NAME='CONSTRUCTION' AND (PERMIT_SUBTYPE_NAME LIKE '%NEW BUILDING%' OR UPPER(DESC_OF_WORK) LIKE '%NEW CONSTRUCTION%' OR UPPER(DESC_OF_WORK) LIKE '%UNIT%')")
        permits += k.spatial(layer, geom, where, ["PERMIT_ID", "ISSUE_DATE", "PERMIT_SUBTYPE_NAME", "FULL_ADDRESS", "DESC_OF_WORK"], "ISSUE_DATE DESC")
    pipeline = []
    seen = set()
    for p in permits:
        work = (p["DESC_OF_WORK"] or "").upper()
        m = re.search(r"(\d{1,3})\s*[- ]?\s*(?:RESIDENTIAL\s+|DWELLING\s+|APARTMENT\s+|CONDO(?:MINIUM)?\s+)?(?:UNITS?|DWELLINGS?|APARTMENTS)\b", work)
        units = int(m.group(1)) if m else None
        is_new = "NEW BUILDING" in (p["PERMIT_SUBTYPE_NAME"] or "") or "NEW CONSTRUCTION" in work
        adds_units = bool(re.search(r"CONVER|EXPAN|ADDITIONAL\s+\d*\s*(?:DWELLING\s+)?UNIT|ADD(?:ING)?\s+(?:\d+\s+)?(?:NEW\s+)?UNIT", work)) and "TO REMAIN" not in work
        if not (is_new or (units and units >= 3 and adds_units)) or (units is not None and units > 400):
            continue
        if any(w in work for w in ("REVISION", "SUPPLEMENT", "SHEETING", "SHORING", "ACCESSORY", "GARAGE", "SHED", "DECK")):
            continue
        addr = (p["FULL_ADDRESS"] or "").replace(", WASHINGTON, DC", "").strip()
        addr = re.sub(r"\s+\d{5}$", "", addr)
        if addr in seen:
            continue
        seen.add(addr)
        pipeline.append({"addr": k.titleish(addr), "day": k.day(p["ISSUE_DATE"]), "units": units, "new": is_new,
                         "work": (p["DESC_OF_WORK"] or "").strip()[:150]})
    pipeline.sort(key=lambda x: (-(x["units"] or 0), x["day"]), reverse=False)
    pipe_rows = "".join(
        f"<tr><td>{k.esc(x['addr'])}</td><td>{k.esc(k.nice_date(x['day']))}</td><td class=\"n\">{x['units'] or '—'}</td>"
        f"<td>{'New building' if x['new'] else 'Conversion / addition'}</td><td class=\"work\">{k.esc(x['work'].capitalize())}</td></tr>"
        for x in pipeline[:20])
    total_units = sum(x["units"] or 0 for x in pipeline)

    month = today.strftime("%B %Y")
    body = f"""
<section class="card sponsor agent" aria-label="Page sponsor">
  <div class="avatar" aria-hidden="true">[AN]</div>
  <div class="who">
    <span class="label">Petworth Housing Pulse is sponsored by</span>
    <b>[Agent name]</b>
    <span class="muted">[Brokerage] · Petworth specialist</span>
  </div>
  <a class="cta" href="#about-demo">Contact [Agent name]</a>
</section>

{stats}

<section class="card">
  <h2>Prices by quarter</h2>
  {trend}
  <p class="muted" style="font-size:.85rem;margin:.6rem 0 .2rem">Market sales per quarter (current quarter in progress)</p>
  {vols}
</section>

<section class="card">
  <h2>Where prices landed, last 12 months</h2>
  {band_svg}
</section>

<section class="card">
  <h2>Recently sold</h2>
  <p class="muted" style="margin-top:0">Market sales recorded by DC's Office of Tax and Revenue in the last 60 days{f" (newest {CAP} shown)" if len(recent) > CAP else ""}. Deeds are recorded a few weeks after closing.</p>
  <div class="scroll"><table>
    <thead><tr><th>Address</th><th>Recorded</th><th>Type</th><th class="n">Price</th><th class="n">$/sq ft</th><th class="n">Beds</th></tr></thead>
    <tbody>{table or '<tr><td colspan="6" class="muted">No sales recorded in this window.</td></tr>'}</tbody>
  </table></div>
</section>

<section class="card">
  <h2>New housing coming</h2>
  <p class="muted" style="margin-top:0">{len(pipeline)} building permits since {k.nice_date(time.strftime('%Y-%m-%d', time.gmtime(since)))} for new buildings, or conversions and expansions that mention 3+ units{f", about {total_units:,} units where the permit states a count" if total_units else ""}. Largest first; first 20 shown.</p>
  <div class="scroll"><table>
    <thead><tr><th>Address</th><th>Issued</th><th class="n">Units</th><th>Kind</th><th>Permit says</th></tr></thead>
    <tbody>{pipe_rows or '<tr><td colspan="5" class="muted">No qualifying permits in this window.</td></tr>'}</tbody>
  </table></div>
</section>

<p class="disclose">Sponsor disclosure: [Agent name] pays to sponsor this page for 12 months. The sponsor does not choose, edit or see the data before it is published, and we never sell visitor contact details.</p>
"""
    extra_css = """
.agent{display:flex;flex-wrap:wrap;align-items:center;gap:12px 16px}
.agent .avatar{width:56px;height:56px;border-radius:50%;background:var(--accent);color:var(--card);display:grid;place-items:center;font-weight:700;font-size:.85rem;flex:none}
.agent .who{flex:1 1 180px;min-width:0}.agent .who b{display:block;font-size:1.15rem}
.agent .cta{font-weight:600;text-decoration:none;border:1px solid var(--accent);border-radius:999px;padding:.4rem .9rem}
td.work{font-size:.82rem;color:var(--muted);min-width:220px}
.disclose{font-size:.8rem;color:var(--muted)}
"""
    values = k.base_values(RANK, IDEA_ID, SCORE, "live", pulled)
    values.update({
        "SHORT_NAME": "Petworth Housing Pulse",
        "EXTRA_CSS": extra_css,
        "EYEBROW": f"Petworth Housing Pulse · {month}",
        "HEADLINE": "What Petworth homes are selling for, and what's being built",
        "DECK": f"{len(last12)} market sales in the last 12 months, straight from DC's tax records, plus every new-housing permit. Updated nightly.",
        "BODY": body,
        "PITCH": "An auto-updating housing data page per neighborhood with one real-estate agent or team as its exclusive 12-month sponsor. The data stays neutral and public-record; the agent buys brand association, not leads.",
        "WHATS_REAL": f"All prices, counts and charts. This run pulled {len(sales)} Petworth house and condo sales that OTR codes as \"Market Sale\" over 24 months from the Integrated Tax System Public Extract, building area and bedrooms from CAMA Residential, and {len(permits)} candidate permits from DOB's Building Permits layers inside the DC Health Petworth boundary. Sales use OTR's \"Petworth\" assessment neighborhood, which is close to but not identical to that boundary.",
        "WHATS_MOCKED": "The sponsor card ([Agent name], [Brokerage], the [AN] initials and the contact button) is a placeholder, not a real agent. Rent ranges from the original idea are left out because there is no open rent source. Only each parcel's most recent sale is in the tax extract, so the earlier sale of a home that resold within 24 months is missing, which slightly undercounts the older quarters.",
        "NEXT_STEPS": "Pull full sale history from Tax System Property Sales for exact quarterly counts; add condo $/sq ft from CAMA Condominium; add a rent snapshot only from a licensed or open source; build the sponsor admin (headshot, link, 12-month term) and a one-page sponsor pitch with traffic numbers.",
        "SOURCES": f'<a href="{itspe}">Integrated Tax System Public Extract (OTR)</a>, <a href="{cama_url}">CAMA Residential (OTR)</a>, Building Permits (DOB) via Open Data DC',
    })
    k.write(OUT, k.fill(values))
    print(f"{len(sales)} sales, {len(recent)} recent, {len(pipeline)} pipeline permits")


if __name__ == "__main__":
    main()
