import { defineConfig, devices } from "@playwright/test";

/**
 * Browser tests. Separate from Vitest by directory: `e2e/` here, `tests/` there, and
 * neither runner is allowed to pick up the other's files.
 *
 * The server is started by Playwright rather than assumed, so a bare `pnpm test:e2e`
 * works on a clean machine. `reuseExistingServer` off in CI so a run can never silently
 * test a stale process; on locally, because a developer usually has `pnpm dev` up
 * already and waiting for a second build helps nobody.
 *
 * Note for whoever adds the first real test: do NOT use the `@/` alias in this
 * directory. Playwright's TypeScript loader does not read tsconfig `paths`, and these
 * files drive a browser rather than importing application code anyway.
 */
export default defineConfig({
  testDir: "./e2e",
  // A test that only passes when run alone is a test that lies, and finding that out on
  // the fifth test is worse than on the first.
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "pnpm build && pnpm start",
    url: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
