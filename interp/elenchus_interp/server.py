"""The HTTP face: one analysis at a time, behind a shared token."""

import asyncio
import hmac
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import TypeVar

from fastapi import FastAPI, Header, HTTPException
from starlette.concurrency import run_in_threadpool

from elenchus_interp.analysis import Analyzer, PromptTooLongError
from elenchus_interp.prompt import PromptLayoutError
from elenchus_interp.schemas import (
    AnalyseRequest,
    Analysis,
    AttributeRequest,
    AttributionResult,
    Health,
)

T = TypeVar("T")


def create_app(
    load_analyzer: Callable[[], Analyzer], token: str, *, model: str, revision: str
) -> FastAPI:
    """The app, loading the model once at startup.

    One analysis at a time, because two would only share the same CPU and each take twice
    as long, and a queue that says so is more honest than two requests that both look slow.
    """
    state: dict[str, Analyzer] = {}
    lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        state["analyzer"] = await run_in_threadpool(load_analyzer)
        yield

    app = FastAPI(title="Elenchus interpretability", lifespan=lifespan)

    @app.get("/health", response_model=Health)
    async def health() -> Health:
        analyzer = state.get("analyzer")
        return Health(
            model=model,
            revision=revision,
            device=str(analyzer.device) if analyzer else "loading",
            ready=analyzer is not None,
        )

    def _authorised(authorization: str | None) -> Analyzer:
        # Compared in constant time: the token is the only thing between the network and
        # a process that reads whatever prompt it is handed.
        if authorization is None or not hmac.compare_digest(authorization, f"Bearer {token}"):
            raise HTTPException(status_code=401, detail="missing or wrong interp token")
        analyzer = state.get("analyzer")
        if analyzer is None:
            raise HTTPException(status_code=503, detail="the model is still loading")
        return analyzer

    async def _one_at_a_time(work: Callable[[], T]) -> T:
        async with lock:
            try:
                return await run_in_threadpool(work)
            except PromptTooLongError as exc:
                raise HTTPException(status_code=413, detail=str(exc)) from exc
            except (PromptLayoutError, ValueError, KeyError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/analyse", response_model=Analysis)
    async def analyse(
        body: AnalyseRequest, authorization: str | None = Header(default=None)
    ) -> Analysis:
        analyzer = _authorised(authorization)
        return await _one_at_a_time(lambda: analyzer.analyse(body))

    @app.post("/attribute", response_model=AttributionResult)
    async def attribute(
        body: AttributeRequest, authorization: str | None = Header(default=None)
    ) -> AttributionResult:
        analyzer = _authorised(authorization)
        return await _one_at_a_time(lambda: analyzer.attribute(body))

    return app
