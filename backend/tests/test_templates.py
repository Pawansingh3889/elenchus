"""Service-level tests for template CRUD, publishing, and version immutability."""

from uuid import uuid4

import pytest

from app.errors import ConflictError, NotFoundError
from app.templates.enums import AnswerType, TemplateStatus
from app.templates.models import SurveyTemplateVersion
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.templates.service import TemplateService


def _q(text: str, answer_type: AnswerType = AnswerType.short_text) -> QuestionInput:
    return QuestionInput(text=text, answer_type=answer_type)


async def test_create_and_get_draft(session, author):
    svc = TemplateService(session)
    created = await svc.create_draft(
        TemplateCreate(title="T1", questions=[_q("q1"), _q("q2")]), author
    )
    fetched = await svc.get_draft(created.id, author)
    assert fetched.title == "T1"
    assert fetched.status is TemplateStatus.draft
    assert [q.text for q in fetched.questions] == ["q1", "q2"]
    assert [q.position for q in fetched.questions] == [0, 1]


async def test_publish_creates_version_one(session, author):
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="T", questions=[_q("q1")]), author)
    version = await svc.publish(t.id, author)
    assert version.version == 1
    assert (await svc.get_draft(t.id, author)).status is TemplateStatus.published


async def test_republish_increments_and_v1_is_immutable(session, author):
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Orig", questions=[_q("q1")]), author)
    v1 = await svc.publish(t.id, author)
    assert v1.version == 1

    # Edit the draft, then re-publish.
    await svc.update_draft(
        t.id, TemplateUpdate(title="Changed", questions=[_q("q1"), _q("q2")]), author
    )
    v2 = await svc.publish(t.id, author)
    assert v2.version == 2

    # v1's frozen snapshot must be untouched by the later edit — re-read from the db.
    fresh_v1 = await session.get(SurveyTemplateVersion, v1.id)
    assert fresh_v1 is not None
    assert fresh_v1.definition["title"] == "Orig"
    assert len(fresh_v1.definition["questions"]) == 1
    assert v2.definition["title"] == "Changed"
    assert len(v2.definition["questions"]) == 2


async def test_publish_empty_template_conflicts(session, author):
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Empty"), author)
    with pytest.raises(ConflictError):
        await svc.publish(t.id, author)


async def test_get_missing_template_not_found(session, author):
    with pytest.raises(NotFoundError):
        await TemplateService(session).get_draft(uuid4(), author)


async def test_update_replaces_questions(session, author):
    svc = TemplateService(session)
    t = await svc.create_draft(
        TemplateCreate(title="T", questions=[_q("a"), _q("b"), _q("c")]), author
    )
    updated = await svc.update_draft(
        t.id, TemplateUpdate(title="T", questions=[_q("c"), _q("a")]), author
    )
    assert [q.text for q in updated.questions] == ["c", "a"]
    assert [q.position for q in updated.questions] == [0, 1]
