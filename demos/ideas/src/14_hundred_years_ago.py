"""Demo #14 (culture-content#2): "100 Years Ago This Week" from the Evening Star.

    python demos/ideas/src/14_hundred_years_ago.py

Searches the Library of Congress (Chronicling America on loc.gov, no key) for Evening Star pages
printed this calendar week 100 years ago that mention each neighborhood, pulls each page's OCR text,
and clips a sentence or two around the mention. Newspapers this old are public domain.
About 5 searches plus up to 40 page-text fetches per run, spaced out to respect loc.gov rate limits.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "demos" / "ideas" / "14-hundred-years-ago.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

UA = "dc-neighborhoods-demo/0.1 (+https://petworth.org)"
SEARCH = "https://www.loc.gov/collections/chronicling-america/"
STAR = "evening star (washington, d.c.) 1854-1972"
STAR_ITEM = "https://www.loc.gov/item/sn83045462/"
PAGES_PER_PHRASE = 8
SHOW_PER_HOOD = 3

# (display name, search phrases, regex that finds the mention in OCR text, note)
HOODS = [
    ("Petworth", ["Petworth"], r"petworth", ""),
    ("Tenleytown", ["Tenleytown", "Tenley"], r"tenley\s*-?\s*town", ""),
    ("Friendship Heights", ['"Friendship Heights"'], r"friendship\s+heights", ""),
    ("Adams Morgan", ['"Lanier Heights"', '"Kalorama road"'], r"lanier\s+heights|kalorama\s+road",
     'The name "Adams Morgan" didn\'t exist until the 1950s, so this section searches period names inside '
     "today's Adams Morgan: Lanier Heights and Kalorama Road."),
]
# Legal notices (trustee sales, probate) name private individuals and rarely interest readers; skip them.
LEGAL = re.compile(r"\b(trustees?|liber|folio|plat recorded|deed of trust|probate|executor|administratri?x)\b", re.I)
# Items with these words are held back for an editor instead of auto-published: 1920s real-estate ads
# and news often carry segregation language that needs context, not a bare clipping.
HOLD_FOR_REVIEW = re.compile(r"\b(colou?red|negro(es)?|white\s+only|for\s+whites|restricted|race|covenants?)\b", re.I)
NAME_LIST = re.compile(r"\b[A-Z][a-z]+(?: [A-Z]\.)? [A-Z][a-z]+, [a-z]")
ABBREV = {"st", "ave", "n", "s", "e", "w", "mr", "mrs", "dr", "rev", "no", "sts", "jr", "co", "p.m", "a.m",
          "d.c", "nw", "n.w", "ne", "se", "sw", "pl", "rd"}

e = html.escape


def get_json(url: str, params: dict | None = None, tries: int = 4):
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(tries):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
            return json.loads(raw)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))  # loc.gov answers bursts with HTML/429; back off
    raise AssertionError("unreachable")


def week_100_years_ago(today: date) -> tuple[date, date]:
    try:
        then = today.replace(year=today.year - 100)
    except ValueError:  # Feb 29
        then = today.replace(year=today.year - 100, day=28)
    start = then - timedelta(days=(then.weekday() + 1) % 7)  # back to Sunday
    return start, start + timedelta(days=6)


def search(phrase: str, start: date, end: date, retry: bool = True) -> tuple[list[dict], int]:
    data = get_json(SEARCH, {
        "q": phrase,
        "dates": f"{start.isoformat()}/{end.isoformat()}",
        "fa": f"partof_title:{STAR}",
        "fo": "json", "c": PAGES_PER_PHRASE, "at": "results,pagination",
    })
    time.sleep(2)
    results = data.get("results", [])
    if not results and retry:  # loc.gov search sometimes returns an empty page under load; ask once more
        time.sleep(6)
        return search(phrase, start, end, retry=False)
    return results, (data.get("pagination") or {}).get("of", 0)


def page_text(result: dict) -> str:
    wc = result.get("word_coordinates_url") or ""
    seg = urllib.parse.parse_qs(urllib.parse.urlparse(wc).query).get("segment", [""])[0]
    if not seg:
        return ""
    data = get_json("https://tile.loc.gov/text-services/word-coordinates-service",
                    {"segment": seg, "format": "alto_xml", "full_text": 1})
    time.sleep(1.5)
    for v in data.values():
        if isinstance(v, dict):
            return v.get("full_text", "")
    return ""


def clean(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)          # rejoin hyphenated line breaks
    text = text.replace("�", "").replace("­", "")
    text = re.sub(r"[^\x20-\x7E‘-”\n]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


WORD = re.compile(r"^[\"'(“]?[A-Za-z][a-z]*[.,;:!?'\")”]*$|^\$?[\d,.]+[.,;:]?$")


SHORT_OK = {"a", "i", "an", "as", "at", "be", "by", "do", "go", "he", "if", "in", "is", "it", "me", "my", "no", "of",
            "on", "or", "so", "to", "up", "us", "we", "am", "mr", "dr", "st", "n.w", "s.w", "ave", "mrs", "&", "…"}


def legibility(s: str) -> float:
    """1.0 for clean prose; each garbled token costs double, so OCR soup drops fast."""
    toks = s.split()
    bad = 0
    for t in toks:
        core = t.strip(".,;:!?'\"()“”").lower()
        if not WORD.match(t) and t not in ("…", "&"):
            bad += 1
        elif core.isalpha() and len(core) <= 2 and core not in SHORT_OK:
            bad += 1
    return 1 - 2 * bad / max(1, len(toks))


def sentence_end(s: str, start: int) -> int:
    for m in re.finditer(r"[.?!]\s+(?=[A-Z\"“])", s[start:]):
        i = start + m.start()
        prev = re.search(r"([A-Za-z.]+)$", s[:i])
        if prev and (prev.group(1).lower().strip(".") in ABBREV or len(prev.group(1)) == 1):
            continue
        return i
    return -1


def sentence_start(s: str, k: int) -> int:
    """Index just after the last real sentence break before k, or -1."""
    best = -1
    for m in re.finditer(r"[.?!]\s+(?=[A-Z\"“])", s[:k]):
        prev = re.search(r"([A-Za-z.]+)$", s[:m.start()])
        if prev and (prev.group(1).lower().strip(".") in ABBREV or len(prev.group(1)) == 1):
            continue
        best = m.end()
    return best


def snippet(text: str, pattern: str) -> tuple[str, float] | None:
    best = None
    for m in re.finditer(pattern, text, re.I):
        lo, hi = max(0, m.start() - 240), min(len(text), m.end() + 240)
        window = text[lo:hi]
        k = m.start() - lo
        left = sentence_start(window, k)
        if left != -1 and k - left < 220:
            window, k = window[left:], k - left
        else:
            sp = window.find(" ", max(0, k - 160))
            if 0 <= sp < k:
                window, k = "… " + window[sp + 1:], k - sp + 1
        right = sentence_end(window, k + 10)
        if right != -1 and right - k < 240:
            window = window[:right + 1]
        elif len(window) > k + 200:
            window = window[:window.rfind(" ", 0, k + 200)] + " …"
        score = legibility(window)
        if best is None or score > best[1]:
            best = (window.strip(), score)
    return best


def kind_of(s: str) -> str:
    if re.search(r"for sale|for rent|\brooms?\b|\bbath|cash payment|monthly payments|\$\s?[\d,]+ (cash|down)", s, re.I):
        return "Classified / real estate"
    return "News"


def highlight(s: str, pattern: str) -> str:
    out, last = "", 0
    for m in re.finditer(pattern, s, re.I):
        out += e(s[last:m.start()]) + f"<mark>{e(m.group(0))}</mark>"
        last = m.end()
    return out + e(s[last:])


def pick(items: list[dict]) -> list[dict]:
    """Best-reading clips, preferring different days, shown in date order."""
    items = sorted(items, key=lambda i: -i["score"])
    picked, days = [], set()
    for i in items:
        if i["date"] not in days:
            picked.append(i)
            days.add(i["date"])
    for i in items:
        if i not in picked:
            picked.append(i)
    return sorted(picked[:SHOW_PER_HOOD], key=lambda i: i["date"])


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
    today = date.fromtimestamp(now)
    start, end = week_100_years_ago(today)
    if start.month != end.month:
        week_label = f"{start:%B} {start.day} – {end:%B} {end.day}, {end.year}"
    else:
        week_label = f"{start:%B} {start.day}–{end.day}, {end.year}"

    sections, total_items, total_pages, held, skipped_legal = [], 0, 0, 0, 0
    for name, phrases, pattern, note in HOODS:
        results, hits, seen = [], 0, set()
        for phrase in phrases:
            res, n = search(phrase, start, end)
            hits += n
            for r in res:
                if r.get("id") not in seen:
                    seen.add(r.get("id"))
                    results.append(r)
        total_pages += hits
        items, seen_text = [], set()
        for r in results:
            text = clean(page_text(r))
            snip = snippet(text, pattern) if text else None
            if not snip or snip[1] < 0.7 or len(snip[0]) < 50:
                continue
            if len(NAME_LIST.findall(snip[0])) >= 3:  # rosters of private individuals (transfers, guests)
                continue
            key = re.sub(r"[^a-z]", "", snip[0].lower())[:60]
            if key in seen_text:
                continue
            seen_text.add(key)
            if LEGAL.search(snip[0]):
                skipped_legal += 1
                continue
            if HOLD_FOR_REVIEW.search(snip[0]):
                held += 1
                continue
            items.append({
                "date": date.fromisoformat(r["date"]), "page": str(r.get("shelf_id") or "").lstrip("0"),
                "text": snip[0], "score": snip[1], "url": r.get("url") or r.get("id"), "kind": kind_of(snip[0]),
            })
        items = pick(items)
        total_items += len(items)
        print(f"{name}: {hits} pages mention it, {len(items)} clipped")
        lis = "".join(
            f"""<li class="clip">
  <div class="meta"><span class="day">{i['date']:%a}, {i['date']:%b} {i['date'].day}</span> · page {e(i['page'])} · <span class="kind">{e(i['kind'])}</span></div>
  <blockquote><span class="ocr">OCR text</span> {highlight(i['text'], pattern)}</blockquote>
  <a href="{e(i['url'])}">See the page at the Library of Congress →</a>
</li>"""
            for i in items
        ) or '<li class="clip empty">No usable mentions this week. Some weeks a neighborhood just isn\'t in the paper.</li>'
        link = SEARCH + "?" + urllib.parse.urlencode({"q": phrases[0], "dates": f"{start}/{end}", "fa": f"partof_title:{STAR}"})
        more = f'<a href="{e(link)}">search the archive →</a>' if hits else ""
        count = f"{hits} page match{'es' if hits != 1 else ''}" + (f" · {more}" if more else "")
        sections.append(f"""<section class="card hood">
  <h2>{e(name)} <span class="count">{count}</span></h2>
  {f'<p class="muted small">{e(note)}</p>' if note else ''}
  <ul class="clips">{lis}</ul>
</section>""")

    held_txt = (
        f"{held} clipping{'s' if held != 1 else ''} this week {'were' if held != 1 else 'was'} held back for an editor because "
        f"{'they mention' if held != 1 else 'it mentions'} race, covenants or deed restrictions. "
        if held else "No clippings were held back this week. "
    )
    body = f"""
<div class="card masthead">
  <p class="paper">The Evening Star · Washington, D.C.</p>
  <p class="week">{e(week_label)}</p>
  <p class="muted small">Clippings are raw machine-read text (OCR) from scanned pages, lightly cleaned: line-break hyphens rejoined and stray symbols removed. Misspellings are the scanner's, not ours. Tap through to read the real page.</p>
</div>

<div class="card signup"><b>Get it every Sunday.</b> One short email per neighborhood, with what the paper said a century ago. <span class="fake-input">you@example.com</span><span class="btn">Subscribe</span> <span class="muted small">(inactive in this demo)</span></div>

{''.join(sections)}

<div class="card sponsor"><div class="label">This week's issue is supported by</div><b>[Sponsor name]</b>. One labeled slot per issue.</div>

<p class="muted small">{held_txt}Ads and news from the 1920s often carry segregation language, and those items get written context before they run, not a bare clipping. Legal notices (trustee sales, probate) are skipped because they name private individuals{f" ({skipped_legal} this week)" if skipped_legal else ""}.</p>
"""

    extra_css = """
.masthead{text-align:center;border-top:4px double var(--ink);border-bottom:4px double var(--ink);border-radius:0;background:transparent;border-left:0;border-right:0}
.masthead .paper{font-family:Georgia,"Times New Roman",serif;font-size:1.5rem;font-weight:700;margin:.2rem 0 0}
.masthead .week{font-family:Georgia,serif;font-style:italic;margin:.1rem 0 .5rem}
.small{font-size:.84rem}
.hood h2{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px}
.hood .count{font-size:.8rem;font-weight:400;color:var(--muted)}
.clips{list-style:none;margin:0;padding:0}
.clip{padding:.7rem 0;border-top:1px solid var(--line)}
.clip:first-child{border-top:0}
.clip .meta{font-size:.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.clip .day{color:var(--brick);font-weight:700}
.clip blockquote{margin:.4rem 0;font-family:Georgia,"Times New Roman",serif;font-size:1rem;line-height:1.5;border-left:3px solid var(--line);padding-left:.8rem;overflow-wrap:anywhere}
.clip .ocr{font-family:system-ui,sans-serif;font-size:.62rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--muted);color:var(--muted);border-radius:4px;padding:0 4px;vertical-align:2px}
.clip a{font-size:.88rem}
.clip.empty{color:var(--muted);font-size:.92rem}
mark{background:var(--soft);color:var(--ink);font-weight:700;padding:0 2px;border-bottom:2px solid var(--gold)}
.signup{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.fake-input{flex:1 1 160px;border:1px solid var(--line);border-radius:6px;padding:.35rem .6rem;color:var(--muted);background:var(--bg)}
.btn{background:var(--accent);color:var(--card);border-radius:6px;padding:.35rem .9rem;font-weight:600}
"""

    today_s = time.strftime("%Y-%m-%d", time.gmtime(now))
    page = render({
        "IDEA_ID": "culture-content#2",
        "RANK": "14",
        "SCORE": "70.9",
        "SHORT_NAME": "100 Years Ago This Week",
        "PROVENANCE_CLASS": "live",
        "PROVENANCE_TEXT": f"Live data · Library of Congress · pulled {today_s}",
        "EYEBROW": "100 years ago this week",
        "HEADLINE": "What the Evening Star said about your neighborhood",
        "DECK": e(f"Every week, the paper from exactly a century ago, searched for Petworth, Tenleytown, Friendship Heights and the streets that became Adams Morgan. This week: {week_label}."),
        "BODY": body,
        "PITCH": "A weekly column and email that mines the public-domain Evening Star for each neighborhood, 100 years back. The source never runs dry: every January another year of the paper enters the public domain.",
        "WHATS_REAL": f"The searches, page counts and every clipping were pulled from loc.gov on {today_s}: Evening Star pages dated {week_label} that match each neighborhood's search terms. Clippings are the Library's own OCR text around the most legible mention on each page, with only hyphen and symbol clean-up, and each links to its scanned page.",
        "WHATS_MOCKED": "The sign-up box and sponsor slot. In the product an editor would add a one-line plain-English summary and, where needed, historical context to each item. This demo shows raw clippings and simply holds back items that mention race, covenants or deed restrictions.",
        "NEXT_STEPS": "Run weekly in GitHub Actions. Widen each neighborhood's search to more period and street names (Columbia Road, Wisconsin Avenue with Tenley, Georgia Avenue). Have Claude rank items and draft summaries for a 15-minute human review, crop the article image from the page (the LOC word-coordinates service gives the box), then publish to the site and the newsletter.",
        "SOURCES": f'<a href="{STAR_ITEM}">Evening Star (Washington, D.C.), Chronicling America, Library of Congress</a>, public domain; full text via the loc.gov JSON API',
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    })
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT}: {total_items} clippings from {total_pages} matching pages, {held} held, "
          f"{skipped_legal} legal notices skipped ({len(page.encode()) // 1024} KB)")


if __name__ == "__main__":
    main()
