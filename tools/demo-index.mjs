// Build demos/ideas/index.html: one card per top-30 idea, linking to its demo, with provenance read from the page itself.
// Usage: node tools/demo-index.mjs
import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(join(root, p), "utf8");
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const ALIASES = { 3: { href: "../digest-petworth.html", path: "demos/digest-petworth.html" } };

const block = read("research/IDEAS.md").match(/<!-- ranking:start -->([\s\S]*?)<!-- ranking:end -->/)[1];
const ideas = [...block.matchAll(/^\| (\d+) \| (.*?) \| (\w+) \|.*\| ([\d.]+) \| [\d.]+ \| `([^`]+)` \|$/gm)]
  .map((m) => ({ rank: +m[1], title: m[2], engine: m[3], score: m[4], id: m[5] }))
  .filter((i) => i.rank <= 30);

const files = readdirSync(join(root, "demos/ideas")).filter((f) => /^\d\d-.*\.html$/.test(f));
const lensName = { "civic-data": "Civic data", monetization: "Money", "culture-content": "History & culture", "transit-tech": "Transit & tech" };

const cards = ideas.map((i) => {
  const nn = String(i.rank).padStart(2, "0");
  const alias = ALIASES[i.rank];
  const file = alias ? null : files.find((f) => f.startsWith(`${nn}-`));
  const href = alias ? alias.href : file;
  const path = alias ? alias.path : file && `demos/ideas/${file}`;
  const html = path && existsSync(join(root, path)) ? read(path) : "";
  const prov = alias ? "live" : html.match(/data-provenance="(live|sample)"/)?.[1] ?? "missing";
  const name = i.title.split(/:\s|\s\(/)[0];
  const pitch = i.title.includes(":") ? i.title.slice(i.title.indexOf(":") + 1).trim() : "";
  return `<li class="card" data-rank="${i.rank}" data-idea="${esc(i.id)}">
  <div class="top"><span class="rank">#${i.rank}</span><span class="score">${i.score}</span></div>
  <h2>${href ? `<a href="${esc(href)}">${esc(name)}</a>` : esc(name)}</h2>
  ${pitch ? `<p>${esc(pitch.replace(/^"|"$/g, ""))}</p>` : ""}
  <div class="meta"><span class="eng eng-${i.engine.toLowerCase()}">${i.engine}</span><span class="lens">${esc(lensName[i.id.split("#")[0]])}</span><span class="prov prov-${prov}">${prov === "live" ? "Live data" : prov === "sample" ? "Sample data" : "Not built"}</span></div>
</li>`;
});

const live = cards.filter((c) => c.includes("prov-live")).length;
const page = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Top 30 Idea Demos</title>
<style>
:root{--bg:#f6f7f4;--card:#fff;--ink:#1c2420;--muted:#5b6660;--line:#dfe3dc;--accent:#245c4f;--brick:#a2412b;--gold:#8a6a1f;--live:#2c6e49;--sample:#8a6a1f}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121715;--card:#1a201d;--ink:#e6ebe7;--muted:#9ba7a1;--line:#2c3430;--accent:#7dc3ac;--brick:#e58a72;--gold:#d8b25c;--live:#8fd3a8;--sample:#d8b25c;color-scheme:dark}}
:root[data-theme=dark]{--bg:#121715;--card:#1a201d;--ink:#e6ebe7;--muted:#9ba7a1;--line:#2c3430;--accent:#7dc3ac;--brick:#e58a72;--gold:#d8b25c;--live:#8fd3a8;--sample:#d8b25c;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:24px max(16px,env(safe-area-inset-right,0px)) 48px max(16px,env(safe-area-inset-left,0px))}
h1{margin:.2rem 0 .4rem;font-size:clamp(1.7rem,5vw,2.3rem)}a{color:var(--accent)}
.muted{color:var(--muted)}
ol{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:6px;min-width:0}
.card h2{font-size:1.02rem;margin:0;line-height:1.3}
.card p{margin:0;font-size:.88rem;color:var(--muted)}
.top{display:flex;justify-content:space-between;font-size:.8rem;color:var(--muted);font-variant-numeric:tabular-nums}
.rank{font-weight:700;color:var(--brick)}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:auto;padding-top:6px;font-size:.72rem}
.meta span{border:1px solid var(--line);border-radius:999px;padding:2px 8px}
.eng-data{color:var(--accent)}.eng-history{color:var(--gold)}.eng-transit{color:var(--brick)}
.prov-live{color:var(--live);border-color:currentColor!important;font-weight:600}.prov-sample{color:var(--sample);border-color:currentColor!important;font-weight:600}.prov-missing{color:var(--brick)}
</style></head><body><div class="wrap">
<p class="muted"><a href="../../">← Research summary</a></p>
<h1>Top 30 ideas, demoed</h1>
<p class="muted">One working demo per idea, in ranked order. ${live} of ${ideas.length} run on live DC data; the rest use clearly labeled sample data where the real source needs an API key or doesn't exist yet. Every demo ends with an "About this demo" box saying what's real and what's mocked.</p>
<ol>
${cards.join("\n")}
</ol>
</div></body></html>`;

writeFileSync(join(root, "demos/ideas/index.html"), page);
console.log(`index: ${ideas.length} ideas, ${live} live, ${cards.filter((c) => c.includes("prov-sample")).length} sample, ${cards.filter((c) => c.includes("prov-missing")).length} missing`);
