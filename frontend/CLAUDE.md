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
- **`recharts` is the one charting dependency, and chart colour is validated, not chosen.**
  Series colours are `--series-1` to `--series-4` in all three token blocks of
  `globals.css` (light, dark by media query, dark by `data-theme`), checked with the
  dataviz palette script on 13 Sep 2026 against `--raised`. All four pass for adjacent marks
  (bars, stacks, lines). Only the first three pass for all-pairs forms in light, and no
  three pass on dark, so a scatter or small multiple uses one series and facets instead of
  seating more hues. Dark steps are their own values, not the light ones flipped: the
  light steps sat below 3:1 on the dark card. Colour follows the entity, never its rank;
  text wears text tokens, never a series colour.
- **Every lens chart has a table twin and its sample size.** `ChartCard` in
  `components/lens/Chart.tsx` gives each plot a subtitle naming n and a "Show as a table"
  view, because a tooltip must never be the only way to read a value. Below
  `TOO_FEW` (5) samples a chart says it is too few to read a trend from. The factor pages
  share one filter row, kept in the URL (`lib/lensScope.ts`), so every chart below it reads
  the same slice and a narrowed page can be linked.
- **One frontend test, by policy.** `tests/smoke.test.tsx` proves the harness renders and
  queries a component. The checks are `tsc --noEmit`, `eslint`, `next build` and `vitest`.
  A new test is written when something breaks, and it names that bug.
- **The lens is administrators only, and every figure on it is measured.** `/lens` lists
  traced runs under a strip of totals per tier; `/lens/runs/[id]` draws one run's spans as
  a waterfall, each bar placed against its own turn, with an attempt's time before its first
  token shaded. The link shows only when `/me` says `is_admin`, because the server refuses
  the reads to anyone else and half of that rule is an allowlist the browser never sees.
  `lib/lensFormat.ts` writes the numbers, and its rule is the thing to keep: **unknown is
  never zero**. A figure not reported reads "not reported", an unpriced cost "unpriced", and
  a sum over attempts that reported nothing "at least". Nothing on these pages is an
  estimate yet; when one arrives it has to say so beside the number.
- **Responses the lens renders numbers from are parsed at the boundary.** `lib/schemas.ts`
  holds zod schemas and the types are inferred from them; `parsed()` in `lib/api.ts` throws
  `ApiContractError`, naming the paths, when a response does not match. Lifted from the
  closed PR #65. Unknown keys are stripped rather than rejected, so an added field never
  breaks a page. The respondent pages still cast; move them across when they are touched.
- **A correlation is never a finding below 20 calls, and never a cause.** The Relationships
  page reads Spearman coefficients with a 95% bootstrap interval from
  `/lens/correlations`. Under the minimum a cell is outlined and uncoloured, and a side
  with no variation reads "no variation", not 0. Cells mix from `--div-mid` toward
  `--div-pos` or `--div-neg` by |rho|, a diverging pair with a neutral grey midpoint,
  defined in all three token blocks; text on a strong cell switches to `--on-slab`.
- **The prompt screen saves, it never switches.** "Save as a new version" adds the next
  version and changes nothing for respondents; only "Activate", confirmed by a second
  click rather than a browser dialog, makes a version live. The editor is keyed by version
  so opening another one mounts fresh state instead of copying text in an effect. Only
  the conduct prompt is editable here, by decision.
- **The embeddings page reads one survey, and says what the view spent.** `/lens/embeddings`
  needs a survey chosen in the filter row and ignores the run filter. Each report carries a
  cost block measured from the ledger (texts embedded now, texts read from the cache,
  tokens, cost, time), and the tiles sum the reports loaded, so a repeat view reading $0
  is the cache working. Themes and near duplicates wait for the answer map, so a fresh
  survey pays once for its texts instead of three reports embedding them in parallel. The
  reads are not retried: a 503 means embeddings are switched off, and the banner says so.
  The answer map is one series per question, faceted, with no axis units, because a
  projection's axes mean nothing. The grounding section needs no survey: it draws the
  committed measurement, the margins of the pairs the word check refused and the mistakes
  at each margin, both marked at the recommended margin.
