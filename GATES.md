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
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=94a60ef805b57d11a3ef493388ad081ca05629c3913483cbd240545b844714dd; output-bytes=155

- [x] G5: ingested data contains no personal-name fields (checker proven against a positive control)
  CHECK: node tools/verify.mjs privacy
  EXPECT: privacy verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=e4f33f46c339003236114a3774ad55186cbebb1389d011d7b0a9b866e19ffd89; output-bytes=17

- [x] G6: Astro site builds and emits a page per neighborhood with data, freshness stamp, and independence disclaimer
  CHECK: npm --prefix site run build && node tools/verify.mjs site
  EXPECT: site verified
  EVIDENCE: exit=0; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\ericn\source\repos\DCNeighborhoods; path=acc3919f8bbe/61 entries; EXPECT=matched; output-sha256=16ff7cdc4065777fe63311474eaf5a77c7bc88069778a69e246d8e706e75ba47; output-bytes=1517

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
