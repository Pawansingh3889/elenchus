"""Results routes: an author reading responses to their survey."""

import json
import re
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_author
from app.db.session import get_session
from app.runs.schemas import DashboardRow, RunDetail, RunSummary
from app.runs.service import ResultsService, to_csv
from app.runs.summary import RunSummaryContent, RunSummaryService
from app.users.models import User

router = APIRouter(prefix="/api/v1/templates", tags=["results"])

# Its own prefix rather than /api/v1/templates/dashboard. The templates router is
# registered first and owns /{template_id}, so a literal path added here would be matched
# as a template id and rejected as a malformed UUID, which is a confusing way to learn
# about route ordering across two modules.
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@dashboard_router.get("", response_model=list[DashboardRow])
async def dashboard(
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> list[DashboardRow]:
    """Every survey this author owns and how each is going, in one request."""
    return await ResultsService(session).dashboard(author)


@router.get("/{template_id}/runs", response_model=list[RunSummary])
async def list_runs(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> list[RunSummary]:
    return await ResultsService(session).list_runs(template_id, author)


# Declared before the {run_id} route so the literal path segment "export" is never
# parsed as a run id.
@router.get("/{template_id}/runs/export")
async def export_runs(
    template_id: UUID,
    format: Literal["csv", "json"] = Query("csv"),
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Download the responses: CSV (opens directly in Excel) or JSON.

    The two are deliberately different shapes rather than the same rows twice. CSV is
    flat because a spreadsheet cell cannot hold a follow-up, so it stays one row per
    recorded answer. JSON nests, so it carries the whole survey per run: every question
    including the ones nobody answered, each follow-up under the question it was asked
    about, and every value in its stored shape as well as flattened.
    """
    service = ResultsService(session)
    if format == "json":
        document = await service.export_structured(template_id, author)
        title = document["template"]["title"]
        stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "survey"
        return Response(
            json.dumps(document, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{stem}-responses.json"'},
        )
    title, rows = await service.export(template_id, author)
    stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "survey"
    return Response(
        to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{stem}-responses.csv"'},
    )


@router.get("/{template_id}/runs/{run_id}", response_model=RunDetail)
async def get_run(
    template_id: UUID,
    run_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> RunDetail:
    return await ResultsService(session).get_run(template_id, run_id, author)


@router.post("/{template_id}/runs/{run_id}/summary", response_model=RunSummaryContent)
async def summarise_run(
    template_id: UUID,
    run_id: UUID,
    refresh: bool = Query(False, description="Regenerate even if a summary is stored."),
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> RunSummaryContent:
    """Summarise one completed run. Author-triggered rather than generated when the
    respondent finishes: a model call on the respondent's last turn would put LLM latency
    (and LLM failure) in the path of recording their final answer."""
    return await RunSummaryService(session).summarise(template_id, run_id, author, refresh)
