"""`history` section: how the neighborhood was built, and what the paper said 100 years ago this week.

    python ingest/history.py petworth

Buildings come from DC HPO's "Historic Data on DC Buildings" (HistoryQuest), which indexes original
building permits. Historic owner names are never requested: only address, date, architect, builder,
estimated cost and permit number.

The archive comes from the Evening Star on the Library of Congress's Chronicling America (loc.gov JSON
API, no key). It searches the calendar week exactly 100 years before `now` for each neighborhood's
terms, pulls each matching page's OCR text and clips a sentence or two around the mention. Clips that
touch race, covenants, deed restrictions or slurs are skipped (see SCREEN_TERMS): they need an editor's
context, not a bare clipping.
"""

from __future__ import annotations

import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dcdata  # noqa: E402
from run import find_forbidden, hundred_block, iso  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

HISTORIC = "https://services.arcgis.com/neT9SoYxizqTHZPH/arcgis/rest/services/DC_HistoricalBuildings2017/FeatureServer/0"
HISTORIC_PAGE = "https://opendata.dc.gov/datasets/historic-data-on-dc-buildings"
# "Owner" is deliberately absent.
HQ_FIELDS = ["FULLADDRES", "Date", "Architect", "Builder", "EstimatedCost", "PermitNumber"]

LOC_SEARCH = "https://www.loc.gov/collections/chronicling-america/"
LOC_TEXT = "https://tile.loc.gov/text-services/word-coordinates-service"
STAR = "evening star (washington, d.c.) 1854-1972"
STAR_ITEM = "https://www.loc.gov/item/sn83045462/"
UA = "dc-neighborhoods-ingest/0.1 (+https://petworth.org)"
PAGES_PER_TERM = 8
MAX_PAGE_FETCHES = 24
ARCHIVE_BUDGET_S = 110  # leave room inside the ~3 minute per-neighborhood budget
MAX_CLIPS = 6

# Per-neighborhood archive settings. `pattern` finds the mention in OCR text; `local` boosts clips that
# also name a local street or institution, so clearly-local items rank above passing mentions.
ARCHIVE = {
    "petworth": {
        "terms": ["Petworth", '"Grant Circle"', '"Sherman Circle"'],
        "pattern": r"petworth|grant\s+circle|sherman\s+circle",
        "local": r"georgia\s+av|upshur|shepherd|iowa\s+av|delafield|kansas\s+av|new\s+hampshire\s+av|"
                 r"rock\s+creek\s+church|petworth\s+(school|m\.?\s*e\.?|methodist|citizens|library)|st\.?\s+gabriel|"
                 r"roosevelt\s+high|sherman\s+circle|grant\s+circle",
    },
    "tenleytown": {
        "terms": ["Tenleytown", "Tenley", '"Fort Reno"'],
        # Bare "Tenley" also matches people's surnames, so the clip must say Tenleytown, Tenley road/circle, or Fort Reno.
        "pattern": r"tenley\s*-?\s*town|tenley\s+(road|circle)|fort\s+reno",
        "local": r"wisconsin\s+av|river\s+road|albemarle|brandywine|chesapeake|fessenden|grant\s+road|"
                 r"janney|st\.?\s+ann|fort\s+reno|reno\s+road|nebraska\s+av|american\s+university",
    },
    "adamsmorgan": {
        # "Adams Morgan" dates from the 1950s (the Adams and Morgan schools). In 1926 the paper said Lanier Heights,
        # Washington Heights or Kalorama; "Washington Heights" also names a New York neighborhood, so it only
        # counts with a local street or landmark nearby (see `pattern`).
        # Tested against the 1926 Evening Star (2026-11-01): each term had hits in the target week, all DC.
        # Most reliable first: the page budget can run out before later terms are read.
        "terms": ['"Kalorama road"', '"Ontario road"', '"Lanier Heights"', '"Champlain street"', '"Washington Heights"'],
        "pattern": r"lanier\s+heights|kalorama\s+(road|park|heights)|ontario\s+road|champlain\s+st|"
                   r"washington\s+heights(?=.{0,200}(columbia\s+road|18th|kalorama|lanier|champlain|ontario))|"
                   r"columbia\s+road(?=.{0,120}18th)",
        "local": r"18th\s+st|columbia\s+road|kalorama|lanier|champlain|ontario\s+road|belmont|mintwood|calvert|"
                 r"adams\s+school|morgan\s+school|meridian\s+hill",
    },
    "friendshipheights": {
        # Only "Friendship Heights" itself: "Chevy Chase, D.C." was tried and pulled in house ads near Connecticut
        # Ave, which is Chevy Chase, not this area.
        "terms": ['"Friendship Heights"'],
        "pattern": r"friendship\s+heights",
        "local": r"wisconsin\s+av|western\s+av|jenifer|harrison\s+st|military\s+road|reno\s+road|"
                 r"chevy\s+chase\s+circle|tenley",
    },
    # East-side terms tested against the 1926 Evening Star (ingest/SOURCES-EAST.md); west side from 1926 usage.
    "capitolhill": {
        "terms": ['"Lincoln Park"', '"Stanton Park"', '"East Capitol street"', '"Capitol Hill"'],
        # "Capitol Hill" and "Lincoln Park" also mean Congress and Chicago, so they need a local cue (see `local`).
        "pattern": r"stanton\s+park|east\s+capitol\s+st|pennsylvania\s+av(enue|e)?\.?\s+(southeast|s\.?\s?e)|eastern\s+market|"
                   r"seward\s+square|(lincoln\s+park|capitol\s+hill)(?=.{0,200}(s\.\s?e\.|n\.\s?e\.|southeast|northeast|citizens|"
                   r"east\s+capitol|massachusetts\s+av))",
        "local": r"east\s+capitol|lincoln\s+park|stanton\s+park|eastern\s+market|southeast|northeast|s\.\s?e\.|n\.\s?e\.",
    },
    "hstreet": {
        "terms": ['"H street"'],  # loc.gov drops one-letter words, so the NE form is checked locally
        "pattern": r"\bh\s+st(reet|\.)?\s*,?\s*n(orth)?\.?\s?e(ast)?\b",
        "local": r"northeast|n\.\s?e\.|empire\s+theat|gallaudet",
    },
    "navyyard": {
        "terms": ['"Washington Navy Yard"', '"navy yard"'],
        # In 1926 "navy yard" usually meant Philadelphia or Norfolk; only the Washington yard or SE cues count.
        "pattern": r"washington\s+navy\s+yard|navy\s+yard\s+(here|in\s+this\s+city|employes|workers|gate)|gun\s+factory|"
                   r"\bm\s+st(reet|\.)?\s+(southeast|s\.?\s?e)|(8th|eighth)\s+st(reet|\.)?\s+(southeast|s\.?\s?e)",
        "local": r"southeast|s\.\s?e\.|washington\s+navy\s+yard|8th\s+st|m\s+st",
    },
    "anacostia": {
        "terms": ['"Anacostia"', '"Nichols avenue"', '"Good Hope road"'],
        # In 1926 Anacostia was the town; the river and its flats, park and bridge are excluded.
        "pattern": r"anacostia(?!\s+(river|flats?|park|water\s*front|bridge|reclamation|basin))|nichols\s+av|good\s+hope\s+r(oa)?d",
        "local": r"nichols\s+av|good\s+hope|minnesota\s+av|cedar\s+hill|douglass|anacostia\s+(citizens|lodge|station|road)",
    },
    "columbiaheights": {
        "terms": ['"Columbia Heights"', '"Tivoli"'],
        "pattern": r"columbia\s+heights|tivoli\s+theat|crandall.s\s+tivoli",
        "local": r"14th\s+st|fourteenth|park\s+road|irving|columbia\s+road|tivoli|citizens",
    },
    "georgetown": {
        "terms": ['"Georgetown"'],
        # Georgetown in 1926 also meant towns in other states and the university's teams; keep local cues.
        "pattern": r"georgetown(?!,?\s+(ky|del|s\.?\s?c|texas|ohio|colo|mass|me\b|kentucky|delaware))(?=.{0,200}"
                   r"(m\s+st|wisconsin\s+av|canal|key\s+bridge|n\.\s?w\.|northwest|citizens|p\s+st|q\s+st|r\s+st|dumbarton))",
        "local": r"m\s+st|wisconsin\s+av|canal|dumbarton|citizens|n\.\s?w\.",
    },
    "dupontcircle": {
        "terms": ['"Dupont Circle"', '"Du Pont Circle"'],
        "pattern": r"du\s*pont\s+circle",
        "local": r"connecticut\s+av|massachusetts\s+av|new\s+hampshire\s+av|p\s+st|q\s+st|r\s+st|n\.\s?w\.",
    },
    "clevelandpark": {
        "terms": ['"Cleveland Park"'],
        "pattern": r"cleveland\s+park(?!,?\s+(ohio|o\.))",
        "local": r"connecticut\s+av|macomb|newark|ordway|porter|wisconsin\s+av|citizens",
    },
    "chevychase": {
        # Real-estate ads near Connecticut Ave are this neighborhood (they were wrong only for Friendship Heights).
        "terms": ['"Chevy Chase, D. C."', '"Chevy Chase, D.C."'],
        "pattern": r"chevy\s+chase,?\s+d\.?\s*c",
        "local": r"connecticut\s+av|chevy\s+chase\s+circle|livingston|northampton|military\s+road|citizens",
    },
    # Added 2026-11-01; terms tested against the Evening Star (ingest/SOURCES-NORTHWEST.md, SOURCES-CENTRAL.md).
    "brookland": {
        "terms": ["Brookland", '"Brookland Citizens"', '"Catholic University"'],
        # "Catholic University" in 1926 is mostly its football team.
        "pattern": r"brookland|catholic\s+univ|franciscan\s+monastery|national\s+shrine|turkey\s+thicket",
        "reject": r"foot\s*ball|eleven|gridiron|touchdown|varsity|coach|quarterback|basket\s*ball|blue\s+ridge|stadium",
        "local": r"12th\s+st|twelfth|monroe\s+st|newton\s+st|otis\s+st|quincy|rhode\s+island\s+av|michigan\s+av|10th\s+st|n\.\s?e\.|"
                 r"northeast|citizens.\s+association|masonic\s+temple",
    },
    "gloverpark": {
        # The Glover Park subdivision was new in 1926 (mostly real-estate ads).
        "terms": ['"Glover Park"', '"Tunlaw road"'],
        "pattern": r"glover\s+park|tunlaw|cathedral\s+heights\s+citizens|observatory\s+(hill|circle)",
        "local": r"wisconsin\s+av|tunlaw|cathedral\s+av|calvert\s+st|39th|37th|38th|new\s+mexico\s+av|n\.\s?w\.|citizens",
    },
    "palisades": {
        # MacArthur Boulevard was Conduit Road in 1926; "Palisades" alone also means the Hudson.
        "terms": ['"Conduit road"', '"Chain Bridge"', "Palisades"],
        "pattern": r"conduit\s+r(oa)?d|chain\s+bridge\s+r(oa)?d|palisades\s+of\s+the\s+potomac|"
                   r"palisades(?=.{0,200}(conduit|d\.\s?c|n\.\s?w|potomac|reservoir))",
        "reject": r"hudson|new\s+jersey|n\.\s?j\.|palisades\s+(interstate|park,?\s+n)|cross\s+chain\s+bridge\s+to\s+va|virginia\s+side",
        "local": r"conduit|reservoir|potomac|canal|chain\s+bridge\s+road|foxhall|arizona\s+av|macarthur|dalecarlia|n\.\s?w\.",
    },
    "vanness": {
        # The National Bureau of Standards held the future UDC site in 1926; "Forest Hills" in sports copy is Queens tennis.
        "terms": ['"North Cleveland Park"', '"Bureau of Standards"', '"Van Ness street"', '"Forest Hills"'],
        "pattern": r"bureau\s+of\s+standards(?=.{0,200}(near|squares|connecticut|van\s+ness|home|house|lot))|north\s+cleveland\s+park|"
                   r"van\s+ness\s+st|forest\s+hills(?=.{0,200}(connecticut|d\.\s?c|n\.\s?w|chevy\s+chase|rock\s+creek))",
        "reject": r"forest\s+hills,?\s+(l\.\s?i|long\s+island|n\.\s?y|queens)|tennis",
        "local": r"connecticut\s+av|van\s+ness|veazey|upton|tilden|yuma|albemarle|windom|38th|36th|reno\s+road|soapstone|n\.\s?w\.",
    },
    # Several of these names are later coinages (NoMa, L'Enfant Plaza, Shaw as a neighborhood; Logan Circle was Iowa Circle
    # until 1930), so the terms are 1926 landmarks and streets. loc.gov drops one-letter words, so "U street" is really a
    # search for "street": the pattern does the real filtering. The 1926 Star was segregated, so Shaw and U Street clips are
    # thin and many are screened out.
    "chinatown": {
        "terms": ['"Mount Vernon place"', "\"Ford's Theater\"", '"Pension Office"', '"Seventh street"', "Chinatown"],
        "pattern": r"mount\s+vernon\s+(place|square)|ford.s\s+theat|pension\s+(office|building)|judiciary\s+square|court\s+house\s+park|"
                   r"\b[4-9]\d\d\s+(seventh|7th|eighth|8th|ninth|9th|tenth|10th)\s+st(reet|\.)?|"
                   r"(seventh|7th|eighth|8th|ninth|9th)\s+st(reet|\.)?\s+(between|and|at)\s+[d-i]\b|chinatown",
        "reject": r"sage\s+of\s+chinatown|(seventh|7th)\s+st(reet|\.)?\s+(southwest|s\.\s?w)|patent\s+office\s+(examiner|team|bowl|roll)|"
                  r"chinatown.{0,40}(san\s+francisco|new\s+york)",
        "local": r"n\.\s?w\.|northwest|seventh\s+st|7th\s+st|massachusetts\s+av|new\s+york\s+av|mount\s+vernon|judiciary|lansburgh|"
                 r"woodward|palais\s+royal|kann|patent\s+office|pension",
    },
    "lenfantplaza": {
        "terms": ['"Southwest Washington"', '"Neighborhood House"', "Southwest", '"Maine avenue"'],
        "pattern": r"southwest\s+(washington|site|market|section|citizens)|neighborhood\s+house|"
                   r"\b\d{2,4}\s+[\w\-½]+\s+st(reet|\.)?\s+(southwest|s\.\s?w)|maine\s+av(enue|e)?\.?\s+(southwest|s\.\s?w)|"
                   r"water\s+st(reet|\.)?\s+(southwest|s\.\s?w)|four.and.a.half\s+st|fish\s+wharf|seventh\s+street\s+wharf",
        "reject": r"(south\s+and\s+)?southwest\s+winds?|winds?,?\s+(mostly\s+)?(south\s+and\s+)?southwest|southwest\s+(virginia|texas|africa|pacific)|"
                  r"maine\s+av(enue|e)?\.?\s+(southeast|s\.\s?e)",
        "local": r"s\.\s?w\.|southwest|maine\s+av|water\s+st|n\s+street|seventh\s+st|four.and.a.half|wharf|barney",
    },
    "noma": {
        "terms": ['"Sibley Hospital"', "Eckington", '"North Capitol street"', '"Government Printing Office"'],
        "pattern": r"sibley\s+hospital|eckington|government\s+printing\s+office|swampoodle|gonzaga\s+(college|high)|"
                   r"\b([2-9]\d\d|1[0-5]\d\d)\s+north\s+capitol\s+st|north\s+capitol\s+(street\s+)?(and|at)\s+[g-r]\s+st|tiber\s+creek",
        "reject": r"gonzaga\s*(vs\.?|,|\d)|spokane",
        "local": r"north\s+capitol|first\s+st(reet)?\s+n|1st\s+st|n\.\s?e\.|northeast|eckington|florida\s+av|new\s+york\s+av|k\s+st|m\s+st|"
                 r"union\s+station|printing\s+office",
    },
    "shaw": {
        "terms": ['"Shaw Junior High"', '"Rhode Island avenue"', '"Ninth street"', '"Seventh street"'],
        "pattern": r"shaw\s+junior\s+high|howard\s+theat|o\s+street\s+market|northern\s+liberty|"
                   r"\b1[1-9]\d\d\s+(seventh|7th|ninth|9th|eighth|8th)\s+st(reet|\.)?|"
                   r"(seventh|ninth)\s+(street\s+)?and\s+(rhode\s+island|[m-t]\s+st)|rhode\s+island\s+av(enue|e)?\.?\s+and\s+(sixth|seventh|eighth|ninth|tenth)",
        "reject": r"(seventh|ninth|rhode\s+island)\s+(street|avenue)\s+(southwest|northeast|s\.\s?w|n\.\s?e)",
        "local": r"n\.\s?w\.|northwest|seventh\s+st|ninth\s+st|rhode\s+island\s+av|o\s+st|p\s+st|r\s+st|s\s+st|t\s+st|shaw|howard",
    },
    "logancircle": {
        "terms": ['"Iowa Circle"', '"Thomas Circle"', '"Vermont avenue"', '"Fourteenth street"'],
        "pattern": r"iowa\s+circle|logan\s+circle|thomas\s+circle|vermont\s+avenue\s+(christian|church|m\.\s?e)|"
                   r"\b1[0-6]\d\d\s+(vermont|rhode\s+island)\s+av|\b1[0-6]\d\d\s+(fourteenth|14th|thirteenth|13th|fifteenth|15th)\s+st|"
                   r"\b1[3-5]\d\d\s+[n-r]\s+st(reet|\.)?\s+n\.?\s?w|(fourteenth|thirteenth)\s+(street\s+)?and\s+[n-r]\s+st",
        "reject": r"park\s+r(oa)?d|columbia\s+heights|arcadia|above\s+.?k.?\b",
        "local": r"vermont\s+av|rhode\s+island\s+av|fourteenth|thirteenth|fifteenth|\b[n-r]\s+st|iowa\s+circle|thomas\s+circle|n\.\s?w\.",
    },
    "ustreet": {
        "terms": ['"Howard University"', '"Lincoln Theater"', '"U street"', '"Florida avenue"'],
        "pattern": r"howard\s+university|lincoln\s+theat|lincoln\s+colonnade|true\s+reformers?|industrial\s+savings\s+bank|"
                   r"\b([7-9]|1[0-9])\d\d\s+U\s+st(reet|\.)?|\bU\s+st(reet|\.)?\s+(n\.?\s?w|northwest)|le\s?droit\s+park|"
                   r"(eleventh|twelfth|thirteenth|fourteenth|ninth|seventh)\s+(street\s+)?and\s+(U|florida\s+av)",
        # Griffith Stadium (now Howard University Hospital) is only ever a football venue in November 1926.
        "reject": r"foot\s*ball|eleven|touchdown|gridiron|varsity|quarterback|coach|base\s*ball|senators|griffith\s+stadium|"
                  r"\bU\s+st(reet|\.)?\s+(s\.\s?e|southeast|n\.\s?e|northeast)",
        "local": r"\bU\s+st|florida\s+av|georgia\s+av|vermont\s+av|seventh\s+st|eleventh|twelfth|thirteenth|fourteenth|le\s?droit|"
                 r"howard\s+place|sherman\s+av|n\.\s?w\.",
    },
    # Added 2026-11-02 (ingest/SOURCES-LATE.md).
    "bloomingdale": {
        "terms": ['"Eckington"', '"North Capitol street"', "Bloomingdale", '"McMillan"'],
        "pattern": r"eckington|bloomingdale\s+(playground|citizens|section|field|basket)|(at|the)\s+bloomingdale\b(?!\W+\d)|truxton\s+circle|"
                   r"mcmillan\s+(park|reservoir)|filtration\s+plant|\b(1[3-9]|2[0-4])\d\d\s+north\s+capitol\s+st|north\s+capitol\s+(street\s+)?(near|and|at)\s+[p-w]\b",
        # Bloomingdale's stock, and "Eckington as per plat", which LEGAL mostly catches.
        "reject": r"bloomingdale['’]?s|bloomingdale\W+\d|as\s+per\s+plat|north\s+capitol\s+st(reet)?\s+(s\.\s?e|southeast)",
        "local": r"north\s+capitol|first\s+st|rhode\s+island\s+av|florida\s+av|lincoln\s+road|t\s+st|u\s+st|n\.\s?e\.|n\.\s?w\.|market\s+site|citizens",
    },
    "foggybottom": {
        # "Foggy Bottom" had 0 pages this week. GW's campus was already at 20th-21st and G.
        "terms": ['"Washington Circle"', '"George Washington University"', '"Twenty-first street"', '"Twenty-third street"'],
        "pattern": r"washington\s+circle|foggy\s+bottom|george\s+washington\s+univ|\b2[0-5]\d\d\s+(pa\.?|pennsylvania)\s+ave|\b(19|2[0-5])\d\d\s+[e-k]\s+st|"
                   r"(twenty.?(first|second|third|fourth|fifth)|2[1-5](st|nd|rd|th))\s+st(reet|\.)?\s+(n\.?\s?w|northwest|and\s+(pennsylvania|virginia|new\s+hampshire|[c-l]\b)|between|near)",
        "reject": r"foot\s*ball|eleven|touchdown|gridiron|varsity|quarterback|coach|hockey|cross.country|grif\s?fith|ursinus|colonials|sigma|fraternity",
        "local": r"n\.\s?w\.|pennsylvania\s+av|pa\.\s+ave|new\s+hampshire|virginia\s+av|washington\s+circle|twenty|2[0-5]th|st\.?\s+paul|g\s+st|h\s+st|i\s+st",
    },
    "hilleast": {
        "terms": ['"Potomac avenue"', '"Fifteenth street southeast"', '"Massachusetts avenue southeast"', '"Thirteenth street southeast"'],
        "pattern": r"\b1[3-9]\d\d\s+(potomac|massachusetts|independence|north\s+carolina|kentucky|pennsylvania)\s+av(enue|e)?\.?\s+(s\.?\s?e|southeast)|"
                   r"(thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth)\s+st(reet|\.)?\s+(s\.?\s?e|southeast)|\b\d{2,4}\s+1[3-9]th\s+st\.?\s+s\.?\s?e|"
                   r"potomac\s+av(enue|e)?\.?\s+(s\.?\s?e|southeast)|hill\s+east",
        "reject": r"interment|funeral|deaths?\s+reported|years\s+old",
        "local": r"s\.\s?e\.|southeast|potomac\s+av|kentucky\s+av|massachusetts\s+av|pennsylvania\s+av|lincoln\s+park|eastern\s+high|citizens",
    },
    "kingmanpark": {
        # "Kingman Lake", "Kingman Park", "Anacostia Park": 0 this week. Kingman Park wasn't built until the late 1920s.
        "terms": ['"Eastern High School"', '"Rosedale"', '"Benning road"', '"Maryland avenue northeast"'],
        "pattern": r"eastern\s+high|kingman\s+(lake|park)|rosedale\s+(st|playground|citizens|recreation|section)|\b(1[5-9]|2[0-5])\d\d\s+benning\s+r|"
                   r"\b1[5-9]\d\d\s+(gales|rosedale|c|d|e|f|g|h|isherwood|maryland)\s+(st|ave)[a-z.]*\s+(n\.?\s?e|northeast)|seventeenth\s+and\s+east\s+capitol",
        "reject": r"foot\s*ball|eleven|touchdown|gridiron|cadet|basket\s*ball|miss\s+rosedale|furlongs|terminations?|substitute|caretaker|janitor|years\s+old|interment",
        "local": r"n\.\s?e\.|northeast|east\s+capitol|benning|maryland\s+av|rosedale|eastern\s+high|seventeenth|nineteenth",
    },
    "mountpleasant": {
        # "Mt. Pleasant" also leads the rooms-for-rent classifieds and is a Maryland Grange town; Mount Pleasant No. 33 is a Masonic lodge.
        "terms": ['"Mount Pleasant Citizens"', '"Mount Pleasant Library"', '"Mount Pleasant"', '"Irving street"'],
        "pattern": r"mount\s+pleasant\s+(citizens|public\s+library|branch|library|street|m\.\s?e|methodist|congregational|car\s+line|section)|mt\.?\s+pleasant\s+(st|citizens|library)|"
                   r"\b1[6-9]\d\d\s+(lamont|irving|kilbourne|kenyon|newton|harvard|hobart)\s+st|\b3[0-3]\d\d\s+(mount|mt\.?)\s+pleasant\s+st|shrine\s+of\s+the\s+sacred\s+heart",
        "reject": r"duckpin|team\s+standings|pomona|grange|new\s+market|maryland|(mount|mt\.?)\s+pleasant,?\s+no\.?\s*\d|odd\s+fellows|masonic|frederick|a\.?m\.?i\.?\b",
        "local": r"sixteenth|16th|seventeenth|17th|park\s+road|irving|lamont|kenyon|harvard|mount\s+pleasant\s+st|columbia\s+road|n\.\s?w\.|citizens",
    },
    "stadiumarmory": {
        # 1926 here is the cemetery, the jail and Gallinger Municipal Hospital. The stadium is 35 years off, and funeral notices dominate.
        "terms": ['"Congressional Cemetery"', '"District jail"', '"Gallinger Hospital"', '"East Capitol street"'],
        "pattern": r"congressional\s+cemetery|district\s+jail|washington\s+asylum|gallinger\s+(municipal\s+)?hospital|jail\s+hill|\b(19|2[0-3])\d\d\s+east\s+capitol\s+st|"
                   r"\b(19th|nineteenth|twentieth|20th)\s+(st(reet|\.)?\s+)?and\s+(b\s+st|east\s+capitol|independence)",
        "reject": r"interment|inter\s+ment|funeral|deaths?\s+reported|remains|years\s+old|hospital\.\s",
        "local": r"s\.\s?e\.|southeast|nineteenth|19th|east\s+capitol|anacostia|e\s+st|cemetery|chapel|commissioners|hospital",
    },
    "trinidad": {
        # Bare "Trinidad" is shipping news (Maravi--Trinidad). Union Market's ancestor came later. Gallaudet College = Kendall Green.
        "terms": ['"Ivy City"', '"Trinidad avenue"', '"Gallaudet College"', '"Mount Olivet"', '"Montello"'],
        "pattern": r"ivy\s+city|trinidad\s+(ave|citizens|section|community|school)|gallaudet\s+college|kendall\s+green|montello\s+av|mount\s+olivet\s+(road|r\.?\s?d)|"
                   r"\b\d{3,4}\s+(montello|trinidad|holbrook|neal|orren|queen|raum)\s+(st|av)[a-z.]*\s+n\.?\s?e",
        "reject": r"tobago|port\s+of\s+spain|foot\s*ball|eleven|touchdown|gridiron|varsity|quarterback|coach|american\s+university\s+(at|vs)|interment|inter\s+ment|cemetery",
        "local": r"n\.\s?e\.|northeast|florida\s+av|bladensburg|new\s+york\s+av|west\s+virginia\s+av|ivy\s+city|crummell|gallaudet|kendall\s+green|citizens",
    },
    "woodleypark": {
        # Woodley Park proper only. Most reliable first; "Wardman Park" (47 pages this week) goes last so it can't eat the page budget.
        "terms": ['"Woodley Park"', '"Connecticut avenue bridge"', '"Zoological Park"', '"Woodley road"', '"Wardman Park"'],
        "pattern": r"woodley\s+park|\b2[6-9]\d\d\s+woodley\s+r|wardman\s+park|national\s+zoological\s+park|connecticut\s+avenue\s+bridge|\bzoo\b(?=.{0,120}(rock\s+creek|connecticut|national))|"
                   r"\b2[3-9]\d\d\s+calvert\s+st|\b2[6-9]\d\d\s+connecticut\s+av",
        "reject": r"cathedral|mount\s+st\.?\s+alban|john\s+eaton|tilden|cleveland\s+park|syncopating|horsem[ae]n|this\s+afternoon\s+and\s+evening",
        "local": r"connecticut\s+av|calvert\s+st|woodley|rock\s+creek|wardman|zoo|cathedral\s+av|twenty-(sixth|seventh|eighth|ninth)|2[6-9]th\s+st",
    },
}

# Content screening. A clip that matches any of these is skipped, never published. 1920s news and
# real-estate ads often carry segregation language that needs written context from an editor.
SCREEN_TERMS = [
    "race", "races", "racial", "colored", "coloured", "negro", "negroes", "white only", "whites only", "for whites",
    "white people", "white persons", "white residents", "caucasian", "segregation", "segregated",
    "covenant", "covenants", "restricted", "restriction", "restrictions", "restrictive",
    "darky", "darkey", "darkies", "pickaninny", "coon", "nigger", "jap", "chink", "dago", "wop", "kike",
]
SCREEN = re.compile(r"\b(" + "|".join(re.escape(t).replace(r"\ ", r"\s+") for t in SCREEN_TERMS) + r")\b", re.I)
# Legal notices (trustee sales, probate) and rosters name private individuals; skip them too.
LEGAL = re.compile(r"\b(trustees?|liber|folio|plat recorded|deed of trust|probate|executor|administratri?x)\b", re.I)
# Building-permit and sale columns name the owner ("John Smith, owner and builder"); historic owner names are forbidden.
OWNER_NOTICE = re.compile(r"\bowners?\s+and\s+builders?\b|,\s*owners?\b|\bto\s+erect\b|\bsquare\s+\d+|\blot\s+\d+", re.I)
NAME_LIST = re.compile(r"\b[A-Z][a-z]+(?: [A-Z]\.)? [A-Z][a-z]+, [a-z]")
ABBREV = {"st", "ave", "n", "s", "e", "w", "mr", "mrs", "dr", "rev", "no", "sts", "jr", "co", "p.m", "a.m",
          "d.c", "nw", "n.w", "ne", "se", "sw", "pl", "rd"}
SHORT_OK = {"a", "i", "an", "as", "at", "be", "by", "do", "go", "he", "if", "in", "is", "it", "me", "my", "no", "of",
            "on", "or", "so", "to", "up", "us", "we", "am", "mr", "dr", "st", "n.w", "s.w", "ave", "mrs", "&", "…"}
WORD = re.compile(r"^[\"'(“]?[A-Za-z][a-z]*[.,;:!?'\")”]*$|^\$?[\d,.]+[.,;:]?$")
JUNK_NAMES = {"", "unknown", "none", "n/a", "na", "not listed", "owner", "same", "self", "?"}


# ---------------------------------------------------------------- buildings (HistoryQuest)

def year_of(ms: int | None) -> int | None:
    # Historic permit dates are negative epoch milliseconds, which time.gmtime rejects on Windows.
    if ms is None:
        return None
    return (datetime(1970, 1, 1) + timedelta(milliseconds=ms)).year


def clean_name(name: str | None) -> str | None:
    """'Thompson, D. D.' -> 'D. D. Thompson'; firms ('Shannon & Luchs, Inc.') are left alone."""
    n = re.sub(r"\s+", " ", (name or "").strip())
    if n.lower().strip(".") in JUNK_NAMES:
        return None
    parts = [p.strip() for p in n.split(",")]
    if len(parts) == 2 and parts[1] and not re.search(r"\b(inc|co|corp|company|bros|jr|sr|ltd|llc)\b", parts[1], re.I) \
            and "&" not in n and " and " not in n.lower():
        return f"{parts[1]} {parts[0]}"
    return n


def street_title(s: str) -> str:
    out = []
    for w in s.split():
        if w.upper() in ("NW", "NE", "SW", "SE"):
            out.append(w.upper())
        elif re.match(r"^\d+(ST|ND|RD|TH)$", w, re.I):
            out.append(w.lower())
        else:
            out.append(w.capitalize())
    return " ".join(out)


def block_label(address: str | None) -> str | None:
    if not address or not re.match(r"^\s*\d+\s+\S", address):
        return None
    hb = hundred_block(address)
    m = re.match(r"^(\S+ block of )(.*)$", hb or "")
    return m.group(1) + street_title(m.group(2)) if m else None


def cost_of(value) -> int | None:
    digits = re.sub(r"[^\d]", "", str(value or ""))
    return int(digits) if digits else None


def names_list(people: list[str]) -> str:
    return people[0] if len(people) == 1 else ", ".join(people[:-1]) + " and " + people[-1]


def featured_block(rows: list[dict]) -> dict | None:
    """The block with the most records sharing one builder and one year (a speculative row, usually)."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r["block"] and r["builder"] and r["year"]:
            groups[(r["block"], r["builder"], r["year"])].append(r)
    if not groups:
        return None
    (block, builder, year), members = max(groups.items(), key=lambda kv: (len(kv[1]), -kv[0][2]))
    # Cost is per permit, not per house: one permit often covered a whole row.
    permits: dict[str, list[dict]] = defaultdict(list)
    for r in members:
        permits[r["permit"] or "unknown"].append(r)
    largest_num, largest = max(permits.items(), key=lambda kv: (len(kv[1]), kv[1][0]["cost"] or 0))
    architects = Counter(r["architect"] for r in members if r["architect"])
    arch = [{"name": n, "count": c} for n, c in architects.most_common(5)]
    largest_cost = largest[0]["cost"]
    n_permits = len(permits)
    sentence = (
        f"In {year}, {builder} built {len(members)} buildings on the {block} under "
        f"{n_permits} permit{'s' if n_permits != 1 else ''}"
    )
    if arch:
        sentence += f", designed by {names_list([a['name'] for a in arch[:2]])}"
    sentence += "."
    if n_permits > 1 or len(largest) > 1:
        sentence += f" The largest permit covered {len(largest)} buildings"
        sentence += f" at an estimated ${largest_cost:,} in total." if largest_cost else "."
    return {
        "block": block,
        "year": year,
        "buildings": len(members),
        "permits": n_permits,
        "builder": builder,
        "architects": arch,
        "largest_permit": {"buildings": len(largest), "cost": largest_cost},
        "sentence": sentence,
    }


def build_buildings(geom: dict) -> dict:
    for attempt in range(3):  # dcdata retries URLError only; ArcGIS Online sometimes drops the connection
        try:
            raw = dcdata.query_features(HISTORIC, geom, "1=1", HQ_FIELDS)
            break
        except (http.client.HTTPException, OSError):
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))
    rows = [
        {
            "block": block_label(r.get("FULLADDRES")),
            "year": year_of(r.get("Date")),
            "architect": clean_name(r.get("Architect")),
            "builder": clean_name(r.get("Builder")),
            "cost": cost_of(r.get("EstimatedCost")),
            "permit": str(r.get("PermitNumber") or "").strip() or None,
        }
        for r in raw
    ]
    years = [r["year"] for r in rows if r["year"] and 1800 <= r["year"] <= 2100]
    decades = Counter(y // 10 * 10 for y in years)
    return {
        "records": len(rows),
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "by_decade": [{"decade": d, "count": decades[d]} for d in sorted(decades)],
        "top_architects": [{"name": n, "count": c} for n, c in Counter(r["architect"] for r in rows if r["architect"]).most_common(5)],
        "top_builders": [{"name": n, "count": c} for n, c in Counter(r["builder"] for r in rows if r["builder"]).most_common(5)],
        "featured_block": featured_block(rows),
    }


# ---------------------------------------------------------------- archive (Evening Star, loc.gov)

def week_100_years_ago(now: float) -> tuple[date, date]:
    today = datetime.fromtimestamp(now, timezone.utc).date()
    try:
        then = today.replace(year=today.year - 100)
    except ValueError:  # Feb 29
        then = today.replace(year=today.year - 100, day=28)
    start = then - timedelta(days=(then.weekday() + 1) % 7)  # back to Sunday
    return start, start + timedelta(days=6)


def week_label(start: date, end: date) -> str:
    if start.year != end.year:
        return f"{start:%B} {start.day}, {start.year} – {end:%B} {end.day}, {end.year}"
    if start.month != end.month:
        return f"{start:%B} {start.day} – {end:%B} {end.day}, {end.year}"
    return f"{start:%B} {start.day}–{end.day}, {end.year}"


def get_json(url: str, params: dict, tries: int = 3):
    full = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, http.client.HTTPException, OSError, json.JSONDecodeError, ValueError):
            if attempt == tries - 1:
                raise
            time.sleep(4 * (attempt + 1))  # loc.gov answers bursts with HTML/429; back off
    raise AssertionError("unreachable")


def search(term: str, start: date, end: date) -> list[dict]:
    params = {
        "q": term, "dates": f"{start.isoformat()}/{end.isoformat()}", "fa": f"partof_title:{STAR}",
        "fo": "json", "c": PAGES_PER_TERM, "at": "results,pagination",
    }
    data = get_json(LOC_SEARCH, params)
    time.sleep(2)
    results = data.get("results", [])
    if not results and (data.get("pagination") or {}).get("of"):
        time.sleep(5)  # loc.gov sometimes returns an empty page under load; ask once more
        results = get_json(LOC_SEARCH, params).get("results", [])
    return results


def page_text(result: dict) -> str:
    wc = result.get("word_coordinates_url") or ""
    seg = urllib.parse.parse_qs(urllib.parse.urlparse(wc).query).get("segment", [""])[0]
    if not seg:
        return ""
    data = get_json(LOC_TEXT, {"segment": seg, "format": "alto_xml", "full_text": 1})
    time.sleep(1.2)
    for v in data.values():
        if isinstance(v, dict):
            return v.get("full_text", "") or ""
    return ""


def clean(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)  # rejoin hyphenated line breaks
    text = re.sub(r"_{1,}", " ", text)
    text = text.replace("�", "").replace("­", "")
    text = re.sub(r"[^\x20-\x7E‘-”\n]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def legibility(s: str) -> float:
    """1.0 for clean prose; each garbled token costs double, so OCR soup drops fast."""
    toks = s.split()
    bad = 0
    for t in toks:
        core = t.strip(".,;:!?'\"()“”").lower()
        if not WORD.match(t) and t not in ("…", "&"):
            bad += 1
        elif core.isalpha() and len(core) <= 2 and core not in SHORT_OK:
            bad += 1
    return 1 - 2 * bad / max(1, len(toks))


def _is_break(s: str, i: int) -> bool:
    prev = re.search(r"([A-Za-z.]+)$", s[:i])
    return not (prev and (prev.group(1).lower().strip(".") in ABBREV or len(prev.group(1)) == 1))


def sentence_end(s: str, start: int) -> int:
    for m in re.finditer(r"[.?!]\s+(?=[A-Z\"“])", s[start:]):
        if _is_break(s, start + m.start()):
            return start + m.start()
    return -1


def sentence_start(s: str, k: int) -> int:
    best = -1
    for m in re.finditer(r"[.?!]\s+(?=[A-Z\"“])", s[:k]):
        if _is_break(s, m.start()):
            best = m.end()
    return best


def snippets(text: str, pattern: str) -> list[tuple[str, float]]:
    """1-3 sentences around each mention, with a legibility score."""
    out = []
    for m in re.finditer(pattern, text, re.I):
        lo, hi = max(0, m.start() - 240), min(len(text), m.end() + 240)
        window, k = text[lo:hi], m.start() - lo
        left = sentence_start(window, k)
        if left != -1 and k - left < 220:
            window, k = window[left:], k - left
        else:
            sp = window.find(" ", max(0, k - 160))
            if 0 <= sp < k:
                window, k = "… " + window[sp + 1:], k - sp + 1
        right = sentence_end(window, k + 10)
        if right != -1 and right - k < 240:
            window = window[:right + 1]
        elif len(window) > k + 200:
            window = window[:window.rfind(" ", 0, k + 200)] + " …"
        out.append((window.strip(), legibility(window)))
    return out


def build_archive(slug: str, now: float) -> dict:
    cfg = ARCHIVE.get(slug)
    start, end = week_100_years_ago(now)
    base_note = (
        "Clips are machine-read text (OCR) from scanned Evening Star pages on the Library of Congress's "
        "Chronicling America, lightly cleaned (line-break hyphens rejoined, stray symbols removed); misspellings "
        "are the scanner's. Newspapers this old are public domain. Each clip links to its page at loc.gov. "
        "Clips that mention race, covenants, deed restrictions or slurs are skipped automatically "
        f"(keyword list: {', '.join(SCREEN_TERMS[:21])}, plus a list of slurs), because they need an editor's context; "
        "legal notices and lists of private individuals are skipped too."
    )
    section = {
        "week_label": week_label(start, end),
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "paper": "Evening Star",
        "terms": cfg["terms"] if cfg else [],
        "clips": [],
        "screened": 0,
        "note": base_note,
    }
    if not cfg:
        section["note"] = f"No archive search terms are configured for this neighborhood yet. {base_note}"
        return section

    t0 = time.time()
    results, seen = [], set()
    try:
        for term in cfg["terms"]:
            for r in search(term, start, end):
                if r.get("id") and r["id"] not in seen:
                    seen.add(r["id"])
                    results.append(r)
    except Exception as exc:  # noqa: BLE001 - the archive is optional; never fail the section
        section["note"] = f"The Library of Congress search could not be reached this run ({type(exc).__name__}). {base_note}"
        return section

    items, seen_text, screened, fetched, unread = [], set(), 0, 0, 0
    for r in results:
        if fetched >= MAX_PAGE_FETCHES or time.time() - t0 > ARCHIVE_BUDGET_S:
            break
        try:
            text = clean(page_text(r))
        except Exception:  # noqa: BLE001 - skip a page whose text will not load
            unread += 1
            continue
        fetched += 1
        for snip, score in snippets(text, cfg["pattern"]):
            if score < 0.7 or len(snip) < 50 or len(snip) > 700:
                continue
            if len(NAME_LIST.findall(snip)) >= 3 or LEGAL.search(snip) or OWNER_NOTICE.search(snip):
                continue
            if cfg.get("reject") and re.search(cfg["reject"], snip, re.I):  # e.g. 1926 college football, other states
                continue
            if SCREEN.search(snip):
                screened += 1
                continue
            key = re.sub(r"[^a-z]", "", snip.lower())[:60]
            if key in seen_text:
                continue
            seen_text.add(key)
            local = 0.3 if re.search(cfg["local"], snip, re.I) else 0.0
            page_m = re.search(r"[?&]sp=(\d+)", r.get("id") or "") or re.match(r"0*(\d+)", str(r.get("shelf_id") or ""))
            url = (r.get("id") or r.get("url") or "").replace("http://", "https://", 1)
            items.append({
                "date": r.get("date"), "page": int(page_m.group(1)) if page_m else None,
                "text": snip, "url": url, "_rank": score + local, "_res": r["id"],
            })

    # Best per page, then prefer different days; shown in date order.
    items.sort(key=lambda i: -i["_rank"])
    picked, pages, days = [], set(), set()
    for pass_ in (0, 1):
        for i in items:
            if len(picked) >= MAX_CLIPS or i in picked or i["_res"] in pages:
                continue
            if pass_ == 0 and i["date"] in days:
                continue
            picked.append(i)
            pages.add(i["_res"])
            days.add(i["date"])
    picked.sort(key=lambda i: (i["date"] or "", i["page"] or 0))
    section["clips"] = [{k: i[k] for k in ("date", "page", "text", "url")} for i in picked]
    section["screened"] = screened
    if screened:
        section["note"] += f" This week {screened} otherwise usable clip{'s were' if screened != 1 else ' was'} held back by that screen."
    if not picked and unread:  # pages we couldn't read prove nothing, so don't call it a quiet week
        section["note"] = f"The Library of Congress search could not be reached this run ({unread} pages would not load). {base_note}"
        return section
    if not picked:
        section["note"] = (
            f"No usable mentions in the Evening Star for {section['week_label']} "
            f"({len(results)} matching page{'s' if len(results) != 1 else ''} searched). "
            "Some weeks a neighborhood just isn't in the paper. " + section["note"]
        )
    return section


# loc.gov refuses requests from GitHub's cloud runners (every search fails there, while the same request from a home
# connection succeeds), so the weekly clips are fetched ahead of time with ingest/prefetch_archive.py and committed
# here, one file per week and neighborhood. The nightly run uses the cached week when it exists and only then tries
# loc.gov live.
ARCHIVE_CACHE = Path(__file__).resolve().parent / "archive_cache"


def cached_archive(slug: str, now: float) -> dict | None:
    start, _ = week_100_years_ago(now)
    path = ARCHIVE_CACHE / start.isoformat() / f"{slug}.json"
    cfg = ARCHIVE.get(slug)
    try:
        section = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # A cache from older search terms is stale; fetch again rather than show clips the current rules wouldn't pick.
    return section if cfg and section.get("terms") == cfg["terms"] else None


# ---------------------------------------------------------------- module interface

def build(geom: dict, hood: dict, now: float) -> dict:
    return {
        "generated_at": iso(int(now * 1000)),
        "sources": [
            {"name": "DC Historic Preservation Office, Historic Data on DC Buildings (HistoryQuest), CC BY 4.0", "url": HISTORIC_PAGE},
            {"name": "Evening Star (Washington, D.C.), Chronicling America, Library of Congress; public domain", "url": STAR_ITEM},
        ],
        "buildings": build_buildings(geom),
        "archive": cached_archive(hood["slug"], now) or build_archive(hood["slug"], now),
    }


def check(section: dict) -> list[str]:
    errors = []
    for key in ("generated_at", "sources", "buildings", "archive"):
        if key not in section:
            errors.append(f"history: missing {key}")
    if errors:
        return errors
    b = section["buildings"]
    if not b.get("records"):
        errors.append("history: buildings.records is 0")
    if not b.get("by_decade"):
        errors.append("history: buildings.by_decade is empty")
    fb = b.get("featured_block")
    if not fb:
        errors.append("history: featured_block missing")
    else:
        for k in ("block", "year", "buildings", "permits", "builder", "architects", "largest_permit", "sentence"):
            if fb.get(k) in (None, ""):
                errors.append(f"history: featured_block.{k} missing")
        if fb.get("largest_permit", {}).get("buildings", 0) > fb.get("buildings", 0):
            errors.append("history: largest permit covers more buildings than the block")
    if not b.get("top_architects") or not b.get("top_builders"):
        errors.append("history: top architects/builders empty")
    a = section["archive"]
    for k in ("week_label", "paper", "terms", "clips", "note"):
        if k not in a:
            errors.append(f"history: archive.{k} missing")
    for c in a.get("clips", []):
        if not (c.get("url", "").startswith("https://www.loc.gov/") and c.get("text") and c.get("date")):
            errors.append(f"history: bad clip {c.get('url')}")
        if SCREEN.search(c.get("text", "")):
            errors.append(f"history: clip failed screening {c.get('url')}")
    if len(a.get("clips", [])) > MAX_CLIPS:
        errors.append("history: too many clips")
    errors += [f"history: forbidden field {h}" for h in find_forbidden(section)]
    return errors


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    slug = sys.argv[1] if len(sys.argv) > 1 else "petworth"
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    hood = next((h for h in config["neighborhoods"] if h["slug"] == slug), None)
    if not hood:
        print(f"unknown neighborhood {slug!r}", file=sys.stderr)
        return 2
    now = time.time()
    t0 = time.time()
    geom = dcdata.hood_boundary(config, hood)
    section = build(geom, hood, now)
    out_dir = ROOT / "ingest" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"history-{slug}.json").write_text(json.dumps(section, indent=1, ensure_ascii=False), encoding="utf-8")
    b, a = section["buildings"], section["archive"]
    fb = b["featured_block"] or {}
    print(f"{slug}: {b['records']} HistoryQuest records, {b['year_min']}-{b['year_max']}, {len(b['by_decade'])} decades")
    print(f"  featured: {fb.get('sentence')}")
    print(f"  archive {a['week_label']}: {len(a['clips'])} clips, {a.get('screened', 0)} screened out ({time.time() - t0:.0f}s)")
    errors = check(section)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("history ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
