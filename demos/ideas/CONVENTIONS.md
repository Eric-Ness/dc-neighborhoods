# Idea demo conventions

Each of the top 30 ranked ideas gets one demo page that shows what the product would look like and feel like, using real DC data wherever it can be fetched without a key.

## Files (yours only; touch nothing else)

- Page: `demos/ideas/NN-slug.html` (NN = two-digit rank from research/IDEAS.md, e.g. `07-block-report-card.html`).
- Generator: `demos/ideas/src/NN_slug.py`, Python 3.13 stdlib only. It must write the page. Run it with `python demos/ideas/src/NN_slug.py` from the repo root.
- Import the shared client with `sys.path.insert(0, str(ROOT / "ingest")); import dcdata`. Read `ingest/dcdata.py` and `ingest/run.py` first: they already handle ArcGIS paging, spatial queries, yearly dataset lookup (`resolve_yearly_layer`), server-side counts (`count_by`), boundaries and address coarsening (`hundred_block`). You may import helpers from `run.py`. **Do not edit any shared file** (`ingest/*`, `site/*`, `tools/*`, `TEMPLATE.html`, other demos).
- Neighborhood boundaries: `dcdata.boundary("https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/13", "DC_HPN_NAME='PETWORTH'")`. Other names there: 'TENLEYTOWN' (includes Friendship Heights), 'ADAMS MORGAN', 'SW/WATERFRONT' (includes L'Enfant Plaza).
- Find dataset URLs with the Open Data DC search API, as `dcdata.resolve_yearly_layer` does: `https://opendata.dc.gov/api/search/v1/collections/dataset/items?q=<title>`.

## Page rules

1. Start from `demos/ideas/TEMPLATE.html`: read it in your generator and replace every `{{...}}` placeholder. Keep its `<style>` block; add demo-specific CSS only via `{{EXTRA_CSS}}`.
2. Self-contained: no external scripts, stylesheets, fonts, images or iframes. Charts and maps are inline SVG drawn by your generator. Small inline `<script>` for interactivity is fine (no network calls from the page). Photos are allowed only as embedded `data:` URIs of public-domain or CC0 images (e.g. Library of Congress items marked "No known restrictions"), resized small (≤150 KB each) and credited with a link to the source record. Plain `<a href>` links to source pages are fine.
3. **Provenance is mandatory and honest.**
   - `live` badge ("Live data · Open Data DC · pulled YYYY-MM-DD") only when the main content was fetched by your generator this run.
   - `sample` badge ("Sample data · illustrative") when anything central is made up (e.g. WMATA arrivals need an API key we don't have). Sample values must be plausible, labeled, and never presented as real facts about real people or businesses. Use generic placeholder names like "[Sponsor name]" or "Sample Café", not real business names, for anything invented.
   - If the page mixes both, use `live` only if the core content is live, and say exactly which parts are sample in "What's mocked".
4. Privacy: never output owner names, applicant names, inspector names, 311 free-text details, exact 311 house numbers (use `hundred_block`), individual crime incidents, or historic owner names. Elected officials and businesses' public license names are fine.
5. Tone: plain, neighborly, numbers first. No percentages on counts under 100. Independent disclaimer stays in the footer.
6. Mobile: must work at 375 px wide with no horizontal page scroll (wide tables go inside `.scroll`).
7. Keep each page under 1.5 MB. Cap long lists (e.g. 50 rows) and say so.
8. Fill `{{SCORE}}` and `{{IDEA_ID}}` exactly from the assignment you were given.
9. Make it look like a real product page someone would bookmark, not a report about one. The "About this demo" box is where you explain.

## Self-check before you finish

```
node tools/verify.mjs ideademos NN
```

It checks one demo (or all, with no number). Fix everything it reports. Then open the HTML file and read it once as a resident would.
