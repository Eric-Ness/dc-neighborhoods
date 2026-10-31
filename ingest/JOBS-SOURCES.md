# "Jobs nearby" sources for Petworth and Tenleytown

Research date: 2026-10-31. Every endpoint below was requested live with
`User-Agent: dc-neighborhoods-ingest/0.1 (+https://petworth.org)`. Fields we would show:
title, employer, location, posted date, link.

## Bottom line

- **Tenleytown has usable volume**: American University (Tenley Campus about 8 jobs; all AU DC campuses about 97, all within roughly 1.3 mi) and Children's National's Friendship Heights practice (1 to 3 jobs).
- **Petworth is thin.** The only employer physically in Petworth with a clean machine-readable feed is the Safeway at 3830 Georgia Ave NW, and that is "conditional" (see below). It had 1 job on the test date. Children's National Columbia Heights (2 jobs, about 1 mi) is the nearest clean source. Expect 0 to 5 Petworth listings on a typical night.
- **No API keys needed for anything that qualifies.** USAJOBS needs a free key, but it is on the conditional list because its robots.txt disallows everything.
- The DC government, DCPS, DPR and DC Public Library postings (the most "local" jobs) are not available in any machine-readable form, so they are rejected.

---

## Qualifying sources

### 1. American University on Workday (Tenleytown)

- **Endpoint (list):** `POST https://american.wd1.myworkdayjobs.com/wday/cxs/american/AU/jobs`
  - Body: `{"appliedFacets":{"locations":["<id>"]},"limit":20,"offset":0,"searchText":""}`, with `Content-Type: application/json`. Page with `offset`; the maximum `limit` is 20.
- **Endpoint (detail, for exact posted date):** `GET https://american.wd1.myworkdayjobs.com/wday/cxs/american/AU<externalPath>`
  - It returns `jobPostingInfo.startDate` (ISO date, e.g. `2026-10-31`), `location` and `externalUrl`. The list endpoint only gives relative dates such as "Posted 3 Days Ago".
- **Auth:** none.
- **Caveat:** this is Workday's undocumented JSON API that the careers page itself calls. It is public and stable across thousands of tenants, but it is not a documented, versioned API.
- **Filter.** The `locations` facet IDs, all DC (taken from the facet list in the response):

  | Campus | Facet ID | Open jobs | Distance |
  |---|---|---|---|
  | Tenley Campus (4300 Nebraska Ave NW) | `9fbb5efe5046102cdd3ded698cfc0000` | 8 | In Tenleytown |
  | Main Campus (4400 Massachusetts Ave NW) | `9fbb5efe5046102cdd3df8d993c60000` | 73 | About 0.8 mi |
  | 4401 Connecticut Campus (Van Ness) | `9fbb5efe5046102cdd3de15d184d0000` | 7 | About 0.9 mi |
  | Spring Valley Campus | `9fbb5efe5046102cdd3e044a563e0000` | 6 | About 1 mi |
  | East Campus | `9fbb5efe5046102cdd3df2d4597a0000` | 2 | About 0.7 mi |
  | 3201 New Mexico Campus | `9fbb5efe5046102cdd3de7641bac0000` | 2 | About 1.3 mi |

  Recommendation: use Tenley Campus as "in Tenleytown". Add the other campuses either as "nearby" or with a cap (the newest N), because about half the postings are adjunct or student jobs.
  - Petworth: none (AU has no Petworth sites).
- **Sample, Tenleytown (Tenley Campus):**
  - Practitioner-In-Residence | American University | Tenley Campus (Washington, DC) | Posted about 2026-10-28 | https://american.wd1.myworkdayjobs.com/AU/job/Tenley-Campus-Washington-DC/Practitioner-In-Residence_R5134
  - Legal Education Advisor | American University | Tenley Campus | Posted about 2026-10-22 | https://american.wd1.myworkdayjobs.com/AU/job/Tenley-Campus-Washington-DC/Legal-Education-Advisor_R5104
  - Circulation Manager | American University | Tenley Campus | Posted about 2026-10-21 | https://american.wd1.myworkdayjobs.com/AU/job/Tenley-Campus-Washington-DC/Circulation-Manager_R5092
  - Main Campus examples, with exact dates from the detail endpoint: Academic Program Assistant (2026-10-31); Merit Awards Program Coordinator (2026-10-30).
- **robots.txt** (`https://american.wd1.myworkdayjobs.com/robots.txt`):
  ```
  User-agent: *
  Allow: /AU/
  Disallow: /refreshFacet/
  ```
  `/wday/cxs/` is not disallowed, so it is allowed by default.
- **ToS:** Workday career sites carry no site terms of their own. AU publishes no website terms-of-use page; only its Data Privacy Notice and a web-content policy turned up, and neither prohibits automated access. No prohibition was found.
- **Volume:** 8 jobs at Tenley Campus; 97 across all AU DC campuses. AU posts several new jobs a week.

### 2. Children's National Hospital on Workday (Friendship Heights for Tenleytown; Columbia Heights near Petworth)

- **Endpoint (list):** `POST https://childrensnational.wd108.myworkdayjobs.com/wday/cxs/childrensnational/CN_Careers/jobs`, using the same body format as AU.
- **Endpoint (detail):** `GET https://childrensnational.wd108.myworkdayjobs.com/wday/cxs/childrensnational/CN_Careers<externalPath>`. It returns `startDate`, `location` and `externalUrl`.
- **Auth:** none. The same undocumented-Workday-API caveat applies.
- **Filter.** `locations` facet IDs:

  | Location | Facet ID | Open jobs |
  |---|---|---|
  | Friendship Heights (Tenleytown) | `8788a69939e31000c3973f7517460000` | 3 |
  | Columbia Heights (about 1 mi south of Petworth) | `8788a69939e31000c397793ee6910000` | 2 |
  | Main Campus, 111 Michigan Ave NW (about 1.2 mi from Petworth) | `8788a69939e31000c397cf5867be0000` | 265 |
  | Shepherd Park & Rare Disease Institute (about 2 mi north of Petworth) | `8788a69939e31000c397bfb758b40000` | 5 |

  Caveat: a multi-location posting can match the Friendship Heights facet even when its primary `location` is Main Campus; 2 of the 3 Friendship Heights hits are like this. Keep only jobs whose detail `location` equals the target site. Do not use Main Campus as "Petworth": it is too far and would flood the list.
- **Sample, Tenleytown:**
  - Ambulatory Patient Care Tech, Friendship Heights, Part-time | Children's National Hospital | Friendship Heights | 2026-08-10 | https://childrensnational.wd108.myworkdayjobs.com/CN_Careers/job/Friendship-Heights/Ambulatory-Patient-Care-Tech---Friendship-Heights---Part-time--8-hours-a-week-_R-000891
- **Sample, Petworth (nearby, Columbia Heights):**
  - Pediatrician (CA) Primary Care Columbia Heights (PRN) | Children's National Hospital | Columbia Heights | 2026-09-25 | https://childrensnational.wd108.myworkdayjobs.com/CN_Careers/job/Columbia-Heights/Pediatrician--CA--Primary-Care-Columbia-Heights--PRN-_R-000581
  - LPN II, Primary Care Columbia Heights | Children's National Hospital | Columbia Heights | 2026-08-12 | https://childrensnational.wd108.myworkdayjobs.com/CN_Careers/job/Columbia-Heights/LPN-II---Primary-Care-Columbia-Heights_R-000920
- **robots.txt** (`https://childrensnational.wd108.myworkdayjobs.com/robots.txt`):
  ```
  User-agent: *
  Allow: /HSCSN_Careers/
  Allow: /CN_Careers/ ...
  ```
  `/wday/cxs/` is not disallowed.
- **ToS:** https://www.childrensnational.org/about-us/terms-of-use has no clause on robots, spiders, scraping or crawling. I searched the page text for robot, spider, scrap, automated, data mining and crawl.
- **Volume:** 1 job at Friendship Heights and 2 at Columbia Heights.
- **To confirm:** the street address of the Friendship Heights practice (likely Wisconsin Ave NW, DC side). The API gives only the site name.

### 3. Greenhouse and Lever public job-board APIs (generic; no local hits yet)

- **Endpoints:**
  - `GET https://boards-api.greenhouse.io/v1/boards/<token>/jobs`
  - `GET https://api.lever.co/v0/postings/<company>?mode=json`
- Both are documented public APIs with no key. Greenhouse jobs include `location.name`, `updated_at` and `absolute_url`. Lever postings include `categories.location`, `createdAt` and `hostedUrl`.
- **robots.txt:**
  - `boards-api.greenhouse.io`: `User-agent: *` / `Disallow: /embed/`. `/v1/` is allowed.
  - `api.lever.co`: `User-agent: *` / `Allow: /` / `Crawl-delay: 1`. Sleep 1 second between calls.
- **ToS:** both platforms publish these endpoints specifically so third parties can display the jobs.
- **Local employers found:** I probed about 30 likely slugs, covering charter schools (E.L. Haynes, Capital City, Center City, KIPP DC, Washington Latin, DCIS), Sidwell, GDS, UDC, Wesley, WAMU, CAVA, &pizza, Compass Coffee and Call Your Mother. None of them uses Greenhouse or Lever. Only `sweetgreen` (Greenhouse, 67 jobs, full street addresses) is relevant to DC. Today it has DC jobs only at 601 Massachusetts Ave NW and an unspecified DC location; none are in either neighborhood.
- **Use:** a cheap "watch list": fetch sweetgreen and filter `location.name` by zip 20011, 20015 or 20016 or by street. Add more employers as they are discovered.
- **Volume:** 0 today.

---

## Conditional (technically workable; needs the owner's call)

### A. Safeway / Albertsons on Oracle Recruiting Cloud (the only in-Petworth source)

- **Endpoint (tested):**
  ```
  GET https://eofd.fa.us6.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.workLocation&finder=findReqs;siteNumber=CX_1001,locationId=300000002781168,limit=100,sortBy=POSTING_DATES_DESC
  ```
  - `locationId=300000002781168` is Washington, DC; this request returned 20 jobs.
  - Each item's `workLocation[0]` has `AddressLine1`, `PostalCode`, `Latitude` and `Longitude`, so filtering by zip or distance is exact. `PostedDate` is given.
  - The public link format is `https://jobs.albertsons.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/<Id>`.
- **Auth:** none.
- **Filter:**
  - Petworth: `PostalCode == 20011`. The store is 3830 Georgia Ave NW.
  - Tenleytown: `PostalCode in (20016, 20015)`. The store is 4203 Davenport St NW; it had no openings today. Or filter by distance from the coordinates.
- **Sample, Petworth:**
  - Pharmacy Technician | Safeway | 3830 Georgia Ave NW, 20011 | 2026-10-26 | requisition 785868
- **Sample, Tenleytown:** none today. The nearest is Front End Entry Level at 1855 Wisconsin Ave NW, 20007 (Glover Park), posted 2026-10-08.
- **robots.txt:** `https://eofd.fa.us6.oraclecloud.com/robots.txt` returns 404 (no restrictions). `https://jobs.albertsons.com/robots.txt` also has no robots file; it returns the careers app HTML.
- **ToS: unverified.** Both `albertsonscompanies.com/terms-of-use.html` (429 with a "script and cookies" challenge) and `safeway.com/terms-of-use.html` (403) block non-browser clients, so I could not read them. Big-grocer terms usually ban robots. I would treat this as excluded until someone reads the terms in a browser.
- **Volume:** 0 to 2 at the Petworth store.

### B. Target on Workday (Tenleytown store, 4500 Wisconsin Ave NW)

- **Endpoint (tested):** `POST https://target.wd5.myworkdayjobs.com/wday/cxs/target/targetcareers/jobs` with body `{"appliedFacets":{},"limit":20,"offset":0,"searchText":"4500 Wisconsin Ave NW"}`. `locationsText` is a full street address, so filter on it.
- **Sample, Tenleytown:**
  - Target Security Specialist | Target | 4500 Wisconsin Ave NW, 20016 | 2026-10-26 | https://target.wd5.myworkdayjobs.com/targetcareers/job/4500-Wisconsin-Ave-NW-WashingtonDC-20016-4628/Target-Security-Specialist_R0000478713
  - Overnight Inbound (Stocking) (T3351) | Target | 4500 Wisconsin Ave NW | 30+ days old
  - On-Demand: Guest Advocate (Cashier), General Merchandise, Fulfillment (T3351) | Target | 4500 Wisconsin Ave NW | 30+ days old
- **Sample, Petworth:** there is no Target in Petworth. The nearest are 3100 14th St NW (Columbia Heights, about 1.4 mi) and 7828 Georgia Ave NW (about 2.5 mi).
- **robots.txt:** `User-agent: *` / `Allow: /targetcareers/` / `Disallow: /refreshFacet/`. This is allowed.
- **ToS:** this is the problem. Target's Terms & Conditions (https://www.target.com/c/terms-conditions/-/N-4sr7l) prohibit using "browsers, spiders, robots, avatars or intelligent agents" and "data extraction, scraping, mining or other data gathering tools". They define the Site to include other sites and tools where the terms are linked, and cover Target's subsidiaries and affiliates. Whether that reaches the Workday-hosted careers site is unclear. **Recommend excluding** unless Target gives permission.
- **Volume:** 5 jobs at the Tenleytown store.

### C. USAJOBS Search API (federal jobs)

- **Endpoint (from the docs; not called):** `GET https://data.usajobs.gov/api/search?LocationName=Washington,%20DC&...`
  - Required headers: `Host: data.usajobs.gov`, `User-Agent: <contact email>` and `Authorization-Key: <key>`.
  - The key is **free**: request one at https://developer.usajobs.gov (the "API Request" page), then store it as a GitHub secret.
  - USAJOBS requires the User-Agent to be a contact email, so use a project address, not a personal one.
- **ToS:** fine. The developer terms say Public Data "may be copied, stored, reformatted, adapted, analyzed, published, redistributed" with no OPM approval needed. Do not imply OPM endorsement and do not use the seal; attribution is encouraged.
- **robots.txt:** this fails Rule 2. `https://data.usajobs.gov/robots.txt` says:
  ```
  User-agent: *
  Disallow: /
  ```
  (The www and developer hosts only disallow `/Content/`, `/Scripts/` and similar paths.) OPM plainly intends keyed API use and the robots file most likely targets crawlers, but under the hard rule this is excluded. Because of that, I did not request it.
- **Likely local hits, if allowed:** Armed Forces Retirement Home (3700 N Capitol St NW, 20011, about 1 mi from Petworth); DC VA Medical Center (50 Irving St NW, about 1.3 mi); DHS Nebraska Avenue Complex (3801 Nebraska Ave NW, 20016, Tenleytown). Expect 0 to 5 per neighborhood, mostly VA.

---

## Rejected

- **DC Government careers (careers.dc.gov):** this covers DPR rec centers, DC Public Library (Petworth Library, Tenley-Friendship Library) and most agencies. It is an Oracle PeopleSoft Candidate Gateway (`/psp/erecruit/...HRS_CG_SEARCH_FL.GBL`) with HTML only and no RSS or JSON. dchr.dc.gov only links to it. The only option would be scraping HTML.
- **DCPS jobs (dcps.my.salesforce-sites.com):** this would cover Jackson-Reed, Deal, Janney, Powell, Roosevelt and other schools. robots.txt says `User-agent: *` / `Disallow: /` (only login paths are allowed), and there is no feed. joindcpublicschools.com did not respond.
- **Starbucks (apply.starbucks.com Eightfold `/api/pcsx/search`):** the endpoint works, robots allows `/api/pcsx`, and it returns store addresses. However, Starbucks Terms of Use ban anyone who "uses or launches any automated system, including without limitation, 'robots,' 'spiders'". There are also no stores with openings in either neighborhood; the closest are Spring Valley, Friendship Heights MD and Parks at Walter Reed.
- **CVS Health (Workday):** robots allows it, but postings say only "DC - Washington" with no store address, even in the detail record, so jobs cannot be placed in a neighborhood.
- **Whole Foods (careers.wholefoods.com, Paradox):** HTML with embedded `window.__PRELOAD_STATE__` and no public API. amazon.jobs `search.json` returns Whole Foods corporate jobs, not store jobs, and Amazon's conditions of use forbid robots and data mining.
- **Chipotle:** the Workday tenant (`chipotle.wd5.../ChipotleCareers`) is corporate only; a search for "Washington" returned 0. Crew jobs on jobs.chipotle.com are blocked: `Disallow:/search-jobs/`.
- **Best Buy (jobs.bestbuy.com, ServiceNow):** an app with no public or documented job API. robots does allow it.
- **Giant Food:** the careers site timed out and giantfood.com/pages/careers returned 403. No public endpoint found.
- **UDC (udc.applicantstack.com):** HTML openings page only, with no feed. UDC is in Van Ness, about 0.9 mi from Tenleytown.
- **Wesley Theological Seminary, E.L. Haynes PCS (Petworth):** both use Paycom (`paycomonline.net/v4/ats/web.php`), which is HTML only with no public API.
- **Georgetown Day School (Tenleytown):** uses ADP Workforce Now. That JSON is undocumented, and ADP's robots.txt redirects to a login page.
- **Sidwell Friends:** no online job listings were found on its employment page.
- **Washington National Cathedral:** uses Paylocity, which is HTML only. It is in Cathedral Heights, outside both neighborhoods.
- **DC Networks / DOES (dcnetworks.org):** a Cloudflare bot challenge, even for robots.txt.
- **opendata.dc.gov:** a Hub search for job and vacancy datasets found none; the hits were contractor engagements, not jobs.
- **NLx Research Hub / us.jobs:** NLx requires an approved data-sharing agreement. us.jobs returned 509 (bandwidth limit).
- **Culinary Agents:** no public API (sitemaps only), so it would mean scraping job pages.
- **Poached:** no public API, and the terms page returned 403 to our client.
- **Indeed, LinkedIn, Glassdoor, ZipRecruiter, Craigslist:** excluded per brief.
  - The aggregators prohibit automated collection and republishing in their terms.
  - Indeed's legacy Publisher API is gone.
  - Craigslist's robots allows most paths, but its terms of use ban robots.
  - None offers a free public job-search API.

## Implementation notes (Python stdlib)

- Workday: `urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": UA})`.
  - Page by 20.
  - Fetch the detail record only for new IDs, to get `startDate`, and cache by `jobReqId`.
  - About 1 request per second is polite.
- Workday facet IDs can change. Each night, read the `facets` block of a `limit:1` call and look up the location by its `descriptor` text, instead of hard-coding the IDs.
- Store only title, employer, location, posted date and link. The detail JSON includes `jobDescription`; drop it.
