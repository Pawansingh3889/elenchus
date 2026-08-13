import { expect, test } from "@playwright/test";

/**
 * A smoke test, and only that.
 *
 * It proves the app builds, serves, and runs its client JavaScript in a real browser.
 * It deliberately needs no backend, no Postgres and no seeding: with nothing in
 * localStorage the landing page renders its signed-out state without a single
 * successful fetch, so this stays a one-service test until a real one earns the whole
 * stack. `/` is a better home for it since the split: it is the one route that is meant
 * to render for a visitor with no user at all, where `/dashboard` only ever says to go
 * and sign in.
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

  // The landing explains itself to someone who has never seen it, with no user and no
  // backend. This is the copy a first-time arrival is here for, so it is worth asserting.
  await expect(
    page.getByRole("heading", { name: "Surveys that ask like a person, not a form" }),
  ).toBeVisible();

  // And the client component decided what to show, which means React hydrated and the
  // store was read. A server-rendered husk would not get this far. The copy moved when
  // signing in became an address rather than a picker, and this assertion sat on the
  // old sentence for five hours of red CI: it is the page's words, so it moves with them.
  await expect(page.getByText("Sign in at the top of the page to start.")).toBeVisible();
});
