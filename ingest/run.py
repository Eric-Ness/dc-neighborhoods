"""Nightly ingest: pull DC open data for each enabled neighborhood and write site JSON.

Usage:
    python ingest/run.py            # write site/src/data/<slug>.json
    python ingest/run.py --check    # same, then validate the output (used by CI and GATES.md)

Privacy rules are enforced here, at ingest, so nothing personal reaches the repo or the site:
- Permits keep an allowlist of fields; owner and applicant names are never requested.
- 311 addresses are coarsened to the hundred block; inspector names and free-text details are never requested.
- Crime is fetched only as server-side counts by offense, never as individual incidents.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "ingest" / "neighborhoods.json"
OUT_DIR = ROOT / "site" / "src" / "data"

DAY = 86400
PERMIT_DAYS = 30
SR_DAYS = 30

PERMITS_TITLE = "Building Permits in {year}"
SR_TITLE = "311 City Service Requests in {year}"
CRIME_TITLE = "Crime Incidents in {year}"
SMD_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Administrative_Other_Boundaries_WebMercator/MapServer/55"

PERMIT_FIELDS = [
    "PERMIT_ID", "ISSUE_DATE", "PERMIT_TYPE_NAME", "PERMIT_SUBTYPE_NAME", "PERMIT_CATEGORY_NAME",
    "FULL_ADDRESS", "DESC_OF_WORK", "ZONING", "LATITUDE", "LONGITUDE", "SMD",
]
SR_FIELDS = [
    "SERVICEREQUESTID", "SERVICECODEDESCRIPTION", "SERVICETYPECODEDESCRIPTION", "ORGANIZATIONACRONYM",
    "ADDDATE", "RESOLUTIONDATE", "SERVICEORDERSTATUS", "STREETADDRESS", "LATITUDE", "LONGITUDE",
]
# Fields that must never appear in output. tools/verify.mjs checks the written JSON against this list too.
FORBIDDEN_KEYS = {"OWNER_NAME", "PERMIT_APPLICANT", "INSPECTORNAME", "DETAILS", "CCN"}


def years_in(start: float, end: float) -> list[int]:
    return sorted({time.gmtime(start).tm_year, time.gmtime(end).tm_year})


def yearly_layers(title: str, start: float, end: float) -> list[str]:
    layers = []
    for year in years_in(start, end):
        url = dcdata.resolve_yearly_layer(title, year)
        if url:
            layers.append(url)
    if not layers:
        raise RuntimeError(f"no Open Data DC layer found for {title!r} in {years_in(start, end)}")
    return layers


def iso(ms: int | None) -> str | None:
    return None if ms is None else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ms / 1000))


def hundred_block(address: str | None) -> str | None:
    """'1234 UPSHUR STREET NW' -> '1200 block of UPSHUR STREET NW'."""
    if not address:
        return None
    # DC sometimes sends ranges already: "3600 - 3649 BLOCK OF YUMA STREET NW".
    m = re.match(r"^\s*(\d+)\s*-\s*\d+\s+BLOCK OF\s+(.*)$", address, re.I) or re.match(r"^\s*(\d+)\s+(.*)$", address)
    if not m:
        return address  # intersections and landmarks carry no house number
    base = int(m.group(1)) // 100 * 100
    # DC usage: numbers 1-99 are the "unit block".
    return f"{'Unit' if base == 0 else base} block of {m.group(2).strip()}"


def round_coord(value: float | None, places: int) -> float | None:
    return None if value is None else round(value, places)


def fetch_permits(geom: dict, now: float) -> list[dict]:
    start = now - PERMIT_DAYS * DAY
    rows = []
    for layer in yearly_layers(PERMITS_TITLE, start, now):
        rows += dcdata.query_features(layer, geom, dcdata.date_where("ISSUE_DATE", start), PERMIT_FIELDS, "ISSUE_DATE DESC")
    permits = []
    for r in rows:
        work = (r["DESC_OF_WORK"] or "").strip()
        if work.lower() in ("undefined", "null", "none", "n/a"):
            work = ""
        permits.append(_permit(r, work[:400]))
    permits.sort(key=lambda p: p["issued"] or "", reverse=True)
    return permits


def _permit(r: dict, work: str) -> dict:
    return {
        "id": r["PERMIT_ID"],
        "issued": iso(r["ISSUE_DATE"]),
        "group": permit_group(r["PERMIT_TYPE_NAME"], r["PERMIT_SUBTYPE_NAME"], work),
        "type": r["PERMIT_TYPE_NAME"],
        "subtype": r["PERMIT_SUBTYPE_NAME"],
        "address": (r["FULL_ADDRESS"] or "").replace(", WASHINGTON, DC", "").strip(),
        "work": work,
        "zoning": r["ZONING"],
        "lat": round_coord(r["LATITUDE"], 5),
        "lon": round_coord(r["LONGITUDE"], 5),
        "smd": r["SMD"],
    }


def fetch_311(geom: dict, now: float) -> dict:
    # Two windows so the page can show change versus the previous 30 days.
    start = now - 2 * SR_DAYS * DAY
    rows = []
    for layer in yearly_layers(SR_TITLE, start, now):
        rows += dcdata.query_features(layer, geom, dcdata.date_where("ADDDATE", start), SR_FIELDS)
    cutoff_ms = (now - SR_DAYS * DAY) * 1000
    current = [r for r in rows if (r["ADDDATE"] or 0) >= cutoff_ms]
    previous = [r for r in rows if (r["ADDDATE"] or 0) < cutoff_ms]
    cur_counts = Counter(r["SERVICECODEDESCRIPTION"] for r in current)
    prev_counts = Counter(r["SERVICECODEDESCRIPTION"] for r in previous)
    by_type = [
        {"type": t, "count": n, "previous": prev_counts.get(t, 0)}
        for t, n in cur_counts.most_common()
    ]
    recent = sorted(current, key=lambda r: r["ADDDATE"] or 0, reverse=True)[:50]
    return {
        "total": len(current),
        "previous_total": len(previous),
        "by_type": by_type,
        "open": sum(1 for r in current if (r["SERVICEORDERSTATUS"] or "").upper() not in ("CLOSED", "CLOSE")),
        "recent": [
            {
                "type": r["SERVICECODEDESCRIPTION"],
                "agency": r["ORGANIZATIONACRONYM"],
                "added": iso(r["ADDDATE"]),
                "resolved": iso(r["RESOLUTIONDATE"]),
                "status": r["SERVICEORDERSTATUS"],
                "block": hundred_block(r["STREETADDRESS"]),
                # ~110 m precision: enough for a block-level map dot, not a front door.
                "lat": round_coord(r["LATITUDE"], 3),
                "lon": round_coord(r["LONGITUDE"], 3),
            }
            for r in recent
        ],
    }


def fetch_crime_counts(geom: dict, now: float) -> dict:
    start = now - 2 * SR_DAYS * DAY
    mid = now - SR_DAYS * DAY
    current: Counter = Counter()
    previous: Counter = Counter()
    for layer in yearly_layers(CRIME_TITLE, start, now):
        current.update(dcdata.count_by(layer, geom, dcdata.date_where("REPORT_DAT", mid), "OFFENSE"))
        previous.update(dcdata.count_by(layer, geom, dcdata.date_where("REPORT_DAT", start, mid), "OFFENSE"))
    offenses = sorted(set(current) | set(previous), key=lambda o: -current.get(o, 0))
    return {
        "total": sum(current.values()),
        "previous_total": sum(previous.values()),
        "by_offense": [{"offense": o, "count": current.get(o, 0), "previous": previous.get(o, 0)} for o in offenses],
        "note": "Preliminary MPD counts by DC Code offense; not FBI NIBRS totals.",
    }


def ring_centroid(ring: list[list[float]]) -> tuple[float, float]:
    """Area-weighted centroid of one polygon ring (shoelace formula)."""
    area = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if area == 0:
        return ring[0][0], ring[0][1]
    return cx / (3 * area), cy / (3 * area)


def point_in_rings(x: float, y: float, rings: list[list[list[float]]]) -> bool:
    """Even-odd ray casting across all rings, so holes are handled."""
    inside = False
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def fetch_smds(geom: dict) -> list[dict]:
    """SMDs whose centroid lies inside the neighborhood. Plain 'intersects' also returns
    neighbors that merely share a border street, which would overstate who represents the area."""
    data = dcdata._request(
        f"{SMD_LAYER}/query",
        {
            "where": "1=1",
            "outFields": "SMD_ID,ANC_ID,REP_NAME,WEB_URL",
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "json",
            "geometry": json.dumps(geom),
            "geometryType": "esriGeometryPolygon",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
        },
        post=True,
    )
    smds = []
    for f in data.get("features", []):
        outer = max(f["geometry"]["rings"], key=len)
        if not point_in_rings(*ring_centroid(outer), geom["rings"]):
            continue
        smds.append(
            {
                "smd": f["attributes"]["SMD_ID"],
                "anc": f["attributes"]["ANC_ID"],
                # Elected commissioners are public officials; their names are public record.
                "commissioner": f["attributes"]["REP_NAME"],
                "url": f["attributes"]["WEB_URL"],
            }
        )
    return sorted(smds, key=lambda s: s["smd"])


def permit_group(permit_type: str | None, subtype: str | None, work: str) -> str:
    """Collapse DOB's type/subtype codes into the handful of groups a resident cares about."""
    t, s, w = (permit_type or "").upper(), (subtype or "").upper(), work.upper()
    if "RAZE" in s or "RAZE" in w or "DEMOLITION" in s:
        return "Demolition"
    if "NEW BUILDING" in s or "NEW CONSTRUCTION" in w:
        return "New construction"
    if "ADDITION" in s or "ADDITION" in w:
        return "Additions"
    if t == "CONSTRUCTION":
        return "Renovation & repair"
    if t == "SUPPLEMENTAL":
        return "Electrical, plumbing & mechanical"
    if t == "HOME OCCUPATION":
        return "Home businesses"
    if t in ("POST CARD", "POSTCARD"):
        return "Minor work"
    return "Other"


def build(hood: dict, boundary_layer: str, boundary_source: str, now: float) -> dict:
    geom = dcdata.boundary(boundary_layer, hood["boundary_where"])
    permits = fetch_permits(geom, now)
    sr = fetch_311(geom, now)
    crime = fetch_crime_counts(geom, now)
    smds = fetch_smds(geom)
    return {
        "slug": hood["slug"],
        "name": hood["name"],
        "generated_at": iso(int(now * 1000)),
        "boundary": {"source": boundary_source, "rings": geom["rings"]},
        "windows": {"permits_days": PERMIT_DAYS, "requests_days": SR_DAYS},
        "permits": permits,
        "requests": sr,
        "crime": crime,
        "smds": smds,
        "sources": {
            "permits": "Open Data DC: Building Permits (DOB)",
            "requests": "Open Data DC: 311 City Service Requests (OUC)",
            "crime": "Open Data DC: Crime Incidents (MPD), counts only",
            "smds": "Open Data DC: Single Member Districts 2023",
            "license": "CC BY 4.0",
        },
    }


def find_forbidden(obj, path="$") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.upper() in FORBIDDEN_KEYS:
                hits.append(f"{path}.{k}")
            hits += find_forbidden(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += find_forbidden(v, f"{path}[{i}]")
    return hits


def check(outputs: dict[str, dict]) -> list[str]:
    errors = []
    for slug, data in outputs.items():
        if not data["permits"]:
            errors.append(f"{slug}: no permits")
        if data["requests"]["total"] <= 0:
            errors.append(f"{slug}: no 311 requests")
        if not data["smds"]:
            errors.append(f"{slug}: no SMDs")
        if len(data["boundary"]["rings"]) == 0:
            errors.append(f"{slug}: empty boundary")
        errors += [f"{slug}: forbidden field {h}" for h in find_forbidden(data)]
        reread = json.loads((OUT_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        if reread["generated_at"] != data["generated_at"]:
            errors.append(f"{slug}: written file does not match this run")
    return errors


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = time.time()
    outputs: dict[str, dict] = {}
    for hood in config["neighborhoods"]:
        if not hood["enabled"]:
            continue
        data = build(hood, config["boundary_layer"], config["boundary_source"], now)
        (OUT_DIR / f"{hood['slug']}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
        outputs[hood["slug"]] = data
        print(
            f"{hood['slug']}: {len(data['permits'])} permits, {data['requests']['total']} 311 requests, "
            f"{data['crime']['total']} crime reports, {len(data['smds'])} SMDs"
        )
    index = [
        {"slug": h["slug"], "name": h["name"], "hosts": h["hosts"], "redirect_hosts": h["redirect_hosts"]}
        for h in config["neighborhoods"]
        if h["enabled"]
    ]
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")

    if "--check" in sys.argv:
        errors = check(outputs)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print("ingest verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
