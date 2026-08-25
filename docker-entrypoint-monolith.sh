#!/bin/bash
# Entrypoint for the monolith image: runs the backend and the frontend as two
# processes in one container, behind the single public port Railway assigns.
#
# Next.js binds $PORT and is the only publicly reachable process; its rewrite in
# next.config.ts proxies /api/* to uvicorn on 127.0.0.1:8000, which is never exposed
# outside the container. This is what makes one Railway service work for both halves
# without a separate reverse proxy: Next.js already is one.
#
# Real migrations run here (`alembic upgrade head`), not the `stamp head` shortcut the
# split backend-only Dockerfile still carries from the Railway migration-state fights —
# see CLAUDE.md's history-cleanup entry. If the schema and migration history have
# drifted apart on the target database, this fails loudly instead of pretending.
set -e

cd /app/backend
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
backend_pid=$!

cd /app/frontend
# Next's own binary directly, not `pnpm start`: pnpm re-verifies the lockfile against
# supply-chain build-script policy on every `run`, which means downloading pnpm itself
# from the registry at container start (nothing pins a version, so corepack fetches
# whatever is current) and then refusing to proceed over ignored build scripts that the
# original `pnpm install` accepted silently. None of that machinery is needed to run an
# already-built app; the binary is already sitting in node_modules.
PORT="${PORT:-3000}" node_modules/.bin/next start &
frontend_pid=$!

# Either process dying is a failure: a live frontend proxying to a dead backend, or a
# live backend behind a dead frontend, both look "up" to Railway's own TCP check and
# are not. `wait -n` returns as soon as the first job exits, and its exit code is that
# job's, so the container dies loudly and Railway's restart policy takes over.
trap 'kill -TERM "$backend_pid" "$frontend_pid" 2>/dev/null' TERM INT
wait -n "$backend_pid" "$frontend_pid"
code=$?
kill -TERM "$backend_pid" "$frontend_pid" 2>/dev/null
wait
exit "$code"

