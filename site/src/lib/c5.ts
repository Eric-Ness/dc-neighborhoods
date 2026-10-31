// C5 presentation helpers, ported from design/layouts/src/C5_hybrid.py.
// They return small HTML/SVG strings so Astro components can share one look (render with set:html).
import type { Neighborhood, Permit } from "./data";

export const STEADY_BAND = 0.05; // within ±5% of the comparison reads as "steady"

export type State = "rising" | "easing" | "steady";
export const STATE_WORD: Record<State, string> = { rising: "Rising", easing: "Easing", steady: "Steady" };

export const esc = (s: unknown) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export const fmt = (n: number) => Math.round(n).toLocaleString("en-US");
export const money = (n: number | null | undefined) =>
  n == null ? "—" : n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(2)}M` : `$${Math.round(n / 1000)}K`;
export const sign = (d: number) => (d > 0 ? "+" : d < 0 ? "−" : "±");

const KEEP = new Set(["NW", "NE", "SW", "SE", "ADU", "DC"]);
export function titleCase(s: string): string {
  return (s ?? "")
    .split(/\s+/)
    .map((w) =>
      KEEP.has(w) ? w
      : /^\d+(ST|ND|RD|TH)$/i.test(w) ? w.toLowerCase() // "46TH" -> "46th"
      : /\d/.test(w) ? w
      : w.charAt(0).toUpperCase() + w.slice(1).toLowerCase(),
    )
    .join(" ");
}

export const addr = (s: string) => titleCase((s ?? "").replace(/\s+\d{5}$/, "").trim());

/** All-caps permit text ("SELECTIVE INTERIOR DEMOLITION OF...") to sentence case; mixed-case text is left alone. */
export function sentenceCase(s: string): string {
  const letters = s.replace(/[^A-Za-z]/g, "");
  if (letters.length < 8 || letters.replace(/[^A-Z]/g, "").length / letters.length < 0.8) return s;
  return s
    .toLowerCase()
    .replace(/(^|[.!?]\s+)([a-z])/g, (_, p, c) => p + c.toUpperCase())
    .replace(/\b(nw|ne|sw|se|dc|adu|hvac|mep|ddot|dob|dcra|wasa)\b/g, (w) => w.toUpperCase())
    .replace(/\b([a-z]?\d{6,})\b/g, (w) => w.toUpperCase()); // permit numbers like b2506312
}

export function cleanWork(s: string, max = 150): string {
  let t = sentenceCase((s ?? "").replace(/\s+/g, " ").trim());
  t = t.replace(/(?<=[a-z]\.)(?=[A-Z])/g, " ").replace(/(?<=[A-Z]{3})(?=[A-Z][a-z])/g, " ");
  return t.length > max ? t.slice(0, max).replace(/\s+\S*$/, "") + "…" : t;
}

export interface Reading { d: number; state: State; pct: number | null; txt: string }

/** State + signed delta. Percentages only when both counts are 100 or more. */
export function reading(cur: number, prev: number): Reading {
  const d = cur - prev;
  const ratio = prev ? d / prev : 0;
  const state: State = Math.abs(ratio) < STEADY_BAND ? "steady" : d > 0 ? "rising" : "easing";
  const pct = cur >= 100 && prev >= 100 ? Math.round(ratio * 100) : null;
  const txt = `${sign(d)}${fmt(Math.abs(d))}` + (pct !== null ? ` (${sign(d)}${Math.abs(pct)}%)` : "");
  return { d, state, pct, txt };
}

/** Shape-coded state glyph (▲ ▼ =), drawn as SVG so it aligns and inherits color. */
export function icon(state: State, cls = "ic"): string {
  const shapes: Record<State, string> = {
    rising: '<path d="M6 1.5 L11 10.5 H1 Z"/>',
    easing: '<path d="M6 10.5 L11 1.5 H1 Z"/>',
    // Two bars ("equals"), so it never reads as a minus sign next to a negative number.
    steady: '<rect x="1" y="2.5" width="10" height="2.2" rx="1.1"/><rect x="1" y="7.3" width="10" height="2.2" rx="1.1"/>',
  };
  return `<svg class="${cls}" viewBox="0 0 12 12" aria-hidden="true">${shapes[state]}</svg>`;
}

export const MIX_ICON =
  '<svg class="ic" viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/></svg>';

export const stateTag = (s: State) => `<span class="tag s-${s}">${icon(s)}${STATE_WORD[s]}</span>`;

export function bar(cur: number, max: number, cls: string): string {
  const w = Math.max((100 * cur) / (max || 1), 0.6).toFixed(1);
  return `<svg class="hb" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><rect class="trk" width="100" height="8" rx="1"/><rect class="${cls}" width="${w}" height="8" rx="1"/></svg>`;
}

/** Paired bars: the latest period over the earlier one, values right-aligned. */
export function pair(curLbl: string, cur: number, curTxt: string, prevLbl: string, prev: number, prevTxt: string, curCls: string): string {
  const m = Math.max(cur, prev) || 1;
  return (
    `<div class="cr-r"><span class="k">${curLbl}</span>${bar(cur, m, curCls)}<span class="v num">${curTxt}</span></div>` +
    `<div class="cr-r"><span class="k">${prevLbl}</span>${bar(prev, m, "prev")}<span class="v num">${prevTxt}</span></div>`
  );
}

// ---------- permit categories ----------
export interface Cat { key: string; group: string; short: string; kind: string }
export const CATS: Cat[] = [
  { key: "add", group: "Additions", short: "Additions", kind: "num" },
  { key: "demo", group: "Demolition", short: "Demolition", kind: "numsq" },
  { key: "newc", group: "New construction", short: "New construction", kind: "num" },
  { key: "ren", group: "Renovation & repair", short: "Renovation & repair", kind: "dot" },
  { key: "mep", group: "Electrical, plumbing & mechanical", short: "Electrical / plumbing", kind: "ring" },
  { key: "home", group: "Home businesses", short: "Home businesses", kind: "sq" },
  { key: "minor", group: "Minor work", short: "Minor work", kind: "small" },
  { key: "other", group: "Other", short: "Other", kind: "small" },
];
export const GKEY: Record<string, string> = Object.fromEntries(CATS.map((c) => [c.group, c.key]));
export const BIG = ["Demolition", "New construction", "Additions"];

export function glyph(kind: string, key = ""): string {
  const inner: Record<string, string> = {
    num: `<circle cx="7" cy="7" r="5.5" class="gl-${key || "add"}"/>`,
    numsq: '<rect x="2" y="2" width="10" height="10" rx="1" class="gl-demo"/>',
    dot: '<circle cx="7" cy="7" r="3.2" class="gl-ink"/>',
    ring: '<circle cx="7" cy="7" r="3" class="gl-ring"/>',
    sq: '<rect x="4" y="4" width="6" height="6" class="gl-ink2"/>',
    small: '<circle cx="7" cy="7" r="2" class="gl-mut"/>',
  };
  return `<svg class="gl" viewBox="0 0 14 14" width="14" height="14" aria-hidden="true">${inner[kind] ?? inner.small}</svg>`;
}

export function groupCounts(permits: Permit[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const p of permits) out[p.group] = (out[p.group] ?? 0) + 1;
  return out;
}

// ---------- time ----------
const ET = "America/New_York";
export function asOf(iso: string): string {
  const d = new Date(iso);
  const date = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: ET });
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", timeZone: ET });
  return `${date}, ${time} ET`;
}
export const asOfDay = (iso: string) =>
  new Date(iso).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", timeZone: ET });
export const shortDate = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: ET }) : "";

// ---------- 311 naming ----------
const SHORT: Record<string, string> = { "DC Health Rodent & Vector Control": "Rodent & vector control" };
const LEAD_NAME: Record<string, string> = { "DC Health Rodent & Vector Control": "Rodent complaints" };
export const shortType = (t: string) => SHORT[t] ?? t;
export const leadName = (t: string) => LEAD_NAME[t] ?? `${shortType(t)} requests`;

// ---------- derived neighborhood view model ----------
export interface Mover { type: string; count: number; previous: number; r: Reading }
export interface Project extends Permit { n: number; key: string; isNew: boolean }

export function model(n: Neighborhood) {
  const req = n.requests;
  const movers: Mover[] = req.by_type
    .filter((t) => Math.max(t.count, t.previous) >= 30 && t.previous >= 10)
    .map((t) => ({ ...t, r: reading(t.count, t.previous) }))
    .sort((a, b) => Math.abs(b.r.d) - Math.abs(a.r.d))
    .slice(0, 3);
  const rises = movers.filter((m) => m.r.d > 0).sort((a, b) => b.r.d - a.r.d);
  const lead = rises[0] ?? movers[0];
  const others = movers.filter((m) => m !== lead);
  const reqR = reading(req.total, req.previous_total);
  const crimeR = reading(n.crime.total, n.crime.previous_total);

  let leadSentence = `${n.name} residents filed ${fmt(req.total)} 311 requests in the past 30 days.`;
  if (lead) {
    const verb = lead.r.d > 0 ? "rose" : "fell";
    leadSentence = `${leadName(lead.type)} ${verb} to ${fmt(lead.count)} in the past 30 days, ${lead.r.d > 0 ? "up" : "down"} from ${fmt(lead.previous)}`;
    const totalDir = reqR.d < 0 ? "fell" : "rose";
    leadSentence +=
      (lead.r.d > 0) !== (reqR.d > 0)
        ? `, even as total 311 requests in ${n.name} ${totalDir} from ${fmt(req.previous_total)} to ${fmt(req.total)}.`
        : `, while total 311 requests in ${n.name} ${totalDir} from ${fmt(req.previous_total)} to ${fmt(req.total)}.`;
  }

  const gen = Date.parse(n.generated_at);
  const big = n.permits
    .filter((p) => BIG.includes(p.group))
    .sort((a, b) => (b.issued ?? "").localeCompare(a.issued ?? ""));
  const projects: Project[] = big.map((p, i) => ({
    ...p,
    n: i + 1,
    key: GKEY[p.group] ?? "other",
    isNew: !!p.issued && gen - Date.parse(p.issued) <= 7 * 86400_000,
  }));
  return { lead, others, movers, reqR, crimeR, leadSentence, projects, groups: groupCounts(n.permits) };
}

export const ICON_SEARCH =
  '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M13 13l4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
