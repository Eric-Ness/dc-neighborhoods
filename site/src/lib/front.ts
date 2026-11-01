// Everything the Atlas front page derives from a neighborhood's JSON: the ordered news, the lists the map
// letters and numbers, the 311 condition sentence, and the neighborhood-wide lookups. Pure functions of the data.
import type { Neighborhood, NewsItem } from "./data";
import { neighborhoods } from "./data";
import { blockKey, blockIndex, neighborsOf, placePoint } from "./blocks";
import { addr, cleanWork, fmt } from "./c5";
import type { Layers } from "./atlas";

// Crime stories are listed like any other headline, but never as the lead (decided 2026-11-01).
const CRIME = /\b(shoot\w*|shot|homicide|murder\w*|stabb\w*|robber\w*|carjack\w*|gunfire|gunman|killed|slain|assault\w*|burglar\w*)\b/i;
export const isCrime = (title: string) => CRIME.test(title);

/** The neighborhood's own headlines, with the newest non-crime story moved to the top. */
export function ownNews(n: Neighborhood, limit: number): NewsItem[] {
  const items = [...(n.news?.items ?? [])];
  const i = items.findIndex((it) => !isCrime(it.title));
  if (i > 0) items.unshift(...items.splice(i, 1));
  return items.slice(0, limit);
}

const DAY = 86400_000;

/** Recent headlines from bordering neighborhoods that this one's feeds didn't already carry. */
export function nearbyNews(n: Neighborhood, limit: number, days = 21) {
  const seen = new Set((n.news?.items ?? []).map((i) => i.url));
  const cutoff = Date.parse(n.generated_at) - days * DAY;
  const out: (NewsItem & { hood: Neighborhood })[] = [];
  for (const o of neighborsOf(n)) {
    for (const it of o.news?.items ?? []) {
      if (seen.has(it.url) || Date.parse(it.published) < cutoff) continue;
      seen.add(it.url);
      out.push({ ...it, hood: o });
    }
  }
  return out.sort((a, b) => b.published.localeCompare(a.published)).slice(0, limit);
}

/** The newest headline from each of the other DC sites (not this one, not its neighbors): a reason to visit them. */
export function elsewhereNews(n: Neighborhood, limit: number, days = 10) {
  const skip = new Set([n.slug, ...neighborsOf(n).map((o) => o.slug)]);
  const cutoff = Date.parse(n.generated_at) - days * DAY;
  const seen = new Set((n.news?.items ?? []).map((i) => i.url));
  const out: (NewsItem & { hood: Neighborhood })[] = [];
  for (const o of neighborhoods) {
    if (skip.has(o.slug)) continue;
    const it = (o.news?.items ?? []).find((x) => !seen.has(x.url) && !isCrime(x.title) && Date.parse(x.published) >= cutoff);
    if (it) { seen.add(it.url); out.push({ ...it, hood: o }); }
  }
  return out.sort((a, b) => b.published.localeCompare(a.published)).slice(0, limit);
}

/** Upcoming events in the next `days`, with a letter per distinct mapped place. */
export function eventPlaces(n: Neighborhood, days: number) {
  const ev = n.events;
  if (!ev) return { soon: [], later: [], places: new Map<string, { id: string; letter: string; lat: number; lon: number }>() };
  const end = new Date(Date.parse(ev.today + "T12:00:00Z") + days * DAY).toISOString().slice(0, 10);
  const all = [...ev.events].sort((a, b) => (a.date + (a.time ?? "")).localeCompare(b.date + (b.time ?? "")));
  const soon = all.filter((e) => e.date >= ev.today && e.date <= end);
  const later = all.filter((e) => e.date > end);
  const places = new Map<string, { id: string; letter: string; lat: number; lon: number }>();
  for (const e of soon) {
    if (!e.place || places.has(e.place) || places.size >= 12) continue;
    const pt = placePoint(n, e.place);
    if (pt) places.set(e.place, { id: `e${places.size + 1}`, letter: "ABCDEFGHJKLM"[places.size], lat: pt.lat, lon: pt.lon });
  }
  return { soon, later, places };
}

/** Curb permits starting soon, grouped by type, street and dates (a mover's permit often spans two blocks). */
export function curbGroups(n: Neighborhood) {
  const groups = new Map<string, { type: string; street: string; blocks: number[]; start: string; end: string; hours: string | null; ft: number; keys: string[] }>();
  for (const c of n.streets?.curb.upcoming ?? []) {
    const m = c.block.match(/^(Unit|\d+) block of (.+)$/i);
    const street = m ? m[2] : c.block;
    const k = [c.type, street, c.start, c.end, c.hours ?? ""].join("|");
    const g = groups.get(k) ?? { type: c.type, street, blocks: [], start: c.start, end: c.end, hours: c.hours, ft: 0, keys: [] };
    if (m) g.blocks.push(m[1].toLowerCase() === "unit" ? 0 : +m[1]);
    g.ft += c.ft ?? 0;
    const bk = blockKey(c.block);
    if (bk) g.keys.push(bk);
    groups.set(k, g);
  }
  const idx = blockIndex(n);
  return [...groups.values()].map((g, i) => {
    const bs = [...new Set(g.blocks)].sort((a, b) => a - b);
    const where = bs.length > 1 ? `${bs[0]}–${bs[bs.length - 1]} blocks of ${g.street}` : bs.length ? `${bs[0] || "Unit"} block of ${g.street}` : g.street;
    const first = g.keys.map((k) => idx.get(k)).find(Boolean);
    return { ...g, id: `c${i + 1}`, where: where.replace(/ (NW|NE|SW|SE)$/, ""), at: first ? { lat: first.lat, lon: first.lon } : undefined };
  });
}

const BIG_GROUPS = ["Additions", "Demolition", "New construction"];

/** Additions, demolitions and new buildings, one per address, newest first, numbered for the map. */
export function bigProjects(n: Neighborhood) {
  const byAddr = new Map<string, typeof n.permits>();
  for (const p of n.permits) byAddr.set(p.address, [...(byAddr.get(p.address) ?? []), p]);
  const seen = new Set<string>();
  const out = [];
  for (const p of [...n.permits].filter((p) => BIG_GROUPS.includes(p.group)).sort((a, b) => (b.issued ?? "").localeCompare(a.issued ?? ""))) {
    if (seen.has(p.address) || p.lat == null || p.lon == null) continue;
    seen.add(p.address);
    out.push({ id: `p${out.length + 1}`, num: out.length + 1, addr: addr(p.address), rawAddr: p.address, group: p.group, issued: p.issued,
      work: cleanWork(p.work, 150), lat: p.lat, lon: p.lon, others: (byAddr.get(p.address)?.length ?? 1) - 1, permit: p.id });
  }
  return out;
}

export function mapLayers(n: Neighborhood, projects: ReturnType<typeof bigProjects>, ev: ReturnType<typeof eventPlaces>, curb: ReturnType<typeof curbGroups>): Layers {
  const big = new Set(projects.map((p) => `${p.lat},${p.lon}`));
  const minor = new Map<string, { lat: number; lon: number; n: number }>();
  for (const p of n.permits) {
    if (p.lat == null || p.lon == null || big.has(`${p.lat},${p.lon}`)) continue;
    const k = `${p.lat},${p.lon}`;
    minor.set(k, { lat: p.lat, lon: p.lon, n: (minor.get(k)?.n ?? 0) + 1 });
  }
  const reqs = new Map<string, { lat: number; lon: number; n: number }>();
  for (const r of n.requests.recent) {
    if (r.lat == null || r.lon == null) continue;
    const k = `${r.lat},${r.lon}`;
    reqs.set(k, { lat: r.lat, lon: r.lon, n: (reqs.get(k)?.n ?? 0) + 1 });
  }
  const fb = n.history?.buildings.featured_block;
  const fbKey = fb ? blockKey(fb.block) : null;
  return {
    projects: projects.map((p) => ({ id: p.id, lat: p.lat, lon: p.lon, label: String(p.num), title: `${p.num}. ${p.addr}: ${p.group}`, addr: p.rawAddr })),
    minor: [...minor.values()],
    events: [...ev.places.entries()].map(([place, v]) => ({ id: v.id, lat: v.lat, lon: v.lon, label: v.letter, title: `${v.letter}. ${place}` })),
    curb: curb.map((c) => ({ id: c.id, keys: c.keys, title: `${c.type}: ${c.where}`, at: c.at })),
    then: fb && fbKey && blockIndex(n).has(fbKey) ? { key: fbKey, title: `${fb.block}: ${fb.buildings} buildings in ${fb.year}`, year: fb.year } : undefined,
    requests: [...reqs.values()],
    stations: (n.transit?.stations ?? []).map((s) => ({ name: s.name, lat: s.lat, lon: s.lon })),
    docks: (n.transit?.bike_docks ?? []).map((d) => ({ name: d.name, lat: d.lat, lon: d.lon })),
  };
}

// ---- 311 condition: one sentence, and a tally of request types rising, easing or steady
const LABELS: Record<string, string> = {
  "DC Health Rodent & Vector Control": "rodent complaints", "DOEE - LIHEAP": "heating-assistance (LIHEAP) requests",
  "Bulk Collection": "bulk trash pickups", "Scheduled Yard Waste": "yard-waste pickups", "Illegal Dumping": "illegal dumping reports",
  "Trash Collection - Missed": "missed trash pickups", "Recycling Collection - Missed": "missed recycling pickups",
  "Container Removal": "trash-can removals", "Parking Enforcement": "parking enforcement calls",
  "Sanitation Enforcement": "sanitation enforcement calls", "Dead Animal Collection": "dead animal pickups",
  "Residential Parking Permit Violation": "residential parking violations", "Abandoned Vehicle - On Public Property": "abandoned vehicle reports",
  "Streetlight Repair Investigation": "streetlight repairs", "Pothole": "pothole reports", "Tree Inspection": "tree inspections",
};
export const reqLabel = (t: string) => LABELS[t] ?? t.toLowerCase();
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
export const reqTitle = (t: string) => cap(reqLabel(t));
/** Percentages only when both counts are 100 or more (privacy and noise rule). */
export const pctOk = (a: number, b: number) => a >= 100 && b >= 100;
export const pct = (a: number, b: number) => `${a >= b ? "+" : "−"}${Math.abs(Math.round(((a - b) / b) * 100))}%`;

export function condition(n: Neighborhood) {
  const days = n.windows.requests_days;
  const bt = n.requests.by_type;
  const tot = n.requests.total, ptot = n.requests.previous_total;
  const phrase = (r: { type: string; count: number; previous: number }) => {
    if (r.previous === 0) return `${reqLabel(r.type)} went from none to ${fmt(r.count)}`;
    return `${reqLabel(r.type)} ${r.count > r.previous ? "rose" : "fell"} to ${fmt(r.count)} from ${fmt(r.previous)}${pctOk(r.count, r.previous) ? ` (${pct(r.count, r.previous)})` : ""}`;
  };
  let lead = `311 requests in ${n.name} ${tot < ptot ? "fell" : tot > ptot ? "rose" : "held"} to ${fmt(tot)} in the last ${days} days, from ${fmt(ptot)} the ${days} days before${pctOk(tot, ptot) ? ` (${pct(tot, ptot)})` : ""}.`;
  if (bt.length) {
    const deltas = [...bt].sort((a, b) => Math.abs(b.count - b.previous) - Math.abs(a.count - a.previous) || b.count - a.count);
    const rise = bt.reduce((m, r) => (r.count - r.previous > m.count - m.previous ? r : m));
    const fall = bt.reduce((m, r) => (r.count - r.previous < m.count - m.previous ? r : m));
    const first = deltas[0];
    if (first.count !== first.previous) {
      lead += ` The biggest swing: ${phrase(first)}.`;
      const second = first === fall ? rise : fall;
      if (second !== first && second.count !== second.previous) lead += ` ${second === rise ? "Biggest rise" : "Biggest drop"}: ${phrase(second)}.`;
    }
  }
  const tally = { rising: 0, easing: 0, steady: 0 };
  for (const r of bt) {
    if (Math.max(r.count, r.previous) < 10) continue;
    const thr = Math.max(2, 0.1 * r.previous);
    if (r.count - r.previous > thr) tally.rising++;
    else if (r.previous - r.count > thr) tally.easing++;
    else tally.steady++;
  }
  return { lead, tally };
}

// ---- neighborhood-wide lookups from the block records
export function lookups(n: Neighborhood) {
  const items = n.blocks?.items ?? [];
  const count = (vals: (string | null | undefined)[]) => {
    const m = new Map<string, number>();
    for (const v of vals) if (v) m.set(v, (m.get(v) ?? 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  };
  const schoolCounts = (level: "elementary" | "middle" | "high") =>
    count(items.map((b) => b.schools[level])).map(([id, c]) => ({ id, blocks: c, ...(n.blocks!.schools[id] ?? { name: id, address: null, url: null, grades: null }) }));
  const snow = [...new Set(items.filter((b) => b.snow_emergency).map((b) => b.street))].sort();
  return {
    total: items.length,
    trash: count(items.map((b) => b.trash_day)),
    recycling: count(items.map((b) => b.recycling_day)),
    leafZones: count(items.map((b) => b.leaf_zone)).map(([z, c]) => ({ zone: z, blocks: c, status: n.blocks?.leaf_status[z] ?? null,
      done: items.filter((b) => b.leaf_zone === z && b.leaf_done).length })),
    schools: { elementary: schoolCounts("elementary"), middle: schoolCounts("middle"), high: schoolCounts("high") },
    snow,
    rpp: count(items.flatMap((b) => b.parking.map((p) => p.rpp))),
  };
}

/** "Thursday for 180 blocks; Wednesday for 50" */
export const dayList = (rows: [string, number][], total: number) =>
  rows.length === 1 ? `${rows[0][0]}, every block` : rows.map(([d, c], i) => (i === 0 ? `${d} for most blocks (${c} of ${total})` : `${d} for ${c}`)).join("; ");
