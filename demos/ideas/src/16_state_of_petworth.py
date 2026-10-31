"""Demo #16: Annual Neighborhood Data Report, "The State of Petworth" (idea monetization#10).

Built from the nightly ingest output (site/src/data/petworth.json: last-30-day permits, 311, crime
and the SMD/commissioner list) plus a fresh 24-month pull inside the DC Health Petworth boundary:
- Building Permits (DOB): rows with type/subtype only, for monthly counts and groups.
- 311 City Service Requests: monthly server-side counts and 12-month counts by type.
- Crime Incidents (MPD): server-side counts by offense, 12 months vs the 12 before.
- Integrated Tax System Public Extract (OTR): market-sale prices, Petworth assessment neighborhood.
- Basic Business Licenses (DLCP): new licenses by category in ANC 4C and 4D (server-side counts).
- Vacant and Blighted Building Addresses (DOB): current count in the boundary.
No individual records are shown; everything is a count or a median.

Run from the repo root: python demos/ideas/src/16_state_of_petworth.py
"""

from __future__ import annotations

import datetime
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propkit_shared as k  # noqa: E402

RANK, IDEA_ID, SCORE = 16, "monetization#10", "69.7"
OUT = k.ROOT / "demos" / "ideas" / "16-state-of-petworth.html"
INGEST = k.ROOT / "site" / "src" / "data" / "petworth.json"


def month_starts(today: datetime.date, n: int) -> list[datetime.date]:
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        out.append(datetime.date(y, m, 1))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


def epoch(d: datetime.date) -> float:
    return datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc).timestamp()


def layers(title: str, start: float, end: float) -> list[str]:
    out = []
    for y in range(time.gmtime(start).tm_year, time.gmtime(end).tm_year + 1):
        u = k.dcdata.resolve_yearly_layer(title, y)
        if u:
            out.append(u)
    return out


def pct(a: float, b: float) -> str:
    if not b:
        return ""
    p = (a - b) / b * 100
    return f'<span class="{"up" if p > 0 else "down"}">{"+" if p > 0 else ""}{p:.0f}%</span>'


def delta(a: int, b: int) -> str:
    """Change on counts: show % only when both are 100+, else the raw difference."""
    if a >= 100 and b >= 100:
        return pct(a, b) + " vs prior year"
    d = a - b
    return f'{"+" if d > 0 else ""}{d} vs prior year'


def main() -> None:
    ingest = json.loads(INGEST.read_text(encoding="utf-8"))
    now = time.time()
    today = datetime.date.fromtimestamp(now)
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    geom = k.boundary("PETWORTH")
    y_end = now
    y_start = now - 365 * k.DAY
    p_start = now - 730 * k.DAY

    # Permits, 24 months.
    permits = []
    for layer in layers("Building Permits in {year}", p_start, y_end):
        permits += k.spatial(layer, geom, k.dcdata.date_where("ISSUE_DATE", p_start), ["PERMIT_ID", "ISSUE_DATE", "PERMIT_TYPE_NAME", "PERMIT_SUBTYPE_NAME"])
    seen = set()
    perm = []
    for p in permits:
        if p["PERMIT_ID"] in seen or not p["ISSUE_DATE"]:
            continue
        seen.add(p["PERMIT_ID"])
        perm.append({"ms": p["ISSUE_DATE"], "group": k.permit_group(p["PERMIT_TYPE_NAME"], p["PERMIT_SUBTYPE_NAME"], "")})
    perm_cur = [p for p in perm if p["ms"] >= y_start * 1000]
    perm_prev = [p for p in perm if p["ms"] < y_start * 1000]

    # 311 monthly counts (12 months) and types.
    months = month_starts(today, 12)
    sr_month = []
    for i, m0 in enumerate(months):
        m1 = months[i + 1] if i + 1 < len(months) else today + datetime.timedelta(days=1)
        n = 0
        for layer in layers("311 City Service Requests in {year}", epoch(m0), epoch(m1) - 1):
            n += k.count(layer, k.dcdata.date_where("ADDDATE", epoch(m0), epoch(m1)), geom)
        sr_month.append((m0.strftime("%b"), n))
    sr_types: Counter = Counter()
    sr_prev_total = 0
    for layer in layers("311 City Service Requests in {year}", y_start, y_end):
        sr_types.update(k.dcdata.count_by(layer, geom, k.dcdata.date_where("ADDDATE", y_start), "SERVICECODEDESCRIPTION"))
    for layer in layers("311 City Service Requests in {year}", p_start, y_start):
        sr_prev_total += k.count(layer, k.dcdata.date_where("ADDDATE", p_start, y_start), geom)
    sr_total = sum(sr_types.values())

    # Crime counts.
    crime_cur: Counter = Counter()
    crime_prev: Counter = Counter()
    for layer in layers("Crime Incidents in {year}", p_start, y_end):
        crime_cur.update(k.dcdata.count_by(layer, geom, k.dcdata.date_where("REPORT_DAT", y_start), "OFFENSE"))
        crime_prev.update(k.dcdata.count_by(layer, geom, k.dcdata.date_where("REPORT_DAT", p_start, y_start), "OFFENSE"))

    # Home sales.
    itspe = k.resolve(k.ITSPE_TITLE)
    d_prev = (today - datetime.timedelta(days=730)).isoformat()
    sales = k.query(itspe, f"NBHDNAME='Petworth' AND USECODE IN ('011','012','013','016','017') AND ACCEPTCODE='Market Sale' AND SALEDATE >= DATE '{d_prev}' AND SALEPRICE >= 75000",
                    ["USECODE", "SALEPRICE", "SALEDATE"])
    cut = (today - datetime.timedelta(days=365)).isoformat()
    def med(rows, houses: bool):
        return k.median([r["SALEPRICE"] for r in rows if (r["USECODE"] in ("011", "012", "013")) == houses])
    s_cur = [r for r in sales if k.day(r["SALEDATE"]) >= cut]
    s_prev = [r for r in sales if k.day(r["SALEDATE"]) < cut]

    # New business licenses (ANC 4C/4D, approximate).
    bbl = k.resolve(k.BBL_TITLE)
    lic = k.group_count(bbl, k.dcdata.date_where("INITIALISSUEDATE", y_start) + " AND ANC IN ('ANC 4C','ANC 4D')", ["CATEGORYSERVICETYPE"])
    lic_c = Counter({(r["CATEGORYSERVICETYPE"] or "Other"): r["n"] for r in lic})
    lic_prev = sum(r["n"] for r in k.group_count(bbl, k.dcdata.date_where("INITIALISSUEDATE", p_start, y_start) + " AND ANC IN ('ANC 4C','ANC 4D')", ["CATEGORYSERVICETYPE"])
                   if r["CATEGORYSERVICETYPE"] in ("Food Services", "General Sales and Services", "Beauty and Grooming Services"))
    storefront = sum(lic_c.get(c, 0) for c in ("Food Services", "General Sales and Services", "Beauty and Grooming Services"))

    vb = k.count(k.resolve(k.VB_ADDR_TITLE), "1=1", geom)

    # ---- render
    yr = today.year
    period = f"{(today - datetime.timedelta(days=365)).strftime('%b %Y')} – {today.strftime('%b %Y')}"
    perm_months = []
    for i, m0 in enumerate(months):
        m1 = months[i + 1] if i + 1 < len(months) else today + datetime.timedelta(days=1)
        perm_months.append((m0.strftime("%b"), sum(1 for p in perm_cur if epoch(m0) * 1000 <= p["ms"] < epoch(m1) * 1000)))
    groups_cur = Counter(p["group"] for p in perm_cur)
    groups_prev = Counter(p["group"] for p in perm_prev)
    g_rows = "".join(f'<tr><td>{k.esc(g)}</td><td class="n">{n}</td><td class="n">{groups_prev.get(g, 0)}</td></tr>' for g, n in groups_cur.most_common())
    crime_rows = "".join(
        f'<tr><td>{k.esc(o.title())}</td><td class="n">{crime_cur.get(o, 0)}</td><td class="n">{crime_prev.get(o, 0)}</td></tr>'
        for o in sorted(set(crime_cur) | set(crime_prev), key=lambda o: -crime_cur.get(o, 0)))
    c_tot, c_prev = sum(crime_cur.values()), sum(crime_prev.values())
    smd_rows = "".join(f'<tr><td>{k.esc(s["smd"])}</td><td>{k.esc(s["commissioner"] or "Vacant seat")}</td></tr>' for s in ingest.get("smds", []))
    lic_items = [(c, n) for c, n in lic_c.most_common(8)]

    body = f"""
<section class="hero">
  <p class="kicker">Annual report · {period}</p>
  <p class="big">The State of Petworth {yr}</p>
  <p class="lede">A year of permits, 311 calls, home sales, new businesses and public safety in one of DC's fastest-changing rowhouse neighborhoods, measured from the District's own open data.</p>
  <div class="title-sponsor"><span class="label">Presented by</span> <b>[Title sponsor]</b></div>
  <nav class="toc" aria-label="Chapters"><a href="#ch-build">Building</a><a href="#ch-homes">Homes</a><a href="#ch-biz">Business</a><a href="#ch-311">311</a><a href="#ch-safety">Safety</a><a href="#ch-gov">Who represents you</a></nav>
</section>

<div class="grid kpis">
  <div class="card stat"><span class="muted">Building permits</span><b>{len(perm_cur):,}</b><span class="muted">{delta(len(perm_cur), len(perm_prev))}</span></div>
  <div class="card stat"><span class="muted">Median house sale</span><b>{k.money(med(s_cur, True), True)}</b><span class="muted">{pct(med(s_cur, True) or 0, med(s_prev, True) or 0)} vs prior year</span></div>
  <div class="card stat"><span class="muted">311 requests</span><b>{sr_total:,}</b><span class="muted">{delta(sr_total, sr_prev_total)}</span></div>
  <div class="card stat"><span class="muted">Reported crimes</span><b>{c_tot:,}</b><span class="muted">{delta(c_tot, c_prev)}</span></div>
</div>

<section class="card chapter" id="ch-build">
  <p class="eyebrow">Chapter 1</p><h2>Building</h2>
  <p>DOB issued <b>{len(perm_cur):,}</b> building permits inside Petworth in the last 12 months, compared with {len(perm_prev):,} the year before. The last 30 days in the nightly feed add {len(ingest["permits"])} more to watch.</p>
  {k.svg_columns(perm_months, height=160, title="Building permits issued per month", highlight_last=True)}
  <div class="scroll"><table><thead><tr><th>Kind of work</th><th class="n">Last 12 mo</th><th class="n">Prior 12 mo</th></tr></thead><tbody>{g_rows}</tbody></table></div>
</section>

<section class="card chapter" id="ch-homes">
  <p class="eyebrow">Chapter 2</p><h2>Homes</h2>
  <p>OTR recorded <b>{len(s_cur)}</b> market-rate sales of Petworth houses and condos in the last 12 months. The median house sold for <b>{k.money(med(s_cur, True))}</b> and the median condo for <b>{k.money(med(s_cur, False))}</b>.</p>
  <div class="grid">
    <div class="stat"><span class="muted">Houses, median</span><b>{k.money(med(s_cur, True), True)}</b><span class="muted">prior year {k.money(med(s_prev, True), True)}</span></div>
    <div class="stat"><span class="muted">Condos, median</span><b>{k.money(med(s_cur, False), True)}</b><span class="muted">prior year {k.money(med(s_prev, False), True)}</span></div>
    <div class="stat"><span class="muted">On the vacant/blighted list</span><b>{vb}</b><span class="muted">addresses today</span></div>
  </div>
</section>

<section class="card chapter" id="ch-biz">
  <p class="eyebrow">Chapter 3</p><h2>Business</h2>
  <p>DC issued <b>{storefront}</b> new storefront-type business licenses (food, retail and services, personal care) in ANC 4C and 4D over the year, against {lic_prev} the year before. All new licenses by category:</p>
  {k.svg_bars(lic_items, label_w=230, title="New business licenses by category, ANC 4C and 4D")}
</section>

<section class="card chapter" id="ch-311">
  <p class="eyebrow">Chapter 4</p><h2>311</h2>
  <p>Residents and city crews logged <b>{sr_total:,}</b> service requests inside Petworth this year. The top requests:</p>
  {k.svg_bars(sr_types.most_common(10), label_w=250, title="Top 311 request types, last 12 months")}
  <p class="muted" style="font-size:.85rem;margin:.6rem 0 .2rem">Requests per month</p>
  {k.svg_columns(sr_month, height=150, title="311 requests per month", highlight_last=True)}
</section>

<section class="card chapter" id="ch-safety">
  <p class="eyebrow">Chapter 5</p><h2>Public safety</h2>
  <p>MPD recorded <b>{c_tot:,}</b> reported crimes in Petworth over the last 12 months, compared with {c_prev:,} the year before. These are preliminary DC Code counts, not FBI totals.</p>
  <div class="scroll"><table><thead><tr><th>Offense</th><th class="n">Last 12 mo</th><th class="n">Prior 12 mo</th></tr></thead><tbody>{crime_rows}</tbody></table></div>
</section>

<section class="card chapter" id="ch-gov">
  <p class="eyebrow">Chapter 6</p><h2>Who represents you</h2>
  <p>Petworth's single-member districts and their elected ANC commissioners.</p>
  <div class="scroll"><table><thead><tr><th>SMD</th><th>Commissioner</th></tr></thead><tbody>{smd_rows}</tbody></table></div>
</section>

<section class="card sponsor">
  <span class="label">Title sponsor</span>
  <p style="margin:.2rem 0 0"><b>[Title sponsor]</b> makes this report free for everyone. The sponsor did not see or shape the findings. Want the data behind every chart? <b>[Data pack: CSV + methodology]</b></p>
</section>
"""
    extra_css = """
.hero{background:var(--accent);color:var(--card);border-radius:14px;padding:26px 22px;margin:10px 0 16px}
.hero .kicker{text-transform:uppercase;letter-spacing:.1em;font-size:.72rem;font-weight:700;margin:0;opacity:.85}
.hero .big{font-size:clamp(2rem,8vw,3.2rem);font-weight:800;line-height:1.05;margin:.3rem 0 .5rem;letter-spacing:-.01em}
.hero .lede{margin:0 0 .9rem;max-width:56ch;opacity:.95}
.hero .title-sponsor{display:inline-block;border:1px dashed currentColor;border-radius:8px;padding:.3rem .7rem;font-size:.9rem}
.hero .title-sponsor .label{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;opacity:.85}
.toc{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:14px;font-size:.88rem}
.toc a{color:var(--card);opacity:.9}
.chapter h2{font-size:1.45rem;margin-top:.1rem}
.chapter .eyebrow{margin-bottom:0}
.kpis .stat b{font-size:1.9rem}
"""
    values = k.base_values(RANK, IDEA_ID, SCORE, "live", pulled)
    values.update({
        "SHORT_NAME": f"The State of Petworth {yr}",
        "EXTRA_CSS": extra_css,
        "EYEBROW": "Petworth · Annual data report",
        "HEADLINE": f"Petworth by the numbers, {period}",
        "DECK": "Six short chapters, every number from DC open data, refreshed when the report is published each fall.",
        "BODY": body,
        "PITCH": "A once-a-year, press-ready data report per neighborhood (permits, homes, businesses, 311, safety, representation) published as a microsite and PDF. A bank, developer or brokerage pays as title sponsor; a CSV data pack is sold to brokers and retailers.",
        "WHATS_REAL": f"Every number. This run pulled 24 months of building permits inside the DC Health Petworth boundary ({len(perm):,} permits), 12 monthly 311 counts plus counts by type, MPD crime counts by offense for two 12-month windows, {len(sales)} OTR market sales, business-license counts for ANC 4C and 4D, and the vacant/blighted address count. The 30-day permit count and the commissioner list come from the nightly ingest file generated {ingest['generated_at'][:10]}.",
        "WHATS_MOCKED": "The title sponsor and data-pack slots are placeholders. Business licenses use ANC 4C and 4D, which are close to but not the same as the Petworth boundary, and home sales use OTR's Petworth assessment neighborhood. Metro ridership and foot-traffic chapters from the original idea are left out (WMATA ridership needs a separate download).",
        "NEXT_STEPS": "Freeze a dated snapshot each October so year-over-year numbers are reproducible; add a methodology appendix and printable PDF; add WMATA station ridership; pitch three title sponsors per neighborhood with this demo; offer the CSV pack via a simple checkout.",
        "SOURCES": "Nightly ingest (site/src/data/petworth.json); Building Permits, 311 City Service Requests, Crime Incidents, Integrated Tax System Public Extract, Basic Business Licenses and Vacant and Blighted Building Addresses via Open Data DC",
    })
    k.write(OUT, k.fill(values))
    print(f"permits {len(perm_cur)}/{len(perm_prev)}, 311 {sr_total}/{sr_prev_total}, crime {c_tot}/{c_prev}, sales {len(s_cur)}/{len(s_prev)}, lic {storefront}/{lic_prev}, vb {vb}")


if __name__ == "__main__":
    main()
