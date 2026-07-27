# Changelog

All notable changes to the ViewOps Survey Service, from the first commit onward.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The project is not yet versioned, so entries are grouped by date. Newest first.

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
- The ViewOps survey trial brief pack (requirements, architecture, and spec).
