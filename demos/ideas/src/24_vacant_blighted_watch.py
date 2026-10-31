"""Demo #24: Vacant & Blighted Watch (idea civic-data#10).

Live this run, for the DC Health "Petworth" planning neighborhood:
- Vacant and Blighted Building Addresses (DOB): the public list of addresses, with location and SSL.
- Integrated Tax System Public Extract Vacant and Blighted (OTR): tax class, property type and
  assessment, joined by SSL. Owner fields are never requested.
- Building Permits (DOB), yearly layers covering the last 24 months, joined by SSL.
Addresses only; no owner names, no characterisation of anyone.

Run from the repo root: python demos/ideas/src/24_vacant_blighted_watch.py
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propkit_shared as k  # noqa: E402

RANK, IDEA_ID, SCORE = 24, "civic-data#10", "66.1"
OUT = k.ROOT / "demos" / "ideas" / "24-vacant-blighted-watch.html"
PERMIT_MONTHS = 24
CLASS = {"3": ("Vacant", "Class 3", "var(--gold)"), "4": ("Blighted", "Class 4", "var(--brick)")}
CAP = 80


def main() -> None:
    now = time.time()
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    geom = k.boundary("PETWORTH")

    addr_layer = k.resolve(k.VB_ADDR_TITLE)
    pts = k.spatial(addr_layer, geom, "1=1", ["ADDRESS", "SSL", "LATITUDE", "LONGITUDE", "SMD"])
    ssls = sorted({p["SSL"] for p in pts if p["SSL"]})
    if not pts:
        raise RuntimeError("no vacant/blighted addresses found in Petworth")

    tax_layer = k.resolve(k.VB_TITLE)
    tax: dict[str, dict] = {}
    for i in range(0, len(ssls), 200):
        chunk = ",".join("'" + s + "'" for s in ssls[i:i + 200])
        for r in k.query(tax_layer, f"SSL IN ({chunk})", ["SSL", "CLASSTYPE", "PROPTYPE", "USECODE", "NEWTOTAL", "SALEDATE"]):
            tax[r["SSL"]] = r

    since = now - PERMIT_MONTHS * 30.44 * k.DAY
    permits: dict[str, list] = defaultdict(list)
    for y in range(time.gmtime(since).tm_year, time.gmtime(now).tm_year + 1):
        layer = k.dcdata.resolve_yearly_layer("Building Permits in {year}", y)
        if not layer:
            continue
        for i in range(0, len(ssls), 200):
            chunk = ",".join("'" + s + "'" for s in ssls[i:i + 200])
            rows = k.query(layer, k.dcdata.date_where("ISSUE_DATE", since) + f" AND SSL IN ({chunk})",
                           ["PERMIT_ID", "ISSUE_DATE", "PERMIT_TYPE_NAME", "PERMIT_SUBTYPE_NAME", "SSL", "DESC_OF_WORK"])
            for r in rows:
                if all(r["PERMIT_ID"] != q["PERMIT_ID"] for q in permits[r["SSL"]]):
                    permits[r["SSL"]].append(r)

    items = []
    seen_addr = set()
    for p in pts:
        if p["ADDRESS"] in seen_addr:
            continue
        seen_addr.add(p["ADDRESS"])
        t = tax.get(p["SSL"], {})
        cls = t.get("CLASSTYPE")
        plist = sorted(permits.get(p["SSL"], []), key=lambda r: r["ISSUE_DATE"] or 0, reverse=True)
        latest = plist[0] if plist else None
        groups = {k.permit_group(r["PERMIT_TYPE_NAME"], r["PERMIT_SUBTYPE_NAME"], (r["DESC_OF_WORK"] or "")) for r in plist}
        items.append({
            "addr": k.titleish(p["ADDRESS"].replace("STREET", "ST").replace("AVENUE", "AVE").replace("PLACE", "PL").replace("ROAD", "RD")),
            "lat": p["LATITUDE"], "lon": p["LONGITUDE"], "smd": (p["SMD"] or "").replace("SMD ", ""),
            "cls": cls, "prop": (t.get("PROPTYPE") or "").replace("Residential-", "").replace("(Row", "(row)").replace("(Semi", "(semi)").replace("(Det", "(detached)").strip(),
            "value": t.get("NEWTOTAL"), "sold": (k.day(t.get("SALEDATE")) or "")[:4],
            "n_permits": len(plist), "latest": k.day(latest["ISSUE_DATE"]) if latest else None,
            "latest_kind": k.permit_group(latest["PERMIT_TYPE_NAME"], latest["PERMIT_SUBTYPE_NAME"], latest["DESC_OF_WORK"] or "") if latest else None,
            "work_started": bool(groups & {"Renovation & repair", "New construction", "Additions", "Demolition"}),
        })
    items.sort(key=lambda x: (x["cls"] != "4", x["smd"], x["addr"]))

    n_vac = sum(1 for x in items if x["cls"] == "3")
    n_bl = sum(1 for x in items if x["cls"] == "4")
    n_other = len(items) - n_vac - n_bl
    n_work = sum(1 for x in items if x["work_started"])
    n_any = sum(1 for x in items if x["n_permits"])

    dots = []
    for x in items:
        c = CLASS.get(x["cls"], ("Listed", "", "var(--muted)"))
        dots.append({"lat": x["lat"], "lon": x["lon"], "color": c[2], "label": f"{x['addr']} · {c[0]}"})
    svg = k.svg_map(geom, dots, title="Map of listed vacant and blighted addresses in Petworth")

    by_smd = defaultdict(int)
    for x in items:
        by_smd[x["smd"] or "?"] += 1
    smd_svg = k.svg_bars(sorted(by_smd.items()), label_w=80, title="Listed addresses by SMD")

    def tr(x):
        c = CLASS.get(x["cls"])
        badge = f'<span class="tag t{x["cls"]}">{c[0]}</span>' if c else '<span class="tag">Listed</span>'
        if x["n_permits"]:
            act = f'{x["n_permits"]} permit{"s" if x["n_permits"] != 1 else ""}; latest {k.esc(k.nice_date(x["latest"]))} ({k.esc(x["latest_kind"].lower())})'
        else:
            act = '<span class="muted">none</span>'
        return (f"<tr><td>{k.esc(x['addr'])}</td><td>{badge}</td><td>{k.esc(x['prop']) or '—'}</td><td>{k.esc(x['smd'])}</td>"
                f'<td class="n">{k.money(x["value"])}</td><td>{act}</td></tr>')

    table = "".join(tr(x) for x in items[:CAP])
    body = f"""
<div class="grid">
  <div class="card stat"><span class="muted">Addresses on DC's list</span><b>{len(items)}</b><span class="muted">inside Petworth</span></div>
  <div class="card stat"><span class="muted">Taxed as vacant</span><b>{n_vac}</b><span class="muted">Class 3, $5 per $100</span></div>
  <div class="card stat"><span class="muted">Taxed as blighted</span><b>{n_bl}</b><span class="muted">Class 4, $10 per $100</span></div>
  <div class="card stat"><span class="muted">Building permit in last {PERMIT_MONTHS} mo</span><b>{n_any}</b><span class="muted">{n_work} for construction or renovation</span></div>
</div>

<section class="card">
  <h2>Where they are</h2>
  {svg}
  <p class="legend"><span><i style="background:var(--gold)"></i>Vacant (Class 3)</span> <span><i style="background:var(--brick)"></i>Blighted (Class 4)</span> <span><i style="background:var(--muted)"></i>Listed, other tax class{f" ({n_other})" if n_other else ""}</span></p>
</section>

<section class="card">
  <h2>The list</h2>
  <p class="muted" style="margin-top:0">Every address on DC's vacant and blighted building list inside Petworth, blighted first, then by SMD{f" (first {CAP} shown)" if len(items) > CAP else ""}. A permit can mean work is under way, but it is not proof. "Listed, other tax class" means the building is on DOB's list but OTR currently taxes it at a regular rate, for example after an exemption or a recent change.</p>
  <div class="scroll"><table>
    <thead><tr><th>Address</th><th>Status</th><th>Property</th><th>SMD</th><th class="n">Assessed</th><th>Permits, last {PERMIT_MONTHS} mo</th></tr></thead>
    <tbody>{table}</tbody>
  </table></div>
</section>

<section class="card">
  <h2>By single-member district</h2>
  {smd_svg}
  <p class="muted" style="font-size:.85rem;margin:.4rem 0 0">For ANC commissioners: the count of listed addresses in each SMD.</p>
</section>

<section class="card">
  <h2>Know a building that looks empty?</h2>
  <p style="margin:0">DOB inspects buildings reported as possibly vacant. You can report one through <a href="https://311.dc.gov">DC 311</a>. Owners can apply for exemptions (for example, during active construction) through DOB, which is why some listed buildings are taxed at regular rates.</p>
</section>
"""
    extra_css = """
.legend{font-size:.82rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 14px;margin:.5rem 0 0}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px;vertical-align:-1px}
.tag{display:inline-block;font-size:.75rem;font-weight:600;padding:1px 7px;border-radius:999px;border:1px solid var(--muted);color:var(--muted);white-space:nowrap}
.tag.t3{border-color:var(--gold);color:var(--gold)}.tag.t4{border-color:var(--brick);color:var(--brick)}
"""
    values = k.base_values(RANK, IDEA_ID, SCORE, "live", pulled)
    values.update({
        "SHORT_NAME": "Petworth Vacant & Blighted Watch",
        "EXTRA_CSS": extra_css,
        "EYEBROW": "Petworth · Vacant &amp; blighted buildings",
        "HEADLINE": f"{len(items)} Petworth addresses on DC's vacant and blighted list",
        "DECK": "Where they are, how DC taxes them, and whether anyone has pulled a permit since. Addresses only, from the District's own public list.",
        "BODY": body,
        "PITCH": "A neutral, data-only tracker of buildings DC classifies as vacant or blighted in each neighborhood, with tax class and any permit activity. Daily snapshots turn the list into a record of how long each building has been listed and which ones came back into use.",
        "WHATS_REAL": f"Everything shown. This run pulled {len(pts)} points from DOB's Vacant and Blighted Building Addresses inside the DC Health Petworth boundary, joined {len(tax)} of them by SSL to OTR's Vacant and Blighted tax extract for class, property type and assessment, and matched building permits issued in the last {PERMIT_MONTHS} months by SSL. Owner names are in the tax extract and were never requested.",
        "WHATS_MOCKED": "Nothing is invented. Not built yet: \"listed since\" dates and the \"back in use\" list, which need the daily snapshots the product would start collecting; DC does not publish a listing date.",
        "NEXT_STEPS": "Snapshot the list nightly to record first-seen and removal dates; add the Adams Morgan page; show a small \"recently removed\" section; offer an RSS feed for ANC offices; keep wording neutral and never add owner data.",
        "SOURCES": f'<a href="{addr_layer}">Vacant and Blighted Building Addresses (DOB)</a>, <a href="{tax_layer}">ITS Public Extract Vacant and Blighted (OTR)</a>, Building Permits (DOB) via Open Data DC',
    })
    k.write(OUT, k.fill(values))
    print(f"{len(items)} addresses: {n_vac} vacant, {n_bl} blighted, {n_other} other; {n_any} with permits")


if __name__ == "__main__":
    main()
