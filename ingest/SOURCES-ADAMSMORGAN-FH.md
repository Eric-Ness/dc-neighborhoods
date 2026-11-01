# Sources for Adams Morgan and Friendship Heights (DC)

Tested 2026-10-31 / 11-01. Every fetch used the user agent `dc-neighborhoods-ingest/0.1 (+https://petworth.org)`, and robots.txt was checked with `urllib.robotparser` for agent `dc-neighborhoods-ingest` on the exact path. A "403 to our UA" means the server refused our agent outright, robots.txt included. No other agent was tried.

## 0. Geography findings that change the plan

- **Adams Morgan HPN (`DC_HPN_NAME='ADAMS MORGAN'`)**: by grid-sampled area it is about 75% ANC 1C, 22% ANC 2B (Dupont, the southern strip) and 3% ANC 1B. ANC 1A, 1D, 2D and 3C only touch its edges. The neighborhood-name points "Adams Morgan" and "Lanier Heights" both fall in ANC 1C. All of these landmarks checked out inside the HPN: 1747 Columbia Rd (Safeway), 2333 Ontario Rd (Mary's Center), 1707 Kalorama Rd, 1919 Connecticut Ave (Washington Hilton), 2022 Columbia Rd, 2100–2300 18th St, 2400 16th St (west side of 16th).
  - **Zip 20009 is not a usable filter.** It also covers Dupont, Logan and U St. For example, Safeway at 1701 Corcoran St (20009) is in LOGAN CIRCLE/SHAW. Filter jobs and events by point-in-polygon instead.
- **Friendship Heights DC has no HPN.** Every FH-DC landmark checked out inside the **TENLEYTOWN** HPN, which is already live, and in ANC 3E SMD 3E04: 5335 Wisconsin (Chevy Chase Pavilion), 5300 Wisconsin (Mazza Gallerie), 5225 Wisconsin, 5255 Western Ave (former Lord & Taylor), 4400 Jenifer St, 4300 Military Rd (Embassy Suites). The DC "Neighborhood Names" point for Friendship Heights also lies in ANC 3E. ANC 3/4G covers Chevy Chase DC to the east (3700 Jenifer St is in 3/4G and the CHEVY CHASE HPN). The FH site therefore overlaps Tenleytown unless you draw a custom boundary. A likely boundary is ANC 3E SMD 3E04, optionally plus 3E03 and the western edge of 3/4G.

## 1. NEWS

### Keyword rules (tested against the feeds below)

**Adams Morgan** (match title + description, case-insensitive):
```
\badams[\s-]?morgan\b|\bkalorama\s+(park|triangle)\b|\blanier\s+heights\b|\bmarie\s+reed\b|\bwalter\s+pierce\s+park\b|\bjumbo\s+slice\b
```
plus case-sensitive `\bAdMo\b`.
- Do **not** match on "Kalorama" alone. 2221 Kalorama Rd, for example, is in ANC 2D / Sheridan-Kalorama.
- Do not match on "18th Street NW" or "Columbia Road" alone either. Both run into Dupont and Columbia Heights (1460 Columbia Rd is in Columbia Heights). Use them only as a boost.
- "Mary's Center" has sites in Petworth, Fort Totten and MD, so it is not a match term.
- Skip "PorchFest": Takoma and others hold PorchFests too.

**Friendship Heights DC** (accept if A, or B):
- A. DC-only landmark:
  ```
  \bmazza\s+gallerie\b|\bchevy\s+chase\s+pavilion\b|\bjenifer\s+st(reet)?\b|\bfort\s+bayard\b|\b5[0-4]\d\d\s+wisconsin\s+ave(nue)?\b|\bwestern\s+ave(nue)?\s*,?\s*n\.?\s?w\b
  ```
  Mazza, the Pavilion and 50xx–54xx Wisconsin were confirmed DC via DC address points.
- B. `friendship\s+heights` **and** a DC cue (`\bD\.?\s?C\.?\b|\bN\.?W\.?\b|northwest|\bANC\s*3[EG]|\bward\s*3\b|tenleytown|district`) **and no** MD cue (`maryland|\bMd\.|montgomery\s+county|bethesda|wisconsin\s+place|the\s+collection|geico|friendship\s+heights\s+village|hubbard\s+park|somerset`).
  - On the WTOP FH tag this correctly dropped the Brookdale lawsuit, the GEICO campus and Amazon Fresh MD, and kept "Cheesecake Factory in DC's Friendship Heights", Mazza Residences and The Heights food hall (at the Pavilion).
  - "Chevy Chase" alone is not a cue in either direction.

### Feeds: Adams Morgan

Counts are from the newest ≤20 items, using the rule above.

| Feed (exact URL) | robots | items | AM hits / last 20 | Notes |
|---|---|---|---|---|
| `https://www.popville.com/feed/` (+ `?paged=2`, `?paged=3`) | allow | 20 each | 1 / 1 / 1 | Already in the engine. One "Adams Morgan" title (29 Oct) plus mentions in bodies; the 3 pages cover about 5 days. Tag/category feeds (`/tag/adams-morgan/feed/`, `/category/adams-morgan/feed/`) return 200 with **0 items**. `?s=` redirects to Google. |
| `https://www.washingtonian.com/?s=adams+morgan&feed=rss2&orderby=date&order=DESC` | allow | 10 | 9 | Newest 29 Oct 2026, spans about 6 weeks. Mostly body mentions in roundups; 1 title hit ("A Garden-Party-Themed Wedding in Adams Morgan"). `/tag/adams-morgan/feed/` is stale (newest Oct 2024). |
| `https://wtop.com/tag/adams-morgan/feed/` | allow | 10 | 10 (3 in title) | All tagged AM; newest 30 Apr 2026 ("Adams Morgan's PorchFest brings 100+ bands…"), oldest May 2025. Slow but clean. **WTOP `?s=` search feed is robots-DISALLOWED; don't use it.** |
| `https://www.washingtonblade.com/?s=adams+morgan&feed=rss2&orderby=date&order=DESC` | allow | 10 | 9 (1 in title) | Newest 27 Oct 2026, e.g. "Dawn Huggins reflects on year-long reign as Miss Adams Morgan". Many are body-only mentions, so title-only matching is the safer choice. |
| `https://thedcline.org/?s=adams+morgan&feed=rss2&orderby=date&order=DESC` | allow | 20 | 15 (10 in title) | **Stale**: newest 15 Mar 2024. It works, but adds nothing current. Low priority. |
| `https://washingtoncitypaper.com/feed/` | allow | 10 | 0 | Already in the engine; general match only. `?s=` feed returns 200 with **0 items**; `/tag/adams-morgan/feed` returns HTML. |
| `https://ggwash.org/rss` | allow | 10 | 0 | General match only; `/view/tag/adams-morgan/rss` → 404. |
| `https://www.dupontcircleanc.net/wordpress/feed/` (ANC 2B) | allow | 5 | 0 | Real WordPress feed of agenda posts ("ANC 2B October 21st, 2026 Final Agenda"). Relevant only to the HPN's southern strip; keyword-match it, don't take all. |

Checked and **not usable**:
- **Adams Morgan Partnership BID**: `adamsmorgandc.org` has no DNS. The real sites are `admodc.org` and `adamsmorgan.com`, and both return **403 to our UA, including robots.txt**.
- **ANC 1C**: `https://www.anc1c.org/` is Wix. robots allows it, but there is no blog, so `/feed/` and `/blog-feed.xml` return 404. The sitemap holds only static pages (2019–2025 archive pages, committees, SMDs). Its meeting calendar is a third-party BoomTech widget (`calendar.boomte.ch`) loaded with a signed Wix instance token, which is not a public feed.
- **ANC 1A** `anc1a.org/feed/`: 200, 0 items. **ANC 1D** (`anc1d.org`, Squarespace) and **ANC 2D** (`anc2d.org`): `/feed/` 404. Neither covers the HPN materially anyway.
- **Northwest Current** `https://www.currentnewspapers.com/feed/`: now **200, not 520**, but returns 0 items. Its `?s=` feed returns only pages last modified 25 Jul 2020, so the site is dead.
- **Others with no usable feed**: InTowner (`intowner.com/feed/` 404; `?s=` returns HTML), Hill Rag/MidCity (`hillrag.com/feed/` 3 items, `?s=` 0 items), UrbanTurf (`/feed`, `/rss` 404), Mt Pleasant blog (`mtpleasantdc.org/feed/`, last post 2017), WAMU `?s=` (HTML).
- **No DNS**: kaloramapark.org, adamsmorganday.org, amomainstreet.org.

### Feeds: Friendship Heights DC

| Feed (exact URL) | robots | items | FH hits / last 20 | Notes |
|---|---|---|---|---|
| `https://anc3e.org/feed/` | allow | 25 | 1 (strict) | Already used for Tenleytown. ANC 3E is FH-DC's ANC (3E04), so take it whole ("all"), as Tenleytown does. Example: "Resolution on Friendship Heights (Maryland) Sector Plan", 10 Sep. |
| `https://anc3e.org/?s=friendship+heights&feed=rss2&orderby=date&order=DESC` | allow | 25 | 12 (strict); all 25 contain the phrase | Mostly minutes/agendas that mention FH; newest 8 Oct 2026. Useful as an "FH-specific" slice of 3E. |
| `https://anc3g.dc.gov/rss.xml` (ANC 3/4G) | allow | 10 | 0 strict | Drupal events feed: Civic Core hearings, special meetings. About Chevy Chase DC, so use it only if the FH boundary takes in 3/4G. |
| `https://wtop.com/tag/friendship-heights/feed/` | allow | 10 | 3 strict, title 1 | Mixed DC/MD (Brookdale, GEICO), so it needs the MD filter; newest 9 Jul 2026. |
| `https://www.washingtonian.com/?s=friendship+heights&feed=rss2&orderby=date&order=DESC` | allow | 10 | 3 | Newest 24 Aug 2026; body mentions in roundups. `/tag/friendship-heights/feed/` is stale (newest Jan 2024). |
| `https://foresthillsconnection.com/?s=friendship+heights&feed=rss2&orderby=date&order=DESC` | allow | 10 | 7 | Stale-ish: newest Jun 2025. The main feed (`/feed/`, already used) had 0 FH hits in its last 10. |
| `https://thedcline.org/?s=friendship+heights&feed=rss2&orderby=date&order=DESC` | allow | 20 | 5 | Stale: newest Oct 2024. |
| `https://www.popville.com/feed/` (pages 1–3) | allow | 60 | 0 | The general matcher would still catch future FH posts. |

Checked and **not usable**:
- **Friendship Heights Alliance** (`friendshipheights.com`): **403 to our UA, including robots.txt**.
- `chevychasepavilion.com`: 403.
- **`mazzagallerie.com` now redirects to an unrelated third-party site (trustpositif.com). Do not link it.**
- Chevy Chase DC citizens sites: `chevychasecitizens.org/feed/` 404; `chevychasedc.org` TLS error; ccdccitizens.org no DNS.
- `bethesdamagazine.com/feed/` works (10 items) but is MD-centric; its `?s=` returns HTML.
- strollmag `/feed/` 404.

## 2. EVENTS

| Source | Endpoint | Result |
|---|---|---|
| ANC 3E agendas (FH) | `https://anc3e.org/feed/` | **Yes.** Posts titled "October 8, 2026 Meeting Agenda" (the slug says `october-9-…`, so parse the title, not the slug) and "September 10, 2026 Meeting Agenda". Already handled for Tenleytown. |
| ANC 3/4G meetings | `https://anc3g.dc.gov/rss.xml` | **Yes, but parse the date from the title**: "October 15, 2026, ANC Special Meeting…", "2026-11-12 Hearing on Chevy Chase Civic Core…". The `<description>` date (e.g. "Sun, 10/25/2026 - 17:45") is the post time, not the event time. Some items have no date in the title ("ANC 3/4G Admin meeting"); skip those. |
| ANC 1C agendas (AM) | none | **No machine-readable source.** The anc1c.org calendar is a BoomTech Wix widget. Agendas exist as PDFs on oanc.dc.gov (e.g. `/sites/default/files/2026-03/ANC 1C March 4, 2026 meeting agenda.pdf`), but they are not in a feed. OANC's `https://oanc.dc.gov/rss.xml` (already used) carries only the 10 newest event nodes citywide; none were 1C, 3E or 3/4G today. Keep it with an `ANC 1C` / `ANC 3E` / `ANC 3/4G` title filter for the rare hit. ANC 1C meets the first Wednesday at 7 pm (per its 2026 agendas); a static "how to attend" link is the realistic option. |
| ANC 2B agendas (AM southern strip) | `https://www.dupontcircleanc.net/wordpress/feed/` | Works: "ANC 2B October 21st, 2026 Final Agenda". Optional; 2B is mostly Dupont. |
| Adams Morgan BID / PorchFest / AM Day | admodc.org, adamsmorgan.com (403); admoporchfest.com (403 on home page, robots 404) | **Blocked.** The AM Day festival has no site that resolves. The DC Government's `https://hsema.dc.gov/rss.xml` (special-event permits, robots allow) lists AM PorchFest/AM Day pages when posted, but the feed only ever holds the 10 newest items (`?page=` is ignored). Today it had 0 AM items, so the yield is low. |
| Tribe Events API | anc3e.org `/wp-json/tribe/events/v1/events` (200, 0 events); smartergrowth.net (200, 0); foresthillsconnection, dupontcircleanc, washingtonian (404) | Nothing usable. |
| DPR (Kalorama Park, Chevy Chase CC) | `https://dpr.dc.gov/rss.xml` | Newsroom feed with stale 2016–17 items; no per-site events. |
| Farmers markets (existing layer, MapServer/2) | — | **Adams Morgan Farmers Market**, Euclid St & Columbia Rd, Saturdays (in the neighborhood, about 0.1 mi from 18th & Columbia). Within 1 mi: FRESHFARM Dupont Circle (Sun), FRESHFARM Columbia Heights (Wed/Sat), Mount Pleasant Farmers' Market (Sat). **FH: none within 1 mi in the layer.** The FH Alliance Sunday market at 5210 Wisconsin is not in it. |
| Libraries | — | DCPL blocks bots (noted, not retested). |

## 3. JOBS

| Employer / source | Endpoint | Neighborhood fit | robots | Verdict |
|---|---|---|---|---|
| **Children's National, "Friendship Heights" site** | `POST https://childrensnational.wd108.myworkdayjobs.com/wday/cxs/childrensnational/CN_Careers/jobs`, body `{"appliedFacets":{"locations":["<id>"]},...}`. Facet param is **`locations`**; "Friendship Heights" id is `8788a69939e31000c3973f7517460000` (look it up by descriptor nightly). | Address in posting text: **5028 Wisconsin Ave NW**. That is ANC 3E03, inside the **TENLEYTOWN** HPN, just south of the FH core. 3 hits, but only 1 has primary `location` = Friendship Heights: "Ambulatory Patient Care Tech – Friendship Heights – Part-time", posted 2026-08-10. Keep the existing `location ==` check. | allow | **Use for FH** ("in" or "nearby", depending on the boundary). Already used for Tenleytown. |
| Children's National, "CNPA Chevy Chase" | same; id `8788a69939e31000c396eb13a52d0000` | 3 jobs, but the address is **4601 North Park Ave = Chevy Chase, MD** | allow | **Exclude** (Maryland). |
| Children's National, Adams Morgan | — | No AM site among the 31 location facets. The nearest are Shaw Metro (5 jobs) and Columbia Heights (2). | — | None for AM. |
| sweetgreen (Greenhouse) | `https://boards-api.greenhouse.io/v1/boards/sweetgreen/jobs` | 67 jobs; DC jobs only at 601 Massachusetts Ave NW plus one unspecified "Washington, DC". None in 20009/20015/20016. | allow | Keep as a watch list; no hits today. |
| Safeway (Oracle Recruiting Cloud) | as in JOBS-SOURCES.md §A (`locationId=300000002781168`) | **1747 Columbia Rd NW (in the AM HPN)**: Front End Entry Level, posted 2026-09-25, req 772022. It returns lat/long, so use point-in-polygon. 1701 Corcoran (20009) is *not* AM. | robots 404 | Same status as before: **terms unverified (blocked to non-browsers); excluded until the owner reads them.** |
| Mary's Center (UKG/UltiPro) | `POST https://recruiting.ultipro.com/MAR1048MARY/JobBoard/88f33d62-f5a4-4f55-b429-d203a9b78da7/JobBoardView/LoadSearchResults` | The JSON works and is exact: 26 jobs, including 7 at Ontario Clinic (2333 Ontario Rd), 5 at Kalorama BH Center (1707-B Kalorama Rd) and 3 at Kalorama Admin. It also has 6 at the Georgia Clinic, 3912 Georgia Ave NW (Petworth). | **DISALLOW**: `Disallow: */JobBoardView` | **Exclude.** This is the best AM jobs source, so it is worth asking Mary's Center for permission. Its old SmartRecruiters board returns 0 jobs, and `api.smartrecruiters.com` robots disallows `*`. |
| The LINE DC hotel (CareerPlug `line-saguaro-careers.careerplug.com`) | `/jobs`, `/jobs.json`, `/jobs.rss` | Hotel is in AM | **403 to our UA (incl. robots)** | Exclude. |
| Washington Hilton (1919 Connecticut, in the AM HPN) / Embassy Suites (4300 Military Rd, FH) | jobs.hilton.com | — | `Disallow: /api/*`, no feed | Exclude. |
| Greenhouse/Lever/Ashby slugs probed (no boards): tatte, districttaco, cava, mundoverde, unityhealthcare, jubileehousing, line/sydell/saguaro, compasscoffee, callyourmother, tryst, pinstripes, cheesecakefactory, federalrealty, douglasdevelopment, jbgsmith, washingtonclinic, sibley, wmata, citydance, layc, carlosrosario and others | — | — | — | Nothing found. |
| DCPS (Marie Reed, H.D. Cooke), Target, Whole Foods, GEICO (MD) | — | — | — | Excluded as instructed or as already documented. |

Bottom line for jobs: **FH gets 1 job today (Children's National at 5028 Wisconsin, already a Tenleytown source). AM has no qualifying source today.** The two real AM options, Mary's Center and Safeway at 1747 Columbia, need the owner's call or the employer's permission.

## 4. HISTORY (Evening Star, loc.gov)

loc.gov answered normally (no 403). I used the same query shape as `history.py` (`q`, `dates`, `fa=partof_title:evening star (washington, d.c.) 1854-1972`, `fo=json`). Hit counts are for the target week **1926-10-31 → 11-06** and for Oct–Nov 1926; I read OCR snippets to check for ambiguity.

### Adams Morgan (the name dates from the 1950s; 0 hits in 1926)

| Term | Week | Oct–Nov | Notes |
|---|---|---|---|
| `"Washington Heights"` | 9 | 51 | **All 6 sampled hits in the week were DC**: Washington Heights Presbyterian Church "Columbia and Kalorama roads", and real-estate ads ("Exclusive Washington Heights Section. BILTMORE ST."). Risk: NYC's Washington Heights in wire copy. Require a local cue (below). |
| `"Lanier Heights"` | 4 | 11 | Unambiguous. Mostly real-estate ads (Ontario Rd). |
| `"Kalorama road"` | 7 | 88 | Kalorama Rd addresses ≥2100 are Sheridan-Kalorama (2221 = ANC 2D), so accept only house numbers <2000. |
| `"Ontario road"` | 7 | 23 | Unambiguous street, entirely in AM; mostly ads. |
| `"Champlain street"` | 3 | 10 | Unambiguous, small. |
| `"Ambassador Theater"` | 9 | 53 | Crandall's Ambassador at 18th & Columbia ("18TH ST. AT COLUMBIA ROAD, OPPOSITE Ambassador Theater"). Very local, but mostly movie listings. Pitfall: the Ambassador **Hotel** (14th & K). |
| `"Knickerbocker"` | 2 | 33 | The 1922 theater disaster site (same corner). Pitfall: Knickerbocker as a NY name or brand; needs a local cue. |
| `"Adams School"` | 1 | 5 | One of the two schools behind the later name. Small; ambiguous with other Adams schools. |
| `"Meridian Hill"` | 3 | 53 | Mostly the park/16th St (Columbia Heights side). Use as a booster only. |
| `"Kalorama Heights"` | 0 | 2 | Rare. |

**Recommended `terms`:** `"Lanier Heights"`, `"Washington Heights"`, `"Ontario road"`, `"Kalorama road"`, `"Champlain street"`, `"Ambassador Theater"`.
- **pattern**:
  ```
  lanier\s+heights|washington\s+heights|ontario\s+road|(1[0-9]{3})\s+kalorama\s+road|champlain\s+st|ambassador\s+theat
  ```
  Also require that the clip does **not** contain `new\s+york|N\.\s?Y\.|manhattan` when the only hit is "Washington Heights".
- **local**:
  ```
  columbia\s+road|18th\s+st|eighteenth\s+st|kalorama|biltmore|calvert|adams\s+mill|mintwood|belmont\s+road|euclid|knickerbocker|washington\s+heights\s+presbyterian
  ```
- Expect real-estate ads to dominate. The existing LEGAL/SCREEN filters will drop some of them; that is intended.

### Friendship Heights DC

| Term | Week | Oct–Nov | Notes |
|---|---|---|---|
| `"Friendship Heights"` | 0 | 14 | **In 1926 this means Maryland**: "Friendship Heights. Md., 15 minutes from the city", "101 Wooton ave", the Friendship Heights citizens group in Montgomery County federations. |
| `"Chevy Chase Circle"` | 7 | 76 | DC/MD line on Connecticut Ave, about 1 mi east of FH. Chevy Chase DC, not FH. |
| `"Chevy Chase, D. C."` | 82 | 779 | Inflated: punctuation is dropped, so it matches any "Chevy Chase … D. C.". Chevy Chase DC, not FH. |
| `"Jenifer street"` | 0 | 21 | Sampled hits are 37xx–39xx Jenifer (Chevy Chase DC, ANC 3/4G), not the FH end. Accept only 4[0-9]xx Jenifer. |
| `"Western avenue"` | 0 | 8 | Mostly Chevy Chase DC ads ("Drive east on Western Avenue from Chevy Chase Circle"). |
| `"Military road"` | 5 | 51 | Long road (Rock Creek to Wisconsin); ambiguous without a number. |
| `"Fort Bayard"` | 0 | 1 | DC park at Western & River Rd, but also an Army post in New Mexico. |
| `"Belt road"`, `"Fessenden street"` | 0 / 1 | 6 / 5 | Tenleytown-ish. |

**Recommendation:** in 1926 the DC side of today's Friendship Heights had no distinct name in the Star. It was the northern edge of "Tenleytown" and the western edge of "Chevy Chase, D.C.", and "Friendship Heights" meant the Maryland village. The best options:
- (a) Reuse Tenleytown's archive config (`Tenleytown`, `Tenley`, `"Fort Reno"`), labeled as "the area then called Tenleytown".
- (b) Use `"Friendship Heights"` + `"Wisconsin avenue"` + `"Chevy Chase Circle"`, with pattern `friendship\s+heights|chevy\s+chase\s+circle`, a clip filter that **rejects** `\bMd\b|Maryland|Montgomery|Wooton|Somerset|Bethesda`, and local `wisconsin\s+av|western\s+av|4[0-9]{3}\s+jenifer|river\s+road|fort\s+bayard|military\s+road|tenley`. Expect **0–2 usable clips** in most weeks (0 hits in the target week).

I'd ship (a), and add (b) once the boundary is settled.

## Not verified / excluded
- Everything returning 403 to our UA (AdMo BID ×2, FH Alliance, AdMo PorchFest, CareerPlug, Chevy Chase Pavilion) was not retried with any other agent.
- Not tested: Hilton terms beyond robots; ANC 1C's BoomTech calendar data (signed token, not a public API).
