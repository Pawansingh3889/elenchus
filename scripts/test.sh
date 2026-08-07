#!/usr/bin/env bash
# Run the backend suite from anywhere in the repo.
#
#   ./scripts/test.sh                 the whole suite, quietly
#   ./scripts/test.sh -k visibility   any pytest arguments are passed straight through
#   ./scripts/test.sh --gates         everything CI runs, by delegating to `make gate`
#
# Exists because the suite has two environmental preconditions that are easy to
# trip over and whose failures look nothing like each other:
#
#   wrong directory  ModuleNotFoundError: No module named 'app', because the
#                    pytest config lives in backend/pyproject.toml and sets
#                    pythonpath there; run from the repo root and it never loads.
#   no DATABASE_URL  a Settings ValidationError during collection, since three
#                    test modules import settings at module scope and .env sits
#                    at the repo root while pytest runs from backend/.
#
# The URL below only satisfies that import. Which database the tests actually use
# is fixed in backend/tests/conftest.py (elenchus_test, rebuilt from the migrations
# once per run and truncated per test), so development data is never touched.
set -euo pipefail

cd "$(dirname "$0")/../backend"

# Compose sets DATABASE_URL for the containers; a host shell has to say it. Kept
# as an override rather than a default in app code, which fails loudly on purpose.
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus}"

RUNTIME=docker
command -v docker >/dev/null 2>&1 || RUNTIME=podman

# Fail with the cause rather than 200 identical connection errors halfway through.
if ! (exec 3<>/dev/tcp/localhost/5432) 2>/dev/null; then
  echo "Nothing is listening on localhost:5432. The suite needs Postgres." >&2
  echo "Start it with:  $RUNTIME compose up -d postgres" >&2
  exit 1
fi
exec 3<&- 2>/dev/null || true

# --gates delegates to `make gate` rather than re-implementing it: a hand-kept subset
# here (it was ruff/black/mypy only) drifts from what CI actually runs, and a gate that
# checks less than CI teaches people the wrong "it passed". `make test` calls this
# script WITHOUT the flag, so there is no recursion.
[ "${1:-}" = "--gates" ] && exec make -C .. gate

exec uv run pytest "${@:--q}"
