"""Generate self-contained demo pages from live DC data.

    python demos/make_demos.py

Writes:
  demos/digest-petworth.html   weekly email digest (idea: Data Digest + Block Watch), from site/src/data/petworth.json
  demos/block-delafield.html   block page (idea: House & Block History + Block Report Card), queried live
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

DATA = ROOT / "site" / "src" / "data"
OUT = ROOT / "demos"
HISTORIC = "https://services.arcgis.com/neT9SoYxizqTHZPH/arcgis/rest/services/DC_HistoricalBuildings2017/FeatureServer/0"
HPN = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"

e = html.escape

CSS = """
:root{--bg:#fbfaf7;--card:#fff;--ink:#1d2321;--muted:#5d6763;--line:#e3e0d8;--accent:#245c4f;--soft:#e4efeb;--up:#a33a2c;--down:#2c6e49}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141816;--card:#1c211f;--ink:#e8ece9;--muted:#9aa5a0;--line:#2e3532;--accent:#7cc4ad;--soft:#22312c;--up:#f08a7a;--down:#8fd3a8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:680px;margin:0 auto;padding:24px 16px}a{color:var(--accent)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.muted{color:var(--muted)}.eyebrow{text-transform:uppercase;letter-spacing:.08em;font-size:.75rem;color:var(--accent);font-weight:700;margin:0}
h1{margin:.2rem 0 .3rem;line-height:1.15}h2{font-size:1.1rem;margin:0 0 .6rem}
.sponsor{border:1px dashed var(--accent);background:var(--soft);font-size:.92rem}
.sponsor .label{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
ul{padding-left:1.1rem;margin:.3rem 0}li{margin:.3rem 0}
table{width:100%;border-collapse:collapse;font-size:.92rem}th,td{text-align:left;padding:.4rem .4rem;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:.75rem;text-transform:uppercase;color:var(--muted)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.up{color:var(--up);font-weight:600}.down{color:var(--down);font-weight:600}
.demo-banner{background:#fff3cd;color:#5c4400;padding:8px 16px;font-size:.85rem;text-align:center}
.stat{display:inline-block;margin-right:22px}.stat b{font-size:1.6rem;display:block}
.scroll{overflow-x:auto}
"""


def page(title: str, body: str, note: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><style>{CSS}</style></head><body>
<div class="demo-banner">DEMO · {e(note)}</div>
{body}
</body></html>"""


def tc(s: str) -> str:
    return re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(0).upper(), (s or "").title())


# ---------------------------------------------------------------- digest demo

def digest_demo() -> Path:
    d = json.loads((DATA / "petworth.json").read_text(encoding="utf-8"))
    gen = d["generated_at"][:10]
    big = [p for p in d["permits"] if p["group"] in ("Demolition", "New construction", "Additions")]
    other = Counter(p["group"] for p in d["permits"] if p not in big)
    movers = sorted(
        (t for t in d["requests"]["by_type"] if max(t["count"], t["previous"]) >= 30 and t["previous"] >= 10),
        key=lambda t: -abs(t["count"] - t["previous"]),
    )[:4]
    def mover(t):
        pct = round((t["count"] - t["previous"]) / t["previous"] * 100)
        cls = "up" if pct > 0 else "down"
        return f'<li>{e(t["type"])}: <b>{t["count"]}</b> <span class="{cls}">({pct:+d}%)</span> <span class="muted">vs {t["previous"]}</span></li>'
    smd_lines = "".join(
        f'<li>SMD {e(s["smd"])}: {e(tc(s["commissioner"] or "vacant"))}</li>' for s in d["smds"]
    )
    body = f"""<div class="wrap">
<p class="eyebrow">Petworth Weekly · {e(gen)}</p>
<h1>What changed in Petworth</h1>
<p class="muted">Every item below comes from DC's own open data, pulled automatically. Independent; not affiliated with DC Government, the ANC or any BID.</p>

<div class="card sponsor"><div class="label">Presented by</div><b>[Local sponsor name]</b>, your Petworth real-estate team. One line of copy and a link. <span class="muted">(One clearly labeled sponsor slot per issue.)</span></div>

<div class="card"><h2>At a glance (last 30 days)</h2>
<div class="stat"><b>{len(d["permits"])}</b>permits</div><div class="stat"><b>{d["requests"]["total"]:,}</b>311 requests</div><div class="stat"><b>{d["crime"]["total"]}</b>crime reports <span class="muted">({d["crime"]["previous_total"]} prior)</span></div></div>

<div class="card"><h2>Bigger projects ({len(big)})</h2><ul>
{"".join(f'<li><b>{e(tc(p["address"]))}</b>: {e(p["group"])}<br><span class="muted">{e((p["work"] or "")[:180])}</span></li>' for p in big) or "<li>None this period.</li>"}
</ul><p class="muted">Also issued: {", ".join(f"{n} {g.lower()}" for g, n in other.most_common())}.</p></div>

<div class="card"><h2>What neighbors reported to 311</h2><ul>{"".join(mover(t) for t in movers)}</ul>
<p class="muted">Compared with the previous 30 days.</p></div>

<div class="card"><h2>Your commissioners</h2><ul>{smd_lines}</ul>
<p class="muted">ANC meetings are open to the public. Find agendas at <a href="https://anc.dc.gov">anc.dc.gov</a>.</p></div>

<div class="card sponsor"><div class="label">Community notice</div>Free slot for a nonprofit or school event each week. <span class="muted">(Builds goodwill; costs nothing.)</span></div>

<p class="muted" style="font-size:.85rem">Sources: Open Data DC (CC BY 4.0): Building Permits, 311 City Service Requests, Crime Incidents (counts only), Single Member Districts 2023. Generated {e(d["generated_at"])}.<br>You're getting this because you subscribed at petworth.org. Unsubscribe.</p>
</div>"""
    out = OUT / "digest-petworth.html"
    out.write_text(page("Petworth Weekly (demo)", body, f"Weekly digest built from live data pulled {gen}"), encoding="utf-8")
    return out


# ---------------------------------------------------------------- block page demo

BLOCK_LO, BLOCK_HI = 400, 499
STREET_HIST = "DELAFIELD PLACE NW"
STREET_RE = re.compile(r"^(\d+)\s+DELAFIELD\s+(PL|PLACE)\s+NW", re.I)


def year_of(ms):
    # Historic permit dates are negative epoch milliseconds, which time.gmtime rejects on Windows.
    if ms is None:
        return None
    return (datetime(1970, 1, 1) + timedelta(milliseconds=ms)).year


def block_demo() -> Path:
    geom = dcdata.boundary(HPN, "DC_HPN_NAME='PETWORTH'")
    hist = dcdata.query_features(
        HISTORIC, geom, f"FULLADDRES LIKE '4__ {STREET_HIST}'",
        ["FULLADDRES", "Date", "Architect", "Builder", "EstimatedCost", "Stories", "Material", "Extant", "Purpose", "House_Type", "PermitNumber"],
    )
    hist = [h for h in hist if STREET_RE.match(h["FULLADDRES"] or "") and BLOCK_LO <= int(STREET_RE.match(h["FULLADDRES"]).group(1)) <= BLOCK_HI]
    hist.sort(key=lambda h: int(STREET_RE.match(h["FULLADDRES"]).group(1)))
    years = [y for y in (year_of(h["Date"]) for h in hist) if y]
    architects = Counter(h["Architect"] for h in hist if h["Architect"])
    builders = Counter(h["Builder"] for h in hist if h["Builder"])

    now = time.time()
    permits = []
    for layer in [dcdata.resolve_yearly_layer("Building Permits in {year}", y) for y in (time.gmtime(now).tm_year - 1, time.gmtime(now).tm_year)]:
        if layer:
            permits += dcdata.query_features(layer, geom, "FULL_ADDRESS LIKE '4__ DELAFIELD%'", ["PERMIT_ID", "ISSUE_DATE", "PERMIT_TYPE_NAME", "PERMIT_SUBTYPE_NAME", "FULL_ADDRESS", "DESC_OF_WORK"])
    permits = [p for p in permits if STREET_RE.match(p["FULL_ADDRESS"] or "")]
    permits.sort(key=lambda p: p["ISSUE_DATE"] or 0, reverse=True)

    sr_layer = dcdata.resolve_yearly_layer("311 City Service Requests in {year}", time.gmtime(now).tm_year)
    sr = dcdata.query_features(sr_layer, geom, "STREETADDRESS LIKE '4__ DELAFIELD%'", ["SERVICECODEDESCRIPTION", "ADDDATE", "STREETADDRESS"]) if sr_layer else []
    sr = [r for r in sr if STREET_RE.match(r["STREETADDRESS"] or "")]
    sr_counts = Counter(r["SERVICECODEDESCRIPTION"] for r in sr)

    # One historic permit often covered a whole row of houses, and its estimated cost is for the
    # entire permit, so group by permit rather than repeating the total on every house.
    by_permit: dict[str, list[dict]] = {}
    for h in hist:
        by_permit.setdefault(str(h["PermitNumber"] or "unknown"), []).append(h)
    hist_rows = ""
    for num, houses in by_permit.items():
        first = houses[0]
        nums = [int(STREET_RE.match(h["FULLADDRES"]).group(1)) for h in houses]
        cost = first["EstimatedCost"] or ""
        cost_txt = f"${int(cost):,}" if cost.isdigit() else ""
        hist_rows += (
            f"<tr><td>{min(nums)}–{max(nums)} Delafield Pl NW<br><span class='muted'>{len(houses)} buildings, permit {e(num)}</span></td>"
            f"<td class='n'>{year_of(first['Date']) or ''}</td><td>{e(first['Architect'] or '')}</td><td>{e(first['Builder'] or '')}</td>"
            f"<td class='n'>{cost_txt}</td><td>{e(first['Material'] or '')} {e((first['House_Type'] or '').lower())}</td></tr>"
        ) if len(houses) > 1 else (
            f"<tr><td>{e(tc(first['FULLADDRES']))}<br><span class='muted'>permit {e(num)}</span></td><td class='n'>{year_of(first['Date']) or ''}</td>"
            f"<td>{e(first['Architect'] or '')}</td><td>{e(first['Builder'] or '')}</td><td class='n'>{cost_txt}</td>"
            f"<td>{e(first['Material'] or '')} {e((first['House_Type'] or '').lower())}</td></tr>"
        )
    permit_rows = "".join(
        f"<li><b>{e(tc(p['FULL_ADDRESS'].replace(', WASHINGTON, DC', '')))}</b> · {time.strftime('%b %d, %Y', time.gmtime(p['ISSUE_DATE'] / 1000)) if p['ISSUE_DATE'] else ''}"
        f"<br><span class='muted'>{e(tc(p['PERMIT_SUBTYPE_NAME'] or p['PERMIT_TYPE_NAME'] or ''))}: {e((p['DESC_OF_WORK'] or '')[:160])}</span></li>"
        for p in permits[:12]
    ) or "<li>No permits in the last two calendar years.</li>"
    sr_rows = "".join(f"<tr><td>{e(t)}</td><td class='n'>{n}</td></tr>" for t, n in sr_counts.most_common(8)) or "<tr><td colspan=2>None this year.</td></tr>"
    era = "unknown" if not years else str(min(years)) if min(years) == max(years) else f"{min(years)}–{max(years)}"
    top_arch = ", ".join(f"{a} ({n})" for a, n in architects.most_common(2))
    top_build = ", ".join(f"{b} ({n})" for b, n in builders.most_common(2))
    sanborn = "https://www.loc.gov/collections/sanborn-maps/?q=washington+d.c.+1927"

    body = f"""<div class="wrap">
<p class="eyebrow">Petworth · Block page</p>
<h1>400 block of Delafield Place NW</h1>
<p class="muted">What this block was built as, and what is happening on it now. One page like this could exist for every block in the neighborhood.</p>

<div class="card"><h2>Then: how the block was built</h2>
<div class="stat"><b>{len(hist)}</b>original building permits</div><div class="stat"><b>{era}</b>construction years</div>
<p>Most-named architects: {e(top_arch) or "not recorded"}.<br>Most-named builders: {e(top_build) or "not recorded"}.</p>
<p class="muted">From DC Historic Preservation Office "Historic Data on DC Buildings" (HistoryQuest, CC BY 4.0), which indexes original building permits. See this area on the 1927 Sanborn fire-insurance maps at the <a href="{sanborn}">Library of Congress</a> (public domain).</p>
<div class="scroll"><table><thead><tr><th>Addresses</th><th>Year</th><th>Architect</th><th>Builder</th><th>Permit est. cost</th><th>Type</th></tr></thead><tbody>{hist_rows}</tbody></table></div></div>

<div class="card"><h2>Now: permits on this block</h2><ul>{permit_rows}</ul>
<p class="muted">Building permits issued since January {time.gmtime(now).tm_year - 1}. Source: Open Data DC.</p></div>

<div class="card"><h2>Now: what neighbors reported to 311 this year</h2><div class="scroll"><table><thead><tr><th>Request type</th><th>Count</th></tr></thead><tbody>{sr_rows}</tbody></table></div>
<p class="muted">Counts only. Source: Open Data DC 311 City Service Requests.</p></div>

<div class="card sponsor"><div class="label">Sponsor slot</div>A single labeled sponsor per neighborhood's block pages (for example, a local agent). Data stays neutral.</div>
<p class="muted" style="font-size:.85rem">Independent project; not affiliated with DC Government. Historic owner names are omitted on purpose. Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(now))}.</p>
</div>"""
    out = OUT / "block-delafield.html"
    out.write_text(page("400 block of Delafield Place NW (demo)", body, "Block page built from live DC data"), encoding="utf-8")
    print(f"block: {len(hist)} historic records, {len(permits)} permits, {len(sr)} 311 requests")
    return out


if __name__ == "__main__":
    print(digest_demo())
    print(block_demo())
