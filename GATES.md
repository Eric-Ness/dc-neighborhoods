# Gates: DC Neighborhoods research + v1 scaffold

OWNS: research/**, ingest/**, site/**, demos/**, tools/**, worker/**, .github/**, .claude/launch.json, wrangler.jsonc, GATES.md, README.md, .gitignore

Scope: 20-40 scored ideas from parallel research, ranked review, business case, content strategy, working demos on live DC data, and a v1 scaffold (Python ingest, Astro site, nightly GitHub Action, Cloudflare deploy config) for Petworth and Tenleytown

- [x] G1: idea files hold 20-40 scored ideas, each with a valid Scores line whose Total equals the sum of its 7 scores
  CHECK: node tools/verify.mjs ideas
  EXPECT: ideas verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=aa388f3ce87bc7be916911a14eff42351fa08a52c1964359807b117c30be3e18; output-bytes=15

- [x] G2: research/IDEAS.md ranks every idea from the idea files (no idea missing, none invented)
  CHECK: node tools/verify.mjs ranking
  EXPECT: ranking verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=0dcbb37a15b1b6ecb6921ac34dd7b12a99ec24eec83b180961203ce4187a6b6e; output-bytes=17

- [x] G3: business case and content strategy docs exist with every required section
  CHECK: node tools/verify.mjs docs
  EXPECT: docs verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=8714c68620dded8a6b58f3bbb44269c0f16e0e25f6bc3730781931d67f37d6ed; output-bytes=14

- [x] G4: ingest runs against live DC data and writes non-empty permits and 311 data for petworth and tenleytown
  CHECK: python ingest/run.py --check
  EXPECT: ingest verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=0c66b77966776e588db325b9a10bae07a0d4c431e03382d02cce26ff80a5ea48; output-bytes=155

- [x] G5: ingested data contains no personal-name fields (checker proven against a positive control)
  CHECK: node tools/verify.mjs privacy
  EXPECT: privacy verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=e4f33f46c339003236114a3774ad55186cbebb1389d011d7b0a9b866e19ffd89; output-bytes=17

- [x] G6: Astro site builds and emits a page per neighborhood with data, freshness stamp, and independence disclaimer
  CHECK: npm --prefix site run build && node tools/verify.mjs site
  EXPECT: site verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=ede750da4ca3e18612b4c3bd65c020264e9aa0d96473467db44db151fba05611; output-bytes=3371

- [x] G7: nightly workflow exists, runs ingest then build then deploy, and the deploy config covers both .org hosts and .net redirects
  CHECK: node tools/verify.mjs deploy
  EXPECT: deploy verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=be310063cc381e67520efeb0c7b1cd2a0b429f27bdc5fd82bed65062857cd18c; output-bytes=16

- [x] G8: demo pages exist, are self-contained, and embed live data fetched this session
  CHECK: node tools/verify.mjs demos
  EXPECT: demos verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=ea8201f3891ff937e5a192f298763b0bd5e86a9252ccb3868590cb6cfbd6913b; output-bytes=15

- [x] G10: each of the top 30 ideas has a demo page (rank 3 reuses the digest) with honest live/sample provenance, About box, self-contained, privacy-clean
  CHECK: node tools/verify.mjs ideademos
  EXPECT: ideademos verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=bc2b9b5f36d699992ea184d9b912f8341854bb233651190ec1ae1736b5718cf9; output-bytes=19

- [x] G11: demo index lists all 30 ideas in rank order with links that resolve and none marked not built
  CHECK: node tools/demo-index.mjs && node tools/verify.mjs demoindex
  EXPECT: demoindex verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=e6b5958fae7715bc7e28373db9f8d2e2c74365245f866e56ad826f2594a844d4; output-bytes=66

- [x] G12: every top-30 demo was read by the driver (not just its builder) and problems found were fixed; hub republished with the demo index
  EVIDENCE: manual review 2026-10-31: driver read head + About box of all 29 new demos (groups A-F) and grepped B/D for owner names (only disclaimers and CofO "Owner change" reasons); checked #28 F4 sample labeling; 375px overflow test over all 31 pages in iframes found 1 failure (#23, repeated ANCSMD values), fixed in generator and re-tested 371/371; hub republish recorded in research/README.md

- [x] G9: research hub is published as a private artifact and its URL is recorded in research/README.md
  EVIDENCE: manual 2026-10-31: Artifact publish returned https://claude.ai/artifact/8265xWrJ9cvUsL3AXBzvW2 (version 1, with demos/digest-petworth.html and demos/block-delafield.html as files); URL written to research/README.md hub row

## Phase 3: C5 site, filled out

- [x] G13: both neighborhoods' data has complete homes, streets and history sections from live ingest
  CHECK: node tools/verify.mjs datafull
  EXPECT: datafull verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=d8e4f9aa582c06fa0eec5d68560e008e9aaf414a332742221f2a44eb072e8ec5; output-bytes=18

- [x] G14: every neighborhood has all 8 pages built (home, projects, homes, streets, then, representatives, about, subscribe) with freshness stamp, disclaimer, working section links, no mockup leftovers
  CHECK: npm --prefix site run build && node tools/verify.mjs sitefull
  EXPECT: sitefull verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=85102c1ff255d028699269d13ee1f5e3a47170c51eac4b5d10812565fed18890; output-bytes=3376

- [x] G15: map markers are tied to projects by permit id (not list order), one marker per bigger project with coordinates
  CHECK: node tools/verify.mjs markers
  EXPECT: markers verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=dabc24ba0cac826211c7d1abe651cfbda8e470d5830ebdc649be7498200c2f0c; output-bytes=17

- [x] G16: no built page scrolls horizontally at 375px (CDP phone emulation over every page)
  CHECK: node tools/overflow.mjs
  EXPECT: overflow verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=05cfaec38c822d845e64f5dc05c97cf4881e4b2527ed278ca7549a6d1809a5e2; output-bytes=44

- [x] G17: worker serves every sub-page on the .org hosts and still redirects .net/www
  CHECK: node tools/verify.mjs deploy
  EXPECT: deploy verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=be310063cc381e67520efeb0c7b1cd2a0b429f27bdc5fd82bed65062857cd18c; output-bytes=16

- [x] G18: driver reviewed screenshots of every page type at phone and desktop width and fixed what was wrong
  EVIDENCE: manual review 2026-10-31: driver viewed home (PW/TT desktop+phone), projects (TT desktop), homes (PW desktop, TT phone), streets (PW desktop+phone), then (TT desktop), representatives+about+subscribe (PW phone). Fixed: map script ran before rows (row hover dead on home), "46TH" ordinals, all-caps permit text, curb-row empty space, "0 readings rising" wording, stale Teddy-Tenley clip (module already guarded; regenerated), verify NaN false positive, stale G6 markup assertion. Known/accepted: on phone, streets curb and 311 tables scroll sideways inside their own container (page does not; G16 passes).

## Phase 4: news & events

- [x] G19: both neighborhoods' data has news (headlines only: title, outlet, date, link) and events (dated, in the next 30 days, linked) from a live run, with most outlets read (checker proven against a positive control)
  CHECK: node tools/verify.mjs newsdata
  EXPECT: newsdata verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=3e6ce5642bb9f9a46568bf5eda77aee2eb791fe2cfe4410ce95be91961fb1514; output-bytes=18

- [x] G20: every headline and event is on the News & events page, the home page leads with the news & events band above today's condition, and headline links go out to the outlets
  CHECK: npm --prefix site run build && node tools/verify.mjs sitenews
  EXPECT: sitenews verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=162f7ae52f967fd477ff290501cd1760764dff092b0eeb6d67ad752f6a0a026c; output-bytes=3385

- [x] G21: driver reviewed the news page and new home band at phone and desktop width and fixed what was wrong
  EVIDENCE: manual review 2026-10-31: driver viewed petworth home (desktop+phone), petworth/news, tenleytown home, tenleytown/news (desktop) and tenleytown/news (phone). Fixed: event times wrapped ("9:00 AM - 1:00 / PM" -> "9 AM–1 PM"), header tagline still said data-only, stray backspace chars in the time regex. Negative control: injected a headline missing from the page -> sitenews exit 1, restored -> verified. Known/accepted: Tenleytown events are only two recurring farmers markets this month (Main Street calendar and ANC 3E agendas list nothing yet for November); crime headlines from outlets are shown unfiltered.

## Phase 5: openings & closings, ANC Decoder, street names, voices, cross-site links

- [x] G22: every street-name entry cites at least one https source and every oral-history item links to its archive, all rendered on the Then page (checker proven against an unsourced entry)
  CHECK: npm --prefix site run build && node tools/verify.mjs curated
  EXPECT: curated verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=2104812493d936bcedb7fa893dd17308e32bb5a7d4b7e03d6de999672434fc11; output-bytes=3377

- [x] G23: the ANC Decoder lists the ANC's own posts, Openings & closings shows cancelled licenses that aren't still active, and every page links every other live neighborhood's domain
  CHECK: npm --prefix site run build && node tools/verify.mjs decoder
  EXPECT: decoder verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=662ebaa34a2f88dc67dfdb24c5e7b3e7d1bbeb71d619ea49bcb5f7f77cd64573; output-bytes=3383

- [x] G24: driver reviewed the Then, News & events and Representatives pages at desktop and phone width after these additions and fixed what was wrong
  EVIDENCE: manual review 2026-10-31: driver viewed petworth/then (desktop, 3 segments), tenleytown/then (desktop), tenleytown/representatives and petworth/news (desktop), petworth/streets and petworth/representatives (phone). Fixed: "Tenleytown's ANCs ()" empty before the new field existed (falls back to the commissioner list), DC Water presentation tagged Other (added Presentation topic), name and address wrapping onto separate lines in the openings/closings rows, "Who was Upshur?" heading when Upshur is unsourced, http Ghosts of DC links (now https). Content: moved Jefferson and Farragut to unsourced (source did not name the Petworth streets) and dropped one oral history tagged Petworth that never discusses it. Collapse control tested in browser: 6 of 16 rows, expands to 16, collapses to 6. Negative controls: unsourced entry -> curated exit 1.

## Phase 6: jobs, blue-gray palette

- [x] G25: both neighborhoods have a jobs section from employer feeds (title, employer, place, date, link; never a description) and every job is on the Jobs page (checker proven against a positive control)
  CHECK: npm --prefix site run build && node tools/verify.mjs jobs
  EXPECT: jobs verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=1cf85da436e2a05170572c74bb7584fcf6617ff91d85e172118bf72576e50a4c; output-bytes=3378

- [x] G26: driver reviewed the Jobs page and the blue-gray palette at phone and desktop width and fixed what was wrong
  EVIDENCE: manual review 2026-10-31: driver viewed petworth home (desktop+phone) and tenleytown/news (desktop) in blue-gray; tenleytown/jobs (desktop+phone) and petworth/jobs (desktop). Fixed: preview served a stale cream build (rebuilt), muted text darkened to #5e6a73 for 4.69:1 on the page background, Tenleytown homes NaN when DC returned no address points (page guard + ingest reuses last measurement, fallback path tested), stale January adjunct posting (age cutoff moved after the exact-date lookup), duplicated "Columbia Heights" label, "below" pointing at a side panel. Contrast measured: text 12.5:1, accent 4.8:1, muted 4.7:1 on --bg.
