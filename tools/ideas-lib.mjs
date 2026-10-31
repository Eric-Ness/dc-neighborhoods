// Shared parser for research/ideas/*.md. Used by rank.mjs (to build IDEAS.md) and verify.mjs (to check it).
import { readFileSync, readdirSync } from "node:fs";
import { join, basename } from "node:path";

export const CRITERIA = ["Usefulness", "Uniqueness", "Monetization", "Low-upkeep", "Build ease", "Traffic", "Skill fit"];

// Weights reflect the owner's stated priorities: useful, low-upkeep, a great idea (unique, finds an audience), some money.
// Skill fit is low-weighted because nearly every idea fits an Astro/Cloudflare/Python developer.
export const WEIGHTS = {
  Usefulness: 1.5,
  Uniqueness: 1.25,
  Monetization: 1.25,
  "Low-upkeep": 1.5,
  "Build ease": 1.0,
  Traffic: 1.25,
  "Skill fit": 0.5,
};

const SCORE_RE = /^\s*(?:-\s*)?\*\*Scores:\*\*\s*(.+)$/;
const IDEA_RE = /^## (\d+)\.\s+(.+)$/;

export function parseIdeaFile(path) {
  const lens = basename(path, ".md");
  const lines = readFileSync(path, "utf8").split(/\r?\n/);
  const ideas = [];
  let current = null;
  for (const line of lines) {
    const head = line.match(IDEA_RE);
    if (head) {
      current = { id: `${lens}#${head[1]}`, lens, num: Number(head[1]), title: head[2].trim(), scores: null, total: null, errors: [] };
      ideas.push(current);
      continue;
    }
    if (line.startsWith("## ")) current = null;
    const m = current && line.match(SCORE_RE);
    if (m) {
      const scores = {};
      for (const c of CRITERIA) {
        const sm = m[1].match(new RegExp(`${c.replace("-", "\\-")}\\s+(\\d)`));
        if (!sm) current.errors.push(`missing ${c}`);
        else scores[c] = Number(sm[1]);
      }
      const tm = m[1].match(/Total\s+(\d+)/);
      current.scores = scores;
      current.total = tm ? Number(tm[1]) : null;
      if (current.total === null) current.errors.push("missing Total");
    }
  }
  for (const idea of ideas) {
    if (!idea.scores) idea.errors.push("no Scores line");
    else {
      const sum = CRITERIA.reduce((a, c) => a + (idea.scores[c] ?? 0), 0);
      if (sum !== idea.total) idea.errors.push(`Total ${idea.total} != sum ${sum}`);
      for (const c of CRITERIA) if (!(idea.scores[c] >= 1 && idea.scores[c] <= 5)) idea.errors.push(`${c} out of range`);
    }
  }
  return ideas;
}

export function loadIdeas(root) {
  const dir = join(root, "research", "ideas");
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .flatMap((f) => parseIdeaFile(join(dir, f)));
}

export function weighted(scores) {
  const max = Object.values(WEIGHTS).reduce((a, w) => a + w * 5, 0);
  const got = CRITERIA.reduce((a, c) => a + WEIGHTS[c] * scores[c], 0);
  return Math.round((got / max) * 1000) / 10;
}

// Apply reviewer adjustments (research/reviewer-adjustments.json) on top of each researcher's self-scores.
export function adjusted(idea, adjustments) {
  const adj = adjustments[idea.id];
  const scores = { ...idea.scores };
  if (adj) for (const [c, v] of Object.entries(adj.set)) scores[c] = v;
  return { scores, note: adj?.why ?? "" };
}
