"""Demo #28: Ask L'Enfant, a grounded visitor concierge (transit-tech#6).

Writes demos/ideas/28-ask-lenfant.html.
No live LLM calls. The page shows a scripted conversation in which every answer cites rows of a small embedded
fact table, and the assistant refuses or defers when the table lacks the fact. A tiny in-page keyword matcher lets
visitors type a question and see which facts would ground the answer (or a refusal).
Live: Capital Bikeshare docks near the station (fact F9). Sample: elevator status and train arrivals.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402

OUT = ROOT / "demos" / "ideas" / "28-ask-lenfant.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

GBFS = "https://gbfs.capitalbikeshare.com/gbfs/gbfs.json"
STATION = (38.8849, -77.0219)
WMATA_INFO = "https://www.wmata.com/ridertools/station/l'enfant-plaza/info"
SHUTTLE = "https://www.wharfdc.com/getting-here/the-wharf-shuttle/"
NASM = "https://www.si.edu/museums/air-and-space-museum"
NMNH = "https://www.si.edu/museums/natural-history-museum"
WHARF = "https://www.wharfdc.com/"

e = html.escape


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": dcdata.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def meters(a, b) -> float:
    p = math.radians
    h = math.sin(p(b[0] - a[0]) / 2) ** 2 + math.cos(p(a[0])) * math.cos(p(b[0])) * math.sin(p(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def walk_min(m: float) -> int:
    return max(1, round(m * 1.3 / 80))


def eastern(now_utc: dt.datetime) -> dt.datetime:
    y = now_utc.year
    mar = dt.datetime(y, 3, 8 + (6 - dt.date(y, 3, 8).weekday()) % 7, 7, tzinfo=dt.timezone.utc)
    nov = dt.datetime(y, 11, 1 + (6 - dt.date(y, 11, 1).weekday()) % 7, 6, tzinfo=dt.timezone.utc)
    return (now_utc + dt.timedelta(hours=-4 if mar <= now_utc < nov else -5)).replace(tzinfo=None)


def nearest_docks(n: int = 2):
    feeds = {f["name"]: f["url"] for f in get_json(GBFS)["data"]["en"]["feeds"]}
    info = get_json(feeds["station_information"])["data"]["stations"]
    status = {s["station_id"]: s for s in get_json(feeds["station_status"])["data"]["stations"]}
    rows = []
    for s in info:
        d = meters(STATION, (s["lat"], s["lon"]))
        st = status.get(s["station_id"])
        if st and d <= 700:
            rows.append({"name": s["name"], "m": round(d), "bikes": st.get("num_bikes_available", 0),
                         "docks": st.get("num_docks_available", 0)})
    rows.sort(key=lambda r: r["m"])
    return rows[:n], feeds["station_status"]


def shuttle_today(local: dt.datetime) -> str:
    wd = local.weekday()
    if wd < 5:
        return "Yes. Weekdays it runs 7 a.m. to 7 p.m."
    if wd == 5 and (4, 1) <= (local.month, local.day) <= (10, 31):
        last = " Today is the last Saturday of that season." if (local.month, local.day) == (10, 31) else ""
        return f"Yes, Saturdays 12 to 6 p.m. from April 1 through October 31.{last}"
    return "Not on the published schedule today: it lists weekdays and spring-to-fall Saturdays only. Event-day service gets posted on the shuttle page."


def build() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    local = eastern(now)
    stamp = f"{local:%I:%M %p}".lstrip("0") + f" {local:%b} {local.day}"
    today = local.date().isoformat()
    docks, gbfs_status = nearest_docks()
    nasm_walk = walk_min(meters(STATION, (38.8882, -77.0199)))

    dock_txt = "; ".join(f'{d["name"]} ({d["m"]} m): {d["bikes"]} bikes, {d["docks"]} open docks' for d in docks) or "No docks reported within 700 m"

    # The whole knowledge base. Every answer must cite these ids; anything not here is refused or deferred.
    facts = [
        ("F1", "Station levels", "Green and Yellow trains use upper-level side platforms; Orange, Blue and Silver use a lower-level center platform.",
         "WMATA station page", WMATA_INFO, "verified", today, "line lines level platform green yellow orange blue silver transfer upstairs downstairs"),
        ("F2", "Entrances", "Three street entrances: 7th St/Maryland Ave (Smithsonian Museums, VRE); 9th & D St (L'Enfant Plaza); 7th & D St (USDOT).",
         "WMATA station page", WMATA_INFO, "verified", today, "exit exits entrance entrances street door way out letter"),
        ("F3", "Elevators", "At the 7th St/Maryland Ave entrance: an elevator from street to mezzanine and from the mezzanine to each Green/Yellow platform. At 9th & D St: an elevator linking the upper platform to Branch Ave/Huntington and the lower Blue/Orange platform.",
         "WMATA station page", WMATA_INFO, "verified", today, "elevator elevators stroller wheelchair step-free stairs accessible lift"),
        ("F4", "Elevator status", "All 4 station elevators in service.",
         "WMATA ElevatorIncidents (sample)", "https://developer.wmata.com/", "sample", stamp, "elevator working broken out status outage"),
        ("F5", "Next trains", "Green toward Branch Ave: 4 and 12 min. Silver toward Ashburn: 6 and 18 min.",
         "WMATA Rail Predictions (sample)", "https://developer.wmata.com/", "sample", stamp, "train next when arrival minutes branch green silver ashburn"),
        ("F6", "SW Shuttle", "Free. Mon–Fri 7 a.m.–7 p.m.; Sat 12–6 p.m., Apr 1–Oct 31; no Sunday hours listed. Stops include L'Enfant Plaza Metro & VRE (7th St at Maryland Ave SW) and the National Mall (Independence Ave at 7th St SW, near the Hirshhorn).",
         "Wharf Neighborhood Shuttle page", SHUTTLE, "verified", today, "shuttle bus free wharf ride circulator"),
        ("F7", "Air and Space Museum hours", "10 a.m.–5:30 p.m. daily; closed Dec. 25. A free timed-entry pass is required.",
         "si.edu (via search; direct fetch blocked)", NASM, "verified", today, "air space museum hours open close pass ticket nasm"),
        ("F8", "Walk to Air and Space", f"About {nasm_walk} min on foot from the station, estimated from map distance.",
         "Map-distance estimate", "", "estimate", today, "walk far distance minutes air space"),
        ("F9", "Bikeshare near the station", dock_txt + ".",
         "Capital Bikeshare GBFS", gbfs_status, "live", stamp, "bike bikes bikeshare capital dock cycle"),
    ]
    fact_by = {f[0]: f for f in facts}

    def cite(*ids: str) -> str:
        return "".join(f'<a class="cite {fact_by[i][5]}" href="#{i}">{i}</a>' for i in ids)

    convo = [
        ("I have 3 hours and a stroller. Can we get from the train to the Air and Space Museum without stairs?",
         f"Yes. Use the <b>7th St/Maryland Ave (Smithsonian Museums)</b> entrance: WMATA lists elevators there from each Green/Yellow platform to the mezzanine and from the mezzanine to the street{cite('F3')}. "
         f"All 4 elevators were in service as of {stamp}{cite('F4')}. From there it's about {nasm_walk} minutes on foot{cite('F8')}. "
         f"The museum is open 10 a.m. to 5:30 p.m. and you need a free timed-entry pass, so book one before you go{cite('F7')}.", "grounded"),
        ("Is the Natural History Museum open late tonight?",
         f"I don't have verified hours for the Natural History Museum, so I won't guess. Check <a href=\"{NMNH}\">its si.edu page</a>. "
         f"The only museum hours in my sources are Air and Space{cite('F7')}.", "refused"),
        ("Is the free shuttle running today?",
         f"{e(shuttle_today(local))} It stops at the station (7th St at Maryland Ave SW) and on the Mall near the Hirshhorn{cite('F6')}.", "grounded"),
        ("My kids are done walking. Can we bike back?",
         f"Bikes near the station as of {stamp}: {e(dock_txt)}{cite('F9')}. Check Capital Bikeshare's own rider rules before riding with kids; they aren't in my sources.", "grounded"),
        ("Which exit letter goes to the Spy Museum?",
         f"I don't know that yet. Exit letters at L'Enfant aren't in my verified facts. WMATA names three entrances{cite('F2')}; "
         "we still need to walk the station to say which one is best for the Spy Museum.", "deferred"),
        ("When's the next Green Line to Branch Ave?",
         f"4 minutes, then 12{cite('F5')}. (Demo note: this fact is sample data until the WMATA feed is connected.)", "grounded"),
        ("What's the best crab cake near the Wharf?",
         f"That's outside what I cover: I only answer from cited transit, museum and shuttle facts. <a href=\"{WHARF}\">The Wharf's own site</a> lists its restaurants.", "refused"),
    ]

    chat = []
    for q, a, kind in convo:
        tag = {"grounded": "", "refused": '<span class="kind no">Out of sources</span>', "deferred": '<span class="kind defer">Deferred</span>'}[kind]
        chat.append(f'<div class="msg me">{e(q)}</div><div class="msg bot">{tag}{a}</div>')

    fact_rows = "".join(
        f'<tr id="{fid}"><td><b>{fid}</b></td><td><b>{e(title)}</b><br>{e(text)}</td>'
        f'<td><span class="prov {prov}">{prov}</span><br><span class="muted small">{e(asof)}</span></td>'
        f'<td class="small">{f"<a href=\"{e(url)}\">{e(src)}</a>" if url else e(src)}</td></tr>'
        for fid, title, text, src, url, prov, asof, _ in facts
    )

    kb = json.dumps([{"id": f[0], "t": f[1], "x": f[2], "p": f[5], "k": f[7].split()} for f in facts])

    body = f"""
<div class="chat card">
  <div class="chat-h"><b>Ask L'Enfant</b><span class="muted small">Answers only from the cited facts below · as of {e(stamp)}</span></div>
  <div class="log">{"".join(chat)}</div>
  <form id="ask" class="ask" autocomplete="off">
    <label for="q" class="vh">Ask a question</label>
    <input id="q" placeholder="Try: is there an elevator? / bikes? / museum hours?">
    <button>Ask</button>
  </form>
  <div id="out" class="msg bot" hidden aria-live="polite"></div>
  <p class="small muted">Demo: typed questions are matched to facts by keyword in your browser. No AI model runs on this page.</p>
</div>

<div class="card">
  <h2>What the assistant knows</h2>
  <p class="small muted">The entire knowledge base for this demo. Citations above link to these rows.
  <span class="prov verified">verified</span> from the operator's page,
  <span class="prov live">live</span> pulled at build,
  <span class="prov sample">sample</span> made up for the demo,
  <span class="prov estimate">estimate</span> computed by us.</p>
  <div class="scroll"><table class="facts"><thead><tr><th>Id</th><th>Fact</th><th>Type</th><th>Source</th></tr></thead><tbody>{fact_rows}</tbody></table></div>
</div>

<script>
(function(){{
var KB={kb};
var f=document.getElementById('ask'),q=document.getElementById('q'),o=document.getElementById('out');
function esc(s){{return s.replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}});}}
f.onsubmit=function(ev){{
  ev.preventDefault();
  var w=q.value.toLowerCase().match(/[a-z-]+/g)||[];
  var hits=KB.map(function(r){{return [r,w.filter(function(x){{return r.k.indexOf(x)>=0;}}).length];}}).filter(function(h){{return h[1]>0;}}).sort(function(a,b){{return b[1]-a[1];}}).slice(0,2);
  o.hidden=false;
  if(!hits.length){{o.innerHTML='<span class="kind no">Out of sources</span>I don\\u2019t have a cited fact for that, so I won\\u2019t guess. Try the station, elevators, trains, the shuttle, Air and Space hours, or bikes.';return;}}
  o.innerHTML='Facts that would ground this answer:'+hits.map(function(h){{var r=h[0];return '<div class="hit"><a class="cite '+r.p+'" href="#'+r.id+'">'+r.id+'</a> <b>'+esc(r.t)+':</b> '+esc(r.x)+'</div>';}}).join('')+'<div class="muted small">The real version passes only these rows to the model and requires it to cite them.</div>';
}};
}})();
</script>
"""

    extra_css = """
.chat{padding:0;overflow:hidden}
.chat-h{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--line);background:var(--soft)}
.log{padding:12px 14px;display:flex;flex-direction:column;gap:8px}
.msg{max-width:88%;padding:9px 13px;border-radius:14px;font-size:.94rem;overflow-wrap:anywhere}
.msg.me{align-self:flex-end;background:var(--accent);color:var(--card);border-bottom-right-radius:4px}
.msg.bot{align-self:flex-start;background:var(--soft);border-bottom-left-radius:4px}
#out{margin:0 14px 10px;max-width:none}
.cite{display:inline-block;margin-left:3px;font-size:.68rem;font-weight:700;text-decoration:none;padding:0 5px;border-radius:4px;vertical-align:super;line-height:1.4;border:1px solid currentColor}
.cite.sample,.prov.sample{color:var(--sample)}.cite.live,.prov.live{color:var(--live)}.cite.verified,.prov.verified{color:var(--accent)}.cite.estimate,.prov.estimate{color:var(--muted)}
.prov{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.kind{display:block;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px}
.kind.no{color:var(--up)}.kind.defer{color:var(--gold)}
.ask{display:flex;gap:8px;padding:10px 14px;border-top:1px solid var(--line)}
.ask input{flex:1;min-width:0;padding:10px;font:inherit;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
.ask button{font:inherit;font-weight:600;padding:8px 16px;border:0;border-radius:8px;background:var(--accent);color:var(--card);cursor:pointer}
.chat > p{padding:0 14px}
.hit{margin-top:6px}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.small{font-size:.86rem}
.facts td{font-size:.88rem}
tr:target{background:var(--soft)}
"""

    repl = {
        "IDEA_ID": "transit-tech#6", "RANK": "28", "SCORE": "64.2",
        "SHORT_NAME": "Ask L'Enfant",
        "PROVENANCE_CLASS": "sample", "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": "lenfantplaza.net · Visitor concierge",
        "HEADLINE": "Ask L'Enfant",
        "DECK": "Ask about the station, the Mall and getting around. Every answer shows where it came from, and if we don't know, we say so.",
        "BODY": body, "EXTRA_CSS": extra_css,
        "PITCH": "A chat box for visitors at L'Enfant Plaza that answers combined questions (\"3 hours, a stroller, which museum and how?\") using only a curated, regularly refreshed set of facts, cites each one with its as-of time, and refuses anything outside them.",
        "WHATS_REAL": (
            f"The conversation is scripted, but its facts are real where marked: Capital Bikeshare dock counts (F9) were pulled live at build time; "
            "station levels, entrances and elevators (F1–F3) come from WMATA's station page; the SW Shuttle schedule (F6) from wharfdc.com; "
            "Air and Space hours (F7) from si.edu as shown in search results (si.edu blocked our direct fetch). The shuttle answer is computed for the build date."
        ),
        "WHATS_MOCKED": (
            "No language model runs here: the answers were written by hand to show the intended behavior. Elevator status (F4) and train times (F5) are sample. "
            "The typing box only keyword-matches the fact table. The walk time (F8) is a map-distance estimate."
        ),
        "NEXT_STEPS": (
            "Grounding design: a cron Worker refreshes a small fact store (D1 rows with id, text, source URL, fetched-at, type) from WMATA, NPS, NWS, GBFS, "
            "the shuttle page and per-museum si.edu scrapes. For each question, retrieval (keyword plus Vectorize) picks at most about 8 rows; the model "
            "(Workers AI or the Claude API) gets only those rows and a system prompt requiring a citation id on every sentence, \"I don't know that; check X\" when no row "
            "answers it, and no restaurant, medical or safety advice. A post-check drops any answer whose citations don't exist or whose numbers don't appear in the cited rows. "
            "Log questions that got refusals and add facts for the common ones. Rate-limit per IP to cap inference cost, and keep commerce on the .net domain."
        ),
        "SOURCES": (
            f'<a href="{WMATA_INFO}">WMATA station page</a>, <a href="{SHUTTLE}">Wharf Neighborhood Shuttle</a>, '
            f'<a href="{NASM}">si.edu Air and Space Museum</a>, <a href="{gbfs_status}">Capital Bikeshare GBFS</a> (live)'
        ),
        "GENERATED_UTC": now.strftime("%Y-%m-%d %H:%M UTC"),
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    page = re.sub(r"<!--.*?-->\s*", "", page, count=1, flags=re.S)
    for k, v in repl.items():
        page = page.replace("{{" + k + "}}", v)
    page = page.replace("any ANC, BID or property owner.", "any ANC, BID or property owner. Not affiliated with WMATA or the Smithsonian.")
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page) // 1024} KB, {len(docks)} docks)")


if __name__ == "__main__":
    build()
