// The drawn street map behind the bus map and the 311 map: the neighborhood's streets (ingest/blocks.py basemap),
// its boundary and major street names, projected into an SVG box. Drawn at build time, so no map tiles.
import type { Neighborhood } from "./data";

type Pt = [number, number];

export function basemap(n: Neighborhood, extra: Pt[] = [], W = 640, PAD = 0.0025) {
  const pts = [...n.boundary.rings.flat(), ...extra];
  const west = Math.min(...pts.map((p) => p[0])) - PAD, east = Math.max(...pts.map((p) => p[0])) + PAD;
  const south = Math.min(...pts.map((p) => p[1])) - PAD, north = Math.max(...pts.map((p) => p[1])) + PAD;
  const cos = Math.cos((((south + north) / 2) * Math.PI) / 180);
  const K = W / ((east - west) * cos), H = Math.round((north - south) * K);
  const x = (lo: number) => +((lo - west) * cos * K).toFixed(1);
  const y = (la: number) => +((north - la) * K).toFixed(1);
  const path = (p: Pt[]) => "M" + p.map(([lo, la]) => `${x(lo)},${y(la)}`).join("L");
  const inBox = (lo: number, la: number) => lo >= west && lo <= east && la >= south && la <= north;
  const segs = (n.blocks?.basemap.streets ?? []).filter((s) => s.p.some(([lo, la]) => inBox(lo, la)));
  const outline = n.boundary.rings.map((r) => path(r) + "Z").join("");

  // The dashed edge skips sides two districts share, so a neighborhood made of several reads as one shape.
  const side = (a: Pt, b: Pt) => [a, b].map((p) => p.map((v) => v.toFixed(5)).join(",")).sort().join("|");
  const sides = new Map<string, number>();
  for (const r of n.boundary.rings) for (let i = 1; i < r.length; i++) { const k = side(r[i - 1], r[i]); sides.set(k, (sides.get(k) ?? 0) + 1); }
  const edge = n.boundary.rings.map((r) => {
    let d = "", open = false;
    for (let i = 1; i < r.length; i++) {
      if (sides.get(side(r[i - 1], r[i]))! > 1) { open = false; continue; }
      d += open ? `L${x(r[i][0])},${y(r[i][1])}` : `M${x(r[i - 1][0])},${y(r[i - 1][1])}L${x(r[i][0])},${y(r[i][1])}`;
      open = true;
    }
    return d;
  }).join("");

  // One label per major street, on the segment nearest the middle of its run in view, turned to follow it.
  const nice = (s: string) => s.replace(/ (NW|NE|SW|SE)$/, "").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
  const runs = new Map<string, { x: number; y: number; a: number; len: number }[]>();
  for (const s of segs.filter((s) => s.k === "major" && s.p.length > 1)) {
    const [a, b] = [s.p[0], s.p[s.p.length - 1]];
    const dx = x(b[0]) - x(a[0]), dy = y(b[1]) - y(a[1]);
    let ang = (Math.atan2(dy, dx) * 180) / Math.PI;
    if (ang > 90) ang -= 180; else if (ang < -90) ang += 180;
    const k = nice(s.n);
    runs.set(k, [...(runs.get(k) ?? []), { x: (x(a[0]) + x(b[0])) / 2, y: (y(a[1]) + y(b[1])) / 2, a: ang, len: Math.hypot(dx, dy) }]);
  }
  const labels: { name: string; x: number; y: number; a: number }[] = [];
  for (const [k, r] of runs) {
    if (/\b(Bn|Ramp|Exit)$/i.test(k)) continue;
    const long = r.filter((p) => p.len > 45 && p.x > 40 && p.x < W - 40 && p.y > 30 && p.y < H - 30);
    if (!long.length || r.length < 3) continue;
    const cx = r.reduce((t, p) => t + p.x, 0) / r.length, cy = r.reduce((t, p) => t + p.y, 0) / r.length;
    const best = long.sort((p, q) => Math.hypot(p.x - cx, p.y - cy) - Math.hypot(q.x - cx, q.y - cy))[0];
    labels.push({ name: k, x: best.x, y: best.y, a: best.a });
  }

  return { W, H, K, cos, west, south, east, north, x, y, path, inBox, segs, outline, edge, labels };
}
