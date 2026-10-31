// RSS feed of the latest building permits for one neighborhood: the cheapest possible "subscribe" button.
import type { APIRoute } from "astro";
import { neighborhoods, titleCase, type Neighborhood } from "../../lib/data";

export function getStaticPaths() {
  return neighborhoods.map((n) => ({ params: { slug: n.slug }, props: { n } }));
}

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export const GET: APIRoute = ({ props }) => {
  const n = (props as { n: Neighborhood }).n;
  const items = n.permits
    .slice(0, 100)
    .map(
      (p) => `<item>
  <title>${esc(`${p.group}: ${titleCase(p.address)}`)}</title>
  <description>${esc(p.work || `${p.type ?? ""} ${p.subtype ?? ""}`.trim())}</description>
  <guid isPermaLink="false">${esc(p.id)}</guid>
  <pubDate>${p.issued ? new Date(p.issued).toUTCString() : ""}</pubDate>
  <link>https://${n.slug}.org/#permits</link>
</item>`,
    )
    .join("\n");
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>${esc(n.name)}: new building permits</title>
<link>https://${n.slug}.org/</link>
<description>Building permits issued in ${esc(n.name)}, from Open Data DC. Independent; not affiliated with DC Government.</description>
<lastBuildDate>${new Date(n.generated_at).toUTCString()}</lastBuildDate>
${items}
</channel></rss>`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } });
};
