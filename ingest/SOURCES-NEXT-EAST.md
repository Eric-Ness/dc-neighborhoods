# Sources for Congress Heights, Deanwood and Hillcrest (DC)

Tested 2026-11-03. Every feed and calendar fetch used the user agent `dc-neighborhoods-ingest/0.1 (+https://petworth.org)`. I checked robots.txt with the engine's own matcher (`news.parse_robots`, `news.parse_crawl_delay`, `news.robots_allows`) on the exact URL, query string included. Each host got at least 2 s between requests, and more where a Crawl-delay asked for it: East of the River 10 s, anc8d.org 10 s, Hill Rag 20 s. About 290 URLs in all.

Counts read **body / summary / title**, as in SOURCES-LATE. "Summary" is what `match` mode sees in `news.parse_feed(body=False)`. Counts apply TERMS and NOT_HERE together, and "60 d" means published on or after 2026-09-04. The slugs `congressheights`, `deanwood` and `hillcrest` are my suggestions. None is in `neighborhoods.json`, and I did not check domains.

Congress Heights can carry a site. Deanwood and Hillcrest can't on headlines alone: about 1 and 1.7 matched headlines a month, and most of Hillcrest's are about a park outside its boundary. Verdicts are in §5.

## 0. Cross-cutting findings

### 0.1 Geography (DC GIS: HPN `Health_WebMercator/MapServer/13`, SMD-2023 `Administrative_Other_Boundaries_WebMercator/MapServer/55`, BID `Business_Betterment_Areas_WebMercator/MapServer/15`, Main Streets `…/MapServer/16`, Neighborhood Clusters `Administrative_Other_Boundaries_WebMercator/MapServer/17`, address points `Location_WebMercator/MapServer/0`)

Shares come from polygon intersection, not a grid. "Centroid SMDs" follows the rule in `run.py` / `setup_hood.py`. Bold rows are my recommendations.

| Area | Boundary option | ~km² | Centroid SMDs | SMDs by area | ANCs by area | BIDs / Main Streets |
|---|---|---|---|---|---|---|
| Congress Heights | HPN `CONGRESS HEIGHTS/SHIPLEY` | 2.29 | 8C04, 8C06, 8C07, 8D08, 8E03, 8E04, 8E05 | 8E05 21%, 8C07 19%, 8C04 14%, 8E04 12%, 8D08 12%, 8C06 11%, 8E03 7%, 8D01 5% | 8C 44%, 8E 39%, 8D 17% | Soul of the City BID 36% here, Congress Heights Main Street 45% here |
| | HPN + `SAINT ELIZABETHS` | 6.41 | 8A06, 8C02, 8C03, 8C04, 8C06, 8C07, 8D08, 8E03, 8E04, 8E05 | 8C01 26%, 8C03 13%, 8A06 11%, 8C04 9%, 8E05 7%, 8C07 7%, 8D01 5%, others under 5% | 8C 63%, 8E 14%, 8A 11%, 8D 9%, 8F 3% | **Anacostia BID 87% here**, Soul of the City 78%, Main Street 96% |
| | + `DOUGLASS` | 7.94 | adds 8C05, 8C08, 8E01, 8E02 | 8C01 21%, 8C03 15%, 8A06 9%, 8C04 8%, 8E05 7% | 8C 62%, 8E 19%, 8A 9%, 8D 7%, 8F 2% | Soul of the City 88%, Main Street 100%, Anacostia BID 87% |
| | CH + St. E + `BELLEVUE` | 13.80 | 18 SMDs | 8D04 37%, 8C01 12%, 8C03 6% | 8D 53%, 8C 29%, 8E 11%, 8A 5%, 8F 1% | as above |
| | **SMDs 8C02, 8C03, 8C04, 8C06, 8C07, 8C08, 8E03, 8E04, 8E05** | **4.40** | as given, plus 8C05, whose centroid falls inside | 8C03 27%, 8E05 16%, 8C04 14%, 8C07 11%, 8E04 10%, 8C06 6%, 8E03 5%, 8C08 5%, 8C02 5% | 8C 68%, 8E 32% | **Soul of the City 88% here**, Main Street 92% here, Anacostia BID 5% here |
| | ANC 8C entire | 7.05 | all 8C | 8C01 53%, 8C03 17%, 8C04 9% | 8C 100% | 29% is `NAVAL STATION & AIR FORCE`. No. |
| Deanwood | HPN `LINCOLN HEIGHTS` | 3.53 | 7C01–7C07, 7C09 | 7C07 17%, 7C03 16%, 7C05 15%, 7C06 14%, 7C04 12%, 7C02 11%, 7C01 7%, 7C09 6%, 7F04 2% | 7C 98%, 7F 2% | Deanwood Heights Main Street 94% here |
| | HPN `MARSHALL HEIGHTS` | 2.78 | 7C08, 7E01–7E07 | 7E02 16%, 7E01 15%, 7E07 15%, 7C08 13%, 7E04 11%, 7E05 11%, 7E06 10%, 7E03 9% | 7E 87%, 7C 13% | None |
| | Both HPNs | 6.30 | 7C01–7C09, 7E01–7E07 | no SMD above 9% | 7C 61%, 7E 38%, 7F 1% | Deanwood Heights 94% |
| | **ANC 7C entire** | **4.32** | 7C01–7C09 | 7C07 18%, 7C05 13%, 7C03 13%, 7C06 12%, 7C09 11%, 7C04 9%, 7C02 9%, 7C08 9%, 7C01 6% | 7C 100% | **Deanwood Heights 100% here**, Minnesota Avenue Main Street 7% |
| | ANC 7C + 7E | 6.74 | all of both | 7C07 12%, others 8% or less | 7C 64%, 7E 36% | Deanwood Heights 100% |
| Hillcrest | HPN `NAYLOR/HILLCREST` | 3.57 | 7B02, 7B03, 7B05, 7B06, 8B01, 8B02, 8B03, 8B05 | 7B02 30%, 7B05 18%, 7B06 16%, 7B03 10%, 8B02 9%, 8B05 7%, 8B01 6%, 8B03 6% | 7B 72%, 8B 28% | Pennsylvania Avenue East Main Street 55% here |
| | **SMDs 7B02, 7B03, 7B05, 7B06, 8B02, 8B05** | **3.16** | as given | 7B02 33%, 7B05 20%, 7B06 18%, 7B03 11%, 8B02 10%, 8B05 8% | 7B 82%, 8B 18% | Pennsylvania Avenue East 54% here. 99% is the HPN. |
| | SMDs 7B02, 7B03, 7B05, 7B06 only | 2.60 | as given | 7B02 41%, 7B05 24%, 7B06 22%, 7B03 13% | 7B 100% | Loses part of Naylor Gardens (below) |
| | HPN `FORT DUPONT` | 3.04 | 7B09, 7D04, 7F02, 7F05, 7F07 | 7F05 18%, 7D04 17%, 7F07 16%, 7B09 13%, 7F02 11% | 7F 63%, 7B 20%, 7D 17% | Minnesota Avenue 52%. **Doesn't hold the park.** |
| | NAYLOR/HILLCREST + FORT DUPONT | 6.61 | 13 SMDs | 7B02 16%, others 9% or less | 7B 48%, 7F 29%, 8B 15%, 7D 8% | These two polygons make no sense together. |
| | ANC 7B entire | 7.25 | 7B01–7B09 | 7B01 23%, 7B02 15%, 7B08 14%, 7B07 12% | 7B 100% | Penn Ave East 100% here. HPN mix: TWINING 55%, NAYLOR/HILLCREST 36%, FORT DUPONT 9%. |
| | ANC 7B + 8B02, 8B05 | 7.81 | 7B01–7B09, 8B02, 8B05 | 7B01 22%, 7B02 13%, 7B08 13%, 7B07 11% | 7B 93%, 8B 7% | The one to use if you want Fort Dupont Park and Penn Branch. The Ice Arena is still out (7F06). |

**Which HPN holds Deanwood?** There's no DEANWOOD name. `LINCOLN HEIGHTS` holds it: every Deanwood landmark I tested is in that HPN, and 92% of Neighborhood Cluster 31 ("Deanwood, Burrville, Grant Park, Lincoln Heights, Fairmont Heights") lies inside it. Slivers of the cluster fall in `EASTLAND GARDENS` and `MARSHALL HEIGHTS`.

**Landmarks, address points checked against both layers.** "(coord)" means my own approximate coordinate.

| Landmark | HPN, SMD |
|---|---|
| **Congress Heights set** | |
| Entertainment & Sports Arena 1100 Oak Dr SE; Cedar Hill Regional 1200 Pecan St SE; 3100 MLK Ave SE | SAINT ELIZABETHS, 8C03 |
| St. Elizabeths West, DHS, 2701 MLK Ave SE | SAINT ELIZABETHS, **8C01** |
| **Congress Heights Metro 1290 Alabama Ave SE** | **DOUGLASS**, 8C03 |
| Ballou 3401 4th St SE; 3200 MLK Ave SE | CONGRESS HEIGHTS/SHIPLEY, 8C04 |
| Malcolm X ES 1351 Alabama Ave SE | CONGRESS HEIGHTS/SHIPLEY, 8C06 |
| Simon ES 401 Mississippi Ave SE; Hart MS 601 Mississippi Ave SE | CONGRESS HEIGHTS/SHIPLEY, 8C07 |
| Parklands-Turner Library 1547 Alabama Ave SE | CONGRESS HEIGHTS/SHIPLEY, 8E03 |
| **THEARC 1901 Mississippi Ave SE** | **DOUGLASS**, 8E05 |
| Turner ES 3264 Stanton Rd SE | DOUGLASS, 8C08 |
| 4001 Wheeler Rd SE | WASHINGTON HIGHLANDS, 8E04 |
| Outside: Anacostia Metro 1101 Howard Rd SE; Savoy ES 2400 Shannon Pl SE | SAINT ELIZABETHS, 8A06 |
| Outside: Barry Farm Rec 1230 Sumner Rd SE | SAINT ELIZABETHS, 8C01 |
| Outside: Bellevue Library 115 Atlantic St SW; 4100 MLK Ave SW | BELLEVUE, 8D01 |
| Outside: Hendley ES 425 Chesapeake St SE | BELLEVUE, 8E09 |
| Outside: Patterson ES; Bald Eagle Rec | BELLEVUE, 8D06; 8D04 |
| Outside: Ferebee-Hope 3999 8th St SE; Oxon Run Park (coord) | WASHINGTON HIGHLANDS, 8E06 |
| **Deanwood set** | |
| Deanwood Rec and Library 1350 49th St NE; Deanwood Metro 4720 Minnesota Ave NE; Ron Brown 4800 Meade St NE | LINCOLN HEIGHTS, 7C07 |
| Burrville ES 801 Division Ave NE; HD Woodson 540 55th St NE; Riverside Center 5200 Foote St NE; Marvin Gaye Park (coord) | LINCOLN HEIGHTS, 7C06 |
| Kelly Miller MS 301 49th St NE; Nannie Helen Burroughs School 601 50th St NE; Strand Theater 5131 NHB Ave NE; 400 50th St NE | LINCOLN HEIGHTS, 7C03 |
| Drew ES 5600 Eads St NE | LINCOLN HEIGHTS, 7C05 |
| Merritt 5002 Hayes St NE | LINCOLN HEIGHTS, 7C01 |
| Aiton ES 533 48th Pl NE; 4801 NHB Ave NE | LINCOLN HEIGHTS, 7C09 |
| Richardson Dwellings 5300 Central Ave SE; UDC East Capitol 5929 East Capitol St SE | MARSHALL HEIGHTS, **7C08** |
| Capitol View Library 5001 Central Ave SE; Davis ES; Plummer ES; Ridge Rec | MARSHALL HEIGHTS, 7E05; 7E02; 7E07; 7E01 |
| Outside: Minnesota Ave Metro 4000 Minnesota Ave NE; Kenilworth Aquatic Gardens; Kenilworth Rec | EASTLAND GARDENS, 7F01; 7D01; 7D01 |
| Outside: Benning Library 3935 Benning Rd NE; 3939 Benning Rd NE, the Deanwood Heights Main Street address in a search listing | FORT DUPONT, 7F01 |
| **Hillcrest set** | |
| Hillcrest Rec 3100 Denver St SE | NAYLOR/HILLCREST, 7B05 |
| Francis Gregory Library 3660 Alabama Ave SE; Beers ES 3600 Alabama Ave SE; Randle Highlands ES 1650 30th St SE | NAYLOR/HILLCREST, 7B02 |
| Fairfax Village 3800 W St SE | NAYLOR/HILLCREST, 7B06 |
| Naylor Rd SE 2701–2841; Gainesville St SE 2804–2907; Stanton ES 2701 Naylor Rd SE | NAYLOR/HILLCREST, **8B02** |
| Naylor Rd SE 2760–3036; Gainesville St SE 3000–3319 | NAYLOR/HILLCREST, 7B05 |
| Garfield ES 2435 Alabama Ave SE | NAYLOR/HILLCREST, 8B05 |
| Outside: **Fort Dupont Park (coord)**; Dupont Park 3985 Massachusetts Ave SE | **TWINING**, 7B07 |
| Outside: **Fort Dupont Ice Arena 3779 Ely Pl SE** | **TWINING, 7F06** |
| Outside: Sousa MS 3650 Ely Pl SE | FORT DUPONT, 7F06 |
| Outside: Penn Branch corridor, 2800–3250 Pennsylvania Ave SE | TWINING, 7B04 |
| Outside: Orr ES; Kramer MS | TWINING, 8A01 |
| Outside: Fort Stanton Rec 1812 Erie St SE | HISTORIC ANACOSTIA, 8A04 |

**Things you may want to act on:**
- **The HPN names mislead on all three.** Congress Heights' own Metro station and THEARC sit in DOUGLASS. The arena, Cedar Hill and most of St. Elizabeths are not in CONGRESS HEIGHTS/SHIPLEY. Fort Dupont Park and the ice arena are in TWINING, not FORT DUPONT, which is really River Terrace, Benning and Greenway (84% Cluster 32).
- **Don't use the SAINT ELIZABETHS HPN whole.** It holds Anacostia Metro, Barry Farm and 87% of the Anacostia BID. The nine-SMD boundary keeps the east campus (8C03) and drops those. It also drops **St. Elizabeths West and DHS (8C01)**. 8C01 is 53% of ANC 8C by area, much of it Joint Base Anacostia-Bolling and Barry Farm, so I'd leave it out. West campus news still matches by name.
- **Bellevue isn't worth adding by HPN.** It's 7.39 km², but 36% is Cluster 45 (Potomac River) and 37% is Joint Base Anacostia-Bolling. Only 26% is the neighborhood cluster. The rules still catch "Bellevue Library" and similar as nearby items.
- **Naylor Gardens straddles 7B05 and 8B02**, which is why the Hillcrest set takes 8B02. I placed it by street ranges, not a mapped polygon, so that's an inference.
- **Skyland is unresolved.** `2300 Good Hope Rd` isn't in the address layer. Good Hope Road is now Marion Barry Avenue SE there, and `TERMS["anacostia"]` only knows the old name. 2300–2330 Marion Barry is TWINING 8A07 and 2365 is NAYLOR/HILLCREST 8B01. Neither SMD is in the recommended set, so assume Skyland is just outside. I didn't check its exact parcel.
- **I couldn't look up** Congress Heights Rec (100 Randle Pl SE, no match in the layer) or Benning Road Metro.

**Overlaps with live sites.** All tested HPN pairs against `HISTORIC ANACOSTIA`, `STADIUM ARMORY` and `KINGMAN PARK` intersect at 0.0000 km². The real overlaps are ANCs and news:
- Hillcrest's recommended set shares ANC 8B with Anacostia (`ANCS["anacostia"] = ["8A", "8B"]`). Congress Heights' set has no 8A or 8B. Deanwood's has no 7D or 7F.
- Any option with the FORT DUPONT HPN shares 7D with Kingman Park, and 7D and 7F with Stadium-Armory. Another reason to skip it.
- `TERMS["anacostia"]` has `ANC 8A`, and 8A06 is 11% of CH + St. E if you ever use those HPNs.
- **Unrelated to the candidates:** `FEEDS["anacostia"]` reads neither East of the River nor Congress Heights on the Rise, though SOURCES-EAST recommended the first. I didn't count them for Anacostia.

**Farmers markets in the existing layer** (`events.MARKETS`, tested with `events.market_dates` for today).

| Market | Point falls in | Layer schedule | Engine result, next 30 days |
|---|---|---|---|
| Ward 8 Farmers Market, 2724 MLK Ave SE | SAINT ELIZABETHS 8C03 (CH set) | Saturdays, "Junes" to October | Reads fine, season over |
| FRESHFARM THEARC, 1901 Mississippi Ave SE | DOUGLASS 8E05 (CH set) | Saturdays, June to November | Nov 7, 14, 21, 28 |
| FRESHFARM Simon Elementary, 401 Mississippi Ave SE | CONGRESS HEIGHTS/SHIPLEY 8C07 (CH set) | Thursdays, May to November | Nov 5, 12, 19, 26 |
| Arcadia at Oxon Run, Wheeler Rd and Valley Ave SE | WASHINGTON HIGHLANDS, no SMD on my point test (edge) | Thursdays, to 2026-11-19 | Nov 5, 12, 19. Test against the final polygon. |
| Arcadia at Bellevue Library, 115 Atlantic St SW | BELLEVUE 8D01 (outside) | Thursdays, to 2026-11-19 | Only with Bellevue |
| Dreaming Out Loud's Kelly Miller Market, 301 49th St NE | LINCOLN HEIGHTS 7C03 (Deanwood) | Saturdays, to 2026-11-21 | Nov 7, 14, 21 |
| UDC East Capitol, 5929 East Capitol St SE | MARSHALL HEIGHTS 7C08 (ANC 7C, so Deanwood) | Saturdays, May to November | Nov 7, 14, 21, 28 |
| FRESHFARM Minnesota Ave, 322 40th St NE | FORT DUPONT 7F01 (outside) | Thursdays, June to November | Not in any recommended set |
| none | Hillcrest | | **Hillcrest has no market.** |

### 0.2 Keyword rules (Python `re`; drop-in for `TERMS` and `NOT_HERE` in news.py)

Hillcrest is partly case-sensitive with scoped `(?i:…)` groups. It must not get `re.I`. These compile as written.

Two kinds of test, as in SOURCES-LATE. Real: every feed in this file, 1,761 distinct items. Synthetic: 81 strings I wrote, traps such as "Pride in Hillcrest, San Diego's gay neighborhood", "Man killed in Hillcrest Heights, Prince George's County", "Stabbing near Naylor Road Metro station in Temple Hills", "Fort DuPont, Delaware, state park opens", "Lincoln Heights, Ohio police chief quits", "Deanwood train station in Perth, Western Australia", "Congress passes spending bill on Capitol Hill", "Bellevue, Wash., council approves housing", "St. Elizabeth's Medical Center in Boston lays off staff". All 81 pass, which only proves the rules do what I intended.

**In real feeds the geographic rejects never fired.** NOT_HERE dropped only 5 of the 1,761 items, all real-estate listings or a PoPville "Fresh Finds" roundup. These are DC outlets. The rejects guard against wire copy I didn't see today. The one real out-of-town item was a Washingtonian piece on a priest in Hillcrest Heights, Md., which TERMS refused on its own. Bare "Deanwood" (29 items) and "Marshall Heights" (12) turned up nothing outside DC.

**TERMS:**
```python
"congressheights": re.compile(r"\bcongress\s+heights\b(?!\s+on\s+the\s+rise)|\bshipley\s+terrace\b|\b(st\.?|saint)\s+elizabeths?\s+(east|campus|hospital|west)\b|\bst\.?\s+e['\u2019]?s\s+(east|campus)\b|\b(st\.?|saint)\s+elizabeth['\u2019]?s\b(?=.{0,200}\b(d\.?c\.?|southeast|SE|ward\s*8|bowser|patients?|ICE)\b)|\bdc['\u2019]s\s+st\.?\s+elizabeth|\bentertainment\s+(and|&)\s+sports\s+arena\b|\bcedar\s+hill\s+(regional|urgent|hospital|medical)\b|\bballou\s+(high|senior|stay|sr)\b|\bmalcolm\s+x\s+(elementary|opportunity|avenue|ave)\b|\bsimon\s+elementary\b|\bhart\s+middle\b|\bhendley\s+elementary\b|\bfletcher[-\s]johnson\b|\boxon\s+run\b|\bparklands[-\s]turner\b|\bparklands\s+(library|community)\b|\bTHEARC\b|\bfort\s+greble\b|\bdestination\s+congress\s+heights\b|\bsoul\s+of\s+the\s+city\b|\bANC\s*8[CE]\b|\b8[CE]0[1-9]\b|\b(2[7-9]|3[0-7])\d\d\s+(martin\s+luther\s+king|MLK)(\s+jr\.?)?\s+(ave(nue)?)\.?,?\s+s\.?e\b|\b([4-9]\d\d|1[0-5]\d\d)\s+alabama\s+ave(nue)?\.?,?\s+s\.?e\b|\b\d{3,4}\s+mississippi\s+ave(nue)?\.?,?\s+s\.?e\b|\bwashington\s+highlands\b|\bbellevue\s+(community|library|neighborhood|anc)\b|\bbellevue\b(?=.{0,200}\b(d\.?c\.?|SW|SE|ward\s*8|southeast|southwest|ANC)\b)", re.I | re.S),
"deanwood": re.compile(r"\bdeanwood\b(?!\s+(road|rd|drive|dr|court|ct|lane|ln|way|park,?\s+(va|virginia)))|\bmarshall\s+heights\b|\bburrville\b|\bcapitol\s+view\s+(library|neighborhood)\b|\blincoln\s+heights\b(?=.{0,300}\b(d\.?c\.?|NE|northeast|ward\s*7|new\s+communities|richardson|washington|50th\s+st)\b)|\brichardson\s+dwellings\b|\beast\s+capitol\s+dwellings\b|\bnew\s+communities\b(?=.{0,200}\b(lincoln\s+heights|deanwood)\b)|\bnannie\s+helen\s+burroughs\b|\bmarvin\s+gaye\s+(park|recreation)\b|\bwatts\s+branch\b|\bstrand\s+theat(er|re)\b(?=.{0,200}\b(deanwood|NE|northeast|nannie|ward\s*7)\b)|\bron\s+brown\s+(college|high|prep|hs)\b|\b(h\.?\s?d\.?|h\s+d)\s+woodson\b|\bkelly\s+miller\s+(middle|ms|market|school)\b|\bdrew\s+elementary\b|\baiton\s+elementary\b|\bburrville\s+elementary\b|\bplummer\s+elementary\b|\bdavis\s+elementary\b(?=.{0,200}\b(d\.?c\.?|SE|ward\s*7)\b)|\bdeanwood\s+heights\b|\bANC\s*7[CE]\b|\b7[CE]0[1-9]\b|\bsheriff\s+r(oa)?d\.?,?\s+n\.?e\b|\b4[3-9]\d\d\s+minnesota\s+ave(nue)?\.?,?\s+n\.?e\b|\bdivision\s+ave(nue)?\.?,?\s+(n\.?e|s\.?e)\b|\b(4[4-9]|5\d|6[01])(th|st|nd|rd)\s+st(reet)?\.?,?\s+n\.?e\b|\b(4[6-9]|5\d)\d\d\s+(east\s+capitol\s+st(reet)?|benning\s+r(oa)?d|central\s+ave(nue)?)\b", re.I | re.S),
"hillcrest": re.compile(r"\b(?i:in|of|near|around)\s+Hillcrest\b(?!\s+[Hh]eights)(?=.{0,300}\b(?i:d\.?c\.?|SE|southeast|ward\s*7|washington|naylor|skyland|ANC)\b)|\bHillcrest\s+(?i:rec(reation)?(\s+center)?|community\s+civic|civic\s+association|day|children['\u2019]?s\s+center|neighborhood)\b(?=.{0,300}\b(?i:d\.?c\.?|SE|southeast|ward\s*7|washington|denver|naylor|ANC|civic)\b)|\bHillcrest\s+(?i:community\s+civic|civic\s+association)\b|\bHillcrest\s+(?i:rec(reation)?\s+center)\b|(?i:\bHillcrest\s+dr(ive)?\.?,?\s+s\.?e\b|\bward\s*7['\u2019]?s\s+hillcrest\b|\b(d\.?c\.?|southeast)['\u2019]?s?\s+hillcrest\b|\bnaylor\s+gardens\b|\bnaylor\s+r(oa)?d\.?,?\s+s\.?e\b|\b\d{4}\s+naylor\s+r(oa)?d\b|\bHillcrest\s+(indoor|aquatic|resident|neighborhood)|\bskyland\s+(town|workforce|shopping|development|walmart|plaza|center)\b|\bskyland\b(?=.{0,200}\b(d\.?c\.?|ward\s*7|ward\s*8|SE|southeast|bowser|gray)\b)|\bfairfax\s+village\b|\bsummit\s+park\b(?=.{0,200}\b(d\.?c\.?|SE|southeast|ward\s*7)\b)|\bpenn\s+branch\b|\brandle\s+highlands\b|\bfort\s+davis\b(?=.{0,200}\b(d\.?c\.?|SE|southeast|ward\s*7|rec)\b)|\bfrancis\s+a?\.?\s*gregory\b|\banne\s+beers\b|\bbeers\s+elementary\b|\bstanton\s+elementary\b|\bgarfield\s+elementary\b|\bANC\s*7B\b|\b7B0[1-9]\b|\b(2[5-9]|3\d)\d\d\s+pennsylvania\s+ave(nue)?\.?,?\s+s\.?e\b|\b(2[89]|3[0-7])\d\d\s+alabama\s+ave(nue)?\.?,?\s+s\.?e\b|\b\d{3,4}\s+branch\s+ave(nue)?\.?,?\s+s\.?e\b|\bfort\s+dupont\s+(park|ice|arena|summer)\b|\bfort\s+dupont\b(?=.{0,200}\b(d\.?c\.?|SE|southeast|ward\s*7|ice)\b))", re.S),
```

**NOT_HERE:**
```python
"congressheights": (re.compile(r"^\W*(?:(?:home|building)\s+)?(?:for\s+sale|short\s+sale|coming\s+soon|price\s+reduction|open\s+house)\b|^DC\s+Fresh\s+Finds\b|\bboston\b|\bbrighton\b|\byoungstown\b|\bdayton\b|\bdhs\s+headquarters\b(?!.{0,200}\bcongress\s+heights\b)|\bmount\s+st\.?\s+elizabeth|\bbellevue,?\s+(wash|washington|wa|neb|nebraska|ne|ky|kentucky|tenn|ohio|idaho|iowa)\b|\bseattle\b|\bking\s+county\b|\bbellevue\s+hospital\b|\bmanhattan\b|\bnew\s+york\b|\bvs\.?\s|\bpoints\b.{0,80}\brebounds\b|\bwashington\s+highlands?,?\s+(n\.?y|new\s+york)\b", re.I | re.S),
    re.compile(r"^(?!(?i:\W*(?:(?:home|building)\s+)?(?:for\s+sale|short\s+sale|coming\s+soon|price\s+reduction|open\s+house)\b|DC\s+Fresh\s+Finds\b)).*?(?:\bcongress\s+heights\b|\bANC\s*8[CE]\b|\bcedar\s+hill\s+regional\b|\b(st\.?|saint)\s+elizabeths\s+(east|campus)\b.{0,200}\b(ward\s*8|southeast|SE|bowser|ANC)\b)", re.I | re.S)),
"deanwood": (re.compile(r"^\W*(?:(?:home|building)\s+)?(?:for\s+sale|short\s+sale|coming\s+soon|price\s+reduction|open\s+house)\b|^DC\s+Fresh\s+Finds\b|\bdeanwood,?\s+(perth|western\s+australia|wa\b|oregon|portland|va\b|virginia|md\b|maryland)|\bperth\b|\baustralia\b|\bportland\b|\blincoln\s+heights,?\s+(ohio|los\s+angeles|l\.?a\.?|calif|n\.?c)\b|\bcincinnati\b|\blos\s+angeles\b|\bLAPD\b|\bmarshall\s+heights,?\s+(mo|tx|texas)\b", re.I),
    re.compile(r"^(?!(?i:\W*(?:(?:home|building)\s+)?(?:for\s+sale|short\s+sale|coming\s+soon|price\s+reduction|open\s+house)\b|DC\s+Fresh\s+Finds\b)).*?(?:\b(D\.?C\.?|NE|Northeast)\b|\b[Ww]ard\s*7\b|\bANC\s*7[CE]\b)", re.S)),
"hillcrest": (re.compile(r"^\W*(?:(?:home|building)\s+)?(?:for\s+sale|short\s+sale|coming\s+soon|price\s+reduction|open\s+house)\b|^DC\s+Fresh\s+Finds\b|\bnaylor\s+r(oa)?d\s+(metro|station)\b|\bhillcrest\s+heights\b|\bprince\s+george['\u2019]?s\b|\btemple\s+hills\b|\bsan\s+diego\b|\blos\s+angeles\b|\bhillcrest\s+(country\s+club|hospital|high\s+school|medical|elementary|baptist)\b|\btulsa\b|\bcleveland\b|\butah\b|\bdallas\b|\bfort\s+du\s?pont,?\s+(de|del|delaware)\b|\bdelaware\s+city\b|\bskyland,?\s+(n\.?c|north\s+carolina|va|virginia|shenandoah)\b|\bskyline\s+drive\b|\bshenandoah\b|\bsummit,?\s+n\.?j\b", re.I | re.S),
    re.compile(r"^(?!(?i:\W*(?:(?:home|building)\s+)?(?:for\s+sale|short\s+sale|coming\s+soon|price\s+reduction|open\s+house)\b|DC\s+Fresh\s+Finds\b)).*?(?:\bANC\s*7B\b|\bnaylor\s+(gardens|r(oa)?d)\b|\bHillcrest\s+(rec|civic|community\s+civic)|\b(D\.?C\.?|SE)\b(?!-area)|\b[Ww]ard\s*7\b|\bskyland\s+town\b)", re.S)),
```

**Congress Heights notes:**
- Never bare "Congress". `(?!\s+on\s+the\s+rise)` is essential: the blog's own name sits in its promo posts and cross-promotions. Without it, "Voting Now Open for The Washington Informer's Best of the DMV 2026" counts as neighborhood news. Same lesson as "Forest Hills Connection" in the engine.
- St. Elizabeths needs `East`, `campus`, `Hospital` or `West`, or a DC cue within 200 characters. Real test: `wtop.com/tag/st-elizabeths/feed/` went from 9/5/4 to 10/8/7 with the cue form. "DC protesters oppose St. Elizabeths development plans for ICE headquarters" stays.
- Accepted leaks, all seen in real feeds: "Job Seekers Drop-in Clinic at Bellevue Library" is outside. "SWEET CITY RIDE" (PoPville), "The fight against colorectal cancer" (WTOP) and "Deeply Invested In the Health of Our Neighbors" (Informer) mention a landmark in passing.
- `Entertainment & Sports Arena` could pull game notes. None reached these feeds today. The stat-line reject is tested only on my own string.

**Deanwood notes:**
- Marshall Heights terms are in even if the boundary stops at ANC 7C, because the page needs them.
- Lincoln Heights needs a DC cue within 300 characters, for Los Angeles and Ohio. Only 1 real item with that name turned up.
- Bare `Nannie Helen Burroughs` also catches history pieces about her ("A Legacy That Was Never Meant to Be History"). The avenue is the neighborhood's spine, so I took that trade.
- Never Grant Park, bare Kelly Miller, bare Ron Brown or bare Strand Theater.

**Hillcrest notes:**
- **Hillcrest Heights, Md. is next door and the main trap.** "In Hillcrest" fails without a cue.
- **Naylor Road is also a Green Line station in Temple Hills, Md.** The rule needs `SE` or a house number. WTOP's search for `naylor` returned 80 items since May, and none passed.
- **The Fort Dupont terms are outside the recommended boundary (TWINING).** I kept them because they supply most of the headlines. Delete the last two alternatives if that bothers you, and expect about 0.5 headlines a month.
- `Branch Ave SE`, `Pennsylvania Ave SE 2500–3999` and `Alabama Ave SE 2800–3799` reach Penn Branch and Fairfax Village by address.

**Real-estate rule, shared by all three.** Each reject starts with a listing pattern ("For Sale |", "Short Sale |", "Price Reduction |", "DC Fresh Finds"), and each rescue refuses to rescue them. Congress Heights on the Rise posted 46 listings in 60 days.

**Crime share.** I counted a headline as crime when its **title** hit my own list: shooting, stabbing, homicide, murder, robbery, carjacking, assault, arrest, indicted, sentenced, convicted, pleads guilty, suspect, armed, burglary, crime, charged, gun, police, MPD, violence, blotter. Quieter titles are missed.

**The low crime numbers reflect what the rules can see, not what happens in these places.** Congress Heights on the Rise reposts MPD and US Attorney releases, and 142 of its 447 posts in 60 days (32%) are crime-worded. Almost all say "in Southeast" or name a street with no neighborhood, such as "Fatal Shooting of Joshua Carter, 17, on Minnesota Avenue SE". Street-level rules would raise both the crime share and the counts. I left them out because they'd turn these pages into blotters.

**A note on names.** Those posts name people who've been arrested, with ages ("Ashley Ray, 27, Arrested for Atlantic Street Shooting"). Crime headlines stay unfiltered by your rule, but this source goes further than WTOP-style copy. I'd look at a few before turning it on. Your decision.

### 0.3 General feeds already in the engine, counted for the new areas (60 d b/s/t, all items in brackets when different)

| Feed | robots | items (dates) | CH | DW | HC |
|---|---|---|---|---|---|
| `https://www.popville.com/feed/` | allow | 20 (2026-10-30 to 2026-11-03) | 0 | 0 | 0 |
| `https://www.popville.com/feed/?paged=2` | allow | 20 (2026-10-29 to 2026-10-30) | 0 | 0 | 1/0/0 |
| `https://www.popville.com/feed/?paged=3` | allow | 20 (2026-10-27 to 2026-10-29) | 0 | 0 | 0 |
| `https://washingtoncitypaper.com/feed/` | allow | 10 (2026-10-29 to 2026-11-02) | 0 | 0 | 0 |
| `https://wtop.com/local/dc/feed/` | allow | 10 (2026-11-02 to 2026-11-03) | 0 | 0 | 0 |
| `https://wamu.org/feed/` | allow | 10 (2026-10-30 to 2026-11-02) | 0 | 0 | 0 |
| `https://51st.news/rss/` | allow | 15 (2026-10-21 to 2026-11-03) | 1/0/0 | 2/0/0 | 0 |
| `https://thedcline.org/feed/` | allow | 20 (2026-10-09 to 2026-11-02) | 0 | 0 | 0 |
| `https://mayor.dc.gov/rss.xml` | allow | 10 (2015-05-22 to 2026-04-10) | 0 (3/3/0) | 0 (3/3/0) | 0 (1/1/0) |
| `https://ddot.dc.gov/rss.xml` | allow | 10 (2026-08-05 to 2026-10-30) | 0 | 0 | 0 |
| `https://dpr.dc.gov/rss.xml` | allow | 10 (2015-05-22 to 2026-04-10) | 0 (1/1/0) | 0 (2/2/1) | 0 |
| `https://oanc.dc.gov/rss.xml` | allow | 10 (2026-10-13 to 2026-11-02) | 0 | 0 | 1/1/1 |

`https://ggwash.org/rss` **not fetched**, because of its documented 3000 s Crawl-delay. PoPville's three pages hold about a week, so its 0s are one sample.

**New outlet-wide sources, the ones that do the work:**

| Feed (exact URL) | robots | items | CH | DW | HC | Notes |
|---|---|---|---|---|---|---|
| **`https://www.congressheightsontherise.com/blog?format=rss`** (Squarespace) | allow | 20 per page; walked 23 pages with `&offset=`; 447 posts, 5 Sep to 2 Nov | 21/18 by post, **5 unique titles** | 5/1/1 | 4/0/0 | **About 7 posts a day, by far the busiest source east of the river, with Ward 7 and Ward 8 as its stated beat.** Mix by title: 137 crime-worded, 5 police blotters, 80 dated events ("Nov 7 \| …"), 46 listings, 23 job posts, 156 other. Mostly citywide reposts. It reposts items several times, and the engine's title dedupe handles that. The feed holds 3 days, fine for a nightly run. One-person blog, runs sponsored posts tagged `[SP]`, and polled readers in September about coming changes. `match` only. |
| **`https://eastoftheriverdcnews.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,excerpt,link`** | allow, **Crawl-delay 10** | About 1 post a day: 61 in 60 d, from a 100-item read | 4/4/3 | 0 | 0 | Capital Community News' Ward 7 and 8 paper. RSS `/feed/` gives 1 item, so use JSON. Over 180 days: CH 5, DW 2, HC 3. |
| `https://www.washingtoninformer.com/tag/ward-8/feed/` | allow | 10 (19 Aug – 28 Oct), 7 in 60 d | 1/1/0 | 0 | 0 | |
| `https://www.washingtoninformer.com/tag/ward-7/feed/` | allow | 10 (3 Jun – 16 Oct), 3 in 60 d | 0 | 0 | 1/1/0 | Via Fort DuPont. |
| `https://www.washingtoninformer.com/feed/` | allow | 10 (29 Oct – 2 Nov) | 0 | 0 | 0 | High volume, and geography rarely shows in the summary. |
| `https://mpdc.dc.gov/rss.xml` | allow | 10 (30 Oct – 3 Nov) | 0 | 1/1/1 | 0 | **Not recommended.** It's a crime feed by nature. |

**How I measured flow.** Search feeds show little that's recent, so I also asked WP JSON directly for 12 terms at East of the River, the Informer, The DC Line, WTOP, Washingtonian and PoPville, with `after=2026-05-07&per_page=100`. These calls were for measuring only, so don't put them in `FEEDS`. Totals are unique titles over everything fetched. Congress Heights on the Rise covers only 60 days, so 180-day totals undercount a little.

| Area | 60 d (crime) | 180 d (crime) | Expected headlines per month |
|---|---|---|---|
| Congress Heights | 13 (0) | 27 (1) | **5 to 7, moderate** |
| Deanwood + Marshall Heights | 2 (2, the same robbery from two outlets) | 7 (2) | **About 1, thin** |
| Hillcrest + Fort Dupont + Penn Branch | 3 (0) | 10 (0) | **About 1.7, thin** |

For comparison, words alone over 60 days across these feeds: "Ward 8" 31 unique headlines, "Ward 7" 18, "east of the river" 5. None were crime-worded.

---

## 1. Congress Heights (SMDs 8C02, 8C03, 8C04, 8C06, 8C07, 8C08, 8E03, 8E04, 8E05; ANC 8C ~68% + 8E ~32%)

### NEWS

| Feed (exact URL) | robots | items | 60 d hits | All hits | Notes |
|---|---|---|---|---|---|
| Congress Heights on the Rise (§0.3) | allow | 447 in 60 d | 21/18 by post | | 5 unique: "Sept 12 \| Congress Heights Day Parade", "Sept 26 \| ANC 8C07 Community Cleanup", "Ward 8's Malcolm X Elementary Celebrates $67 Million Transformation", "Sept 20 \| Bellevue Community to Come Together…", and the parade's traffic advisory. |
| East of the River (§0.3) | allow, delay 10 | 61 in 60 d | 4/4/3 | 5/5/4 | Best general source. "ANC 8C Wants A Say In Barry Farm's Redevelopment". |
| `https://www.washingtoninformer.com/tag/congress-heights/feed/` | allow | 10 (Jul 2024 – 30 Sep 2026) | 1/1/0 | 10/10/1 | Clean and slow. |
| `https://www.washingtoninformer.com/tag/ward-8/feed/` | allow | 10 | 1/1/0 | 1/1/0 | |
| `https://wtop.com/tag/congress-heights/feed/` | allow | 10 (Mar 2022 – 8 Jan 2026) | 0 | 10/10/1 | Slow, under 3 a year. |
| `https://wtop.com/tag/st-elizabeths/feed/` | allow | 10 (Jul 2019 – 3 Jan 2026) | 0 | 10/8/7 | |
| `https://wtop.com/tag/ballou-high-school/feed/` | allow | 10 (May 2018 – 20 May 2026) | 0 | 10/10/3 | |
| `https://thedcline.org/?s=congress+heights&feed=rss2&orderby=date&order=DESC` | allow | 20 (Aug 2022 – 10 Jun 2026) | 0 | 9/9/5 | Mostly "District Links" lists. `match`. |
| `https://thedcline.org/?s=st.+elizabeths&feed=rss2&orderby=date&order=DESC` | allow | 20 (Sep 2022 – Jul 2026) | 0 | 12/12/9 | |
| `https://anc8e.dc.gov/rss.xml` | allow | 10 (Jan 2026) | 0 | 10/10/9 | OANC site. 9 of 10 are meetings. See Events. |
| `https://chctdc.org/feed/` (now Prospering Places, `prosperingplaces.org`) | allow | 10 (Nov 2024 – 17 Sep 2026) | 0 | 7/5/2 | "Mayor Certifies Soul of the City Business Improvement District". Slow, and partly personal essays. |
| `https://buildingbridgesdc.org/feed/` | allow | 10 (Nov 2025 – 23 Sep 2026) | 0 | 2/1/1 | Mostly parks in other cities. Skip. |

Not usable:
- **afro.com: 403 on all 8 URLs** (`/feed/`, category, tags, `?s=`, WP JSON). robots.txt answers and allows, and the server (CloudFront) refuses the fetch. Recorded as blocked, not retried any other way.
- `washingtoninformer.com/?s=…&feed=rss2`: 200 with **0 items**. `/tag/st-elizabeths/feed/` is stale (Jun 2022).
- WTOP `entertainment-and-sports-arena`, `cedar-hill`, `cedar-hill-regional-medical-center`, `saint-elizabeths`, `st-elizabeths-east`, `bellevue`, `east-of-the-river`: 200 with 0 items. `thearc`: newest Aug 2023.
- `stelizabethseast.com/feed/`: all from 2014.
- **No own site found for** Soul of the City BID, Destination Congress Heights or Congress Heights Main Street. The domains I guessed have no DNS. The BID was certified in 2026, so re-check later.
- `thearcdc.org`: connection timed out, and `www.` failed the TLS handshake. `archdc.org` no DNS. I can't say whether either has a feed.

```python
"congressheights": [
    ("East of the River", "https://eastoftheriverdcnews.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,excerpt,link", "https://eastoftheriverdcnews.com/", "match"),  # Crawl-delay 10
    ("Congress Heights on the Rise", "https://www.congressheightsontherise.com/blog?format=rss", "https://www.congressheightsontherise.com/", "match"),  # never "all": about 7 posts a day, mostly citywide
    ("Washington Informer", "https://www.washingtoninformer.com/tag/congress-heights/feed/", "https://www.washingtoninformer.com/", "match"),
    ("Washington Informer", "https://www.washingtoninformer.com/tag/ward-8/feed/", "https://www.washingtoninformer.com/", "match"),
    ("WTOP", "https://wtop.com/tag/congress-heights/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/st-elizabeths/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/ballou-high-school/feed/", "https://wtop.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="congress+heights"), "https://thedcline.org/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="st.+elizabeths"), "https://thedcline.org/", "match"),
    ("ANC 8E", "https://anc8e.dc.gov/rss.xml", "https://anc8e.dc.gov/", "match"),
    ("Prospering Places", "https://chctdc.org/feed/", "https://prosperingplaces.org/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| FRESHFARM THEARC, Simon Farm Stand, Ward 8 Farmers Market | existing layer | Dated (§0.1). The first two run through November. |
| **Building Bridges Across the River** (THEARC) | `https://buildingbridgesdc.org/wp-json/tribe/events/v1/events` (`bbardc.org` redirects here) | **Works.** 14 events in the next 30 days with venue and address. 9 are volunteer shifts. The skip pattern below keeps 5: Food and Farm Fridays (2), 2026 Turkey Giveaway, a Garden Club session at Eightfold Farm (2315 Elvans Rd SE), East of the River Homebuyer Club. |
| **ANC 8E** | `https://anc8e.dc.gov/rss.xml` | **Dated in titles**: "December 7, 2026, ANC 8E In Person Public Meeting". 9 for 2026. `OANC_TITLE` doesn't match "In Person", and the engine reads only `oanc.dc.gov`. See below. |
| **ANC 8C** | `https://www.anc8c.org/calendar` (Squarespace) | Page has `<time datetime="2026-11-12">`, 6:30 PM. `?format=ical` is **robots-disallowed**. HTML only, so Links, unless you decide to scrape. `anc8c.dc.gov` no DNS. |
| Congress Heights on the Rise | `/events?format=rss` 404 | No calendar. But 80 of 447 posts open with a date. Parseable, no place field. It would be a new kind of source, so that's your call. 3 unique ones matched in 60 days. |
| Prospering Places | `prosperingplaces.org/wp-json/tribe/events/v1/events` | Plugin on, **0 events**. Re-check. |
| Entertainment & Sports Arena | `entertainmentandsportsarena.com` no DNS | I didn't look for its real domain. |
| OANC | `https://oanc.dc.gov/rss.xml` | None for 8C or 8E among today's 10. |

**`OANC_TITLE` misses real meetings, including today's only upcoming one for these ANCs.** "November 5, 2026, ANC 7B Special Meeting" fails because the regex needs `Public`, `Virtual` or `Regular` before "Meeting". That also affects live sites whenever OANC words it this way. In the 5 feeds I tested (OANC, 8A, 8B, 8D, 8E), the current regex matches 20 of 37 dated meeting titles. This one matches all 37 and loses none:
```python
OANC_TITLE = re.compile(r"^([A-Z][a-z]+ \d{1,2}, \d{4}),?\s+(?:ANC\s+)?([0-9/]+[A-Z])\s+(?:In[-\s]Person\s+)?(Special\s+)?(?:(?:Public|Virtual|Regular)\s+)?Meeting", re.I)
```
Reading the `anc8*.dc.gov` feeds for meetings would also need a small code change. `build_oanc` reads only `oanc.dc.gov`.

```python
TRIBE["bbar"] = ("Building Bridges Across the River", "https://buildingbridgesdc.org/wp-json/tribe/events/v1/events", "https://buildingbridgesdc.org/",
                 r"^volunteer\b|union\s+temple|hopkins\s+garden", 0)
CALENDARS["congressheights"] = ["bbar"]
ANCS["congressheights"] = ["8C", "8E"]
LINKS["congressheights"] = [
    {"name": "ANC 8C calendar", "url": "https://www.anc8c.org/calendar"},
    {"name": "ANC 8E", "url": "https://anc8e.dc.gov/"},
    {"name": "Parklands-Turner Library events", "url": "https://dclibrary.libnet.info/events?l=Parklands-Turner%20Neighborhood%20Library"},
    {"name": "Congress Heights on the Rise", "url": "https://www.congressheightsontherise.com/"},
]
```
Library location names follow DCPL's pattern and aren't confirmed.

---

## 2. Deanwood (ANC 7C; optional 7E for Marshall Heights)

### NEWS

| Feed (exact URL) | robots | items | 60 d hits | All hits | Notes |
|---|---|---|---|---|---|
| Congress Heights on the Rise (§0.3) | allow | 447 in 60 d | 5/1/1 | | "12-Year-Old Arrested for Nannie Helen Burroughs Robbery" is the only summary hit. |
| East of the River (§0.3) | allow, delay 10 | 61 in 60 d | 0 | 0 | 2 in 180 d: "NRP Group and Marshall Heights CDC Break Ground on Affordable Community", "Ward 7 Launches Cafe Concert Series". |
| `https://www.washingtoninformer.com/tag/deanwood/feed/` | allow | 7 (Feb 2019 – 3 Aug 2026) | 0 | 7/7/5 | "A Closer Look at the Restaurant Closure That Rocked Deanwood". Clean, about 1 a year. |
| `https://www.washingtoninformer.com/tag/ward-7/feed/` | allow | 10 | 0 | 0 | |
| `https://wtop.com/tag/deanwood/feed/` | allow | 8 (Oct 2013 – 25 Jan 2024) | 0 | 8/8/4 | **Stale.** Cheap to keep. |
| `https://wtop.com/tag/ward-7/feed/` | allow | 10 (Dec 2023 – 14 May 2026) | 0 | 1/0/0 | Rarely fires. |
| `https://thedcline.org/?s=deanwood&feed=rss2&orderby=date&order=DESC` | allow | 20 (Feb 2022 – 19 Jun 2026) | 0 | 3/3/2 | |
| `https://thedcline.org/?s=marshall+heights&feed=rss2&orderby=date&order=DESC` | allow | 20 (Apr 2021 – May 2024) | 0 | 3/3/0 | **Stale.** Skip. |
| `https://www.washingtonian.com/?s=deanwood&feed=rss2&orderby=date&order=DESC` | allow | 10 (Apr 2025 – 5 May 2026) | 0 | 9/1/0 | Body-only. Skip. |
| `https://www.hillrag.com/wp-json/wp/v2/posts?search=deanwood&after=2026-05-07T00:00:00&per_page=20&_fields=date,title,excerpt,link` | allow, Crawl-delay 20 | 5 | 0 | 0 | Skip. |
| `https://mhcdo.org/feed/` | allow | 10 (Mar 2021 – Jun 2022) | 0 | 4/1/0 | **Stale.** Marshall Heights Community Development Organization. |

Not usable:
- **`deanwoodcitizens.org` redirects to `mawartotoresmi.com`, a site unrelated to the association that looks like lottery spam. Do not link it.** `deanwoodcitizensassociation.org` no DNS. I found no association site. Its meetings show up in Congress Heights on the Rise posts.
- **`anc7c.org` is parked**: 114 bytes of script sending you to `/lander`, even though OANC documents give it as the commission's site. Do not link it. `anc7c.dc.gov`, `anc7e.dc.gov`, `anc7f.dc.gov` no DNS.
- `deanwoodheights.org`, `deanwoodheightsmainstreet.org`, `ward7bp.org`, `ward7arts.org`, `deanwoodhistory.org`: no DNS.
- WTOP `marshall-heights`, `lincoln-heights`: 200 with 0 items. `minnesota-avenue`: newest Oct 2022. `benning-road`: newest Nov 2025.
- `dcnewcommunities.org/feed/`: 200 with 0 items.

```python
"deanwood": [
    ("East of the River", "https://eastoftheriverdcnews.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,excerpt,link", "https://eastoftheriverdcnews.com/", "match"),  # Crawl-delay 10
    ("Congress Heights on the Rise", "https://www.congressheightsontherise.com/blog?format=rss", "https://www.congressheightsontherise.com/", "match"),
    ("Washington Informer", "https://www.washingtoninformer.com/tag/deanwood/feed/", "https://www.washingtoninformer.com/", "match"),
    ("Washington Informer", "https://www.washingtoninformer.com/tag/ward-7/feed/", "https://www.washingtoninformer.com/", "match"),
    ("WTOP", "https://wtop.com/tag/deanwood/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/ward-7/feed/", "https://wtop.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="deanwood"), "https://thedcline.org/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| Kelly Miller Market, UDC East Capitol | existing layer | Dated (§0.1). |
| Dreaming Out Loud | `dolgrocery.org/events?format=ical` **robots-disallowed**; `?format=rss` 404 | No. |
| Marshall Heights CDO | `mhcdo.org/wp-json/tribe/events/v1/events` | Plugin on, **0 events**. |
| ANC 7C | No feed, no live site found | OANC only. None in today's 10 items. A search listing shows meetings at Deanwood Rec. |
| ANC 7E | `anc7e.us` (GoDaddy builder), `/feed/` and Tribe 404, has a `/public-meetings-1` link I didn't read | Link only. |

```python
ANCS["deanwood"] = ["7C"]  # add "7E" if the boundary takes Marshall Heights
LINKS["deanwood"] = [
    {"name": "Deanwood Library events", "url": "https://dclibrary.libnet.info/events?l=Deanwood%20Neighborhood%20Library"},
    {"name": "Capitol View Library events", "url": "https://dclibrary.libnet.info/events?l=Capitol%20View%20Neighborhood%20Library"},
    {"name": "DC Office of ANCs calendar (ANC 7C)", "url": "https://oanc.dc.gov/"},
    {"name": "ANC 7E public meetings", "url": "https://anc7e.us/public-meetings-1"},
]
```
No calendar and no reliable civic source. Library location names are unconfirmed.

---

## 3. Hillcrest (SMDs 7B02, 7B03, 7B05, 7B06, 8B02, 8B05; ANC 7B ~82% + 8B ~18%)

### NEWS

| Feed (exact URL) | robots | items | 60 d hits | All hits | Notes |
|---|---|---|---|---|---|
| Congress Heights on the Rise (§0.3) | allow | 447 in 60 d | 4/0/0 | | Nothing in summaries once listings are out. |
| East of the River (§0.3) | allow, delay 10 | 61 in 60 d | 0 | 3 in 180 d | "Attend the Hillcrest Indoor Aquatic Center Community Meeting", "Ribbon Cut on New Community Park at Skyland Town Center", "Become a Volunteer Rink Guard at Fort Dupont Ice Arena". |
| `https://oanc.dc.gov/rss.xml` | allow | 10 | 1/1/1 | | "November 5, 2026, ANC 7B Special Meeting". Better as an event. |
| `https://www.washingtoninformer.com/tag/ward-7/feed/` | allow | 10 (3 in 60 d) | 1/1/0 | | Via Fort DuPont. |
| `https://wtop.com/tag/hillcrest/feed/` | allow | 3 (Jun 2017 – Sep 2022) | 0 | 3/2/1 | **Stale.** |
| `https://www.washingtoninformer.com/tag/hillcrest/feed/` | allow | 1 (Jun 2024) | 0 | 1/1/1 | **Stale.** Skip. |
| `https://thedcline.org/?s=skyland&feed=rss2&orderby=date&order=DESC` | allow | 20 (Sep 2021 – Jul 2024) | 0 | 9/9/3 | **Stale.** Skip. |
| `https://thedcline.org/?s=hillcrest&feed=rss2&orderby=date&order=DESC` | allow | 20 (Jan 2020 – Jun 2024) | 0 | 1/1/0 | Skip. |
| `https://www.nps.gov/feeds/getNewsRSS.htm?id=fodu` | allow | 31 (Sep 2012 – Aug 2025) | 0 | 20/20/14 | Newest is 15 months old. Outside the boundary. |
| `http://www.hillcrestdc.com/feed/` | allow | 10, **all dated 27 Jan 2023** | 0 | 10/3/0 | HCCA's "Hillcrest Heartbeat" newsletter. **Stale.** |
| WP JSON flow, 180 d | | | | | WTOP 2, PoPville 3, Informer 1, all via Fort Dupont. |

Not usable:
- `www.hillcrestdc.com` over **https fails certificate verification**. Plain http answers. Search results offered a third-party mirror, and I did not use it. The home page says HCCA meets the first Saturday, 10:00 a.m. to 1:00 p.m., Zoom registration. No calendar.
- `anc7b.com/feed/`: 1 item, from 2019. Its agenda page was last modified in 2020 (per WP JSON). `anc7b.dc.gov` no DNS.
- WTOP `fort-dupont`, `naylor-gardens`, `penn-branch`, `skyland`: 200 with 0 items.
- `fdia.org` redirects to `kidsonicedc.org`. `/feed/` is stale (Oct 2022).

```python
"hillcrest": [
    ("East of the River", "https://eastoftheriverdcnews.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,excerpt,link", "https://eastoftheriverdcnews.com/", "match"),  # Crawl-delay 10
    ("Congress Heights on the Rise", "https://www.congressheightsontherise.com/blog?format=rss", "https://www.congressheightsontherise.com/", "match"),
    ("Washington Informer", "https://www.washingtoninformer.com/tag/ward-7/feed/", "https://www.washingtoninformer.com/", "match"),
    ("WTOP", "https://wtop.com/tag/hillcrest/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/ward-7/feed/", "https://wtop.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| Farmers markets | existing layer | **None inside.** |
| ANC 7B | `anc7b.com/wp-json/tribe/events/v1/events` | Plugin on, **0 events**. OANC carries special meetings: needs the regex fix in §1. |
| ANC 8B | `https://anc8b.dc.gov/rss.xml` | Dated titles: Nov 17 and Dec 15, 2026, both "In Person Public Meeting". Needs the same fix, plus reading this feed. |
| HCCA | No feed | First Saturday, per its home page. I wouldn't compute dates from that. |
| Fort Dupont Ice Arena | `kidsonicedc.org` Tribe 404 | No. |
| DPR | `dpr.dc.gov/events` HTML; `dpr.dc.gov/rss.xml` newest Apr 2026 | No calendar feed. |
| calendar.dc.gov | `/rss.xml` holds items from 2016 to 2019; `/events` is HTML | No. |

```python
ANCS["hillcrest"] = ["7B", "8B"]
LINKS["hillcrest"] = [
    {"name": "Francis A. Gregory Library events", "url": "https://dclibrary.libnet.info/events?l=Francis%20A.%20Gregory%20Neighborhood%20Library"},
    {"name": "Hillcrest Community Civic Association", "url": "http://www.hillcrestdc.com/"},
    {"name": "ANC 7B", "url": "https://anc7b.com/"},
    {"name": "ANC 8B", "url": "https://anc8b.dc.gov/"},
]
```
The HCCA link is plain http because of the certificate problem. Library location names are unconfirmed. Events would be just the occasional ANC meeting.

---

## 4. HISTORY (Evening Star, loc.gov, week 1926-10-31 → 11-06)

loc.gov answered our UA, at about 30 s a search and once 161 s. I ran 11 terms through the engine's `history.build_archive` with `ARCHIVE` patched in memory, then 11 follow-up searches, and read the OCR of 6 more pages. No project file changed.

| Area | Clips (max 6) | Screened | Page failures |
|---|---|---|---|
| Congress Heights | 3, then 2 once the leak below is fixed | 0 | 0 |
| Deanwood | 0 | 0 | 2 pages would not load, read later: both snippets fail the legibility filter |
| Hillcrest | 0 | 0 | 4 pages would not load, 4 read later: none about this Hillcrest |

**This is one week, and it isn't enough to judge an area.** Year counts say more:

| Term | Pages in 1926 | Pages this week |
|---|---|---|
| `"Congress Heights"` | 388 | **0 quoted, 3 unquoted** |
| `"Randle Highlands"` | 151 | 0 |
| `"Hillcrest"` | 128 | 3 |
| `"Deanwood"` | 96 | 2 |
| `"Suburban Gardens"` | 17 | 0 |
| `"St. Elizabeth's"` | not counted | 5 |
| `"Nichols avenue"` | not counted | 0 |
| `"Burrville"` | not counted | 1, then 0 on a second try |
| `"Naylor road"` | not counted | 1 |
| `"Lincoln Heights"`, `"Fort Dupont"` | not counted | 0 |

**A pitfall for the whole project, flagged rather than proven.** Quoted `"Congress Heights"` returned 0 pages for this week, twice. Yet a page the `"St. Elizabeth's"` search found has "one in Congress Heights" and "Nichols avenue, Anacostia" in its OCR, and `"Nichols avenue"` also returned 0. Unquoted `Congress Heights` returned 3. So a quoted-phrase zero on loc.gov may not mean the phrase is absent. I don't know why, and it may be OCR line breaks. SOURCES-LATE's "0 pages this week" notes used the same kind of search, so they may be weaker than they read.

**Pitfalls for these areas:**
1. **"Hillcrest" in 1926 is mostly the wrong place.** On 31 Oct, the Star's "Hillcrest" is the Washington City Orphan Asylum's new home near Mount Vernon Seminary. Another is a rooming house on 16th St NW. An ad selling lots in Hillcrest may be the Southeast subdivision, but the snippet doesn't say. The pattern needs a Southeast cue and the reject names the orphan asylum.
2. **"Randle Highlands" looks like the right 1926 name for this area**, at 151 pages for the year, though 0 this week. It goes first.
3. **St. Elizabeth's is partly death notices.** My first draft let through a death notice naming a private person, because `years old` didn't catch "55 years,". The reject below fixes that. I checked it with a regex test on the three clips, not a second engine run.
4. **Screening.** 0 clips screened this week, but I expect it to matter most for Deanwood. Deanwood was a largely Black community in 1926 and Suburban Gardens a Black-owned amusement park. That's my background knowledge, not from this research. SOURCES-LATE found the Star writing about Ivy City in terms the screen blocks. Expect Deanwood's coverage to be sparse and often screened. It needs an editor's context, which a regex can't supply.
5. **Death lists.** "Naylor road" this week is one line in a list of children's deaths, caught only on legibility. The reject now covers `years old`.

Term order puts the most reliable first, since the 110 s budget can run out. **I did not run unquoted `Congress Heights` through `build_archive`.** It took 161 s in one search, which alone could exhaust the budget, so run `prefetch_archive.py` outside the nightly window.

```python
"congressheights": {
    # In 1926 this is the subdivision and the government hospital. Nichols avenue is now MLK Ave.
    "terms": ['"St. Elizabeth\'s"', "Congress Heights", '"Nichols avenue"'],
    "pattern": r"congress\s+heights|st\.?\s+elizabeth.?s\s+(hospital|asylum|grounds)?|\b(2[7-9]|3\d)\d\d\s+nichols\s+av|shepherd\s+park(way)?\b(?=.{0,120}(s\.\s?e|s\.\s?w|nichols|bellevue))",
    "reject": r"interment|inter\s+ment|funeral|deaths?\s+reported|\b\d+\s+years(\s+old)?\b|patient|insane|n\.\s?j\.|new\s+jersey|convent\s+station|ohio|boston|massachusetts|foot\s*ball|eleven|gridiron|touchdown",
    "local": r"nichols\s+av|alabama\s+av|s\.\s?e\.|southeast|congress\s+heights|anacostia|citizens|randle|portland\s+st|fourth\s+st",
},
"deanwood": {
    # Deanwood and Suburban Gardens coverage is sparse in the 1926 Star, and the screen will hold back some of what exists.
    "terms": ["Deanwood", '"Suburban Gardens"', '"Burrville"', '"Lincoln Heights"'],
    "pattern": r"deanwood|burrville|suburban\s+gardens|lincoln\s+heights(?=.{0,200}(n\.\s?e|northeast|deanwood|benning|d\.\s?c))|marshall\s+heights|sheriff\s+road",
    "reject": r"ohio|cincinnati|los\s+angeles|california|interment|funeral|years\s+old|foot\s*ball|eleven|gridiron",
    "local": r"n\.\s?e\.|northeast|benning|deanwood|sheriff\s+road|kenilworth|division\s+av|citizens|suburban\s+gardens",
},
"hillcrest": {
    # Randle Highlands is the 1926 name. "Hillcrest" alone is usually the Washington City Orphan Asylum in Northwest.
    "terms": ['"Randle Highlands"', '"Naylor road"', '"Hillcrest"'],
    "pattern": r"randle\s+highlands|naylor\s+r(oa)?d|fort\s+du\s?pont(?!,?\s+del)|hillcrest\s+(citizens|section)|hillcrest(?=.{0,200}(s\.\s?e|southeast|naylor|good\s+hope|randle|pennsylvania\s+av))",
    "reject": r"\bdel\.|delaware|interment|funeral|years\s+old|orphan|asylum|seminary|n\.\s?w\.|hillcrest,?\s+(n\.\s?y|pa\.|va\.|calif)|hillcrest\s+(farm|stable|kennels|school)|foot\s*ball|eleven|gridiron",
    "local": r"s\.\s?e\.|southeast|pennsylvania\s+av|good\s+hope|naylor|randle|alabama\s+av|citizens",
},
```
These final entries compile but weren't all rerun: the Congress Heights term order and reject, and the Hillcrest pattern, term order and reject, changed after the engine run. Congress Heights' real clips were a Commissioners' item on the District's deficiency appropriation for St. Elizabeth's and a piece on the hospital's 803 acres, one parcel in Congress Heights. It should work most weeks. Expect empty weeks for Deanwood (about 2 pages a week) and for Hillcrest, where Randle Highlands hasn't produced a clip for me yet.

---

## 5. Verdicts

**Congress Heights: yes.** About 5 to 7 matched headlines a month, moderate, with real local institutions: Cedar Hill, the arena, THEARC, Ballou, the ANCs. It has events through the Building Bridges calendar and two or three markets, and the 1926 archive works. Crime share by title is low (0 of 13 in 60 days, 1 of 27 in 180), but read the caveat in §0.2. Risks: 3 of the 13 are passing mentions, and two sources (East of the River, Congress Heights on the Rise) supply 9 of them. The second is one person's blog. Best boundary: the nine SMDs, 4.40 km². They keep the Metro, THEARC and the east campus and stay out of Anacostia.

**Deanwood: no, not as a news-first site.** About 1 headline a month even counting Marshall Heights and Nannie Helen Burroughs Avenue. The last 60 days hold one story, a robbery, from two outlets. Under your rule that crime never leads, the home page would have nothing to lead with. It has two markets but no calendar, no live ANC site and a dead civic domain. Its history needs a person, and your model is no moderation. Best boundary if you go ahead: ANC 7C, 4.32 km².

**Hillcrest: no, also not as a news-first site.** About 1.7 headlines a month, and 7 of those 10 in 180 days are about Fort Dupont, outside any sensible Hillcrest line. Inside the line it's closer to one every two months. No market, no calendar, a stale civic feed. Best boundary if you go ahead: the six SMDs, 3.16 km². ANC 7B + 8B02, 8B05 (7.81 km²) takes in Fort Dupont Park and Penn Branch, but no longer means Hillcrest.

**An option you didn't ask about.** A single Ward 7 site might hold more than these two neighborhoods combined: "Ward 7" alone gives about 9 headlines a month, from a word count I didn't run through NOT_HERE. It breaks the one-neighborhood pattern and I haven't sized it, so treat it as a question.

**What would change my mind:** the 180-day counts undercount somewhat, since Congress Heights on the Rise covers only 60 of those days, and GGW and the Afro aren't counted. A few weeks of a nightly archive would show the true rate. Even double the rate would still be thin.

---

## 6. Not verified / excluded

- **Blocked (403 to our UA):** `afro.com`, all 8 URLs, robots.txt allowed and CloudFront refused. Not retried another way.
- **Robots-disallowed for our agent (none fetched):** `dolgrocery.org/events?format=ical`, `anc8c.org/calendar?format=ical`, `anc8c.org/calendar/november-public-meeting?format=ical`.
- **Not fetched because of the crawl delay:** `ggwash.org`.
- **Crawl-delays recorded:** `eastoftheriverdcnews.com` 10, `anc8d.org` 10, `www.hillrag.com` 20.
- **Connection or TLS failures, not retried with anything else:** `thearcdc.org` (timeout), `www.thearcdc.org` (TLS handshake), `https://www.hillcrestdc.com` (certificate; plain http was used, same client and agent).
- **No DNS:** `anc7b.dc.gov`, `anc7c.dc.gov`, `anc7e.dc.gov`, `anc7f.dc.gov`, `anc8c.dc.gov`, `anc8e.org`, `anc8e.com`, `archdc.org`, `congressheightsmainstreet.org`, `congressheightspartnership.org`, `deanwoodcitizensassociation.org`, `deanwoodheights.org`, `deanwoodheightsmainstreet.org`, `deanwoodhistory.org`, `destinationcongressheights.org`, `destinationcongressheights.com`, `entertainmentandsportsarena.com`, `fosterdc.org`, `soulofthecitybid.org`, `soulofthecitybid.com`, `ward7arts.org`, `ward7bp.org`. Most are my guesses at domains, so no DNS doesn't show an organization has no site.
- **Hijacked or parked, do not link:** `deanwoodcitizens.org`, `anc7c.org`.
- **Empty feeds (200, 0 items):** `ward8woods.org/feed/`, `anc8d.org/feed/`, `dcnewcommunities.org/feed/`, Informer `?s=` feeds, and the WTOP tags listed above. `ward8woods.org` and `ward8farmersmarket.org` Tribe 404.
- **PoPville `?s=…&feed=rss2` redirects to a Google search.** My script followed that redirect three times before I saw it, so three requests carrying our UA went to google.com. I threw out those bodies. Don't use that URL form. PoPville's WP JSON search works, and I used it for measuring.
- **Discovery used a web search tool** for candidate domains (`anc7b.com`, `anc7c.org`, `anc7e.us`, `chctdc.org`, `hillcrestdc.com`, `congressheightsontherise.com`, the BID's certification). The search tool doesn't use our agent. Every site I then tested got our agent and a robots check.
- **Not tested at all:** Washington Post, Street Sense, UrbanTurf (`urbanturf.com/feed/` redirected to an HTML home page), Anacostia Community Museum, the arena's real site, Events DC, DPR rec center pages, DCPL location names, `anc7e.us/public-meetings-1`, GGW tags. WUSA9, Fox 5 and DC News Now got one read each, with 0 hits.
- **Shallow samples:** `washingtoninformer.com/feed/` and `popville.com/feed/` hold days, not months, so their 0s are one sample. East of the River's flow comes from `per_page=100`. I only checked that the `per_page=20` URL answers.
- **Engine changes these recommendations assume** (not made):
  1. The wider `OANC_TITLE` in §1. It would help live sites today.
  2. Reading ANC feeds on `anc8*.dc.gov` for meetings, if you want them.
  3. `TERMS["anacostia"]` learning Marion Barry Avenue.
  4. A dated-title parser for Congress Heights on the Rise, if you want that kind of source at all.

---

## Summary

| Area | Verdict | News per month | Crime share of matched headlines | Best boundary |
|---|---|---|---|---|
| Congress Heights | **Viable** | 5 to 7, moderate | 0 of 13 (60 d), 1 of 27 (180 d) | SMDs 8C02, 8C03, 8C04, 8C06, 8C07, 8C08, 8E03, 8E04, 8E05 (4.40 km²) |
| Deanwood | **Not viable as news-first** | About 1, thin | 2 of 2 (one robbery, two outlets), 2 of 7 (180 d) | ANC 7C (4.32 km²); HPN `LINCOLN HEIGHTS` holds Deanwood |
| Hillcrest | **Not viable as news-first** | About 1.7, thin; about 0.5 inside the boundary | 0 of 3, 0 of 10 | SMDs 7B02, 7B03, 7B05, 7B06, 8B02, 8B05 (3.16 km²) |

**Blocked:** afro.com (403 on all 8 URLs). Robots-disallowed: Squarespace ical at `dolgrocery.org` and `anc8c.org`. Unreachable: `thearcdc.org`; https on `hillcrestdc.com`. GGW wasn't fetched because of its delay. No loc.gov or other site blocked our agent otherwise.

**Uncertainty to keep in mind:**
- The crime shares are low partly because crime posts name streets or "Southeast", not neighborhoods. Congress Heights on the Rise is 32% crime-worded overall.
- The geographic rejects never fired on real feeds, so only my synthetic tests back them.
- The 1926 week is one sample. loc.gov failed to load 6 pages in the engine run, and quoted-phrase zeros there look unreliable.
- The final ARCHIVE edits weren't rerun through the engine.
- Naylor Gardens and Skyland placement is inferred from address ranges.

**Report path:** not written. Intended path `C:\Users\ericn\source\repos\DCNeighborhoods\ingest\SOURCES-NEXT-EAST.md`. The Write tool refused the report file, so the content above needs saving by you or the lead session.