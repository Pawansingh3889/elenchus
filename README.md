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

## Layout

```
backend/
  app/
    config.py          settings (env-driven, no fallbacks)
    db/                declarative base + async session
    users/             User model
    templates/         template, question, immutable version models
    runs/              run, answer, transcript-message models
    conduct/           the deterministic run engine
    llm/               single Anthropic client + versioned prompts
    auth/              dev-auth dependency
  migrations/          Alembic (async env)
frontend/              Next.js App Router app
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
