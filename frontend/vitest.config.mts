import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * Unit and component tests, in jsdom, with nothing running.
 *
 * `.mts` rather than `.ts`: package.json declares no `"type"`, so the package is CommonJS
 * and a plain `.ts` config would be read as such. `**\/*.mts` is already in tsconfig's
 * include, so this file is type-checked like everything else.
 *
 * `resolve.tsconfigPaths` rather than the vite-tsconfig-paths plugin, which Vite 8 made
 * redundant and now warns about. Either way the point is the same: the `@/` alias is
 * declared in tsconfig with no `baseUrl`, and a second copy of it here would be one more
 * thing to keep in step with a file that already answers the question.
 */
export default defineConfig({
  plugins: [react()],
  resolve: { tsconfigPaths: true },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    // Scoped deliberately: e2e/ belongs to Playwright, and a runner that picks up the
    // other one's files fails in a way that reads like a broken test rather than a
    // misrouted file.
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
