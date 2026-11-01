"""`streets` section: curb permits (DDOT TOPS), street trees (Urban Forestry) and 311 time-to-close.

Privacy: permittee, owner, applicant and contractor names are never requested. Tree notes and
311 free text are never requested. Every location is coarsened to the hundred block.

Standalone:  python ingest/streets.py petworth
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
from run import hundred_block, iso, point_in_rings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DAY = 86400

# Per-neighborhood settings (none needed yet; everything is driven by the boundary polygon).
SETTINGS: dict[str, dict] = {"petworth": {}, "tenleytown": {}, "adamsmorgan": {}}

# ---------------------------------------------------------------- curb (DDOT TOPS)
OCC_TITLE = "Occupancy Permits (via DDOT TOPs)"
AHEAD = 7
LONG_DAYS = 90
UPCOMING_CAP = 40
OCC_FIELDS = ["TrackingNumber", "EventTypeDescription", "EffectiveDate", "ExpirationDate",
              "WorkLocationFullAddress", "CurbLaneLength", "ParkingStartTime", "ParkingEndTime"]
GROUPS = [
    ("Moving & storage", ("Moving Truck", "Moving Storage Container")),
    ("Dumpsters", ("Roll Off Debris Container",)),
    ("Construction staging", ("Construction Staging Area", "Other Work Related Occupancy", "Steel plate")),
    ("Cranes", ("Mobile Crane",)),
    ("Lead pipe replacement", ("Lead Free DC",)),
    ("Utility & DDOT work", ("ENP For DDOT", "Small Cell", "Manhole")),
    ("Events & reserved parking", ()),
]

# ---------------------------------------------------------------- trees (fixed, non-yearly layer)
TREES = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Urban_Tree_Canopy/MapServer/23"
TREE_FIELDS = ["OBJECTID", "CMMN_NM", "DBH", "CONDITION", "TBOX_STAT", "VICINITY", "DATE_PLANT", "LAST_EDITED_DATE"]

# ---------------------------------------------------------------- 311
SR_TITLE = "311 City Service Requests in {year}"
SR_DAYS = 365
SERVICE_TYPES = 8
CLOSED = "SERVICEORDERSTATUS = 'Closed' AND RESOLUTIONDATE >= ADDDATE"
QUANTILES = [i / 20 for i in range(0, 21)]  # 0, 0.05, ... 1 (0 and 1 are min and max)

FORBIDDEN_KEYS = {"OWNER_NAME", "OWNERNAME", "OWNNAME", "OWNER", "PERMIT_APPLICANT", "APPLICANT",
                  "INSPECTORNAME", "DETAILS", "CCN"}


def _day(ms: int | None) -> str | None:
    # TOPS stores DC local time as if it were UTC, so the UTC calendar date is the local date.
    return None if not ms else time.strftime("%Y-%m-%d", time.gmtime(ms / 1000))


def _find_layer(title: str) -> str:
    url = dcdata.resolve_yearly_layer(title, 0)  # title has no {year}; this is a plain exact-title lookup
    if not url:
        raise RuntimeError(f"layer not found on Open Data DC: {title}")
    return url


def _tidy(s: str) -> str:
    s = s.title()
    s = re.sub(r"\b(Nw|Ne|Sw|Se)\b", lambda m: m.group(1).upper(), s)
    s = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), s)
    return s.replace(" Block Of ", " block of ")


def _block(addr: str | None) -> str:
    """Any DC address form -> '4200 block of 3rd Street NW'. Never returns a house number."""
    v = re.sub(r"\s+", " ", (addr or "")).strip()
    if not v:
        return "Location not listed"
    v = re.sub(r"^(OPP|REAR|NEAR|BEHIND)\s+", "", v, flags=re.I)
    v = re.sub(r"\s*\(.*?\)\s*", " ", v).strip()
    m = re.match(r"^(\d+)\s+BLK\s+(.*)$", v, re.I)
    if m:
        v = f"{m.group(1)} {m.group(2)}"
    v = re.sub(r",?\s*WASHINGTON,?\s*DC.*$", "", v, flags=re.I)
    return _tidy(hundred_block(v) or v)


def _clock(v: str | None) -> str | None:
    m = re.match(r"^\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*([AP]M)?", v or "", re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), m.group(2), (m.group(3) or "").lower()
    if not ap:
        ap = "am" if h < 12 else "pm"
        h = h % 12 or 12
    return f"{h}{'' if mi == '00' else ':' + mi} {ap}"


def _hours(a: str | None, b: str | None) -> str:
    s, e = _clock(a), _clock(b)
    return "" if not s or not e or s == e else f"{s}–{e}"


def _group(event: str | None) -> str:
    e = event or ""
    for name, keys in GROUPS:
        if any(e.startswith(k) for k in keys):
            return name
    return GROUPS[-1][0]


def _latest(url: str, field: str) -> int | None:
    data = dcdata._request(f"{url}/query", {"where": f"{field} IS NOT NULL", "orderByFields": f"{field} DESC",
                                            "outFields": field, "resultRecordCount": 1, "returnGeometry": "false", "f": "json"})
    feats = data.get("features", [])
    return feats[0]["attributes"][field] if feats else None


def build_curb(geom: dict, now: float) -> tuple[dict, str]:
    occ_url = _find_layer(OCC_TITLE)
    now_ms = now * 1000
    horizon = time.strftime("%Y-%m-%d", time.gmtime(now + (AHEAD + 1) * DAY))
    where = (f"{dcdata.date_where('ExpirationDate', now)} AND EffectiveDate < TIMESTAMP '{horizon} 00:00:00' "
             "AND Status IN ('ISSUED','APPROVED')")
    rows = dcdata.query_features(occ_url, geom, where, OCC_FIELDS)

    seen, items = set(), []
    for r in rows:
        key = (r["TrackingNumber"], r["WorkLocationFullAddress"], r["EventTypeDescription"])
        if key in seen:
            continue
        seen.add(key)
        dur = ((r["ExpirationDate"] or 0) - (r["EffectiveDate"] or 0)) / 1000 / DAY
        items.append({
            "type": _group(r["EventTypeDescription"]),
            "block": _block(r["WorkLocationFullAddress"]),
            "start_ms": r["EffectiveDate"] or 0,
            "end_ms": r["ExpirationDate"],
            "ft": int(r["CurbLaneLength"] or 0),
            "hours": _hours(r["ParkingStartTime"], r["ParkingEndTime"]),
            "long": dur > LONG_DAYS,
        })
    items.sort(key=lambda i: i["start_ms"])
    upcoming = [i for i in items if i["start_ms"] > now_ms]
    by_type = Counter(i["type"] for i in items)

    last_issue, last_update = _latest(occ_url, "IssueDate"), _latest(occ_url, "LastUpdateDate")
    stale = last_update is None or (now_ms - last_update) / 1000 / DAY > 3
    freshness = (f"DDOT TOPS occupancy layer, checked {time.strftime('%Y-%m-%d', time.gmtime(now))}: newest permit issued "
                 f"{_day(last_issue) or 'unknown'}, newest record update {_day(last_update) or 'unknown'}"
                 + (". The layer looks stale; treat counts with caution." if stale else ", so the layer is current to within a day or two."))
    return {
        "active_this_week": len(items),
        "starting_next_7d": len(upcoming),
        "reserved_ft": sum(i["ft"] for i in items),
        "long_running_90d": sum(1 for i in items if i["long"]),
        "freshness_note": freshness,
        "by_type": [{"type": name, "count": by_type[name]} for name, _ in GROUPS if by_type.get(name)],
        "upcoming": [
            {"type": i["type"], "block": i["block"], "start": _day(i["start_ms"]), "end": _day(i["end_ms"]),
             "ft": i["ft"], "hours": i["hours"]}
            for i in upcoming[:UPCOMING_CAP]
        ],
    }, occ_url


def build_trees(geom: dict) -> dict:
    rows = dcdata.query_features(TREES, geom, "1=1", TREE_FIELDS, "OBJECTID")
    rows = list({r["OBJECTID"]: r for r in rows}.values())
    stat = Counter((r["TBOX_STAT"] or "Blank").strip() for r in rows)
    planted = [r for r in rows if (r["TBOX_STAT"] or "").strip() == "Plant"]
    live = [r for r in planted if (r["CONDITION"] or "") != "Dead"]
    named = [r for r in live if r["CMMN_NM"] and not r["CMMN_NM"].strip().lower().startswith(("other", "unknown", "vacant"))]
    species = Counter(r["CMMN_NM"].strip() for r in named)
    five_years_ago_ms = (time.time() - 5 * 365 * DAY) * 1000
    big = sorted((r for r in live if r["DBH"] and 0 < r["DBH"] < 90), key=lambda r: -r["DBH"])[:5]
    conflict = sum(n for k, n in stat.items() if k.startswith(("Conflict", "Utility")))
    last_edit = max((r["LAST_EDITED_DATE"] or 0) for r in rows) if rows else 0
    return {
        "total": len(live),
        "species": len(species),
        "planted_5y": sum(1 for r in live if r["DATE_PLANT"] and r["DATE_PLANT"] > five_years_ago_ms),
        "empty_boxes": stat.get("Open", 0),
        "empty_boxes_note": (f"Counted from the layer's tree-box status (TBOX_STAT). 'Open' = an empty box ready to plant "
                             f"({stat.get('Open', 0)}). Not counted: 'Proposed' = planting scheduled ({stat.get('Proposed', 0)}), "
                             f"'Conflict'/'Utility' = empty but blocked ({conflict}), 'Retired' = box removed ({stat.get('Retired', 0)}). "
                             f"'total' is boxes with status 'Plant' whose condition is not Dead."),
        "condition": dict(Counter(r["CONDITION"] or "Not rated" for r in live).most_common()),
        "dead": len(planted) - len(live),
        "top_species": [{"name": n, "count": c} for n, c in species.most_common(8)],
        "biggest": [{"species": r["CMMN_NM"] or "Unidentified", "dbh_in": round(r["DBH"], 1), "block": _block(r["VICINITY"])} for r in big],
        "inventory_date": _day(last_edit) or "",
    }


def _quantile_stats(layer: str, where: str, geom: dict | None) -> dict[str, tuple[int, list[float]]]:
    """Server-side quantiles of days-to-close per request type: {type: (n, [q0..q100])}."""
    stats = [{"statisticType": "percentile_cont", "statisticParameters": {"value": q},
              "onStatisticField": "RESOLUTIONDATE - ADDDATE", "outStatisticFieldName": f"q{round(q * 100)}"} for q in QUANTILES]
    stats.append({"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"})
    params = {"where": where, "groupByFieldsForStatistics": "SERVICECODEDESCRIPTION", "outStatistics": json.dumps(stats), "f": "json"}
    if geom:
        params.update(dcdata._spatial(geom))
    data = dcdata._request(f"{layer}/query", params, post=True)
    out = {}
    for f in data.get("features", []):
        a = {k.lower(): v for k, v in f["attributes"].items()}
        qs = [a.get(f"q{round(q * 100)}") for q in QUANTILES]
        if a.get("n") and all(v is not None for v in qs):
            out[a["servicecodedescription"]] = (a["n"], qs)
    return out


def _cdf(x: float, qs: list[float]) -> float:
    """Piecewise-linear CDF through the known quantiles."""
    if x <= qs[0]:
        return 0.0
    if x >= qs[-1]:
        return 1.0
    for i in range(1, len(qs)):
        if x <= qs[i]:
            lo, hi = qs[i - 1], qs[i]
            frac = 0.5 if hi == lo else (x - lo) / (hi - lo)
            return QUANTILES[i - 1] + frac * (QUANTILES[i] - QUANTILES[i - 1])
    return 1.0


def _merged_median(parts: list[tuple[int, list[float]]]) -> float:
    """Median across yearly layers. One layer: the exact server median. Two: solve the n-weighted CDF = 0.5."""
    if len(parts) == 1:
        return parts[0][1][10]
    total = sum(n for n, _ in parts)
    lo, hi = min(qs[0] for _, qs in parts), max(qs[-1] for _, qs in parts)
    for _ in range(60):
        mid = (lo + hi) / 2
        if sum(n * _cdf(mid, qs) for n, qs in parts) / total < 0.5:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def build_service(geom: dict, now: float) -> tuple[list[dict], list[str]]:
    start = now - SR_DAYS * DAY
    layers = []
    for year in sorted({time.gmtime(start).tm_year, time.gmtime(now).tm_year}):
        url = dcdata.resolve_yearly_layer(SR_TITLE, year)
        if url:
            layers.append(url)
    if not layers:
        raise RuntimeError("no 311 layer found")
    where = f"{dcdata.date_where('ADDDATE', start, now)} AND {CLOSED}"

    # Neighborhood: a polygon spatial filter on the 400k-row current-year 311 layer routinely times out
    # (>90 s), so filter by the polygon's bounding box on the LATITUDE/LONGITUDE attributes (fast), then
    # keep points inside the polygon locally. Only type and two timestamps are kept; no address or text.
    xs = [p[0] for ring in geom["rings"] for p in ring]
    ys = [p[1] for ring in geom["rings"] for p in ring]
    bbox = (f"LATITUDE BETWEEN {min(ys)} AND {max(ys)} AND LONGITUDE BETWEEN {min(xs)} AND {max(xs)}")
    durations: dict[str, list[float]] = {}
    for layer in layers:
        offset = 0
        while True:
            data = dcdata._request(f"{layer}/query", {
                "where": f"{where} AND {bbox}",
                "outFields": "SERVICECODEDESCRIPTION,ADDDATE,RESOLUTIONDATE,LATITUDE,LONGITUDE",
                "returnGeometry": "false", "orderByFields": "OBJECTID",
                "resultOffset": offset, "resultRecordCount": 1000, "f": "json"}, post=True)
            batch = [f["attributes"] for f in data.get("features", [])]
            for r in batch:
                if r["LATITUDE"] is None or r["LONGITUDE"] is None or not r["SERVICECODEDESCRIPTION"]:
                    continue
                if point_in_rings(r["LONGITUDE"], r["LATITUDE"], geom["rings"]):
                    durations.setdefault(r["SERVICECODEDESCRIPTION"], []).append(
                        (r["RESOLUTIONDATE"] - r["ADDDATE"]) / 1000 / DAY)
            if not data.get("exceededTransferLimit") or not batch:
                break
            offset += len(batch)

    top = sorted(durations, key=lambda t: -len(durations[t]))[:SERVICE_TYPES]
    if not top:
        return [], layers
    # Citywide: server-side quantiles (no spatial filter, fast), merged across yearly layers.
    in_list = ",".join("'" + t.replace("'", "''") + "'" for t in top)
    city = [_quantile_stats(layer, f"{where} AND SERVICECODEDESCRIPTION IN ({in_list})", None) for layer in layers]
    out = []
    for t in top:
        there = [p[t] for p in city if t in p]
        out.append({
            "type": t,
            "median_days": round(statistics.median(durations[t]), 2),
            "city_median_days": round(_merged_median(there), 2) if there else None,
            "closed_n": len(durations[t]),
        })
    return out, layers


def build(geom: dict, hood: dict, now: float) -> dict:
    curb, occ_url = build_curb(geom, now)
    trees = build_trees(geom)
    service, sr_layers = build_service(geom, now)
    sources = [
        {"name": "DDOT TOPS: Occupancy Permits (Open Data DC)", "url": occ_url},
        {"name": "DDOT Urban Forestry Division: Urban Forestry Street Trees (Open Data DC)", "url": TREES},
    ] + [{"name": f"311 City Service Requests (OUC), layer {i + 1} of {len(sr_layers)}", "url": u} for i, u in enumerate(sr_layers)]
    return {
        "generated_at": iso(int(now * 1000)),
        "sources": sources,
        "curb": curb,
        "trees": trees,
        "service": service,
        "service_note": ("Median days from request to closure for requests opened in the last 12 months and already closed, "
                         "computed from request and resolution timestamps only (exact here; citywide from server-side quantiles). When the window spans two yearly layers "
                         "the citywide median is merged from each layer's quantiles (accurate to a few percent). Requests still open are "
                         "excluded, which biases recent months toward faster closes, equally here and citywide."),
    }


def _forbidden(obj, path="$") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).upper() in FORBIDDEN_KEYS:
                hits.append(f"{path}.{k}")
            hits += _forbidden(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _forbidden(v, f"{path}[{i}]")
    return hits


def check(section: dict) -> list[str]:
    errors = []
    if not section.get("generated_at"):
        errors.append("missing generated_at")
    if not section.get("sources"):
        errors.append("missing sources")
    curb, trees, service = section.get("curb") or {}, section.get("trees") or {}, section.get("service") or []
    for k in ("active_this_week", "starting_next_7d", "reserved_ft", "long_running_90d", "freshness_note", "by_type", "upcoming"):
        if k not in curb:
            errors.append(f"curb.{k} missing")
    if not curb.get("active_this_week"):
        errors.append("curb.active_this_week is zero")
    if len(curb.get("upcoming", [])) > UPCOMING_CAP:
        errors.append("curb.upcoming over cap")
    for u in curb.get("upcoming", []):
        if re.match(r"^\d+ (?!block)", u.get("block") or ""):
            errors.append(f"curb.upcoming has a house number: {u['block']}")
    for k in ("total", "species", "planted_5y", "empty_boxes", "empty_boxes_note", "condition", "top_species", "biggest", "inventory_date"):
        if k not in trees:
            errors.append(f"trees.{k} missing")
    if not trees.get("total"):
        errors.append("trees.total is zero")
    if len(service) < 4:
        errors.append(f"service has {len(service)} rows (need >= 4)")
    for s in service:
        for k in ("median_days", "city_median_days"):
            if s.get(k) is None or s[k] < 0:
                errors.append(f"service {s.get('type')}: bad {k} {s.get(k)}")
    errors += [f"forbidden key {h}" for h in _forbidden(section)]
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python ingest/streets.py <slug>", file=sys.stderr)
        return 2
    slug = sys.argv[1]
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if hood is None:
        print(f"unknown slug {slug}", file=sys.stderr)
        return 2
    t0 = time.time()
    geom = dcdata.hood_boundary(config, hood)
    section = build(geom, hood, time.time())
    out = ROOT / "ingest" / "_out" / f"streets-{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(section, indent=1), encoding="utf-8")
    c, t = section["curb"], section["trees"]
    print(f"{slug}: curb {c['active_this_week']} active, {c['starting_next_7d']} starting in 7d, {c['reserved_ft']:,} ft, "
          f"{c['long_running_90d']} long-running; {c['freshness_note']}")
    print(f"  by type: " + ", ".join(f"{b['type']} {b['count']}" for b in c["by_type"]))
    print(f"  trees {t['total']:,} living, {t['species']} species, {t['planted_5y']} planted 5y, {t['empty_boxes']} empty boxes, "
          f"{t.get('dead', 0)} dead, inventory {t['inventory_date']}")
    for s in section["service"]:
        print(f"  311 {s['type']}: {s['median_days']} d here vs {s['city_median_days']} d city (n={s['closed_n']})")
    print(f"  {time.time() - t0:.0f}s -> {out.relative_to(ROOT)}")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("streets ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
