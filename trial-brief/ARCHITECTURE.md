# Survey Service — Architecture & Engineering Standards

These are the conventions our platform is built on. Following them is a first-class assessment criterion — a working app built differently is not a pass. Where this doc is silent, use your judgement and note the decision in the repo.

## 1. Stack

| Layer | Requirement |
|---|---|
| Backend | Python 3.11+, **FastAPI**, fully **async** for all I/O |
| ORM | **SQLAlchemy 2.x async** + **Alembic** migrations |
| DB | **PostgreSQL** |
| Schemas | **Pydantic v2** for every request/response body |
| Frontend | **Next.js (App Router only)**, React, TypeScript |
| Server state | **TanStack Query** |
| Client state | **Zustand** (only for genuinely client-side state — UI mode, draft edits) |
| LLM | Anthropic Claude via the official SDK (model id from env config, e.g. `claude-sonnet-5`) |
| Dev environment | **docker-compose**: postgres + backend + frontend, one command up, README-documented |

Dependency management: Poetry (or uv) on the backend, pnpm on the frontend. Lockfiles committed.

## 2. Backend layering (strict)

```
routes  →  services  →  repositories  →  SQLAlchemy models
```

- **Routes** are thin: parse/validate via Pydantic, resolve the current user via the auth dependency, call one service method, shape the response. No business logic, no ORM access.
- **Services** own business logic and transactions: publishing, run lifecycle, the conduct engine, LLM orchestration.
- **Repositories** own all queries. No ORM/session access from routes or anywhere above services.
- Organise by domain (e.g. `app/templates/`, `app/runs/`, `app/conduct/`, `app/llm/`, `app/auth/`), not by layer-only folders with 30 files each.

## 3. LLM engineering (this is the heart of the assessment)

**The engine is deterministic; the model is a constrained collaborator.** Concretely:

1. **Tool calls with JSON schemas, always.** Any LLM output the system acts on (a generated template, a recorded answer, a follow-up decision) comes back through a tool/structured-output call validated against a schema. Never regex/parse structured data out of prose.
2. **The conduct engine owns state.** Which question is current, whether the run is complete, how many follow-ups have been used — all decided by your code from the database, never by asking the model or trusting its narrative. Per turn, the engine hands the model the current question + conversation context and a small toolset, e.g.:
   - `record_answer(question_id, value, mapped_option?)` — value must validate against the question's answer type; the engine advances the pointer.
   - `ask_follow_up(question_id, follow_up_text)` — engine rejects it if the question disallows follow-ups or the cap (2) is spent; the model then must record instead.
   - `flag_unanswerable(question_id, reason)` — respondent declined/can't answer; recorded as such, engine moves on.
3. **Validate then act.** A tool call that fails validation is returned to the model for one retry with the error; a second failure fails the turn loudly (surfaced to the user as a retryable error, logged with the raw output). It must never corrupt the run.
4. **Prompts are code.** Version-controlled files under `prompts/` (e.g. `prompts/conduct_v1.md`, `prompts/generate_template_v1.md`), loaded by name+version — not inline string literals scattered through services.
5. **One LLM client module.** A single thin wrapper owns model id, retries on transient API errors, timeouts, and logging of token usage. Nothing else imports the SDK directly.
6. **Bound the loops.** Max model turns per respondent message, max follow-ups per question, max questions per generated template — all enforced in code with explicit constants.

## 4. Working rules (non-negotiable)

- **No fallbacks.** No silent defaults masking bad data. If a precondition fails (run not found, template not published, answer type mismatch, missing env var), fail loudly with a typed error → correct HTTP status. `.get(x, default)`-style shrugs over required data are an instant red flag.
- **Root-cause every bug.** Don't paper over symptoms — find why, fix why. If we spot symptom-patching in the history, we'll ask about it.
- **Modularise.** No god-files, no layer-tangling. If a file needs a scroll map, split it.
- **Security-conscious by default.** Parameterised queries only (the ORM gives you this — don't bypass it), respondents can only read/write their own runs, authors can't act as respondents mid-run, no secrets in the repo, LLM outputs rendered as text (no `dangerouslySetInnerHTML`).
- **Honest errors.** Backend errors map to a consistent problem shape; the frontend shows real states (loading / error / empty), never pretends success.

## 5. Frontend conventions

- App Router with server components where sensible; client components for the builder and chat.
- TanStack Query for every API interaction (queries + mutations, invalidation on writes). No hand-rolled fetch-in-useEffect.
- Zustand only for local/UI state (e.g. unsaved builder edits, chat composer state).
- A typed API client module — one place that knows base URL and response shapes.
- Follow `DESIGN.md` for look and feel; the mock at `reference/survey_builder_demo.html` shows the intended builder layout (builder left, live preview right).

## 6. Testing

- **pytest** (with `pytest-asyncio`) on the backend. Priorities, in order: the **conduct engine** (advancement, follow-up cap, validation-failure handling, resume), the **publish/versioning** logic (immutability, in-flight runs unaffected), repositories against a real Postgres (compose makes this easy).
- Mock the LLM at your client wrapper's boundary — tests must run without an API key. Include at least one test feeding the engine malformed tool output.
- No frontend test harness required for the trial; don't burn time on it.

## 7. Repo hygiene

- `README.md`: prerequisites, one-command startup, seed data, env vars (`.env.example` committed, `.env` ignored).
- Conventional commits on feature branches (`feature/<slug>`), merged to main. Small, coherent commits.
- Keep your planning/spec/prompt artifacts from LLM-assisted development in the repo (e.g. `docs/`, `CLAUDE.md`) — we want to see how you drove the tools.
- Lint/format configured and clean: `ruff` + `black` + `mypy` backend; `eslint` + `tsc --noEmit` frontend.
