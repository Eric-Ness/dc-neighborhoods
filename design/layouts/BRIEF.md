# Layout mockups: the petworth.org home page

Three designers each build one complete home-page mockup for **petworth.org**, in a different visual direction. The owner will compare them as phone screenshots and pick one, or mix them. The content is identical across all three; only the layout, type, color and hierarchy differ.

## The site

petworth.org is an independent, automatically updated civic-data site for the Petworth neighborhood of Washington, DC. A nightly job pulls DC open data. It is **not** official: it must never look like DC Government, the ANC or a BID. That means no DC flag stars-and-bars, no seals, no "Official", and no government blue-and-red. Readers are residents, renters, house hunters and ANC watchers, mostly on phones.

## Content (all three must include every section, in any order or arrangement that suits the direction)

1. **Header:** "Petworth" plus a short descriptor (e.g. "What's changing in Petworth, from DC's own data"), and a "data as of" stamp from `generated_at`.
2. **Address search:** "Look up your block or building". A mock input, non-functional, leading to the block and building pages.
3. **This week:** a lead story built from the data (e.g. rodent complaints up from 84 to 118), plus permits, 311 and crime counts. Show crime as counts only, with no percentages on numbers under 100.
4. **Bigger projects:** the demolition, addition and new-construction permits, with addresses.
5. **Homes:** the median house price, sales count and a link to the assessment check.
6. **Streets:** curb permits this week, the 311 top types, and street trees with empty boxes.
7. **History:** the Delafield Place Cafritz fact, and the 1926 Evening Star excerpt marked as OCR with its source.
8. **Who represents you:** the 6 SMDs with commissioner names; elected officials are public.
9. **Subscribe:** the weekly email signup (mock), plus the RSS link.
10. **Sponsor slot:** one, labeled "Presented by [Local sponsor]".
11. **Footer:** "Independent project. Not affiliated with the DC Government, any Advisory Neighborhood Commission, or any Business Improvement District." Plus sources (Open Data DC, CC BY 4.0; Library of Congress).

Link each section to its full demo using the paths in `facts.json` `demo_links`, rewritten relative to your file (e.g. `../../demos/ideas/01-block-watch.html`).

## Data

Use **only** `design/layouts/facts.json`. Every number and name on the page must come from it. Don't invent figures, businesses or people. If you want a map, draw it as inline SVG from `boundary_rings` and `permit_points` (lon/lat; use an equirectangular projection with a cos(latitude) correction, the way `site/src/components/BoundaryMap.astro` does). Embed the data you need directly in the HTML; the page must not fetch at runtime.

## Build rules

- One self-contained file: `design/layouts/<letter>-<slug>.html`. Generate it with a small Python script `design/layouts/src/<letter>_<slug>.py` that reads facts.json and writes the HTML, so it can be rebuilt with new data.
- Fonts: Google Fonts `<link>` is allowed (2 families max, with real fallback stacks). No other external resources, no JS libraries, no images except inline SVG.
- Mobile first: design for a 390px-wide phone, with no horizontal scrolling at 375px (wide tables go inside `overflow-x:auto`). It should also look intentional at desktop width.
- Define colors as CSS variables. A dark-mode variant is welcome but optional.
- Keep it under 300 KB.
- At the very top, add a small "LAYOUT <letter>: <direction name>" label so the screenshots are easy to tell apart.
- Write the page copy plainly: numbers first, no hype, and no "alarming" or "surge".

## Done

Run your generator, open the HTML once, and read it as a Petworth resident on a phone would. Final reply: ≤120 words. Say which file you made, the core idea of the direction, and one trade-off it makes.
