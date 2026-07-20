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

## Layout

```
backend/
  app/
    config.py          settings (env-driven, no fallbacks)
    db/                declarative base + async session
    users/             User model
    templates/         template, question, immutable version models
    runs/              run, answer, transcript-message models
    conduct/           the deterministic run engine (Thu)
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
