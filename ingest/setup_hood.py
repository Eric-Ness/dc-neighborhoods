"""Measure a neighborhood before adding it: what its boundary holds and how it lines up with DC's other areas.

    python ingest/setup_hood.py <slug>        # the slug must already be in neighborhoods.json (enabled or not)

Prints, for the boundary that entry defines:
- its size and the ANC single-member districts inside it (by centroid, the same rule run.py uses);
- which OTR tax-assessment sub-areas its homes belong to, how much of each sub-area falls inside, and a
  suggested `HOODS` entry for ingest/homes.py (sub-areas holding at least 5% of in-boundary homes), plus
  whether houses or condos should lead (`primary`);
- how many tax squares it shares with every other neighborhood in neighborhoods.json (overlap).

It only reads public data and writes nothing. Copy what fits into homes.py, news.py, events.py, jobs.py and
history.py by hand, then run each module standalone (see MODULES.md).
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
import homes  # noqa: E402
from run import SMD_LAYER, point_in_rings, ring_centroid  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MIN_SHARE = 0.05  # sub-areas below this share of in-boundary homes are noise or edge squares
CONDO_LEAD = 3.0  # condos lead when they outnumber houses this many times over


def area_km2(rings: list) -> float:
    total = 0.0
    for r in rings:
        k = 111.32 * math.cos(math.radians(sum(p[1] for p in r) / len(r)))
        a = sum(x1 * k * y2 * 110.57 - x2 * k * y1 * 110.57 for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))
        total += abs(a) / 2
    return total


def squares(geom: dict) -> set[str]:
    return {s for s in dcdata.count_by(homes.ADDRESS_POINTS, geom, "1=1", "SQUARE") if s}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    slug = sys.argv[1]
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if not hood:
        print(f"{slug!r} is not in neighborhoods.json; add it (enabled: false) first", file=sys.stderr)
        return 2
    geom = dcdata.hood_boundary(config, hood)
    print(f"{hood['name']}: {len(geom['rings'])} ring(s), {area_km2(geom['rings']):.2f} km²")

    smds = dcdata.query_features(SMD_LAYER, geom, "1=1", ["SMD_ID", "ANC_ID"])
    inside = []
    for s in smds:
        d = dcdata._request(f"{SMD_LAYER}/query", {"where": f"SMD_ID='{s['SMD_ID']}'", "outFields": "SMD_ID",
                                                   "outSR": 4326, "f": "json"})
        rings = d["features"][0]["geometry"]["rings"]
        if point_in_rings(*ring_centroid(max(rings, key=len)), geom["rings"]):
            inside.append(s["SMD_ID"])
    ancs = sorted({s.rstrip("0123456789") for s in inside})
    print(f"SMDs inside (centroid): {', '.join(sorted(inside)) or 'none'}  ->  ANCs {ancs}")

    sq = squares(geom)
    itspe = homes._layer(homes.ITSPE_TITLE, time.gmtime(time.time()).tm_year)
    res = "USECODE IN (" + ",".join(homes._q(c) for c in {**homes.HOUSE_CODES, **homes.CONDO_CODES}) + ")"
    rows = homes._group_count(itspe, "SQUARE IN (" + ",".join(homes._q(s) for s in sq) + f") AND {res}",
                              ["NBHDNAME", "SUBNBHD", "USECODE"]) if sq else []
    agg: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        agg[(r["NBHDNAME"], r["SUBNBHD"])][0 if r["USECODE"] in homes.HOUSE_CODES else 1] += r["n"]
    total = sum(a + b for a, b in agg.values()) or 1
    houses = sum(a for a, _ in agg.values())
    condos = sum(b for _, b in agg.values())
    print(f"\n{len(sq)} tax squares; residential parcels on them: {houses} houses, {condos} condos")
    print(f"{'OTR area':26} {'sub':4} {'houses':>7} {'condos':>7} {'share':>6} {'of area inside':>15}")
    keep = []
    for (name, sub), (a, b) in sorted(agg.items(), key=lambda kv: -sum(kv[1])):
        share = (a + b) / total
        if share < 0.01:
            continue
        whole = homes._group_count(itspe, f"NBHDNAME={homes._q(name)}" + (f" AND SUBNBHD={homes._q(sub)}" if sub else "")
                                   + f" AND {res}", ["NBHDNAME"])
        whole_n = sum(r["n"] for r in whole) or 1
        print(f"{name!s:26} {sub!s:4} {a:7} {b:7} {share:6.0%} {(a + b) / whole_n:15.0%}")
        if share >= MIN_SHARE:
            keep.append((name, sub))
    primary = "condo" if condos >= CONDO_LEAD * max(houses, 1) else "house"
    print(f"\nSuggested homes.py HOODS entry (check the 'of area inside' column; low values mean the sub-area"
          f" mostly lies outside):\n    \"{slug}\": {{\"otr\": {keep!r}, \"primary\": \"{primary}\"}},")

    print("\nShared tax squares with other neighborhoods:")
    for other in config["neighborhoods"]:
        if other["slug"] == slug:
            continue
        shared = sq & squares(dcdata.hood_boundary(config, other))
        if len(shared) >= 3:  # one or two are square numbers reused across the city, not real overlap
            print(f"  {other['name']:22} {len(shared):4} ({len(shared) / max(len(sq), 1):.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
