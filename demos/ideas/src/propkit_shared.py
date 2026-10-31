"""Shared helpers for the property / license idea demos (#04, #05, #09, #16, #21, #24).

Stdlib only. Wraps ingest/dcdata.py for attribute-only (non-spatial) queries, fills TEMPLATE.html,
and draws small inline-SVG charts and maps. Owner fields are never requested by any caller:
every query passes an explicit field allowlist, and `assert_no_owner_fields` guards it.
"""

from __future__ import annotations

import html
import json
import math
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ingest"))
import dcdata  # noqa: E402
from run import hundred_block, permit_group, point_in_rings  # noqa: E402,F401

DAY = 86400
HOODS_LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13"
ITSPE_TITLE = "Integrated Tax System Public Extract"
CAMA_RES_TITLE = "Computer Assisted Mass Appraisal - Residential"
VB_TITLE = "Integrated Tax System Public Extract Vacant and Blighted"
VB_ADDR_TITLE = "Vacant and Blighted Building Addresses"
BBL_TITLE = "Basic Business Licenses"
ABCA_TITLE = "Alcohol License Business Locations"
OTR_APPEAL_URL = "https://otr.cfo.dc.gov/page/real-property-assessment-appeal-rights-application"

BANNED_FIELDS = {"OWNERNAME", "OWNNAME2", "CAREOFNAME", "ADDRESS1", "ADDRESS2", "CITYSTZIP", "SALE_CURR_OWNER",
                 "OWNER_NAME", "PERMIT_APPLICANT", "APPLICANT", "BUSINESSOWNERFIRSTNAME", "BUSINESSOWNERLASTNAME",
                 "BUSINESSOWNERMIDDLENAME", "AGENTFIRSTNAME", "AGENTLASTNAME", "AGENTMIDDLENAME", "INSPECTORNAME",
                 "DETAILS", "MORTGAGECO", "BILLINGADDRESS"}


def assert_no_owner_fields(fields: list[str]) -> None:
    bad = BANNED_FIELDS & {f.upper() for f in fields}
    if bad:
        raise ValueError(f"refusing to request personal fields: {sorted(bad)}")


_resolved: dict[str, str] = {}


def resolve(title: str) -> str:
    """Exact-title lookup through the Open Data DC search API; returns a layer URL."""
    if title in _resolved:
        return _resolved[title]
    data = dcdata._request(dcdata.SEARCH_API, {"q": title, "limit": 10})
    for f in data.get("features", []):
        p = f.get("properties", {})
        if p.get("title", "").strip().lower() == title.lower() and p.get("url"):
            url = p["url"].rstrip("/")
            if re.search(r"/(FeatureServer|MapServer)$", url):
                url += "/0"
            _resolved[title] = url
            return url
    raise RuntimeError(f"Open Data DC search found no dataset titled {title!r}")


def query(layer: str, where: str, fields: list[str], order_by: str | None = None, limit: int | None = None) -> list[dict]:
    """Attribute query with paging (no spatial filter)."""
    assert_no_owner_fields(fields)
    rows: list[dict] = []
    offset = 0
    while True:
        params = {"where": where, "outFields": ",".join(fields), "returnGeometry": "false",
                  "resultOffset": offset, "resultRecordCount": 1000 if limit is None else min(1000, limit - len(rows)), "f": "json"}
        if order_by:
            params["orderByFields"] = order_by
        data = dcdata._request(f"{layer}/query", params, post=True)
        batch = [f["attributes"] for f in data.get("features", [])]
        rows.extend(batch)
        if not batch or not data.get("exceededTransferLimit") or (limit is not None and len(rows) >= limit):
            return rows
        offset += len(batch)


def spatial(layer: str, geom: dict, where: str, fields: list[str], order_by: str | None = None) -> list[dict]:
    assert_no_owner_fields(fields)
    return dcdata.query_features(layer, geom, where, fields, order_by)


def count(layer: str, where: str, geom: dict | None = None) -> int:
    params = {"where": where, "returnCountOnly": "true", "f": "json"}
    if geom:
        params.update(dcdata._spatial(geom))
    return int(dcdata._request(f"{layer}/query", params, post=True).get("count", 0))


def group_count(layer: str, where: str, fields: list[str], geom: dict | None = None) -> list[dict]:
    stats = [{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]
    params = {"where": where, "groupByFieldsForStatistics": ",".join(fields), "outStatistics": json.dumps(stats), "f": "json"}
    if geom:
        params.update(dcdata._spatial(geom))
    data = dcdata._request(f"{layer}/query", params, post=True)
    out = []
    for f in data.get("features", []):
        a = {k.lower(): v for k, v in f["attributes"].items()}
        out.append({**{fld: a.get(fld.lower()) for fld in fields}, "n": a.get("n", 0)})
    return out


def boundary(name: str) -> dict:
    return dcdata.boundary(HOODS_LAYER, f"DC_HPN_NAME='{name}'")


def bbox(geom: dict) -> tuple[float, float, float, float]:
    xs = [p[0] for r in geom["rings"] for p in r]
    ys = [p[1] for r in geom["rings"] for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def ts(epoch: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(epoch))


def day(ms_or_str) -> str | None:
    """ArcGIS epoch-ms or 'YYYY-MM-DD' DateOnly -> 'YYYY-MM-DD'."""
    if ms_or_str is None:
        return None
    if isinstance(ms_or_str, str):
        return ms_or_str[:10]
    return time.strftime("%Y-%m-%d", time.gmtime(ms_or_str / 1000))


def nice_date(iso_day: str | None) -> str:
    if not iso_day:
        return "—"
    t = time.strptime(iso_day[:10], "%Y-%m-%d")
    return time.strftime("%b %d, %Y", t).replace(" 0", " ")


def money(v: float | None, short: bool = False) -> str:
    if v is None:
        return "—"
    if short:
        if abs(v) >= 1e6:
            return f"${v / 1e6:.2f}M".replace(".00M", "M")
        if abs(v) >= 1e3:
            return f"${v / 1e3:.0f}K"
    return f"${v:,.0f}"


def median(vals: list[float]) -> float | None:
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


def clean_premise(addr: str | None) -> str:
    """'5128 KANSAS AVE NW WASHINGTON DC 20011' -> '5128 Kansas Ave NW'."""
    if not addr:
        return ""
    a = re.sub(r"\s+WASHINGTON\s+DC.*$", "", addr.strip(), flags=re.I)
    a = re.sub(r"\s+", " ", a)
    return titleish(a)


def titleish(s: str) -> str:
    keep = {"NW", "NE", "SW", "SE"}
    out = []
    for w in s.split(" "):
        if w.upper() in keep:
            out.append(w.upper())
        elif re.match(r"^\d+(ST|ND|RD|TH)$", w, re.I):
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out)


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def fill(values: dict[str, str]) -> str:
    page = (ROOT / "demos" / "ideas" / "TEMPLATE.html").read_text(encoding="utf-8")
    page = re.sub(r"<!--\s*Template for idea demos.*?-->\n", "", page, flags=re.S)
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        raise RuntimeError(f"unfilled placeholders: {left}")
    return page


def base_values(rank: int, idea_id: str, score: str, provenance: str, pulled: str) -> dict[str, str]:
    live = provenance == "live"
    return {
        "RANK": str(rank),
        "IDEA_ID": idea_id,
        "SCORE": score,
        "PROVENANCE_CLASS": provenance,
        "PROVENANCE_TEXT": f"Live data · Open Data DC · pulled {pulled}" if live else "Sample data · illustrative",
        "GENERATED_UTC": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
    }


def write(path: Path, page: str) -> None:
    for bad in ("OWNERNAME", "OWNER_NAME", "OWNNAME2", "CAREOFNAME", "PERMIT_APPLICANT", "INSPECTORNAME"):
        if bad in page:
            raise RuntimeError(f"{path.name}: banned field name {bad} in output")
    path.write_text(page, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(page.encode()) / 1024:.0f} KB)")


# ---------------------------------------------------------------- SVG helpers

def svg_bars(items: list[tuple[str, float]], width: int = 640, bar_h: int = 22, fmt=lambda v: f"{v:,.0f}",
             color: str = "var(--accent)", label_w: int = 210, title: str = "") -> str:
    """Horizontal bar chart. items: (label, value)."""
    if not items:
        return '<p class="muted">No records in this window.</p>'
    mx = max(v for _, v in items) or 1
    h = len(items) * (bar_h + 6) + 4
    plot_w = width - label_w - 70
    parts = [f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="{esc(title)}" style="max-width:{width}px">']
    for i, (lab, v) in enumerate(items):
        y = i * (bar_h + 6) + 2
        w = max(1.5, plot_w * v / mx)
        lab_s = lab if len(lab) <= 34 else lab[:32] + "…"
        parts.append(f'<text x="{label_w - 8}" y="{y + bar_h * .68:.1f}" text-anchor="end" style="font-size:12px">{esc(lab_s)}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{color}"><title>{esc(lab)}: {esc(fmt(v))}</title></rect>')
        parts.append(f'<text x="{label_w + w + 6:.1f}" y="{y + bar_h * .68:.1f}" style="font-size:12px;fill:var(--ink)">{esc(fmt(v))}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_columns(items: list[tuple[str, float]], width: int = 640, height: int = 180, fmt=lambda v: f"{v:,.0f}",
                color: str = "var(--accent)", title: str = "", highlight_last: bool = False) -> str:
    """Vertical column chart with labels under each column (e.g. months)."""
    if not items:
        return '<p class="muted">No records in this window.</p>'
    mx = max(v for _, v in items) or 1
    n = len(items)
    pad_l, pad_b, pad_t = 6, 24, 18
    cw = (width - pad_l * 2) / n
    ph = height - pad_b - pad_t
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="{esc(title)}">']
    parts.append(f'<line x1="0" x2="{width}" y1="{pad_t + ph}" y2="{pad_t + ph}" stroke="var(--line)"/>')
    for i, (lab, v) in enumerate(items):
        bh = ph * v / mx
        x = pad_l + i * cw + cw * 0.14
        fill = "var(--brick)" if highlight_last and i == n - 1 else color
        parts.append(f'<rect x="{x:.1f}" y="{pad_t + ph - bh:.1f}" width="{cw * .72:.1f}" height="{max(bh, 1):.1f}" rx="2" fill="{fill}"><title>{esc(lab)}: {esc(fmt(v))}</title></rect>')
        parts.append(f'<text x="{x + cw * .36:.1f}" y="{pad_t + ph - bh - 4:.1f}" text-anchor="middle" style="font-size:10px">{esc(fmt(v))}</text>')
        parts.append(f'<text x="{x + cw * .36:.1f}" y="{height - 7}" text-anchor="middle" style="font-size:10px">{esc(lab)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_lines(series: dict[str, list[float | None]], labels: list[str], width: int = 640, height: int = 210,
              fmt=lambda v: money(v, True), colors: list[str] | None = None, title: str = "") -> str:
    """Multi-series line chart over shared x labels; None values break the line."""
    colors = colors or ["var(--accent)", "var(--brick)", "var(--gold)"]
    vals = [v for s in series.values() for v in s if v is not None]
    if not vals:
        return '<p class="muted">Not enough sales to chart.</p>'
    lo, hi = min(vals) * 0.92, max(vals) * 1.05
    pad_l, pad_r, pad_t, pad_b = 58, 14, 12, 26
    pw, ph = width - pad_l - pad_r, height - pad_t - pad_b
    n = len(labels)
    xs = [pad_l + (pw * i / (n - 1) if n > 1 else pw / 2) for i in range(n)]
    y = lambda v: pad_t + ph - ph * (v - lo) / ((hi - lo) or 1)  # noqa: E731
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="{esc(title)}">']
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        parts.append(f'<line x1="{pad_l}" x2="{width - pad_r}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="var(--line)"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{esc(fmt(v))}</text>')
    step = max(1, n // 8)
    for i in range(0, n, step):
        parts.append(f'<text x="{xs[i]:.1f}" y="{height - 6}" text-anchor="middle">{esc(labels[i])}</text>')
    for ci, (name, s) in enumerate(series.items()):
        c = colors[ci % len(colors)]
        seg: list[str] = []
        for i, v in enumerate(s):
            if v is None:
                if len(seg) > 1:
                    parts.append(f'<polyline fill="none" stroke="{c}" stroke-width="2.2" points="{" ".join(seg)}"/>')
                seg = []
                continue
            seg.append(f"{xs[i]:.1f},{y(v):.1f}")
            parts.append(f'<circle cx="{xs[i]:.1f}" cy="{y(v):.1f}" r="2.6" fill="{c}"><title>{esc(name)} {esc(labels[i])}: {esc(fmt(v))}</title></circle>')
        if len(seg) > 1:
            parts.append(f'<polyline fill="none" stroke="{c}" stroke-width="2.2" points="{" ".join(seg)}"/>')
    parts.append("</svg>")
    legend = " ".join(f'<span style="white-space:nowrap"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:{colors[i % len(colors)]}"></span> {esc(n)}</span>'
                      for i, n in enumerate(series))
    return "".join(parts) + f'<p class="muted" style="font-size:.82rem;margin:.3rem 0 0">{legend}</p>'


def svg_map(geom: dict, points: list[dict], width: int = 640, title: str = "", radius: float = 4.5) -> str:
    """Neighborhood outline plus dots. points: {lat, lon, color?, label?}."""
    x0, y0, x1, y1 = bbox(geom)
    k = math.cos(math.radians((y0 + y1) / 2))
    sx = (x1 - x0) * k
    sy = y1 - y0
    pad = 10
    height = int((width - 2 * pad) * sy / sx + 2 * pad)
    px = lambda lon: pad + (lon - x0) * k / sx * (width - 2 * pad)  # noqa: E731
    py = lambda lat: pad + (y1 - lat) / sy * (height - 2 * pad)  # noqa: E731
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="{esc(title)}" style="max-width:{width}px;display:block;margin:auto">']
    for ring in geom["rings"]:
        pts = " ".join(f"{px(x):.1f},{py(yy):.1f}" for x, yy in ring)
        parts.append(f'<polygon points="{pts}" fill="var(--soft)" stroke="var(--accent)" stroke-width="1.5"/>')
    for p in points:
        if p.get("lat") is None or p.get("lon") is None:
            continue
        c = p.get("color", "var(--brick)")
        parts.append(f'<circle cx="{px(p["lon"]):.1f}" cy="{py(p["lat"]):.1f}" r="{p.get("r", radius)}" fill="{c}" fill-opacity=".85" stroke="var(--card)" stroke-width="1"><title>{esc(p.get("label", ""))}</title></circle>')
    parts.append("</svg>")
    return "".join(parts)
