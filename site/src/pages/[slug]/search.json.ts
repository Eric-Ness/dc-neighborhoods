// Street/address lookup index for one neighborhood: permits, recent home sales and upcoming curb permits.
// Each entry: a = address or block, k = kind, d = detail, u = link to the row on the site.
import type { APIRoute } from "astro";
import { staticPaths, type Neighborhood } from "../../lib/data";
import { addr, money, shortDate } from "../../lib/c5";

export const getStaticPaths = staticPaths;

export const GET: APIRoute = ({ props }) => {
  const n = (props as { n: Neighborhood }).n;
  const base = `/${n.slug}/`;
  const hits: { a: string; k: string; d: string; u: string }[] = [];
  for (const p of n.permits) {
    hits.push({ a: addr(p.address), k: `Permit · ${p.group}`, d: shortDate(p.issued), u: `${base}projects/#p${p.id}` });
  }
  for (const s of n.homes?.recent_sales ?? []) {
    hits.push({ a: addr(s.address), k: `Sold · ${s.kind}`, d: `${money(s.price)} · ${shortDate(s.date)}`, u: `${base}homes/#recent` });
  }
  for (const c of n.streets?.curb.upcoming ?? []) {
    hits.push({ a: c.block, k: `Curb · ${c.type}`, d: `from ${shortDate(c.start)}`, u: `${base}streets/#curb` });
  }
  return new Response(JSON.stringify(hits), { headers: { "Content-Type": "application/json" } });
};
