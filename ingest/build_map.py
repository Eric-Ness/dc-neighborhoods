"""Draws the shapes for the /map/ page into site/src/data/map.json. Run from the repo root after adding a site:

    python ingest/build_map.py

A local tool, not part of the nightly run: it needs shapely, which the nightly ingest doesn't install, and boundaries
only change when a site is added. `node tools/verify.mjs site` fails if a live site is missing from the map.
"""
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import polylabel, unary_union

sys.path.insert(0, str(Path(__file__).parent))
import dcdata

HPN = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
DATA = Path("site/src/data")
WIDTH = 1000
PAD = 8

# Hand placement in the middle of the city, where centered names collide (map units).
NUDGE = {
    "Fort Dupont": (28, 6), "National Mall": (-30, 8), "Michigan Park": (14, -10),
    "Friendship Heights": (-6, -16), "Tenleytown": (10, 14),
    "Mount Pleasant": (-42, 0), "Columbia Heights": (28, 0),
    "Dupont Circle": (-20, 0), "Logan Circle": (12, -16),
    "Chinatown": (-16, 0), "Eastland Gardens": (-40, -6),
}
# Planning areas that stay unlabeled because their name would land on top of a site's.
NO_LABEL = {"DC Medical Center", "Edgewood", "Saint Elizabeths", "Cathedral Heights", "South Columbia Heights", "Bellevue"}


def area_name(raw):
    return raw.title().replace("/", " / ").replace("16Th", "16th").replace("Dc ", "DC ")


def merge(rings):
    # Boundaries are stored as one ring per Census tract; merged so no seams show inside a neighborhood.
    merged = unary_union([Polygon(r).buffer(0) for r in rings])
    merged = merged.buffer(1e-5, join_style="mitre").buffer(-1e-5, join_style="mitre").simplify(3e-5)
    polys = list(getattr(merged, "geoms", [merged]))
    outline = []
    for poly in polys:
        outline.append(list(poly.exterior.coords))
        outline += [list(i.coords) for i in poly.interiors if Polygon(i).area > 1e-6]
    return outline, polylabel(max(polys, key=lambda q: q.area), 0.0003), merged


def rdp(pts, tol):
    # Douglas-Peucker: drops vertices nobody can see at this size.
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy)
    far, at = 0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        dist = abs(dy * (px - x1) - dx * (py - y1)) / n if n else math.hypot(px - x1, py - y1)
        if dist > far:
            far, at = dist, i
    if far <= tol:
        return [pts[0], pts[-1]]
    return rdp(pts[: at + 1], tol)[:-1] + rdp(pts[at:], tol)


def main():
    res = dcdata._request(f"{HPN}/query", {"where": "1=1", "outFields": "DC_HPN_NAME", "outSR": 4326, "f": "json", "maxAllowableOffset": 0.0002})
    raw_areas = [(area_name(f["attributes"]["DC_HPN_NAME"]), f["geometry"]["rings"]) for f in res["features"]]

    pts = [p for _, rs in raw_areas for r in rs for p in r]
    lon0, lon1 = min(p[0] for p in pts), max(p[0] for p in pts)
    lat0, lat1 = min(p[1] for p in pts), max(p[1] for p in pts)
    k = math.cos(math.radians((lat0 + lat1) / 2))
    scale = WIDTH / ((lon1 - lon0) * k)
    height = (lat1 - lat0) * scale

    def xy(p):
        return ((p[0] - lon0) * k * scale + PAD, (lat1 - p[1]) * scale + PAD)

    def path(rings, tol=0.7):
        out = []
        for r in rings:
            c = [xy(p) for p in r]
            half = len(c) // 2
            s = rdp(c[: half + 1], tol)[:-1] + rdp(c[half:], tol)
            if len(s) >= 4:
                out.append("M" + "L".join("%.1f,%.1f" % q for q in s[:-1]) + "Z")
        return "".join(out)

    def label(name, pt):
        x, y = xy(pt)
        dx, dy = NUDGE.get(name, (0, 0))
        return [round(x + dx), round(y + dy)]

    sites = []
    shapes = []
    for h in json.loads((DATA / "index.json").read_text(encoding="utf-8")):
        rings = json.loads((DATA / f"{h['slug']}.json").read_text(encoding="utf-8"))["boundary"]["rings"]
        outline, center, shape = merge(rings)
        shapes.append(shape)
        sites.append({"slug": h["slug"], "name": h["name"], "host": h["hosts"][0], "d": path(outline), "label": label(h["name"], (center.x, center.y)), "_area": shape.area})
    sites.sort(key=lambda s: -s.pop("_area"))  # small shapes last, so they stay clickable where boundaries overlap

    covered = unary_union(shapes)
    areas = []
    for name, rings in raw_areas:
        poly = unary_union([Polygon(r).buffer(0) for r in rings])
        row = {"name": name, "d": path(rings)}
        # Gray areas get a name only when most of them have no site.
        if poly.difference(covered).area / poly.area > 0.6 and name not in NO_LABEL:
            biggest = max(getattr(poly, "geoms", [poly]), key=lambda q: q.area)
            row["label"] = label(name, (biggest.centroid.x, biggest.centroid.y))
        areas.append(row)

    out = {"width": WIDTH + 2 * PAD, "height": round(height + 2 * PAD), "areas": areas, "sites": sites}
    (DATA / "map.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"map.json: {len(sites)} sites, {len(areas)} planning areas, {len(json.dumps(out)) // 1024} KB")


if __name__ == "__main__":
    main()
