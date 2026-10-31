# Transit, visitors, and tech-forward ideas

Lens: WMATA rail/bus, Capital Bikeshare, visitors, accessibility, alerts, AI, displays. Special focus on L'Enfant Plaza, which has few residents but a five-line Metro transfer (Blue, Orange, Silver, Green, Yellow), a VRE stop, and heavy tourist and office foot traffic.

**Constraints that apply to every idea here (verified from the WMATA Transit Data Terms of Use, developer.wmata.com/license):**
- The API is free with a registered key. WMATA says it may start charging later.
- Commercial apps and websites are allowed. You may not re-expose WMATA data through your own public API without written approval (Section 8b). Showing it to your own site's users is fine.
- You can't use WMATA's logo or marks, or imply that WMATA endorses you (Sections 6-7). Don't put "Metro" branding on these sites, and add a "not affiliated with WMATA" footer.
- Getting around call limits (for example, by having users bring their own keys) is prohibited. Build the architecture as one Cloudflare Worker that polls on a cron, caches in KV or D1, and serves every visitor from that cache. That keeps API calls flat no matter how much traffic comes in.

---

## 1. L'Enfant Transfer Coach: "Which escalator, which platform, which exit"

**Pitch:** A phone-first guide to the most confusing transfer in the system, with live arrivals and elevator status baked in.

- **Neighborhoods / audience:** L'Enfant Plaza (lenfantplaza.org). Tourists, conference-goers, VRE commuters, and federal workers changing lines.
- **What the page shows:** A picker that takes "I'm on ___ heading to ___" (for example, "Green toward Branch Ave → Silver toward Ashburn") and returns plain steps for the transfer: which end of the platform to stand at, which escalator bank to take, and roughly how many minutes the walk takes. It also shows live next trains on the connecting platform and flags any elevator or escalator outage on that route, with the step-free alternative. A second tab, "Exits A-F," lists what is above each lettered exit (the Spy Museum, the Wharf shuttle stop, the Mall, the HUD and DOT buildings, the VRE platform) and its walk time. Each exit gets a short URL like `lenfantplaza.org/a`. Static Astro pages carry the routes, and a small Worker island adds live data.
- **Sources:**
  - WMATA Rail Predictions and Incidents APIs, developer.wmata.com (verified). Elevator outages come from `https://api.wmata.com/Incidents.svc/json/ElevatorIncidents?StationCode=…` (verified), which refreshes about every 20-30 seconds.
  - WMATA's own step-by-step accessible wayfinding pages for L'Enfant (verified, wmata.com/ride/accessibility/metro-wayfinding/…). Use them as reference only; write your own text.
  - The WMATA lettered-exit wayfinding pilot at L'Enfant Plaza (verified via WJLA and a WMATA board PDF).
  - Platform and escalator positions: you would survey these in person once. Platform end positions are unverified until then.
- **Ongoing effort:** 0.5 h/week. Re-check routes when WMATA changes signage or construction closes an escalator bank.
- **Monetization:** $0-150/month. Assumes about 10-20k sessions/month in tourist season. Options are a tasteful sponsor slot (a hotel or the SW BID) or a "Buy me a coffee" link. Hotel concierges might want a printable PDF version. Keep it clean of ads because of the .org domain.
- **Key risks:** WMATA's own signage keeps improving, which shrinks the problem. Wrong directions during track work erode trust, so the page needs a visible "last verified" date. Traffic depends on SEO for "L'Enfant Plaza transfer" queries.
- **Scores:** Usefulness 5 · Uniqueness 4 · Monetization 2 · Low-upkeep 4 · Build ease 4 · Traffic 4 · Skill fit 5 · **Total 28**
- **Why it could be great:** Nobody else answers "how do I get from Green to Silver at L'Enfant without getting lost" in under ten seconds, and the domain name is the exact search term.

---

## 2. Step-Free Status: elevator outage pages and alerts for the five neighborhoods' stations

**Pitch:** Live and historical elevator status for each neighborhood's station, with free email or push alerts and the nearest working alternative.

- **Neighborhoods / audience:** All five. The stations are L'Enfant Plaza, Tenleytown-AU, Friendship Heights, Georgia Ave-Petworth, and Woodley Park/Columbia Heights for Adams Morgan. Audience is wheelchair users, parents with strollers, travelers with luggage, and older residents.
- **What the page shows:** A status block on each neighborhood site's home page (green, or a red "Street elevator out since Tue"). An uptime chart for the last 90 days. If an elevator is out, a "plan B" line: the nearest accessible station, and the WMATA shuttle-bus note when one runs. Subscribing works through ntfy.sh topics or email digests from Cloudflare Email Workers or Resend. SMS is deliberately left out because of cost and carrier registration.
- **Sources:** WMATA ElevatorIncidents API (verified). The ELstat sign-up is mentioned on wmata.com/service/elevators-escalators (verified). History has to be built by snapshotting into D1 every 5 minutes.
- **Ongoing effort:** 0.25 h/week.
- **Monetization:** $0-50/month. Donations only. This is a civic good, and ads next to accessibility info would look bad.
- **Key risks:** **Competitor:** elevatoruptime.com already publishes per-station uptime and 90-day logs for WMATA (verified), and WMATA has ELstat alerts. The differentiators are being neighborhood-embedded and offering plan-B routing, which is thin. Alert delivery adds a small support burden.
- **Scores:** Usefulness 4 · Uniqueness 2 · Monetization 1 · Low-upkeep 5 · Build ease 5 · Traffic 2 · Skill fit 5 · **Total 24**
- **Why it could be great:** It's a weekend build, and it becomes a shared widget that makes every one of the eight domains more useful on day one.

---

## 3. Last Ride Home (Adams Morgan nightlife edition)

**Pitch:** A late-night board that answers "can I still catch a train, and if not, which bus or bike?"

- **Neighborhoods / audience:** Adams Morgan primarily (18th St bars, with Woodley Park and Columbia Heights stations about 10-15 minutes' walk away). Also Petworth. Audience is bar-goers, restaurant staff, and visitors.
- **What the page shows:** A large-type countdown to the last train in each direction from the two nearest stations, with walk time added. Live late-night bus arrivals. Capital Bikeshare docks near 18th St with bikes and e-bikes available right now, and dock space at the destination. A "share my ETA" link. The board goes dark-mode after 10pm. QR table tents could go to bars that opt in.
- **Sources:**
  - WMATA Rail Predictions, Bus Predictions, and GTFS static schedules (verified).
  - WMATA bus GTFS-RT `bus-gtfsrt-tripupdates.pb` (verified; GTFS-RT 1.0 only).
  - Capital Bikeshare GBFS 1.1: `https://gbfs.lyft.com/gbfs/1.1/dca-cabi/gbfs.json` with `station_status`, `station_information`, and `ebikes_at_stations` (verified live). The license is listed in `system_information.license_url`, which was not opened (unverified terms; Lyft's bikeshare data license generally allows display).
- **Ongoing effort:** 0.5 h/week. The Better Bus network redesign renamed routes, so GTFS should refresh automatically through an Action.
- **Monetization:** $50-300/month. Assumes 5-15k sessions/month on weekends. Bar sponsorship ("brought to you by ___", one sponsor at a time) fits a .org domain if it's clearly labeled. Lyft or Capital Bikeshare affiliate links are unverified.
- **Key risks:** Transit app, Citymapper, and Google Maps already cover this generically. The value is hyper-local framing and QR distribution, which depends on bar partnerships (owner time). Late-night hours in Metro's service plan change.
- **Scores:** Usefulness 4 · Uniqueness 3 · Monetization 3 · Low-upkeep 4 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 26**
- **Why it could be great:** One QR code on a bar table is the cheapest, most context-perfect distribution channel any of these sites will get.

---

## 4. Lobby Boards: free e-ink and kiosk transit displays for local businesses (unusual)

**Pitch:** A free, branded "next train / next bus / bikes nearby" display URL for any café, office lobby, or church in the five neighborhoods. There's a paid TRMNL e-ink version too.

- **Neighborhoods / audience:** All. Audience is small businesses, apartment lobbies, libraries, and L'Enfant office-building lobbies.
- **What the page shows:** `tenleytown.org/board/<slug>` renders a full-screen, auto-refreshing board for a chosen stop set, with a small credit line for the neighborhood site. Variants include an old-tablet kiosk mode, a TV mode, and an 800×480 1-bit image endpoint for TRMNL or Kindle-style e-ink screens. A Worker renders the image server-side.
- **Sources:**
  - WMATA APIs (verified). Data stays within your own app, so this complies with Section 8.
  - CaBi GBFS (verified).
  - TRMNL device: 7.5" 800×480 monochrome display, BYOS (bring-your-own-server) plugins (verified via the TRMNL shop and the open-source Munich plugin). I found no existing WMATA TRMNL plugin (search only; absence is unverified).
- **Ongoing effort:** 0.5-1 h/week, mostly onboarding new boards through a self-serve form.
- **Monetization:** $100-500/month if 10-30 businesses pay $10-20/month for custom branding, or if pre-configured e-ink units sell at a $40-60 markup. The free tier drives backlinks. **Competitor:** TransitScreen (DC-based) sells commercial lobby screens (verified; a 2013 price of about $2k/screen, current pricing unverified). You'd be the cheap, hyperlocal alternative.
- **Key risks:** Hardware support is a time sink. Under WMATA's terms, one key serves everyone, so heavy board counts must stay on the shared cache. Refresh is limited to about 1-5 minutes. That's fine for e-ink but not second-accurate.
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 3 · Low-upkeep 3 · Build ease 3 · Traffic 2 · Skill fit 5 · **Total 23**
- **Why it could be great:** Every board is a physical, always-on advertisement for the neighborhood site sitting in a storefront.

---

## 5. Will There Be a Bike? Bikeshare dock reliability forecasts

**Pitch:** Historical odds that a Capital Bikeshare dock will have a bike (or an open slot) at a given hour on a given weekday, for every station in each neighborhood.

- **Neighborhoods / audience:** All. It's strongest for Petworth, Tenleytown, and Adams Morgan commuters, and for L'Enfant office workers docking at 9am.
- **What the page shows:** For each station: live counts, plus a heatmap (hour × weekday) of "probability of zero bikes" and "probability of a full dock." E-bike availability is shown separately. A plain-English note sits with each, like "Arrive before 8:10 on weekdays or expect it empty." There's a monthly auto-written "rebalancing report card."
- **Sources:**
  - CaBi GBFS `station_status` and `ebikes_at_stations` (verified live). Snapshot every 2-5 minutes into D1 or R2 Parquet from a cron Worker.
  - Monthly trip-history CSVs from capitalbikeshare.com/system-data (unverified this session, though they've long been published).
- **Ongoing effort:** 0.25 h/week once the pipeline runs. It needs about 4-6 weeks of data before the forecasts mean anything.
- **Monetization:** $0-100/month. Assumes 3-8k sessions/month. Options are display ads or a local bike-shop sponsor. It works as a portfolio and data-journalism piece.
- **Key risks:** It's a niche audience. Lyft could change the feed (it's GBFS 1.1, and v2/v3 migrations happen). D1 row growth (about 50 stations × 288 snapshots/day) needs rollups.
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 2 · Low-upkeep 5 · Build ease 4 · Traffic 2 · Skill fit 5 · **Total 25**
- **Why it could be great:** It's genuinely new information. Every app shows bikes right now, and nobody tells you whether to trust that dock at 8:15 tomorrow.

---

## 6. Ask L'Enfant: an AI visitor concierge grounded in live data (unusual)

**Pitch:** A chat box that answers "I have 3 hours and a stroller, the Air & Space Museum is closed, what's near me?" using only verified, live sources.

- **Neighborhoods / audience:** L'Enfant Plaza first, then extendable to all. Audience is tourists, conference attendees, and hotel guests.
- **What the page shows:** A single chat page plus suggested prompts. Behind it is retrieval over a curated corpus that is refreshed by cron: museum hours, NPS alerts and events, WMATA arrivals and elevator status, the SW Shuttle schedule, weather, and walk times. Answers cite their source and "as of" time, and it refuses anything outside scope. Cloudflare Workers AI or the Claude API handles generation, and Vectorize does retrieval.
- **Sources:**
  - NPS API `https://developer.nps.gov/api/v1/alerts` and `/events`, free key (verified). Park code `nama` for National Mall and Memorial Parks is unverified.
  - Smithsonian Open Access API via api.data.gov (verified; collections metadata only). **Museum hours have no API.** You'd scrape si.edu/visit, which is unverified as stable.
  - WMATA APIs (verified).
  - SW Shuttle: free loop connecting the Wharf, L'Enfant Metro/VRE, and the Mall, with weekday 7am-7pm hours (verified at wharfdc.com/getting-here/the-wharf-shuttle). Seasonal schedule changes need watching.
- **Ongoing effort:** 1-1.5 h/week. Review logs for bad answers and fix scrapers.
- **Monetization:** $50-400/month. Assumes 5-20k sessions/month. Tour affiliate links (GetYourGuide or Viator, about 8% commission, unverified) would conflict with a .org domain, so **use lenfantplaza.net** for any commerce. LLM inference costs offset part of the revenue (roughly $10-60/month at this volume, estimated).
- **Key risks:** Hallucinated hours or directions are a real harm to visitors, so it needs strict grounding and refusal. Prompt abuse could drive up costs. Generic assistants (ChatGPT, Google AI Overviews) are tough competition, so the edge is live, local freshness.
- **Scores:** Usefulness 4 · Uniqueness 4 · Monetization 3 · Low-upkeep 2 · Build ease 3 · Traffic 3 · Skill fit 4 · **Total 23**
- **Why it could be great:** A narrowly grounded, citation-first assistant for one transit hub is a strong portfolio piece, and it answers combinational questions that maps can't.

---

## 7. Mall Day Planner from L'Enfant

**Pitch:** A one-page visitor dashboard for the morning of your Mall day: what's open, what's closed, what's crowded, and how to get there from L'Enfant.

- **Neighborhoods / audience:** L'Enfant Plaza. Audience is tourists, school groups, and families staying at SW and Wharf hotels.
- **What the page shows:**
  - Today's closures and alerts on the Mall (NPS).
  - Museum open/closed status.
  - A heat-index or rain banner with water-fountain and restroom pointers.
  - Free SW Shuttle next-run info.
  - Walking times from each L'Enfant exit to the top 15 sights.
  - Elevator status for stroller routes.
  - A "Today on the Mall" list of permitted events and demonstrations.
  - A printable PDF for hotel front desks.
- **Sources:** NPS API alerts and events (verified), the NWS API at api.weather.gov (well known, not re-verified this session), si.edu hours by scrape (unverified), WMATA (verified), and the SW Shuttle page (verified). The DC Circulator, including its National Mall route, ended at the end of 2024 (verified), so there's a gap in "how do I get around the Mall" info.
- **Ongoing effort:** 0.5-1 h/week, mostly scraper maintenance.
- **Monetization:** $100-500/month on lenfantplaza.net. Assumes 15-40k sessions/month from spring through fall. Options are display ads, tour and ticket affiliates, and hotel sponsorship. Keep the .org version ad-free.
- **Key risks:** Seasonal traffic. Heavy competition from washington.org (Destination DC), NPS.gov, and travel blogs. SEO ranking is the main hurdle. Overlaps with idea 6, so build this first and add the chat later.
- **Scores:** Usefulness 4 · Uniqueness 3 · Monetization 4 · Low-upkeep 3 · Build ease 4 · Traffic 4 · Skill fit 5 · **Total 27**
- **Why it could be great:** It turns a domain with no residents into the obvious morning-of page for the millions of visitors who funnel through that station.

---

## 8. Bus Report Card: automated reliability grades for neighborhood bus lines

**Pitch:** Monthly auto-published on-time and headway grades for the buses that actually serve each neighborhood, computed from GTFS-RT.

- **Neighborhoods / audience:** Petworth, Adams Morgan, Tenleytown, and Friendship Heights. These are bus-dependent residential areas. Audience is residents, ANC commissioners, and transit advocates (Greater Greater Washington readers).
- **What the page shows:** For each route and stop: scheduled vs. observed headways, the percentage of gaps over 2× schedule, "ghost bus" counts (scheduled trips that never appeared in the real-time feed), and a trend chart. Each month gets an auto-written plain-English summary and a shareable chart image for ANC meetings.
- **Sources:**
  - WMATA bus GTFS-RT trip updates (verified) and vehicle positions (endpoint name unverified).
  - WMATA GTFS static (verified).
  - A cron Worker snapshots the data, and a monthly GitHub Action runs the Python analytics and commits charts.
  - Prior art: MetroHero did rail performance and shut down in 2023, though forks lived on (verified). No current bus-grade site was found (search-limited).
- **Ongoing effort:** 0.5 h/week.
- **Monetization:** $0-100/month. Assumes 2-5k sessions/month. Grants or sponsorship from advocacy groups are possible but unverified. Mainly portfolio and civic credibility.
- **Key risks:** Methodology disputes with WMATA. A GTFS-RT 1.0 feed may lack fields the analysis needs. Route renames after the Better Bus redesign. Publishing aggregate statistics is fine, but don't publish a raw-data API (Section 8).
- **Scores:** Usefulness 4 · Uniqueness 4 · Monetization 1 · Low-upkeep 4 · Build ease 3 · Traffic 2 · Skill fit 5 · **Total 23**
- **Why it could be great:** It gives residents hard numbers to bring to their ANC, and it's the kind of automated data journalism that gets cited by local press.

---

## 9. Border Board: Friendship Heights DC + MD transit in one view

**Pitch:** The only departure board that treats Friendship Heights as one place: Metro, WMATA buses, and Montgomery County Ride On, plus construction detours.

- **Neighborhoods / audience:** Friendship Heights. Audience is commuters and shoppers crossing Western Ave, and new residents of the Mazza redevelopment.
- **What the page shows:** Combined next departures at the Friendship Heights bus bays and station. Ride On routes are tagged MD. Elevator status. Bikeshare plus the MD side of the system. A "construction and detours" panel drawn from DC building permits and DDOT notices.
- **Sources:**
  - WMATA APIs (verified).
  - Montgomery County Ride On GTFS and GTFS-RT (unverified; MCDOT has historically published GTFS through data.montgomerycountymd.gov).
  - Open Data DC building permits (confirmed in the brief).
  - CaBi GBFS covers the MD stations (verified feed; station coverage not checked).
- **Ongoing effort:** 0.5 h/week.
- **Monetization:** $50-200/month. Assumes 3-8k sessions/month. Sponsorship from the redeveloper's leasing office or retailers, on friendshipheights.org only if clearly labeled.
- **Key risks:** Ride On feed availability or terms are unverified. The audience is small. The Friendship Heights Alliance BID could build something similar.
- **Scores:** Usefulness 3 · Uniqueness 4 · Monetization 2 · Low-upkeep 4 · Build ease 3 · Traffic 2 · Skill fit 5 · **Total 23**
- **Why it could be great:** Every regional app splits along the DC/MD border, and this one is built around the fact that this neighborhood doesn't.

---

## 10. Crowd Forecast: event-surge alerts for L'Enfant and the Green/Yellow line (unusual)

**Pitch:** A "how bad will Metro be today" forecast built from the calendar of things that flood L'Enfant: Mall events, Wharf concerts, Nats games, and federal events.

- **Neighborhoods / audience:** L'Enfant Plaza primarily, with Petworth (on the Green line) as a secondary audience. Audience is office workers, commuters, and VRE riders.
- **What the page shows:**
  - A daily 1-5 crowd score with reasons, for example "Nats home game 7:05pm + Anthem show → Green line packed 5:30-7pm southbound."
  - Current WMATA rail incidents.
  - A weekly email digest every Monday (Cloudflare Email or Resend), plus an ICS calendar feed people can subscribe to.
- **Sources:**
  - NPS events for the Mall (verified API).
  - WMATA Rail Incidents (verified).
  - Nationals schedule via the MLB Stats API (unverified terms).
  - Anthem and Wharf event calendars by scrape (unverified).
  - Planned track work from wmata.com service notices (scrape, unverified).
- **Ongoing effort:** 1 h/week. Scrapers break, and the scores need a sanity check.
- **Monetization:** $50-250/month. Assumes 1-3k newsletter subscribers plus about 5k sessions/month. The newsletter could take one sponsor per issue.
- **Key risks:** Forecasts without ridership ground truth are guesswork. WMATA publishes ridership data, but how granular it is was unverified. Scraping event sites is fragile. Getting a crowd call wrong costs credibility.
- **Scores:** Usefulness 3 · Uniqueness 5 · Monetization 2 · Low-upkeep 2 · Build ease 3 · Traffic 2 · Skill fit 4 · **Total 21**
- **Why it could be great:** No app warns you that the 5:45 Green line will be a sardine can because three unrelated venues let out at once, and this one would.

---

## Summary ranking

| # | Idea | Total |
|---|------|-------|
| 1 | L'Enfant Transfer Coach | 28 |
| 7 | Mall Day Planner from L'Enfant | 27 |
| 3 | Last Ride Home | 26 |
| 5 | Will There Be a Bike? | 25 |
| 2 | Step-Free Status | 24 |
| 4 | Lobby Boards | 23 |
| 6 | Ask L'Enfant AI concierge | 23 |
| 8 | Bus Report Card | 23 |
| 9 | Border Board | 23 |
| 10 | Crowd Forecast | 21 |

**Best single bet:** Idea 1 (L'Enfant Transfer Coach) on lenfantplaza.org, with idea 7 on lenfantplaza.net as its commercial companion. Both use one shared Worker cache for WMATA, NPS, and GBFS data, and the elevator-status widget from idea 2 can be dropped into all five neighborhood sites for free.

## Sources

- WMATA Transit Data Terms of Use: https://developer.wmata.com/license
- WMATA developer portal: https://developer.wmata.com/ and https://www.wmata.com/about/developers.html
- WMATA ElevatorIncidents API docs: https://developer.wmata.com/docs/services/54763641281d83086473f232/operations/54763641281d830c946a3d76
- WMATA GTFS / GTFS-RT docs: https://developer.wmata.com/docs/services/gtfs/operations/5cdc51ea7a6be320cab064fe
- MobilityDatabase WMATA GTFS-RT listing: https://mobilitydatabase.org/feeds/gtfs_rt/mdb-1851
- WMATA elevators and escalators (ELstat): https://www.wmata.com/service/elevators-escalators
- WMATA L'Enfant accessible wayfinding example: https://www.wmata.com/fr/ride/accessibility/metro-wayfinding/lenfant-wmata-green-yellow-towards-branch.html
- WJLA, L'Enfant wayfinding pilot: https://wjla.com/news/local/metro-unveils-new-wayfinding-system-at-lenfant-plazabut-not-everyone-is-rejoicing
- WMATA 3D Wayfinding board update: https://www.wmata.com/about/board/meetings/board-pdfs/upload/3D-Wayfinding-and-Customer-Service-Improvement-Update.pdf
- Capital Bikeshare GBFS discovery feed: https://gbfs.capitalbikeshare.com/gbfs/gbfs.json (resolves to https://gbfs.lyft.com/gbfs/1.1/dca-cabi/gbfs.json)
- GBFS spec reference: https://gbfs.org/reference
- Competitor, elevator uptime: https://www.elevatoruptime.com/
- MetroHero shutdown: https://dcist.com/story/23/02/10/metrohero-app-shutting-down-wmata-metro-bus-train-wait-times and https://en.wikipedia.org/wiki/MetroHero
- TransitScreen (competitor, lobby displays): https://technical.ly/software-development/transitscreen-mobility.md
- TRMNL device and Munich BYOS plugin: https://shop.usetrmnl.com and https://github.com/giglabo/munich-glance
- NPS Data API: https://www.nps.gov/subjects/developer/get-started.htm and https://www.nps.gov/subjects/digital/nps-data-api.htm
- Smithsonian Open Access API: https://www.si.edu/openaccess/devtools
- SW Shuttle (Wharf, L'Enfant, Mall): https://www.wharfdc.com/getting-here/the-wharf-shuttle/
- DC Circulator end of service: https://en.wikipedia.org/wiki/DC_Circulator and https://m.washingtontimes.com/news/2024/dec/31/dc-circulator-buses-reached-end-line/
