"""`transit` section: the fixed places the live transit board asks about.

- Metro stations within about 1 km of the boundary (DC GIS), with their lines.
- WMATA bus stops inside the boundary or just outside it (DC GIS layer, whose REG_ID is WMATA's StopID).
- Capital Bikeshare stations inside or just outside the boundary (DC GIS mirror of the GBFS feed).

Live arrivals are not stored here: the Cloudflare Worker (worker/transit.js) asks WMATA and Capital Bikeshare
when someone opens the page, using these ids, and caches each answer for about 30 seconds.

Standalone:  python ingest/transit.py petworth
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
from run import iso, point_in_rings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
S = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA"
METRO = f"{S}/Transportation_Rail_Bus_WebMercator/MapServer/51"      # NAME, LINE, ADDRESS (regional stations)
BUS = f"{S}/Transportation_Rail_Bus_WebMercator/MapServer/53"        # REG_ID (= WMATA StopID), BSTP_MSG_TEXT, lat/lon
BIKES = f"{S}/Transportation_Bikes_Trails_WebMercator/MapServer/5"   # STATION_ID (= GBFS station_id), NAME, CAPACITY
METRO_KM = 1.0   # stations this close to the boundary count as "nearby"
MAX_STATIONS = 3
EDGE_M = 150     # stops and docks this far outside the boundary still serve it (across the street)
MAX_BUS = 60     # the board shows the stops nearest the reader; this caps what the page carries


def _km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    k = math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot((lon1 - lon2) * 111.32 * k, (lat1 - lat2) * 110.57)


def _edge_km(lon: float, lat: float, rings: list) -> float:
    """0 inside the boundary, else the distance to its nearest vertex (good enough at this scale)."""
    if point_in_rings(lon, lat, rings):
        return 0.0
    return min(_km(lon, lat, x, y) for r in rings for x, y in r)


def _env(rings: list, pad: float) -> dict:
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return {"xmin": min(xs) - pad, "ymin": min(ys) - pad, "xmax": max(xs) + pad, "ymax": max(ys) + pad,
            "spatialReference": {"wkid": 4326}}


def _points(layer: str, env: dict, fields: list[str]) -> list[dict]:
    data = dcdata._request(f"{layer}/query", {
        "where": "1=1", "outFields": ",".join(fields), "returnGeometry": "true", "outSR": 4326,
        "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "resultRecordCount": 2000, "f": "json"}, post=True)
    return data.get("features", [])


def build(geom: dict, hood: dict, now: float) -> dict:
    rings = geom["rings"]
    stations = []
    for f in _points(METRO, _env(rings, 0.015), ["NAME", "LINE", "ADDRESS"]):
        g = f.get("geometry") or {}
        if "x" not in g:
            continue
        d = _edge_km(g["x"], g["y"], rings)
        if d <= METRO_KM:
            a = f["attributes"]
            stations.append({"name": a["NAME"], "lines": [l.strip() for l in (a.get("LINE") or "").split(",") if l.strip()],
                             "lat": round(g["y"], 5), "lon": round(g["x"], 5), "km_outside": round(d, 2)})
    stations.sort(key=lambda s: (s["km_outside"], s["name"]))
    stations = stations[:MAX_STATIONS]

    stops = []
    for f in _points(BUS, _env(rings, 0.003), ["REG_ID", "BSTP_MSG_TEXT", "BSTP_LAT", "BSTP_LON", "BSTP_OPS_TCD"]):
        a = f["attributes"]
        lon, lat = a.get("BSTP_LON"), a.get("BSTP_LAT")
        if not a.get("REG_ID") or lon is None or _edge_km(lon, lat, rings) * 1000 > EDGE_M:
            continue
        stops.append({"id": str(a["REG_ID"]), "name": (a.get("BSTP_MSG_TEXT") or "").replace("+", " & "),
                      "lat": round(lat, 5), "lon": round(lon, 5)})
    # When a neighborhood has more stops than the cap, keep an even spread rather than one corner.
    if len(stops) > MAX_BUS:
        stops.sort(key=lambda s: (s["lat"], s["lon"]))
        stops = stops[:: math.ceil(len(stops) / MAX_BUS)]
    stops.sort(key=lambda s: s["name"])

    docks = []
    for f in _points(BIKES, _env(rings, 0.003), ["STATION_ID", "NAME", "CAPACITY", "LATITUDE", "LONGITUDE"]):
        a = f["attributes"]
        lon, lat = a.get("LONGITUDE"), a.get("LATITUDE")
        if not a.get("STATION_ID") or lon is None or _edge_km(lon, lat, rings) * 1000 > EDGE_M:
            continue
        docks.append({"id": a["STATION_ID"], "name": a.get("NAME"), "capacity": int(a.get("CAPACITY") or 0),
                      "lat": round(lat, 5), "lon": round(lon, 5)})
    docks.sort(key=lambda d: d["name"] or "")

    return {
        "generated_at": iso(int(now * 1000)),
        "sources": [{"name": "Metro stations (Open Data DC)", "url": METRO},
                    {"name": "Metro bus stops (Open Data DC; stop ids are WMATA's)", "url": BUS},
                    {"name": "Capital Bikeshare stations (Open Data DC)", "url": BIKES}],
        "stations": stations,
        "bus_stops": stops,
        "bike_docks": docks,
    }


def check(section: dict) -> list[str]:
    errors = []
    for k in ("generated_at", "sources"):
        if not section.get(k):
            errors.append(f"missing {k}")
    if not section.get("bus_stops"):
        errors.append("no bus stops")
    if len({s["id"] for s in section.get("bus_stops", [])}) != len(section.get("bus_stops", [])):
        errors.append("duplicate bus stop ids")
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python ingest/transit.py <slug>", file=sys.stderr)
        return 2
    slug = sys.argv[1]
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if hood is None:
        print(f"unknown slug {slug}", file=sys.stderr)
        return 2
    t0 = time.time()
    section = build(dcdata.hood_boundary(config, hood), hood, time.time())
    out = ROOT / "ingest" / "_out" / f"transit-{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(section, indent=1), encoding="utf-8")
    print(f"{slug}: stations {[(s['name'], s['lines'], s['km_outside']) for s in section['stations']]}, "
          f"{len(section['bus_stops'])} bus stops, {len(section['bike_docks'])} bike docks, {time.time() - t0:.0f}s")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("transit ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
