# Content creation and curation

The goal is a site that publishes something new and true every week without anyone writing it, plus a slowly growing layer of evergreen pages that a person shaped. Machines do the volume and you do the judgment, in about 15 minutes a week.

## Content pillars

| Pillar | What it is | Made by | Cadence | Example from v1 data |
|---|---|---|---|---|
| **What's changing** | Permits, demolitions, additions, new construction | Pipeline | Nightly page, weekly digest | "7 permits for demolition, additions or new construction in Petworth this month" |
| **What neighbors report** | 311 trends by type, compared with the prior period | Pipeline | Nightly, weekly | "Rodent complaints up 39% (117 vs 84)" |
| **Who represents you** | SMDs, commissioners, ANC links | Pipeline | Nightly | 6 SMDs across ANC 4C/4D for Petworth |
| **Public safety, in proportion** | Counts by offense, never incidents | Pipeline | Nightly | "49 reports (40 prior)", no percentage, no map |
| **How the block was built** | Original permits, builders, architects, Sanborn links | Pipeline + human caption | One block feature a month | "Cafritz built the whole 400 block of Delafield Pl in 1926: 62 rowhouses on 4 permits" |
| **The month in data** | A short monthly post with 3 charts and 3 sentences | Generated draft + human edit | Monthly | Rodent season, leaf collection, permit spikes |
| **Annual report** | "State of Petworth 2027" | Generated + 1 day of editing | Yearly | Sponsorable, pitchable to press |

## Automation pipeline

1. **Ingest (nightly, GitHub Actions):** `ingest/run.py` pulls permits, 311, crime counts and SMDs for each enabled neighborhood. It finds next year's datasets by title, and it fails the job if any feed is empty or a personal field appears.
2. **Snapshot:** the JSON is committed to git each night. That gives free history for "new since last week" diffs and for the annual report.
3. **Render:** Astro builds every page. Headlines come from rules in `site/src/lib/data.ts`: rank 311 changes by absolute size, ignore small counts, and never put a percentage on fewer than 100 events.
4. **Digest (v1.5):** `demos/make_demos.py` already renders the email. The next step is to send it with Buttondown or beehiiv via their API, on Friday mornings.
5. **Optional LLM pass:** turn raw permit text ("ALTERATION AND REPAIR - INTERIOR RENOVATION...") into one plain sentence. Cache it per permit ID, always show the original text one click away, and run nothing generated through the crime pillar.
6. **Human gate:** the digest is a draft until you click send. That one skim is the whole editorial process.

## Curation rules

**Always:**
- Link every item to its official source.
- Show "data as of" and hide or flag anything older than 3 days.
- Present numbers with their comparison period.
- Give elected officials' names. They're public officials.

**Never:**
- Owner or applicant names from permits (they're never fetched).
- Exact addresses for 311 requests (coarsened to the hundred block).
- Individual crime incidents or crime maps.
- Percentages on small counts.
- Composite "neighborhood scores" that read as steering.
- Paid placement inside the data.
- Historic owner names on block pages.

**Corrections:** a "suggest a correction" email link on every page. Fix within a week, and log the change in a public `CORRECTIONS.md`.

**Sponsors:** labeled "Presented by", visually separate from the data, one exclusive slot per neighborhood digest. No sponsor gets a say over what the data shows.

## Editorial calendar

| When | Content | Effort |
|---|---|---|
| Nightly | Pages refresh | 0 |
| Friday | Weekly digest per neighborhood | 15 min skim |
| First Monday | "Month in data" post per neighborhood | 30 min |
| Mid-month | One block-history feature (rotate neighborhoods) | 30–60 min |
| January | Dataset rollover check (automatic, but watch the first run) | 15 min |
| Seasonal hooks | Spring: rodent season, assessment appeals. Fall: leaf collection. Winter: snow removal. November of even years: ANC elections | 15 min each |
| Yearly | Annual data report | 1 day |

## Distribution

1. **Search:** each neighborhood page targets "[neighborhood] permits", "[neighborhood] 311" and "[neighborhood] ANC". Block pages (v2) target "[street] [neighborhood]". Register both domains in Google Search Console on day one.
2. **RSS:** already live per neighborhood (`/petworth/permits.xml`). It's a cheap subscription and feeds the digest.
3. **One post per launch:** the neighborhood listserv or Google Group, r/washingtondc, and the ANC's public comment period. Be factual and mention that it's independent.
4. **Print:** a QR flyer at the Petworth and Tenley-Friendship library branches and at coffee-shop corkboards. Ask first.
5. **Word of mouth:** the share-worthy units are a block history ("your house was built by Cafritz in 1926") and a big 311 swing ("rodent complaints up 39%"). Make both easy to screenshot.

## Partnerships

- **Petworth News / PoPville:** offer a free data feed or embed. Their reporting plus your data beats either alone. Link to their coverage.
- **ANC commissioners:** send each one the page for their SMD. Commissioners are the most likely early sharers because the data supports their agency asks.
- **BIDs and Main Streets:** a free community-notice slot in the digest for their events. In return, ask for a link.
- **DC HPO / HistoryQuest:** credit the data prominently. Ask them for corrections and for any newer data.
- **Libraries (DCPL):** flyers, and possibly a "history of your block" talk using the block pages.

## Voice

- **Plain and neighborly.** "Rodent complaints are up" beats "Vector control service requests increased".
- **Numbers first, adjectives last.** No "alarming", "surge" or "crisis".
- **Neutral on development.** Report what was filed and link to how to comment. Take no side.
- **Short.** Each digest item is one or two lines. Every item links to the source for anyone who wants detail.
- **Honest about limits.** Say when data is preliminary, lagging or incomplete. The footer already does this on every page.
