"""Fetch "100 years ago this week" clips ahead of time, from a machine loc.gov answers.

    python ingest/prefetch_archive.py                 # this week and the next 5, every enabled neighborhood
    python ingest/prefetch_archive.py --weeks 12      # further ahead
    python ingest/prefetch_archive.py --only=shaw,noma

loc.gov refuses GitHub's cloud runners, so the nightly run can't search the Evening Star itself. This writes one
file per week and neighborhood to ingest/archive_cache/<1926 week start>/<slug>.json, which history.py uses when it
exists. Commit the new files. Weeks already cached (with the current search terms) are skipped, and a week whose
search failed is not written, so running it again fills only the gaps. Searches are paced (history.py waits
between requests), so a week for all 23 neighborhoods takes roughly half an hour.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import history  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DAY = 86400


def main() -> int:
    weeks = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--weeks=")), None)
                or (sys.argv[sys.argv.index("--weeks") + 1] if "--weeks" in sys.argv else 6))
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    config = json.loads((ROOT / "ingest" / "neighborhoods.json").read_text(encoding="utf-8"))
    slugs = [h["slug"] for h in config["neighborhoods"] if h["enabled"] and (not only or h["slug"] in only)]
    now = time.time()
    for k in range(weeks):
        t = now + 7 * k * DAY
        start, _ = history.week_100_years_ago(t)
        for slug in slugs:
            if slug not in history.ARCHIVE or history.cached_archive(slug, t):
                continue
            t0 = time.time()
            section = history.build_archive(slug, t)
            if "could not be reached" in section["note"]:
                print(f"{start} {slug}: loc.gov failed, not cached", flush=True)
                continue
            path = history.ARCHIVE_CACHE / start.isoformat() / f"{slug}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(section, indent=1), encoding="utf-8")
            print(f"{start} {slug}: {len(section['clips'])} clips ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
