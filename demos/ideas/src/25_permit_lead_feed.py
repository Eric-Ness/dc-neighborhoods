"""Demo #25: Permit & License Lead Feed (B2B). Writes demos/ideas/25-permit-lead-feed.html.

Citywide DOB building permits issued in the last 7 days, tagged by trade and
filterable in the page. Owner and applicant names are never requested, even
though lead buyers would want them. Addresses are masked to the hundred block
in this public preview.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402
from run import hundred_block, permit_group, yearly_layers  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "25-permit-lead-feed.html"
DAYS = 7
DAY = 86400
SHOW = 50
# Allowlist only. OWNER_NAME and PERMIT_APPLICANT exist in the layer and are deliberately left out.
FIELDS = ["PERMIT_ID", "ISSUE_DATE", "PERMIT_TYPE_NAME", "PERMIT_SUBTYPE_NAME", "PERMIT_CATEGORY_NAME", "FULL_ADDRESS",
          "DESC_OF_WORK", "ZONING", "FEES_PAID", "WARD", "ANC"]
TAGS = [
    ("Roofing", r"\broof|shingle|gutter"),
    ("Solar", r"\bsolar|photovoltaic|\bpv\b"),
    ("HVAC", r"\bhvac|heat pump|furnace|boiler|air condition|\bac unit|mini.?split|ductwork"),
    ("Windows & doors", r"window|door"),
    ("Kitchen & bath", r"kitchen|bath"),
    ("Basement", r"basement|underpin|cellar"),
    ("Deck & porch", r"\bdeck|porch|patio"),
    ("Fence & retaining wall", r"fence|retaining wall"),
    ("Electrical service", r"service upgrade|panel|amp\b|\bev charg|charger"),
    ("Plumbing & water line", r"plumb|water (service|line)|sewer|lead"),
    ("Demolition", r"\bdemo|raze"),
    ("Signs", r"\bsign"),
    ("Restaurant & retail fit-out", r"restaurant|retail|tenant|fit.?out|build.?out"),
]
esc = html.escape


def tags_for(text: str) -> list[str]:
    t = text.lower()
    return [name for name, rx in TAGS if re.search(rx, t)]


def fee_band(v) -> str:
    try:
        v = float(v or 0)
    except (TypeError, ValueError):
        return "Unknown"
    if v <= 0:
        return "Unknown"
    if v < 250:
        return "Under $250"
    if v < 1000:
        return "$250–999"
    if v < 5000:
        return "$1k–5k"
    return "$5k+"


FEE_ORDER = ["$5k+", "$1k–5k", "$250–999", "Under $250", "Unknown"]


def render(fields: dict) -> str:
    t = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    t = re.sub(r"<!--\s*\n\s*Template for idea demos.*?-->\n", "", t, flags=re.S)
    for k, v in fields.items():
        t = t.replace("{{" + k + "}}", v)
    if "{{" in t:
        raise RuntimeError("unfilled placeholder")
    return t


def fetch(layer: str, where: str) -> list[dict]:
    rows, offset = [], 0
    while True:
        data = dcdata._request(f"{layer}/query", {"where": where, "outFields": ",".join(FIELDS), "returnGeometry": "false",
                                                  "orderByFields": "ISSUE_DATE DESC", "resultOffset": offset, "resultRecordCount": 1000, "f": "json"}, post=True)
        batch = [f["attributes"] for f in data.get("features", [])]
        rows += batch
        if not data.get("exceededTransferLimit") or not batch:
            return rows
        offset += len(batch)


def main() -> None:
    now = time.time()
    pulled = time.strftime("%Y-%m-%d", time.gmtime(now))
    start = now - DAYS * DAY
    rows = []
    for layer in yearly_layers("Building Permits in {year}", start, now):
        rows += fetch(layer, dcdata.date_where("ISSUE_DATE", start))
    leads = []
    for r in rows:
        work = re.sub(r"\s+", " ", (r["DESC_OF_WORK"] or "").strip())
        if work.lower() in ("undefined", "null", "none", "n/a"):
            work = ""
        addr = re.sub(r",.*$", "", r["FULL_ADDRESS"] or "")
        masked = hundred_block(re.sub(r"\s+\d{5}$", "", addr)) or ""
        masked = re.sub(r"\b(\d+)(ST|ND|RD|TH)\b", lambda m: m.group(1) + m.group(2).lower(), masked.title() if masked.isupper() else masked)
        masked = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), masked.title()).replace(" Block Of ", " block of ")
        masked = re.sub(r"(?<=\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1).lower(), masked)
        group = permit_group(r["PERMIT_TYPE_NAME"], r["PERMIT_SUBTYPE_NAME"], work)
        leads.append({
            "d": time.strftime("%Y-%m-%d", time.gmtime(r["ISSUE_DATE"] / 1000)),
            "g": group,
            "s": "" if (r["PERMIT_SUBTYPE_NAME"] or "").upper() in ("NA", "N/A") else (r["PERMIT_SUBTYPE_NAME"] or "").capitalize(),
            "a": re.sub(r"\b(NW|NE|SW|SE)\b.*$", r"\1", masked),  # drop unit numbers
            "w": str(r["WARD"] or "").strip(),
            "anc": r["ANC"] or "",
            "f": fee_band(r["FEES_PAID"]),
            "t": tags_for(work + " " + (r["PERMIT_SUBTYPE_NAME"] or "")),
            "x": work[:220] + ("…" if len(work) > 220 else ""),
            "id": r["PERMIT_ID"],
        })
    if not leads:
        raise RuntimeError("no permits in window")
    by_group = Counter(l["g"] for l in leads)
    by_ward = Counter(l["w"] for l in leads if l["w"])
    by_tag = Counter(t for l in leads for t in l["t"])
    by_fee = Counter(l["f"] for l in leads)
    big = sum(1 for l in leads if l["f"] == "$5k+")

    # Ward bars.
    wards = [str(i) for i in range(1, 9)]
    mx = max([by_ward.get(w, 0) for w in wards] + [1])
    ward_bars = "".join(
        f'<rect x="{10 + i * 40}" y="{80 - 64 * by_ward.get(w, 0) / mx:.1f}" width="28" height="{64 * by_ward.get(w, 0) / mx:.1f}" rx="2" fill="var(--accent)"></rect>'
        f'<text x="{24 + i * 40}" y="{74 - 64 * by_ward.get(w, 0) / mx:.1f}" text-anchor="middle" class="v">{by_ward.get(w, 0)}</text>'
        f'<text x="{24 + i * 40}" y="96" text-anchor="middle">W{w}</text>' for i, w in enumerate(wards))
    ward_svg = f'<svg viewBox="0 0 330 100" style="width:100%;max-width:440px;height:auto" role="img" aria-label="Leads by ward">{ward_bars}</svg>'

    opt = lambda vals: "".join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in vals)  # noqa: E731
    group_opts = opt([g for g, _ in by_group.most_common()])
    tag_opts = opt([t for t, _ in by_tag.most_common()])
    ward_opts = opt([w for w in wards if by_ward.get(w)])
    fee_opts = opt([f for f in FEE_ORDER if by_fee.get(f)])
    data_json = json.dumps(leads, separators=(",", ":")).replace("</", "<\\/")
    top_tags = " · ".join(f"{esc(t)} <b>{n}</b>" for t, n in by_tag.most_common(6))
    since = time.strftime("%b %d", time.gmtime(start)).replace(" 0", " ")

    body = f"""
<div class="grid">
  <div class="card stat"><b>{len(leads):,}</b>permits issued citywide since {since}</div>
  <div class="card stat"><b>{by_group.get('New construction', 0) + by_group.get('Additions', 0)}</b>new buildings and additions</div>
  <div class="card stat"><b>{big}</b>with $5k+ in permit fees (bigger jobs)</div>
  <div class="card stat"><b>{by_group.get('Demolition', 0)}</b>demolition and raze permits</div>
</div>

<section class="card">
  <h2>This week's leads</h2>
  <form class="filters" id="f" onsubmit="event.preventDefault()">
    <label>Type<select name="g"><option value="">All types</option>{group_opts}</select></label>
    <label>Trade<select name="t"><option value="">All trades</option>{tag_opts}</select></label>
    <label>Ward<select name="w"><option value="">Citywide</option>{ward_opts}</select></label>
    <label>Fees paid<select name="f"><option value="">Any</option>{fee_opts}</select></label>
    <label class="grow">Keyword<input name="q" type="search" placeholder="e.g. solar, ADU, restaurant"></label>
    <label class="chk"><input type="checkbox" name="desc" checked> Has a description</label>
  </form>
  <p class="muted small" id="count" aria-live="polite"></p>
  <div class="scroll"><table class="leads"><thead><tr><th>Issued</th><th>Lead</th><th>Location <span class="lock">(masked)</span></th><th>Ward</th><th>Fees</th><th>Permit</th></tr></thead><tbody id="rows"></tbody></table></div>
  <p class="muted small">Public preview: addresses are cut to the hundred block and only the first {SHOW} matches are listed. Paid plans get full addresses, every row, CSV and webhook delivery.
  Owner and applicant names are never included, in any plan.</p>
  <div class="actions"><button type="button" disabled title="Demo only">Download CSV (paid)</button><button type="button" disabled title="Demo only">Save this filter as a daily email (paid)</button></div>
</section>

<div class="two">
<section class="card">
  <h2>Where the work is</h2>
  {ward_svg}
  <p class="muted small">Permits issued in the last {DAYS} days by ward.</p>
</section>
<section class="card">
  <h2>Trade signals</h2>
  <p class="small" style="margin-top:0">{top_tags}</p>
  <p class="muted small">Tags come from keywords in DOB's description of work. A permit can carry more than one.</p>
</section>
</div>

<section class="card">
  <h2>Plans</h2>
  <div class="tiers">
    <div class="tier"><h3>Preview</h3><p class="price">Free</p><ul><li>Last 7 days</li><li>Hundred-block locations</li><li>First 50 matches</li></ul></div>
    <div class="tier hot"><h3>Trade</h3><p class="price">$29<span>/month</span></p><ul><li>Full addresses, all rows</li><li>Saved filters, daily email</li><li>CSV export</li></ul></div>
    <div class="tier"><h3>Territory</h3><p class="price">$79<span>/month</span></p><ul><li>Everything in Trade</li><li>Webhook and API</li><li>ABCA license applications (planned)</li></ul></div>
  </div>
  <p class="muted small">Proposed prices. All plans use the same public DOB data; what you pay for is the filtering, tagging and delivery.</p>
</section>

<script id="data" type="application/json">{data_json}</script>
<script>
(function(){{
  var L=JSON.parse(document.getElementById('data').textContent),f=document.getElementById('f'),tb=document.getElementById('rows'),ct=document.getElementById('count');
  function esc(s){{return String(s).replace(/[&<>"]/g,function(c){{return{{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]}})}}
  function run(){{
    var g=f.g.value,t=f.t.value,w=f.w.value,fe=f.f.value,q=f.q.value.trim().toLowerCase(),d=f.desc.checked;
    var m=L.filter(function(l){{return(!g||l.g===g)&&(!t||l.t.indexOf(t)>=0)&&(!w||l.w===w)&&(!fe||l.f===fe)&&(!d||l.x)&&(!q||(l.x+' '+l.s+' '+l.a).toLowerCase().indexOf(q)>=0)}});
    ct.textContent=m.length.toLocaleString()+' matching permit'+(m.length===1?'':'s')+(m.length>{SHOW}?' · showing the newest {SHOW}':'');
    tb.innerHTML=m.slice(0,{SHOW}).map(function(l){{
      return '<tr><td class="nw">'+esc(l.d.slice(5))+'</td><td><b>'+esc(l.g)+'</b>'+(l.t.length?' <span class="tags">'+l.t.map(function(x){{return '<i>'+esc(x)+'</i>'}}).join('')+'</span>':'')+'<br><span class="desc">'+esc(l.x||l.s)+'</span></td><td>'+esc(l.a)+'</td><td>'+esc(l.w)+'</td><td class="nw">'+esc(l.f)+'</td><td class="nw small">'+esc(l.id)+'</td></tr>';
    }}).join('')||'<tr><td colspan="6" class="muted">No permits match these filters.</td></tr>';
  }}
  f.addEventListener('input',run);f.addEventListener('change',run);run();
}})();
</script>
"""
    extra_css = """
.small{font-size:.86rem}
.filters{display:flex;flex-wrap:wrap;gap:10px 12px;align-items:flex-end;margin-bottom:6px}
.filters label{display:flex;flex-direction:column;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);gap:3px;min-width:0}
.filters label.grow{flex:1 1 180px}
.filters label.chk{flex-direction:row;align-items:center;text-transform:none;letter-spacing:0;font-size:.86rem;color:var(--ink)}
.filters select,.filters input[type=search]{font:inherit;font-size:.9rem;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);max-width:100%}
table.leads td{font-size:.86rem}
td.nw,.nw{white-space:nowrap}
.desc{color:var(--muted);font-size:.82rem}
.tags i{font-style:normal;font-size:.68rem;font-weight:600;background:var(--soft);color:var(--accent);border-radius:4px;padding:0 5px;margin-left:4px;white-space:nowrap}
.lock{font-size:.7rem}
.actions{display:flex;flex-wrap:wrap;gap:8px}
.actions button{font:inherit;font-size:.85rem;padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--soft);color:var(--muted)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 14px}
svg text.v{fill:var(--ink);font-weight:600}
.tiers{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.tier{border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.tier.hot{border:2px solid var(--accent)}
.tier h3{margin:0}
.price{font-size:1.6rem;font-weight:700;margin:.2rem 0}.price span{font-size:.85rem;color:var(--muted);font-weight:400}
.tier ul{margin:0;padding-left:1.1rem;font-size:.88rem}
"""
    fields = {
        "IDEA_ID": "monetization#3",
        "RANK": "25",
        "SCORE": "66.1",
        "SHORT_NAME": "Permit Lead Feed",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}",
        "EYEBROW": "For contractors, suppliers &amp; installers",
        "HEADLINE": "New DC permits, sorted into leads",
        "DECK": f"Every building permit DC issued in the last {DAYS} days, tagged by trade and filterable by ward, size and keyword. Refreshed every morning.",
        "BODY": body,
        "EXTRA_CSS": extra_css,
        "PITCH": "A weekly (or daily) feed of new building permits, and later ABCA license applications, sold to contractors, architects, solar and roofing installers, restaurant suppliers and commercial brokers.",
        "WHATS_REAL": (f"All {len(leads):,} rows are DOB building permits issued citywide since {since}, pulled from Open Data DC's 'Building Permits in {time.gmtime(now).tm_year}' layer on {pulled}. "
                       f"The newest issue date in the layer was {max(l['d'] for l in leads)}; DOB posts with a lag of a few days. "
                       "Type groups, trade tags and fee bands are computed by the generator from DOB's own fields (subtype, description of work, fees paid). Filtering runs in your browser over that snapshot."),
        "WHATS_MOCKED": ("Plans, prices, the CSV and saved-filter buttons are mockups. ABCA license-application leads are not included yet (they come from weekly PDFs). "
                         "<b>Owner and applicant names are never shown</b>, even though lead buyers would want them: the generator does not request those fields, and the product would not sell them. "
                         "Addresses are cut to the hundred block in this preview; fees are shown as bands, not exact amounts. Fees paid are a rough proxy for job size, not project value."),
        "NEXT_STEPS": ("Run the same query nightly, keep a 90-day archive, add ABCA weekly-issuance parsing, deliver saved filters by email and webhook, "
                       "take payments through Stripe, and check DOB and ABCA terms before any outreach use."),
        "SOURCES": '<a href="https://opendata.dc.gov/">Open Data DC</a>: Building Permits (DOB); CC BY 4.0',
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
    }
    html_out = render(fields)
    OUT.write_text(html_out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(leads)} leads, {len(html_out) // 1024} KB, groups {dict(by_group)}")


if __name__ == "__main__":
    main()
