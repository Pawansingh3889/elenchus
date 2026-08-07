"""Run routes. Thin: resolve the respondent, call one engine method, shape the response."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.auth.dependencies import require_respondent
from app.conduct.engine import ConductEngine
from app.conduct.schemas import (
    CurrentQuestion,
    ResumableRun,
    RunMessageRequest,
    RunRead,
    StartRunRequest,
)
from app.db.session import get_session
from app.i18n import parse_locale
from app.runs.models import SurveyRun
from app.runs.schemas import AnswerRead, MessageRead
from app.users.models import User

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


async def _to_read(engine: ConductEngine, run: SurveyRun) -> RunRead:
    questions = await engine.questions(run)
    current = None
    if run.current_question_index < len(questions):
        q = questions[run.current_question_index]
        current = CurrentQuestion(
            id=UUID(q["id"]),
            text=q["text"],
            answer_type=q["answer_type"],
            options=q["options"],
            allow_other=q["allow_other"],
            required=q["required"],
        )
    answered, total = engine.progress(run, questions)
    return RunRead(
        id=run.id,
        status=run.status,
        current_question=current,
        awaiting_follow_up=engine.probing(run, questions),
        answered=answered,
        total=total,
        messages=[
            MessageRead.model_validate(m) for m in sorted(run.messages, key=lambda m: m.created_at)
        ],
        answers=[AnswerRead.model_validate(a) for a in run.answers],
    )


@router.post("", response_model=RunRead, status_code=HTTP_201_CREATED)
async def start_run(
    data: StartRunRequest,
    respondent: User = Depends(require_respondent),
    session: AsyncSession = Depends(get_session),
    accept_language: str | None = Header(default=None),
) -> RunRead:
    engine = ConductEngine(session)
    # The language is settled here, once, and stored on the run. Later turns read it
    # from the run rather than the header, so resuming somewhere else cannot switch
    # the interview's language halfway through.
    run = await engine.start_run(
        data.template_id, respondent, language=parse_locale(accept_language)
    )
    return await _to_read(engine, run)


# Declared before /{run_id} so the literal path is never parsed as a run id.
@router.get("", response_model=list[ResumableRun])
async def my_unfinished_runs(
    respondent: User = Depends(require_respondent),
    session: AsyncSession = Depends(get_session),
) -> list[ResumableRun]:
    """The respondent's own unfinished runs, so a survey left half-done can be resumed
    rather than restarted from scratch under a second run."""
    engine = ConductEngine(session)
    return [
        ResumableRun(
            id=run.id,
            template_id=template_id,
            title=title,
            answered=answered,
            total=total,
            started_at=run.started_at,
        )
        for run, template_id, title, answered, total in await engine.resumable(respondent)
    ]


@router.get("/{run_id}", response_model=RunRead)
async def get_run(
    run_id: UUID,
    respondent: User = Depends(require_respondent),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    engine = ConductEngine(session)
    run = await engine.load(run_id, respondent)
    return await _to_read(engine, run)


@router.post("/{run_id}/messages", response_model=RunRead)
async def post_message(
    run_id: UUID,
    data: RunMessageRequest,
    respondent: User = Depends(require_respondent),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    engine = ConductEngine(session)
    run = await engine.handle_message(run_id, data.content, respondent)
    return await _to_read(engine, run)


@router.post("/{run_id}/rewind", response_model=RunRead)
async def rewind_last_answer(
    run_id: UUID,
    respondent: User = Depends(require_respondent),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    """Take back the most recent answer so the respondent can give a better one.

    No body: which answer this is, is the engine's to decide, not the client's. Asking
    for one by id would be the same door the model is refused at in ``_rejection``.
    """
    engine = ConductEngine(session)
    run = await engine.rewind_last_answer(run_id, respondent)
    return await _to_read(engine, run)
