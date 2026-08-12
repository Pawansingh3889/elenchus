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
