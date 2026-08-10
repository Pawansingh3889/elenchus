# Elenchus Survey Service

A standalone, embeddable survey service. Authors build survey templates (by natural
language or a builder UI) and publish immutable versions; respondents complete published
surveys through a conversational, LLM-driven runner that keeps the model on rails.

Full brief in [`trial-brief/`](trial-brief/README.md); what the app does
in [`docs/OVERVIEW.md`](docs/OVERVIEW.md); build conventions in [`CLAUDE.md`](CLAUDE.md);
what every check is asking in [`docs/CHECKS.md`](docs/CHECKS.md); project history
in [`CHANGELOG.md`](CHANGELOG.md).

## Stack

- **Backend**: Python 3.12, FastAPI (async), SQLAlchemy 2.x async + Alembic, PostgreSQL, Pydantic v2
- **Frontend**: Next.js (App Router) + TypeScript, TanStack Query, Zustand
- **LLM**: an ordered chain of up to four OpenAI-compatible tiers, tried until one
  answers: OpenAI, then Groq, then OpenRouter, with a fourth slot free for anything else
  that speaks the same API. One client speaks to all of them, so no provider SDK is
  vendored. A tier that is not enabled is skipped, and when every tier fails the API
  returns a calm 503 rather than a raw upstream error. See `LLM_TIER*_*` in `.env.example`
- **Dev**: docker-compose (postgres + backend + frontend)

## Prerequisites

- Docker + Docker Compose, **or** Podman + podman-compose (verified on Fedora with
  rootless Podman; the compose file carries the `:z` SELinux mount labels it needs)
- (For working outside containers) [uv](https://docs.astral.sh/uv/) and Node 22 + pnpm

## Quick start

```bash
cp .env.example .env          # enable an LLM tier (only needed for LLM features)
docker compose up --build     # or: podman compose up --build
```

- Backend API → http://localhost:8000 (health: `/api/v1/health`, docs: `/docs`)
- Frontend → http://localhost:3000
- Postgres → localhost:5432 (`elenchus` / `elenchus`)

The backend applies Alembic migrations on start, so the schema is ready once it's up.

## Seed data and auth

Dev auth is deliberately thin: every request identifies its caller with an `X-User-Id`
header, resolved by a single dependency. A real deployment replaces that dependency with
an identity provider without touching the routes. Requests without the header get a 401.

`python -m app.seed` runs automatically on backend start and is idempotent. It creates
two authors and three respondents with stable ids:

| Role | Name | Email | `X-User-Id` |
|---|---|---|---|
| author | Ava Author | ava@elenchus.dev | `00000000-0000-0000-0000-0000000000a1` |
| author | Arjun Author | arjun@elenchus.dev | `00000000-0000-0000-0000-0000000000a2` |
| respondent | Rosa Respondent | rosa@elenchus.dev | `00000000-0000-0000-0000-0000000000b1` |
| respondent | Ravi Respondent | ravi@elenchus.dev | `00000000-0000-0000-0000-0000000000b2` |
| respondent | Remy Respondent | remy@elenchus.dev | `00000000-0000-0000-0000-0000000000b3` |

```bash
curl -s http://localhost:8000/api/v1/templates \
  -H "X-User-Id: 00000000-0000-0000-0000-0000000000a1"
```

In the browser app you pick a user in the top bar and the header is sent for you. When
trying endpoints from `/docs`, add the header yourself.

## Walk through it

1. Pick **Ava Author** in the top bar. On **Dashboard**, which lists your surveys and how
   each is going, write a survey or describe one in the "Draft with AI" box, then
   **Publish** it. Publishing freezes the current draft as an immutable version; the
   draft carries on evolving separately.
2. Switch to **Rosa Respondent** and open **Respond**. Start the survey and answer it in
   the chat. Chips, stars and date pickers appear with the question, but they only produce
   text: the engine validates every answer against the question's type either way.
3. Switch back to an author and open **Responses** on that template to read what came back,
   both the answers and the full transcript. Follow-ups the model chose to ask are marked,
   and each question shows how many times it was probed. **Generate summary** asks the model
   for the headline, key facts and notable quotes in that response; quotes are checked
   verbatim against the recorded answers before they are shown.

Two more things worth trying:

- **Conditional visibility.** In the builder, a question after the first can be set to show
  **only if…** an earlier answer matches. The engine skips it when the condition is not met,
  and the respondent's progress counts only what they will actually be asked.
- **Leaving mid-survey.** Close the tab, or use **Finish later**. Every turn is already saved
  server-side, so the run reappears on **Respond** as **Continue** with the progress you left
  at, rather than starting a second, competing run.

Answering needs at least one working tier, configured via `LLM_TIER1_*` through
`LLM_TIER4_*` (any OpenAI-compatible endpoint). With several enabled, the app uses the
lowest-numbered one and falls through to the next only when it errors. Everything else
runs without a model.

## Layout

```
backend/
  app/
    config.py          settings (env-driven, no fallbacks)
    db/                declarative base + async session
    users/             User model
    templates/         template, question, immutable version models + publishing
    runs/              run, answer and transcript models, and results for authors
    conduct/           the deterministic run engine (answer validation, run locking)
    templates/…        visibility.py (show_when evaluation), estimate.py (time to complete)
    runs/summary.py    the AI summary of a completed run
    llm/               the OpenAI-compatible client + tier failover chain,
                       tolerant decoding of model JSON, versioned prompts
    auth/              dev-auth dependency
  migrations/          Alembic (async env)
  tests/               pytest against a real Postgres, LLM faked at the client boundary
frontend/
  app/
    page.tsx           template list, and drafting one with AI
    templates/[id]/    the builder, with live preview
    templates/[id]/results/   responses to a survey
    respond/           surveys open to the current respondent
    runs/[id]/         the conversational runner
  lib/                 typed API client, TanStack Query hooks, Zustand store,
                       conditions.ts (repointing show_when when questions move)
docker-compose.yml        development stack: postgres, backend, frontend
docker-compose.prod.yml   deployment: pinned digests, no seeding, no bind mounts
```

## Tests and CI

`make gate` is the whole contract, and it is exactly what CI runs.
[docs/CHECKS.md](docs/CHECKS.md) says what each check is asking, what a failure means and
how to fix it, and collects every command in one place.

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus uv run pytest -q
```

The suite runs against a real Postgres (the repository layer is exercised against the engine
it ships on) and fakes the LLM at the client wrapper, so it needs no API key. If a test ever
needs one, that is the bug. The tiers follow the same rule: the OpenAI-compatible client is
driven through an in-process mock transport, so failover coverage runs offline too.

GitHub Actions runs the same gates on every pull request: `alembic upgrade head` from an empty
database, `ruff`, `black`, `mypy` and `pytest` for the backend; `tsc --noEmit`, `eslint` and
`next build` for the frontend. Both are required to pass before `main` will accept a merge.

`.github/workflows/live-conduct.yml` is the opposite check: it drives real conversations
through a real model and only runs when you press *Run workflow*, since it costs credit. It
needs an `LLM_TIER1_API_KEY` repository secret.

## Backend development (outside Docker)

```bash
cd backend
uv sync
uv run alembic upgrade head           # against a running postgres (compose up postgres)
uv run uvicorn app.main:app --reload
```

## Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```
