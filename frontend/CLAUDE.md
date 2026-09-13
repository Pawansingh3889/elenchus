# Frontend decisions

Loaded when working under `frontend/`. Each one only bites while editing frontend files,
and the root file is in context for every session including the ones that never open
this directory.

- **The browser is the respondent path, and nothing else.** Cut on 13 Sep 2026, asked for
  directly. Four pages remain: `/`, `/signin`, `/respond` and `/runs/[id]`. The dashboard,
  builder, Results page, people admin and LLM admin screens are gone from the browser;
  every endpoint behind them is still served and still covered by the backend suite, so
  authoring is an API call. The only planned additions are the lens pages, one per factor
  (hidden layers, embeddings, attention, state, relationship, inference, tool selection,
  evaluation, validation), each showing cost and latency beside what it explains. Do not
  rebuild an authoring screen to get there.
- **Styling is `app/globals.css` and nothing else.** Tailwind, shadcn/ui, Radix, cva,
  clsx, tailwind-merge and lucide were removed with the pages that used them. Tokens sit
  at the top of the file, where `check_contrast.py` measures them; class rules sit below,
  in physical-direction-free CSS, which `check_logical_properties.py` enforces. The element
  resets are unlayered: they lived in `@layer base` only so utilities could beat them.
  A class with no rule renders unstyled and no checker notices, so rendering is verified
  by looking at the page. Do not reintroduce a utility framework or a component kit for
  the lens pages without a reason that names what plain classes cannot do.
- **`recharts` is the one charting dependency**, kept for the lens pages.
- **One frontend test, by policy.** `tests/smoke.test.tsx` proves the harness renders and
  queries a component. The checks are `tsc --noEmit`, `eslint`, `next build` and `vitest`.
  A new test is written when something breaks, and it names that bug.
- **Parse at the boundary when the lens pages arrive.** `lib/api.ts` still casts response
  bodies to their types. PR #65 (closed, branch `feat/parse-api-responses-at-the-boundary`)
  holds a zod mechanism, `lib/schemas.ts` plus `ApiContractError`, written for pages that
  render numbers from the API. The lens pages are exactly that, so lift it rather than
  casting.
