"""Demo #6: L'Enfant Transfer Coach (transit-tech#1).

Writes demos/ideas/06-lenfant-transfer-coach.html.
Live: Capital Bikeshare GBFS docks nearest the station (keyless, fetched each run).
Sample: train arrivals and elevator/escalator status (WMATA API key needed).
Station structure (levels, entrances, elevators) comes from WMATA's own pages, linked.
Platform positions, exit letters and walk times are bracketed placeholders until an on-site walk.
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

OUT = ROOT / "demos" / "ideas" / "06-lenfant-transfer-coach.html"
TEMPLATE = ROOT / "demos" / "ideas" / "TEMPLATE.html"

GBFS = "https://gbfs.capitalbikeshare.com/gbfs/gbfs.json"
STATION = (38.8849, -77.0219)  # 650 Maryland Ave SW (WMATA station address), approximate point
WMATA_INFO = "https://www.wmata.com/ridertools/station/l'enfant-plaza/info"
WMATA_WAYFIND = "https://www.wmata.com/ride/accessibility/metro-wayfinding/lenfant-wmata-green-yellow-towards-branch.html"
WMATA_ELEV_HQ = "https://www.wmata.com/ride/accessibility/metro-wayfinding/wmata-lenfant-elevators.html"
WMATA_ELEV_API = "https://developer.wmata.com/docs/services/54763641281d83086473f232/operations/54763641281d830c946a3d76"
WJLA = "https://wjla.com/news/local/metro-unveils-new-wayfinding-system-at-lenfant-plazabut-not-everyone-is-rejoicing"


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": dcdata.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    p = math.radians
    h = math.sin(p(b[0] - a[0]) / 2) ** 2 + math.cos(p(a[0])) * math.cos(p(b[0])) * math.sin(p(b[1] - a[1]) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def walk_min(m: float) -> int:
    # Straight line x1.3 for the street grid, 80 m/min walking pace. A rough estimate, labeled as such.
    return max(1, round(m * 1.3 / 80))


def nearest_docks(n: int = 5) -> tuple[list[dict], str]:
    feeds = {f["name"]: f["url"] for f in get_json(GBFS)["data"]["en"]["feeds"]}
    info = get_json(feeds["station_information"])["data"]["stations"]
    status = {s["station_id"]: s for s in get_json(feeds["station_status"])["data"]["stations"]}
    rows = []
    for s in info:
        d = meters(STATION, (s["lat"], s["lon"]))
        st = status.get(s["station_id"])
        if not st or d > 700:
            continue
        rows.append({
            "name": s["name"], "m": round(d), "cap": s.get("capacity"),
            "bikes": st.get("num_bikes_available", 0), "ebikes": st.get("num_ebikes_available", 0),
            "docks": st.get("num_docks_available", 0), "renting": bool(st.get("is_renting", 1)),
            "reported": st.get("last_reported"),
        })
    rows.sort(key=lambda r: r["m"])
    return rows[:n], feeds["station_status"]


def eastern(now_utc: dt.datetime) -> dt.datetime:
    """US Eastern without tzdata: DST from 2nd Sunday of March 07:00 UTC to 1st Sunday of November 06:00 UTC."""
    y = now_utc.year
    mar = dt.datetime(y, 3, 8 + (6 - dt.date(y, 3, 8).weekday()) % 7, 7, tzinfo=dt.timezone.utc)
    nov = dt.datetime(y, 11, 1 + (6 - dt.date(y, 11, 1).weekday()) % 7, 6, tzinfo=dt.timezone.utc)
    off = -4 if mar <= now_utc < nov else -5
    return (now_utc + dt.timedelta(hours=off)).replace(tzinfo=None)


e = html.escape

LINES = {
    "G": ("Green", "#00a650", "#fff"),
    "Y": ("Yellow", "#ffd200", "#1c2420"),
    "O": ("Orange", "#f7931d", "#1c2420"),
    "B": ("Blue", "#0076c0", "#fff"),
    "S": ("Silver", "#a1a3a1", "#1c2420"),
}

# Direction options. Platform naming follows WMATA's station page ("platform to Branch Ave/Huntington",
# "platform to Greenbelt/Mt. Vernon Sq", "Blue/Orange" lower platform). Terminals are the lines' public endpoints.
DIRS = [
    ("G-S", "G", "Green toward Branch Ave", "upper", "BH"),
    ("G-N", "G", "Green toward Greenbelt", "upper", "GM"),
    ("Y-S", "Y", "Yellow toward Huntington", "upper", "BH"),
    ("Y-N", "Y", "Yellow toward Mt Vernon Sq", "upper", "GM"),
    ("O-W", "O", "Orange toward Vienna", "lower", "W"),
    ("O-E", "O", "Orange toward New Carrollton", "lower", "E"),
    ("B-W", "B", "Blue toward Franconia-Springfield", "lower", "W"),
    ("B-E", "B", "Blue toward Downtown Largo", "lower", "E"),
    ("S-W", "S", "Silver toward Ashburn", "lower", "W"),
    ("S-E", "S", "Silver toward Downtown Largo", "lower", "E"),
]

# Sample arrivals (minutes) per direction. Plausible off-peak headways. NOT live.
SAMPLE_ARR = {
    "G-S": [3, 11, 19], "G-N": [5, 13, 21], "Y-S": [7, 19], "Y-N": [2, 14],
    "O-W": [4, 12, 20], "O-E": [6, 14], "B-W": [9, 21], "B-E": [1, 13],
    "S-W": [8, 20], "S-E": [10, 22],
}

# Sample elevator status, keyed to the four elevators WMATA lists for this station.
ELEVATORS = [
    ("el-street", "7th St/Maryland Ave entrance: street to mezzanine", "ok"),
    ("el-bh", "7th St/Maryland Ave: mezzanine to Branch Ave/Huntington platform", "ok"),
    ("el-gm", "7th St/Maryland Ave: mezzanine to Greenbelt/Mt Vernon Sq platform", "out"),
    ("el-9d", "9th & D St: mezzanine/upper platform (Branch Ave/Huntington) to lower Blue/Orange platform", "ok"),
]

ENTRANCES = [
    {
        "name": "7th St / Maryland Ave · Smithsonian Museums · VRE",
        "letter": "[Exit letter — verify on site]",
        "lift": "Elevator street ↔ mezzanine (WMATA lists it)",
        "near": [("Smithsonian museums on the Mall", (38.8882, -77.0199)), ("VRE platform", None),
                 ("Free SW Shuttle stop (7th St at Maryland Ave)", None)],
        "slug": "[a]",
    },
    {
        "name": "9th & D St · L'Enfant Plaza entrance",
        "letter": "[Exit letter — verify on site]",
        "lift": "Escalators street ↔ mezzanine; elevator inside links upper and lower platforms",
        "near": [("International Spy Museum", (38.8840, -77.0254)), ("L'Enfant Plaza shops", None)],
        "slug": "[b]",
    },
    {
        "name": "7th & D St · USDOT entrance",
        "letter": "[Exit letter — verify on site]",
        "lift": "Escalators street ↔ mezzanine (WMATA's step-by-step route uses a ramp at street level)",
        "near": [("7th & D St SW corner", (38.8838, -77.0219)), ("Federal offices on D St SW", None)],
        "slug": "[c]",
    },
]


def transfer_steps() -> dict:
    """Plain-language steps for each from->to pair. Verified structure from WMATA; unverified details bracketed."""
    out = {}
    for fid, fl, flabel, flev, fplat in DIRS:
        for tid, tl, tlabel, tlev, tplat in DIRS:
            if fid == tid:
                continue
            steps: list[str] = []
            free: list[str] = []
            mins = ""
            if flev == "upper" and tlev == "upper":
                if fplat == tplat:
                    steps = [
                        "Stay where you are. Green and Yellow trains going your way use the <b>same side platform</b>.",
                        f"Watch the platform sign for the next {e(tlabel.split(' toward ')[0])} train toward {e(tlabel.split(' toward ')[1])}.",
                    ]
                    free = ["No level change needed."]
                    mins = "0 min walk"
                else:
                    steps = [
                        "You need the <b>other</b> upper-level side platform (across the tracks).",
                        "Walk to the end of the platform and take the escalator <b>up</b> to the mezzanine that crosses over the Green/Yellow tracks.",
                        "Cross over, then take the escalator <b>down</b> to the opposite side platform.",
                        "[Which platform end is closer — verify on site]",
                    ]
                    free = [
                        "Take the elevator from your platform up to the mezzanine at the 7th St/Maryland Ave end, then the elevator down to the other platform.",
                        "[Elevator positions on the platform — verify on site]",
                    ]
                    mins = "[~3–4 min — time on site]"
            elif flev == "upper" and tlev == "lower":
                steps = [
                    "You're on the <b>upper level</b> (Green/Yellow side platform). Orange, Blue and Silver use the <b>lower level</b> center platform.",
                    "Follow signs for Orange/Blue/Silver to the escalators down. [Which escalator bank, which end of the platform — verify on site]",
                    f"On the lower platform, board on the side signed for {e(tlabel.split(' toward ')[1])}. [Which side — verify on site]",
                ]
                free = (
                    ["From the Branch Ave/Huntington side, WMATA lists an elevator at the 9th & D St end linking this platform to the lower Blue/Orange platform."]
                    if fplat == "BH" else
                    ["From the Greenbelt/Mt Vernon Sq side: elevator up to the mezzanine at the 7th St/Maryland Ave end, then follow signs to the lower platform elevator. [Exact route — verify on site]"]
                )
                mins = "[~2–4 min — time on site]"
            elif flev == "lower" and tlev == "upper":
                steps = [
                    "You're on the <b>lower level</b> center platform. Green and Yellow are <b>upstairs</b> on side platforms.",
                    f"Take the escalator up and follow signs for the platform to <b>{'Branch Ave/Huntington' if tplat == 'BH' else 'Greenbelt/Mt Vernon Sq'}</b>. [Which escalator bank — verify on site]",
                    "Green and Yellow going the same way share that platform; check the sign for your line.",
                ]
                free = (
                    ["WMATA lists an elevator at the 9th & D St end that runs from the lower Blue/Orange platform to the Branch Ave/Huntington platform."]
                    if tplat == "BH" else
                    ["Elevator to the mezzanine, then the Greenbelt/Mt Vernon Sq platform elevator at the 7th St/Maryland Ave end. [Exact route — verify on site]"]
                )
                mins = "[~2–4 min — time on site]"
            else:
                same_side = fplat == tplat
                steps = [
                    "Orange, Blue and Silver all share the <b>lower-level center platform</b>.",
                    ("Stay on your side of the platform; trains going your way stop here." if same_side
                     else "Cross to the <b>other side</b> of the same island platform. No stairs."),
                ]
                free = ["No level change needed."]
                mins = "0–1 min walk"
            uses_gm = (flev == "upper" and tlev == "upper" and fplat != tplat) or (fplat == "GM" and tlev == "lower") or (flev == "lower" and tplat == "GM")
            out[f"{fid}>{tid}"] = {"steps": steps, "free": free, "mins": mins, "gm": uses_gm}
    return out


def line_dot(code: str) -> str:
    name, bg, fg = LINES[code]
    return f'<span class="ln" style="background:{bg};color:{fg}" title="{name} Line">{code}</span>'


def build() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    local = eastern(now)
    docks, status_url = nearest_docks()

    steps = transfer_steps()
    opts = "".join(f'<option value="{d[0]}">{e(d[2])}</option>' for d in DIRS)
    arrivals_js = json.dumps({k: v for k, v in SAMPLE_ARR.items()})
    labels_js = json.dumps({d[0]: d[2] for d in DIRS})
    lines_js = json.dumps({d[0]: [d[1], LINES[d[1]][1], LINES[d[1]][2]] for d in DIRS})
    elev_js = json.dumps({k: s for k, _, s in ELEVATORS})

    elev_rows = "".join(
        f'<li class="{s}"><span class="dot"></span>{e(label)} <em>{"Out of service (sample)" if s == "out" else "Running (sample)"}</em></li>'
        for _, label, s in ELEVATORS
    )

    exit_cards = []
    for ent in ENTRANCES:
        near = []
        for name, pt in ent["near"]:
            w = f' · ~{walk_min(meters(STATION, pt))} min walk (est.)' if pt else ""
            near.append(f"<li>{e(name)}{w}</li>")
        exit_cards.append(
            f'<div class="exit"><div class="exit-h"><span class="letter">{e(ent["letter"])}</span>'
            f'<b>{e(ent["name"])}</b></div><p class="muted small">{e(ent["lift"])}</p><ul>{"".join(near)}</ul>'
            f'<p class="small muted">Short link: lenfantplaza.org/{e(ent["slug"])} (planned)</p></div>'
        )

    if docks:
        dock_rows = "".join(
            f'<tr><td>{e(d["name"])}</td><td class="n">{d["m"]} m</td><td class="n"><b>{d["bikes"]}</b>'
            f'{f" <span class=muted>({d["ebikes"]} e)</span>" if d["ebikes"] else ""}</td><td class="n">{d["docks"]}</td></tr>'
            for d in docks
        )
        dock_html = (
            f'<div class="scroll"><table><thead><tr><th>Dock</th><th class="n">From station</th><th class="n">Bikes</th>'
            f'<th class="n">Open docks</th></tr></thead><tbody>{dock_rows}</tbody></table></div>'
        )
    else:
        dock_html = "<p>No Capital Bikeshare docks reported within 700 m right now.</p>"

    body = f"""
<div class="card coach" id="coach">
  <div class="tabs" role="tablist">
    <button role="tab" aria-selected="true" data-tab="t-transfer">Transfer</button>
    <button role="tab" aria-selected="false" data-tab="t-exits">Exits</button>
    <button role="tab" aria-selected="false" data-tab="t-bikes">Bikes</button>
  </div>

  <section id="t-transfer" class="tab">
    <label class="pick">I'm on <select id="from">{opts}</select></label>
    <label class="pick">heading to <select id="to">{opts}</select></label>
    <div id="result" aria-live="polite"></div>
  </section>

  <section id="t-exits" class="tab" hidden>
    <p class="small">WMATA lists three street entrances. Lettered exit signs are being piloted here
    (<a href="{WJLA}">WJLA</a>); the letters below are placeholders until we walk the station.</p>
    {"".join(exit_cards)}
  </section>

  <section id="t-bikes" class="tab" hidden>
    <p class="small"><span class="badge live">Live</span> Capital Bikeshare docks within 700 m, as of {local:%I:%M %p}
    on {local:%a %b} {local.day} (DC time, when this page was built).</p>
    {dock_html}
  </section>
</div>

<div class="card">
  <h2>Elevators today <span class="badge sample">sample</span></h2>
  <ul class="elev">{elev_rows}</ul>
  <p class="small muted">WMATA lists four elevators at this station (<a href="{WMATA_INFO}">station page</a>).
  The real page reads WMATA's <a href="{WMATA_ELEV_API}">ElevatorIncidents</a> feed every minute and re-routes the step-free steps above.</p>
</div>

<div class="card warn">
  <b>Last verified on site:</b> not yet. Platform ends, escalator banks, exit letters and walk times shown
  in [brackets] need an in-person walk before launch. Station layout facts (upper Green/Yellow side platforms,
  lower Orange/Blue/Silver center platform, the three entrances, the four elevators) are from WMATA's
  <a href="{WMATA_INFO}">station page</a> and <a href="{WMATA_WAYFIND}">step-by-step wayfinding</a>.
</div>

<script>
(function(){{
var S={json.dumps(steps)},A={arrivals_js},L={labels_js},C={lines_js},E={elev_js};
var f=document.getElementById('from'),t=document.getElementById('to'),r=document.getElementById('result');
f.value='G-S';t.value='S-W';
function dot(id){{var c=C[id];return '<span class="ln" style="background:'+c[1]+';color:'+c[2]+'">'+c[0]+'</span>';}}
function render(){{
  if(f.value===t.value){{r.innerHTML='<p class="muted">Pick a different line or direction to transfer to.</p>';return;}}
  var s=S[f.value+'>'+t.value],a=A[t.value];
  var h='<div class="route">'+dot(f.value)+' <span class="arrow">→</span> '+dot(t.value)+' <b>'+L[t.value]+'</b> <span class="mins">'+s.mins+'</span></div>';
  h+='<ol class="steps">'+s.steps.map(function(x){{return '<li>'+x+'</li>';}}).join('')+'</ol>';
  h+='<div class="free"><b>Step-free:</b> '+s.free.join(' ')+(s.gm&&E['el-gm']==='out'?' <span class="alert">Sample alert: the mezzanine–Greenbelt/Mt Vernon Sq platform elevator is out. Plan B: ride one stop and back, or ask the station manager. [Plan B wording — confirm with WMATA guidance]</span>':'')+'</div>';
  h+='<div class="board"><div class="board-h">Next '+L[t.value]+' <span class="badge sample">sample</span></div>'+a.map(function(m){{return '<span class="min">'+(m<=1?'ARR':m+' min')+'</span>';}}).join('')+'</div>';
  r.innerHTML=h;
}}
f.onchange=t.onchange=render;render();
var tabs=document.querySelectorAll('[data-tab]');
tabs.forEach(function(b){{b.onclick=function(){{tabs.forEach(function(x){{x.setAttribute('aria-selected',x===b);document.getElementById(x.dataset.tab).hidden=(x!==b);}});}};}});
}})();
</script>
"""

    extra_css = """
.coach{padding:0;overflow:hidden}
.tabs{display:flex;border-bottom:1px solid var(--line);background:var(--soft)}
.tabs button{flex:1;padding:12px 8px;border:0;background:none;font:inherit;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent}
.tabs button[aria-selected=true]{color:var(--ink);border-bottom-color:var(--accent)}
.tab{padding:16px 18px}
.pick{display:block;margin:0 0 10px;font-weight:600}
.pick select{display:block;width:100%;margin-top:4px;padding:10px;font:inherit;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
.ln{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;font-weight:700;font-size:.8rem;vertical-align:middle}
.route{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:14px 0 6px;font-size:1.05rem}
.arrow{color:var(--muted)}
.mins{margin-left:auto;font-size:.85rem;color:var(--muted)}
.steps{padding-left:1.3rem;margin:.4rem 0}.steps li{margin:.35rem 0}
.free{background:var(--soft);border-radius:8px;padding:10px 12px;font-size:.92rem;margin:10px 0}
.alert{display:block;margin-top:6px;color:var(--up);font-weight:600}
.board{background:#101614;color:#f5c542;border-radius:8px;padding:10px 12px;font-family:ui-monospace,Consolas,monospace}
.board-h{color:#e6ebe7;font-size:.8rem;margin-bottom:6px}
.board .badge.sample{color:#d8b25c}
.min{display:inline-block;margin-right:18px;font-size:1.25rem;font-weight:700}
.exit{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:10px 0}
.exit-h{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}
.letter{font-size:.75rem;color:var(--gold);font-weight:600}
.exit ul{margin:.3rem 0;padding-left:1.1rem}
.small{font-size:.86rem}
.elev{list-style:none;padding:0;margin:0}.elev li{padding:6px 0;border-bottom:1px solid var(--line);font-size:.92rem}
.elev em{font-style:normal;font-weight:600;margin-left:4px}
.elev .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;background:var(--down)}
.elev .out .dot{background:var(--up)}.elev .out em{color:var(--up)}
.warn{border-left:4px solid var(--gold);font-size:.92rem}
"""

    lines_html = " ".join(line_dot(c) for c in "GYOBS")
    repl = {
        "IDEA_ID": "transit-tech#1",
        "RANK": "6",
        "SCORE": "75.2",
        "SHORT_NAME": "L'Enfant Transfer Coach",
        "PROVENANCE_CLASS": "sample",
        "PROVENANCE_TEXT": "Sample data · illustrative",
        "EYEBROW": "lenfantplaza.org · Transfer Coach",
        "HEADLINE": "Which escalator, which platform, which exit",
        "DECK": f"Five lines meet at L'Enfant Plaza {lines_html}. Tell us where you are and where you're going; we'll give you the steps, the next train and the step-free way.",
        "BODY": body,
        "EXTRA_CSS": extra_css,
        "PITCH": "A phone-first guide to the most confusing transfer in the system: pick your train and your connection, get plain steps, the next trains on the connecting platform and the step-free route if an elevator is out. A second tab says what's above each street exit.",
        "WHATS_REAL": (
            f"Capital Bikeshare dock counts (Bikes tab) were pulled live from the public GBFS feed when this page was built ({len(docks)} docks within 700 m). "
            "The station's layout is from WMATA's own pages: Green/Yellow on upper-level side platforms (one to Branch Ave/Huntington, one to Greenbelt/Mt Vernon Sq), "
            "Orange/Blue/Silver on a lower-level center platform, three street entrances (7th St/Maryland Ave, 9th &amp; D St, 7th &amp; D St), four elevators, and the "
            "end-of-platform escalator up to a mezzanine that crosses over the Green/Yellow tracks. Walk times to places are straight-line estimates (×1.3, 80 m/min)."
        ),
        "WHATS_MOCKED": (
            "Next-train minutes and elevator status are sample values (no WMATA API key); one elevator is shown out on purpose so you can see the step-free alert. "
            "Everything in [brackets] (platform ends, escalator banks, exit letters, transfer walk times, short links) is unverified and needs an on-site walk."
        ),
        "NEXT_STEPS": (
            "Register a free WMATA key and run one Cloudflare Worker on a 30-second cron that calls Rail Predictions for L'Enfant's two station codes "
            "(upper and lower level) and ElevatorIncidents, caches both in KV, and feeds this page; visitors never hit WMATA directly. Walk the station once "
            "with a phone timer to fill every bracket, photograph the exit letters, and stamp a visible \"last verified\" date. Add a \"not affiliated with WMATA\" "
            "line and no Metro marks, per WMATA's data terms."
        ),
        "SOURCES": (
            f'<a href="{WMATA_INFO}">WMATA L\'Enfant Plaza station page</a>, '
            f'<a href="{WMATA_WAYFIND}">WMATA step-by-step wayfinding</a>, '
            f'<a href="{WMATA_ELEV_HQ}">WMATA elevator wayfinding</a>, '
            f'<a href="{WJLA}">WJLA on the wayfinding pilot</a>, '
            f'<a href="{status_url}">Capital Bikeshare GBFS</a> (live)'
        ),
        "GENERATED_UTC": now.strftime("%Y-%m-%d %H:%M UTC"),
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    # Drop the template's instruction comment (it contains a literal placeholder marker).
    page = re.sub(r"<!--.*?-->\s*", "", page, count=1, flags=re.S)
    for k, v in repl.items():
        page = page.replace("{{" + k + "}}", v)
    page = page.replace("any ANC, BID or property owner.", "any ANC, BID or property owner. Not affiliated with or endorsed by WMATA.")
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page) // 1024} KB, {len(docks)} docks)")


if __name__ == "__main__":
    build()
