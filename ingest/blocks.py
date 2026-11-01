"""`blocks` section: DDOT's roadway blocks, used twice on the site.

- `basemap`: every street segment in a padded box around the neighborhood, drawn as the Atlas map's streets.
- `items`: one record per hundred block inside the boundary (e.g. "4200 block of Kansas Ave NW"), with what DDOT
  records about it: cross streets, snow emergency route, residential permit parking, speed limit, bike lanes,
  pavement condition. The site builds one page per block from these and joins the neighborhood's permits,
  311 requests, sales and curb permits to it by hundred block.

Privacy: roadway blocks describe streets, not people. Nothing here is finer than a block.

Standalone:  python ingest/blocks.py petworth
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
from run import iso, point_in_rings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

ROADWAY_BLOCKS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_WebMercator/MapServer/163"
FIELDS = ["ROUTENAME", "ADDRESS_RANGE_LOW", "ADDRESS_RANGE_HIGH", "FROMSTREET", "TOSTREET", "DCFUNCTIONALCLASS",
          "SNOWROUTE_DDOT", "SPEEDLIMITS_IB", "SPEEDLIMITS_OB", "TOTALBIKELANES",
          "BIKELANE_PROTECTED", "PCI_CONDCATEGORY", "PCI_LASTINSPECTED", "SLOWSTREETINFO", "SMD_ID",
          "BUSLANE_INBOUND", "BUSLANE_OUTBOUND"]
S = "https://maps2.dcgis.dc.gov/dcgis/rest/services"
# Lookups joined to each block by its midpoint (polygons) or its name (lines). Researched 2026-11-01; see the
# block page's sources. Street sweeping has no current per-block schedule in DC's open data (only 2015/2022
# layers), so the site points to the posted signs instead of showing an old schedule.
TRASH = f"{S}/DCGIS_DATA/Public_Service_WebMercator/MapServer/28"        # DAY_
RECYCLING = f"{S}/DCGIS_DATA/Public_Service_WebMercator/MapServer/27"    # ROUTE_DAY
LEAF_ZONES = f"{S}/DPW/leafCollection2011Site/FeatureServer/1"           # Route_Num
LEAF_STREETS = f"{S}/DPW/leafCollection2011Site/FeatureServer/0"         # BLOCKNAME, QA_Streets
LEAF_STATUS = f"{S}/DPW/LeafCollectionTonnage/MapServer/0"               # Route_Num, ResidentUp
SCHOOL_ZONES = {"elementary": f"{S}/DCGIS_DATA/Education_WebMercator/MapServer/19",
                "middle": f"{S}/DCGIS_DATA/Education_WebMercator/MapServer/17",
                "high": f"{S}/DCGIS_DATA/Education_WebMercator/MapServer/15"}  # NAME, DCPS_ID (boundaries from SY2025-26)
SCHOOLS = f"{S}/DCGIS_DATA/Education_WebMercator/MapServer/5"            # SCHOOL_ID, NAME, ADDRESS, WEB_URL
PARKING = f"{S}/DCGIS_DATA/Transportation_Parking_WebMercator/MapServer/0"  # BLOCK_ADDRESS, BLOCK_SIDE, RPP_ZONE, PTP_POLICY_DESC
PAD = 0.004  # degrees (~350-450 m) of streets drawn beyond the boundary, so the map has context at its edges
MAJOR = 16   # DC functional class 11-16 are interstates through minor arterials; 17 collectors; 19 local streets

SUFFIX = {"STREET": "ST", "AVENUE": "AVE", "PLACE": "PL", "ROAD": "RD", "TERRACE": "TER", "CIRCLE": "CIR",
          "DRIVE": "DR", "BOULEVARD": "BLVD", "COURT": "CT", "LANE": "LN", "PARKWAY": "PKWY", "WAY": "WAY"}


def street_key(name: str) -> str:
    """'UPSHUR STREET NW' and 'Upshur St NW' -> 'UPSHUR ST NW'. The site uses the same rule (lib/blocks.ts)."""
    words = re.sub(r"[^A-Z0-9 ]", " ", name.upper()).split()
    return " ".join(SUFFIX.get(w, w) for w in words)


def nice(name: str) -> str:
    """'9TH ST NW/VARNUM ST NW' -> '9th St NW / Varnum St NW'."""
    def word(w: str) -> str:
        if w in ("NW", "NE", "SW", "SE"):
            return w
        return w.lower() if re.match(r"^\d+(ST|ND|RD|TH)$", w) else w.capitalize()
    return " / ".join(" ".join(word(w) for w in part.split()) for part in name.split("/") if part.strip())


def _query(layer: str, env: dict, fields: list[str], geometry: bool = False, where: str = "1=1") -> list[dict]:
    rows, offset = [], 0
    while True:
        params = {"where": where, "outFields": ",".join(fields), "returnGeometry": str(geometry).lower(), "outSR": 4326,
                  "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                  "spatialRel": "esriSpatialRelIntersects", "resultOffset": offset, "resultRecordCount": 1000, "f": "json"}
        if geometry:
            params["maxAllowableOffset"] = 0.00002  # ~2 m; zone polygons can be very detailed
        data = dcdata._request(f"{layer}/query", params, post=True)
        batch = data.get("features", [])
        rows += batch
        if not data.get("exceededTransferLimit") or not batch:
            return rows
        offset += len(batch)


def _zone(polys: list[dict], lon: float, lat: float) -> dict | None:
    """Attributes of the first polygon containing the point."""
    for f in polys:
        rings = (f.get("geometry") or {}).get("rings")
        if rings and point_in_rings(lon, lat, rings):
            return f["attributes"]
    return None


def _block_key(address: str) -> str | None:
    """'4300 - 4399 BLOCK OF GEORGIA AVENUE NW' or '800 VARNUM ST NW' -> '4300-georgia-ave-nw'."""
    m = re.match(r"^\s*(\d+)\s*(?:-\s*\d+\s+BLOCK OF\s+)?(.+)$", address or "", re.I)
    if not m:
        return None
    return f"{int(m.group(1)) // 100 * 100}-{street_key(m.group(2)).lower().replace(' ', '-')}"


def _lookups(env: dict, items: dict) -> tuple[dict, list[str]]:
    """Attach collection days, leaf collection, school zones and parking to each block. Returns the neighborhood-level
    notes (leaf status by zone, school details) and a list of lookups that failed (the rest still apply)."""
    failed: list[str] = []

    def safe(name, fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - one missing lookup must not drop the blocks
            failed.append(f"{name}: {type(exc).__name__}: {exc}")
            return []

    trash = safe("trash", lambda: _query(TRASH, env, ["DAY_"], True))
    recycling = safe("recycling", lambda: _query(RECYCLING, env, ["ROUTE_DAY"], True))
    leaf_zones = safe("leaf zones", lambda: _query(LEAF_ZONES, env, ["Route_Num"], True))
    zones = {k: safe(f"{k} school zones", lambda u=u: _query(u, env, ["NAME", "DCPS_ID"], True)) for k, u in SCHOOL_ZONES.items()}
    for it in items.values():
        lon, lat = it["lon"], it["lat"]
        t, r, lz = _zone(trash, lon, lat), _zone(recycling, lon, lat), _zone(leaf_zones, lon, lat)
        it["trash_day"] = (t or {}).get("DAY_")
        it["recycling_day"] = (r or {}).get("ROUTE_DAY")
        it["leaf_zone"] = (lz or {}).get("Route_Num")
        it["leaf_done"] = None
        it["schools"] = {k: (z.get("DCPS_ID"), z.get("NAME")) for k, polys in zones.items() if (z := _zone(polys, lon, lat))}

    for f in safe("leaf streets", lambda: _query(LEAF_STREETS, env, ["BLOCKNAME", "QA_Streets"])):
        it = items.get(_block_key(f["attributes"].get("BLOCKNAME") or "") or "")
        if it and f["attributes"].get("QA_Streets"):
            it["leaf_done"] = f["attributes"]["QA_Streets"].strip().lower() == "completed"

    for it in items.values():
        it["parking"] = []
    for f in safe("parking", lambda: _query(PARKING, env, ["BLOCK_ADDRESS", "BLOCK_SIDE", "RPP_ZONE", "PTP_POLICY_DESC", "PARKING_SPACES"])):
        a = f["attributes"]
        it = items.get(_block_key(a.get("BLOCK_ADDRESS") or "") or "")
        if it and not any(p["side"] == a.get("BLOCK_SIDE") for p in it["parking"]):
            it["parking"].append({"side": a.get("BLOCK_SIDE"), "rpp": a.get("RPP_ZONE"),
                                  "meter": a.get("PTP_POLICY_DESC"), "spaces": a.get("PARKING_SPACES")})

    used_zones = sorted({it["leaf_zone"] for it in items.values() if it.get("leaf_zone")})
    leaf = {}
    if used_zones:
        where = "Route_Num IN (" + ",".join("'" + z.replace("'", "''") + "'" for z in used_zones) + ")"
        for f in safe("leaf status", lambda: _query(LEAF_STATUS, env, ["Route_Num", "ResidentUp"], where=where)):
            a = f["attributes"]
            if a.get("Route_Num") and a.get("ResidentUp"):
                leaf[a["Route_Num"]] = re.sub(r"\s+", " ", a["ResidentUp"]).strip()

    ids = sorted({sid for it in items.values() for sid, _ in it["schools"].values() if sid})
    schools = {}
    if ids:
        nums = [i.split("_")[-1] for i in ids if i.split("_")[-1].isdigit()]
        where = "SCHOOL_ID IN (" + ",".join(nums) + ")" if nums else "1=0"
        big = {"xmin": -77.12, "ymin": 38.79, "xmax": -76.90, "ymax": 39.0, "spatialReference": {"wkid": 4326}}
        for f in safe("schools", lambda: _query(SCHOOLS, big, ["SCHOOL_ID", "NAME", "ADDRESS", "WEB_URL", "GRADES"], where=where)):
            a = f["attributes"]
            schools[f"dcps_{a['SCHOOL_ID']}"] = {"name": a.get("NAME"), "address": a.get("ADDRESS"),
                                                  "url": a.get("WEB_URL"), "grades": a.get("GRADES")}
    for it in items.values():  # blocks store school ids; names and addresses live once in `schools`
        for sid, name in it["schools"].values():
            if sid and sid not in schools:  # zone without a location row: the zone's own name still says it
                schools[sid] = {"name": name, "address": None, "url": None, "grades": None}
        it["schools"] = {k: sid for k, (sid, _) in it["schools"].items() if sid}
    return {"leaf_status": leaf, "schools": schools}, failed


def _simplify(path: list, tol: float = 0.00003) -> list:
    """Ramer-Douglas-Peucker in degrees (~3 m): a block is drawn a few hundred pixels wide at most."""
    if len(path) < 3:
        return path
    (x0, y0), (x1, y1) = path[0], path[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = (dx * dx + dy * dy) ** 0.5 or 1e-12
    dists = [abs(dy * x - dx * y + x1 * y0 - y1 * x0) / norm for x, y in path[1:-1]]
    i = max(range(len(dists)), key=dists.__getitem__)
    if dists[i] <= tol:
        return [path[0], path[-1]]
    return _simplify(path[:i + 2], tol)[:-1] + _simplify(path[i + 1:], tol)


def _mid(path: list) -> tuple[float, float]:
    """The point halfway along a polyline (lon, lat)."""
    seg = [((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for a, b in zip(path, path[1:])]
    half, run = sum(seg) / 2, 0.0
    for (a, b), s in zip(zip(path, path[1:]), seg):
        if run + s >= half and s:
            t = (half - run) / s
            return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        run += s
    return path[0][0], path[0][1]


def build(geom: dict, hood: dict, now: float) -> dict:
    xs = [p[0] for r in geom["rings"] for p in r]
    ys = [p[1] for r in geom["rings"] for p in r]
    env = {"xmin": min(xs) - PAD, "ymin": min(ys) - PAD, "xmax": max(xs) + PAD, "ymax": max(ys) + PAD,
           "spatialReference": {"wkid": 4326}}
    feats = _query(ROADWAY_BLOCKS, env, FIELDS, geometry=True)

    streets, items = [], {}
    for f in feats:
        a, paths = f["attributes"], (f.get("geometry") or {}).get("paths") or []
        if not paths or not a.get("ROUTENAME"):
            continue
        route = street_key(a["ROUTENAME"])
        major = (a.get("DCFUNCTIONALCLASS") or 99) <= MAJOR
        lon, lat = _mid(max(paths, key=len))
        low = a.get("ADDRESS_RANGE_LOW")
        inside = low is not None and point_in_rings(lon, lat, geom["rings"])
        hundred = int(low or 0) // 100 * 100
        key = f"{hundred}-{route.lower().replace(' ', '-')}"
        for p in paths:
            seg = {"n": route, "k": "major" if major else "minor",
                   "p": [[round(x, 5), round(y, 5)] for x, y in _simplify(p)]}
            if inside:
                seg["b"] = key  # lets the map highlight a block (curb permits, the featured 1926 block)
            streets.append(seg)
        if not inside:
            continue
        speeds = [s for s in (a.get("SPEEDLIMITS_IB"), a.get("SPEEDLIMITS_OB")) if s]
        rec = {
            "key": key, "hundred": hundred, "street": route,
            "name": f"{'Unit' if hundred == 0 else hundred} block of {nice(route)}",
            "from": nice(a.get("FROMSTREET") or ""), "to": nice(a.get("TOSTREET") or ""),
            "lat": round(lat, 5), "lon": round(lon, 5),
            "major": major,
            "snow_emergency": bool(a.get("SNOWROUTE_DDOT")),
            "speed": max(speeds) if speeds else None,
            "bike_lanes": a.get("TOTALBIKELANES") or 0,
            "protected_bike_lane": bool(a.get("BIKELANE_PROTECTED")),
            "bus_lane": bool(a.get("BUSLANE_INBOUND") or a.get("BUSLANE_OUTBOUND")),
            "slow_street": bool(a.get("SLOWSTREETINFO")),
            "pavement": a.get("PCI_CONDCATEGORY"),
            "pavement_checked": time.strftime("%Y", time.gmtime(a["PCI_LASTINSPECTED"] / 1000)) if a.get("PCI_LASTINSPECTED") else None,
            "smd": a.get("SMD_ID"),
        }
        old = items.get(key)
        if old is None:
            items[key] = rec
        else:  # a hundred block split in two segments (e.g. at an alley): keep the first, OR the flags
            for k in ("snow_emergency", "protected_bike_lane", "bus_lane", "slow_street", "major"):
                old[k] = old[k] or rec[k]
            if not old["to"] or old["to"] == rec["from"]:
                old["to"] = rec["to"] or old["to"]

    extra, failed = _lookups(env, items)
    return {
        "generated_at": iso(int(now * 1000)),
        "sources": [{"name": "DDOT Roadway Blocks (Open Data DC)", "url": ROADWAY_BLOCKS},
                    {"name": "DPW trash collection days (Open Data DC)", "url": TRASH},
                    {"name": "DPW recycling collection days (Open Data DC)", "url": RECYCLING},
                    {"name": "DPW leaf collection zones and progress", "url": LEAF_STREETS},
                    {"name": "DCPS school attendance zones, SY2025-26 onward (Open Data DC)", "url": SCHOOL_ZONES["elementary"]},
                    {"name": "DCPS school locations (Open Data DC)", "url": SCHOOLS},
                    {"name": "DDOT parking blockfaces: RPP zones and meters (Open Data DC)", "url": PARKING}],
        "lookup_errors": failed,
        "leaf_status": extra["leaf_status"],
        "schools": extra["schools"],
        "basemap": {"bbox": [round(v, 5) for v in (env["xmin"], env["ymin"], env["xmax"], env["ymax"])],
                    "streets": streets},
        "items": sorted(items.values(), key=lambda r: (r["street"], r["hundred"])),
    }


def check(section: dict) -> list[str]:
    errors = []
    for k in ("generated_at", "sources", "basemap", "items"):
        if not section.get(k):
            errors.append(f"missing {k}")
    items = section.get("items") or []
    if len(items) < 15:
        errors.append(f"only {len(items)} blocks")
    if len({i["key"] for i in items}) != len(items):
        errors.append("duplicate block keys")
    if len((section.get("basemap") or {}).get("streets") or []) < len(items):
        errors.append("basemap has fewer streets than blocks")
    for i in items:
        if not re.match(r"^\d+-[a-z0-9-]+$", i["key"]):
            errors.append(f"bad key {i['key']}")
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python ingest/blocks.py <slug>", file=sys.stderr)
        return 2
    slug = sys.argv[1]
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if hood is None:
        print(f"unknown slug {slug}", file=sys.stderr)
        return 2
    t0 = time.time()
    section = build(dcdata.hood_boundary(config, hood), hood, time.time())
    out = ROOT / "ingest" / "_out" / f"blocks-{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(section), encoding="utf-8")
    items = section["items"]
    print(f"{slug}: {len(items)} blocks, {len(section['basemap']['streets'])} street segments drawn, "
          f"{sum(i['snow_emergency'] for i in items)} on snow emergency routes, {sum(any(p['rpp'] for p in i['parking']) for i in items)} RPP, trash days {sorted({i['trash_day'] for i in items if i['trash_day']})}, leaf zones {sorted(section['leaf_status'])}, {len(section['schools'])} schools, errors {section['lookup_errors']}, "
          f"{out.stat().st_size // 1024} KB, {time.time() - t0:.0f}s")
    print("  e.g.", json.dumps(items[len(items) // 2]))
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("blocks ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
