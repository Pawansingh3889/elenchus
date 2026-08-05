# ViewOps Survey Service

A standalone, embeddable survey service. Authors build survey templates (by natural
language or a builder UI) and publish immutable versions; respondents complete published
surveys through a conversational, LLM-driven runner that keeps the model on rails.

Full brief in [`ViewOps_Survey_Trial/`](ViewOps_Survey_Trial/README.md); what the app does
in [`docs/OVERVIEW.md`](docs/OVERVIEW.md); build conventions in [`CLAUDE.md`](CLAUDE.md);
working on it in an editor in [`docs/DEVELOPING.md`](docs/DEVELOPING.md); project history
in [`CHANGELOG.md`](CHANGELOG.md).

## Stack

- **Backend** — Python 3.12, FastAPI (async), SQLAlchemy 2.x async + Alembic, PostgreSQL, Pydantic v2
- **Frontend** — Next.js (App Router) + TypeScript, TanStack Query, Zustand
- **LLM** — Anthropic Claude via the official SDK (primary), then an ordered chain of up
  to three OpenAI-compatible backups (Groq, Gemini, OpenRouter, self-hosted vLLM/Ollama/NIM,
  …), each tried until one answers. Any tier whose key is absent is skipped, and when every
  tier fails the API returns a calm 503 rather than a raw upstream error. See `LLM_BACKUP*_*`
  in `.env.example`
- **Dev** — docker-compose (postgres + backend + frontend)

## Prerequisites

- Docker + Docker Compose, **or** Podman + podman-compose (verified on Fedora with
  rootless Podman; the compose file carries the `:z` SELinux mount labels it needs)
- (For working outside containers) [uv](https://docs.astral.sh/uv/) and Node 22 + pnpm

## Quick start

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY (only needed for LLM features)
docker compose up --build     # or: podman compose up --build
```

- Backend API → http://localhost:8000 (health: `/api/v1/health`, docs: `/docs`)
- Frontend → http://localhost:3000
- Postgres → localhost:5432 (`viewops` / `viewops`)

The backend applies Alembic migrations on start, so the schema is ready once it's up.

## Seed data and auth

Dev auth is deliberately thin: every request identifies its caller with an `X-User-Id`
header, resolved by a single dependency. A real deployment replaces that dependency with
an identity provider without touching the routes. Requests without the header get a 401.

`python -m app.seed` runs automatically on backend start and is idempotent. It creates
two authors and three respondents with stable ids:

| Role | Name | Email | `X-User-Id` |
|---|---|---|---|
| author | Ava Author | ava@viewops.dev | `00000000-0000-0000-0000-0000000000a1` |
| author | Arjun Author | arjun@viewops.dev | `00000000-0000-0000-0000-0000000000a2` |
| respondent | Rosa Respondent | rosa@viewops.dev | `00000000-0000-0000-0000-0000000000b1` |
| respondent | Ravi Respondent | ravi@viewops.dev | `00000000-0000-0000-0000-0000000000b2` |
| respondent | Remy Respondent | remy@viewops.dev | `00000000-0000-0000-0000-0000000000b3` |

```bash
curl -s http://localhost:8000/api/v1/templates \
  -H "X-User-Id: 00000000-0000-0000-0000-0000000000a1"
```

In the browser app you pick a user in the top bar and the header is sent for you. When
trying endpoints from `/docs`, add the header yourself.

## Walk through it

1. Pick **Ava Author** in the top bar. On **Build**, write a survey or describe one in the
   "Draft with AI" box, then **Publish** it. Publishing freezes the current draft as an
   immutable version; the draft carries on evolving separately.
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
  at — rather than starting a second, competing run.

Answering needs a working model: `ANTHROPIC_API_KEY`, and/or the optional backup LLM
configured via `LLM_BACKUP_*` (any OpenAI-compatible endpoint — with both set, the app
uses Claude and falls back to the backup only when Claude errors). Everything else runs
without a model.

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
    llm/               Anthropic client, OpenAI-compatible backups + failover chain,
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
docker-compose.yml
```

## Tests and CI

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://viewops:viewops@localhost:5432/viewops uv run pytest -q
```

The suite runs against a real Postgres — the repository layer is exercised against the engine
it ships on — and fakes the LLM at the client wrapper, so it needs no API key. If a test ever
needs one, that is the bug. The backup providers follow the same rule: the OpenAI-compatible
client is driven through an in-process mock transport, so failover coverage runs offline too.

GitHub Actions runs the same gates on every pull request: `alembic upgrade head` from an empty
database, `ruff`, `black`, `mypy` and `pytest` for the backend; `tsc --noEmit`, `eslint` and
`next build` for the frontend. Both are required to pass before `main` will accept a merge.

`.github/workflows/live-conduct.yml` is the opposite check — it drives real conversations
through a real model and only runs when you press *Run workflow*, since it costs credit. It
needs an `ANTHROPIC_API_KEY` repository secret.

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
