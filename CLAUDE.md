# ViewOps Survey Service — Project Guide

Standing instructions for *how* we build this service. The brief in `ViewOps_Survey_Trial/`
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
  module owns the SDK, retries, timeouts, and token logging.
- **No fallbacks**: missing or invalid data fails loudly with a typed error and the correct
  HTTP status. No `.get(x, default)` shrugs over required data.

## Data model

See SPEC.md §3. Tables: `users`, `survey_templates`, `survey_questions`,
`survey_template_versions` (immutable), `survey_runs`, `answers`, `run_messages`.
Alembic migrations from the first table; no `create_all` in application code.

## Plan (4 working days)

- **Tue** — scaffold (compose, FastAPI skeleton, Next.js skeleton), full data model +
  initial migration, template CRUD API.
- **Wed** — builder UI + natural-language template generation (shares the LLM plumbing the
  runner needs next).
- **Thu** — conversational runner: conduct engine, answer recording, persistence, resume.
  *Review call today.*
- **Fri** — LLM follow-ups, results view, polish, demo.

Must-haves are the bar. Stretch goals only if the must-haves are solid.

## Conventions

- **Commits**: conventional and atomic, on `feature/<slug>` branches merged to main.
  Commit only when a unit is complete and verified (builds, migration applies, tests pass).
- **Backend quality**: `ruff` + `black` + `mypy` clean. `pytest` + `pytest-asyncio`; the
  conduct engine and publish/versioning logic are the test priorities. The LLM is mocked at
  the client-wrapper boundary so tests run without an API key.
- **Frontend quality**: `eslint` + `tsc --noEmit` clean. No frontend test harness for the trial.
- **Secrets**: `.env` is git-ignored, `.env.example` is committed. The Anthropic key never
  enters the repo.
- **Prompts as code**: versioned under `backend/app/llm/prompts/`, loaded by name + version.

## Decisions log

- **Python 3.12** (not the host's 3.14) for stable wheels on asyncpg and friends; pinned via uv.
- **uv** for backend dependency management, **pnpm** for the frontend. Lockfiles committed.
- **Native Postgres enums** for the controlled lists (role, template status, answer type,
  run status, answer kind, message role) — the schema enforces the vocabularies, not just
  the app layer.
