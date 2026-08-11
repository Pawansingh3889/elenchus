// Screenshot a page as a signed-in author, for looking at while designing. Not a test:
// the .mjs extension keeps it out of the spec glob deliberately.
//
// It exists mostly to hold the two traps in one place. The current user lives in
// localStorage and the picker's own list 401s without it, so a browser cannot click its
// way in; and the app is built with NEXT_PUBLIC_API_URL=http://localhost:8000, which is
// the host's backend but this browser's own container.
// Run inside the frontend container:
//   node e2e/shot.mjs /  /tmp/dashboard.png
import { chromium } from "@playwright/test";

const [, , path = "/", out = "/tmp/shot.png"] = process.argv;
const AVA = "00000000-0000-0000-0000-0000000000a1";

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 1400 } });
await context.addInitScript((id) => {
  localStorage.setItem(
    "elenchus-user",
    JSON.stringify({ state: { currentUserId: id }, version: 0 }),
  );
}, AVA);
// The app is built with NEXT_PUBLIC_API_URL=http://localhost:8000, which is correct for
// a browser on the host and wrong for this one: it runs inside the frontend container,
// where localhost:8000 is the frontend. Rewrite to the service name on the compose
// network rather than rebuilding the app with a different base for a screenshot.
const page = await context.newPage();
await page.route("http://localhost:8000/**", (route) =>
  route.continue({ url: route.request().url().replace("http://localhost:8000", "http://backend:8000") }),
);
await page.goto(`http://localhost:3000${path}`, { waitUntil: "domcontentloaded" });
// Wait for hydration to have actually happened rather than for the network to go quiet:
// the dev server restarts on a memory threshold and a quiet network can mean the chunks
// 404'd, which screenshots as unstyled server HTML.
await page.waitForFunction(() => !document.body.innerText.includes("Pick a user"), null, {
  timeout: 30000,
});
// And for the data, not just the shell: the stat row and every survey row are absent
// while the dashboard query is in flight, so a shot taken at hydration is an empty page.
await page.waitForSelector(process.env.SHOT_WAIT || ".template-row", { timeout: 30000 });
await page.waitForLoadState("networkidle");
await page.waitForTimeout(800);
await page.screenshot({ path: out, fullPage: true });
console.log("wrote", out);
await browser.close();
