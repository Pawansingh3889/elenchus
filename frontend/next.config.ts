import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      // Report was merged into Results. Temporary rather than permanent: a 308 is
      // cached by the browser forever and would make the path unreclaimable, and
      // there is no external link to this to preserve, only an author's bookmark.
      {
        source: "/templates/:id/report",
        destination: "/templates/:id/results",
        permanent: false,
      },
    ];
  },
  turbopack: {
    // Pin the workspace root. Under the container bind mount Turbopack otherwise
    // infers ./app and crashes `next dev` on compile (exit 1), killing the container.
    // Known upstream bug: https://github.com/vercel/next.js/issues/92540 — docs: https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopack
    root: path.join(__dirname),
  },
};

export default nextConfig;
