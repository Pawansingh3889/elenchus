"""FastAPI application entrypoint.

Routes stay thin and delegate to services; domain routers are mounted here as
they are built (templates, runs, ...).
"""

from fastapi import FastAPI

app = FastAPI(title="ViewOps Survey Service", version="0.1.0")


@app.get("/api/v1/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
