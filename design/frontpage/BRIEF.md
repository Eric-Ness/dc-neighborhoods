# Front-page design exploration: brief for each designer

You are one of five designers working independently on the **front page** of a neighborhood website. Use fresh
eyes: do not copy the current design. The owner likes the content and the general feel (calm, trustworthy,
local, data-literate) but finds the *design* not quite there. Your job is a design that is clearly better and
clearly yours.

## The product

Thirteen independent websites, one per Washington, DC neighborhood (petworth.org, tenleytown.org,
adamsmorgan.org, ...), all built from one engine and updated automatically every night from public data. Design
**Petworth**. Residents come mainly for **news and what's happening**, then for "what's changing on my block".

## The content (all of it is real; use it, don't invent any)

Read the live data: `C:\Users\ericn\source\repos\DCNeighborhoods\site\src\data\petworth.json` (and look at the
current page for reference only: `C:\Users\ericn\source\repos\DCNeighborhoods\site\dist\petworth\index.html`).

The front page currently carries, roughly in this order:
1. **Latest news**: local headlines (`news.items`: title, source, published, url). Links go to the outlet; we
   never copy article text.
2. **Coming up**: events for the next 14 days (`events.events`: title, date, time, place, kind, url), plus
   "also check" links (`events.links`).
3. **Today's condition**: one auto-written lead sentence about the biggest change in 311 requests, plus a
   tally of readings rising / easing / steady. (Derive from `requests.by_type`: count vs previous.)
4. **Measures**: 311 requests, crime reports (counts only, never graded or mapped), median house price
   (`homes.house`), building permits; each "last period vs the one before".
5. **Permit map**: permits with lat/lon inside the neighborhood boundary (`boundary.rings`, `permits`); bigger
   projects (demolition, new construction, additions) are highlighted.
6. **Bigger projects** list, and permits by type.
7. **Homes** (median prices, recent sales), **street trees** (`streets.trees`), **top 311 requests**, **curb
   permits starting soon** (`streets.curb`), **then** (history: `history.buildings.featured_block`, 1926
   newspaper clips in `history.archive.clips`), **representatives** (`smds`), **weekly email** signup.

You may reorder, merge, drop to a link, or re-imagine any of these. Lead with news and events.

## Rules (non-negotiable)

- **Independent, never official.** No DC seals, flag stars/bars motifs, or government styling. The footer says
  it's independent and not affiliated with the DC Government.
- **No cream/beige background.** The owner says cream reads as "AI-made". (Currently a soft blue-gray; you may
  change it.) Avoid other generic-AI tells: purple gradients, glassmorphism, emoji icons, everything in
  rounded cards with soft shadows.
- **Privacy.** No person names from data. Crime: counts only, never mapped, never colored as alarming. 311
  locations only at hundred-block level. Percentages only when both counts are 100 or more.
- **Honest data.** Real numbers from the JSON only. If something is empty, show an honest empty state.
- **Works on a phone.** At 375px wide there must be no horizontal page scroll; design phone and desktop
  (1280px) both on purpose.
- **Accessible.** Body text contrast at least 4.5:1, real headings, links that look like links, meaningful alt
  text / aria labels.

## Deliverable

Work only inside your own folder: `C:\Users\ericn\source\repos\DCNeighborhoods\design\frontpage\<your-name>\`.
Do not edit anything else in the repo.

1. `index.html`: one self-contained page (inline CSS and JS; Google Fonts allowed; no other external requests
   except links). Embed the data you need (generate the HTML with a small Python script, `build.py`, in your
   folder, that reads petworth.json, so the numbers are real and the page can be rebuilt).
2. `DESIGN.md`: under 250 words: the idea in one sentence, the layout logic, type and color choices, what you
   dropped or demoted and why.
3. Check it yourself: render it (e.g. headless Chrome) at 1280px and 375px and fix what's wrong (overflow,
   clipped text, cramped spacing) before you report.

Report back with: your design's name and one-sentence idea, the paths of your files, and anything you couldn't
do.
