"""FastAPI application entrypoint.

Routes stay thin and delegate to services; domain routers are mounted here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.conduct.router import router as runs_router
from app.config import get_settings
from app.errors import register_error_handlers
from app.templates.router import router as templates_router
from app.users.router import router as users_router

app = FastAPI(title="ViewOps Survey Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(users_router)
app.include_router(templates_router)
app.include_router(runs_router)


@app.get("/api/v1/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
