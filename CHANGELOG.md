# Changelog

All notable changes to the Elenchus Survey Service, from the first commit onward.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The project is not yet versioned, so entries are grouped by date. Newest first.

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

Adopted from the copernus project, whose Makefile states the principle: a gate that
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
