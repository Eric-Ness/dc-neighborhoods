"""Demo #04: Home Sales & Assessment Check (idea civic-data#5).

Live this run, for houses (row, semi-detached, detached) in OTR's "Petworth" assessment neighborhood:
- Integrated Tax System Public Extract (OTR): address, assessment sub-area, tax square, current
  total assessment, last recorded sale price/date and OTR's sale acceptance code.
- CAMA Residential (OTR): gross building area and bedrooms, joined by SSL.
Owner fields are never requested (propkit_shared.assert_no_owner_fields guards every query).

The assessment checker runs client-side over the embedded parcel list; no network calls from the page.
Run from the repo root: python demos/ideas/src/04_home_sales_assessment_check.py
"""

from __future__ import annotations

import datetime
import functools
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propkit_shared as k  # noqa: E402

RANK, IDEA_ID, SCORE = 4, "civic-data#5", "75.8"
OUT = k.ROOT / "demos" / "ideas" / "04-home-sales-assessment-check.html"
NBHD = "Petworth"
HOUSE_CODES = {"011": "Rowhouse", "013": "Semi-detached", "012": "Detached"}
COMP_MONTHS = 18
RECENT_DAYS = 60
CAP = 50


def fetch(now: float) -> tuple[list[dict], dict[str, dict], str]:
    itspe = k.resolve(k.ITSPE_TITLE)
    codes = ",".join(f"'{c}'" for c in HOUSE_CODES)
    fields = ["SSL", "PREMISEADD", "USECODE", "SUBNBHD", "SQUARE", "NEWTOTAL", "OLDTOTAL", "SALEPRICE", "SALEDATE", "ACCEPTCODE"]
    parcels = k.query(itspe, f"NBHDNAME='{NBHD}' AND USECODE IN ({codes})", fields)
    cama_url = k.resolve(k.CAMA_RES_TITLE)
    cama: dict[str, dict] = {}
    ssls = [p["SSL"] for p in parcels if p["SSL"]]
    for i in range(0, len(ssls), 400):
        chunk = ",".join("'" + s.replace("'", "''") + "'" for s in ssls[i:i + 400])
        for r in k.query(cama_url, f"SSL IN ({chunk})", ["SSL", "BLDG_NUM", "GBA", "BEDRM", "BATHRM"]):
            if r["SSL"] not in cama or (r["BLDG_NUM"] or 9) < (cama[r["SSL"]]["BLDG_NUM"] or 9):
                cama[r["SSL"]] = r
    return parcels, cama, itspe


@functools.lru_cache(maxsize=None)
def months_between(a: str, b: str) -> float:
    da, db = datetime.date.fromisoformat(a), datetime.date.fromisoformat(b)
    return abs((da - db).days) / 30.44


def comps_for(subj: list, rows: list[list], today: str) -> list[list]:
    """Mirror of the page's JS: same house type, recent market sales, then nearest by sub-area,
    tax-square number, size and recency. Row layout documented in build()."""
    addr, sub, sq, typ, gba, assessed = subj[:6]
    pool = [r for r in rows if r[8] == 1 and r[0] != addr and r[3] == typ and r[7] and months_between(r[6], today) <= COMP_MONTHS]
    if len(pool) < 5:
        pool = [r for r in rows if r[8] == 1 and r[0] != addr and r[7] and months_between(r[6], today) <= COMP_MONTHS]

    def score(r):
        s = 0 if r[1] == sub else 1
        s += min(abs((r[2] or 0) - (sq or 0)), 200) / 100
        if gba and r[4]:
            s += 2 * abs(r[4] - gba) / gba
        else:
            s += 0.6
        s += 0.5 * months_between(r[6], today) / COMP_MONTHS
        return s

    return sorted(pool, key=score)[:5]


def judge(subj: list, comps: list[list]) -> tuple[float | None, float | None]:
    """Return (indicated value, ratio of assessment to indicated value)."""
    gba, assessed = subj[4], subj[5]
    ppsf = [c[7] / c[4] for c in comps if c[4]]
    if gba and len(ppsf) >= 3:
        ind = gba * k.median(ppsf)
    else:
        ind = k.median([c[7] for c in comps])
    if not ind or not assessed:
        return None, None
    return ind, assessed / ind


def build() -> None:
    now = time.time()
    today = time.strftime("%Y-%m-%d", time.gmtime(now))
    parcels, cama, itspe_url = fetch(now)

    # Compact rows for the page:
    # [address, subarea, square(int), type code, gba, assessed, sale date, sale price (market only else 0), market flag, beds]
    rows: list[list] = []
    for p in parcels:
        addr = k.clean_premise(p["PREMISEADD"])
        if not addr or not p["NEWTOTAL"]:
            continue
        c = cama.get(p["SSL"], {})
        sale_day = k.day(p["SALEDATE"])
        market = 1 if (p["ACCEPTCODE"] or "") == "Market Sale" and (p["SALEPRICE"] or 0) >= 150_000 and sale_day else 0
        try:
            sq = int("".join(ch for ch in (p["SQUARE"] or "") if ch.isdigit()) or 0)
        except ValueError:
            sq = 0
        rows.append([addr, p["SUBNBHD"] or "", sq, p["USECODE"], int(c.get("GBA") or 0) or None, int(p["NEWTOTAL"]),
                     sale_day or "", int(p["SALEPRICE"] or 0) if market else 0, market, int(c.get("BEDRM") or 0) or None])
    rows.sort(key=lambda r: r[0])
    if len(rows) < 500:
        raise RuntimeError(f"only {len(rows)} parcels; expected thousands")

    recent = [r for r in rows if r[8] == 1 and months_between(r[6], today) * 30.44 <= RECENT_DAYS]
    recent.sort(key=lambda r: r[6], reverse=True)
    comp_pool = [r for r in rows if r[8] == 1 and months_between(r[6], today) <= COMP_MONTHS]
    all_recent_sales = [r for r in rows if r[6] and months_between(r[6], today) * 30.44 <= RECENT_DAYS]

    # Sample address: a rowhouse whose ratio sits clearly away from 1, so the flag is visible.
    candidates = []
    for r in rows:
        if r[3] != "011" or not r[4] or r[8] == 1:
            continue
        cs = comps_for(r, rows, today)
        ind, ratio = judge(r, cs)
        if ratio and 1.08 <= ratio <= 1.16 and len(cs) == 5 and all(c[1] == r[1] for c in cs):
            candidates.append((abs(ratio - 1.12), r[0]))
        if len(candidates) >= 40:
            break
    sample = min(candidates)[1] if candidates else next(r[0] for r in rows if r[4])

    # Ratio across the whole comp pool: assessment / sale price.
    pool_ratios = [r[5] / r[7] for r in comp_pool if r[7]]
    med_ratio = k.median(pool_ratios)

    def tr(r):
        ppsf = f"${r[7] / r[4]:,.0f}" if r[4] else "—"
        return (f"<tr><td>{k.esc(r[0])}</td><td>{k.esc(k.nice_date(r[6]))}</td><td>{HOUSE_CODES[r[3]]}</td>"
                f'<td class="n">{k.money(r[7])}</td><td class="n">{ppsf}</td><td class="n">{r[9] or "—"}</td>'
                f'<td class="n">{k.money(r[5])}</td></tr>')

    sold_rows = "".join(tr(r) for r in recent[:CAP])
    med_recent = k.median([r[7] for r in recent])
    med_ppsf = k.median([r[7] / r[4] for r in recent if r[4]])

    # Monthly median sale price, last 12 months (market sales only).
    months = []
    t = time.gmtime(now)
    y, m = t.tm_year, t.tm_mon
    for _ in range(12):
        months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    by_month = {mo: [r[7] for r in comp_pool if r[6].startswith(mo) and r[3] == "011"] for mo in months}
    labels = [time.strftime("%b", time.strptime(mo, "%Y-%m")) for mo in months]
    trend = k.svg_lines({"Rowhouse median sale": [k.median(v) if len(v) >= 3 else None for v in by_month.values()]}, labels,
                        title="Median rowhouse sale price by month")
    counts = k.svg_columns([(lab, len(v)) for lab, v in zip(labels, by_month.values())], height=120, title="Rowhouse market sales per month")

    data_js = json.dumps({"rows": rows, "today": today, "compMonths": COMP_MONTHS, "types": HOUSE_CODES, "sample": sample},
                         separators=(",", ":")).replace("</", "<\\/")

    body = f"""
<div class="grid">
  <div class="card stat"><span class="muted">Market sales recorded, last {RECENT_DAYS} days</span><b>{len(recent)}</b><span class="muted">houses; {len(all_recent_sales)} deeds of any kind</span></div>
  <div class="card stat"><span class="muted">Median price</span><b>{k.money(med_recent, True)}</b><span class="muted">those {len(recent)} sales</span></div>
  <div class="card stat"><span class="muted">Median $/sq ft</span><b>{k.money(med_ppsf)}</b><span class="muted">building area from CAMA</span></div>
  <div class="card stat"><span class="muted">Assessment ÷ sale price</span><b>{med_ratio:.2f}</b><span class="muted">median, {len(comp_pool):,} sales in {COMP_MONTHS} mo</span></div>
</div>

<section class="card" id="checker">
  <h2>Check your assessment</h2>
  <p class="muted" style="margin-top:0">Type a Petworth house address. We pull the five most similar recent market sales and compare your assessed value with what they sold for. Informational only, not tax or legal advice.</p>
  <label for="addr" class="lbl">House address</label>
  <div class="row">
    <input id="addr" list="addrs" autocomplete="off" spellcheck="false" placeholder="e.g. 4100 8th St NW">
    <button id="go" type="button">Check</button>
  </div>
  <datalist id="addrs"></datalist>
  <div id="result" aria-live="polite"><p class="muted">Loading the sample address…</p></div>
  <p class="fine">Comparables: same house type, a recorded market sale in the last {COMP_MONTHS} months, then ranked by same OTR sub-area, nearest tax square, closest building size and most recent sale. "Indicated value" is your building area × the comparables' median price per square foot (or their median price when size is missing). Sale prices lag deeds by a few weeks, and assessments value the property as of January 1, so small gaps are normal. The pre-filled address is an example picked automatically from public tax records, not a judgment about that home.</p>
  <div class="appeal">
    <b>Think your assessment is too high?</b> Appeals are free. File a first-level review with OTR after your assessment notice arrives; the deadline is printed on the notice.
    <a href="{k.OTR_APPEAL_URL}">OTR: Real property assessment appeal rights &amp; application</a>
  </div>
</section>

<section class="card">
  <h2>Sold recently in Petworth</h2>
  <p class="muted" style="margin-top:0">Market-rate house sales recorded by OTR in the last {RECENT_DAYS} days, newest first{" (first " + str(CAP) + " shown)" if len(recent) > CAP else ""}. Foreclosures, transfers between related parties and other non-market deeds are left out.</p>
  <div class="scroll"><table>
    <thead><tr><th>Address</th><th>Recorded</th><th>Type</th><th class="n">Price</th><th class="n">$/sq ft</th><th class="n">Beds</th><th class="n">Assessed</th></tr></thead>
    <tbody>{sold_rows or '<tr><td colspan="7" class="muted">No market sales recorded in this window.</td></tr>'}</tbody>
  </table></div>
</section>

<section class="card">
  <h2>Rowhouse prices, last 12 months</h2>
  {trend}
  <p class="muted" style="font-size:.85rem;margin:.6rem 0 .2rem">Rowhouse market sales per month (months with under 3 sales have no median point)</p>
  {counts}
</section>

<section class="card sponsor">
  <span class="label">Sponsor</span>
  <p style="margin:.2rem 0 0"><b>[Sponsor name]</b> supports this free tool. Sponsors never see what you look up, and the checker is never gated.</p>
</section>

<script>
(() => {{
const D = {data_js};
const R = D.rows, byAddr = new Map(R.map(r => [r[0].toUpperCase(), r]));
const fmt = v => v == null ? "—" : "$" + Math.round(v).toLocaleString("en-US");
const months = d => Math.abs(new Date(D.today) - new Date(d)) / (30.44 * 864e5);
const med = a => {{ a = a.filter(v => v != null).sort((x, y) => x - y); if (!a.length) return null; const m = a.length >> 1; return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; }};
const esc = s => String(s).replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}})[c]);
const dl = document.getElementById("addrs");
dl.innerHTML = R.map(r => '<option value="' + esc(r[0]) + '">').join("");
function comps(s) {{
  const ok = r => r[8] === 1 && r[0] !== s[0] && r[7] && months(r[6]) <= D.compMonths;
  let pool = R.filter(r => ok(r) && r[3] === s[3]);
  if (pool.length < 5) pool = R.filter(ok);
  const score = r => (r[1] === s[1] ? 0 : 1) + Math.min(Math.abs(r[2] - s[2]), 200) / 100
    + (s[4] && r[4] ? 2 * Math.abs(r[4] - s[4]) / s[4] : 0.6) + 0.5 * months(r[6]) / D.compMonths;
  return pool.map(r => [score(r), r]).sort((a, b) => a[0] - b[0]).slice(0, 5).map(x => x[1]);
}}
function show(addr) {{
  const out = document.getElementById("result");
  const s = byAddr.get(addr.trim().toUpperCase());
  if (!s) {{ out.innerHTML = '<p class="muted">No Petworth house found at that address. Pick one from the suggestions (houses only in this demo; condos are not included).</p>'; return; }}
  const cs = comps(s);
  const ppsf = cs.filter(c => c[4]).map(c => c[7] / c[4]);
  const ind = s[4] && ppsf.length >= 3 ? s[4] * med(ppsf) : med(cs.map(c => c[7]));
  const ratio = ind ? s[5] / ind : null;
  let flag = "", cls = "even";
  if (ratio == null) flag = "Not enough comparable sales to judge.";
  else if (ratio > 1.10) {{ flag = "Your assessment is " + Math.round((ratio - 1) * 100) + "% above what comparable homes sold for. Worth a closer look before the appeal deadline."; cls = "high"; }}
  else if (ratio < 0.90) {{ flag = "Your assessment is " + Math.round((1 - ratio) * 100) + "% below what comparable homes sold for."; cls = "low"; }}
  else flag = "Your assessment is in line with comparable sales (within 10%).";
  const rows = cs.map(c => "<tr><td>" + esc(c[0]) + "</td><td>" + c[6] + '</td><td class="n">' + fmt(c[7]) + '</td><td class="n">' + (c[4] ? c[4].toLocaleString("en-US") : "—") + '</td><td class="n">' + (c[4] ? fmt(c[7] / c[4]) : "—") + '</td><td class="n">' + fmt(c[5]) + '</td><td class="n">' + (c[5] / c[7]).toFixed(2) + "</td></tr>").join("");
  out.innerHTML =
    '<div class="subject"><div><span class="muted">Your home</span><b>' + esc(s[0]) + '</b><span class="muted">' + D.types[s[3]] + (s[4] ? " · " + s[4].toLocaleString("en-US") + " sq ft" : "") + (s[9] ? " · " + s[9] + " bed" : "") + " · sub-area " + esc(s[1] || "?") + "</span></div>" +
    '<div><span class="muted">Assessed</span><b>' + fmt(s[5]) + '</b></div><div><span class="muted">Indicated by comps</span><b>' + fmt(ind) + '</b></div><div><span class="muted">Ratio</span><b>' + (ratio ? ratio.toFixed(2) : "—") + "</b></div></div>" +
    '<p class="flag ' + cls + '">' + flag + "</p>" +
    '<div class="scroll"><table><thead><tr><th>Comparable sale</th><th>Recorded</th><th class="n">Price</th><th class="n">Sq ft</th><th class="n">$/sq ft</th><th class="n">Assessed</th><th class="n">Assessed ÷ price</th></tr></thead><tbody>' + rows + "</tbody></table></div>";
}}
const inp = document.getElementById("addr");
document.getElementById("go").addEventListener("click", () => show(inp.value));
inp.addEventListener("keydown", e => {{ if (e.key === "Enter") show(inp.value); }});
inp.addEventListener("change", () => {{ if (byAddr.has(inp.value.trim().toUpperCase())) show(inp.value); }});
inp.value = D.sample; show(D.sample);
}})();
</script>
"""
    extra_css = """
.lbl{display:block;font-size:.8rem;font-weight:600;margin-bottom:4px}
.row{display:flex;gap:8px;flex-wrap:wrap}
.row input{flex:1 1 220px;min-width:0;font:inherit;padding:.5rem .6rem;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
.row button{font:inherit;font-weight:600;padding:.5rem 1rem;border-radius:8px;border:0;background:var(--accent);color:var(--card);cursor:pointer}
#result{margin-top:14px}
.subject{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;background:var(--soft);border-radius:8px;padding:12px}
.subject b{display:block;font-size:1.25rem;font-variant-numeric:tabular-nums}
.subject span{display:block;font-size:.8rem}
.flag{font-weight:600;padding:.55rem .7rem;border-radius:8px;border-left:4px solid var(--accent);background:var(--soft)}
.flag.high{border-color:var(--up);color:var(--up)}.flag.low{border-color:var(--down)}
.fine{font-size:.8rem;color:var(--muted)}
.appeal{border-top:1px solid var(--line);padding-top:10px;font-size:.92rem}
.appeal a{display:inline-block;margin-top:4px}
"""
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    values = k.base_values(RANK, IDEA_ID, SCORE, "live", pulled)
    values.update({
        "SHORT_NAME": "Petworth Home Sales & Assessment Check",
        "EXTRA_CSS": extra_css,
        "EYEBROW": "Petworth · Home sales &amp; assessments",
        "HEADLINE": "Is your assessment in line with what homes like yours sold for?",
        "DECK": f"Every recorded market sale of a Petworth house, and a free checker that puts your assessed value next to five comparable sales. Built from DC's own tax records for {len(rows):,} houses.",
        "BODY": body,
        "PITCH": "A monthly list of recorded home sales plus a free tool that compares a homeowner's assessment with nearby comparable sales, timed to the appeal season. A single local real-estate or mortgage sponsor pays for the page; the tool is never gated.",
        "WHATS_REAL": f"Everything above. This run pulled {len(rows):,} Petworth houses (row, semi-detached, detached) from OTR's Integrated Tax System Public Extract: address, sub-area, tax square, current assessment, last recorded sale and OTR's sale code. Building area and bedrooms come from CAMA Residential, joined by SSL. Sales shown are those OTR codes as \"Market Sale\" at $150,000 or more. Owner names exist in the tax data and were never requested.",
        "WHATS_MOCKED": "The sponsor card is a placeholder. Comparables use tax-square numbers as a stand-in for distance because the tax extract has no coordinates. Only each parcel's most recent sale is in the extract, so a home sold twice in 18 months counts once. Condos are left out of this demo.",
        "NEXT_STEPS": "Add parcel coordinates (Address Points or tax lots) for true distance-based comps and a map; add condos via CAMA Condominium; refresh nightly with the existing ingest; send an appeal-season reminder when notices mail; have a local appraiser review the comp logic and wording.",
        "SOURCES": f'<a href="{itspe_url}">Integrated Tax System Public Extract (OTR)</a>, <a href="{k.resolve(k.CAMA_RES_TITLE)}">CAMA Residential (OTR)</a> via Open Data DC; appeal info from <a href="{k.OTR_APPEAL_URL}">OTR</a>',
    })
    k.write(OUT, k.fill(values))
    print(f"{len(rows)} parcels, {len(recent)} recent market sales, {len(comp_pool)} comp pool, sample {sample}")


if __name__ == "__main__":
    build()
