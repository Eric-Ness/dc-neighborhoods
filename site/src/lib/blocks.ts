// Hundred blocks: matching the neighborhood's records to DDOT's roadway blocks (ingest/blocks.py), placing places
// named in the data, and finding which neighborhoods border which. Same street-name rule as ingest/blocks.py.
import type { Block, Neighborhood } from "./data";
import { neighborhoods } from "./data";

const SUFFIX: Record<string, string> = {
  STREET: "ST", AVENUE: "AVE", PLACE: "PL", ROAD: "RD", TERRACE: "TER", CIRCLE: "CIR", DRIVE: "DR",
  BOULEVARD: "BLVD", COURT: "CT", LANE: "LN", PARKWAY: "PKWY", AV: "AVE",
};

/** "Upshur Street NW" and "UPSHUR ST NW" -> "UPSHUR ST NW". */
export function streetKey(name: string): string {
  // Bus-stop names write "9 St NW"; DDOT writes "9TH ST NW".
  const ord = (d: string) => d + (/1\d$/.test(d) ? "TH" : ({ "1": "ST", "2": "ND", "3": "RD" } as Record<string, string>)[d.slice(-1)] ?? "TH");
  return name.toUpperCase().replace(/[^A-Z0-9 ]/g, " ").split(/\s+/).filter(Boolean)
    .map((w) => SUFFIX[w] ?? w).map((w) => (/^\d+$/.test(w) ? ord(w) : w)).join(" ");
}

const slugOf = (hundred: number, street: string) => `${hundred}-${streetKey(street).toLowerCase().replace(/ /g, "-")}`;

/** Block key for a street address, a "1200 block of ..." label, or "4131-4101 Block 9th St NW". */
export function blockKey(text: string | null | undefined): string | null {
  if (!text) return null;
  const t = text.replace(/\s+\d{5}(-\d{4})?\s*$/, "").trim(); // drop a ZIP
  let m = t.match(/^(\d+)\s*-\s*(\d+)\s+block\s+(?:of\s+)?(.+)$/i);
  if (m) return slugOf(Math.floor(Math.min(+m[1], +m[2]) / 100) * 100, m[3]);
  m = t.match(/^(unit|\d+)\s+block\s+of\s+(.+)$/i);
  if (m) return slugOf(m[1].toLowerCase() === "unit" ? 0 : Math.floor(+m[1] / 100) * 100, m[2]);
  m = t.match(/^(\d+)[A-Z]?\s+(.+)$/i);
  if (m) return slugOf(Math.floor(+m[1] / 100) * 100, m[2]);
  return null;
}

export function blockIndex(n: Neighborhood): Map<string, Block> {
  return new Map((n.blocks?.items ?? []).map((b) => [b.key, b]));
}

/** Where a place named in the data sits: a block's midpoint, or the corner where two named streets meet. */
export function placePoint(n: Neighborhood, place: string | null | undefined): { lat: number; lon: number; key?: string } | null {
  if (!place || !n.blocks) return null;
  const k = blockKey(place);
  const b = k ? blockIndex(n).get(k) : undefined;
  if (b) return { lat: b.lat, lon: b.lon, key: b.key };
  const m = place.match(/^(.+?)\s*(?:&|and|at)\s*(.+)$/i);
  if (!m) return null;
  let a = streetKey(m[1]), c = streetKey(m[2]);
  const quad = (s: string) => s.match(/\b(NW|NE|SW|SE)$/)?.[1];
  const q = quad(a) ?? quad(c);
  if (q) { if (!quad(a)) a += ` ${q}`; if (!quad(c)) c += ` ${q}`; }
  const ends = (name: string) => n.blocks!.basemap.streets.filter((s) => s.n === name).flatMap((s) => [s.p[0], s.p[s.p.length - 1]]);
  const ea = ends(a), ec = ends(c);
  let best: [number, number] | null = null, bd = 0.0003; // ~30 m: the two streets really meet here
  for (const p of ea) for (const r of ec) {
    const d = Math.hypot(p[0] - r[0], p[1] - r[1]);
    if (d < bd) { bd = d; best = p; }
  }
  return best ? { lon: best[0], lat: best[1] } : null;
}

/** Everything the neighborhood's data says about one block, from records that carry an address or block. */
export function blockActivity(n: Neighborhood, key: string) {
  const permits = n.permits.filter((p) => blockKey(p.address) === key);
  const requests = n.requests.recent.filter((r) => blockKey(r.block) === key);
  const sales = (n.homes?.recent_sales ?? []).filter((s) => blockKey(s.address) === key);
  const curb = (n.streets?.curb.upcoming ?? []).filter((c) => blockKey(c.block) === key);
  const trees = (n.streets?.trees.biggest ?? []).filter((t) => blockKey(t.block) === key);
  return { permits, requests, sales, curb, trees };
}

const km = (a: number[], b: number[]) => {
  const k = Math.cos(((a[1] + b[1]) / 2) * Math.PI / 180);
  return Math.hypot((a[0] - b[0]) * 111.32 * k, (a[1] - b[1]) * 110.57);
};

/** Neighborhoods whose boundaries come within ~400 m of this one (or overlap it), nearest first. */
export function neighborsOf(n: Neighborhood): Neighborhood[] {
  const pts = (x: Neighborhood) => x.boundary.rings.flat().filter((_, i) => i % 3 === 0);
  const mine = pts(n);
  return neighborhoods
    .filter((o) => o.slug !== n.slug)
    .map((o) => {
      let d = Infinity;
      for (const p of pts(o)) for (const q of mine) { const v = km(p, q); if (v < d) d = v; }
      return { o, d };
    })
    .filter((x) => x.d < 0.4)
    .sort((a, b) => a.d - b.d)
    .map((x) => x.o);
}
