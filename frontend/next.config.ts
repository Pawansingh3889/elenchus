import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  turbopack: {
    // Pin the workspace root. Under the container bind mount Turbopack otherwise
    // infers ./app and crashes `next dev` on compile (exit 1), killing the container.
    root: path.join(__dirname),
  },
};

export default nextConfig;
