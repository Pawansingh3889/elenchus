# Elenchus Survey Service

A standalone, embeddable survey service. Authors build survey templates through the API
(by natural language or by hand) and publish them; respondents complete published surveys
in the browser, through a conversational, LLM-driven runner that keeps the model on rails.

Full brief in [`trial-brief/`](trial-brief/README.md); what the app does
in [`docs/OVERVIEW.md`](docs/OVERVIEW.md); build conventions in [`CLAUDE.md`](CLAUDE.md);
what every check is asking in [`docs/CHECKS.md`](docs/CHECKS.md); who can see what, and
what an answer is worth, in [`docs/ACCESS_AND_RESULTS.md`](docs/ACCESS_AND_RESULTS.md);
project history in [`CHANGELOG.md`](CHANGELOG.md); every defect and what fixed it
in [`docs/DEFECTS.md`](docs/DEFECTS.md).

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

In the browser you sign in by typing a seeded email address in the top bar, which calls
`POST /api/v1/dev/identify` and stores the id the header needs. That endpoint is
unauthenticated by necessity and is only mounted outside production (a test pins this).
When trying endpoints from `/docs`, add the `X-User-Id` header yourself.

`python -m app.seed` runs automatically on backend start and is idempotent. There is no
stored role: each person holds one job, a function crossed with a band, and every right
derives from it (authoring is manager band and up; see
[`docs/ACCESS_AND_RESULTS.md`](docs/ACCESS_AND_RESULTS.md)). The cast covers what the
access rules need to be visible; the "Author"/"Respondent" surnames are cosmetic
leftovers from a retired vocabulary. The ones the walkthrough uses:

| Name | Email | Job | Why they are in the cast |
|---|---|---|---|
| Ava Author | ava@elenchus.dev | production / manager | A shift manager who authors from the floor |
| Arjun Author | arjun@elenchus.dev | hr / manager | An office author |
| Adaeze Author | adaeze@elenchus.dev | executive / head | Reads every survey, edits none |
| Rosa Respondent | rosa@elenchus.dev | production / operative | The floor |
| Ravi Respondent | ravi@elenchus.dev | production / line_leader | One job only, on purpose |
| Rohan Respondent | rohan@elenchus.dev | production / supervisor | Carries the health and safety hat |

`app/seed.py` holds the full list of sixteen, with a comment on each explaining which
rule it exists to demonstrate. Nobody seeded is in IT, so nobody seeded is an
administrator; that is deliberate.

```bash
curl -s http://localhost:8000/api/v1/templates \
  -H "X-User-Id: 00000000-0000-0000-0000-0000000000a1"
```

## Walk through it

1. Author a survey as Ava through the API; the browser has no authoring screens. Describe
   it, then publish the draft that comes back (its id is `template.id` in the response):

   ```bash
   AVA="X-User-Id: 00000000-0000-0000-0000-0000000000a1"
   curl -s -X POST http://localhost:8000/api/v1/templates/generate -H "$AVA" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Five questions on how the new chiller rota is going", "audience": "everyone"}'
   curl -s -X POST http://localhost:8000/api/v1/templates/<id>/publish -H "$AVA"
   ```

   Publishing freezes the survey, and what each person was actually asked is also recorded
   on their answers.
2. Sign in as **rosa@elenchus.dev** and open **Respond**. Start the survey and answer it in
   the chat. Chips, stars and date pickers appear with the question, but they only produce
   text: the engine validates every answer against the question's type either way.
3. Read the results as Ava: `GET /api/v1/templates/<id>/report` gives the counts per
   question, averages and spreads, and what the follow-ups drew out.
   `POST /api/v1/templates/<id>/summary` asks the model for the survey recap; its quotes are
   checked verbatim against the recorded answers, and its caveat line is computed by the
   engine, never written by the model.

Two more things worth trying:

- **Conditional visibility.** A question after the first can carry a `show_when`, so it shows
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
    users/             User model (one job: function x band + hats), admin account
                       routes, the append-only account_changes audit table
    access/            every access rule, as pure functions over the job
    templates/         template and question models, publishing, reading.py
    runs/              run, answer and transcript models, and results for authors
    conduct/           the deterministic run engine (answer validation, run locking)
    templates/…        visibility.py (show_when evaluation), estimate.py (time to complete)
    runs/summary.py    the AI summary of a completed run
    runs/survey_summary.py   the survey-level recap, fixed shape, engine-computed caveat
    llm/               the OpenAI-compatible client + tier failover chain,
                       tolerant decoding of model JSON, versioned prompts
    trace/             llm_spans (every turn's tree of decisions, attempts and checks)
                       and the admin-only lens reads over it
    auth/              dev-auth dependency
  migrations/          Alembic (async env)
  tests/               pytest against a real Postgres, LLM faked at the client boundary
frontend/
  app/
    page.tsx           the front door: what the service is, and a way to answer
    signin/            sign-in with whichever providers the deployment has
    respond/           surveys open to the current user
    runs/[id]/         the conversational runner
    lens/              admin only: traced runs, their cost and latency per tier
    lens/runs/[id]/    one run's spans as a waterfall, with what each call cost
    lens/inference/    each call split into time before its first token and writing
    lens/state/        input tokens by turn, and what the engine knew at every ask
    lens/tools/        tools offered, picked and accepted at every ask
    lens/validation/   refusals, what they cost, and answers given up as unanswerable
  lib/                 typed API client, TanStack Query hooks, Zustand store,
                       zod schemas for the responses the lens renders numbers from
docker-compose.yml        development stack: postgres, backend, frontend
docker-compose.prod.yml   deployment: pinned digests, no seeding, no bind mounts
```

## Tests and CI

`make gate` is the whole backend contract, and it is exactly what CI runs for the backend.
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

The frontend's checks are `make front-gate` (`tsc --noEmit`, `eslint` and
`vitest`), which runs inside the frontend container because the host has no
node. There is no browser suite: rendering is verified by looking at the rendered page.

GitHub Actions runs the same gates on every pull request: `alembic upgrade head` from an
empty database, `ruff`, `black`, `mypy`, the import contracts, the guards and `pytest` for
the backend; `tsc --noEmit`, `eslint`, `next build` and `vitest`
for the frontend. Both are required to pass before `main` will accept a merge.

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
