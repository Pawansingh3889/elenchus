# Every check, and what it is telling you

The README lists the tools this project runs. This file says what each one is *for*, what
a failure actually means, and what to do about it. It also collects every command in one
place.

For getting the stack running the first time, see the [README](../README.md).

All commands run from the repository root unless they say otherwise.

---

## First, what `uv` is

The backend has its own private Python and its own copy of every package, kept in
`backend/.venv`. `uv` manages it. That is why backend commands start with `uv run`: it
means "run this using the project's packages, not whatever happens to be on my laptop".

```bash
cd backend && uv sync          # install exactly what uv.lock says. Run after every git pull.
cd backend && uv run <cmd>     # run a command inside the project's environment
cd backend && uv add <pkg>     # add a package and update the lockfile
cd backend && uv add --dev <pkg>   # add a tool only developers need
cd backend && uv lock          # rebuild the lockfile after hand-editing pyproject.toml
```

`uv.lock` is committed on purpose. It pins the exact version of everything, so your
machine and CI install identical packages. Do not delete it.

The frontend uses `pnpm` the same way, with `pnpm-lock.yaml` playing the same role.

---

## The one command that matters

```bash
make gate
```

This is exactly what CI runs, no more and no less. If it is green you can commit and push
with confidence. If it is red, one of the questions below got a "no".

**It needs Postgres running**, because the suite uses a real database rather than a
stand-in:

```bash
podman compose up -d postgres      # or: docker compose up -d postgres
```

---

## What each check asks

`make gate` runs these in order. Later checks assume earlier ones passed, which is why a
formatting problem can produce a confusing type error.

| Command | The question | A failure means | The fix |
| --- | --- | --- | --- |
| `make lint` | Is the code tidy and free of obvious slips? | An unused import, imports in the wrong order, a variable assigned and never read | `cd backend && uv run ruff check --fix app tests scripts`, then `make fmt` |
| `make typecheck` | Do the types line up? | Text passed where a number is expected, or something that might be `None` used as though it cannot be | Read the file and line it names and fix the code. Do not silence it. |
| `make imports` | Does the code respect the layers? | A router reached into the database directly, or something outside the LLM client imported `httpx` | Move the code to the layer it belongs in |
| `make guards` | Do this project's own rules hold? | See the five below | Each guard prints the file, the line and the rule |
| `make test` | Does it actually work? | Real broken behaviour | Read the failure and fix the code |
| `make gate-proof` | Do the guards still catch anything? | A guard has quietly stopped working | Rare, and it is the reason the guards can be trusted at all |

`make fmt` is not a check. It rewrites the code into one consistent style. Run it, look at
what changed, and commit.

### The five guards, in plain terms

These enforce decisions that a linter cannot express. They live in `backend/scripts/`.

- **query surface**: only repository files may write database queries. Stops queries
  leaking into routers where nobody thinks to look for them.
- **no create_all**: the database schema comes from migrations, never from the models.
  Stops tests passing against a schema that a real deployment would never have.
- **prompts versioned**: every AI prompt file is named with a version, and every prompt
  the code asks for exists on disk. Catches a renamed prompt now rather than at the moment
  a model is called, which is the one path that costs money and that the mocked suite
  cannot exercise.
- **contrast**: text colours are readable against their backgrounds.
- **logical properties**: no `left` or `right` in the stylesheet, so the layout still works
  in a language that reads right to left.

### Why `gate-proof` exists

A guard that has never been seen to reject anything is decoration. `make gate-proof`
plants a deliberate violation for each one and checks it is caught. `tests/test_gates.py`
also runs each guard against an empty directory, because the failure that hides is a
checker that walks no files, finds nothing, and reports success having verified nothing.

---

## The frontend

There is no test suite here by design. Two checks:

```bash
cd frontend
pnpm exec tsc --noEmit    # do the types line up (there is no "typecheck" script)
pnpm lint                 # eslint
```

CI also runs `next build`, which catches things the two above miss.

---

## Every command, grouped

### Checks

```bash
make gate            # everything CI runs
make lint            # ruff + black --check
make fmt             # rewrite to the standard format
make typecheck       # mypy
make imports         # the layering contracts
make guards          # the five architecture guards
make test            # the pytest suite alone
make gate-proof      # prove each guard rejects a planted violation
```

### Running tests directly

```bash
./scripts/test.sh                        # whole suite, quiet
./scripts/test.sh -v                     # verbose
./scripts/test.sh -x                     # stop at the first failure
./scripts/test.sh tests/test_conduct.py  # one file
./scripts/test.sh -k grounded            # every test whose name contains "grounded"
./scripts/test.sh --gates                # delegates to make gate
```

Any pytest argument passes straight through. Use this rather than calling `pytest`
yourself: the suite has two preconditions that fail in ways that look nothing like their
cause, and the script handles both. Run pytest from the repository root and the config in
`backend/pyproject.toml` never loads, so importing `app` fails. Run it without
`DATABASE_URL` and settings raise while tests are still being collected.

### The stack

```bash
podman compose up -d postgres      # just the database, which is all the tests need
podman compose up -d               # the whole stack
podman compose logs -f backend     # follow the backend's logs
podman compose stop                # stop without deleting anything
podman compose up -d --force-recreate backend   # pick up changed environment variables
```

Substitute `docker` for `podman` if you prefer. Note that `make stack-up` and
`make stack-down` say `docker compose` literally, so they will not work on a
podman-only machine, whereas `scripts/test.sh` detects which you have.

### Running the backend or frontend on the host

```bash
make serve      # backend on :8000 with reload, against the compose Postgres
make front      # frontend dev server on :3000
```

### Database

Alembic and the seed both load settings, and settings require `DATABASE_URL`. They run
from `backend/`, while the `.env` you edit lives at the repository root, so they do not
see it. There are two ways round that, and the first is worth doing once:

```bash
# Option 1, once per clone: a small backend/.env holding only the database URL.
# It is gitignored, so a fresh clone will not have it and nothing will tell you.
echo 'DATABASE_URL=postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus' > backend/.env

# Option 2, per command:
cd backend
DATABASE_URL=postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus uv run alembic current
```

With `backend/.env` in place these all work bare:

```bash
cd backend
uv run alembic upgrade head                              # apply migrations
uv run alembic revision --autogenerate -m "describe it"  # create one from model changes
uv run alembic current                                   # which revision is applied
uv run alembic history                                   # all of them
uv run python -m app.seed                                # dev users + sample data, idempotent
```

`./scripts/test.sh` does not need any of this. It sets `DATABASE_URL` itself, which is
one of the reasons to use it rather than calling pytest directly.

Always read a generated migration before committing it. Autogenerate is a good first
draft and not a finished one.

### Housekeeping

```bash
make setup                    # uv sync + pnpm install
make clean                    # remove caches
./scripts/demo_reset.sh       # wipe and rebuild a known demo state
./scripts/demo_reset.sh --db-only   # same, but leave the servers running
./scripts/decrypt-env.sh      # regenerate .env from .env.encrypted (needs the age key)
```

---

## Your daily rhythm

**Starting work:**

```bash
git pull
cd backend && uv sync && cd ..
podman compose up -d postgres
```

**While changing one thing**, run only the tests for it. Fast feedback beats complete
feedback:

```bash
./scripts/test.sh tests/test_conduct.py
./scripts/test.sh -k grounded
```

**Before committing**, always both of these:

```bash
make gate
cd frontend && pnpm exec tsc --noEmit && pnpm lint
```

---

## How to read a failure

**pytest**: read the **bottom** of the output first. The last lines are headed
`short test summary info` and name exactly which tests failed. Then scroll up to the
`assert` line, which shows what was expected against what actually happened.

**mypy**: gives `file.py:42: error: ...`. Go to that line. It names the type it wanted and
the type it found.

**ruff**: usually fixable automatically. Try `--fix` before reading further.

**guards**: they print the offending file, the line and the rule in one sentence. They are
written to be read.

**Fix in this order**: formatting, then lint, then types, then tests. Each can cause
confusing failures in the next, so working upwards saves time.

---

## Failures that are not your fault

**"Nothing is listening on localhost:5432"** means Postgres is not running. Start it with
`podman compose up -d postgres`. Note that other projects on this machine may already hold
that port.

**A test fails that you never touched.** Usually you pulled someone's change without
running `uv sync`. Run it and try again.

**The suite never touches your development data.** It creates and drops its own
`elenchus_test` database on every run, built from the migrations rather than from the
models, so what you are testing is the schema a deployment would actually get.
