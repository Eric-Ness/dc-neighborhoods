// Typed access to the JSON written by ingest/run.py.

export interface Permit {
  id: string;
  issued: string | null;
  group: string;
  type: string | null;
  subtype: string | null;
  address: string;
  work: string;
  zoning: string | null;
  lat: number | null;
  lon: number | null;
  smd: string | null;
}

export interface Neighborhood {
  slug: string;
  name: string;
  generated_at: string;
  boundary: { source: string; rings: number[][][] };
  windows: { permits_days: number; requests_days: number };
  permits: Permit[];
  requests: {
    total: number;
    previous_total: number;
    open: number;
    by_type: { type: string; count: number; previous: number }[];
    recent: { type: string; agency: string; added: string; status: string; block: string | null }[];
  };
  crime: {
    total: number;
    previous_total: number;
    by_offense: { offense: string; count: number; previous: number }[];
    note: string;
  };
  smds: { smd: string; anc: string; commissioner: string | null; url: string | null }[];
  sources: Record<string, string>;
}

const files = import.meta.glob<{ default: Neighborhood }>("../data/*.json", { eager: true });

export const neighborhoods: Neighborhood[] = Object.entries(files)
  .filter(([path]) => !path.endsWith("/index.json"))
  .map(([, mod]) => mod.default)
  .sort((a, b) => a.name.localeCompare(b.name));

export function pctChange(now: number, before: number): number | null {
  // Percentages on small counts read as alarming swings; below this, show raw numbers only.
  if (before < 100 && now < 100) return null;
  return Math.round(((now - before) / before) * 100);
}

export function fmtDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "America/New_York" });
}

export function fmtDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "America/New_York",
    timeZoneName: "short",
  });
}

export function titleCase(s: string): string {
  return s.toLowerCase().replace(/\b([a-z])/g, (m) => m.toUpperCase()).replace(/\b(Nw|Ne|Sw|Se)\b/g, (m) => m.toUpperCase());
}

/** Headline facts a resident would actually notice, generated from the numbers. */
export function headlines(n: Neighborhood): string[] {
  const out: string[] = [];
  // Rank by absolute change so a jump from 84 to 117 outranks one from 13 to 20.
  const movers = n.requests.by_type
    .filter((t) => Math.max(t.count, t.previous) >= 30 && t.previous >= 10)
    .map((t) => ({ ...t, pct: Math.round(((t.count - t.previous) / t.previous) * 100) }))
    .sort((a, b) => Math.abs(b.count - b.previous) - Math.abs(a.count - a.previous));
  for (const m of movers.slice(0, 2)) {
    if (Math.abs(m.pct) < 20) continue;
    out.push(`${m.type} requests ${m.pct > 0 ? "up" : "down"} ${Math.abs(m.pct)}% vs. the previous 30 days (${m.count} vs. ${m.previous}).`);
  }
  const big = n.permits.filter((p) => ["Demolition", "New construction", "Additions"].includes(p.group));
  if (big.length) out.push(`${big.length} permit${big.length === 1 ? "" : "s"} for demolition, additions or new construction issued in the last ${n.windows.permits_days} days.`);
  return out;
}
