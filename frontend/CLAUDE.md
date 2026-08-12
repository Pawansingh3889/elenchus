# Frontend decisions

Loaded when working under `frontend/`. These were in the root `CLAUDE.md` and moved here
on 12 Aug 2026: each one only bites while editing frontend files, and the root file is in
context for every session including the ones that never open this directory.

- **Tailwind sits beside `globals.css`, and only the element resets are layered.**
  Adopted 12 Aug 2026 with vendored shadcn/ui primitives under `components/ui/`,
  Recharts and TanStack Table. The palette stays in `globals.css`, where
  `check_contrast.py` measures it; `app/tailwind.css` maps it with `@theme inline`, so
  utilities compile to `var(--ink)` and the existing `prefers-color-scheme` swap drives
  Tailwind with no `dark:` variants. Preflight is not imported, because the respondent
  pages render from `globals.css` alone.
  The rule to keep: **class rules in `globals.css` stay unlayered and beat every
  utility; the `*`, `a` and `button` resets are in `@layer base` so utilities can
  override them.** Unlayered, `* { padding: 0 }` silently defeated every `px-*` on every
  new component and `a { color: inherit }` rendered a light-on-dark button's label in
  body ink. Both compile and lint clean, so they were found by reading computed styles
  off a rendered page. If a utility ever appears to do nothing, look for an unlayered
  element rule before anything else.
- **A Tailwind class that produces no CSS fails the gate.** `frontend/scripts/check-tailwind-classes.mjs`
  compiles the app's own entry stylesheet and checks every class named in a `className`,
  `cn()` or `cva()` string literal. An invented utility is a correct string, so `tsc` and
  `eslint` both pass it and the element renders unstyled; two were written on the day the
  guard was added. Only literals are checked, so a class built at runtime is invisible to
  it, which is why it is a guard and not a proof.
- **Report and Responses are one Results page, sliceable by any closed answer.** Merged
  12 Aug 2026, the shape `docs/ACCESS_AND_RESULTS.md` had already specified. The server
  reports the whole survey; `GET /templates/{id}/answers` returns every answer with its
  respondent so the client can cross-tabulate, and `lib/tally.ts` is a port of
  `_report_question` because a sliced view must retally over a subset and a server number
  beside a client number would invite a comparison between two provenances. The port is
  pinned by vitest against the server's own cases. `SLICE_MIN_GROUP` in `lib/slicing.ts`
  is 0 and every sliced view passes through it: that is the suppression threshold the
  docs asked to be left one constant away.
