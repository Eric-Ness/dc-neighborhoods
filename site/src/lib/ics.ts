// Calendar feeds (.ics) a reader can subscribe to: each block's trash and recycling days, and the neighborhood's
// events and ANC meetings. Built nightly with the rest of the site, so a subscribed calendar picks up changes.
import type { Neighborhood } from "./data";

const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const BYDAY = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"];

/** "Tuesday/Friday" -> [2, 5]; anything unrecognized -> []. */
export const weekdays = (s?: string | null) =>
  (s ?? "").split(/[/,&]| and /).map((d) => DAYS.findIndex((x) => x.toLowerCase() === d.trim().toLowerCase())).filter((i) => i >= 0);

const daySlug = (s?: string | null) => weekdays(s).map((i) => DAYS[i].toLowerCase()).join("-") || "none";

/** The feed for a block's pickup days, or null when DPW's route map has no day for it. */
export const pickupFeed = (trash?: string | null, recycling?: string | null) =>
  weekdays(trash).length || weekdays(recycling).length ? `pickup-${daySlug(trash)}-${daySlug(recycling)}` : null;

const esc = (s: string) => s.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");

// Lines longer than 75 octets continue on the next line after a space (RFC 5545 3.1).
function fold(line: string): string {
  const out: string[] = [];
  let cur = "", bytes = 0;
  for (const ch of line) {
    const b = new TextEncoder().encode(ch).length;
    if (bytes + b > (out.length ? 74 : 75)) { out.push(cur); cur = ""; bytes = 0; }
    cur += ch; bytes += b;
  }
  out.push(cur);
  return out.join("\r\n ");
}

const TZ = [
  "BEGIN:VTIMEZONE", "TZID:America/New_York",
  "BEGIN:DAYLIGHT", "TZOFFSETFROM:-0500", "TZOFFSETTO:-0400", "TZNAME:EDT", "DTSTART:19700308T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU", "END:DAYLIGHT",
  "BEGIN:STANDARD", "TZOFFSETFROM:-0400", "TZOFFSETTO:-0500", "TZNAME:EST", "DTSTART:19701101T020000", "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU", "END:STANDARD",
  "END:VTIMEZONE",
];

const stamp = (iso: string) => iso.replace(/[-:]/g, "").replace(/\.\d+/, "").replace(/Z?$/, "Z");
const ymd = (d: string) => d.slice(0, 10).replace(/-/g, "");
const nextDay = (d: string) => { const t = new Date(`${d.slice(0, 10)}T12:00:00Z`); t.setUTCDate(t.getUTCDate() + 1); return t.toISOString().slice(0, 10); };
const hash = (s: string) => { let h = 5381; for (const c of s) h = ((h * 33) ^ c.charCodeAt(0)) >>> 0; return h.toString(36); };

function calendar(name: string, desc: string, host: string, events: string[][]): string {
  return [
    "BEGIN:VCALENDAR", "VERSION:2.0", `PRODID:-//${host}//neighborhood calendar//EN`, "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
    `X-WR-CALNAME:${esc(name)}`, `X-WR-CALDESC:${esc(desc)}`, "X-WR-TIMEZONE:America/New_York",
    "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H",
    ...TZ, ...events.flat(), "END:VCALENDAR",
  ].map(fold).join("\r\n") + "\r\n";
}

export function pickupCalendar(n: Neighborhood, host: string, feed: string, trash: string | null, recycling: string | null): string {
  const now = stamp(n.generated_at);
  const today = n.generated_at.slice(0, 10);
  // First occurrence on or after today, so the series starts now.
  const first = (dow: number) => { const t = new Date(`${today}T12:00:00Z`); t.setUTCDate(t.getUTCDate() + ((dow - t.getUTCDay() + 7) % 7)); return t.toISOString().slice(0, 10); };
  const note = `DC Department of Public Works residential collection, from DPW's route map on Open Data DC. Holiday weeks can shift pickup; check dpw.dc.gov. Put bins out the night before. From ${host}, an independent site; not affiliated with DC government.`;
  const series = (what: string, days: number[]) => {
    const start = days.map(first).sort()[0];
    return [
      "BEGIN:VEVENT", `UID:${feed}-${what.toLowerCase().replace(/\W+/g, "-")}@${host}`, `DTSTAMP:${now}`,
      `DTSTART;VALUE=DATE:${ymd(start)}`, `DTEND;VALUE=DATE:${ymd(nextDay(start))}`,
      `RRULE:FREQ=WEEKLY;BYDAY=${days.map((d) => BYDAY[d]).join(",")}`,
      `SUMMARY:${esc(what)}`, `DESCRIPTION:${esc(note)}`, "TRANSP:TRANSPARENT",
      // 7 PM the evening before.
      "BEGIN:VALARM", "ACTION:DISPLAY", `DESCRIPTION:${esc(`${what} tomorrow`)}`, "TRIGGER:-PT5H", "END:VALARM",
      "END:VEVENT",
    ];
  };
  const t = weekdays(trash), r = weekdays(recycling);
  const same = t.length && t.join() === r.join();
  const events = same ? [series("Trash and recycling pickup", t)]
    : [...(t.length ? [series("Trash pickup", t)] : []), ...(r.length ? [series("Recycling pickup", r)] : [])];
  const label = same ? `${trash}` : [trash && `trash ${trash}`, recycling && `recycling ${recycling}`].filter(Boolean).join(", ");
  return calendar(`${n.name}: trash and recycling (${label})`, `Weekly pickup days for blocks in ${n.name} collected ${label}.`, host, events);
}

/** "9:00 AM - 1:00 PM", "6:30 PM to 8", "7 PM" -> 24-hour start and end, or null for all-day. */
export function parseTimes(s?: string | null): { start: string; end: string | null } | null {
  const m = (s ?? "").match(/(\d{1,2})(?::(\d{2}))?\s*([AP])\.?M\.?(?:\s*(?:-|–|to)\s*(\d{1,2})(?::(\d{2}))?\s*(?:([AP])\.?M\.?)?)?/i);
  if (!m) return null;
  const h24 = (h: string, min: string | undefined, ap: string) => {
    let hh = +h % 12;
    if (ap.toUpperCase() === "P") hh += 12;
    return `${String(hh).padStart(2, "0")}${(min ?? "00").padStart(2, "0")}00`;
  };
  const start = h24(m[1], m[2], m[3]);
  let end = m[4] ? h24(m[4], m[5], m[6] ?? m[3]) : null;
  if (end && end <= start) end = null;
  return { start, end };
}

export function eventsCalendar(n: Neighborhood, host: string): string {
  const now = stamp(n.generated_at);
  const events = (n.events?.events ?? []).map((e) => {
    const t = parseTimes(e.time);
    const when = t
      ? [`DTSTART;TZID=America/New_York:${ymd(e.date)}T${t.start}`, ...(t.end ? [`DTEND;TZID=America/New_York:${ymd(e.date)}T${t.end}`] : [])]
      : [`DTSTART;VALUE=DATE:${ymd(e.date)}`, `DTEND;VALUE=DATE:${ymd(nextDay(e.date))}`];
    return [
      "BEGIN:VEVENT", `UID:${hash(`${e.title}|${e.date}|${e.place ?? ""}`)}-${e.date}@${host}`, `DTSTAMP:${now}`, ...when,
      `SUMMARY:${esc(e.title)}`,
      ...(e.place ? [`LOCATION:${esc(e.place)}`] : []),
      `DESCRIPTION:${esc([e.time && `Listed time: ${e.time}.`, `Source: ${e.source}.`, e.url && `Details: ${e.url}`].filter(Boolean).join(" "))}`,
      ...(e.url ? [`URL:${e.url}`] : []),
      "END:VEVENT",
    ];
  });
  return calendar(`${n.name}: events and ANC meetings`, `Community events, markets and ANC meetings in and around ${n.name}, gathered nightly from public calendars. Check each listing's source before you go.`, host, events);
}
