# Business case: DC Neighborhoods

## Summary

Build one automated civic-data platform: a nightly job pulls DC open data, clips it to each neighborhood, and publishes a page plus a weekly email per neighborhood. Make money with a few clearly labeled local sponsors, not ads. Expand to address and block pages for long-tail search traffic. Treat L'Enfant Plaza as a separate, seasonal tourist product.

- **Cost:** about $60–150 a year in cash, plus the weekend build.
- **Time:** 1–2 hours a week once running, and most of that is selling sponsorships, not maintenance.
- **Revenue (estimate):** $0–300/month in the first 6–12 months, with a realistic base case of $600–1,200/month by month 18 if the list grows. Every number here is an estimate unless it cites a source.
- **The bet:** DC already publishes the data. Nobody turns it into something a resident reads every week for these neighborhoods. The pipeline is the hard part, and v1 already has it working on live data.

## Market

**Audience.** Residents, homeowners and renters of four residential neighborhoods: Petworth, Tenleytown, Adams Morgan and Friendship Heights. The secondary audiences are house hunters, ANC commissioners, local reporters, contractors and agents.

**Size.** At about 2,000 residents per SMD, the 6 Petworth SMDs and 11 Tenleytown SMDs in v1 cover roughly 12,000 and 22,000 residents. If one in fifty households subscribes after a year, that is a few hundred subscribers per neighborhood. The documented solo comparable, Side Dish, earns about $6K/month from 2–3K subscribers, so treat "a few hundred" as the floor and 1,000+ as a good outcome.

**Competition and the gap:**

| Neighborhood | Existing outlet | What they do | What they don't |
|---|---|---|---|
| Petworth | Petworth News, PoPville | News, events, newsletter | Structured permit/311/ANC data |
| Tenleytown | Tenleytown Main Street | Events, business promotion | Civic data, development tracking |
| Adams Morgan | Adams Morgan BID | Business map, events | Liquor-license pipeline, noise/trash data |
| Friendship Heights | Friendship Heights Alliance | Property-owner promotion | Neutral "what's being built" tracker |

Position the platform as complementary to these outlets: link to Petworth News stories, give the BIDs' events a free community slot, and never compete on news.

**Evidence from the v1 run (live data, 31 Oct 2026):**
- Petworth: 84 permits, 1,167 311 requests and 49 crime reports in 30 days. Rodent complaints rose 39% (117 vs 84).
- Tenleytown: 115 permits and 1,716 311 requests.

There is a new, specific, true thing to say about each neighborhood every week without anyone writing it.

## Revenue

Benchmarks are from the monetization research ([ideas/monetization.md](ideas/monetization.md)):
- Newsletters under 5K subscribers sell placements for $50–250.
- Side Dish runs 12 sponsors at $500/month on about 2–3K subscribers.
- PoPville charges $99 per announcement.
- Display ads at this scale earn about $25–100/month.

| Stream | Where | Price | Notes |
|---|---|---|---|
| Exclusive "presented by" sponsor on each weekly digest | 4 neighborhoods | $150–400/month each | Realtors, mortgage brokers, title companies, architects. One per neighborhood keeps the .org feel |
| Block-page sponsor (v2) | Address and block pages | $200–500/month per neighborhood | Agents value association with every address search |
| Small sponsor slots (2–3 per issue) | Digest | $50–150/month each | Dentist, gym, contractor, restaurant |
| Annual "State of Petworth" data report | Once a year | $1–5K title sponsor | Press-driven. Year one is a portfolio piece |
| L'Enfant affiliate (v3) | lenfantplaza.net only | Stay22 hotel map and tour links | Seasonal, $50–400/month |
| Domain lease (option) | friendshipheights.org, lenfantplaza.* | $100–1,000/month or sale | Zero upkeep. Gives up that domain |

**Scenarios (estimates, monthly, at month 18):**

| Scenario | Subscribers per neighborhood | Sponsors | Revenue |
|---|---|---|---|
| Conservative | 200–400 | 1 total | $0–300 |
| Base | 600–1,000 | 1 exclusive per neighborhood + 2 small | $600–1,200 |
| Upside | 1,500+ | Side-Dish style, 3–5 per neighborhood | $2,000–4,000 |

Rule: no display ads, no paid placement inside the data, no lead selling, and every sponsor labeled.

## Costs

| Item | Annual cost (estimate) |
|---|---|
| Domains: 4 .org + 3 .net renewals | ~$80–100 (drop the .nets to save ~$35) |
| Cloudflare Workers + static assets | $0 on the free tier; $60/year if you need Workers Paid |
| GitHub Actions | $0 (well under free minutes; one nightly job of ~5 minutes) |
| Email sending (Buttondown, beehiiv or Cloudflare Email) | $0 to start; ~$100–300/year once past free-tier limits |
| LLM permit summaries (optional) | <$5/month at a few hundred permits a month |
| **Total** | **~$80–500/year** |

## Time budget

| Activity | Hours/week |
|---|---|
| Skim the generated digest before it sends | 0.25 |
| Fix a broken feed (averages out; DC renames datasets every January) | 0.1–0.25 |
| Sponsor sales and renewals (once there's a list) | 0.5–1 |
| Optional human note at the top of the digest | 0–0.5 |
| **Total** | **1–2** |

## Milestones

| When | Milestone | Success signal |
|---|---|---|
| Week 1 | v1 live on petworth.org and tenleytown.org | Nightly job green 7 days in a row |
| Week 2 | One post each to the local listserv and r/washingtondc | 100+ visitors not from the launch post |
| Month 1 | Weekly digest email (v1.5) | 100 subscribers total |
| Month 2 | Adams Morgan + Friendship Heights (needs a custom boundary, because DC's "Tenleytown" polygon includes Friendship Heights) | Subscribers growing week over week |
| Month 3 | First sponsor pitch (one realtor per neighborhood), using real open and subscriber numbers | 1 signed sponsor |
| Month 3–4 | Address and block pages (v2), starting with blocks that have rich HistoryQuest records | Search Console impressions on "[street] DC" queries |
| Spring | L'Enfant Transfer Coach (v3), before tourist season | Organic search for "L'Enfant Plaza transfer" |
| Month 12 | Annual data report | Press pickup or BID citation |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Looks official, or is mistaken for the ANC or BID | Medium | Disclaimer on every page, own visual identity, no seals |
| Data feed breaks (dataset renamed, yearly rollover) | High once a year | Ingest resolves "...in {year}" titles automatically; the job fails loudly; a stale banner appears after 3 days |
| Privacy complaint (permit or 311 address) | Low | Owner and applicant names never fetched; 311 coarsened to hundred block; crime counts only |
| Nobody subscribes | Medium | Cheap to test; kill criteria below |
| Sponsor sales take more time than budgeted | Medium | One exclusive sponsor per neighborhood on an annual contract, not many small ones |
| Petworth News sees it as competition | Low | Link to their stories, offer data to them, stay out of news |
| Fear-driven crime framing | Medium | Counts only, no maps of incidents, no percentages on small numbers (already enforced in v1) |

## Kill criteria

Decide at the end of month 4:
- **Keep going** if either neighborhood has 300+ subscribers, or organic search traffic is growing month over month.
- **Pivot** to block and history pages only (an evergreen SEO play with no weekly cadence) if subscribers are flat but block pages get search impressions.
- **Stop** and lease or sell the domains if both are flat. The pipeline and demos remain as a portfolio piece.
