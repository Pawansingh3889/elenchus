import { expect, test } from "@playwright/test";

/**
 * A smoke test, and only that.
 *
 * It proves the app builds, serves, and runs its client JavaScript in a real browser.
 * It deliberately needs no backend, no Postgres and no seeding: with nothing in
 * localStorage the home page renders its "pick a user" state without a single successful
 * fetch, so this stays a one-service test until a real one earns the whole stack.
 *
 * For whoever writes that first real test, the trap is worth knowing in advance: the
 * current user lives in localStorage under `elenchus-user`, and the user picker's own
 * list comes from an endpoint that 401s without the header that key supplies. So a test
 * cannot click its way in. Seed it before the page scripts run:
 *
 *   await context.addInitScript(() =>
 *     localStorage.setItem(
 *       "elenchus-user",
 *       JSON.stringify({ state: { currentUserId: "00000000-0000-0000-0000-0000000000a1" }, version: 0 }),
 *     ),
 *   );
 *
 * That id is Ava Author, stable in the seed data.
 */
test("the app boots and renders its signed-out state", async ({ page }) => {
  await page.goto("/");

  // The shell rendered.
  await expect(page.getByText("Survey", { exact: false }).first()).toBeVisible();

  // And the client component decided what to show, which means React hydrated and the
  // store was read. A server-rendered husk would not get this far.
  await expect(page.getByText("Pick a user in the top bar to start authoring.")).toBeVisible();
});
