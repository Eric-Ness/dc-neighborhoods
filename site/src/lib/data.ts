// Typed access to the JSON written by ingest/run.py (core sections) and its modules
// (ingest/homes.py, ingest/streets.py, ingest/history.py). Module sections are optional
// so a page still builds if one feed fails on a given night.

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

export interface Source { name: string; url: string }

export interface Homes {
  generated_at: string;
  sources: Source[];
  area_note: string;
  house: { median_12mo: number; count_12mo: number; median_prev_12mo: number; count_prev_12mo: number };
  condo: { median_12mo: number; count_12mo: number; median_prev_12mo: number; count_prev_12mo: number };
  last_60d: { median: number; count: number; median_ppsf: number | null };
  above_assessment_12mo: { n: number; of: number };
  by_month: { month: string; median: number; count: number }[];
  by_month_basis?: string;
  recent_sales: { address: string; date: string; price: number; kind: string; beds: number | null; sqft: number | null; assessed: number | null }[];
  [k: string]: unknown;
}

export interface Streets {
  generated_at: string;
  sources: Source[];
  curb: {
    active_this_week: number; starting_next_7d: number; reserved_ft: number; long_running_90d: number;
    freshness_note: string;
    by_type: { type: string; count: number }[];
    upcoming: { type: string; block: string; start: string; end: string; ft: number | null; hours: string | null }[];
  };
  trees: {
    total: number; species: number; planted_5y: number; empty_boxes: number; empty_boxes_note: string;
    condition: Record<string, number>;
    top_species: { name: string; count: number }[];
    biggest: { species: string; dbh_in: number; block: string }[];
    inventory_date: string;
  };
  service: { type: string; median_days: number; city_median_days: number; closed_n: number }[];
}

export interface History {
  generated_at: string;
  sources: Source[];
  buildings: {
    records: number; year_min: number; year_max: number;
    by_decade: { decade: number; count: number }[];
    top_architects: { name: string; count: number }[];
    top_builders: { name: string; count: number }[];
    featured_block: {
      block: string; year: number; buildings: number; permits: number; builder: string;
      architects: { name: string; count: number }[];
      largest_permit: { buildings: number; cost: number | null };
      sentence: string;
    } | null;
  };
  archive: { week_label: string; paper: string; terms: string[]; clips: { date: string; page: number; text: string; url: string }[]; note: string };
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
    recent: { type: string; agency: string; added: string; resolved: string | null; status: string; block: string | null }[];
  };
  crime: {
    total: number;
    previous_total: number;
    by_offense: { offense: string; count: number; previous: number }[];
    note: string;
  };
  smds: { smd: string; anc: string; commissioner: string | null; url: string | null }[];
  sources: Record<string, string>;
  homes?: Homes;
  streets?: Streets;
  history?: History;
}

const files = import.meta.glob<{ default: Neighborhood }>("../data/*.json", { eager: true });

export const neighborhoods: Neighborhood[] = Object.entries(files)
  .filter(([path]) => !path.endsWith("/index.json"))
  .map(([, mod]) => mod.default)
  .sort((a, b) => a.name.localeCompare(b.name));

export function titleCase(s: string): string {
  return s.toLowerCase().replace(/\b([a-z])/g, (m) => m.toUpperCase()).replace(/\b(Nw|Ne|Sw|Se)\b/g, (m) => m.toUpperCase());
}

/** Every page of a neighborhood section, in nav order. */
export const PAGES = [
  { path: "", label: "Overview" },
  { path: "projects/", label: "Projects" },
  { path: "homes/", label: "Homes" },
  { path: "streets/", label: "Streets" },
  { path: "then/", label: "Then" },
  { path: "representatives/", label: "Representatives" },
  { path: "subscribe/", label: "Weekly email" },
  { path: "about/", label: "About the data" },
] as const;

export const pageUrl = (slug: string, path = "") => `/${slug}/${path}`;

export function staticPaths() {
  return neighborhoods.map((n) => ({ params: { slug: n.slug }, props: { n } }));
}
