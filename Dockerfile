# Railway builds from the repo root, so this root-level Dockerfile adapts the
# backend one (which expects backend/ as its context) for that layout.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ .

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Start server directly (skip migrations due to Railway database state issues)
# The database schema should already be correct from previous deployments
CMD ["sh", "-c", "cd /app && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]