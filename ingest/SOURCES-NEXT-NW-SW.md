# Sources for Brightwood, Takoma DC and Southwest Waterfront / The Wharf (candidates)

Tested 2026-11-03. Every feed and calendar fetch used `dc-neighborhoods-ingest/0.1 (+https://petworth.org)` through the engine's `news.allowed` and `news.fetch`, on the exact URL with its query string. Each host got at least 2 s between requests, longer where a Crawl-delay asked (Hill Rag 20 s, Brightwood Community Association 10 s, ANC 4C 5 s, tpss.coop 3 s). `ggwash.org` (Crawl-delay 3000) got one request.

Hit counts read **body / summary / title**, as in SOURCES-LATE. "Summary" is what `match` mode sees. Counts apply TERMS and NOT_HERE together. "60d" means items dated 2026-09-04 or later that matched in summary mode, unless a row says otherwise. The slugs `brightwood`, `takoma` and `swwaterfront` are not in `neighborhoods.json`.

## Verdicts

| Area | Verdict | News, 60 days | Events | Best boundary |
|---|---|---|---|---|
| Takoma DC + Shepherd Park | **Viable: thin news, good events.** Build it if a calendar-led page is acceptable. | 8 matched, or 13 with ANC 4B read as `all`. About 4 to 6 a month, roughly half ANC posts. | Best of the three: 23 usable DC events in the next 30 days, after an engine change. | SMDs 4B01–04 + 4A01–03, 5.16 km² |
| Brightwood + Brightwood Park | **Marginal.** Data pages plus a trickle of PoPville items. | 8, all PoPville. About 4 a month. | 2 meetings in 30 days from one calendar. No market inside. | SMDs 4A04–07, 4B05, 4D01–03, 2.62 km² |
| Southwest Waterfront / The Wharf | **Don't build it.** Plenty of news, but it's the same news. | 37, about 18 a month, strong. 32 of the 37 are already reachable by L'Enfant Plaza. | Nothing new. | None. Every Wharf-area address that resolved, except the Fish Market at 1100 Maine, is in the Southwest BID. |

**The geographic finding changes the plan: DC's HPN names don't match Takoma.** Takoma Metro, the Takoma library, Carroll Street and the Takoma Theatre are all in HPN `BRIGHTWOOD`. HPN `SHEPHERD PARK` has none of them. So "Brightwood = its HPN" plus "Takoma = Shepherd Park HPN" gives a Takoma site without Takoma. Both sites need SMD boundaries, which also stops them overlapping.

**Single-source risk:** all 8 Brightwood items and 4 of Takoma's 8 come from PoPville. If PoPville stops tagging these neighborhoods, Brightwood's headline list goes to about zero.

## 0. Cross-cutting findings

### 0.1 Geography

Layers: HPN `Health_WebMercator/MapServer/13`, SMD-2023 `Administrative_Other_Boundaries_WebMercator/MapServer/55`, BID `Business_Betterment_Areas_WebMercator/MapServer/15`, Main Streets `…/MapServer/16`, historic districts `Historic_WebMercator/MapServer/6`, address points `Location_WebMercator/MapServer/0` (field `ADDRESS`, street types spelled out). Shares come from a 70×70 grid sample. "Centroid SMDs" uses the `setup_hood.py` rule. "Lic." counts active ABCA licenses inside, which indicates how much the openings and closings list can carry. Sums can read slightly over 100% from rounding.

| Option | ~km² | Centroid SMDs | ANCs by area | HPNs by area | BIDs / Main Streets | Live overlap | Lic. |
|---|---|---|---|---|---|---|---|
| HPN `BRIGHTWOOD` | 3.48 | 4A04–07, 4B04, 4B05, 4B07 | 4B 50, 4A 49, 3/4G 1 | | Upper Georgia 5% | Chevy Chase 1% | 20 |
| HPN `BRIGHTWOOD` + `BRIGHTWOOD PARK` | 4.80 | adds 4D01–03, 4D07, 4D08 | 4B 41, 4A 36, 4D 21 | 73 / 27 | Upper Georgia 3, Uptown 2, Petworth 1 | none at 1% | 48 |
| Those + `16th ST HEIGHTS` | 9.61 | adds 4C01–04, 4E01–06 | 4E 42, 4B 21, 4A 19, 4D 11, 4C 9 | 16th 50, Brightwood 36, Park 14 | Uptown 3, Petworth 2, Upper Georgia 2 | none at 1% | 83 |
| **SMDs 4A04–07, 4B05, 4D01–03 (recommended)** | **2.62** | same | 4A 61, 4D 24, 4B 15 | Brightwood 76, Park 23 | Upper Georgia 5, Petworth 2, Uptown 2 | none | 40 |
| Same + 4D08 | 2.92 | same | 4A 55, 4D 32, 4B 14 | + Petworth 2 | same | Petworth 2% | 43 |
| Same + 4D08 + all 4E | 6.86 | adds 4E01–06 | 4E 58, 4A 23, 4D 13, 4B 5 | 16th 59, Brightwood 28, Park 12 | Uptown 4 | Petworth 1% | 54 |
| HPN `SHEPHERD PARK` | 3.78 | 4A01–03, 4B01, 4B02 | 4A 83, 4B 16, 3/4G 1 | | Upper Georgia 3 | Chevy Chase 1% | 9 |
| Takoma Park Historic District | 0.45 | 4B04 | 4B 100 (4B04 73, 4B01 19, 4B02 8) | Brightwood 80, Shepherd Park 19 | none | none | 3 |
| SMDs 4B01, 4B02, 4B04 | 1.24 | same | 4B 100 | Brightwood 50, Shepherd Park 48 | Upper Georgia 8 | none | 6 |
| SMDs 4B01–04 | 1.77 | same | 4B 100 | Brightwood 50, Shepherd Park 34, Lamond Riggs 15 | Upper Georgia 6 | none | 6 |
| SMDs 4B01, 4B02, 4B04 + 4A01–03 | 4.63 | same | 4A 73, 4B 27 | Shepherd Park 81, Brightwood 17 | Upper Georgia 4 | none | 13 |
| **SMDs 4B01–04 + 4A01–03 (recommended)** | **5.16** | same | 4A 66, 4B 34 | Shepherd Park 73, Brightwood 21, Lamond Riggs 5 | Upper Georgia 3 | none | 13 |
| HPN `SW/WATERFRONT` | 5.72 | 6D02–08, 8F01–05 | 6D 70, 8F 27, 6B 3 | | Southwest BID 32, Navy Yard BID 29 | **L'Enfant Plaza 32%, Navy Yard 29%** | 168 |
| ANC 6D, all | 8.24 | 6D01–08 | 6D 100 | **National Mall 52**, SW/Waterfront 47 | Southwest BID 22, Navy Yard BID 4 | L'Enfant 22%, Navy Yard 4% | 96 |
| Southwest BID | 1.92 | 6D02–05 | 6D 97, 2A 4 | SW/Waterfront 96, Mall 4 | | **This is the L'Enfant Plaza site** | 68 |
| SMDs 6D05–08 | 2.07 | same | 6D 100 | SW/Waterfront 98 | Navy Yard BID 16, Southwest BID 11 | Navy Yard 16%, L'Enfant 11% | 13 |
| SMDs 6D06–08 | 1.82 | same | 6D 100 | SW/Waterfront 98 | Navy Yard BID 18, Southwest BID 2 | Navy Yard 18%, L'Enfant 2% | 13 |

The recommended Brightwood and Takoma boundaries share no SMD and no live site. 4A07 (0.99 km²), 4A01 (1.98) and 4E06 (1.87) probably hold a lot of parkland, so the km² overstates built area. I didn't measure parkland. 6D01 is 5.24 km², 82% HPN `NATIONAL MALL`.

**Landmarks checked against the layers.** (coord) marks my own approximate coordinates, so trust those only away from an edge. Place labels on addresses are from my memory: a match confirms the address, not the label.

| Area | Inside | Outside, and where it actually is |
|---|---|---|
| Brightwood SMDs | 6000, 6100, 6200, 6218 Georgia Ave NW (4A05/06), 5929 Georgia (4B05), Fort Stevens site (coord, 4A06), Rock Creek golf (coord, 4A07), Kennedy St NW 300, 500, 800 (4D02/03), Truesdell 800 Ingraham (4D03), Emery Rec 5701 Georgia (4D01), Neptune Room 5405 Georgia (4D03), Georgia and Missouri (coord, 4D01) | **Fort Stevens Rec 1327 Van Buren: 4A03**, Takoma side. **Brightwood Education Campus 1300 Nicholson: 4E02, HPN 16th ST HEIGHTS.** Coolidge 6315 5th, Whittier 6201 5th: 4B03, LAMOND RIGGS. 6500 Piney Branch: 4B02. Capital City 100 Peabody: 4B06. Rock Creek Cemetery 201 Allison: PETWORTH 4D05, on the live Petworth site. |
| Takoma SMDs | Takoma Metro (coord), Library 416 Cedar, Theatre 6833 4th, Busboys 235 Carroll, Seekers 276 Carroll, Takoma Station 6914 4th, Big Bad Woof 6960 Maple, DC Arts Studios 6925 Willow, 300 Aspen (all 4B04), Takoma Education Campus 7010 Piney Branch (4B02), Takoma Rec 300 Van Buren, Whittier, Coolidge (4B03), Thornton Library 7420 Georgia, Shepherd ES 7800 14th, Tifereth Israel 7701 16th (4A02), 7000 Georgia, 7150 12th St, Walter Reed centre (coord, 4A03), 1600 Portal Dr (4A01) | Takoma Park, MD (coord, outside every DC layer). Rittenhouse St 200 NW and Lamond Rec: 4B07. |
| 16th St Heights HPN | Hamilton Rec (4E03), Carter Barron and 4800 16th St (4E06), Georgia 5200 (4E03), FRESHFARM Uptown 5501 Colorado (4E01), **Upshur Rec, Roosevelt HS, Sharpe, Petworth Library 4200 Kansas (4C01)**, 3725 10th St (4C03) | |
| Southwest | **In Southwest BID, so on L'Enfant Plaza today:** Anthem 901 Wharf St, 801 Wharf St, 525, 660 and 800 Water St, 800, 950 and 1000 Maine Ave, Arena Stage 1101 6th, SW Library 900 Wesley, Amidon-Bowen 401 I, Jefferson 801 7th, Waterfront Station 1101 4th, Waterfront and L'Enfant Metros (coord), HUD, USDA, Farmers Market SW 608 Wharf. **In Navy Yard BID:** Audi Field, Buzzard Point (coord), 2100 2nd St SW, Half Street market, Navy Yard Metro (coord). | **In neither BID:** Municipal Fish Market 1100 Maine and 1330 Maryland Ave SW (6D01), Fort McNair 300 A St, 1301 Delaware, 222 M St (6D07), 429 and 500 N St, 450 M St (6D06), 203 N St (6D05), Titanic Memorial (coord, 6D07). A pier coordinate and Hains Point (coord) are NATIONAL MALL, in 6D01, outside the BID. |

**Flags.**
- **"Brightwood" places are scattered.** The Brightwood Education Campus is in 4E02. Fort Stevens Rec is 4A03 while the fort site is 4A06, so a boundary can't hold both without taking in Walter Reed. I gave the rec center to Takoma geographically and the term `fort stevens` to Brightwood.
- **4B is split.** It's 45% LAMOND RIGGS by area. The recommended sites use 4B01–05. 4B06–10 stay out, so Lamond Riggs and Manor Park remain uncovered.
- **16th Street Heights isn't a cheap add.** It's more area than the other two HPNs together, half of it 4E06, and PoPville named it 0 times in 60 days. It also reaches Petworth Library and Roosevelt HS. If you want one thing from it, SMD 4E01 (0.21 km²) picks up FRESHFARM Uptown and gives Brightwood a dated market.
- **No "Wharf" polygon avoids L'Enfant Plaza.** What's left after removing both BIDs (6D06–08) is Fort McNair and the residential blocks south of M, with 13 licenses.

```python
# neighborhoods.json, recommended options
{"slug": "brightwood", "name": "Brightwood", "boundary_where": "SMD_ID IN ('4A04','4A05','4A06','4A07','4B05','4D01','4D02','4D03')", "boundary_parts": 8,
 "boundary_layer": "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Administrative_Other_Boundaries_WebMercator/MapServer/55", "enabled": false}
{"slug": "takoma", "name": "Takoma", "boundary_where": "SMD_ID IN ('4A01','4A02','4A03','4B01','4B02','4B03','4B04')", "boundary_parts": 7,
 "boundary_layer": "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Administrative_Other_Boundaries_WebMercator/MapServer/55", "enabled": false}
```

**Farmers markets in the existing layer** (run through `events.market_dates`).

| Market | Point falls in | Schedule | Engine result |
|---|---|---|---|
| FRESHFARM Whittier Elementary Farm Stand, 6201 5th St NW | 4B03, **inside the Takoma option** | Tuesdays 3–6, May to November | Dated: Nov 3, 10, 17, 24 |
| FRESHFARM Uptown, 5501 Colorado Ave NW | 4E01, **inside only if you add 4E01** | Saturdays 9–1, April to November | Dated: Nov 7, 14, 21, 28 |
| Farmers Market SW, 608 Wharf St | 6D06, Southwest BID, **already on L'Enfant Plaza** | Saturdays 9–1, April to November | Dated |
| Half Street Central, 1250 Half St SE | 8F02, already on Navy Yard | Saturdays 9–1, May to Nov 21 | Dated |

No market in the layer sits in HPN `BRIGHTWOOD`, `BRIGHTWOOD PARK` or `SHEPHERD PARK`. The Takoma Park and Crossroads markets on Main Street Takoma's calendar are outside this layer's DC set, and I treat them as Maryland.

### 0.2 Keyword rules (drop-in for `TERMS` and `NOT_HERE`)

All compile as written. I tested them on every feed here, then on 71 strings I wrote: 40 traps and 31 true cases (Brightwood 12/11, Takoma 17/11, Southwest 11/9). All pass, which proves only that the rules do what I meant. On real feeds, the Takoma reject list fired on 49 summary-mode items (the ones I read were Source of the Spring plus one GGW piece). Southwest's fired once, on Hill Rag's "Potomac Water Taxi Returns for the Season". **Brightwood's never fired.** Its out-of-state list has only my synthetic tests behind it, as do `Shepherd Park` elsewhere and Fisherman's Wharf.

**Brightwood**:
```python
"brightwood": re.compile(
    r"\bbrightwood\b(?!\s+(college|capital|career|hospital|golf|forest))|"
    r"\bkennedy\s+st(reet)?\b|\buptown\s+main\s+street\b|\bfort\s+stevens\b|\bemery\s+(heights\s+)?(rec|community|park)|"
    r"\bmissouri\s+ave(nue)?\.?(,?\s+n\.?w\b|\s+(and|&|at)\s+(georgia|14th|16th|riggs|kansas))|\bgeorgia\s+(ave(nue)?\.?\s+)?(and|&|at)\s+(missouri|kennedy|sheridan|peabody|rittenhouse)\b|"
    r"\b(5[4-9]|6[0-7])\d\d\s+(block\s+of\s+)?georgia\s+ave(nue)?\b|\btruesdell\b|\bupper\s+georgia\s+ave|\bANC\s*4A0?[4-7]\b|\bANC\s*4B05\b|\bANC\s*4D0?[1-3]\b|\b4A0[4-7]\b|\b4B05\b|\b4D0[1-3]\b|\bANC\s*4A\b", re.I|re.S),
"brightwood": (re.compile(r"\bbrightwood,?\s+(ore|oregon|or|va|virginia|ind|indiana|mass|massachusetts|mi|mich|michigan|ma|n\.?c|il|ill|nj|n\.j|ohio|ga)\b|\bindianapolis\b|\bspringfield\b|\bmt\.?\s+hood\b|\bmount\s+hood\b|\bfort\s+stevens,?\s+(state\s+park|ore|oregon)\b|\bfort\s+stevens\s+state\s+park\b|\bastoria\b|\bhammond,?\s+ore|\bkennedy\s+st(reet)?\b.{0,60}\b(boston|dorchester|quincy|brooklyn|queens|baltimore|hyattsville|bronx|alexandria,?\s+va)\b|\bjersey\s+city\b", re.I|re.S),
               re.compile(r"\bbrightwood\s+park\b|\bANC\s*4[AD]\b|\bgeorgia\s+ave|\bward\s*4\b|\bkennedy\s+st(reet)?\.?,?\s+n\.?w\b|\b(d\.?c\.?|NW)\b.{0,30}\bbrightwood\b|\bbrightwood\b.{0,60}\b(NW|northwest\s+(dc|d\.c\.))\b", re.S)),
```
- Bare "Brightwood" counts. I first required a DC cue within 300 characters, which lost "DDOT's Cool Corridors Pilot Has Begun in Brightwood!" and "Helluva Way to Wake Up cont. Brightwood edition". PoPville's tag text also has to count alone.
- `kennedy st` is bare because PoPville's tag says "Kennedy Street". Kennedy Center can't match.
- Georgia Ave counts only at 5400–6799, with "block of" allowed for MPD copy. Most Georgia Ave mentions in 60 days were Park View or Petworth.
- `ANC 4A` is on both Brightwood and Takoma, since 4A covers both.

**Takoma**:
```python
"takoma": re.compile(
    r"\btakoma\s+(dc|d\.c\.|metro|station|library|neighborhood\s+library|theat(re|er)|education\s+campus|rec(reation)?(\s+center)?|community\s+center|aquatic|central|park\s+dc|park,?\s+d\.?c)\b|\btakoma\s*\(takoma\s+park\)|"
    r"\b(dc|d\.c\.)['\u2019]?s\s+takoma\b|\btakoma\b(?!\s+park\b)(?!\s+academy\b)(?![-\s]langley\b)(?=.{0,200}\b(d\.?c|washington|nw|n\.w|northwest|ward\s*4|mpd|red\s+line)\b)|\bin\s+takoma\b(?!\s+park\b)|"
    r"\b(carroll|cedar|aspen|butternut|blair|laurel|maple|willow)\s+(st(reet)?|r(oa)?d|ave(nue)?)\.?,?\s+n\.?w\b|\bpiney\s+branch\s+r(oa)?d\.?,?\s+n\.?w\b|\b6[89]\d\d\s+4th\s+st(reet)?\.?,?\s+n\.?w\b|"
    r"\bshepherd\s+park\b|\bshepherd\s+elementary\b|\bjuanita\s+(e\.?\s+)?thornton\b|\bcolonial\s+village\b(?=.{0,200}\b(n\.?w|d\.?c|16th|shepherd)\b)|\bnorth\s+portal\b|\bportal\s+dr(ive)?\b|\btifereth\s+israel\b|\bwashington\s+ethical\s+society\b|"
    r"\b(the\s+)?parks\s+at\s+walter\s+reed\b|\b(former|old)\s+walter\s+reed\b|\bwalter\s+reed\s+(campus|site|redevelopment|development)\b|\bdown\s+in\s+the\s+reeds\b|"
    r"\b(6[89]|7\d|8[01])\d\d\s+(block\s+of\s+)?georgia\s+ave(nue)?\b|\b7[0-9]\d\d\s+(block\s+of\s+)?(1[2-6]th)\s+st(reet)?\b|\bANC\s*4A0?[1-3]\b|\bANC\s*4B0?[1-4]\b|\b4A0[1-3]\b|\b4B0[1-4]\b|\bANC\s*4B\b", re.I|re.S),
"takoma": (re.compile(r"\btakoma\s+park,?\s+(md|maryland|city|council|police|mayor|middle|elementary|folk)\b|\bmaryland\b|\bmd\.|\bmontgomery\s+(county|co\.?)\b|\bmoco\b|\bsilver\s+spring\b|\btakoma[-\s]langley\b|\bpurple\s+line\b|\bprince\s+george|\bwalter\s+reed\s+(national\s+military|medical\s+center|army\s+medical|bethesda)\b|\bbethesda\b|\bsligo\s+creek\b|\bshepherd\s+park\b.{0,40}\b(ky|ga|mo|iowa|ohio|tx|texas|pa|nc|n\.c|mich)\b|\bshepherd\s+university\b|\bshepherdstown\b", re.I|re.S),
           re.compile(r"\btakoma\s+(dc|d\.c\.|metro\s+(station\s+)?(lot|development|site)|library|rec(reation)?\s+center|education\s+campus|theat(re|er))\b(?!\s*\|)|\b(dc|d\.c\.)['\u2019]?s\s+takoma\b|\b(carroll|cedar|aspen|blair)\s+(st(reet)?|r(oa)?d)\.?,?\s+n\.?w\b|\bANC\s*4[AB]\b|\bward\s*4\b|\bshepherd\s+park\b(?=.{0,200}\b(d\.?c|nw|ward\s*4)\b)|\bparks\s+at\s+walter\s+reed\b", re.I|re.S)),
```
- **Bare "Takoma Park" never matches**, since it means the Maryland city. PoPville needs its own rule: it tags DC posts with the literal `Takoma (Takoma Park)`. A bare "from Takoma Park" in PoPville is undecidable and falls out.
- "in Takoma" counts, for "Sabina's Cafe in Takoma is now Open!". That shop could be on either side. The rule can't tell, and neither could I from the headline.
- "Walter Reed" never counts alone, because the hospital in Bethesda is the trap. `wtop.com/tag/walter-reed/feed/` scores 3 of 10 in summary mode.
- `wtop.com/tag/takoma-park/feed/` scores 0/0/0, all 10 Maryland. That's the real-data test.
- **Source of the Spring is a trap.** 20 of its 50 items carry the category text `TKPK | Takoma Park & Takoma D.C.`, and category text counts as summary. They score 0 only because of the reject list. Don't subscribe.
- Regex note: `\btakoma\s+d\.c\.\b` can't match "Takoma D.C. " with a space after it, since no word boundary follows the period. The bare-Takoma lookahead catches it in TERMS. The rescue doesn't, which is why that label doesn't rescue Maryland items. `TERMS["lenfantplaza"]`'s `\bwharf\s+(dc|d\.c\.)\b` has the same quirk.
- Accepted leak: `ANC 4B` also brings notices about 4B05–10.

**Southwest Waterfront**:
```python
"swwaterfront": re.compile(
    r"\bsouthwest\s+waterfront\b|\b(sw|southwest)\s+(dc|d\.c\.)\b|\bdistrict\s+wharf\b|\bwharf\s+(dc|d\.c\.)\b|\bthe\s+wharf\b(?=.{0,200}\b(d\.?c|sw|southwest|maine\s+ave|washington|district|pier|anthem)\b)|\b(dc|d\.c\.)['\u2019]?s\s+wharf\b|\b(at|on)\s+the\s+wharf\b|"
    r"\bwharf\s+st(reet)?\.?,?\s+s\.?w\b|\bwater\s+st(reet)?\.?,?\s+s\.?w\b|\bmaine\s+ave(nue)?\.?(,?\s+s\.?w\b)?|\bmunicipal\s+fish\s+market\b|\bpearl\s+street\s+warehouse\b|\bthe\s+anthem\b(?=.{0,120}\b(wharf|d\.?c|concert|show|tour)\b)|\bmarket\s+sw\b|\bfarmers\s+market\s+sw\b|"
    r"\bbuzzard\s+point\b|\bfort\s+(lesley\s+j\.?\s+)?mcnair\b|\bgreenleaf\s+(gardens|senior|redevelopment|plan)\b|\bjames\s+creek\b|\brandall\s+rec|\bamidon[-\s]bowen\b|\bsouthwest\s+(neighborhood\s+(assembly|library)|library|duck\s*pond|bid|business\s+improvement)\b|\bSWBID\b|\bSWNA\b|"
    r"\bwaterfront\s+(station|metro|village)\b|\btiber\s+island\b|\bharbour\s+square\b|\bcapitol\s+park\s+(towers|apartments|plaza)\b|\barena\s+stage\b|\bwesley\s+pl|\bthe\s+stacks\b(?=.{0,200}\b(buzzard|sw|southwest|d\.?c)\b)|\bcapital\s+yacht\s+club\b|\brevada\s+arts\b|"
    r"\bANC\s*6D\b|\b6D0[1-8]\b|\b\d{2,4}\s+([1-9]|1[0-4])(th|st|nd|rd)\s+st(reet)?\.?,?\s+s\.?w\b|\b\d{2,4}\s+[A-Z]\s+st(reet)?\.?,?\s+s\.?w\b|\bm\s+st(reet)?\.?,?\s+s\.?w\b", re.I|re.S),
"swwaterfront": (re.compile(r"fisherman['\u2019]?s\s+wharf|\bsouthwest\s+airlines\b|\bwharf\b.{0,80}\b(alexandria|baltimore|san\s+francisco|boston|national\s+harbor|london|canary|liverpool|nantucket|sydney|fells\s+point|annapolis|provincetown|gloucester|orange\s+beach)\b|\bcanary\s+wharf\b|\bpier\s+39\b", re.I|re.S),
                 re.compile(r"\bSWBID\b|\bANC\s*6D\b|\bmaine\s+ave|\bsouthwest\s+waterfront|\b(dc|d\.c\.)['\u2019]?s\s+wharf|\bwharf\s+(dc|d\.c\.)", re.I|re.S)),
```
- "The Anthem" needs a venue cue, for the song and the insurer. "Audi Field" is out: it's Navy Yard BID and game copy.
- Roundups get through. Washingtonian's "26 Things to Do" says "at the Wharf" in its summary, so leave Washingtonian's search out.

### 0.3 General feeds counted for these areas (b/s/t). BW Brightwood, TK Takoma, SW Southwest.

| Feed | robots | items (dates) | BW | TK | SW |
|---|---|---|---|---|---|
| `https://www.popville.com/feed/` p1–p3 | allow | 60 (27 Oct–3 Nov) | 0 | 0 | 3/2/2 |
| **PoPville p1–p30** (one-off sample, 2 s apart) | allow | 600 (2 Sep–3 Nov) | **10/8/3** | **7/4/1** | **17/11/7** |
| `https://washingtoncitypaper.com/feed/` | allow | 10 (29 Oct–2 Nov) | 0 | 0 | 0 |
| `https://wtop.com/local/dc/feed/` | allow | 10 (2–3 Nov) | 0 | 0 | 0 |
| `https://wamu.org/feed/` | allow | 10 (30 Oct–2 Nov) | 0 | 0 | 0 |
| `https://51st.news/rss/` | allow | 15 (21 Oct–3 Nov) | 0 | 0 | 1/0/0 |
| `https://ggwash.org/rss` (Crawl-delay 3000, one request) | allow | 10 (29 Oct–2 Nov) | 0 | 0 | 0 |
| `https://mayor.dc.gov/rss.xml` | allow | 10 (2015–Apr 2026) | 0 | 1/1/0 | 1/1/0 |
| `https://ddot.dc.gov/rss.xml` | allow | 10 (Aug–30 Oct) | 0 | 1/1/1 ("ANC 4B SMD Meeting") | 0 |
| `https://dpr.dc.gov/rss.xml` | allow | 10 (2015–Apr 2026) | 0 | 0 | 0 |
| `https://oanc.dc.gov/rss.xml` | allow | 10 (13 Oct–2 Nov) | 0 | 0 | 0 |
| `https://thedcline.org/feed/` | allow | 20 (9 Oct–2 Nov) | 0 | 0 | 0 |
| `https://www.washingtoninformer.com/feed/` | allow | 10 (29 Oct–2 Nov) | 0 | 0 | 0 |
| Hill Rag `/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link` (Crawl-delay 20) | allow | 20 (19 Oct–2 Nov) | 0 | 0 | 0 |
| `https://www.petworthnews.org/blog?format=rss` | allow | 20 (Oct 2025–5 Sep 2026) | 6/5/0 | 3/3/2 | 0 |

The p1–p3 row shows why I went deeper. A week of PoPville gave Brightwood and Takoma nothing, and 62 days gave them 8 and 4. A nightly run with the 180-day archive sees all of that from p1 most days. I paged back once to measure; the engine shouldn't.

**Yardstick, with a caveat.** Items dated in the same 60 days in the live data files: L'Enfant Plaza 41, Capitol Hill 23, Foggy Bottom 18, Stadium-Armory 13, Chevy Chase 8, Kingman Park 6, Petworth 4, Woodley Park 2, Bloomingdale 1. That isn't like for like. Those sites saw only what their feeds held at launch, some just days ago, while my 8 comes from paging 30 pages back. It doesn't mean Brightwood beats Petworth. I'd expect both candidates to land at the low end of the network.

---

## 1. Brightwood (SMDs 4A04–07, 4B05, 4D01–03; ANC 4A ~61%, 4D ~24%, 4B ~15%)

**Expected headlines: thin, about 4 a month, all PoPville.** The sample includes "DDOT's Cool Corridors Pilot Has Begun in Brightwood!", "Update: The Practical Cyclist is coming soon!", "Cantina Paraiso is listed at 'temporarily closed'", and a banh mi pop-up at 5405 Georgia. 40 licenses should add some openings and closings.

### NEWS

| Feed (exact URL) | robots | items | b/s/t | 60d | Notes |
|---|---|---|---|---|---|
| PoPville p1–p3 | allow | 60 | §0.3 | 8 over p1–p30 | **The only live source.** `match`. |
| `https://www.petworthnews.org/blog?format=rss` | allow | 20 | 6/5/0 | 0 | Slow. `match`. |
| `https://anc4a.dc.gov/rss.xml` | allow | 10 (26 Jan–4 Jun 2026) | 10/10/8 | 0 | Meeting nodes. **Nothing since June, no November meeting.** `match`. |
| `https://anc4d.org/feed/` | allow | 10 (Oct 2025–24 Sep 2026) | 1/1/0 | 0 | Mostly "4D Grants Committee Meeting". 4D is half Petworth. Marginal. |
| `https://thedcline.org/?s=brightwood&feed=rss2&orderby=date&order=DESC` | allow | 20 (Oct 2021–20 Mar 2026) | 13/13/1 | 0 | One hit this year. `match`. |
| `https://thedcline.org/?s=kennedy+street&feed=rss2&orderby=date&order=DESC` | allow | 20 (Sep 2021–25 Sep 2026) | 3/3/2 | 0 | Word-split search, opinion columns. Skip. |
| `https://www.washingtonian.com/?s=brightwood&feed=rss2&orderby=date&order=DESC` | allow | 10 (Feb 2025–14 Aug 2026) | 10/3/0 | 0 | Mostly roundups. `match`. |
| `https://wtop.com/tag/brightwood-park/feed/` | allow | 10 (2014–17 Jan 2023) | 10/10/1 | 0 | **Stale**, crime when it fires. Cheap to keep. |
| `https://wtop.com/tag/ward-4/feed/`, `georgia-avenue` | allow | 6, 10 (newest Dec 2023, Feb 2025) | 2/1/1, 1/1/1 | 0 | **Stale.** Skip. |
| Hill Rag `search=brightwood` | allow, Crawl-delay 20 | 13 (2017–May 2025) | 1/1/0 | 0 | Skip. |

Not usable:
- `brightwoodcommunity.org` has no news. `/feed/` and its post list hold 2 template posts ("title of post", "Examples post") from 2024. Its calendar is real; see Events.
- `www.uptownmainstreet.org` (Squarespace, Kennedy Street): `?format=rss` gives 0 items, `/blog`, `/news` and `/events` RSS 404, `/news-events?format=rss` returns HTML.
- `brightwooddc.org` TLS failure. `uppergeorgiaavenue.org`, `uppergeorgia.org`, `uppergeorgiamainstreet.org`, `16thstreetheights.org`, `lamondriggs.org`: no DNS.
- Upper Georgia Avenue Main Street exists only as a page at `nonprofitadvancement.org`, whose `/feed/` is **robots-disallowed**.
- `sshca.org` is a **trap**: its feed is South Seminole Heights, Tampa. DC's 16th Street Heights Civic Association appears on ANC 4E's resource page only as `groups.io/g/sshcadc`, not tested.
- WTOP tags `brightwood`, `kennedy-street`, `fort-stevens`, `16th-street-heights`: 200 with 0 items. WTOP `?s=`: **robots-disallowed**. City Paper and Informer `?s=`: 0 items. PoPville `?s=`: HTML.
- `anc4e.dc.gov/rss.xml`: commissioner profiles and old meetings, newest June. `anc4e.org` 404.

```python
"brightwood": [
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    ("Petworth News", "https://www.petworthnews.org/blog?format=rss", "https://www.petworthnews.org/", "match"),
    ("ANC 4A", "https://anc4a.dc.gov/rss.xml", "https://anc4a.dc.gov/", "match"),
    ("WTOP", "https://wtop.com/tag/brightwood-park/feed/", "https://wtop.com/", "match"),
    ("The DC Line", WP_SEARCH.format(base="https://thedcline.org", q="brightwood"), "https://thedcline.org/", "match"),
    ("Washingtonian", WP_SEARCH.format(base="https://www.washingtonian.com", q="brightwood"), "https://www.washingtonian.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **Brightwood Community Association** | `https://brightwoodcommunity.org/wp-json/tribe/events/v1/events` (Crawl-delay 10) | **Works and fits `TRIBE` as is.** 2 in the next 30 days: "BCA General Meeting" 10 Nov at St. John United Baptist, 6343 13th St NW, and "MPD Sector 1 Virtual Meeting" 12 Nov on Zoom. 50 listed across 2026–27: mostly those two series, plus "Jazz on the Plaza" and "Fort Stevens Day". |
| ANC 4A | `https://anc4a.dc.gov/rss.xml` | 6 of 10 titles fit `OANC_TITLE`, but `build_oanc` reads only the OANC feed, and this one stopped in June. Link. |
| ANC 4D | `https://anc4d.org/feed/`; tribe 404 | Free-form titles. Link. |
| OANC | `https://oanc.dc.gov/rss.xml` | Filter works. None of 4A–4E or 6D in today's 10. |
| Markets | layer | None inside. Add 4E01 for FRESHFARM Uptown. |

```python
TRIBE["bca"] = ("Brightwood Community Association", "https://brightwoodcommunity.org/wp-json/tribe/events/v1/events", "https://brightwoodcommunity.org/calendar/", None, 10)
CALENDARS["brightwood"] = ["bca"]
ANCS["brightwood"] = ["4A", "4B", "4D"]
LINKS["brightwood"] = [
    {"name": "ANC 4A", "url": "https://anc4a.dc.gov/"},
    {"name": "ANC 4D", "url": "https://anc4d.org/"},
    {"name": "Uptown Main Street (Kennedy Street)", "url": "https://www.uptownmainstreet.org/news-events"},
    {"name": "Petworth Library events", "url": "https://dclibrary.libnet.info/events?l=Petworth%20Neighborhood%20Library"},
]
```

---

## 2. Takoma DC + Shepherd Park (SMDs 4B01–04, 4A01–03; ANC 4A ~66%, 4B ~34%)

**Expected headlines: thin, about 4 to 6 a month.** 60-day matches: PoPville 4, ANC 4B 3 in summary mode, DDOT 1. With ANC 4B as `all` that becomes 13 (8 ANC, 4 PoPville, 1 DDOT), and meeting posts are more than half. Only 13 licenses, so openings won't fill the gap.

### NEWS

| Feed (exact URL) | robots | items | b/s/t | 60d | Notes |
|---|---|---|---|---|---|
| **`https://anc4b.com/feed/`** | allow | 10 (19 Jun–2 Nov 2026) | 9/4/0 | 3 (8 as `all`) | **Most reliable local source.** "November 2026 Planning Meeting". Civic, not news. Also covers Lamond Riggs. `all`. |
| PoPville p1–p3 | allow | 60 | §0.3 | 4 over p1–p30 | New gym at the Parks at Walter Reed, Cantina Paraiso, a house-fire fundraiser. `match`. |
| `https://mainstreettakoma.org/feed/` (same site as `oldtakoma.com`) | allow | 12 (Mar 2025–12 Aug 2026) | 8/5/4 | 0 | Under one post a month, both sides of the line. "Wings on Deck Opens in Takoma". `match`, some will be Maryland. |
| `https://www.petworthnews.org/blog?format=rss` | allow | 20 | 3/3/2 | 0 | "Live music, dancing, fitness, and a giant book sale: The Parks at Walter Reed" (11 Aug). `match`. |
| `https://wtop.com/tag/takoma/feed/` | allow | 9 (2016–17 Apr 2026) | 8/1/0 | 0 | DC stories whose summaries rarely say Takoma, so `all`. About 1 to 2 a year. |
| `https://wtop.com/tag/the-parks-at-walter-reed/feed/` | allow | 4 (2017–Jun 2023) | 4/4/2 | 0 | **Stale.** Clean. |
| `https://wtop.com/tag/shepherd-park/feed/` | allow | 3 (2014–Apr 2019) | 3/3/1 | 0 | **Stale.** |
| `https://wtop.com/tag/walter-reed/feed/` | allow | 10 (2018–10 Apr 2026) | 5/3/2 | 0 | Mostly the Bethesda hospital. Optional. |
| DC Line `?s=takoma`, `?s=shepherd+park`, `?s=walter+reed` | allow | 20 each (newest Mar 2023, Aug 2023, Sep 2026) | 10/10/5, 2/2/1, 3/3/1 | 0 | Stale, or opinion columns. Skip. |
| Washingtonian `?s=takoma`, `?s=shepherd+park`, `?s=walter+reed` | allow | 10 each | 2/0/0, 2/0/0, 3/0/0 | 0 | Body-only. Skip. |
| Blade `?s=takoma`; Hill Rag `search=takoma` | allow | 10; 20 | 5/0/0; 0 | 0 | Skip. |

Not usable:
- **`takomavoice.com/feed/`: robots-disallowed for our agent.** Not fetched and not tried any other way. It's the obvious Takoma paper, and the one source that could change this verdict, so it may be worth asking them.
- `themocoshow.com/feed/`: robots-disallowed.
- `sourceofthespring.com`: works, but say no (§0.2). `www.tpss.coop/feed/` (Crawl-delay 3): 0 matches.
- `www.shepherdpark.org/feed/`: 4 items, **all dated 10 May 2024**. Link only.
- `ethicalsociety.org/feed/`: newest Jul 2025. `theparksdc.com/feed/` and its post list: 0 items.
- `www.historictakoma.org`: `/feed/`, WP posts and tribe all 404, `?format=rss` returns HTML.
- `takomafoundation.org` certificate mismatch. `takomadc.org`, `anc4b.dc.gov` no DNS. `takomaradio.org/feed/` 404. `takomaparkmd.gov/feed/` 404, Crawl-delay 10. WTOP `takoma-dc` 0 items.

```python
"takoma": [
    ("ANC 4B", "https://anc4b.com/feed/", "https://anc4b.com/", "all"),
    ("Main Street Takoma", "https://mainstreettakoma.org/feed/", "https://mainstreettakoma.org/", "match"),  # both sides of the line
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=3", "https://www.popville.com/", "match"),
    ("Petworth News", "https://www.petworthnews.org/blog?format=rss", "https://www.petworthnews.org/", "match"),
    ("WTOP", "https://wtop.com/tag/takoma/feed/", "https://wtop.com/", "all"),
    ("WTOP", "https://wtop.com/tag/the-parks-at-walter-reed/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/shepherd-park/feed/", "https://wtop.com/", "match"),
    ("ANC 4A", "https://anc4a.dc.gov/rss.xml", "https://anc4a.dc.gov/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **Main Street Takoma** | `https://mainstreettakoma.org/wp-json/tribe/events/v1/events` (`oldtakoma.com` serves the same; total 1,203) | **The reason to build this site.** 110 events in the next 30 days, **41 at DC venues** by state, city or "NW" address. After dropping classes, the duplicate farm stand and dog nail trims, **23 remain**: "Takoma Jazz" at Takoma Station Tavern (4 Saturdays), "Takoma Comedy Night" and "Grapevine Storytelling" at Busboys, "First Fridays at DC Arts Studios!", two book clubs at the Takoma library, the Seekers Church art show, adoption events at The Big Bad Woof. |
| | | **Catches:** (1) The other 69 are Maryland or unclear, and `build_tribe` filters by title only, so it needs a venue filter. (2) `per_page=50` stops at 12 Nov here, so it needs paging. (3) Venue data is user-entered: some states are blank, one Takoma Park venue says "ME". My test may miss a few blank-state DC venues. The ones I read looked like Maryland (7117 Maple Ave, 8006 Flower Ave). |
| FRESHFARM Whittier Farm Stand | layer, 4B03 | Dated. |
| **ANC 4B** | `https://anc4b.com/feed/` | Current. By the dates in its posts, planning meetings fall on the second Tuesday and public meetings on the fourth Monday. Titles lack the day, so `AGENDA` doesn't match, but the body has it ("Monday, November 23, 2026"). Tribe 404. Link, or add a small parser. |
| The Parks at Walter Reed | `https://theparksdc.com/events/` | **HTML only**: 1 MB with 302 `<time>` tags. `?ical=1` returns HTML, tribe 404. Link. A scraper would break the machine-readable rule, so I don't recommend it. |

```python
TRIBE["mainstreettakoma"] = ("Main Street Takoma", "https://mainstreettakoma.org/wp-json/tribe/events/v1/events", "https://mainstreettakoma.org/events/",
                             r"flatfoot|\btap\b|tap\s+class|woof\s+clinic|whittier\s+farm\s+stand|\bclass(es)?\b|pilates|workshop", 0)  # needs a DC-venue filter and paging in build_tribe
CALENDARS["takoma"] = ["mainstreettakoma"]
ANCS["takoma"] = ["4A", "4B"]
LINKS["takoma"] = [
    {"name": "Takoma Library events", "url": "https://dclibrary.libnet.info/events?l=Takoma%20Park%20Neighborhood%20Library"},
    {"name": "Juanita E. Thornton Library events", "url": "https://dclibrary.libnet.info/events?l=Juanita%20E.%20Thornton%20Shepherd%20Park%20Neighborhood%20Library"},
    {"name": "The Parks at Walter Reed events", "url": "https://theparksdc.com/events/"},
    {"name": "ANC 4B", "url": "https://anc4b.com/"},
    {"name": "Shepherd Park Citizens Association", "url": "https://www.shepherdpark.org/"},
    {"name": "Historic Takoma", "url": "https://www.historictakoma.org/"},
]
```
The two library location names are guesses at DCPL's pattern and were not requested, since `events.py` records that DCPL refuses automated calendar requests. Check them by hand.

---

## 3. Southwest Waterfront / The Wharf

**Expected headlines: strong, about 18 a month, and mostly already on lenfantplaza.org.** The Southwest BID boundary is the L'Enfant Plaza site, and it holds the Wharf's addresses, Waterfront Metro, Arena Stage, the Southwest Library and Farmers Market SW.

**Overlap test.** I built this site's 60-day list: The Southwester and SWBID as `all`, every other tested feed through the rules above. That gives 37 distinct items: Southwester 20, PoPville 11, Washingtonian 4, Hill Rag 1, Blade 1.
- **22 of 37 are already in `site/src/data/lenfantplaza.json`.**
- **32 of 37 match `TERMS["lenfantplaza"]` or come from its `all` feeds.**
- **5 don't:** two Washingtonian items (a roundup and party photos), "Oktoberfest at The Wharf" (Hill Rag), a volleyball team at The Anthem (PoPville), and Blade photos at the Wharf.

A separate site would be a copy under another name.

### NEWS

| Feed (exact URL) | robots | items | b/s/t | 60d | Notes |
|---|---|---|---|---|---|
| `https://thesouthwester.com/wp-json/wp/v2/posts?per_page=20&_fields=date_gmt,title,excerpt,link` (tested with `content` added, for body counts) | allow | 20 (8 Oct–2 Nov 2026) | 16/12/7 | 12 (20 as `all`) | **Already `lenfantplaza`.** Monthly batches: 19 of 20 dated 2 Nov. `/feed/` returns HTML. |
| `https://www.swbid.org/feed/` | allow | 10 (Mar 2025–19 Aug 2026) | 10/10/3 | 0 | **Already `lenfantplaza`.** |
| PoPville p1–p3 | allow | 60 | §0.3 | 11 over p1–p30 | **Already `lenfantplaza`.** Mi Vida and Easy Company closures. |
| Hill Rag `/wp-json/wp/v2/posts?search=wharf&per_page=20&_fields=date,title,excerpt,link` | allow, Crawl-delay 20 | 20 (May–12 Oct 2026) | 7/7/6 | 1 | The one feed L'Enfant doesn't read and could. `match`. |
| Hill Rag `search=anc+6d` | allow, Crawl-delay 20 | 20 (Oct 2025–13 Oct 2026) | 8/8/3 | 0 | "District Steps Up Air B&B Enforcement: ANC 6D Report". |
| Hill Rag `search=buzzard+point` | allow, Crawl-delay 20 | 20 (Mar 2025–12 Oct 2026) | 14/14/7 | 0 | "Plans for the Buzzard Point Steam Plant". Navy Yard BID. |
| Hill Rag `search=southwest` | allow, Crawl-delay 20 | 20 | 7/7/2 | 0 | Skip. |
| Washingtonian `?s=the+wharf`; `?s=southwest+waterfront` | allow | 10; 10 | 9/4/1; 9/3/2 | 4; 0 | Roundups. Skip. |
| Blade `?s=the+wharf` | allow | 10 | 10/4/0 | 1 | Skip. |
| WTOP `the-wharf`; `southwest-dc` | allow | 10; 10 (newest 19 Sep 2025; 2 Apr 2026) | 10/6/5; 10/10/5 | 0 | **Already `lenfantplaza`.** Quiet. |
| WTOP `wharf`, `southwest-waterfront`, `buzzard-point`, `the-anthem`, `audi-field`, `fort-mcnair`, `maine-avenue` | allow | 10, 10, 10, 10, 10, 2, 4 | 10/5/2, 10/10/6, 10/10/6, 9/9/3, 5/1/0, 2/2/0, 4/4/1 | 0 | Slow or stale. |
| DC Line `?s=the+wharf`, `?s=southwest+waterfront`, `?s=buzzard+point` | allow | 20 each (newest Jun 2025, Jun 2024, Dec 2022) | 13/13/4, 12/12/4, 15/15/11 | 0 | **Stale.** |

Not usable: `www.wharfdc.com/feed/` and its WP routes 404. `swna.org` and `swdc.org` are the same site: `/feed/` returns HTML and the post list holds one post from Aug 2020. `www.anc6d.org/feed/` is valid RSS with 0 items and its post list is empty. `anc6d.dc.gov` no DNS. `arenastage.org`, `capitolriverfront.org`, `westminsterdc.org`, `marketswdc.com` `/feed/` 404. `swdcaction.org`, `waterfrontvillage.org`, `swduckpond.org` no DNS. `thestacksdc.com` TLS failure.

```python
# Only if you overrule the verdict: lenfantplaza's feeds with Hill Rag added.
"swwaterfront": [
    ("The Southwester", "https://thesouthwester.com/wp-json/wp/v2/posts?per_page=20&_fields=date_gmt,title,excerpt,link", "https://thesouthwester.com/", "all"),
    ("Southwest BID", "https://www.swbid.org/feed/", "https://www.swbid.org/", "all"),
    ("Hill Rag", "https://www.hillrag.com/wp-json/wp/v2/posts?search=wharf&per_page=20&_fields=date,title,excerpt,link", "https://www.hillrag.com/", "match"),  # Crawl-delay 20
    ("WTOP", "https://wtop.com/tag/the-wharf/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/southwest-dc/feed/", "https://wtop.com/", "match"),
    ("WTOP", "https://wtop.com/tag/buzzard-point/feed/", "https://wtop.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/", "https://www.popville.com/", "match"),
    ("PoPville", "https://www.popville.com/feed/?paged=2", "https://www.popville.com/", "match"),
    *SHARED,
],
```

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| Southwest BID | `https://www.swbid.org/wp-json/tribe/events/v1/events` | **Already `CALENDARS["lenfantplaza"]`.** 1 in 30 days: "Jingle Block Rock 2026", 2 Dec. |
| The Wharf | `https://www.wharfdc.com/upcoming-events/` | HTML only: no `<time>` tags, JSON-LD events or `.ics`. `?ical=1` returns HTML, tribe 404. Already linked from L'Enfant. |
| Farmers Market SW | layer | Already on L'Enfant. |
| ANC 6D | `https://www.anc6d.org/anc-6d-meeting-schedule-2/` | HTML, and my date search found no 2026 dates. Feed empty. No 6D in today's OANC items. |
| Arena Stage, Pearl Street Warehouse, The Anthem (Crawl-delay 10), SWNA | tribe route 404 | No API. Union Stage timed out, not retried. |

```python
ANCS["swwaterfront"] = ["6D"]  # same commission as lenfantplaza
LINKS["swwaterfront"] = [
    {"name": "Southwest Library events", "url": "https://dclibrary.libnet.info/events?l=Southwest%20Neighborhood%20Library"},
    {"name": "The Wharf events", "url": "https://www.wharfdc.com/upcoming-events/"},
    {"name": "ANC 6D meeting schedule", "url": "https://www.anc6d.org/anc-6d-meeting-schedule-2/"},
    {"name": "Southwest Neighborhood Assembly", "url": "https://swna.org/"},
]
```

**What I'd do instead.** If you want a Wharf domain, add it to `redirect_hosts` on `lenfantplaza`. To improve L'Enfant itself, read Hill Rag's `search=wharf` there and add `\b(at|on)\s+the\s+wharf\b` to its terms. Neither change is made.

---

## 4. History (Evening Star, loc.gov, week 1926-10-31 to 11-06)

loc.gov answered our agent, robots allow, and `www.loc.gov` has **Crawl-delay 5**. `history.py` doesn't read that delay and sleeps 2 s after a search. Searches took 28 to 80 s each, so the gap held in practice, but it's worth a look. I ran 10 searches, then `history.build_archive` once per area with `ARCHIVE` patched in memory and `MAX_PAGE_FETCHES` lowered to 14 (engine: 24), so clip counts may run low.

| Term | Week pages | | Term | Week pages |
|---|---|---|---|---|
| `"Brightwood"` | 13 | | `"Takoma Park"` | 48 |
| `"Brightwood Park"` | 4 | | `"Walter Reed"` | 30 |
| `"Fort Stevens"` | 5 | | `"Shepherd Park"` | 1 |
| `"Army War College"` | 1 | | `"Water street"`, `"Seventh street wharf"`, `"fish wharf"` | 0 each |

| Area | Clips | Screened | Quality |
|---|---|---|---|
| Brightwood | 3 | 0 | Weak. One was sandlot football ("Barrett proved the main cog in Brightwood's offensive"), one a "Fort Stevens R…" house ad, one OCR soup. I added `offensive|cog\s+in` to the reject after the run, **not re-tested**. |
| Takoma | 4 | 0 | Mostly house ads. One real neighborhood line about Takoma Park gardeners (6 Nov). "Takoma Park" in 1926 spans DC and Maryland, and a clip often doesn't say which. Expect some Maryland through. |
| Southwest | 0 | 0 | **Inconclusive.** The engine reported "2 pages would not load". The 0 for "Water street" came with an 80 s response, so I don't trust it. Not retried, to keep loc.gov use modest. L'Enfant's ARCHIVE entry already covers Southwest's Maine Ave and wharf patterns. |

```python
"brightwood": {
    "terms": ['"Brightwood"', '"Brightwood Park"', '"Fort Stevens"'],
    "pattern": r"brightwood\s+(park|citizens|heights|school|section|avenue|community|hotel|m\.\s?e|methodist|baptist|car\s+line|branch)|(at|in|of)\s+brightwood\b|fort\s+stevens|\b(5[4-9]|6[0-7])\d\d\s+georgia\s+av",
    "reject": r"brightwood\s*,?\s*(mass|va\b|n\.\s?c|ind|ore|pa\b)|springfield|foot\s*ball|eleven|touchdown|gridiron|offensive|cog\s+in|interment|funeral|years\s+old",
    "local": r"georgia\s+av|fourteenth|14th|missouri\s+av|kennedy\s+st|n\.\s?w\.|citizens|sherman\s+av|rock\s+creek\s+church|emory",
},
"takoma": {
    "terms": ['"Takoma Park"', '"Walter Reed"', '"Shepherd Park"'],
    "pattern": r"takoma(\s+park)?,?\s+d\.?\s?c|takoma\s+(park\s+)?(citizens|library|branch|school|section|baptist|presbyterian|lutheran)|shepherd\s+park|walter\s+reed\s+(general\s+)?hospital(?=.{0,200}(georgia|concert|band|visit|patients|red\s+cross|entertain|ward|soldier))|takoma\s+park",
    "reject": r"takoma\s+park,?\s+md|maryland|montgomery\s+county|silver\s+spring|sligo|foot\s*ball|eleven|touchdown|gridiron|interment|funeral|years\s+old|tacoma|duckpin|sanitarium|washington\s+missionary",
    "local": r"georgia\s+av|butternut|cedar\s+st|carroll|blair\s+road|n\.\s?w\.|citizens|fourth\s+st|piney\s+branch|sixteenth",
},
"swwaterfront": {  # untested in practice: the one run returned no clips
    "terms": ['"Water street"', '"Army War College"', '"Seventh street wharf"', '"fish wharf"'],
    "pattern": r"water\s+st(reet|\.)?\s+(southwest|s\.\s?w)|fish\s+wharf|seventh\s+street\s+wharf|(steamboat|norfolk|river)\s+wharf|army\s+war\s+college|washington\s+barracks|maine\s+av(enue|e)?\.?\s+(southwest|s\.\s?w)|greenleaf\s+point|james\s+creek|buzzard\s+point",
    "reject": r"maine\s+av(enue|e)?\.?\s+(southeast|s\.\s?e)|interment|funeral|years\s+old|foot\s*ball|eleven|touchdown|gridiron|polo\s+team",
    "local": r"s\.\s?w\.|southwest|maine\s+av|water\s+st|seventh\s+st|wharf|war\s+college|barracks|channel",
},
```
The terms for `brightwood` and `takoma` were fixed before these searches ran. One week of results says little about other weeks.

---

## 5. Not verified / excluded

- **Robots-disallowed (none fetched):** `takomavoice.com/feed/`, `themocoshow.com/feed/`, `www.nonprofitadvancement.org/feed/`, `wtop.com/?s=…`.
- **403 or 429 to our UA:** none. No mirror, cache or other client was used.
- **Crawl-delays recorded:** `ggwash.org` 3000, Hill Rag 20, `brightwoodcommunity.org` 10, `takomaparkmd.gov` 10, `nonprofitadvancement.org` 10, `theanthemdc.com` 10, `www.anc4c.com` 5, `www.loc.gov` 5, `tpss.coop` 3. GGW tag feeds untested, as before.
- **Connection or TLS failures, not retried another way:** `brightwooddc.org`, `takomafoundation.org`, `www.crestwood-dc.org`, `www.thestacksdc.com`, `www.unionstage.com`.
- **No DNS:** `takomadc.org`, `anc4b.dc.gov`, `anc4d.dc.gov`, `anc6d.dc.gov`, `uptownmainstdc.org`, `uppergeorgiaavenue.org`, `uppergeorgia.org`, `uppergeorgiamainstreet.org`, `16thstreetheights.org`, `lamondriggs.org`, `swdcaction.org`, `waterfrontvillage.org`, `swduckpond.org`.
- **`www.anc4c.com`** (Crawl-delay 5): `?format=rss` returned HTML, `/blog` and `/news` RSS 404. Only relevant if 4C joins Brightwood.
- **`www.ssna-dc.org/events?format=rss`** (16th Street Neighborhood Association, linked from ANC 4E): 20 items, 1 in 60 days. I didn't check whether its dates are event dates. `?format=ical` not tried.
- **Not tested at all:** groups.io lists, NPS Fort Stevens or Rock Creek events, Lamond Riggs and Manor Park beyond guessed domains, DCPL location names, domain availability, HistoryQuest counts, and `setup_hood.py` (it needs a `neighborhoods.json` entry, off limits here), so OTR tax areas and tax-square overlap are unmeasured.
- **Discovery used a web search tool** for candidate domains (`anc4b.com`, `shepherdpark.org`, the Main Street Takoma and Upper Georgia leads). It doesn't use our user agent. Every site I then tested got our agent and a robots check.
- **The news rates rest on one 62-day autumn window**, with an election in it. I don't know how steady PoPville's tagging is across a year.
- **Some Main Street Takoma headlines will be Maryland businesses.** "in Takoma" can't separate them.
- **Engine changes these recommendations assume (not made):**
  1. `build_tribe`: a venue filter and paging past 50, for `mainstreettakoma`. This is what makes the Takoma site worth building.
  2. ANC 4B meeting dates from post bodies, if you want them dated rather than linked.

---

## Summary

- **Takoma DC + Shepherd Park: viable, thin news, good events.** About 4 to 6 headlines a month, half ANC posts. 23 usable DC events in 30 days, but only after a `build_tribe` change. Best boundary: SMDs 4B01–04 + 4A01–03 (5.16 km²), not HPN `SHEPHERD PARK`, which misses the Takoma core.
- **Brightwood + Brightwood Park: marginal.** About 4 headlines a month, all PoPville. 2 meetings in 30 days from a working BCA calendar, no market. Best boundary: SMDs 4A04–07, 4B05, 4D01–03 (2.62 km²). Adding 16th Street Heights adds area, not news.
- **Southwest Waterfront / The Wharf: don't build.** About 18 headlines a month, but 32 of 37 are already reachable by L'Enfant Plaza, and the Wharf's addresses sit in the Southwest BID. Redirect a domain if you want one.
- **Blocked by robots:** Takoma Voice, MoCo Show, nonprofitadvancement.org feed, WTOP search. **No 403 or 429.**
- **Uncertain:**
  - The news rates come from one 62-day sample and depend heavily on PoPville.
  - The Brightwood reject list and the Shepherd Park traps have only synthetic tests behind them.
  - The Brightwood `reject` addition is untested, and Southwest's archive test was inconclusive.
  - DCPL link names are unconfirmed.
- **Report path:** intended for `C:\Users\ericn\source\repos\DCNeighborhoods\ingest\SOURCES-NEXT-NW-SW.md`, **not written** because the Write tool refused subagent report files. Save the text above there.
