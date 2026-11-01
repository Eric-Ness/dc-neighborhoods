// Gate checks for GATES.md. Usage: node tools/verify.mjs <check> (run with no argument to list them)
// Each check prints "<name> verified" only after every assertion passes, and exits 1 otherwise.
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { loadIdeas } from "./ideas-lib.mjs";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(join(root, p), "utf8");
const errors = [];
const assert = (cond, msg) => { if (!cond) errors.push(msg); };

const checks = {
  ideas() {
    const ideas = loadIdeas(root);
    assert(ideas.length >= 20 && ideas.length <= 40, `expected 20-40 ideas, found ${ideas.length}`);
    for (const i of ideas) for (const e of i.errors) errors.push(`${i.id}: ${e}`);
    const files = readdirSync(join(root, "research/ideas")).filter((f) => f.endsWith(".md"));
    assert(files.length >= 4, `expected 4 lens files, found ${files.length}`);
    for (const f of files) assert(/^## Sources/m.test(read(`research/ideas/${f}`)), `${f}: no Sources section`);
  },

  ranking() {
    const ideas = loadIdeas(root);
    const doc = read("research/IDEAS.md");
    const block = doc.match(/<!-- ranking:start -->([\s\S]*?)<!-- ranking:end -->/)?.[1] ?? "";
    const ranked = [...block.matchAll(/^\| \d+ \|.*\| `([^`]+)` \|$/gm)].map((m) => m[1]);
    const known = new Set(ideas.map((i) => i.id));
    assert(ranked.length === ideas.length, `ranking has ${ranked.length} rows for ${ideas.length} ideas`);
    for (const id of known) assert(ranked.includes(id), `missing from ranking: ${id}`);
    for (const id of ranked) assert(known.has(id), `ranking row for unknown idea: ${id}`);
    assert(new Set(ranked).size === ranked.length, "duplicate ranking rows");
    const scores = [...block.matchAll(/^\| \d+ \|.*\| ([\d.]+) \| [\d.]+ \| `/gm)].map((m) => Number(m[1]));
    assert(scores.every((s, i) => i === 0 || scores[i - 1] >= s), "ranking not sorted by weighted score");
  },

  docs() {
    const need = {
      "research/BUSINESS-CASE.md": ["Summary", "Market", "Revenue", "Costs", "Time budget", "Milestones", "Risks", "Kill criteria"],
      "research/CONTENT-STRATEGY.md": ["Content pillars", "Automation pipeline", "Curation rules", "Editorial calendar", "Distribution", "Partnerships", "Voice"],
    };
    for (const [file, sections] of Object.entries(need)) {
      assert(existsSync(join(root, file)), `${file} missing`);
      if (!existsSync(join(root, file))) continue;
      const text = read(file);
      for (const s of sections) {
        const body = text.split(new RegExp(`^## ${s}\\s*$`, "m"))[1]?.split(/^## /m)[0] ?? "";
        assert(body.trim().length >= 200, `${file}: section "${s}" missing or under 200 chars`);
      }
      assert(!/\b(TODO|TBD|lorem)\b/i.test(text), `${file}: placeholder text`);
    }
  },

  privacy() {
    const FORBIDDEN = ["OWNER_NAME", "OWNERNAME", "OWNNAME", "OWNER", "PERMIT_APPLICANT", "APPLICANT", "INSPECTORNAME", "DETAILS", "CCN"];
    const scan = (obj, hits = [], path = "$") => {
      if (Array.isArray(obj)) obj.forEach((v, i) => scan(v, hits, `${path}[${i}]`));
      else if (obj && typeof obj === "object")
        for (const [k, v] of Object.entries(obj)) {
          if (FORBIDDEN.includes(k.toUpperCase())) hits.push(`${path}.${k}`);
          scan(v, hits, `${path}.${k}`);
        }
      return hits;
    };
    // Positive control: the scanner must catch a planted field, or a clean result proves nothing.
    const control = scan({ permits: [{ id: "x", owner_name: "Jane Doe" }], requests: { recent: [{ INSPECTORNAME: "x" }] } });
    assert(control.length === 2, `positive control failed: scanner found ${control.length}/2 planted fields`);
    const index = JSON.parse(read("site/src/data/index.json"));
    assert(index.length > 0, "no neighborhoods in index.json");
    for (const h of index) {
      const data = JSON.parse(read(`site/src/data/${h.slug}.json`));
      for (const hit of scan(data)) errors.push(`${h.slug}: forbidden field ${hit}`);
      for (const r of data.requests.recent) {
        // Intersections and landmarks carry no house number; anything starting with one must be a hundred block.
        const houseNumber = r.block && /^\s*\d+\s/.test(r.block);
        assert(!houseNumber || /^\d*00 block of [A-Z0-9]/.test(r.block), `${h.slug}: 311 address not coarsened: ${r.block}`);
        assert(!r.block || !/\d+\s*-\s*\d+/.test(r.block), `${h.slug}: 311 address range not normalized: ${r.block}`);
        assert(r.lat === null || Math.round(r.lat * 1000) / 1000 === r.lat, `${h.slug}: 311 latitude too precise`);
      }
      assert(!("by_incident" in data.crime) && Array.isArray(data.crime.by_offense), `${h.slug}: crime must be counts only`);
    }
  },

  site() {
    const index = JSON.parse(read("site/src/data/index.json"));
    assert(index.length >= 2, "expected at least 2 neighborhoods");
    for (const h of index) {
      const page = `site/dist/${h.slug}/index.html`;
      assert(existsSync(join(root, page)), `${page} not built`);
      if (!existsSync(join(root, page))) continue;
      const html = read(page);
      const data = JSON.parse(read(`site/src/data/${h.slug}.json`));
      assert(html.includes("Data as of"), `${h.slug}: no freshness stamp`);
      assert(html.includes(`datetime="${data.generated_at}"`), `${h.slug}: page not built from current data`);
      assert(html.includes("Independent project"), `${h.slug}: no independence disclaimer`);
      // C5 shows the count in the permit-map header and the permits measure.
      assert(html.includes(`<b id="shown">${data.permits.length}</b>`) && html.includes(`${data.permits.length} issued`), `${h.slug}: permit count ${data.permits.length} not rendered`);
      assert(data.permits.length > 0 && data.requests.total > 0, `${h.slug}: empty data`);
      const rss = `site/dist/${h.slug}/permits.xml`;
      assert(existsSync(join(root, rss)) && (read(rss).match(/<item>/g) ?? []).length === Math.min(100, data.permits.length), `${h.slug}: RSS item count wrong`);
    }
  },

  async deploy() {
    const wf = read(".github/workflows/nightly.yml");
    const order = ["python ingest/run.py --check", "npm run build", "node tools/verify.mjs site", "wrangler-action"];
    const pos = order.map((s) => wf.indexOf(s));
    assert(pos.every((p) => p >= 0), `workflow missing a step: ${order.filter((_, i) => pos[i] < 0).join(", ")}`);
    assert(pos.every((p, i) => i === 0 || pos[i - 1] < p), "workflow steps out of order");
    assert(/schedule:\s*\n\s*- cron:/.test(wf), "workflow has no nightly schedule");
    const wr = read("wrangler.jsonc");
    const index = JSON.parse(read("site/src/data/index.json"));
    // Each neighborhood's primary .org (and www) must be routed. Redirect domains (.net) are routed only once
    // their zone is on Cloudflare; the Worker test below still proves they 301 to the .org.
    for (const h of index) for (const host of h.hosts) {
      assert(wr.includes(`"${host}"`), `wrangler.jsonc missing route for ${host}`);
      assert(wr.includes(`"www.${host}"`), `wrangler.jsonc missing route for www.${host}`);
    }

    // Exercise the Worker's routing against a fake asset binding.
    const worker = (await import(pathToFileURL(join(root, "worker/index.js")).href)).default;
    const seen = [];
    const env = { ASSETS: { fetch: async (req) => { seen.push(new URL(req.url ?? req).pathname); return new Response("ok"); } } };
    for (const h of index) {
      const host = h.hosts[0];
      await worker.fetch(new Request(`https://${host}/`), env);
      assert(seen.at(-1) === `/${h.slug}/`, `${host}/ served ${seen.at(-1)} instead of /${h.slug}/`);
      await worker.fetch(new Request(`https://${host}/permits.xml`), env);
      assert(seen.at(-1) === `/${h.slug}/permits.xml`, `${host}/permits.xml served ${seen.at(-1)}`);
      for (const sub of ["projects/", "homes/", "streets/", "then/", "representatives/", "subscribe/", "about/", "search.json"]) {
        await worker.fetch(new Request(`https://${host}/${sub}`), env);
        assert(seen.at(-1) === `/${h.slug}/${sub}`, `${host}/${sub} served ${seen.at(-1)}`);
        await worker.fetch(new Request(`https://${host}/${h.slug}/${sub}`), env);
        assert(seen.at(-1) === `/${h.slug}/${sub}`, `${host}/${h.slug}/${sub} (prefixed link) served ${seen.at(-1)}`);
      }
      await worker.fetch(new Request(`https://${host}/_astro/x.css`), env);
      assert(seen.at(-1) === "/_astro/x.css", `${host} rewrote a shared asset path`);
      for (const r of h.redirect_hosts) {
        const res = await worker.fetch(new Request(`https://${r}/a?b=1`), env);
        assert(res.status === 301 && res.headers.get("location") === `https://${host}/a?b=1`, `${r} did not 301 to ${host}`);
      }
      const www = await worker.fetch(new Request(`https://www.${host}/x`), env);
      assert(www.status === 301 && www.headers.get("location") === `https://${host}/x`, `www.${host} did not 301`);
    }
  },

  demos() {
    const files = ["demos/digest-petworth.html", "demos/block-delafield.html"];
    const generated = JSON.parse(read("site/src/data/petworth.json")).generated_at.slice(0, 10);
    for (const f of files) {
      assert(existsSync(join(root, f)), `${f} missing`);
      if (!existsSync(join(root, f))) continue;
      const html = read(f);
      assert(!/<script[^>]+src=|<link[^>]+stylesheet/i.test(html), `${f}: not self-contained`);
      assert(html.includes("DEMO"), `${f}: not labeled as a demo`);
      assert(html.includes("not affiliated with DC Government") || html.includes("Independent project"), `${f}: no independence disclaimer`);
    }
    const digest = read(files[0]);
    assert(digest.includes(generated), "digest not built from the current ingest run");
    const block = read(files[1]);
    const histCount = Number(block.match(/<b>(\d+)<\/b>original building permits/)?.[1] ?? 0);
    assert(histCount > 0, "block demo has no historic records");
    assert(/Generated \d{4}-\d{2}-\d{2}/.test(block), "block demo has no generation stamp");
    assert(!/Owner/i.test(block.replace(/owner names are omitted/i, "")), "block demo shows historic owner field");
  },
};

// Top-30 idea demos. Rank 3 (Data Digest) is served by the existing demos/digest-petworth.html.
export const DEMO_ALIASES = { 3: "demos/digest-petworth.html" };

function rankedIdeas() {
  const block = read("research/IDEAS.md").match(/<!-- ranking:start -->([\s\S]*?)<!-- ranking:end -->/)?.[1] ?? "";
  return [...block.matchAll(/^\| (\d+) \| (.*?) \| (\w+) \|.*\| ([\d.]+) \| [\d.]+ \| `([^`]+)` \|$/gm)].map((m) => ({
    rank: Number(m[1]), title: m[2], engine: m[3], score: m[4], id: m[5],
  }));
}

checks.ideademos = () => {
  const only = process.argv[3] ? Number(process.argv[3]) : null;
  const dir = join(root, "demos/ideas");
  const files = existsSync(dir) ? readdirSync(dir) : [];
  const srcFiles = existsSync(join(dir, "src")) ? readdirSync(join(dir, "src")) : [];
  for (const idea of rankedIdeas().filter((i) => i.rank <= 30 && (only === null || i.rank === only))) {
    const nn = String(idea.rank).padStart(2, "0");
    if (DEMO_ALIASES[idea.rank]) {
      assert(existsSync(join(root, DEMO_ALIASES[idea.rank])), `#${nn}: alias ${DEMO_ALIASES[idea.rank]} missing`);
      continue;
    }
    const pages = files.filter((f) => f.startsWith(`${nn}-`) && f.endsWith(".html"));
    assert(pages.length === 1, `#${nn}: expected 1 page demos/ideas/${nn}-*.html, found ${pages.length}`);
    assert(srcFiles.some((f) => f.startsWith(`${nn}_`) && f.endsWith(".py")), `#${nn}: no generator demos/ideas/src/${nn}_*.py`);
    if (pages.length !== 1) continue;
    const path = `demos/ideas/${pages[0]}`;
    const html = read(path);
    const tag = `#${nn} ${pages[0]}`;
    assert(html.includes(`data-idea="${idea.id}"`), `${tag}: data-idea must be ${idea.id}`);
    assert(html.includes(`data-rank="${idea.rank}"`), `${tag}: data-rank must be ${idea.rank}`);
    assert(html.includes(`Idea #${idea.rank} of 39`) && html.includes(`weighted score ${idea.score}/100`), `${tag}: demo bar must say Idea #${idea.rank} of 39 and weighted score ${idea.score}/100`);
    assert(!html.includes("{{"), `${tag}: unfilled template placeholder`);
    const prov = html.match(/data-provenance="(live|sample)"/)?.[1];
    assert(prov, `${tag}: provenance badge must be live or sample`);
    if (prov === "live") assert(/pulled \d{4}-\d{2}-\d{2}/.test(html), `${tag}: live badge must say "pulled YYYY-MM-DD"`);
    assert(!/<script[^>]+src=|<link[^>]+rel=["']?stylesheet|<iframe|<img[^>]+src=["']?https?:|@import|url\(\s*["']?https?:/i.test(html), `${tag}: external resource (must be self-contained)`);
    assert(/<script[^>]*>[^<]*\bfetch\(/i.test(html) === false, `${tag}: page must not fetch at runtime`);
    assert((html.match(/<dt>/g) ?? []).length >= 4 && html.includes('id="about-demo"'), `${tag}: About this demo box incomplete`);
    assert(html.includes("not affiliated with DC Government"), `${tag}: independence footer missing`);
    assert(/Generated \d{4}-\d{2}-\d{2}/.test(html), `${tag}: no Generated stamp`);
    assert(!/OWNER_NAME|PERMIT_APPLICANT|INSPECTORNAME/.test(html), `${tag}: raw personal field name present`);
    assert(!/lorem ipsum/i.test(html), `${tag}: lorem ipsum`);
    assert(Buffer.byteLength(html) < 1.5 * 1024 * 1024, `${tag}: page over 1.5 MB`);
  }
};

// ---------- phase 3: filled-out C5 site ----------
const SITE_PAGES = ["", "news/", "projects/", "homes/", "streets/", "then/", "jobs/", "representatives/", "subscribe/", "about/"];
const hoods = () => JSON.parse(read("site/src/data/index.json"));

checks.datafull = () => {
  for (const h of hoods()) {
    const d = JSON.parse(read(`site/src/data/${h.slug}.json`));
    const tag = h.slug;
    assert(d.homes && d.streets && d.history, `${tag}: homes/streets/history section missing (${JSON.stringify(d.module_errors ?? {})})`);
    if (!d.homes || !d.streets || !d.history) continue;
    assert(Object.keys(d.module_errors ?? {}).length === 0, `${tag}: module errors ${JSON.stringify(d.module_errors)}`);
    const hm = d.homes, st = d.streets, hi = d.history;
    const pk = hm.primary ?? "house"; // the home type that leads the section
    assert(hm[pk].count_12mo > 0 && hm[pk].median_12mo >= 100000 && hm[pk].median_12mo <= 5000000, `${tag}: implausible ${pk} median ${hm[pk].median_12mo}`);
    assert(hm.by_month.length >= 6, `${tag}: homes.by_month has ${hm.by_month.length} months`);
    assert(hm.recent_sales.length > 0, `${tag}: no recent sales`);
    assert(st.curb.active_this_week > 0 && st.trees.total > 0, `${tag}: empty curb or trees`);
    assert(st.service.length >= 4 && st.service.every((s) => s.median_days >= 0), `${tag}: service medians incomplete`);
    assert(hi.buildings.records > 0 && hi.buildings.featured_block && hi.buildings.by_decade.length > 0, `${tag}: history buildings incomplete`);
    assert(typeof hi.archive.note === "string" && Array.isArray(hi.archive.clips), `${tag}: archive malformed`);
    for (const sec of [hm, st, hi]) assert(Array.isArray(sec.sources) && sec.sources.length > 0, `${tag}: a section has no sources`);
    // Same-run freshness: every module section was produced by the run that wrote this file.
    for (const [k, sec] of Object.entries({ homes: hm, streets: st, history: hi }))
      assert(Math.abs(Date.parse(sec.generated_at) - Date.parse(d.generated_at)) < 30 * 60 * 1000, `${tag}: ${k} not from this run`);
  }
};

checks.sitefull = () => {
  for (const h of hoods()) {
    const d = JSON.parse(read(`site/src/data/${h.slug}.json`));
    for (const p of SITE_PAGES) {
      const file = `site/dist/${h.slug}/${p}index.html`;
      assert(existsSync(join(root, file)), `${file} not built`);
      if (!existsSync(join(root, file))) continue;
      const html = read(file);
      const tag = `${h.slug}/${p}`;
      assert(html.includes(`datetime="${d.generated_at}"`), `${tag}: freshness stamp missing or stale`);
      assert(html.includes("Not affiliated with the DC Government"), `${tag}: independence footer missing`);
      const visible = html.replace(/<script[\s\S]*?<\/script>/g, "");
      // Case-insensitive for mockup leftovers; whole-word and case-sensitive for NaN/undefined,
      // so real permit text like "maintenance" or "TENANT" can't trip it. ("approx" was dropped: permits say
      // "approx. 5,901 sf".)
      assert(!/LAYOUT C\d|lorem|\{\{/i.test(visible), `${tag}: mockup leftover in page`);
      assert(!/\bNaN\b|\bundefined\b/.test(visible), `${tag}: NaN or undefined rendered in page`);
      for (const q of SITE_PAGES) assert(html.includes(`href="/${h.slug}/${q}"`), `${tag}: nav link to /${h.slug}/${q} missing`);
      // every internal link on the page resolves to a built file (anchors ignored)
      for (const m of html.matchAll(/href="(\/[^"#?]*)/g)) {
        const target = m[1].endsWith("/") ? `${m[1]}index.html` : m[1];
        assert(existsSync(join(root, "site/dist", target)), `${tag}: broken internal link ${m[1]}`);
      }
    }
    assert(existsSync(join(root, `site/dist/${h.slug}/search.json`)), `${h.slug}: search.json not built`);
    const idx = JSON.parse(read(`site/dist/${h.slug}/search.json`));
    assert(idx.length >= d.permits.length, `${h.slug}: search index smaller than permit count`);
  }
};

checks.markers = () => {
  for (const h of hoods()) {
    const d = JSON.parse(read(`site/src/data/${h.slug}.json`));
    const html = read(`site/dist/${h.slug}/index.html`);
    const big = d.permits.filter((p) => ["Demolition", "New construction", "Additions"].includes(p.group));
    const withCoords = big.filter((p) => p.lat && p.lon);
    const marks = [...html.matchAll(/class="mk c-\w+" data-id="p([^"]+)" data-pid="[^"]+" data-lat="([^"]+)" data-lon="([^"]+)" data-addr="([^"]+)"/g)];
    assert(marks.length === withCoords.length, `${h.slug}: ${marks.length} markers for ${withCoords.length} mapped bigger projects`);
    for (const [, id, lat, lon, a] of marks) {
      const p = big.find((x) => x.id === id);
      assert(p, `${h.slug}: marker for unknown permit ${id}`);
      if (!p) continue;
      assert(+lat === p.lat && +lon === p.lon, `${h.slug}: marker ${id} not at its permit's coordinates`);
      assert(a.replace(/&amp;/g, "&") === p.address, `${h.slug}: marker ${id} address mismatch`);
    }
  }
};

checks.demoindex = () => {
  const path = "demos/ideas/index.html";
  assert(existsSync(join(root, path)), `${path} missing`);
  if (!existsSync(join(root, path))) return;
  const html = read(path);
  const top = rankedIdeas().filter((i) => i.rank <= 30);
  for (const i of top) {
    const card = html.match(new RegExp(`<li class="card" data-rank="${i.rank}" data-idea="${i.id.replace("#", "\\#")}">([\\s\\S]*?)</li>`))?.[1];
    assert(card, `index: no card for #${i.rank} ${i.id}`);
    if (!card) continue;
    const href = card.match(/<a href="([^"]+)"/)?.[1];
    assert(href, `index: #${i.rank} has no link`);
    if (href) assert(existsSync(join(root, "demos/ideas", href)), `index: #${i.rank} link ${href} does not resolve`);
    assert(!card.includes("prov-missing"), `index: #${i.rank} marked not built`);
  }
  assert((html.match(/<li class="card"/g) ?? []).length === 30, "index must have exactly 30 cards");
};

// ---- news & events ----
const NEWS_KEYS = ["first_seen", "published", "source", "title", "url"];
const EVENT_KEYS = ["date", "kind", "place", "source", "time", "title", "url"];
const etDay = (iso) => new Date(iso).toLocaleDateString("en-CA", { timeZone: "America/New_York" });
const addDays = (day, k) => new Date(Date.parse(day + "T12:00:00Z") + k * 86400_000).toISOString().slice(0, 10);
function newsItemProblems(it, now, days) {
  const p = [];
  if (Object.keys(it).sort().join() !== NEWS_KEYS.join()) p.push(`fields ${Object.keys(it).sort()}`); // no article text, ever
  if (!/^https?:\/\//.test(it.url ?? "")) p.push("url");
  if (!it.title || !it.source) p.push("title/source");
  const t = Date.parse(it.published);
  if (!(t <= now + 86400_000 && t >= now - days * 86400_000)) p.push(`published ${it.published} outside ${days} days`);
  return p;
}

checks.newsdata = () => {
  // Positive control: the item check must reject an item that carries article text or a stale date.
  const now0 = Date.now();
  const good = { title: "t", url: "https://x.test/a", source: "s", published: new Date(now0).toISOString(), first_seen: new Date(now0).toISOString() };
  assert(newsItemProblems(good, now0, 180).length === 0, "control: valid item rejected");
  assert(newsItemProblems({ ...good, summary: "copied text" }, now0, 180).length > 0, "control: item with article text accepted");
  assert(newsItemProblems({ ...good, published: "2001-01-01T00:00:00Z" }, now0, 180).length > 0, "control: stale item accepted");
  for (const h of hoods()) {
    const d = JSON.parse(read(`site/src/data/${h.slug}.json`));
    const tag = h.slug, nw = d.news, ev = d.events;
    assert(nw && ev, `${tag}: news/events section missing (${JSON.stringify(d.module_errors ?? {})})`);
    if (!nw || !ev) continue;
    const now = Date.parse(d.generated_at);
    for (const [k, sec] of Object.entries({ news: nw, events: ev }))
      assert(Math.abs(Date.parse(sec.generated_at) - now) < 30 * 60 * 1000, `${tag}: ${k} not from this run`);
    const ok = nw.outlets.filter((o) => o.state === "ok" || o.state === "partial");
    assert(ok.length >= nw.outlets.length / 2, `${tag}: only ${ok.length}/${nw.outlets.length} outlets read`);
    assert(nw.items.length > 0, `${tag}: no headlines`);
    for (const it of nw.items) { const p = newsItemProblems(it, now, nw.archive_days); assert(!p.length, `${tag}: news item ${it.url}: ${p.join(", ")}`); }
    assert(new Set(nw.items.map((i) => i.url)).size === nw.items.length, `${tag}: duplicate headline urls`);
    assert(nw.items.every((it, i) => i === 0 || nw.items[i - 1].published >= it.published), `${tag}: headlines not newest first`);
    assert(nw.licenses.active > 0 && Array.isArray(nw.licenses.ids), `${tag}: liquor licenses missing`);
    assert(nw.licenses.new.every((l) => Object.keys(l).sort().join() === "address,first_seen,license,trade_name,type"), `${tag}: license item carries extra fields`);
    assert(ev.today === etDay(d.generated_at), `${tag}: events.today ${ev.today} is not the run's Washington date ${etDay(d.generated_at)}`);
    const end = addDays(ev.today, ev.days_ahead);
    for (const e of ev.events) {
      assert(Object.keys(e).sort().join() === EVENT_KEYS.join(), `${tag}: event fields ${Object.keys(e)}`);
      assert(e.date >= ev.today && e.date < end, `${tag}: event ${e.title} on ${e.date} outside ${ev.today}..${end}`);
      assert(/^https?:\/\//.test(e.url), `${tag}: event ${e.title} has no link`);
    }
    assert(ev.events.every((e, i) => i === 0 || ev.events[i - 1].date <= e.date), `${tag}: events not in date order`);
    assert(ev.calendars.some((c) => c.name === "DC farmers market list" && c.state === "ok"), `${tag}: DC farmers market list not read`);
  }
};

const unamp = (s) => s.replace(/&/g, "&amp;");
checks.sitenews = () => {
  for (const h of hoods()) {
    const d = JSON.parse(read(`site/src/data/${h.slug}.json`));
    const page = read(`site/dist/${h.slug}/news/index.html`);
    const home = read(`site/dist/${h.slug}/index.html`);
    for (const it of d.news?.items ?? []) assert(page.includes(`href="${unamp(it.url)}"`), `${h.slug}/news: headline missing ${it.url}`);
    for (const e of d.events?.events ?? []) assert(page.includes(`href="${unamp(e.url)}"`) && page.includes(unamp(e.title).replace(/'/g, "&#39;")) , `${h.slug}/news: event missing ${e.title} ${e.date}`);
    for (const it of (d.news?.items ?? []).slice(0, 6)) assert(home.includes(`href="${unamp(it.url)}"`), `${h.slug}/: top headline missing ${it.url}`);
    const iH = home.indexOf('id="happening"'), iC = home.indexOf('id="condition"');
    assert(iH > 0 && iC > iH, `${h.slug}/: news & events band is not above today's condition`);
    assert(home.includes('href="/' + h.slug + '/news/"'), `${h.slug}/: no link to the news page`);
    // Every headline link opens the outlet (external), never a copy on our site.
    for (const m of page.matchAll(/<ol class="hl">([\s\S]*?)<\/ol>/g))
      for (const a of m[1].matchAll(/<a href="([^"]+)"/g)) assert(/^https?:\/\//.test(a[1]), `${h.slug}/news: headline link ${a[1]} is not external`);
  }
};

// ---- curated history content: every street-name entry cites a source; every voice links to an archive ----
const words = (t) => (t ?? "").trim().split(/\s+/).filter(Boolean).length;
checks.curated = () => {
  const sn = JSON.parse(read("site/src/curated/streetnames.json"));
  const vo = JSON.parse(read("site/src/curated/voices.json"));
  // Curated research exists for some neighborhoods only; the Then page omits the sections elsewhere.
  // Both researched neighborhoods must keep their entries.
  for (const slug of ["petworth", "tenleytown"]) assert(sn.neighborhoods?.[slug]?.entries?.length > 0, `${slug}: no street-name entries`);
  for (const h of hoods()) {
    const s = sn.neighborhoods?.[h.slug];
    for (const e of s?.entries ?? []) {
      assert(e.name && e.summary, `${h.slug}: street entry missing name/summary`);
      assert(words(e.summary) <= 60, `${h.slug}: ${e.name} summary over 60 words`);
      assert(Array.isArray(e.sources) && e.sources.length > 0 && e.sources.every((x) => /^https:\/\//.test(x.url) && x.title), `${h.slug}: ${e.name} has no usable source`);
    }
    for (const v of vo.neighborhoods?.[h.slug] ?? []) {
      assert(/^https:\/\//.test(v.url) && v.title && v.archive, `${h.slug}: voice item incomplete ${v.title}`);
      assert(words(v.summary) <= 70, `${h.slug}: voice summary over 70 words ${v.title}`);
    }
    const page = read(`site/dist/${h.slug}/then/index.html`);
    for (const e of s?.entries ?? []) for (const x of e.sources) assert(page.includes(`href="${x.url.replace(/&/g, "&amp;")}"`), `${h.slug}/then: source link missing for ${e.name}`);
    for (const v of vo.neighborhoods?.[h.slug] ?? []) assert(page.includes(`href="${v.url.replace(/&/g, "&amp;")}"`), `${h.slug}/then: voice link missing ${v.title}`);
  }
};

// ---- ANC Decoder, openings & closings, cross-site links ----
checks.decoder = () => {
  const sites = JSON.parse(read("site/src/data/index.json"));
  for (const h of hoods()) {
    const d = JSON.parse(read(`site/src/data/${h.slug}.json`));
    const rep = read(`site/dist/${h.slug}/representatives/index.html`);
    assert(rep.includes('id="decoder"'), `${h.slug}: no ANC Decoder section`);
    for (const it of (d.news?.items ?? []).filter((i) => /^ANC /.test(i.source)).slice(0, 14))
      assert(rep.includes(`href="${it.url.replace(/&/g, "&amp;")}"`), `${h.slug}: ANC post missing from decoder ${it.url}`);
    const lic = d.news?.licenses;
    assert(lic && Array.isArray(lic.cancelled), `${h.slug}: licenses.cancelled missing`);
    const news = read(`site/dist/${h.slug}/news/index.html`);
    assert(news.includes('id="openings"'), `${h.slug}: no Openings & closings section`);
    for (const c of lic?.cancelled ?? []) {
      assert(Object.keys(c).sort().join() === "address,cancelled,first_seen,license,trade_name,type", `${h.slug}: cancelled item fields ${Object.keys(c)}`);
      assert(!lic.ids.includes(c.license), `${h.slug}: ${c.license} is both active and cancelled`);
    }
    // every page links every other live neighborhood's own domain
    for (const p of SITE_PAGES) {
      const html = read(`site/dist/${h.slug}/${p}index.html`);
      for (const o of sites.filter((x) => x.slug !== h.slug)) assert(html.includes(`href="https://${o.hosts[0]}/"`), `${h.slug}/${p}: no link to ${o.hosts[0]}`);
    }
  }
};

// ---- jobs: title/employer/place/date/link only, every job on the page, links go to the employer ----
const JOB_KEYS = "employer,hours,note,place,posted,title,url,where";
const jobProblems = (j) => {
  const p = [];
  if (Object.keys(j).sort().join() !== JOB_KEYS) p.push(`fields ${Object.keys(j).sort()}`);
  if (!/^https:\/\//.test(j.url ?? "")) p.push("url");
  if (!["in", "nearby"].includes(j.where)) p.push("where");
  return p;
};
checks.jobs = () => {
  const good = { title: "t", employer: "e", place: "p", where: "in", note: null, posted: null, hours: null, url: "https://x.test/j" };
  assert(jobProblems(good).length === 0, "control: valid job rejected");
  assert(jobProblems({ ...good, description: "copied" }).length > 0, "control: job with a description accepted");
  for (const h of hoods()) {
    const d = JSON.parse(read(`site/src/data/${h.slug}.json`));
    const jb = d.jobs;
    assert(jb, `${h.slug}: jobs section missing (${JSON.stringify(d.module_errors ?? {})})`);
    if (!jb) continue;
    assert(jb.employers.some((e) => e.state === "ok"), `${h.slug}: no employer feed read`);
    const page = read(`site/dist/${h.slug}/jobs/index.html`);
    for (const j of jb.jobs) {
      const p = jobProblems(j);
      assert(!p.length, `${h.slug}: job ${j.url}: ${p.join(", ")}`);
      assert(page.includes(`href="${j.url.replace(/&/g, "&amp;")}"`), `${h.slug}/jobs: missing ${j.title}`);
    }
  }
};

const name = process.argv[2];
if (!checks[name]) {
  console.error(`usage: node tools/verify.mjs <${Object.keys(checks).join("|")}>`);
  process.exit(2);
}
await checks[name]();
if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}
console.log(`${name} verified`);
