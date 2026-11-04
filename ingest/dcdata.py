"""Small stdlib-only client for DC's ArcGIS REST services and Open Data DC search.

DC publishes many datasets as one layer per year ("Building Permits in 2026"),
so layer URLs change every January. `resolve_yearly_layer` finds the layer for a
given year by exact title through the Open Data DC search API, which keeps the
pipeline working across the rollover without a config edit.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

SEARCH_API = "https://opendata.dc.gov/api/search/v1/collections/dataset/items"
USER_AGENT = "dc-neighborhoods-ingest/0.1 (+https://petworth.org)"


class BoundaryRefused(RuntimeError):
    """DC's address layer refuses some multi-part boundaries outright (400) while taking each part alone."""


def _request(url: str, params: dict, post: bool = False, retries: int = 5, multipart: bool = False) -> dict:
    body = urllib.parse.urlencode(params).encode()
    for attempt in range(retries):
        try:
            if post:
                req = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT})
            else:
                req = urllib.request.Request(f"{url}?{body.decode()}", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.load(resp)
            # ArcGIS reports many failures as HTTP 200 with an "error" object.
            if isinstance(data, dict) and "error" in data:
                if multipart and data["error"].get("code") == 400:
                    raise BoundaryRefused(f"ArcGIS refused the boundary at {url}: {data['error']}")
                raise RuntimeError(f"ArcGIS error from {url}: {data['error']}")
            return data
        except BoundaryRefused:
            raise  # waiting won't change this answer; the caller asks one part at a time instead
        except (urllib.error.URLError, TimeoutError, ConnectionError, RuntimeError):  # incl. "connection reset by peer"
            if attempt == retries - 1:
                raise
            # DC's servers answer "503 wait timeout" under load; give them real time (5, 10, 20, 40 s).
            time.sleep(5 * 2 ** attempt)
    raise AssertionError("unreachable")


_layer_cache: dict[str, str] = {}


def resolve_yearly_layer(title_template: str, year: int) -> str | None:
    """Return the FeatureServer/MapServer layer URL whose title is exactly title_template.format(year=year)."""
    title = title_template.format(year=year)
    if title in _layer_cache:
        return _layer_cache[title]
    data = _request(SEARCH_API, {"q": title, "limit": 10})
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        if props.get("title", "").strip().lower() == title.lower() and props.get("url"):
            _layer_cache[title] = props["url"]
            return props["url"]
    return None


def boundary(layer_url: str, where: str, parts: int = 1) -> dict:
    """Fetch a neighborhood polygon (WGS84) as an Esri geometry dict. With parts > 1 the where clause must match
    exactly that many features (e.g. two adjacent ANC districts), and their rings are combined into one polygon."""
    data = _request(f"{layer_url}/query", {"where": where, "outFields": "*", "outSR": 4326, "f": "json"})
    features = data.get("features", [])
    if len(features) != parts:
        raise RuntimeError(f"expected {parts} boundary feature(s) for {where!r}, got {len(features)}")
    rings = [ring for f in features for ring in f["geometry"]["rings"]]
    return {"rings": rings, "spatialReference": {"wkid": 4326}}


MAX_QUERY_VERTICES = 3000


def hood_boundary(config: dict, hood: dict) -> dict:
    """The polygon for one entry of ingest/neighborhoods.json. A neighborhood may override the default layer
    (DC Health Planning Neighborhoods) when DC has no planning area for it, as with Friendship Heights."""
    return boundary(hood.get("boundary_layer", config["boundary_layer"]), hood["boundary_where"], hood.get("boundary_parts", 1))


def _thin(geometry: dict) -> dict:
    """DC's address layer refuses very detailed polygons (seen at about 3,300 vertices), so drop vertices evenly past
    the limit. Vertices on SMD boundaries sit metres apart, so this doesn't move what falls inside."""
    total = sum(len(r) for r in geometry["rings"])
    if total <= MAX_QUERY_VERTICES:
        return geometry
    step = total // MAX_QUERY_VERTICES + 1
    return {**geometry, "rings": [r[:-1][::step] + [r[0]] for r in geometry["rings"]]}


def _spatial(geometry: dict) -> dict:
    return {
        "geometry": json.dumps(_thin(geometry)),
        "geometryType": "esriGeometryPolygon",
        "inSR": 4326,
        "outSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
    }


def query_features(layer_url: str, geometry: dict, where: str, fields: list[str], order_by: str | None = None) -> list[dict]:
    """Page through every matching feature inside geometry, returning attribute dicts."""
    rows: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": ",".join(fields),
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": 1000,
            "f": "json",
            **_spatial(geometry),
        }
        if order_by:
            params["orderByFields"] = order_by
        try:
            data = _request(f"{layer_url}/query", params, post=True, multipart=len(geometry["rings"]) > 1)
        except BoundaryRefused:
            return _combine(layer_url, [{**geometry, "rings": [r]} for r in geometry["rings"]], where, fields, order_by)
        batch = [f["attributes"] for f in data.get("features", [])]
        rows.extend(batch)
        if not data.get("exceededTransferLimit") or not batch:
            return rows
        offset += len(batch)


def _combine(layer_url: str, parts: list[dict], where: str, fields: list[str], order_by: str | None) -> list[dict]:
    """The parts share edges, so a record exactly on one can come back twice."""
    rows, seen = [], set()
    for part in parts:
        for row in query_features(layer_url, part, where, fields, order_by):
            key = json.dumps(row, sort_keys=True)
            if key not in seen:
                seen.add(key)
                rows.append(row)
    for term in reversed((order_by or "").split(",")):
        if term.strip():
            name, *way = term.split()
            rows.sort(key=lambda r: (r.get(name) is None, r.get(name)), reverse=bool(way) and way[0].upper() == "DESC")
    return rows


def count_by(layer_url: str, geometry: dict, where: str, field: str) -> dict[str, int]:
    """Server-side GROUP BY count, so individual records never leave DC's servers."""
    stats = [{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]
    try:
        data = _request(
            f"{layer_url}/query",
            {
                "where": where,
                "groupByFieldsForStatistics": field,
                "outStatistics": json.dumps(stats),
                "f": "json",
                **_spatial(geometry),
            },
            post=True,
            multipart=len(geometry["rings"]) > 1,
        )
    except BoundaryRefused:
        totals: dict[str, int] = {}
        for r in geometry["rings"]:
            for k, v in count_by(layer_url, {**geometry, "rings": [r]}, where, field).items():
                totals[k] = totals.get(k, 0) + v
        return totals
    out: dict[str, int] = {}
    for f in data.get("features", []):
        # Some DC servers uppercase outStatisticFieldName, so match keys case-insensitively.
        attrs = {k.lower(): v for k, v in f["attributes"].items()}
        out[attrs[field.lower()]] = attrs["n"]
    return out


def date_where(field: str, start_epoch: float, end_epoch: float | None = None) -> str:
    start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_epoch))
    clause = f"{field} >= TIMESTAMP '{start}'"
    if end_epoch is not None:
        end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(end_epoch))
        clause += f" AND {field} < TIMESTAMP '{end}'"
    return clause
