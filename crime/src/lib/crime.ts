// Shapes and arithmetic for the crime pages. Every figure here is a count from ingest/crime.py; nothing is estimated.
import data from "../data/crime.json";

export type Series = Record<string, number[]>; // offense -> one count per month, oldest first

export interface Area {
  slug: string;
  name: string;
  host: string;
  offenses: Series;
}

export const months: string[] = data.months;
export const violentSet = new Set<string>(data.violent);
export const source: string = data.source;
export const generatedAt: string = data.generated_at;
export const dc: Series = data.dc.offenses;
export const wards: { ward: string; offenses: Series }[] = data.wards;
export const unknownWard: Series = data.unknown_ward;
export const areas: Area[] = data.areas;

const HALF = months.length / 2; // the first half is the previous 12 months, the second the last 12

const MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const monthLabel = (m: string, long = false) => {
  const [y, n] = m.split("-").map(Number);
  return long ? `${MONTH[n - 1]} ${y}` : MONTH[n - 1];
};
export const prevLabel = `${monthLabel(months[0], true)} to ${monthLabel(months[HALF - 1], true)}`;
export const curLabel = `${monthLabel(months[HALF], true)} to ${monthLabel(months[months.length - 1], true)}`;

// DC's offense names, written for people.
const NAMES: Record<string, string> = {
  HOMICIDE: "Homicide",
  "SEX ABUSE": "Sex abuse",
  "ASSAULT W/DANGEROUS WEAPON": "Assault with a dangerous weapon",
  ROBBERY: "Robbery",
  BURGLARY: "Burglary",
  "MOTOR VEHICLE THEFT": "Motor vehicle theft",
  "THEFT F/AUTO": "Theft from a vehicle",
  "THEFT/OTHER": "Other theft",
  ARSON: "Arson",
};
export const offenseName = (o: string) => NAMES[o] ?? o.charAt(0) + o.slice(1).toLowerCase();

export const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

/** Total per month, over the offenses that pass the filter. */
export function monthly(s: Series, keep: (o: string) => boolean = () => true): number[] {
  return months.map((_, i) => Object.entries(s).reduce((t, [o, v]) => (keep(o) ? t + v[i] : t), 0));
}
export const isViolent = (o: string) => violentSet.has(o);
export const isProperty = (o: string) => !violentSet.has(o);

export interface Window {
  prev: number;
  cur: number;
}
export const windows = (perMonth: number[]): Window => ({ prev: sum(perMonth.slice(0, HALF)), cur: sum(perMonth.slice(HALF)) });

/**
 * The change from the previous 12 months to the last 12, in words. A percentage only when both counts are at least
 * 100: below that, a swing of a few reports reads as a dramatic rate, so the change is given as a count.
 */
export function change({ prev, cur }: Window): { text: string; short: string; dir: "up" | "down" | "same" } {
  const d = cur - prev;
  if (d === 0) return { text: "no change", short: "same", dir: "same" };
  const dir = d > 0 ? "up" : "down";
  if (prev >= 100 && cur >= 100) {
    const pct = Math.round((Math.abs(d) / prev) * 100);
    if (pct === 0) return { text: `about the same (${Math.abs(d).toLocaleString("en-US")} ${d > 0 ? "more" : "fewer"})`, short: "≈ same", dir };
    return { text: `${dir} ${pct}%`, short: `${d > 0 ? "+" : "−"}${pct}%`, dir };
  }
  const n = Math.abs(d).toLocaleString("en-US");
  return { text: `${n} ${d > 0 ? "more" : "fewer"}`, short: `${d > 0 ? "+" : "−"}${n}`, dir };
}

export const fmt = (n: number) => n.toLocaleString("en-US");

/** Rows for an offense table: every offense with a report in either window, largest last-12 count first. */
export function offenseRows(s: Series) {
  return Object.entries(s)
    .map(([o, v]) => ({ offense: o, name: offenseName(o), violent: isViolent(o), ...windows(v) }))
    .filter((r) => r.prev || r.cur)
    .sort((a, b) => b.cur - a.cur || b.prev - a.prev || a.name.localeCompare(b.name));
}

export interface Summary {
  total: Window;
  violent: Window;
  property: Window;
  homicide: Window;
}
export function summary(s: Series): Summary {
  return {
    total: windows(monthly(s)),
    violent: windows(monthly(s, isViolent)),
    property: windows(monthly(s, isProperty)),
    homicide: windows(monthly(s, (o) => o === "HOMICIDE")),
  };
}

export const wardName = (w: string) => `Ward ${w}`;
