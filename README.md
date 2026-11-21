# DC Neighborhoods

Independent, automatically updated civic data for Washington, DC neighborhoods, served on petworth.org, tenleytown.org and (later) adamsmorgan.org, friendshipheights.org and lenfantplaza.org.

Each night a Python job pulls DC open data (building permits, 311 requests, crime counts, ANC districts), clips it to each neighborhood, strips personal fields, and writes JSON. Astro turns that into one static page per neighborhood, plus an RSS feed of new permits. A Cloudflare Worker serves each domain its own neighborhood and 301s the .net names to the .org.

## Layout

| Path | What it is |
|---|---|
| `ingest/` | Python 3.13, stdlib only. `run.py` is the nightly job; `dcdata.py` is the ArcGIS/Open Data DC client; `neighborhoods.json` lists neighborhoods, boundaries and hosts. Extra sections are one module each (`homes`, `streets`, `history`, `news`, `events`; see `ingest/MODULES.md`). `news.py` keeps headline links only and reads its archive back from the last snapshot |
| `site/` | Astro 7 static site. Data lands in `site/src/data/` |
| `worker/` | Cloudflare Worker: hostname → neighborhood folder, .net and www → .org redirects |
| `wrangler.jsonc` | Worker + static assets config, custom domain routes |
| `.github/workflows/nightly.yml` | Ingest → build → verify → commit snapshot → deploy |
| `demos/` | Weekly digest email and block-history page, generated from live data (`python demos/make_demos.py`) |
| `demos/ideas/` | One demo per top-30 idea (`NN-slug.html`), each rebuilt by `src/NN_*.py`; `index.html` lists them (`node tools/demo-index.mjs`). Rules in `CONVENTIONS.md` |
| `research/` | 39 scored ideas, ranking, business case, content strategy |
| `tools/` | `verify.mjs` (gate checks), `rank.mjs` (rebuilds the idea ranking) |

## Run it locally

```bash
python ingest/run.py --check
```

```bash
npm --prefix site install
```

```bash
npm --prefix site run build
```

```bash
npm --prefix site run preview
```

Then open http://localhost:4321/petworth/.

## Deploy (one-time setup)

1. Add each domain as a zone in your Cloudflare account. For Cloudflare to serve custom domains, the domains must use Cloudflare nameservers.
2. Create a Cloudflare API token with the "Edit Cloudflare Workers" template.
3. Push this repo to GitHub and add the repository secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
4. Run the "Nightly ingest, build, deploy" workflow manually once. After that it runs every night at 07:30 UTC (02:30 Eastern in winter, 03:30 in summer).

To deploy by hand instead, run `npx wrangler deploy` from the repo root after building.

## Add a neighborhood

1. Add an entry to `ingest/neighborhoods.json` with `"enabled": true`. Boundaries come from DC Health Planning Neighborhoods, which include Adams Morgan, Petworth and Tenleytown. Friendship Heights is inside DC's "Tenleytown" polygon, and L'Enfant Plaza is inside "SW/Waterfront", so both need a custom boundary (`boundary_where` against another layer, or a GeoJSON file; not built yet).
2. Add its hosts to the `routes` in `wrangler.jsonc`.
3. Run the ingest and the build.

## Privacy rules (enforced in code)

- Permit owner and applicant names are never requested from DC's servers.
- 311 locations are coarsened to the hundred block and about 110 m.
- Crime is fetched only as server-side counts by offense, never as incidents.
- `node tools/verify.mjs privacy` checks the output. A planted positive control proves the scanner itself works.

## Gates

`GATES.md` lists the completion gates for this build. Each runnable gate is a `node tools/verify.mjs <check>` or `python ingest/run.py --check` command.
