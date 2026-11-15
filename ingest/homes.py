"""`homes` section: recorded market sales of houses and condos for one neighborhood.

Sources (both from DC's Office of Tax and Revenue, resolved by exact title through Open Data DC):
- Integrated Tax System Public Extract (ITSPE): address, use code, current assessment, last recorded
  sale price/date and OTR's sale acceptance code. A table with no geometry, so sales are tied to the
  neighborhood through OTR's own assessment neighborhood (NBHDNAME, optionally a SUBNBHD), set per slug below.
- CAMA Residential: building area (GBA) and bedrooms, joined by SSL, for house sales only.
- Address Points (DC MAR, fixed URL): only used to measure how well the chosen OTR neighborhoods line up
  with the DC Health boundary (which tax squares have an address point inside the polygon).

Owner fields exist in ITSPE and are never requested: every query passes an explicit field allowlist,
and `_fields` refuses anything personal.

Standalone: python ingest/homes.py petworth
"""

from __future__ import annotations

import datetime
import json
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
from run import iso  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

ITSPE_TITLE = "Integrated Tax System Public Extract"
CAMA_RES_TITLE = "Computer Assisted Mass Appraisal - Residential"
ADDRESS_POINTS = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Location_WebMercator/MapServer/0"

HOUSE_CODES = {"011": "Rowhouse", "012": "Detached", "013": "Semi-detached"}
CONDO_CODES = {"016": "Condo (horizontal)", "017": "Condo (vertical)"}
# Same filter as demos #04/#05: only OTR's "Market Sale" acceptance code. "Multi-Market Sale" is left out
# because its price covers several parcels. Demo #05 used a $75K floor (#04 used $150K for houses only);
# we use #05's so the numbers line up with it. The floor only drops nominal-price deeds.
MARKET_CODE = "Market Sale"
PRICE_FLOOR = 75_000
RECENT_DAYS = 60
RECENT_CAP = 40
MIN_MONTH_SALES = 3  # a month with fewer sales of the primary home type gets a count but no median

DAY = 86400

# Per-slug OTR assessment neighborhoods. Each entry is (NBHDNAME, SUBNBHD or None for all sub-areas).
# Overlap figures were measured 2026-10-31 by taking every tax square with a DC MAR address point inside
# the DC Health polygon and grouping ITSPE residential parcels (use codes 011-017) on those squares;
# build() re-measures them every run and reports them in area_note.
HOODS = {
    "petworth": {
        # OTR "Petworth" (NBHD 042, sub-areas A-C) is the obvious match, and what demo #05 used. It is larger
        # than the DC Health PETWORTH area: in the 2026-10 check about 61% of its residential parcels sat on
        # squares inside the boundary (the rest is mostly north and east of it), while ~94% of residential
        # parcels on in-boundary squares were OTR Petworth (the remainder: Columbia Heights C, Woodridge, etc.).
        "otr": [("Petworth", None)],
        "label": "OTR assessment neighborhood \"Petworth\" (all sub-areas)",
    },
    "tenleytown": {
        # The DC Health TENLEYTOWN planning area also covers Friendship Heights and AU Park. In the 2026-10 check,
        # in-boundary squares held residential parcels from exactly six OTR areas, all included here:
        # American University A, B, C (AU Park / Tenleytown west of Wisconsin), Chevy Chase sub-area A
        # (Friendship Heights / east of Wisconsin up to the line; Chevy Chase B-E had zero parcels inside),
        # North Cleveland Park and Wakefield (east toward Connecticut Ave). Close to 100% of their parcels sit
        # on squares touching the boundary; squares that straddle the edge make that an upper bound.
        "otr": [
            ("American University", None),
            ("Chevy Chase", "A"),
            ("North Cleveland Park", None),
            ("Wakefield", None),
        ],
        "label": "OTR assessment neighborhoods \"American University\" (all), \"Chevy Chase\" sub-area A, "
                 "\"North Cleveland Park\" and \"Wakefield\"",
    },    "adamsmorgan": {
        # No OTR area is called Adams Morgan. In the 2026-10-31 check, 96% of residential parcels on squares
        # inside the DC Health ADAMS MORGAN area were in five OTR sub-areas: Old City 2 D (30%), Mount
        # Pleasant C (21%), Kalorama C (20%), Kalorama B (15%) and Mount Pleasant B (9%). All of Kalorama B/C
        # and Mount Pleasant B/C sit inside; Old City 2 D is split (about 46% inside, the rest toward Dupont
        # and U Street), so it's included and the per-run fit note reports the overlap. The other ~4% were
        # scattered matches across the city (square numbers reused with suffixes), not real overlap.
        "otr": [
            ("Kalorama", "B"), ("Kalorama", "C"),
            ("Mount Pleasant", "B"), ("Mount Pleasant", "C"),
            ("Old City 2", "D"),
        ],
        "label": "OTR assessment sub-areas Kalorama B and C, Mount Pleasant B and C, and Old City 2 D",
        # Mostly apartments: 234 condo sales against 26 house sales in the 12 months to 2026-10, too few houses
        # for a monthly trend. Condos lead the section here.
        "primary": "condo",
    },
    "friendshipheights": {
        # Boundary is ANC districts 3E03+3E04 (DC has no Friendship Heights planning area). In the 2026-11-01
        # check, residential parcels on in-boundary squares were OTR Chevy Chase A (63%), American University A
        # (30%) and American University B (7%). B is left out: it is mostly AU Park, outside these districts.
        # Both included areas extend past the districts (toward Tenleytown and Chevy Chase DC); the per-run fit
        # note reports how far.
        "otr": [("Chevy Chase", "A"), ("American University", "A")],
        "label": "OTR assessment sub-areas Chevy Chase A and American University A",
    },
    # The nine below were measured 2026-11-01 with ingest/setup_hood.py. Rule: keep a sub-area that holds at
    # least 5% of in-boundary homes, unless less than about 30% of the sub-area itself lies inside.
    "capitolhill": {
        # Capitol Hill A/B/C are 85-100% inside; Old City 1 M is 70% inside. Old City 1 C (29% inside) is left out.
        "otr": [("Capitol Hill", "A"), ("Capitol Hill", "B"), ("Capitol Hill", "C"), ("Old City 1", "M")],
        "label": "OTR assessment sub-areas Capitol Hill A, B and C and Old City 1 M",
    },
    "columbiaheights": {
        # D and C are 93-100% inside, A 53%. E (26% inside) is left out.
        "otr": [("Columbia Heights", "D"), ("Columbia Heights", "C"), ("Columbia Heights", "A")],
        "label": "OTR assessment sub-areas Columbia Heights A, C and D",
    },
    "georgetown": {
        # Boundary is the Georgetown Historic District, which holds every OTR Georgetown sub-area (A-J), each
        # wholly inside. Observatory Circle (13% inside) is left out.
        "otr": [("Georgetown", None)],
        "label": "OTR assessment neighborhood \"Georgetown\" (all sub-areas)",
    },
    "chevychase": {
        # Boundary is ANC 3/4G. Chevy Chase B-E and Hawthorne are 84-100% inside; A is 49% (it is shared with
        # Friendship Heights, west of Wisconsin) and holds 19% of in-boundary homes, so it is kept.
        "otr": [("Chevy Chase", None), ("Hawthorne", None)],
        "label": "OTR assessment neighborhoods \"Chevy Chase\" (all sub-areas) and \"Hawthorne\"",
    },
    "anacostia": {
        # Anacostia A 96% inside, Barry Farms 85%, Randle Heights B 56%. Anacostia B (24% inside) is left out.
        "otr": [("Anacostia", "A"), ("Barry Farms", None), ("Randle Heights", "B")],
        "label": "OTR assessment sub-areas Anacostia A and Randle Heights B, and Barry Farms",
    },
    "clevelandpark": {
        # The historic district holds parts of two OTR areas: Cleveland Park (39% of it inside: the area runs
        # north and west of the district) and Forest Hills (24%: the Connecticut Ave apartment houses).
        "otr": [("Cleveland Park", None), ("Forest Hills", None)],
        "label": "OTR assessment neighborhoods Cleveland Park and Forest Hills",
    },
    "dupontcircle": {
        # 73% of homes in the historic district are OTR Old City 2 D (78% of it inside). Central (20% inside,
        # mostly downtown condos) is left out. Old City 2 D is shared with Adams Morgan's southern edge.
        "otr": [("Old City 2", "D")],
        "label": "OTR assessment sub-area Old City 2 D",
        "primary": "condo",  # 4,062 condo parcels against 261 houses
    },
    "hstreet": {
        # Old City 1 J 87% inside, L 57%, F 51%. K (22% inside) is left out.
        "otr": [("Old City 1", "L"), ("Old City 1", "F"), ("Old City 1", "J")],
        "label": "OTR assessment sub-areas Old City 1 F, J and L",
    },
    "navyyard": {
        # Old City 1 E (84% inside) and the Washington Navy Yard area (wholly inside). Mostly apartment and condo
        # buildings: 839 condo parcels against 301 houses.
        "otr": [("Old City 1", "E"), ("Washington Navy Yard", None)],
        "label": "OTR assessment sub-areas Old City 1 E and Washington Navy Yard",
        # Mostly rental apartments: about 15 house and 27 condo sales a year, too few of either for a monthly
        # trend, so houses and condos are counted together.
        "primary": "all",
    },
    # The ten below were measured 2026-11-01 with ingest/setup_hood.py, same rule as above.
    "brookland": {
        # Boundary 5B02-5B06 + 5F02 + 5A04: Brookland C (76% inside), E (45%) and D (100%), Woodridge A (44%).
        "otr": [("Brookland", "C"), ("Brookland", "E"), ("Brookland", "D"), ("Woodridge", "A")],
        "label": "OTR assessment sub-areas Brookland C, D and E and Woodridge A",
    },
    "chinatown": {
        # Central (44% inside) and Old City 2 B (76%, shared with Shaw at its northern edge). Downtown is nearly all
        # condos: 4,273 condo parcels against 203 houses.
        "otr": [("Central", None), ("Old City 2", "B")],
        "label": "OTR assessment neighborhood Central and sub-area Old City 2 B",
        "primary": "condo",
    },
    "gloverpark": {
        # Glover Park and Wesley Heights B are wholly inside; Observatory Circle 47%.
        "otr": [("Glover Park", None), ("Wesley Heights", "B"), ("Observatory Circle", None)],
        "label": "OTR assessment neighborhoods Glover Park and Observatory Circle and sub-area Wesley Heights B",
    },
    "lenfantplaza": {
        # The Southwest BID holds one OTR area, R. L. A. SW (69% inside; the rest is toward the Wharf).
        "otr": [("R. L. A. SW", None)],
        "label": "OTR assessment neighborhood R. L. A. SW",
        "primary": "condo",
    },
    "noma": {
        # Only Eckington B is a real match (28% inside, 64% of in-boundary homes); the other areas setup_hood lists are
        # square numbers reused across the city. NoMa's big buildings are mostly rentals, so sales are few.
        "otr": [("Eckington", "B")],
        "label": "OTR assessment sub-area Eckington B",
        # About 23 house and 25 condo sales a year: too few of either for a monthly trend, so counted together.
        "primary": "all",
    },
    "palisades": {
        # The Kent/Palisades planning area also takes in Wesley Heights, Spring Valley, Foxhall and Berkley; every
        # sub-area below is wholly inside. Wesley Heights B is shared with Glover Park.
        "otr": [("Palisades", None), ("Wesley Heights", "A"), ("Wesley Heights", "B"), ("Spring Valley", "B"),
                ("Berkley", "A"), ("Kent", "B"), ("Kent", "C"), ("Foxhall", None)],
        "label": "OTR assessment neighborhoods Palisades and Foxhall and sub-areas Wesley Heights A and B, "
                 "Spring Valley B, Berkley A and Kent B and C",
    },
    "shaw": {
        # ANC 2G: Old City 2 B (48% inside) and G (39%). Old City 2 C is mostly Logan Circle (73% there), so it stays out.
        "otr": [("Old City 2", "B"), ("Old City 2", "G")],
        "label": "OTR assessment sub-areas Old City 2 B and G",
        # About 31 house and 50 condo sales a year; houses alone leave half the months blank, so counted together.
        "primary": "all",
    },
    "logancircle": {
        # ANC 2F: Old City 2 C (73% inside) and E (70%).
        "otr": [("Old City 2", "C"), ("Old City 2", "E")],
        "label": "OTR assessment sub-areas Old City 2 C and E",
        "primary": "condo",
    },
    "ustreet": {
        # Old City 2 F and LeDroit Park A wholly inside, Columbia Heights E 35%, Old City 2 G 39% (shared with Shaw).
        # Old City 2 E (27%) is mostly Logan Circle and stays out.
        "otr": [("Old City 2", "F"), ("Ledroit Park", "A"), ("Columbia Heights", "E"), ("Old City 2", "G")],
        "label": "OTR assessment sub-areas Old City 2 F and G, LeDroit Park A and Columbia Heights E",
    },
    "vanness": {
        # Forest Hills (35% inside), Wakefield (72%) and North Cleveland Park (47%); the last two are shared with Tenleytown,
        # whose planning area runs to Connecticut Avenue.
        "otr": [("Forest Hills", None), ("Wakefield", None), ("North Cleveland Park", None)],
        "label": "OTR assessment neighborhoods Forest Hills, Wakefield and North Cleveland Park",
    },
    # The eight below were measured 2026-11-02 with ingest/setup_hood.py, same rule as above.
    "bloomingdale": {
        # LeDroit Park B and Old City 2 A (86%), Eckington A (87%) and B (51%), Brookland E (35%). The planning area runs
        # east to the tracks, so it also takes in Eckington and Edgewood.
        "otr": [("Ledroit Park", "B"), ("Old City 2", "A"), ("Eckington", "A"), ("Eckington", "B"), ("Brookland", "E")],
        "label": "OTR assessment sub-areas LeDroit Park B, Old City 2 A, Eckington A and B and Brookland E",
    },
    "foggybottom": {
        # Foggy Bottom is 96% inside. Central (8%) and Old City 2 D (3%) barely touch it. Mostly condos.
        "otr": [("Foggy Bottom", None)],
        "label": "OTR assessment neighborhood Foggy Bottom",
        # About 5 house and 27 condo sales a year: too few for a monthly trend of either alone.
        "primary": "all",
    },
    "hilleast": {
        # Old City 1 A (91% inside), B and D (100%), C (71%). M (30%) is mostly Capitol Hill's.
        "otr": [("Old City 1", "A"), ("Old City 1", "B"), ("Old City 1", "C"), ("Old City 1", "D")],
        "label": "OTR assessment sub-areas Old City 1 A, B, C and D",
    },
    "kingmanpark": {
        # Old City 1 H and G (100% inside), F (73%), K (58%).
        "otr": [("Old City 1", "F"), ("Old City 1", "G"), ("Old City 1", "H"), ("Old City 1", "K")],
        "label": "OTR assessment sub-areas Old City 1 F, G, H and K",
    },
    "mountpleasant": {
        # Mount Pleasant A is 97% inside.
        "otr": [("Mount Pleasant", "A")],
        "label": "OTR assessment sub-area Mount Pleasant A",
    },
    "stadiumarmory": {
        # Almost no homes inside (about 170 parcels): it's the RFK campus, the Armory and Congressional Cemetery. The two
        # sub-areas touching it (8% and 5% inside) are mostly Hill East's, so these are really the rowhouses next door;
        # the page's area note and fit figures say so.
        "otr": [("Old City 1", "A"), ("Old City 1", "B")],
        "label": "OTR assessment sub-areas Old City 1 A and B, the rowhouse blocks just west of the stadium grounds",
    },
    "trinidad": {
        # Trinidad A, B and C and Brentwood B are all wholly inside.
        "otr": [("Trinidad", "A"), ("Trinidad", "B"), ("Trinidad", "C"), ("Brentwood", "B")],
        "label": "OTR assessment sub-areas Trinidad A, B and C and Brentwood B",
    },
    "woodleypark": {
        # Boundary is ANC 3C01, 3C02, 3C03 and 3C07. Garfield is wholly inside; Woodley and Massachusetts Avenue Heights 79%.
        # Observatory Circle (13%) is left out.
        "otr": [("Garfield", None), ("Woodley", None), ("Massachusetts Avenue Heights", None)],
        "label": "OTR assessment neighborhoods Garfield, Woodley and Massachusetts Avenue Heights",
        # About 24 house and 21 condo sales a year, so counted together.
        "primary": "all",
    },
    "brightwood": {
        # Boundary is ANC 4A04-07, 4B05 and 4D01-03. Brightwood A is 87% inside, Brightwood C 51% (the rest is on the Takoma
        # site's side) and Petworth B 44%, which holds Kennedy Street and Brightwood Park and is shared with the Petworth site.
        "otr": [("Brightwood", "A"), ("Brightwood", "C"), ("Petworth", "B")],
        "label": "OTR assessment sub-areas Brightwood A and C and Petworth B",
    },
    "deanwood": {
        # Boundary is ANC 7C. Deanwood A is only 30% inside, so it's left out.
        "otr": [("Deanwood", "B"), ("Deanwood", "C"), ("Deanwood", "D"), ("Deanwood", "E")],
        "label": "OTR assessment sub-areas Deanwood B, C, D and E",
    },
    "hillcrest": {
        # Hillcrest C is wholly inside and A 44%. Randle Heights B (32% inside) mostly belongs to its neighbors.
        "otr": [("Hillcrest", "A"), ("Hillcrest", "C")],
        "label": "OTR assessment sub-areas Hillcrest A and C",
    },
    "bellevue": {
        # Boundary is 8D01, 8D03, 8D05, 8D06, 8E07-09. Congress Heights A is 89% inside and C 51%; B goes to the Congress Heights site.
        "otr": [("Congress Heights", "A"), ("Congress Heights", "C")],
        "label": "OTR assessment sub-areas Congress Heights A and C",
    },
    "16thstreetheights": {
        # Boundary is all of ANC 4E. Crestwood and 16th Street Heights A and B are wholly inside, C 87%.
        "otr": [("16th Street Heights", "A"), ("16th Street Heights", "B"), ("16th Street Heights", "C"), ("Crestwood", None)],
        "label": "OTR assessment sub-areas 16th Street Heights A, B and C and Crestwood",
    },
    "twining": {
        # DC's TWINING planning area, measured 2026-11-15. Fort Dupont Park D, Hillcrest B and Randle Heights A are
        # wholly inside, Anacostia B 77%. Hillcrest A (56% inside) is already the Hillcrest site's.
        "otr": [("Fort Dupont Park", "D"), ("Hillcrest", "B"), ("Randle Heights", "A"), ("Anacostia", "B")],
        "label": "OTR assessment sub-areas Fort Dupont Park D, Hillcrest B, Randle Heights A and Anacostia B",
    },
    "fortlincoln": {
        # DC's FORT LINCOLN/GATEWAY planning area, measured 2026-11-15. Fort Lincoln, Woodridge B and D are wholly
        # inside, Woodridge C 74%. Old City 2 D (8% inside) is left out.
        "otr": [("Fort Lincoln", None), ("Woodridge", "B"), ("Woodridge", "C"), ("Woodridge", "D")],
        "label": "OTR assessment area Fort Lincoln and sub-areas Woodridge B, C and D",
    },
    "congressheights": {
        # Boundary is ANC 8C02-04, 8C06-08 and 8E03-05. Congress Heights B is 79% inside, Randle Heights D 67%, Randle Heights C 42%.
        # Congress Heights C (27% inside) is mostly Washington Highlands, so it's left out.
        "otr": [("Congress Heights", "B"), ("Randle Heights", "D"), ("Randle Heights", "C")],
        "label": "OTR assessment sub-areas Congress Heights B and Randle Heights C and D",
    },
    "takoma": {
        # Boundary is ANC 4A01-03 and 4B01-04. Shepherd Park, Colonial Village and Brightwood B and D are wholly inside. Brightwood C
        # splits about evenly with the Brightwood site and goes there. OTR's own "Takoma" area is mostly off this boundary (13% inside).
        "otr": [("Shepherd Park", None), ("Colonial Village", None), ("Brightwood", "B"), ("Brightwood", "D")],
        "label": "OTR assessment neighborhoods Shepherd Park and Colonial Village and sub-areas Brightwood B and D",
    },
}

PERSONAL = {"OWNERNAME", "OWNNAME2", "CAREOFNAME", "ADDRESS1", "ADDRESS2", "CITYSTZIP", "MORTGAGECO", "SALE_CURR_OWNER"}
FORBIDDEN_KEYS = {"OWNER_NAME", "OWNERNAME", "OWNNAME", "OWNER", "PERMIT_APPLICANT", "APPLICANT",
                  "INSPECTORNAME", "DETAILS", "CCN"}


def _fields(fields: list[str]) -> str:
    bad = PERSONAL & {f.upper() for f in fields}
    if bad:
        raise ValueError(f"refusing to request personal fields: {sorted(bad)}")
    return ",".join(fields)


def _layer(title: str, year: int) -> str:
    # Not a yearly dataset, but resolving by title survives OTR republishing under a new service name
    # (the ITSPE service name embeds its extract date).
    url = dcdata.resolve_yearly_layer(title, year)
    if not url:
        raise RuntimeError(f"Open Data DC search found no dataset titled {title!r}")
    url = url.rstrip("/")
    if re.search(r"/(FeatureServer|MapServer)$", url):
        url += "/0"
    return url


def _query(layer: str, where: str, fields: list[str], order_by: str | None = None) -> list[dict]:
    """Attribute-only paged query (ITSPE and CAMA have no geometry)."""
    rows: list[dict] = []
    offset = 0
    while True:
        params = {"where": where, "outFields": _fields(fields), "returnGeometry": "false",
                  "resultOffset": offset, "resultRecordCount": 1000, "f": "json"}
        if order_by:
            params["orderByFields"] = order_by
        data = dcdata._request(f"{layer}/query", params, post=True)
        batch = [f["attributes"] for f in data.get("features", [])]
        rows.extend(batch)
        if not batch or not data.get("exceededTransferLimit"):
            return rows
        offset += len(batch)


def _group_count(layer: str, where: str, fields: list[str]) -> list[dict]:
    stats = [{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]
    data = dcdata._request(f"{layer}/query", {"where": where, "groupByFieldsForStatistics": _fields(fields),
                                              "outStatistics": json.dumps(stats), "f": "json"}, post=True)
    out = []
    for f in data.get("features", []):
        a = {k.lower(): v for k, v in f["attributes"].items()}
        out.append({**{fld: a.get(fld.lower()) for fld in fields}, "n": a.get("n", 0)})
    return out


def _q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _area_where(otr: list[tuple[str, str | None]]) -> str:
    parts = [f"(NBHDNAME={_q(n)}" + (f" AND SUBNBHD={_q(s)})" if s else ")") for n, s in otr]
    return "(" + " OR ".join(parts) + ")"


def _in_area(nbhd: str | None, sub: str | None, otr) -> bool:
    return any(nbhd == n and (s is None or sub == s) for n, s in otr)


def _day(v) -> str | None:
    """ITSPE SALEDATE is DateOnly ('YYYY-MM-DD'); handle epoch-ms too."""
    if v is None:
        return None
    if isinstance(v, str):
        return v[:10]
    return time.strftime("%Y-%m-%d", time.gmtime(v / 1000))


def _median(vals) -> int | None:
    vals = [v for v in vals if v is not None]
    return int(round(statistics.median(vals))) if vals else None


def _address(premise: str | None, unit: str | None) -> str:
    a = re.sub(r"\s+WASHINGTON\s+DC.*$", "", (premise or "").strip(), flags=re.I)
    a = re.sub(r"\s+", " ", a)
    keep = {"NW", "NE", "SW", "SE"}
    words = []
    for w in a.split(" "):
        if w.upper() in keep:
            words.append(w.upper())
        elif re.match(r"^\d+(ST|ND|RD|TH)$", w, re.I):
            words.append(w.lower())
        else:
            words.append(w[:1].upper() + w[1:].lower())
    a = " ".join(words)
    if unit and unit.strip() and unit.strip() not in a:
        a += f" #{unit.strip()}"
    return a


def _overlap(geom: dict, itspe: str, otr) -> dict:
    """How the chosen OTR areas line up with the polygon, by tax square. Approximate: a square counts
    as inside if any address point on it falls inside, so edge squares inflate both shares slightly."""
    squares = [s for s in dcdata.count_by(ADDRESS_POINTS, geom, "1=1", "SQUARE") if s]
    if not squares:
        return {}
    res = "USECODE IN (" + ",".join(_q(c) for c in {**HOUSE_CODES, **CONDO_CODES}) + ")"
    sq_in = "SQUARE IN (" + ",".join(_q(s) for s in squares) + ")"
    inside = _group_count(itspe, f"{sq_in} AND {res}", ["NBHDNAME", "SUBNBHD"])
    total_area = sum(r["n"] for r in _group_count(itspe, f"{_area_where(otr)} AND {res}", ["NBHDNAME"]))
    inside_all = sum(r["n"] for r in inside)
    inside_area = sum(r["n"] for r in inside if _in_area(r["NBHDNAME"], r["SUBNBHD"], otr))
    return {
        "squares": len(squares),
        "area_parcels": total_area,
        "area_share_inside": round(inside_area / total_area, 3) if total_area else None,
        "boundary_share_in_area": round(inside_area / inside_all, 3) if inside_all else None,
    }


def build(geom: dict, hood: dict, now: float) -> dict:
    slug = hood["slug"]
    cfg = HOODS.get(slug)
    if not cfg:
        raise KeyError(f"homes.py has no OTR neighborhood mapping for {slug!r}; add it to HOODS")
    otr = cfg["otr"]
    year = time.gmtime(now).tm_year
    itspe = _layer(ITSPE_TITLE, year)
    cama_url = _layer(CAMA_RES_TITLE, year)

    today = datetime.datetime.fromtimestamp(now, datetime.timezone.utc).date()
    start = today - datetime.timedelta(days=730)
    codes = ",".join(_q(c) for c in {**HOUSE_CODES, **CONDO_CODES})
    where = (f"{_area_where(otr)} AND USECODE IN ({codes}) AND ACCEPTCODE={_q(MARKET_CODE)} "
             f"AND SALEDATE >= DATE '{start}' AND SALEPRICE >= {PRICE_FLOOR}")
    rows = _query(itspe, where, ["SSL", "PREMISEADD", "UNITNUMBER", "USECODE", "SALEPRICE", "SALEDATE", "NEWTOTAL"],
                  order_by="SALEDATE DESC")

    sales = []
    for r in rows:
        d = _day(r["SALEDATE"])
        if not d or d > today.isoformat():
            continue
        sales.append({
            "ssl": r["SSL"], "address": _address(r["PREMISEADD"], r["UNITNUMBER"]),
            "kind": "house" if r["USECODE"] in HOUSE_CODES else "condo",
            "price": int(r["SALEPRICE"]), "date": d, "assessed": int(r["NEWTOTAL"]) if r["NEWTOTAL"] else None,
        })
    sales.sort(key=lambda s: (s["date"], s["address"]), reverse=True)

    def since(days: int, until: int = 0) -> list[dict]:
        lo = (today - datetime.timedelta(days=days)).isoformat()
        hi = (today - datetime.timedelta(days=until)).isoformat()
        # Current windows include today; the previous window ends the day before the current one starts.
        return [s for s in sales if lo <= s["date"] and (s["date"] <= hi if until == 0 else s["date"] < hi)]

    last12, prev12, recent = since(365), since(730, 365), since(RECENT_DAYS)

    def of(kind: str, s: dict) -> bool:  # "all" = houses and condos together, for areas with few of either
        return kind == "all" or s["kind"] == kind

    def block(kind: str) -> dict:
        a = [s["price"] for s in last12 if of(kind, s)]
        b = [s["price"] for s in prev12 if of(kind, s)]
        return {"median_12mo": _median(a), "count_12mo": len(a), "median_prev_12mo": _median(b), "count_prev_12mo": len(b)}

    # CAMA building area and bedrooms for recent house sales (condos are in CAMA Condominium, not used here).
    house_ssls = sorted({s["ssl"] for s in recent if s["kind"] == "house" and s["ssl"]})
    cama: dict[str, dict] = {}
    for i in range(0, len(house_ssls), 300):
        chunk = ",".join(_q(x) for x in house_ssls[i:i + 300])
        for r in _query(cama_url, f"SSL IN ({chunk})", ["SSL", "BLDG_NUM", "GBA", "BEDRM"]):
            if r["SSL"] not in cama or (r["BLDG_NUM"] or 9) < (cama[r["SSL"]]["BLDG_NUM"] or 9):
                cama[r["SSL"]] = r

    def gba(s):
        v = cama.get(s["ssl"], {}).get("GBA") if s["kind"] == "house" else None
        return int(v) if v else None

    def beds(s):
        v = cama.get(s["ssl"], {}).get("BEDRM") if s["kind"] == "house" else None
        return int(v) if v else None

    primary = cfg.get("primary", "house")  # what leads the section: houses, condos where houses are rare, or "all"
    recent_primary = [s for s in recent if primary == "all" or s["kind"] == primary]
    ppsf = [s["price"] / gba(s) for s in recent_primary if gba(s)]  # floor area is known for houses only

    # Calendar months: this month (partial) and the 11 before it. Primary home type only.
    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append(f"{y:04d}-{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    months.reverse()
    by_month = []
    for mo in months:
        p = [s["price"] for s in sales if (primary == "all" or s["kind"] == primary) and s["date"].startswith(mo)]
        by_month.append({"month": mo, "median": _median(p) if len(p) >= MIN_MONTH_SALES else None, "count": len(p)})

    with_assessment = [s for s in last12 if s["assessed"]]
    ov = _overlap(geom, itspe, otr)
    if ov.get("area_share_inside") is not None:
        ov["measured"] = str(today)
    else:
        # DC's address-point query sometimes comes back empty; the fit barely moves, so keep the last measurement.
        try:
            last = json.loads((ROOT / "site" / "src" / "data" / f"{slug}.json").read_text(encoding="utf-8"))["homes"]["boundary_fit"]
            if last.get("area_share_inside") is not None:
                ov = {**last, "measured": last.get("measured") or "an earlier run"}
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass
    if ov.get("area_share_inside") is not None:
        fit = (f" Fit with the {hood['name']} boundary, measured this run by tax square (a square counts as inside if any "
               f"DC address point on it falls inside the DC Health polygon, so edge squares make these upper bounds; measured {ov['measured']}): "
               f"{ov['area_share_inside']:.0%} of the {ov['area_parcels']:,} house and condo parcels in the OTR area(s) sit on "
               f"squares inside the boundary, and {ov['boundary_share_in_area']:.0%} of house and condo parcels on in-boundary "
               f"squares belong to the OTR area(s).")
    else:
        fit = " The fit with the boundary could not be measured this run."
    area_note = (
        f"Sales are tied to {hood['name']} through {cfg['label']} in OTR's Integrated Tax System Public Extract, "
        f"not through the DC Health planning-area boundary used elsewhere on this site, because the tax extract has no "
        f"coordinates. The two areas overlap but do not match exactly.{fit}"
    )
    sales_note = (
        f"Only deeds OTR codes \"{MARKET_CODE}\" at ${PRICE_FLOOR:,} or more are counted (same filter as the prototypes); "
        f"foreclosures, buyer=seller transfers, speculative, tax-deed, unusual and multi-parcel sales are excluded. "
        f"\"house\" = row, semi-detached and detached (use codes 011-013); \"condo\" = use codes 016-017. "
        f"Dates are deed sale dates; deeds reach the extract a few weeks after closing, so the newest weeks undercount. "
        f"The extract keeps only each parcel's most recent sale, so a home that resold within 24 months counts once, "
        f"in its later window. \"Assessed\" is OTR's current total assessment (NEWTOTAL), which may postdate the sale. "
        f"Building area and bedrooms are from CAMA Residential (houses only)."
    )
    return {
        "generated_at": iso(int(now * 1000)),
        "sources": [
            {"name": "Integrated Tax System Public Extract (OTR) via Open Data DC", "url": itspe},
            {"name": "Computer Assisted Mass Appraisal - Residential (OTR) via Open Data DC", "url": cama_url},
            {"name": "Address Points (DC MAR) via Open Data DC, for the boundary-fit check", "url": ADDRESS_POINTS},
        ],
        "area_note": area_note,
        "sales_note": sales_note,
        "otr_neighborhoods": [{"nbhdname": n, "subnbhd": s} for n, s in otr],
        "boundary_fit": ov,
        "primary": primary,
        **({"all": block("all")} if primary == "all" else {}),
        "house": block("house"),
        "condo": block("condo"),
        "last_60d": {
            "median": _median([s["price"] for s in recent_primary]),
            "count": len(recent_primary),
            "median_ppsf": _median(ppsf),
            "ppsf_count": len(ppsf),
        },
        "above_assessment_12mo": {"n": sum(1 for s in with_assessment if s["price"] > s["assessed"]), "of": len(with_assessment)},
        "by_month": by_month,
        "by_month_basis": f"{'houses and condos together' if primary == 'all' else primary + 's only'}; calendar months, the last one in progress; median null when under {MIN_MONTH_SALES} sales",
        "recent_sales": [
            {"address": s["address"], "date": s["date"], "price": s["price"], "kind": s["kind"],
             "beds": beds(s), "sqft": gba(s), "assessed": s["assessed"]}
            for s in recent[:RECENT_CAP]
        ],
    }


def _forbidden(obj, path="$") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.upper() in FORBIDDEN_KEYS:
                hits.append(f"{path}.{k}")
            hits += _forbidden(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _forbidden(v, f"{path}[{i}]")
    return hits


def check(section: dict) -> list[str]:
    errors = []
    for key in ("generated_at", "sources", "area_note", "house", "condo", "last_60d", "above_assessment_12mo",
                "by_month", "by_month_basis", "recent_sales"):
        if key not in section:
            errors.append(f"missing {key}")
    if errors:
        return errors
    if not section["sources"] or not all(s.get("name") and s.get("url") for s in section["sources"]):
        errors.append("sources incomplete")

    def plausible(label, v):
        if v is None or not (100_000 <= v <= 5_000_000):
            errors.append(f"{label} implausible: {v}")

    for kind in ("house", "condo"):
        b = section[kind]
        for c in ("count_12mo", "count_prev_12mo"):
            if not b.get(c):
                errors.append(f"{kind}.{c} is zero")
        plausible(f"{kind}.median_12mo", b.get("median_12mo"))
        plausible(f"{kind}.median_prev_12mo", b.get("median_prev_12mo"))
    l60 = section["last_60d"]
    if not l60.get("count"):
        errors.append("last_60d.count is zero")
    plausible("last_60d.median", l60.get("median"))
    if l60.get("median_ppsf") is not None and not (100 <= l60["median_ppsf"] <= 3000):
        errors.append(f"last_60d.median_ppsf implausible: {l60['median_ppsf']}")
    a = section["above_assessment_12mo"]
    if not a.get("of") or a.get("n", -1) < 0 or a["n"] > a["of"]:
        errors.append(f"above_assessment_12mo inconsistent: {a}")
    months = [m for m in section["by_month"] if m.get("median") is not None]
    # A month needs 3 sales for a median, so a thin market legitimately leaves most months blank.
    need = 6 if section[section.get("primary", "house")]["count_12mo"] >= 60 else 1
    if len(section["by_month"]) != 12 or len(months) < need:
        errors.append(f"by_month has {len(months)} months with a median (need >= {need} of 12)")
    for m in months:
        plausible(f"by_month {m['month']}", m["median"])
    if not section["recent_sales"]:
        errors.append("recent_sales is empty")
    if len(section["recent_sales"]) > RECENT_CAP:
        errors.append("recent_sales over cap")
    dates = [s["date"] for s in section["recent_sales"]]
    if dates != sorted(dates, reverse=True):
        errors.append("recent_sales not newest first")
    errors += [f"forbidden key {h}" for h in _forbidden(section)]
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python ingest/homes.py <slug>", file=sys.stderr)
        return 2
    slug = sys.argv[1]
    config = json.loads((Path(__file__).parent / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if not hood:
        print(f"unknown slug {slug!r}", file=sys.stderr)
        return 2
    now = time.time()
    geom = dcdata.hood_boundary(config, hood)
    section = build(geom, hood, now)
    out_dir = Path(__file__).parent / "_out"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"homes-{slug}.json").write_text(json.dumps(section, indent=1), encoding="utf-8")
    h, c, l60 = section["house"], section["condo"], section["last_60d"]
    print(f"{slug}: houses 12mo median ${h['median_12mo'] or 0:,} over {h['count_12mo']} sales "
          f"(prev ${h['median_prev_12mo'] or 0:,} / {h['count_prev_12mo']}); "
          f"condos 12mo ${c['median_12mo'] or 0:,} / {c['count_12mo']} (prev ${c['median_prev_12mo'] or 0:,} / {c['count_prev_12mo']}); "
          f"60d houses ${l60['median'] or 0:,} / {l60['count']}, ${l60['median_ppsf'] or 0}/sqft; "
          f"above assessment {section['above_assessment_12mo']['n']}/{section['above_assessment_12mo']['of']}; "
          f"fit {section['boundary_fit']}")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("homes ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
