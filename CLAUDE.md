# Elenchus Survey Service — Project Guide

Standing instructions for *how* we build this service. The brief in `trial-brief/`
is the source of truth for *what*; this file is the source of truth for *how*.

## What this is

A standalone, embeddable survey service, in two halves:

- **Authoring** — an author builds a survey template either by describing it in natural
  language (the LLM drafts it via a schema-constrained tool call) or by hand in a builder
  UI. Both edit the same draft. Publishing snapshots the draft into an immutable version.
- **Conducting** — a respondent completes a published survey through a conversational,
  LLM-driven chat. The engine owns state; the model is a constrained collaborator.

## Non-negotiable architecture (from ARCHITECTURE.md)

- **Backend**: Python 3.12, FastAPI, fully async. SQLAlchemy 2.x async + Alembic.
  PostgreSQL. Pydantic v2 on every request/response body.
- **Layering**: `routes → services → repositories → models`. Routes are thin (parse,
  resolve the current user, call one service method, shape the response). Services own
  business logic and transactions. Repositories own every query. No ORM/session access
  above the repository layer.
- **Organise by domain**, not by layer: `app/users`, `app/templates`, `app/runs`,
  `app/conduct`, `app/llm`, `app/auth`.
- **Frontend**: Next.js App Router + TypeScript. TanStack Query for all server state.
  Zustand only for local UI state.
- **LLM on rails**: every model output the system acts on returns through a
  schema-constrained tool call, validated before use. The conduct engine — not the model —
  owns which question is current, whether the run is complete, and how many follow-ups are
  spent. Prompts are versioned files under `backend/app/llm/prompts/`. One LLM client
  module owns the HTTP calls, timeouts, and token logging.
- **No fallbacks**: missing or invalid data fails loudly with a typed error and the correct
  HTTP status. No `.get(x, default)` shrugs over required data.

## Data model

See SPEC.md §3. Tables: `users`, `survey_templates`, `survey_questions`,
`survey_template_versions` (immutable), `survey_runs`, `answers`, `run_messages`.
Alembic migrations from the first table; no `create_all` in application code.

## Conventions

- **Commits**: conventional and atomic, on `feature/<slug>` branches merged to main.
  Commit only when a unit is complete and verified (builds, migration applies, tests pass).
- **Backend quality**: `make gate` clean, which is `ruff` + `black` + `mypy` + import
  contracts + guards + the suite, and is what CI runs. `pytest` + `pytest-asyncio`; the
  conduct engine and publish/versioning logic are the test priorities. The LLM is mocked at
  the client-wrapper boundary so tests run without an API key.
- **Frontend quality**: `make front-gate` clean, which is `tsc --noEmit` + `eslint` +
  `vitest`, run inside the frontend container because there is no node on the host.
  Playwright drives a real browser from `frontend/e2e/`; CI runs it, and locally it
  needs `pnpm exec playwright install --with-deps chromium` in the container first.
  Frontend tests are written when something breaks, so each one names a bug that
  actually happened rather than a failure someone imagined.
- **Secrets**: `.env` is git-ignored, `.env.example` is committed. No provider key ever
  enters the repo.
- **Prompts as code**: versioned under `backend/app/llm/prompts/`, loaded by name + version.

## Decisions log

- **Python 3.12** (not the host's 3.14) for stable wheels on asyncpg and friends; pinned via uv.
- **uv** for backend dependency management, **pnpm** for the frontend. Lockfiles committed.
- **Native Postgres enums** for the controlled lists (role, template status, answer type,
  run status, answer kind, message role) — the schema enforces the vocabularies, not just
  the app layer.
- **Architecture rules are executable, and every gate is proven.** The layering in
  this file is enforced by import-linter contracts and by guards under
  `backend/scripts/`, not by review alone. `tests/test_gates.py` plants a violation
  for each guard and asserts it is rejected, because a gate nobody has watched reject
  anything is decoration. Guards fail when they cannot run, rather than passing having
  checked nothing. `make gate` is exactly what CI runs. Adopted from a sibling
  project on 6 Aug 2026.
- **One provider protocol, no vendored SDK.** Every LLM tier is reached over the OpenAI
  Chat Completions API through a single `httpx` client, so adding a provider is config
  rather than code. The Anthropic SDK and its client were removed on 6 Aug 2026; the
  chain is OpenAI, Groq, then OpenRouter, in that order.
- **The live check writes everything down, and judges itself.** Real conversations are the
  only thing that finds fabrication, and a live finding neither keeps nor reproduces. So
  every run captures its transcript to `backend/tests/live_runs/`, and the mocked suite
  replays those runs on every push: answers accepted live must stay accepted, and answers a
  human marks `"invented"` must be refused. A second model pass judges each recorded answer
  during the run, but its verdicts are soft everywhere and are never ground truth for a
  test, because it is a model and it produced false positives in two distinct classes on
  the day it was written. Adopted 9 Aug 2026. Do not promote the judge to a hard failure
  without a measured false-positive rate to point at.
- **Nothing is served locally.** The compose stack ran an Ollama as tier 4 until
  8 Aug 2026. It was removed: three hosted tiers cover failover, and the weights cost
  1.9 GB and a cold-load penalty to carry. Tier 4 survives as an empty slot any
  OpenAI-compatible server can fill from `.env`, so this is config to undo, not code.
  Do not reintroduce an inference service to the stack without a reason that names
  what the hosted tiers cannot do.
- **Frontend decisions live in `frontend/CLAUDE.md`**, which loads when working under that
  directory. The Tailwind layering rule, the class guard and the unified Results page are
  there: each only bites while editing frontend files, and this file is in context for
  every session including the ones that never open it.
- **A survey is aimed at the floor, and membership decides who may answer.** Adopted
  12 Aug 2026. `SurveyAudience` is everyone, one of five plant groups, or one named
  person; the office-team values it replaced were remapped onto `managers`, which rewrote
  what those surveys said they were for and was chosen knowingly. Membership lives in
  `user_group_memberships` because the groups overlap, and it is read live rather than
  frozen at publish so somebody who starts on Tuesday can answer a survey published on
  Monday. **`role` is not consulted when deciding who may answer**, and reinstating that
  check is the specific mistake to avoid: the senior groups are full of people who sign in
  with Teams and therefore hold author accounts, so a role check refuses a supervisors
  survey to every supervisor. `tests/test_access_rules.py` pins this.
- **Departments group authors; IT grants admin.** The second half reverses the earlier
  rule that administration came only from `ADMIN_EMAILS` so it could never be a database
  edit. It was asked for directly. Be clear-eyed about the cost: `UPDATE users SET
  department = 'it'` is now a grant of administration. The allowlist still works alongside
  it, so an admin who does not work in IT is still expressible. Colleagues in a department
  read each other's surveys and results and **cannot change them**: `may_edit` is owner or
  admin, and it exists because every mutation used to fetch its template through the
  listing rule, so widening that for reading widened it for writing in the same line.
- **Identity: a Microsoft account makes you a creator.** Recorded 12 Aug 2026, not yet
  wired. `users.microsoft_id` is the Entra object id, and its presence is what will decide
  `role` once real sign-in exists; everyone else is a named account reached by a QR link.
  Until then `role` is a stored column and the header shim stands in for a login, so
  `test_the_seed_agrees_with_how_people_will_sign_in` holds the two consistent while the
  data is small enough to fix.
- **An administrator makes accounts, and `role` is stored as sent.** Built 13 Aug 2026,
  and it closes the blocker the entry above named: `POST`/`PUT /api/v1/admin/users` behind
  `require_admin`, with `/people` as the screen. `users.created_by` records which
  administrator made each account, null for everyone the screen did not create. Four
  shapes are refused at the schema, and the one to understand before relaxing any of them
  is **a respondent with a department**: `_colleague` would make them a colleague of that
  department's authors, and `may_read_rows` hands a colleague every individual answer.
  The knowing cost: `role` comes from the request rather than being derived from
  `microsoft_id`, which is the opposite of what the entry above intends. An author with no
  Entra id therefore builds surveys today and loses that the day the derivation lands. The
  form sets the Entra id and `/people` badges the authors missing one, but nothing
  enforces the pair, and the seed test only covers `SEED_USERS` rather than the table.
  **A seeded account already in the database never gains a column the seed adds later**,
  because the seed inserts only when the id is absent: every author in a dev database
  seeded before 12 Aug has a null `microsoft_id` while the constant says otherwise.
- **Reach is live, and the guardrails are a witness, not a freeze.** Decided 13 Aug 2026,
  against snapshotting membership into published versions: who a survey is for is whoever
  is in the group today, so a new starter is asked Monday's survey and every denominator
  moves when membership does. What makes that honest is that changes are seen and
  recorded: the publish dialog shows the live headcount beside the audience; an admin
  edit that would move an open survey's reach shows exactly which surveys and by how much
  before saving (warn and proceed, never block, because people genuinely leave teams);
  and `account_changes` is an append-only audit table written in the same transaction as
  every create and edit, so "why did the completion rate drop on Tuesday" has an answer
  with a name on it. Open-source engines were evaluated for this on 13 Aug and rejected
  with reasons: Oso's library is deprecated, OpenFGA/SpiceDB/Cerbos are always-on
  services against the no-local-services decision, and pycasbin would replace the pure,
  reasoned `app/access` with a PERM DSL while providing none of the guardrails, which
  are change-management, not authorization. Do not re-litigate that without new facts.
  One number to keep in mind: reach and preview iterate every user and open survey per
  request, which is fine at plant size and author-side only, so the break-time burst
  (the whole floor answering at once, the reason `DB_POOL_SIZE`/`DB_POOL_MAX_OVERFLOW`
  exist and are forwarded in compose) never pays for them.
- **Seed ids are forever, and the seed refuses impostors.** Two ids reused from a retired
  generation of `SEED_USERS` were still occupied in databases seeded before 10 Aug; the
  insert silently skipped and the membership loop decorated the strangers holding them.
  New seed users take fresh c-block ids, `seed()` raises when an id's email disagrees,
  and `test_the_seed_only_decorates_its_own_users` pins the shape.
- **Signing in is an address, not a list.** `POST /api/v1/dev/identify` added 13 Aug 2026,
  because the app could not be entered at all from a clean browser: listing users requires
  a caller, a caller is an id under the header shim, and that list was the only source of
  an id. Every page told you to pick a user in a dropdown that could never be filled, and
  only a leftover localStorage entry hid it. The endpoint is unauthenticated of necessity,
  so **its mount is its only protection**: registered beside the picker and only outside
  production, pinned by a test. Knowing an address is therefore enough to act as somebody,
  which is the honest state of authentication here until a real provider replaces
  `get_current_user`. Do not move it out from behind that branch, and do not "fix" the
  deadlock by unauthenticating the user list: that hands out every id, which is every
  credential.
