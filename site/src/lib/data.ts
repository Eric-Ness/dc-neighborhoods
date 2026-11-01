// Typed access to the JSON written by ingest/run.py (core sections) and its modules
// (ingest/homes.py, streets.py, history.py, news.py, events.py). Module sections are optional
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
  primary?: "house" | "condo" | "all"; // what leads: condos where houses are rare, "all" where both are
  all?: { median_12mo: number; count_12mo: number; median_prev_12mo: number; count_prev_12mo: number };
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

export interface NewsItem { title: string; url: string; source: string; published: string; first_seen: string }
export interface News {
  generated_at: string;
  archive_days: number;
  sources: Source[];
  outlets: { name: string; url: string; state: string; matched: number }[];
  items: NewsItem[];
  licenses: {
    tracked_since: string; active: number;
    by_type: { type: string; count: number }[];
    new: { license: string; trade_name: string | null; address: string; type: string; first_seen: string }[];
    cancelled?: { license: string; trade_name: string | null; address: string; type: string; cancelled: string | null; first_seen: string | null }[];
  };
}

export interface EventItem { title: string; date: string; time: string | null; place: string | null; url: string; source: string; kind: string }
export interface Events {
  generated_at: string;
  today: string;
  days_ahead: number;
  sources: Source[];
  calendars: { name: string; url: string; state: string }[];
  events: EventItem[];
  unscheduled: (Omit<EventItem, "date"> & { schedule: string })[];
  links: Source[];
  ancs?: string[];
  anc_meetings?: { anc: string; date: string; special: boolean; title: string; url: string }[];
}

export interface Job { title: string; employer: string; place: string; where: "in" | "nearby"; note: string | null; posted: string | null; hours: string | null; url: string }
export interface Jobs {
  generated_at: string;
  max_age_days: number;
  sources: Source[];
  employers: { name: string; url: string; state: string; count: number }[];
  jobs: Job[];
}

export interface Block {
  key: string; hundred: number; street: string; name: string; from: string; to: string;
  lat: number; lon: number; major: boolean;
  snow_emergency: boolean; speed: number | null; bike_lanes: number; protected_bike_lane: boolean; bus_lane: boolean;
  slow_street: boolean; pavement: string | null; pavement_checked: string | null; smd: string | null;
  trash_day: string | null; recycling_day: string | null; leaf_zone: string | null; leaf_done: boolean | null;
  schools: { elementary?: string; middle?: string; high?: string };
  parking: { side: string | null; rpp: string | null; meter: string | null; spaces: number | null }[];
}
export interface Blocks {
  generated_at: string;
  sources: Source[];
  lookup_errors: string[];
  leaf_status: Record<string, string>;
  schools: Record<string, { name: string; address: string | null; url: string | null; grades: string | null }>;
  basemap: { bbox: [number, number, number, number]; streets: { n: string; k: "major" | "minor"; p: [number, number][]; b?: string }[] };
  items: Block[];
}

export interface Transit {
  generated_at: string;
  sources: Source[];
  stations: { name: string; lines: string[]; lat: number; lon: number; km_outside: number }[];
  bus_stops: { id: string; name: string; lat: number; lon: number }[];
  bike_docks: { id: string; name: string; capacity: number; lat: number; lon: number }[];
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
    recent: { type: string; agency: string; added: string; resolved: string | null; status: string; block: string | null; lat?: number | null; lon?: number | null }[];
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
  news?: News;
  events?: Events;
  jobs?: Jobs;
  blocks?: Blocks;
  transit?: Transit;
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
  { path: "news/", label: "News & events" },
  { path: "transit/", label: "Getting around" },
  { path: "blocks/", label: "Your block" },
  { path: "projects/", label: "Projects" },
  { path: "homes/", label: "Homes" },
  { path: "streets/", label: "Streets" },
  { path: "then/", label: "Then" },
  { path: "jobs/", label: "Jobs" },
  { path: "representatives/", label: "Representatives" },
  { path: "subscribe/", label: "Weekly email" },
  { path: "about/", label: "About the data" },
] as const;

export const pageUrl = (slug: string, path = "") => `/${slug}/${path}`;

export function staticPaths() {
  return neighborhoods.map((n) => ({ params: { slug: n.slug }, props: { n } }));
}
