"""Retention policy and content-expiry tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.embeddings.models import EmbeddingVector
from app.embeddings.service import digest
from app.errors import ConflictError, ForbiddenError
from app.interp.models import InterpAnalysis
from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.runs.models import Answer, RunMessage, SurveyRun
from app.templates.enums import AnswerType
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from app.trace.enums import SpanKind
from app.trace.models import LLMRequest, LLMSpan
from app.users.models import Band, Function, User, WorkspaceRole
from app.workspaces.models import (
    ResponseDeletionAudit,
    ResponseUsageTotal,
    WorkspaceRetentionChange,
)
from app.workspaces.schemas import RetentionUpdate
from app.workspaces.service import WorkspaceService


async def _owner(session) -> User:
    owner = User(
        email="owner@retention.test",
        display_name="Retention Owner",
        function=Function.hr,
        band=Band.manager,
        workspace_role=WorkspaceRole.owner,
    )
    session.add(owner)
    await session.flush()
    return owner


async def test_shortening_retention_requires_confirmation_and_is_audited(session):
    owner = await _owner(session)
    service = WorkspaceService(session)

    with pytest.raises(ConflictError):
        await service.update_retention(RetentionUpdate(retention_days=30), owner)

    updated = await service.update_retention(
        RetentionUpdate(retention_days=30, confirm_shorter=True), owner
    )
    assert updated.retention_days == 30
    change = await session.scalar(select(WorkspaceRetentionChange))
    assert change is not None
    assert (change.before_days, change.after_days, change.changed_by) == (90, 30, owner.id)


async def test_only_owner_changes_retention(session, author):
    with pytest.raises(ForbiddenError):
        await WorkspaceService(session).update_retention(
            RetentionUpdate(retention_days=30, confirm_shorter=True), author
        )


async def test_purge_deletes_content_and_keeps_non_identifying_usage(session, respondent):
    owner = await _owner(session)
    template = await TemplateService(session).create_draft(
        TemplateCreate(
            title="Retention survey",
            questions=[QuestionInput(text="What happened?", answer_type=AnswerType.short_text)],
        ),
        owner,
    )
    await TemplateService(session).publish(template.id, owner)
    await WorkspaceService(session).update_retention(
        RetentionUpdate(retention_days=1, confirm_shorter=True), owner
    )

    old = datetime.now(UTC) - timedelta(days=2)
    run = SurveyRun(
        template_id=template.id,
        respondent_id=respondent.id,
        status=RunStatus.completed,
        started_at=old,
        completed_at=old,
        llm_calls=2,
        llm_prompt_tokens=100,
        llm_completion_tokens=20,
        llm_unmetered_calls=1,
        llm_cost_usd=Decimal("0.12"),
    )
    question = template.questions[0]
    run.answers.append(
        Answer(
            question_id=question.id,
            kind=AnswerKind.scripted,
            question_text=question.text,
            value={"text": "secret answer"},
            answered_by=respondent.id,
            answered_at=old,
        )
    )
    run.messages.append(
        RunMessage(
            role=MessageRole.user,
            content="secret answer",
            created_at=old,
        )
    )
    session.add(run)
    await session.flush()

    span_id = uuid4()
    session.add(
        LLMSpan(
            id=span_id,
            run_id=run.id,
            kind=SpanKind.attempt,
            name="model",
            started_at=old,
            duration_ms=10,
        )
    )
    session.add(
        LLMRequest(
            span_id=span_id,
            run_id=run.id,
            messages=[{"role": "user", "content": "secret answer"}],
            tools=[],
            created_at=old,
        )
    )
    session.add(
        InterpAnalysis(
            span_id=span_id,
            run_id=run.id,
            model="qwen",
            revision="test",
            device="cpu",
            result={"reading": "secret"},
            duration_ms=1,
            created_at=old,
        )
    )
    session.add(
        EmbeddingVector(
            digest=digest("secret answer"),
            model="test-embedding",
            dimensions=2,
            vector=[0.1, 0.2],
        )
    )
    await session.commit()

    result = await WorkspaceService(session).purge_expired(owner)
    assert result.deleted_runs == 1
    assert result.deleted_completed_responses == 1
    assert result.retained_usage_months == 1
    assert await session.get(SurveyRun, run.id) is None
    assert await session.scalar(select(func.count()).select_from(LLMSpan)) == 0
    assert await session.scalar(select(func.count()).select_from(LLMRequest)) == 0
    assert await session.scalar(select(func.count()).select_from(InterpAnalysis)) == 0
    assert await session.scalar(select(func.count()).select_from(EmbeddingVector)) == 0
    audit = await session.scalar(select(ResponseDeletionAudit))
    assert audit is not None
    assert audit.triggered_by == owner.id
    totals = await session.scalar(select(ResponseUsageTotal))
    assert totals is not None
    assert (totals.completed_responses, totals.llm_calls, totals.llm_cost_usd) == (
        1,
        2,
        Decimal("0.12"),
    )


async def test_unfinished_response_uses_last_respondent_activity(session, respondent):
    owner = await _owner(session)
    template = await TemplateService(session).create_draft(
        TemplateCreate(
            title="Unfinished retention survey",
            questions=[QuestionInput(text="What happened?", answer_type=AnswerType.short_text)],
        ),
        owner,
    )
    old = datetime.now(UTC) - timedelta(days=3)
    recent = datetime.now(UTC) - timedelta(hours=12)
    run = SurveyRun(
        template_id=template.id,
        respondent_id=respondent.id,
        status=RunStatus.in_progress,
        started_at=old,
    )
    run.messages.append(
        RunMessage(role=MessageRole.user, content="still working", created_at=recent)
    )
    session.add(run)
    await session.flush()
    await WorkspaceService(session).update_retention(
        RetentionUpdate(retention_days=1, confirm_shorter=True), owner
    )

    first = await WorkspaceService(session).purge_expired(owner)
    assert first.deleted_runs == 0
    assert await session.get(SurveyRun, run.id) is not None

    run.messages[0].created_at = old
    await session.commit()
    second = await WorkspaceService(session).purge_expired(owner)
    assert second.deleted_runs == 1
