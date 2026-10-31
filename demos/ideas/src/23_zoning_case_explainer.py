"""Demo #23: Zoning Case Explainer (BZA / Zoning Commission watch).

Pulls DC Office of Zoning cases filed since 2024 inside the TENLEYTOWN (includes
Friendship Heights) and PETWORTH planning neighborhoods and writes
demos/ideas/23-zoning-case-explainer.html.

Run from the repo root:  python demos/ideas/src/23_zoning_case_explainer.py
"""

from __future__ import annotations

import html
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "23-zoning-case-explainer.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

BOUNDARY_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
ZONING_CASES = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Planning_Landuse_and_Zoning_WebMercator/MapServer/34"
SINCE = "2024-01-01"
HOODS = [
    ("tenleytown", "Tenleytown &amp; Friendship Heights", "DC_HPN_NAME='TENLEYTOWN'"),
    ("petworth", "Petworth", "DC_HPN_NAME='PETWORTH'"),
]
# CASE_NAME (usually the applicant's name) and OWNERNAME are deliberately not requested.
FIELDS = [
    "CASE_ID", "CASE_NUMBER", "CASEPOINT_URL", "CASE_TYPE", "CASE_TYPE_RELIEF", "PREMISE_ADDRESS", "DATEFILED",
    "DESCRIPTION", "EXISTINGZONING", "REQUESTEDZONING", "ACTION_TAKEN", "BZARELIEFOF", "ANCSMD",
]
IZIS = "https://dcoz.dc.gov/service/interactive-zoning-information-system-izis"

RELIEF_TYPE = {
    "special exception": "A <b>special exception</b>: the Board approves it if the project passes tests already written into the code, such as not unduly hurting neighbors' light, air and privacy.",
    "area variance": "An <b>area variance</b>: permission to break a size or placement rule. The applicant must show something unusual about the property makes the rule a practical difficulty. A harder bar than a special exception.",
    "use variance": "A <b>use variance</b>: permission for a use the zone doesn't allow. The hardest bar to clear.",
    "time extension": "A <b>time extension</b>: more time to start work under an approval already granted.",
    "modification": "A <b>modification</b>: a change to an earlier approval.",
    "modification of significance": "A <b>modification of significance</b>: a bigger change to an earlier approval, which gets a fresh look.",
    "map amendment": "A <b>map amendment</b> (rezoning): changing which zone, and so which height and density rules, apply to these lots.",
    "text amendment": "A <b>text amendment</b>: changing the wording of the zoning rules themselves.",
    "consolidated pud": "A <b>Planned Unit Development</b>: extra height or density in exchange for public benefits, with the design approved in the same case.",
}

RELIEF_OF = [  # (keyword in BZARELIEFOF, plain English)
    ("rear addition", "how far a rear addition may reach past the houses next door"),
    ("rear yard", "the open space required at the back of the lot"),
    ("side yard", "the gap required between the building and the side lot line"),
    ("lot occupancy", "how much of the lot the building may cover"),
    ("parking", "the minimum number of off-street parking spaces"),
    ("penthouse", "the rules for rooftop penthouses"),
    ("setback", "how far a structure must step back from the roof edge or lot line"),
    ("height", "the height or number-of-stories limit"),
    ("stories", "the height or number-of-stories limit"),
    ("matter-of-right uses", "the uses allowed without a hearing (this one needs Board approval)"),
    ("antenna", "the rules for antennas mounted on buildings"),
    ("new residential development", "the standards for new homes in a residential zone"),
    ("residential conversion", "the rules for turning a building into three or more apartments"),
    ("accessory apartment", "the rules for a small second unit, such as a basement apartment"),
    ("alley centerline", "how far a building must sit back from the middle of the alley"),
    ("building area", "the size cap on an accessory building such as a garage"),
    ("garage door", "the garage door height limit"),
    ("accessory structure", "the rules for sheds, garages and other secondary buildings"),
    ("roof top or upper floor", "the rule protecting rooftop features such as cornices and turrets"),
    ("private school", "the conditions for a private school in a residential zone"),
    ("campus plan", "a university campus plan"),
    ("size and layout", "the design rules for parking lots"),
    ("order number", "an earlier Board order"),
]

ZONE_FAMILY = [
    (r"^R-1", "detached houses"),
    (r"^R-2", "detached and semi-detached houses"),
    (r"^R-3", "rowhouses"),
    (r"^RF", "rowhouse flats"),
    (r"^RA", "apartment buildings"),
    (r"^MU", "mixed use: shops below, homes or offices above"),
    (r"^NC", "a neighborhood shopping street"),
    (r"^PDR", "light industry"),
]

STATUS_CLASS = {"Pending": "pending", "Approved": "approved"}


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def nice_date(ms: float) -> str:
    t = time.gmtime(ms / 1000)
    return f"{time.strftime('%b', t)} {t.tm_mday}, {t.tm_year}"


def clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("�", "§")).strip()


def tidy_addr(a: str) -> str:
    out = a.title()
    out = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), out)
    return re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), out)


def zone_gloss(z: str) -> str:
    for pat, txt in ZONE_FAMILY:
        if re.match(pat, z):
            return txt
    return ""


def relief_of_gloss(text: str) -> str:
    t = text.lower()
    for kw, plain in RELIEF_OF:
        if kw in t:
            return plain
    return ""


def group_cases(rows: list[dict]) -> list[dict]:
    by = defaultdict(list)
    for r in rows:
        by[r["CASE_ID"]].append(r)
    cases = []
    for cid, rs in by.items():
        statuses = Counter(clean(r["ACTION_TAKEN"]) or "Unknown" for r in rs)
        status = "Pending" if "Pending" in statuses else statuses.most_common(1)[0][0]
        addrs = sorted({clean(r["PREMISE_ADDRESS"]) for r in rs} - {"", "NW", "NE", "SW", "SE"}, key=lambda a: (re.sub(r"^\d+\s*", "", a), a))
        types = sorted({clean(r["CASE_TYPE_RELIEF"]).lower() for r in rs if r["CASE_TYPE_RELIEF"]})
        reliefs = []
        for r in rs:
            t = clean(r["BZARELIEFOF"])
            if t and t not in reliefs:
                reliefs.append(t)
        desc = clean(rs[0]["DESCRIPTION"])
        zm = re.search(r"\bin the ([A-Z]{1,3}-[0-9A-Z]+(?:/[A-Z0-9-]+)?) zone", desc)
        zones = sorted({clean(r["EXISTINGZONING"]) for r in rs if r["EXISTINGZONING"]})
        req_zones = sorted({clean(r["REQUESTEDZONING"]) for r in rs if r["REQUESTEDZONING"]})
        cases.append({
            "id": cid,
            "type": clean(rs[0]["CASE_TYPE"]),
            "filed": min(r["DATEFILED"] for r in rs if r["DATEFILED"]),
            "status": status,
            "addresses": addrs,
            "types": types,
            "reliefs": reliefs,
            "desc": desc,
            "zone": zm.group(1) if zm else (zones[0] if len(zones) == 1 else ""),
            "req_zones": req_zones,
            # ANCSMD can hold one SMD repeated many times ("3E04,3E04,..."), so split before de-duplicating.
            "smds": sorted({s.strip() for r in rs if r["ANCSMD"] for s in clean(r["ANCSMD"]).split(",") if s.strip()}),
            "url": clean(rs[0]["CASEPOINT_URL"]) or IZIS,
        })
    cases.sort(key=lambda c: (c["status"] != "Pending", -c["filed"]))
    return cases


def case_card(c: dict) -> str:
    sc = STATUS_CLASS.get(c["status"], "closed")
    body = "BZA" if c["type"] == "BZA" else "Zoning Commission"
    if not c["addresses"]:
        where = "Address not listed in the case record"
    elif len(c["addresses"]) <= 3:
        where = "; ".join(tidy_addr(a) for a in c["addresses"])
    else:
        where = f"{len(c['addresses'])} properties, including " + "; ".join(tidy_addr(a) for a in c["addresses"][:3])
    gl = []
    for t in c["types"]:
        g = RELIEF_TYPE.get(t)
        if g and g not in gl:
            gl.append(g)
    items = []
    for r in c["reliefs"]:
        plain = relief_of_gloss(r)
        items.append(f"<li>{esc(plain[0].upper() + plain[1:]) if plain else esc(r)} <span class='muted small'>({esc(r)})</span></li>")
    zone_txt = ""
    if c["zone"]:
        zg = zone_gloss(c["zone"])
        zone_txt = f"<p class='small'>Zone: <b>{esc(c['zone'])}</b>{' — ' + esc(zg) if zg else ''}.</p>"
    if c["req_zones"]:
        zone_txt += f"<p class='small'>Requested zoning: {esc(', '.join(c['req_zones'][:6]))}{' and more' if len(c['req_zones']) > 6 else ''}.</p>"
    smd = f" · SMD {esc(', '.join(c['smds'][:4]))}{'…' if len(c['smds']) > 4 else ''}" if c["smds"] else ""
    return f"""
<article class="case" data-status="{sc}">
  <header><span class="st {sc}">{esc(c['status'])}</span> <b>{body} case {esc(c['id'])}</b> <span class="muted small">filed {nice_date(c['filed'])}{smd}</span></header>
  <p class="where">{esc(where)}</p>
  <p class="desc">{esc(c['desc'])}</p>
  <div class="plain"><p class="eyebrow">In plain English</p>
    {''.join(f'<p>{g}</p>' for g in gl)}
    {'<p>The rules they want relief from:</p><ul>' + ''.join(items) + '</ul>' if items else ''}
    {zone_txt}
  </div>
  <p class="small"><a href="{esc(c['url'])}">Case record, filings and exhibits on IZIS →</a></p>
</article>"""


def main() -> int:
    now = time.time()
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    where = f"DATEFILED >= TIMESTAMP '{SINCE} 00:00:00'"
    sections, totals = [], {}
    tabs = []
    all_cases = 0
    for slug, label, bwhere in HOODS:
        geom = dcdata.boundary(BOUNDARY_LAYER, bwhere)
        rows = dcdata.query_features(ZONING_CASES, geom, where, FIELDS, "OBJECTID")
        cases = group_cases(rows)
        if not cases:
            raise RuntimeError(f"no zoning cases for {slug}")
        all_cases += len(cases)
        st = Counter(c["status"] for c in cases)
        totals[slug] = (len(cases), st)
        shown = cases[:50]
        cap = f"<p class='muted small'>Showing 50 of {len(cases)} cases.</p>" if len(cases) > 50 else ""
        chips = " · ".join(f"{n} {esc(s.lower())}" for s, n in st.most_common())
        tabs.append(f'<button type="button" data-hood="{slug}" aria-pressed="{"true" if not tabs else "false"}">{label} <span class="muted">({len(cases)})</span></button>')
        sections.append(f"""
<section class="hood" id="{slug}" {'hidden' if sections else ''}>
  <h2>{label}</h2>
  <p class="muted small">{len(cases)} cases filed since {SINCE[:4]}: {chips}.</p>
  {''.join(case_card(c) for c in shown)}
  {cap}
</section>""")

    t_n, t_st = totals["tenleytown"]
    p_n, p_st = totals["petworth"]
    pending = t_st.get("Pending", 0) + p_st.get("Pending", 0)
    stats = f"""
<section class="grid" aria-label="Headline numbers">
  <div class="card stat"><b>{pending}</b>cases still pending</div>
  <div class="card stat"><b>{t_n}</b>Tenleytown &amp; Friendship Heights cases since {SINCE[:4]}</div>
  <div class="card stat"><b>{p_n}</b>Petworth cases since {SINCE[:4]}</div>
</section>
<section class="card hearing">
  <h2>Upcoming hearings</h2>
  <p>The city's zoning-case data doesn't include hearing dates, so we don't guess. Open a pending case below and check its IZIS record for the hearing date, the ANC's report and how to testify.</p>
  <p class="small"><a href="{IZIS}">About IZIS, the Office of Zoning's case system →</a></p>
</section>"""

    body = f"""
{stats}
<div class="tabs" role="group" aria-label="Choose a neighborhood">{''.join(tabs)}</div>
{''.join(sections)}
<section class="card" id="glossary">
  <h2>The two boards, in a sentence each</h2>
  <p><b>BZA</b> (Board of Zoning Adjustment) rules on one property at a time: an addition that's too deep, a use the zone doesn't allow outright.</p>
  <p><b>Zoning Commission</b> writes and changes the rules and the map: rezonings, text changes and large Planned Unit Developments.</p>
</section>
<section class="card sponsor"><span class="label">Presented by</span><br><b>[Sponsor name]</b>: sponsor slot for this page. On a civic page like this, we'd keep land-use firms out of it to avoid a conflict of interest.</section>
"""

    extra_css = """
.small{font-size:.84rem}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 4px}
.tabs button{font:inherit;font-size:.9rem;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:4px 13px;cursor:pointer}
.tabs button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--card)}
.tabs button[aria-pressed=true] .muted{color:inherit}
.hood h2{margin-top:14px}
.case{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.case header{line-height:1.7}
.case .where{font-weight:600;margin:.3rem 0}
.case .desc{margin:.3rem 0;color:var(--muted);font-size:.92rem}
.plain{background:var(--soft);border-radius:8px;padding:8px 12px;margin:.5rem 0;font-size:.93rem}
.plain p{margin:.35rem 0}.plain ul{margin:.2rem 0 .3rem;padding-left:1.2rem}
.plain .eyebrow{color:var(--accent);margin:0}
.st{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;border-radius:999px;padding:1px 9px;border:1px solid currentColor}
.st.pending{color:var(--gold)}.st.approved{color:var(--down)}.st.closed{color:var(--muted)}
.hearing{border-left:4px solid var(--gold)}
"""
    script = """
<script>
(function(){var bs=document.querySelectorAll('.tabs button');bs.forEach(function(b){b.addEventListener('click',function(){bs.forEach(function(o){o.setAttribute('aria-pressed',o===b?'true':'false')});document.querySelectorAll('section.hood').forEach(function(s){s.hidden=s.id!==b.getAttribute('data-hood')})})})})();
</script>"""

    fill = {
        "IDEA_ID": "civic-data#2",
        "RANK": "23",
        "SCORE": "66.7",
        "SHORT_NAME": "Zoning Case Explainer",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "Zoning watch · BZA &amp; Zoning Commission",
        "HEADLINE": f"{pending} zoning cases are still open in Tenleytown, Friendship Heights and Petworth",
        "DECK": f"Every Board of Zoning Adjustment and Zoning Commission case filed since {SINCE[:4]} in these neighborhoods, with what's being asked in plain English and a link to the official record.",
        "BODY": body + script,
        "PITCH": "Every BZA and Zoning Commission case touching the neighborhood gets one plain-English entry: what's requested, its status, which ANC it's in, and where to read the filings and testify.",
        "WHATS_REAL": (
            f"Case numbers, filing dates, status, addresses, ANC/SMD, official descriptions and the specific relief requested come from the Office of Zoning's \"Zoning Cases\" layer, "
            f"queried live on {pulled} inside the DC Health planning-neighborhood boundaries for Tenleytown (which includes Friendship Heights) and Petworth ({all_cases} cases). "
            "Case-name and owner fields, which usually carry the applicant's name, are never requested."
        ),
        "WHATS_MOCKED": (
            "Only the sponsor slot. The \"In plain English\" notes are our generic glosses of the relief type and the rule cited, written once and matched by keyword; they are not legal advice "
            "and are not specific to each case. Hearing dates and ANC votes are not shown because this dataset doesn't carry them."
        ),
        "NEXT_STEPS": (
            "Pull hearing dates from the Office of Zoning's public hearing calendar, link each ANC's filed resolution from IZIS exhibits, "
            "add a small map per case, send a weekly email when a case is filed or decided, and have a human review the gloss on big Zoning Commission cases."
        ),
        "SOURCES": (
            '<a href="https://catalog.data.gov/dataset/weekly-zoning-cases-report">Zoning Cases (DC Office of Zoning)</a>, '
            f'<a href="{IZIS}">IZIS</a>, DC Health Planning Neighborhoods; Open Data DC, CC BY 4.0'
        ),
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    }
    page = render(fill)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: tenleytown {t_n} cases, petworth {p_n} cases, {pending} pending, {len(page)//1024} KB")
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
