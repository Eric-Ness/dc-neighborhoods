# Monetization lens: ideas for the five DC neighborhood domains

Lens: how these sites could earn money with 1-3 hours/week of upkeep. Benchmarks first, then the ideas.

## Revenue benchmarks found (what's realistic)

- **Small local newsletters sell sponsorships at low absolute prices.** beehiiv's guides put lists under 5K subscribers at about $50-$250 per placement ([beehiiv](https://www.beehiiv.com/blog/newsletter-sponsorship-cost)). Another beehiiv-hosted guide says $50-$150 per placement at 1,000 subscribers ([beehiiv blog](https://beehiivblog.beehiiv.com/p/how-much-money-can-you-make-from-1-000-newsletter-subscribers-in-2025)). One local publisher says beehiiv's ad network paid less than the deals it sold directly ([beehiiv](https://www.beehiiv.com/blog/how-beehiiv-powers-our-local-newsletter-strategy)).
- **The best-documented solo comparable is Side Dish with Schniper**, a Colorado Springs food newsletter. It reportedly has about 2,000-3,000 subscribers and earns about $6K/month from 12 exclusive local sponsors paying $500/month each ([Niche Site Growth](https://nichesitegrowth.beehiiv.com/p/this-newsletter-makes-7k-mo-from-3-000-subscribers)). Spokane Pulse reports 7,400 subscribers and about $2K/month in ads, but that comes from a forum post and is weak evidence ([Skool post](https://www.skool.com/claude-code-pirates-8106/my-hyperlocal-newsletter-spot-report)).
- **City-scale operations (for context, not for comparison):** 6AM City targets about 100K subscribers and $1M/year per city, with roughly $250K in costs per market ([Press Gazette](https://pressgazette.co.uk/news/6am-city-ryan-heafy-interview/)). Axios Local made $5M in 2021 and $8.6M in 2022 against a $10M forecast, and its revenue split was about 60% local and 40% national advertisers ([Press Gazette](https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/), [Nieman Lab](https://www.niemanlab.org/2021/06/ted-williams-proved-local-news-can-be-profitable-now-hell-try-to-replicate-the-success-for-axios/)).
- **Patch's average ad order is about $48.** Its self-serve calendar and announcement postings are its highest-margin product ([AdExchanger](https://www.adexchanger.com/the-sell-sider/patchs-ceo-makes-hyperlocal-profitable/)). PoPville charges $99 for a user-submitted announcement that includes newsletter placement, on a site with about 500K monthly uniques ([PoPville advertise](https://www.popville.com/advertise/)).
- **Display ads won't pay at this size.** Mediavine Journey accepts sites from 1,000 sessions/month ([Productive Blogging](https://www.productiveblogging.com/everything-you-need-to-know-about-journey-by-mediavine/)). Typical RPMs are about $5-20 ([upgrowth](https://upgrowth.in/website-ad-revenue-2026/)), so 5,000 pageviews comes to about $25-100/month.
- **Affiliate:** Lemonade renters insurance pays about $15-25 per lead or sale, depending on the network ([affilimate](https://affilimate.com/programs/lemonade-affiliate-program/)). Stay22 hotel maps pay a 30%+ share of the booking partner's commission ([Stay22 FAQ](https://stay22.com/faq)). Multifamily landlords pay about $10-90 per rental lead ([RentEngine](https://rentengine.io/blog/rental-lead-worth)).

**Honest takeaway:** for a part-time operator, direct sales of a small number of exclusive local sponsorships beat ads and affiliate by roughly 10x. Ad networks and affiliate links are filler. Every sponsorship idea below needs about an hour a month of selling, and that is the real constraint.

---

## 1. Data Digest + Exclusive Sponsors: an automated weekly neighborhood email with 3-6 sponsor slots

- **Pitch:** An auto-generated Friday email for each neighborhood: new permits, liquor-license notices, 311 trends, new restaurant inspections and Metro disruptions. It runs the Side Dish model of a few exclusive local sponsors on a flat monthly fee.
- **Neighborhoods / audience:** Tenleytown, Friendship Heights and Adams Morgan first; Petworth last, because Petworth News already has a strong newsletter. Audience: residents, homeowners and ANC watchers.
- **What the page shows:** A web archive of each issue plus the sign-up box. Each issue has five sections of data, each item one line with a map link, and a "Presented by" block at the top and middle.
- **Sources:** Open Data DC permits, 311 and crime ([opendata.dc.gov](https://opendata.dc.gov)); ABCA weekly issuance PDFs ([example](https://abca.dc.gov/sites/default/files/dc/sites/abra/page_content/attachments/Weekly%20Issuance%20-%202-20-2026.pdf)); WMATA API ([developer.wmata.com](https://developer.wmata.com), unverified in this pass). A GitHub Action builds the issue and Beehiiv or Buttondown sends it.
- **Ongoing effort:** 1-1.5 hrs/week: a 10-minute skim of each draft plus sponsor emails.
- **Monetization:** 3-6 sponsors per neighborhood (realtor, dentist, gym, restaurant, plumber) at $100-300/month at 800-2,000 subscribers, which is **$300-1,500/month per neighborhood, and $900-4,000 across three** (estimate). Side Dish gets $500/sponsor at about 2-3K subscribers. The first 6-12 months will likely bring $0-300/month while the list grows.
- **Key risks:** Growing a list without original reporting is slow. Sponsor churn. On .org domains, sponsor blocks must be clearly labeled. Crime data can make the email read as fear-driven, so lead with permits and openings.
**Scores:** Usefulness 4 · Uniqueness 3 · Monetization 4 · Low-upkeep 4 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 27**
- **Why it could be great:** It is the one proven solo hyperlocal revenue model, and the owner's automation skills replace the writer that model normally needs.

## 2. Realtor Market Page: one exclusive agent sponsors each neighborhood's housing-data page

- **Pitch:** An auto-updated "[Neighborhood] Housing Pulse" page: monthly sales, median prices, rent ranges, new units from permits and pipeline projects such as the Residences at Mazza. One local real estate agent or team sponsors it for 12 months.
- **Neighborhoods / audience:** Tenleytown, Friendship Heights (high home values plus Mazza lease-up), Petworth and Adams Morgan. Not L'Enfant Plaza, which has few residents. Audience: buyers, sellers and renters researching a move.
- **What the page shows:** Price and rent trend charts, a "new housing coming" list built from permits (new building or 5+ units), a building-by-building rent snapshot, and a sponsor card with headshot and contact link.
- **Sources:** Redfin Data Center neighborhood downloads (unverified); RentCafe and RentHop neighborhood rent pages ([RentCafe Tenleytown](https://www.rentcafe.com/average-rent-market-trends/us/dc/washington/tenleytown/), [RentHop Petworth](https://www.renthop.com/average-rent-in/petworth-washington-dc)); permits from opendata.dc.gov; UrbanTurf pipeline ([Mazza entry](https://dc.urbanturf.com/pipeline/1241/The_Residences_At_Mazza)).
- **Ongoing effort:** 0.5 hr/week once built; the data refreshes monthly.
- **Monetization:** One agent per neighborhood at $250-750/month on an annual contract. Agents already pay for hyperlocal farming such as postcards and Zillow Premier Agent. **Four neighborhoods: $1,000-3,000/month** (estimate) at only about 1,500-5,000 pageviews/month per page, because the agent is buying brand association as much as clicks.
- **Key risks:** Sales listings data may be licensed (MLS rules). Each sponsor needs a yearly renewal pitch. A "sponsored by a realtor" page on a .org can look like an ad, so keep the data neutral and add a disclosure.
**Scores:** Usefulness 4 · Uniqueness 4 · Monetization 4 · Low-upkeep 5 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 29**
- **Why it could be great:** One signed contract per neighborhood pays more than thousands of ad impressions, and the page runs itself.

## 3. Permit & License Lead Feed: a B2B email or CSV of new projects for contractors and suppliers

- **Pitch:** A weekly feed of new building permits (renovations, additions, new construction, demolition) and ABCA license applications. It is sold to contractors, architects, solar and roofing installers, restaurant suppliers and commercial brokers.
- **Neighborhoods / audience:** Starts with all five, but buyers want a whole territory. Realistically it expands to citywide under a neutral brand, with the neighborhood sites as the showroom. Audience: trades and B2B vendors, not residents.
- **What the page shows:** Free public view of the last 7 days with addresses partly masked. Paid tier: full CSV, filters by permit type and dollar value, email and webhook delivery, and new-liquor-license leads with license class.
- **Sources:** Open Data DC Building Permits ([opendata.dc.gov](https://opendata.dc.gov)); ABCA weekly issuance and placard PDFs ([abca.dc.gov](https://abca.dc.gov/sites/default/files/dc/sites/abra/page_content/attachments/Weekly%20Issuance%20-%2012-19-2025.pdf)). Comparable products: Construction Monitor ([site](https://www.constructionmonitor.com)), Permit Ledger ([Product Hunt](https://www.producthunt.com/products/permit-ledger/makers)), and permit scrapers on Apify at about $3-4 per 1,000 results ([Apify](https://apify.com/ledgerstar/building-permits)).
- **Ongoing effort:** 0.5-1 hr/week; customer support is minimal.
- **Monetization:** $29-79/month per subscriber, with Stripe on Cloudflare Workers. **10-30 subscribers citywide comes to $300-2,000/month** (estimate). Five neighborhoods alone would support perhaps 3-8 subscribers ($100-500/month, estimate).
- **Key risks:** The data is free, so competitors can copy it and buyers can build it themselves. Coverage of five neighborhoods is too thin to sell. Check ABCA terms before outreach use. Sales means cold outreach to tradespeople.
**Scores:** Usefulness 3 · Uniqueness 3 · Monetization 3 · Low-upkeep 5 · Build ease 4 · Traffic 2 · Skill fit 5 · **Total 25**
- **Why it could be great:** It's pure data engineering the owner already knows how to do, and B2B buyers pay for saved time, not for content.

## 4. Grand Opening Spotlight: a new-business tracker with paid $49-149 launch features

- **Pitch:** An automatically detected list of "what's opening" built from liquor-license applications, new food-establishment inspections and commercial build-out permits. New businesses can buy a one-time spotlight in the page and newsletter.
- **Neighborhoods / audience:** Adams Morgan (dense restaurant churn), Friendship Heights (Mazza retail: Wonder food hall, Total Wine, TJ Maxx), and Tenleytown. Audience: residents and food fans.
- **What the page shows:** A pipeline from "applied" to "permitted" to "inspected" to "open". Each item gets a card with its source document and a "Claim this listing" link for owners. Paid spotlights are badged "Featured".
- **Sources:** ABCA PDFs; DC Health inspection search (manual, no bulk feed per BRIEF); permits on opendata.dc.gov; Friendship Heights retail news ([Axios DC](https://www.axios.com/local/washington-dc/2025/10/31/friendship-heights-new-apartments-total-wine-trader-joes)).
- **Ongoing effort:** 1 hr/week to sanity-check the auto-detected items and handle claims.
- **Monetization:** Patch's average order is $48 and PoPville charges $99 per announcement. At 2-6 spotlights a month across the sites at $49-149: **$100-900/month** (estimate), assuming roughly 2,000+ monthly visitors plus a newsletter.
- **Key risks:** Opening volume in five neighborhoods is low, perhaps 3-10 a month (estimate). Auto-detection makes mistakes: an applied license is not an opening. BIDs already promote openings for free.
**Scores:** Usefulness 4 · Uniqueness 4 · Monetization 2 · Low-upkeep 4 · Build ease 3 · Traffic 3 · Skill fit 4 · **Total 24**
- **Why it could be great:** "What's opening on my block" is the most shareable local content there is, and here it comes from data instead of a reporter.

## 5. Building Report Cards for Renters, with affiliate and featured-building revenue

- **Pitch:** One page per large apartment building: permits pulled, 311 complaints at the address (housing code, rodents, heat), nearby crime and Metro walk time, plus a rent range. It earns from renters-insurance and moving affiliate links and from "verified building" profiles that buildings pay for.
- **Neighborhoods / audience:** Petworth, Adams Morgan, Tenleytown, Friendship Heights (the Mazza lease-up), and to a lesser degree L'Enfant/SW. Audience: renters comparing buildings, a group that is very search-driven.
- **What the page shows:** A letter grade or traffic-light summary per address, a 311 complaint timeline, a permit history, and "Moving here? Renters insurance / movers / internet" affiliate cards.
- **Sources:** Open Data DC 311 and permits (address-level); building rent listings such as [Apartments.com Mazza units](https://www.apartments.com/5300-wisconsin-ave-nw-washington-dc-unit-419/mfrgs7l/) (used for reference only, not scraped); Lemonade affiliate ([affilimate](https://affilimate.com/programs/lemonade-affiliate-program/)).
- **Ongoing effort:** 0.5-1 hr/week.
- **Monetization:** Affiliate at about $15-25 per renters-insurance conversion: 5-20 a month is $75-500. Featured building profiles at $100-300/month from 1-4 buildings is $100-1,200. Rental-lead referrals have market value of $10-90 each ([RentEngine](https://rentengine.io/blog/rental-lead-worth)). **Total $150-1,500/month** (estimate) at 5,000-15,000 monthly organic visits.
- **Key risks:** Landlords may push back on negative grades (defamation risk if grades are opinions, so show raw public data). Taking money from buildings you grade is a conflict of interest, which is especially bad on .org; keep paid profiles off the .org domains or drop them. SEO competition from ILS sites.
**Scores:** Usefulness 5 · Uniqueness 4 · Monetization 3 · Low-upkeep 4 · Build ease 3 · Traffic 4 · Skill fit 5 · **Total 28**
- **Why it could be great:** Renters badly want this information and nobody puts DC's 311 history next to a building's name.

## 6. L'Enfant Plaza Transfer Companion: transit and visitor utility with hotel and tour affiliate

- **Pitch:** A fast mobile page for the 5-line transfer hub: live train arrivals, elevator and escalator outages, which exit leads to which museum, food open now, plus a Stay22 hotel map and tour and ticket affiliate links for the tourists and conference-goers passing through.
- **Neighborhoods / audience:** L'Enfant Plaza (.net is the commercial domain, so commerce fits). Audience: commuters, tourists, Wharf and Mall visitors.
- **What the page shows:** Arrival boards by platform, a status strip for elevators out, a walking-time grid to the Air and Space Museum, the Wharf and Nationals Park, and a "Stay nearby" map.
- **Sources:** WMATA developer API for arrivals and elevator incidents ([developer.wmata.com](https://developer.wmata.com), unverified in this pass); Stay22 ([FAQ](https://stay22.com/faq)); GetYourGuide or Viator affiliate (unverified).
- **Ongoing effort:** 0.25 hr/week; it is fully automated.
- **Monetization:** Stay22's 30%+ share of booking commissions plus tours. Bloggers report about $2K/month at much higher traffic ([Helena Bradbury](https://www.helenabradbury.com/blog-1/stay22-review-blogger-commission-stats)). At 5,000-20,000 visits/month: **$50-400/month** (estimate), plus about $25-150 from display ads at $5-20 RPM.
- **Key risks:** Google Maps and transit apps already cover most of this. Tourists rarely find niche sites. WMATA API terms may restrict commercial use (check).
**Scores:** Usefulness 3 · Uniqueness 3 · Monetization 2 · Low-upkeep 5 · Build ease 4 · Traffic 3 · Skill fit 5 · **Total 25**
- **Why it could be great:** It's the only one of the five domains where a tourist audience and affiliate commerce fit naturally.

## 7. Domain Lease to a Stakeholder (unusual)

- **Pitch:** Don't run a business on the domain; rent the domain itself. Offer the domain on a 1-3 year lease, or a build-and-maintain deal, to the party that values it most: a BID, a developer in lease-up, a brokerage or a hotel.
- **Neighborhoods / audience:** friendshipheights.org (Friendship Heights Alliance runs friendshipheights.com; Tishman Speyer and Bozzuto run the Mazza lease-up), lenfantplaza.org/.net (the property owner runs lenfantplaza.com), adamsmorgan.org (the BID runs adamsmorgan.com), tenleytown.org (Tenleytown Main Street).
- **What the page shows:** Either a redirect or co-branded page for the lessee, or the owner's civic data site with a "presented by [lessee]" banner and a contractual hands-off rule for editorial content.
- **Sources:** Stakeholder sites per BRIEF; Mazza leasing and management ([REBusiness](https://rebusinessonline.com/tishman-speyer-launches-leasing-at-321-unit-residences-at-mazza-apartments-in-dc)).
- **Ongoing effort:** About 0 hr/week after the deal; 5-10 hours of outreach once.
- **Monetization:** $100-1,000/month per domain lease, or a one-time sale of $2K-20K (estimate; exact-match .org prices for neighborhoods vary widely and no comps were found). Hit rate is uncertain: perhaps 1 in 4 approaches converts (estimate).
- **Key risks:** Gives up the community and portfolio goals for that domain. BIDs have small budgets. Approaching a BID could look like squatting. Keep at least one or two domains for the owner's own projects.
**Scores:** Usefulness 2 · Uniqueness 4 · Monetization 3 · Low-upkeep 5 · Build ease 5 · Traffic 1 · Skill fit 2 · **Total 22**
- **Why it could be great:** It turns a dormant asset into income with zero upkeep, and the money can fund the other projects.

## 8. Address Watch: paid "what's happening within 500 ft of my home" alerts (unusual)

- **Pitch:** Enter your address and get an email the day a permit, liquor-license notice, 311 request, raze or new crime incident appears within a chosen radius. One block is free; $3-5/month covers multiple addresses, wider radii and instant delivery.
- **Neighborhoods / audience:** All five to start; it's cheap to extend citywide later. Audience: homeowners, landlords, ANC commissioners, condo boards, and property managers who pay.
- **What the page shows:** A map with the subscriber's radius, a feed of events, and a weekly roll-up. Subscriber data stays private; there's no public map of who watches what.
- **Sources:** opendata.dc.gov permits, 311 (last-30-days feed) and crime; ABCA PDFs (geocoded); ANC/SMD boundaries for "your commissioner" context. Stack: Cloudflare Workers, D1, Stripe, at a $5/month Workers paid plan ([costbench](https://costbench.com/software/cloud-infrastructure/cloudflare-pages-workers/)).
- **Ongoing effort:** 0.5 hr/week.
- **Monetization:** Consumer conversion is low. At 1,000 free users and 3-5% paid at $4/month, that's $120-200/month. A "Pro" tier for property managers and landlords at $19-49/month adds 5-15 accounts, about $100-700. **Total $200-900/month** (estimate) once it reaches a few thousand users.
- **Key risks:** Consumers seldom pay for civic alerts, and Nextdoor and Citizen are free. Storing addresses means a privacy duty. Crime alerts can feed fear; make that alert type opt-in only.
**Scores:** Usefulness 4 · Uniqueness 4 · Monetization 3 · Low-upkeep 5 · Build ease 3 · Traffic 3 · Skill fit 5 · **Total 27**
- **Why it could be great:** It turns the owner's data pipelines into a real product that keeps working with no editorial input, and it scales to the whole city without more effort.

## 9. Local Hourly Jobs & Gigs Board, with paid postings for restaurants and shops

- **Pitch:** A walkable-jobs board ("jobs within 15 minutes' walk of Tenleytown–AU Metro") for restaurants, retail, tutoring and childcare. Employers pay $25-75 per 30-day post, and it is seeded with automatically pulled public listings.
- **Neighborhoods / audience:** Adams Morgan (hospitality-heavy), Tenleytown (AU students), Friendship Heights (new Mazza retail). Audience: students, service workers and local employers.
- **What the page shows:** A filterable job list with walk/Metro time, pay range and "posted by a verified local business" badges.
- **Sources:** Employer self-serve posts; aggregated feeds such as job-board APIs (unverified which are licensable); permits and liquor licenses to find new employers for outreach.
- **Ongoing effort:** 1-1.5 hr/week (spam and scam moderation is the cost).
- **Monetization:** 4-15 paid posts a month at $25-75, which is **$100-1,000/month** (estimate), assuming about 2,000+ monthly job-seeker visits. Indeed is free for employers at the basic level, which caps pricing.
- **Key risks:** Moderation (scam postings) runs against the owner's low-moderation preference. Indeed and Craigslist dominate. Thin traffic means employers see few applicants and don't renew.
**Scores:** Usefulness 3 · Uniqueness 2 · Monetization 2 · Low-upkeep 2 · Build ease 4 · Traffic 2 · Skill fit 4 · **Total 19**
- **Why it could be great:** Hyperlocal hiring is a pain point for small restaurants. Even so, it scores lowest because of moderation.

## 10. Annual Neighborhood Data Report: sponsored PDF and microsite, sold to businesses

- **Pitch:** Once a year, publish "The State of Tenleytown 2027" (and so on for each neighborhood), a polished data report on housing pipeline, foot-traffic proxies, Metro ridership, business openings and closings, permits by value, and 311 trends. A title sponsor such as a bank, developer or brokerage pays, and businesses and investors can buy a deep-dive CSV pack.
- **Neighborhoods / audience:** All five; L'Enfant Plaza works here because office and commercial real estate readers care. Audience: commercial brokers, retailers scouting sites, ANC and BID staff, journalists.
- **What the page shows:** An interactive microsite (Astro and charts) plus a downloadable PDF; a paid tier with raw data and a methodology appendix.
- **Sources:** opendata.dc.gov (permits, 311, crime); WMATA ridership data (unverified); ABCA; RentCafe and Apartment List rent data for context ([RentCafe](https://www.rentcafe.com/average-rent-market-trends/us/dc/washington/tenleytown/)).
- **Ongoing effort:** Bursty: about 20-30 hours once a year (spread as 0.5 hr/week, estimate), and the pipelines are reusable.
- **Monetization:** Title sponsor at $1,000-5,000 per report per year (estimate) plus data packs at $49-199 × 5-20 buyers. **Across five reports, about $400-2,500/month annualized** (estimate). Unproven; sponsor appetite depends on press pickup (Axios DC, UrbanTurf and Washington Business Journal coverage would sell it).
- **Key risks:** Sponsors are hard to land with no track record, so year one is likely unsponsored and serves as a portfolio piece. BIDs may see it as competition, or as a partnership opportunity.
**Scores:** Usefulness 4 · Uniqueness 4 · Monetization 3 · Low-upkeep 4 · Build ease 3 · Traffic 2 · Skill fit 5 · **Total 25**
- **Why it could be great:** One press-worthy report a year builds credibility and portfolio value, and it gives every sponsor pitch for ideas 1 and 2 something to point to.

---

## Ranking and recommendation

| # | Idea | Total | Realistic $/mo after 12-18 months (estimate) |
|---|------|-------|------|
| 2 | Realtor Market Page | 29 | $1,000-3,000 (4 neighborhoods) |
| 5 | Building Report Cards | 28 | $150-1,500 |
| 1 | Data Digest + Exclusive Sponsors | 27 | $900-4,000 (3 neighborhoods) |
| 8 | Address Watch | 27 | $200-900 |
| 3 | Permit & License Lead Feed | 25 | $100-500 local; $300-2,000 citywide |
| 6 | L'Enfant Transfer Companion | 25 | $75-550 |
| 10 | Annual Data Report | 25 | $400-2,500 annualized |
| 4 | Grand Opening Spotlight | 24 | $100-900 |
| 7 | Domain Lease (unusual) | 22 | $100-1,000 per domain |
| 9 | Hourly Jobs Board | 19 | $100-1,000 |

**Best single bet:** combine #2 and #1. Build one data pipeline that feeds an automated page and weekly email for each neighborhood, then sell one exclusive realtor sponsorship per neighborhood first, because it needs the least traffic, and add 2-4 small category sponsors as the list grows. **.org trust note:** keep sponsor blocks clearly labeled and the data neutral, and put the most commercial pieces (#5 paid profiles, #6 affiliate, #3 B2B) on the .net domains or a separate brand.

## Sources

- https://www.beehiiv.com/blog/newsletter-sponsorship-cost
- https://beehiivblog.beehiiv.com/p/how-much-money-can-you-make-from-1-000-newsletter-subscribers-in-2025
- https://www.beehiiv.com/blog/how-beehiiv-powers-our-local-newsletter-strategy
- https://www.beehiiv.com/blog/case-study-catskill-crew
- https://nichesitegrowth.beehiiv.com/p/this-newsletter-makes-7k-mo-from-3-000-subscribers
- https://www.skool.com/claude-code-pirates-8106/my-hyperlocal-newsletter-spot-report
- https://www.niemanlab.org/2025/10/are-these-local-newsletters-local-news-and-does-it-matter/
- https://pressgazette.co.uk/news/6am-city-ryan-heafy-interview/
- https://theaudiencers.com/in-conversation-with-6am-city-tech-stack-audience-strategy-and-unit-economics/
- https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/
- https://www.niemanlab.org/2021/06/ted-williams-proved-local-news-can-be-profitable-now-hell-try-to-replicate-the-success-for-axios/
- https://www.adweek.com/media/axios-local-openai-2026/
- https://www.adexchanger.com/the-sell-sider/patchs-ceo-makes-hyperlocal-profitable/
- https://www.popville.com/advertise/
- https://www.productiveblogging.com/everything-you-need-to-know-about-journey-by-mediavine/
- https://upgrowth.in/website-ad-revenue-2026/
- https://affilimate.com/programs/lemonade-affiliate-program/
- https://stay22.com/faq
- https://www.helenabradbury.com/blog-1/stay22-review-blogger-commission-stats
- https://rentengine.io/blog/rental-lead-worth
- https://www.constructionmonitor.com
- https://www.producthunt.com/products/permit-ledger/makers
- https://apify.com/ledgerstar/building-permits
- https://abca.dc.gov/sites/default/files/dc/sites/abra/page_content/attachments/Weekly%20Issuance%20-%202-20-2026.pdf
- https://abca.dc.gov/sites/default/files/dc/sites/abra/page_content/attachments/Weekly%20Issuance%20-%2012-19-2025.pdf
- https://opendata.dc.gov
- https://dc.urbanturf.com/pipeline/1241/The_Residences_At_Mazza
- https://rebusinessonline.com/tishman-speyer-launches-leasing-at-321-unit-residences-at-mazza-apartments-in-dc
- https://www.axios.com/local/washington-dc/2025/10/31/friendship-heights-new-apartments-total-wine-trader-joes
- https://www.apartments.com/5300-wisconsin-ave-nw-washington-dc-unit-419/mfrgs7l/
- https://www.rentcafe.com/average-rent-market-trends/us/dc/washington/tenleytown/
- https://www.renthop.com/average-rent-in/petworth-washington-dc
- https://costbench.com/software/cloud-infrastructure/cloudflare-pages-workers/
- https://developer.wmata.com (unverified in this pass)
