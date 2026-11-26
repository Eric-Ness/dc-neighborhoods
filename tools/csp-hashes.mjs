// After `astro build`: list the SHA-256 hash of every inline script in site/dist and write them to
// worker/csp-hashes.json. The Worker's Content-Security-Policy allows exactly those inline scripts,
// so it needs no 'unsafe-inline'. A script someone manages to inject has a different hash and
// doesn't run.
//
//   node tools/csp-hashes.mjs            write the list (the site build runs this)
//   node tools/csp-hashes.mjs --check    fail if the committed list is out of date with site/dist
//
// Inline scripts must be the same on every page for this list to stay short: put per-page values
// in data attributes (see the staleness script in site/src/layouts/Base.astro), not in the code.
import { createHash } from "node:crypto";
import { readdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const dist = join(root, "site", "dist");
const out = join(root, "worker", "csp-hashes.json");
const MAX = 60; // far more than this means a per-page value leaked into a script

const SCRIPT = /<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi;
const DATA_TYPES = /\btype\s*=\s*["']?(application\/(ld\+)?json|text\/template|text\/plain)/i;

async function* htmlFiles(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) yield* htmlFiles(p);
    else if (e.name.endsWith(".html")) yield p;
  }
}

const hashes = new Map(); // hash -> { pages, example }
let pages = 0;
for await (const file of htmlFiles(dist)) {
  pages++;
  const html = await readFile(file, "utf8");
  for (const [, attrs, body] of html.matchAll(SCRIPT)) {
    if (/\bsrc\s*=/i.test(attrs) || DATA_TYPES.test(attrs)) continue; // external, or data the browser never runs
    // Browsers hash the script text after the HTML parser turns CRLF and CR into LF.
    const text = body.replace(/\r\n?/g, "\n");
    const h = `'sha256-${createHash("sha256").update(text, "utf8").digest("base64")}'`;
    const seen = hashes.get(h) ?? { pages: 0, example: file.slice(dist.length + 1) };
    seen.pages++;
    hashes.set(h, seen);
  }
}
if (!pages) throw new Error(`No HTML in ${dist}: build the site first.`);

const list = [...hashes.keys()].sort();
if (list.length > MAX) {
  const rare = [...hashes].sort((a, b) => a[1].pages - b[1].pages).slice(0, 5);
  console.error(`${list.length} different inline scripts across ${pages} pages (limit ${MAX}). The rarest:`);
  for (const [h, s] of rare) console.error(`  ${h} on ${s.pages} page(s), e.g. ${s.example}`);
  process.exit(1);
}

const json = JSON.stringify(list, null, 2) + "\n";
if (process.argv.includes("--check")) {
  const current = await readFile(out, "utf8").catch(() => "");
  if (current !== json) {
    console.error("worker/csp-hashes.json is out of date with site/dist: run node tools/csp-hashes.mjs");
    process.exit(1);
  }
  console.log(`csp-hashes.json matches: ${list.length} inline scripts on ${pages} pages`);
} else {
  await writeFile(out, json);
  console.log(`Wrote ${list.length} inline script hashes from ${pages} pages to worker/csp-hashes.json`);
}
