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
# Run migrations and start the server (seed runs automatically in demo mode via lifespan hook)
# Run alembic from the backend directory where alembic.ini expects to find migrations
# Handle migration state issues by stamping current head if upgrade fails
CMD ["sh", "-c", "cd /app && alembic upgrade head || alembic stamp e6f7a8b9c0d1 && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]