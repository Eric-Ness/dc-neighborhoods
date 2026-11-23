// RSS feed of the latest building permits for one neighborhood: the cheapest possible "subscribe" button.
import type { APIRoute } from "astro";
import { neighborhoods, titleCase, hostOf, type Neighborhood } from "../../lib/data";

export function getStaticPaths() {
  return neighborhoods.map((n) => ({ params: { slug: n.slug }, props: { n } }));
}

// DC's permit text carries control characters (\x1a where a quote or dash was lost), which XML 1.0 forbids: one
// makes a strict feed reader reject the whole feed. They become a space; tab, newline and return are allowed.
const esc = (s: string) =>
  s
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\ufffe\uffff]/g, " ")
    .replace(/ {2,}/g, " ")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

export const GET: APIRoute = ({ props }) => {
  const n = (props as { n: Neighborhood }).n;
  // Each site's own domain (fortlincoln.net, twiningdc.org...), not <slug>.org, which for most sites is someone else's.
  const site = `https://${hostOf(n.slug)}/`;
  const items = n.permits
    .slice(0, 100)
    .map(
      (p) => `<item>
  <title>${esc(`${p.group}: ${titleCase(p.address)}`)}</title>
  <description>${esc(p.work || `${p.type ?? ""} ${p.subtype ?? ""}`.trim())}</description>
  <guid isPermaLink="false">${esc(p.id)}</guid>
  <pubDate>${p.issued ? new Date(p.issued).toUTCString() : ""}</pubDate>
  <link>${site}projects/</link>
</item>`,
    )
    .join("\n");
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>${esc(n.name)}: new building permits</title>
<link>${site}</link>
<description>Building permits issued in ${esc(n.name)}, from Open Data DC. Independent; not affiliated with DC Government.</description>
<lastBuildDate>${new Date(n.generated_at).toUTCString()}</lastBuildDate>
${items}
</channel></rss>`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } });
};
