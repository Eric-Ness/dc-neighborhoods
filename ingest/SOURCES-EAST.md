# Sources for Capitol Hill, H Street NE, Navy Yard, Anacostia and Columbia Heights (DC)

Tested 2026-10-31. Every fetch used the user agent `dc-neighborhoods-ingest/0.1 (+https://petworth.org)`. robots.txt was checked with `urllib.robotparser` for agent `dc-neighborhoods-ingest` on the exact path. "403 to our UA" means the server refused our agent, robots.txt included; no other agent was tried. Hit counts use the regexes in §0.2, run over title + body of the newest ≤20 items ("body N / title M").

## 0. Cross-cutting findings

### 0.1 Geography (checked against DC GIS: HPN layer `Health_WebMercator/MapServer/13`, SMD-2023 layer `Administrative_Other_Boundaries_WebMercator/MapServer/55`, BID layer `Business_Betterment_Areas_WebMercator/MapServer/15`, address points `Location_WebMercator/MapServer/0`)

- **There is no "NAVY YARD" HPN.** Navy Yard falls in **SW/WATERFRONT** (1100 New Jersey Ave SE (DOT HQ), 1250 Half St SE, 355 Water St SE, 1500 S Capitol St SE (Nationals Park) all check out as SW/WATERFRONT, SMD 8F0x). Use the BID polygon as the boundary: `boundary_layer = https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Betterment_Areas_WebMercator/MapServer/15`, `boundary_where = NAME='Navy Yard BID'` (one polygon; `WEB_URL` = navyyarddc.org). By grid sample it is 88% SW/WATERFRONT HPN + 12% HILL EAST. Its SMDs: 8F01 28%, 8F02 24%, 6B08 12%, 6D07 9%, 6D08 7%, 8F04 7%, 8F03 7%, 8F05 3%. ANC "8F" is now styled **ANC 6/8F** on anc8f.dc.gov.
- **H Street NE is in the UNION STATION HPN**, not its own. The six SMDs you listed are right: house numbers checked 301/401 H → 6C04, 420/501 → 6C06, 601 → 6C05, 701–1001 → 6A02, 1220/1320 → 6A01, 1301/1401 → 6A06. So `SMD_ID IN ('6A01','6A02','6A06','6C04','6C05','6C06')` on layer 55 works, as for Friendship Heights. **Don't use the DC "H St NE" Main Street polygon** (layer 16): it is 43% Eastland Gardens / 7D03 (it must take in the Benning Rd corridor).
- **Capitol Hill HPN**: SMDs 6B01 20%, 6B02 16%, 6B03 14%, 6B04 12%, 6B06 11%, 6C02 11%, 6B05 10%, 6C03 6%. So that's **ANC 6B (~83%) + 6C (~17%)**. Inside: Eastern Market (225 7th St SE, 6B02), Hill Center (921 Pennsylvania Ave SE, 6B04), Folger (201 East Capitol, 6B02), 700 Penn Ave SE. **Outside**: Library of Congress (10 1st St SE) is NATIONAL MALL, Congressional Cemetery (1801 E St SE) is STADIUM ARMORY. The Barracks Row Main Street is 75% Capitol Hill HPN, 25% SW/WATERFRONT; the Capitol Hill BID polygon is only 31% in the HPN.
- **Historic Anacostia HPN**: 8A04 30%, 8A06 17%, 8B06 14%, 8A05 13%, 8B04 11%, 8B07 7%, 8B03 6%. So that's **ANC 8A (~60%) + 8B (~40%)**. Inside: 2101 MLK Jr Ave SE (Children's National Anacostia), 2004 MLK (Busboys & Poets), 2020 Shannon Pl, 1301 U St SE, Frederick Douglass NHS (1411 W St SE), Anacostia Community Museum (1901 Fort Pl SE). **Outside**: Anacostia Metro (1101 Howard Rd) and Cedar Hill hospital (1200 Pecan St) are SAINT ELIZABETHS; the Anacostia BID office (1800 MLK) is TWINING; THEARC (1801 Mississippi Ave) is DOUGLASS. The Anacostia BID polygon is 87% SAINT ELIZABETHS HPN and only 10% Historic Anacostia, so filter BID content by keyword, not by assuming it's all in.
- **Columbia Heights HPN**: 1E01–1E04 ~41%, 1A02–1A10 ~51%, 1D06/1D07 ~8%. So **ANC 1A + ANC 1E (Park View, east of Sherman/Georgia)** + a sliver of 1D (Mt Pleasant). DC USA (3100 14th St NW, 1A05), GALA/Tivoli (3333 14th St NW, 1A02), 1460 Columbia Rd and 3400 Georgia Ave (1E03) are all inside.

### 0.2 Keyword rules (Python `re`, IGNORECASE|DOTALL unless noted; tested on the feeds below)

**Capitol Hill.** Accept if A, or B together with a cue. Never accept bare "Capitol Hill".
- A (landmarks):
  ```
  \beastern\s+market\b|\bbarracks\s+row\b|\bstanton\s+park\b|\bseward\s+square\b|\bhill\s+center\b|\bfolger\s+(shakespeare|theat|library)|\bmarine\s+barracks\b|\beast\s+capitol\s+st|\bpennsylvania\s+ave(nue)?\.?\s+s\.?e\b|\bcapitol\s+hill\s+(neighborhood|restoration\s+society|village|day\s+school|montessori|arts\s+workshop|classic|community\s+foundation|presbyterian|baptist|bid|business\s+improvement|main\s+street|resident|neighbor|rowhouse|home)|\bANC\s*6B\b|\blincoln\s+park\b(?=.*\b(SE|NE|capitol\s+hill|east\s+capitol|D\.?C\.?)\b)
  ```
  "Lincoln Park" needs the DC lookahead because Chicago has one. ("Eastern Market" also names a Detroit market. That's rare in DC feeds, but if you add wire feeds, add `(?<!detroit\W)` or require a DC cue there too.)
- B: `\bcapitol\s+hill\b` **plus** a cue in the same item:
  ```
  \b\d{2,4}\s+[\w\.]+\s+(st|street|ave|avenue|pl|place|ter|terrace)\.?\s+(s\.?e|n\.?e)\b|\bward\s*6\b|\bANC\s*6[ABC]\b|\browhouse|\bneighbou?rhood\b|\bhill\s+rag\b
  ```
  On WTOP's capitol-hill tag this kept "It's mosquito season and Capitol Hill residents are biting back" and the community items, and dropped Congress stories. Lever lists a solidcore studio as "Capitol Hill, **WA**" (Seattle), so jobs never match on the name alone.

**H Street NE**:
```
\bh\s+st(reet)?\.?\s*,?\s*n\.?e\b|\bh\s+street\s+(corridor|festival|main\s+street|streetcar|country\s+club)\b|\bon\s+H\s+Street\b|\batlas\s+(district|performing\s+arts|theat)|\bstarburst\s+(plaza|intersection)\b|\bANC\s*6A\b|\bANC\s*6C\b
```
Notes: "H Street" alone is ambiguous, because H St NW runs downtown (e.g. "601 H St NW"). Require the NE, "corridor" or "Festival" forms. ANC 6C also covers the Capitol Hill HPN's north side, so if you want H-Street-only, use "ANC 6C" only as a booster.

**Navy Yard**:
```
\bnavy\s+yard\b|\bcapitol\s+riverfront\b|\byards\s+park\b|\bcanal\s+park\b(?=.*\b(d\.?c|SE|navy)\b)|\bANC\s*(6/)?8F\b
```
plus case-sensitive `\bThe\s+Yards\b` (the lowercase "the yards" shows up in sports copy). Reject if `\b(brooklyn|philadelphia|boston|charleston|norfolk|portsmouth|mare\s+island|puget\s+sound|pearl\s+harbor)\s+navy\s+yard|naval\s+shipyard` is present and no SE cue is. "Navy Yard" also means the Navy installation itself (base news, the 2013 shooting), but that is in the neighborhood, so keep it. I recommend **not** matching `Nationals Park` / `Audi Field` alone, because game stories would flood the feed. Audi Field is at Buzzard Point (SW), outside the BID. Use them only as a boost, or match them in titles only for non-game items.

**Anacostia.** Accept if A, or B with a cue (B should be title-only).
- A:
  ```
  \bhistoric\s+anacostia\b|\bgood\s+hope\s+r(oa)?d\b|\b(mlk|martin\s+luther\s+king(,?\s+jr\.?)?)\s+(ave(nue)?|blvd)\.?\s*,?\s*(s\.?e\b)?|\bbig\s+chair\b|\banacostia\s+(arts\s+center|playhouse|bid|business\s+improvement|community\s+museum|neighborhood\s+library|library|high\s+school|metro|historic\s+district|neighborhood)\b|\bfrederick\s+douglass\s+(national\s+historic|house|home)|\bcedar\s+hill\b|\bmarion\s+barry\s+market|\bANC\s*8A\b
  ```
  Caveat: `MLK Ave` without SE also matches MLK Ave in other cities and DC's long MLK Ave south into Congress Heights. Keep "(SE)" optional only in DC-local feeds. "Cedar Hill" is the Douglass house **and** the new hospital (which is in the St. Elizabeths HPN); both are in common local use for "Anacostia".
- B: `\banacostia\b(?!\s+(river|watershed|riverwalk|waterfront|riverkeeper|river\s*partners|freeway|park))` **and** a cue `\bs\.?e\.?\b|\bsoutheast\b|\bward\s*8\b|\beast\s+of\s+the\s+river\b`. The negative lookahead drops the river ("Anacostia River Partners Announce Real-Time E. coli…" in Hill Rag), but it still let through "Annual Anacostia Boat Ride…" (Washington Informer, a river cruise). Hence apply B to **titles only**. The "Anacostia Park" exclusion is deliberate: it is the NPS riverside park, which runs well beyond the neighborhood.

**Columbia Heights**:
```
\bcolumbia\s+heights\b(?!.*\b(minn|minnesota|MN)\b)|\bDC\s?USA\b(?=.{0,40}\b(mall|shopping|center|target|garage)\b)|\btivoli\s+(theat|square)|\bgala\s+(hispanic\s+)?theat|\bcolumbia\s+heights\s+civic\s+plaza\b|\bpark\s+view\b(?=.*\b(d\.?c|NW|ANC)\b)|\bANC\s*1A\b|\bANC\s*1E\b
```
Columbia Heights MN is a Minneapolis suburb, so it needs the negative lookahead for wire copy. "DC USA" needs a mall cue because "Washington, DC USA" occurs. Park View is inside this HPN (ANC 1E), so "Park View" counts. Don't match "14th Street" or "Irving Street" alone.

### 0.3 Already-used general feeds, counted for the new areas

| Feed | robots | items | CH | HS | NY | AN | CO |
|---|---|---|---|---|---|---|---|
| `https://www.popville.com/feed/` p1 / `?paged=2` / `?paged=3` (≈5 days) | allow | 20 each | 2/0/0 (body) | 1/0/0 | 1/0/0 | 0 | 1/2/1 (p2–p3 one title each: "End of an Era on 14th Street in Columbia Heights: ZEBA closing…", "…Don Julio's… Sign Taken Down in Columbia Heights") |
| `https://ggwash.org/rss` | allow | 10 | 0 | 0 | 1 body | 0 | 0 |
| `https://washingtoncitypaper.com/feed/` | allow | 10 | 1 body | 0 | 0 | 0 | 0 |
| `https://www.washingtoninformer.com/feed/` (new; Black-press weekly, strong Wards 7/8) | allow | 10 (≈3 days) | 0 | 0 | 1 body (ANC 6/8F commissioner piece) | 0 | 0 |
| `https://www.wusa9.com/feeds/syndication/rss/news/local`, `https://www.fox5dc.com/rss/category/local-news`, `https://www.nbcwashington.com/?rss=y` | allow | 20/16/20 | 0/0/1 | 0 | 0/0/1 | 0/0/1 | 0 | General TV; 0–1 hits; optional. |

---

## 1. Capitol Hill (HPN `CAPITOL HILL`; ANC 6B + 6C)

### NEWS

| Feed (exact URL) | robots | items | CH hits (body / title) | Notes |
|---|---|---|---|---|
| `https://www.hillrag.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link` | allow, **Crawl-delay: 20** | 20 (19–31 Oct) | 7 / 1 | **Best CH source.** The RSS `/feed/` only returns 3 items, so use WP JSON. Titles include "ANC 6B Seeks Security Conditions for Café 8 After Shooting", "National Guardsman Shot in Barracks Row Gunfire Exchange", "Capitol Hill Day School", "Join The Dad Games – A Free Capitol Hill Family Festival". It's the CH paper, so taking it whole is defensible. Some items are calendar blurbs ("DC Beer Fest at Nats Park", National Gallery). Keyword-filter for CH, and also run the NY/HS rules on it. `/?s=` feed returns 0 items. Honour the 20 s crawl delay between requests to this host. |
| `https://thehillishome.com/feed/` (+ `?paged=2`) | allow | 5 per page | 4 / 0 (p2: 3 / 0) | CH blog: weekly "Hill Buzz" and "The To Do List". It's CH-specific, so **take all**. Titles are generic, so the regex only hits bodies. |
| `https://www.capitolhillcorner.org/feed/` | allow | 10 (19–29 Oct) | 3 / 0 | CH-specific blog (ANC 6B and community coverage, e.g. "Photos and Dueling Accounts Raise Questions About Café 8 Shooting"). **Take all.** |
| `https://www.chrs.org/feed/` (Capitol Hill Restoration Society) | allow | 10 (Oct 2025 – Oct 2026) | 7 / 2 | Slow (~1/month). "House Expo Set for October 31 at Eastern Market", "Stanton Park Neighbors Celebrate America's 250th…". Take all. |
| `https://www.hillcenterdc.org/feed/` | allow | 10 (Jan–Oct 2026) | 9 / 2 | Hill Center (921 Penn Ave SE) announcements. Low volume; take all. |
| `https://wtop.com/tag/eastern-market/feed/` | allow | 10 (Dec 2021 – Jan 2026) | 9 / 5 | Slow but clean ("Community street party celebrates 15th anniversary of Eastern Market reopening"). |
| `https://wtop.com/tag/barracks-row/feed/` | allow | 10 (2017 – Aug 2024) | 9 / 4 | **Stale** (newest Aug 2024). Low priority. |
| `https://wtop.com/tag/capitol-hill/feed/` | allow | 10 (May 2025 – Jul 2026) | 5 / 1 | Mixed with Congress. Use rule B. |
| `https://www.washingtonian.com/?s=eastern+market&feed=rss2&orderby=date&order=DESC` / `?s=barracks+row…` | allow | 10 / 10 | 7 / 0; 9 / 0 | Body mentions in roundups ("26 Things to Do…"). Title-only matching gives 0 today; keep for body-mention links only if you want volume. |
| `https://www.washingtonblade.com/?s=capitol+hill+neighborhood&feed=rss2&orderby=date&order=DESC` | allow | 10 | 8 / 0 | Body-only. Optional. |
| ANC 6B | — | — | — | `https://anc6b.org/feed/` is stale (2 items, newest Nov 2023). Use its meetings JSON for events (below). |
| ANC 6C | **DISALLOW** | — | — | `anc6c.org/robots.txt` is `User-agent: * / Disallow: /`. **Excluded.** Its feed works, but we may not fetch it. Use OANC (events). |

Not usable: Hill Now (`hillnow.com/feed/` 404, defunct); `capitalcommunitynews.com` (feed and JSON empty); Capitol Hill BID (`capitolhillbid.org`, **403 to our UA incl. robots.txt**); Barracks Row Main Street (`barracksrow.org`, Wix, no feed); Eastern Market (`easternmarket-dc.org/feed/` 200 with 0 items); `hilleast.org` (no DNS).

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **Hill Center** | `https://www.hillcenterdc.org/wp-json/tribe/events/v1/events?per_page=50&start_date=<today>` | **Yes.** robots allow. 680 upcoming events, 14 pages. Venue is always "Hill Center DC, 921 Pennsylvania Avenue, SE" (inside the HPN). Heavy on recurring classes ("Tippi Toes…", "Tai Chi Chuan", "Immersive Saturday Spanish for Kids"). Dedupe by title and drop classes (e.g. skip titles seen ≥3 times in 14 days), or filter by `categories`. |
| **CHRS** | `https://www.chrs.org/wp-json/tribe/events/v1/events` | **Yes.** 4 upcoming: "Annual House Expo" 31 Oct (North Hall at Eastern Market, 225 7th St SE), "Historic Preservation Committee Meeting" 2 Nov (420 10th St SE), "Zoning Committee Meeting" 4 Nov (Northeast Library, 330 7th St NE). Venue addresses are given, so point-in-polygon them. |
| **ANC 6B meetings** | `https://anc6b.org/wp-json/wp/v2/meetings?per_page=12&orderby=id&order=desc&_fields=id,date,title,link,content` (custom post type `meetings`) | **Partial.** robots allow. Titles are month-only ("November 2026 ANC6B Full Meeting", "November 2026 Transportation Committee Meeting", "November 2026 Southeast Library Task Force Meeting"). The full-meeting post body lists committee dates as "(11/02/2026)", "(11/04/2026)", "(11/05/2026)", "(11/16/2026)", "(11/21/2026)", but **does not state the full meeting's own date**. The location is in the body ("700 Pennsylvania Ave SE; First Floor"). Default `orderby=date` returns 2020 posts first, so use `orderby=id&order=desc`. Use OANC (next row) for the dated full meeting. The body also carries Zoom passcodes, so never republish body text. |
| **OANC** (already used) | `https://oanc.dc.gov/rss.xml` | **Yes** for 6B and 6C. Today it includes "December 9, 2026, ANC 6C Public Meeting", "November 12, 2026, ANC 6C Public Meeting", and older 6B items ("April 8, 2025, ANC 6B Public Meeting"). Parse the title date; filter `ANC 6[BC]`. The 10-item window means hits come and go. |
| Congressional Cemetery (nearby, STADIUM ARMORY HPN) | `https://www.congressionalcemetery.org/wp-json/tribe/events/v1/events` | Works. 124 events (tours, "Soul Strolls", and "Closed to Dogs" closure entries to drop). Label it "nearby" or skip. |
| Eastern Market | `easternmarket-dc.org` | **No.** WordPress with no events post type (`/wp-json/wp/v2/types` lists only `blog_post`); tribe 404. Use a static "open Tue–Sun" note. |
| Folger | `folger.edu` | **No.** WordPress, no events type in `/wp-json/wp/v2/types`, tribe 404. |
| Capitol Hill BID / Barracks Row MS | — | 403 / Wix with no feed. |
| Library of Congress | `https://www.loc.gov/events/?fo=json` | JSON works (robots allow), but 10 1st St SE is in the **NATIONAL MALL** HPN. Optional "nearby". |

### JOBS

**No qualifying in-area source today.** Probed: Children's National (no Capitol Hill site among its 31 location facets); Greenhouse, Lever and Ashby slugs for Folger, Hill Center, Capitol Hill Day School and others (no boards); solidcore has "Capitol Hill, WA" only. CVS's Workday tenant (`cvshealth.wd1…/CVS_Health_Careers`, robots allow) has 70 "DC - Washington" jobs **without store addresses**, so they can't be placed. Excluded. Hill Rag's job ads are not machine-readable.

### HISTORY → see §6.

---

## 2. H Street NE (SMDs 6A01, 6A02, 6A06, 6C04, 6C05, 6C06; HPN UNION STATION; ANC 6A + 6C)

### NEWS

| Feed (exact URL) | robots | items | HS hits (body / title) | Notes |
|---|---|---|---|---|
| `https://www.hillrag.com/wp-json/wp/v2/posts?per_page=20…` | allow (Crawl-delay 20) | 20 | 0 / 0 today | Same request as Capitol Hill; run the HS rule on it. Hill Rag regularly covers 6A/6C. |
| `https://eastoftheriverdcnews.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link` | allow | 20 (14–31 Oct) | 1 title in 40 ("Atlas Performing Arts Center Honors Dolly Parton's Legacy…", 12 Oct) | Same publisher. Many posts are shared with Hill Rag. |
| `https://thehillishome.com/feed/` (+ `?paged=2`) | allow | 5 + 5 | 1 + 1 body | Hill Buzz covers H St. |
| `https://wtop.com/tag/h-street-corridor/feed/` | allow | 10 (Sep 2014 – Apr 2026) | 10 / 2 | Clean but slow: "'We are dying': Neighbors look for crime solutions along the H Street corridor" (1 Apr 2026), "H Street Festival brings colorful crowds to corridor". |
| `https://wtop.com/tag/h-street/feed/` | allow | 10 (Sep 2023 – Mar 2026) | 8 / 1 | Overlaps the above; dedupe by link. |
| `https://www.popville.com/feed/` p1–3 | allow | 60 | 1 body | General matcher. |
| ANC 6A | `https://anc6a.org/feed/` | allow | 10 | 10 / 4 | **Stale: newest 13 Feb 2015.** The site is alive (pages updated 26 Oct 2026) but doesn't post news. Use its Agendas page (events). |
| ANC 6C | — | **DISALLOW** | — | — | See Capitol Hill. |

Not usable: H Street Main Street (`hstreet.org/feed/` 200, 0 items; use its events API instead); `hstreetnews.com`, `hstreetmainstreet.org` (no DNS); `wtop.com/tag/h-street-ne/feed/` (1 item, 2017); Washingtonian `?s=h+street+ne` (a non-phrase search; 1 HS body hit in 10, mostly noise); Atlas Performing Arts (`atlasarts.org`, tribe 404, no feed found).

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **H Street Main Street** (hstreet.org; its About page says "H Street Main Street's mission…") | `https://www.hstreet.org/wp-json/tribe/events/v1/events?per_page=50&start_date=<today>` | **Works but thin.** robots allow. 105 events over 3 pages, **all "H Street NE Year-Round Market"** (FRESHFARM, 800 13th St NE, Saturdays 9:30, through Oct 2027). Show the market as one recurring item. Festival and Second Saturdays pages exist (`/second-saturdays-on-h/`, `/mardigrasonh/`) but are not in the API. |
| **ANC 6A agendas** | `https://anc6a.org/wp-json/wp/v2/pages?slug=agendas&_fields=modified,content` | **Yes (parse the page JSON).** robots allow. Content lists "October 8, 2026 (package) / October 8, 2026 (agenda only) / … September 10, 2026 …". Regex `([A-Z][a-z]+\.? \d{1,2},? \d{4}) \(agenda only\)` gives meeting dates, each linking to its PDF. ANC 6A meets the 2nd Thursday (8 Oct, 10 Sep, 9 Jul, 11 Jun, 14 May all fit). The next meeting appears once its agenda is posted. Note the typos in the source ("June 11. 2026", "May, 14, 2026"), so normalise punctuation before parsing. |
| ANC 6A community calendar | `https://anc6a.org/community-calendar/` | **No.** Text only; no embedded calendar or iCal. |
| **OANC** | `https://oanc.dc.gov/rss.xml` | 6C meetings ("November 12, 2026, ANC 6C Public Meeting") as above. Filter `ANC 6[AC]`. |
| Atlas Performing Arts Center (1333 H St NE, SMD 6A06) | — | No machine-readable calendar found (tribe 404). |

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **solidcore H St** (Lever) | `https://api.lever.co/v0/postings/solidcore?mode=json`, filter `text` endswith `- H St, DC` | "Core Crew (Front Desk & Sales) - H St, DC", `createdAt` 2023-02-08, `https://jobs.lever.co/solidcore/2b1561a2-5a3d-420f-9c86-2443ec9a36b3`. The posting has no street address; the studio is named in the title only. | allow (`Crawl-delay: 1`) | **Usable but weak**: an evergreen talent-pool posting (created 2023), so the date is old. If used, show it without a "posted" date or with "ongoing". |
| Others probed | Greenhouse, Lever and Ashby slugs incl. andpizza, chipotle, shakeshack, bluejacket, neighborhoodrestaurantgroup, atlasarts, kippdc, friendship, dcprep (9 jobs, none on H St) | — | — | Nothing on H St. |

---

## 3. Navy Yard (Navy Yard BID polygon; HPN SW/WATERFRONT; ANC 6/8F + parts of 6B, 6D)

### NEWS

| Feed (exact URL) | robots | items | NY hits (body / title) | Notes |
|---|---|---|---|---|
| `https://wtop.com/tag/navy-yard/feed/` | allow | 10 (12 Apr – 1 Jul 2026) | 10 / 4 | **Best current feed.** "4th teenager arrested following Navy Yard Chipotle brawl", "Police release photos…". |
| `https://www.washingtonian.com/?s=navy+yard&feed=rss2&orderby=date&order=DESC` | allow | 10 (25 Sep – 26 Oct 2026) | 10 / 1 | "Latin-Euro Bar Nuestro in Navy Yard Isn't Your Average Bistro". Mostly roundup body mentions. |
| `https://www.washingtonian.com/?s=capitol+riverfront&feed=rss2&orderby=date&order=DESC` | allow | 10 (Oct 2025 – May 2026) | 10 / 1 | Slower ("Catahoula Brings Crawfish Boils and Sazeracs to Navy Yard"). |
| `https://www.hillrag.com/wp-json/wp/v2/posts…` | allow (Crawl-delay 20) | 20 | 2 / 1 | "Nightmare at Navy Yard at Supplyhouse"; 18 Oct "Capitol Cuisine Samples A Navy Yard Izakaya" (in the newest 40). |
| `https://thehillishome.com/feed/` | allow | 5 + 5 | 3 + 1 body | To Do List mentions. |
| `https://wtop.com/tag/the-yards/feed/` / `…/capitol-riverfront/feed/` / `…/yards-park/feed/` | allow | 10 / 10 / 6 | 10/8; 10/8; 6/3 | **Stale**: newest Feb 2024 / May 2024 / Feb 2023. Low priority. |
| `https://www.washingtonblade.com/?s=navy+yard&feed=rss2&orderby=date&order=DESC` | allow | 10 | 10 / 0 | Body mentions in event roundups only. |
| `https://wtop.com/tag/southeast-dc/feed/` | allow | 10 | 2 / 1 | "Man dies after being rescued from Anacostia River near Navy Yard…". Optional. |
| ANC 6/8F | `https://anc8f.dc.gov/rss.xml` | allow | 10 | 10 / 0 (rule matches on ANC 8F) | Drupal feed of commissioner profiles and meeting nodes (newest 10 Jun 2026). Little news; use it for events. `anc8f.org` (Squarespace) has no blog feed (`/feed/` 404). |
| ANC 6D | `https://anc6d.org/feed/` | allow | 0 | — | WordPress feed empty; posts JSON empty. Only 6D07/6D08 (~16%) touch the BID. |

Not usable: Capitol Riverfront / Navy Yard BID (`capitolriverfront.org` → `navyyarddc.org`, Webflow): robots allow, but `/feed/`, `/rss.xml`, `/events/rss.xml`, `/news/rss.xml` all 404. The sitemap lists 9 `/news/` and 27 `/event/` pages, but they are HTML only with no JSON-LD. **No feed.** JDLand (`jdland.com`, no feed); Yards Park (`yardspark.org`, TLS handshake timeout; untested).

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **ANC 6/8F meetings** | `https://anc8f.dc.gov/rss.xml` | **Yes, parse the title**: "March 24, 2026, ANC 6/8F Public Meeting", "April 7, 2026, ANC 6/8F Special Public Meeting". Watch for wrong-year titles ("February 18, 2025, ANC 6/8F Public Meeting" posted 9 Jun 2026), so drop dates in the past. Non-meeting items ("Commissioner …", "Join us at our next Neighborhood Night at La Famosa!") have no date; skip them. |
| ANC 6/8F (anc8f.org) | `/events?format=json`, `/meetings?format=json` | Squarespace pages with **empty** content (no event collection); `?format=rss` gives 400. No. |
| ANC 6D schedule | `https://www.anc6d.org/wp-json/wp/v2/pages?slug=anc-6d-meeting-schedule-2&_fields=modified,content` | Parseable list ("Monday, Jan. 5 (via Zoom) … Tuesday, Sept. 8** (in person) … Monday, Oct. …", all at 7 pm, year in heading "2026"). Only ~16% of the BID; optional. |
| Navy Yard BID events | `https://navyyarddc.org/events`, `/event/<slug>` | **HTML only** (Webflow, no RSS, no JSON-LD). robots allows it, but it's not machine-readable under our rule. **Excluded.** Ask the BID whether it can turn on Webflow's collection RSS. |
| Nationals Park / Audi Field / Yards Park | — | No feed tested that qualifies. MLB schedule downloads are subject to MLB terms (not reviewed); Yards Park is unreachable (TLS timeout). |
| Hill Rag calendar blurbs | Hill Rag WP JSON | Some posts are event blurbs ("DC Beer Fest at Nats Park", "Nightmare at Navy Yard at Supplyhouse"), but they have no structured date. News, not events. |

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **solidcore Navy Yard** (Lever) | `https://api.lever.co/v0/postings/solidcore?mode=json`, `text` endswith `- Navy Yard, DC` | "Core Crew (Front Desk & Sales) - Navy Yard, DC", created 2023-02-08, `https://jobs.lever.co/solidcore/ecb3ea2b-dd25-446c-987f-a817f46757bb`. No address. | allow | Weak (evergreen), same caveat as H St. |
| DOT HQ, Navy (WNY) | USAJOBS | — | robots-blocked (known) | Excluded. |
| DC Water HQ (1385 Canal St SE, in the BID), Brookfield, JBG Smith, Nationals, DC United, WC Smith | Workday guesses (`dcwater.wd1/DCWater`, `brookfield*.wd*`, `jbgsmith.wd1`) → 422 (wrong or no tenant); Greenhouse/Lever/Ashby slugs `nationals`, `washingtonnationals`, `mlb`, `dcunited`, `audifield`, `wcsmith`, `brookfieldproperties`, `jbgsmith` → none | — | — | **No verified feed.** |
| sweetgreen (Greenhouse) | `https://boards-api.greenhouse.io/v1/boards/sweetgreen/jobs` | 67 jobs; DC = 601 Massachusetts Ave NW + an unspecified "Washington, DC" | allow | No Navy Yard jobs today. |

---

## 4. Anacostia (HPN `HISTORIC ANACOSTIA`; ANC 8A ~60% + 8B ~40%)

### NEWS

| Feed (exact URL) | robots | items | AN hits (body / title) | Notes |
|---|---|---|---|---|
| **`https://anacostiabid.org/news?format=rss`** (Squarespace) | allow | 20 (23 Aug – 23 Oct 2026) | 7 / 4 | **Best AN source.** "Household Battery Recycling Now Available at Marion Barry Market in Historic Anacostia", "'We Make History' at the Anacostia Community Museum…", "Art All Night Returns to Historic Anacostia September 11…". The BID area is mostly St. Elizabeths HPN (§0.1) and it also reposts citywide items ("DC Celebrates 10 Years of 202Creates…"), so keyword-filter rather than taking all. |
| `https://eastoftheriverdcnews.com/wp-json/wp/v2/posts?per_page=20&_fields=date,title,content,link` | allow | 20 (14–31 Oct) | 2 / 0 | Capital Community News' Wards 7/8 paper. **Use JSON**: its RSS `/feed/` returns only 1 item. In the newest 40: "ANC 8C Wants A Say In Barry Farm's Redevelopment" (13 Oct), "ACM Celebrates 59 Years Of Community Stories" (29 Sep). It shares many posts with Hill Rag; dedupe by title. |
| `https://wtop.com/tag/anacostia/feed/` | allow | 10 (Aug 2025 – Jun 2026) | 6 / 2 | "Inside Southeast Sourdough, Anacostia's fresh-milled bakery on the rise", "New grocery store opens in Anacostia…". |
| `https://wtop.com/tag/ward-8/feed/` | allow | 10 (Jul 2025 – May 2026) | 6 / 1 | Overlaps the tag above. |
| `https://wtop.com/tag/southeast-dc/feed/` | allow | 10 | 2 / 1 | "'Growing pains' and financial losses: DC's Cedar Hill hospital…". The hospital is in St. Elizabeths, so this is borderline. |
| `https://www.washingtonian.com/?s=historic+anacostia&feed=rss2&orderby=date&order=DESC` | allow | 10 (Jul – Oct 2026) | 6 / 0 | Body mentions only ("Brent Leggs on Suing Trump and Saving Historic Places"). |
| `https://www.washingtoninformer.com/tag/ward-8/feed/` | allow | 10 (Aug – Oct 2026) | 1 / 0 | Its hit, "Annual Anacostia Boat Ride…", is a river false positive, which shows why rule B must be title-only. The Informer's `?s=anacostia` feed returns 0 items. |
| `https://www.washingtonblade.com/?s=anacostia&feed=rss2&orderby=date&order=DESC` | allow | 10 | 4 / 0 | Body-only. Optional. |
| **ANC 8A** `https://anc8a.dc.gov/rss.xml` | allow | 10 | 9 / 8 | Meeting nodes plus the occasional notice ("How to Get Help with your Energy Bills"). Take all, as for Tenleytown's ANC. |

Not usable: `anc8a.org` (TLS hostname mismatch); `anc8b.org`, `anc8b.dc.gov`, `anc8c.dc.gov` (no DNS). **No ANC 8B source found**, though 8B is ~40% of the HPN. The Anacostia Arts Center (`anacostiaartscenter.com`) is WordPress with no news feed. The Anacostia Playhouse domain didn't resolve.

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **ANC 8A meetings** | `https://anc8a.dc.gov/rss.xml` | **Yes.** "November 4, 2026, ANC 8A Public Meeting" (posted 9 Oct), "December 1, 2026, 8A Virtual Meeting", "October 7, 2026, ANC 8A Public Meeting". Parse the title (the `<description>` date is post time). Drop past dates ("March 30, 2026, ANC 8A Special Meeting" was re-posted 9 Oct). Note the inconsistent prefix ("8A Virtual Meeting" lacks "ANC"). |
| OANC | `https://oanc.dc.gov/rss.xml` | Today: "October 21, 2026, ANC 8A Special Public Meeting" and older 8A items. Use as a backup. |
| Anacostia BID events | `https://anacostiabid.org/events-1`, `/events-2` | **No.** Squarespace *pages* (not event collections). `?format=json` returns page HTML-in-JSON; JSON-LD is Organization/LocalBusiness only. Events reach the BID's news RSS as posts ("Art All Night Returns… September 11"), but without structured dates. |
| Anacostia Arts Center | `https://anacostiaartscenter.com/wp-json/wp/v2/event_feed` | **No.** The CPT `event_feed` holds 2 feed-config objects ("AAC Events"), not events; the plugin renders HTML from an external source. Tribe 404. |
| Anacostia Community Museum / Frederick Douglass NHS (both inside the HPN) | — | Not tested to a feed (Smithsonian / NPS). Smithsonian's event calendar is a candidate to check later; not verified. |

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **Children's National, "Anacostia" site** | `POST https://childrensnational.wd108.myworkdayjobs.com/wday/cxs/childrensnational/CN_Careers/jobs`, body `{"appliedFacets":{"locations":["8788a69939e31000c397639631920000"]},"limit":20,"offset":0,"searchText":""}` (look up the id by descriptor "Anacostia" nightly) | **2 jobs**: "Nutritionist II" (startDate 2026-10-22; posting text gives **2101 Martin Luther King Jr. Ave** = HISTORIC ANACOSTIA, SMD 8A06) and "Pediatrician (Primary Care Anacostia)" (2026-06-25). Primary `location` = "Anacostia" for both. | allow | **Use ("in").** Same tenant already used. |
| Children's National "THEARC" (`8788a69939e31000c397a2d2ca3c0000`) | same | 2 jobs ("CDL Driver (Class A) – Mobile Unit Driver – PRN", "Dentist (20hrs/wk)"); 1801 Mississippi Ave SE = **DOUGLASS** HPN | allow | "Nearby" at most (≈1.5 mi). |
| Children's National "Cedar Hill Med Ctr" (`8788a69939e31000c397d92083390000`) | same | 1 job ("Hospitalist (CA), Cedar Hill Neonatology"); 1200 Pecan St SE = SAINT ELIZABETHS HPN | allow | "Nearby" at most. |
| Unity Health Care, Busboys & Poets (2004 MLK, in the HPN), Smithsonian ACM | Workday guess `unityhealthcare.wd1` → 422; Greenhouse/Lever/Ashby `unityhealthcare`, `unity`, `busboysandpoets`, `busboys` → none; Smithsonian = USAJOBS (blocked) | — | — | No verified feed. |

---

## 5. Columbia Heights (HPN `COLUMBIA HEIGHTS`; ANC 1A ~51% + 1E ~41% + 1D)

### NEWS

| Feed (exact URL) | robots | items | CO hits (body / title) | Notes |
|---|---|---|---|---|
| `https://www.popville.com/feed/` p1–3 | allow | 60 | 4 / 2 | **Best general source for CO** (PoPville's home turf): "End of an Era on 14th Street in Columbia Heights: ZEBA closing after 15 Years…" (29 Oct), "…Don Julio's (Grocery/Pupuseria) Sign Taken Down in Columbia Heights", "Shooting Homicide in Park View…". Already in the engine. |
| `https://wtop.com/tag/columbia-heights/feed/` | allow | 10 (Feb 2024 – Mar 2026) | 10 / 3 | "Salvadoran restaurant in Columbia Heights struggles amid fears of ICE raids", "Homicide suspect dead after shootout with DC police in Columbia Heights". |
| `https://www.washingtonian.com/?s=columbia+heights&feed=rss2&orderby=date&order=DESC` | allow | 10 (25 Aug – 30 Oct 2026) | 8 / 0 | Body mentions ("DC Is Getting Its Own Beatboxing Competition"). |
| `https://www.washingtonblade.com/?s=columbia+heights&feed=rss2&orderby=date&order=DESC` | allow | 10 (Sep 2025 – Oct 2026) | 10 / 1 | "José Zayas brings 'The House of Bernarda Alba' to GALA Hispanic Theatre". |
| **ANC 1E** `https://anc1e.org/feed/` | allow | 10 (Mar – Aug 2026) | 10 / 6 | Park View / east Columbia Heights. Real news posts ("ANC 1E Hosts Public Safety Community Meeting…", "ANC 1E Calls on DC Health to Fix Rat Birth-Control Pilot…"). Take all. |
| **ANC 1E** `https://anc1e.dc.gov/rss.xml` | allow | 10 (Jul – 29 Oct 2026) | 9 / 6 | Meeting nodes plus repeats of the anc1e.org news; dedupe by title. |
| ANC 1A | `https://anc1a.org/feed/` | allow | 0 | — | WordPress feed empty. Use its Agenda page (events). |

Not usable: **Park View D.C. blog (`parkviewdc.com/feed/`) is robots-DISALLOWED for our agent. Excluded.** MidCity DC (`midcitydc.com`, now a parked domain); `columbiaheightsnews.com` (no DNS); `anc1a.dc.gov`, `anc1d.dc.gov` (no DNS); `anc1d.org` (Squarespace, `/feed/` 404); `wtop.com/tag/park-view/feed/` (0 items).

### EVENTS

| Source | Endpoint | Result |
|---|---|---|
| **ANC 1A agenda** | `https://anc1a.org/wp-json/wp/v2/pages?slug=agenda&_fields=modified,content` | **Yes.** robots allow. Content: "Regular Meeting Wednesday, November 18, 2026 Time: 7:00 P.M. Location: Harriet Tubman Elementary School (3101 13th St NW) and via Zoom". Regex on `Regular Meeting\s+\w+day,\s+(\w+ \d{1,2}, \d{4})`. The `/calendar/` page only points to a Zoom Events hub, so no feed. |
| **ANC 1E meetings** | `https://anc1e.dc.gov/rss.xml` | **Partial.** Titles like "ANC 1E Jan. 2027 Regular Meeting", "ANC 1E Jan. 2027 Committee of the Whole Regular Meeting" give only a month. "Park View Recreation Center Community Meeting: November 10, 2026" has a full date. Accept only titles with a full date; skip month-only ones. |
| GALA Hispanic Theatre (3333 14th St NW, in the HPN) | `galatheatre.org` | Squarespace; `www.` robots returned **429**, tribe 404. Not usable. |
| Columbia Heights & Mt Pleasant Main Street | — | Exists in DC's Main Streets layer (82% CH HPN), but no website found (guessed domains don't resolve). |
| Farmers market | existing layer | FRESHFARM Columbia Heights (Wed/Sat, from the earlier note), already in the engine. |

### JOBS

| Employer / source | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **TJX (Marshalls at DC USA)** | `POST https://tjx.wd1.myworkdayjobs.com/wday/cxs/tjx/TJX_EXTERNAL/jobs`, body `{"appliedFacets":{},"limit":20,"offset":0,"searchText":"Washington DC"}` → 9 DC jobs; keep those whose `locationsText` is `Washington, DC 20010` **and** whose detail (`GET https://tjx.wd1.myworkdayjobs.com/wday/cxs/tjx/TJX_EXTERNAL<externalPath>`, field `jobPostingInfo.jobDescription`) contains `3100 14th St` | **3 jobs** at **3100 14th St NW** (DC USA; HPN COLUMBIA HEIGHTS, SMD 1A05): "Merchandise Coordinator" (startDate 2026-10-20), "merchandise associate" (2026-10-20), "merchandise associate" (2026-09-16). The other 6 are Georgetown (3254 M St), downtown (601 13th St NW), Brentwood (2480 Market St NE) and 5300 Wisconsin. | allow | **Use ("in").** Same Workday cxs API as Children's National. Filter on the address, not the zip: 20010 also covers Petworth and Park View. |
| **Children's National, "Columbia Heights"** (`8788a69939e31000c397793ee6910000`) | as already used | 2 jobs: "Pediatrician (CA) Primary Care Columbia Heights (PRN)" (2026-09-25), "LPN II – Primary Care Columbia Heights" (2026-08-12). Posting text has no street address. | allow | **Use** (already wired). |
| Mary's Center, Safeway | — | — | Mary's Center JobBoardView DISALLOW; Safeway terms unverified (per earlier notes) | Excluded. |
| Target (DC USA), Best Buy, Giant (Park Rd), Ross | Target excluded as before; Workday guesses for Best Buy, Ross, Ahold/Giant → 422 | — | — | No verified feed. |
| CVS (`cvshealth.wd1…/CVS_Health_Careers`) | 70 "DC - Washington" jobs | No store address in postings | allow | Can't be placed; excluded. |

---

## 6. HISTORY (Evening Star, loc.gov)

loc.gov answered normally. I used the same query shape as `history.py` (`q="<term>"`, `dates=1926-10-31/1926-11-06`, `fa=partof_title:evening star (washington, d.c.) 1854-1972`, `fo=json`). "Week" = target week, "Oct–Nov" = 1926-10-01 → 11-30. I read OCR text (word-coordinates service, `full_text`) for up to 5 pages per main term.

**Two general pitfalls found:**
1. **loc.gov ignores single-letter words.** `"H street northeast"` returns 32 pages that week, but most hits are "Twentieth street northeast", "Fourth street northeast" and so on, and `"M street southeast"` (25) is the same. The counts for lettered streets are meaningless. Query `"H street"` (339 pages!) and require the regex locally (`\bH\s+street\s+n(orth)?\.?\s?e\b|\bH\s+st\.?\s+n\.?\s?e\b`). Sampled hits: "repairs 1251 H street northeast (lot 808, square 1004)" (building permits), "EMPIRE 911 H Street N.E." (movie ad).
2. **"navy yard" in 1926 is mostly other Navy Yards**: all sampled hits in the week were Philadelphia or Norfolk Navy Yard (battleship modernization). `"Washington Navy Yard"` has only 2 pages.

### Capitol Hill

| Term | Week | Oct–Nov | Notes |
|---|---|---|---|
| `"Capitol Hill"` | 10 | 93 | 1926 uses it for the **neighborhood** often: "the Capitol Hill churches", "ONE OF THE FINEST BUILDINGS ON CAPITOL HILL", "apartment… preferably Capitol Hill". The Congress sense appears too ("headquarters on Capitol Hill"). Needs a cue. |
| `"Lincoln Park"` | 19 | 209 | **Clean and local**: "The Lincoln Park Citizens Association has appointed committees…", "Massachusetts ave. at Lincoln Park", "NEAR LINCOLN PARK FOR $8,250". (`"Lincoln Park Citizens"`: 3.) Chicago's park is a residual risk. |
| `"Stanton Park"` | 1 | 29 | "NEAR STANTON PARK… 312 6th st n.e." Unambiguous. |
| `"East Capitol street"` | 2 | 27 | Unambiguous. |
| `"Marine Barracks"` | 4 | 27 | DC's at 8th & I SE, but also Quantico and other posts; needs "8th" / "southeast". |
| `"Pennsylvania avenue southeast"` | 1 | 18 | Unambiguous. |
| `"Eastern Market"` / `"Seward Square"` / `"Folger"` | 0 / 0 / 0 | 11 / 11 / 0 | Rare (the Folger opened in 1932). |

**Recommended terms:** `"Lincoln Park"`, `"Capitol Hill"`, `"Stanton Park"`, `"East Capitol street"`, `"Pennsylvania avenue southeast"`, `"Eastern Market"`.
- **pattern**:
  ```
  lincoln\s+park|stanton\s+park|east\s+capitol\s+st|pennsylvania\s+av(enue|e)?\.?\s+(southeast|s\.?\s?e)|eastern\s+market|seward\s+square|capitol\s+hill
  ```
- **local** (required when the only hit is `capitol hill` or `lincoln park`):
  ```
  s\.\s?e\.|n\.\s?e\.|southeast|northeast|citizens|church|apartment|rooms|lincoln\s+park\s+citizens|east\s+capitol|massachusetts\s+av|\b1[0-3]th\s+st|\b[4-9]th\s+st
  ```
- **reject** a `capitol hill` clip containing `senat|congress|house\s+of\s+rep|legislat|committee\s+on` with no local cue; reject `lincoln\s+park` with `chicago|ill\.`.

### H Street NE

| Term | Week | Oct–Nov | Notes |
|---|---|---|---|
| `"H street"` (+ local regex for NE) | 339 (all quadrants) | — | See pitfall 1. Sampled NE hits are building permits and the Empire theater (911 H St NE). Expect a few true clips per week. |
| `"Northeast Washington"` | 6 | 21 | "THE PRETTIEST LITTLE HOME IN northeast Washington: 1207 6th st. n.e.", plus a "Northeast Washington" bowling team. Too broad (all NE). Booster only. |
| `"Union Station"` | 27 | 258 | Mostly train and travel copy, not the neighborhood. Don't use. |
| `"Gallaudet"` | 8 | 52 | The college at Florida Ave NE, just north of the corridor and outside the SMDs. Booster only. |
| `"Trinidad"` | 16 | 124 | **Caribbean** cruise and shipping ads. Reject. |
| `"Benning road"` / `"Florida avenue northeast"` / `"Maryland avenue northeast"` | 2 / 0 / 0 | 13 / 5 / 13 | Rare; Benning Rd is east of the corridor. |

**Recommended terms:** `"H street"` (the only productive one) plus `"Northeast Washington"` as a second query.
- **pattern**: `\bH\s+st(reet|\.)?\s*,?\s*n(orth)?\.?\s?e(ast)?\b|\b(9|1[0-4])\d\d\s+H\s+st` (the second form needs an NE cue in the clip).
- **local**: `n\.\s?e\.|northeast|\b([3-9]|1[0-5])(st|d|th)\s+st(reet)?\s+n|empire\s+theat|atlas\s+theat|gallaudet|florida\s+av` (The Atlas theater opened in 1938, so it will be rare.)
- **reject**: `n\.\s?w\.|northwest` in the same clip when no NE cue is present (H St NW downtown dominates the 339 hits).

### Navy Yard

| Term | Week | Oct–Nov | Notes |
|---|---|---|---|
| `"navy yard"` | 12 | 96 | **All sampled hits in the week were Philadelphia/Norfolk Navy Yard.** Needs a DC cue. |
| `"Washington Navy Yard"` | 2 | — | Unambiguous but rare. |
| `"M street southeast"` | 25 (unreliable, pitfall 1) | 203 | Query `"M street"` and filter locally instead. |
| `"Eighth street southeast"` | 1 | 8 | Barracks Row / Navy Yard gate. |
| `"Southeast Washington"` | 0 | 11 | Rare. |
| `"Garfield Park"` / `"Navy Yard Bridge"` | 0 / 0 | 3 / 1 | Rare. |

**Recommended terms:** `"navy yard"`, `"Washington Navy Yard"`, `"Eighth street southeast"`, `"M street"` (local filter), `"Southeast Washington"`. Expect **0–3 usable clips** in a typical week; the 1926 Navy Yard area was industrial (the "Naval Gun Factory").
- **pattern**: `washington\s+navy\s+yard|navy\s+yard\s+(here|in\s+this\s+city|employes|workers|gate)|gun\s+factory|\bM\s+st(reet|\.)?\s+(southeast|s\.?\s?e)|(8th|eighth)\s+st(reet|\.)?\s+(southeast|s\.?\s?e)|southeast\s+washington`
- **reject** any clip with `(philadelphia|norfolk|brooklyn|new\s+york|boston|charleston|portsmouth|mare\s+island|puget\s+sound|pearl\s+harbor)\s+navy\s+yard|navy\s+yards` and no `washington\s+navy\s+yard|s\.\s?e\.|southeast`.

### Anacostia

| Term | Week | Oct–Nov | Notes |
|---|---|---|---|
| `"Anacostia"` | 25 | 225 | **In the week, sampled hits were the town**: "Anacostia Lodge, in Masonic Hall, Anacostia", "Helen … Anacostia Station, sends in a cartoon". `"Anacostia River"` had 0 pages that week, so the river sense is a minority, but it is real in other weeks (and "Anacostia flats/Park/bridge"). |
| `"Nichols avenue"` | 3 | 24 | 1926 name of MLK Ave SE. Clean: "Nichols avenue and Howard street southeast", "S street and Nichols avenue southeast", "each side of Nichols avenue, Anacostia". |
| `"Good Hope road"` | 0 | 26 | Unambiguous; quiet this week. |
| `"Uniontown"` | 0 | 5 | The pre-1886 name; rare by 1926 (also a PA city). |
| `"Congress Heights"` | 16 | 71 | **Outside** the HPN (Congress Heights/St. Elizabeths). Don't use. |
| `"Barry Farm"` / `"Anacostia citizens"` | 0 / 0 | 4 / 5 | Rare; Barry Farm is outside the HPN anyway. |

**Recommended terms:** `"Anacostia"`, `"Nichols avenue"`, `"Good Hope road"`, `"Uniontown"`.
- **pattern**: `anacostia(?!\s+(river|flats?|park|water\s*front|bridge|reclamation|basin))|nichols\s+av|good\s+hope\s+r(oa)?d|uniontown(?!,?\s+pa)`
- **reject** a clip whose only hits are `anacostia\s+(river|flats|park|reclamation|basin)`, and `uniontown` near `pa\.|pennsylvania`.
- **local** (optional booster): `s\.\s?e\.|southeast|nichols\s+av|good\s+hope|masonic\s+hall|anacostia\s+station|anacostia\s+citizens|w\s+st(reet)?\s+s|cedar\s+hill|douglass`

### Columbia Heights

| Term | Week | Oct–Nov | Notes |
|---|---|---|---|
| `"Columbia Heights"` | 26 | 205 | **Clean and rich**: "TAX ASSESSORS CALLED TOO FEW — Columbia Heights Citizens Believe Capital Should Have 16 More" (St. Stephen's Parish Hall, 3017 Fourteenth street), "Columbia Heights Community Center", real-estate ads ("Columbia Heights, just off 14th st."). |
| `"Tivoli"` | 15 | 154 | Crandall's Tivoli Theater (14th & Park Rd) is the real one: "Crandall's Tivoli Theater", movie listings. Use `tivoli\s+theat`; listings will dominate. |
| `"Park road"` | 37 | 243 | Inside the HPN (1100–1300 Park Rd NW check out), but it also runs into Mt Pleasant and Petworth. Booster only. |
| `"Irving street"` | 8 | 61 | Also Irving St NE (Brookland). Needs NW. |
| `"Columbia road"` | 26 | 266 | Mostly Adams Morgan. Don't use. |
| `"Central High"` | 37 | 258 | Central High (13th & Clifton, now Cardozo) is in **SOUTH COLUMBIA HEIGHTS** HPN, not this one; mostly sports. Don't use. |
| `"Fourteenth street northwest"` / `"Meridian Hill"` | 1 / 3 | 9 / 53 | The Star usually writes "14th st." Low. |

**Recommended terms:** `"Columbia Heights"`, `"Tivoli"`, `"Park road"`, `"Irving street"`.
- **pattern**: `columbia\s+heights|tivoli\s+theat|crandall.s\s+tivoli|1[0-4]\d\d\s+park\s+r(oa)?d|(1[0-6]\d\d|3[0-5]\d\d)\s+irving\s+st`
- **reject** `columbia\s+heights` near `minn|minneapolis` (rare in 1926), and `irving\s+st` near `n\.\s?e\.|northeast|brookland`.
- **local**: `14th\s+st|fourteenth|park\s+r(oa)?d|irving|harvard\s+st|girard\s+st|columbia\s+heights\s+citizens|tivoli|sherman\s+av|georgia\s+av`

## 7. Not verified / excluded

- **Robots-disallowed for our agent:** `anc6c.org` (`Disallow: /` for `*`), `parkviewdc.com`. Previously known: Mary's Center JobBoardView, USAJOBS, WTOP `?s=`.
- **403 to our UA (not retried):** `capitolhillbid.org` (including robots.txt), `axios.com/local/washington-dc/feed`.
- **No machine-readable source:** Navy Yard BID events and news (Webflow HTML), Anacostia BID events (Squarespace pages), Anacostia Arts Center (plugin), Eastern Market, Folger, Barracks Row (Wix), Atlas, GALA (429).
- **Unreachable:** `yardspark.org` (TLS timeout), `anc8a.org` (TLS mismatch), `anacostiaplayhouse.com`, `anc8b`/`8c` hosts, `hilleast.org`.
- **Not tested:** Smithsonian/NPS event feeds (ACM, Douglass NHS); MLB/Nationals schedule terms.
- **Evergreen postings:** the solidcore Lever postings (H St, Navy Yard) are 2023 talent pools. They are listed above, but treat them as optional.
