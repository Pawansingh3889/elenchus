"""Results routes: an author reading responses to their survey."""

import json
import re
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_author
from app.db.session import get_session
from app.runs.schemas import RunDetail, RunSummary
from app.runs.service import ResultsService, to_csv
from app.users.models import User

router = APIRouter(prefix="/api/v1/templates", tags=["results"])


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
    """Download every answer as a file: CSV (opens directly in Excel) or JSON."""
    title, rows = await ResultsService(session).export(template_id, author)
    stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "survey"
    if format == "json":
        return Response(
            json.dumps(rows, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{stem}-responses.json"'},
        )
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
