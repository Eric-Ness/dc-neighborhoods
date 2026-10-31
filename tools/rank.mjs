// Rebuild the ranking table inside research/IDEAS.md from the idea files and reviewer adjustments.
// Usage: node tools/rank.mjs
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { loadIdeas, adjusted, weighted, CRITERIA } from "./ideas-lib.mjs";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const adjustments = JSON.parse(readFileSync(join(root, "research", "reviewer-adjustments.json"), "utf8"));

// Which shared engine each idea runs on. Ideas on the same engine share most of their build cost.
const ENGINE = {
  "civic-data": "Data",
  "culture-content": "History",
  "transit-tech": "Transit",
  "monetization#6": "Transit",
  "monetization#7": "None",
  "monetization#9": "None",
};
const engineOf = (idea) => ENGINE[idea.id] ?? ENGINE[idea.lens] ?? "Data";

const rows = loadIdeas(root).map((idea) => {
  const { scores, note } = adjusted(idea, adjustments);
  return { ...idea, adj: scores, note, w: weighted(scores), selfW: weighted(idea.scores), engine: engineOf(idea) };
});
rows.sort((a, b) => b.w - a.w || a.id.localeCompare(b.id));

const short = { Usefulness: "Use", Uniqueness: "Uniq", Monetization: "$", "Low-upkeep": "Upk", "Build ease": "Build", Traffic: "Traf", "Skill fit": "Fit" };
const lines = [];
lines.push(`| Rank | Idea | Engine | ${CRITERIA.map((c) => short[c]).join(" | ")} | Weighted /100 | Self-score /100 | Source |`);
lines.push(`|---:|---|---|${CRITERIA.map(() => "---:").join("|")}|---:|---:|---|`);
rows.forEach((r, i) => {
  const cells = CRITERIA.map((c) => (r.adj[c] !== r.scores[c] ? `**${r.adj[c]}**` : `${r.adj[c]}`));
  const title = r.title.replace(/\|/g, "/");
  lines.push(`| ${i + 1} | ${title} | ${r.engine} | ${cells.join(" | ")} | ${r.w} | ${r.selfW} | \`${r.id}\` |`);
});
lines.push("");
lines.push("Bold cells are reviewer adjustments to the researcher's self-score:");
lines.push("");
for (const r of rows.filter((r) => r.note)) lines.push(`- \`${r.id}\`: ${r.note}`);

const engines = {};
for (const r of rows) (engines[r.engine] ??= []).push(r);
lines.push("");
lines.push("| Engine | Ideas | Mean weighted | Best idea |");
lines.push("|---|---:|---:|---|");
for (const [name, list] of Object.entries(engines).sort((a, b) => b[1].length - a[1].length)) {
  const mean = Math.round((list.reduce((a, r) => a + r.w, 0) / list.length) * 10) / 10;
  lines.push(`| ${name} | ${list.length} | ${mean} | ${list[0].title.replace(/\|/g, "/")} |`);
}

const table = lines.join("\n");
const target = join(root, "research", "IDEAS.md");
const START = "<!-- ranking:start -->";
const END = "<!-- ranking:end -->";
let doc = existsSync(target) ? readFileSync(target, "utf8") : `# Idea ranking\n\n${START}\n${END}\n`;
if (!doc.includes(START) || !doc.includes(END)) throw new Error("IDEAS.md is missing ranking markers");
doc = doc.replace(new RegExp(`${START}[\\s\\S]*?${END}`), `${START}\n${table}\n${END}`);
writeFileSync(target, doc);
console.log(`ranked ${rows.length} ideas`);
for (const r of rows.slice(0, 12)) console.log(`${r.w}\t${r.engine}\t${r.id}\t${r.title}`);
