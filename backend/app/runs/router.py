"""Results routes: an author reading responses to their survey."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_author, require_results_reader
from app.db.session import get_session
from app.runs.schemas import (
    AnswersMatrix,
    DashboardRow,
    RespondentRow,
    RunDetail,
    RunSummary,
    SurveyReport,
)
from app.runs.service import ResultsService
from app.runs.summary import RunSummaryContent, RunSummaryService
from app.runs.survey_summary import SurveyRecapStatus, SurveySummaryRead, SurveySummaryService
from app.users.models import User

logger = logging.getLogger("app.runs.router")

router = APIRouter(prefix="/api/v1/templates", tags=["results"])

# Its own prefix rather than /api/v1/templates/dashboard. The templates router is
# registered first and owns /{template_id}, so a literal path added here would be matched
# as a template id and rejected as a malformed UUID, which is a confusing way to learn
# about route ordering across two modules.
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@dashboard_router.get("", response_model=list[DashboardRow])
async def dashboard(
    author: User = Depends(require_results_reader),
    session: AsyncSession = Depends(get_session),
) -> list[DashboardRow]:
    """Every survey this author owns and how each is going, in one request."""
    return await ResultsService(session).dashboard(author)


@router.get("/{template_id}/runs", response_model=list[RunSummary])
async def list_runs(
    template_id: UUID,
    author: User = Depends(require_results_reader),
    session: AsyncSession = Depends(get_session),
) -> list[RunSummary]:
    return await ResultsService(session).list_runs(template_id, author)


@router.get("/{template_id}/report", response_model=SurveyReport)
async def survey_report(
    template_id: UUID,
    author: User = Depends(require_results_reader),
    session: AsyncSession = Depends(get_session),
) -> SurveyReport:
    """What the survey found, question by question. Declared before /{template_id}/runs
    is irrelevant here (different literal), but it is grouped with the other read
    endpoints for the same reason they are: one service call, shaped by the schema."""
    return await ResultsService(session).report(template_id, author)


@router.get("/{template_id}/answers", response_model=AnswersMatrix)
async def answers_matrix(
    template_id: UUID,
    author: User = Depends(require_results_reader),
    session: AsyncSession = Depends(get_session),
) -> AnswersMatrix:
    """Every answer on the current version, by respondent, with nothing tallied.

    The report shows one question at a time and cannot answer "did the people who said X
    also say Y". Reconstructing that took one request per run, so the join lives here
    once and the client slices it.
    """
    return await ResultsService(session).answers_matrix(template_id, author)


@router.get("/{template_id}/respondents", response_model=list[RespondentRow])
async def list_respondents(
    template_id: UUID,
    author: User = Depends(require_results_reader),
    session: AsyncSession = Depends(get_session),
) -> list[RespondentRow]:
    """All respondents for a survey with their participation summary and current status.

    Returns one row per respondent, aggregating their runs and showing their latest
    session status for real-time tracking. Used by the dashboard to show who is
    currently active on a survey.
    """
    return await ResultsService(session).respondents(template_id, author)


@router.get("/{template_id}/respondents/stream")
async def stream_respondents(
    template_id: UUID,
    author: User = Depends(require_results_reader),
) -> StreamingResponse:
    """Real-time stream of respondent status updates using Server-Sent Events.

    Polls for changes in respondent status and sends updates when respondents
    start, complete, or abandon surveys. The client receives SSE events with
    the current respondent list when changes are detected.
    """

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generator that yields SSE events when respondent status changes."""
        from app.db.session import SessionFactory

        last_keepalive = datetime.now()

        # Get initial state
        async with SessionFactory(info={"workspace_id": author.workspace_id}) as session:
            service = ResultsService(session)
            previous_respondents = await service.respondents(template_id, author)

        # Send initial state
        yield f"data: {json.dumps([r.model_dump() for r in previous_respondents])}\n\n"

        try:
            while True:
                # Wait before checking for updates (poll every 2 seconds)
                await asyncio.sleep(2)

                # Get current respondent state with fresh session
                async with SessionFactory(info={"workspace_id": author.workspace_id}) as session:
                    service = ResultsService(session)
                    current_respondents = await service.respondents(template_id, author)

                # Check if anything changed
                if _respondents_changed(previous_respondents, current_respondents):
                    previous_respondents = current_respondents
                    yield f"data: {json.dumps([r.model_dump() for r in current_respondents])}\n\n"

                # Send a keepalive comment every 15 seconds to prevent timeout
                now = datetime.now()
                if (now - last_keepalive).total_seconds() > 15:
                    yield ": keepalive\n\n"
                    last_keepalive = now

        except asyncio.CancelledError:
            logger.info("SSE stream cancelled for template=%s", template_id)
        except Exception as e:
            logger.error("SSE stream error for template=%s: %s", template_id, e)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def _respondents_changed(previous: list[RespondentRow], current: list[RespondentRow]) -> bool:
    """Check if respondent status has changed since last poll."""
    if len(previous) != len(current):
        return True

    # Compare by current status and activity timestamps
    prev_by_id = {r.respondent_id: r for r in previous}
    curr_by_id = {r.respondent_id: r for r in current}

    for respondent_id, current_row in curr_by_id.items():
        if respondent_id not in prev_by_id:
            return True

        prev_row = prev_by_id[respondent_id]

        # Check if key fields changed
        if (
            prev_row.current_status != current_row.current_status
            or prev_row.current_run_id != current_row.current_run_id
            or prev_row.last_activity_at != current_row.last_activity_at
            or prev_row.total_runs != current_row.total_runs
            or prev_row.completed_runs != current_row.completed_runs
            or prev_row.in_progress_runs != current_row.in_progress_runs
        ):
            return True

    return False


@router.get("/{template_id}/summary", response_model=SurveyRecapStatus)
async def survey_recap(
    template_id: UUID,
    author: User = Depends(require_results_reader),
    session: AsyncSession = Depends(get_session),
) -> SurveyRecapStatus:
    """The recap this survey already has, if the results have not moved past it.

    Same path as the POST, different verb: reading a recap should not cost a model call,
    and until this existed generating one was the only way to see it, so a page that
    navigated away and back paid to read prose already sitting in the column.
    """
    return await SurveySummaryService(session).stored(template_id, author)


@router.post("/{template_id}/summary", response_model=SurveySummaryRead)
async def summarise_survey(
    template_id: UUID,
    refresh: bool = Query(False, description="Regenerate even if a current recap is stored."),
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> SurveySummaryRead:
    """What the whole survey found, across every completed response.

    Author-triggered for the reason the per-run summary is: a model call costs seconds
    and can fail, and neither belongs in the path of a page an author opens to read
    numbers. The stored recap is reused only while the version and the completed-run
    count are what they were when it was written, because a recap of eight responses
    served after twenty have arrived is not stale, it is wrong.
    """
    return await SurveySummaryService(session).summarise(template_id, author, refresh)


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
