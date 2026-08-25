# Monolith image: backend and frontend built here and run as two processes in one
# container behind one Railway service. See docker-entrypoint-monolith.sh for how they
# share the single public port, and CLAUDE.md's decisions log for why this replaced the
# split Vercel+Railway deployment.
#
# Railway builds from the repo root, which is why every COPY below is qualified with
# backend/ or frontend/ rather than assuming either as the build context.

# ---- frontend build stage -------------------------------------------------
FROM node:22-slim AS frontend-builder

RUN corepack enable
WORKDIR /app/frontend

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ .

# Baked into the client bundle at build time, so it must be resolvable from the
# browser. Empty and relative: the browser calls this same origin (/api/v1/...), and
# next.config.ts's rewrite forwards it internally to uvicorn. Not baked from a
# build-arg default that could silently point at the wrong deployment, matching the
# "fail loudly" rule: a monolith build with no ARG override is a monolith build.
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
# next.config.ts's rewrites() is baked into routes-manifest.json at `next build` time,
# not re-evaluated per request under `next start`. Setting this only in the final stage
# (where uvicorn actually listens) has no effect on an already-built app, so it has to
# be here too, matching the literal port the entrypoint script binds uvicorn to.
ARG INTERNAL_BACKEND_URL="http://127.0.0.1:8000"
ENV INTERNAL_BACKEND_URL=${INTERNAL_BACKEND_URL}
RUN pnpm build

# ---- final image ------------------------------------------------------------
FROM python:3.12-slim

# Node runtime to execute the already-built frontend/node_modules/.bin/next binary
# directly (see docker-entrypoint-monolith.sh). No pnpm/corepack here: nothing in this
# stage installs packages, so there is nothing for a package manager to do, and pulling
# one in only adds a network call at container start. NodeSource rather than Debian's
# own nodejs package: bookworm's apt package trails behind the frontend's pinned Node 22.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y curl gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Backend, unchanged from the split image.
COPY backend/pyproject.toml backend/uv.lock backend/
RUN cd backend && uv sync --frozen --no-dev
COPY backend/ backend/
ENV PATH="/app/backend/.venv/bin:$PATH"

# Frontend: only what `next start` needs at runtime, not the toolchain that built it.
COPY --from=frontend-builder /app/frontend/.next frontend/.next
COPY --from=frontend-builder /app/frontend/node_modules frontend/node_modules
COPY --from=frontend-builder /app/frontend/package.json frontend/package.json
COPY --from=frontend-builder /app/frontend/next.config.ts frontend/next.config.ts

# Matches the build-time value above; the rewrite itself is already compiled into
# .next, this is only so the running process's own environment is honest about what it
# was built to talk to.
ENV INTERNAL_BACKEND_URL="http://127.0.0.1:8000"

COPY docker-entrypoint-monolith.sh /app/docker-entrypoint-monolith.sh
RUN chmod +x /app/docker-entrypoint-monolith.sh

EXPOSE 3000
CMD ["/app/docker-entrypoint-monolith.sh"]
