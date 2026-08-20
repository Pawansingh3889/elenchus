"""FastAPI application entrypoint.

Routes stay thin and delegate to services; domain routers are mounted here.
"""

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import router as auth_router
from app.conduct.router import router as runs_router
from app.config import get_settings
from app.db.session import get_session
from app.errors import register_error_handlers
from app.llm.router import router as llm_admin_router
from app.runs.router import dashboard_router
from app.runs.router import router as results_router
from app.seed import reset_demo
from app.templates.router import router as templates_router
from app.users.router import admin_router, dev_router, me_router
from app.users.router import directory_router as people_router
from app.users.router import router as users_router


def _configure_logging() -> None:
    """Give the app's own loggers somewhere to write.

    Without this they had nowhere to go. The app runs as ``uvicorn app.main:app``, and
    uvicorn's default config attaches handlers only to the ``uvicorn*`` loggers — the root
    gets none — so every ``app.*`` record fell through to ``logging.lastResort``, which
    drops anything below WARNING. The per-call token-usage lines ARCHITECTURE.md 3.5 calls
    non-negotiable are logged at INFO, so across a full day of live runs not one was ever
    written, and the warnings that did survive arrived as a bare message with no level or
    source.

    Configured on the ``app`` logger rather than the root: uvicorn owns its own
    configuration, and reconfiguring the root either fights it or double-emits every line.
    Every logger in this codebase already sits under that namespace, so one handler covers
    all of them. ``python -m app.seed`` and Alembic do not import this module and are
    unaffected; both print their own output.
    """
    app_logger = logging.getLogger("app")
    if app_logger.handlers:  # tests import this module repeatedly
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    app_logger.addHandler(handler)
    app_logger.setLevel(get_settings().log_level.upper())
    app_logger.propagate = False


_configure_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Reset the demo database on startup when APP_ENV=demo.

    A reset rather than a seed: the demo's data is disposable by design, so the honest
    boot state is the seed's clean state, not whatever a stranger left behind. This is
    what the banner's "resets on reload" points at, and it is the same wipe the /reset
    endpoint performs, so the two cannot drift apart.
    """
    if get_settings().app_env == "demo":
        logger.info("demo mode: resetting data on startup")
        await reset_demo()
    yield


app = FastAPI(title="Elenchus Survey Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
    # The session is an HttpOnly cookie on this origin, and the browser app is on
    # another, so without this the cookie is never attached and a signed-in person reads
    # as signed out. It is also why allow_origins names one origin rather than "*":
    # credentials and a wildcard are not allowed together, and should not be.
    allow_credentials=True,
    # Without this the browser can read a download's body but not its filename.
    expose_headers=["Content-Disposition"],
)
register_error_handlers(app)
# The user list exists to populate the dev-auth picker, and under that shim a user's id
# is their credential. Outside development the picker does not exist, nobody is seeded,
# and the endpoint's only remaining use would be handing an attacker the ids. So it is
# not mounted at all: absent beats guarded, because an endpoint that is not registered
# cannot be reached by a bug in whatever guards it.
#
# This is also the first thing in the codebase that branches on APP_ENV. The deployment
# file has been carrying a note that setting it changes no behaviour; that stops being
# true here.
if get_settings().app_env != "prod":
    app.include_router(users_router)
    # Same branch, same lifetime, and the branch is doing more work here. The picker is
    # guarded and merely useless to a stranger; identify is unauthenticated by necessity,
    # because requiring a caller is the deadlock it exists to undo. Not registering it
    # outside development is therefore the whole of its protection. Demo mode mounts both
    # so the public can sign in by email (the dev shim) and use the reset endpoint.
    app.include_router(dev_router)
# Mounted always, unlike the dev picker above, and it is what makes that branch
# survivable: this is how a production deployment is entered at all. An unconfigured
# provider answers that it is unconfigured rather than 404ing as though sign-in did not
# exist, because "nobody set the client secret" and "this build has no sign-in" are
# different problems with different fixes.
app.include_router(auth_router)
# Not behind that branch: the people directory is a page authors use, not scaffolding
# for the auth shim, and a deployment that dropped it would leave every reach number
# on the dashboard unexplainable.
app.include_router(people_router)
# Also unconditional, and for a sharper reason than the directory above it. These are the
# only way to create an account or change what somebody is, so a deployment without them
# is a deployment where the seed script is still the answer to who may build surveys.
# They carry their own gate rather than an environment branch: `require_admin` on every
# route, which is a rule about the caller and holds the same in every environment.
app.include_router(me_router)
app.include_router(admin_router)
app.include_router(llm_admin_router)
app.include_router(templates_router)
app.include_router(results_router)
app.include_router(dashboard_router)
app.include_router(runs_router)


class HealthRead(BaseModel):
    status: str
    database: str
    demo_mode: bool = False


@app.get("/api/v1/health", response_model=HealthRead, tags=["meta"])
async def health(session: AsyncSession = Depends(get_session)) -> Response:
    """Readiness, not just liveness.

    This used to answer "ok" whenever the process was up, which is the least useful
    thing it could say: when Postgres stopped, health stayed green while every real
    endpoint failed, and the app looked broken for no visible reason. Both callers that
    poll this — the demo reset and the live-conduct workflow — are waiting to find out
    whether the API can actually serve, so answer that question.
    """
    is_demo = get_settings().app_env == "demo"
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — any failure here means "not ready"
        logger.error("health check could not reach the database: %r", exc)
        return JSONResponse(
            status_code=503,
            content=HealthRead(
                status="degraded", database="unreachable", demo_mode=is_demo
            ).model_dump(),
        )
    return JSONResponse(
        content=HealthRead(status="ok", database="ok", demo_mode=is_demo).model_dump()
    )
