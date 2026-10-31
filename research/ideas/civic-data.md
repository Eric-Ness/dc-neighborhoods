# Civic & open-data utility ideas

Lens: automated pages built from DC's own open data (permits, 311, zoning, ABCA, assessments, trees, crashes, schools), all of which can be pulled by a scheduled GitHub Action or Cloudflare Worker cron, filtered to each neighborhood polygon, and rendered by Astro.

**Shared plumbing (build once, reuse for every idea below):** define each neighborhood as a polygon (DC GIS "Neighborhood Clusters" or a hand-drawn GeoJSON, plus the 2023 ANC/SMD layers). A nightly Python job queries ArcGIS REST endpoints with a spatial filter (`geometry=<polygon>&spatialRel=esriSpatialRelIntersects`), diffs against yesterday's snapshot in D1 or R2, and commits JSON that triggers a Pages rebuild. Once that pipeline exists, each extra dataset costs about a day of work.

**Competitive landscape checked:** OpenANC (openanc.org) covers ANC commissioners, candidates and district maps, but not agendas, votes or cases. Apify sells DC permit and TOPS scrapers to lead-gen buyers, and PermitMint offers per-address permit history. None of these are neighborhood-framed or aimed at residents. DCOZ's IZIS and the interactive zoning map are official but hard to use. I found no resident-facing "what's changing near me" digest for any of the five neighborhoods.

---

## 1. Block Watch: "What's changing in [Neighborhood] this week"
**Pitch:** An automatic weekly digest, published as a page plus an email, that lists every new building permit, zoning case, liquor-license action, and DDOT street-occupancy permit inside the neighborhood, written in plain English.

- **Neighborhoods / audience:** All five. The core readers in Petworth, Tenleytown and Adams Morgan are homeowners, renters, ANC commissioners and civic-association members. In Friendship Heights it also covers the Mazza redevelopment area, and in L'Enfant it serves office managers.
- **What the page shows:** A reverse-chronological feed grouped by type: "New construction / additions", "Demolition / raze", "Zoning relief requested", "Liquor licenses", and "Dumpsters, cranes & street closures". Each item has a small map pin, the address, the permit or case number linking to the official source, and a one-line summary. An LLM generates the summary from the permit description field, and the result is cached so each record costs one call. Archive pages exist by week and by street. An optional Buttondown or Cloudflare Email digest goes out every Monday.
- **Data sources:**
  - Building Permits in 2025/2026 (DOB, yearly layers): https://catalog.data.gov/dataset/building-permits-in-2026 (verified listing; some records have 0,0 coordinates, so fall back to an address match)
  - Zoning Cases layer and Weekly Zoning Cases Report (pulled from IZIS; has Case #, relief sought, status): https://catalog.data.gov/dataset/weekly-zoning-cases-report (verified)
  - Alcohol License Business Locations (ABCA): https://catalog.data.gov/dataset/liquor-licenses-45a2f (verified), plus the ABCA protest-notice PDFs already confirmed in the brief
  - DDOT TOPS Construction Permits and Occupancy Permits: https://catalog.data.gov/dataset/construction-permits-via-ddot-tops, https://catalog.data.gov/dataset/occupancy-permits-via-ddot-tops (verified; refresh cadence unverified)
- **Ongoing effort:** 0.5 h/week to skim the digest before it sends and fix odd summaries. Otherwise it runs itself.
- **Monetization:** One "presented by" sponsor slot per neighborhood newsletter, such as a local architect, contractor, real-estate attorney or title company, at $100–300/month per neighborhood. That assumes about 500–1,500 subscribers in each of Petworth, Tenleytown and Adams Morgan after a year, since ANC and listserv cross-posting drives sign-ups. Realistic total: $200–600/month. On the .org domains, keep it to a single sponsor credit, not ads.
- **Key risks:** Raw permit text is cryptic, so LLM summaries can mislead; always link to the source and add a disclaimer. The datasets are split by year, so the job has to roll over each January. Petworth News could copy the feature.
- **Scores:** Usefulness 5 · Uniqueness 4 · Monetization 3 · Low-upkeep 4 · Build ease 3 · Traffic 4 · Skill fit 5 · **Total 28**
- **Why it could be great:** It answers the single most common neighborhood-listserv question ("what's going on at that house?") before anyone asks, and it costs nothing to keep running.

---

## 2. Zoning Case Explainer (BZA / Zoning Commission watch)
**Pitch:** Every BZA and Zoning Commission case touching the neighborhood gets one plain-English page covering what's requested, when the hearing is, how the ANC voted, and how to testify.

- **Neighborhoods / audience:** Strongest in Tenleytown and Friendship Heights (Wisconsin Ave upzoning, Mazza, the Comprehensive Plan corridor) and in Petworth (rowhouse pop-ups and variances). Readers are neighbors deciding whether to engage, and the developers and architects who watch precedent.
- **What the page shows:** A case list with status chips (filed, set down, hearing, decided). Each case page has the address map, the relief sought, a translation of the zoning code (for example "special exception for lot occupancy over 60% = rear addition"), the hearing date, the ANC resolution if one has been filed, and a link to IZIS exhibits. An "upcoming hearings" box sits on the home page.
- **Data sources:**
  - Weekly Zoning Cases Report (Date, Case #, Case Name, Relief Sought, Case Type, Status; ArcGIS REST): https://catalog.data.gov/dataset/weekly-zoning-cases-report (verified)
  - Zoning Cases GIS layer on opendata.dc.gov (verified via catalog listing)
  - IZIS case records and exhibit PDFs, viewable without login: https://dcoz.dc.gov/service/interactive-zoning-information-system-izis (verified). I found no IZIS API, so scraping case pages is unverified as feasible.
- **Ongoing effort:** 0.5–1 h/week. The automated part is the case list. Optional hand-written notes on big cases add time.
- **Monetization:** Low. Possible sponsorship from a land-use law firm or architect at $100–250/month, though that may look like a conflict of interest on a .org. Realistic: $0–200/month at about 1,000–3,000 pageviews/month, which spike around contentious cases.
- **Key risks:** Low traffic between big cases. A 2026 Hoodline report said the BZA had lost its quorum, so the case flow can stall. Plain-English summaries of legal relief must be careful.
- **Scores:** Usefulness 4 · Uniqueness 4 · Monetization 2 · Low-upkeep 4 · Build ease 3 · Traffic 2 · Skill fit 5 · **Total 24**
- **Why it could be great:** Zoning fights are where neighborhoods actually get shaped, and right now following one requires clicking through a 2000s-era exhibit viewer.

---

## 3. ANC Decoder (agendas, votes, and what passed)
**Pitch:** An auto-built tracker of the ANC that covers each neighborhood, showing the next meeting, the agenda items explained, and a searchable history of resolutions.

- **Neighborhoods / audience:** All five. Likely ANCs are 1C (Adams Morgan), 4C/1A (Petworth), 3E (Tenleytown/Friendship Heights) and 6D (L'Enfant/SW). These mappings are unverified; confirm with the 2023 ANC layer. Readers are engaged residents, candidates and local reporters.
- **What the page shows:** A "Next meeting" card with date, Zoom link and agenda items, each item tagged (zoning, liquor, public space, grants, transportation) and cross-linked to the matching permit or case from ideas 1 and 2. A resolution archive is searchable by address and topic, with a per-commissioner page showing attendance and votes where minutes record them.
- **Data sources:**
  - Each ANC's dc.gov site "agenda by calendar year" pages (for example https://anc1e.dc.gov/agenda-by-calendar-year, verified pattern; per-ANC URLs for 1C/3E/4C/6D unverified)
  - OANC agenda and recordings hub, Mayor's ANC Resolutions Portal: https://oanc.dc.gov (verified site; resolutions portal contents unverified)
  - ANC/SMD 2023 boundaries (in the brief); OpenANC Google Sheets for commissioner names: https://openanc.org/about.html (verified)
- **Ongoing effort:** 1 h/week. The PDF agendas vary in format and some ANCs post late, so the LLM extraction needs spot checks.
- **Monetization:** Very little; this is civic goodwill. Grants or donations (Buy Me a Coffee) might bring $0–50/month. Its value is driving sign-ups to idea 1.
- **Key risks:** Scrapers break when ANCs change sites. Commissioners may object to how votes are characterized. OpenANC could expand into this.
- **Scores:** Usefulness 4 · Uniqueness 4 · Monetization 1 · Low-upkeep 3 · Build ease 3 · Traffic 2 · Skill fit 5 · **Total 22**
- **Why it could be great:** ANCs get "great weight" in DC law yet almost nobody can tell you what theirs voted on last month.

---

## 4. 311 Report Card: "How fast does the city fix things here?"
**Pitch:** A live scoreboard of 311 requests in the neighborhood showing what people report, how long each type takes to close, and how that compares to the rest of DC.

- **Neighborhoods / audience:** All five, with the most meaning in Petworth and Adams Morgan, where residents are heavy reporters. Readers are residents, ANC commissioners preparing for agency meetings, and journalists.
- **What the page shows:** Top request types this month (potholes, rodent abatement, bulk pickup, streetlights, illegal dumping). Median days-to-close for each type, compared with citywide and the other four neighborhoods. A "still open after 30 days" list mapped by block, a heat map, and year-over-year trend sparklines. Each neighborhood also gets an auto-generated monthly paragraph ("Rodent complaints in Petworth up 40% vs. last October").
- **Data sources:**
  - 311 City Service Requests in 2026 (OUC; CSV/GeoJSON/REST): https://catalog.data.gov/dataset/311-city-service-requests-in-2026 (verified)
  - All 311 City Service Requests, Last 30 Days: https://geo.btaa.org/catalog/14faf3d4bfbe4ca4a713bf203a985151_0 (verified listing; current refresh status unverified, as one mirror showed May 2026)
- **Ongoing effort:** About 0.25 h/week. The site is fully automated.
- **Monetization:** Low to moderate. EthicalAds or Carbon-style display ads bring $20–80/month at about 5,000–10,000 pageviews/month. A local pest-control or junk-hauling sponsor could pay $100–200/month, but that conflicts with the .org feel.
- **Key risks:** 311 close times are gamed (requests closed without being fixed), so frame the numbers as "reported closure". Many DC-wide 311 dashboards exist. Its uniqueness comes only from the neighborhood framing.
- **Scores:** Usefulness 4 · Uniqueness 3 · Monetization 2 · Low-upkeep 5 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 26**
- **Why it could be great:** It turns "the city never fixes anything here" into a number that ANC commissioners will screenshot and bring to agency oversight hearings.

---

## 5. Home Sales & Assessment Check
**Pitch:** Every recorded sale in the neighborhood this month, plus a tool that checks whether your property-tax assessment is out of line with comparable recent sales, timed to the appeal deadline.

- **Neighborhoods / audience:** Petworth, Tenleytown, Friendship Heights and Adams Morgan, which have rowhouse and condo stock. L'Enfant has almost no residential property. Readers are homeowners, buyers and agents.
- **What the page shows:** A monthly "sold" table (address, date, price, $/sq ft, beds) and median-price trends by property type. An assessment checker where you enter an address and see your current assessed value next to five nearby comparable sales and their assessments, with a ratio flag ("your assessment is 12% above comps"). Every page links to OTR's free appeal process and deadline.
- **Data sources:**
  - Computer Assisted Mass Appraisal: Residential (sale history, updated daily): https://catalog.data.gov/dataset/computer-assisted-mass-appraisal-residential-0dca4 (verified); the CAMA Condominium variant (verified listing)
  - Tax System Property Sales (CAMA): https://catalog.data.gov/dataset/tax-system-property-sales-cama (verified)
  - Integrated Tax System Public Extract (assessments, owners, SSL): https://catalog.data.gov/dataset/integrated-tax-system-public-extract (verified)
- **Ongoing effort:** 0.25–0.5 h/week.
- **Monetization:** The best of the civic ideas. A single real-estate agent or mortgage-broker sponsor per neighborhood pays $200–500/month, or an "assessment appeal help" referral. Assuming 3,000–8,000 pageviews/month with a spring spike around appeal season, a realistic total is $300–900/month. Trust risk: on the .org domains, keep sponsors clearly labeled, never sell leads, and never gate the checker.
- **Key risks:** Zillow and Redfin dominate sales data, so uniqueness rests on the assessment angle. Owner names in the ITSPE are public but showing them feels invasive, so omit them. The comps logic must be explainable to avoid bad tax advice; label it informational.
- **Scores:** Usefulness 4 · Uniqueness 3 · Monetization 4 · Low-upkeep 4 · Build ease 3 · Traffic 4 · Skill fit 5 · **Total 27**
- **Why it could be great:** An assessment-appeal nudge that saves a Petworth homeowner $800 a year is the kind of thing people forward to their whole block.

---

## 6. Curb Radar: dumpsters, cranes & emergency no-parking (unusual)
**Pitch:** A daily map and alert feed of every DDOT public-space permit on the neighborhood's streets, showing who has reserved the curb, where a crane is going up, and which block will lose parking next week.

- **Neighborhoods / audience:** All five. Very practical in Adams Morgan and Petworth rowhouse blocks, where dumpsters and moving trucks take scarce parking. In L'Enfant/SW, commuters and office facilities managers care about crane and lane closures.
- **What the page shows:** A "today and next 7 days" map of active occupancy and construction permits (moving trucks, roll-off containers, storage pods, staging areas, mobile cranes, reserved parking), color-coded by type. A list grouped by street. A per-street RSS/email subscription ("alert me about permits on Upshur St"). Long-running occupancies (over 90 days) get flagged.
- **Data sources:**
  - Construction Permits (via DDOT TOPs), whose fields include moving truck, roll-off container, staging, mobile crane: https://catalog.data.gov/dataset/construction-permits-via-ddot-tops (verified)
  - Occupancy Permits (via DDOT TOPs): https://catalog.data.gov/dataset/occupancy-permits-via-ddot-tops (verified; one catalog record says last modified Sept 2025, so **daily refresh is unverified**; check the live REST layer before building)
  - TOPS portal: https://tops.ddot.dc.gov (verified reference)
- **Ongoing effort:** About 0.25 h/week.
- **Monetization:** Modest. A local moving company or junk-hauler sponsor at $100–250/month across neighborhoods, assuming about 2,000–5,000 pageviews/month plus a few hundred street subscribers.
- **Key risks:** If the TOPS layer isn't refreshed frequently, the "radar" goes stale and the idea collapses into part of idea 1. Per-street subscriptions need light email infrastructure.
- **Scores:** Usefulness 4 · Uniqueness 5 · Monetization 2 · Low-upkeep 4 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 27**
- **Why it could be great:** No one else tells you on Tuesday that your block loses six spaces on Friday, and in a rowhouse neighborhood that is the most practical piece of civic data there is.

---

## 7. Liquor License & Nightlife Pipeline
**Pitch:** A tracker of every alcohol licensee in the neighborhood, covering new applications, protest deadlines, settlement agreements, cancellations and moratorium zones, written for both nightlife fans and nervous neighbors.

- **Neighborhoods / audience:** Mainly Adams Morgan (18th St nightlife). Also useful for Petworth's growing restaurant strip and for Tenleytown. Readers are residents, restaurateurs scouting locations, and ANC liquor committees.
- **What the page shows:** A map of current licensees by class (tavern, restaurant, nightclub, retail). A "new and pending" list with placard dates and protest-petition deadlines extracted from ABCA notice PDFs, plus recent cancellations ("closed" signal). Moratorium-zone boundaries are overlaid. A "who's opening" feed doubles as a restaurant-openings list.
- **Data sources:**
  - Alcohol License Business Locations (ABCA; REST layer): https://catalog.data.gov/dataset/liquor-licenses-45a2f (verified)
  - Alcohol License Cancellations: https://catalog.data.gov/dataset/alcohol-license-cancellations (verified)
  - ABCA Moratorium Zones: https://catalog.data.gov/dataset/alcohol-license-moratorium-zones (verified; whether an Adams Morgan moratorium is currently in force is **unverified**)
  - ABCA protest/placard notice PDFs (confirmed in the brief)
- **Ongoing effort:** 0.5 h/week, mostly checking PDF extraction.
- **Monetization:** Moderate for Adams Morgan only. Restaurant and bar "now open" sponsorships, or a featured-opening slot at $50–150 per placement, comes to perhaps $100–400/month at about 3,000–6,000 pageviews/month. The BID already lists businesses, so position this as the regulatory pipeline, not a directory.
- **Key risks:** PDF formats change. ABCA disclaims accuracy. Restaurateurs may dislike protest coverage. The overlap with the Adams Morgan BID is partial.
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 3 · Low-upkeep 4 · Build ease 3 · Traffic 3 · Skill fit 5 · **Total 25**
- **Why it could be great:** Liquor placards are the earliest public signal that a new bar or restaurant is coming, often months before any press.

---

## 8. Street Tree Atlas & Empty-Box Finder (unusual)
**Pitch:** Every public street tree in the neighborhood, with species, size and health, plus a map of empty tree boxes where residents can request a free DDOT planting.

- **Neighborhoods / audience:** All five, best in Petworth and Tenleytown (rowhouse and single-family blocks). Readers are gardeners, families, Casey Trees volunteers and school science classes.
- **What the page shows:** Per-neighborhood stats (tree count, top species, canopy share, trees planted or removed since 2014). An interactive map with species-filter toggles. A "vacant planting spaces" layer with a one-click link to request a tree via 311. A "notable trees" page listing the biggest oak on each street. A seasonal "what's blooming" page generated from species bloom months.
- **Data sources:**
  - Urban Forestry Street Trees (about 175–200k trees, metadata updated Apr 2026): https://catalog.data.gov/dataset/urban-forestry-street-trees (verified)
  - Street Tree Archive (annual changes 2014–present): https://catalog.data.gov/dataset/street-tree-archive (verified)
  - Urban Forestry Street Tree Benefits: https://catalog.data.gov/dataset/urban-forestry-street-tree-benefits (verified listing)
  - trees.dc.gov (referenced by the dataset; verified as pointer)
- **Ongoing effort:** About 0.1 h/week. It is near-static and only needs a monthly refresh.
- **Monetization:** Minimal. Possibly an affiliate link to native-plant nurseries or a local garden-center sponsor at $0–100/month. Assumes about 1,000–3,000 pageviews/month with spring spikes.
- **Key risks:** Low urgency means low repeat traffic. Whether the dataset includes empty-box records needs checking (**unverified**).
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 1 · Low-upkeep 5 · Build ease 5 · Traffic 2 · Skill fit 5 · **Total 25**
- **Why it could be great:** It's a weekend build that gets more beautiful every year and gives the .org domains a warm, non-commercial civic identity.

---

## 9. Block Report Card: one page per block (unusual)
**Pitch:** A programmatically generated page for every block face in the five neighborhoods that combines permits, 311, crashes, trees, liquor licenses, school boundary, and lead-service-line status into one shareable "know your block" card.

- **Neighborhoods / audience:** All five. Readers are house hunters, new residents, and anyone searching "[street name] Petworth".
- **What the page shows:** For example, "1300 block of Upshur St NW": in-boundary DCPS schools; crashes within 150 m in the last 3 years (with pedestrian or bike involvement); 311 top requests; street trees; recent permits and sales; nearby liquor licensees; a link to DC Water's lead-pipe lookup; and the ANC/SMD and commissioner. Hundreds to thousands of static pages are built by Astro from one joined dataset.
- **Data sources:**
  - Crashes in DC (24-hour publication) and Crash Details Table: https://catalog.data.gov/dataset/crashes-in-dc, https://catalog.data.gov/dataset/crash-details-table (verified)
  - Enrollment Boundary Information System (school by address): https://catalog.data.gov/dataset/enrollment-boundary-information-system (verified)
  - DC School Report Card public data files: https://osse.dc.gov/page/dc-school-report-card-resource-library (verified)
  - DC Water Service Line Materials Dashboard (updated daily; bulk download **unverified**, so link out rather than ingest): https://www.dcwater.com/service-line-materials-dashboard
  - Plus the datasets from ideas 1, 4, 5 and 8
- **Ongoing effort:** 0.25 h/week once the build is stable.
- **Monetization:** The best SEO surface of the set. Long-tail "[street] DC" searches could reach 10,000–30,000 pageviews/month after 12–18 months. At about $5–10 RPM with tasteful display ads, or with a realtor sponsor per neighborhood, that is roughly $100–400/month. Heavy ads would undercut the .org trust, so use a sponsor model.
- **Key risks:** It could look like a thin-content SEO farm to Google if the pages aren't substantive. Crash and school data on a "neighborhood quality" page edges toward steering, so present facts neutrally with no composite score. It is the most complex build of the set.
- **Scores:** Usefulness 4 · Uniqueness 4 · Monetization 3 · Low-upkeep 4 · Build ease 2 · Traffic 4 · Skill fit 5 · **Total 26**
- **Why it could be great:** It's the page a house hunter wishes existed, and once built, each new dataset makes thousands of pages richer at no extra effort.

---

## 10. Vacant & Blighted Watch
**Pitch:** A neutral, data-only list of properties the District has classified as vacant or blighted in each neighborhood, with how long they've been listed, any permits pulled since, and the tax class.

- **Neighborhoods / audience:** Petworth, plus pockets of Adams Morgan. Few such properties exist in Tenleytown, Friendship Heights or L'Enfant. Readers are neighbors, ANC commissioners, small developers and journalists.
- **What the page shows:** A map and list of addresses on the vacant and blighted rolls, with first-seen date (tracked by the bot's own daily snapshots), assessed value, and recent permit activity ("permit filed, so maybe being renovated"). Also a list of properties removed from the list this year ("brought back to life"), and a link to report a suspected vacant building via 311.
- **Data sources:**
  - Integrated Tax System Public Extract: Vacant Property and Vacant & Blighted subsets (OCFO): https://catalog-old.data.gov/dataset/integrated-tax-system-public-extract-vacant-property (verified listing)
  - Vacant and Blighted Building Footprints: https://catalog-old.data.gov/dataset/vacant-and-blighted-building-footprints (verified listing)
  - Building Permits (idea 1) for the activity join
- **Ongoing effort:** About 0.1 h/week.
- **Monetization:** Little directly. It could attract investor or developer traffic, but selling leads would harm trust: $0–100/month at about 500–2,000 pageviews/month.
- **Key risks:** Owners may object to being named, so show addresses only, not owner names. The classification lags reality. The audience is small outside Petworth.
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 1 · Low-upkeep 5 · Build ease 4 · Traffic 2 · Skill fit 5 · **Total 24**
- **Why it could be great:** Tracking the list over time turns a static tax roll into an accountability story ("this rowhouse has been vacant for 7 years") that a hyperlocal newsroom like Petworth News would gladly cite.

---

## Ranking summary

| # | Idea | Total |
|---|------|-------|
| 1 | Block Watch weekly digest | 28 |
| 5 | Home Sales & Assessment Check | 27 |
| 6 | Curb Radar (TOPS permits) | 27 |
| 4 | 311 Report Card | 26 |
| 9 | Block Report Card | 26 |
| 7 | Liquor License Pipeline | 25 |
| 8 | Street Tree Atlas | 25 |
| 2 | Zoning Case Explainer | 24 |
| 10 | Vacant & Blighted Watch | 24 |
| 3 | ANC Decoder | 22 |

**Recommended path:** Build the shared spatial-filter pipeline once, launch **Block Watch (#1)** as the flagship on all five domains, and add 6, 4 and 5 as tabs that reuse the same nightly job. Treat 9 as the long-term SEO expansion once the data joins exist.

## Sources
- https://catalog.data.gov/dataset/building-permits-in-2026
- https://catalog.data.gov/dataset/building-permits-in-2025/resource/e47c351b-b7cc-4ef3-a318-7dde5dbb6767
- https://catalog.data.gov/dataset/weekly-zoning-cases-report
- https://dcoz.dc.gov/howtosearch
- https://dcoz.dc.gov/fr/service/interactive-zoning-information-system-izis
- https://hoodline.com/2026/04/zoning-chaos-d-c-projects-frozen-as-board-loses-its-quorum/
- https://catalog.data.gov/dataset/integrated-tax-system-public-extract
- https://catalog.data.gov/dataset/computer-assisted-mass-appraisal-residential-0dca4
- https://catalog.data.gov/dataset/tax-system-property-sales-cama
- https://catalog-old.data.gov/dataset/integrated-tax-system-public-extract-vacant-property
- https://catalog-old.data.gov/dataset/vacant-and-blighted-building-footprints
- https://catalog.data.gov/dataset/urban-forestry-street-trees
- https://catalog.data.gov/dataset/street-tree-archive
- https://catalog.data.gov/dataset/urban-forestry-street-tree-benefits
- https://catalog.data.gov/dataset/construction-permits-via-ddot-tops
- https://catalog.data.gov/dataset/occupancy-permits-via-ddot-tops
- https://catalog.data.gov/dataset/liquor-licenses-45a2f
- https://catalog.data.gov/dataset/alcohol-license-cancellations
- https://catalog.data.gov/dataset/alcohol-license-moratorium-zones
- https://catalog.data.gov/dataset/311-city-service-requests-in-2026
- https://geo.btaa.org/catalog/14faf3d4bfbe4ca4a713bf203a985151_0
- https://catalog.data.gov/dataset/crashes-in-dc
- https://catalog.data.gov/dataset/crash-details-table
- https://octo.dc.gov/release/mayor-bowser-announces-public-crash-data-be-published-every-twenty-four-hours
- https://catalog.data.gov/dataset/enrollment-boundary-information-system
- https://osse.dc.gov/page/dc-school-report-card-resource-library
- https://www.dcwater.com/service-line-materials-dashboard
- https://catalog.data.gov/dataset/real-estate-portfolio-at-dmped
- https://catalog.data.gov/dataset/wdcep-development-report
- https://electionresults.dcboe.org/Downloads/Reports/November_8_2022_General_Election_Certified_Results.pdf (checked; election results are PDF-only, so no election idea was included)
- https://anc1e.dc.gov/agenda-by-calendar-year
- https://oanc.dc.gov
- https://openanc.org/about.html
- https://ggwash.org/view/78626/this-app-makes-it-easier-to-get-information-about-your-local-anc
- https://apify.com/j0401/dc-building-permits
- https://apify.com/j0401/dc-tops-permits
- https://permitmint.com/permit-history/washington-dc/
