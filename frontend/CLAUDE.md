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
- **Colour on the report carries a group, and amber carries a flag. Nothing else.**
  Built 17 Aug 2026. A hue per option was the obvious way to "add colour to the charts"
  and is wrong: a tally of options is one series, so colouring each bar claims the
  options differ in kind when they differ only in count. Colour arrives with a second
  dimension instead, which is `?compare=<question id>`: pick a question whose answers
  split the room and every card draws one bar per group. Four hues, computed rather than
  chosen (the dataviz validator passes `#005eb8,#0d9488,#7c3aed,#b6357a` on the lightness
  band, chroma floor, CVD separation and contrast); a fifth candidate either read grey or
  took the amber, so a fifth group folds into a neutral "other". Colour follows position
  in the group list, never rank in a chart, so a filter never repaints the survivors, and
  every bar keeps its count as text because identity is never colour alone.
  That is why amber is rationed: `lib/flags.ts` is the only place a status colour appears
  on this page, and **a flag is a fact about the answers, never a judgement about the
  plant.** Two kinds only. Half the room declined, which holds for any question type; or
  a rating averaging in the bottom two steps of the app's own 1-5 scale. One line per
  question, refusal winning when both apply, so the strip and the tile counting it cannot
  disagree. The exclusions are the design and are the thing not to undo: **a number is
  never flagged**, because a chiller at 6C is a chill-chain breach and six years of
  service is not, and a question carries its text and its type but no safe range, so any
  threshold would be the app inventing a limit and attributing it to the survey (the day
  questions carry an author-set range, that is where the flag goes); and **a yes/no
  majority is never flagged**, because "was PPE available" answered no is bad and "did you
  have any problems" answered no is good, and only the question text separates them.
