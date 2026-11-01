// GET /api/transit?rail=<station names, |-separated>&stops=<WMATA stop ids>&docks=<bikeshare station ids>
// Live arrivals for the transit board on our own pages. WMATA's key stays here (env.WMATA_API_KEY, a Worker
// secret); every upstream answer is cached ~30 s, so traffic to the sites never multiplies calls to WMATA.
// WMATA's terms allow showing the data in our own site but not redistributing it, so only our pages may call
// this (same-origin), and requests are capped to a handful of ids.

const WMATA = "https://api.wmata.com";
const GBFS_STATUS = "https://gbfs.lyft.com/gbfs/1.1/dca-cabi/en/station_status.json";
const TTL = 30;           // seconds, predictions and dock status
const STATIONS_TTL = 86400;
const MAX = { rail: 3, stops: 6, docks: 6 };

const json = (body, status = 200, extra = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });

async function cached(url, ttl, headers = {}) {
  const cache = caches.default;
  // The cache key never includes the API key (that travels in a header).
  const key = new Request(url, { method: "GET" });
  const hit = await cache.match(key);
  if (hit) return hit.json();
  const r = await fetch(url, { headers: { accept: "application/json", ...headers } });
  if (!r.ok) throw new Error(`${new URL(url).pathname} ${r.status}`);
  const body = await r.text();
  await cache.put(key, new Response(body, { headers: { "content-type": "application/json", "cache-control": `max-age=${ttl}` } }));
  return JSON.parse(body);
}

function sameOrigin(request, url) {
  const site = request.headers.get("sec-fetch-site");
  if (site) return site === "same-origin";
  const ref = request.headers.get("referer");
  try { return !!ref && new URL(ref).host === url.host; } catch { return false; }
}

const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

export async function transit(request, env) {
  const url = new URL(request.url);
  if (!sameOrigin(request, url)) return json({ error: "This endpoint serves this site's own pages only." }, 403);

  const rail = (url.searchParams.get("rail") || "").split("|").map((s) => s.trim()).filter(Boolean).slice(0, MAX.rail);
  const stops = (url.searchParams.get("stops") || "").split(",").filter((s) => /^\d{4,8}$/.test(s)).slice(0, MAX.stops);
  const docks = (url.searchParams.get("docks") || "").split(",").filter((s) => /^[\w-]{1,64}$/.test(s)).slice(0, MAX.docks);
  const out = { rail: null, bus: null, bikes: null, alerts: [] };
  const key = env.WMATA_API_KEY;
  const wh = key ? { api_key: key } : null;

  const tasks = [];
  if (wh && rail.length) {
    tasks.push((async () => {
      const all = await cached(`${WMATA}/Rail.svc/json/jStations`, STATIONS_TTL, wh);
      const byName = new Map();
      for (const s of all.Stations || []) {
        const k = norm(s.Name);
        byName.set(k, [...(byName.get(k) || []), s]);
      }
      const want = rail.map((name) => {
        // DC GIS names ("Georgia Ave-Petworth") and WMATA's match once punctuation is dropped; fall back to a prefix.
        let ss = byName.get(norm(name));
        if (!ss) for (const [k, v] of byName) if (k.startsWith(norm(name).slice(0, 10))) { ss = v; break; }
        return { name, codes: (ss || []).map((s) => s.Code), lines: (ss || []).flatMap((s) => [s.LineCode1, s.LineCode2, s.LineCode3, s.LineCode4]).filter(Boolean) };
      });
      const codes = want.flatMap((w) => w.codes);
      const preds = codes.length ? await cached(`${WMATA}/StationPrediction.svc/json/GetPrediction/${codes.join(",")}`, TTL, wh) : { Trains: [] };
      out.rail = want.map((w) => ({
        station: w.name,
        trains: (preds.Trains || [])
          .filter((t) => w.codes.includes(t.LocationCode) && t.Destination && t.Line && t.Line !== "--" && t.Line !== "No")
          .map((t) => ({ line: t.Line, dest: t.DestinationName || t.Destination, min: t.Min })),
      }));
      const lines = new Set(want.flatMap((w) => w.lines));
      const inc = await cached(`${WMATA}/Incidents.svc/json/Incidents`, TTL * 2, wh).catch(() => ({ Incidents: [] }));
      out.alerts = (inc.Incidents || [])
        .filter((i) => (i.LinesAffected || "").split(/[;,\s]+/).some((l) => lines.has(l)))
        .map((i) => i.Description).slice(0, 2);
    })().catch(() => { out.rail = null; }));
  }
  if (wh && stops.length) {
    tasks.push(Promise.all(stops.map(async (id) => {
      try {
        const p = await cached(`${WMATA}/NextBusService.svc/json/jPredictions?StopID=${id}`, TTL, wh);
        return { stop: id, preds: (p.Predictions || []).map((x) => ({ route: x.RouteID, dir: x.DirectionText, min: x.Minutes })) };
      } catch { return { stop: id, preds: [] }; }
    })).then((r) => { out.bus = r; }));
  }
  if (docks.length) {
    tasks.push(cached(GBFS_STATUS, TTL).then((g) => {
      const want = new Set(docks);
      out.bikes = (g.data?.stations || []).filter((s) => want.has(s.station_id)).map((s) => ({
        id: s.station_id, bikes: s.num_bikes_available ?? 0, ebikes: s.num_ebikes_available ?? 0,
        docks: s.num_docks_available ?? 0, renting: s.is_renting === 1 || s.is_renting === true,
      }));
    }).catch(() => { out.bikes = null; }));
  }
  await Promise.all(tasks);
  if (!key) out.note = "Live Metro and bus times aren't switched on yet.";
  return json(out);
}
