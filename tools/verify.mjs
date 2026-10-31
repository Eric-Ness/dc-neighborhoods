// Gate checks for GATES.md. Usage: node tools/verify.mjs <ideas|ranking|docs|privacy|site|deploy|demos>
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
    const FORBIDDEN = ["OWNER_NAME", "PERMIT_APPLICANT", "INSPECTORNAME", "DETAILS", "CCN"];
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
      assert(html.includes(`>${data.permits.length}</div>`), `${h.slug}: permit count ${data.permits.length} not rendered`);
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
    for (const h of index) for (const host of [...h.hosts, ...h.redirect_hosts]) assert(wr.includes(`"${host}"`), `wrangler.jsonc missing route for ${host}`);

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
