# Sources for Chinatown, L'Enfant Plaza, NoMa, Shaw, U Street and Logan Circle (DC)

Tested 2026-11-01. Every fetch used the user agent `dc-neighborhoods-ingest/0.1 (+https://petworth.org)`. robots.txt was checked with the engine's own wildcard-aware matcher (`news.allowed`, agent `dc-neighborhoods-ingest`) on the exact URL, query string included. "403 to our UA" means the server refused our agent; no other agent was tried. Hit counts are run over the newest ≤20 items and are given as **body / summary / title**: "body" includes `content:encoded`, "summary" is title + description + categories (what `match` mode sees in `news.parse_feed(body=False)`), "title" is the headline alone. Regexes are in §0.2. Each host was fetched once per URL, with at least 2 s between requests to the same host (Hill Rag's 20 s and MVT's 10 s crawl delays were honoured: one request each).

Slugs used below (not yet in `neighborhoods.json`): `chinatown`, `lenfantplaza`, `noma`, `shaw`, `ustreet`, `logancircle`.

## 0. Cross-cutting findings

### 0.1 Geography (DC GIS: HPN `Health_WebMercator/MapServer/13`, SMD-2023 `Administrative_Other_Boundaries_WebMercator/MapServer/55`, BID `Business_Betterment_Areas_WebMercator/MapServer/15`, Main Streets `…/MapServer/16`, address points `Location_WebMercator/MapServer/0` with `FULLADDRESS` spelled out, e.g. `620 T STREET NW`). Shares are from a 60×60 or 70×70 grid sample.

| Site | Boundary (as given by the lead) | ~km² | SMDs by area | HPNs / BIDs by area |
|---|---|---|---|---|
| Chinatown | HPN `CHINATOWN` | 3.1 | 2C01 19%, 6E08 19%, 2C03 12%, 2C02 10%, 6E07 9%, 2C04 6%, 6E03 6%, 2G06 5%, 2G05 3%, 6E01 3%, 6E04 2% → **ANC 2C ~47%, 6E ~39%, 2G ~8%** | Holds 83% of the Downtown BID and **100% of the Mount Vernon Triangle CID**. |
| L'Enfant Plaza | `Southwest BID` | 1.9 | 6D01 37%, 6D02 34%, 6D05 11%, 6D04 7%, 6D03 6%, 2A01 4% → **ANC 6D ~96%** | HPN SW/WATERFRONT 96%, NATIONAL MALL 4% |
| NoMa | `NoMa BID` | 0.95 | 6E07 33%, 5F06 14%, 6E06 12%, 5F07 12%, 6C07 11%, 6E05 11%, 6C06 3%, 6E04 3% → **ANC 6E ~59%, 5F ~26%, 6C ~14%** | HPN UNION STATION 70%, EDGEWOOD 14%, **CHINATOWN 12%**, BLOOMINGDALE 4% |
| Shaw | ANC 6E (`SMD_ID LIKE '6E%'`) | 1.7 | 6E01–6E09 | **HPN CHINATOWN 74%, UNION STATION 25%**; Downtown BID 38%, **NoMa BID 32%**, MVT CID 15% |
| U Street | HPN `U ST/PLEASANT` | 2.2 | 1E05 29%, 1B01 13%, 1E07 10%, 1B02 10%, 1B08 8%, 1E06 6%, 1B04 6%, 1B03 5%, 2F01 3%, 1B05 3%, 2B09 3%, 1B07 2% → **ANC 1B ~47%, 1E ~45%**, 2F/2B ~6% | U Street Main Street polygon is 83% this HPN, 17% ADAMS MORGAN. |
| Logan Circle | ANC 2F (`SMD_ID LIKE '2F%'`, 2F01–2F08) | 0.77 | 2F01–2F08 | HPN LOGAN CIRCLE/SHAW 91%, U ST/PLEASANT 9% (2F01). Logan Circle Main Street polygon: 2F 95%, 1B08 5%. |

**Shaw = ANC 6E does not contain Shaw.** This is the most important finding here; please check it with the lead before building the Shaw site.
- ANC 6E is Mount Vernon Triangle, Judiciary Square/east Penn Quarter, Northwest One and the west half of NoMa. 74% of it is in the CHINATOWN HPN and 25% in UNION STATION. Its commissioners' addresses (e.g. 400 Massachusetts Ave NW, SMD 6E09) are in MVT.
- Every historic-Shaw landmark I geocoded falls **outside** 6E:
  - 1630 7th St NW → 2G01
  - 1400 7th St NW (O Street Market / Giant) → 2G02
  - 1535 7th St NW → 2G03
  - 1250 9th St NW (Blagden Alley) → 2G04
  - 1317 9th St NW → 2G05
  - 620 T St NW (Howard Theatre) → 1B02
  - 641 S St NW (Children's National "Shaw Metro") → 1B02
- Historic Shaw is **ANC 2G** (2G01–2G06; 1.1 km²; HPN LOGAN CIRCLE/SHAW 72%, CHINATOWN 28%), plus the Shaw–Howard Metro blocks in **1B02**.
- **Recommendation:** `SMD_ID LIKE '2G%' OR SMD_ID = '1B02'`. Caveat: 1B02 also reaches into the U ST/PLEASANT HPN, which takes in the African American Civil War Museum at 1925 Vermont Ave, so that SMD would overlap the U Street site.
- If 6E is kept, the Shaw site is mostly a second Chinatown/MVT site and half of a NoMa site. The overlaps below quantify that.

**Overlaps between these sites (and with live ones).**
- **Chinatown ∩ NoMa:** 12% of the NoMa BID, the blocks just west of North Capitol, is in the CHINATOWN HPN. It includes the GPO at 732 North Capitol St NW (6E07).
- **Chinatown ∩ Shaw-as-6E:** 6E is 39% of the Chinatown HPN.
- **NoMa ∩ Shaw-as-6E:** 6E is 59% of the BID.
- **Logan ∩ U Street:** 2F01 (14th & U south side, e.g. 1914 14th St NW, 1400 U St NW) is in both.
- **U Street ∩ Columbia Heights:** they share no ground, but the U ST HPN is 45% ANC 1E, whose feed (`anc1e.org/feed/`) the Columbia Heights site already reads.
- **U Street ∩ Dupont/Adams Morgan:** the 1500 block of U (2B09) is in the U ST HPN, while 1600 U St (2B08) is ADAMS MORGAN.
- **NoMa and H Street:** Union Station (50 Massachusetts Ave NE) is in **6C04**, so it belongs to the live H Street site, not NoMa.
- **Outside the NoMa BID:** Union Market (1309 5th St NE) is SMD 5D01, HPN TRINIDAD. 1100 4th St NE and Gonzaga (19 I St NW) are also outside.

**Inside / outside checks (address points):**
- **Chinatown HPN:**
  - In: Capital One Arena 601 F St NW (2C01), MLK Library 901 G St NW (2C01), Woolly Mammoth 641 D St NW (2C03), Ford's Theatre 511 10th St NW (2C03), National Building Museum 401 F St NW (6E08), sweetgreen 601 Massachusetts Ave NW (6E01), TJX/Marshalls 601 13th St NW (2C01), 1000 H St NW (2C01), 1301 7th St NW (2G05).
  - Old Chinatown (Pennsylvania Ave and 4½ St, before 1931) is now Federal Triangle, in the NATIONAL MALL HPN. That matters for history (§7).
- **Southwest BID:**
  - The BID is really **all of Southwest north of M St**: the L'Enfant federal area (1000 Independence Ave SW, 300/400 7th St SW, 550 C St SW, 500 E St SW, 700 Delaware Ave SW) plus residential SW and the Wharf.
  - In: Wharf 760 and 800 Maine Ave SW and 600 Water St SW, Arena Stage 1101 6th St SW (6D03), Southwest Library 900 Wesley Pl SW (6D05), Waterfront Station 1100/1101 4th St SW (6D04).
  - **Out:** 1100 Maine Ave SW (the Maine Avenue Fish Market's block, 6D01) and 1250 4th St SW (6D07). So "L'Enfant Plaza" as a name is far narrower than the boundary; the site will mostly carry Southwest/Wharf news.
- **NoMa BID:** NPR 1111 North Capitol St NE (6E06), CNN 820 1st St NE (6E07), REI/Uline Arena 201 M St NE (6C07), 1100–1300 1st St NE, 1500 Harry Thomas Way NE (5F06).
- **U ST HPN:**
  - In: Howard University campus 2400 6th St NW (1E05), Howard University Hospital 2041 Georgia Ave NW (1B01), Banneker Rec 2500 Georgia Ave NW (1E06), Lincoln Theatre 1215 U St NW (1B08), 9:30 Club 815 V St NW (1B04), Reeves Center 2000 14th St NW (1B07), AACWM 1925 Vermont Ave NW (1B02), 1816 12th St NW (Anthony Bowen YMCA, 1B08).
  - Out: **Howard Theatre** (620 T St NW, LOGAN CIRCLE/SHAW HPN).
- **ANC 2F:**
  - In: Logan Circle itself (1 Logan Cir NW, 2F04), 1333 and 1400 14th St NW, 1425 N St NW, 1427/1440 P St NW (Whole Foods P St), 1500 Rhode Island Ave NW, 1301 Vermont Ave NW.
  - Out: 1530 P St NW (2B04, Dupont) and 1630 R St NW (2B03).

### 0.2 Keyword rules (Python `re`; drop-in for `TERMS` / `NOT_HERE` in news.py)

Rules marked "case-sensitive" must not get `re.I`; they use scoped `(?i:…)` groups (Python ≥3.11) where case doesn't matter.

**Chinatown**:
```python
"chinatown": re.compile(
    r"\bchinatown\b|\bfriendship\s+arch(way)?\b|\bgallery\s+place\b|\b(near|outside|around|behind|by)\s+(the\s+)?capital\s+one\s+arena\b|"
    r"\bpenn\s+quarter\b|\bmartin\s+luther\s+king\s+jr\.?\s+memorial\s+library\b|\bMLK\s+(memorial\s+)?library\b|"
    r"\bsmithsonian\s+american\s+art\s+museum\b|\bnational\s+portrait\s+gallery\b|\bcapital\s+jewish\s+museum\b|\bnational\s+building\s+museum\b|"
    r"\bford['\u2019]?s\s+theat(re|er)\b|\bjudiciary\s+square\b|\bmount\s+vernon\s+(triangle|square)\b|"
    r"\bwalter\s+e\.?\s+washington\s+convention\s+center\b|\bANC\s*2C\b|"
    r"\b[4-9]\d\d\s+[HIGF]\s+st(reet)?\.?,?\s+n\.?w\b|\b[6-9]\d\d\s+7th\s+st(reet)?\.?,?\s+n\.?w\b", re.I | re.S),
```
```python
OTHER_CT = (r"(new\s+york|NYC|manhattan|flushing|san\s+francisco|boston|philadelphia|philly|chicago|oakland|los\s+angeles|seattle|portland|"
            r"toronto|vancouver|london|montreal|honolulu|houston|las\s+vegas|bangkok|singapore|kuala\s+lumpur|sydney|melbourne|liverpool|"
            r"manchester|yokohama|havana|lima|paris)")
"chinatown": (re.compile(OTHER_CT + r"(['\u2019]s)?\s+chinatown\b|\bchinatown,?\s+" + OTHER_CT + r"\b|\bchinatown\s+(in|of)\s+" + OTHER_CT, re.I),
              re.compile(r"\b(washington|d\.?c\.?)(['\u2019]s)?\s+chinatown\b|\bchinatown\s+(d\.?c|park|community\s+cultural|service\s+center|coalition)\b|"
                         r"\bfriendship\s+arch|\bgallery\s+place\b|\bpenn\s+quarter\b|\bANC\s*2C\b|\b[4-9]\d\d\s+[HIGF]\s+st(reet)?\.?,?\s+n\.?w\b", re.I)),
```
Notes:
- **Capital One Arena** only counts as "near/outside/around … Capital One Arena". On `wtop.com/tag/capital-one-arena/feed/` the bare name hit 7/10 items in bodies, all concert and game roundups. With the prefix form only "DC police identify, charge man shot by officer near Capital One Arena" survives.
- The 1st version of the reject list also rejected on sports words (Wizards, Capitals). That wrongly dropped "Fuddruckers makes its Chinatown return…" (WTOP), so sports words are gone. Reject only on other cities' Chinatowns, and rescue with a DC cue.
- **Penn Quarter, Mount Vernon Square/Triangle, Judiciary Square and the convention center are inside this HPN.**
  - MVT CID news therefore belongs here.
  - If the lead keeps Shaw = 6E, the same items also belong to Shaw.
- Museum names (NPG, SAAM, Capital Jewish Museum) mostly hit "things to do" roundups, and only in bodies. With `match` (summary) mode they rarely fire.
- Tested today:
  - WTOP chinatown tag: 10/10/7 kept, 0 wrong.
  - Washingtonian `?s=chinatown`: 10 body / 3 summary / 0 title. The 10 body hits are roundups; summary mode keeps "Why a Vegetarian Taco Shop Is Now Adding Chicken" (Chinatown) and "What to Eat and Drink Inside Capital One Arena".
  - No other-city Chinatown appeared in today's items. The reject list is defensive (wire and Blade travel copy).

**L'Enfant Plaza (Southwest BID)**:
```python
"lenfantplaza": re.compile(
    r"\bl['\u2019]?\s?enfant\s+(plaza|promenade)\b|\bbanneker\s+(park|overlook)\b|\b10th\s+st(reet)?\.?\s+overlook\b|\bspy\s+museum\b|"
    r"\bsouthwest\s+(bid|business\s+improvement|ecodistrict|waterfront|duck\s*pond|neighborhood\s+library|library)\b|\bSWBID\b|"
    r"\bwaterfront\s+station\b|\bANC\s*6D\b|\barena\s+stage\b|\bfedlandia\b|\bamidon[-\s]bowen\b|\brandall\s+rec|"
    r"\b\d{2,4}\s+([4-9]|1[0-4])(th|st|nd|rd)\s+st(reet)?\.?,?\s+s\.?w\b|\b\d{2,4}\s+[CDEGIM]\s+st(reet)?\.?,?\s+s\.?w\b|"
    r"\b(in\s+)?(southwest|SW)\s+(dc|d\.c\.)\b|\bwharf\s+(dc|d\.c\.)\b|\bthe\s+wharf\b(?=.{0,200}\b(d\.?c|SW|southwest|maine\s+ave)\b)", re.I | re.S),
"lenfantplaza": (re.compile(r"fisherman['\u2019]?s\s+wharf|\bsouthwest\s+airlines\b|"
                            r"\bwharf\b.{0,60}\b(alexandria|baltimore|san\s+francisco|boston|national\s+harbor)\b", re.I),
                 re.compile(r"\bl['\u2019]?\s?enfant\s+plaza|\bSWBID\b|\bANC\s*6D\b|\bmaine\s+ave|\bsouthwest\s+waterfront", re.I)),
```
Notes:
- **Never match bare "L'Enfant".** It is the planner, "the L'Enfant Plan", and L'Enfant Circle in other cities. Only "L'Enfant Plaza" and "L'Enfant Promenade" count, and both are inside the BID.
- Many "L'Enfant Plaza" hits are Metro service stories that list the station among others (WTOP's lenfant-plaza tag, 7 of 10 in summary only). Prefer **title-only** for that tag.
- "Southwest DC" also covers Buzzard Point and Fort McNair (6D07/6D08, outside the BID). That leak is accepted, since local copy rarely names them separately.
- "Maine Avenue Fish Market" is left out on purpose: its block (1100 Maine Ave SW) is just outside the BID.
- "The Wharf" needs a DC cue within 200 characters.
- Tested today:
  - `wtop.com/tag/the-wharf/feed/` 8/6/1: "The Wharf, one of DC's biggest-ever developments, has been sold", "6 people arrested after large group of teens descend on DC's Wharf".
  - `wtop.com/tag/southwest-dc/feed/` 9/9/4: "'Fedlandia': New neighborhood could take shape in DC amid sale of federal buildings", "3 arrested in Southwest DC shooting…".
  - An earlier draft rejected "JINYA opens another DC ramen bar… at The Wharf" because "Georgetown" appeared near "wharf". Georgetown was then removed from the reject list.

**NoMa**: **case-sensitive** (no `re.I`), so "Noma" (the Copenhagen restaurant), "NOMA" (National Organization of Minority Architects) and "NoMad" (Manhattan) never match.
```python
"noma": re.compile(r"\bNoMa\b|\b(?i:noma[-\s]gallaudet)\b|\bNoMa\s+BID\b|"
                   r"(?i:\balethia\s+tanner\s+park\b|\bswampoodle\b|\bmamie\s+.{0,2}peanut.{0,2}\s+johnson\s+plaza\b|\buline\s+arena\b|\bharry\s+thomas\s+(way|rec))"),
"noma": (re.compile(r"\bNoMad\b|(?i:\bcopenhagen\b|\bren[e\u00e9]\s+redzepi\b)"),
         re.compile(r"(?i:\bnoma[-\s]gallaudet\b|\bNoMa\s+BID\b|\bunion\s+(market|station)\b|\bnortheast\s+(dc|d\.c\.)\b)")),
```
Notes:
- **Union Market and the Metropolitan Branch Trail were in the 1st draft and are removed.**
  - Union Market is outside the BID (5D01, TRINIDAD), and in roundups it hit 9 body items in today's Washingtonian/Blade feeds, none about NoMa.
  - The MBT runs to Silver Spring.
  - Keep "Union Market" as a "nearby" booster only.
- "Mamie 'Peanut' Johnson Plaza" (the renamed Dave Thomas Circle) sits on the BID's north edge.
- Tested today:
  - `wtop.com/tag/noma/feed/` 9/5/4: "NoMa farmers market is moving — and getting bigger", "DC residents vote on new name for Dave Thomas Circle in NoMa". Two body hits are curfew-zone and beer-trail lists that name NoMa among others.
  - The DC Line `?s=noma` 8/8/4.
  - PoPville p3 3/3/1: "Now in NoMa – 'CURVE, a 12 foot tall sculpture…'".

**Shaw (written for historic Shaw: ANC 2G + 1B02; see §0.1)**: **case-sensitive** on "Shaw" (the surname is far more common than the neighborhood).
```python
"shaw": re.compile(
    r"\b(?i:in|of|around|across|near|to|from|historic|north|eastern|western|downtown)\s+Shaw\b(?![\s,]+(AFB|[Aa]ir\s+[Ff]orce|University))|"
    r"\bShaw\s+(?i:neighborhood|main\s+streets?|library|dc|d\.c\.|metro|community\s+center|residents?|rowhouse)\b|"
    r"\bShaw[-/\u2013]Howard\b|\bShaw['\u2019]s\s+(?i:7th|9th|main|historic|neighborhood|restaurant\s+scene)|"
    r"\b(?i:blagden\s+alley|naylor\s+court|howard\s+theat(re|er)|watha\s+t\.?\s+daniel|kennedy\s+rec(reation)?\s+center|o\s+street\s+market|ANC\s*2G)\b|"
    r"\b(?i:1[1-9]\d\d\s+(7th|9th|seventh|ninth)\s+st(reet)?\.?,?\s+n\.?w|walter\s+e\.?\s+washington\s+convention\s+center)\b"),
"shaw": (re.compile(r"\b(George\s+Bernard|Bernard|Artie|Robert\s+Gould|Irwin|Brian|Tony|Tim|Sandy|Carla|Ella|Craig|Mark|Lee|Hank|Patty)\s+Shaw\b|"
                    r"\bShaw\s+(AFB|Air\s+Force\s+Base|University|Festival|Industries|Communications)\b|\bShaw['\u2019]s\s+(supermarket|grocery)|\bFort\s+Shaw\b"),
         re.compile(r"\b(?i:in|of|historic)\s+Shaw\b(?=.*\b(?i:d\.?c|washington|NW|7th|9th|howard)\b)|\bShaw\s+(?i:neighborhood|main\s+streets?|library|metro)\b|"
                    r"\bShaw[-/\u2013]Howard\b|(?i:\bblagden\s+alley\b|\bANC\s*2G\b)")),
```
Notes:
- Addresses are limited to the **1100–1999** blocks of 7th and 9th St NW. In the 1st draft, "450 7th St NW" (Woolly Mammoth), "781 7th St NW" (Fuddruckers) and "829 Seventh St NW" (Hill Rag) matched; those are Chinatown.
- **Separating Shaw from Logan Circle:** Shaw takes 7th/9th St, Blagden/Naylor, Howard Theatre, O Street Market and the convention center. Logan takes Logan Circle, 14th St NW 1000–1699, P St NW, Studio Theatre and the 13th–15th & P–R intersections.
  - The two term lists don't overlap.
  - "Logan Circle/Shaw" (the HPN name, and an old ANC 2F/2C label) hits both, which is correct.
- **Overlap with U Street:** "Shaw/U Street" items match both (PoPville: "Down Goes Dragon Hero in Shaw/U Street near 9:30 Club…"), which is correct. Howard Theatre is a Shaw term only.
- **If the lead keeps Shaw = ANC 6E**, add `\bmount\s+vernon\s+(triangle|square)\b|\bMVT\b|\bANC\s*6E\b|\bnorthwest\s+one\b|\bsursum\s+corda\b|\bjudiciary\s+square\b` and expect the site to duplicate the Chinatown and NoMa feeds.
- Tested today:
  - `wtop.com/tag/shaw/feed/` 9/4/1. The body hits come from "…in the Shaw neighborhood" in story bodies; WTOP tags Shaw stories reliably.
  - Washingtonian `?s=shaw`: 4 body / 0 / 0, all roundup addresses ("1250 Ninth St., NW"). That search is mostly people named Shaw; low value.
  - No surname false positive got through the reject list.

**U Street**:
```python
"ustreet": re.compile(
    r"\bU\s+st(reet)?\b(?!\.?\s*,?\s*(s\.?e|n\.?e|southeast|northeast)\b)|\bben['\u2019]?s\s+chili\s+bowl\b|"
    r"\blincoln\s+theat(re|er)\b(?=.*\b(d\.?c|washington|u\s+st)\b)|\b9:30\s+club\b|\bblack\s+broadway\b|"
    r"\bafrican\s+american\s+civil\s+war\s+(memorial|museum)\b|\btrue\s+reformer\b|\breeves\s+center\b|\bANC\s*1B\b|\bLeDroit\s+park\b|"
    r"\b1[0-6]th\s+(and|&)\s+U\b|\bpleasant\s+plains\b|\bhoward\s+university\s+hospital\b|\bbanneker\s+(rec(reation)?\s+center|pool)\b|"
    r"\bhoward\s+(university|u\.)\b(?=.{0,300}\b(campus|neighbors?|georgia\s+ave|homecoming|yardfest|U\s+street|residents)\b)", re.I | re.S),
"ustreet": (re.compile(r"\bU\s+st(reet)?\.?\s*,?\s*(s\.?e|southeast)\b|\blincoln\s+theat(re|er)\b(?=.*\b(nebraska|columbus|marion|napa|decatur)\b)", re.I),
            re.compile(r"\bU\s+st(reet)?\.?\s*,?\s*(n\.?w|northwest|corridor)\b|\b1[0-6]th\s+(and|&)\s+U\b|\bben['\u2019]?s\s+chili\s+bowl\b|\bANC\s*1B\b", re.I)),
```
Notes:
- **"U Street" vs U St SE:** U St SE in Anacostia (e.g. 1301 U St SE, already in SOURCES-EAST) is rejected by the lookahead and the reject list.
- **"U St" vs "U.S.":** "U.S." never matches, because "U Street" needs a word after "U".
- **Howard University is inside this HPN** (campus 1E05, hospital 1B01), but most Howard news is national or sports. It counts only with a neighborhood cue within 300 characters.
  - On `wtop.com/tag/howard-university/feed/` that gives 7/4/3, keeping the homecoming-shooting and road-closure stories and dropping "Philanthropist MacKenzie Scott gives historic donation…".
- **9:30 Club and Lincoln Theatre** fire in concert roundups, in bodies only; in `match` mode they rarely fire.
- Tested today:
  - `wtop.com/tag/u-street/feed/` 10/10/5 and `…/u-street-corridor/feed/` 10/10/6: "Why it's about to get more expensive to park along DC's popular U Street corridor".
  - PoPville p1–3 6/5/2: "Lil Sto (Fashion) opening soon on U Street", "'Old Banneker High School Trees All Gone'" (Pleasant Plains).
  - Washington Blade `?s=logan+circle`: U Street hit 8 bodies but only 1 summary. The body hits look like a recurring byline/boilerplate paragraph on opinion pieces (not verified line by line). **Use summary mode for the Blade.**

**Logan Circle (ANC 2F)**:
```python
"logancircle": re.compile(
    r"\blogan\s+circle\b|\bP\s+st(reet)?\.?\s+(n\.?w\b|whole\s+foods)|\bstudio\s+theat(re|er)\b|\bmary\s+mcleod\s+bethune\s+council\s+house\b|"
    r"\bmetropolitan\s+A\.?M\.?E\b|\bANC\s*2F\b|\bLCCA\b|\b1[3-5]th\s+(and|&)\s+[P-R]\b|\b1[0-6]\d\d\s+14th\s+st(reet)?\.?,?\s+n\.?w\b|"
    r"\b14th\s+st(reet)?\s+corridor\b|\bvermont\s+ave(nue)?\.?\s+n\.?w\b.{0,40}\blogan", re.I | re.S),
"logancircle": (re.compile(r"\blogan\s+circle,?\s+(indianapolis|indiana|philadelphia|IN|PA)\b|\blogan\s+square\b", re.I),
                re.compile(r"\bANC\s*2F\b|\b(d\.?c|NW)\b|\b14th\s+st", re.I)),
```
Notes:
- "Logan Square" (Chicago, Philadelphia) and Indianapolis's Logan Circle are rejected. None appeared today.
- "P St NW" also runs through Dupont (1530 P St is 2B04). That is accepted as a small leak.
- "14th St" alone is not a term (it runs from the Mall to Colorado Ave); only the 1000–1699 address blocks and "14th Street corridor" count.
- **Overlap:** 14th & U is U Street (2F01 is in both sites), while 14th & P–R is Logan.
- Tested today:
  - `wtop.com/tag/logan-circle/feed/` 10/10/7.
  - The DC Line `?s=logan+circle` 14/14/7.
  - Washingtonian `?s=logan+circle` 9/2/2: "The Ice Cream House: A Logan Circle Landmark", "A Perfect Day in Logan Circle".
  - Washington Blade `?s=logan+circle` 10/1/0: body boilerplate again, so use summary mode.

### 0.3 General feeds already in the engine, counted for the new areas (body / summary / title)

| Feed | robots | items (dates) | CT | LE | NO | SH | US | LO |
|---|---|---|---|---|---|---|---|---|
| `https://www.popville.com/feed/` p1 / p2 / p3 | allow | 20 each (26–30 Oct) | 1/1/1, 0, 1/1/1 (both "Penn Quarter" titles) | 2/1/0, 2/2/1 ("Can we talk about the Halloween store in L'Enfant Plaza!?!"), 0 | 0, 0, 3/3/1 | 0, 1/1/1, 0 | 3/3/0, 1/1/1, 2/1/1 | 1/0/0, 0, 0 |
| `https://ggwash.org/rss` | allow | 10 (27–30 Oct) | 0 | 0 | 1/1/0 | 0 | 1/1/0 | 0 |
| `https://washingtoncitypaper.com/feed/` | allow | 10 (28–30 Oct) | 0 | 0 | 1/0/0 | 0 | 0 | 0 |
| `https://wtop.com/local/dc/feed/` | allow | 10 (30 Oct–1 Nov) | 0 | 0 | 0 | 0 | 0 | 0 |
| `https://wamu.org/feed/` | allow | 10 | 0 | 0 | 0 | 1/0/0 | 0 | 0 |
| `https://51st.news/rss/` | allow | 15 (21–29 Oct) | 5/0/0 | 1/0/0 | 2/0/0 | 1/0/0 | 2/0/0 | 1/0/0 |
| `https://thedcline.org/feed/` | allow | 20 (8–30 Oct) | 0 | 0 | 1/1/0 | 0 | 0 | 0 |
| `https://www.hillrag.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link` (Crawl-delay 20) | allow | 20 (18–31 Oct) | 1/0/0 | 0 | 0 | 0 | 0 | 0 |

The shared feeds give 0–1 summary hits per area per day; the area-specific feeds below carry the load. 51st's body hits are all in listicles ("Dinner under $15?…"), so `match` mode correctly ignores them.

---

## 1. Chinatown (HPN `CHINATOWN`; ANC 2C ~47% + 6E ~39% + 2G ~8%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/chinatown/feed/` | allow | 10 (21 Mar 2025 – 8 Jun 2026) | 10/10/7 | **Best clean source**, but slow. "Chinatown Coalition brings expanded Lunar New Year celebrations to DC", "With Chinatown development planned, group pushes DC Council to prioritize small businesses", "'It creates a buzz': Ideas about transforming DC's Gallery Place-Chinatown neighborhood". `match`. |
| `https://wtop.com/tag/penn-quarter/feed/` | allow | 10 (Apr 2023 – 28 Oct 2025) | 10/10/4 | "Private membership club HQ DC House opens in Penn Quarter", "Another downtown DC loss: Penn Quarter farmers market won't reopen". `match`. |
| **`https://www.mvtcid.org/feed/`** (Mount Vernon Triangle CID; = `mountvernontriangle.org/feed/`) | allow, **Crawl-delay: 10** | 10 (23–30 Oct 2026) | 10/10/1 | **Freshest local source.** MVT is 100% inside the HPN, so **take all**. "This November: Mount Vernon Triangle Food Drive Returns!", "RASA Introduces Salmon to Its Menu". Some posts are business promos. |
| `https://thedcline.org/?s=chinatown&feed=rss2&orderby=date&order=DESC` | allow | 20 (Feb 2022 – Oct 2025) | 10/10/7 | `search`. "District Links: Task force launches to develop ideas for Gallery Place/Chinatown…". Slow (newest Oct 2025). |
| `https://www.washingtonian.com/?s=chinatown&feed=rss2&orderby=date&order=DESC` | allow | 10 (Jun – 15 Oct 2026) | 10/3/0 | `match` (summary). Mostly roundups. |
| `https://www.downtowndc.org/feed/` (DowntownDC BID) | allow | 10 (12 Aug – 21 Oct 2026) | 3/1/0 | Biweekly newsletters ("October 21, 2026 – Downtown Has Bites, Frights, and Fall Delights") and RFPs. The BID is 83% in the HPN, but it also covers Franklin Square/K St. `match`. |
| `https://www.washingtonblade.com/?s=chinatown&feed=rss2&orderby=date&order=DESC` | allow | 10 (Apr 2023 – Oct 2026) | 10/2/0 | Body-only roundups. Optional. |
| ANC 2C `https://anc2c.dc.gov/rss.xml` | allow | 10 (13 Sep – 13 Oct 2026) | 10/10/10 | Meeting nodes only. Today 8 of 10 are **2020 meetings re-posted on 13 Sep 2026** ("January 12, 2021, ANC 2C Public Meeting"). Plus "NEW Website for ANC2C!" (the new site is anc2c.dc.gov; `anc2c.org` has no DNS). Use for events, not news. |
| `https://wtop.com/tag/mount-vernon-triangle/feed/` | allow | 7 (2016 – Oct 2024) | 7/7/2 | **Stale.** Skip. |

Not usable:
- `wtop.com/tag/capital-one-arena/feed/`: game and concert stories, with 2 body hits after the "near … arena" rule. Skip it.
- `chinatowndc.org` (no DNS); `chinatowndc.com` (TLS internal error); `ccccdc.org` (parked, for sale).
- Woolly Mammoth (`woollymammoth.net/feed/`: 6 items, newest Sep 2025, and one is titled "TEST").
- `penn-quarter.com` (no DNS).

```python
"chinatown": [
    ("Mount Vernon Triangle CID", "https://www.mvtcid.org/feed/", "https://www.mvtcid.org/", "all"),  # Crawl-delay 10
    ("WTOP", "https://wtop.com/tag/chinatown/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/penn-quarter/feed/", "https://wtop.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="chinatown"), "https://thedcline.org/", "search"),
    ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="chinatown"), "https://www.washingtonian.com/", "match"),
    ("DowntownDC BID", "https://www.downtowndc.org/feed/", "https://www.downtowndc.org/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **MVT CID** | `https://www.mvtcid.org/wp-json/tribe/events/v1/events` (Crawl-delay 10; `/events/?ical=1` also works, 8 VEVENTs) | **Yes.** 14 upcoming over 2 pages. "FRESHFARM MVT Market" (Saturdays 9:00, no venue address), "Free Public Art Tours at Walter E. Washington Convention Center" (10 Nov), "Center Stage Presents: The Serpent Queen" (17 Nov, 901 4th St NW Suite 700), "VIDA Fitness Open House" (19 Nov, 445 K St NW), "Writers of Washington Presents…" (3 Dec, D.C. Bar, 901 4th St NW). Show the market as one recurring item. **Page 2 needs `?page=2`**: mvtcid's robots only blocks `?add-to-cart=`, so it's allowed, but wait 10 s. |
| **ANC 2C** | `https://anc2c.dc.gov/rss.xml` (Drupal, OANC platform) | **Yes, but parse the event date from the body, not the title or pubDate.** Each node's description has `Date and Time Tue, Oct 20 2026, 4 - 5pm`; regex `Date and Time \w{3}, (\w{3}) (\d{1,2}) (\d{4}), ([\d:]+\s*(?:-\s*[\d:]+)?\s*[ap]m)`. Today: "October 20, 2026, ANC 2C Special Meeting 11th St Shelter" (Tue 20 Oct, 4–5 pm). The re-posted 2020 meetings give their own 2020/2021 dates; drop past dates. Bodies carry Zoom links/passcodes, so never republish body text. |
| ANC 6E | `https://anc6e.dc.gov/rss.xml` | Same Drupal pattern. See §4 (Shaw). |
| OANC (already used) | `https://oanc.dc.gov/rss.xml` | No 2C/6E items in today's window (8A, 6B, 3B, 6C only). **Caveat:** `OANC_TITLE` requires "Public Meeting", but the ANC 6E calendar titles its meetings "November 18, 2026, ANC 6E Virtual Meeting", so it would not match. Widen it to `(Special\s+)?(Public|Virtual|Regular)\s+Meeting`. |
| DowntownDC BID | `/wp-json/tribe/events/v1/events` → 404. `/wp-json/wp/v2/event` (custom type) → 200, 20 items ("Fall Festival at MLK LIbrary", "DowntownDC Holiday Market 2nd Annual Carol Sing-Along"…). | **No.** The CPT exposes only the post date; `acf` is `[]`, `meta` has no date, and there is no schema Event in `yoast_head_json`. The event date is only in the HTML. Excluded. |
| MLK Memorial Library (901 G St NW, in the HPN) | `dclibrary.libnet.info` | robots allows `/events` (it only blocks `/results*`, `/sitesearch*`), but the page has no RSS/iCal link. Keep it as a static link as for other sites: `https://dclibrary.libnet.info/events?l=Martin%20Luther%20King%20Jr.%20Memorial%20Library`. |
| Capital One Arena / Monumental | — | No feed tested that qualifies (Ticketmaster terms not reviewed). |
| Smithsonian (NPG/SAAM, 8th & F) / Capital Jewish Museum / Spy Museum | Capital Jewish Museum tribe 404; Smithsonian not tested | None verified. |

```python
ANCS["chinatown"] = ["2C", "6E", "2G"]
```

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **Monumental Sports & Entertainment** (Greenhouse) | `https://boards-api.greenhouse.io/v1/boards/monumentalsports/jobs` | 38 jobs; **25 with `location.name` = `Washington, DC 20004`**. The board's `/offices` endpoint maps 20004 to "Capital One Arena (COA)", "Capital One Arena North (COAN)" and "District E", all at 601 F St NW (2C01). Samples: "Coordinator, Content Metadata & Distribution" (updated 2026-10-30), "Safety Team Full Time" (10-27), "Junior Videographer" (10-26), "Vice President, Global Partnerships" (10-22), many "Game Night Staff: … (Part-Time/Seasonal)". **Exclude** `Fairfax, VA 22030` (EagleBank Arena), `Arlington, VA 22203` (IcePlex), and the bare `Washington, DC` / `Washington, District of Columbia, United States` rows (6+3): offices include "MedStar Health Performance Center" (20032, Congress Heights) and "The Lofts", so those can't be placed. | allow | **Use ("in").** Add `"monumentalsports"` to `GREENHOUSE` and `ZIPS["chinatown"] = ("20004",)`. 20004 is Penn Quarter/Federal Triangle and does not spill into another site's area, though Federal Triangle itself is National Mall HPN. |
| **TJX (Marshalls, 601 13th St NW)** | same Workday cxs call as Columbia Heights; keep `locationsText` `Washington, DC 20005` **and** posting text containing `601 13th St` | 1 job today: "Merchandise Associate" (startDate 2026-10-14). 601 13th St NW = 2C01, inside the HPN (it is the "downtown" store in SOURCES-EAST). | allow | **Use ("in")**, filtered by address. 20005 also covers Logan Circle/Thomas Circle. |
| **sweetgreen, 601 Massachusetts Ave NW** (Greenhouse, already probed) | `boards-api.greenhouse.io/v1/boards/sweetgreen/jobs` | 1 job: "Restaurant General Manager", `601 Massachusetts Ave NW, Washington DC 20001` (updated 2026-10-19). Address = 6E01, CHINATOWN HPN. | allow | **Use, but only by address**: `ZIPS` won't work, because 20001 also covers Shaw, NoMa and Bloomingdale. Needs a per-board address match (e.g. `ADDRESSES = {"chinatown": ("601 Massachusetts Ave NW",)}`). |
| **solidcore "Mt Vernon Square"** (Lever) | `api.lever.co/v0/postings/solidcore?mode=json`, `text` endswith `- Mt Vernon Square, DC` | "Core Crew (Front Desk & Sales) - Mt Vernon Square, DC", created 2022-09-08 | allow (Crawl-delay 1) | Evergreen pool posting; optional, no date. |
| Smithsonian (NPG/SAAM), GAO, FBI | USAJOBS | — | robots-blocked (known) | Excluded. |
| Events DC (convention center), Spy Museum, National Building Museum, Woolly, Capital Jewish Museum | Greenhouse/Lever/Ashby slugs `eventsdc`, `spymuseum`, `internationalspymuseum`, `nationalbuildingmuseum`, `woollymammoth`, `capitaljewishmuseum`, `downtowndc` → none | — | — | No verified feed. |

---

## 2. L'Enfant Plaza (Southwest BID; ANC 6D ~96%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| **`https://thesouthwester.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link`** (The Southwester, SW's community paper) | allow | 20 (30 Sep – 8 Oct 2026) | 12/2/2 | **Best SW source; take all.** It posts each monthly issue in a batch: "Local Candidates Step Up to Serve in ANC 6D Elections", "Southwest's First Cinema To Open at Revada Arts Center", "New Southwest Arts Hub to Open October 23", "HIPS in Conversation about the Needs of Southwest Residents". Its RSS **`/feed/` returns the HTML home page** (a cache plugin), so use the WP JSON. It covers all of SW, including south of M St (outside the BID); acceptable. |
| `https://www.swbid.org/feed/` (= `swbid.org/feed/`) | allow | 10 (18 Mar 2025 – 19 Aug 2026) | 10/10/2 | BID news; slow (~monthly). "Ten Years In, Southwest Is Still Setting a Place for Everyone", "The Lot at 4th and M St. SW Gets a Makeover". Take all. |
| `https://wtop.com/tag/southwest-dc/feed/` | allow | 10 (Oct 2022 – Apr 2026) | 9/9/4 | "'Fedlandia': New neighborhood could take shape…", "Boy found unconscious outside SW DC apartment building". Also used (optional) for Navy Yard; dedupe. |
| `https://wtop.com/tag/the-wharf/feed/` | allow | 10 (22 Apr – 19 Sep 2025) | 8/6/1 | "The Wharf, one of DC's biggest-ever developments, has been sold". Stale-ish (newest Sep 2025). |
| `https://wtop.com/tag/lenfant-plaza/feed/` | allow | 10 (May 2019 – Feb 2024) | 10/10/3 | **Stale** and mostly Metro service stories. Title-only if used. |
| `https://www.washingtonian.com/?s=l%27enfant+plaza&feed=rss2&orderby=date&order=DESC` | allow | 10 (Apr 2024 – Sep 2026) | 10/1/1 | Mostly body mentions (fireworks maps, news roundups). The one title: "A Disco-Themed Rooftop Sushi Omakase Restaurant Is Opening in Southwest DC". Low value. |
| `https://thedcline.org/?s=southwest+waterfront&feed=rss2&orderby=date&order=DESC` | allow | 20 (Nov 2021 – Jun 2024) | 12/12/1 | **Stale** (newest Jun 2024). Skip. |
| PoPville p1–p2 | allow | 40 | 4/3/1 | "Uh Oh, Officina at The Wharf not taking reservations after Friday", "Mi Vida on the Wharf 'closed for repairs'…". |

Not usable:
- **ANC 6D:** `anc6d.org/feed/` returns 200 but is an empty WordPress feed, and `/wp-json/wp/v2/posts` returns `[]`, as in SOURCES-EAST. `anc6d.dc.gov` has no DNS.
- **L'Enfant Plaza** (`lenfantplaza.com`): TLS handshake failure on both hosts.
- **The Wharf** (`wharfdc.com`): `/feed/` 404, `/wp-json/` 404. Events are HTML pages (`/upcoming-events/…`).
- Arena Stage `/feed/` 404. Spy Museum: tribe 404.

```python
"lenfantplaza": [
    ("The Southwester", "https://thesouthwester.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link", "https://thesouthwester.com/", "all"),  # WP JSON, not RSS
    ("Southwest BID", "https://www.swbid.org/feed/", "https://www.swbid.org/", "all"),
    ("WTOP", "https://wtop.com/tag/southwest-dc/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/the-wharf/feed/", "https://wtop.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    *SHARED,
],
```
`news.parse_feed` handles RSS/Atom only, so The Southwester needs the WP-JSON path, the same as Hill Rag.

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **Southwest BID** | `https://www.swbid.org/wp-json/tribe/events/v1/events` (also `/events/?ical=1`) | **Yes, thin.** 1 upcoming: "Jingle Block Rock 2026", 2 Dec 17:00, Waterfront Station, 399 M St SW. |
| **ANC 6D schedule** | `https://www.anc6d.org/wp-json/wp/v2/pages?slug=anc-6d-meeting-schedule-2&_fields=modified,content` | Same parseable page as in SOURCES-EAST (200, 2.5 KB today): "Monday, Jan. 5 (via Zoom) …", 7 pm, with the year in the heading. ANC 6D is ~96% of this boundary, so here it is primary, not optional. |
| OANC | `https://oanc.dc.gov/rss.xml` | Filter `ANC 6D`; none in today's window. |
| The Wharf | `wharfdc.com/upcoming-events/` | HTML only (no feed, no WP JSON). Excluded. |
| Arena Stage, Spy Museum | — | No feed (404s above). |
| Southwest Library (900 Wesley Pl SW) | DCPL | Static link only: `https://dclibrary.libnet.info/events?l=Southwest%20Neighborhood%20Library`. |

```python
ANCS["lenfantplaza"] = ["6D"]
```

### JOBS

**No qualifying in-area feed found.**
- The BID is dominated by federal HQs (HUD, DOE Forrestal, FAA, USDA South Building), which post on USAJOBS (robots-blocked).
- Slugs probed with no board: `spymuseum`, `internationalspymuseum`, `arenastage`, `wharfdc`, `hoffmanmadison`.
- `ZIPS["lenfantplaza"] = ("20024",)` would be safe in that 20024 doesn't spill into another site's area, though it also covers Buzzard Point and Fort McNair (outside the BID). No Greenhouse board in `GREENHOUSE` lists 20024 today, so it would return nothing for now.

---

## 3. NoMa (NoMa BID; ANC 6E ~59%, 5F ~26%, 6C ~14%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/noma/feed/` | allow | 10 (Oct 2023 – 17 Apr 2026) | 9/5/4 | **Best clean source**, slow. "NoMa farmers market is moving — and getting bigger", "'Retail follows roofs': Why the NoMa area in DC is booming". `match`. |
| `https://thedcline.org/?s=noma&feed=rss2&orderby=date&order=DESC` | allow | 20 (Jan 2022 – Mar 2026) | 8/8/4 | `search`. Mostly "District Links" round-ups. |
| PoPville p1–p3 | allow | 60 | 3/3/1 | Real NoMa items: "Now in NoMa – 'CURVE…'", "Stellar Sandwich News – A. Litteri now partnering with Bread Alley!!". |
| `https://www.washingtonian.com/?s=noma&feed=rss2&orderby=date&order=DESC` | allow | 10 (28 Sep – 28 Oct 2026) | 6/0/0 (with the final rule; 11 body hits came from "Union Market" before it was dropped) | Roundups only. Optional. |
| NoMa BID `news` type | `https://www.nomabid.org/wp-json/wp/v2/news?per_page=20&_fields=date,title,content,link` | 20 (Oct 2023 – **12 Mar 2025**) | — | **Stale** (nothing since Mar 2025) and mostly press clippings ("'Epcot' in D.C.: NoMa has something for everyone, residents say."). Low priority. `/feed/` (standard posts) is 200 with 0 items; `/wp-json/wp/v2/posts` returns `[]`. |
| ANC 6E `https://anc6e.dc.gov/rss.xml` | allow | 10 (10 Jun – 13 Oct 2026) | — | Commissioner profiles and meeting nodes; no news. Use for events. |

Not usable:
- **ANC 6C** (`anc6c.org`) is robots-DISALLOWED (see SOURCES-EAST).
- **ANC 5F:** `anc5f.org` and `anc5f.dc.gov` have no DNS; no site found.
- **Union Market** (WTOP union-market tag): its 10 items are all Union Market district, which is outside the BID. As "nearby" at most.
- **Hill Rag:** 0 NoMa hits in 20.

```python
"noma": [
    ("WTOP", "https://wtop.com/tag/noma/feed/", "https://wtop.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="noma"), "https://thedcline.org/", "search"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="noma"), "https://www.washingtonian.com/", "match"),
    *SHARED,
],
```
`TERMS["noma"]` must be compiled **without `re.I`** (see §0.2).

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| NoMa BID | `https://www.nomabid.org/wp-json/wp/v2/event?per_page=20` (custom type `event`; also `venue`, `organizer`) | **No usable date.** 20 items ("The Sunday Reset: HIIT & Flow", "Bonsai Science Cafe", "DC Family Bike Fest 2026"), but `acf` is `[]`, there are no date fields, and the Yoast schema has no Event. The date is only in prose ("Saturday, November 7th from 6 to 8 PM"). Tribe API 404. Several items are outside NoMa (National Arboretum). **Excluded**; ask the BID to expose dates or turn on an iCal feed. |
| **ANC 6E** | `https://anc6e.dc.gov/rss.xml` | **Yes, parse the body** (`Date and Time Wed, Nov 4 2026, 6 - 7pm`, same regex as ANC 2C). Today: three "ANC 6E Executive Meeting" nodes (14 Oct, 4 Nov, 2 Dec, 6–7 pm). The full meetings ("November 18, 2026, ANC 6E Virtual Meeting", "December 16, 2026…", 6:30 pm) are listed on `anc6e.org` (the OANC-platform site; https has a **certificate error**, http works) but were not in the feed's newest 10. Bodies carry Zoom passcodes. |
| OANC | `https://oanc.dc.gov/rss.xml` | Today has "November 12, 2026, ANC 6C Public Meeting" and "December 9, 2026, ANC 6C Public Meeting". Filter `ANC 6[CE]`; see the 6E title caveat in §1. |
| NoMa farmers market | existing farmers-market layer | Not checked against the layer today. |

```python
ANCS["noma"] = ["6E", "5F", "6C"]
```

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **NPR** (HQ 1111 North Capitol St NE = 6E06, inside the BID) | `https://boards-api.greenhouse.io/v1/boards/nationalpublicradioinc/jobs` | 10 jobs; 8 list `Washington, District of Columbia, United States` (1 also New York), 2 `Remote`. "Overnight/Live Broadcast Supervising Editor, Morning Edition & Up First" (updated 2026-10-29), "Temporary Senior Editor, Visuals" (10-30), "Cloud Systems Engineer" (10-06). NPR's only DC office is the HQ. | allow | **Use ("in")**, but the location has **no ZIP**, so `ZIPS` won't catch it. It needs a board-level rule ("all DC jobs on `nationalpublicradioinc` → NoMa"). Exclude `Remote`. |
| **solidcore "Union Market"** (Lever) | `api.lever.co/v0/postings/solidcore?mode=json` | "Coach - Union Market, DC" (created 2026-09-15), "Head Coach & Community Manager - Union Market, DC" (2026-09-04) | allow | "Nearby" (Union Market is outside the BID). |
| CNN (820 1st St NE), REI (201 M St NE), Harris Teeter, ATF HQ | slugs `cnn`, `warnerbrosdiscovery`, `rei` → none; ATF = USAJOBS | — | — | No verified feed. |

---

## 4. Shaw (lead's boundary ANC 6E; see §0.1: historic Shaw is ANC 2G + 1B02)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/shaw/feed/` | allow | 10 (Nov 2022 – 16 Dec 2025) | 9/4/1 | **Best clean source**, slow. "New rooftop lounge in Shaw brings 'Seychellois cuisine' to the menu", "After 2-year break, a holiday shopping tradition returns to DC's Shaw". `match`, with the body counted (`search`) if you trust WTOP's tag; 9/10 bodies say "Shaw neighborhood". |
| PoPville p1–p3 | allow | 60 | 1/1/1 | "Down Goes Dragon Hero in Shaw/U Street near 9:30 Club…". PoPville covers Shaw often; today's window is thin. |
| `https://thedcline.org/?s=shaw&feed=rss2&orderby=date&order=DESC` | allow | 20 (Sep 2022 – Apr 2026) | 1/1/0 | WordPress search matches "Shaw" surnames; only one neighborhood item ("…A Fight Brews Over Limiting Bars And Clubs Near U Street In Shaw…"). Use `match`, not `search`. Low. |
| `https://www.washingtonian.com/?s=shaw&feed=rss2&orderby=date&order=DESC` | allow | 10 (15–29 Oct 2026) | 4/0/0 | Roundup addresses only. Optional. |
| `https://www.washingtonblade.com/?s=shaw&feed=rss2&orderby=date&order=DESC` | allow | 10 (Sep – Oct 2026) | 2/0/0 | Skip. |
| **ANC 2G** `https://www.anc2g.org/meetings?format=rss` (Squarespace) | allow | 22 (posted Jan – Oct 2026) | 20/9/0 | Meeting pages, not news; use for events (below). ANC 2G has no news/blog collection (sitemap: `meetings`, `committees`, `resolutions`, `meeting-minutes`, …). |
| ANC 6E `https://anc6e.dc.gov/rss.xml` | allow | 10 | 0 under the Shaw rule | Commissioner profiles and meetings. **Only if Shaw stays = 6E**, take all. |
| ANC 1B `https://www.anc1b.org/announcements?format=rss` | allow | 20 (Aug 2025 – 29 Oct 2026) | 1/1/0 | Covers 1B02 (Howard Theatre / Shaw–Howard Metro). See U Street. |

Not usable:
- **Shaw Main Streets** (`shawmainstreets.org`, custom CMS): `/feed/` returns the HTML home page. News is HTML pages only (`/news/Art_All_Night_Shaw_Returns_…`).
- Its events page embeds a **Google Calendar** (`src=cla5vv6hnsl3571i2qgqj7ikg8@group.calendar.google.com`). The public ICS (`calendar.google.com/calendar/ical/…/public/basic.ics`) is **robots-DISALLOWED** for our agent. Excluded.
- `shawdish.com` (no DNS). `anc6e.org` https (certificate verify failed; the http version is the OANC Drupal site, same data as anc6e.dc.gov).

```python
"shaw": [
    ("WTOP", "https://wtop.com/tag/shaw/feed/", "https://wtop.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="shaw"), "https://thedcline.org/", "match"),  # surname noise: match, not search
    ("ANC 1B", "https://www.anc1b.org/announcements?format=rss", "https://www.anc1b.org/", "match"),
    *SHARED,
],
```
If 6E is kept, add `("Mount Vernon Triangle CID", "https://www.mvtcid.org/feed/", …, "all")` and `("ANC 6E", "https://anc6e.dc.gov/rss.xml", …, "all")`.

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **ANC 2G** | `https://www.anc2g.org/meetings?format=rss` | **Partial.** Items are pre-created month pages ("November ANC Meeting" → `/meetings/november-2026`, "December ANC Meeting"), pubDate = creation date (12 Jan 2026). The body says "**When**: The second Thursday of each month at 6:30 PM", "Where: Via Zoom". So take the month from the link slug (`/meetings/(\w+)-(\d{4})`) and compute the 2nd Thursday: 2026-11-12, 2026-12-10. One-off items carry a full date in the title ("Emergency Meeting - October 27, 2026"). Committee items: "May 2026 - Transportation Advisory and Public Space Committee Meeting" (month only). `?format=json` is robots-disallowed on Squarespace; `?format=rss` is allowed. |
| **ANC 6E** (if kept) | `https://anc6e.dc.gov/rss.xml` | As in §3. |
| OANC | `https://oanc.dc.gov/rss.xml` | Filter `ANC 2G` / `ANC 6E` (widen the title regex for "Virtual Meeting"). |
| Shaw Main Streets | Google Calendar ICS | **robots-disallowed.** Excluded. |
| Howard Theatre (620 T St NW, 1B02) | `howardtheatre.com` (Wix; `/feed/` 404) | No feed. |
| Watha T. Daniel/Shaw Library | DCPL | Static link: `https://dclibrary.libnet.info/events?l=Shaw%20(Watha%20T.%20Daniel)%20Neighborhood%20Library` (the exact `l=` name is not verified). |

```python
ANCS["shaw"] = ["2G", "1B"]   # recommended (2G + 1B02); with the lead's boundary: ["6E"]
```

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **Children's National "Shaw Metro"** (existing Workday tenant `cn`) | location facet descriptor `Shaw Metro` (id today `8788a69939e31000c39712e00d1f0000`; look it up nightly as jobs.py does) | **5 jobs**: "Special Police Officer" (startDate 2026-10-28), "Clinic Operations Representative, Full Time, Primary Care - Shaw Metro Tech, DC" (10-22), "Medical Director Urgent Care" (10-05), "Clinical Manager I - Pediatric Urgent Care" (09-29), "Chief of General Pediatrics" (07-31). Posting text: **641 S Street NW** = SMD **1B02**, HPN LOGAN CIRCLE/SHAW. | allow | **Use ("in") if Shaw = 2G + 1B02.** With Shaw = 6E it is outside ("nearby", ~0.8 mi). `SITES["shaw"] = [("cn", "Shaw Metro", "in", "641 S St NW")]`; also a "nearby" candidate for U Street and Logan Circle. |
| solidcore | Lever | No Shaw-named studio today ("Mt Vernon Square" is Chinatown HPN / 6E). | allow | — |
| Compass Coffee (HQ 7th St), Giant (O Street Market), Howard Theatre | slugs `compasscoffee` → none; Giant/Ahold Workday 422 (earlier notes) | — | — | No verified feed. |

---

## 5. U Street (HPN `U ST/PLEASANT`; ANC 1B ~47% + 1E ~45%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/u-street/feed/` | allow | 10 (Nov 2024 – 22 Apr 2026) | 10/10/5 | **Best clean source.** Dedupe with the next row. |
| `https://wtop.com/tag/u-street-corridor/feed/` | allow | 10 (Jun 2023 – 28 May 2026) | 10/10/6 | "Why it's about to get more expensive to park along DC's popular U Street corridor". |
| `https://wtop.com/tag/howard-university/feed/` | allow | 10 (23 Oct 2025 – 23 Apr 2026) | 7/4/3 | With the Howard cue rule: "5 shot near Howard University during homecoming weekend…", "Howard homecoming brings (a lot of) DC road closures". `match`. |
| PoPville p1–p3 | allow | 60 | 6/5/2 | "Lil Sto (Fashion) opening soon on U Street", "Red Light (Bar & Detroit Pizza) coming soon to Blue Building", "'Old Banneker High School Trees All Gone'". |
| **ANC 1B** `https://www.anc1b.org/announcements?format=rss` (Squarespace) | allow | 20 (29 Aug 2025 – 29 Oct 2026) | 2/2/0 | Monthly agenda posts plus the odd notice ("Learn About Ranked Choice Voting at Our March 5 Meeting"). Take all (1B is ~47% of the HPN). The home feed `home-1?format=rss` is empty (last build 2015). |
| **African American Civil War Memorial Museum** `https://www.afroamcivilwar.org/feed/` (1925 Vermont Ave NW, in the HPN) | allow | 10 (12 Mar 2025 – 29 Oct 2026) | 9/7/1 | Slow but local: "AACWM Grand ReOpening New Date Set for Veterans Day", "Voting Rights and the USCT". Take all. |
| ANC 1E `https://anc1e.org/feed/` (already used for Columbia Heights) | allow | 10 (Mar – Aug 2026) | 6/1/0 | 1E05–1E07 (Pleasant Plains/Howard) are 45% of this HPN, but the feed is Park View–heavy. `match`. |
| `https://districtbridges.org/feed/` (runs U Street Main Street and Logan Circle Main Street) | allow | 10 (May 2025 – 15 Oct 2026) | 2/2/0 | "PROTECT THE BRIDGE: …", "World Pride 2025 Specials & Events on Your DC Main Street". `match`. |
| Washingtonian `?s=u+street` / Blade `?s=u+street` | allow | 10 / 10 | 2/0/0, 1/0/0 | Roundups and boilerplate. Skip. |
| `https://thedcline.org/?s=u+street&feed=rss2&orderby=date&order=DESC` | allow | 20 | 0 | WordPress search treats "u" as a stopword. Skip. |

Not usable:
- U Street Main Street domains: `ustreetdc.org` (TLS internal error), `ustreetmainstreet.org` (timeout). The program lives on districtbridges.org.
- `anc1b.org/feed/` 404 (Squarespace); `anc1b.dc.gov` (no DNS).
- The Hilltop (`thehilltoponline.com/feed/`: 5 items, all 9 Dec 2024, stale).
- Lincoln Theatre and 9:30 Club (I.M.P.): `/feed/` has 0 items; their `lincoln_event` / `930_event` types return `[]` via REST.

```python
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
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **ANC 1B** | `https://www.anc1b.org/announcements?format=rss` | **Partial.** Titles are month-only ("November 2026 Agenda"). The body names the day: "Please see the agenda for our November 5th Commission meeting below. We will convene at 6:30 p.m. … formal meeting at 7:00", so take the month and year from the title and the day from `our (\w+ \d{1,2})(st\|nd\|rd\|th)? (special )?Commission meeting`. **Caveat:** the October 2026 post's body says "September 3rd" (copy-paste error), so reject a body date whose month differs from the title's. Special meetings have the date in the title ("September 28 Special Meeting Agenda"). `/upcoming-meetings?format=json` is **robots-disallowed**. ANC 1B meets the first Thursday. |
| **ANC 1E** | `https://anc1e.dc.gov/rss.xml` | As documented for Columbia Heights (accept only titles with a full date). |
| **District Bridges events** (U Street Main Street) | `https://districtbridges.org/events/feed/` (MEC RSS; already documented) | **Yes, but nothing for U Street today.** The 10 upcoming items are Chevy Chase, Columbia Heights and Cleveland Park. Filter by `mec:location` / title containing "U Street", "14th & U", "Reeves". Earlier editions ("Art All Night U Street", Sept) appear seasonally. |
| AACWM | tribe 404 | Events appear as posts only. |
| Lincoln Theatre / 9:30 Club | REST types empty; Ticketmaster links only | No. |
| Howard University | not tested | — |

```python
ANCS["ustreet"] = ["1B", "1E"]
```

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **solidcore "14th & U"** (Lever) | `api.lever.co/v0/postings/solidcore?mode=json`, `text` endswith `- 14th & U, DC` | "Core Crew (Front Desk & Sales) - 14th & U, DC", created 2022-12-08 | allow | Evergreen; optional, no date. |
| Children's National "Shaw Metro" (641 S St NW) | see §4 | 5 jobs | allow | "Nearby" (~0.3 mi south of the HPN). |
| Howard University / Howard University Hospital | Greenhouse `howarduniversity` exists but has **0 jobs**; `howard` none; Workday tenant not found (not guessed further) | — | — | No verified feed. |
| Reeves Center (DC government) | — | — | — | DC government jobs: not tested. |

---

## 6. Logan Circle (ANC 2F)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/logan-circle/feed/` | allow | 10 (Jun 2022 – 2 Apr 2026) | 10/10/7 | Clean, slow. `match`. |
| `https://thedcline.org/?s=logan+circle&feed=rss2&orderby=date&order=DESC` | allow | 20 (Oct 2020 – 15 Jul 2026) | 14/14/7 | `search`. Mostly link round-ups. |
| `https://www.washingtonian.com/?s=logan+circle&feed=rss2&orderby=date&order=DESC` | allow | 10 (8 Sep – 27 Oct 2026) | 9/2/2 | "The Ice Cream House: A Logan Circle Landmark", "A Perfect Day in Logan Circle". `match`. |
| **ANC 2F** `https://anc2f.org/feed/` (= `www.anc2f.org`) | allow | 10 (14 Jun – 29 Oct 2026) | 4/4/4 (all 10 are 2F items) | Meeting notices and agendas ("November 4, 2026 ANC 2F Monthly Commission Meeting", "October 21st Alcohol Cannabis Policy Committee Meeting"). **Take all**; it is also the events source. |
| `https://districtbridges.org/feed/` (Logan Circle Main Street) | allow | 10 | 2/2/0 | "LCMS FY26 Small Business Grant Applications Open!". `match`. |
| `https://www.washingtonblade.com/?s=logan+circle&feed=rss2&orderby=date&order=DESC` | allow | 10 (Jun – Oct 2026) | 10/1/0 | Body hits look like boilerplate on opinion pieces ("Queering America 250", "Celebrating 250 years of LGBTQ Icons"). Use summary (`match`) only; low value. |
| PoPville p1 | allow | 20 | 1/0/0 | "Red Light (Bar & Detroit Pizza) coming soon to Blue Building" (body: "14th and R"). |

Not usable:
- **Logan Circle Community Association** (`logancircle.org`, Squarespace): no blog/news collection (sitemap: `calender`, `lcca-newsletter-archives`, `local-stories`, `initiatives-*`…).
  - Its `calender?format=json` is **robots-disallowed**, and `calender?format=rss` returns 400 (not a blog/events collection).
  - `/feed/` 404.
- `logancirclemainstreet.org/feed/` 404; the program is on districtbridges.org.
- `anc2f.dc.gov` (no DNS). Studio Theatre `/feed/` 404.

```python
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
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **ANC 2F** | `https://anc2f.org/feed/` | **Yes, parse the title.** "November 4, 2026 ANC 2F Monthly Commission Meeting", "October 7, 2026, ANC 2F Monthly Commission Meeting", "July 1, 2026 ANC2F Monthly Commission Meeting". Regex `^([A-Z][a-z]+ \d{1,2}),? (\d{4}),?\s+ANC\s?2F\b`. The existing `AGENDA` regex in events.py ("… Meeting Agenda") will **not** match, so add this as a second pattern for `ANC_FEEDS["logancircle"] = ("ANC 2F", "https://anc2f.org/feed/", "https://anc2f.org/")`. Committee posts have day-month without year ("October 21st Alcohol Cannabis Policy Committee Meeting"); the body has "October 21, 2026 @7PM". Some titles start with "Cancelled". Skip those (or show them as cancelled). "September ANC 2F Monthly Commission Meeting" has no day. Commission meets the 1st Wednesday at 7 pm. The site's Tribe API is installed but has **0 events** and `/events/?ical=1` is empty. |
| District Bridges events (Logan Circle Main Street) | `https://districtbridges.org/events/feed/` | Nothing for Logan today; filter by title/location as for U Street. |
| LCCA calendar | Squarespace | robots-disallowed (`?format=json`). Excluded. |
| OANC | `https://oanc.dc.gov/rss.xml` | Filter `ANC 2F`. |

```python
ANCS["logancircle"] = ["2F"]
ANC_FEEDS["logancircle"] = ("ANC 2F", "https://anc2f.org/feed/", "https://anc2f.org/")  # title regex differs; see above
```

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **solidcore "Logan Circle"** (Lever) | `api.lever.co/v0/postings/solidcore?mode=json`, `text` endswith `- Logan Circle, DC` | "Coach - Logan Circle, DC", **created 2026-09-25** (a current posting, not a 2022 pool). No street address in the posting (studio address not verified). | allow (Crawl-delay 1) | **Use ("in")**, with the name-only caveat. |
| Children's National "Shaw Metro" (641 S St NW) | see §4 | 5 jobs | allow | "Nearby" (~0.5 mi east). |
| Whole Foods P St (1440 P St NW, 2F03), Studio Theatre, Trader Joe's 14th St | Amazon/WFM jobs (not tested); slugs `studiotheatre` → none | — | — | No verified feed. |
| ZIPs | 20005 (also downtown and Chinatown's 601 13th St), 20009 (Dupont/Adams Morgan) | — | — | **No usable ZIP.** |

---

## 7. HISTORY (Evening Star, loc.gov, week 1926-10-31 → 11-06)

loc.gov answered our UA normally (robots allow), but slowly: 2–3 minutes per term including OCR fetches. I used the same query shape as `history.py`: `q`, `dates=1926-10-31/1926-11-06`, `fa=partof_title:evening star (washington, d.c.) 1854-1972`, `fo=json`. I read OCR (`word-coordinates-service`, `full_text`) for the top 3 pages per term. "Week" is the page count in the target week.

**Pitfalls specific to these areas:**
1. **Single-letter words are dropped by loc.gov** (as found for H Street).
   - `"U street"` returns **339** pages, the same count as `"H street"`: in effect it is the query "street". `"Twelfth Street Y. M. C. A."` likewise collapses to "Twelfth Street" (19 pages, none naming the YMCA).
   - Query the long form and require the regex locally.
2. **Names didn't exist yet or meant something else in 1926:**
   - "Logan Circle" returns **0**: the circle was **Iowa Circle** until 1930.
   - "Chinatown" (7 pages) is almost all the syndicated quip column "said Hi Ho, the sage of Chinatown". DC's Chinatown then sat on Pennsylvania Ave/4½ St, now Federal Triangle (NATIONAL MALL HPN); it moved to H St in 1931.
   - "NoMa", "L'Enfant Plaza" and "Shaw" (as a neighborhood name) are all later coinages.
3. **Southwest's 1926 street grid was erased** by 1950s urban renewal. 1926 SW addresses (e.g. Neighborhood House, 470 N St SW) are real SW, but they don't map onto today's BID blocks: 470 N St SW is 6D06, just south of the BID. Treat any SW cue as in-area.
4. **The Star in 1926 was segregated.** U Street, Shaw and Howard coverage is thin, and the clips that exist often say "colored", so the SCREEN filter will drop them. Example: the 2 Nov headline on the reception for Mordecai Johnson, Howard's new president, given by 67 "colored" Baptist churches. Expect 0–3 publishable clips a week for Shaw and U Street.

### Chinatown

| Term | Week | What the snippets show |
|---|---|---|
| `Chinatown` | 7 | All 3 sampled: "Hi Ho, the sage of Chinatown" (syndicated filler). **Don't use** without the reject below. |
| `"Mount Vernon place"` | 3 | Mount Vernon Place M.E. Church South (900 Massachusetts Ave NW = 2C04, inside): a "Messiah" chorus, a week of prayer, a missionary federation meeting. Clean. |
| `"Ford's Theater"` | 3 | The War Department may sell the brick stable "back of the old Ford's Theater" where Booth kept his horse (4 Nov). Clean, in-area (511 10th St NW). |
| `"Pension Office"` | 1 | Real-estate ad: 407 4th St NW "facing Court House Park and near U.S. Pension Office". In-area (National Building Museum, 6E08). |
| `"Patent Office"` | 4 | Federal: site plans, a bowling league, a want ad. Weak. |
| `"Seventh street"` | 29 | Mixed: "612 Seventh street southwest" (SW!), and a furniture ad for "Seventh Street Between D and E" (in-area). Needs an NW/block filter. |
| `"Lansburgh"` | 16 | All department-store ads (7th–8th & E). Booster only. |
| `"Mount Vernon Square"` / `"Judiciary Square"` | 0 / 0 | — |
| `"Public Library"` | 5 | Branch libraries (Mount Pleasant, Southeast); the central library at Mt Vernon Sq isn't named this way. Don't use. |

```python
"chinatown": {
    "terms": ['"Mount Vernon place"', "\"Ford's Theater\"", '"Pension Office"', '"Seventh street"', "Chinatown"],
    "pattern": r"mount\s+vernon\s+(place|square)|ford.s\s+theat|pension\s+(office|building)|judiciary\s+square|court\s+house\s+park|"
               r"\b[4-9]\d\d\s+(seventh|7th|eighth|8th|ninth|9th|tenth|10th)\s+st(reet|\.)?|"
               r"(seventh|7th|eighth|8th|ninth|9th)\s+st(reet|\.)?\s+(between|and|at)\s+[d-i]\b|chinatown",
    "local": r"n\.\s?w\.|northwest|seventh\s+st|7th\s+st|massachusetts\s+av|new\s+york\s+av|mount\s+vernon|judiciary|lansburgh|"
             r"woodward|palais\s+royal|kann|patent\s+office|pension",
},
```
- **reject**: `sage\s+of\s+chinatown|(seventh|7th)\s+st(reet|\.)?\s+(southwest|s\.\s?w)|patent\s+office\s+(examiner|team|bowl|roll)|chinatown.{0,40}(san\s+francisco|new\s+york)`.

### L'Enfant Plaza (Southwest)

| Term | Week | What the snippets show |
|---|---|---|
| `Southwest` | 56 | Mixed. Real items: the **Southwest market-site fight** (a citizens' association urged to back "the Southwest market site"). Noise: the **weather box** ("gentle winds, mostly south and southwest"), so the reject below is required. |
| `"Southwest Washington"` | 2 | The market fight (a cold-storage plant "in Southwest Washington"), and Alice Barney's arts-and-crafts house on N Street SW. Clean. |
| `"Neighborhood House"` | 3 | The settlement house at **470 N St SW**: its 25th-anniversary celebration and gifts of property and cash (3–6 Nov). Clean, civic, a strong local story. |
| `"Maine avenue"` | 1 | Building permit at "Third street and Maine avenue **southeast**". In 1926 Maine Ave also ran in SE; needs SW. |
| `"Water street"` / `"fish wharf"` / `"Seventh street wharf"` / `"Four-and-a-half street"` | 1 / 0 / 0 / 0 | Quiet this week. |

```python
"lenfantplaza": {
    "terms": ['"Southwest Washington"', '"Neighborhood House"', "Southwest", '"Maine avenue"'],
    "pattern": r"southwest\s+(washington|site|market|section|citizens)|neighborhood\s+house|"
               r"\b\d{2,4}\s+[\w\-½]+\s+st(reet|\.)?\s+(southwest|s\.\s?w)|maine\s+av(enue|e)?\.?\s+(southwest|s\.\s?w)|"
               r"water\s+st(reet|\.)?\s+(southwest|s\.\s?w)|four.and.a.half\s+st|fish\s+wharf|seventh\s+street\s+wharf",
    "local": r"s\.\s?w\.|southwest|maine\s+av|water\s+st|n\s+street|seventh\s+st|four.and.a.half|wharf|barney",
},
```
- **reject**: `(south\s+and\s+)?southwest\s+winds?|winds?,?\s+(mostly\s+)?(south\s+and\s+)?southwest|southwest\s+(virginia|texas|africa|pacific)|maine\s+av(enue|e)?\.?\s+(southeast|s\.\s?e)`.

### NoMa

| Term | Week | What the snippets show |
|---|---|---|
| `"Sibley Hospital"` | 9 | Old Sibley Hospital, then at 1140 North Capitol St NW. It moved in 1961; the NW side of North Capitol is partly in the BID, e.g. GPO, 6E07. The hits are a hospital-guild membership drive and birth/death lists; the existing list filters will drop the lists. |
| `Eckington` | 8 | The **farmers' market site fight**: the B&O Railroad backing the Eckington site, and the Ivy City citizens endorsing it. Eckington's south edge (5F06/07) is in the BID. |
| `"North Capitol street"` | 8 | Runs the full length of the city. "1805 North Capitol street" (north of the BID), and a repairs permit at 1311 North Capitol (near the BID). Needs a block filter. |
| `"Government Printing Office"` | 1 | Bowling league. Weak. |
| `"Gonzaga"` | 2 | **Gonzaga University (Spokane) football scores.** Reject. |
| `Swampoodle` / `Uline` | 0 / 0 | — |

```python
"noma": {
    "terms": ['"Sibley Hospital"', "Eckington", '"North Capitol street"', '"Government Printing Office"'],
    "pattern": r"sibley\s+hospital|eckington|government\s+printing\s+office|swampoodle|gonzaga\s+(college|high)|"
               r"\b([2-9]\d\d|1[0-5]\d\d)\s+north\s+capitol\s+st|north\s+capitol\s+(street\s+)?(and|at)\s+[g-r]\s+st|tiber\s+creek",
    "local": r"north\s+capitol|first\s+st(reet)?\s+n|1st\s+st|n\.\s?e\.|northeast|eckington|florida\s+av|new\s+york\s+av|k\s+st|m\s+st|"
             r"union\s+station|printing\s+office",
},
```
- **reject**: `gonzaga\s*(vs\.?|,|\d)|spokane`.

### Shaw

| Term | Week | What the snippets show |
|---|---|---|
| `"Shaw Junior High"` | 2 | School-board items: a repairs list naming the Shaw Junior High schoolyard (5 Nov), and a teacher transfer. The school (7th & Rhode Island) gave the neighborhood its later name. Clean. |
| `"Ninth street"` | 21 | Mostly **NE** (Keller Memorial Lutheran, 9th & Maryland Ave NE; "529 Ninth street northeast"). One NW ad, "512 ninth street n.w.", is Chinatown. Needs the 1100–1999 NW filter. |
| `"Rhode Island avenue"` | 9 | Mixed NE/NW. A traffic item at "Rhode Island avenue and Seventh street" is a Shaw corner, but the clip says "colored", so it would be screened. |
| `"Seventh street northwest"` / `"Howard Theater"` / `"Dunbar Theater"` / `"O Street Market"` / `"Northern Liberty"` | 0 each | The Star wrote "Seventh street" without "northwest"; the Black theaters weren't named in this week's (segregated) entertainment pages. |

```python
"shaw": {
    "terms": ['"Shaw Junior High"', '"Rhode Island avenue"', '"Ninth street"', '"Seventh street"'],
    "pattern": r"shaw\s+junior\s+high|howard\s+theat|o\s+street\s+market|northern\s+liberty|"
               r"\b1[1-9]\d\d\s+(seventh|7th|ninth|9th|eighth|8th)\s+st(reet|\.)?|"
               r"(seventh|ninth)\s+(street\s+)?and\s+(rhode\s+island|[m-t]\s+st)|rhode\s+island\s+av(enue|e)?\.?\s+and\s+(sixth|seventh|eighth|ninth|tenth)",
    "local": r"n\.\s?w\.|northwest|seventh\s+st|ninth\s+st|rhode\s+island\s+av|o\s+st|p\s+st|r\s+st|s\s+st|t\s+st|shaw|howard",
},
```
- **reject**: `(seventh|ninth|rhode\s+island)\s+(street|avenue)\s+(southwest|northeast|s\.\s?w|n\.\s?e)` when there is no `n\.\s?w|northwest` in the clip.

### U Street

| Term | Week | What the snippets show |
|---|---|---|
| `"U street"` | 339 (meaningless; pitfall 1) | Some real: a building-and-loan ad at "1421 U Street N.W.". Others ambiguous ("3316 U street"). Filter locally with the 700–1999 NW block regex. |
| `"Howard University"` | 8 | **Mordecai Johnson**, newly elected as Howard's first Black president: receptions and his first public speech (1–2 Nov), plus an R.O.T.C. transfer. In-area (campus 1E05). Most will be screened. |
| `"Griffith Stadium"` | 5 | All football (GWU vs Ursinus, the Mohawks vs Waverly). The stadium (7th & Florida, now Howard University Hospital, 1B01) is in-area, but drop sports. |
| `"Lincoln Theater"` | 1 | Movie listing. Listing-heavy. |
| `"Florida avenue"` | 7 | Permits ("Eleventh street and Florida avenue"), and North Capitol widening "from Florida avenue". Booster. |
| `"Republic Theater"` / `"Murray"` | 0 / 34 | "Murray" is surnames only. Don't use. |

```python
"ustreet": {
    "terms": ['"Howard University"', '"Lincoln Theater"', '"U street"', '"Florida avenue"'],
    "pattern": r"howard\s+university|lincoln\s+theat|lincoln\s+colonnade|true\s+reformers?|industrial\s+savings\s+bank|"
               r"\b([7-9]|1[0-9])\d\d\s+U\s+st(reet|\.)?|\bU\s+st(reet|\.)?\s+(n\.?\s?w|northwest)|le\s?droit\s+park|"
               r"(eleventh|twelfth|thirteenth|fourteenth|ninth|seventh)\s+(street\s+)?and\s+(U|florida\s+av)",
    "local": r"\bU\s+st|florida\s+av|georgia\s+av|vermont\s+av|seventh\s+st|eleventh|twelfth|thirteenth|fourteenth|le\s?droit|"
             r"howard\s+place|sherman\s+av|n\.\s?w\.",
},
```
- **reject** (sports and other places): `foot\s*ball|eleven|touchdown|gridiron|varsity|quarterback|coach|base\s*ball|senators|griffith\s+stadium|\bU\s+st(reet|\.)?\s+(s\.\s?e|southeast|n\.\s?e|northeast)`.
- Griffith Stadium is in the reject list on purpose: in Nov 1926 it is only ever a football venue.

### Logan Circle

| Term | Week | What the snippets show |
|---|---|---|
| `"Logan Circle"` | **0** | The name dates from 1930. |
| `"Iowa Circle"` | 2 | Apartment ads ("THE BERLIN. 7 IOWA CIRCLE N.W."). Clean, in-area (Logan Circle, 2F04). |
| `"Thomas Circle"` | 15 | Rooms-for-rent classifieds ("1124 Vermont ave. (Thomas Circle)", "1404 M N.W. (Thomas Circle)"). Thomas Circle is the 2F/2C edge; the exact SMD split is **not verified**. |
| `"Vermont avenue"` | 10 | Vermont Avenue Christian Church, "north of N Street" (in 2F; sermon notices), and the Arlington Hotel "above K" (south of 2F). Needs a block filter. |
| `"Fourteenth street"` | 31 | Mixed: a police-court story, and the Arcadia Auditorium at 14th & Park Rd (Columbia Heights). Block filter required. |
| `"Logan statue"` | 0 | — |

```python
"logancircle": {
    "terms": ['"Iowa Circle"', '"Thomas Circle"', '"Vermont avenue"', '"Fourteenth street"'],
    "pattern": r"iowa\s+circle|logan\s+circle|thomas\s+circle|vermont\s+avenue\s+(christian|church|m\.\s?e)|"
               r"\b1[0-6]\d\d\s+(vermont|rhode\s+island)\s+av|\b1[0-6]\d\d\s+(fourteenth|14th|thirteenth|13th|fifteenth|15th)\s+st|"
               r"\b1[3-5]\d\d\s+[n-r]\s+st(reet|\.)?\s+n\.?\s?w|(fourteenth|thirteenth)\s+(street\s+)?and\s+[n-r]\s+st",
    "local": r"vermont\s+av|rhode\s+island\s+av|fourteenth|thirteenth|fifteenth|\b[n-r]\s+st|iowa\s+circle|thomas\s+circle|n\.\s?w\.",
},
```
- **reject**: `park\s+r(oa)?d|columbia\s+heights|arcadia|above\s+.?k.?\b`.
- Expect 3–8 clips a week, mostly classifieds; the existing LEGAL/list filters will thin them.

## 8. Not verified / excluded

- **Robots-disallowed for our agent:**
  - `calendar.google.com/calendar/ical/…` (Shaw Main Streets' public calendar).
  - Squarespace `?format=json`: `anc1b.org/upcoming-meetings`, `logancircle.org/calender`.
  - Previously known: `anc6c.org`, USAJOBS, `parkviewdc.com`, WTOP `?s=`.
- **403 to our UA:** none new.
- **TLS / DNS failures (not retried with other agents):**
  - `lenfantplaza.com` (handshake failure); `ustreetdc.org` (TLS internal error); `ustreetmainstreet.org` (timeout).
  - `anc6e.org` https (certificate verify failed; http OK); `anc2g.org` without www (unrecognized name); `chinatowndc.com` (TLS error).
  - No DNS: `chinatowndc.org`, `shawdish.com`, `penn-quarter.com`, `anc1b.dc.gov`, `anc2f.dc.gov`, `anc2c.org`, `anc5f.org`, `anc5f.dc.gov`, `anc6d.dc.gov`, `noma.dc.gov`, `bloomingdaledc.net`.
- **No machine-readable dates:**
  - NoMa BID `event` type, DowntownDC BID `event` type, ANC 2G committee items (month only).
  - Wharf, Howard Theatre (Wix), Lincoln Theatre / 9:30 Club (types empty), Shaw Main Streets (HTML + robots-blocked Google Calendar).
- **Feeds that return HTML instead of RSS:** `thesouthwester.com/feed/` (use WP JSON), `shawmainstreets.org/feed/`.
- **Stale:**
  - NoMa BID news type (newest Mar 2025); WTOP `lenfant-plaza` (Feb 2024), `mount-vernon-triangle` (Oct 2024), `the-wharf` (Sep 2025), `shaw` (Dec 2025).
  - The DC Line `?s=southwest+waterfront` (Jun 2024); The Hilltop (Dec 2024); Woolly Mammoth feed (Sep 2025).
- **Not tested:** Smithsonian event feeds (NPG/SAAM); Howard University's job platform; DC government job feeds; Whole Foods/Amazon jobs; Ticketmaster/venue calendars (terms not reviewed); whether the FRESHFARM NoMa and MVT markets are in the existing farmers-market layer.
- **Engine changes these recommendations assume** (not made; this file is the only edit):
  1. A WP-JSON news path for The Southwester (as for Hill Rag).
  2. Case-sensitive TERMS for NoMa and Shaw.
  3. A body-date parser for OANC-platform ANC feeds (`Date and Time …`).
  4. An ANC 2F title regex.
  5. An OANC title regex that accepts "Virtual Meeting".
  6. Per-board rules for Greenhouse boards without ZIPs (NPR) or with shared ZIPs (sweetgreen by address).
