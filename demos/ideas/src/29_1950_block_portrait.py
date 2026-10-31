"""Demo #29 (culture-content#8): 1950 Block Portrait.

    python demos/ideas/src/29_1950_block_portrait.py

The 1950 census has no per-block statistics API: the real build means transcribing the non-name
columns of NARA's population schedules for each enumeration district. So every chart here is drawn
from clearly labeled SAMPLE figures. No network calls, no names, ever.
"""

from __future__ import annotations

import html
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "demos" / "ideas" / "29-1950-block-portrait.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

NARA = "https://1950census.archives.gov/"
NARA_ABOUT = "https://1950census.archives.gov/about/"
NARA_RECORDS = "https://www.archives.gov/research/census/1950"
AWS = "https://registry.opendata.aws/nara-1950-census/"
MORSE = "https://stevemorse.org/census/faq1950.htm"

BLOCK = "400 block of Upshur Street NW"
HOOD = "Petworth"

# ---- SAMPLE figures: plausible, invented for layout. Not facts about anyone. ----
SAMPLE_PEOPLE = 118
SAMPLE_HOUSEHOLDS = 33
JOBS = [("Government clerk", 15), ("Laborer", 9), ("Teacher", 6), ("Domestic worker", 6), ("Messenger", 5),
        ("Salesperson", 5), ("Carpenter", 4), ("Nurse", 3)]
BORN = [("District of Columbia", 39), ("Virginia", 22), ("Maryland", 17), ("North Carolina", 11),
        ("Pennsylvania", 6), ("Other states", 18), ("Outside the U.S.", 5)]
AGES = [("0–9", 19), ("10–19", 14), ("20–29", 17), ("30–39", 21), ("40–49", 18), ("50–59", 14), ("60+", 15)]
HH_SIZE = [("1", 3), ("2", 7), ("3", 8), ("4", 7), ("5", 4), ("6+", 4)]

e = html.escape


def bars(rows: list[tuple[str, int]], label_w: int = 128, unit: str = "") -> str:
    W, rh = 380, 26
    H = rh * len(rows) + 6
    mx = max(n for _, n in rows)
    span = W - label_w - 44
    out = []
    for i, (lab, n) in enumerate(rows):
        y = i * rh + 4
        w = max(2, n / mx * span)
        out.append(
            f'<text x="{label_w - 8}" y="{y + 15}" text-anchor="end" class="lab">{e(lab)}</text>'
            f'<rect x="{label_w}" y="{y + 3}" width="{w:.1f}" height="16" rx="2" class="bar"/>'
            f'<text x="{label_w + w + 6:.1f}" y="{y + 15}" class="val">{n}{unit}</text>'
        )
    return (f'<svg viewBox="0 0 {W} {H}" role="img" class="chart" aria-label="Sample chart">'
            f'{"".join(out)}</svg>')


def columns(rows: list[tuple[str, int]]) -> str:
    W, H, pad = 360, 170, 26
    mx = max(n for _, n in rows)
    bw = (W - 20) / len(rows)
    out = []
    for i, (lab, n) in enumerate(rows):
        h = n / mx * (H - pad - 22)
        x = 10 + i * bw
        out.append(
            f'<rect x="{x + 8:.1f}" y="{H - pad - h:.1f}" width="{bw - 16:.1f}" height="{h:.1f}" rx="2" class="bar"/>'
            f'<text x="{x + bw / 2:.1f}" y="{H - pad - h - 5:.1f}" text-anchor="middle" class="val">{n}</text>'
            f'<text x="{x + bw / 2:.1f}" y="{H - 8}" text-anchor="middle" class="lab">{e(lab)}</text>'
        )
    return (f'<svg viewBox="0 0 {W} {H}" role="img" class="chart" aria-label="Sample chart">'
            f'{"".join(out)}</svg>')


def render(fields: dict) -> str:
    out = TEMPLATE.read_text(encoding="utf-8")
    out = re.sub(r"<!--.*?-->\n", "", out, count=1, flags=re.S)
    for k, v in fields.items():
        out = out.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        raise RuntimeError(f"unfilled placeholders: {left}")
    return out


def main() -> None:
    now = time.time()
    assert sum(n for _, n in BORN) == SAMPLE_PEOPLE and sum(n for _, n in AGES) == SAMPLE_PEOPLE
    assert sum(n for _, n in HH_SIZE) == SAMPLE_HOUSEHOLDS
    avg_hh = SAMPLE_PEOPLE / SAMPLE_HOUSEHOLDS
    sample_tag = '<span class="stag">SAMPLE FIGURES</span>'

    body = f"""
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" class="hbg"/><line x1="0" y1="0" x2="0" y2="6" class="hline"/></pattern></defs></svg>
<div class="card ribbon"><b>Every number on this page is a made-up sample</b> that shows the layout. The real figures would come from transcribing NARA's 1950 census sheets for this block's enumeration district.</div>

<div class="card">
  <div class="grid">
    <div class="stat"><b>{SAMPLE_PEOPLE}</b>people counted {sample_tag}</div>
    <div class="stat"><b>{SAMPLE_HOUSEHOLDS}</b>households {sample_tag}</div>
    <div class="stat"><b>{avg_hh:.1f}</b>people per household {sample_tag}</div>
    <div class="stat"><b>Apr 1, 1950</b>census day</div>
  </div>
  <p class="muted small">Enumeration district: <b>1-[###]</b> (looked up from the ED descriptions; placeholder here). Counts only: no names, and any category with fewer than 3 people is folded into "other" before publishing.</p>
</div>

<section class="card">
  <h2>What people did for work {sample_tag}</h2>
  {bars(JOBS)}
  <p class="muted small">From the occupation column, grouped into plain job names. Shown for people with a listed occupation.</p>
</section>

<section class="card">
  <h2>Where they were born {sample_tag}</h2>
  {bars(BORN, label_w=150)}
  <p class="muted small">From the birthplace column (state, or country if born abroad).</p>
</section>

<div class="grid two">
<section class="card">
  <h2>Ages {sample_tag}</h2>
  {columns(AGES)}
</section>
<section class="card">
  <h2>Household size {sample_tag}</h2>
  {columns(HH_SIZE)}
  <p class="muted small">Number of households by people living in them. The product would set this beside today's figure from the Census Bureau's American Community Survey.</p>
</section>
</div>

<section class="card">
  <h2>What the sheets can and can't tell us</h2>
  <ul class="tight">
    <li>Census day was April 1, 1950. Each Form P1 page has a line for each of 30 people, and six people per page were asked extra "sample" questions. <a class="src" href="{NARA_ABOUT}">NARA</a></li>
    <li>Renters versus owners is <b>not</b> available: the housing schedule was on the back of the form, was never microfilmed, and the paper originals no longer exist. <a class="src" href="{NARA_ABOUT}">NARA</a></li>
    <li>The records opened on April 1, 2022, after the 72-year privacy restriction. <a class="src" href="{NARA_RECORDS}">NARA</a></li>
    <li>NARA's own name index was built with AI/OCR and isn't 100 percent accurate. <a class="src" href="{NARA_RECORDS}">NARA</a></li>
  </ul>
  <p><a class="btn" href="{NARA}">See the original sheets at the National Archives →</a></p>
  <p class="muted small">Names stay on NARA's site. This project never transcribes, indexes or displays them. Some people counted in 1950 are still alive.</p>
</section>

<section class="card">
  <h2>How the real version gets built</h2>
  <ol class="steps">
    <li><b>Find the district.</b> Match each block to its 1950 enumeration district using NARA's ED maps and descriptions (<a href="{MORSE}">Steve Morse's 1950 ED tools</a> help).</li>
    <li><b>Download the sheets.</b> NARA publishes every population schedule, ED map and description as open data on AWS, free and with no account. <a class="src" href="{AWS}">AWS Open Data</a></li>
    <li><b>Transcribe only the non-name columns:</b> relationship, age, birthplace, occupation. Run OCR or Claude vision on roughly 200–400 sheets per neighborhood, then spot-check by hand.</li>
    <li><b>Aggregate and suppress.</b> Roll up to block or ED, fold small groups into "other", and publish counts and charts only.</li>
    <li><b>Link out for names.</b> Each portrait links to the matching sheets on NARA's viewer.</li>
  </ol>
</section>

<div class="card sponsor"><div class="label">Partner slot</div><b>[Grant funder or newsroom partner]</b>. A good fit for a humanities grant or a data-journalism partnership.</div>
"""

    extra_css = """
.small{font-size:.84rem}
.ribbon{background:var(--soft);border-color:var(--gold);border-left:4px solid var(--gold);font-size:.92rem}
.stag{display:inline-block;vertical-align:middle;font-size:.6rem;font-weight:700;letter-spacing:.08em;color:var(--sample);border:1px dashed var(--sample);border-radius:4px;padding:0 5px;margin-left:4px}
h2 .stag{vertical-align:3px}
.stat{font-size:.88rem;color:var(--muted)}.stat b{color:var(--ink)}
.chart{width:100%;height:auto;display:block}
.chart .bar{fill:url(#hatch)}
.hbg{fill:var(--accent);opacity:.85}
.hline{stroke:var(--card);stroke-width:2;opacity:.35}
.chart .lab{fill:var(--ink);font-size:13px}
.chart .val{fill:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
.two{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}.two .card{margin:0}
.tight{padding-left:1.1rem;margin:.3rem 0}.tight li{margin:.4rem 0}
.steps{padding-left:1.2rem}.steps li{margin:.5rem 0}
a.src{font-size:.72rem;color:var(--muted);white-space:nowrap}
a.src::before{content:"["}a.src::after{content:"]"}
.btn{display:inline-block;background:var(--accent);color:var(--card);padding:.45rem .9rem;border-radius:8px;text-decoration:none;font-weight:600}
"""

    page = render({
        "IDEA_ID": "culture-content#8",
        "RANK": "29",
        "SCORE": "63.6",
        "SHORT_NAME": "1950 Block Portrait",
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": f"{HOOD} · 1950 Block Portrait",
        "HEADLINE": f"The {BLOCK}, as counted in 1950",
        "DECK": "Jobs, birthplaces, ages and household sizes for one block, from the 1950 census sheets. Charts only. No names, ever.",
        "BODY": body,
        "PITCH": "A per-block statistical portrait built from the 1950 census manuscript schedules, released free in 2022: what people did, where they came from and how they lived. A social-history page for every block, not a people search.",
        "WHATS_REAL": f"The facts about the 1950 census and its records (census day, the Form P1 layout, the missing housing schedule, the 2022 release, NARA's AI/OCR name index, the AWS open-data copy), each linked to NARA or AWS. The block and neighborhood are real places.",
        "WHATS_MOCKED": "Every count and chart. They are invented sample figures that show the layout, because no per-block 1950 statistics exist to query. The enumeration district number is a placeholder.",
        "NEXT_STEPS": "For each neighborhood, map blocks to 1950 enumeration districts, pull those sheets from NARA's AWS bucket, transcribe only the non-name columns with OCR or Claude vision, spot-check, aggregate with small-group suppression, and add today's ACS figures for comparison. Expect 40–80 hours for the first neighborhood.",
        "SOURCES": f'<a href="{NARA}">NARA 1950 Census</a>; <a href="{NARA_RECORDS}">NARA 1950 Census Records</a>; <a href="{AWS}">1950 Census on AWS Open Data</a>; <a href="{MORSE}">Steve Morse 1950 ED FAQ</a>. All charts are sample figures',
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    })
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({len(page.encode()) // 1024} KB)")


if __name__ == "__main__":
    main()
