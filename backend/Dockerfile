FROM python:3.12-slim

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dependency layer — cached unless pyproject.toml / uv.lock change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

# Run migrations with fallback for Railway deployment
# Stamp to head if migration fails (handles Railway migration state mismatches)
CMD sh -c "alembic upgrade head || alembic stamp head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
