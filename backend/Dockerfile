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

# Handle migration stamp mismatch for Railway deployment
# Stamp the database to current head if migration fails
CMD sh -c "alembic upgrade head || alembic stamp head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
