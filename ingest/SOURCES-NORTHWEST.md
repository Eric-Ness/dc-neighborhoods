# Sources for Brookland, Glover Park, the Palisades and Van Ness (DC)

Tested 2026-11-01. Every fetch used the user agent `dc-neighborhoods-ingest/0.1 (+https://petworth.org)`. robots.txt was checked for agent `dc-neighborhoods-ingest` on the exact path, query string included, with the engine's own wildcard-aware matcher (`news.parse_robots` / `news.robots_allows`), and stated crawl delays were honoured. "403 to our UA" means the server refused our agent; it was not retried with any other agent. Hit counts use the rules in each area's keyword block, run over the newest ≤20 items. **MATCH** = title + summary + tags, which is what `news.py` "match" mode reads. **body** = the article body too, which is what "search" mode reads.

## 0. Geography findings that change the plan

All from DC GIS: HPN layer `Health_WebMercator/MapServer/13`, SMD-2023 layer `Administrative_Other_Boundaries_WebMercator/MapServer/55`, Neighborhood Clusters `…/MapServer/17`, Neighborhood Names `…/MapServer/18`, Main Street corridors `Business_Betterment_Areas_WebMercator/MapServer/16`, address points `Location_WebMercator/MapServer/0` (its `SMD` field). Area shares come from a 40×40 grid sample of each polygon.

**Three of the four have no HPN, and the fourth is too wide.** The HPN list has `KENT/PALISADES`, but no Brookland, Glover Park or Van Ness. Use SMD sets on layer 55, as Friendship Heights and H Street do.

- **Brookland.** The core is split across four HPNs. 12th & Monroe NE (3500 12th St NE) is in BRENTWOOD, 5B04. Monroe Street Market (716 Monroe St NE) and Dance Place (3225 8th St NE) are in EDGEWOOD, 5F02. Catholic University (620 Michigan Ave NE) and the Basilica (400 Michigan Ave NE) are in MICHIGAN PARK, 5A04. The Franciscan Monastery (1400 Quincy St NE) is in WOODRIDGE, 5B02. Turkey Thicket and Brookland MS (1100/1150 Michigan Ave NE) are in MICHIGAN PARK, 5B05. The "Brookland" neighborhood-name point falls in 5B03.
  - **Recommendation:** `SMD_ID IN ('5B02','5B03','5B04','5B05','5B06','5F02','5A04')` with `boundary_parts: 7`.
    - 5F02 belongs in because it holds the Metro-side commercial strip, the Arts Walk, Dance Place and FRESHFARM Monroe Street.
    - 5A04 belongs in because it is the CUA campus and the Basilica. It is 73% MICHIGAN PARK and 26% DC MEDICAL CENTER by area. MedStar Washington Hospital Center (110 Irving St NW) is **not** in it; that is 5E06.
    - Left out: 5B01 (Michigan Park / Bunker Hill Rd, 96% WOODRIDGE) and 5B07 (Woodridge / Fort Lincoln).
  - **ANCs:** 5B (core), 5F (5F02 only), 5A (5A04 only).
- **Glover Park.** The Glover Park Main Street polygon is 3B02 89%, 3C08 5%, 2E01 2%. By HPN it is 69% WOODLEY PARK and 27% CATHEDRAL HEIGHTS, so the commercial strip (2200–2400 Wisconsin) is in the **WOODLEY PARK** HPN, not Cathedral Heights. The "Glover Park" name point falls in 3B02.
  - **Recommendation:** all of ANC 3B, `SMD_ID LIKE '3B%'` (3B01–3B06), which is how the ANC describes itself ("Glover Park and Cathedral Heights").
  - The tighter Glover Park core is 3B01, 3B02, 3B03 and 3B05. 3B04 and 3B06 are Cathedral Heights / New Mexico Ave; 3B06 is 100% KENT/PALISADES HPN and holds AU's 3201 New Mexico Ave campus.
  - **Overlap with Georgetown:** 2115 and 2121 Wisconsin Ave (Georgetown University offices) are in 3B02. SOURCES-WEST already excludes them from Georgetown, so they land here cleanly.
  - McLean Gardens (3811 Porter) and Cathedral Commons (3500 Wisconsin) are 3A01, outside ANC 3B.
- **Palisades.** HPN `KENT/PALISADES` is ANC 3D: 3D04 17%, 3D06 15%, 3D03 14%, 3D01 13%, 3D07 12%, 3D05 9%, 3D02 9%. It also takes in Spring Valley, Wesley Heights and Foxhall, and **AU's Main Campus** (4400 Massachusetts Ave NW, SMD 3E07, is inside this HPN). With the HPN, AU's 70 Main Campus jobs would count as "in the Palisades".
  - **Recommendation:** `SMD_ID IN ('3D03','3D04','3D05','3D06')`. That covers the MacArthur Blvd corridor and is where the Palisades Main Street polygon lies: 3D06 27%, 3D05 25%, 3D04 22%, 3D01 11%, 3D07 8%, 3D03 5%.
  - Inside: the Palisades shops (4865/4883 MacArthur, 3D05), the Palisades Library (4901 V St, 3D05), the Rec Center (5200 Sherier Pl, 3D05), the farmers market (MacArthur & 48th Pl, 3D05), 5101 MacArthur (3D04), Sibley Memorial Hospital (5255 Loughboro Rd, 3D03) and 4500 MacArthur (3D06).
  - Use the HPN only if you want "Palisades and Spring Valley/Wesley Heights" and accept the AU problem.
  - **ANC:** 3D.
- **Van Ness.** The "Van Ness" name point is in 3F05, and **3F05 is 78% TENLEYTOWN HPN**. UDC (4200 Conn), the Van Ness–UDC Metro block and 4250/4310/4340 Conn are all in the **live Tenleytown site's boundary**. 4401/4455 Conn (east side) are FOREST HILLS HPN, 3F03. The Van Ness Main Street polygon covers all of ANC 3F: 3F03 24%, 3F04 19%, 3F06 16%, 3F05 16%, 3F02 14%, 3F01 8%.
  - **Recommendation:** `SMD_ID LIKE '3F%'`. That is ANC 3F's own "Van Ness, North Cleveland Park, Wakefield, Forest Hills".
  - It overlaps Tenleytown: the TENLEYTOWN HPN contains 3F01 100%, 3F05 78% and 3F04 50%. There is no overlap with Chevy Chase (`3/4G%`) or the Cleveland Park HD (3C).
  - **ANC:** 3F.

## 1. BROOKLAND (SMDs 5B02–5B06, 5F02, 5A04; ANC 5B + 5F + 5A)

### News

| Feed (exact URL) | robots | items | MATCH / body / title | Mode / notes |
|---|---|---|---|---|
| `https://brooklandcivic.org/feed/` (Brookland Neighborhood Civic Association) | allow, **Crawl-delay 3**; `Disallow: /*?` | 10 (Jul 2025 – 9 Aug 2026) | 5 / 10 / 0 | **all**. Every item is a monthly minutes post ("May 2026 Minutes"). Titles are generic, so take all rather than match. Slow. Because of `/*?`, never add query strings on this host. |
| `https://wtop.com/tag/brookland/feed/` | allow | 10 (Jan 2023 – 1 Feb 2026) | 10 / 10 / 4 | **match**. Clean but slow: "Trader Joe's opens Brookland store…" (May 2025), "2nd black bear in a year enters DC's Brookland neighborhood". |
| `https://wtop.com/tag/catholic-university/feed/` | allow | 10 (Jul 2023 – Jan 2026) | 3 / 6 / 1 | **match**. Rule keeps "Teenage boy killed in shooting at Brookland Metro station…" and drops campus-only items ("Catholic University adds a layer of security…" has no neighbourhood cue in the summary). Optional. |
| `https://anc5a.org/feed/` (ANC 5A, WordPress) | allow | 10 (23 Jun – 13 Oct 2026) | 1 / 1 / 1 | **match**. Only 5A04 is in the boundary, so filter it. Kept: "Work Scheduled (John McCormack Rd, from Brookland Metro…)". Also posts "ANC 5A Monthly Meetings" / "ANC Executive Meetings for 2026" schedule notes. |
| `https://www.danceplace.org/feed/` | allow | 10 (Jun 2025 – 16 Sep 2026) | 10 / 10 / 2 | **match** (it hits only because "Dance Place" is a term). It is arts-organisation news ("Pathways Forward: A Dance Place Town Hall"); low priority. Its events API is the better use (below). |
| `https://cuatower.com/feed/` (The Tower, CUA student paper) | allow | 10 (20–26 Oct 2026) | 0 / 0 / 0 | Active but campus-only ("Cardinal Court Tradition…", "SGA Senate Recap"). **Skip**, as with The Hoya's main feed for Georgetown. |
| `https://www.catholic.edu/rss.xml` (CUA newsroom, Drupal) | allow | 10 (Oct 2024 – 2 Oct 2026) | 1 / 1 / 0 | University PR; the one hit is from 2024. Skip. |
| `https://thedcline.org/?s=brookland&feed=rss2&orderby=date&order=DESC` | allow | 20 (Jan 2022 – 24 Nov 2025) | 13 / 13 / 7 | **search**, but stale: the newest item is Nov 2025. Fine to keep for parity with other sites. |
| `https://www.popville.com/feed/` p1–p5 (already used) | allow | 100 (22–30 Oct) | 2 / 5 / 0 | "Listing of the Day: 2881 Chancellor's Way" and "DC Fresh Finds…" (Brookland listings in the summary). The others are body-only. |
| `https://51st.news/rss/` (SHARED) | allow | 15 | 0 / 3 / 0 | Body mentions only ("In these hyperlocal ANC races…"). |
| `https://ddot.dc.gov/rss.xml` (SHARED) | allow | 10 | 1 / 1 / 1 | "ANC 5B Monthly Meeting [Virtual]" (a DDOT staff-attendance notice; 3 Sep). |
| `https://www.washingtonblade.com/?s=brookland&feed=rss2&orderby=date&order=DESC` | allow | 10 | 3 / 10 / 0 | Incidental (real-estate columns, "The gayborhood is changing"). Skip. |

**Not usable:**
- **ANC 5B** `www.anc5b.org` is a Google Sites site: no feed, robots 404. `anc5b.dc.gov`, `anc5a.dc.gov` and `anc5f.dc.gov` have no DNS. **ANC 5F** `www.anc5f.com` is also Google Sites with no feed.
- Monroe Street Market `monroestreetmarket.com/feed/` is stale (newest 12 Jan 2024).
- Washington City Paper and the Washington Informer `?s=brookland` feeds return 0 items. The Informer's `/tag/ward-5/feed/` had 0 hits.
- WTOP `/tag/ward-5/`, `/tag/northeast-dc/` and Washingtonian `?s=brookland` have body-only or near-zero hits (Washingtonian 0 MATCH / 9 body).
- PoPville tag/category feeds (`/tag/brookland/feed/`, `/category/brookland/feed/`) return 200 with 0 items.
- Hill Rag WP JSON `?search=brookland` (Crawl-delay 20) is mostly its vet column. Skip.
- No "Brookland Main Street" organisation exists in DC's Main Streets layer, and no site was found.

**Keyword rule (Brookland).**
- TERMS:
  ```
  \bbrookland\b(?!,?\s+(ark|arkansas|ar)\b)|\bmonroe\s+street\s+market\b|\b(brookland\s+)?arts\s+walk\b(?=.*\b(brookland|monroe|NE)\b)|\b12th\s+st(reet)?\.?\s+(n\.?e\b|corridor)|\bturkey\s+thicket\b|\bfranciscan\s+monastery\b|\bdance\s+place\b|\bbasilica\s+of\s+the\s+national\s+shrine\b|\bnational\s+shrine\s+of\s+the\s+immaculate\b|\bANC\s*5B\b|\bcatholic\s+university\b(?=.*\b(neighbou?rs?|neighbou?rhood|residents?|brookland|NE|ANC|michigan\s+ave|metro)\b)|\bbrookland[-\s/]+cua\b|\bwoodridge\s+(library|neighborhood\s+library)\b
  ```
  (flags `re.I | re.S`)
- NOT_HERE[0] (reject):
  ```
  \bbrookland,?\s+(ark|arkansas|ar)\b|\bjonesboro\b|\bbrooklands\b|\bkent\b|\bromney\s+marsh\b
  ```
- NOT_HERE[1] (rescue): `\bANC\s*5B\b|\bNE\b|\bnortheast\b|\b12th\s+st|\bmonroe\s+st|\bD\.?C\.?\b`
- Notes:
  - `\bbrookland\b` cannot match "Brooklyn" or "Brooklands", the UK motor circuit. The trailing `\b` already blocks the plural; the reject list catches "Brooklands" anyway.
  - The real collisions are Brookland, Arkansas (a Jonesboro suburb) and the Kent (UK) village.
  - "Catholic University" alone is campus news, so it needs a neighbourhood cue, the same idea as Georgetown University.
  - Precision check (synthetic headlines; no out-of-area items appeared in today's feeds): "Brookland, Ark., school district names superintendent" is rejected, "Catholic University announces new provost" is rejected, and "Catholic University neighbors weigh in on campus plan at ANC 5A" is kept.

### Events

| Source | Endpoint | Result |
|---|---|---|
| **Dance Place** (3225 8th St NE, SMD 5F02) | `GET https://www.danceplace.org/wp-json/tribe/events/v1/events` (robots allow; it disallows only `/wp-admin/`, `/cgi-bin/`, `/fb/`, `/email/`, `/test/`, `/wp-content/plugins/`) | **Yes.** 13 upcoming: "NOËL" (4 Dec), "Kwanzaa Celebration" (12 Dec), "Chocolate Charm Holiday Spectacular" (19 Dec 7 pm), "Coyaba Academy & KanKouran Youth Ensemble" (16 Jan 2027). The venue is "Dance Place, 3225 8th Street NE" on most; some have no venue (assume Dance Place). |
| **Basilica of the National Shrine** (400 Michigan Ave NE, 5A04) | `GET https://www.nationalshrine.org/wp-json/tribe/events/v1/events` (robots allow) | **Yes, but filter.** 43 upcoming, mostly the liturgical calendar ("Solemnity of All Saints", "Thirty-Second Sunday in Ordinary Time") and pilgrimages ("Diocese of Camden Pilgrimage"). Keep concerts and lectures (e.g. "Choral Concert for the Commemoration of All Souls", 2 Nov 7 pm, Crypt Church). Drop titles matching `solemnity\|sunday in ordinary\|commemoration of\|pilgrimage\|feast of\|memorial of`. Venue has a name only (Great Upper Church, Crypt Church). |
| **ANC 5B** | `www.anc5b.org/meetings` (Google Sites HTML) | **No machine-readable source.** The page text lists the schedule: full meetings on the third Wednesday (Oct 21, Nov 18, Dec 16, Jan 20 2027) plus committee dates. It is HTML only, so use a static link plus OANC (filter `ANC 5B`). OANC had no 5B item in today's 10. |
| ANC 5F (5F02 only) | `www.anc5f.com/meetings` (Google Sites) | Same as 5B: HTML only. Third Tuesday (Nov 17, Dec 15, 2026). Static link. |
| ANC 5A (5A04 only) | `https://anc5a.org/feed/` | The posts "ANC 5A Monthly Meetings" (17 Sep) and "ANC Executive Meetings for 2026" list dates in the body, not the title. `events.py`'s `AGENDA` title pattern doesn't fit. Tribe API 404; `/events/feed/` 0 items. Use OANC. |
| Brookland Neighborhood Civic Association | `/events/feed/` 200 with 0 items. robots blocks `/calendar/action*` and `/events/action*` (the iCal export paths). | **No.** |
| Catholic University | `www.catholic.edu/event-calendar` (Drupal) | **No feed found.** `/event-calendar/rss.xml` and `/event-calendar.ics` 404; `?_format=json` returns 406. Link only. |
| Monroe Street Market | `/events/feed/` 0 items; Tribe API 404 | No. |
| Franciscan Monastery (1400 Quincy St NE, 5B02) | `https://www.myfranciscan.org/wp-json/tribe/events/v1/events` | 200, **0 events**. Keep watching; otherwise none. |
| Farmers markets (existing layer) | — | **FRESHFARM Monroe Street**, 716 Monroe St NE, Saturdays 9–1 (5F02, inside). Nearby: Co-Op Farmers Market, 2015 Bunker Hill Rd NE (5B01, 1st/3rd Sat); Edgewood Market, 670 Rhode Island Ave NE (5F03, 1st/3rd Sat). |
| Library | link only | DCPL blocks bots. Brookland has no branch; nearest is **Woodridge** (1801 Hamlin St NE, SMD 5C07): `https://dclibrary.libnet.info/events?l=Woodridge%20Neighborhood%20Library`. Also link Turkey Thicket Rec Center (DPR). |

Suggested config:
- `ANCS["brookland"] = ["5B", "5F", "5A"]`.
- No `ANC_FEEDS` entry (no ANC 5B feed).
- New calendars: `CALENDARS["brookland"] = ["danceplace", "shrine"]`. Both are Tribe; reuse the Hill Center/CHRS-style Tribe reader.

### Jobs

| Employer | Endpoint | Filter | robots | Verdict |
|---|---|---|---|---|
| **Children's National, "Rehabilitation and Specialized Care Bunker Hill Road"** | `POST https://childrensnational.wd108.myworkdayjobs.com/wday/cxs/childrensnational/CN_Careers/jobs`, `locations: ["8788a69939e31000c3977508fef00000"]` (look up by descriptor nightly) | **8 jobs.** Posting text gives **1731 Bunker Hill Road NE, 20017** (SMD 5B01, 0.8 mi from 12th & Monroe). Samples: "Speech Language Pathologist PRN" (2026-10-13), "Team Lead Cook" (2026-10-01), "Occupational Therapist, Inpatient PRN" (2026-10-01). One result's primary location is Main Campus (a multi-location posting); filter on the detail's `location`. | allow (same tenant already wired) | **Use, "nearby"** (or "in" if you add 5B01 to the boundary). `SITES["brookland"] = [("cn", "Rehabilitation and Specialized Care Bunker Hill Road", "nearby", "1731 Bunker Hill Rd NE, about 0.8 mi")]`. |
| Children's National Main Campus (111 Michigan Ave NW, 5E06) | same | 264 jobs, 1.26 mi west across the tracks and McMillan | allow | Optional "nearby" with `NEARBY_CAP`. It is really the Hospital Center campus, not Brookland; I'd leave it out. |
| Catholic University | iCIMS (`staff-cua.icims.com`) | — | robots allows the search pages | **Not an allowed platform** (same as Brookings in SOURCES-WEST). Excluded. |
| Dance Place, Monroe Street Market, Shrine | no Greenhouse/Lever board | — | — | — |

**ZIP:** `ZIPS["brookland"] = ("20017",)` is safe. 20017 covers Brookland, CUA and Michigan Park, and no other live site uses it. Today it matches nothing on the sweetgreen Greenhouse board, so it only matters if Greenhouse employers are added.

## 2. GLOVER PARK (ANC 3B, `SMD_ID LIKE '3B%'`)

### News

| Feed (exact URL) | robots | items | MATCH / body / title | Mode / notes |
|---|---|---|---|---|
| **`https://gpcadc.org/feed/`** (Glover Park Citizens' Association) | allow | 10 (9 Jan – 26 Oct 2026) | 5 / 6 / 4 | **all.** GP-only organisation. Meeting notices ("GPCA Meeting on November 3rd, 2026 at 7 pm via Zoom"), "Glover Park Day on June 6th!", "Glover Park Art-n-Music Walk on Saturday, April 18th!". About one post a month. The printed *Gazette* is a PDF; link only. |
| `https://wtop.com/tag/glover-park/feed/` | allow | 10 (Apr 2016 – 12 Feb 2026) | 10 / 10 / 4 | **match**. Slow. "Police identify mother killed in DC shooting…" (Feb 2026), "This isn't the FBI's 'spy house' anymore…" (Jan 2026). |
| `https://www.popville.com/feed/` p1–p5 (already used) | allow | 100 | 2 / 2 / 1 | "About that Huge Police Presence in Glover Park…" (29 Oct), "Kiin Laow Thai Restaurant & Bar Soft Opening…" (22 Oct). PoPville is the best current GP source. |
| `https://thedcline.org/?s=glover+park&feed=rss2&orderby=date&order=DESC` | allow | 20 (Nov 2020 – 16 Jul 2026) | 8 / 8 / 4 | **search**; slow. |
| `https://51st.news/rss/` (SHARED) | allow | 15 | 0 / 1 / 0 | Body only. |

**Not usable:**
- **ANC 3B `anc3b.org/feed/` is robots-DISALLOWED** (`Disallow: /feed/`, also `/pdf/`). Its WP REST API is not disallowed; see Events.
- Glover Park Main Street `gloverparkmainstreet.org/feed/`: 4 items, newest 31 Aug 2020, **Crawl-delay 10**. Dead feed; no Tribe API; `/events/feed/` 0 items. Its "discover" subdomain was not tested.
- Georgetown outlets:
  - `georgetownmetropolitan.com/?s=glover+park…`: 1 MATCH / 10 body ("Northwest Georgetown … ANC Update").
  - `georgetowner.com/?s=glover+park…`: 0.
  - The Hoya City News: 0.
- Washingtonian `?s=glover+park`: 0 MATCH / 5 body (roundups). Washington City Paper `?s=` feeds return 0 items. Washington Blade `?s=glover+park`: 2 MATCH, from 2021–22.
- `anc3b.dc.gov`: no DNS.

**Keyword rule (Glover Park).**
- TERMS:
  ```
  \bglover\s+park\b|\bguy\s+mason\b|\bstoddert\s+(elementary|es|rec|school)\b|\bwhitehaven\s+(park|parkway|st)\b|\bANC\s*3B\b|\bglover[-\s]+archbold\b(?=.*\b(glover\s+park|wisconsin|ANC\s*3[BD]|neighbo)\b)
  ```
- NOT_HERE[0] (reject): `\brussian\s+embassy\b|\bkremlin\b|\bmoscow\b|\bputin\b`
- NOT_HERE[1] (rescue): `\bglover\s+park\b|\bANC\s*3B\b|\bguy\s+mason\b|\bstoddert\b`
- Notes:
  - `\bglover\s+park\b` cannot match "Glover-Archbold Park" (a hyphen or "Archbold" follows "Glover"). Glover-Archbold is NPS parkland that runs from the Potomac to Van Ness St, through 3B and 3D. It counts only with a GP cue.
  - The Russian Embassy (2650 Wisconsin) is physically in Glover Park, but its coverage is geopolitics. The reject list drops it unless the item says "Glover Park" itself. The DC Line's "Protesters gather… outside Russian embassy" does say Glover Park and is kept, which is defensible.
  - **Don't add** "Cathedral Heights" or "McLean Gardens". Augie's Mussel House (PoPville, "opening in Cathedral Heights") is at Cathedral Commons, 3A01, outside ANC 3B. McLean Gardens is 3A01 too.
  - Synthetic checks: "Glover-Archbold Park trail closes for repairs" is rejected; "…repairs near Glover Park neighbors" is kept.

### Events

| Source | Endpoint | Result |
|---|---|---|
| **GPCA meetings** | `https://gpcadc.org/feed/` | **Yes, parse the title.** "GPCA Meeting on November 3rd, 2026 at 7 pm via Zoom", "GPCA Meeting on Tuesday, September 8th at 7 pm at Stoddert Elementary School". Regex `GPCA Meeting on (?:\w+day,\s+)?([A-Z][a-z]+ \d{1,2})(?:st\|nd\|rd\|th)?(?:,\s*(\d{4}))?` and take the year from `pubDate` when it is absent. First Tuesday, 7 pm (none in Jun/Jul/Aug/Dec). Glover Park Day and the Art-n-Music Walk arrive as posts with the date in the title. Tribe API 404; `/events/feed/` 0. |
| **ANC 3B** | `https://anc3b.org/wp-json/wp/v2/posts?per_page=10&_fields=date,title,link,content` and `https://anc3b.org/wp-json/wp/v2/pages?slug=meeting-schedule&_fields=modified,content` (robots: `/wp-json/` is not disallowed) | **Yes, but read the caveat.** Posts alternate "<Month> 2026 Meeting" (announcement) and "<Month> 2026 Meeting Report". The announcement body gives the date without a year: "NEW DATE!! The next meeting of ANC 3B is on Thursday, November 5th at 7 pm via Zoom". The schedule page lists 2026 dates (second Thursday: … October 8, November 12, December 10, January 14, 2027) at Stoddert ES / Glover Park Community Center, 4001 Calvert St NW, or Zoom. **The November post overrides the schedule** (5 Nov, not 12 Nov), so prefer the post. **Caveat:** the commission disallows `/feed/` in robots.txt. The REST API is technically allowed, but they evidently don't want the feed scraped. Fetch at most daily, and consider asking anc3b first. Post bodies carry Zoom links, so never republish body text. |
| OANC | `https://oanc.dc.gov/rss.xml` | Today it carried "January 9, 2025, ANC 3B Public Meeting", a **stale repost** (posted 26 Oct 2026). Drop past dates. |
| Glover Park Main Street | — | No calendar feed (see News). |
| Farmers market | existing layer | **None inside ANC 3B.** Nearest: Rose Park (Georgetown, Wed). |
| Library / rec | link only | No DCPL branch in 3B. Nearest is Georgetown Neighborhood Library (3260 R St NW): `https://dclibrary.libnet.info/events?l=Georgetown%20Neighborhood%20Library`. Guy Mason Recreation Center (3600 Calvert St NW, 3B02) is DPR: link only. |

Suggested config:
- `ANCS["gloverpark"] = ["3B"]`.
- An `ANC_FEEDS`-style reader can't use anc3b's RSS (disallowed), so add a small WP-JSON reader. Otherwise use static links: ANC 3B meeting schedule, GPCA.

### Jobs

| Employer | Endpoint | Filter | robots | Verdict |
|---|---|---|---|---|
| **Georgetown University (Workday), 2115/2121 Wisconsin Ave** | `POST https://georgetown.wd1.myworkdayjobs.com/wday/cxs/georgetown/Georgetown_Admin_Careers/jobs`, `locations`: the IDs for descriptors `2115 Wisconsin Avenue`, `2115 Wisconsin Ave 3rd Floor`, `2115 Wisconsin Ave G1 Floor`, `2121 Wisconsin Avenue` (look up nightly) | **11 jobs, all SMD 3B02** (0.25 mi from 2400 Wisconsin). Samples, with `startDate` from the detail endpoint: "Chief of Staff & Director of Special Projects" (2026-10-30), "Director of AV Support" (2026-10-27), "Managing Director of Development, Lombardi Comprehensive Cancer Center" (2026-10-26). | allow (as in SOURCES-WEST) | **Use, "in".** This is exactly the set SOURCES-WEST excluded from Georgetown. |
| **AU (Workday), "3201 New Mexico Campus (Washington, DC)"** | AU tenant (already wired), facet `9fbb5efe5046102cdd3de7641bac0000` | 2 jobs ("Senior Payroll Specialist", 2026-10-13; "AU Ready Hire", 2026-06-23, an evergreen pool that `MAX_AGE_DAYS` will drop). 3201 New Mexico is SMD **3B06**. | allow | "in" with the whole-3B boundary; "nearby" (1.06 mi) with the GP-core boundary. |
| Georgetown Main Campus / Medical Center | same tenant | 48 / 21 jobs; 0.94 / 0.65 mi from 2400 Wisconsin | allow | Optional "nearby" under `NEARBY_CAP`. They already feed the Georgetown site. |
| solidcore "Cathedral Commons" | Lever | 3500 Wisconsin = 3A01 (outside); postings from 2020/2022 (evergreen) | allow | No. |

**ZIP:** none. 20007 is shared with Georgetown and the Palisades, and 20016 with Tenleytown.

## 3. PALISADES (SMDs 3D03–3D06; ANC 3D)

### News

| Feed (exact URL) | robots | items | MATCH / body / title | Mode / notes |
|---|---|---|---|---|
| **`https://palisadesdc.org/feed/`** (Palisades Citizens' Association) | allow | 10 (Nov 2025 – 13 Jun 2026) | 2 / 7 / 0 | **all.** PCA-only: "PCA Annual Meeting and Board of Directors Vote", "4th of July Parade Marching and Registration FAQs", "Linking Historical Maps of the Palisades…", "Get the Latest Issue of The Conduit!". Slow (nothing since June). The titles rarely say "Palisades", so don't match. |
| `https://wtop.com/tag/palisades/feed/` | allow | 7 (2013 – 4 Jul 2026) | 4 / 7 / 0 | **match**. "60th annual Fourth of July parade in the Palisades goes off without a hitch…" (Jul 2026), "DC police shoot, kill man… in Palisades" (Sep 2025). |
| `https://www.washingtonian.com/?s=palisades&feed=rss2&orderby=date&order=DESC` | allow | 10 (Dec 2025 – Sep 2026) | 1 / 8 / 0 | **match**. Kept: "A Subcontinent-Traversing Indian Restaurant Arrives in the Palisades" (11 Sep). The body hits are roundups (fireworks lists, Kennedy Center). |
| `https://wtop.com/tag/spring-valley/feed/` | allow | 10 (Feb 2022 – Feb 2025) | 4 / 9 / 0 | Only if you take the wider HPN boundary (Spring Valley munitions cleanup, "Piggly Wiggly mansion…"). Stale. |
| `https://thedcline.org/?s=palisades&feed=rss2&orderby=date&order=DESC` | allow | 20 (Nov 2021 – Mar 2024) | 6 / 6 / 1 | **search**; stale (newest Mar 2024). |
| `https://www.popville.com/feed/` p1–p5 | allow | 100 | 0 / 3 / 0 | Body-only (roundups). PoPville rarely covers the Palisades. |
| `https://foresthillsconnection.com/?s=palisades…` | allow | 10 (2019 – 2024) | 0 / 10 / 0 | Ward-3 roundups only. Skip. |

**Not usable:**
- **ANC 3D** `www.anc3d.org` is Wix; its `blog-feed.xml` is **stale** (newest 6 Apr 2022, 20 items) and robots disallows only `*?lightbox=`. `anc3d.dc.gov`: no DNS.
- Palisades Main Street: none found. The DC layer has a "The Palisades" corridor, but no website surfaced.
- `palisadesvillage.org`: no Tribe API.
- AU's *The Eagle* (`theeagleonline.com/feed/` 404; its `?s=` feed returns HTML).
- WTOP `/tag/pacific-palisades/` and `/tag/palisades-fire/`: 0 items.
- The Blade `?s=palisades`: body-only.

**Keyword rule (Palisades): strict.** Accept a bare "Palisades" only with a DC cue in the same item. Wire and national copy is dominated by Pacific Palisades (the LA fire), the Palisades nuclear plant (Covert Township, Michigan; restarted by Holtec), the NJ Palisades and Palisades Park NJ, and the Palisades Center mall (NY).
- TERMS:
  ```
  \b(the\s+)?palisades\b(?=.*\b(d\.?c\.?|NW|northwest|macarthur|ANC\s*3D|citizens|library|recreation|sibley|ward\s*3)\b)|\bmacarthur\s+(blvd|boulevard)\b|\bANC\s*3D\b|\bdalecarlia\b|\bbattery\s+kemble\b|\bsibley\s+(memorial\s+)?hospital\b|\bspring\s+valley\b(?=.*\b(d\.?c\.?|NW|american\s+university|munitions|chemical|army\s+corps|ANC)\b)|\bwesley\s+heights\b|\bfoxhall\b|\bchain\s+bridge\s+r(oa)?d\b
  ```
  (flags `re.I | re.S`)
- NOT_HERE[0] (reject):
  ```
  \bpacific\s+palisades\b|\bpalisades\s+(fire|nuclear|power\s+plant|plant|interstate|parkway|center|tahoe|charter|park,?\s+(n\.?j|new\s+jersey)|village\s+(mall|shopping))\b|\bnew\s+jersey\b|\bhudson\s+river\b|\bmichigan\b|\blos\s+angeles\b|\bcalifornia\b|\bmalibu\b|\bholtec\b|\bentergy\b|\bcovert\s+township\b|\bfort\s+lee\b|\bnyack\b
  ```
- NOT_HERE[1] (rescue):
  ```
  \bmacarthur\s+(blvd|boulevard)\b|\bANC\s*3D\b|\bpalisades\s+(citizens|library|neighborhood\s+library|recreation|rec\b|farmers|parade|4th|fourth|main\s+street)|\bdalecarlia\b|\bsibley\b|\b(d\.?c\.?|NW)\b(?!-area)
  ```
- Notes:
  - "Palisades Village" is ambiguous: it is the DC aging-in-place nonprofit, and also Rick Caruso's shopping centre in Pacific Palisades. Not used as a term.
  - Drop `spring valley`, `wesley heights` and `foxhall` from TERMS if you keep the narrow SMD boundary. They are ANC 3D but not the Palisades proper.
  - `\bmichigan\b` in the reject list hits "Michigan Ave" (a DC street, in Brookland). That's harmless here because no Palisades story names it, and the DC rescue covers it.
  - Synthetic checks (no out-of-area items appeared in today's feeds):
    - Rejected: "Pacific Palisades residents return…", "Holtec restarts Palisades nuclear plant in Michigan", "Palisades Park, N.J., council…".
    - Kept: "Palisades Fourth of July parade returns to MacArthur Boulevard", "…the Palisades in Northwest DC; residents also recall the Pacific Palisades fire" (rescued by NW).

### Events

| Source | Endpoint | Result |
|---|---|---|
| **Palisades Citizens' Association** | `GET https://palisadesdc.org/wp-json/tribe/events/v1/events?per_page=50` (robots allow; WordPress 7.1, The Events Calendar). Also `https://palisadesdc.org/events/feed/` (10 items). | **Yes.** Right now all 53 upcoming are "Palisades Farmer's Market" (Sundays 9:00; no venue), which duplicates the market layer, so drop that title. With `start_date=2026-01-01` the 2026 history shows the real community calendar: "PCA Board Meeting" (monthly, 2nd Wed), "PCA Town Hall", "St. Paddy's Street Party", "Eggstravaganza", "Pride Street Party", "Hoedown on the Green" (3 Jul), "4th of July Parade & Picnic", "Fabric Recycling with Helpsy". Expect those to reappear as dates are posted. |
| ANC 3D | `www.anc3d.org` (Wix) | **No machine-readable source.** Meeting pages are Wix HTML (`/2026-meetings` 404s; navigation is "RECENT MEETINGS / 2026 MEETINGS"). Use OANC filtered on `ANC 3D` (none in today's 10) plus a static link. |
| Farmers markets (existing layer) | — | **Palisades Farmers Market**, MacArthur Blvd & 48th Pl NW, Sundays 9–1 (3D05, inside). **Arcadia Mobile Market at Sibley Hospital**, 5522 Loughboro Rd NW, 2nd & 4th Tuesdays (3D03, inside). |
| Library / rec | link only | **Palisades Neighborhood Library** (4901 V St NW, 3D05, inside): `https://dclibrary.libnet.info/events?l=Palisades%20Neighborhood%20Library`. Palisades Recreation Center (5200 Sherier Pl NW, 3D05): DPR link. |

Suggested config:
- `ANCS["palisades"] = ["3D"]`.
- `CALENDARS["palisades"] = ["pca"]`: the Tribe reader, skipping titles matching `farmer'?s market`.

### Jobs

| Employer | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| Sibley Memorial Hospital (5255 Loughboro Rd, 3D03) | `jobs.hopkinsmedicine.org/sibley-memorial-hospital` (Johns Hopkins Medicine's Radancy/TMP site) | the obvious big employer | robots allows the job pages but disallows `/feeds/`; `Crawl-delay: 2` | **Not an allowed platform** (no Workday/Greenhouse/Lever). Excluded. |
| AU (Workday), "3201 New Mexico Campus" / "Main Campus" / "Spring Valley Campus" | AU tenant (already wired) | 2 / 70 / 6 jobs; 1.23 / 1.54 / 1.9 mi from 4865 MacArthur | allow | Optional "nearby" (cap). Thin relevance; I'd include only 3201 New Mexico, if anything. |
| Georgetown Main Campus | Georgetown tenant | 1.43 mi | allow | Optional "nearby"; same caveat. |
| Safeway (4865 MacArthur), Palisades restaurants | — | Safeway terms unverified (as before) | — | No verified feed. |

**ZIP:** none. 20016 is Tenleytown's, and 20007 is shared with Georgetown and Glover Park. The Palisades straddles both.

**Expect 0 "in" jobs** on most nights unless Sibley moves to an allowed platform.

## 4. VAN NESS (ANC 3F, `SMD_ID LIKE '3F%'`)

### News

| Feed (exact URL) | robots | items | MATCH / body / title | Mode / notes |
|---|---|---|---|---|
| **`https://foresthillsconnection.com/feed/`** (already used for Tenleytown, Cleveland Park and Chevy Chase) | allow | 10 (1–27 Oct 2026) | 5 / 7 / 4 | **match.** FHC is the Van Ness / Forest Hills / North Cleveland Park paper: "Meet the ANC 3F candidates: Carlos Silva, 3F06", "ANC 3F Oct. 26 agenda: ANC candidates and plans for this intersection's first sidewalks", "…traces of their lives in the Soapstone Valley". Arguably **all**, but it also runs Ward 3-wide items ("DC residents could not always choose…", body-only). |
| **`https://foresthillsconnection.com/?s=van+ness&feed=rss2&orderby=date&order=DESC`** | allow | 10 (24 Sep – 21 Oct 2026) | 9 / 10 / 7 | **search.** "Van Ness neighbors have gathered for this holiday for a quarter century" (8 Oct). Overlaps the main feed; dedupe by link. |
| `https://anc3f.dc.gov/rss.xml` (ANC 3F, Drupal) | allow | 10 | 10 / 10 / 10 | **all** (it is a meeting feed; see Events). Little news. |
| `https://wtop.com/tag/van-ness/feed/` | allow | 10 (Sep 2019 – 5 May 2026) | 7 / 10 / 1 | **match**. Slow: "Neighborhood violence in Van Ness sparks discussion at ANC meeting", "Police find UDC cruiser stolen…". |
| `https://wtop.com/tag/university-of-the-district-of-columbia/feed/` (= `/tag/udc/`) | allow | 10 (Nov 2023 – Feb 2026) | 2 / 3 / 0 with the final rule | Mostly campus-wide UDC news ("UDC pushing to add educators…", a Ward 7/8 cyber hub), which the rule drops; it kept only the 2023 stolen-UDC-cruiser stories. **Skip**: UDC also has Backus and Lamond-Riggs campuses. |
| `https://ddot.dc.gov/rss.xml` (SHARED) | allow | 10 | 1 / 1 / 1 | "ANC 3F Public Meeting [VIRTUAL]" (21 Oct). |
| `https://www.popville.com/feed/` p1–p5 | allow | 100 | 0 | PoPville rarely covers Van Ness. |
| `https://mayor.dc.gov/rss.xml` | allow | 10 | 0 with the final rule (3 under an earlier draft that matched any "University of the District of Columbia") | Budget releases naming UDC; not neighbourhood news. |

**Not usable:**
- **Van Ness Main Street** `vannessmainstreet.org/feed/` has 1 item ("Hello world!", Nov 2025). Elementor site; events are Eventbrite links (below).
- ANC 3F's Wix site `www.anc3f.com` has no feed.
- Washingtonian `?s=van+ness` is not a phrase search: 10 unrelated items, 0 hits. The DC Line `?s=van+ness` is likewise unrelated. Washington City Paper `?s=` returns 0 items. The Blade `?s=van+ness`: 0.
- WTOP `/tag/forest-hills/feed/`: 0 items.

**Keyword rule (Van Ness).**
- TERMS:
  ```
  \bvan\s+ness\b(?=.*\b(d\.?c\.?|NW|connecticut|UDC|university\s+of\s+the\s+district|metro|forest\s+hills|ANC|main\s+street|neighbo)\b)|\bvan\s+ness[-\s/]+udc\b|\bANC\s*3F\b|\bforest\s+hills\s+(of\s+d\.?c|playground|neighborhood|park|DC)\b|\bnorth\s+cleveland\s+park\b|\bsoapstone\s+valley\b|\binternational\s+(chancery\s+)?cent(er|re)\b(?=.*\bvan\s+ness\b)|\b(university\s+of\s+the\s+district\s+of\s+columbia|UDC)\b(?=.*\b(connecticut\s+ave|van\s+ness|4200\s+connecticut)\b)
  ```
  (flags `re.I | re.S`)
- NOT_HERE[0] (reject):
  ```
  \bjonathan\s+van\s+ness\b|\bJVN\b|\bqueer\s+eye\b|\bsan\s+francisco\b|\bvan\s+ness\s+ave(nue)?\b|\bS\.F\.|\bforest\s+hills,?\s+(queens|n\.?y|new\s+york)\b|\bus\s+open\b|\bwest\s+side\s+tennis\b
  ```
- NOT_HERE[1] (rescue):
  ```
  \bconnecticut\s+ave|\bANC\s*3F\b|\bUDC\b|\bvan\s+ness\s+(st(reet)?|metro|station|main\s+street)\b|\bNW\b|\bforest\s+hills\s+connection\b
  ```
- Notes:
  - **Do not put "Forest Hills Connection" in TERMS.** Every FHC item carries the outlet name in its summary ("…appeared first on Forest Hills Connection"), so an earlier draft matched 10/10 of everything FHC publishes.
  - **Do not match bare "UDC" or "University of the District of Columbia"**: it lets through Ward 7/8 campus news.
  - DC has a Van Ness *Street*, never an Avenue, so `van ness ave` is a safe San Francisco reject.
  - Jonathan Van Ness (Queer Eye) is the realistic collision in the Blade and entertainment copy.
  - "Forest Hills" alone is Queens (and the old US Open venue), so it needs a DC suffix.
  - Synthetic checks: "Jonathan Van Ness launches new Queer Eye season", "…Van Ness Avenue in San Francisco", "UDC enrollment climbs 8 percent" and "US Open history at Forest Hills, Queens" are all rejected. "Neighborhood violence in Van Ness sparks discussion at ANC meeting" and "New cafe opens near the Van Ness-UDC Metro" are kept.

### Events

| Source | Endpoint | Result |
|---|---|---|
| **ANC 3F** | `https://anc3f.dc.gov/rss.xml` | **Yes, parse the title.** The titles fit `events.py`'s `OANC_TITLE` exactly: "September 15, 2026, ANC 3F Public Meeting", "August 4, 2026, ANC 3F Special Public Meeting". The description also has "Date and Time Tue, Sep 15 2026, 6 - 7pm". **Watch out:** 8 of the 10 items are 2022–23 meetings re-posted on 27 Mar 2026 ("September 20, 2022, ANC 3F Public Meeting"), so drop past dates. The 26 Oct 2026 meeting (per FHC's agenda story) **never appeared** in this feed, so it lags. FHC's "ANC 3F <date> agenda" posts are a useful backup. Meeting days vary (Tue 15 Sep, Mon 26 Oct), so don't infer a fixed schedule. Feed it to the OANC reader as `ANC_FEEDS`-style. |
| **UDC events (25Live Publisher)** | `GET https://25livepub.collegenet.com/calendars/udc-events-2.ics` (also `.rss`). The calendar is linked from udc.edu's home page. robots: `User-agent: * / Disallow:` (allow all). | **Yes, iCal, but filter hard.** 191 events from 1 Nov 2026 to Mar 2028. Each VEVENT has `GEO` (38.943695;-77.063625 = the Van Ness campus), `CATEGORIES` (e.g. "Student Events Calendar") and `X-TRUMBA-CUSTOMFIELD;NAME="Event Type"` ("Social" …). Much of it is internal: "DC Board of Elections General 2026" (Heritage Hall polling site), "Chess Club Sessions", "Afrobics Fitness Class", "Winter Break (University Closed)", "UDCMI Model Practice". Some items are other campuses ("Ward 8 Healthcare Council Meeting"). Keep events whose GEO is inside the boundary and whose title doesn't match `hold\|practice\|class\|club\|closed\|meeting\|registration\|orientation`. Good keepers: "UDC Homecoming", "2nd Annual Quantum Conference", "Mid-term election debrief w/ Maya Wiley", "CAUSES Farmer's Market". |
| Van Ness Main Street | `https://vannessmainstreet.org/events/` | **No.** Elementor page with Eventbrite links (`eventbrite.com/e/1989621105285…` etc.). Eventbrite's API needs an OAuth token (not tested), and Tribe returns 404. Static link. Signature events: Art All Night (Sep), Octoberfest, Artisan Pop-Up, Spooktacular, Holiday Pop-Up (4340 Conn). |
| Forest Hills Connection calendar | `foresthillsconnection.com` | **No.** The old `/event/` URLs are from a retired Tribe install; Tribe API 404; post types are Elementor/Jetpack only. |
| Levine Music (2801 Upton St NW) | `levinemusic.org` | **robots.txt 403 to our UA.** Excluded. |
| Hillwood (Forest Hills) | — | 403 to our UA (per SOURCES-WEST). Excluded. |
| Politics & Prose (5015 Conn, 3F06) | Tribe 404 | Its job pages were 403 before; no events feed found. |
| Farmers markets (existing layer) | — | **UDC Van Ness Farmers Market**, 4200 Connecticut Ave, Saturdays 9–1 (3F05). **New Morning Farm at Sheridan School**, 4400 36th St NW (3F01; Sat, plus Tue Jun–Sep). Both are also inside the Tenleytown HPN. |
| Library | link only | No DCPL branch in 3F. Link Cleveland Park (3310 Connecticut Ave NW) and Tenley-Friendship: `https://dclibrary.libnet.info/events?l=Cleveland%20Park%20Neighborhood%20Library`. |

Suggested config:
- `ANCS["vanness"] = ["3F"]`.
- `ANC_FEEDS`-style source `https://anc3f.dc.gov/rss.xml`, using `OANC_TITLE` and not `AGENDA`.
- `CALENDARS["vanness"] = ["udc25live"]`.

### Jobs

| Employer | Endpoint | Fit | robots | Verdict |
|---|---|---|---|---|
| **AU (Workday), "4401 Connecticut Campus (Washington, DC)"** | AU tenant (already wired), facet `9fbb5efe5046102cdd3de15d184d0000` | **6 jobs**; 4401 Conn = SMD 3F03, Van Ness Main Street polygon. Samples: "Senior Administrative Assistant" (2026-10-26), "Senior Director of Executive Engagement" (2026-10-14), "1A Plus Podcast Producer (Producer I)" (2026-10-07; WAMU is at 4401 Conn). | allow | **Use, "in".** Tenleytown already lists this campus as "nearby". |
| AU Tenley Campus (4300 Nebraska) | same | 8 jobs, 0.83 mi | allow | Optional "nearby". |
| UDC | ApplicantStack (`udc.applicantstack.com/x/openings`) | the area's biggest employer | robots allows `/x/openings` | **Not an allowed platform.** Excluded; consider proposing it as a platform addition (simple public list pages). |
| Howard University School of Law (2900 Van Ness St, 3F05) | Greenhouse slug `howarduniversity` exists with **0 jobs** | — | allow | Nothing today. |
| Intelsat, embassies (International Chancery Center) | — | — | — | No verified feed. |

**ZIP:** none. 20008 is shared with Cleveland Park and Woodley Park, and 20016 with Tenleytown.

## 5. HISTORY (Evening Star via loc.gov, week of 1926-10-31 to 11-06)

loc.gov answered normally (robots allow; no 403), at roughly 30–60 s per query. Query shape is the same as `history.py` (`q`, `dates`, `fa=partof_title:evening star (washington, d.c.) 1854-1972`, `fo=json`), run through `history.get_json`. "Week" is the number of pages hit in 1926-10-31 → 11-06; "Oct–Nov" is 1926-10-01 → 11-30. I read OCR text for up to 3 pages per term. **The run was stopped early at the lead's request:** the four remaining Van Ness terms (`"Van Ness street"`, `"Forest Hills"`, `"Connecticut avenue extended"`, `"Tilden street"`) and `"North Cleveland Park"` were **not tested**.

### Brookland

| Term | Week | Oct–Nov | What the snippets show |
|---|---|---|---|
| `Brookland` | 34 | 285 | **DC in every sample.** Mostly rent and sale classifieds ("Brookland. 3317 10th st.—Detached. 6 rooms…", "2703 12th St., Brookland"). There are also school-board personnel lists naming staff "Brookland School", which `NAME_LIST`/`LEGAL` should screen out. The football copy says "at Brookland" for CUA games. |
| `"Brookland Citizens"` | 1 | 3 | "The Brookland Citizens' Association will meet at the Masonic Temple, Twelfth and Monroe streets…" (6 Nov). Rare but ideal. |
| `"Catholic University"` | 25 | 170 | **Mostly football** (vs. Blue Ridge College at the CUA stadium, 6 Nov), plus campus religious news (the Feast of Christ the King, mass "in the crypt of the national shrine"). Needs a sports reject, as with Georgetown. |
| `"Michigan Park"` | 6 | 26 | Michigan Park Citizens' Association (school and PTA items) and real-estate ads ("MICHIGAN PARK 4204 12th Place N.E."). It is just north of the boundary (5A/5B01); use it only as a booster. |
| `"Monroe street northeast"` | 2 | 16 | John Burroughs School addition (18th–20th Sts, east of the core); a children's-contest list with home addresses. Low value. |
| `"Twelfth street northeast"` | 1 | 11 | Too rare. |
| `"Franciscan Monastery"` | 0 | 17 | Quiet this week. |

**Recommended Brookland config:**
- `terms` (most reliable first): `"Brookland"`, `'"Brookland Citizens"'`, `'"Catholic University"'`
- `pattern`:
  ```
  brookland|catholic\s+univ|franciscan\s+monastery|national\s+shrine|turkey\s+thicket
  ```
- Clip reject (sports):
  ```
  foot\s*ball|eleven|gridiron|touchdown|varsity|coach|quarterback|basket\s*ball|blue\s+ridge|stadium
  ```
- `local`:
  ```
  12th\s+st|twelfth|monroe\s+st|newton\s+st|otis\s+st|quincy|rhode\s+island\s+av|michigan\s+av|10th\s+st|n\.\s?e\.|northeast|citizens.\s+association|masonic\s+temple
  ```
- Expect 5–10 clips a week, mostly real estate.

### Glover Park

| Term | Week | Oct–Nov | Snippets |
|---|---|---|---|
| `"Glover Park"` | 4 | 42 | **The subdivision was new in 1926**: "Beautifully Designed Homes of English Type in GLOVER PARK" and "GLOVER PARK. A Graver subdivision of English type homes" (both real-estate ads). Also a hiking-club note: "going through Glover Park" (from Wisconsin and Massachusetts avenues). That one may mean the parkland, now Glover-Archbold, rather than the subdivision. Both are local, so accept. |
| `"Tunlaw road"` | 1 | 8 | A Cathedral Heights Citizens' Association resolution asking for "a sidewalk along Cathedral avenue from Massachusetts avenue to Tunlaw road". Good civic item. |
| `"Whitehaven"` / `"Glover-Archbold"` | 0 / 0 | 1 / 0 | Too rare. (Glover-Archbold Park was named later.) |

**Recommended Glover Park config:**
- `terms`: `'"Glover Park"'`, `'"Tunlaw road"'`, `'"Cathedral Heights"'`
- I did not count `"Cathedral Heights"` on its own; it appeared in the Tunlaw and Wesley Heights snippets ("Cathedral Heights Citizens' Association… at the Wesley Heights clubhouse"). **Unverified as a standalone term.**
- `pattern`:
  ```
  glover\s+park|tunlaw|cathedral\s+heights\s+citizens|observatory\s+(hill|circle)
  ```
- `local`:
  ```
  wisconsin\s+av|tunlaw|cathedral\s+av|calvert\s+st|39th|37th|38th|new\s+mexico\s+av|n\.\s?w\.|citizens
  ```
- Expect 2–5 clips a week, mostly ads.

### Palisades

| Term | Week | Oct–Nov | Snippets |
|---|---|---|---|
| `"Conduit road"` | 8 | 57 | **The 1926 name of MacArthur Blvd, and the best term.** "Conduit Road School — Playground too small" (school-inspection list), "Reservoir Center, Conduit road near the reservoir" (community-centre schedule), park and street changes "in the vicinity of Conduit road". |
| `"Chain Bridge"` | 3 | 42 | Mixed: hiking-club walks and apple-stand ads "Cross Chain Bridge to Va.", which are Virginia-side. Also "Chain Bridge Road School" (DC, local). Needs `chain\s+bridge\s+road` or a DC cue. |
| `Palisades` | 0 | 14 | Quiet this week. Expect NJ/Hudson Palisades usage in other weeks; the "Palisades of the Potomac" was the DC subdivision. |
| `"Wesley Heights"` | 1 | 11 | Cathedral Heights Citizens' Association meeting "at the Wesley Heights clubhouse". That is ANC 3D but outside the recommended Palisades SMDs. |
| `"Spring Valley"` / `"Little Falls"` | 0 / 0 | 0 / 1 | Too rare. |

**Recommended Palisades config:**
- `terms`: `'"Conduit road"'`, `'"Chain Bridge"'`, `"Palisades"`
- `pattern`:
  ```
  conduit\s+r(oa)?d|chain\s+bridge\s+r(oa)?d|palisades\s+of\s+the\s+potomac|palisades(?=.{0,200}(conduit|d\.\s?c|n\.\s?w|potomac|reservoir))
  ```
- Clip reject:
  ```
  hudson|new\s+jersey|n\.\s?j\.|palisades\s+(interstate|park,?\s+n)|cross\s+chain\s+bridge\s+to\s+va|virginia\s+side
  ```
- `local`:
  ```
  conduit|reservoir|potomac|canal|chain\s+bridge\s+road|foxhall|arizona\s+av|macarthur|dalecarlia|n\.\s?w\.
  ```
- Expect 2–6 clips a week.

### Van Ness

| Term | Week | Oct–Nov | Snippets |
|---|---|---|---|
| `"Bureau of Standards"` | 11 | 100 | **The National Bureau of Standards occupied the future UDC/Van Ness site** (Connecticut Ave & Van Ness St) from 1901 to the 1960s. The week's hits include real-estate ads ("NEAR BUREAU OF STANDARDS… within two squares of the Bureau of Standards") and, presumably, the Bureau's own science news. That news is national rather than neighbourhood; I sampled only the ads. |
| `"Van Ness street"`, `"Forest Hills"`, `"Connecticut avenue extended"`, `"Tilden street"`, `"North Cleveland Park"` | **not tested** | — | Run stopped. SOURCES-WEST found "NORTH CLEVELAND PARK … 38th and Veazey Streets" ads in this week, which are Van Ness/Wakefield, so `"North Cleveland Park"` is very likely productive. |

**Provisional Van Ness config (verify before enabling):**
- `terms`: `'"Bureau of Standards"'`, `'"North Cleveland Park"'`, `'"Van Ness street"'`, `'"Forest Hills"'`
- `pattern`:
  ```
  bureau\s+of\s+standards(?=.{0,200}(near|squares|connecticut|van\s+ness|home|house|lot))|north\s+cleveland\s+park|van\s+ness\s+st|forest\s+hills(?=.{0,200}(connecticut|d\.\s?c|n\.\s?w|chevy\s+chase|rock\s+creek))
  ```
- Clip reject: `forest\s+hills,?\s+(l\.\s?i|long\s+island|n\.\s?y|queens)|tennis` ("Forest Hills" in 1926 sports copy is the West Side Tennis Club in Queens).
- `local`:
  ```
  connecticut\s+av|van\s+ness|veazey|upton|tilden|yuma|albemarle|windom|38th|36th|reno\s+road|soapstone|n\.\s?w\.
  ```

## Not verified / excluded (summary)

- **Robots-disallowed for our agent:** `anc3b.org/feed/` (its WP REST API is allowed; see the Glover Park caveat); `levinemusic.org` (robots.txt returns 403); `brooklandcivic.org` with any query string (`/*?`) and its calendar/iCal action paths.
- **403 to our UA (known, not retried):** hillwoodmuseum.org, politics-prose.com job pages, MedStar.
- **Not allowed platforms:** iCIMS (Catholic University), ApplicantStack (UDC), Radancy/TMP (Sibley / Johns Hopkins Medicine), Eventbrite (Van Ness Main Street; API needs a token).
- **No machine-readable source:** ANC 5B and 5F (Google Sites), ANC 3D (Wix; blog feed stale since Apr 2022), ANC 3F's Wix site (use anc3f.dc.gov), Catholic University's Drupal calendar, Monroe Street Market (stale since Jan 2024), Glover Park Main Street (feed stale since Aug 2020), Forest Hills Connection calendar.
- **No DNS:** `anc3b.dc.gov`, `anc3d.dc.gov`, `anc5a.dc.gov`, `anc5b.dc.gov`, `anc5f.dc.gov`, `brooklandmainstreet.org`, `thetowerdc.com`.
- **History, not tested (run stopped early):** the Van Ness terms `"Van Ness street"`, `"Forest Hills"`, `"Connecticut avenue extended"`, `"Tilden street"` and `"North Cleveland Park"`, plus `"Cathedral Heights"` as a standalone Glover Park term. The Van Ness archive config is provisional.
- **Not tested:** Eventbrite's API for Van Ness Main Street; `discover.gloverparkmainstreet.org`; Smithsonian/NPS calendars; DPR rec-centre calendars (DPR's feed is stale, as noted before).
- **Overlap to decide before launch:** Van Ness's core (3F05, 3F01, half of 3F04) is inside the live Tenleytown HPN, so UDC, the Van Ness Metro and the UDC farmers market will appear on both sites.
- **Synthetic-only precision tests:** today's feeds contained no Pacific Palisades, Palisades nuclear plant, San Francisco Van Ness or Jonathan Van Ness items, so those rejections were checked on constructed headlines (22 cases, 0 errors), not on live items.
