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
# Run migrations and start server (seed runs automatically in demo mode via lifespan hook)
CMD ["sh", "-c", "cd /app && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]