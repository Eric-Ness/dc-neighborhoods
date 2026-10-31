# Sub-page brief

The site uses the **C5 design** ("C3 layout + C4 data"). The home page `site/src/pages/[slug]/index.astro` is done. Study it first, along with:

- `site/src/layouts/Hood.astro`: the frame for every neighborhood page. Pass `page` (its path from `PAGES` in `lib/data.ts`), `heading` and `intro`.
- `site/src/lib/c5.ts`: helpers that every page must reuse: `reading`, `pair`, `bar`, `icon`, `stateTag`, `glyph`, `money`, `fmt`, `addr`, `titleCase`, `shortType`, `shortDate`, `model(n)`, `CATS`, `BIG`.
- `site/src/lib/data.ts`: types for every data section. `homes`, `streets` and `history` are optional; render a short "didn't update tonight" note if one is missing.
- `site/src/styles/c5.css`: the classes `panel`, `ph`, `row`, `row.even`, `stack`, `stats`, `hero`, `cta`, `cmp`/`cr-r` paired bars, `t311`, `dtable`/`dtable-wrap`, `hbars`, `vbars`, `clip`, `prose`, `note`, `then`/`thencard`, `anc`, `subband`, `sponsor`.
- `site/src/components/PermitMap.astro` and `ProjectList.astro`: reusable.
- Live data: `site/src/data/petworth.json` and `tenleytown.json`.

## Pages (one file each, `site/src/pages/[slug]/<name>.astro`, using `export const getStaticPaths = staticPaths`)

| Page | Must show |
|---|---|
| `projects.astro` | Large PermitMap; the full ProjectList (`full` descriptions); then **every** permit grouped by type (collapsible `<details>`, address · date · id · description), anchored `id="p<permit id>"` so search links land on rows. Bigger projects already carry those ids in ProjectList, so only give ids to non-big permits in the grouped list (ids must stay unique). |
| `homes.astro` | House and condo medians with 12-month vs prior paired bars; 60-day figures; sold-above-assessment; monthly median chart (`vbars`, labeled with month and count); `recent_sales` table (`id="recent"`); `area_note`, shown honestly; how to appeal an assessment (link to the DC Office of Tax and Revenue site, `https://otr.cfo.dc.gov/`); sources. |
| `streets.astro` | Curb section (`id="curb"`): stats, `by_type` hbars, `upcoming` table and `freshness_note`. 311 section (`id="requests"`): **all** request types with paired bars or t311 rows. Service section (`id="service"`): median days to close vs citywide. Recent 311 list (hundred block only). Trees (`id="trees"`): stats, condition, top species hbars, biggest trees, `empty_boxes_note`, and a 311 planting link `https://311.dc.gov/`. |
| `then.astro` | Buildings: record count and year span, `by_decade` vbars, top architects and builders hbars. Featured block (`id="featured"`). Archive (`id="archive"`): week label, every clip as a `clip` with an OCR badge and a link to loc.gov, and the archive note. Sources. |
| `representatives.astro` | SMDs grouped by ANC with commissioner names and ANC site links; what an ANC is and does, in plain language (they give "great weight" advice to DC agencies on zoning, liquor licenses, public space and permits); how to find your SMD (link `https://anc.dc.gov/`); meeting info belongs on the ANC's own site. |
| `subscribe.astro` | What the weekly email contains, mirroring the home page sections; the signup form (`method="get"`, no real submission; show "Signups open soon. Use the RSS feed meanwhile" when the `email` query param is present, via a tiny inline script); RSS link; a privacy promise (one email a week, no selling addresses); the sponsor policy (one labeled sponsor, never inside the data). |
| `about.astro` | Independence statement. Every data source used, gathered from each section's `sources` plus the core `n.sources`, with links. Update schedule (nightly 05:15 ET). Privacy rules: no owner or applicant names, 311 to the hundred block, crime as counts only and never mapped (`id="crime"`, explaining the preliminary MPD counts). How the boundary is defined. Corrections: a placeholder email `corrections@[domain]`, shown as text, not a mailto. License (CC BY 4.0 data). |

## Rules

- **Only data from the JSON.** Every number comes from the data, and nothing is invented. Placeholder text is allowed only for `[Local sponsor]` and the corrections address.
- Privacy: never output owner, applicant or inspector names, 311 details, or exact 311 addresses.
- No percentages on counts under 100 (use `reading()`). Crime is never graded or colored as rising.
- Work at 375px with no horizontal page scroll; wide tables go inside `dtable-wrap`. Also check 1440px.
- Use relative internal links built with `pageUrl(n.slug, "...")` only.
- Don't edit the shared files (`lib/*`, `layouts/*`, `components/*`, `styles/c5.css`, `index.astro`). If you truly need a new CSS class, add it in a `<style is:global>` block inside your page, prefixed with your page name.
- Build with `npm --prefix site run build`, then look at each page by previewing `site/dist`.
