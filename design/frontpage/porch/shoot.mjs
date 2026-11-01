// Phone-viewport screenshots via the Chrome DevTools Protocol (Node 22 global WebSocket).
// Usage: node shoot.mjs <outDir> <url> [<url>...]
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
import { join } from "node:path";

const [outDir, ...urls] = process.argv.slice(2);
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless=new", "--disable-gpu", "--hide-scrollbars", "--remote-debugging-port=9471",
  `--user-data-dir=${join(process.env.TEMP || outDir, "porch-cdp-profile")}`, "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 160 && !target; i++) {
  await sleep(250);
  try { target = (await (await fetch("http://127.0.0.1:9471/json")).json()).find((t) => t.type === "page"); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const msg = JSON.parse(e.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
});
const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });

await send("Emulation.setDeviceMetricsOverride", { width: Number(process.env.W ?? 390), height: 844, deviceScaleFactor: Number(process.env.DPR ?? 2), mobile: !process.env.W });
for (const url of urls) {
  await send("Page.navigate", { url });
  await sleep(2500);
  if (process.env.CSS) {
    const css = (await import("node:fs")).readFileSync(process.env.CSS, "utf8");
    await send("Runtime.evaluate", { expression: `(()=>{const s=document.createElement('style');s.textContent=${JSON.stringify(css)};document.head.appendChild(s);})()` });
    await sleep(400);
  }
  const { result } = await send("Runtime.evaluate", { expression: "JSON.stringify([document.documentElement.scrollWidth, document.documentElement.scrollHeight])" });
  const [w, h] = JSON.parse(result.result.value);
  const height = Math.min(h, Number(process.env.MAXH ?? 2400));
  const seg = Number(process.env.SEG ?? height);
  const parts = Math.ceil(height / seg);
  for (let i = 0; i < parts; i++) {
    const y = i * seg, hh = Math.min(seg, height - y);
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y, width: Number(process.env.W ?? 390), height: hh, scale: 1 } });
    const base = new URL(url).pathname.replace(/\.html$/, "").split("/").filter(Boolean).join("_") || "root";
    const name = parts > 1 ? `${base}-${i + 1}of${parts}.png` : `${base}.png`;
    writeFileSync(join(outDir, name), Buffer.from(shot.result.data, "base64"));
    console.log(`${name}: layout ${w}px wide, captured ${process.env.W ?? 390}x${hh} from y=${y}`);
  }
}
ws.close();
chrome.kill();
