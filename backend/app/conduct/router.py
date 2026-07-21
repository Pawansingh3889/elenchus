"""Run routes. Thin: resolve the respondent, call one engine method, shape the response."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.auth.dependencies import get_current_user
from app.conduct.engine import ConductEngine
from app.conduct.schemas import (
    CurrentQuestion,
    RunMessageRequest,
    RunRead,
    StartRunRequest,
)
from app.db.session import get_session
from app.runs.enums import AnswerKind
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
            options=q.get("options") or [],
            allow_other=bool(q.get("allow_other")),
            required=bool(q.get("required")),
        )
    return RunRead(
        id=run.id,
        status=run.status,
        current_question=current,
        answered=sum(1 for a in run.answers if a.kind is AnswerKind.scripted),
        total=len(questions),
        messages=[
            MessageRead.model_validate(m) for m in sorted(run.messages, key=lambda m: m.created_at)
        ],
        answers=[AnswerRead.model_validate(a) for a in run.answers],
    )


@router.post("", response_model=RunRead, status_code=HTTP_201_CREATED)
async def start_run(
    data: StartRunRequest,
    respondent: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    engine = ConductEngine(session)
    run = await engine.start_run(data.template_id, respondent)
    return await _to_read(engine, run)


@router.get("/{run_id}", response_model=RunRead)
async def get_run(
    run_id: UUID,
    respondent: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    engine = ConductEngine(session)
    run = await engine.load(run_id, respondent)
    return await _to_read(engine, run)


@router.post("/{run_id}/messages", response_model=RunRead)
async def post_message(
    run_id: UUID,
    data: RunMessageRequest,
    respondent: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    engine = ConductEngine(session)
    run = await engine.handle_message(run_id, data.content, respondent)
    return await _to_read(engine, run)
