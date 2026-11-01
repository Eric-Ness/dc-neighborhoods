// Cloudflare Worker in front of the static site.
// - petworth.org/...  -> serves site/dist/petworth/...
// - petworth.net/...  -> 301 to https://petworth.org/...
// - anything else (e.g. *.workers.dev previews) -> serves the multi-neighborhood site unchanged
// - /api/transit on any of them -> live transit arrivals (worker/transit.js)
import hoods from "../site/src/data/index.json" with { type: "json" };
import { transit } from "./transit.js";

const HOSTS = new Map();
const REDIRECTS = new Map();
for (const h of hoods) {
  for (const host of h.hosts) {
    HOSTS.set(host, h.slug);
    REDIRECTS.set(`www.${host}`, host);
  }
  for (const host of h.redirect_hosts) {
    REDIRECTS.set(host, h.hosts[0]);
    REDIRECTS.set(`www.${host}`, h.hosts[0]);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = url.hostname.toLowerCase();

    const target = REDIRECTS.get(host);
    if (target) {
      return Response.redirect(`https://${target}${url.pathname}${url.search}`, 301);
    }

    if (url.pathname === "/api/transit") return transit(request, env);

    const slug = HOSTS.get(host);
    const isShared = url.pathname.startsWith("/_astro/") || url.pathname.startsWith("/favicon");
    if (slug && !isShared && !url.pathname.startsWith(`/${slug}/`)) {
      url.pathname = `/${slug}${url.pathname === "/" ? "/" : url.pathname}`;
      return env.ASSETS.fetch(new Request(url, request));
    }
    return env.ASSETS.fetch(request);
  },
};
