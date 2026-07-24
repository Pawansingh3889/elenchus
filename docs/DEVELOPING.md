# Developing in VS Code

The project runs entirely in Docker, so the only hard requirement is Docker itself.
Everything below is about making it comfortable to work on from the editor — and
avoiding the handful of traps that cost me time.

## 1. Open the right folder

The repository lives inside WSL, not on the Windows filesystem. Open it as a remote
folder rather than through `\\wsl.localhost\...`, or file watching and git will both
be slow.

- Command Palette → **WSL: Connect to WSL using Distro…** → `Ubuntu`
- **File → Open Folder…** → `/home/pawan/viewops-survey-service`

**Check the status bar reads `WSL: Ubuntu`.** If it says anything else you are in a
different Linux install with a different copy of the code, and your edits will not be
in the repository. The Source Control panel is the other tell: it should show a git
repository on `main`, not "no source control providers".

On first open, VS Code offers the extensions in `.vscode/extensions.json`. Accept them:
Claude Code, Python, Pylance, Ruff, mypy, ESLint and Docker. The workspace settings
wire Ruff to `backend/pyproject.toml` and point ESLint at `frontend/`, so formatting
and linting match what CI runs.

## 1b. The three-pane cockpit

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
   model turn — including any `primary LLM failed … using backup` failover — scrolls
   live while you click around the app on the right.

The result: ask Claude Code for a change on the left, watch the diff land in the
middle, and see the running app react on the right with the engine narrating below.

## 2. Run everything in Docker

The default. From the integrated terminal at the repository root:

```bash
docker compose up --build
```

Postgres, the API and the frontend come up together. The backend applies migrations and
seeds users on start.

- Frontend → http://localhost:3000
- API → http://localhost:8000 (docs at `/docs`)
- Postgres → localhost:5432 (`viewops` / `viewops`)

Both application containers hot-reload from the mounted source, so editing in VS Code is
enough — no rebuild for ordinary changes. Rebuild only when a dependency changes:

```bash
docker compose up -d --build backend
```

## 3. Run the backend on the host, with breakpoints

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

## 4. Run the tests

**Run and Debug → `backend: pytest`**, or from the terminal:

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://viewops:viewops@localhost:5432/viewops uv run pytest -q
```

The suite needs Postgres running but never touches development data — it creates and
drops its own `viewops_test` database per run. It also needs no `ANTHROPIC_API_KEY`: the
model is faked at the client wrapper, deliberately, so the tests stay honest about what
they prove. If a test ever needs a real key, that is the bug. The backup-provider tests
follow the same rule — the OpenAI-compatible client is driven through an in-process mock
transport, so failover coverage also runs offline.

The same checks CI runs:

```bash
cd backend && uv run ruff check . && uv run black --check app tests && uv run mypy app
cd frontend && pnpm exec tsc --noEmit && pnpm exec eslint .
```

## 5. Run the frontend on the host

Rarely needed, since the container hot-reloads. If you want the dev server in your own
terminal, stop the container first so port 3000 is free:

```bash
docker compose stop frontend
cd frontend && pnpm install && pnpm dev
```

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`, so it finds the containerised
API without configuration.

## 6. Reset to a known state

```bash
./scripts/demo_reset.sh
```

Wipes the database volume, rebuilds, and leaves one survey published twice with a
respondent part-way through version 1. Takes about forty seconds and prints the URLs.
Use it whenever the data gets messy, and before showing the app to anyone.

## Traps

**Only one stack at a time.** WSL distributions share a network namespace, so a second
copy of the project cannot bind 3000, 8000 or 5432 while the first is up. `docker compose
down` in the other one first.

**`.next` and `.venv` can end up owned by root.** The containers run as root and write
into the mounted source. If a host-side `pnpm build` fails with `EACCES` on
`.next/trace`, that is why — `sudo rm -rf .next` and run it again.

**`DATABASE_URL` is required outside Docker.** Compose sets it for the containers.
Running `alembic` or `pytest` from your own shell needs it exported, or settings loading
fails immediately, by design — there is no default to fall back to.

**The API key is optional but the runner is not.** Everything except answering a survey
works with `ANTHROPIC_API_KEY` blank: building, publishing, versioning, starting a run,
resuming it, reading results. Answering calls the model, and without a funded key returns
a typed 502 naming the reason. That is the intended behaviour, not a bug — the service
never invents an answer when the model is unavailable.
