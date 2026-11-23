import { defineConfig } from "astro/config";

// The private crime site (crime.georgetowndc.org), behind Cloudflare Access. Static pages, no client framework.
export default defineConfig({
  output: "static",
  trailingSlash: "ignore",
  build: { format: "directory" },
});
