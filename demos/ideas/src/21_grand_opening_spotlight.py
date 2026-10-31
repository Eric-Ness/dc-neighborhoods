"""Demo #21: Grand Opening Spotlight, a new-business tracker (idea monetization#4).

Live this run, for the ANCs covering Adams Morgan (1C), Petworth (4C, 4D), Tenleytown/Friendship
Heights (3E, 3/4G) and SW Waterfront (6D), last 60 days:
- Basic Business Licenses (DLCP): licenses whose initial issue date is in the window, filtered to
  storefront-type categories (food, retail/general sales, beauty, health, vehicle). Rentals,
  contractors, salespeople, charities and home addresses with apartment numbers are dropped.
  Sole proprietors' legal names are never shown; only trade names or business-entity names.
- Certificates of Occupancy (DOB) issued inside the ANC 1C boundary, non-residential only.
- Alcohol License Business Locations (ABCA): has no issue date, so only the newest license numbers
  in its latest snapshot are shown, labeled as such.
Sample: the paid "Featured" spotlight card.

Run from the repo root: python demos/ideas/src/21_grand_opening_spotlight.py
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propkit_shared as k  # noqa: E402

RANK, IDEA_ID, SCORE = 21, "monetization#4", "68.5"
OUT = k.ROOT / "demos" / "ideas" / "21-grand-opening-spotlight.html"
HOODS = [("Adams Morgan", ["1C"]), ("Petworth", ["4C", "4D"]), ("Tenleytown & Friendship Heights", ["3E", "3/4G"]), ("SW Waterfront", ["6D"])]
ANC_OF = {a: h for h, ancs in HOODS for a in ancs}
ANC_IN = ",".join(f"'ANC {a}'" for a in ANC_OF)
ANC_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Administrative_Other_Boundaries_WebMercator/MapServer/54"
WINDOW_DAYS = 60
KEEP = {"Food Services": "Food & drink", "General Sales and Services": "Shops & services", "Beauty and Grooming Services": "Beauty & grooming",
        "Health Services": "Health", "Vehicular Services": "Vehicle services", "Environmental Services": "Services"}
NO_NAME = {"", "N/A", "NA", "NONE", "NULL", "-"}


def norm_addr(a: str | None) -> str:
    a = (a or "").upper().split(",")[0]
    a = re.sub(r"\s+(STE|SUITE|UNIT|#|C-?\d|R-?\d).*$", "", a)
    a = a.replace(" STREET ", " ST ").replace(" AVENUE ", " AVE ").replace(" ROAD ", " RD ").replace(" PLACE ", " PL ")
    return re.sub(r"\s+", " ", a).strip()


def main() -> None:
    now = time.time()
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    start = now - WINDOW_DAYS * k.DAY

    bbl = k.resolve(k.BBL_TITLE)
    lic_rows = k.query(bbl, k.dcdata.date_where("INITIALISSUEDATE", start) + f" AND ANC IN ({ANC_IN})",
                       ["CATEGORYSERVICETYPE", "BUSINESSACTIVITY", "ENTITYTRADENAME", "ENTITYNAME", "ENTITYTYPE",
                        "PREMISEADDRESS", "INITIALISSUEDATE", "LICENSESTATUS", "SMD", "ANC"], order_by="INITIALISSUEDATE DESC")
    total_new = len(lic_rows)
    biz: dict[tuple, dict] = {}
    dropped_home = 0
    for r in lic_rows:
        cat = r["CATEGORYSERVICETYPE"]
        if cat not in KEEP:
            continue
        prem = r["PREMISEADDRESS"] or ""
        if re.search(r"\bAPT\b|\bAPARTMENT\b", prem, re.I):
            dropped_home += 1
            continue
        trade = (r["ENTITYTRADENAME"] or "").strip()
        if trade.upper() in NO_NAME:
            trade = ""
        entity = (r["ENTITYNAME"] or "").strip()
        sole = (r["ENTITYTYPE"] or "").lower().startswith("sole") or not r["ENTITYTYPE"]
        name = trade or ("" if sole else entity)
        if not name:
            dropped_home += 1  # sole proprietor with no trade name: likely a person working from home
            continue
        addr = norm_addr(prem)
        key = (addr, (name or "?").upper())
        item = biz.setdefault(key, {"name": name, "addr": k.titleish(addr), "cat": KEEP[cat], "acts": set(),
                                    "day": k.day(r["INITIALISSUEDATE"]), "smd": r["SMD"] or "", "food": False,
                                    "hood": ANC_OF.get((r["ANC"] or "").replace("ANC ", ""), "")})
        item["acts"].add((r["BUSINESSACTIVITY"] or "").strip())
        item["food"] = item["food"] or cat == "Food Services"
        if cat == "Food Services":
            item["cat"] = KEEP[cat]
    items = sorted(biz.values(), key=lambda x: (x["day"] or ""), reverse=True)

    # Keep only addresses DC's address registry marks as non-residential or mixed use, so a person's
    # home office never shows up as an "opening".
    def mar_form(a: str) -> str:
        words = a.upper().split(" ")
        full = {"ST": "STREET", "AVE": "AVENUE", "RD": "ROAD", "PL": "PLACE", "DR": "DRIVE", "CIR": "CIRCLE",
                "TER": "TERRACE", "CT": "COURT", "BLVD": "BOULEVARD", "PKWY": "PARKWAY", "LN": "LANE", "SQ": "SQUARE"}
        if len(words) >= 3 and words[-1] in ("NW", "NE", "SW", "SE"):
            words[-2] = full.get(words[-2], words[-2])
        return " ".join(words)

    ap = k.resolve("Address Points")
    forms = sorted({mar_form(it["addr"]) for it in items})
    rtype: dict[str, str] = {}
    for i in range(0, len(forms), 100):
        chunk = ",".join("'" + f.replace("'", "''") + "'" for f in forms[i:i + 100])
        for r in k.query(ap, f"ADDRESS IN ({chunk})", ["ADDRESS", "RESIDENTIAL_TYPE"]):
            rtype[r["ADDRESS"]] = r["RESIDENTIAL_TYPE"] or ""
    before = len(items)
    items = [it for it in items if rtype.get(mar_form(it["addr"]), "") in ("NON RESIDENTIAL", "MIXED USE")]
    dropped_home += before - len(items)

    co_layer = k.resolve("Certificate of Occupancy")
    co_rows = []
    for anc, hood in ANC_OF.items():
        g = k.dcdata.boundary(ANC_LAYER, f"ANC_ID='{anc}'")
        for r in k.spatial(co_layer, g, k.dcdata.date_where("ISSUE_DATE", start),
                           ["PERMIT_NUMBER", "ISSUE_DATE", "ADDRESS", "DESCRIPTION_OF_OCCUPANCY", "TRADING_AS", "OCCUPANCY_LOAD"], "ISSUE_DATE DESC"):
            r["hood"] = hood
            co_rows.append(r)
    cos: dict[str, dict] = {}
    for r in co_rows:
        if (r["OCCUPANCY_LOAD"] or "").upper() == "DWELLINGUNITS":
            continue
        d = r["DESCRIPTION_OF_OCCUPANCY"] or ""
        use = re.search(r"ZONING CODE USE:\s*(.*?)\s+TYPE OF CHANGES", d)
        app = re.search(r"TYPE OF CHANGES:\s*(.*?)\s*TYPE OF APPLICATION:\s*(.*?)\s+TYPE OF CERTIFICATE", d)
        cur = cos.setdefault(r["PERMIT_NUMBER"], {"addr": norm_addr(r["ADDRESS"]), "day": k.day(r["ISSUE_DATE"]), "name": "", "use": "", "change": "", "hood": r["hood"]})
        t = (r["TRADING_AS"] or "").strip()
        if t and t.upper() not in NO_NAME and not cur["name"]:
            cur["name"] = t
        if use and not cur["use"]:
            cur["use"] = use.group(1).strip().capitalize()
        if app and not cur["change"]:
            cur["change"] = (app.group(1) or app.group(2) or "").strip().capitalize()
    co_list = sorted(cos.values(), key=lambda x: x["day"] or "", reverse=True)
    co_addrs = {c["addr"]: c for c in co_list}
    for it in items:
        it["co"] = co_addrs.get(norm_addr(it["addr"]))

    abca = k.resolve(k.ABCA_TITLE)
    liq = k.query(abca, f"ANC IN ({ANC_IN}) AND STATUS='ACTIVE'", ["LICENSE", "TRADE_NAME", "TYPE", "ADDRESS", "CREATED", "ANC"])
    snap = max((r["CREATED"] or 0) for r in liq) if liq else None
    liq.sort(key=lambda r: int(m.group(1)) if (m := re.search(r"(\d+)", r["LICENSE"] or "")) else 0, reverse=True)
    liq_top = liq[:8]

    # ---- render
    def card(it):
        acts = ", ".join(sorted(a for a in it["acts"] if a))
        stages = ['<li class="done">License issued ' + k.esc(k.nice_date(it["day"])) + "</li>"]
        if it["co"]:
            stages.insert(0, '<li class="done">Certificate of occupancy ' + k.esc(k.nice_date(it["co"]["day"])) + "</li>")
        stages.append('<li class="todo">Opening date: not in public data</li>')
        return (f'<article class="biz{" food" if it["food"] else ""}" data-hood="{k.esc(it["hood"])}"><span class="cat">{k.esc(it["cat"])}</span>'
                f'<h3>{k.esc(it["name"])}</h3><p class="addr">{k.esc(it["addr"])} · {k.esc(it["hood"])} · SMD {k.esc(it["smd"])}</p>'
                f'<p class="acts">{k.esc(acts)}</p><ol class="pipe">{"".join(stages)}</ol>'
                f'<a class="claim" href="#about-demo">Is this your business? Claim this listing</a></article>')

    def hood_of(anc_field):
        return ANC_OF.get((anc_field or "").replace("ANC ", ""), "")

    food = [it for it in items if it["food"]]
    other = [it for it in items if not it["food"]]
    cards_food = "".join(card(it) for it in food[:30])
    cards_other = "".join(card(it) for it in other[:40])
    co_rows_html = "".join(
        f'<tr data-hood="{k.esc(c["hood"])}"><td>{k.esc(k.nice_date(c["day"]))}</td><td>{k.esc(c["hood"])}</td><td>{k.esc(c["name"] or "—")}</td>'
        f'<td>{k.esc(k.titleish(c["addr"]))}</td><td>{k.esc(c["use"] or "—")}</td><td>{k.esc(c["change"] or "—")}</td></tr>'
        for c in co_list[:40])
    liq_html = "".join(
        f'<tr data-hood="{k.esc(hood_of(r.get("ANC")))}"><td>{k.esc(r["TRADE_NAME"] or "—")}</td><td>{k.esc(hood_of(r.get("ANC")))}</td>'
        f'<td>{k.esc(r["TYPE"] or "")}</td><td>{k.esc(k.titleish(r["ADDRESS"] or ""))}</td><td>{k.esc(r["LICENSE"])}</td></tr>'
        for r in liq_top)
    per_hood = {h: sum(1 for it in items if it["hood"] == h) for h, _ in HOODS}
    chips = f'<button type="button" class="chip on" data-f="">All ({len(items)})</button>' + "".join(
        f'<button type="button" class="chip" data-f="{k.esc(h)}">{k.esc(h)} ({per_hood[h]})</button>' for h, _ in HOODS)
    anc_list = "; ".join(f"{h}: ANC {', '.join(a)}" for h, a in HOODS)

    body = f"""
<div class="grid">
  <div class="card stat"><span class="muted">Storefront-type licenses issued</span><b>{len(items)}</b><span class="muted">last {WINDOW_DAYS} days, four neighborhoods</span></div>
  <div class="card stat"><span class="muted">Food &amp; drink</span><b>{len(food)}</b><span class="muted">restaurants, delis, caterers, grocers</span></div>
  <div class="card stat"><span class="muted">Spaces cleared for a new use</span><b>{len(co_list)}</b><span class="muted">non-residential certificates of occupancy</span></div>
  <div class="card stat"><span class="muted">All new business licenses</span><b>{total_new}</b><span class="muted">incl. rentals, contractors</span></div>
</div>

<nav class="chips" aria-label="Filter by neighborhood">{chips}</nav>

<section class="featured card" aria-label="Featured listing (paid)">
  <span class="feat">Featured</span>
  <h3>[Your business here]</h3>
  <p class="muted" style="margin:.2rem 0 .4rem">[Address] · [Opening date]</p>
  <p style="margin:0">Opening soon? A one-time spotlight puts your photo, hours and opening-day offer at the top of this page and in the weekly email. Featured listings are always labeled.</p>
</section>

<section class="card">
  <h2>Food &amp; drink: license issued</h2>
  <p class="muted" style="margin-top:0">New food-service business licenses, newest first. A license is a step toward opening, not proof a place is open.</p>
  <div class="cards">{cards_food or '<p class="muted">No new food-service licenses in this window.</p>'}</div>
</section>

<section class="card">
  <h2>Shops &amp; services: license issued</h2>
  <p class="muted" style="margin-top:0">Other storefront-type licenses, newest first{f" (first 40 of {len(other)})" if len(other) > 40 else ""}. Some will be offices or online businesses registered at a commercial or mailbox address.</p>
  <div class="cards">{cards_other or '<p class="muted">None in this window.</p>'}</div>
</section>

<section class="card">
  <h2>Spaces cleared for a new use</h2>
  <p class="muted" style="margin-top:0">Non-residential certificates of occupancy DOB issued in the last {WINDOW_DAYS} days. A new certificate often comes shortly before a new tenant opens, or after an ownership change.</p>
  <div class="scroll"><table><thead><tr><th>Issued</th><th>Area</th><th>Trading as</th><th>Address</th><th>Approved use</th><th>Change</th></tr></thead>
  <tbody>{co_rows_html or '<tr><td colspan="6" class="muted">None in this window.</td></tr>'}</tbody></table></div>
</section>

<section class="card">
  <h2>Liquor licenses: newest on file</h2>
  <p class="muted" style="margin-top:0">ABCA's open dataset has no issue dates and is a periodic snapshot (latest: {k.nice_date(k.day(snap)) if snap else "unknown"}), so it can't show the last {WINDOW_DAYS} days. These are the highest-numbered active licenses in these ANCs in that snapshot, a rough proxy for the newest.</p>
  <div class="scroll"><table><thead><tr><th>Trade name</th><th>Area</th><th>Type</th><th>Address</th><th>License</th></tr></thead>
  <tbody>{liq_html or '<tr><td colspan="5" class="muted">No records.</td></tr>'}</tbody></table></div>
</section>
<p class="muted" style="font-size:.8rem">Areas are matched by ANC: {k.esc(anc_list)}.</p>

<script>
(() => {{
  const chips = document.querySelectorAll(".chip");
  chips.forEach(c => c.addEventListener("click", () => {{
    chips.forEach(x => x.classList.toggle("on", x === c));
    const f = c.dataset.f;
    document.querySelectorAll("[data-hood]").forEach(el => {{ el.hidden = !!f && el.dataset.hood !== f; }});
  }}));
}})();
</script>
"""
    extra_css = """
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.chip{font:inherit;font-size:.82rem;padding:.3rem .75rem;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.chip.on{background:var(--accent);border-color:var(--accent);color:var(--card)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.biz{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--bg);min-width:0}
.biz[hidden],tr[hidden]{display:none}
.biz.food{border-left:4px solid var(--brick)}
.biz h3{margin:.15rem 0 .1rem;font-size:1.02rem;overflow-wrap:anywhere}
.biz .cat{font-size:.68rem;text-transform:uppercase;letter-spacing:.07em;color:var(--brick);font-weight:700}
.biz .addr{margin:0;font-size:.85rem;color:var(--muted)}
.biz .acts{margin:.3rem 0;font-size:.82rem}
.pipe{list-style:none;padding:0;margin:.4rem 0;font-size:.8rem}
.pipe li{padding-left:16px;position:relative;margin:2px 0}
.pipe li:before{content:"";position:absolute;left:2px;top:.45em;width:8px;height:8px;border-radius:50%;border:1.5px solid var(--accent)}
.pipe li.done:before{background:var(--accent)}.pipe li.todo{color:var(--muted)}
.claim{font-size:.8rem}
.featured{border:2px solid var(--gold)}
.featured .feat{display:inline-block;font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);border:1px solid var(--gold);border-radius:999px;padding:1px 8px}
.featured h3{margin:.4rem 0 0}
"""
    values = k.base_values(RANK, IDEA_ID, SCORE, "live", pulled)
    values.update({
        "SHORT_NAME": "Grand Opening Spotlight",
        "EXTRA_CSS": extra_css,
        "EYEBROW": f"New business licenses · last {WINDOW_DAYS} days",
        "HEADLINE": "What's coming to the neighborhood",
        "DECK": f"{len(items)} storefront-type business licenses issued in Adams Morgan, Petworth, Tenleytown/Friendship Heights and SW Waterfront in the last {WINDOW_DAYS} days, {len(food)} of them for food and drink, plus every commercial space DC cleared for a new use.",
        "BODY": body,
        "PITCH": "An automatically built list of new businesses from license and occupancy records, with a $49–149 paid \"Featured\" spotlight for owners who want to announce their opening. Items are labeled by the record that exists (\"license issued\"), never \"opened\".",
        "WHATS_REAL": f"Every listing. This run pulled {total_new} Basic Business Licenses first issued in the last {WINDOW_DAYS} days in these ANCs ({k.esc(anc_list)}) and kept {len(items)} storefront-type businesses (food, retail and services). {dropped_home} were dropped as likely home-based: an apartment address, an address DC's address registry marks as residential, or a sole proprietor with no trade name (whose legal name is a person's name and is never shown). It also pulled {len(co_list)} non-residential certificates of occupancy inside the same ANC boundaries and the newest active ABCA liquor licenses there.",
        "WHATS_MOCKED": "The Featured card and the \"Claim this listing\" links are placeholders. The liquor-license section is from ABCA's latest open snapshot, not the last 60 days, because that dataset has no issue dates. Matching by ANC is approximate at neighborhood edges, and grouping licenses into one business by address and name is automatic.",
        "NEXT_STEPS": "Track ABCA placard notices and hearing agendas for true liquor-license dates; add DC Health food inspections when a bulk feed exists; review items weekly before the email goes out; build the claim form and a checkout for spotlights; match by neighborhood polygon once license coordinates are published at full precision (they are rounded to whole degrees today).",
        "SOURCES": f'<a href="{bbl}">Basic Business Licenses (DLCP)</a>, <a href="{co_layer}">Certificate of Occupancy (DOB)</a>, <a href="{abca}">Alcohol License Business Locations (ABCA)</a>, ANC boundaries via Open Data DC',
    })
    k.write(OUT, k.fill(values))
    print(f"{total_new} new licenses, {len(items)} kept ({len(food)} food), {len(co_list)} COs, {len(liq)} ABCA, snapshot {k.day(snap) if snap else None}, per hood {per_hood}")


if __name__ == "__main__":
    main()
