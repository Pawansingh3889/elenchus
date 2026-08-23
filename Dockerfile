# Railway builds from the repo root, so this root-level Dockerfile adapts the
# backend one (which expects backend/ as its context) for that layout.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ .
COPY scripts/ scripts/

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Fix missing audience in sample surveys, then start server
# This fixes the issue where surveys were hidden from dashboard due to missing audience field
# Run the fix script from within the backend directory for proper imports
CMD ["sh", "-c", "cd /app && python scripts/fix_survey_audience.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]