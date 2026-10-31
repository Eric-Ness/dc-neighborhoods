# Culture, history, community and content ideas

Lens: neighborhood history, archives, oral histories, walking tours, food and drink, arts, newsletters, AI-assisted curation with human review.

**Rights findings that shape every idea below**

- **Free to republish:** Library of Congress Sanborn maps (LOC says the online collection is public domain). Chronicling America newspapers more than 95 years old, which in 2026 means the Evening Star through 1930. Most LOC prints and photos marked "no known restrictions", checked item by item. DC HPO "Historic Data on DC Buildings" (HistoryQuest), Historic Landmarks/Districts and Basic Business Licenses on Open Data DC, all CC BY 4.0. NARA 1950 census images, which are federal records and free.
- **Link, don't rehost:** DC Public Library Dig DC / The People's Archive carries mixed rights. For example, the Washington Post holds copyright on the Washington Star staff photos, and DCPL licenses their use for a fee. DC History Center (Historical Society of Washington) images need a paid permission request. HMdb has no published license or API. Prologue DC's Mapping Segregation data has no stated license (unverified), so partner with them instead of copying it.
- **Existing competitors on this lens:** Tenleytown Historical Society (active nonprofit, heritage trail). Historic Chevy Chase DC (covers Friendship Heights edges, house histories, oral histories). Ghosts of DC and Streets of Washington (citywide vintage photos and stories). Cultural Tourism DC heritage trails exist for Tenleytown and Adams Morgan ("Roads to Diversity"), but I found none for Petworth itself; Georgia Ave/Pleasant Plains is the nearest. Petworth News already runs Prologue DC segregation stories. Nobody publishes structured, per-building or per-block history pages for these five neighborhoods.

---

## 1. House & Block History Pages: an auto-generated "biography" for every building

**Pitch:** A static page for each extant building, showing its construction year, original architect, owner and builder, landmark or district status, and its block on the 1903/1927 Sanborn maps. "1415 Upshur St NW: built 1919, architect X" ranks for address searches.

- **Neighborhoods / audience:** Petworth, Adams Morgan, Tenleytown and Friendship Heights. L'Enfant Plaza is mostly post-1960 federal buildings, so it would get only a small set. The audience is homeowners, buyers, renters, realtors and preservation buffs.
- **What the page shows:**
  - Per address: a facts card from HistoryQuest data and an embedded Sanborn sheet crop, georeferenced or linked to the LOC deep-zoom viewer.
  - Historic district and landmark badge, plus "other buildings by this architect/builder" (Petworth rowhouse builders such as Kennedy Bros. would surface here).
  - Per block: a construction-year heat map and a "who built your street" summary.
  - A short AI-drafted narrative per block that you review before publishing.
- **Sources:**
  - Historic Data on DC Buildings (HistoryQuest), CC BY 4.0: https://catalog.data.gov/dataset/historic-data-on-dc-buildings and https://catalog.data.gov/dataset/history-quest-dc
  - Historic Landmarks: https://catalog.data.gov/dataset/historic-landmarks
  - Historic Districts: https://catalog.data.gov/dataset/historic-districts-7b313
  - LOC Sanborn maps (public domain), e.g. the 1888 DC volume: https://www.loc.gov/resource/g3851gm.g3851gm_g012271888/
  - LOC JSON API: https://www.loc.gov/apis/json-and-yaml/requests/
  - Georeferenced Sanborn tiles for DC: unverified. You may need to georeference the sheets yourself with QGIS/Allmaps.
- **Ongoing effort:** 0.5 h/week. The data is near-static; a yearly refresh plus a review queue for corrections.
- **Monetization:**
  - Print-on-demand framed Sanborn sheet of "your block", plus a "house history report" PDF upsell at $15-$29.
  - Realtor sponsorship slot per neighborhood.
  - Assuming 4-8k visits/month across sites with 0.3% buying at ~$40 margin: **$50-$300/mo**. Prints are fine on .org if framed as supporting the project.
- **Key risks:**
  - HistoryQuest data has gaps and errors, and records cover only pre-1949 permits.
  - Georeferencing Sanborn sheets is fiddly.
  - Tenleytown Historical Society and Historic Chevy Chase DC may see it as overlap, so invite them to link and contribute.
- **Scores:** Usefulness 4 · Uniqueness 4 · Monetization 3 · Low-upkeep 5 · Build ease 3 · Traffic 4 · Skill fit 5 · **Total 28**
- **Why it could be great:** Every homeowner wants to know who built their house, and thousands of permanent, address-specific pages would bring search traffic for years with almost no upkeep.

## 2. "100 Years Ago This Week": an Evening Star dispatch mined from Chronicling America

**Pitch:** An automated weekly column and email of what the Evening Star printed about each neighborhood exactly 100 years earlier. In late 2026 that is the 1926 paper: fires, school openings, streetcar fights, real-estate ads for "new Petworth homes."

- **Neighborhoods / audience:** All five. For L'Enfant Plaza, use the pre-renewal Southwest neighborhood. The audience is history fans, newsletter readers and local social media.
- **What the page shows:**
  - A weekly post per neighborhood with 3-6 clipped items. Each has the original page image crop, a short modern-English summary, and a link to the LOC page.
  - A searchable archive that builds up over time.
- **Sources:**
  - Evening Star on Chronicling America / loc.gov (LCCN sn83045462). Public domain for issues over 95 years old: https://www.loc.gov/item/sn83045462/
  - Full-text OCR search through the loc.gov JSON API: https://www.loc.gov/apis/json-and-yaml/requests/
  - Exact OCR full-text endpoint parameters: unverified, so test before building.
- **Pipeline:**
  1. A GitHub Action queries the API weekly for issues dated 100 years back, using keyword sets per neighborhood ("Petworth", "Tenleytown", "Tenley", "Lanier Heights", "Washington Heights", "Kalorama Road", "Friendship" plus "Wisconsin", "Southwest" plus street names).
  2. Claude scores relevance and drafts summaries.
  3. You approve in a 15-minute review and publish to Astro plus Buttondown.
- **Ongoing effort:** 0.5-1 h/week for review.
- **Monetization:**
  - Newsletter sponsorship from local realtors or businesses, $50-$150/issue once the list reaches 1-2k.
  - Paid "supporter" tier.
  - Assuming 1,500 subscribers across neighborhoods within a year: **$100-$400/mo**.
- **Key risks:**
  - OCR noise.
  - "Adams Morgan" did not exist as a name until ~1955, so you need period place names.
  - 1920s coverage includes racist content that needs careful editorial framing. Keep human review mandatory.
- **Scores:** Usefulness 3 · Uniqueness 5 · Monetization 3 · Low-upkeep 4 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 27**
- **Why it could be great:** It is a content engine that never runs dry: the 95-year public-domain window moves forward by one year every January, and no DC outlet does this per neighborhood.

## 3. Lost Southwest: a self-guided walk for the people stuck at L'Enfant Plaza

**Pitch:** A phone-first, GPS-aware walking and audio tour. It shows the 23,000-resident, 1,500-business Southwest neighborhood that urban renewal razed in 1954-60, overlaid on the concrete plaza and Metro transfer that replaced it.

- **Neighborhoods / audience:** L'Enfant Plaza only (lenfantplaza.org). The audience is tourists heading to the Mall and Wharf, federal office workers on lunch, transferring Metro riders, school groups and urbanism nerds.
- **What the page shows:**
  - 8-12 stops, each with a public-domain "before" image (LOC HABS/HAER, Sanborn sheets, 1920s Evening Star clippings) and the current view.
  - A 90-second audio clip per stop, written by you and voiced by TTS or by you.
  - A "where did they go" section on displacement, and a 15/30/45-minute route chooser.
  - A "you have 12 minutes before your train" mini-tour.
- **Sources:**
  - LOC Sanborn and HABS (public domain; check each item).
  - Background to cite, not copy: Ghosts of DC's 2026 history https://ghostsofdc.org/2026/04/12/before-fedlandia-lenfant-plaza-southwest-dc-history/, SW BID history https://swbid.org/history/, WETA Boundary Stones https://blogs.weta.org/metromap/renewalcenter
  - DCPL Washington Star photos of 1950s SW would be ideal, but they need a DCPL/Post license, so either pay for a few or link out.
- **Ongoing effort:** 0.25 h/week after a ~20-hour authoring push.
- **Monetization:**
  - A HumanitiesDC grant is realistic; they fund place-based history.
  - Tip jar, and paid group-tour referrals to local guides.
  - A **one-off $2-5k grant** plus **$0-$75/mo** in tips, assuming 1-3k visits/month driven by QR stickers (with permission) and SEO for "L'Enfant Plaza history".
- **Key risks:**
  - The private plaza owner may object to on-site signage; stay on public sidewalks.
  - The displacement narrative needs community voices, so consult SW neighborhood groups.
  - Ghosts of DC already covers the history in prose (but not as a tour).
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 2 · Low-upkeep 5 · Build ease 4 · Traffic 3 · Skill fit 4 · **Total 25**
- **Why it could be great:** It turns the domain with the fewest residents into the one with the clearest purpose: a civic, grant-fundable .org that tells a story the plaza's commercial owner never will.

## 4. Then & Now Slider Gallery: rephotography of public-domain views

**Pitch:** Drag-to-compare sliders that pair a public-domain historic photo with a matching modern photo shot from the same spot, organized by street.

- **Neighborhoods / audience:** All five. The strongest material is for Adams Morgan (18th St, Columbia Rd), Tenleytown (Wisconsin Ave, the old Western High area) and Friendship Heights (streetcar barn, Hecht's/Mazza). The audience is residents and social media.
- **What the page shows:**
  - A map of pins, each opening a before/after slider with date, source, and a 2-3 sentence caption.
  - A "Friendship Heights in transition" series documenting the Mazza Gallerie conversion as it happens, so you create tomorrow's archive.
- **Sources:**
  - LOC Prints & Photographs (check for "no known restrictions" per item), e.g. https://www.loc.gov/pictures/item/dc0379/
  - DDOT historic photo library, which says pre-late-1973 DC-agency photos are public domain: https://ddotlibrary.omeka.net/permissions-and-usage
  - Dig DC (link only unless the item is cleared): https://www.dclibrary.org/research-and-learn/dig-dc
  - Your own photos for "now".
- **Ongoing effort:** 1-2 h/week while adding pairs (shooting is the pleasant part), then 0.
- **Monetization:**
  - Fine-art print sales of pairs and an annual calendar.
  - Assuming 2-5k visits/month with spikes from Reddit or PoPville shares: **$30-$200/mo**.
- **Key risks:**
  - Finding enough public-domain images per neighborhood. Petworth and Tenleytown may only yield 15-30 good ones.
  - Licensed DCPL images get expensive.
  - Ghosts of DC does occasional then/now posts.
- **Scores:** Usefulness 3 · Uniqueness 3 · Monetization 2 · Low-upkeep 4 · Build ease 4 · Traffic 4 · Skill fit 4 · **Total 24**
- **Why it could be great:** Then/now sliders are among the most shared local-history formats online, and the owner's walks become the content pipeline.

## 5. Openings, Closings & the Lost Restaurants Wall

**Pitch:**
- An automated ledger of new and lapsed business licenses, filtered to food, drink and retail, per neighborhood.
- A "Lost Restaurants" memorial wall where residents post memories of closed places, e.g. Adams Morgan's long-gone clubs and Tenleytown's old diners.

- **Neighborhoods / audience:** All five, strongest for Adams Morgan and Petworth. The audience is food-curious residents and newcomers.
- **What the page shows:**
  - "New this month" and "Gone this month" lists generated from license issue and expiry data, cross-checked with ABCA liquor notices.
  - A per-business timeline.
  - Memorial wall entries, each with one optional photo the submitter owns, held for approval.
- **Sources:**
  - Basic Business Licenses (CC BY 4.0) and its 30-day feed: https://catalog.data.gov/dataset/basic-business-licenses and https://catalog.data.gov/dataset/basic-business-license-in-last-30-days
  - ABCA notices (per the brief).
  - Historic restaurant references from Chronicling America (public domain).
- **Ongoing effort:** 0.5-1 h/week, mostly moderating wall submissions.
- **Monetization:**
  - A restaurant "featured opening" slot, and delivery or reservation affiliate links.
  - Assuming 3-6k visits/month: **$50-$250/mo**. Paid placement on a .org risks trust, so label it clearly or skip it on Petworth/Tenleytown .org.
- **Key risks:**
  - PoPville and Petworth News already break opening news faster.
  - A license lapse does not equal a closure, so false "closed" claims are a reputational risk; label entries "license lapsed".
  - The wall requires moderation, which the owner dislikes.
- **Scores:** Usefulness 3 · Uniqueness 2 · Monetization 3 · Low-upkeep 3 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 23**
- **Why it could be great:** The automated ledger plus the nostalgic wall is a mix of data and memory that news sites don't keep as a permanent record.

## 6. Street-Name Dictionary: who was Upshur? Why "Tenley"?

**Pitch:** A small, evergreen reference with one page per street, park, school and Metro station name in each neighborhood, covering who or what it honors, when it was named, and what it used to be called.

- **Neighborhoods / audience:** All five. Petworth's alphabetical streets (Allison through Webster), Adams Morgan (Champlain, Kalorama, Lanier) and Tenleytown/Friendship Heights (Albemarle, Brandywine, Chesapeake) all have stories. The audience is curious residents, students and trivia fans.
- **What the page shows:** An A-Z list, a map with street lines colored by naming era (1905 renaming of county roads versus earlier subdivisions), and a citation block on every entry.
- **Sources:**
  - Street centerlines from DC GIS on Open Data DC (exact dataset URL unverified).
  - LOC maps for old names (public domain).
  - Chronicling America for renaming debates.
  - Content drafted by Claude from cited primary sources, then verified by hand. Do not publish unverified etymology.
- **Ongoing effort:** 0.1 h/week after a build of ~15-25 hours.
- **Monetization:**
  - Display ads at low RPM, assuming 1-3k visits/month, for **$5-$40/mo**.
  - Realistically a portfolio and traffic feeder for ideas 1 and 2.
- **Key risks:**
  - AI hallucinated etymologies are the main danger, so require a source link on every entry.
  - Small total traffic.
  - The Tenleytown Historical Society likely covers "Tenley" already.
- **Scores:** Usefulness 2 · Uniqueness 3 · Monetization 1 · Low-upkeep 5 · Build ease 4 · Traffic 2 · Skill fit 4 · **Total 21**
- **Why it could be great:** It is the cheapest idea here to keep alive forever, and it makes a strong internal-linking spine for the other history pages.

## 7. Neighborhood Voices: an index to oral histories you're allowed to point at

**Pitch:** A curated, searchable index of existing oral-history interviews about each neighborhood. Each entry has an AI-assisted summary, topic tags, and jump-to-timestamp links into the original archive. You link to the interviews rather than hosting them.

- **Neighborhoods / audience:** Adams Morgan is strongest: the DCOHC holds interviews with Nancy Shia, the Hargroves and John Jones. Tenleytown and Friendship Heights are covered by the Historic Chevy Chase DC oral histories. Petworth is thinner. The audience is students, journalists, teachers, long-time residents and grant reviewers.
- **What the page shows:**
  - An entry per interviewee with neighborhood, decade, topics (organizing, rent strikes, Latino community, the 1970s Adams Morgan Organization), and a 100-word summary you have checked.
  - Key quotes under 15 words, plus "listen at the source" links.
  - Topic pages that thread voices together.
- **Sources:**
  - DC Oral History Collaborative in The People's Archive: https://thepeoplesarchive.dclibrary.org/repositories/2/digital_objects/1384
  - Sample interview: https://thepeoplesarchive.dclibrary.org/repositories/2/archival_objects/605036
  - HumanitiesDC DCOHC program reports: https://humanitiesdc.org/wp-content/uploads/2023/04/dcohc-survey-public-report.pdf
  - Historic Chevy Chase DC: https://www.historicchevychasedc.org/resources
  - Transcript reuse rights are per-item and unverified, so summaries and links only.
- **Ongoing effort:** 0.5 h/week. Check for new DCOHC additions quarterly.
- **Monetization:**
  - Essentially none directly; a DCOHC "Beyond the Archives" grant is plausible (the 2023 round gave $12k to an Adams Morgan project).
  - **$0/mo**, with a **one-off $3-12k grant** possible.
- **Key risks:**
  - Narrow audience.
  - Summarizing someone's life story badly is harmful, so human review is mandatory.
  - Archive URLs may change.
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 1 · Low-upkeep 4 · Build ease 3 · Traffic 1 · Skill fit 4 · **Total 20**
- **Why it could be great:** Thousands of hours of recorded neighborhood memory sit almost undiscoverable in finding aids, and a good index makes adamsmorgan.org the obvious civic front door to them.

## 8. 1950 Block Portrait: what your street looked like in the 1950 census (unusual)

**Pitch:** A per-block statistical portrait from the 1950 census manuscript schedules, released free in 2022: occupations, birthplaces, household sizes, renters versus owners, and lodgers. Shown as charts, not a people-search site.

- **Neighborhoods / audience:**
  - Petworth: a 1950 snapshot of a neighborhood mid-transition after covenants were struck down in 1948.
  - Adams Morgan, just before the name existed.
  - Tenleytown, Friendship Heights, and pre-renewal Southwest for L'Enfant Plaza.
  - The audience is residents, teachers, genealogists and data journalists.
- **What the page shows:**
  - Per enumeration district: "Most common jobs on your block in 1950," "% born outside DC," "average household size then vs now" (vs ACS), and a link to the actual census sheet image at NARA.
  - Names appear only via NARA's own viewer, not reindexed.
- **Sources:**
  - NARA 1950 census site: https://1950census.archives.gov/
  - Bulk images and ED maps on AWS Open Data: https://registry.opendata.aws/nara-1950-census/
  - ED lookup: https://stevemorse.org/census/faq1950.htm
  - Transcription: run Claude vision or OCR on ~200-400 sheets per neighborhood, then spot-check. NARA's own name OCR is admittedly imperfect.
- **Ongoing effort:** ~0 h/week once built. The build is the hard part (40-80 hours).
- **Monetization:**
  - Grant or data-journalism partnership.
  - Small donations.
  - **$0-$50/mo**, assuming 1-2k visits/month with spikes when a local outlet covers it.
- **Key risks:**
  - Transcription accuracy.
  - Mapping ED boundaries to modern blocks.
  - Privacy sensitivities: some 1950 residents are alive, so aggregate only and never build a name search.
  - The biggest effort of any idea here.
- **Scores:** Usefulness 3 · Uniqueness 5 · Monetization 1 · Low-upkeep 5 · Build ease 1 · Traffic 3 · Skill fit 4 · **Total 22**
- **Why it could be great:** No one has turned the 1950 census into neighborhood-scale social history for DC, and the AWS bulk dataset makes it a real Python and AI portfolio piece.

## 9. Murals & Public Art Field Guide (unusual: walkable, photo-driven, self-updating)

**Pitch:** A map and field guide to murals, sculpture and public art, with artist bios and a yearly "new and lost art" report. Adams Morgan's mural density is the anchor.

- **Neighborhoods / audience:** Adams Morgan (strong) and Petworth (Georgia Ave and Upshur murals). Tenleytown, Friendship Heights and L'Enfant Plaza have federal and plaza sculpture. The audience is tourists, photographers and families looking for walks.
- **What the page shows:**
  - A pin per work with your own photo, artist, year, commissioning body, and status (extant / painted over).
  - A seasonal "mural walk" route.
  - An "art lost to redevelopment" list.
- **Sources:**
  - DC Commission on the Arts and Humanities public art eMuseum (searchable, no bulk dataset found): https://dcarts.dc.gov/page/dcartsemuseum
  - Read the Plaque (example entry): https://readtheplaque.com/plaque/walter-pierce-park
  - Your own photos, which avoid image rights issues. Murals themselves are copyrighted art; photographing public art for non-commercial documentation is generally fine, but selling prints of murals is not.
  - Existing citywide mural maps: unverified.
- **Ongoing effort:** 0.5-1 h/week in season (a photo walk), plus a quarterly status check.
- **Monetization:**
  - Artist-commission referrals, and walking-tour partnerships.
  - **$0-$75/mo**, assuming 1-3k visits/month.
  - No print sales of murals because of artists' rights.
- **Key risks:**
  - Without a feed, the data goes stale as murals change.
  - Artist attribution errors.
  - Competing with Instagram and Google Maps photo spots.
- **Scores:** Usefulness 3 · Uniqueness 3 · Monetization 1 · Low-upkeep 3 · Build ease 4 · Traffic 3 · Skill fit 3 · **Total 20**
- **Why it could be great:** Murals are what visitors actually photograph in Adams Morgan, and a careful, attributed guide supports artists better than a geotagged selfie spot.

---

## Recommendation

**Build #1 (House & Block History Pages) first, with #2 ("100 Years Ago This Week") as its recurring layer.**
- #1 gives permanent, address-level search traffic from CC BY 4.0 and public-domain data, with almost no maintenance.
- #2 adds a weekly email reason to return, at about 30 minutes of human review.
- #3 (Lost Southwest) is the best specific fit for the hard-to-use L'Enfant Plaza domain.

## Sources

- https://catalog.data.gov/dataset/historic-data-on-dc-buildings
- https://catalog.data.gov/dataset/history-quest-dc
- https://dcpreservation.org/places-and-spaces/historyquest-dc/
- https://ggwash.org/view/61696/this-great-tool-will-teach-you-about-historic-buildings
- https://catalog.data.gov/dataset/historic-landmarks
- https://catalog.data.gov/dataset/historic-districts-7b313
- https://dcatlas.dcgis.dc.gov/metadata/HistDisPly.html
- https://catalog.data.gov/dataset/basic-business-licenses
- https://catalog.data.gov/dataset/basic-business-license-in-last-30-days
- https://www.loc.gov/item/sanborn01227_001/ (Sanborn public-domain statement)
- https://www.loc.gov/resource/g3851gm.g3851gm_g012271888/
- https://www.loc.gov/apis/json-and-yaml/requests/
- https://www.loc.gov/item/sn83045462/ (Evening Star, Chronicling America)
- https://www.dclibrary.org/research-and-learn/dig-dc
- https://thepeoplesarchive.dclibrary.org/repositories/2/resources/2149 (Evening Star/Washington Star records: Post holds copyright)
- https://ddotlibrary.omeka.net/permissions-and-usage
- https://dchistory.org/permission-to-publish-request-form/
- https://thepeoplesarchive.dclibrary.org/repositories/2/digital_objects/1384 (DC Oral History Collaborative)
- https://humanitiesdc.org/wp-content/uploads/2023/04/dcohc-survey-public-report.pdf
- https://www.historicchevychasedc.org/resources
- https://tenleytownhistoricalsociety.org/
- https://eventsdc.com/dc-neighborhood-heritage-trails
- https://www.theeagleonline.com/article/2024/05/stepping-through-history-tenleytown-heritage-trail
- https://adamsmorgan.com/about/history
- https://www.petworthnews.org/blog/systemic-racism-in-historic-petworth
- https://ggwash.org/view/64764/how-segregation-shaped-dcs-northernmost-ward-4-petworth-brightwood-takoma-shepherdpark
- https://ghostsofdc.org/2026/04/12/before-fedlandia-lenfant-plaza-southwest-dc-history/
- https://swbid.org/history/
- https://blogs.weta.org/metromap/renewalcenter
- https://en.wikipedia.org/wiki/L%27Enfant_Plaza
- https://streetsofwashington.substack.com
- https://hmdb.org/about.asp
- https://dcarts.dc.gov/page/dcartsemuseum
- https://readtheplaque.com/plaque/walter-pierce-park
- https://1950census.archives.gov/
- https://registry.opendata.aws/nara-1950-census/
- https://stevemorse.org/census/faq1950.htm
