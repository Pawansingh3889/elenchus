# Changelog

All notable changes to the Elenchus Survey Service, from the first commit onward.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The project is not yet versioned, so entries are grouped by date. Newest first.

## 2026-09-21. Company-isolation foundation (working branch)

- Added workspace ownership to customer data, forced PostgreSQL row policies, and
  tenant-consistent parent references. Existing rows migrate to one explicit legacy
  workspace; multi-company downgrade is refused.
- Scoped prompt and embedding reuse, evaluation accounts, background work, traces, and
  file-ledger reads to the authenticated company. Unattributed legacy ledger entries
  are excluded from customer reports.
- Split migration and runtime credentials. Production refuses superuser, RLS-bypass,
  or object-owner runtime roles and tables without forced row security.
- Required a pre-linked Microsoft object ID, removing automatic account linking by
  mutable email. Google still requires an explicitly verified existing address.
- Added two-company regressions, migration/startup tests, and migration-only metadata
  so generated revisions preserve composite tenant constraints without changing ORM joins.
- Added explicit workspace roles, survey-scoped analyst grants, owner/admin-only assignment,
  and append-only access-change auditing. Legacy unlabelled accounts retain the job-based
  compatibility path until provisioning and backfill are complete.
- Added owner-configured response retention with confirmation for shortening, protected
  purge of response content and derived traces, deletion audits, and non-identifying
  monthly usage totals.
- Added workspace invitations and approved employee-roster records, one-time invitation
  token storage, and append-only access-change history. Verified-email redemption and
  account provisioning from those records remain open.
- Documented deployment limitations and recorded owner-only spending, audited
  owner/admin analyst assignment, and owner-configurable 90-day retention requirements.
- Not deployed or commercial-ready. Role authorization, retention, invitations, billing,
  disclosure, restore verification, and load testing remain release blockers.

## 2026-09-19. Commercial readiness contract and telemetry corrections

- Added `docs/COMMERCIAL_READINESS.md`, recording the pilot tenancy, verified-email
  eligibility, workspace role matrix, identified-response disclosure, allowance behavior,
  KPI definitions, spike detection contract, drilldown path, telemetry fields, and the
  proposed live evaluation envelope.
- Corrected production authentication so a known account id cannot substitute for a
  session, and constrained `APP_ENV` to `dev`, `demo`, or `prod`.
- Required Google sign-in profiles to report `email_verified` explicitly as true.
- Kept missing cached and reasoning token counts distinct from measured zero in the lens
  API and frontend, with regression tests for both cases.
- This is not a commercial-ready release. Tenant isolation, workspace roles, billing,
  allowance enforcement, invitations, disclosed transcript access, restore evidence, and
  100-respondent load evidence remain open as documented blockers.




## 2026-09-13. Evaluation: accuracy against cost, drafted scenarios and Qwen agreement

Phase 7 closes with what it was planned to give: accuracy per model against its cost and
latency.

- **Accuracy beside cost and latency.** `/lens/evaluation` reads completed evaluation runs
  by model and conduct prompt version: the share of runs where no hard check failed and the
  share of hard checks passed, each with a Wilson interval, beside the median cost per run,
  time and turns, and a matrix of each scenario under each group. Capped, failed and
  unfinished runs are counted as left out and never scored. On dev data that is one group,
  gpt-5.5 with `conduct_v8`, from the single `numbers_dates` run: 1 of 1 clean at $0.0853.
- **Broad and evasive run from the lens.** The two scenarios the harness drafts from a
  brief now run like the other nine. The pinned tier drafts the survey, the draft's cost is
  measured around it and charged to the evaluation row and the batch cap, and a draft that
  spends what is left stops as capped before any conversation starts.
- **Does Qwen disagreeing predict trouble?** Each stored Qwen reading is linked through its
  attempt to the engine's check and, for an accepted `record_answer`, to a person's label
  on the answer it recorded. The four readings in dev agree with gpt-5.5 on 2 of 4, all
  four calls were accepted and none is labelled, so every split reads too few or none yet.

## 2026-09-13. Evaluation: faithfulness, conversation quality and scripted runs

Evaluation asks whether what got through was right, where Validation shows what the engine
refused. A person's label is the ground truth; the judge model is scored against the labels
and never stands in for them.

- **Faithfulness.** `/lens/evaluation` queues recorded answers from the committed corpus
  (189) and from the database (139 in dev) beside what the respondent had typed, to be
  labelled supported, invented or unsure, with who and when. A database run can be judged
  on request with `judge_answers_v1` through a structured tool call, priced in the ledger.
  The report gives the invention rate and the judge's precision, recall and false alarms
  against the labels, by source, answer type and model, each with a Wilson 95% interval
  and marked too few below twenty. No answer is labelled yet, so every rate reads none.
- **How conversations went**, measured from what runs record with no model asked:
  completion, refusals, messages per answer, characters typed, minutes to complete, the
  wait for each reply, follow-ups and the new words they drew, and cost per completed run
  and per answer, by survey, model and prompt version. Two figures mislead on today's data
  and are read with care: cost per completed run is $0 because most runs predate the
  pricing fix, and the word-overlap measure of follow-ups is crude.
- **Scripted runs.** The nine scenarios from `scripts/live_conversation.py` now run from
  the page through the real engine, pinned to one tier with no failover and one conduct
  prompt version, under a spend cap for the batch that is read after every turn. Each
  builds a survey for an evaluation respondent who holds no job, so no reach count moves.
  An estimate appears only from earlier completed runs pinned the same way. The engine
  invariants moved into `app/conduct/invariants.py` so a run can check itself.
- **First real run.** `numbers_dates` on tier 1 (gpt-5.5) with `conduct_v8` and a $0.50
  cap completed in 15 s for $0.0853, reconciled across the run's rollup, its four priced
  calls and the evaluation row, and passed all nine hard checks: "the ninth of this month"
  stored as 2026-09-09, and "a couple, maybe three" and "eleven out of ten" refused rather
  than guessed. One run proves the path, not the cap: no real run has reached it yet.

## 2026-09-13. Inside a model: hidden layers, attention and token relationships

The hosted models expose no hidden layers or attention, so the lens now reads the exact
prompt a hosted call was sent with a small open model, Qwen3-0.6B, running on the host.
Every page says it shows that model's reading, never the hosted model's internals.

- **Exact prompts are kept.** Every traced chat attempt stores the messages, tools and tool
  choice it sent in `llm_requests`, deleted with the run. Calls before this release have
  none and are not read.
- **`interp/`** is its own service, pinned to revision c1899de and started with
  `make interp`. It needs `INTERP_TOKEN`, because the backend container can only reach it
  when it listens beyond localhost. The backend reaches it through one module and stores
  each result in `interp_analyses`, with a ledger row priced by wall clock like any local
  tier.
- **Reading and attribution are separate requests, each timed and priced.** On this
  laptop's CPU four gpt-5.5 calls of 3,326 to 3,481 prompt tokens each took 80 to 86 s to
  read ($0.0014 to $0.0015 of electricity at 200 W), where the hosted calls took 2.3 to
  4.2 s and cost $0.006 to $0.021. Attributing two of them took 229 s and 259 s ($0.0041
  and $0.0046). Reading the whole prompt with eager attention had taken 7.6 minutes and
  7.1 GB; the fused kernel with a short eager step brought it to 6.2 minutes and 4.8 GB.
- **`/lens/hidden-layers`** reads every layer through the model's own output head as a
  leaning between the offered tools, and marks the layer where Qwen settles. **`/lens/attention`**
  shows where the decision point looks, per part of the prompt. **`/lens/tokens`** shows
  gradient times input toward the hosted pick, per part of the prompt and for each word
  the respondent last typed. **Tool selection** gains how often Qwen picks the same tool.
- **First readings, on four calls.** Qwen picked the same tool as gpt-5.5 on 2 of 4, both
  `record_answer` (with 99.6% and 53.6% on it), and picked `reply` where gpt-5.5 called
  `flag_unanswerable` and `move_on`, giving those picks under 0.1%. At the decision point
  92.8% of the last layer's attention rests on the chat template's own tokens and 0.3% on
  the respondent's last message. Four calls demonstrate the pages; they do not measure
  agreement.

## 2026-09-13. Embeddings: answers placed by meaning, and grounding by a measured margin

Embeddings run through the same OpenAI-compatible client as every chat call, on hosted
`text-embedding-3-small`, and stay off until `LLM_EMBEDDING_ENABLED` is set with a URL, a
model and a price, which has no default. Every embed call is a ledger row with op `embed`,
priced per input token; the four made while measuring cost $0.0000234 together.

- **Vectors are cached, never the text.** `embedding_vectors` holds one vector per sha256
  of a text and the model, so a text is embedded once and a repeat view costs nothing.
  Withdrawing a run deletes the vectors of what it said, and two requests storing the same
  vector at once no longer collide on the unique key.
- **`/lens/embeddings`** reads one survey: an answer map per question placing each recorded
  answer by the meaning of the message that produced it, with its three nearest answers;
  themes in free text, grouped by spherical k-means and quoted by the answer nearest each
  group's middle; and near duplicates across runs at similarity 0.95 or more. Tiles above
  them show what the view spent, measured from the ledger: texts embedded now and read
  from the cache, tokens, cost and time.
- **Grounding by meaning, measured and switched off (O12).** With
  `GROUNDING_SEMANTIC_ENABLED`, a choice the word check refuses is accepted when it is the
  closest of its question's options to what was said, by `GROUNDING_SIMILARITY_MARGIN`
  over the runner-up. An absolute similarity threshold was measured first and rejected:
  the best one cleared the nearest wrong answer by 0.009. On 35 labelled pairs in five
  languages the word check alone accepts 5 wrong answers and refuses 13 real ones. The
  recommended margin, 0.021, is the middle of the gap between the highest refused wrong
  answer (+0.0007) and the lowest real answer above it (+0.041), and accepts the same 5
  while refusing 1. An embeddings outage leaves the refusal standing, and every similarity
  and margin is written on the validation span. The page draws the margins and the
  mistakes at each margin.
- **Two open defects the measurement found.** O13: a message under four content words
  skips the word check, so "i'm on the filleting line" grounds Dispatch as readily as
  Processing. O14: one shared word grounds its opposite, so "I loved the training" can
  record "No formal training". Both are wrong answers the word check itself accepts, which
  no margin reaches.

## 2026-09-13. Relationships: what moves with cost and latency, and a versioned conduct prompt

Three real surveys on AI problems and solutions around the world (healthcare in English,
jobs in Spanish, misinformation in German) were drafted through `gpt-5.5` and each
answered by two seeded respondents with different answer styles: 6 runs, 55 turns, 83
calls, $1.01. With the onboarding run that gives 93 traced calls, enough for correlation.

- **`/lens/relationships`** shows each factor of a call (tokens in, cached, out,
  transcript length, turn number, retry) against each outcome (wait for the first token,
  writing time, total time, cost) as Spearman rank correlations with a seeded 95%
  bootstrap interval, computed in plain Python in `app/trace/stats.py`. Below 20 calls a
  cell is shown for reference and never coloured. On the 93 calls: tokens out moves with
  the wait for the first token (rho +0.74, interval +0.60 to +0.85), cached tokens move
  against cost (-0.76, -0.82 to -0.65), and transcript length and turn number show nothing
  whose interval clears zero. Correlation, not cause, and the page says so.
- **The flow of asks** runs answer type, the tool picked, the check and what the ask
  resolved to as a Sankey with a table twin.
- **`/lens/chains`** lays out every question's asks in order per run, with the chain's
  time and cost, and which questions need the longest chains.
- **`/lens/compare`** puts two runs side by side, question by question.
- **The conduct prompt is versioned in the database as well as in files.** An
  administrator saves text from `/lens/prompts` as the next version (`conduct_v9`, then
  `v10`), never editing one, and activates any version from the next turn; rolling back
  is activating an older one. `prompt_versions` and the append-only `prompt_activations`
  log hold it; the engine resolves the live version once per turn, so every ask, ledger
  row, span and reply in the turn names the same one. Each version shows the turns, runs,
  median turn and cost traced under it. An identical save is refused, and only the conduct
  family is editable. `CLAUDE.md` records the change to the prompts-as-code rule.

## 2026-09-13. Four factor pages: inference, state, tool selection, validation

Each lens factor now has its own page, scoped by one filter row (a survey or a run, kept in
the URL), with every chart carrying its sample size and a table twin.

- **Inference** splits every call into the wait before its first token and the writing.
  On Rosa's completed onboarding survey (10 calls to `gpt-5.5`, $0.2031 in all), the
  median wait before the first token was 3,136 ms against 364 ms of writing.
- **State** plots input tokens by turn, one line per run with the run in focus
  emphasised, and tabulates what the engine knew at every ask. Input was 97% of all tokens
  on that survey. Decision spans now record the engine's state: answer type, follow-up
  policy, whether a follow-up was forced or awaiting a reply, whether an answer was already
  recorded or recorded this turn, and follow-ups and replies used. Flags and counts only;
  the engine's copy of a respondent's answer stays out, and a test pins that.
- **Tool selection** shows, per tool, how often it was offered, picked and accepted, and
  every ask with its cost. Confidence arrives with the local model.
- **Validation** shows refusals and what their own calls cost, and counts answers the model
  gave up as unanswerable, which the check accepts and which still lose an answer: a
  "decent, nothing special" on a rating went that way in the real run.
- **`GET /api/v1/lens/attempts` and `/lens/decisions`**, admin-only and filterable by
  `survey_id` or `run_id`, place each span in its run and turn. A decision counts only its
  own attempts, so a refusal's cost and its retry's cost stay apart. State fields are null
  on asks traced before they were recorded, which is unknown, not false. `AttemptRow` and
  `DecisionRow` join the access guard's types.
- **Chart colour is validated**: four series tokens per theme, checked with the dataviz
  palette script against the card surface in light and dark. Only the first three pass for
  all-pairs forms in light and none on dark, so the scatter is one series.

## 2026-09-13. The lens: every traced run, what it cost, and where its time went

The first page that puts cost and latency beside what explains them. Administrators only.

- **`GET /api/v1/lens/strip`, `/lens/runs` and `/lens/runs/{id}/spans`**, in a new
  `app/trace` router behind `require_admin`, with `is_admin` asked again inside the service.
  Spans hold refusal reasons that can quote a value a model proposed from a respondent's
  words, so `TracedRun`, `SpanRead` and `LensStrip` join the types `check_access_consulted`
  holds every service to, and `app/trace` joins the layering contract now that it has a
  router.
- **Totals are aggregated in the database** with `FILTER` and `percentile_cont`, so every
  figure is a sum or a percentile over the spans it describes: turns, asks, retries,
  attempts and failures per run; tokens in, cached, out and reasoning; cost; the wait a
  respondent had; and latency and first-token time at p50 and p95 per tier and model. A
  failed attempt has no first token, and the percentile skips it rather than reading zero.
- **`/lens` lists traced runs under that strip; `/lens/runs/[id]` draws the run as a
  waterfall**, each bar placed against its turn, an attempt's time before its first token
  shaded, and a click showing the span's figures and what the engine knew.
- **Unknown is never zero on the page.** A figure not reported reads "not reported", an
  unpriced cost "unpriced", and a sum over attempts that reported nothing "at least".
- **Lens responses are parsed with zod at the boundary** (`lib/schemas.ts`), lifted from the
  closed PR #65, and a response in the wrong shape throws `ApiContractError` naming its
  paths. The top bar shows the Lens link only when `/me` says the caller is an administrator.

## 2026-09-13. Every turn leaves a trace: what it asked, what each call cost, what was decided

The ledger could say what a run cost, never why. A turn whose cost doubled looked the same
as any other two-call turn, whether the second call was a planned move-on or a retry after
the engine refused the model's first answer.

- **New `llm_spans` table**, one row per span, linked by `parent_id` into a tree per
  respondent message: a `turn` span, a `decision` span for every ask of the model, an
  `attempt` span for every HTTP call to a tier (failed ones included), and a `validation`
  span for the engine's check of each action.
- **A retry nests under the ask it retries**, so its cost belongs to the refusal that
  caused it. A decision records the tools offered, whether it was a retry, and what it
  resolved to; its validation span records the tool the model actually picked, the
  outcome, and the refusal reason.
- **Attempt spans carry what the ledger row carries**: tier, model, status, error, the
  four token counts, first-token time and cost, so a page can read a tree with its costs
  without opening the file.
- **Spans are written in their own transaction**, after the turn commits or, when the
  turn fails, before the error leaves. A failed turn keeps the record of what it tried.
- **`run_id` and `parent_id` are indexed, not foreign keys.** The turn still holds
  `FOR UPDATE` on its run while spans are written, and a foreign key check would wait on
  that lock forever. Withdrawing a run deletes its spans explicitly for the same reason.
- **Collection lives in the ledger**, in context variables like its spend accumulator, so
  the transport records attempts without knowing which decision they serve. The ledger
  still owns no session: `tracing()` hands the spans back and the engine writes them
  through `SpanRepository`.
- Conduct turns only, for now. Summaries and drafting are measured in the ledger but not
  yet traced, and `app/trace` joins the layering contract when its router arrives with the
  lens pages.

## 2026-09-13. Every tier streams, and the ledger records when the first token came

A call's total latency hid where the time went. On a live `gpt-5.5` tool call the model
produced nothing for 3,393 ms and then wrote the whole answer in 96 ms: nearly all of the
wait was reading the prompt and reasoning, which no amount of shorter output would fix.

- **Every request streams with `stream_options.include_usage`**, and every ledger row
  carries `first_token_ms` beside `latency_ms`. The difference is time spent writing.
- **The stream is assembled back into the unstreamed body before anything reads it**, so
  tool-call validation, salvage from text, truncation and failover behave exactly as
  before. Text fragments are joined, tool-call arguments are rebuilt from their pieces.
- **A stream cut before its usage chunk still yields its turn**, and books the call as
  unmetered rather than free: OpenAI's docs say an interrupted stream may never send the
  counts.
- **A tier that ignores `stream: true`** and answers in one piece is still understood; it
  records no first-token time, since it has none to give.
- **A mid-answer hang-up stays a cheap, retried failure**, since holding the connection
  for the whole answer makes one more likely.
- An event that is not a JSON object fails loudly and is booked, like a non-JSON body.

## 2026-09-13. Cached and reasoning tokens are recorded, and cached input is priced

A turn's two token totals could not explain its cost or its latency. `gpt-5.5` bills a
cached prompt prefix at a tenth of the input rate, so a long prompt that was mostly cached
cost far less than its total says; and a short answer can take seconds because the model
spent them reasoning.

- **Every ledger row now carries `cached_tokens` and `reasoning_tokens`**, read from
  `prompt_tokens_details` and `completion_tokens_details`, the shapes OpenAI and
  OpenRouter send. A provider that reports neither records unknown, not zero.
- **Cached input is priced at `LLM_TIER<n>_PRICE_CACHED_IN_PER_MTOK`** where it is set.
  Unset, cached tokens pay the full input rate, which overstates a call rather than
  inventing a discount. A cached count larger than its own prompt is not trusted.
- **Reasoning tokens are shown, not charged twice.** They are already inside the output
  count the provider bills.
- The new setting is forwarded by all three compose files, with no default.

## 2026-09-13. An enabled hosted tier states its price, or the app does not start

No deployment had ever set a tier price, so 1,808 of the ledger's 1,841 calls were booked
as free: about 5.6 million tokens, roughly $18 at the providers' listed rates on this
date, $17.91 of it on `gpt-5.5`. Zero was both the price of a free model and the default
for a price nobody set, and the only signal was one warning per process.

- **Price settings have no default.** An enabled tier that is not local must state both
  its input and output price, or settings refuse to load and name the variables. `0` is
  still a price, so a free model loads.
- **The compose files stop defaulting prices to `0`.** A price nobody set now reaches the
  container empty, which settings read as unstated. Before, `:-0` answered the question
  for the operator and the refusal could never fire. `test_compose_settings.py` checks all
  three files and proves the check rejects a planted `:-0`.
- **The once-per-process "no price configured" warning is removed**, because the refusal
  replaces it. A call booked against an unpriced tier anyway records its cost as unknown,
  never zero, and counts as unmetered.
- **`.env.example` lists this date's listed prices** for the three tiers the chain
  describes, in place of a tier 1 example that still carried `gpt-4o-mini`'s rates.
- **Existing rows are left as they were recorded.** The ledger prices at call time by
  design, so history is not restated; the lens pages will mark those rows as unpriced and
  show an estimate beside them.

A deployment with an enabled tier and no prices (the local `.env` here, and
`docker-compose.prod.yml`, whose tier 1 defaults to enabled) will not start until the
prices are set.

## 2026-09-13. The browser becomes the respondent path

The frontend had grown to ten pages and about 14,700 lines around authoring, results and
administration. It is now the four pages a respondent needs. This is the first step
towards lens pages that show the model's workings (hidden layers, embeddings, attention,
state, relationship, inference, tool selection, evaluation, validation), each with its
cost and latency beside it.

- **Kept:** `/`, `/signin`, `/respond` and `/runs/[id]`. The home page says what the
  service is and offers one action.
- **Removed from the browser:** the dashboard, builder, Results page, people admin and LLM
  admin screens, with every component and library only they reached: 58 files. Every
  endpoint behind those screens is still served and still covered by the backend suite,
  so authoring is an API call now, and the README walkthrough shows it.
- **Tailwind, shadcn/ui, Radix, TanStack Table, cva, clsx, tailwind-merge and lucide
  removed.** The kept pages were already styled by `globals.css`, apart from three
  skeletons, two buttons, a card and the error banner, which now use plain classes. The
  element resets leave `@layer base`, which existed only so utilities could beat them.
  Runtime dependencies go from 17 to 6, and the lockfile loses 60 packages.
- **The Tailwind class guard goes with Tailwind**, from the Makefile, GitHub CI and
  Jenkins. It proved utility classes compile. With no utilities it would check nothing and
  still exit 0, which is the kind of gate this repo refuses to keep.
- **One frontend test remains**, the harness smoke test. The tally, units, query
  invalidation, draft questions and class guard tests went with the code they pinned.
- `lib/api.ts`, `lib/queries.ts` and `lib/types.ts` keep only what the respondent path
  calls: 12 endpoints and 13 hooks.
- **Verified:** `make gate` (1,059 passed, 84 skipped, and both CSS guards ran against the
  one stylesheet), and in a clean Node 22 container `tsc --noEmit` over 34 project files,
  `eslint`, `next build` (the four routes and nothing else) and `vitest`.
- **`globals.css` drops every rule that can no longer match: 1,796 lines to 1,122.** A
  selector naming a class no component carries cannot match, whatever else it says, so the
  cut was made by parsing the stylesheet rather than by hand: 102 rules, 110 selectors, two
  reduced-motion blocks and the modal's keyframes, plus the comments that introduced them.
  Every class a component names still has its rules. Checked by rendering the pages before
  and after: pixel-identical, apart from one survey row that had gained a Continue button
  between the two runs.

## 2026-08-17. The class guard reads the plainest way to write a class

It never had. The guard collects the regions of a file where a class may legitimately
appear and then pulls the quoted literals out of each one, but the `className="..."`
branch pushed its capture group, which is the text between the quotes. A region with no
quotes in it yields no literal, so every plain string className went uncollected from
the day the guard was written, and only `cn()`, `cva()` and `className={...}` were ever
checked.

- **The candidate count goes from 172 to 356.** The hole surfaced when a CSS-less name
  inside a `cn()` was rejected while the identical one in a plain string three files
  away had been passing all along.
- **Two dead marker classes removed rather than given a rule.** `results-controls` was a
  hook on the sticky bar that nothing selects, in the stylesheet or anywhere else, and
  `qcard-policy` was a hook on the builder's follow-up label that never had a rule in
  any commit; the label is styled by `.qcard-flags label` and renders the same without
  it.
- **`classNamesIn` is exported and pinned by `tests/classGuard.test.ts`**, with the scan
  behind an entry-point check so importing it does not run a second pass over the
  codebase. A guard is the one kind of code whose failure is silent: it goes on exiting
  0, and 0 is also what it says when it checks nothing. Watched it reject a planted
  `inset-inline-end-3` in a plain className, exit 1.

## 2026-08-17. The results page becomes something an author can read

Six changes to one page, which had been a column of full-width charts with no way to
narrow it, compare it, or tell where you were in it.

- **Compare by adds the second dimension, and colour arrives with it.** A hue per option
  was refused: a tally of options is one series, so colouring each bar would claim the
  options differ in kind when they differ only in count. Picking a question that splits
  the room turns "3 of 4 said yes" into "packing said yes twice, intake said yes once
  and no once". Four hues, computed and run through the validator rather than chosen; a
  fifth group folds into a neutral other rather than inventing a hue or borrowing the
  amber; every bar keeps its count as text, because identity is never colour alone.
- **A flag strip says which questions to read first.** Two kinds only, and the
  exclusions are the design: half the room declined, or a rating averaging in the bottom
  two steps of the app's own 1-5 scale. A number is never flagged, because a chiller at
  6C is a chill-chain breach and six years of service is not, and a question carries no
  safe range for this app to invent one from. A yes/no majority is never flagged,
  because "was PPE available" answered no is bad and "did you have any problems"
  answered no is good, and only the question text separates them. Two responses minimum.
- **The slicers moved into one sticky bar that says what it is doing.** Slice and compare
  used to scroll away, and a filtered number with no visible filter is how "3 of 4 said
  yes" gets quoted as the whole survey. One band under the title now, with a chip per
  active control, the compare legend beside the chip that created it, a live "N of M
  responses", and Clear as a single navigation.
- **Clicking a mark is a filter.** `?slice=` already existed, so a click on a bar, a
  donut segment or a legend group sets it and a second click clears it. The selected
  mark keeps its colour and the rest of that card steps back to a third opacity, on that
  card only. Write-ins are not clickable, because one person's words are not a group,
  and the keyboard path stays the control bar, because an SVG rectangle is not
  focusable.
- **The cards became a grid, and a long option list folds its zeros.** Eight questions
  measured 4429px at 1400x900 before, five screens, with a 654px bar drawn for a count
  of one. Two columns from lg up, each card choosing its own span from the data it
  holds, brings that to 3219px and clipped axis labels from 1 to 0. Zero rows fold
  behind a count past eight options, stated as "8 options nobody picked", which is
  arguably the better way to say it; rating never folds, because its five steps are the
  scale.
- **A rail lists the questions, and the sticky bar publishes its own height.** Eight
  charts with no contents list is eight charts you scroll blind. The rail marks the
  flagged questions so it and the flag strip cannot disagree, and scroll position
  decides which entry is current, so arriving from the rail, the strip or a pasted link
  lights the same one. The offset everything depends on is the bar's height, which runs
  from 61px to 101px as chips and a legend appear, so the bar measures itself and both
  the rail's sticky top and the cards' scroll-margin read the published value. The
  respondent table moved below the charts, and the page widened to 1280px, scoped with
  `:has` so the rest of the app keeps its reading measure.

Verified by rendering and measuring rather than by the checks, which is how three of
these were found: grouping read `run.answers[question.id]` when answers are a list, a
yes/no card kept drawing a donut while comparing, and the fold control was a bare
`<button>` that the unlayered element rule dresses as a raised pill. The narrow layout
below `lg`, where the rail is a horizontal row and does not stick, is unverified: the
test window would not resize.

## 2026-08-17. A probe that re-asks the question corrects the answer it re-asked

A follow-up is a question the model wrote, so its answer belongs to no option list and
is never counted. That rule is right, and it was wrong in one case: sometimes the probe
is the author's question re-asked with the options spelled out, and the reply is a
selection from the same set.

- **What it cost, from a real run.** Asked where product had been above the chill
  specification, one respondent gave a reading and a place not on the list, which became
  a write-in of the fragment "sat on the bay"; another gave "intake", a worse spelling
  of an option that was offered. Both were probed and both then named real locations.
  Filed as follow-ups, those were never counted, so the chart tallied zero for "Vehicle
  unloading at intake" while two of the three transcripts above it said otherwise.
- **Two conditions, and they are the whole rule.** The parent's vocabulary must be
  closed, because only then is the probe's answer a selection from the same set and only
  then does one of the two have to be wrong; on free text a probe elaborates, and
  replacing the answer with the elaboration would delete an answer to make room for a
  note about it. And the probe must have answered in that vocabulary, so prose under a
  closed parent stays a follow-up.
- **Correction replaces rather than merges**, because what the respondent settled on is
  the answer, and merging would leave the misparse on the chart beside the option it was
  a worse spelling of. The row keeps its `question_text`, which since versions were
  removed is the only record of what this person was actually asked, and the transcript
  keeps every word.

## 2026-08-17. The org chart fills out, and the People page draws who a survey reaches

- **The roster the plant actually has.** Supply chain arrives two deep, manager and
  head, because intake and dispatch are where a chill-chain problem becomes somebody
  else's problem. A factory manager joins as executive at head, which is what makes her
  the only person who can aim a survey at the heads of other functions. HR moves to
  head, since the office functions are one person deep and their lead is that person,
  and finance is a single director, deliberately alone.
- **The seed's own invariant caught the mistake in it.** Supply chain manager is an
  authoring band, and the test pinning "authoring bands carry a sign-in" failed until
  Sam got one.
- **The People page stopped promising an answer it left to the reader.** It said "who is
  on the plant, and which surveys can reach them" above a table of jobs. There is a grid
  now: function down, band across, people in the cells, and the chosen audience lit
  across it, so `operatives` is one cell, `qa` is a row, `managers` is everything right
  of a line, and `health_safety` is a function plus whoever carries the hat. The shape
  is the explanation, where a list of names says who without saying why.
- **Membership is never computed in the browser.** Each person arrives carrying the
  audiences that reach them, decided by the same `in_audience` call the denominators
  use, because a map drawn from a paraphrase of the rules drifts from them.
- **Two numbers that were one are now separate:** how many people an audience includes,
  and how many of those could actually receive a survey. Health and safety reaches two
  people, one of whom has no sign-in recorded, so the page says so and names him. While
  the floor has no way in, a reach number that ignores that overstates itself.

## 2026-08-17. Publishing freezes a survey, and only an unanswered one can be deleted

Asked for directly, a day after versions were removed, and the two are coherent rather
than contradictory: versions froze a copy while the draft went on evolving, and this
freezes the survey itself. Either way nobody's answer is re-pointed at a question they
were not asked. A survey that needs different questions is a new survey, which also
stops two sets of answers blending under one title.

- **Editing a published survey is refused, wholly**, where the rule used to cover the
  audience alone. Refining with the model is editing, so it is refused too, and the
  builder stops offering Save and Publish once a survey is live rather than offering
  buttons that can only fail.
- **Delete is permanent and therefore narrow.** The survey and its questions go, and it
  refuses the moment any run exists, of any status, because an abandoned
  half-conversation is still something a person said. The gate is the run count rather
  than the status: a draft nobody could answer and a published survey nobody did are the
  same situation. The builder prints the count as the reason instead of showing a
  disabled control that explains nothing.
- **Six tests described behaviour that can no longer happen and were removed**, and five
  more changed sides. Two of the removed ones were written the day before to pin the
  cost of live editing, which this freeze makes impossible.
- **Backups, on the 3-2-1-1-0 rule, since deletion is now real.** Continuous WAL
  archiving to encrypted object storage with a lock, a pgBackRest service that is inert
  until credentials exist, and a weekly restore test that asserts the schema matches the
  code and that the restored tables are not empty, because an empty restore succeeds
  quietly. `docs/BACKUP.md` says plainly that the bucket does not exist and nothing has
  been restored yet.

## 2026-08-16. A sign-in page, and pages that need you point at it

Signing in was a box in the top bar, which is the right size for a development shim and
the wrong size for the first thing a person does. There is a page now: it names the
service, offers the providers this deployment actually has, and says who to ask when it
will not let you in.

- **It cannot create an account, deliberately.** Every right here derives from a job an
  administrator assigns, and an account made by a first sign-in holds none: it sits in
  no audience, can be surveyed by nobody, and widens every denominator until somebody
  notices. An unknown address is refused with a sentence naming the fix.
- **The callback returns people to `/signin`** rather than the landing page, since
  somebody just turned away needs the reason beside the button they pressed. The top
  bar's duplicate copy of that error handling is deleted: both read the same query
  parameter and the top bar cleared it first, so the message rendered nowhere.
- **Pages that need a caller** (dashboard, people, builder) show a prompt that links to
  the page rather than a sentence telling the reader to find a control. A component
  rather than a redirect, so the address they asked for survives and the back button
  still means something.
- **Worth knowing rather than discovering:** this serves the ~50 office accounts with a
  provider login. The ~450 on the floor have no work email and no Microsoft account, and
  their way in is a break-room kiosk with a works number and a PIN that does not exist
  yet.

## 2026-08-16. Published versions are removed

Asked for directly. A survey had a draft and a stack of immutable versions; it now has
one definition, and publishing is a status change.

- **A run names its survey**, not a version of it, and the engine reads the questions and
  the setting at each turn rather than from a snapshot taken when the run started.
- **Every run counts in the report.** Runs that answered earlier wording used to be
  excluded and counted separately, with a line on the page and a clause in the recap's
  caveat saying so. There is nothing to exclude now, so both are gone.
- **`published_at` and `published_by` move onto the survey**, set once on the first
  publish, so "when did this go out and who sent it" survives the versions that used to
  answer it.
- **`snapshot.py` becomes `reading.py`.** It existed so that no reader had to guess what
  a missing field in a frozen document meant; it now builds the same shape from the
  question rows, and its tests were rewritten to pin the shape rather than the JSON.
- **The publish dialog stops promising a freeze.** It now says that later edits change
  the survey for everyone, including anyone part-way through, because they do.

Four tests changed sides rather than being deleted: they asserted the guarantee that has
been given up, and now assert what happens instead, so an author editing a live survey
mid-run is a documented behaviour rather than a surprise. The cost of the whole change,
including that a stored recap can now outlive the questions it described, is written up
in CLAUDE.md.

## 2026-08-13. The generator is held to the brief's question count

Defect O2, live twice: asked for exactly 10 questions, the model returned 11, and the
draft was persisted as if that were what the author wrote. The count is now a bound
rather than a hope, closing the defect as row 30.

- **Parsed conservatively from the brief.** Only an unambiguous exact ask binds:
  "exactly 10 questions", "a 10-question survey", "ten questions". Softened ("about
  10"), ranged ("8-10", "between 8 and 10"), scoped ("2 questions per shift", "the
  first 3 questions") and conflicting counts stay advisory, because a false bound
  rejects drafts the author never asked to constrain, while a missed one just leaves
  today's behaviour.
- **Pinned in the tool schema** as `minItems`/`maxItems` on the questions array, where
  a constrained decoder can hold the model to it before a wrong draft exists.
- **Enforced by the validator either way**, since not every provider honours those
  bounds: a draft with the wrong count burns the one retry with an error naming both
  numbers, and a second miss fails loudly rather than persisting.
- **A count past the cap is the author's problem, said immediately.** A brief asking
  for 30 against the cap of 20 could only ever fail after two paid model calls, blaming
  the model for the brief. It is refused as a 422 before any call is made.

The other half of O2, open questions drafted as four-option selects, is not fixed but
superseded: drafting free text has since been banned deliberately, and the write-in is
the mechanism that carries what an option list cannot anticipate.

## 2026-08-13. Playwright leaves the repo

The browser suite was one smoke spec asserting the landing page's copy, and it cost
more than it caught: it sat red for five hours on a copy change, the dev image cannot
install its browser libraries at all, and CI paid a two minute browser download on
every push to run it. Removed rather than fixed: `frontend/e2e/`,
`playwright.config.ts`, the `@playwright/test` dependency, the `test:e2e` script and
both CI steps. The `shot.mjs` screenshot helper goes with the dependency it imported.
Rendering is still verified, but by looking at the rendered page rather than by a
runner; vitest, `tsc`, `eslint` and the Tailwind class guard are unchanged.

## 2026-08-13. The recap gets a fixed short shape

Asked for directly: a survey recap the author can trust to read the same way every
time, short enough to take in whole. One headline sentence, at most three findings with
their counts attached from the report, and one caveat line.

- **Findings cap drops from six to three**, and the writer is told the ranking is the
  job: with three slots, a finding that restates one bar chart is a wasted third.
- **Quotes leave the survey recap.** The per-run summary keeps its verbatim quotes and
  their grounding gate; the report's question cards still carry every answer in full.
  A side effect worth naming: the who-said-what roster no longer travels to the
  provider at all on this path.
- **The caveat is the engine's, never the model's.** Computed from the report and
  stored with the recap: who answered of how many, how many answered an earlier
  version, which question was mostly declined. The one line that qualifies the
  findings cannot itself be a model's claim.
- **Old recaps read as outdated rather than mis-rendering.** The prompt version joins
  the reuse condition, so a document written under the old shape invites a fresh recap
  instead of being served into a page that renders today's. Prompts move to
  `summarise_survey_v2` and `verify_survey_summary_v2`.

## 2026-08-13. One job per person, and the org chart becomes the access model

The plant's own hierarchy said the old model was wrong: the membership table happily
recorded a line leader who was also QA, a job that does not exist, and the stored role
column both duplicated and contradicted it. Rebuilt after looking at how this is done
elsewhere (NIST RBAC's role hierarchies and separation-of-duty constraints, ordinary
job-architecture practice, and the food industry's requirement that QA stands apart
from production): every person now holds exactly one job, and every right derives.

- **`function` x `band`, plus hats.** Ten functions (production, quality,
  health_safety, technical, planning, hr, finance, supply_chain, it, executive), six
  ordered bands (operative, line_leader, supervisor, manager, head, director), and a
  hats table for cross-cutting duties, H&S first: a supervisor with H&S responsibility
  keeps their production job and carries the hat. One job per person is a schema fact,
  so the impossible overlap cannot be recorded again.
- **`role`, `department` and `user_group_memberships` are gone.** Authoring is manager
  band and up; admin is the IT function or the allowlist; `microsoft_id` is a sign-in
  method and decides nothing. The admin screen writes jobs and hats, the reach preview
  warns on the edits that move denominators (band and hat changes now), and old audit
  rows keep their old vocabulary because history is served as written.
- **Audiences derive from the job.** The production audiences are that ladder's bands,
  `qa` is the whole quality function, the new `health_safety` audience is the function
  or the hat, `managers` is the band anywhere, and `everyone` is anyone with a job,
  which now includes the office, decided knowingly: a finance manager was never
  honestly outside an all-staff survey.
- **Sharing rules settled and pinned.** Colleagues are the authoring bands of one
  function, symmetric, office functions silo'd; the executive function reads every
  survey and its results and edits none of them; the audience's own seniors do not
  read surveys aimed at their team, so HR can survey a team candidly about its own
  management. Colleague results-reading had actually been dormant (the rule existed
  and its call site never passed the department); it is wired and tested now.
- **Migration with a remap, not a reset.** Seed accounts map by email to their new
  jobs, stranger rows map by deterministic rules (authors by department at manager
  band, respondents by their highest group), Adaeze's local IT grant survives, and the
  seed grows a floor H&S manager (Hana) and a ground QA (Noor) on fresh c-block ids.

## 2026-08-13. A refine no longer discards what the model was never shown

Found by a live end-to-end run rather than by the suite: the first refine of the
traceability survey came back with its setting deleted, and kept its audience only
because the description happened to mention the QA team. The refine brief deliberately
omits both fields, but the tool schema still carries them, so the model returned
guesses and `update_draft` wrote them through: the show_when loss again, one shelf over.

- **`refine_draft` restores `audience`, `audience_user_id` and `setting` from the
  stored draft** after the model answers, the same ruling `generate_draft` already
  makes for the author's audience. A wrong guess can also no longer trip the
  published-audience guard, which used to fail the whole refine as a 409.
- **`_describe` now names its deliberate exceptions** and why their remedy is carry-over
  rather than description: they are the author's decisions, not prose to revise, so
  showing them to the model would only invite it to change them.
- **`update_of` in the test builders carries `setting` and `audience_user_id`**, so a
  test changing one thing cannot quietly clear another: the same mistake the app-side
  builder made once, waiting in the test helper.
- Four tests pin it: the setting kept, the audience kept against a guess, a person
  target kept as a pair, and a refine of a published survey surviving a wrong guess.

## 2026-08-13. Reach stays live, and gets witnesses instead of a freeze

A survey's denominator follows its group: somebody hired Tuesday is asked Monday's
survey, and every reach number moves when membership does. That was confirmed as the
intended design, against snapshotting membership at publish, and this work makes it
honest rather than surprising. Open-source authorization engines were evaluated first
and none adopted: Oso's library is deprecated, the Zanzibar family and Cerbos are
always-on services this stack has a decision against, and pycasbin would swap the
readable, reasoned access rules for a policy DSL while providing none of what was
actually needed, which is change-management around the data those rules read.

- **The publish confirmation counts.** Beside who the survey is for, it now says "2
  people can answer it right now", from a new author-side reach endpoint that asks the
  same rule the dashboard and report already ask. Live, and phrased so.
- **An admin edit warns before it moves a denominator.** Saving a change that would flip
  a person in or out of any open survey's audience first shows those surveys with reach
  before and after, and Save becomes "Save anyway". Warn, never block: people genuinely
  leave teams, and a reach dropping is then the truth.
- **Every account change is recorded.** `account_changes` is append-only, written in the
  same transaction as the create or edit it records, with before and after snapshots.
  The edit dialog shows the recent entries, so "why did this number move" is answered
  where the mover is standing. Seeded and Entra-provisioned accounts have no rows,
  which is itself information: nobody in the app did it.
- **The pool is sized for break-time.** The plant answers surveys in bursts, a shift at
  once, and each live conversation holds a database connection across its LLM call. The
  SQLAlchemy defaults queued half of a thirty-person break into 30-second timeouts;
  `DB_POOL_SIZE`/`DB_POOL_MAX_OVERFLOW` now default to 10+30, are forwarded through
  compose, and none of the new endpoints sit on the respondent path that burst travels.
- **Quality and shift managers exist.** A `quality` office department and a
  `shift_managers` floor group with its matching audience, in the enums, the access
  map, both pickers, all eight locales, and the seed: Quinn (Quality, and QA on the
  line), Rina and Rohan. Two ids first chosen for the new seed users collided with
  rows an older seed generation left behind, which silently handed the new group to
  two bystanders; the seed now takes fresh ids, refuses an id whose email disagrees,
  and a test pins that SEED_GROUPS can only decorate SEED_USERS.

## 2026-08-13. Somebody can be given an account, and told what they are

Until today `users.role` was written by the seed script and by nothing else, so the real
answer to "who decides who can be an author" was "whoever can reach the database". That
also left the plant unstaffable: an account in no group can be asked nothing at all, not
even a survey aimed at everyone, and there was no way to put anybody in one.

- **`POST` and `PUT /api/v1/admin/users`**, behind a new `require_admin`. It asks
  `is_admin` and so never consults `role`, deliberately: an administrator whose own
  account is a respondent must still reach the screen that would fix that.
- **`/people` is that screen.** An administrator gets an "Add person" button and a per-row
  edit; everybody else sees exactly the table that was there before. Hiding the controls is
  a courtesy, not the enforcement, and the page asks the server whether it is talking to an
  administrator rather than guessing, because half of `is_admin` is an email allowlist that
  never leaves the server.
- **`users.created_by`** records which administrator made each account. Null for everyone
  the screen did not make, which is every account that exists today and every account a
  real Microsoft sign-in will provision.
- **Four shapes of account are refused**, each named after the row the access rules would
  otherwise misread. The one worth knowing is a respondent holding a department: that would
  make them a colleague of that department's authors, and a colleague may read every
  individual answer.
- **An administrator cannot edit away their own administration**, because from that state
  nobody inside the app can give it back.
- **`role` is stored as sent, not derived from `microsoft_id`.** Chosen knowingly, against
  the direction recorded in the model: an author created without an Entra id will stop
  being one the day sign-in derives the role from it. The form sets that id and the
  directory badges the authors missing one, but nothing enforces the pair.

### A browser could not get in at all

Found while using the above, and older than it. `GET /api/v1/users` was hardened to
require a caller, and under the header shim a caller is an id, and that list was the only
place to get an id. So a browser with empty storage was locked out permanently: the picker
had nothing in it, and every page's advice to "pick a user in the top bar" was advice
about an empty dropdown. Only an id left over in localStorage from an earlier session hid
it.

- **`POST /api/v1/dev/identify`** trades an address for an id, and the top bar shows a
  sign-in box while nobody is selected. Deliberately an address rather than a list: the
  list is what needs a caller, and handing it out unauthenticated would hand out every id.
  Knowing somebody's address is now enough to act as them, which is the whole of the
  authentication story until a real provider replaces `get_current_user`, so the endpoint
  is registered only outside production. A test asserts that mounting, because the mount
  is the protection.
- **The advice now matches the control.** All four "pick a user in the top bar" strings
  and the landing hint say sign in, in all eight locales.
- **The cold load no longer fails a request on purpose.** `useUsers` did not wait for an
  id, so every signed-out page spent a request to be told 401 and left a real error in the
  dev overlay of a page that was working.
- **A new account appears in the picker immediately.** The account mutations invalidated
  the directory and the dashboard but not `["users"]`, which backs that picker and the
  author nav, so somebody just created could not be switched to until a hard reload.

## 2026-08-09. The live check audits itself, and stops forgetting

Yesterday's invented `yes` was found by a human reading a transcript, and could not be
reproduced against a real model minutes later: the model answered in words the second time.
Both halves of that sentence are problems. This fixes both.

- **Every run audits itself.** A second model pass reads the finished transcript and judges
  each recorded answer against what the respondent actually typed. It calls the provider
  directly rather than through our API, because a second opinion routed back through the
  engine it is auditing is not one. Replaying yesterday's transcript, it flags the invented
  `yes` and passes the four sound answers.
- **Its verdicts are soft**, printed and excluded from the exit code, for the reason already
  written above the checks: a judge is a model, and a build that goes red on judgement
  teaches people that red means nothing. `--strict-judge` promotes them once we know how
  often it cries wolf; `--no-judge` buys a cheaper run.
- **Two false-positive classes turned up while building it**, both fixed in the prompt and
  both worth knowing about, because they will recur if it is retuned. `unanswerable` is
  judged by the opposite test to a value: it records that someone did *not* answer, so a
  refusal supports it, and the first draft flagged three correct refusals while giving
  reasons that argued for them. And normalisation is not invention: a date is stored as ISO
  and a rating as an integer, so the stored value shares no characters with what was typed.
- **Every run is now written down.** Each conversation lands in `backend/tests/live_runs`
  as a fixture, captured turn by turn so each answer carries the messages the grounding
  gates actually saw when it was recorded. A run-wide snapshot taken at the end could not
  replay a yes/no, which is judged on the latest message alone.
- **The mocked suite replays the saved runs on every push**, free and without a key, in two
  directions. Every answer a real model produced and the engine accepted must still be
  accepted, which is what catches a gate tightened too far. And any answer a human has
  marked `"invented": true` must be refused, which is how a live finding becomes permanent.
  The judge's verdict is recorded in each fixture for a reader and never used as ground
  truth, because it is a model too.
- **Pull requests touching the conduct engine, the answer gate or the prompts** now run two
  scenarios automatically, one scripted and one prompt-generated, roughly a tenth of the
  calls of a full sweep. The `generate` shape crash sat in main precisely because nothing
  ran this on a change. CI keeps each run's transcripts as an artifact; nothing is committed
  from CI, because a run that lands in tests/live_runs unread is one nobody has judged.

`make gate` clean, 373 tests.

## 2026-08-08. A yes nobody said, and the live check that could not reach it

Both of these came out of running the live check against gpt-4o-mini rather than reading
it. The mocked suite cannot find either: one is a real model's judgement, the other is a
crash in the check harness itself.

- **A yes/no can be invented too.** Asked "Would you recommend the new handover process?",
  a respondent sent the single message `4` and the engine recorded `yes`. The grounding
  gate added on 7 Aug covers free text only, on the stated reasoning that free text is the
  only shape that can be invented wholesale. A yes/no is the cheaper invention: two values,
  one of them right by luck half the time, and it renders in the author's results as a
  recommendation nobody made. Recording a boolean now requires the respondent's latest
  message to contain letters.
- **Judged on the latest message, not the run.** `ungrounded_text` pools every message the
  respondent has sent, which is the right leniency for prose the model merges across turns.
  It is useless here: every respondent types words eventually, so a run-wide check passes
  the moment anyone says anything, and this exact failure would go through it.
- **"Any letters", not "any content word".** `_content_words` keeps only words longer than
  two characters. Reusing it would refuse a plain `no`, and refuse every yes and no in
  Chinese and Japanese, where each is a single character. In a service that conducts in
  eight languages that is the expensive way to be wrong.
- **The live check could not run its two prompt-generated scenarios.** `POST /templates`
  answers with the template; `POST /templates/generate` answers with `{"template": ...,
  "note": ...}`. `build_survey` read both as the same shape, so `broad` and `evasive` died
  on `KeyError: 'id'` before their first question. Since the live-conduct workflow defaults
  its scenario input to `all`, its default invocation crashed at `broad`, after paying for
  the eight scripted scenarios ahead of it. Both now run clean.

`make gate` clean, 361 tests.

## 2026-08-08. The local model tier removed, and two hosted backstops turned on

The stack ran its own Ollama as tier 4, the backstop reached only when all three hosted
tiers failed. It is gone. Three hosted tiers already cover failover, and carrying a
fourth cost 1.9 GB of model weights, a container in every `compose up`, and a cold-load
penalty severe enough that it was the sole reason tier 4's timeout was 300s.

- **Removed from both compose files**: the `ollama` service, the `ollama-pull` job that
  fetched the weights, and the named volume that kept them. `docker-compose.gpu.yml` and
  `docker-compose.gpu-wsl.yml` went with them, since accelerating that one service was
  the only thing either file did.
- **Tier 4 survives as an empty slot**, off by default and pointing nowhere. Removing it
  outright would have been the larger change and bought nothing: the tier is only a base
  URL and a model id, so any OpenAI-compatible server can take the slot from `.env` with
  no code change. What went is the service, not the capability.
- **Groq and OpenRouter are enabled** as tiers 2 and 3. Failover that exists but is never
  reached is not failover: with one tier enabled the chain does nothing at all, and
  removing the backstop without turning these on would have left OpenAI as a single point
  of failure for every conducted survey.
- **Tier 4's economics now default like every other tier's**, hosted and unpriced,
  rather than describing the 3B local model that used to be wired into it. Anyone
  filling the slot with a model they serve themselves has to say so, because a local
  tier bills no tokens and is priced from wall clock instead.
- **The compose check that guarded this inverted.** It asserted tier 4 was marked local,
  the risk then being that a tier billing no tokens would record as free. With nothing
  served locally the risk runs the other way: an inference service comes back and the
  pricing question goes unasked. It now rejects any tier defaulted to local without the
  wall-clock inputs to price it, and carries a planted violation of its own, because the
  condition is unreachable against the files as they currently ship.
- **The suite had been leaning on that default.** Six tests asserted spend reaches a run
  by way of tier 4 being local out of the box, which is a test depending on a shipped
  default rather than on what it means to test. The assumption is now stated once in
  conftest.

`make gate` clean, 356 tests.

## 2026-08-07. What every call costs, an answer you can take back, eight languages

Most of this came out of a review of the OpenAI-only migration. The migration itself
was sound; what it had quietly dropped was not, and three of the entries below are
guarantees the vendored SDK used to provide that nothing replaced.

- **A spend ledger.** Every model call appends one JSONL line: tier, model, parameter
  count, tokens, latency, status and cost, with the same figures rolled up onto
  `survey_runs`. The rollup is denormalised on purpose, because a request should not be
  parsing a telemetry file to answer what a conversation cost. Unknown is not zero: a
  provider that reports no usage increments `llm_unmetered_calls` rather than folding
  into the sums, so a total can honestly say "at least". Cost is `Numeric(18, 8)`,
  being money that gets summed across runs. A local tier bills no tokens but costs the
  machine while it runs, so it is priced from wall clock against `hardware_watts` and
  `electricity_price_per_kwh`; reporting a locally served run as free is the one number
  that is certainly wrong. Parameter count is configuration because no provider reports
  it, and it is the axis the measurement turns on.
- **Three guarantees restored** to the OpenAI-compatible client. The old client sent
  `disable_parallel_tool_use` on every turn; the replacement asked only for
  `tool_choice: required`, then read `tool_calls[0]` and discarded a second call in
  silence, so a respondent's answer could vanish. `max_retries=2` disappeared with
  nothing in its place, and cross-tier failover is no substitute: it does nothing at all
  when a single tier is enabled. And every error path raised before reaching the ledger,
  so the calls most worth measuring left no row. `NoToolCallError` also no longer
  cascades through the chain, because a model that merely chatted is not a downed
  provider and the engine already answers it with one nudged retry.
- **Taking back the last answer.** `POST /runs/{run_id}/rewind` removes the most recent
  scripted answer, its follow-ups and the transcript from that turn on, then refunds the
  probe and reply budgets of that question *and of every question after it*. Refunded
  rather than carried forward, because an answer worth probing deserves the probes the
  first one spent, and budgets spent on later questions during the deleted turns would
  otherwise stay charged while the transcript that spent them was erased. The endpoint
  takes no body: which answer this is, is the engine's to decide.
- **A different set of languages.** The picker now offers en, es, de, pl, lv, lt, ro and
  fil. The retired tags stay in the backend catalogue, because `survey_runs.language` is
  fixed when a run starts and a run already under way in French has to be finished in
  French; deleting those messages would have stranded every run begun under the previous
  roster. `SUPPORTED` is what the picker offers, `SERVED` is what still resolves.
- **The `create_all` guard could not see the async idiom.** It flagged the call form
  only, so `await conn.run_sync(Base.metadata.create_all)` passed straight through, and
  this repository's own conftest built the test schema exactly that way. The suite was
  testing the models rather than the migrations while the gate that exists to forbid
  that reported ok on every run. The planted violation had paired the async idiom with a
  direct call, so the gate was catching the pair for the wrong reason; it is now planted
  alone, which is what makes the test mean anything. conftest builds the schema with
  `alembic upgrade head`, and points the ledger at a temp file so the suite stops
  writing invented calls into the record real runs are measured in.
- **A probe's answer could be stored as the wrong thing.** On a select with
  `allow_other`, `validate_answer` accepts any non-empty string as a write-in, which made
  the prose path unreachable: free text was recorded as an option the respondent had
  supposedly picked. A prose string now counts as a re-ask answer only when it names an
  actual option.
- **Interface.** The composer and the builder's option rows grow with what is typed
  instead of scrolling it out of sight. Enter no longer sends mid-word: CJK and Indic
  keyboards use it to commit a conversion candidate, so every Enter had been submitting
  a half-composed answer. Renaming an option no longer destroys the conditions naming
  it, repair having run on every keystroke and cleared them at the first one that
  stopped matching, with no way back once the author finished typing.
- **`compose up` no longer waits on the model pull**, revising what the 6 Aug entry
  below says. Gating the API on a multi-gigabyte download put it on the critical path of
  every start and left anyone offline unable to reach template CRUD, which needs no
  model at all. Until the pull lands, tier-4 calls surface as `llm_unavailable`, which is
  the honest state of the system.
- **The prod overlay booted green and 503'd on every call.** It defaulted
  `LLM_TIER1_ENABLED` to true while `LLM_TIER1_MODEL` defaulted to empty, unmentioned in
  the file's own list of required variables. It now carries a model that works.
- **`make test` had been broken** since the Makefile was pointed at a `scripts/test.sh`
  that was never committed. The script is now in the tree, and fails with the cause when
  Postgres is not up rather than with 200 connection errors halfway through.

### Then a review of all of the above, and of the code it landed on

Three of the findings reached a running deployment, so they were fixed the same day. One
of them was caused by the work above:

- **The failover carve-out was made unconditional**, and justified by a nudged retry that
  only the conduct engine has. `tool_turn` has three callers: template drafting retries
  only on a validation error, and run summarising only on a Pydantic one, so both went
  from falling through to the next tier to raising on the spot. On a fully configured
  chain, an author pressing Draft with AI or Summarise while the tier-1 model answered in
  prose got a 503 with three healthy tiers never tried. Whether a chatty turn should cost
  a tier depends on whether the caller will retry, which only the caller knows, so it is
  now theirs to say. A tier that is genuinely down still cascades either way, because a
  nudge cannot revive a provider that is not answering.
- **A missing prompt file accused the database.** `load_prompt` raised
  `FileNotFoundError`, which is an `OSError`, which the handler for a departed Postgres
  renders as "The service cannot reach its database right now". Renaming a prompt
  answered every respondent turn that way while `/health` went on saying "ok". It now
  raises a typed `PromptNotFoundError` and reads as the 500 it is. The guard meant to
  catch this before runtime could not see it either: it resolved `PROMPT_VERSION`
  constants only, and three call sites name their prompt inline, so a rename left the
  gate green and broke the conversation at the one moment that costs money to discover.
- **The ledger's prices never reached the container.** Compose reads `.env` only to
  interpolate its own `${...}`, so a service sees exactly the variables its `environment`
  block names, and both files stopped at the connection settings. Every price documented
  in `.env.example` was set by the operator and dropped at the container boundary, so a
  deployment paying a real provider recorded every call as free, unfixable after the fact
  because the ledger prices at call time rather than recomputing. That block is a
  hand-maintained copy of part of `Settings`, so a test now asserts the copy is complete.

339 tests.

## 2026-08-06. Architecture rules made executable, and the gates proven

Adopted from a sibling project, whose Makefile states the principle: a gate that
has never been observed to reject anything is decoration.

The layering in CLAUDE.md was true only by review. It is now enforced:

- **Import contracts** (`lint-imports`). Inside every domain, imports point downward
  only, router to service to repository to models. `service` and `models` are optional
  layers because app.conduct keeps its logic in engine.py and app.users has no service;
  a layer that is absent is skipped, a layer that exists is ordered. A second contract
  keeps transport in one module: nothing above `app.llm.openai_compatible` may import
  httpx, urllib, socket or requests directly.
- **Guards** (`backend/scripts/`), for the rules a contract cannot express. Only
  repositories may import the query surface, meaning select, func and selectinload,
  while a router naming AsyncSession for its dependency is fine and always was; that
  distinction is below module granularity, and import-linter cannot forbid a subpackage
  of an external package. Alembic owns the schema, so `create_all` is rejected in app
  code and in tests. Prompts must be named `<name>_v<N>.md`, and every PROMPT_VERSION
  constant must resolve to a file that exists, which otherwise fails at the one moment
  a model is called.
- **Proof that each gate works** (`tests/test_gates.py`, 15 tests). Each guard is run
  against a clean fake repository, against one with exactly one planted violation, and
  against an empty directory. The third case is the one that hides: a naive checker
  walks no files, finds nothing, and exits 0 having verified nothing at all.
- **`make gate`**, which is exactly what CI runs, and the repo's first Makefile.

227 tests.

## 2026-08-06. Ported from glance: summary verification and the local tier

The glance project is a parallel build of this same service. Three pieces of it were
worth taking, and were taken rather than reinvented:

- **A checker on the run summary.** The schema and the verbatim-quote gate cannot
  decide whether the headline and key facts are *supported* by the answers; a rule can
  prove a quote verbatim, only a reader can notice a fact the respondent never gave. A
  second call now reads the draft against the same extract the writer was fed, blind to
  how it was drafted, and either passes it or sends it back once with notes. Refused
  twice is a 502 and nothing is stored. The verdict is itself schema-gated: unfaithful
  while naming no problem is invalid, because it cannot be redrafted against.
- **A local Ollama as tier 4.** The tier was configurable but unreachable, so the last
  resort in the chain was decorative. Compose now runs its own, with a healthcheck that
  asserts the model is pulled rather than that the server answers, and the model kept
  resident server-side because the /v1 OpenAI shim does not reliably honour a per-request
  keep_alive. The backend waits on the pull, so a fresh machine downloads weights before
  the API accepts traffic.
- **GPU overrides and a deployment compose.** Two GPU files, because Docker Desktop on
  WSL2 has no nvidia runtime and needs /dev/dxg mapped instead. The prod file pins images
  by digest, keeps Postgres off the host interface, refuses to start without a password,
  and skips the seed. Its header states plainly that auth is still the X-User-Id shim, so
  the stack is not fit for the public internet.

Deliberately not taken: glance's `incidents` and `ask` domains, the first already dead in
glance and the second specific to a factory floor. Its `sample_data` package needed no
porting, this repo having the same one already.

## 2026-08-06. One provider protocol: the Anthropic path removed

The Anthropic key had been blank for a while, and the factory only ever built that client
when a key was set, so in practice every turn was already served by an OpenAI-compatible
tier. This makes that the design rather than an accident:

- `LLMClient`, the Anthropic SDK wrapper, and the `anthropic` dependency are gone.
  `app/llm/client.py` now holds only the contract every client satisfies: the typed
  errors, the one-turn shape, and the protocol. `backup.py` became `openai_compatible.py`
  and is the single client, reached over `httpx`.
- The chain is now four ordered tiers: OpenAI, Groq, OpenRouter, then a local Ollama.
  `LLM_BACKUP*_*` became `LLM_TIER1_*` through `LLM_TIER4_*`, since nothing is a backup
  once there is no primary. Tier order is positional: disabling one promotes nothing.
- With no tier enabled the factory now raises rather than returning a client that fails
  later, further from the cause.
- A turn cut off at the token limit raises `TruncatedTurnError` instead of arriving as a
  retryable `NoToolCallError`. Only the Anthropic client had ever made that distinction,
  and retrying a truncated turn at the same budget stops in the same place. Salvage still
  runs first, so a call that completed before the cut-off is used.
- `test_llm_client.py` is deleted along with the SDK path it exercised. 207 tests pass.

## 2026-08-05 — Client branding removed from the code and from history

The trial ended on 28 July and the client asked that their branding and template styling
not travel with the code. Removed from the working tree **and rewritten out of all 120
commits**, so no earlier revision carries them either:

- `DESIGN.md` and `reference/survey_builder_demo.html`, the client's visual language and
  builder mock, deleted from every commit that ever held them.
- The colour palette, replaced token by token with neutral values.
- The client's typeface, replaced with a system font stack.
- The palette's variable names, which were taken verbatim from the client's design
  document, renamed to semantic ones (`--ink`, `--canvas`, `--surface`, `--muted`,
  `--accent`, `--accent-strong`, `--highlight`, `--border`).
- The product name in the page title and top bar.

The rest of the brief pack is kept: it records what was asked for, and carries no styling.

## 2026-08-05 — Cleanup pass

No behaviour change. A sweep for things the repo was carrying but not using, and for
knowledge written down in more than one place.

### Removed
- **Misfiled steward pilot docs.** `docs/steward-pilot-plan.md` and `docs/steward-pilot/`
  (841 lines) were operational materials for a different project. Nothing linked to them.
- **create-next-app leftovers.** The generated `frontend/README.md` documented npm, yarn
  and bun against a pnpm repo and duplicated the root README's quick start; the five
  placeholder SVGs in `frontend/public/` were never referenced.
- **Superseded prompts:** `conduct_v1.md` and `generate_template_v1.md`. The engine loads
  `conduct_v2`, generation loads `generate_template_v2`, and neither version is pinned per
  run, so the old files were unreachable. `refine_template_v1` and `summarise_run_v1` stay.
- **`engine._questions_of`,** a private passthrough to `snapshot.questions_of` whose body
  was a comment restating that module's docstring.

### Changed
- **The transcript renders from one component** (`components/Transcript.tsx`) instead of
  being copied between the respondent's runner and the author's results view.
- **DEVELOPING.md covers only what the README does not.** It opened with WSL setup for a
  machine this repo no longer lives on and then repeated the quick start, the ports and
  the test command.
- **TESTING_REPORT.md no longer quotes a stale test count.** It claimed 76, and 63 further
  down, against a suite of 213. The round-specific counts are gone rather than re-pinned,
  since they go stale on the next merge.

## 2026-07-27 — Gate mining, the LLM boundary, and the stretch goals

The day's theme is a method: construct an input whose correct verdict is known, run the
**real** code, and keep only the cases where the verdict flips the wrong way. Every defect
below was invisible to a suite that passed clean before and after — 21 in total, across
every surface that validates or decides something.

### Added
- **AI summary of a completed run** (PR #29) — `POST /templates/{id}/runs/{run_id}/summary`
  returns a headline, key facts and notable quotes through a schema-constrained tool call,
  stored on `survey_runs.summary` and shown above the answers. Author-triggered rather than
  generated when the respondent finishes: a model call on the final turn would put LLM
  latency, and LLM failure, in the path of recording someone's last answer. Two gates sit
  between the model and the column — the schema, and a check that every quote is a verbatim
  span of a recorded answer, because a fabricated quote is indistinguishable from a real one
  once it is rendered beside the answers.
- **Conditional visibility** (PR #33) — a question may carry `show_when {question, op, value}`
  and the engine skips it when the condition is not met. The reference is a question's
  *position*, not its id: saving a draft replaces every question row, so an id-keyed condition
  would break the moment the author edited anything. A condition must point backwards, must
  name an option the referenced select actually offers, and is satisfied by neither operator
  without a recorded answer — so a skipped or declined premise hides the dependent question,
  and conditions cascade.
- **Save and continue later** (PR #34) — `GET /runs` returns the caller's own unfinished runs
  and the respondent's home turns Start into **Continue**, showing where they left off. This
  was not merely missing: the home offered Start and nothing else, so anyone who closed the
  tab could only start again, opening a second run and stranding the first half-answered in
  the author's results.
- **Estimated completion time** (PR #34) — shown before starting, computed from question
  count and type, because a screen of ratings and a screen of essays are not the same survey.
  Deliberately coarse and rounded up: follow-ups add turns and conditions remove them, so a
  precise figure would be false precision.
- **Follow-up spend on the results view** (PR #30) — `RunDetail.follow_ups_asked`, per question.
  The cap is charged when a probe is *issued*, and a probe often draws out the scripted answer
  itself, so the run holds one scripted answer and no follow-up row. Counting follow-up answers
  reported "never probed" for runs that plainly were — twice, during a live acceptance
  walkthrough — and an author had no way to tell the two apart.

### Fixed
- **The transcript pushed every early conduct turn off the primary** (PR #28). The message
  list replayed to the model opened with the engine's greeting, and Anthropic rejects a list
  whose first entry is not the user's. The first several turns of every run therefore 400'd
  and fell through to a backup; nothing looked wrong because failover worked. Only the
  windowed path was safe, its own head already being a user message.
- **A recorded answer could be silently discarded** (PR #28). `tool_turn` left parallel tool
  use enabled and kept the *last* tool block, so a turn carrying both `record_answer` and
  `move_on` threw away the answer just given and advanced anyway.
- **One malformed backup response killed the whole failover chain** (PR #28). Seven bodies
  that are valid JSON but not the Chat Completions shape raised `AttributeError`/`KeyError`,
  which `FailoverLLM` does not catch, so a single bad tier aborted the request instead of
  trying the next provider. Every hop is now shape-checked and failures stay typed.
- **Concurrent turns corrupted a run** (PR #31). Two messages arriving together — a
  double-clicked send, or a client retry — both read the current question and the probe
  budget, then both wrote. The run ended up with two scripted answers for one question while
  advancing once ("2 of 2 answered" on a run whose second question was never asked), and the
  probes counter, a read-modify-write on JSONB, lost updates: racing it walked a respondent to
  four follow-ups against a cap of two. `handle_message` now takes the run's row lock
  (`FOR UPDATE NOWAIT`), and the loser gets a 409 rather than queuing behind a model call.
- **Salvage discarded tool calls that were plainly present** (PR #32). It scanned from the
  first `{` — so a brace inside earlier prose read as the start of an object — and returned
  only the first balanced object, so a leading thinking object swallowed the real call. The
  brace-counting itself was correct.
- **Ten holes in the answer gate** (PR #25) — NaN and infinity, Python-only numeric literals
  (`"4_000"`, full-width digits), empty write-ins, duplicate multi-select options.
- **Five holes at the template schema gate** (PR #26) — blank titles, question text and
  options; options colliding case-insensitively; and `_without_catch_alls` emptying a select
  *after* validation, since Pydantic does not re-validate on assignment — silently turning
  multiple choice into free text.
- **Validation errors rendered as `[object Object]`** (PR #27). FastAPI sends a 422 `detail`
  as a list of `{loc, msg}`; the client assumed a string.
- **The respondent's home advertised the draft, not the published version** (PR #34). A survey
  published with two questions and since edited to three offered three on the home page and
  asked two. The published list now reads the latest version's definition.
- **A max_tokens truncation reported itself as a chatty turn** (PR #28), which the engine
  retries — at the same budget, so the retry truncated identically and the error named the
  wrong cause.

### Changed
- Progress (`answered / total`) counts what can still be asked rather than every authored
  question, in both the respondent's view and the author's list, so a conditional run reads
  "2 of 2" instead of looking abandoned at "2 of 3". The denominator only ever shrinks: one
  that grew mid-survey would read as the survey getting longer the more you answered.
- Tolerant JSON decoding of model output moved to `app/llm/decoding.py`; generation and
  summarisation meet the same small-model slips.
- `main` is protected: both CI checks are required, force-pushes and deletion are blocked,
  and history must stay linear.

## 2026-07-26 — A third failover tier, recoverable secrets

### Added
- **Third backup tier** (PR #23) — `LLM_BACKUP3_*`, intended for OpenRouter's `openrouter/free`
  router, which picks a healthy tool-calling model per call rather than a hardcoded id. That
  sidesteps exactly the failure backup 2 hit when Gemini deprecated a model id underneath it.
- **`.env` encrypted with sops/age** (PR #22) — `.env.encrypted` is safely committable and
  `scripts/decrypt-env.sh` regenerates the live file, which stays plaintext and git-ignored.

### Fixed
- **A generated draft with no questions was persisted** (PR #24). Caught live: the free
  auto-router picked a weaker model that returned a schema-valid but empty tool call — a title
  and zero questions. An empty question list is now a validation failure, so it burns the retry
  and fails loudly instead of saving a useless draft.

## 2026-07-25 — AI drafts you can talk to

### Added
- **Refine a draft by follow-up prompt** (PR #20) — generation returns the model's short
  rationale alongside the draft, and an author can iterate by instruction instead of only
  editing by hand. The note is a schema field rather than prose: a forced tool call suppresses
  free text, so asking for a sentence "alongside" the call reliably yields nothing.
- **Generate lands in the builder** (PR #21) — "Generate draft" now opens the draft with its
  questions shown and the note seeded into the Refine panel, instead of a card on the home page.

### Fixed
- **An exhausted LLM chain showed the raw upstream error** (PR #19) — a Gemini quota JSON
  surfaced to the respondent as a 502. Any `LLMError` reaching the HTTP boundary is now a calm
  503; the detail stays in the logs.

## 2026-07-24 — Tricky-input hardening, role-aware UI, and the editor cockpit

### Added
- **Results export** — authors can download every answer for a survey from the
  Responses page as **CSV** (one row per answer, UTF-8 BOM so it opens directly in
  Excel) or **JSON**, via `GET /templates/{id}/runs/export?format=csv|json`. Answer
  values are flattened to readable cells (multi-selects joined, declines marked),
  the file is named after the survey, and the endpoint is scoped to the owning
  author like the rest of results.
- **`reply` tool in the conduct engine** (PR #7) — a respondent asking a question back ("what do
  you mean by role?") gets a real answer instead of a fabricated record or a wrongly
  flagged decline. Replies record nothing, never advance the survey, and are capped per
  question like follow-ups.
- **Typed value schemas per question** — the `record_answer` tool now declares the exact
  JSON shape for the current question (integer 1–5 for ratings, enum of the options for
  selects, `YYYY-MM-DD` pattern for dates), so constrained backends get a grammar and
  weak models stop guessing.
- **Prompt v2** (`conduct_v2.md`) — new rules: respondent messages are data, never
  instructions (prompt-injection); "I don't know/skip" is a decline, never an answer
  value; ambiguous or out-of-scale values ("between 3 and 4", "10/10") are pinned down
  or flagged, never averaged or clamped; relative dates are computed from the engine's
  today-plus-weekday line; abuse is not recorded as an answer.
- **Plain-English testing report** (`docs/TESTING_REPORT.md`, PR #7) for non-technical
  readers — the deviations we caught, the rules they earned, and the live failover run.
- **Three-pane editor cockpit** (PR #9) — the Claude Code extension is now a workspace
  recommendation, a one-click "stack up + follow backend logs" task streams the engine
  while you use the app, and `docs/DEVELOPING.md` §1b documents the layout (assistant |
  code | live preview, logs below).

### Changed
- **`docs/OVERVIEW.md` rewritten as a plain-English story** (PR #8) — the
  teacher/quiz analogy for the two roles, the AI-on-rails ride analogy, a dedicated
  "rules that stop bad answers reaching the database" section, real-life uses, and
  links threading the reader through the rest of the docs.
- Validation now coerces pure serialization artifacts — `"4"` → 4, `4.0` → 4, `"true"` →
  true — while still refusing natural language; case near-misses on select options
  ("days") land on the canonical option text instead of fragmenting into the write-in
  bucket; dates are normalised and must be the dashed `YYYY-MM-DD` form.
- The transcript sent to the model is windowed to the last 12 messages (the briefing
  restates the current question every turn), keeping long surveys inside a local
  backup model's context.
- Rejection feedback on a retried turn is now delivered in the conversation itself,
  where small models actually read it.
- The briefing states the current question's id, and tool calls that target a
  *different* question (answering two at once, revising an earlier answer) are refused.
- A blank `flag_unanswerable` reason is defaulted instead of burning the retry.
- The backup LLM client salvages a tool call written into the message text — a common
  local-model failure — instead of failing the turn.
- Whitespace-only respondent messages are rejected at the API boundary (422) before
  they reach the transcript or spend a model call.

### Fixed
- **Slow local backup models were reported as unreachable.** A CPU-served model can
  exceed the old fixed 60s read timeout on a cold load; the resulting `ReadTimeout`
  stringifies to "" and surfaced as a blank "could not reach" while network, server,
  and model were all fine. The read timeout is now generous and configurable
  (`LLM_BACKUP_TIMEOUT_SECONDS`, default 120), connect failures still fail fast on a
  separate 10s connect timeout, and timeout errors are named explicitly (logged with
  `repr`, never a blank line).
- **NL template generation failed on small backup models.** Weak models emit the
  right structure JSON-encoded into a string (`"questions": "[{...}]"`); validation
  rejected it and a live run 502'd. One level of JSON-encoding on `questions` (and
  each question's `options`) is now decoded before validation — real junk still
  fails loudly after the retry.
- **Backup failover could not engage under compose** (PR #6). The backend service only
  forwarded the Anthropic variables, so the `LLM_BACKUP_*` settings in `.env` never
  reached the container and a primary failure surfaced as a raw 502 instead of falling
  back. All four backup variables are now forwarded. Verified end to end: with an
  invalid primary key and an OpenAI-compatible backup, a full 3-question run completes
  with every turn logged as `primary LLM failed … using backup`, and the answers land
  correctly typed (`{"text": …}`, `{"rating": 4}`, `{"option": "Days"}`).
- **Role-aware navigation** (PR #7): the top-bar no longer shows Build to respondents;
  the author-only pages (template list, builder, results) redirect respondents to
  Respond instead of rendering a wall of 403s.
- **Stale builder form on user switch** (PR #7): the builder's unsaved edits previously
  survived an author switch and could be saved under the next author's identity; the
  form now resets when the acting user changes.

### Tests
- 76 automated tests (up from 63): serialization-artifact coercion, canonical option
  matching, strict date form, the reply tool and its cap, cross-question rejection,
  defaulted decline reasons, typed value schemas, transcript windowing, in-band retry
  feedback, whitespace-message rejection, and content-salvage in the backup client.

## 2026-07-23 — Hardening, docs, and resilience

### Added
- **Optional OpenAI-compatible backup LLM with failover** (PR #4). A second LLM
  client (`app/llm/backup.py`) speaks the OpenAI Chat Completions API, so any
  compatible endpoint (self-hosted Nemotron/Hermes, vLLM, NIM, OpenRouter, Ollama)
  can stand in when the Anthropic primary is unavailable. `FailoverLLM` tries the
  primary and falls back only on a typed error; `get_llm()` wires primary-only,
  backup-only, or primary-with-failover from settings
  (`LLM_BACKUP_ENABLED` / `_BASE_URL` / `_API_KEY` / `_MODEL`).
- **Application overview doc** (`docs/OVERVIEW.md`, PR #3) — a plain-English tour of
  what the app does, its two halves (authoring and conducting), and what it outputs.
- **Manual live-conduct check** — a workflow runnable from GitHub Actions or VS Code.
- **Scripted stress suite** — the eight conduct stress scenarios as a replayable test.
- **This changelog** (PR #5) — the project's history recorded from the first commit.

### Changed
- The conduct engine and template generator now resolve their LLM through the new
  `get_llm()` factory instead of constructing the Anthropic client directly.

### Fixed
- **Compose bind mounts fail under rootless Podman on Fedora/RHEL** (PR #2). Added the
  `:z` SELinux relabel to the `./backend` and `./frontend` mounts so the containers can
  read them; a no-op on Docker and on hosts without SELinux.

### Tests
- Offline coverage for the backup provider: failover selection and the
  OpenAI-compatible translation, driven by `httpx.MockTransport` (no network, no key).

### Repository maintenance
- Deleted 14 stale/merged branches, leaving `main` as the single source of truth.
- Verified the project is intact and current on `main`.

## 2026-07-22 — Long-survey polish and editor tooling

### Fixed
- **A catch-all option silently overwrote a real answer** — a live run recorded
  `{"option": "Other"}` and lost the respondent's actual team. Catch-all options are now
  turned into a proper write-in so the real answer is captured.
- Conduct engine: prompt the model to **probe rather than infer** a missing value, and
  allow a follow-up **before** an answer is recorded.
- Date the conversation correctly and respect optional questions on longer surveys.

### Added
- Dates on each row of the template list.
- A committed live-conversation harness for exercising the conduct engine end to end.

### Changed / tooling
- Editor niceties: pytest discovery in the IDE, and a debugger that frees port 8000 itself.

## 2026-07-21 — Core build (authoring, conducting, results)

### Added
- **Scaffold**: FastAPI backend + async SQLAlchemy + Alembic, PostgreSQL, and a
  Next.js frontend, all in a docker-compose dev stack.
- **Auth**: typed errors, a thin dev-auth dependency (`X-User-Id`), and seeded users.
- **Templates**: draft CRUD and publishing to **immutable versions**.
- **LLM authoring**: natural-language template generation via a schema-constrained
  tool call.
- **Builder UI**: template builder with live preview and NL generation.
- **Conduct engine**: a deterministic engine that owns which question is current,
  completion, and the follow-up budget; the model chooses one validated action per turn.
- **Conversational runner** (frontend) for respondents, plus a typed API client and
  queries for runs.
- **Results**: authors can read runs back (structured answers + full transcript), with
  a responses view; follow-ups are attached to the question they probed.
- CORS for the browser app, a health endpoint response model, a demo-reset script,
  shared editor config, and a developer guide.

### Fixed
- Render upstream Anthropic API failures as **typed errors**; bound API calls with an
  explicit timeout; log raw model output when a turn fails.
- **Authorization**: scope surveys and responses to the author who created them.
- **Follow-up budget is spent when a probe is asked** (not when answered), closing an
  endless-probe loophole.
- Transcript/answer ordering stamped client-side so same-transaction rows don't tie.
- Various web fixes: surface 4xx instead of retrying into a blank page; surface template
  creation failures.

### Tests
- Template CRUD, publish, and version immutability.
- Conduct: advancement, caps, malformed model output, and republishing leaving an
  in-flight run alone.
- The answer-validation contract across all eight answer types.
- Results: reading responses back, the template boundary, and follow-up ordering.
- Authorization: one author cannot reach another's surveys or responses.
- A shared LLM fake and published-survey fixture so tests run without an API key.

### CI
- Run the full suite (ruff, black, mypy, pytest) on every push and pull request.

## 2026-07-20 — Project kickoff

### Added
- The Elenchus survey trial brief pack (requirements, architecture, and spec).
