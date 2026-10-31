"""Demo #22 (culture-content#4): Then & Now slider gallery.

    python demos/ideas/src/22_then_and_now.py

Fetches two public-domain Library of Congress photos (each embedded only after its live item record
says "No known restrictions"), resized through LOC's IIIF service to stay under 150 KB.
The "now" side has no photo yet, so it is a clearly labeled placeholder; the page is badged sample.
"""

from __future__ import annotations

import base64
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "demos" / "ideas" / "22-then-and-now.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"
UA = "dc-neighborhoods-demo/0.1 (+https://petworth.org)"

PAIRS = [
    {
        "id": "2016829309", "hood": "Petworth", "street": "Petworth School",
        "title": "Petworth School, about 1920",
        "caption": "From the National Photo Company Collection; the Library of Congress titles it simply \"Petworth School.\" "
                   "The reshoot needs the camera position confirmed on site first: match the roofline and window bays, then stand where the photographer stood.",
    },
    {
        "id": "2017825668", "hood": "Friendship Heights", "street": "Chevy Chase, Md. side of the line",
        "title": "Entrance to Friendship Heights, 1942",
        "caption": "Taken by a Farm Security Administration / Office of War Information photographer on the Chevy Chase, Maryland, side of the line. "
                   "The full Library of Congress title names the house in the frame. A matching view taken now would record Friendship Heights as it changes.",
    },
]
PLANNED = [
    ("Adams Morgan", "18th St & Columbia Rd", "searching LOC and DDOT's pre-1973 photo library"),
    ("Tenleytown", "Wisconsin Ave near Tenley Circle", "searching LOC and DDOT's pre-1973 photo library"),
    ("Petworth", "Georgia Ave & Upshur St", "searching LOC National Photo Company negatives"),
]

e = html.escape


def http_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(4 * (attempt + 1))
    raise AssertionError


def loc_photo(item_id: str) -> dict | None:
    rec = json.loads(http_bytes(f"https://www.loc.gov/item/{item_id}/?fo=json&at=item"))["item"]
    rights = rec.get("rights_advisory") or ""
    rights = rights if isinstance(rights, str) else " ".join(rights)
    if "no known restrictions" not in rights.lower():
        print(f"  skip {item_id}: {rights[:80]!r}")
        return None
    big = next((u for u in rec.get("image_url", []) if "v.jpg" in u), None) or rec["image_url"][-1]
    path = big.split("#")[0].split("storage-services/")[1].rsplit(".", 1)[0]
    iiif = f"https://tile.loc.gov/image-services/iiif/{path.replace('/', ':')}/full/640,/0/default.jpg"
    time.sleep(2)
    data = http_bytes(iiif)
    if len(data) > 150 * 1024:
        data = http_bytes(iiif.replace("/full/640,/", "/full/480,/"))
    if len(data) > 150 * 1024:
        return None
    m = re.search(r"#h=(\d+)&w=(\d+)", big)
    ratio = int(m.group(1)) / int(m.group(2)) if m else 0.75
    names = rec.get("contributor_names") or []
    parts = [x.strip() for x in (names[0].split(",") if names else [])]
    parts = [x for x in parts if x and not re.match(r"^(\d|approximately|photographer|creator)", x, re.I)]
    who = f"{parts[1]} {parts[0]}" if len(parts) >= 2 else (parts[0] if parts else "")
    coll = "National Photo Company Collection" if "npco" in rights.lower() or "national photo" in rights.lower() else (
        "FSA/OWI Collection" if "farm security" in rights.lower() else "Prints & Photographs Division")
    time.sleep(2)
    return {
        "data": "data:image/jpeg;base64," + base64.b64encode(data).decode(), "kb": len(data) // 1024,
        "ratio": ratio, "url": f"https://www.loc.gov/item/{item_id}/", "who": who, "coll": coll,
        "date": (rec.get("date") or "")[:4],
    }


def slider(i: int, pair: dict, ph: dict) -> str:
    pct = f"{ph['ratio'] * 100:.2f}%"
    return f"""<section class="card pair" id="pair-{i}">
  <p class="eyebrow">{e(pair['hood'])} · {e(pair['street'])}</p>
  <h2>{e(pair['title'])}</h2>
  <div class="cmp" style="--pos:50%;padding-top:{pct}">
    <img src="{ph['data']}" alt="{e(pair['title'])}, historic photograph" width="640">
    <div class="now" aria-hidden="true"><div class="ph"><b>NOW</b><span>Photo not taken yet</span><span class="muted">Placeholder: a 2026 view from the same spot goes here</span></div></div>
    <div class="handle" aria-hidden="true"><span>‹ ›</span></div>
    <span class="tag then">THEN · {e(ph['date'])}</span><span class="tag nowtag">NOW · placeholder</span>
    <input type="range" min="0" max="100" value="50" aria-label="Drag to compare then and now">
  </div>
  <p class="cap">{e(pair['caption'])}</p>
  <p class="credit">{e(ph['who'] + ', ' if ph['who'] else '')}{e(ph['coll'])}. <a href="{ph['url']}">Library of Congress record</a> · no known restrictions on publication.</p>
</section>"""


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
    cards = []
    for i, pair in enumerate(PAIRS):
        ph = loc_photo(pair["id"])
        if ph:
            cards.append(slider(i, pair, ph))
            print(f"{pair['id']}: {ph['kb']} KB, {ph['who'] or ph['coll']}")
    if not cards:
        raise RuntimeError("no public-domain photos could be embedded")

    planned = "".join(
        f"<li><b>{e(h)}</b> · {e(s)} <span class='muted'>({e(n)})</span></li>" for h, s, n in PLANNED
    )
    chips = "".join(f'<a class="chip" href="#pair-{i}">{e(p["hood"])}</a>' for i, p in enumerate(PAIRS))
    body = f"""
<p class="chips">{chips}<span class="chip off">Adams Morgan · soon</span><span class="chip off">Tenleytown · soon</span></p>
{''.join(cards)}
<section class="card">
  <h2>Next pairs on the list</h2>
  <ul class="tight">{planned}</ul>
  <p class="muted small">Every historic photo must be public domain or marked "no known restrictions" at the source. Images from DC Public Library's Washington Star collection are licensed, so they get a link, not a slider.</p>
</section>
<div class="card sponsor"><div class="label">Prints</div>Framed then-and-now prints of each pair, <b>[price]</b>. Sales support the project. <span class="muted">(Not for sale in this demo.)</span></div>
<script>
document.querySelectorAll('.cmp').forEach(function(c){{
  var r=c.querySelector('input'),drag=false;
  function set(v){{v=Math.max(0,Math.min(100,v));c.style.setProperty('--pos',v+'%');r.value=Math.round(v);}}
  function at(ev){{var b=c.getBoundingClientRect();set((ev.clientX-b.left)/b.width*100);}}
  r.addEventListener('input',function(){{set(+r.value);}});
  c.addEventListener('pointerdown',function(ev){{drag=true;c.setPointerCapture(ev.pointerId);at(ev);r.focus({{preventScroll:true}});}});
  c.addEventListener('pointermove',function(ev){{if(drag)at(ev);}});
  ['pointerup','pointercancel'].forEach(function(t){{c.addEventListener(t,function(){{drag=false;}});}});
}});
</script>
"""

    extra_css = """
.small{font-size:.84rem}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:.2rem 0 0}
.chip{font-size:.82rem;border:1px solid var(--accent);border-radius:999px;padding:3px 11px;text-decoration:none}
.chip.off{border-color:var(--line);color:var(--muted)}
.pair .eyebrow{color:var(--accent)}
.pair h2{font-size:1.25rem;margin:.15rem 0 .7rem}
.cmp{position:relative;width:100%;overflow:hidden;border-radius:8px;background:#222;user-select:none;touch-action:pan-y}
.cmp img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.cmp .now{position:absolute;inset:0;clip-path:inset(0 0 0 var(--pos));background:repeating-linear-gradient(135deg,var(--soft) 0 14px,var(--card) 14px 28px)}
.cmp .ph{position:absolute;top:0;bottom:0;left:var(--pos);right:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;text-align:center;padding:12px;font-size:.85rem;color:var(--ink);overflow:hidden}
.cmp .ph b{font-size:1.4rem;letter-spacing:.12em;color:var(--brick)}
.cmp .handle{position:absolute;top:0;bottom:0;left:var(--pos);width:3px;margin-left:-1.5px;background:#fff;box-shadow:0 0 0 1px rgba(0,0,0,.3);pointer-events:none}
.cmp .handle span{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;color:#222;border-radius:999px;padding:4px 9px;font-weight:700;font-size:.9rem;box-shadow:0 1px 4px rgba(0,0,0,.35)}
.cmp .tag{position:absolute;top:8px;font-size:.68rem;font-weight:700;letter-spacing:.06em;background:rgba(0,0,0,.6);color:#fff;padding:2px 7px;border-radius:4px;pointer-events:none}
.cmp .then{left:8px}.cmp .nowtag{right:8px}
.cmp{cursor:ew-resize}
.cmp input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;pointer-events:none;-webkit-appearance:none;appearance:none}
.cmp input:focus-visible{opacity:.01}
.cmp:focus-within .handle{background:var(--brick)}
.cap{margin:.7rem 0 .3rem}
.credit{font-size:.8rem;color:var(--muted);margin:0}
.tight{padding-left:1.1rem;margin:.3rem 0}.tight li{margin:.3rem 0}
"""

    page = render({
        "IDEA_ID": "culture-content#4",
        "RANK": "22",
        "SCORE": "67.3",
        "SHORT_NAME": "Then & Now",
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": "Then & Now",
        "HEADLINE": "Same street, a century apart",
        "DECK": "Drag the slider to compare a public-domain photo with the same view today. New pairs are added as they're reshot.",
        "BODY": body,
        "PITCH": "Drag-to-compare sliders that pair a public-domain historic photo with a new photo shot from the same spot, organized by street. Then-and-now pairs are among the most shared local-history posts, and the owner's walks become the content pipeline.",
        "WHATS_REAL": f"Both historic photos are real Library of Congress items, fetched and embedded on {time.strftime('%Y-%m-%d', time.gmtime(now))} only after each live record said \"No known restrictions on publication\". The slider works with mouse, touch and keyboard.",
        "WHATS_MOCKED": "The \"now\" side of every pair is a placeholder panel, because the matching photos haven't been taken yet, so the page is badged sample. The camera position for each historic photo is not yet confirmed. The \"next pairs\" list and the print offer are illustrative.",
        "NEXT_STEPS": "Search LOC (National Photo Company, Harris & Ewing, FSA/OWI, HABS) and DDOT's pre-1973 photo library for 15–30 public-domain views per neighborhood, find each camera position, reshoot at the same focal length and season, then publish pairs on a pin map with prints for sale.",
        "SOURCES": 'Library of Congress Prints &amp; Photographs Division (<a href="https://www.loc.gov/rr/print/res/275_npco.html">National Photo Company</a> and <a href="https://www.loc.gov/rr/print/res/071_fsab.html">FSA/OWI</a> rights statements)',
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now)),
        "EXTRA_CSS": extra_css,
    })
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({len(page.encode()) // 1024} KB)")


if __name__ == "__main__":
    main()
