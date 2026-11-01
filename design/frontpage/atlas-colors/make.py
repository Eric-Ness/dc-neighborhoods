"""Five color variants of the Atlas front page.

    python design/frontpage/atlas-colors/make.py

Reads ../atlas/index.html (built by ../atlas/build.py), swaps its color tokens and the map's few fixed colors
for each palette below, and writes <name>/index.html. Prints the contrast of every text color on the page and
map backgrounds, so nothing ships under 4.5:1.
"""

from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE.parent / "atlas" / "index.html").read_text(encoding="utf-8")

# Fixed colors in the Atlas CSS, by role (see ../atlas/build.py).
FIXED = {
    "#eef4f7": "hl",      # highlighted list row
    "#dde9df": "circ",    # traffic circles on the map
    "#d3dbe1": "hatch",   # hatching outside the boundary
    "#7e8e99": "easing",  # tally bar: easing
    "#cfd7dc": "steady",  # tally bar: steady
    "#b8c2c8": "na",      # missing month in a chart
    "#9aa6ae": "lead",    # leader lines
    "#8796a0": "mc",      # month chart bars
    "#7d8b95": "grid",    # map graticule
    "#56656f": "bf",      # bar fills
    "#3d5a45": "lm",      # landmark labels
}

PALETTES = {
    "harbor": dict(  # sea blue-teal
        paper="#ffffff", ink="#0f2533", ink2="#36505f", ink3="#556b78", rule="#cfdde3", rule2="#e5eef1",
        land="#eef5f6", outside="#dfe9ec", street="#ffffff", ave="#ffffff", ribbon="#5aa3a8", line="#0f2533",
        red="#c2452b", green="#1f7a5a", ochre="#a35c0b", sepia="#6f5640", blue="#1f6f8b", link="#0d5f73",
        hl="#e6f1f2", circ="#d5e8e6", hatch="#cfdfe3", easing="#6f8d99", steady="#c8d9de", na="#b3c6cc",
        lead="#93abb3", mc="#6f97a3", grid="#7a99a3", bf="#3f6a78", lm="#2c5a5c"),
    "seaglass": dict(  # green-teal, sea without being blue
        paper="#ffffff", ink="#13241f", ink2="#3a5049", ink3="#566b64", rule="#d2ded8", rule2="#e7efeb",
        land="#eff5f1", outside="#e0ebe5", street="#ffffff", ave="#ffffff", ribbon="#6fb39c", line="#13241f",
        red="#b8432a", green="#2a7a4b", ochre="#9a5d10", sepia="#6e5a44", blue="#2f6e78", link="#156452",
        hl="#e6f0ea", circ="#d6e8dc", hatch="#d3e0d8", easing="#73908a", steady="#cbdcd4", na="#b6c8c0",
        lead="#97aea6", mc="#6f9a8c", grid="#7e9c92", bf="#3f6b5e", lm="#2f5a46"),
    "brickivy": dict(  # DC rowhouse brick with ivy, no blue
        paper="#ffffff", ink="#221a17", ink2="#4a3f3a", ink3="#675b55", rule="#e0d8d4", rule2="#efeae7",
        land="#f4f2f0", outside="#e9e5e2", street="#ffffff", ave="#ffffff", ribbon="#b9705a", line="#221a17",
        red="#a63a24", green="#2f6a3a", ochre="#8f5a12", sepia="#6b4a33", blue="#3d5a6e", link="#2f6a3a",
        hl="#f3ebe7", circ="#e3e8dc", hatch="#e2dbd7", easing="#8a7d76", steady="#ddd4cf", na="#c9beb8",
        lead="#ab9d96", mc="#9a7f70", grid="#a39389", bf="#6b5148", lm="#3f5a33"),
    "graphite": dict(  # near-monochrome, one marigold
        paper="#ffffff", ink="#161616", ink2="#404040", ink3="#5e5e5e", rule="#d9d9d9", rule2="#ececec",
        land="#f3f3f3", outside="#e6e6e6", street="#ffffff", ave="#ffffff", ribbon="#9a9a9a", line="#161616",
        red="#9e6000", green="#3c6e4f", ochre="#8a5a00", sepia="#6a5a4a", blue="#4a4a4a", link="#1d1d1d",
        hl="#fbf3e2", circ="#e2e2e2", hatch="#dcdcdc", easing="#8a8a8a", steady="#d4d4d4", na="#c4c4c4",
        lead="#a8a8a8", mc="#8c8c8c", grid="#9a9a9a", bf="#555555", lm="#3d3d3d"),
    "dusk": dict(  # navy masthead band, sea-foam map, coral marks
        paper="#ffffff", ink="#0e1c2b", ink2="#34485c", ink3="#53677a", rule="#d1dce5", rule2="#e6edf2",
        land="#eaf4f2", outside="#dbe8e6", street="#ffffff", ave="#ffffff", ribbon="#4fa59a", line="#0e1c2b",
        red="#bb432b", green="#1f7a5f", ochre="#965708", sepia="#6f5640", blue="#2a5d8a", link="#1b5a86",
        hl="#e8f2f2", circ="#cfe7e1", hatch="#cfdfe0", easing="#6b8597", steady="#c6d6e0", na="#b0c3cf",
        lead="#8ea5b5", mc="#5f8fa3", grid="#7896a6", bf="#355b74", lm="#21564c"),
}

# Harbor with a slate masthead instead of near-black: (title and nav color, heavy rules color, body ink or None).
SLATES = {
    "harbor-slate": ("#4a5b67", "#4a5b67", None),       # neutral slate on title, nav and the heavy rules
    "harbor-steel": ("#3d5a6c", "#5a7a8a", None),       # bluer steel slate, lighter teal-gray rules
    "harbor-soft": ("#4a5b67", "#4a5b67", "#22323d"),   # slate masthead and softer body ink throughout
}
for _name, (_mast, _rule, _ink) in SLATES.items():
    PALETTES[_name] = dict(PALETTES["harbor"], **({"ink": _ink, "line": _ink} if _ink else {}))

# Extra CSS per variant (small structural touches; "dusk" gets a dark masthead band).
EXTRA = {
    "dusk": """
.topline,.mast,nav.sections{background:#0e1c2b;color:#e8eff5}
.topline{border-bottom-color:#23384d}.topline b{color:#ffffff}.topline,.topline *{color:#c9d6e2}
.mast h1{color:#ffffff}.mast .about{color:#c9d6e2}.mast .coords{color:#8fb0c4}
nav.sections{border-top-color:#4fa59a;border-bottom:0}nav.sections a{color:#ffffff}
""",
    "graphite": """
nav.sections{border-top-color:#e0a000}
[data-ref].on{box-shadow:inset 3px 0 0 #e0a000}
""",
}
for _name, (_mast, _rule, _ink) in SLATES.items():
    EXTRA[_name] = f"""
.mast h1,.topline b,nav.sections a{{color:{_mast}}}
nav.sections,.band{{border-top-color:{_rule}}}
"""


def lum(h: str) -> float:
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


ROOT = re.compile(r":root\{.*?\n\}", re.S)


def build(name: str, p: dict) -> str:
    html = SRC
    m = ROOT.search(html)
    block = m.group(0)
    for k, v in p.items():
        block = re.sub(rf"--{k}:#[0-9a-fA-F]{{6}}", f"--{k}:{v}", block)
    html = html[:m.start()] + block + html[m.end():]
    for hexv, role in FIXED.items():
        html = re.sub(re.escape(hexv), p[role], html, flags=re.I)
    if name in EXTRA:
        html = html.replace("</style>", EXTRA[name] + "</style>", 1)
    return html


def main() -> None:
    for name, p in PALETTES.items():
        out = HERE / name / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(build(name, p), encoding="utf-8")
        checks = {f"{t} on {bg}": contrast(p[t], p[bg]) for t in ("ink", "ink2", "ink3", "link", "red", "green", "ochre", "blue")
                  for bg in ("paper", "land")}
        worst = min(checks, key=checks.get)
        flag = "OK " if checks[worst] >= 4.5 else "LOW"
        print(f"{flag} {name:9} lowest text contrast: {worst} {checks[worst]:.2f}:1")


if __name__ == "__main__":
    main()
