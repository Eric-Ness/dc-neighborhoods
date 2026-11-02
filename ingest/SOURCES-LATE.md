# Sources for Bloomingdale, Foggy Bottom, Hill East, Kingman Park, Mount Pleasant, Stadium-Armory, Trinidad and Woodley Park (DC)

Tested 2026-11-02. Every feed and calendar fetch used the user agent `dc-neighborhoods-ingest/0.1 (+https://petworth.org)`. I checked robots.txt with the engine's own matcher (`news.parse_robots` / `news.allowed`, agent `dc-neighborhoods-ingest`) on the exact URL, query string included. Each host got at least 2 s between requests, and more where a Crawl-delay asked for it (Hill Rag 20 s, Historic Mount Pleasant 20 s, ANC 6B 10 s, Glover Park Main Street 10 s, GW Hatchet 6 s). Hit counts run over the newest ≤20 items and read **body / summary / title**, as in SOURCES-CENTRAL: "summary" is what `match` mode sees in `news.parse_feed(body=False)`. Counts apply TERMS and NOT_HERE together. Regexes are in §0.2.

Slugs are the ones already in `neighborhoods.json`: `bloomingdale`, `foggybottom`, `hilleast`, `kingmanpark`, `mountpleasant`, `stadiumarmory`, `trinidad`, `woodleypark`.

Woodley Park changed mid-research: the lead moved it from the HPN to SMDs 3C01, 3C02, 3C03 and 3C07. Everything below uses the SMD boundary for Woodley Park. No jobs section, as asked.

## 0. Cross-cutting findings

### 0.1 Geography (DC GIS: HPN `Health_WebMercator/MapServer/13`, SMD-2023 `Administrative_Other_Boundaries_WebMercator/MapServer/55`, BID `Business_Betterment_Areas_WebMercator/MapServer/15`, Main Streets `…/MapServer/16`, address points `Location_WebMercator/MapServer/0`). The address field is now `ADDRESS`, not `FULLADDRESS` as SOURCES-CENTRAL says; a `FULLADDRESS` query returns a 400. Shares come from a 70×70 grid sample. "Centroid SMDs" uses the rule in `run.py` / `setup_hood.py`.

| Site | Boundary | ~km² | Centroid SMDs | SMDs by area | ANCs by area | BIDs / Main Streets inside |
|---|---|---|---|---|---|---|
| Bloomingdale | HPN `BLOOMINGDALE` | 2.04 | 5E01–5E06, 5F04, 5F07 | 5E06 18%, 5F07 15%, 5E05 15%, 5E01 13%, 5F04 10%, 5E02 10%, 5E04 8%, 5E03 7%, 5F05 3% | 5E 71%, 5F 29% | North Capitol Main Street polygon is 87% here. NoMa BID 5% here. |
| Foggy Bottom | HPN `GWU` | 2.01 | 2A03, 2A05, 2A08, 2A09, 2B05, 2C02 | 2C02 23%, 2A07 14%, 2A01 14%, 2A04 12%, 2A08 9%, 2B05 8%, 2A03 5%, 2A09 5%, 2A05 4%, 2A06 3%, 2B06 2% | 2A 66%, 2C 23%, 2B 11% | **Golden Triangle BID is 99% here** and covers 37% of the HPN. Foggy Bottom-West End Main Street polygon is 63% here. |
| Hill East | HPN `HILL EAST` | 1.67 | 6B07, 6B08, 7D09, 7D10 | 6B08 36%, 6B07 16%, 6B09 14%, 7D09 13%, 7D10 12%, 6B04 5%, 7D08 2% | 6B 72%, 7D 27%, 8A 1% | Navy Yard BID 13% of the HPN, Capitol Hill BID 11%. |
| Kingman Park | HPN `KINGMAN PARK` | 1.82 | 6A04–6A07, 7D06–7D08 | 7D08 18%, 7D05 13%, 6A04 13%, 6A05 12%, 7D06 11%, 7D07 10%, 6A07 10%, 6A06 9%, 6A03 4%, 6B06 1% | 7D 52%, 6A 47%, 6B 1% | H St NE Main Street polygon 11% here. |
| Mount Pleasant | HPN `MOUNT PLEASANT` | 0.94 | 1D01–1D06 | 1D03 30%, 1D01 24%, 1D05 22%, 1D06 8%, 1D04 8%, 1D02 7% | 1D 99%, 1C 1% | Columbia Heights and Mt. Pleasant Main Street polygon 18% here. |
| Stadium-Armory | HPN `STADIUM ARMORY` | 2.01 | 6B09, 7D05, 7F08 | 7D05 44%, 7F07 22%, 6B09 18%, 7F08 11%, 7D04 3% | 7D 47%, 7F 34%, 6B 18%, 7B 1% | None. |
| Trinidad | HPN `TRINIDAD` | 3.16 | 5D01–5D08 | 5D01 24%, 5C04 15%, 5D02 12%, 5D09 9%, 5D07 8%, 5D05 8%, 5D03 7%, 5D06 6%, 5D04 5%, 5D08 5% | 5D 85%, 5C 15% | H St NE polygon 18% here, Bladensburg Road 5%. |
| Woodley Park | SMDs 3C01 (0.18), 3C02 (0.13), 3C03 (0.61), 3C07 (1.45) | 2.37 | as given | same | 3C only | **Woodley Park Main Street polygon is 100% inside.** The four SMDs are 99% HPN WOODLEY PARK. |

The 2023 lines moved things from where the old numbering would put them. Kingman Park is half Ward 7 (7D). Hill East is split between 6B and 7D. "5C" here means 5C04, which is Mount Olivet Cemetery and little else. Every ANC below comes from geometry.

**Landmarks, address points checked against both layers.** Points marked (coord) are my own approximate coordinates, so treat them as near-certain only away from an edge.

| Area | Inside | Outside, and where it actually is |
|---|---|---|
| Bloomingdale | Big Bear 1700 1st St NW (5E03), Boundary Stone 116 Rhode Island Ave NW (5E03), Dunbar HS 101 N St NW and Friendship Armstrong 111 O St NW (5E01), McMillan 2501 North Capitol St NE (5E06), Crispus Attucks Park (coord, 5E03), **Eckington:** Harry Thomas Rec 1743 Lincoln Rd NE, McKinley Tech 151 T St NE, Langley ES 101 T St NE (all 5F07), **Truxton Circle** (coord, 5E01) | LeDroit Park 400 U St NW (1B01, U ST/PLEASANT), Howard University Hospital (1B01), Rhode Island Ave Metro (coord, 5C05, BRENTWOOD) |
| Foggy Bottom | Watergate 2650 Virginia Ave NW (2A04), GW Hospital 900 23rd St NW (2A09), Foggy Bottom Metro (coord, 2A09), GWU Kogan Plaza (coord, 2A07), World Bank 1818 H St NW (2A07), 1800 K St NW and 1100 Connecticut Ave NW (2C02), 1250 Connecticut Ave NW (2B05) | **Kennedy Center 2700 F St NW and State Department 2201 C St NW: NATIONAL MALL.** White House: NATIONAL MALL. **West End: West End Library 2301 L St NW, Stevens School 2425 N St NW, Ritz 1150 22nd St NW and Trader Joe's 1101 25th St NW are all GEORGETOWN EAST.** Washington Circle (coord) also lands in GEORGETOWN EAST. |
| Hill East | Payne ES 1445 C St SE, Watkins 420 12th St SE (6B07), Jenkins Row 1391 Pennsylvania Ave SE, 700 14th St SE and Potomac Ave Metro (coord) (6B09), 1500 Massachusetts Ave SE (7D09) | Congressional Cemetery, Reservation 13 and the DC Jail: STADIUM ARMORY. Eastern HS 1700 East Capitol St NE, Eliot-Hine 1830 Constitution Ave NE (7D08) and Maury ES 1250 Constitution Ave NE (6A04): **KINGMAN PARK**. Southeast Library 403 7th St SE: CAPITOL HILL. |
| Kingman Park | Miner ES 601 15th St NE (7D06), Rosedale Rec 1701 Gales St NE (7D06), Eastern HS, Eliot-Hine, Maury, RFK Open Air Market 2615 Benning Rd NE (market layer, 7D05) | **Langston Golf Course: FORT LINCOLN/GATEWAY** (5D09). Spingarn 2500 Benning Rd NE, Browne 850 26th St NE, Langston Terrace 2101 G St NE: **TRINIDAD** (5D09). Kingman Island: see below. |
| Mount Pleasant | Library 3160 16th St NW (1D04), 3100 Mount Pleasant St NW (1D04), Bancroft 1755 Newton St NW (1D03), Rosemount Center 2000 Rosemount Ave NW (1D03), Lamont plaza (coord, 1D04) | Bell Multicultural 3101 16th St NW and 3149 16th St NW: west-side blocks of 16th are 1A05, COLUMBIA HEIGHTS. |
| Stadium-Armory | RFK Stadium (coord, 7D05), Armory 2001 East Capitol St SE (7D05), Congressional Cemetery 1801 E St SE (6B09), Reservation 13 1900 Massachusetts Ave SE (7F07), DC Jail 1901 D St SE (7F08), Stadium-Armory Metro (coord, 7F07), Heritage Island (coord, 7D05), 575 Oklahoma Ave NE (7D05) | Potomac Ave Metro: HILL EAST. |
| Trinidad | Union Market 1309 5th St NE and Gallaudet 800 Florida Ave NE (5D01), Hecht 1401 New York Ave NE, Ivy City Smokehouse 1356 Okie St NE, Crummell School 1900 Gallaudet St NE (5D02), Wheatley 1299 Neal St NE (5D03), Trinidad Rec 1310 Childress St NE (5D05), Hechinger Mall 1600 Maryland Ave NE (5D06), Mount Olivet Cemetery 1300 Bladensburg Rd NE (5C04), Spingarn, Browne, Langston Terrace (5D09) | National Arboretum 3501 New York Ave NE (5C04, FORT LINCOLN/GATEWAY). |
| Woodley Park (3C01/02/03/07) | Metro 2700 Connecticut (3C01), 2800 Connecticut (3C01), Calvert 2300 block (3C01), Open City 2331 Calvert, Oyster-Adams 2801 Calvert, 2600 Connecticut (3C02), Wardman Tower (coord, 3C02), Connecticut and Calvert (coord, 3C02), National Zoo 3001 Connecticut (3C03), 2900/3000 Connecticut (3C03), Kennedy-Warren 3133 Connecticut (3C03), Omni Shoreham 2500 Calvert, Maret 3000 Cathedral Ave, 2700 Cathedral Ave (3C07), Duke Ellington Bridge (coord, 3C01) | Uptown 3426 Connecticut and Cleveland Park Library 3310 Connecticut (3C05), Cathedral 3101 Wisconsin and Beauvoir (3C08), Klingle Mansion (3C04), Sidwell (3A03), Taft Bridge (coord, 2D01). |

**Things you may want to act on** (boundaries are decided, so these are flags, not requests):
- **Foggy Bottom's HPN holds less of the West End than the brief assumes.** The landmarks most people call West End (the library, the Ritz, Trader Joe's, Stevens) are in GEORGETOWN EAST. And about a quarter of the HPN is 2C02, Golden Triangle offices on K and Connecticut. Kennedy Center and State are outside. The HPN is campus, Watergate, Golden Triangle. I kept West End and Kennedy Center out of the regexes as bare terms for the second reason as well: their news is national.
- **HPN names misfile things by local usage.** Eastern High School and Eliot-Hine are "Hill East" schools in most people's speech but sit in KINGMAN PARK. Spingarn and Langston Terrace sit in TRINIDAD, and Langston Golf is in neither Kingman nor Stadium-Armory. Congressional Cemetery is in STADIUM ARMORY, as the brief says.
- **6B09 is one SMD with two identities.** Its centroid falls in STADIUM ARMORY (so `ANCS` gets 6B there), but Potomac Ave Metro, Jenkins Row and 700 14th St SE, all in 6B09, are HILL EAST. Barney Circle (coord) falls on the STADIUM ARMORY side.
- **Kingman Island sits on an HPN edge.** The address point 575 Oklahoma Ave NE and my Heritage Island coordinate are 7D05, STADIUM ARMORY. My coordinate for Kingman Island's middle landed in 5D09, FORT LINCOLN/GATEWAY, and I don't trust that coordinate enough to call it. I put island terms in both Kingman Park and Stadium-Armory: people expect it on Kingman Park's page, and most of the access is from the Stadium-Armory side.
- **Overlaps with live sites.**
  - Bloomingdale ∩ NoMa: NoMa BID 5% (Harry Thomas Way side). `TERMS["noma"]` also has `harry thomas (way|rec)`, and the rec center (1743 Lincoln Rd NE) is 5F07, inside Bloomingdale. Both sites will show those items.
  - Woodley Park ∩ Cleveland Park: no shared SMDs with ANC 3C's Cleveland Park side, but `anc3c.dc.gov` is read as `all` by `clevelandpark`, so Woodley Park items already show there.
  - Woodley Park ∩ Glover Park: `woodleypark.org` now redirects to `gloverparkmainstreet.org`. Don't link it.
  - Trinidad ∩ NoMa: Union Market stays out of `TERMS["noma"]`, as SOURCES-CENTRAL recommended, so there's no double count.
  - Hill East ∩ Capitol Hill: `TERMS["capitolhill"]` has `ANC 6B` and `east capitol st`, so Hill Rag ANC 6B reports go to Capitol Hill by default. Hill East takes only 6B07–6B09 mentions.
  - Kingman Park ∩ H Street: `TERMS["hstreet"]` has `ANC 6A`. I left 6A out of Kingman Park's terms for the same reason.

**Farmers markets in the existing layer** (`events.MARKETS`, tested against each boundary).
| Market | Point falls in | Layer schedule | Engine result |
|---|---|---|---|
| Bloomingdale Farmers Market, 100 block R St NW | BLOOMINGDALE 5E02 | Sundays 9–1, "Year round" | `market_dates` can't read "Year round" (`season_bound` returns None), so it lands in `unscheduled` with no dates |
| FRESHFARM Foggy Bottom, 901 23rd St NW | GWU 2A08 | Wednesdays 3–7, "Year round" | same |
| RFK Open Air Market, 2615 Benning Rd NE | KINGMAN PARK 7D05 | Saturdays 8–3, May to December | dated |
| Trinidad Farmers Market, 1299 Neal St NE | TRINIDAD 5D03 | Sundays 9–1, "Year Round" | `unscheduled` |
| FRESHFARM Union Market District, 1298 5th St NE | TRINIDAD 5D01 | Sundays 10–2, April to November | dated |
| Mount Pleasant Farmers' Market, 3200 Mount Pleasant St NW | MOUNT PLEASANT 1D01 | Saturdays 9–1, "year round" | `unscheduled` |
| Maret School Farmers Market, 3000 Cathedral Ave NW | WOODLEY PARK 3C07 | Saturdays 9–1, "year round" | `unscheduled` |

Five of the seven say "year round". Teaching `in_season` that phrase would date all five and every other site's year-round markets. That one-line change is worth more than any calendar found below. Not made.

### 0.2 Keyword rules (Python `re`; drop-in for `TERMS` and `NOT_HERE` in news.py)

Hill East and Trinidad are partly case-sensitive, with scoped `(?i:…)` groups. They must not get `re.I`. The blocks below compile as written.

I ran two kinds of test. The real one: every feed in this file, counted in the tables. The second: 73 strings I wrote myself, 40 traps ("RFK Jr. defends vaccine schedule", "Trinidad and Tobago beat Jamaica", "Bloomingdale's flagship store", "Diplomats in Foggy Bottom fear more cuts at the State Department", "A crash in Kingman, Ariz.", "Mount Pleasant, S.C.", "on a hill east of the river", "Woodley Park in Van Nuys") and 33 true cases. All 73 pass, which proves only that the rules do what I intended. Real feeds carried fewer traps because they're DC outlets. The rejects fired on real items for Bloomingdale, Foggy Bottom, Trinidad and Stadium-Armory; those for Kingman, Mount Pleasant and Woodley Park have only the synthetic tests behind them.

**Bloomingdale**:
```python
"bloomingdale": re.compile(
    r"\bbloomingdale\b(?!['\u2019]s?\b)(?!,?\s+(ill|illinois|il|n\.?y|new\s+york|ny|ga|georgia|tenn|tennessee|tn|mich|michigan|mi|ind|indiana|ohio|n\.?j|new\s+jersey|fla|florida)\b)(?!\s+(road|avenue|ave|trail|township|school\s+district))|"
    r"\beckington\b|\btruxton\s+circle\b|\bmcmillan\s+(park|reservoir|sand|filtration|site|redevelopment|project)\b|\bcrispus\s+attucks\s+park\b|"
    r"\bbig\s+bear\s+caf|\bnorth\s+capitol\s+main\s+street\b|\bdunbar\s+high\b(?=.{0,200}\b(d\.?c|washington|NW)\b)|\bmckinley\s+tech(nology)?\b|\bharry\s+thomas\s+(sr\.?\s+)?rec|"
    r"\bANC\s*5E\b|\b(1[5-9]|2[0-4])\d\d\s+(north\s+capitol|n\.?\s+capitol)\s+st(reet)?\b|\b\d{1,3}\s+rhode\s+island\s+ave(nue)?\.?,?\s+n\.?w\b|"
    r"\b1[6-9]\d\d\s+(1st|first)\s+st(reet)?\.?,?\s+n\.?[we]\b", re.I | re.S),
"bloomingdale": (re.compile(r"\bbloomingdale['\u2019]s\b|\bbloomingdales\b|\bmacy['\u2019]?s\b|\bbloomingdale,?\s+(ill|il|illinois|n\.?y|new\s+york|ga|georgia|tn|tenn|mi|mich|fla|florida|n\.?j|nj)\b|\bdupage\b", re.I),
                 re.compile(r"\bbloomingdale\s+(civic|farmers|neighborhood|library|community)\b|\bin\s+bloomingdale\b(?=.{0,200}\b(d\.?c|washington|NW)\b)|\beckington\b|\btruxton\b|\bmcmillan\b|\bcrispus\s+attucks\b|\bANC\s*5E\b|\b(1st|first|north\s+capitol)\s+st", re.I | re.S)),
```
- The negative lookaheads kill `Bloomingdale's`, `Bloomingdale, Ill.` and `Bloomingdale Road`. The reject list caught real items in body mode: WTOP's own Bloomingdale tag has "If White Flint Mall gets overhaul, Bloomingdale's interested in coming back", and a Washingtonian pub list mentions the store.
- Eckington and Truxton Circle are in the HPN by address, so they count bare.
- `1600–1999 1st St` and `1500–2499 North Capitol St` are the blocks inside.
- Tested today: `wtop.com/tag/bloomingdale` 7/6/1, `washingtonian.com/tag/bloomingdale` 10/10/5, Washingtonian `?s=bloomingdale` 8/1/1. The one summary keeper: "A New 'Modern Coastal' Restaurant With a Dog-Friendly Menu Opens in Bloomingdale". That feed's other 7 body hits are roundups, which `match` mode ignores.

**Foggy Bottom (HPN GWU)**:
```python
"foggybottom": re.compile(
    r"\bfoggy\s+bottom\b|\bANC\s*2A\b|\bgolden\s+triangle\s+(bid|business\s+improvement|dc|d\.c\.)\b|\bwatergate\s+(east|west|south|hotel|complex|apartments|office\s+building|residents?)\b|"
    r"\bgw\s+(university\s+)?hospital\b|\bgeorge\s+washington\s+university\s+hospital\b|\bfarragut\s+square\b|\bwest\s+end\s+(citizens|neighborhood)\b|"
    r"\b(gw|gwu|george\s+washington\s+university)\b(?=.{0,300}\b(foggy\s+bottom|neighbors?|residents|campus\s+plan|ANC\s*2A)\b)|"
    r"\b(1[7-9]|2[0-5])\d\d\s+[HIKL]\s+st(reet)?\.?,?\s+n\.?w\b|\b(2[0-5])\d\d\s+pennsylvania\s+ave(nue)?\.?,?\s+n\.?w\b|\b[5-9]\d\d\s+(19th|2[0-5](st|nd|rd|th))\s+st(reet)?\.?,?\s+n\.?w\b", re.I | re.S),
"foggybottom": (re.compile(r"\bstate\s+department\b|\bdiplomat|\bsecretary\s+of\s+state\b|\bforeign\s+service\b|\bambassadors?\b|\brubio\b|\bblinken\b|\busaid\b|\bforeign\s+policy\b|\bembass", re.I),
                re.compile(r"\bfoggy\s+bottom\s*([-/\u2013]\s*(gwu?|west\s+end)|metro|station|association|neighborhood|farmers|news|main\s+street|residents?|walking\s+tour|campus)\b|\bfoggy\s+bottom['\u2019]s\s+(residents?|neighbors?|restaurant|rowhouse|funkstown)|\bANC\s*2A\b|\bfunkstown\b|\bWest\s+End\b", re.I)),
```
- **Bare "Foggy Bottom" matches, then NOT_HERE drops it if the item also has State Department wording and no neighborhood cue.** I tried requiring a cue up front; that dropped the Washingtonian's "A Witchy Italian Restaurant Opens in Foggy Bottom", which has none.
- Real evidence, in body mode: `washingtonblade.com/?s=foggy+bottom` has two State Department pieces ("LGBTQ people 'erased' from State Department's 2024 human rights report") and the reject drops both. A Washingtonian newsletter naming the Secretary of State drops too.
- The cost: PoPville's Alibi Club post says "diplomat" in its body, so body mode would drop it. `match` mode keeps it (0/1/0). One more reason to read shared outlets in `match` mode.
- Bare "West End", "Watergate", "Kennedy Center", "World Bank" and "GWU" never match. WTOP's Kennedy Center tag is 10 of 10 national politics. `wtop.com/tag/west-end/feed/` has an Ellicott City story and an Alexandria one.
- GW counts only with a neighborhood cue within 300 characters. On WTOP's GW tag that's 2/0/0, dropping the Ashburn campus sale and the delegate race.
- Address rule: 1700–2599 H/I/K/L St NW, 2000–2599 Pennsylvania Ave NW, and 500–999 of 19th through 25th St NW. **The address rule found a real local item the words missed:** PoPville "Major Action at the Alibi Club" (0/1/0, 1806 I St NW). N St and M St east of 2000 are left out since they're Dupont.
- Accepted leak: 1100 and up of 22nd St NW is out, but 2300–2599 L St NW is GEORGETOWN EAST and still matches. Local usage calls it the West End and readers expect it here.

**Hill East**: **case-sensitive** on "Hill East", so lower-case prose never matches.
```python
"hilleast": re.compile(
    r"\bHill\s+East\b|\b(?i:potomac\s+ave(nue)?\s+metro|payne\s+elementary|watkins\s+elementary|jenkins\s+row|kentucky\s+courts?)\b|"
    r"\bANC\s*6B0?[789]\b|\b6B0[789]\b|\b(?i:1[3-7]\d\d\s+(pennsylvania|massachusetts|independence|north\s+carolina)\s+ave(nue)?\.?,?\s+(s\.?e|n\.?e)|1[3-9]th\s+(and|&)\s+(potomac|pennsylvania))\b"),
"hilleast": (re.compile(r"\bcapitol\s+hill\s+east\s+(of|side)\b", re.I), re.compile(r"\bANC\s*6B\b|\bSE\b|\bReservation\s+13\b")),
```
- The address rule (1300–1799 Pennsylvania/Massachusetts/Independence/North Carolina Ave SE or NE, 13th–19th & Potomac or Pennsylvania) reaches the corridor that isn't named in copy.
- Tested: PoPville p1 2/1/0 ("DC Open House List"), The Hill is Home 3/0/0 (body only), Hill Rag `search=hill+east` 1/1/0. Hill Rag's "Change in Hill East: Plans for RFK, Reservation 13 and the DC Armory" matches here and on Stadium-Armory, which is right.
- "Capitol Hill East" isn't a trap in the live data, and NOT_HERE is nearly empty on purpose.

**Kingman Park**: never bare "Kingman".
```python
"kingmanpark": re.compile(
    r"\bkingman\s+park\b|\bkingman\s+(and|&)?\s*heritage\s+islands?\b|\bkingman\s+(island|lake)\b|\bfriends\s+of\s+kingman\b|\brosedale\s+(rec(reation)?(\s+center)?|pool|community\s+center)\b|"
    r"\bminer\s+elementary\b|\beliot[-\s]hine\b|\beastern\s+high\b(?=.{0,200}\b(d\.?c|washington|NE|ramblers|capitol\s+hill)\b)|\bmaury\s+elementary\b|\boklahoma\s+ave(nue)?\.?(\s+n\.?e\b|\s+(metro|streetcar|station))|"
    r"\b(1[5-9]|2[0-6])\d\d\s+benning\s+r(oa)?d\.?,?\s+n\.?e\b|\brfk\s+open\s+air\s+market\b|\bANC\s*7D\b", re.I | re.S),
"kingmanpark": (re.compile(r"\bkingman,?\s+(ariz|arizona|az|kan|kansas|ks)\b|\bmohave\s+county\b|\bkingman\s+reef\b|\b(camp|rob|andrew|fred|peter|fort)\s+kingman\b", re.I),
                re.compile(r"\bkingman\s+(park|island|lake)\b(?=.{0,200}\b(d\.?c|washington|NE|anacostia|RFK)\b)|\bfriends\s+of\s+kingman\b", re.I | re.S)),
```
- `ANC 7D` is here and on Stadium-Armory. 7D is 52% of Kingman Park.
- The rule accepts 1500–2699 Benning Rd NE, to reach the RFK Open Air Market at 2615. 2500 and 2600 Benning (Spingarn, Langston Golf) are outside the HPN by address and the rule still takes them. Readers won't draw that line.
- Tested: Hill Rag `search=kingman` 5/5/5 ("Don't Miss the Kingman Island Teen Band Festival", "Rosedale Pool Reopens After $6.8 Million Renovation"), ANC 7D 6/6/3, Capitol Hill Corner 1/1/1 ("Tomorrow – Maury Elementary Fall Fest"), WTOP `kingman-island` 6/6/2.

**Mount Pleasant**:
```python
"mountpleasant": re.compile(
    r"\b(mount|mt\.?)\s+pleasant\b|\bANC\s*1D\b|\blamont\s+(plaza|st(reet)?\s+n\.?w|park)\b|\bbancroft\s+elementary\b|\brosemount\s+center\b|\bpiney\s+branch\s+parkway\b|\bklingle\s+valley\b", re.I | re.S),
"mountpleasant": (re.compile(r"\b(mount|mt\.?)\s+pleasant,?\s+(s\.?c|south\s+carolina|mich|michigan|mi|wis|wisconsin|wi|iowa|ia|pa|pennsylvania|tx|texas|ut|utah|tenn|tennessee|tn|ny|n\.?y|new\s+york|ohio|nc|n\.?c|north\s+carolina|ontario|fla|florida|va|virginia|md|maryland)\b|"
                             r"\bcentral\s+michigan\s+university\b|\bcharleston\b|\bisle\s+of\s+palms\b|\bracine\b|\bmt\.?\s+pleasant\s+(pirates|high\s+school\s+football)\b|\bwestchester\b|\bvalhalla\b", re.I),
                  re.compile(r"\b(d\.?c\.?|washington)['\u2019]?s?\s+(mount|mt\.?)\s+pleasant\b|\b(mount|mt\.?)\s+pleasant,?\s+(d\.?c|n\.?w)\b|\b(mount|mt\.?)\s+pleasant\s+(st(reet)?|neighborhood|library|farmers|main\s+street)\b|\bANC\s*1D\b|\blamont\s+st|\b16th\s+st", re.I)),
```
- `match` mode only: bare "Mount Pleasant" passes on anything without an out-of-town marker. Every DC feed tested came back DC.
- No out-of-town Mount Pleasant turned up in any feed today, so that reject list has only my synthetic tests behind it.
- `\b16th\s+st` in the rescue means a story that names both a Mount Pleasant elsewhere and 16th Street survives; I accept that.
- Tested: WTOP `mount-pleasant` 10/10/3 and `mt-pleasant` 2/2/2, District Bridges 3/3/1 ("Bring Back Mount Pleasant Streateries"), Historic Mount Pleasant 10/10/5, Washingtonian 9/1/0 ("Michelin Adds 4 New Restaurants…").

**Stadium-Armory**: **never bare "RFK"**.
```python
"stadiumarmory": re.compile(
    r"\bRFK\s+(memorial\s+)?(stadium|campus|site|for\s+all|master\s+plan|redevelopment|festival\s+grounds|fields?|parking|lots?|development|land|project|deal|bill)\b|"
    r"\brobert\s+f\.?\s+kennedy\s+(memorial\s+)?stadium\b|\bstadium[-\s/]armory\b|\bcongressional\s+cemetery\b|\b(d\.?c\.?|district\s+of\s+columbia)\s+armory\b|\bthe\s+armory\b(?=.{0,80}\bRFK\b)|"
    r"\breservation\s+13\b|\b(d\.?c\.?|district)\s+jail\b|\bcorrectional\s+treatment\s+facility\b|\bdc\s+general\b|"
    r"\bbarney\s+circle\b|\bheritage\s+island\b|\bkingman\s+(and|&)\s+heritage\b|\bANC\s*7[DF]\b|\bANC\s*6B09\b|\b\d{3,4}\s+(19th|20th|21st|22nd)\s+st(reet)?\.?,?\s+s\.?e\b", re.I | re.S),
"stadiumarmory": (re.compile(r"\bRFK\s+Jr\b|\bKennedy\s+Jr\b|\bHHS\b|\bvaccines?\b|\bMAHA\b", re.I),
                  re.compile(r"\bRFK\s+(memorial\s+)?(stadium|campus|site)\b|\bstadium[-\s/]armory\b|\bcongressional\s+cemetery\b|\bANC\s*7[DF]\b", re.I)),
```
- `RFK` counts only followed by stadium, campus, site, for all, master plan and so on. "RFK Jr.'s site crashes" is safe because the `Jr.` breaks the sequence.
- Real test: `wtop.com/tag/rfk/feed/` (the worst feed available, 9 items). It kept the stadium stories and dropped "RFK Jr.'s neighbor has Halloween display message for him" and "'A man of everybody' – remembering Robert F. Kennedy". Don't subscribe to that tag anyway; use `rfk-stadium`.
- Also real: `washingtonian.com/?s=rfk` returned 10 items, all national or roundup. It scores 1/0/0. Skip it.
- `DC Jail` is inside (7F08), and "Council bill calls for allowing contact visits at DC jail" (DC Line) matches. That's a citywide policy story about a building here. If you'd rather not, delete `\b(d\.?c\.?|district)\s+jail\b`.
- `the Armory` needs RFK within 80 characters, for The Armory Show and every other armory.
- Tested: The DC Line `?s=rfk` 15/15/11, Hill Rag `search=rfk` 9/9/6, Hill Rag `search=congressional+cemetery` 15/15/13, WTOP `rfk-stadium` 10/10/5.

**Trinidad**: **"Trinidad" is case-sensitive and needs a form that means the neighborhood.** Ivy City and Union Market carry most of the load.
```python
"trinidad": re.compile(
    r"\b(?i:in|near|of|around|across)\s+Trinidad\b(?!\s+(and|&)\s+Tobago)(?=.{0,200}\b(?i:d\.?c|washington|NE|northeast|neighborhood|ward\s*5|police|MPD)\b)|"
    r"\bTrinidad\s+(?i:neighborhood|neighbors|rec(reation)?(\s+center)?|farmers\s+market|ave(nue)?)\b|\b(?i:d\.?c\.?|northeast)['\u2019]?s?\s+Trinidad\b|"
    r"\bTrinidad\s+(?i:section|community|residents?)\b(?=.{0,100}\b(?i:d\.?c|washington|NE|northeast)\b)|"
    r"(?i:\bivy\s+city\b|\bunion\s+market\b|\bmount\s+olivet\s+(r(oa)?d|cemetery)\b|\bmontello\s+ave|\bhecht\s+(warehouse|company|co\.?)\b|\bcrummell\s+school\b|\bokie\s+st|\bANC\s*5D\b|"
    r"\bhechinger\s+mall\b|\bwheatley\s+(education|elementary)\b|\bspingarn\b|\blangston\s+terrace\b|\bbrowne\s+education\b|\bflorida\s+ave(nue)?\.?,?\s+n\.?e\b|"
    r"\bgallaudet\b(?=.{0,300}\b(neighbors?|residents?|ANC|6th\s+st|florida\s+ave|union\s+market|campus\s+(plan|development|expansion))\b))", re.S),
"trinidad": (re.compile(r"\btobago\b|\btrinidadian\b|\bport\s+of\s+spain\b|\bcaribbean\b|\bvenezuela\b|\btrinidad,?\s+(colo|colorado|co|calif|california|ca|cuba|tx|texas)\b|\bboliv|\bunion\s+market\b.{0,60}\b(richmond|brooklyn|park\s+slope|sacramento|baltimore)\b", re.I | re.S),
             re.compile(r"\bANC\s*5D\b|\bivy\s+city\b|\bmontello\b|\bmount\s+olivet\b|\bTrinidad\s+(neighborhood|rec)|\bunion\s+market\s+(district|dc)\b|\b5th\s+st(reet)?\.?,?\s+n\.?e\b|\b(northeast|NE)\s+(dc|d\.c\.)\b", re.I)),
```
- "In Trinidad" needs a DC cue within 200 characters, so "A storm near Trinidad and Tobago" and "Visit Trinidad this Carnival" fail. The reject list also fired on real copy in body mode: a Washingtonian restaurant list with "Trinidadian" and a City Paper list with "Caribbean".
- Real test: `washingtonian.com/?s=trinidad`: 10 items (Kwame Onwuachi, a St. Croix rooftop), scores 1/0/0. SOURCES-EAST already found the 1926 version of this.
- Gallaudet needs a neighborhood cue; WTOP's tag is 1/1/0, dropping the Deaf President Now and scholarship stories. "Gallaudet" alone would swamp this site with university news.
- `Florida Ave NE` is here because the Union Market edge runs along it. It also runs past Gallaudet and into H Street's area.
- Other Union Markets (Richmond, Brooklyn) are in the reject list.
- Tested: WTOP `ivy-city` 10/10/2, `union-market` 10/10/4, `trinidad` 9/6/0, DC Line `?s=ivy+city` 12/12/7, `?s=union+market` 6/6/5, PoPville p3 1/1/0 ("Stellar Sandwich News – A. Litteri now partnering with Bread Alley!!").

**Woodley Park (3C01, 3C02, 3C03, 3C07)**: Woodley Park proper, per the lead. No Cleveland Park terms (Macomb St, Uptown, Tregaron), no bare Wardman surnames.
```python
"woodleypark": re.compile(
    r"\bwoodley\s+park\b|\bwoodley\s+r(oa)?d\.?,?\s+n\.?w\b|\bwardman\s+(tower|park)\b|\bomni\s+shoreham\b|\bmaret\s+school\b|\boyster[-\s]adams\b|\bduke\s+ellington\s+bridge\b|"
    r"\bconnecticut\s+(ave(nue)?\.?\s+)?(and|&|at)\s+calvert\b|\bcalvert\s+st(reet)?\.?,?\s+n\.?w\b|\b2[3-9]\d\d\s+calvert\s+st\b|\b2[6-9]\d\d\s+connecticut\s+ave(nue)?\b|\b3[01]\d\d\s+connecticut\s+ave(nue)?\b|"
    r"\bANC\s*3C0?[1237]\b|\b3C0[1237]\b|\b(smithsonian['\u2019]?s?\s+)?national\s+zoo(logical\s+park)?\b(?=.{0,300}\b(neighbors?|connecticut\s+ave|woodley|ANC|residents|parking|traffic|road\s+closures?|zoolights|lights)\b)", re.I | re.S),
"woodleypark": (re.compile(r"\bencino\b|\bvan\s+nuys\b|\bsepulveda\b|\blos\s+angeles\b|\bLAPD\b|\bcricket\b|\bwoodley,?\s+(reading|berkshire|stockport|new\s+york|ny)\b", re.I),
                re.compile(r"\bwoodley\s+park[-\s/]+(zoo|metro|adams)|\bconnecticut\s+ave|\bANC\s*3C\b|\b(d\.?c\.?|NW)\b", re.I)),
```
- **The zoo is gated.** It's inside the boundary (3C03), but national panda stories would bury the neighborhood, so "National Zoo" counts only with a neighbor, traffic, parking or ZooLights cue within 300 characters. On `wtop.com/tag/national-zoo/feed/` that's 1/1/0, keeping one federal-approval story and dropping the animal births. WTOP's own Woodley Park tag still brings the big zoo stories through the tag text.
- "Woodley Park" in Los Angeles (Encino, Van Nuys, the cricket fields) is rejected. "Woodley" alone never matches, so Shailene Woodley and Woodley near Reading stay out.
- `ANC 3C` alone isn't a term, since it's Cleveland Park's too. Only 3C01, 3C02, 3C03 and 3C07 count.
- Connecticut Ave 2600–3199 and Calvert St 2300–2999 are the addresses inside. 3133 Connecticut (Kennedy-Warren) is 3C03 even though the HPN calls it Forest Hills.
- Tested: WTOP `woodley-park` 10/10/2, DC Line `?s=woodley+park` 12/12/3, PoPville p1 1/1/1 ("Elevator at Woodley Park Metro Out until 11/14?"), ANC 3C 2/2/2 ("Woodley Park Day 2026", "Cleveland and Woodley Park Main Street Holiday Market"), Washingtonian 9/0/0 (body-only roundups).

### 0.3 General feeds already in the engine, counted for the new areas (body / summary / title)

BL Bloomingdale, FB Foggy Bottom, HE Hill East, KP Kingman Park, MP Mount Pleasant, SA Stadium-Armory, TR Trinidad, WP Woodley Park.

| Feed | robots | items (dates) | BL | FB | HE | KP | MP | SA | TR | WP |
|---|---|---|---|---|---|---|---|---|---|---|
| `https://www.popville.com/feed/` p1 | allow | 20 (29 Oct–2 Nov) | 0 | 0 | 2/1/0 | 0 | 1/0/0 | 0 | 0 | 1/1/1 |
| PoPville p2 | allow | 20 (28–29 Oct) | 0 | 0 | 0 | 0 | 0 | 0 | 1/0/0 | 0 |
| PoPville p3 | allow | 20 (26–28 Oct) | 0 | 0/1/0 | 0 | 0 | 0 | 0 | 1/1/0 | 0 |
| `https://washingtoncitypaper.com/feed/` | allow | 10 (28–30 Oct) | 1/0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `https://wtop.com/local/dc/feed/` | allow | 10 (30 Oct–2 Nov) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `https://wamu.org/feed/` | allow | 10 (29 Oct–1 Nov) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `https://51st.news/rss/` | allow | 15 (21–29 Oct) | 0 | 0 | 2/0/0 | 1/0/0 | 1/0/0 | 0 | 3/0/0 | 0 |
| `https://thedcline.org/feed/` | allow | 20 (8–30 Oct) | 0 | 0 | 0 | 0 | 0 | 3/3/3 | 0 | 0 |
| `https://mayor.dc.gov/rss.xml` | allow | 10 (2015–Apr 2026) | 1/1/0 | 1/1/0 | 2/2/0 | 0 | 0 | 3/3/0 | 0 | 1/1/0 |
| `https://dpr.dc.gov/rss.xml` | allow | 10 (2015–Apr 2026) | 0 | 0 | 1/1/0 | 0 | 0 | 1/1/0 | 0 | 0 |
| `https://ddot.dc.gov/rss.xml` | allow | 10 (Aug–30 Oct) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `https://www.hillrag.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link` (Crawl-delay 20) | allow | 20 (18 Oct–2 Nov) | 0 | 0 | 1/0/0 | 0 | 1/0/0 | 3/1/1 | 1/1/1 | 0 |
| `https://oanc.dc.gov/rss.xml` | allow | 10 (13–27 Oct) | 0 | 0 | 1/1/0 | 0 | 0 | 1/1/0 | 0 | 0 |

`https://ggwash.org/rss` **was not counted; see the next paragraph.**

**Crawl delays: a problem already in the engine.**
- **`ggwash.org/robots.txt` says `Crawl-Delay: 3000`** under `User-agent: *` (50 minutes). `SHARED` includes `https://ggwash.org/rss`, so a nightly run fetches it once per site with 0.5 s between feeds, 31 times once these eight are on. SOURCES-CENTRAL tested it without flagging this. `news.parse_robots` ignores Crawl-delay entirely. My own script honoured the delay, which is how I noticed: it sat waiting on the host. I stopped it, so GGW's tag feeds went untested. I fetched `/rss` once to confirm it answers (200, 72 KB) and did not keep the body. Its Content-Signal line also says `ai-train=no`; not relevant to headlines, but you should know it's there. The fix is to fetch GGW once per run and share the result across sites, or move it out of `SHARED`. Same treatment for the hosts below.
- Crawl-delays on hosts recommended here: Hill Rag 20 s, Historic Mount Pleasant 20 s, GW Hatchet 6 s. `build_headlines` sleeps 0.5 s, and only between that slug's feeds. Hill East, Kingman Park, Stadium-Armory and Trinidad all ask Hill Rag for something, so they need the delay enforced per host across slugs. `TRIBE` already carries a delay field; `FEEDS` doesn't. The FEEDS blocks below assume someone adds a per-host wait, e.g. `CRAWL_DELAY = {"www.hillrag.com": 20, "www.historicmountpleasant.org": 20, "gwhatchet.com": 6, "ggwash.org": 3000}`.

**Expect thin news on four of these.** Bloomingdale, Hill East, Kingman Park and Woodley Park have no live neighborhood outlet. Today's 60 PoPville items gave Bloomingdale nothing at all. Liquor licenses and ANC notices will carry those pages.

---

## 1. Bloomingdale (HPN `BLOOMINGDALE`; ANC 5E ~71% + 5F ~29%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://www.washingtonian.com/tag/bloomingdale/feed/` (redirects to `washingtonian.com`) | allow | 10 (Feb 2019 – 22 Oct 2025) | 10/10/5 | Clean, slow. "Neighborhood Guide: Where to Eat, Shop, and Play in Bloomingdale and Eckington". Also one Chevy Chase guide that tags it. `match`. |
| `https://www.washingtonian.com/?s=bloomingdale&feed=rss2&orderby=date&order=DESC` | allow | 10 (Mar – 29 Oct 2026) | 8/1/1 | Freshest source, summary mode essential. "A New 'Modern Coastal' Restaurant…Opens in Bloomingdale". |
| `https://wtop.com/tag/bloomingdale/feed/` | allow | 8 (2013 – 26 Oct 2023) | 7/6/1 | **Stale**, but WTOP tags crime and police stories here when they happen. Cheap to keep. |
| `https://eckingtoncivicassociation.com/feed/` (WordPress.com) | allow | 10 (Oct 2022 – 20 Jul 2025) | 8/3/0 | Real but quiet: "ECA Sends Letters Supporting Traffic Safety Installations", meeting notes. Newest is 15 months old. `all`. |
| `https://thedcline.org/?s=eckington&feed=rss2&orderby=date&order=DESC` | allow | 20 (Dec 2019 – Sep 2022) | 14/14/9 | **Stale.** |
| `https://thedcline.org/?s=bloomingdale&feed=rss2&orderby=date&order=DESC` | allow | 20 (May 2019 – Jun 2022) | 9/9/4 | **Stale.** |
| `https://www.hillrag.com/wp-json/wp/v2/posts?search=bloomingdale&per_page=20&_fields=date,title,excerpt,link` | allow, Crawl-delay 20 | 15 (2017 – Apr 2026) | 2/2/0 | Hill Rag is the wrong side of town. Skip. |
| PoPville p1–p3 | allow | 60 | 0 | Nothing today, though PoPville covers it when something happens. |

Not usable:
- `bloomingdalecivicassociation.org/feed/`: 10 items, newest **Feb 2021**. WP JSON agrees. Live only as a static site with a calendar plugin (§ Events).
- `batesareacivicassociation.org/feed/`: newest Mar 2021. Bates is the Truxton Circle-side group.
- `bloomingdaledc.org`: a hand-built static site (`/news.htm`, `/calendar.htm`), `/feed/` 404. Age not checked.
- **`northcapitoldc.com`: redirects to a gambling-spam page.** Do not link it, even though old listings and search results still point there. `northcapitolmainstreet.org` is a Wix site with no feed and only `/news-and-events`.
- ANC 5E: `anc5edc.org` is a one-page stub, `/feed/` and `/meetings` 404. `anc5e.org` and `anc5e.dc.gov` have no DNS.
- ANC 5F: `anc5f.com` timed out on connect (twice); `anc5f.dc.gov` has no DNS.
- WTOP `eckington`, `mcmillan` tags: 200 with 0 items. PoPville `/tag/…/feed/`: 200 with 0 items for all eight tags I tried. Washingtonian `/location/bloomingdale-eckington/feed/`: 0 items.

```python
"bloomingdale": [
    ("Eckington Civic Association", "https://eckingtoncivicassociation.com/feed/", "https://eckingtoncivicassociation.com/", "all"),
    ("Washingtonian", "https://www.washingtonian.com/tag/bloomingdale/feed/", "https://www.washingtonian.com/", "match"),
    ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="bloomingdale"), "https://www.washingtonian.com/", "match"),
    ("WTOP", "https://wtop.com/tag/bloomingdale/feed/", "https://wtop.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| Bloomingdale Farmers Market | existing layer | Listed, but `unscheduled` (see §0.1). |
| Bloomingdale Civic Association | `https://bloomingdalecivicassociation.org/?plugin=all-in-one-event-calendar&controller=ai1ec_exporter_controller&action=export_events&no_html=true` | robots allow, valid ICS, **1 VEVENT**: "BCA Membership Meeting", DTSTART 20 Nov 2023 with a recurrence I didn't expand, timezone set to Atlantic/Azores, which is wrong. **Not usable** without more work than it's worth. `/wp-json/tribe/…` 404. |
| ANC 5E, 5F | `https://oanc.dc.gov/rss.xml` | Filter works by title; none in today's 10 items. |
| North Capitol Main Street | Wix `/news-and-events` | No feed. |

```python
ANCS["bloomingdale"] = ["5E", "5F"]
LINKS["bloomingdale"] = [
    {"name": "Bloomingdale Civic Association calendar", "url": "https://bloomingdalecivicassociation.org/calendar-2/"},
    {"name": "Eckington Civic Association", "url": "https://eckingtoncivicassociation.com/"},
    {"name": "Shaw Library events", "url": "https://dclibrary.libnet.info/events?l=Shaw%20(Watha%20T.%20Daniel)%20Neighborhood%20Library"},
    {"name": "Northwest One Library events", "url": "https://dclibrary.libnet.info/events?l=Northwest%20One%20Neighborhood%20Library"},
]
```
No library sits inside the HPN (Northwest One, 155 L St NW, is 6E03, CHINATOWN; Shaw is 2G). Location names follow DCPL's pattern; not confirmed.

---

## 2. Foggy Bottom (HPN `GWU`; ANC 2A ~66% + 2C ~23% + 2B ~11%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| **`https://www.foggybottomassociation.org/blog-feed.xml`** (Wix) | allow | 20 (24 Jan – 24 Oct 2026) | 14/14/9 | **Best local source.** The Foggy Bottom Association's history column ("Funkstown – The Titanic, William Jennings Bryan, and Foggy Bottom") and neighborhood news ("Sixth Annual Foggy Bottom Walking Tour a Success"). `all`. |
| **`https://anc2a.org/feed/`** | allow | 10 (19 May – 20 Oct 2026) | 10/10/10 | All agendas, and they are posted more than once ("…October 21, 2026 Regular Meeting" twice). The engine dedupes by title. `all`. |
| **`https://gwhatchet.com/feed/`** (GW Hatchet; `www.` redirects) | allow, **Crawl-delay 6** | 10 (all 2 Nov 2026, posted in a batch) | 4/2/1 | "ANC chair, Foggy Bottom Association president face off in first contested ANC race in years". Mostly campus and DC politics, so `match`. `?s=` is **robots-disallowed**. `/category/metro/feed/` and `/category/news/feed/` returned the same 10 today. |
| `https://goldentriangledc.com/feed/` (Golden Triangle BID) | allow | 10 (15 Oct 2025 – 29 Oct 2026) | 9/9/4 | BID is 99% inside, so `all`. Mostly press releases. "Free Fitness Classes, Live Music, and Fun in Farragut Square this Fall". |
| `https://wtop.com/tag/foggy-bottom/feed/` | allow | 10 (Sep 2023 – 8 Jan 2026) | 10/10/2 | "Electrical cable catches fire, forcing closure of Foggy Bottom Metro station". `match`. |
| `https://www.washingtonian.com/?s=foggy+bottom&feed=rss2&orderby=date&order=DESC` | allow | 10 (Apr – 2 Nov 2026) | 9/1/1 | `match`. Newsletter-roundup body hits; one real title. |
| `https://thedcline.org/?s=foggy+bottom&feed=rss2&orderby=date&order=DESC` | allow | 20 (Jul 2021 – Aug 2026) | 15/15/6 | "District Links" lists. `match`, not `search`. |
| `https://www.washingtonblade.com/?s=foggy+bottom&feed=rss2&orderby=date&order=DESC` | allow | 10 (Nov 2024 – Jul 2026) | 7/3/0 | Skip. Good reject-list test (§0.2), weak source. |
| PoPville p3 | allow | 20 | 0/1/0 | Alibi Club, via the I St address rule. |

Not usable:
- `foggybottomnews.org` no DNS. Foggy Bottom News is the FBA's newsletter; the blog feed above is the online side (per the FBA's site, not independently checked).
- `gwtoday.gwu.edu/rss.xml` 404. `westendcitizens.org` no DNS. No Foggy Bottom-West End Main Street site found.
- `wtop.com/tag/george-washington-university/feed/`: national and sports (2/0/0). `wtop.com/tag/kennedy-center/feed/`: national, outside the HPN. `wtop.com/tag/west-end/feed/`: stale (Feb 2025) and mixes other cities' West Ends.
- `dupontcircleanc.net` (ANC 2B): not added; 2B is 11% and it's Dupont's. ANC 2C's feed (`anc2c.dc.gov`) is meetings only.

```python
"foggybottom": [
    ("Foggy Bottom Association", "https://www.foggybottomassociation.org/blog-feed.xml", "https://www.foggybottomassociation.org/", "all"),
    ("ANC 2A", "https://anc2a.org/feed/", "https://anc2a.org/", "all"),
    ("Golden Triangle BID", "https://goldentriangledc.com/feed/", "https://goldentriangledc.com/", "all"),
    ("GW Hatchet", "https://gwhatchet.com/feed/", "https://gwhatchet.com/", "match"),  # Crawl-delay 6; never a query string here
    ("WTOP", "https://wtop.com/tag/foggy-bottom/feed/", "https://wtop.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="foggy+bottom"), "https://thedcline.org/", "match"),
    ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="foggy+bottom"), "https://www.washingtonian.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| FRESHFARM Foggy Bottom | existing layer | Listed, `unscheduled` (§0.1). |
| **ANC 2A** | `https://anc2a.org/feed/` | **Yes, for meetings close at hand.** Title regex below matched 10 of 10. Agendas go up only days before. `ANC_FEEDS` needs a second title pattern, since `AGENDA` expects "October 8, 2026 Meeting Agenda". ANC 2A meets the third Wednesday (from the agenda dates). |
| ANC 2A Tribe | `https://anc2a.org/wp-json/tribe/events/v1/events` | Plugin on, **total 0**. Re-check later; if it fills, it drops into `TRIBE`. |
| Golden Triangle BID | `/wp-json/tribe/…` 404 | No calendar API. |
| FBA events | Wix `/event-details/…` | HTML only. Link. |
| Kennedy Center, Lisner | not tested | Kennedy Center is outside the HPN anyway. |
| OANC | `https://oanc.dc.gov/rss.xml` | Filter 2A, 2B, 2C. None today. |

```python
AGENDA_2A = re.compile(r"^ANC 2A Agenda for (?:Tomorrow )?\w+,? ([A-Z][a-z]+ \d{1,2}, \d{4}) (?:Regular|Emergency|Special) Meeting")
ANC_FEEDS["foggybottom"] = ("ANC 2A", "https://anc2a.org/feed/", "https://anc2a.org/")  # needs AGENDA_2A; build_anc only knows AGENDA
ANCS["foggybottom"] = ["2A", "2B", "2C"]
LINKS["foggybottom"] = [
    {"name": "ANC 2A meetings", "url": "https://anc2a.org/meetings/"},
    {"name": "Foggy Bottom Association", "url": "https://www.foggybottomassociation.org/"},
    {"name": "Golden Triangle BID", "url": "https://goldentriangledc.com/"},
    {"name": "West End Library events", "url": "https://dclibrary.libnet.info/events?l=West%20End%20Neighborhood%20Library"},
]
```
West End Library (2301 L St NW) is just outside the HPN (GEORGETOWN EAST) and is still the nearest branch.

---

## 3. Hill East (HPN `HILL EAST`; ANC 6B ~72% + 7D ~27%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://www.hillrag.com/wp-json/wp/v2/posts?search=hill+east&per_page=20&_fields=date,title,excerpt,link` | allow, **Crawl-delay 20** | 20 (13 Sep – 27 Oct 2026) | 1/1/0 | WordPress treats the words separately, so most of the 20 are just Capitol Hill. `match` stays strict. "Change in Hill East: Plans for RFK, Reservation 13 and the DC Armory" is the one you want, and it goes to Stadium-Armory's count too. Needs the WP-JSON path `parse_feed` already has. |
| `https://thehillishome.com/feed/` | allow | 5 (22 Oct – 2 Nov 2026) | 3/0/0 | Weekly lists: "From the MPD Blotter", "Hill Buzz". The Hill Buzz body hits are real, but `match` won't see them. **Worth `search` mode here**, since it's a hyper-local outlet. |
| `https://www.capitolhillcorner.org/feed/` (redirects to `capitolhillcorner.org`) | allow | 10 (22 Oct – 2 Nov 2026) | 0 today | Busy, reliable on ANC 6B. `match`. |
| PoPville p1 | allow | 20 | 2/1/0 | Open-house list via the address rule. |
| `https://thedcline.org/?s=stadium-armory&feed=rss2&orderby=date&order=DESC` | allow | 11 (2018 – May 2026) | 3/3/3 | "Hill East redevelopment lands $70M in financing" is 2021; all three hits are old. Slow. |

Not usable:
- **There's no Hill East outlet.** `thehillishome.com/category/hill-east/feed/`: newest Oct 2020. `capitolhillcorner.org/tag/hill-east/feed/`: 2 items, 2014.
- `wtop.com/tag/hill-east/feed/`, `reservation-13`, `dc-jail`: 200 with 0 items. PoPville tag 0 items.
- `hilleastcivicassociation.org` (Squarespace): no collection RSS at `/news`, `/events`, `/blog`, `/calendar`; all 404. It has a home page. I didn't read its sitemap.
- ANC 6B: `anc6b.org/feed/` has 2 items (newest Nov 2023), Crawl-delay 10. `anc6b.dc.gov` no DNS. ANC 7D below.
- Washingtonian `?s=hill+east` scores 0 for Hill East. DC Line `?s=hill+east` (20 items, Mar 2025 – Sep 2026) scores 0 too: a word-split search.

```python
"hilleast": [
    ("Hill Rag", "https://www.hillrag.com/wp-json/wp/v2/posts?search=hill+east&per_page=20&_fields=date,title,excerpt,link", "https://www.hillrag.com/", "match"),  # Crawl-delay 20
    ("The Hill is Home", "https://thehillishome.com/feed/", "https://thehillishome.com/", "search"),
    ("Capitol Hill Corner", "https://www.capitolhillcorner.org/feed/", "https://www.capitolhillcorner.org/", "match"),
    ("ANC 7D", "https://anc7d.dc.gov/rss.xml", "https://anc7d.dc.gov/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| Congressional Cemetery | see §6 | Across the HPN line, belongs to Stadium-Armory. Could appear here as "nearby". |
| Hill Center | `https://www.hillcenterdc.org/wp-json/tribe/events/v1/events` | Works, 667 events, classes. It's at 921 Pennsylvania Ave SE, Capitol Hill HPN. Don't add. |
| CHRS | `https://www.chrs.org/wp-json/tribe/events/v1/events` | Works, 3 events, committee meetings at 420 10th St SE and the Northeast Library. Capitol Hill. Don't add. |
| ANC 6B | `anc6b.org/wp-json/tribe/…` 404; `/calendar/` HTML, Crawl-delay 10 | Link. OANC carries 6B when it posts: today's items are 2025 meetings re-posted 27 Oct 2026, which the date filter drops. |
| ANC 7D | `https://anc7d.dc.gov/rss.xml` | See §4. |
| Capitol Hill BID | `capitolhillbid.org/wp-json/tribe/…` redirects to the home page; `/things-to-do/calendar` HTML | No API. |

```python
ANCS["hilleast"] = ["6B", "7D"]
LINKS["hilleast"] = [
    {"name": "Southeast Library events", "url": "https://dclibrary.libnet.info/events?l=Southeast%20Neighborhood%20Library"},
    {"name": "ANC 6B calendar", "url": "https://anc6b.org/calendar/"},
    {"name": "ANC 7D", "url": "https://anc7d.dc.gov/"},
    {"name": "Hill East Civic Association", "url": "https://hilleastcivicassociation.org/"},
]
```

---

## 4. Kingman Park (HPN `KINGMAN PARK`; ANC 7D ~52% + 6A ~47%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://www.hillrag.com/wp-json/wp/v2/posts?search=kingman&per_page=20&_fields=date,title,excerpt,link` | allow, **Crawl-delay 20** | 20 (22 Oct 2025 – 12 Oct 2026) | 5/5/5 | "Don't Miss the Kingman Island Teen Band Festival", "Rosedale Pool Reopens After $6.8 Million Renovation". Best available. |
| `https://anc7d.dc.gov/rss.xml` (OANC Drupal; the site is new per its own 30 Aug post) | allow | 10 (23 Jun – 28 Oct 2026) | 6/6/3 | "ANC 7D RFK Master Plan Submission to DC Office of Planning". Half its nodes are commissioner profiles, which `match` drops only if they don't say "ANC 7D"; three do. Filter URL `/commissioner/` if it bothers you. `match`. |
| `https://www.capitolhillcorner.org/feed/` | allow | 10 | 1/1/1 | Maury Elementary Fall Fest. |
| `https://wtop.com/tag/kingman-island/feed/` | allow | 6 (2017 – 28 Sep 2024) | 6/6/2 | Slow, mostly cleanups. Clean when it fires. |
| `https://thedcline.org/?s=kingman+park&feed=rss2&orderby=date&order=DESC` | allow | 20 (Aug 2019 – May 2024) | 11/11/5 | **Stale.** |
| `https://www.washingtonian.com/?s=kingman+park&feed=rss2&orderby=date&order=DESC` | allow | 10 | 8/0/0 | Body hits, roundups. Skip. |

Not usable:
- No Kingman Park Civic Association or Friends of Kingman Park site found. `kingmanpark.org`: 404s. `kingmanparkcivic.org`, `kingmanparkcivicassociation.org`: no DNS.
- `wtop.com/tag/kingman-park/feed/`: 0 items.
- `kingmanisland.com/calendar?format=rss` carries Kingman Island events with creation dates (18/16/14). It would read as news about charrettes from three months ago. Use it for Links only.
- ANC 6A: `anc6a.org/feed/` newest **Feb 2015**. `anc6a.dc.gov` no DNS.
- `hstreet.org/feed/`: 200 with 0 items.

```python
"kingmanpark": [
    ("Hill Rag", "https://www.hillrag.com/wp-json/wp/v2/posts?search=kingman&per_page=20&_fields=date,title,excerpt,link", "https://www.hillrag.com/", "match"),  # Crawl-delay 20
    ("ANC 7D", "https://anc7d.dc.gov/rss.xml", "https://anc7d.dc.gov/", "match"),
    ("WTOP", "https://wtop.com/tag/kingman-island/feed/", "https://wtop.com/", "match"),
    ("Capitol Hill Corner", "https://www.capitolhillcorner.org/feed/", "https://www.capitolhillcorner.org/", "match"),
    ("The Hill is Home", "https://thehillishome.com/feed/", "https://thehillishome.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| RFK Open Air Market | existing layer | **Dated** (Saturdays, May to December). |
| **ANC 7D** | `https://anc7d.dc.gov/rss.xml` | **Yes, parse the body** with the regex from SOURCES-CENTRAL, slightly loosened: `Date and Time\s+\w{3}, (\w{3}) (\d{1,2}) (\d{4}),?\s+([\d:]+\s*(?:-\s*[\d:]+\s*)?[ap]m)?`. Today it reads "Transportation and Public Space Committee Meeting" (Oct 28, 7–8 pm), "Zoning and Alcoholic Beverage Licensing Committee" (Oct 20, 6:30–8:30). The full meetings ("November 10, 2026 ANC 7D Virtual Meeting", "December 8…") are on its home page but past the feed's newest 10. Bodies may carry Zoom details, so never store body text. Engine change needed. |
| Kingman + Heritage Islands | `https://www.kingmanisland.com/calendar` (Squarespace) | **No API we may use.** `?format=rss` has no event dates. `?format=ical` is **robots-disallowed**. The HTML has `<time class="event-date" datetime=…>`, and scraping that is your call. Link for now. |
| Anacostia Watershed Society | `https://www.anacostiaws.org/wp-json/tribe/events/v1/events` | Works, 3 events: Anacostia Park and Colmar Manor. Not in the area. Don't add. |
| H Street Main Street | `https://hstreet.org/wp-json/tribe/events/v1/events` | Works. In the next 30 days only the 800 13th St NE market, 4 Saturdays. For the live H Street site, not this one. |
| Rosedale Rec | DPR | Not tested. |

```python
ANCS["kingmanpark"] = ["6A", "7D"]
LINKS["kingmanpark"] = [
    {"name": "Rosedale Library events", "url": "https://dclibrary.libnet.info/events?l=Rosedale%20Neighborhood%20Library"},
    {"name": "Kingman and Heritage Islands calendar", "url": "https://www.kingmanisland.com/calendar"},
    {"name": "ANC 7D", "url": "https://anc7d.dc.gov/"},
    {"name": "ANC 6A calendar", "url": "https://anc6a.org/community-calendar/"},
]
```

---

## 5. Mount Pleasant (HPN `MOUNT PLEASANT`; ANC 1D ~99%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/mount-pleasant/feed/` | allow | 10 (Nov 2020 – 30 Mar 2026) | 10/10/3 | "Longtime DC child care program scrambles to raise funds to continue to operate in Mount Pleasant". All DC. `match`. |
| **`https://www.historicmountpleasant.org/feed/`** | allow, **Crawl-delay 20** | 10 (Dec 2023 – 5 Jun 2026) | 10/10/5 | "100 Years of the Mount Pleasant Branch Public Library". About two a year. All local, so `all`. |
| `https://districtbridges.org/feed/` | allow | 10 (May 2025 – 15 Oct 2026) | 3/3/1 | "Bring Back Mount Pleasant Streateries". District Bridges runs the Main Street. `match`. Note its other posts are Cleveland Park and citywide. |
| `https://www.washingtonian.com/?s=mount+pleasant&feed=rss2&orderby=date&order=DESC` | allow | 10 (3 Sep – 12 Oct 2026) | 9/1/0 | "Michelin Adds 4 New Restaurants to Its DC Guide". Optional. |
| PoPville p1 | allow | 20 | 1/0/0 | Covers it often; one body hit today. |
| `https://thedcline.org/?s=mount+pleasant&feed=rss2&orderby=date&order=DESC` | allow | 20 (May 2021 – Mar 2024) | 10/10/8 | **Stale.** |
| `https://wtop.com/tag/mt-pleasant/feed/` | allow | 2 (2016 – Jan 2020) | 2/2/2 | Dead tag. |

Not usable:
- `mountpleasantdc.org` (`www.` too): **robots-disallowed** for our agent, whole site. Not fetched.
- `mtpleasantdc.org`: certificate mismatch; `www.mtpleasantdc.org/feed/` is 4 Danish and Norwegian **car-rental spam** posts. Don't link.
- `mountpleasantmainstreet.org`: connection timeout. `mtpleasantmainstreet.org`: redirects to Mount Pleasant City, **Utah**.
- `mountpleasantvillage.org/feed/`: 200 with 0 items. `mountpleasant.helpfulvillage.com`: no DNS from here.
- `mountpleasantfarmersmarket.org` no DNS; `mtpfm.org` timeout.
- ANC 1D: `anc1d.org/feed/` 404. `?format=rss` on `/newsletter`, `/meeting-records` gives 400. `anc1d.dc.gov` no DNS.

```python
"mountpleasant": [
    ("Historic Mount Pleasant", "https://www.historicmountpleasant.org/feed/", "https://www.historicmountpleasant.org/", "all"),  # Crawl-delay 20
    ("WTOP", "https://wtop.com/tag/mount-pleasant/feed/", "https://wtop.com/", "match"),
    ("District Bridges", "https://districtbridges.org/feed/", "https://districtbridges.org/", "match"),
    ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="mount+pleasant"), "https://www.washingtonian.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| Mount Pleasant Farmers' Market | existing layer | Listed, `unscheduled` (§0.1). |
| **ANC 1D** | `https://anc1d.org/meetingcalendar` (Squarespace) | **Partial.** `?format=rss` is allowed but its pubDates are creation dates, and items have no event date, though titles name the month ("November Meeting of ANC1D"). `?format=ical` is **robots-disallowed**. The monthly meeting is the third Tuesday: the HTML page's `<time class="event-date">` shows 17 Nov 2026, 15 Dec 2026, 19 Jan 2027. Month from the title plus third Tuesday works, the same trick as ANC 2G in SOURCES-CENTRAL. Committee of the Whole titles have no month. Items carry Zoom links, so keep only title and date. |
| District Bridges | `/wp-json/tribe/…` 404 | Link, already in `LINKS["ustreet"]`. |
| Mount Pleasant Library | DCPL | Link only. |
| Mount Pleasant Village | `/events/` points to a Helpful Village site that didn't resolve | Link. |

```python
ANCS["mountpleasant"] = ["1D"]
LINKS["mountpleasant"] = [
    {"name": "Mt. Pleasant Library events", "url": "https://dclibrary.libnet.info/events?l=Mt.%20Pleasant%20Neighborhood%20Library"},
    {"name": "ANC 1D meetings", "url": "https://anc1d.org/meetingcalendar"},
    {"name": "District Bridges events", "url": "https://districtbridges.org/events/"},
    {"name": "Mount Pleasant Village", "url": "https://mountpleasantvillage.org/events/"},
]
```

---

## 6. Stadium-Armory (HPN `STADIUM ARMORY`; ANC 7D ~47% + 7F ~34% + 6B ~18%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| **`https://www.hillrag.com/wp-json/wp/v2/posts?search=rfk&per_page=20&_fields=date,title,excerpt,link`** | allow, **Crawl-delay 20** | 20 (6 May – 2 Nov 2026) | 9/9/6 | **Best source.** "Bowser Unveils RFK Campus Plan. Next Stop, DC Council", "Six New Neighborhoods Planned For RFK", "ANC 7D Objects to Proposed RFK Bus Facility". `match`. |
| **`https://thedcline.org/?s=rfk&feed=rss2&orderby=date&order=DESC`** | allow | 20 (Jul 2025 – 7 Oct 2026) | 15/15/11 | "District Links: Bowser admin submits updated RFK master plan…". No RFK Jr. in the DC Line's 20. `match`. |
| **`https://www.congressionalcemetery.org/feed/`** (redirects to `congressionalcemetery.org`) | allow | 10 (5 Mar – 8 Oct 2026) | 10/10/4 | "Congressional Cemetery is now a Level 1 Arboretum!". All inside, `all`. |
| `https://www.hillrag.com/wp-json/wp/v2/posts?search=congressional+cemetery&per_page=20&_fields=date,title,excerpt,link` | allow, Crawl-delay 20 | 20 (21 Apr – 27 Oct 2026) | 15/15/13 | Mostly the paper's calendar notices ("Dead Man's Run at Congressional Cemetery"). Optional. |
| `https://wtop.com/tag/rfk-stadium/feed/` | allow | 10 (Feb 2025 – 11 Jul 2026) | 10/10/5 | "DC police announce weekend youth curfew zone near RFK Stadium". `match`. |
| `https://wtop.com/tag/congressional-cemetery/feed/` | allow | 10 (2013 – 23 Oct 2025) | 10/10/5 | "Grave robbers, body snatchers and tales of old…". `match`. |
| `https://wtop.com/tag/dc-armory/feed/` | allow | 6 (Jan 2020 – 12 Aug 2025) | 6/6/3 | "National Guard members report to DC Armory…". `match`. |
| `https://anc7d.dc.gov/rss.xml` | allow | 10 | 6/6/3 | See §4. |
| `https://www.washingtonblade.com/?s=congressional+cemetery&feed=rss2&orderby=date&order=DESC` | allow | 10 (May 2024 – Jun 2026) | 9/5/2 | "Congressional Cemetery hosts Gays & Graves". Optional. |

Not usable:
- **`wtop.com/tag/rfk/feed/` mixes politics** (9 items, 2014–2025). The rules hold, but there's no reason to read it.
- **`washingtonian.com/?s=rfk`: mostly RFK Jr. and Reflecting Pool roundups.** 1/0/0. Skip.
- `wtop.com/tag/stadium-armory/feed/`: 4 items, newest 2021. `rfk-site`: 0 items.
- DC Line `?s=congressional+cemetery`: newest Oct 2023.
- ANC 7F: no site found. `anc7f.org`, `www.anc7f.org`, `anc7f.dc.gov`: no DNS. OANC is the only source.
- Events DC: `eventsdc.com/feed/` 404; Drupal, no RSS link on the home page.

```python
"stadiumarmory": [
    ("Historic Congressional Cemetery", "https://www.congressionalcemetery.org/feed/", "https://www.congressionalcemetery.org/", "all"),
    ("Hill Rag", "https://www.hillrag.com/wp-json/wp/v2/posts?search=rfk&per_page=20&_fields=date,title,excerpt,link", "https://www.hillrag.com/", "match"),  # Crawl-delay 20
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="rfk"), "https://thedcline.org/", "match"),  # never "search": RFK Jr.
    ("ANC 7D", "https://anc7d.dc.gov/rss.xml", "https://anc7d.dc.gov/", "match"),
    ("WTOP", "https://wtop.com/tag/rfk-stadium/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/congressional-cemetery/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/dc-armory/feed/", "https://wtop.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **Historic Congressional Cemetery** | `https://www.congressionalcemetery.org/wp-json/tribe/events/v1/events` (`?ical` not needed) | **Yes.** 121 upcoming, 16 in the next 30 days. "Death Cafe at Congressional Cemetery" (5 Nov 18:00), "John Philip Sousa Birthday Concert 2026" (6 Nov 12:30), "Tombs and Tomes Book Club November". Drop "Closed to Dogs", "Private Funeral Service" and "Office Closed for Federal Holiday" with the skip regex below; SOURCES-EAST saw the closure entries too. |
| ANC 7D | as §4 | Body-date parser needed. |
| ANC 7F, ANC 6B | `https://oanc.dc.gov/rss.xml` | Title filter. A search-engine listing shows 7F meets at Marshall Heights Community Center, outside this area, usually the third Tuesday. Not verified on an official page. |
| Events DC / RFK campus / DC Armory | `eventsdc.com/events` | HTML. Terms not reviewed. Link. |
| RFK Open Air Market | existing layer, KINGMAN PARK | Across the line (2615 Benning Rd NE). |

```python
TRIBE["congcem"] = ("Historic Congressional Cemetery", "https://www.congressionalcemetery.org/wp-json/tribe/events/v1/events",
                    "https://www.congressionalcemetery.org/", r"closed to dogs|private funeral|office closed|cemetery closed", 0)
CALENDARS["stadiumarmory"] = ["congcem"]
ANCS["stadiumarmory"] = ["7D", "7F", "6B"]
LINKS["stadiumarmory"] = [
    {"name": "ANC 7D", "url": "https://anc7d.dc.gov/"},
    {"name": "DC Office of ANCs calendar (ANC 7F)", "url": "https://oanc.dc.gov/"},
    {"name": "Events DC events", "url": "https://eventsdc.com/events"},
    {"name": "Kingman and Heritage Islands calendar", "url": "https://www.kingmanisland.com/calendar"},
]
```

---

## 7. Trinidad (HPN `TRINIDAD`; ANC 5D ~85% + 5C ~15%)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/ivy-city/feed/` | allow | 10 (Aug 2020 – 19 Apr 2026) | 10/10/2 | "DC's newest medical cannabis dispensary opens ahead of 4/20". `match`. |
| `https://wtop.com/tag/union-market/feed/` | allow | 10 (Feb 2024 – 8 Sep 2025) | 10/10/4 | "Country and western bar brings line dancing…to Union Market warehouse". `match`. |
| `https://wtop.com/tag/trinidad/feed/` | allow | 10 (Aug 2014 – 4 Apr 2025) | 9/6/0 | All DC, mostly crime. WTOP's tag is good. `match`. |
| `https://thedcline.org/?s=ivy+city&feed=rss2&orderby=date&order=DESC` | allow | 20 (May 2021 – 22 Jun 2026) | 12/12/7 | `match`. |
| `https://thedcline.org/?s=union+market&feed=rss2&orderby=date&order=DESC` | allow | 20 (Jan 2022 – 19 Jun 2026) | 6/6/5 | `match`; "union" and "market" split, hence 6 of 20. |
| `https://www.hillrag.com/wp-json/wp/v2/posts?search=trinidad&per_page=20&_fields=date,title,excerpt,link` | allow, Crawl-delay 20 | 20 (May 2020 – 12 Oct 2026) | 2/2/0 | "Trinidad (organic) Farmers Market". Hill Rag's general `/feed/` today has "Discover 'The ROW' at Union Market", so Hill Rag does cover it. |
| `https://www.washingtonian.com/?s=union+market&feed=rss2&orderby=date&order=DESC` | allow | 10 (28 Sep – 16 Oct 2026) | 7/0/0 | Body-only roundups. Skip. |
| `https://www.washingtonian.com/?s=ivy+city&feed=rss2&orderby=date&order=DESC` | allow | 10 (Jun – Aug 2026) | 7/2/0 | "No Phones Allowed at DC's Newest Dance Club". Optional. |
| PoPville p2–p3 | allow | 40 | 2/1/0 | A. Litteri (Union Market). |

Not usable:
- `www.gallaudet.edu/feed/`: **robots-disallowed**.
- `unionmarketdc.com/feed/`: 200 with 0 items. `/news/` is HTML.
- `trinidadneighborhood.org`: 114-byte page with no content, at `/` and `/feed/`. `trinidaddc.org` refused; `www.trinidaddc.com` is a single-page app I couldn't read, with `/feed/` 404. `ivycitydc.org` TLS error.
- ANC 5D: `anc5d.org` (Squarespace, title still "Your Site Title"), `/feed/` 404, `?format=rss` 400 on `/newsletters` and `/meeting-minutes`. `anc5d.dc.gov` no DNS. ANC 5C: `anc5c.org`, `anc5c.dc.gov` no DNS.
- `wtop.com/tag/gallaudet-university/feed/`: 1/1/0. Skip. `wtop.com/tag/hechinger-mall/feed/` 0 items. DC Line `?s=trinidad` 2/2/2, newest Jul 2023. DC Line `?s=gallaudet` newest Jul 2023.

```python
"trinidad": [
    ("WTOP", "https://wtop.com/tag/ivy-city/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/union-market/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/trinidad/feed/", "https://wtop.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="ivy+city"), "https://thedcline.org/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="union+market"), "https://thedcline.org/", "match"),
    ("Hill Rag", "https://www.hillrag.com/wp-json/wp/v2/posts?search=trinidad&per_page=20&_fields=date,title,excerpt,link", "https://www.hillrag.com/", "match"),  # Crawl-delay 20
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    *SHARED,
],
```
`TERMS["trinidad"]` must be compiled **without `re.I`**.

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **Union Market District** | `https://unionmarketdc.com/wp-json/tribe/events/v1/events` (`www.` redirects; `/events/?ical=1` is advertised, not tested) | **Yes, plenty.** 64 upcoming, **44 in the next 30 days**, so `per_page=50` holds for now. "Union Market Holiday Tree Lighting", "LEDC Holiday Market", "The ROW Opening Party" (5 Nov, 1348 4th St NE). Venues: La Cosecha 20, Union Market 12, Galería 4, Shelter 3. **It will swamp this page**: 8 "DC Mural Tour", 4 "R&B & Gnocchi Nights", and a dozen cooking classes. Its 3 "FreshFarm Farmers Market" entries duplicate the layer, so the skip regex removes them. I also drop classes and tours below. Your call: delete that part and you get all 44. |
| FRESHFARM Union Market, Trinidad Farmers Market | existing layer | Union Market dated, Trinidad `unscheduled` (§0.1). |
| ANC 5D | `www.anc5d.org` embeds Google Calendar `dcanc5d@gmail.com` | `calendar.google.com/calendar/ical/…` was already found **robots-disallowed** in SOURCES-CENTRAL. Not tried. Link. |
| ANC 5C | OANC | Title filter. |
| Gallaudet | Not tested beyond `/feed/` | Robots blocks that path. Link only. |
| Dock 5, Trinidad Rec | None tested | Unknown |

```python
TRIBE["unionmarket"] = ("Union Market District", "https://unionmarketdc.com/wp-json/tribe/events/v1/events", "https://unionmarketdc.com/events/",
                        r"freshfarm|cooking\s+class|making\s+class|mural\s+tour|gnocchi|pasta|dumpling|mozzarella|focaccia|tapas|tagliatelle|ravioli|run\s+club", 0)
CALENDARS["trinidad"] = ["unionmarket"]
ANCS["trinidad"] = ["5D", "5C"]
LINKS["trinidad"] = [
    {"name": "ANC 5D", "url": "https://www.anc5d.org/"},
    {"name": "Union Market District events", "url": "https://unionmarketdc.com/events/"},
    {"name": "Rosedale Library events", "url": "https://dclibrary.libnet.info/events?l=Rosedale%20Neighborhood%20Library"},
    {"name": "Gallaudet University", "url": "https://www.gallaudet.edu/"},
]
```
5C holds only by area (5C04, Mount Olivet), not by centroid. `setup_hood.py` will say `["5D"]`. Add 5C if you want the cemetery side's notices, though there's almost nobody there.

---

## 8. Woodley Park (ANC 3C01, 3C02, 3C03, 3C07)

### NEWS

| Feed (exact URL) | robots | items | hits (b/s/t) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/woodley-park/feed/` | allow | 10 (29 Apr 2024 – 22 Apr 2026) | 10/10/2 | **Best clean source.** "Macintyre's Pub to permanently close", "New Woodley Park flea market aims for quirky vendors", and zoo stories tagged here ("Giant pandas debut"). `match`. |
| `https://anc3c.dc.gov/rss.xml` | allow | 10 (30 Jun – 19 Oct 2026) | 2/2/2 | "Woodley Park Day 2026", "Cleveland and Woodley Park Main Street Holiday Market". **`match` here, not `all`:** the rest is committee meetings for all of 3C. `clevelandpark` reads this feed as `all`. |
| `https://thedcline.org/?s=woodley+park&feed=rss2&orderby=date&order=DESC` | allow | 20 (Apr 2021 – 8 May 2026) | 12/12/3 | "UrbanTurf: A First Look at the 900 Apartments Proposed for DC's Wardman Marriott Site in Woodley Park". The most recent 3 hits are older. `match`. |
| PoPville p1 | allow | 20 | 1/1/1 | "Elevator at Woodley Park Metro Out until 11/14?" |
| `https://www.washingtonian.com/?s=woodley+park&feed=rss2&orderby=date&order=DESC` | allow | 10 (Mar – 28 Sep 2026) | 9/0/0 | Roundups. Skip. |
| `https://wtop.com/tag/national-zoo/feed/` | allow | 10 (Nov 2025 – 9 Jul 2026) | 1/1/0 | Animal stories; the rule keeps one. Skip the feed. |
| `https://foresthillsconnection.com/feed/`, `https://www.cpcadc.org/feed/` | allow | 10 each | 0 | Neither touches Woodley Park today. Skip. |

Not usable:
- **`woodleyparkmainstreet.org/feed/`**: 10 items, all dated Feb–May 2025. The site looks repurposed. "Beat the Heat: The Importance of HVAC Maintenance for Midwest Summers" and "Georgetown Bagel Shop Faces Backlash from Neighbors" sit under a "Woodley Park News" banner. A 2022 City Paper headline says the council moved to strip Main Street funding. I can't confirm who runs it now. Don't use it or link it. It would score 10/10/1 because of site boilerplate.
- **`woodleypark.org` redirects to Glover Park Main Street**, whose own `/feed/` is 4 items from Aug 2020.
- Woodley Park Community Association: `wpcaonline.org`, GoDaddy static site, `/feed/` 404, updates as PDFs. No machine-readable anything. Link.
- National Zoo: `/feed/`, `/rss.xml`, `/news/rss.xml` 404; `/animals/news/rss.xml` returns HTML.
- WTOP `woodley-park-main-street` tag: 0 items.

```python
"woodleypark": [
    ("WTOP", "https://wtop.com/tag/woodley-park/feed/", "https://wtop.com/", "match"),
    ("ANC 3C", "https://anc3c.dc.gov/rss.xml", "https://anc3c.dc.gov/", "match"),  # all of 3C, so filtered here
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="woodley+park"), "https://thedcline.org/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| Maret School Farmers Market | existing layer, 3C07 | Listed, `unscheduled` (§0.1). FRESHFARM Cleveland Park is 3C05, outside. |
| **ANC 3C** | `https://anc3c.dc.gov/rss.xml` | **Yes, body-date parser.** Same `Date and Time …` regex. Today: "Cleveland and Woodley Park Main Street Holiday Market" (**12 Dec 2026**, no time given), "Woodley Park Day 2026" (19 Sep), committee meetings through Jan 2027 ("ANC 3C Public Safety Committee", 12 Nov, 7–8 pm). This is the only machine source for those two neighborhood events. SOURCES-WEST reached the same feed with a different regex. |
| National Zoo | `nationalzoo.si.edu/events`, no feed found | Link. ZooLights not checked. |
| WPCA | `wpcaonline.org/calendar.htm` | Static. Link. |

```python
ANCS["woodleypark"] = ["3C"]
LINKS["woodleypark"] = [
    {"name": "ANC 3C calendar", "url": "https://anc3c.dc.gov/anc-calendar"},
    {"name": "Woodley Park Community Association", "url": "https://wpcaonline.org/"},
    {"name": "National Zoo events", "url": "https://nationalzoo.si.edu/events"},
    {"name": "Cleveland Park Library events", "url": "https://dclibrary.libnet.info/events?l=Cleveland%20Park%20Neighborhood%20Library"},
]
```
`setup_hood.py` gives `["3C"]` from SMD centroids. Cleveland Park Library is 3C05, the nearest branch, outside the boundary.

---

## 9. HISTORY (Evening Star, loc.gov, week 1926-10-31 → 11-06)

loc.gov answered our UA normally. Query shape is the one in `history.py`: `q`, `dates=1926-10-31/1926-11-06`, `fa=partof_title:evening star (washington, d.c.) 1854-1972`, `fo=json`. I read OCR for the top 3 pages per term. "Week" is the page count for the target week. A few terms in the final entries (`"McMillan"`, `"Twenty-first street"`, `"Twenty-third street"`, `"Thirteenth street southeast"`, `"Mount Pleasant Citizens"`, `"Mount Pleasant Library"`, `"Irving street"`, `"Trinidad avenue"`, `"Gallaudet College"`, `"Montello"`) went through only that engine run, so they have no count of their own.

I then ran each final entry through the engine's own `history.build_archive` with `ARCHIVE` patched in memory (no project file changed). "Clips" below is what that function returned for this week, with all its filters on.

| Area | Clips (max 6) | Screened |
|---|---|---|
| Bloomingdale | 6 | 0 |
| Foggy Bottom | 3 | 0 |
| Hill East | 1 | 0 |
| Kingman Park | 1 | 0 |
| Mount Pleasant | 6 | 0 |
| Stadium-Armory | 2 | 0 |
| Trinidad | 3 | 1 |
| Woodley Park | 6 | 0 |

These are one week's numbers. Expect some weeks at 0 for Hill East and Kingman Park. On my first full run, Foggy Bottom, Hill East and Stadium-Armory all returned 0 with "No usable mentions" and an unchanged config gave 3, 1 and 2 on a rerun. `build_archive` skips a page silently when its OCR won't load, so I assume loc.gov was slow or refusing during that first run. That's an inference, not something I saw. A cached week from a bad night would stay empty, and `prefetch_archive.py` may be the place to retry.

**Pitfalls specific to these areas:**
1. **Single-letter words get dropped** (`"H street"` style), so I used spelled-out long forms and left block-level precision to `pattern`.
2. **Names that weren't in use, or weren't there yet.**
   - "Foggy Bottom", "Hill East", "Kingman Lake", "Kingman Park", "Anacostia Park", "Reservation 13", "Washington Asylum", "Mount Alto", "McMillan Park", "Lamont street", "Montello avenue", "Kentucky avenue", "Trinidad Citizens" and "Florida avenue northeast": **all 0 pages this week.** Zero in one week doesn't mean unused in 1926. The Washington Asylum did exist under that name earlier; by 1926 the paper says Gallinger.
   - RFK Stadium is 35 years off, so Stadium-Armory is the cemetery, the jail and Gallinger Municipal Hospital.
   - Union Market's predecessor isn't in this week's paper under any name I tried.
3. **Bare "Trinidad" is shipping news.** The ship-arrival lists pair a ship with "Trinidad Oct. 23". SOURCES-EAST found the same. Only "Trinidad ave. n.e." and its like count.
4. **The Star wrote about Ivy City in terms the screen blocks.** The 5 Nov piece headed "Ivy City Citizens Urge Colored Police Branch" is the single best local story of the week and exactly what SCREEN holds back. The clip that survives from that piece is about a firm planning 100 houses in Ivy City. Trinidad's "screened 1" is that article. It needs an editor's note, not a regex.
5. **Death notices flood two of these.** "Congressional Cemetery" and "Mount Olivet" are mostly "Interment…" lines, and "Gallinger Hospital" is mostly the daily deaths list. They name private individuals. The reject lists drop them, leaving little.
6. **"Mt. Pleasant" is three things:** a rooms-for-rent heading (41 pages), a Maryland Grange town and a Masonic lodge (No. 33). Only the institution forms and block addresses count. "Mount Pleasant Citizens' Association will meet… at Mount Pleasant Public Library" is the good kind.
7. **Foggy Bottom in the classifieds.** "Washington Circle" (9 pages) and "Twenty-first street" are mostly apartment ads, which the engine's legibility score already rejects. GW sports dominate "George Washington University". The sports reject list copies U Street's.

### Bloomingdale

| Term | Week | What the snippets show |
|---|---|---|
| `"Eckington"` | 8 | **The farmers' market site fight**: the B&O backing the Eckington site, and Ivy City's citizens endorsing it. Same story as NoMa's history section; Eckington is inside this HPN too. |
| `"North Capitol street"` | 8 | A fatal crash near Randolph place, addresses, permits. Needs the block filter. |
| `Bloomingdale` | 3 | Children's Halloween basketball at the **Bloomingdale playground** (4 Nov) and a playground league result (6 Nov), both in-area. Also **Bloomingdale's stock** in the ticker (3 Nov), rejected. |
| `"Rhode Island avenue northeast"` | 3 | Off target. Dropped. |
| `"First street northwest"` | 4 | One ad, and a plat "subdivision of Eckington" (legal). Dropped. |
| `"McMillan Park"` | 0 | Kept `"McMillan"` as the last term; not separately counted. |

```python
"bloomingdale": {
    "terms": ['"Eckington"', '"North Capitol street"', "Bloomingdale", '"McMillan"'],
    "pattern": r"eckington|bloomingdale\s+(playground|citizens|section|field|basket)|(at|the)\s+bloomingdale\b(?!\W+\d)|truxton\s+circle|"
               r"mcmillan\s+(park|reservoir)|filtration\s+plant|\b(1[3-9]|2[0-4])\d\d\s+north\s+capitol\s+st|north\s+capitol\s+(street\s+)?(near|and|at)\s+[p-w]\b",
    # Bloomingdale's stock, and "Eckington as per plat", which LEGAL mostly catches.
    "reject": r"bloomingdale['’]?s|bloomingdale\W+\d|as\s+per\s+plat|north\s+capitol\s+st(reet)?\s+(s\.\s?e|southeast)",
    "local": r"north\s+capitol|first\s+st|rhode\s+island\s+av|florida\s+av|lincoln\s+road|t\s+st|u\s+st|n\.\s?e\.|n\.\s?w\.|market\s+site|citizens",
},
```

### Foggy Bottom

| Term | Week | What the snippets show |
|---|---|---|
| `"Washington Circle"` | 9 | Apartment ads, plus a woman hit by a streetcar near the circle (1 Nov), and St. Paul's Church notices. The circle is in GEORGETOWN EAST by my coordinate, right at the line. |
| `"George Washington University"` | 3 | Football and cross-country, and Anson Phelps Stokes addressing students (3 Nov). |
| `"West End"` | 8 | "West end of the Key Bridge", a bank's West End Branch, Georgetown funeral parlors. **Don't use.** |
| `"Twenty-second street"` | 1 | Church directory, P and Q streets, which is outside. |
| `Heurich` | 1 | Brewery stock quote. The brewery (Kennedy Center's site, 25th and D) would be outside this HPN anyway. |
| `"Foggy Bottom"`, `"Mount Alto"` | 0 / 0 | nothing |

```python
"foggybottom": {
    # "Foggy Bottom" had 0 pages this week. GW's campus was already at 20th-21st and G.
    "terms": ['"Washington Circle"', '"George Washington University"', '"Twenty-first street"', '"Twenty-third street"'],
    "pattern": r"washington\s+circle|foggy\s+bottom|george\s+washington\s+univ|\b2[0-5]\d\d\s+(pa\.?|pennsylvania)\s+ave|\b(19|2[0-5])\d\d\s+[e-k]\s+st|"
               r"(twenty.?(first|second|third|fourth|fifth)|2[1-5](st|nd|rd|th))\s+st(reet|\.)?\s+(n\.?\s?w|northwest|and\s+(pennsylvania|virginia|new\s+hampshire|[c-l]\b)|between|near)",
    "reject": r"foot\s*ball|eleven|touchdown|gridiron|varsity|quarterback|coach|hockey|cross.country|grif\s?fith|ursinus|colonials|sigma|fraternity",
    "local": r"n\.\s?w\.|pennsylvania\s+av|pa\.\s+ave|new\s+hampshire|virginia\s+av|washington\s+circle|twenty|2[0-5]th|st\.?\s+paul|g\s+st|h\s+st|i\s+st",
},
```

### Hill East

| Term | Week | What the snippets show |
|---|---|---|
| `"Potomac avenue"` | 3 | Costume-contest address lists, 1428 Potomac Ave SE, and one in NW. |
| `"Fifteenth street southeast"` | 2 | A prize awarded to a couple at 509 Fifteenth St SE, the one clip that survives. |
| `"Massachusetts avenue southeast"` | 1 | A boy's costume list. |
| `"Lincoln Park"` | 19 | Lincoln Park Citizens' Association and house ads. West of this HPN (the live Capitol Hill site uses it). |
| `"Eastern High School"` | 16 | "1815 A St SE, near Eastern High" ads are in-area, but the school itself is KINGMAN PARK. |
| `"Hill East"`, `"Kentucky avenue"` | 0 / 0 | nothing |

```python
"hilleast": {
    "terms": ['"Potomac avenue"', '"Fifteenth street southeast"', '"Massachusetts avenue southeast"', '"Thirteenth street southeast"'],
    "pattern": r"\b1[3-9]\d\d\s+(potomac|massachusetts|independence|north\s+carolina|kentucky|pennsylvania)\s+av(enue|e)?\.?\s+(s\.?\s?e|southeast)|"
               r"(thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth)\s+st(reet|\.)?\s+(s\.?\s?e|southeast)|\b\d{2,4}\s+1[3-9]th\s+st\.?\s+s\.?\s?e|"
               r"potomac\s+av(enue|e)?\.?\s+(s\.?\s?e|southeast)|hill\s+east",
    "reject": r"interment|funeral|deaths?\s+reported|years\s+old",
    "local": r"s\.\s?e\.|southeast|potomac\s+av|kentucky\s+av|massachusetts\s+av|pennsylvania\s+av|lincoln\s+park|eastern\s+high|citizens",
},
```

### Kingman Park

| Term | Week | What the snippets show |
|---|---|---|
| `"Eastern High School"` | 16 | Inside. Staff changes (rejected as rosters), night classes, sports, apartment ads "opposite Eastern High". |
| `"Rosedale"` | 4 | "1051 Rosedale St. N.E." ads, a Rosedale playground court, and a racehorse named Miss Rosedale, rejected. |
| `"Benning road"` | 2 | 2022 Benning Road N.E. sample house (in-area) and a permit at 3957 (not). |
| `"Maryland avenue northeast"` | 4 | No in-pattern hits on sampled pages. Weak. |
| `"Kingman Lake"`, `"Kingman Park"`, `"Anacostia Park"` | 0 / 0 / 0 | nothing |

```python
"kingmanpark": {
    # "Kingman Lake", "Kingman Park", "Anacostia Park": 0 this week. Kingman Park wasn't built until the late 1920s.
    "terms": ['"Eastern High School"', '"Rosedale"', '"Benning road"', '"Maryland avenue northeast"'],
    "pattern": r"eastern\s+high|kingman\s+(lake|park)|rosedale\s+(st|playground|citizens|recreation|section)|\b(1[5-9]|2[0-5])\d\d\s+benning\s+r|"
               r"\b1[5-9]\d\d\s+(gales|rosedale|c|d|e|f|g|h|isherwood|maryland)\s+(st|ave)[a-z.]*\s+(n\.?\s?e|northeast)|seventeenth\s+and\s+east\s+capitol",
    "reject": r"foot\s*ball|eleven|touchdown|gridiron|cadet|basket\s*ball|miss\s+rosedale|furlongs|terminations?|substitute|caretaker|janitor|years\s+old|interment",
    "local": r"n\.\s?e\.|northeast|east\s+capitol|benning|maryland\s+av|rosedale|eastern\s+high|seventeenth|nineteenth",
},
```

### Mount Pleasant

| Term | Week | What the snippets show |
|---|---|---|
| `"Mount Pleasant"` | 21 | Citizens' association meeting at the library (6 Nov), a bowling league and a lodge (both rejected). |
| `"Mt. Pleasant"` | 41 | Classified headings, Maryland Grange. Not used as a term. |
| `"Irving street"` | not counted | Society and lost-and-found items at 1613–1811 blocks, through `pattern`. |
| `"Park road"` | 37 | Arcadia Auditorium at 14th and Park Road (Columbia Heights). Not used. |
| `"Lamont street"` | 0 | nothing |

```python
"mountpleasant": {
    # "Mt. Pleasant" also leads the rooms-for-rent classifieds and is a Maryland Grange town; Mount Pleasant No. 33 is a Masonic lodge.
    "terms": ['"Mount Pleasant Citizens"', '"Mount Pleasant Library"', '"Mount Pleasant"', '"Irving street"'],
    "pattern": r"mount\s+pleasant\s+(citizens|public\s+library|branch|library|street|m\.\s?e|methodist|congregational|car\s+line|section)|mt\.?\s+pleasant\s+(st|citizens|library)|"
               r"\b1[6-9]\d\d\s+(lamont|irving|kilbourne|kenyon|newton|harvard|hobart)\s+st|\b3[0-3]\d\d\s+(mount|mt\.?)\s+pleasant\s+st|shrine\s+of\s+the\s+sacred\s+heart",
    "reject": r"duckpin|team\s+standings|pomona|grange|new\s+market|maryland|(mount|mt\.?)\s+pleasant,?\s+no\.?\s*\d|odd\s+fellows|masonic|frederick|a\.?m\.?i\.?\b",
    "local": r"sixteenth|16th|seventeenth|17th|park\s+road|irving|lamont|kenyon|harvard|mount\s+pleasant\s+st|columbia\s+road|n\.\s?w\.|citizens",
},
```
Note: Mount Pleasant Congregational Church clips say "Columbia road near Fourteenth street", which is outside the HPN today. I left the church in because of its name, and readers will accept that.

### Stadium-Armory

| Term | Week | What the snippets show |
|---|---|---|
| `"Congressional Cemetery"` | 4 | Almost all interment lines. One: "The Annunciation. Congressional Cemetery Chapel. 3:30-4." |
| `"District jail"` | 2 | A murder defendant held there, and a minister speaking there. Both clean. |
| `"Gallinger Hospital"` | 3 | Daily deaths list. Rejected by `years\s+old` and the hospital rule. |
| `"East Capitol street"` | 2 | Lower blocks, mostly. Address filter keeps only 1900–2399. |
| `"Washington Asylum"`, `"Reservation 13"` | 0 / 0 | nothing |

```python
"stadiumarmory": {
    # 1926 here is the cemetery, the jail and Gallinger Municipal Hospital. The stadium is 35 years off, and funeral notices dominate.
    "terms": ['"Congressional Cemetery"', '"District jail"', '"Gallinger Hospital"', '"East Capitol street"'],
    "pattern": r"congressional\s+cemetery|district\s+jail|washington\s+asylum|gallinger\s+(municipal\s+)?hospital|jail\s+hill|\b(19|2[0-3])\d\d\s+east\s+capitol\s+st|"
               r"\b(19th|nineteenth|twentieth|20th)\s+(st(reet|\.)?\s+)?and\s+(b\s+st|east\s+capitol|independence)",
    "reject": r"interment|inter\s+ment|funeral|deaths?\s+reported|remains|years\s+old|hospital\.\s",
    "local": r"s\.\s?e\.|southeast|nineteenth|19th|east\s+capitol|anacostia|e\s+st|cemetery|chapel|commissioners|hospital",
},
```
Hill East shares this history, in that Gallinger and the jail stand where people now say "Hill East". By HPN they're here.

### Trinidad

| Term | Week | What the snippets show |
|---|---|---|
| `"Ivy City"` | 1 | The association's 5 Nov meeting at the Crummell School. Screened headline, see pitfall 4. Clean clip about 100 planned houses. |
| `"Trinidad" Northeast` | 8 | Shipping lists, plus "Trinidad ave. n.e." ads. Replaced by `"Trinidad avenue"`, which is not separately counted. |
| `"Gallaudet College"` (from `"Gallaudet"` 8) | not counted | Football ("Maryland Swamps Gallaudet"), rejected. Also the Northeast Business Men's letter urging Dr. Percival Hall for commissioner (31 Oct), kept. |
| `"Mount Olivet"` | 9 | Interment lines, rejected. A hike from Mount Olivet to Mount Hamilton (31 Oct) is lost too, because `pattern` asks for Mount Olivet road. Loosen that if you want it. |
| `"Bladensburg road"` | 4 | Weak. Not used. |
| `"Montello avenue"`, `"Florida avenue northeast"` | 0 / 0 | The last term uses `"Montello"` alone. |

```python
"trinidad": {
    # Bare "Trinidad" is shipping news (Maravi--Trinidad). Union Market's ancestor came later. Gallaudet College = Kendall Green.
    "terms": ['"Ivy City"', '"Trinidad avenue"', '"Gallaudet College"', '"Mount Olivet"', '"Montello"'],
    "pattern": r"ivy\s+city|trinidad\s+(ave|citizens|section|community|school)|gallaudet\s+college|kendall\s+green|montello\s+av|mount\s+olivet\s+(road|r\.?\s?d)|"
               r"\b\d{3,4}\s+(montello|trinidad|holbrook|neal|orren|queen|raum)\s+(st|av)[a-z.]*\s+n\.?\s?e",
    "reject": r"tobago|port\s+of\s+spain|foot\s*ball|eleven|touchdown|gridiron|varsity|quarterback|coach|american\s+university\s+(at|vs)|interment|inter\s+ment|cemetery",
    "local": r"n\.\s?e\.|northeast|florida\s+av|bladensburg|new\s+york\s+av|west\s+virginia\s+av|ivy\s+city|crummell|gallaudet|kendall\s+green|citizens",
},
```

### Woodley Park

| Term | Week | What the snippets show |
|---|---|---|
| `"Woodley Park"` | 4 | House ads "in exclusive Woodley Park… bordering on Rock Creek Park". Some are in the Cathedral direction, rejected. |
| `"Woodley road"` | 5 | Mostly the Cathedral end (3707 Woodley Road, Mount St. Alban). West of this boundary. Pattern takes only 2600–2999. |
| `"Zoological Park"` | 2 | A columnist on sunsets over the National Zoological Park (5 Nov), and a theater metaphor, rejected by requiring "National". |
| `"Connecticut avenue bridge"` | 6 | Speed-limit talk after a near miss on the bridge (1 Nov), now Taft Bridge. Taft is 2D01 by my coordinate, right at the south edge. |
| `"Wardman Park"` | 47 | Society pages: legations and art dealers staying at the hotel, the Wardman Park Theater showing "The Four Horsemen". Fine, but it can fill all six clips, so the term goes last. |
| `"Calvert street"` | 8 | Mostly North Calvert St in Baltimore and Calvert St in Adams Morgan's 1800 blocks. Not used as a term; pattern takes 2300–2999. |
| `"Klingle"` | 2 | Outside (3C04). Not used. |

```python
"woodleypark": {
    # Woodley Park proper only. Most reliable first; "Wardman Park" (47 pages this week) goes last so it can't eat the page budget.
    "terms": ['"Woodley Park"', '"Connecticut avenue bridge"', '"Zoological Park"', '"Woodley road"', '"Wardman Park"'],
    "pattern": r"woodley\s+park|\b2[6-9]\d\d\s+woodley\s+r|wardman\s+park|national\s+zoological\s+park|connecticut\s+avenue\s+bridge|\bzoo\b(?=.{0,120}(rock\s+creek|connecticut|national))|"
               r"\b2[3-9]\d\d\s+calvert\s+st|\b2[6-9]\d\d\s+connecticut\s+av",
    "reject": r"cathedral|mount\s+st\.?\s+alban|john\s+eaton|tilden|cleveland\s+park|syncopating|horsem[ae]n|this\s+afternoon\s+and\s+evening",
    "local": r"connecticut\s+av|calvert\s+st|woodley|rock\s+creek|wardman|zoo|cathedral\s+av|twenty-(sixth|seventh|eighth|ninth)|2[6-9]th\s+st",
},
```


## 10. Not verified / excluded

- **Robots-disallowed for our agent (none fetched):**
  - `mountpleasantdc.org` (whole site), `www.gallaudet.edu/feed/`, `gwhatchet.com/?s=…`.
  - Squarespace `?format=ical`: `anc1d.org/meetingcalendar`, `kingmanisland.com/calendar`.
  - Previously known and not retried: Google Calendar ICS (`dcanc5d@gmail.com`).
- **403 to our UA:** none.
- **Not tested because of the crawl delay:** all GGW tag feeds (`ggwash.org/rss/tag/…`), and any keyword count on `ggwash.org/rss`. The tag URLs are a guess from a search result I saw; they may not exist.
- **Connection or TLS failures, not retried with anything else:** `anc5f.com` (timeout, twice), `mountpleasantmainstreet.org` (timeout), `mtpfm.org` (timeout), `mtpleasantdc.org` (certificate mismatch), `ivycitydc.org` (TLS), `trinidaddc.org` (refused).
- **No DNS:** `anc5e.org`, `anc5e.dc.gov`, `anc5f.dc.gov`, `anc2a.dc.gov`, `anc6a.dc.gov`, `anc6b.dc.gov`, `anc7d.org`, `anc7f.org`, `anc7f.dc.gov`, `anc5c.org`, `anc5c.dc.gov`, `anc5d.dc.gov`, `anc1d.dc.gov`, `foggybottomnews.org`, `westendcitizens.org`, `bloomingdalecivic.org`, `eckingtondc.org`, `eckingtoncivic.org`, `kingmanparkcivic.org`, `kingmanparkcivicassociation.org`, `mountpleasantfarmersmarket.org`, `mountpleasant.helpfulvillage.com`.
- **Hijacked or repurposed, do not link:** `northcapitoldc.com` (gambling redirect), `www.mtpleasantdc.org` (car-rental spam), `woodleyparkmainstreet.org` (see §8), `woodleypark.org` (Glover Park redirect), `mtpleasantmainstreet.org` (Utah).
- **Stale:**
  - WTOP `bloomingdale` (2023), `mt-pleasant` (2020), `stadium-armory` (2021), `kingman-island` (Sep 2024), `west-end` (Feb 2025), `trinidad` (Apr 2025), `union-market` (Sep 2025).
  - DC Line `?s=bloomingdale` (2022), `?s=eckington` (2022), `?s=trinidad` (2023), `?s=gallaudet` (2023), `?s=congressional+cemetery` (2023), `?s=kingman+park` (May 2024), `?s=mount+pleasant` (Mar 2024).
  - Bloomingdale Civic (Feb 2021), Bates Area Civic (Mar 2021), ANC 6A (Feb 2015), ANC 6B (Nov 2023), Hill is Home `hill-east` category (Oct 2020), Eckington Civic (Jul 2025).
- **Empty feeds (200, 0 items):** `mountpleasantvillage.org`, `unionmarketdc.com`, `hstreet.org`, all PoPville `/tag/…/feed/`, WTOP `eckington`, `hill-east`, `kingman-park`, `reservation-13`, `dc-jail`, `rfk-site`, `hechinger-mall`, `mcmillan`, `woodley-park-main-street`.
- **Machine-readable dates I found only in HTML:** ANC 1D and Kingman Island (Squarespace `<time>`), ANC 7D full meetings (home page). No scraper recommended here; it's a decision for you.
- **Not tested at all:** Smithsonian's Zoo events beyond the paths above; Events DC beyond the home page and `/feed/`; DPR recreation center calendars; Dock 5; Lisner Auditorium; DCPL location names (they follow the pattern; none confirmed, because DCPL refuses automated requests for calendars per `events.py`); `hilleastcivicassociation.org` sitemap; ANC 6A's calendar format beyond the HTML; `/events/?ical=1` on Union Market and H Street.
- **Discovery used a web search tool** for candidate domains (ANC 5E's `anc5edc.org`, `anc5f.com`, `wpcaonline.org`, the Hill East association, `northcapitoldc.com`). The search tool doesn't use our user agent; every site I then tested got our agent and a robots check. The 7F meeting location comes only from those search results.
- **One diagnostic with `curl`:** I read `ggwash.org/robots.txt` with curl, our UA, when my script appeared stuck. It wasn't a block; the script was honouring the 3000 s delay. Nothing else went through another client.
- **Engine changes these recommendations assume** (not made; this file is the only edit):
  1. A per-host crawl delay in `build_headlines`, and one GGW fetch per run (§0.3). This is the urgent one, because live sites already do it.
  2. `in_season` accepting "year round" (§0.1).
  3. A body-date parser for OANC-platform ANC feeds (`Date and Time …`), for ANC 7D and 3C, already asked for in SOURCES-CENTRAL.
  4. `AGENDA_2A` in `build_anc`.
  5. ANC 1D month-from-title plus third Tuesday, if you want it.
  6. Case-sensitive TERMS for Hill East and Trinidad, as for NoMa and Shaw: already supported, just don't add `re.I`.
