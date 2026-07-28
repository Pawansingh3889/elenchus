"""FastAPI application entrypoint.

Routes stay thin and delegate to services; domain routers are mounted here.
"""

import logging

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.conduct.router import router as runs_router
from app.config import get_settings
from app.db.session import get_session
from app.errors import register_error_handlers
from app.runs.router import router as results_router
from app.templates.router import router as templates_router
from app.users.router import router as users_router

logger = logging.getLogger("app.main")

app = FastAPI(title="ViewOps Survey Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
    # Without this the browser can read a download's body but not its filename.
    expose_headers=["Content-Disposition"],
)
register_error_handlers(app)
app.include_router(users_router)
app.include_router(templates_router)
app.include_router(results_router)
app.include_router(runs_router)


class HealthRead(BaseModel):
    status: str
    database: str


@app.get("/api/v1/health", response_model=HealthRead, tags=["meta"])
async def health(session: AsyncSession = Depends(get_session)) -> Response:
    """Readiness, not just liveness.

    This used to answer "ok" whenever the process was up, which is the least useful
    thing it could say: when Postgres stopped, health stayed green while every real
    endpoint failed, and the app looked broken for no visible reason. Both callers that
    poll this — the demo reset and the live-conduct workflow — are waiting to find out
    whether the API can actually serve, so answer that question.
    """
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — any failure here means "not ready"
        logger.error("health check could not reach the database: %r", exc)
        return JSONResponse(
            status_code=503,
            content=HealthRead(status="degraded", database="unreachable").model_dump(),
        )
    return JSONResponse(content=HealthRead(status="ok", database="ok").model_dump())
