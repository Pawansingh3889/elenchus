# Developing in VS Code

Getting the stack running is in the [README](../README.md) — prerequisites, quick start
and the seeded demo users all live there. This is the editor half: making the project
comfortable to work on, and the handful of traps that cost me time.

## 1. Extensions

On first open, VS Code offers the extensions in `.vscode/extensions.json`. Accept them:
Claude Code, Python, Pylance, Ruff, mypy, ESLint and Docker. The workspace settings
wire Ruff to `backend/pyproject.toml` and point ESLint at `frontend/`, so formatting
and linting match what CI runs.

## 2. The three-pane cockpit

VS Code can be the whole workbench: assistant, code, and the live app side by side.

```
┌────────────┬───────────────┬─────────────────────┐
│ Claude     │  Your code    │  Simple Browser      │
│ Code       │  (editor)     │  localhost:3000      │
├────────────┴───────────────┴─────────────────────┤
│ Terminal: stack up + follow backend logs          │
└────────────────────────────────────────────────────┘
```

Set it up once; VS Code remembers the layout per workspace:

1. **Left — Claude Code.** Install the recommended `anthropic.claude-code` extension
   and click its icon in the Activity Bar (or run `claude` in a terminal and drag the
   terminal tab into the left editor group). Sign in once.
2. **Middle — your code.** The normal editor. Split further with `Ctrl+\` if needed.
3. **Right — the live app.** Command Palette (`Ctrl+Shift+P`) → **Simple Browser:
   Show** → `http://localhost:3000`, then drag that tab to the right edge until the
   drop zone splits the editor. The app hot-reloads in place as containers rebuild.
   (The Ports panel next to the terminal lists 3000/8000 with an open-in-editor globe
   too.)
4. **Bottom — the engine's heartbeat.** Terminal → Run Task… → **stack up + follow
   backend logs**. This starts the whole stack and streams the backend log, so every
   model turn, including any `LLM tier 1/4 failed … trying next` failover, scrolls
   live while you click around the app on the right.

The result: ask Claude Code for a change on the left, watch the diff land in the
middle, and see the running app react on the right with the engine narrating below.

## 3. Editing against the running stack

Bring the stack up as the README describes. Both application containers hot-reload from
the mounted source, so editing in VS Code is enough — no rebuild for ordinary changes.
Rebuild only when a dependency changes:

```bash
docker compose up -d --build backend
```

## 4. Run the backend on the host, with breakpoints

Containers hot-reload but you cannot set a breakpoint in them from here. To debug the
conduct engine, run Postgres in Docker and the API on the host.

```bash
cd backend && uv sync              # first time only, creates .venv
```

Then **Run and Debug → `backend: uvicorn`**. Breakpoints in `app/conduct/engine.py` hit
on the next respondent message.

Port 8000 can only be held by one process, so the launch configuration handles the
swap for you: a pre-launch task brings Postgres up and stops the containerised backend,
and stopping the debugger starts it again. If you run uvicorn by hand instead, do that
yourself — otherwise you get `[Errno 98] Address already in use`:

```bash
docker compose stop backend        # ... debug ... then
docker compose start backend
```

## 5. Run the tests

**Run and Debug → `backend: pytest`**, or from the terminal as the
[README](../README.md#tests-and-ci) shows. The suite needs Postgres running but never
touches development data — it creates and drops its own `elenchus_test` database per run.

The same checks CI runs, locally:

```bash
cd backend && uv run ruff check . && uv run black --check app tests && uv run mypy app
cd frontend && pnpm exec tsc --noEmit && pnpm exec eslint .
```

## 6. Run the frontend on the host

Rarely needed, since the container hot-reloads. If you want the dev server in your own
terminal, stop the container first so port 3000 is free:

```bash
docker compose stop frontend
cd frontend && pnpm install && pnpm dev
```

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`, so it finds the containerised
API without configuration.

## 7. Reset to a known state

```bash
./scripts/demo_reset.sh
```

Wipes the database volume, rebuilds, and leaves one survey published twice with a
respondent part-way through version 1. Takes about forty seconds and prints the URLs.
Use it whenever the data gets messy, and before showing the app to anyone.

## 8. The other compose files

There used to be two GPU overlays here. They accelerated the tier-4 Ollama and nothing
else, so they went with it on 8 Aug 2026. `docker-compose.dbport.yml` is local-only and
uncommitted: it publishes Postgres to the host for a GUI client.

`docker-compose.prod.yml` is a separate file rather than a pile of overrides, because
almost everything the development stack does is wrong for an install: bind-mounting
source over the image, `--reload`, seeding demo accounts every boot, publishing Postgres
to the host, mutable image tags. Read its header before using it. In particular,
authentication is still the `X-User-Id` development shim, so the stack belongs behind
something that does the authenticating and not on the public internet.

## Traps

**No model runs locally any more.** The stack has no inference service, so every LLM
feature needs a key for one of the hosted tiers in `.env`. With none configured, template
CRUD, publishing and results all work; generation and conducting return 503.

**Only one stack at a time.** A second copy of the project cannot bind 3000, 8000 or
5432 while the first is up — and neither can another project's Postgres. `docker compose
down` in the other one first.

**`.next` and `.venv` can end up owned by root.** The containers run as root and write
into the mounted source. If a host-side `pnpm build` fails with `EACCES` on
`.next/trace`, that is why — `sudo rm -rf .next` and run it again.

**`DATABASE_URL` is required outside Docker.** Compose sets it for the containers.
Running `alembic` or `pytest` from your own shell needs it exported, or settings loading
fails immediately, by design — there is no default to fall back to.

**The API key is optional but the runner is not.** Everything except answering a survey
works with no LLM tier enabled: building, publishing, versioning, starting a run,
resuming it, reading results. Answering calls the model, and without a funded key returns
a typed 502 naming the reason. That is the intended behaviour, not a bug — the service
never invents an answer when the model is unavailable.
