"""`news` section: local headlines that mention the neighborhood, plus newly licensed bars and restaurants.

    python ingest/news.py petworth

Headlines come from local outlets' public RSS feeds. Only the headline, outlet, date and link are kept,
never article text: the site sends readers to the outlet. Each feed is fetched only if the outlet's
robots.txt allows it for our user agent (checked every run), and each item must mention one of the
neighborhood's terms in its headline, summary or tags, except outlets that cover only this
neighborhood (Petworth News), where every item counts.

Feeds hold only their latest 10-20 items, so matches are kept in an archive: the previous run's items
are read back from site/src/data/<slug>.json and merged, and anything older than ARCHIVE_DAYS drops off.

Openings and closings come from liquor licenses (restaurants, bars, shops). New ones come from DC ABCA's "Alcohol License Business Locations" layer: a license number
not in the previous run's list is new. The first run only records the list (nothing can be "new" yet).
Closings come from ABCA's cancellation list, minus places relicensed at the same address under a
similar name. DC publishes no cancellation dates for most, so new cancellations are dated by the night
we first see them. The applicant name is never requested; only the trade name, address and license type.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
from run import find_forbidden, iso  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = dcdata.USER_AGENT  # one honest project user agent for every request
DAY = 86400
ARCHIVE_DAYS = 180
MAX_ITEMS = 80

LICENSES = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer/5"
LICENSES_PAGE = "https://opendata.dc.gov/datasets/alcohol-license-business-locations"
# "APPLICANT" is deliberately absent.
LICENSE_FIELDS = ["LICENSE", "TRADE_NAME", "ADDRESS", "TYPE", "STATUS"]
CANCELLED = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer/42"
CANCELLED_PAGE = "https://opendata.dc.gov/datasets/abca-liquor-license-cancellation"
CANCELLED_FIELDS = ["LICENSE", "TRADE_NAME", "ADDRESS", "TYPE", "CANCELLATION_DATE"]

# (outlet, feed url, home page, mode). "all": the outlet covers only this neighborhood.
# "match": keep items whose headline, summary or tags mention a TERMS pattern.
# "search": a hyper-local outlet's own search feed; the article body counts too. (Washingtonian's search
# is "match": its passing body mentions, like a therapist listicle, aren't neighborhood news.)
WP_SEARCH = "{base}/?s={q}&feed=rss2&orderby=date&order=DESC"
SHARED = [
    ("Washington City Paper", "https://washingtoncitypaper.com/feed/", "https://washingtoncitypaper.com/", "match"),
    ("WTOP", "https://wtop.com/local/dc/feed/", "https://wtop.com/", "match"),
    ("WAMU", "https://wamu.org/feed/", "https://wamu.org/", "match"),
    ("51st", "https://51st.news/rss/", "https://51st.news/", "match"),
    ("Greater Greater Washington", "https://ggwash.org/rss", "https://ggwash.org/", "match"),
    ("Mayor's office", "https://mayor.dc.gov/rss.xml", "https://mayor.dc.gov/newsroom", "match"),
    ("DDOT", "https://ddot.dc.gov/rss.xml", "https://ddot.dc.gov/newsroom", "match"),
    ("DC Parks and Recreation", "https://dpr.dc.gov/rss.xml", "https://dpr.dc.gov/", "match"),
]
FEEDS = {
    "petworth": [
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        ("Petworth News", "https://www.petworthnews.org/blog?format=rss", "https://www.petworthnews.org/", "all"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="petworth"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="petworth"), "https://www.washingtonian.com/", "match"),
        *SHARED,
    ],
    "tenleytown": [
        ("ANC 3E", "https://anc3e.org/feed/", "https://anc3e.org/", "all"),
        ("Forest Hills Connection", "https://foresthillsconnection.com/feed/", "https://foresthillsconnection.com/", "match"),
        ("Forest Hills Connection", WP_SEARCH.format(base="https://foresthillsconnection.com", q="tenleytown"), "https://foresthillsconnection.com/", "search"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="tenleytown"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="tenleytown"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "adamsmorgan": [
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="adams+morgan"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="adams+morgan"), "https://www.washingtonian.com/", "match"),
        ("Washington Blade", "https://www.washingtonblade.com/?s=adams+morgan&feed=rss2&orderby=date&order=DESC", "https://www.washingtonblade.com/", "match"),
        ("WTOP", "https://wtop.com/tag/adams-morgan/feed/", "https://wtop.com/", "match"),
        ("ANC 2B", "https://www.dupontcircleanc.net/wordpress/feed/", "https://www.dupontcircleanc.net/", "match"),  # Dupont ANC; covers the southern strip
        *SHARED,
    ],
    "friendshipheights": [
        ("ANC 3E", "https://anc3e.org/feed/", "https://anc3e.org/", "match"),  # also covers Tenleytown, so filtered
        ("WTOP", "https://wtop.com/tag/friendship-heights/feed/", "https://wtop.com/", "match"),  # mixes MD; see NOT_HERE
        ("Forest Hills Connection", WP_SEARCH.format(base="https://foresthillsconnection.com", q="friendship+heights"), "https://foresthillsconnection.com/", "search"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="friendship+heights"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="friendship+heights"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    # The nine below: feeds tested 2026-10-31/11-01 (robots allowed for our agent); see ingest/SOURCES-*.md.
    "capitolhill": [
        ("The Hill is Home", "https://thehillishome.com/feed/", "https://thehillishome.com/", "all"),
        ("Capitol Hill Corner", "https://www.capitolhillcorner.org/feed/", "https://www.capitolhillcorner.org/", "all"),
        ("Capitol Hill Restoration Society", "https://www.chrs.org/feed/", "https://www.chrs.org/", "all"),
        ("Hill Center", "https://www.hillcenterdc.org/feed/", "https://www.hillcenterdc.org/", "all"),
        ("WTOP", "https://wtop.com/tag/eastern-market/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/capitol-hill/feed/", "https://wtop.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="eastern+market"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "hstreet": [
        ("WTOP", "https://wtop.com/tag/h-street-corridor/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/h-street/feed/", "https://wtop.com/", "match"),
        ("The Hill is Home", "https://thehillishome.com/feed/", "https://thehillishome.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "navyyard": [
        ("WTOP", "https://wtop.com/tag/navy-yard/feed/", "https://wtop.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="navy+yard"), "https://www.washingtonian.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="capitol+riverfront"), "https://www.washingtonian.com/", "match"),
        ("The Hill is Home", "https://thehillishome.com/feed/", "https://thehillishome.com/", "match"),
        ("ANC 8F", "https://anc8f.dc.gov/rss.xml", "https://anc8f.dc.gov/", "all"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "anacostia": [
        ("Anacostia BID", "https://www.anacostiabid.org/news?format=rss", "https://www.anacostiabid.org/", "match"),
        ("WTOP", "https://wtop.com/tag/anacostia/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/ward-8/feed/", "https://wtop.com/", "match"),
        ("ANC 8A", "https://anc8a.dc.gov/rss.xml", "https://anc8a.dc.gov/", "all"),
        ("Washington Informer", "https://www.washingtoninformer.com/feed/", "https://www.washingtoninformer.com/", "match"),
        *SHARED,
    ],
    "columbiaheights": [
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        ("WTOP", "https://wtop.com/tag/columbia-heights/feed/", "https://wtop.com/", "match"),
        ("ANC 1E", "https://anc1e.org/feed/", "https://anc1e.org/", "all"),
        ("Washington Blade", "https://www.washingtonblade.com/?s=columbia+heights&feed=rss2&orderby=date&order=DESC", "https://www.washingtonblade.com/", "match"),
        *SHARED,
    ],
    "georgetown": [
        ("Georgetown Metropolitan", "https://georgetownmetropolitan.com/feed/", "https://georgetownmetropolitan.com/", "all"),
        ("The Georgetowner", "https://georgetowner.com/feed/", "https://georgetowner.com/", "match"),
        ("The Hoya (City News)", "https://thehoya.com/section/news/city-news/feed/", "https://thehoya.com/", "match"),
        ("WTOP", "https://wtop.com/tag/georgetown/feed/", "https://wtop.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="georgetown"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "dupontcircle": [
        ("ANC 2B", "https://www.dupontcircleanc.net/wordpress/feed/", "https://www.dupontcircleanc.net/", "all"),
        ("WTOP", "https://wtop.com/tag/dupont-circle/feed/", "https://wtop.com/", "match"),
        ("Washington Blade", "https://www.washingtonblade.com/?s=dupont+circle&feed=rss2&orderby=date&order=DESC", "https://www.washingtonblade.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="dupont+circle"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "clevelandpark": [
        ("Cleveland Park Citizens Association", "https://www.cpcadc.org/feed/", "https://www.cpcadc.org/", "all"),
        ("ANC 3C", "https://anc3c.dc.gov/rss.xml", "https://anc3c.dc.gov/", "all"),
        ("District Bridges", "https://districtbridges.org/feed/", "https://districtbridges.org/", "match"),
        ("WTOP", "https://wtop.com/tag/cleveland-park/feed/", "https://wtop.com/", "match"),
        ("Forest Hills Connection", "https://foresthillsconnection.com/feed/", "https://foresthillsconnection.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="cleveland+park"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "chevychase": [
        ("ANC 3/4G", "https://anc3g.dc.gov/rss.xml", "https://anc3g.dc.gov/", "all"),
        ("Historic Chevy Chase DC", "https://www.historicchevychasedc.org/feed/", "https://www.historicchevychasedc.org/", "all"),
        ("District Bridges", "https://districtbridges.org/feed/", "https://districtbridges.org/", "match"),
        ("WTOP", "https://wtop.com/tag/chevy-chase/feed/", "https://wtop.com/", "match"),
        ("Forest Hills Connection", "https://foresthillsconnection.com/feed/", "https://foresthillsconnection.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="chevy+chase"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    # Added 2026-11-01; feeds tested that day (see ingest/SOURCES-NORTHWEST.md and SOURCES-CENTRAL.md).
    "brookland": [
        # robots.txt there disallows "/*?": never add a query string on this host.
        ("Brookland Neighborhood Civic Association", "https://brooklandcivic.org/feed/", "https://brooklandcivic.org/", "all"),
        ("WTOP", "https://wtop.com/tag/brookland/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/catholic-university/feed/", "https://wtop.com/", "match"),
        ("ANC 5A", "https://anc5a.org/feed/", "https://anc5a.org/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="brookland"), "https://thedcline.org/", "search"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "gloverpark": [
        # ANC 3B's own feed is disallowed by its robots.txt, so it isn't read.
        ("Glover Park Citizens' Association", "https://gpcadc.org/feed/", "https://gpcadc.org/", "all"),
        ("WTOP", "https://wtop.com/tag/glover-park/feed/", "https://wtop.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="glover+park"), "https://thedcline.org/", "search"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "palisades": [
        ("Palisades Citizens' Association", "https://palisadesdc.org/feed/", "https://palisadesdc.org/", "all"),
        ("WTOP", "https://wtop.com/tag/palisades/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/spring-valley/feed/", "https://wtop.com/", "match"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="palisades"), "https://www.washingtonian.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="palisades"), "https://thedcline.org/", "search"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "vanness": [
        ("Forest Hills Connection", "https://foresthillsconnection.com/feed/", "https://foresthillsconnection.com/", "match"),
        ("Forest Hills Connection", WP_SEARCH.format(base="https://foresthillsconnection.com", q="van+ness"), "https://foresthillsconnection.com/", "search"),
        ("ANC 3F", "https://anc3f.dc.gov/rss.xml", "https://anc3f.dc.gov/", "all"),
        ("WTOP", "https://wtop.com/tag/van-ness/feed/", "https://wtop.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "chinatown": [
        ("Mount Vernon Triangle CID", "https://www.mvtcid.org/feed/", "https://www.mvtcid.org/", "all"),  # MVT is wholly inside
        ("WTOP", "https://wtop.com/tag/chinatown/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/penn-quarter/feed/", "https://wtop.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="chinatown"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="chinatown"), "https://www.washingtonian.com/", "match"),
        ("DowntownDC BID", "https://www.downtowndc.org/feed/", "https://www.downtowndc.org/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "lenfantplaza": [
        # The Southwester's RSS returns its home page (a cache plugin), so its WordPress post list is read instead.
        ("The Southwester", "https://thesouthwester.com/wp-json/wp/v2/posts?per_page=20&_fields=date_gmt,title,excerpt,link",
         "https://thesouthwester.com/", "all"),
        ("Southwest BID", "https://www.swbid.org/feed/", "https://www.swbid.org/", "all"),
        ("WTOP", "https://wtop.com/tag/southwest-dc/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/the-wharf/feed/", "https://wtop.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "noma": [
        ("WTOP", "https://wtop.com/tag/noma/feed/", "https://wtop.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="noma"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="noma"), "https://www.washingtonian.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "shaw": [
        ("WTOP", "https://wtop.com/tag/shaw/feed/", "https://wtop.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="shaw"), "https://thedcline.org/", "match"),  # surnames: match, not search
        ("ANC 1B", "https://www.anc1b.org/announcements?format=rss", "https://www.anc1b.org/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "logancircle": [
        ("ANC 2F", "https://anc2f.org/feed/", "https://anc2f.org/", "all"),
        ("WTOP", "https://wtop.com/tag/logan-circle/feed/", "https://wtop.com/", "match"),
        ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="logan+circle"), "https://thedcline.org/", "search"),
        ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="logan+circle"), "https://www.washingtonian.com/", "match"),
        ("District Bridges", "https://districtbridges.org/feed/", "https://districtbridges.org/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        *SHARED,
    ],
    "ustreet": [
        ("WTOP", "https://wtop.com/tag/u-street/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/u-street-corridor/feed/", "https://wtop.com/", "match"),
        ("WTOP", "https://wtop.com/tag/howard-university/feed/", "https://wtop.com/", "match"),
        ("ANC 1B", "https://www.anc1b.org/announcements?format=rss", "https://www.anc1b.org/", "all"),
        ("African American Civil War Museum", "https://www.afroamcivilwar.org/feed/", "https://www.afroamcivilwar.org/", "all"),
        ("ANC 1E", "https://anc1e.org/feed/", "https://anc1e.org/", "match"),
        ("District Bridges", "https://districtbridges.org/feed/", "https://districtbridges.org/", "match"),
        ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
        ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
        *SHARED,
    ],
}
TERMS = {
    # Capitol Hill: never the bare name (it also means Congress); a landmark, or the name plus a neighborhood cue.
    "capitolhill": re.compile(
        r"\beastern\s+market\b|\bbarracks\s+row\b|\bstanton\s+park\b|\bseward\s+square\b|\bhill\s+center\b|"
        r"\bfolger\s+(shakespeare|theat|library)|\bmarine\s+barracks\b|\beast\s+capitol\s+st|\bpennsylvania\s+ave(nue)?\.?\s+s\.?e\b|"
        r"\bcapitol\s+hill\s+(neighborhood|restoration\s+society|village|day\s+school|montessori|arts\s+workshop|bid|"
        r"business\s+improvement|main\s+street|residents?|neighbors?|rowhouses?|homes?)\b|\bANC\s*6B\b|"
        r"\bcapitol\s+hill\b(?=.*(\b\d{2,4}\s+[\w.]+\s+(st|street|ave|avenue|pl|place)\.?\s+(s\.?e|n\.?e)\b|\bward\s*6\b|"
        r"\bANC\s*6[ABC]\b|\browhouse|\bneighbou?rhood\b))", re.I | re.S),
    # "H Street" alone also means H St NW downtown.
    "hstreet": re.compile(r"\bh\s+st(reet)?\.?\s*,?\s*n\.?e\b|\bh\s+street\s+(corridor|festival|main\s+street|streetcar|country\s+club)\b|"
                          r"\batlas\s+(district|performing\s+arts|theat)|\bstarburst\s+(plaza|intersection)\b|\bANC\s*6A\b", re.I),
    "navyyard": re.compile(r"\bnavy\s+yard\b|\bcapitol\s+riverfront\b|\byards\s+park\b|\bANC\s*(6/)?8F\b", re.I),
    # Anacostia is also the river (and the riverside park, which runs far beyond the neighborhood).
    "anacostia": re.compile(
        r"\bhistoric\s+anacostia\b|\bgood\s+hope\s+r(oa)?d\b|\bbig\s+chair\b|"
        r"\banacostia\s+(arts\s+center|playhouse|bid|business\s+improvement|community\s+museum|neighborhood\s+library|library|"
        r"high\s+school|metro|historic\s+district|neighborhood)\b|\bfrederick\s+douglass\s+(national\s+historic|house|home)|"
        r"\bmarion\s+barry\s+market|\bANC\s*8A\b|"
        r"\banacostia\b(?!\s+(river|watershed|riverwalk|waterfront|riverkeeper|river\s*partners|freeway|park))"
        r"(?=.*(\bs\.?e\b|\bsoutheast\b|\bward\s*8\b|\beast\s+of\s+the\s+river\b))", re.I | re.S),
    # Columbia Heights, Minnesota is a Minneapolis suburb.
    "columbiaheights": re.compile(r"\bcolumbia\s+heights\b(?!.*\b(minn|minnesota|MN)\b)|\btivoli\s+(theat|square)|\bgala\s+(hispanic\s+)?theat|"
                                  r"\bpark\s+view\b(?=.*\b(d\.?c|NW|ANC)\b)|\bANC\s*1[AE]\b", re.I | re.S),
    # Georgetown is also the university and towns elsewhere; take the neighborhood's own places.
    "georgetown": re.compile(r"\bgeorgetown\b(?=.*\b(d\.?c|NW|m\s+st(reet)?|wisconsin\s+ave|c&o\s+canal|waterfront|neighborhood|"
                             r"ANC\s*2E)\b)|\bm\s+st(reet)?\s+nw\b.{0,40}\bgeorgetown|\bcitizens\s+association\s+of\s+georgetown", re.I | re.S),
    # "Dupont" alone is also the chemical company.
    "dupontcircle": re.compile(r"\bdupont\s+circle\b|\bANC\s*2B\b", re.I),
    "clevelandpark": re.compile(r"\bcleveland\s+park\b(?!.*\b(ohio|OH|cleveland,)\b)|\bANC\s*3C\b|\bmacomb\s+(st|playground)\b|\buptown\s+theat", re.I | re.S),
    # Chevy Chase, DC only: the Maryland town and village share the name.
    "chevychase": re.compile(r"\bchevy\s+chase,?\s+(dc|d\.c\.)|\bchevy\s+chase\s+(library|community\s+center|circle)\b|\blafayette\s+(elementary|park)\b|"
                             r"\bbroad\s+branch\s+market\b|\bANC\s*3/?4G\b", re.I),
    "petworth": re.compile(r"\bpetworth\b|\bupshur st(reet)?\b|\bgrant circle\b|\bsherman circle\b", re.I),
    # Not "Kalorama" alone (Sheridan-Kalorama is ANC 2D), nor Columbia Road or 18th Street alone.
    "adamsmorgan": re.compile(r"\badams[- ]morgan\b|\badmo\b|\bkalorama (park|triangle)\b|\blanier heights\b|\bmarie reed\b|"
                              r"\bmintwood\b|\bwalter pierce park\b|\bjumbo slice\b", re.I),
    "friendshipheights": re.compile(r"\bfriendship heights\b|\bmazza gallerie\b|\bchevy chase pavilion\b|\bjenifer st(reet)?\b|"
                                    r"\bfort bayard\b", re.I),
    # "Friendship Heights" alone is left out: it also names the Maryland side of the line.
    "tenleytown": re.compile(r"\btenleytown\b|\btenley (circle|library)\b|\bfort reno\b|\bjackson[- ]reed\b|\btenley-friendship\b", re.I),
    # Brookland, Arkansas and the Kent village are rejected in NOT_HERE; Catholic University alone is campus news.
    "brookland": re.compile(
        r"\bbrookland\b(?!,?\s+(ark|arkansas|ar)\b)|\bmonroe\s+street\s+market\b|\b(brookland\s+)?arts\s+walk\b(?=.*\b(brookland|monroe|NE)\b)|"
        r"\b12th\s+st(reet)?\.?\s+(n\.?e\b|corridor)|\bturkey\s+thicket\b|\bfranciscan\s+monastery\b|\bdance\s+place\b|"
        r"\bbasilica\s+of\s+the\s+national\s+shrine\b|\bnational\s+shrine\s+of\s+the\s+immaculate\b|\bANC\s*5B\b|"
        r"\bcatholic\s+university\b(?=.*\b(neighbou?rs?|neighbou?rhood|residents?|brookland|NE|ANC|michigan\s+ave|metro)\b)|"
        r"\bbrookland[-\s/]+cua\b|\bwoodridge\s+(library|neighborhood\s+library)\b", re.I | re.S),
    # Glover-Archbold Park runs through several neighborhoods, so it needs a Glover Park cue.
    "gloverpark": re.compile(
        r"\bglover\s+park\b|\bguy\s+mason\b|\bstoddert\s+(elementary|es|rec|school)\b|\bwhitehaven\s+(park|parkway|st)\b|\bANC\s*3B\b|"
        r"\bglover[-\s]+archbold\b(?=.*\b(glover\s+park|wisconsin|ANC\s*3[BD]|neighbo)\b)", re.I | re.S),
    # Bare "Palisades" needs a DC cue: wire copy is mostly Pacific Palisades, the Michigan nuclear plant and New Jersey.
    "palisades": re.compile(
        r"\b(the\s+)?palisades\b(?=.*\b(d\.?c\.?|NW|northwest|macarthur|ANC\s*3D|citizens|library|recreation|sibley|ward\s*3)\b)|"
        r"\bmacarthur\s+(blvd|boulevard)\b|\bANC\s*3D\b|\bdalecarlia\b|\bbattery\s+kemble\b|\bsibley\s+(memorial\s+)?hospital\b|"
        r"\bspring\s+valley\b(?=.*\b(d\.?c\.?|NW|american\s+university|munitions|chemical|army\s+corps|ANC)\b)|\bwesley\s+heights\b|"
        r"\bfoxhall\b|\bchain\s+bridge\s+r(oa)?d\b", re.I | re.S),
    # Never the outlet name "Forest Hills Connection" (every FHC summary carries it), never bare "UDC" (it has other campuses).
    "vanness": re.compile(
        r"\bvan\s+ness\b(?=.*\b(d\.?c\.?|NW|connecticut|UDC|university\s+of\s+the\s+district|metro|forest\s+hills|ANC|main\s+street|neighbo)\b)|"
        r"\bvan\s+ness[-\s/]+udc\b|\bANC\s*3F\b|\bforest\s+hills\s+(of\s+d\.?c|playground|neighborhood|park|DC)\b|\bnorth\s+cleveland\s+park\b|"
        r"\bsoapstone\s+valley\b|\binternational\s+(chancery\s+)?cent(er|re)\b(?=.*\bvan\s+ness\b)|"
        r"\b(university\s+of\s+the\s+district\s+of\s+columbia|UDC)\b(?=.*\b(connecticut\s+ave|van\s+ness|4200\s+connecticut)\b)", re.I | re.S),
    # Capital One Arena counts only as "near/outside the arena" (bare mentions are game and concert roundups).
    "chinatown": re.compile(
        r"\bchinatown\b|\bfriendship\s+arch(way)?\b|\bgallery\s+place\b|\b(near|outside|around|behind|by)\s+(the\s+)?capital\s+one\s+arena\b|"
        r"\bpenn\s+quarter\b|\bmartin\s+luther\s+king\s+jr\.?\s+memorial\s+library\b|\bMLK\s+(memorial\s+)?library\b|"
        r"\bsmithsonian\s+american\s+art\s+museum\b|\bnational\s+portrait\s+gallery\b|\bcapital\s+jewish\s+museum\b|\bnational\s+building\s+museum\b|"
        r"\bford['\u2019]?s\s+theat(re|er)\b|\bjudiciary\s+square\b|\bmount\s+vernon\s+(triangle|square)\b|\bANC\s*2C\b|"
        r"\b[4-9]\d\d\s+[HIGF]\s+st(reet)?\.?,?\s+n\.?w\b|\b[6-9]\d\d\s+7th\s+st(reet)?\.?,?\s+n\.?w\b", re.I | re.S),
    # Never bare "L'Enfant" (the planner, the L'Enfant Plan); the Southwest BID takes in the Wharf and Waterfront Station.
    "lenfantplaza": re.compile(
        r"\bl['\u2019]?\s?enfant\s+(plaza|promenade)\b|\bbanneker\s+(park|overlook)\b|\b10th\s+st(reet)?\.?\s+overlook\b|\bspy\s+museum\b|"
        r"\bsouthwest\s+(bid|business\s+improvement|ecodistrict|waterfront|duck\s*pond|neighborhood\s+library|library)\b|\bSWBID\b|"
        r"\bwaterfront\s+station\b|\bANC\s*6D\b|\barena\s+stage\b|\bfedlandia\b|\bamidon[-\s]bowen\b|\brandall\s+rec|"
        r"\b\d{2,4}\s+([4-9]|1[0-4])(th|st|nd|rd)\s+st(reet)?\.?,?\s+s\.?w\b|\b\d{2,4}\s+[CDEGIM]\s+st(reet)?\.?,?\s+s\.?w\b|"
        r"\b(in\s+)?(southwest|SW)\s+(dc|d\.c\.)\b|\bwharf\s+(dc|d\.c\.)\b|\bthe\s+wharf\b(?=.{0,200}\b(d\.?c|SW|southwest|maine\s+ave)\b)", re.I | re.S),
    # Case-sensitive on purpose: "Noma" (the Copenhagen restaurant), "NOMA" (the architects' group) and "NoMad" never match.
    "noma": re.compile(r"\bNoMa\b|\b(?i:noma[-\s]gallaudet)\b|\bNoMa\s+BID\b|"
                       r"(?i:\balethia\s+tanner\s+park\b|\bswampoodle\b|\bmamie\s+.{0,2}peanut.{0,2}\s+johnson\s+plaza\b|\buline\s+arena\b|"
                       r"\bharry\s+thomas\s+(way|rec))"),
    # Case-sensitive on "Shaw" (the surname is far more common); historic Shaw = ANC 2G (7th/9th St, Blagden Alley, Howard Theatre).
    "shaw": re.compile(
        r"\b(?i:in|of|around|across|near|to|from|historic|north|eastern|western|downtown)\s+Shaw\b(?![\s,]+(AFB|[Aa]ir\s+[Ff]orce|University))|"
        r"\bShaw\s+(?i:neighborhood|main\s+streets?|library|dc|d\.c\.|metro|community\s+center|residents?|rowhouse)\b|"
        r"\bShaw[-/\u2013]Howard\b|\bShaw['\u2019]s\s+(?i:7th|9th|main|historic|neighborhood|restaurant\s+scene)|"
        r"\b(?i:blagden\s+alley|naylor\s+court|howard\s+theat(re|er)|watha\s+t\.?\s+daniel|kennedy\s+rec(reation)?\s+center|o\s+street\s+market|ANC\s*2G)\b|"
        r"\b(?i:1[1-9]\d\d\s+(7th|9th|seventh|ninth)\s+st(reet)?\.?,?\s+n\.?w|walter\s+e\.?\s+washington\s+convention\s+center)\b"),
    # Logan Circle takes 14th St NW (1000-1699), P St and the circle itself; Shaw takes 7th/9th St.
    "logancircle": re.compile(
        r"\blogan\s+circle\b|\bP\s+st(reet)?\.?\s+(n\.?w\b|whole\s+foods)|\bstudio\s+theat(re|er)\b|\bmary\s+mcleod\s+bethune\s+council\s+house\b|"
        r"\bmetropolitan\s+A\.?M\.?E\b|\bANC\s*2F\b|\bLCCA\b|\b1[3-5]th\s+(and|&)\s+[P-R]\b|\b1[0-6]\d\d\s+14th\s+st(reet)?\.?,?\s+n\.?w\b|"
        r"\b14th\s+st(reet)?\s+corridor\b|\bvermont\s+ave(nue)?\.?\s+n\.?w\b.{0,40}\blogan", re.I | re.S),
    # Not U St SE (Anacostia); Howard University counts only with a neighborhood cue (most of its news is national or sports).
    "ustreet": re.compile(
        r"\bU\s+st(reet)?\b(?!\.?\s*,?\s*(s\.?e|n\.?e|southeast|northeast)\b)|\bben['\u2019]?s\s+chili\s+bowl\b|"
        r"\blincoln\s+theat(re|er)\b(?=.*\b(d\.?c|washington|u\s+st)\b)|\b9:30\s+club\b|\bblack\s+broadway\b|"
        r"\bafrican\s+american\s+civil\s+war\s+(memorial|museum)\b|\btrue\s+reformer\b|\breeves\s+center\b|\bANC\s*1B\b|\bLeDroit\s+park\b|"
        r"\b1[0-6]th\s+(and|&)\s+U\b|\bpleasant\s+plains\b|\bhoward\s+university\s+hospital\b|\bbanneker\s+(rec(reation)?\s+center|pool)\b|"
        r"\bhoward\s+(university|u\.)\b(?=.{0,300}\b(campus|neighbors?|georgia\s+ave|homecoming|yardfest|U\s+street|residents)\b)", re.I | re.S),
}

# Other cities' Chinatowns.
OTHER_CT = (r"(new\s+york|NYC|manhattan|flushing|san\s+francisco|boston|philadelphia|philly|chicago|oakland|los\s+angeles|seattle|portland|"
            r"toronto|vancouver|london|montreal|honolulu|houston|las\s+vegas|bangkok|singapore|kuala\s+lumpur|sydney|melbourne|liverpool|"
            r"manchester|yokohama|havana|lima|paris)")

# (reject, rescue): an item that matches the neighborhood's terms but also the reject pattern is dropped, unless it
# also matches the rescue pattern. Friendship Heights straddles the District line: a story that names only
# "Friendship Heights" and also a Maryland place is about the Maryland side, unless it names a DC-side landmark too.
NOT_HERE = {
    "friendshipheights": (re.compile(r"\b(maryland|md\.?|montgomery county|bethesda|somerset|brookdale|chevy chase,? md|"
                                     r"wisconsin place|the hills plaza|geico)\b", re.I),
                          re.compile(r"\bmazza gallerie\b|\bchevy chase pavilion\b|\bjenifer st(reet)?\b|\bfort bayard\b|"
                                     r"\b(d\.?c\.?|northwest|nw)\b", re.I)),
    "brookland": (re.compile(r"\bbrookland,?\s+(ark|arkansas|ar)\b|\bjonesboro\b|\bbrooklands\b|\bkent\b|\bromney\s+marsh\b", re.I),
                  re.compile(r"\bANC\s*5B\b|\bNE\b|\bnortheast\b|\b12th\s+st|\bmonroe\s+st|\bD\.?C\.?\b", re.I)),
    # The Russian Embassy sits in Glover Park, but its coverage is geopolitics unless the item names the neighborhood.
    "gloverpark": (re.compile(r"\brussian\s+embassy\b|\bkremlin\b|\bmoscow\b|\bputin\b", re.I),
                   re.compile(r"\bglover\s+park\b|\bANC\s*3B\b|\bguy\s+mason\b|\bstoddert\b", re.I)),
    "palisades": (re.compile(r"\bpacific\s+palisades\b|\bpalisades\s+(fire|nuclear|power\s+plant|plant|interstate|parkway|center|tahoe|charter|"
                             r"park,?\s+(n\.?j|new\s+jersey)|village\s+(mall|shopping))\b|\bnew\s+jersey\b|\bhudson\s+river\b|\bmichigan\b|"
                             r"\blos\s+angeles\b|\bcalifornia\b|\bmalibu\b|\bholtec\b|\bentergy\b|\bcovert\s+township\b|\bfort\s+lee\b|\bnyack\b", re.I),
                  re.compile(r"\bmacarthur\s+(blvd|boulevard)\b|\bANC\s*3D\b|\bpalisades\s+(citizens|library|neighborhood\s+library|recreation|rec\b|"
                             r"farmers|parade|4th|fourth|main\s+street)|\bdalecarlia\b|\bsibley\b|\b(d\.?c\.?|NW)\b(?!-area)", re.I)),
    "vanness": (re.compile(r"\bjonathan\s+van\s+ness\b|\bJVN\b|\bqueer\s+eye\b|\bsan\s+francisco\b|\bvan\s+ness\s+ave(nue)?\b|\bS\.F\.|"
                           r"\bforest\s+hills,?\s+(queens|n\.?y|new\s+york)\b|\bus\s+open\b|\bwest\s+side\s+tennis\b", re.I),
                re.compile(r"\bconnecticut\s+ave|\bANC\s*3F\b|\bUDC\b|\bvan\s+ness\s+(st(reet)?|metro|station|main\s+street)\b|\bNW\b|"
                           r"\bforest\s+hills\s+connection\b", re.I)),
    "chinatown": (re.compile(OTHER_CT + r"(['\u2019]s)?\s+chinatown\b|\bchinatown,?\s+" + OTHER_CT + r"\b|\bchinatown\s+(in|of)\s+" + OTHER_CT, re.I),
                  re.compile(r"\b(washington|d\.?c\.?)(['\u2019]s)?\s+chinatown\b|\bchinatown\s+(d\.?c|park|community\s+cultural|service\s+center|coalition)\b|"
                             r"\bfriendship\s+arch|\bgallery\s+place\b|\bpenn\s+quarter\b|\bANC\s*2C\b|\b[4-9]\d\d\s+[HIGF]\s+st(reet)?\.?,?\s+n\.?w\b", re.I)),
    "lenfantplaza": (re.compile(r"fisherman['\u2019]?s\s+wharf|\bsouthwest\s+airlines\b|"
                                r"\bwharf\b.{0,60}\b(alexandria|baltimore|san\s+francisco|boston|national\s+harbor)\b", re.I),
                     re.compile(r"\bl['\u2019]?\s?enfant\s+plaza|\bSWBID\b|\bANC\s*6D\b|\bmaine\s+ave|\bsouthwest\s+waterfront", re.I)),
    "noma": (re.compile(r"\bNoMad\b|(?i:\bcopenhagen\b|\bren[e\u00e9]\s+redzepi\b)"),
             re.compile(r"(?i:\bnoma[-\s]gallaudet\b|\bNoMa\s+BID\b|\bunion\s+(market|station)\b|\bnortheast\s+(dc|d\.c\.)\b)")),
    "shaw": (re.compile(r"\b(George\s+Bernard|Bernard|Artie|Robert\s+Gould|Irwin|Brian|Tony|Tim|Sandy|Carla|Ella|Craig|Mark|Lee|Hank|Patty)\s+Shaw\b|"
                        r"\bShaw\s+(AFB|Air\s+Force\s+Base|University|Festival|Industries|Communications)\b|\bShaw['\u2019]s\s+(supermarket|grocery)|\bFort\s+Shaw\b"),
             re.compile(r"\b(?i:in|of|historic)\s+Shaw\b(?=.*\b(?i:d\.?c|washington|NW|7th|9th|howard)\b)|\bShaw\s+(?i:neighborhood|main\s+streets?|library|metro)\b|"
                        r"\bShaw[-/\u2013]Howard\b|(?i:\bblagden\s+alley\b|\bANC\s*2G\b)")),
    "logancircle": (re.compile(r"\blogan\s+circle,?\s+(indianapolis|indiana|philadelphia|IN|PA)\b|\blogan\s+square\b", re.I),
                    re.compile(r"\bANC\s*2F\b|\b(d\.?c|NW)\b|\b14th\s+st", re.I)),
    "ustreet": (re.compile(r"\bU\s+st(reet)?\.?\s*,?\s*(s\.?e|southeast)\b|\blincoln\s+theat(re|er)\b(?=.*\b(nebraska|columbus|marion|napa|decatur)\b)", re.I),
                re.compile(r"\bU\s+st(reet)?\.?\s*,?\s*(n\.?w|northwest|corridor)\b|\b1[0-6]th\s+(and|&)\s+U\b|\bben['\u2019]?s\s+chili\s+bowl\b|\bANC\s*1B\b", re.I)),
}

# robots.txt, read the way search engines do (RFC 9309): the group naming our agent beats the "*" group, rules
# may use "*" wildcards and a "$" end anchor, the longest matching rule wins, and Allow wins a tie. The stdlib
# parser ignores wildcards, so a rule like "Disallow: /*?" slipped through it.
AGENT_TOKEN = USER_AGENT.split("/")[0].lower()  # "dc-neighborhoods-ingest"
_robots: dict[str, list[tuple[bool, str]] | bool] = {}


def parse_robots(text: str, token: str = AGENT_TOKEN) -> list[tuple[bool, str]]:
    """The (allow, path-pattern) rules that apply to `token`."""
    groups: list[tuple[list[str], list[tuple[bool, str]]]] = []
    agents: list[str] = []
    rules: list[tuple[bool, str]] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, val = (s.strip() for s in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if rules:  # a user-agent line after rules starts a new group
                groups.append((agents, rules))
                agents, rules = [], []
            agents.append(val.lower())
        elif key in ("allow", "disallow") and agents:
            if val:  # an empty Disallow allows everything
                rules.append((key == "allow", val))
    if agents:
        groups.append((agents, rules))
    mine = [r for a, r in groups if any(x != "*" and x in token for x in a)]
    if mine:
        return [rule for r in mine for rule in r]
    return [rule for a, r in groups if "*" in a for rule in r]


def _rule_matches(pattern: str, path: str) -> bool:
    regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in pattern.rstrip("$"))
    return re.match(regex + ("$" if pattern.endswith("$") else ""), path) is not None


def robots_allows(rules: list[tuple[bool, str]], path: str) -> bool:
    best: tuple[int, bool] | None = None
    for allow, pattern in rules:
        if _rule_matches(pattern, path):
            score = (len(pattern), allow)  # longest pattern wins; Allow wins a tie
            best = max(best, score) if best else score
    return True if best is None else best[1]


def allowed(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    host = f"{parts.scheme}://{parts.netloc}"
    if host not in _robots:
        try:
            req = urllib.request.Request(f"{host}/robots.txt", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as r:
                _robots[host] = parse_robots(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            # 401/403 means stay out; any other error (404 and so on) means there is no robots.txt.
            _robots[host] = e.code not in (401, 403)
        except Exception:
            _robots[host] = True
    rules = _robots[host]
    if isinstance(rules, bool):
        return rules
    path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    return robots_allows(rules, path)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.5"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def plain(s: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s.strip())
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def clean_url(u: str) -> str:
    p = urllib.parse.urlsplit(u.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(("utm_", "mc_"))]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), ""))


XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}


def _fix_entities(raw: bytes) -> bytes:
    """Some feeds (Squarespace) use HTML entities like &nbsp; that XML doesn't define."""
    def sub(m: re.Match) -> bytes:
        name = m.group(1).decode()
        return m.group(0) if name in XML_ENTITIES else html.unescape(f"&{name};").encode("utf-8")
    return re.sub(rb"&([A-Za-z][A-Za-z0-9]*);", sub, raw)


def parse_feed(raw: bytes, body: bool = False) -> list[dict]:
    """RSS 2.0, Atom, or a WordPress REST post list (/wp-json/wp/v2/posts, for sites whose RSS is broken) ->
    [{title, url, published, text}] (text is for matching only, never stored).
    body=True also matches on the article body, for outlet search feeds where the outlet already did the search."""
    if raw.lstrip()[:1] == b"[":
        out = []
        for p in json.loads(raw):
            title = plain((p.get("title") or {}).get("rendered"))
            url, pub = p.get("link") or "", parse_date(p.get("date_gmt") or p.get("date"))
            if pub and pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if url.startswith("http") and title and pub:
                out.append({"title": title, "url": clean_url(url), "published": pub,
                            "text": " ".join([title, plain((p.get("excerpt") or {}).get("rendered")),
                                              plain((p.get("content") or {}).get("rendered")) if body else ""])})
        return out
    root = ET.fromstring(_fix_entities(raw))
    out = []
    for it in root.iter():
        tag = it.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        f: dict[str, str] = {}
        cats = []
        for ch in it:
            t = ch.tag.rsplit("}", 1)[-1]
            if t == "link" and ch.get("href"):
                f.setdefault("link", ch.get("href", ""))
            elif t == "category":
                cats.append(ch.text or ch.get("term") or "")
            elif ch.text:
                f.setdefault(t, ch.text)
        url = f.get("link", "")
        title = plain(f.get("title"))
        pub = parse_date(f.get("pubDate") or f.get("published") or f.get("updated") or f.get("date"))
        if url.startswith("http") and title and pub:
            out.append({"title": title, "url": clean_url(url), "published": pub,
                        "text": " ".join([title, plain(f.get("description") or f.get("summary")), " ".join(cats),
                              plain(f.get("encoded") or f.get("content")) if body else ""])})
    return out


def previous(slug: str) -> dict:
    path = ROOT / "site" / "src" / "data" / f"{slug}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("news") or {}
    except (OSError, ValueError):
        return {}


def build_headlines(slug: str, now: float, prev: dict) -> tuple[list[dict], list[dict]]:
    terms = TERMS[slug]
    cutoff = now - ARCHIVE_DAYS * DAY
    found: dict[str, dict] = {}
    status: dict[str, dict] = {}
    for name, url, home, mode in FEEDS[slug]:
        st = status.setdefault(name, {"name": name, "url": home, "state": "ok", "matched": 0})
        if not allowed(url):
            st["state"] = "skipped: robots.txt"
            continue
        try:
            items = parse_feed(fetch(url), body=mode == "search")
        except Exception as e:  # one outlet failing must not sink the others
            st["state"] = f"error: {type(e).__name__}" if st.get("fetched", 0) == 0 else "partial"
            st["failed"] = st.get("failed", 0) + 1
            continue
        st["fetched"] = st.get("fetched", 0) + 1
        if st["state"].startswith("error"):  # an earlier page of this outlet failed, this one worked
            st["state"] = "partial"
        for it in items:
            ts = it["published"].timestamp()
            if ts < cutoff or ts > now + DAY:
                continue
            if mode != "all" and not terms.search(it["text"]):
                continue
            if slug in NOT_HERE and NOT_HERE[slug][0].search(it["text"]) and not NOT_HERE[slug][1].search(it["text"]):
                continue
            if it["url"] not in found:
                st["matched"] += 1
            found[it["url"]] = {"title": it["title"], "url": it["url"], "source": name,
                                "published": iso(int(ts * 1000)), "first_seen": iso(int(now * 1000))}
        time.sleep(0.5)
    # Merge the archive. Items keep their first_seen; same headline from two feeds counts once.
    for old in prev.get("items", []):
        u = old.get("url")
        if not u or u in found:
            if u in found:
                found[u]["first_seen"] = old.get("first_seen", found[u]["first_seen"])
            continue
        ts = parse_date(old.get("published"))
        if ts and ts.timestamp() >= cutoff:
            found[u] = old
    seen_titles: set[str] = set()
    items = []
    for it in sorted(found.values(), key=lambda x: x["published"], reverse=True):
        key = re.sub(r"\W+", "", it["title"].lower())
        if key in seen_titles:
            continue
        seen_titles.add(key)
        items.append(it)
    return items[:MAX_ITEMS], list(status.values())


def build_licenses(geom: dict, now: float, prev: dict) -> dict:
    rows = dcdata.query_features(LICENSES, geom, "STATUS = 'ACTIVE'", LICENSE_FIELDS)
    current = {r["LICENSE"]: r for r in rows if r.get("LICENSE")}
    old = prev.get("licenses") or {}
    known = set(old.get("ids", []))
    stamp = iso(int(now * 1000))
    new = [n for n in old.get("new", []) if (parse_date(n.get("first_seen")) or datetime.now(timezone.utc)).timestamp() >= now - ARCHIVE_DAYS * DAY]
    if known:  # without a previous list, nothing can be called new
        for lic, r in sorted(current.items()):
            if lic not in known:
                new.append({"license": lic, "trade_name": plain(r.get("TRADE_NAME")) or None,
                            "address": plain(r.get("ADDRESS")), "type": plain(r.get("TYPE")), "first_seen": stamp})
    # Closings: cancelled licenses, minus places relicensed at the same address under a similar name
    # (a license change, like Whole Foods' new license, is not a closing).
    def words(n: str | None) -> set[str]:
        return {w for w in re.findall(r"[a-z]{4,}", (n or "").lower())} - {"restaurant", "market", "cafe", "grill", "kitchen", "lounge", "tavern", "the"}
    active_at: dict[str, set[str]] = {}
    for r in current.values():
        active_at.setdefault(plain(r.get("ADDRESS")).upper(), set()).update(words(r.get("TRADE_NAME")))
    gone_prev = {g["license"]: g for g in old.get("cancelled", [])}
    cancelled = []
    for r in dcdata.query_features(CANCELLED, geom, "1=1", CANCELLED_FIELDS):
        lic, a = r.get("LICENSE"), plain(r.get("ADDRESS"))
        if not lic or lic in current or words(r.get("TRADE_NAME")) & active_at.get(a.upper(), set()):
            continue
        when = r.get("CANCELLATION_DATE")
        cancelled.append({"license": lic, "trade_name": plain(r.get("TRADE_NAME")) or None, "address": a, "type": plain(r.get("TYPE")),
                          "cancelled": iso(when) if when else None,
                          # "first_seen" is the night we first saw it; null for the list as it stood when tracking began
                          "first_seen": gone_prev[lic]["first_seen"] if lic in gone_prev else (stamp if "cancelled" in old else None)})
    cancelled.sort(key=lambda c: (c["cancelled"] or c["first_seen"] or "", c["trade_name"] or ""), reverse=True)
    by_type: dict[str, int] = {}
    for r in current.values():
        t = plain(r.get("TYPE")) or "Other"
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "tracked_since": old.get("tracked_since") or stamp,
        "active": len(current),
        "by_type": [{"type": k, "count": v} for k, v in sorted(by_type.items(), key=lambda kv: -kv[1])],
        "ids": sorted(current),
        "new": sorted(new, key=lambda n: n["first_seen"], reverse=True),
        "cancelled": cancelled,
    }


def build(geom: dict, hood: dict, now: float) -> dict:
    slug = hood["slug"]
    prev = previous(slug)
    items, status = build_headlines(slug, now, prev)
    return {
        "generated_at": iso(int(now * 1000)),
        "archive_days": ARCHIVE_DAYS,
        "sources": [{"name": s["name"], "url": s["url"]} for s in status]
        + [{"name": "DC ABCA, Alcohol License Business Locations (Open Data DC)", "url": LICENSES_PAGE},
           {"name": "DC ABCA, Liquor License Cancellations (Open Data DC)", "url": CANCELLED_PAGE}],
        "outlets": status,
        "items": items,
        "licenses": build_licenses(geom, now, prev),
    }


def check(section: dict) -> list[str]:
    errors = []
    for key in ("generated_at", "sources", "outlets", "items", "licenses"):
        if key not in section:
            errors.append(f"news: missing {key}")
    if errors:
        return errors
    ok = [o for o in section["outlets"] if o["state"] in ("ok", "partial")]
    if len(ok) < len(section["outlets"]) / 2:
        errors.append(f"news: only {len(ok)} of {len(section['outlets'])} outlets fetched")
    if not section["items"]:
        errors.append("news: no headlines")
    for it in section["items"]:
        if not (it.get("url", "").startswith("http") and it.get("title") and it.get("source") and it.get("published")):
            errors.append(f"news: incomplete item {it.get('url')}")
        if set(it) - {"title", "url", "source", "published", "first_seen"}:
            errors.append(f"news: item carries extra fields {sorted(set(it))}")
    if not section["licenses"].get("active"):
        errors.append("news: no active liquor licenses found")
    errors += [f"news: forbidden field {h}" for h in find_forbidden(section)]
    return errors


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    slug = sys.argv[1] if len(sys.argv) > 1 else "petworth"
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if not hood:
        print(f"unknown neighborhood {slug!r}", file=sys.stderr)
        return 2
    t0 = time.time()
    geom = dcdata.hood_boundary(config, hood)
    section = build(geom, hood, time.time())
    out_dir = ROOT / "ingest" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"news-{slug}.json").write_text(json.dumps(section, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{slug}: {len(section['items'])} headlines ({time.time() - t0:.0f}s)")
    for o in section["outlets"]:
        print(f"  {o['name']:24} {o['state']:22} {o['matched']}")
    for it in section["items"][:8]:
        print(f"  {it['published'][:10]} {it['source']:16} {it['title'][:80]}")
    lic = section["licenses"]
    print(f"  liquor licenses: {lic['active']} active, {len(lic['new'])} new")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("news ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
