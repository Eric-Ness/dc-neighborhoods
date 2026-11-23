"""Crime counts for the private crime site (crime.georgetowndc.org): DC, its 8 wards and every live neighborhood.

Counts only, grouped on DC's server, so no incident record (block, time, coordinates) is ever downloaded or stored.
Each count is by month of MPD's report date, for the last 24 whole months, split by DC Code offense.

    python ingest/crime.py           # write crime/src/data/crime.json
    python ingest/crime.py --check   # and fail if the result looks wrong
"""
from __future__ import annotations

import calendar
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dcdata  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "ingest" / "neighborhoods.json"
OUT = ROOT / "crime" / "src" / "data" / "crime.json"
CRIME_TITLE = "Crime Incidents in {year}"
MONTHS = 24
# MPD's violent group; everything else in the layer is property crime.
VIOLENT = ["HOMICIDE", "SEX ABUSE", "ASSAULT W/DANGEROUS WEAPON", "ROBBERY"]
WARDS = [str(w) for w in range(1, 9)]
SOURCE = "Open Data DC, Crime Incidents (MPD). Preliminary counts by report date and DC Code offense, not FBI NIBRS figures."


def month_bounds(now: float) -> list[tuple[str, float, float]]:
    """The last MONTHS whole calendar months (UTC, which is how DC's yearly layers split), oldest first."""
    t = time.gmtime(now)
    out = []
    for k in range(MONTHS, 0, -1):
        y, m = t.tm_year, t.tm_mon - k
        while m <= 0:
            m += 12
            y -= 1
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        out.append((f"{y}-{m:02d}", calendar.timegm((y, m, 1, 0, 0, 0)), calendar.timegm((ny, nm, 1, 0, 0, 0))))
    return out


def grouped(layer: str, where: str, fields: str) -> list[dict]:
    """Citywide GROUP BY count (no boundary), keys lowercased since some DC servers uppercase them."""
    stats = [{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]
    data = dcdata._request(f"{layer}/query", {"where": where, "groupByFieldsForStatistics": fields,
                                              "outStatistics": json.dumps(stats), "f": "json"}, post=True)
    if "features" not in data:
        raise RuntimeError(f"no features in DC's answer: {str(data)[:200]}")
    return [{k.lower(): v for k, v in f["attributes"].items()} for f in data["features"]]


def series(by_month: list[dict[str, int]]) -> dict[str, list[int]]:
    """[{offense: n} per month] -> {offense: [n per month]}, offenses sorted by name."""
    offenses = sorted({o for c in by_month for o in c})
    return {o: [c.get(o, 0) for c in by_month] for o in offenses}


def main() -> int:
    now = time.time()
    months = month_bounds(now)
    years = {int(m[:4]) for m, _, _ in months}
    found = {y: dcdata.resolve_yearly_layer(CRIME_TITLE, y) for y in years}
    layers: dict[int, str] = {y: u for y, u in found.items() if u}
    missing = sorted(years - set(layers))
    if missing:
        print(f"no crime layer for {missing}", file=sys.stderr)
        return 1

    def citywide(month):
        label, a, b = month
        rows = grouped(layers[int(label[:4])], dcdata.date_where("REPORT_DAT", a, b), "WARD,OFFENSE")
        out: dict[str, dict[str, int]] = {}
        for r in rows:
            ward = r["ward"] if r["ward"] in WARDS else "unknown"
            offense = r["offense"] or "UNKNOWN"
            out.setdefault(ward, {})[offense] = out.get(ward, {}).get(offense, 0) + r["n"]
        return out

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    hoods = [h for h in config["neighborhoods"] if h["enabled"]]

    def area(hood):
        geom = dcdata.hood_boundary(config, hood)
        by_month = [dcdata.count_by(layers[int(label[:4])], geom, dcdata.date_where("REPORT_DAT", a, b), "OFFENSE")
                    for label, a, b in months]
        print(f"  {hood['slug']}: {sum(sum(c.values()) for c in by_month)}", flush=True)
        return {"slug": hood["slug"], "name": hood["name"], "host": hood["hosts"][0], "offenses": series(by_month)}

    with ThreadPoolExecutor(6) as ex:
        city = list(ex.map(citywide, months))
        areas = list(ex.map(area, hoods))

    dc = [{} for _ in months]
    for i, m in enumerate(city):
        for counts in m.values():
            for o, n in counts.items():
                dc[i][o] = dc[i].get(o, 0) + n
    data = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "months": [m for m, _, _ in months],
        "violent": VIOLENT,
        "source": SOURCE,
        "dc": {"offenses": series(dc)},
        "wards": [{"ward": w, "offenses": series([m.get(w, {}) for m in city])} for w in WARDS],
        "unknown_ward": series([m.get("unknown", {}) for m in city]),
        "areas": sorted(areas, key=lambda a: a["name"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    total = lambda s: sum(map(sum, s["offenses"].values()))
    print(f"crime: DC {total(data['dc'])} reports over {MONTHS} months, {len(areas)} neighborhoods")

    if "--check" in sys.argv:
        errors = check(data)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print("crime verified")
    return 0


def check(data: dict) -> list[str]:
    errors = []
    dc = data["dc"]["offenses"]
    monthly = [sum(v[i] for v in dc.values()) for i in range(MONTHS)]
    # DC logs well over 1,000 reports a month; far fewer means a layer answered empty or partly.
    errors += [f"DC {m}: only {n} reports" for m, n in zip(data["months"], monthly) if n < 800]
    wards = [data["unknown_ward"]] + [w["offenses"] for w in data["wards"]]
    for o, v in dc.items():
        if [sum(w.get(o, [0] * MONTHS)[i] for w in wards) for i in range(MONTHS)] != v:
            errors.append(f"wards do not add up to DC for {o}")
    for a in data["areas"]:
        if not any(map(sum, a["offenses"].values())):
            errors.append(f"{a['slug']}: no reports in {MONTHS} months")
    # Only counts belong here: the only strings are names, offenses, labels and the source line.
    text = json.dumps(data)
    for field in ("BLOCK", "LATITUDE", "LONGITUDE", "CCN", "XBLOCK", "START_DATE"):
        if f'"{field.lower()}"' in text.lower():
            errors.append(f"forbidden field {field} in output")
    return errors


if __name__ == "__main__":
    sys.exit(main())
