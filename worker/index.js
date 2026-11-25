// Cloudflare Worker in front of the static site.
// - petworth.org/...  -> serves site/dist/petworth/...
// - petworth.net/...  -> 301 to https://petworth.org/...
// - anything else (e.g. *.workers.dev previews) -> serves the multi-neighborhood site unchanged
// - /api/transit on any of them -> live transit arrivals (worker/transit.js)
// - http://anything -> 301 to https://, and every response carries the security headers below
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

// Sent on every response from every neighborhood domain. Scripts and styles may only come from the
// site itself (plus Google Fonts); photos come from many archives, so images may load from any https host.
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  "img-src 'self' data: https:",
  "connect-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests",
].join("; ");
const SECURITY_HEADERS = {
  // No includeSubDomains or preload yet: both are slow to undo once browsers have cached them.
  "Strict-Transport-Security": "max-age=31536000",
  "Content-Security-Policy": CSP,
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  // The transit board asks for location on a click, so geolocation stays allowed for the site itself.
  "Permissions-Policy": "geolocation=(self), camera=(), microphone=(), payment=(), usb=()",
  "Cross-Origin-Opener-Policy": "same-origin",
};

function secured(response) {
  const out = new Response(response.body, response); // redirect and asset responses have immutable headers
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) out.headers.set(k, v);
  return out;
}

export default {
  async fetch(request, env) {
    return secured(await route(request, env));
  },
};

const LOCAL = new Set(["localhost", "127.0.0.1", "[::1]"]); // wrangler dev runs on plain http
async function route(request, env) {
  const url = new URL(request.url);
  const host = url.hostname.toLowerCase();

  // One hop: http://www.petworth.net/x goes straight to https://petworth.org/x.
  const target = REDIRECTS.get(host);
  if (target || (url.protocol === "http:" && !LOCAL.has(host))) {
    return Response.redirect(`https://${target ?? host}${url.pathname}${url.search}`, 301);
  }

  if (url.pathname === "/api/transit") return transit(request, env);

  const slug = HOSTS.get(host);
  const isShared = url.pathname.startsWith("/_astro/") || url.pathname.startsWith("/favicon");
  // Old or hand-typed prefixed links (petworth.org/petworth/news/) go to the clean address.
  if (slug && (url.pathname === `/${slug}` || url.pathname.startsWith(`/${slug}/`))) {
    return Response.redirect(`https://${host}${url.pathname.slice(slug.length + 1) || "/"}${url.search}`, 301);
  }
  if (slug && !isShared) {
    url.pathname = `/${slug}${url.pathname === "/" ? "/" : url.pathname}`;
    return env.ASSETS.fetch(new Request(url, request));
  }
  return env.ASSETS.fetch(request);
}
