"""Demo #27: Domain Lease to a Stakeholder (friendshipheights.org pitch).

A one-page pitch a domain owner would send to a potential lessee. Terms are sample.
The only real figures are data counts read from the nightly ingest output for the
Tenleytown planning area (site/src/data/tenleytown.json), which includes Friendship Heights.
No DC API calls; no traffic numbers, because none have been measured.

Run from the repo root:  python demos/ideas/src/27_domain_lease_pitch.py
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "demos" / "ideas" / "27-domain-lease-pitch.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"
DATA = ROOT / "site" / "src" / "data" / "tenleytown.json"
DOMAIN = "friendshipheights.org"


def nice_date(iso: str) -> str:
    t = time.strptime(iso[:10], "%Y-%m-%d")
    return f"{time.strftime('%b', t)} {t.tm_mday}, {t.tm_year}"


def main() -> int:
    now = time.time()
    d = json.loads(DATA.read_text(encoding="utf-8"))
    asof = nice_date(d["generated_at"])
    permits = len(d["permits"])
    pdays = d["windows"]["permits_days"]
    sr = d["requests"]["total"]
    sdays = d["windows"]["requests_days"]
    sr_types = len(d["requests"]["by_type"])
    smds = len(d["smds"])
    ancs = sorted({s["anc"] for s in d["smds"]})
    top_sr = d["requests"]["by_type"][0]["type"] if d["requests"]["by_type"] else ""

    data_card = f"""
<section class="card" id="data">
  <p class="eyebrow real">Real numbers · nightly ingest of {asof}</p>
  <h2>What the site already knows about the neighborhood</h2>
  <p>The independent data engine behind this domain already runs every night for the Tenleytown planning area, which takes in Friendship Heights. On its last run it pulled:</p>
  <div class="grid">
    <div class="stat"><b>{permits}</b>building permits issued in the last {pdays} days</div>
    <div class="stat"><b>{sr:,}</b>311 requests in the last {sdays} days, across {sr_types} request types</div>
    <div class="stat"><b>{smds}</b>Single Member Districts in ANCs {', '.join(ancs)}</div>
  </div>
  <p class="muted small">The most common 311 request was "{top_sr}". Source: Open Data DC (DOB permits, OUC 311, ANC boundaries), CC BY 4.0.</p>
  <p class="small"><b>Traffic:</b> not measured yet, so we don't quote any. Before signing, a lessee gets whatever real analytics exist; until then, price the lease as a domain, not as an audience.</p>
</section>"""

    terms = [
        ("Redirect", f"{DOMAIN} and www point to your existing website.", "$150 / month", "12 months", "Domain only. No civic page."),
        ("Presented by", f"The independent neighborhood data page stays at {DOMAIN}. Your name sits in a labeled banner and one sponsor block, linking to you.", "$300 / month", "12–24 months", "Recommended. Residents keep the page; you get the address and the association."),
        ("Build &amp; maintain", "A co-branded page: your news and events section, clearly yours, beside the independent data section we maintain.", "$600 / month", "24–36 months", "Includes setup and upkeep of your section's template."),
    ]
    rows = "".join(
        f"<tr><td><b>{n}</b></td><td>{w}</td><td class='n'>{p}</td><td>{t}</td><td class='muted'>{note}</td></tr>" for n, w, p, t, note in terms
    )
    terms_card = f"""
<section class="card" id="terms">
  <p class="eyebrow sam">Sample terms · for discussion</p>
  <h2>Three ways to lease it</h2>
  <div class="scroll"><table>
    <thead><tr><th>Option</th><th>What happens at the address</th><th class="n">Price</th><th>Term</th><th>Notes</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <ul class="small">
    <li>Billed annually in advance; 10% off for a two-year prepay.</li>
    <li>Right of first refusal on renewal, 60 days before the term ends.</li>
    <li>Either side can end the lease with 60 days' notice; prepaid months are refunded pro rata.</li>
    <li>A purchase option can be priced separately. The domain is not for sale outside a lease conversation.</li>
  </ul>
</section>"""

    gets_card = """
<section class="card" id="gets">
  <h2>What the lessee gets</h2>
  <ul class="checks">
    <li>The exact-match <b>.org</b> for the neighborhood name, the one people guess first.</li>
    <li>Redirects or a labeled banner, live within 48 hours of signing.</li>
    <li>Forwarding email addresses at the domain (for example events@), pointing to your inbox.</li>
    <li>A monthly one-paragraph report: visits, top pages, clicks to your site, once analytics are running. Aggregate numbers only.</li>
    <li>The owner keeps the registration, renewals, DNS and security. You never pay registrar fees or worry about expiry.</li>
  </ul>
</section>"""

    rules_card = f"""
<section class="card rules" id="independence">
  <h2>Editorial independence: the rules that come with the lease</h2>
  <ol>
    <li><b>The data stays independent.</b> Permits, 311, zoning and other public-record sections are produced by an automated pipeline from city data. The lessee can't edit, remove, delay or reorder them.</li>
    <li><b>Your content is labeled as yours.</b> Anything the lessee supplies appears under "From [Lessee name]", visually separate from the data.</li>
    <li><b>No paywall on civic data.</b> Public records stay free to read.</li>
    <li><b>No resident data changes hands.</b> No email lists, no tracking pixels for the lessee, no personal data. Aggregate traffic only.</li>
    <li><b>Corrections follow the evidence.</b> Factual errors are fixed when shown, whoever reports them. Complaints about accurate public records are not corrections.</li>
    <li><b>No official airs.</b> The site never implies it is run by DC Government, an ANC or the lessee. Every page carries "{DOMAIN} is leased to [Lessee name]; data sections are independent."</li>
    <li><b>Conflict rule.</b> We won't lease to a political campaign, or to a party with an open case before the BZA or Zoning Commission in the neighborhood, while that case is open.</li>
    <li><b>Clean exit.</b> When the lease ends, the domain reverts and the lessee's content is removed within 7 days. Nothing is held hostage on either side.</li>
  </ol>
</section>"""

    who_card = """
<section class="card" id="who">
  <h2>Who this is for</h2>
  <div class="who">
    <div><b>A business improvement district or main-street group</b><span class="muted">wants the neighborhood name for events and visitor info.</span></div>
    <div><b>A property owner in lease-up</b><span class="muted">wants renters searching the neighborhood to land on a page that mentions them.</span></div>
    <div><b>A residential brokerage</b><span class="muted">wants a local presence that isn't another listing site.</span></div>
    <div><b>A hotel or retail center</b><span class="muted">wants visitors' first search to point their way.</span></div>
  </div>
  <p class="muted small">Categories only. No organization has been approached or has expressed interest.</p>
</section>"""

    banner_card = f"""
<section class="card" id="preview">
  <h2>What "Presented by" looks like</h2>
  <div class="preview">
    <div class="pv-bar"><span>{DOMAIN}</span><span class="muted">Presented by <b>[Lessee name]</b> →</span></div>
    <div class="pv-body">
      <p class="eyebrow">Tenleytown &amp; Friendship Heights · last {pdays} days</p>
      <p><b>{permits}</b> building permits · <b>{sr:,}</b> 311 requests</p>
      <p class="muted small">Data section: independent, from Open Data DC.</p>
      <div class="pv-spon"><span class="muted small">From [Lessee name]</span><br>[Your event, open house or announcement]</div>
    </div>
  </div>
</section>"""

    contact = """
<section class="card cta-card">
  <h2>Next step</h2>
  <p>A 20-minute call to pick an option and a start date. Terms above are a starting point, not a take-it-or-leave-it sheet.</p>
  <p><b>[Owner name]</b> · [owner email] · [phone]</p>
</section>"""

    body = data_card + banner_card + terms_card + gets_card + rules_card + who_card + contact

    extra_css = """
.small{font-size:.84rem}
.eyebrow.real{color:var(--live)}.eyebrow.sam{color:var(--sample)}
#data .grid{margin:.6rem 0}
#data .stat{border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.checks{list-style:none;padding:0;margin:0}
.checks li{padding-left:1.5rem;position:relative;margin:.45rem 0}
.checks li::before{content:"✓";position:absolute;left:0;color:var(--accent);font-weight:700}
.rules{border-left:4px solid var(--accent)}
.rules ol{padding-left:1.3rem;margin:.3rem 0}.rules li{margin:.5rem 0}
.who{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.who div{border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.who b,.who span{display:block}.who span{font-size:.88rem;margin-top:.2rem}
.preview{border:1px solid var(--line);border-radius:10px;overflow:hidden;max-width:520px}
.pv-bar{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px;background:var(--soft);padding:7px 12px;font-size:.85rem;font-weight:600}
.pv-body{padding:10px 14px}.pv-body p{margin:.3rem 0}
.pv-spon{border:1px dashed var(--accent);border-radius:8px;padding:8px 10px;margin-top:.5rem;font-size:.9rem}
.cta-card{background:var(--soft)}
"""

    fill = {
        "IDEA_ID": "monetization#7",
        "RANK": "27",
        "SCORE": "64.2",
        "SHORT_NAME": "Lease friendshipheights.org",
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": f"For lease · {DOMAIN}",
        "HEADLINE": "Lease the neighborhood's .org",
        "DECK": f"{DOMAIN} is available on a one- to three-year lease to one organization that serves Friendship Heights. You get the name people type first. Residents keep an independent page of public data.",
        "BODY": body,
        "PITCH": "Instead of running a business on the domain, rent the domain itself: a one- to three-year lease, or a build-and-maintain deal, to the party that values the name most, with written rules that keep the civic data independent.",
        "WHATS_REAL": (
            f"The three data figures (permits, 311 requests, Single Member Districts) are read from the project's nightly ingest output for the Tenleytown planning area, generated {asof}. "
            "That ingest pulls Open Data DC; this generator makes no API calls of its own."
        ),
        "WHATS_MOCKED": (
            "Everything commercial: prices, terms, discounts, the banner preview, the owner and lessee placeholders. Lessee types are generic categories; no real organization is named or has shown interest. "
            "There are no traffic figures because none have been measured."
        ),
        "NEXT_STEPS": (
            "Point the domain at a live Friendship Heights page for a few months to collect real traffic, draft the lease with a lawyer (the independence rules become contract clauses), "
            "then send this page to two or three candidates by category, one at a time."
        ),
        "SOURCES": f"Project nightly ingest (site/src/data/tenleytown.json, generated {asof}) from Open Data DC: Building Permits (DOB), 311 City Service Requests (OUC), Single Member Districts; CC BY 4.0",
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    }
    page = render(fill)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: data as of {asof}, {len(page)//1024} KB")
    return 0


def render(fill: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    tpl = re.sub(r"<!--\s*Template for idea demos.*?-->\s*", "", tpl, flags=re.S)
    for k, v in fill.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", tpl)
    if left:
        raise RuntimeError(f"unfilled placeholders: {sorted(set(left))}")
    return tpl


if __name__ == "__main__":
    sys.exit(main())
