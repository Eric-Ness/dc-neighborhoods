// Calendar feeds: /calendar/events.ics (events and ANC meetings) and one /calendar/pickup-<trash>-<recycling>.ics
// per combination of DPW pickup days in the neighborhood, which each block page links to (lib/ics.ts).
import type { APIRoute } from "astro";
import { neighborhoods, hostOf, type Neighborhood } from "../../../lib/data";
import { eventsCalendar, pickupCalendar, pickupFeed } from "../../../lib/ics";

type Props = { n: Neighborhood; trash?: string | null; recycling?: string | null };

export function getStaticPaths() {
  return neighborhoods.flatMap((n) => {
    const pickups = new Map<string, Props>();
    for (const b of n.blocks?.items ?? []) {
      const feed = pickupFeed(b.trash_day, b.recycling_day);
      if (feed && !pickups.has(feed)) pickups.set(feed, { n, trash: b.trash_day ?? null, recycling: b.recycling_day ?? null });
    }
    return [
      { params: { slug: n.slug, feed: "events" }, props: { n } },
      ...[...pickups].map(([feed, props]) => ({ params: { slug: n.slug, feed }, props })),
    ];
  });
}

export const GET: APIRoute = ({ params, props }) => {
  const { n, trash, recycling } = props as Props;
  const host = hostOf(n.slug);
  const body = params.feed === "events" ? eventsCalendar(n, host) : pickupCalendar(n, host, params.feed!, trash ?? null, recycling ?? null);
  return new Response(body, { headers: { "Content-Type": "text/calendar; charset=utf-8" } });
};
