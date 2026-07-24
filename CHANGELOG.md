# Changelog

All notable changes to the ViewOps Survey Service, from the first commit onward.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The project is not yet versioned, so entries are grouped by date. Newest first.

## 2026-07-24 — Tricky-input hardening, role-aware UI, and the editor cockpit

### Added
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
