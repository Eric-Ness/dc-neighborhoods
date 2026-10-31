import { defineConfig } from "astro/config";

// One static build holds every neighborhood under /<slug>/.
// The Cloudflare Worker in ../worker maps each hostname (petworth.org, ...) onto its folder.
export default defineConfig({
  output: "static",
  trailingSlash: "ignore",
  build: { format: "directory" },
});
