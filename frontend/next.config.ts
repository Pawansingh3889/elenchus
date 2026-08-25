import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  async rewrites() {
    // Only set inside the monolith container (see the root Dockerfile), where uvicorn
    // runs as a sibling process on this internal port and NEXT_PUBLIC_API_URL is empty
    // so the browser calls this same origin. Absent here, this is a no-op: the split
    // Vercel+Railway deployment calls Railway's public URL directly and never reaches
    // this function's destination branch.
    const backend = process.env.INTERNAL_BACKEND_URL;
    if (!backend) return [];
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
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
