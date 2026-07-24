"""FastAPI application entrypoint.

Routes stay thin and delegate to services; domain routers are mounted here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.conduct.router import router as runs_router
from app.config import get_settings
from app.errors import register_error_handlers
from app.runs.router import router as results_router
from app.templates.router import router as templates_router
from app.users.router import router as users_router

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


@app.get("/api/v1/health", response_model=HealthRead, tags=["meta"])
async def health() -> HealthRead:
    return HealthRead(status="ok")
