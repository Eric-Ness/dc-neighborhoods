# Sources for Georgetown, Dupont Circle, Cleveland Park and Chevy Chase DC

Tested 2026-10-31. Every fetch used the user agent `dc-neighborhoods-ingest/0.1 (+https://petworth.org)`. robots.txt was checked for agent `dc-neighborhoods-ingest` on the exact path (query string included). A "403 to our UA" means the server refused our agent, and it was not retried with any other agent. Item counts and hit counts are from the newest 20 items or fewer.

**robots matcher caveat (affects the engine).** `news.py` uses `urllib.robotparser`, which does not understand `*` or `$` wildcards. For example, georgetowndc.com has `Disallow: /*?`. The stdlib parser treats that as a literal prefix, so it would allow `/wp-json/tribe/events/v1/events?page=2`, but Google-style matching (which the site intends) disallows it. For this research I used a wildcard-aware matcher. For sites with wildcard rules (georgetowndc.com, cpcadc.org, phillipscollection.org, dupont-circle.org), the engine should use one as well, or call only the exact URLs listed below. (I sent one request to the BID API with `?page=2` before noticing the rule; don't use it.)

## 0. Geography findings that change the plan

All of these come from DC GIS point-in-polygon queries (Health Planning Neighborhoods layer 13, Historic Districts layer 6, ANC SMD layer 55, address points layer `Location_WebMercator/MapServer/0`). The area shares come from grid sampling.

- **HPN `GEORGETOWN` is only the western half of Georgetown.** It covers the GU campus, MedStar Georgetown, Burleith's edge and M St west of about 33rd. The eastern half is HPN **`GEORGETOWN EAST`**, which also includes Dupont, Sheridan-Kalorama and the West End. Tudor Place (1644 31st), Dumbarton Oaks, Rose Park, Washington Harbour (3000 K), 1529 Wisconsin, Book Hill and the Rose Park farmers market are all in GEORGETOWN EAST, not GEORGETOWN. The Georgetown Historic District splits 49% GEORGETOWN / 51% GEORGETOWN EAST.
  - **Recommendation:** use the Georgetown Historic District as the boundary, as for Dupont and Cleveland Park: `Historic_WebMercator/MapServer/6`, `NAME='Georgetown Historic District'`. It is 100% ANC 2E (2E07 25%, 2E05 20%, 2E02 13%, 2E06 13%, 2E03 12%, 2E04 7%, 2E01 5%, 2E08 5%).
  - The HPN as configured (`DC_HPN_NAME='GEORGETOWN'`) is 93% ANC 2E (2E05 40%, 2E02 18%, 2E03 12%, 2E04 10%, 2E01 7%, 2E08 6%) and 7% ANC 3D (3D06/3D07).
- **Dupont Circle Historic District** is 98% ANC 2B (2B05 23%, 2B02 22%, 2B01 17%, 2B03 13%, 2B07 12%, 2B04/06/08 the rest). It straddles four HPNs: GEORGETOWN EAST 30%, LOGAN CIRCLE/SHAW 26%, ADAMS MORGAN 26%, GWU 18%. The Adams Morgan site's southern strip therefore overlaps Dupont. The Phillips Collection (1600 21st), 1 Dupont Circle and 1775/1779 Mass Ave all fall inside the HD.
- **Cleveland Park Historic District** is 87% ANC 3C (3C05 53%, 3C08 22%, 3C06 7%, 3C04 4%) and 13% ANC 3A (3A03, the Wisconsin Ave side). By HPN it is 93% WOODLEY PARK. FRESHFARM Cleveland Park (3426 Conn, the Uptown block) and Tregaron / Washington International School (3100 Macomb) are inside it. The National Cathedral (3101 Wisconsin) is in its own HD and in 3C08, so it is outside.
- **HPN `CHEVY CHASE` stops at Connecticut Ave.** By area it is 3/4G03 43%, 3/4G05 35%, 3F06 10%, 3/4G07 6%, 3/4G06 3%, 3/4G04 3%.
  - Inside: the east side of Conn, including the Chevy Chase Community Center (5601 Conn), Chevy Chase Library (5625), 1 Chevy Chase Circle (Chevy Chase Presbyterian), 5333 Conn and Politics & Prose (5015 Conn, 3F06).
  - Outside: the west side of Conn. 5500 Conn (the Chevy Chase Main Street winter market) and 5612 Conn (Avalon Theatre) are in HPN **TENLEYTOWN**. Lafayette ES and the Chevy Chase farmers market (5701 Broad Branch) are in HPN **BARNABY WOODS**.
  - With the HPN boundary, the commercial strip's west side and the DC-side landmarks people call "Chevy Chase DC" belong to the Tenleytown site. Consider ANC 3/4G (all SMDs) as the boundary instead, the same way Friendship Heights uses SMDs.

## 1. GEORGETOWN

**ANCs:** 2E (whole HD). The HPN edge also touches 3D06/07.

### News

| Feed (exact URL) | robots | items | hits / last 20 (rule below) | Mode / notes |
|---|---|---|---|---|
| `https://georgetowner.com/feed/` | allow (Crawl-delay 10) | 10 | 6 (3 title) | **match**. The Georgetowner, daily; newest 29 Oct 2026. It also runs travel and DC-wide items ("The Italy Most Travelers Never Get To"), so match rather than take all. |
| `https://georgetownmetropolitan.com/feed/` | allow | 10 | 7 (all 10 contain "Georgetown" somewhere) | **all**. Hyperlocal (WordPress.com); newest 29 Oct ("The Weekly Metropolitan", "Surveyor Report Confirms Initial Findings", "La Bonne Vache Goes Up in Flames"). |
| `https://thehoya.com/section/news/city-news/feed/` | allow (Crawl-delay 6) | 10 | 5 | **match**. The Hoya's City News section; newest 24 Oct, oldest Apr 2026. Hits: "La Bonne Vache Devastated in Electrical Fire", "Pop Mart Opens New Georgetown Location", "Uniqlo Opens Georgetown Location". **Don't use the main `https://thehoya.com/feed/`**: under the same rule it let through 4/10 campus-only items ("GU to Join Leading Network of Research Universities"), and it carries sports. (`/category/news/city-news/feed/` 301-redirects here.) |
| `https://wtop.com/tag/georgetown/feed/` | allow | 10 | 10 (8 title) | **match**. Newest 13 Jul 2026, oldest Aug 2025, so slow. One item is about Rosslyn (Key Bridge Marriott); it matched because the body says "Georgetown". |
| `https://www.washingtonian.com/?s=georgetown&feed=rss2&orderby=date&order=DESC` | allow | 10 | 2 desc / 1 title | **match on title+summary** (not body). Newest 30 Oct. Kept "La Bonne Vache in Georgetown Devastated by Fire". |
| `https://www.washingtonblade.com/?s=georgetown&feed=rss2&orderby=date&order=DESC` | allow | 10 | 2 desc / 0 title | Low value: mostly body mentions (Georgetown alumni in obituaries). Optional, title-only. |
| `https://www.popville.com/feed/` (+ `?paged=2..5`) | allow | 20 each | 0 / 3 / 0 / 0 / 1 | Already in the engine. "Huge Smoke Plume Spotted in Georgetown" (28 Oct), "Beauty in Rose Park!" |
| `https://anc2e.com/feed/` (ANC 2E) | allow | 10 | 10 | **Stale: newest post 21 Apr 2025.** Agendas are no longer posted to the feed. Keep it in the feed list only so that a resumed feed gets picked up. |

**Not usable:** `georgetowndc.com/feed/` (BID; 200, 0 items); `georgetownheritage.org/feed/` 404; `cagtown.org/feed/` (Citizens Association of Georgetown) redirects to login; `anc2e.dc.gov` has no DNS.

**Keyword rule (Georgetown).** Match title + summary + tags.
- TERMS:
  ```
  \bgeorgetown\b(?!\s+(university|univ\b|law\b|prep\b|visitation|day school|medical|hoyas?\b|students?\b|faculty|professors?\b|alumn|school of|SFS\b|basketball|men\b|women\b))|\bburleith\b|\bdumbarton oaks\b|\btudor place\b|\bold stone house\b|\bcady'?s alley\b|\bwashington harbou?r\b|\bvolta park\b|\brose park\b|\bbook hill\b|\bmartin'?s tavern\b|\bexorcist steps\b|\bANC ?2E\b|\bold georgetown board\b
  ```
- NOT_HERE[0] (reject):
  ```
  \bgeorgetown,? (texas|tex\.|tx|ky\.?|kentucky|s\.?c\.?|south carolina|del\.?|delaware|ohio|ont\.?|ontario|ma|mass\.?|guyana|penang|indiana|ind\.)(?!\w)|\bguyana\b|\bhoyas\b|basketball|\bbig east\b|\bncaa\b|lacrosse|soccer|volleyball|\bcoach\b|\b(graduated|graduate|degree|attended|studied|alumn\w*|taught|professor)\b[^.]{0,40}\bgeorgetown\b
  ```
- NOT_HERE[1] (rescue, so university news that touches the neighborhood stays):
  ```
  \bburleith\b|\bANC ?2E\b|\bM st(reet)?\b|\bwisconsin ave|\bwaterfront\b|\bC&O\b|\bneighbors?\b|\bneighborhood\b|\bresidents?\b|\bGeorgetown BID\b|\bOld Georgetown Board\b|\bdumbarton\b|\btudor place\b|\bvolta park\b|\brose park\b|\bcampus plan\b
  ```
- Effect: "Georgetown University" by itself does not match, because the negative lookahead skips it. A plain "Georgetown" does. Sports and other-state uses are dropped unless a neighborhood cue rescues them.
- Example: WTOP's "Neighbors near Georgetown University may hear explosions" is kept (via "Neighbors…Georgetown"), and The Hoya's university-only items in the main feed are not used at all.

### Events

| Source | Endpoint | robots / terms | Result |
|---|---|---|---|
| **Georgetown BID** | `GET https://www.georgetowndc.com/wp-json/tribe/events/v1/events` (**exactly this URL, no query string**) | robots: path allowed, but `Disallow: /*?` blocks every query string, so `?page=`, `?per_page=` and `?start_date=` are out. `Crawl-delay: 3`. No terms page exists (`/terms-of-use` redirects to the home page). | **Yes, with limits.** 200 JSON, `total` 133 upcoming, but only the first 10 are reachable, and they start today (31 Oct: "Trick or Treat at Tudor Place", "Halloween Kids Club" at Pinstripes 1064 Wisconsin, "Halloween-Themed Cupcakes" at Georgetown Cupcake 3301 M St). Many are store promos, so filter out categories/titles like "promo", "% off", "kids eat free". Venue `geo_lat/geo_lng` is a fake DC centroid (38.9071923, −77.0368707) on many events; use `venue.address`. Run nightly and archive: each night adds the next ~10. `/events/feed/` returns 200 with 0 items. |
| **Tudor Place** (1644 31st St NW; in the HD) | `GET https://tudorplace.org/wp-json/tribe/events/v1/events` | allow; `Crawl-delay: 10`; no terms page found | **Yes.** 12 upcoming / 2 pages: "Tudor Tots: W is for Warmth" (4 Nov), "Weekend Weeders" and "Guided Garden Tour" (7 Nov), "Landmark Lecture…" at the Dower House (17 Nov), "Holiday Tea & Tour" (5 Dec). `?page=2` is allowed here. |
| The Georgetowner calendar | `GET https://georgetowner.com/wp-json/tribe/events/v1/events` | allow | 5 events, mixed DC (one at Community Forklift in MD, one at the Arts Club on I St). Keep only venues inside the HD (point-in-polygon on the venue address), e.g. "Thos. Moser & Moore Architects…", 1028 33rd St NW, 4 Nov. Optional. |
| ANC 2E | `anc2e.com` Tribe API (`/wp-json/tribe/events/v1/events`, also `?start_date=2026-01-01`): 200, **0 events**. `/events/?ical=1`: empty. `/events/feed/`: 0 items. Post feed stale since Apr 2025. | allow | **No machine-readable source.** ANC 2E meets the first Monday at 6:30 pm at Georgetown Visitation (1524 35th St NW). Agendas are PDFs. Use a static "how to attend" link, plus the OANC feed filtered on `ANC 2E`. |
| Dumbarton Oaks | `doaks.org` | **403 to our UA, including robots.txt** | Excluded. |
| Farmers market (existing layer) | — | — | **Rose Park Farmers Market**, 26th & O St NW, Wednesdays: inside the Georgetown HD (GEORGETOWN EAST HPN). FRESHFARM Foggy Bottom (Wed) is nearby. |
| Not usable | Georgetown Heritage, Old Stone House (NPS), Dumbarton House: no Tribe API / feed (404). | | |

### Jobs

| Employer | Endpoint | Filter | robots / terms | Verdict |
|---|---|---|---|---|
| **Georgetown University (Workday)** | `POST https://georgetown.wd1.myworkdayjobs.com/wday/cxs/georgetown/Georgetown_Admin_Careers/jobs`, body `{"appliedFacets":{"locations":[…ids]},"limit":20,"offset":0,"searchText":""}`; detail `GET …/Georgetown_Admin_Careers<externalPath>` for `startDate` and `externalUrl` | **Location facet allowlist by descriptor** (look the IDs up nightly): `Main Campus` (48), `Medical Center` (21; GUMC at Reservoir Rd, inside the HPN), `Lauinger Library 3rd Floor`, `ICC 2nd Floor`, `Car Barn` (3520 Prospect, in the HD), `Pasquerilla Healthcare Center 1st Floor`, `Pre-Clinical Science Lower Level`, `St. Mary's 4th Floor`, `SWQ Parking Garage …`. **81 of 113 jobs today.** **Exclude** `Law Center`, `Downtown Campus`, `125 E St NW`, `1000 New Jersey Ave`, `Qatar`, `Dubai`, `Washington DC`, `District of Columbia`, and **`2115/2121 Wisconsin Ave`** (address points put 2115 Wisconsin in ANC 3B02, HPN WOODLEY PARK, outside both Georgetown boundaries). | robots: `Allow: /Georgetown_Admin_Careers/`, `Disallow: /refreshFacet/`; `/wday/cxs/` is unmatched, so allowed (same as AU). No terms page on georgetown.edu (`/terms-of-use/` 404). Same undocumented-Workday-API caveat as AU. | **Use.** Samples: "Director of Facilities Services", Main Campus, 2026-10-30; "Access Services Specialist", Lauinger Library, 2026-10-30; "Specimen Collector and Data Submission Specialist – Part-time", Medical Center, 2026-10-30; "Supervisor of Lock Shop and Access Control", Main Campus, 2026-10-29. Other sites: `Georgetown_Hoya_Staffing` (1 job), `Georgetown_Faculty` (0 jobs). |
| MedStar Georgetown University Hospital | careers.medstarhealth.org | **403 to our UA, including robots.txt** | Excluded. |
| Dumbarton Oaks (Harvard) | Harvard posts on SmartRecruiters; `api.smartrecruiters.com` robots `User-agent: * / Disallow: /` | Excluded. careers.harvard.edu disallows `/jobs?*`. |
| Four Seasons Georgetown | `boards-api.greenhouse.io/v1/boards/fourseasons` has 1 job (Roselle, IL); fourseasons.com robots 403 | Nothing local. |
| Others probed (no board): tudorplace, georgetownbid, eastbanc, jamestowngeorgetown, georgetowncupcake, rosewood, georgetownprep, visi | Greenhouse, Lever, Ashby | — | — |

## 2. DUPONT CIRCLE

**ANCs:** 2B (98% of the HD). It touches 2A, 2C, 2D and 1C01 at the edges.

### News

| Feed (exact URL) | robots | items | hits / last 20 | Mode / notes |
|---|---|---|---|---|
| `https://www.dupontcircleanc.net/wordpress/feed/` (ANC 2B) | allow | 5 | 5 (via `ANC ?2B`) | **all**. Already in the engine for Adams Morgan. Agenda posts: "ANC 2B October 21st, 2026 Final Agenda". |
| `https://wtop.com/tag/dupont-circle/feed/` | allow | 10 | 10 (6 title) | **match**. Newest 19 Jun 2026 ("Dupont Circle closed during Capital Pride…"); oldest Oct 2025. |
| `https://www.washingtonian.com/?s=dupont+circle&feed=rss2&orderby=date&order=DESC` | allow | 10 | 2 desc / 1 title | **match**. Newest 29 Oct: "Cool Listing: A Color-Drenched Townhouse in Dupont Circle". Also kept: "4 Open Houses…", which has a Dupont listing. |
| `https://www.washingtonblade.com/?s=dupont+circle&feed=rss2&orderby=date&order=DESC` | allow | 10 | 5 desc / 0 title | **match**. The Blade covers Dupont as the historic gayborhood: "Thousands turn out for annual 17th Street High Heel Race" (29 Oct), "Kramers celebrates 50 years…" (15 Oct), "The gayborhood is changing. Are we?" (26 Oct), "Immersive 'Nation-State'…" (Dupont Underground). |
| `https://www.popville.com/feed/` (pages 1–5) | allow | 100 | 1 | "17th Street High Heel Race is Tonight!" (27 Oct). |

**Not usable:**
- **Dupont Circle BID** `dupontcirclebid.org`: **403 to our UA, including robots.txt.**
- Dupont Circle Main Streets (`dupontcirclemainstreets.org`, Wix): no `/feed/` and no `/blog-feed.xml` (404); `/events` is a Wix page.
- Dupont Circle Citizens Association (`dupont-circle.org`, Wild Apricot): no feed links on the home page, and robots disallows `/Sys/Api/*`.
- InTowner, as noted before, is dead. `dupontcurrent.com` and `dupontcirclecitizens.org` have no DNS. `dupontcircle.net/feed/` returns HTML. `dccitizens.org` has a TLS hostname error.

**Keyword rule (Dupont).**
- TERMS:
  ```
  \bdupont circle\b|\bdupont (underground|metro|farmers'? market|festival)\b|\bANC ?2B\b|\bphillips collection\b|\bkramers\b|\bhigh heel race\b|\bin dupont\b|\bdupont'?s\b
  ```
- NOT_HERE[0] (reject; **case-sensitive**, no `re.I`, so the company's "DuPont" spelling is caught):
  ```
  \bdu ?pont (de nemours|company|co\.|chemical|corp|family|state|stadium|highway)\b|\bDuPont\b(?! Circle)|\bwilmington\b|\bdelaware\b|\bpfas\b
  ```
- NOT_HERE[1] (rescue): `\bdupont circle\b|\bANC ?2B\b|\bphillips collection\b`
- Bare "Dupont" is never a term by itself; only "in Dupont" or "Dupont's" match, and only when no company cue is present.
- "17th Street" alone is not a term: 17th St runs from Dupont down to the White House.

### Events

| Source | Endpoint | Result |
|---|---|---|
| ANC 2B agendas | `https://www.dupontcircleanc.net/wordpress/feed/` | **Yes.** Parse the meeting date from the title: "ANC 2B October 21st, 2026 Final Agenda" → 2026-10-21. The title format varies ("October 14th Permitting and Licensing Committee", which has no year: take the year from `pubDate`). 2B meets on the second or third Wednesday. Tribe API: 404. |
| FRESHFARM Dupont Circle | existing layer (MapServer/2) | **Inside the HD**: 1600 20th St NW, Sundays. Also within 0.5 mi: Rose Park (Wed), Adams Morgan (Sat), FRESHFARM Foggy Bottom (Wed). |
| Phillips Collection | `https://www.phillipscollection.org/rss.xml` (allow) | **Not events.** It is the archive's "on this day" hanging records ("Dining Room, December 15, 1942…"). No Tribe API (404) and no events feed. Exclude. |
| Dupont Circle BID / Main Streets / DCCA | — | 403 / Wix with no feed / Wild Apricot with no public feed. No machine-readable events. |
| Dupont Underground | `/feed/`, Tribe API: 404 | None. |

### Jobs

No qualifying machine-readable employer feed was found inside the Dupont HD.
- **Phillips Collection**: ADP Workforce Now (`workforcenow.adp.com/…/recruitment.html?cid=f8ae008f-…`). Excluded, as noted before: ADP is not an allowed platform, and its robots redirects to login.
- **Brookings / Carnegie** (1775/1779 Mass Ave, both inside the HD): Brookings uses iCIMS (not allowed). The Lever slug `brookings` is an unrelated San Francisco company. Carnegie: no Greenhouse/Lever/Ashby board.
- **sweetgreen** (Greenhouse): 67 jobs; the only DC jobs are 601 Mass Ave NW and an unspecified "Washington, DC".
- Hotels (Dupont Circle Hotel/Doyle, Hilton): no board / `Disallow: /api/*`.
- Slugs probed with no board: phillipscollection, ceip, carnegieendowment, piie, kramers, dupontcirclebid, doylecollection, aspeninstitute, newamerica, thirdway, cgdev, fhi360, nationaltrust, cosmosclub.

## 3. CLEVELAND PARK

**ANCs:** 3C (87%) and 3A03 (13%, Wisconsin side).

### News

| Feed (exact URL) | robots | items | hits / last 20 | Mode / notes |
|---|---|---|---|---|
| `https://www.cpcadc.org/feed/` (Cleveland Park Citizens Association) | allow | 10 | 10 | **all**. Slow: newest 8 Oct 2026 ("CPCA Community Group Fair"), then May 2026, Nov 2025. Note robots blocks `/calendar-2/action~*/` and `*controller=ai1ec_exporter_controller*` (its iCal export), so **do not use the CPCA calendar export**. |
| `https://anc3c.dc.gov/rss.xml` (ANC 3C, Drupal) | allow | 10 | 10 | **all** (it is an event feed; see Events). |
| `https://districtbridges.org/feed/` (runs **Cleveland Park Main Street** and **Chevy Chase Main Street**; `clevelandparkmainstreet.org` redirects to `districtbridges.org/main-street/cleveland-park/`) | allow | 10 | 2 | **match**. "Meet Haru Wok & Roll: Cleveland Park's Newest Restaurant" (16 Sep). |
| `https://wtop.com/tag/cleveland-park/feed/` | allow | 10 | 10 (5 title) | **match**. **Stale-ish**: newest 12 Dec 2025, oldest Mar 2023. Some items are National Zoo stories tagged Cleveland Park (the Zoo is next door, in Woodley Park). |
| `https://foresthillsconnection.com/?s=cleveland+park&feed=rss2&orderby=date&order=DESC` | allow | 10 | 2 strict (all 10 mention CP in the body) | **search** mode with the body is too loose here: the hits are ANC 3F candidate profiles. Use **match** on title+summary: "Pedestrian safety updates: New walk signal at Conn. and Chesapeake…" (Mar 2026). The FHC main feed (already used) had 0. |
| `https://www.washingtonian.com/?s=cleveland+park&feed=rss2&orderby=date&order=DESC` | allow | 10 | 1 | Newest 29 Oct; the one hit is a luxury home-sales roundup. Low value; optional. |
| `https://www.popville.com/feed/` (pages 1–5) | allow | 100 | 2 | "Cleveland Park Smoke Shop Raided…" (28 Oct). |

**Not usable:** Cleveland Park Historical Society (`clevelandparkhistoricalsociety.org/feed/` 404, robots 404); `www.clevelandparkmainstreet.org` (TLS EOF on https; http redirects to District Bridges). The Cleveland Park Listserv is private, so it is excluded by design.

**Keyword rule (Cleveland Park).**
- TERMS:
  ```
  \bcleveland park\b|\buptown theat(er|re)\b|\btregaron\b|\brosedale conservancy\b|\bANC ?3C\b|\bcleveland and woodley park\b|\bmacomb st(reet)?\b
  ```
- NOT_HERE[0]: `\bgreenville\b|\bS\.C\.|\bsouth carolina\b|\bdallas\b|\bspartanburg\b`. Greenville, SC has a large "Cleveland Park" with a zoo, which is the realistic collision.
- NOT_HERE[1] (rescue): `\bconnecticut ave|\bN\.?W\.?\b|\bD\.?C\.?\b(?![-\s]area)|\bANC ?3C\b|\bwoodley\b|\bzoo\b`
- Nothing in today's feeds tripped the reject list.
- "Uptown Theater" is ambiguous elsewhere (Chicago, Kansas City) but rare in DC outlets. Keep it, since the rescue requires a DC cue when a reject cue is present.

### Events

| Source | Endpoint | Result |
|---|---|---|
| **District Bridges events (Cleveland Park Main Street + Chevy Chase Main Street)** | `GET https://districtbridges.org/events/feed/` (Modern Events Calendar RSS; robots allow; no terms page, `/terms-of-use/` 404) | **Yes; best CP/CC source.** 10 upcoming items with `mec:startDate`, `mec:startHour`, `mec:endDate`, `mec:endHour` and `mec:location`. Ignore `pubDate`: it carries the event start, not the post date. Filter by title/location. Today: "Cleveland Park Santa Bar Crawl" (2026-12-05 6 pm, Cleveland Park commercial corridor), "Cleveland Park Winter Fest" (2026-12-12 noon, 3400 block Connecticut Ave NW), "Cleveland Park Night Market" (2027-04-23, 05-27, 06-24, 07-22). It also lists Columbia Heights events (drop those). `?mec-ical-feed=1` returned HTML; the Tribe API 404s; `/wp-json/wp/v2/mec-events` lists posts but without event dates. |
| **ANC 3C** | `GET https://anc3c.dc.gov/rss.xml` (allow) | **Yes, but the date is in the description**, after the Drupal post time: e.g. "…Tue, 06/30/2026 - 10:53 Agenda Forthcoming … Nov 24 2026". Parse the first `\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2} \d{4}\b` that comes *after* the `MM/DD/YYYY - HH:MM` post stamp. Today: committee meetings (Public Safety 12 Nov, Community Engagement & Grants 24 Nov), "Cleveland and Woodley Park Main Street Holiday Market" (Dec 12 2026). The full-commission meeting (third Monday; next 16 Nov per 2026 minutes) was not in the newest 10. |
| **Tregaron Conservancy** (in the HD) | `GET https://tregaron.org/wp-json/tribe/events/v1/events` (allow; robots blocks only `/cgi-bin/`, `/dev/`, `/photo-galleries/`) | **Yes, small.** 1 event: "Meet the Birds of Tregaron with Sam Krause", 2026-11-01 9:00 (no venue; it's at Tregaron). |
| FRESHFARM Cleveland Park | existing layer | **Inside the HD**: 3426 Connecticut Ave NW, Saturdays. Nearby: Maret School market (0.14 mi, Sat), UDC Van Ness (Sat), New Morning Farm at Sheridan School (Sat/Tue). |
| CPCA posts | `https://www.cpcadc.org/feed/` | Event announcements as posts ("CPCA Community Group Fair"), with no structured date. Use as news only. |
| Hillwood (4155 Linnean Ave; Forest Hills, not in the HD) | `hillwoodmuseum.org/wp-json/tribe/events/v1/events` | **403 to our UA** (robots allowed). Not retried; excluded. |
| Washington National Cathedral | outside the HD (own HD, 3C08) | Not pursued. |

### Jobs

No qualifying feed.
- **Washington International School** (Tregaron campus, 3100 Macomb, inside the HD) posts on **AppliTrack/Frontline** (`applitrack.com/wis/onlineapp/`). That is not an allowed platform; exclude.
- National Cathedral: Paylocity (as noted before).
- National Zoo/Smithsonian: USAJOBS is blocked (as noted before).
- Sidwell: no listings (as noted before).
- District Bridges: WooCommerce site, no job board.
- Slugs probed with no board: wis, washingtoninternationalschool, maret, sidwell.

## 4. CHEVY CHASE DC

**ANCs:** 3/4G (about 89% of the HPN) and 3F06 (10%, the 50xx Conn strip around Politics & Prose).

### News

| Feed (exact URL) | robots | items | hits / last 20 (strict rule) | Mode / notes |
|---|---|---|---|---|
| `https://anc3g.dc.gov/rss.xml` (ANC 3/4G) | allow | 10 | 10 | **all**. Already used for Friendship Heights. Civic Core hearings, "Chevy Chase Circle Safety Meeting", "DCPL+DPR Townhall-Designing New Facilities". |
| `https://www.historicchevychasedc.org/feed/` (Historic Chevy Chase DC) | allow | 10 | 10 | **all**. DC-only organization. Newest 3 Oct 2026 ("When Does 'Zoning' Mean Exclusion?"), then Feb 2026. Slow; about half the items are obituaries. Its Tribe API returns 200 with 0 events. |
| `https://districtbridges.org/feed/` (Chevy Chase Main Street) | allow | 10 | 0 strict | **match**; occasional. |
| `https://wtop.com/tag/chevy-chase/feed/` | allow | 10 | 1 strict (2 loose) | **match + strict rule**. The tag is mostly Maryland: 8/10 items were correctly rejected (Montgomery County fires, crashes, The Heights food hall in MD). Kept: "Repurposed phone booth hidden in a DC neighborhood…" (tags include "northwest dc"). `/tag/chevy-chase-dc/feed/` returns 200 with 0 items. |
| `https://www.washingtonian.com/?s=chevy+chase&feed=rss2&orderby=date&order=DESC` | allow | 10 | 1 strict | **match + strict**. "A Popular Chevy Chase Thai Restaurant Is Adding a Luxe Sushi Menu" (17 Sep). The summary says "MiShi. 5507 Connecticut Ave., NW", so it is kept by the 5xxx-Conn-NW cue. |
| `https://foresthillsconnection.com/?s=chevy+chase&feed=rss2&orderby=date&order=DESC` | allow | 10 | 0 strict / 2 loose | **match + strict**. Items mention Chevy Chase only in tags or bylines (e.g. a junk-removal sponsor "of Chevy Chase"). Low value. |
| `https://www.popville.com/feed/` (pages 1–5) | allow | 100 | 1 strict (via "Politics and Prose") | "Hello Buck's Wine Bar" (tagged "Chevy Chase") is lost under the strict rule. PoPville is DC-only, so a bare "Chevy Chase" there means DC. If you want such items, apply a loose rule to PoPville only. |
| `https://www.washingtonblade.com/?s=chevy+chase&feed=rss2&orderby=date&order=DESC` | allow | 10 | 1 strict (Jan 2025; "Chevy Chase Presbyterian" in tags) | Mostly MD and incidental mentions; the newest is 22 Oct. Skip. |

**Not usable:**
- **Chevy Chase Citizens Association** `chevychasedc.org`: https fails at the TLS handshake; **http returns 403 to our UA (including robots.txt)**.
- `chevychasecitizens.org`: TLS hostname mismatch. `chevychasemainstreet.org`: TLS EOF. `chevychasedcmainstreet.org`: no DNS. (Chevy Chase Main Street lives on districtbridges.org.)
- GGWash `/rss` had 0 strict hits today; keep it as a general feed.

**Keyword rule (Chevy Chase DC): strict.** Accept only on a DC-specific cue, never on a bare "Chevy Chase".
- TERMS:
  ```
  chevy chase,? (D\.? ?C\.?|DC)\b|\bchevy chase DC\b|\bANC ?3/?4 ?G\b|\bANC 3G\b|\bcivic ?core\b|\bbroad branch market\b|\b5[0-9]{3} connecticut ave(nue)?\.?,? (nw|n\.w\.)|\bnorthwest (DC|D\.C\.|washington)\b|\bchevy chase (community center|neighborhood library|recreation center|presbyterian)\b|\blafayette (elementary|es)\b|\bavalon theat(re|er)\b|\bpolitics (and|&) prose\b
  ```
- NOT_HERE[0] (reject even if a cue matched, unless NOT_HERE[1] also matches):
  ```
  \bmaryland\b|\bMd\.?\b|montgomery county|\bMoCo\b|\bbethesda\b|chevy chase (village|lake|section|view|heights|club)|town of chevy chase|\bMCPS\b|\bkensington\b|\bsilver spring\b|\bpurple line\b|\bfriendship heights village\b|\bcolumbia country club\b
  ```
- NOT_HERE[1] (rescue): the same as TERMS minus `northwest washington`.
- Notes:
  - "Chevy Chase Library" alone is ambiguous: Montgomery County also has a Chevy Chase Library, at 8005 Connecticut Ave. Require "Chevy Chase Neighborhood Library", or rely on the ANC/HCCDC feeds.
  - "Chevy Chase Circle" straddles the line, so it is accepted only together with a DC cue.
  - Politics & Prose's flagship (5015 Conn) is in the CHEVY CHASE HPN (3F06), but the store also has Wharf and Union Market locations. Treat it as a boost, or require "Connecticut".
  - Tested today:
    - Kept: all 10 ANC 3/4G items, all HCCDC items, the WTOP phone-booth story, and MiShi (after fixing the `Ave.,` punctuation).
    - Rejected: all 8 Montgomery County WTOP items and every MD item in the Blade.

### Events

| Source | Endpoint | Result |
|---|---|---|
| **ANC 3/4G** | `https://anc3g.dc.gov/rss.xml` | **Yes, but parse the date from the title**, as documented for FH ("2026-11-12 Hearing on Chevy Chase Civic Core…", "October 17, 2026, Special Meeting…"). Skip items whose title has no date. |
| **Chevy Chase Main Street (District Bridges)** | `https://districtbridges.org/events/feed/` | **Yes.** "Trivia Night at Chevy Chase Lounge" (2026-11-19 and 12-17, 7 pm; `mec:location` "Parthenon and Chevy Chase Lounge", no street address) and "Chevy Chase Winter Market" (2026-12-05 noon–5 pm, `mec:location` "5500 Connecticut Avenue Northwest"). **5500 Conn is west of Connecticut, in HPN TENLEYTOWN**, so with the HPN boundary it is "nearby", not "in". Accept by title keyword ("Chevy Chase") from this feed rather than by geocoding. |
| Chevy Chase Farmers Market | existing layer | 5701 Broad Branch Rd NW (Lafayette ES), Saturdays: **just outside the HPN** (BARNABY WOODS HPN, SMD 3/4G04). Also New Morning Farm – Chevy Chase, Taylor St & Brookville Rd (Sat), 0.6 mi. |
| Historic Chevy Chase DC | Tribe API 200, 0 events | Webinars appear as posts only. |
| CCCA | 403 | Excluded. |
| DPR Chevy Chase Community Center / DCPL Chevy Chase Library | as noted before: DPR feed stale, DCPL blocks bots | Static links only (the existing `dclibrary.libnet.info` link). |

### Jobs

No qualifying feed.
- **Politics & Prose** (5015 Conn): `politics-prose.com/jobs` and `/employment` **return 403 to our UA**; it is not on Greenhouse, Lever or Ashby.
- **Children's National "CNPA Chevy Chase"** is 4601 North Park Ave, **Maryland**: exclude (as found before).
- Avalon Theatre, Broad Branch Market, Lafayette ES (DCPS): no machine-readable boards.
- Slugs probed with no board: politicsandprose, politicsprose, avalontheatre, broadbranchmarket.

## 5. HISTORY (Evening Star via loc.gov, week of 1926-10-31 to 11-06)

loc.gov answered normally (robots allow; no 403), though slowly (about 30–60 s per query, with retries). Query shape is the same as `history.py`: `q`, `dates`, `fa=partof_title:evening star (washington, d.c.) 1854-1972`, `fo=json`. "Week" is the number of pages hit in 1926-10-31 → 11-06; "Oct–Nov" covers 1926-10-01 → 11-30 (Georgetown and Dupont terms only; I stopped running the second count for the rest to save time). I then read OCR snippets for 8 pages for each main term.

**Phrase search ignores punctuation:** `"Chevy Chase, D. C."` returned exactly the same 82 pages as `"Chevy Chase"`. Do the DC/MD split in the regex, not in the query.

### Georgetown

| Term | Week | Oct–Nov | What the snippets show |
|---|---|---|---|
| `Georgetown` | 74 | 662 | **Mostly Georgetown University football** in Nov 1926 (vs. Lebanon Valley, Syracuse, West Virginia, Navy) and its R.O.T.C. There are real neighborhood items too: "GEORGETOWN AIMS AT RETAINING RELIC… Georgetown Citizens' Association… Canal" (31 Oct); "Christmas tree… Montrose Park… Georgetown Garden Club" (3 Nov). It needs the sports filter. |
| `"Georgetown University"` | 8 | 76 | R.O.T.C., the Hilltop. Fine as GU news, but most of it is campus-only. |
| `"Burleith"` | 17 | 122 | New-home ads ("2034 37th Street N.W. (In the Burleith Section)", "Cooley Bros. … seven new homes at Burleith"). **Pitfall:** "TAKE A BURLEITH BUS TO DOOR" appears in apartment ads for other parts of town (Capitol Hill, 2807 Conn). Reject `burleith\s+bus`. |
| `"Dumbarton"` | 17 | 149 | All Georgetown: Dumbarton Avenue M.E. Church, "3025 Dumbarton ave.", "Wisconsin and Dumbarton Avenues" (the Georgetown Gas Light Co.), and the **Dumbarton theater** (1343 Wisconsin) in movie listings. |
| `"Georgetown Citizens"` | 3 | 15 | Unambiguous and civic. |
| `"Montrose Park"` | 2 | 27 | Unambiguous (Georgetown park). |
| `"Oak Hill Cemetery"` | 3 | 10 | Georgetown (R St). Mostly funeral notices; the existing LEGAL/SCREEN filters may drop them. |
| `"West Washington"` | 3 | 40 | The old name for Georgetown, but too generic; skip. |
| `"Wisconsin avenue"` / `"M street northwest"` | 18 / 44 | 174 / 355 | Both run well outside Georgetown. Use them as `local` boosters only. |
| `"Rose Park"`, `"Tudor Place"`, `"Volta place"`, `"Prospect street"` | 0 | 4 / 1 / 3 / 1 | Too rare. |

**Recommended Georgetown config:**
- `terms` (most reliable first): `'"Georgetown Citizens"'`, `'"Montrose Park"'`, `'"Dumbarton"'`, `'"Burleith"'`, `"Georgetown"`
- `pattern`:
  ```
  georgetown|burleith|dumbarton\s+(av|oaks|theat|st)|montrose\s+park|oak\s+hill\s+cemetery
  ```
- Clip reject (sports, other places, the bus line):
  ```
  foot\s*ball|eleven|touchdown|gridiron|varsity|quarterback|coach|kick|halfback|syracuse|navy|lebanon|r\.\s?o\.\s?t\.\s?c|basket\s*ball|track\s+meet|georgetown,?\s+(del|s\.\s?c|ky|tex|md)\b|burleith\s+bus
  ```
- `local`:
  ```
  wisconsin\s+av|m\s+st|n\s+st|o\s+st|p\s+st|q\s+st|prospect|dumbarton|potomac|canal|key\s+bridge|aqueduct\s+bridge|35th|36th|37th|31st|30th|29th|28th|citizens.\s+association|montrose|holy\s+trinity
  ```
- Dumbarton theater movie listings rank low on legibility anyway.
- Expect about 5–10 usable clips per week after the sports filter.

### Dupont Circle

| Term | Week | Oct–Nov | Snippets |
|---|---|---|---|
| `"Dupont Circle"` | 37 | 337 | **Unambiguous, and DC in every sample.** Nearly all classifieds: "NEAR DUPONT CIRCLE. 1741 P ST. N.W. 11 ROOMS, 4 BATHS", "1740 Corcoran St., near Dupont Circle", "2130 O st. n.w.". There is no DuPont-company risk with the phrase "Dupont Circle". |
| `"Phillips Memorial Gallery"` | 1 | 2 | The Phillips (opened 1921). Rare but excellent. |
| `"Riggs place"` | 1 | 16 | Small street inside the HD. |
| `"Corcoran street"` | 2 | 26 | Inside the HD (17xx–18xx Corcoran). |
| `"Hillyer place"`, `"Swann street"` | 0 / 0 | 2 / 0 | Too rare. |
| `"Massachusetts avenue"` | 12 | 160 | Too broad (it runs citywide); booster only. |

**Recommended Dupont config:**
- `terms`: `'"Dupont Circle"'`, `'"Phillips Memorial Gallery"'`, `'"Riggs place"'`, `'"Corcoran street"'`
- `pattern`:
  ```
  dupont\s+circle|phillips\s+memorial\s+gallery|riggs\s+place|1[5-9]\d\d\s+corcoran\s+st
  ```
- Clip reject: `du\s?pont\s+(company|powder|de\s+nemours)|wilmington|delaware`. Only needed if a broader `Dupont` term is ever added; the phrase itself was clean.
- `local`:
  ```
  p\s+st|q\s+st|r\s+st|s\s+st|n\s+st|o\s+st|corcoran|riggs|hillyer|church\s+st|new\s+hampshire\s+av|massachusetts\s+av|connecticut\s+av|17th|18th|19th|20th|21st|22d|22nd|sheridan\s+circle
  ```
- Expect classifieds to dominate. The existing LEGAL/SCREEN filters will drop many of them, so the 37 page hits shrink to a handful of narrative clips.

### Cleveland Park

| Term | Week | Snippets |
|---|---|---|
| `"Cleveland Park"` | 38 | **DC in every sample.** Real estate ("RODMAN ST., CLEVELAND PARK. Just a few doors off Connecticut ave.", "3512 30th ST. N.W. … one block west of Conn. ave. car line") and society/civic items ("The Cleveland Park Chapter announces a bazaar… 3300 Newark street"). **Pitfalls:** "NORTH CLEVELAND PARK … 38th and Veazey Streets" is today's Wakefield/Van Ness, outside the HD, so reject `north\s+cleveland\s+park`. Some ads say "west of Wisconsin ave", which is outside the HD, but the paper still calls it Cleveland Park; accept those. |
| `"Woodley road"` | 5 | The southern edge of the HD (and Woodley Park); booster or secondary term. |
| `"Macomb street"` | 2 | Inside the HD. |
| `"Newark street"` | 1 | Inside the HD (3300 Newark, as above). |
| `"Ordway street"` | 1 | Inside the HD. |
| `"Highland place"` | 0 | Too rare. |

**Recommended Cleveland Park config:**
- `terms`: `'"Cleveland Park"'`, `'"Macomb street"'`, `'"Newark street"'`, `'"Ordway street"'`, `'"Woodley road"'`
- `pattern`:
  ```
  (?<!north\s)cleveland\s+park|\d{4}\s+(macomb|newark|ordway|porter|rodman|lowell)\s+st|highland\s+place
  ```
- Clip reject: `north\s+cleveland\s+park|cleveland,?\s+o(hio)?\b|greenville`. (1926 wire copy about Cleveland, Ohio parks can say "Cleveland park board".)
- `local`:
  ```
  connecticut\s+av|wisconsin\s+av|macomb|newark|ordway|highland|porter|quebec|rodman|woodley|klingle|idaho\s+av|34th|35th|30th|29th|reno\s+road|rosedale|twin\s+oaks
  ```
- Expect about 5–10 usable clips per week.

### Chevy Chase DC

| Term | Week | Snippets |
|---|---|---|
| `"Chevy Chase"` (= `"Chevy Chase, D. C."`) | 82 | **Mixed DC and MD**. MD: "47 and 49 LENOX ST., CHEVY CHASE, MD.", "CHEVY CHASE. MD., BROOKEVILLE RD. and Shepherd st.", "Community Club of Chevy Chase … Brookeville road", "IN CHEVY CHASE—WASHINGTON'S MOST EXCLUSIVE SUBURB" (unclear). DC: "In Chevy Chase, D. C. Just off Connecticut ave.", "CHEVY CHASE 5832 30th St. N.W.", "3922 Livingston st.", "Chevy Chase Grove, on Quesada st. … square 2001". As noted last time, real-estate ads near Connecticut Ave are genuinely Chevy Chase DC, which is fine. |
| `"Chevy Chase Circle"` | 7 | The line itself; needs a DC cue. |
| `"Northampton street"` | 2 | DC street (Chevy Chase DC). |
| `"Livingston street"`, `"Connecticut avenue extended"` | 0 / 0 | None this week (Livingston did appear inside a "Chevy Chase" hit). |

**Recommended Chevy Chase DC config:**
- `terms`: `'"Chevy Chase"'`, `'"Chevy Chase Circle"'`, `'"Northampton street"'`
- `pattern` (accept a clip only if it matches this AND does not match the reject below, unless it also has a DC cue):
  ```
  chevy\s+chase|northampton\s+st|livingston\s+st|mckinley\s+st|morrison\s+st|patterson\s+st|chevy\s+chase\s+circle
  ```
- Clip reject (MD):
  ```
  chevy\s+chase,?\s+m\s?d\b|\bmd\.|maryland|montgomery\s+county|brookeville|lenox\s+st|chevy\s+chase\s+(village|section|lake|club)|kensington|bethesda|somerset|martin'?s\s+additions?|rollingwood|shepherd\s+st|grafton\s+st|bradley\s+lane
  ```
- DC cue (rescue):
  ```
  chevy\s+chase,?\s+d\.?\s?c|n\.\s?w\.|northwest|connecticut\s+av|30th\s+st|3[0-9]{3}\s+(livingston|morrison|northampton|oliver|patterson|military|mckinley|jenifer|kanawha|quesada|rittenhouse)|broad\s+branch|military\s+road|chevy\s+chase\s+grove|square\s+\d{4}
  ```
- `local`: the same as the DC cue, plus `utah\s+av|nebraska\s+av|reno\s+road|rock\s+creek`.
- Expect 10–20 DC clips in a week like this one, mostly real estate.

## Not verified / excluded (summary)

- **403 to our UA, not retried:** dupontcirclebid.org, doaks.org, careers.medstarhealth.org, hillwoodmuseum.org (Tribe API), politics-prose.com (jobs pages), chevychasedc.org (http), fourseasons.com (robots).
- **Robots-disallowed:** api.smartrecruiters.com (Harvard / Dumbarton Oaks jobs); georgetowndc.com with any query string; CPCA's ai1ec iCal export.
- **Not allowed platforms:** iCIMS (Brookings), ADP (Phillips), AppliTrack (WIS).
- **Stale or empty:** ANC 2E (anc2e.com feed: last post Apr 2025; calendar empty); Phillips `rss.xml` (archive records, not events); WTOP Cleveland Park tag (newest Dec 2025).
