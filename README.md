# ViewOps Survey Service

A standalone, embeddable survey service. Authors build survey templates (by natural
language or a builder UI) and publish immutable versions; respondents complete published
surveys through a conversational, LLM-driven runner that keeps the model on rails.

Full brief in [`ViewOps_Survey_Trial/`](ViewOps_Survey_Trial/README.md); build conventions
in [`CLAUDE.md`](CLAUDE.md).

## Stack

- **Backend** — Python 3.12, FastAPI (async), SQLAlchemy 2.x async + Alembic, PostgreSQL, Pydantic v2
- **Frontend** — Next.js (App Router) + TypeScript, TanStack Query, Zustand
- **LLM** — Anthropic Claude via the official SDK
- **Dev** — docker-compose (postgres + backend + frontend)

## Prerequisites

- Docker + Docker Compose
- (For working outside containers) [uv](https://docs.astral.sh/uv/) and Node 22 + pnpm

## Quick start

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY (only needed for LLM features)
docker compose up --build
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
   both the answers and the full transcript. Follow-ups the model chose to ask are marked.

Answering needs `ANTHROPIC_API_KEY` set. Everything else runs without it.

## Layout

```
backend/
  app/
    config.py          settings (env-driven, no fallbacks)
    db/                declarative base + async session
    users/             User model
    templates/         template, question, immutable version models + publishing
    runs/              run, answer and transcript models, and results for authors
    conduct/           the deterministic run engine
    llm/               single Anthropic client + versioned prompts
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
  lib/                 typed API client, TanStack Query hooks, Zustand store
docker-compose.yml
```

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
