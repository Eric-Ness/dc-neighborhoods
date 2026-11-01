// Gate check: no built page scrolls horizontally on a 375px phone.
// Serves site/dist on a local port, drives headless Chrome over the DevTools protocol with real
// phone emulation (plain --window-size can't go below ~500px on Windows), and measures every page.
// Usage: node tools/overflow.mjs [--width 375]
import { spawn } from "node:child_process";
import { existsSync, readdirSync, statSync, mkdtempSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "site", "dist");
const width = Number(process.argv[process.argv.indexOf("--width") + 1]) || 375;
const CHROME = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
].find((p) => p && existsSync(p));
if (!CHROME) { console.error("no Chrome/Edge found; set CHROME_PATH"); process.exit(1); }

const pages = [];
(function walk(dir) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) { if (!f.startsWith("_")) walk(p); }
    else if (f === "index.html") pages.push("/" + p.slice(dist.length + 1).replace(/\\/g, "/").replace(/index\.html$/, ""));
  }
})(dist);
// ~2,600 block pages share one template: by default measure the 3 longest-named per neighborhood (--all for every one).
if (!process.argv.includes("--all")) {
  const blocks = pages.filter((p) => /\/blocks\/[^/]+\/$/.test(p));
  const keep = new Set();
  for (const slug of new Set(blocks.map((p) => p.split("/")[1])))
    blocks.filter((p) => p.split("/")[1] === slug).sort((a, b) => b.length - a.length).slice(0, 3).forEach((p) => keep.add(p));
  for (let i = pages.length - 1; i >= 0; i--) if (blocks.includes(pages[i]) && !keep.has(pages[i])) pages.splice(i, 1);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const port = 9300 + Math.floor(Math.random() * 400); // clear of the usual dev ports
const server = spawn("python", ["-m", "http.server", String(port), "--bind", "127.0.0.1", "--directory", dist], { stdio: "ignore" });
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--remote-debugging-port=" + (port + 1000),
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "overflow-"))}`, "about:blank"], { stdio: "ignore" });
const cleanup = () => { chrome.kill(); server.kill(); };

try {
  let target;
  for (let i = 0; i < 60 && !target; i++) {
    await sleep(250);
    try { target = (await (await fetch(`http://127.0.0.1:${port + 1000}/json`)).json()).find((t) => t.type === "page"); } catch {}
  }
  if (!target) throw new Error("Chrome did not start");
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r, { once: true }));
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
  await send("Emulation.setDeviceMetricsOverride", { width, height: 812, deviceScaleFactor: 1, mobile: true });

  const failures = [];
  for (const p of pages) {
    await send("Page.navigate", { url: `http://127.0.0.1:${port}${p}` });
    await sleep(900);
    const expr = `(() => { const d = document.documentElement; const over = d.scrollWidth - d.clientWidth;
      let who = ""; if (over > 0) { const el = [...document.body.querySelectorAll("*")].find((e) => e.getBoundingClientRect().right > d.clientWidth + 1 && !e.closest(".tbl-wrap,.dtable-wrap,nav.snav,.scroll")); who = el ? el.tagName + "." + el.className : "?"; }
      return JSON.stringify({ over, who }); })()`;
    const { result } = await send("Runtime.evaluate", { expression: expr });
    const r = JSON.parse(result.result.value);
    if (r.over > 0) failures.push(`${p}: ${r.over}px too wide (${r.who})`);
  }
  ws.close();
  cleanup();
  if (failures.length) { console.error(failures.join("\n")); process.exit(1); }
  console.log(`checked ${pages.length} pages at ${width}px`);
  console.log("overflow verified");
} catch (err) {
  cleanup();
  console.error(err.message);
  process.exit(1);
}
