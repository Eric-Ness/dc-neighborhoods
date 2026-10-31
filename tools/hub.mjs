// Build research/hub.html: a one-page summary of the research, generated from the same files the gates check.
// Usage: node tools/hub.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { loadIdeas, adjusted, weighted } from "./ideas-lib.mjs";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(join(root, p), "utf8");
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const adjustments = JSON.parse(read("research/reviewer-adjustments.json"));
const engineOf = (i) => ({ "civic-data": "Data", "culture-content": "History", "transit-tech": "Transit" })[i.lens] ?? ({ "monetization#6": "Transit", "monetization#7": "None", "monetization#9": "None" })[i.id] ?? "Data";
const ideas = loadIdeas(root)
  .map((i) => ({ ...i, w: weighted(adjusted(i, adjustments).scores), engine: engineOf(i), adj: adjusted(i, adjustments).scores }))
  .sort((a, b) => b.w - a.w);
const lensName = { "civic-data": "Civic data", monetization: "Money", "culture-content": "History & culture", "transit-tech": "Transit & tech" };
const pw = JSON.parse(read("site/src/data/petworth.json"));
const tt = JSON.parse(read("site/src/data/tenleytown.json"));
const rodent = pw.requests.by_type.find((t) => /rodent/i.test(t.type));
const asOf = new Date(pw.generated_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "America/New_York" });
const shortTitle = (t) => t.split(/:\s|\s\(/)[0];

const rows = ideas
  .map(
    (i, n) => `<tr class="${n < 6 ? "top" : ""}"><td class="num">${n + 1}</td><td><span class="idea">${esc(shortTitle(i.title))}</span><span class="lens">${esc(lensName[i.lens])}</span></td>
<td><span class="eng eng-${i.engine.toLowerCase()}">${i.engine}</span></td>
<td class="num">${i.adj.Usefulness}</td><td class="num">${i.adj.Uniqueness}</td><td class="num">${i.adj.Monetization}</td><td class="num">${i.adj["Low-upkeep"]}</td>
<td class="num score"><span class="bar" style="--w:${i.w}%"></span>${i.w}</td></tr>`,
  )
  .join("\n");

const page = `<title>DC Neighborhoods Research</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,650&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: a single reading column with wide tables that scroll inside their own frames; rowhouse-brick accent on a park-green base. */
:root{
  --bg:#f6f7f4; --surface:#ffffff; --ink:#1c2420; --muted:#5b6660; --line:#dfe3dc;
  --green:#245c4f; --brick:#a2412b; --soft:#e5eee9; --gold:#8a6a1f;
  --display:"Newsreader",Georgia,"Times New Roman",serif; --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; --mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121715;--surface:#1a201d;--ink:#e6ebe7;--muted:#9ba7a1;--line:#2c3430;--green:#7dc3ac;--brick:#e58a72;--soft:#1f2b27;--gold:#d8b25c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121715;--surface:#1a201d;--ink:#e6ebe7;--muted:#9ba7a1;--line:#2c3430;--green:#7dc3ac;--brick:#e58a72;--soft:#1f2b27;--gold:#d8b25c;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font:16px/1.6 var(--body)}
.wrap{max-width:900px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:32px 64px}
h1,h2{font-family:var(--display);font-weight:650;text-wrap:balance;line-height:1.15}
h1{font-size:clamp(2rem,5vw,2.8rem);margin:.2rem 0 .6rem}
h2{font-size:1.5rem;margin:2.6rem 0 .8rem}
p{max-width:68ch}
a{color:var(--green)}
a:focus-visible{outline:2px solid var(--brick);outline-offset:2px}
.eyebrow{font:500 .75rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--brick);margin:0}
.lede{font-size:1.1rem;color:var(--muted)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:1.4rem 0}
.fact{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 16px;min-width:0}
.fact b{display:block;font:650 1.7rem/1.1 var(--display);color:var(--green);font-variant-numeric:tabular-nums}
.fact span{font-size:.88rem;color:var(--muted)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:.9rem;min-width:640px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font:500 .7rem/1.2 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);background:var(--soft)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr.top .idea{font-weight:600}
.idea{display:block}
.lens{display:block;font-size:.78rem;color:var(--muted)}
.eng{font:500 .72rem/1 var(--mono);padding:3px 7px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.eng-data{color:var(--green);border-color:var(--green)}
.eng-history{color:var(--gold);border-color:var(--gold)}
.eng-transit{color:var(--brick);border-color:var(--brick)}
.eng-none{color:var(--muted)}
.score{position:relative;font-weight:600;min-width:90px}
.score .bar{position:absolute;left:10px;right:10px;bottom:4px;height:3px;background:var(--line);border-radius:2px}
.score .bar::after{content:"";position:absolute;inset:0 auto 0 0;width:var(--w);background:var(--green);border-radius:2px}
.phases{display:grid;gap:10px;margin:0;padding:0;list-style:none}
.phase{display:grid;grid-template-columns:110px minmax(0,1fr);gap:12px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.phase .when{font:500 .78rem/1.4 var(--mono);color:var(--brick)}
.phase p{margin:.2rem 0 0;color:var(--muted);font-size:.92rem}
@media (max-width:520px){.phase{grid-template-columns:1fr;gap:2px}}
.demos{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.demo{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 16px;min-width:0}
.demo h3{margin:.1rem 0 .3rem;font:600 1rem/1.3 var(--body)}
.demo p{font-size:.9rem;color:var(--muted);margin:0 0 .5rem}
ul.tight{padding-left:1.1rem}ul.tight li{margin:.3rem 0}
.note{font-size:.85rem;color:var(--muted)}
</style>

<div class="wrap">
<p class="eyebrow">Research for petworth.org, tenleytown.org, adamsmorgan.org, friendshipheights.org, lenfantplaza.org</p>
<h1>What to build on five DC neighborhood domains</h1>
<p class="lede">Four research agents proposed ${ideas.length} ideas. I corrected ${Object.keys(adjustments).length} optimistic scores and ranked the ideas against your priorities. The recommendation: build one automated civic-data engine that turns DC's open data into a weekly page and email per neighborhood, then add block-history pages for search traffic.</p>

<div class="facts">
  <div class="fact"><b>${ideas.length}</b><span>ideas scored on 7 criteria</span></div>
  <div class="fact"><b>${ideas.filter((i) => i.engine === "Data").length}</b><span>of them run on the one data engine v1 already built</span></div>
  <div class="fact"><b>${pw.permits.length} / ${pw.requests.total.toLocaleString()}</b><span>permits / 311 requests in Petworth, last 30 days</span></div>
  <div class="fact"><b>${rodent ? `+${Math.round(((rodent.count - rodent.previous) / rodent.previous) * 100)}%` : "n/a"}</b><span>Petworth rodent complaints vs. the prior 30 days${rodent ? ` (${rodent.count} vs ${rodent.previous})` : ""}</span></div>
</div>
<p class="note">Live figures pulled from Open Data DC on ${esc(asOf)}. Tenleytown in the same window: ${tt.permits.length} permits, ${tt.requests.total.toLocaleString()} 311 requests.</p>

<h2>Ranking</h2>
<p>Weighted score out of 100. The weights favor usefulness and low upkeep (1.5 each), then uniqueness, money and traffic (1.25 each), then build ease (1.0) and skill fit (0.5). "Engine" is the shared code an idea runs on; ideas on the same engine share most of their build.</p>
<div class="scroll"><table>
<thead><tr><th class="num">#</th><th>Idea</th><th>Engine</th><th class="num">Useful</th><th class="num">Unique</th><th class="num">Money</th><th class="num">Upkeep</th><th class="num">Weighted</th></tr></thead>
<tbody>
${rows}
</tbody></table></div>

<h2>Recommended path</h2>
<ul class="phases">
  <li class="phase"><span class="when">v1 · built</span><div><strong>Block Watch pages for Petworth and Tenleytown</strong><p>Nightly ingest, Astro pages, RSS, Cloudflare Worker routing, GitHub Action. Ready to deploy once the domains are on Cloudflare.</p></div></li>
  <li class="phase"><span class="when">Month 1–2</span><div><strong>Weekly digest email, plus Adams Morgan and Friendship Heights</strong><p>The email is the retention loop and the sponsor inventory. Friendship Heights needs its own boundary, because DC's "Tenleytown" polygon includes it.</p></div></li>
  <li class="phase"><span class="when">Month 3–4</span><div><strong>Block and address pages</strong><p>Original 1900s building permits next to today's permits and 311. Evergreen search traffic and a realtor sponsorship slot.</p></div></li>
  <li class="phase"><span class="when">Spring</span><div><strong>L'Enfant Transfer Coach</strong><p>Exits, escalators and live arrivals for the five-line transfer, ahead of tourist season. Affiliate links only on lenfantplaza.net.</p></div></li>
</ul>

<h2>Demos built from live data</h2>
<div class="demos">
  <div class="demo"><h3>Petworth Weekly (email)</h3><p>The automated digest with one labeled sponsor slot. Every item comes from the nightly ingest.</p><a href="demos/digest-petworth.html">Open the digest demo</a></div>
  <div class="demo"><h3>400 block of Delafield Place NW</h3><p>The Cafritz Construction Co. built all 62 rowhouses in 1926, on four permits. The block page shows that next to this year's permits and 311 requests.</p><a href="demos/block-delafield.html">Open the block page demo</a></div>
</div>

<h2>Money, honestly</h2>
<ul class="tight">
  <li><strong>Model:</strong> one exclusive "presented by" sponsor per neighborhood digest, plus a few small slots. No display ads, no paid placement in the data, no lead selling.</li>
  <li><strong>Benchmarks found:</strong> newsletters under 5K subscribers sell placements for $50–250. One solo local newsletter reports about $6K a month from 12 sponsors on 2–3K subscribers. Display ads at this scale earn $25–100 a month.</li>
  <li><strong>Estimate at month 18:</strong> $0–300 a month conservative, $600–1,200 base, $2–4K upside. Costs are about $80–500 a year.</li>
  <li><strong>Decision point at month 4:</strong> keep going at 300+ subscribers in a neighborhood or growing search traffic; otherwise pivot to block pages only, or lease the domains.</li>
</ul>

<h2>Guardrails already in the code</h2>
<ul class="tight">
  <li>Permit owner and applicant names are never requested from DC's servers.</li>
  <li>311 locations are coarsened to the hundred block; crime is fetched only as counts by offense.</li>
  <li>No percentages on small counts, so 49 vs. 40 crime reports doesn't read as a spike.</li>
  <li>Every page says it is independent and shows when its data was pulled. A warning appears if the data is more than 3 days old.</li>
</ul>
<p class="note">The full write-ups for all ${ideas.length} ideas, the business case and the content strategy are in the project's research folder.</p>
</div>`;

writeFileSync(join(root, "research", "hub.html"), page);
console.log(`hub.html written: ${ideas.length} ideas`);
