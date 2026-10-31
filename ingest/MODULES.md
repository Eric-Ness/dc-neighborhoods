# Ingest module contract

`ingest/run.py` builds one JSON file per neighborhood (`site/src/data/<slug>.json`). Its core sections are `permits`, `requests`, `crime` and `smds`. Extra sections come from modules, one file per section:

| Module | Key in the neighborhood JSON |
|---|---|
| `ingest/homes.py` | `homes` |
| `ingest/streets.py` | `streets` |
| `ingest/history.py` | `history` |
| `ingest/news.py` | `news` (reads the previous snapshot back to keep its archive) |
| `ingest/events.py` | `events` |
| `ingest/jobs.py` | `jobs` (sources and exclusions in `ingest/JOBS-SOURCES.md`) |

## Interface (each module)

```python
def build(geom: dict, hood: dict, now: float) -> dict: ...
def check(section: dict) -> list[str]: ...   # [] when the section is complete and plausible
```

- `geom`: the neighborhood polygon from `dcdata.boundary(...)`, an Esri geometry in WGS84.
- `hood`: the entry from `ingest/neighborhoods.json` (`slug`, `name`, ...). Per-neighborhood settings the module needs (search terms, an OTR assessment-neighborhood name, etc.) live in a dict **inside the module**, keyed by slug. Do not edit `neighborhoods.json`.
- `now`: epoch seconds of this run. Every date window is relative to it.
- Python 3.13 stdlib only. Use `dcdata` (`_request`, `query_features`, `count_by`, `resolve_yearly_layer`, `date_where`, `boundary`) and helpers from `run.py` (`hundred_block`, `iso`, `round_coord`, `point_in_rings`, `ring_centroid`). Don't modify `dcdata.py` or `run.py`.
- Resolve yearly datasets by title with `resolve_yearly_layer`, never with hard-coded URLs, so the January rollover keeps working. Fixed-URL layers (non-yearly) are fine as module constants.
- Every section includes a `sources` list of `{"name", "url"}` and `generated_at` (ISO).
- Must finish within about 3 minutes per neighborhood. Prefer server-side statistics (`count_by`, `outStatistics`) over pulling full tables.

## Privacy (enforced by `tools/verify.mjs privacy`)

- Never request or output owner names, applicant names, inspector names, 311 free-text details, or historic owner names. Request only the fields you need.
- Addresses: property sales and permits may show the full address, since they are public records tied to the property. Anything about people's behavior (311) shows at most the hundred block.
- Forbidden keys anywhere in the output: `OWNER_NAME`, `OWNERNAME`, `OWNNAME`, `OWNER`, `PERMIT_APPLICANT`, `APPLICANT`, `INSPECTORNAME`, `DETAILS`, `CCN`.

## Standalone test

Each module must run on its own:

```bash
python ingest/<module>.py petworth
```

That runs `build()` for that slug, then `check()`. It writes `ingest/_out/<module>-<slug>.json` (gitignored), prints a short summary, and prints `<module> ok` only if `check()` returns no errors. Run it for both `petworth` and `tenleytown`.
