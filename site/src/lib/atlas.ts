// The Atlas map plate: an SVG drawn at build time from DDOT's roadway blocks (n.blocks.basemap) and the
// neighborhood boundary, with lettered/numbered marks that the lists beside it point to by grid square.
// Crime is never mapped. 311 points are hundred-block coordinates as published, off by default.
import type { Neighborhood } from "./data";

export interface Mark { id: string; lat: number; lon: number; label?: string; title: string; addr?: string }
export interface Layers {
  projects: Mark[];                  // numbered squares
  minor: { lat: number; lon: number; n: number }[];
  events: Mark[];                    // lettered circles
  curb: { id: string; keys: string[]; title: string; at?: { lat: number; lon: number } }[];
  then?: { key: string; title: string; year: number };
  requests: { lat: number; lon: number; n: number }[];
  stations: { name: string; lat: number; lon: number }[];
  docks: { name: string; lat: number; lon: number }[];
}

const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
const f1 = (v: number) => v.toFixed(1);

export function projection(n: Neighborhood) {
  const pts = n.boundary.rings.flat();
  const lons = pts.map((p) => p[0]), lats = pts.map((p) => p[1]);
  const PAD = 0.0009;
  const lon0 = Math.min(...lons) - PAD, lon1 = Math.max(...lons) + PAD;
  const lat0 = Math.min(...lats) - PAD, lat1 = Math.max(...lats) + PAD;
  const cos = Math.cos(((lat0 + lat1) / 2) * Math.PI / 180);
  const MW = 600;
  const K = MW / ((lon1 - lon0) * cos);
  const MH = (lat1 - lat0) * K;
  const COLS = 6;
  const ROWS = Math.max(3, Math.min(9, Math.round((COLS * MH) / MW)));
  const P = (lat: number, lon: number): [number, number] => [(lon - lon0) * cos * K, (lat1 - lat) * K];
  const inPlate = (x: number, y: number, m = 6) => x > m && x < MW - m && y > m && y < MH - m;
  const ref = (lat: number, lon: number) => {
    const [x, y] = P(lat, lon);
    if (!inPlate(x, y, 0)) return null;
    return "ABCDEFGHI"[Math.min(COLS - 1, Math.floor((x / MW) * COLS))] + String(Math.min(ROWS, Math.floor((y / MH) * ROWS) + 1));
  };
  return { P, MW, MH, K, COLS, ROWS, inPlate, ref };
}

/** "GEORGIA AVE NW" -> "Georgia Ave"; "9TH ST NW" -> "9th St". */
export function streetLabel(s: string): string {
  return s.replace(/\s+(NW|NE|SW|SE)$/, "").split(" ")
    .map((w) => (/^\d+(ST|ND|RD|TH)$/.test(w) ? w.toLowerCase() : w.charAt(0) + w.slice(1).toLowerCase())).join(" ");
}

function pointInRings(x: number, y: number, rings: [number, number][][]): boolean {
  let inside = false;
  for (const r of rings) for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [xi, yi] = r[i], [xj, yj] = r[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

export function plate(n: Neighborhood, L: Layers): string {
  const pr = projection(n);
  const { P, MW, MH, COLS, ROWS, inPlate } = pr;
  const ML = 26, MT = 26, MR = 14, MB = 52;
  const VW = ML + MW + MR, VH = MT + MH + MB;
  const rings = n.boundary.rings.map((r) => r.map(([lon, lat]) => P(lat, lon)));
  const bd = rings.map((r) => "M" + r.map(([x, y]) => `${f1(x)},${f1(y)}`).join(" L") + " Z").join(" ");
  // A boundary made of several ANC districts shares edges between them; the line is drawn only along edges that
  // belong to one ring, so the outline is the outer edge of the whole neighborhood.
  const ekey = (a: [number, number], b: [number, number]) => {
    const p = `${f1(a[0])},${f1(a[1])}`, q = `${f1(b[0])},${f1(b[1])}`;
    return p < q ? `${p}|${q}` : `${q}|${p}`;
  };
  const uses = new Map<string, number>();
  for (const r of rings) for (let i = 0; i < r.length; i++) {
    const k = ekey(r[i], r[(i + 1) % r.length]);
    uses.set(k, (uses.get(k) ?? 0) + 1);
  }
  const outline = rings.map((r) => {
    let d = "", pen = false;
    for (let i = 0; i < r.length; i++) {
      const a = r[i], b = r[(i + 1) % r.length];
      if (uses.get(ekey(a, b))! > 1) { pen = false; continue; }
      if (!pen) { d += `M${f1(a[0])},${f1(a[1])}`; pen = true; }
      d += ` L${f1(b[0])},${f1(b[1])}`;
    }
    return d;
  }).join(" ");
  const streets = n.blocks?.basemap.streets ?? [];
  const o: string[] = [];
  const desc = `The ${n.name} boundary with its streets, ${L.minor.reduce((a, m) => a + m.n, 0) + L.projects.length} building permit locations `
    + `(${L.projects.length} bigger projects numbered), ${L.events.length} event places lettered, curb space reserved this week`
    + `${L.stations.length ? ", Metro stations and bikeshare docks" : ""}. Crime is not mapped.`;
  o.push(`<svg viewBox="0 0 ${VW.toFixed(0)} ${VH.toFixed(0)}" role="img" aria-labelledby="plate-t plate-d" xmlns="http://www.w3.org/2000/svg">`);
  o.push(`<title id="plate-t">Map of ${esc(n.name)}</title><desc id="plate-d">${esc(desc)}</desc>`);
  o.push(`<defs><clipPath id="clip-m"><rect x="0" y="0" width="${f1(MW)}" height="${f1(MH)}"/></clipPath>`
    + `<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" class="hatch"/></pattern></defs>`);
  o.push(`<g transform="translate(${ML},${MT})"><g clip-path="url(#clip-m)">`);
  o.push(`<rect class="outside" x="0" y="0" width="${f1(MW)}" height="${f1(MH)}"/><path class="land" d="${bd}"/>`);

  // streets: minor first, majors on top; each segment of a block inside the boundary carries data-b
  const seg = (s: (typeof streets)[number]) => "M" + s.p.map(([lon, lat]) => P(lat, lon).map(f1).join(",")).join(" L");
  for (const kind of ["minor", "major"] as const) {
    o.push(`<g class="${kind === "major" ? "ave" : "st"}">`);
    for (const s of streets) if (s.k === kind) o.push(`<path d="${seg(s)}"${s.b ? ` data-b="${s.b}"` : ""}/>`);
    o.push(`</g>`);
  }
  // hatch the ground outside the boundary (even-odd: plate rectangle minus the boundary)
  o.push(`<path fill="url(#hatch)" fill-rule="evenodd" d="M0,0 H${f1(MW)} V${f1(MH)} H0 Z ${bd}"/>`);
  o.push(`<path class="ribbon" d="${outline}"/><path class="bline" d="${outline}"/>`);
  o.push(`<g class="grid">`);
  for (let c = 1; c < COLS; c++) o.push(`<line x1="${f1((MW / COLS) * c)}" y1="0" x2="${f1((MW / COLS) * c)}" y2="${f1(MH)}"/>`);
  for (let r = 1; r < ROWS; r++) o.push(`<line x1="0" y1="${f1((MH / ROWS) * r)}" x2="${f1(MW)}" y2="${f1((MH / ROWS) * r)}"/>`);
  o.push(`</g>`);

  // street names: the longest drawn piece of each street inside the boundary, majors first, no collisions
  const boxes: { x: number; y: number; w: number; h: number }[] = [];
  const hit = (b: { x: number; y: number; w: number; h: number }) => boxes.some((q) => Math.abs(q.x - b.x) * 2 < q.w + b.w && Math.abs(q.y - b.y) * 2 < q.h + b.h);
  // DDOT draws one segment per block, too short for a name; so measure each street's whole length inside the
  // boundary and hang the label on the piece nearest that street's middle.
  type Piece = { a: [number, number]; b: [number, number]; m: [number, number]; len: number };
  const pieces = new Map<string, { major: boolean; ps: Piece[] }>();
  for (const s of streets) {
    const pts = s.p.map(([lon, lat]) => P(lat, lon));
    for (let i = 0; i + 1 < pts.length; i++) {
      const [a, b] = [pts[i], pts[i + 1]];
      const m: [number, number] = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      if (!inPlate(m[0], m[1], 30) || !pointInRings(m[0], m[1], rings)) continue;
      const e = pieces.get(s.n) ?? { major: s.k === "major", ps: [] };
      e.ps.push({ a, b, m, len: Math.hypot(b[0] - a[0], b[1] - a[1]) });
      pieces.set(s.n, e);
    }
  }
  const byName = new Map<string, { len: number; a: [number, number]; b: [number, number]; major: boolean; alts: Piece[] }>();
  for (const [name, e] of pieces) {
    if (/^INTERSTATE|\bI-?\d|\bRAMP\b|\bEXIT\b/.test(name)) continue; // interstates and ramps read as clutter on a neighborhood plate
    const total = e.ps.reduce((t, p) => t + p.len, 0);
    const cx = e.ps.reduce((t, p) => t + p.m[0] * p.len, 0) / total, cy = e.ps.reduce((t, p) => t + p.m[1] * p.len, 0) / total;
    // candidate anchors: longest pieces near the middle first, so a collision can fall back to another spot
    const alts = [...e.ps].filter((p) => p.len > 12).sort((p, q) => Math.hypot(p.m[0] - cx, p.m[1] - cy) / Math.sqrt(p.len) - Math.hypot(q.m[0] - cx, q.m[1] - cy) / Math.sqrt(q.len));
    if (alts.length) byName.set(name, { len: total, a: alts[0].a, b: alts[0].b, major: e.major, alts });
  }
  const labels = [...byName.entries()].sort((x, y) => Number(y[1].major) - Number(x[1].major) || y[1].len - x[1].len);
  o.push(`<g class="labels" aria-hidden="true">`);
  for (const [name, v] of labels) {
    const text = streetLabel(name);
    const w = text.length * 6.4;
    if (v.len < w * 1.2) continue; // too little of this street inside to carry its name
    for (const pc of v.alts.slice(0, 6)) {
      let ang = (Math.atan2(pc.b[1] - pc.a[1], pc.b[0] - pc.a[0]) * 180) / Math.PI;
      if (ang > 90) ang -= 180;
      if (ang <= -90) ang += 180;
      const [cx, cy] = pc.m;
      const rad = (ang * Math.PI) / 180;
      const box = { x: cx, y: cy, w: Math.abs(Math.cos(rad)) * w + Math.abs(Math.sin(rad)) * 14, h: Math.abs(Math.sin(rad)) * w + Math.abs(Math.cos(rad)) * 14 };
      if (hit(box) || !inPlate(cx - box.w / 2, cy, 4) || !inPlate(cx + box.w / 2, cy, 4)) continue;
      boxes.push(box);
      o.push(`<text class="${v.major ? "avl" : "sl"}" transform="translate(${f1(cx)},${f1(cy)}) rotate(${f1(ang)})" text-anchor="middle" dy="4">${esc(text)}</text>`);
      break;
    }
  }
  o.push(`</g>`);

  // --- layers
  o.push(`<g class="layer L-req">`);
  for (const r of L.requests) {
    const [x, y] = P(r.lat, r.lon);
    if (inPlate(x, y)) o.push(`<circle class="req" cx="${f1(x)}" cy="${f1(y)}" r="${f1(3 + 1.6 * Math.sqrt(r.n - 1))}"><title>${r.n} recent 311 request${r.n > 1 ? "s" : ""} on this block</title></circle>`);
  }
  o.push(`</g><g class="layer L-permits">`);
  for (const m of L.minor) {
    const [x, y] = P(m.lat, m.lon);
    if (inPlate(x, y)) o.push(`<circle class="pm" cx="${f1(x)}" cy="${f1(y)}" r="${f1(2.8 + 1.5 * Math.sqrt(m.n - 1))}"><title>${m.n} smaller permit${m.n > 1 ? "s" : ""}</title></circle>`);
  }
  o.push(`</g><g class="layer L-transit">`);
  for (const d of L.docks) {
    const [x, y] = P(d.lat, d.lon);
    if (inPlate(x, y)) o.push(`<circle class="dock" cx="${f1(x)}" cy="${f1(y)}" r="4"><title>Capital Bikeshare: ${esc(d.name)}</title></circle>`);
  }
  for (const s of L.stations) {
    const [x, y] = P(s.lat, s.lon);
    if (inPlate(x, y)) o.push(`<g class="metro" transform="translate(${f1(x)},${f1(y)})"><title>Metro: ${esc(s.name)}</title><rect x="-9" y="-9" width="18" height="18" rx="2"/><text y="4.5" text-anchor="middle">M</text></g>`);
  }
  o.push(`</g><g class="layer L-curb">`);
  const segsOf = (keys: string[]) => streets.filter((s) => s.b && keys.includes(s.b));
  for (const c of L.curb) {
    const ss = segsOf(c.keys);
    for (const s of ss) o.push(`<path class="curb mk" data-mk="${c.id}" d="${seg(s)}"><title>${esc(c.title)}</title></path>`);
    if (!ss.length && c.at) {
      const [x, y] = P(c.at.lat, c.at.lon);
      o.push(`<circle class="curbdot mk" data-mk="${c.id}" cx="${f1(x)}" cy="${f1(y)}" r="4"><title>${esc(c.title)}</title></circle>`);
    }
  }
  o.push(`</g><g class="layer L-then">`);
  if (L.then) {
    const ss = segsOf([L.then.key]);
    for (const s of ss) o.push(`<path class="thenb mk" data-mk="h1" d="${seg(s)}"><title>${esc(L.then.title)}</title></path>`);
    if (ss.length) {
      const p = ss[0].p[Math.floor(ss[0].p.length / 2)];
      const [x, y] = P(p[1], p[0]);
      o.push(`<text class="thenl" x="${f1(x)}" y="${f1(y - 9)}" text-anchor="middle">${L.then.year}</text>`);
    }
  }
  o.push(`</g><g class="layer L-permits">`);
  for (const m of L.projects) {
    const [x, y] = P(m.lat, m.lon);
    o.push(`<g class="proj mk" data-mk="${m.id}" data-lat="${m.lat}" data-lon="${m.lon}" data-addr="${esc(m.addr ?? "")}" transform="translate(${f1(x)},${f1(y)})"><title>${esc(m.title)}</title><rect x="-8.5" y="-8.5" width="17" height="17"/><text y="4.2" text-anchor="middle">${esc(m.label ?? "")}</text></g>`);
  }
  o.push(`</g><g class="layer L-events">`);
  for (const m of L.events) {
    const [x, y] = P(m.lat, m.lon);
    o.push(`<g class="evt mk" data-mk="${m.id}" transform="translate(${f1(x)},${f1(y)})"><title>${esc(m.title)}</title><circle r="10"/><text y="4.3" text-anchor="middle">${esc(m.label ?? "")}</text></g>`);
  }
  o.push(`</g></g></g>`);

  // frame, grid letters, scale, north
  o.push(`<rect class="neat" x="${ML}" y="${MT}" width="${f1(MW)}" height="${f1(MH)}"/>`);
  o.push(`<rect class="neat2" x="${ML - 5}" y="${MT - 5}" width="${f1(MW + 10)}" height="${f1(MH + 10)}"/>`);
  for (let c = 0; c < COLS; c++) o.push(`<text class="gl" x="${f1(ML + (MW / COLS) * (c + 0.5))}" y="${MT - 11}" text-anchor="middle">${"ABCDEFGHI"[c]}</text>`);
  for (let r = 0; r < ROWS; r++) o.push(`<text class="gl" x="${ML - 14}" y="${f1(MT + (MH / ROWS) * (r + 0.5) + 4)}" text-anchor="middle">${r + 1}</text>`);
  const mPerUnit = 111320 / pr.K;
  const barM = MW * mPerUnit > 2400 ? 400 : 200;
  const bl = barM / mPerUnit, sx = ML, sy = MT + MH + 30;
  o.push(`<g class="scale"><line x1="${sx}" y1="${sy}" x2="${f1(sx + bl)}" y2="${sy}"/><line x1="${sx}" y1="${sy - 4}" x2="${sx}" y2="${sy + 4}"/>`
    + `<line x1="${f1(sx + bl)}" y1="${sy - 4}" x2="${f1(sx + bl)}" y2="${sy + 4}"/><text x="${f1(sx + bl + 8)}" y="${sy + 4}">${barM} m</text></g>`);
  o.push(`<g class="north" transform="translate(${f1(ML + MW - 8)},${sy - 2})"><path d="M0,-14 L5,4 L0,0 L-5,4 Z"/><text x="12" y="3">N</text></g>`);
  o.push(`</svg>`);
  return o.join("");
}
