"""Service-level tests for template CRUD, publishing, and version immutability."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.errors import ConflictError, NotFoundError
from app.templates.enums import AnswerType, TemplateStatus
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from tests.builders import update_of


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


async def test_publish_opens_the_survey_and_records_when(session, author):
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="T", questions=[_q("q1")]), author)
    published = await svc.publish(t.id, author)
    assert published.status is TemplateStatus.published
    assert published.published_at is not None
    assert published.published_by == author.id


async def test_republishing_does_not_move_the_publication_date(session, author):
    """Re-opening a survey is not a new publication.

    This is what is left of versioning. There used to be a v1 frozen against edits and a
    v2 beside it; now an edit changes the one definition, and the only thing publish
    still records is when the survey first went out. Moving that date on every republish
    would rewrite the answer to "when did this go out", which is the question the field
    exists for.
    """
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Orig", questions=[_q("q1")]), author)
    first = await svc.publish(t.id, author)
    stamped = first.published_at

    await svc.update_draft(
        t.id, update_of(t, title="Changed", questions=[_q("q1"), _q("q2")]), author
    )
    again = await svc.publish(t.id, author)
    assert again.published_at == stamped
    # And the edit is simply live: there is no earlier copy of the questions anywhere.
    fetched = await svc.get_draft(t.id, author)
    assert fetched.title == "Changed"
    assert len(fetched.questions) == 2


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
    updated = await svc.update_draft(t.id, update_of(t, questions=[_q("c"), _q("a")]), author)
    assert [q.text for q in updated.questions] == ["c", "a"]
    assert [q.position for q in updated.questions] == [0, 1]


# The schema is the gate for both authoring paths — the builder and the LLM draft — so
# these hold whichever one produced the template.


def test_blank_text_is_refused_and_real_text_is_stored_trimmed():
    """min_length counts characters, not content: "   " satisfies it and renders as a
    question with nothing to read."""
    with pytest.raises(ValidationError):
        QuestionInput(text="   ", answer_type=AnswerType.short_text)
    with pytest.raises(ValidationError):
        TemplateCreate(title="   ", questions=[_q("q")])
    padded = QuestionInput(text="  How long?  ", answer_type=AnswerType.short_text)
    assert padded.text == "How long?"
    assert TemplateCreate(title="  Shift feedback  ").title == "Shift feedback"


def test_a_blank_option_is_refused():
    """A blank option renders as an empty choice, and the answer gate matches "" to it —
    so it is selectable by an empty answer."""
    with pytest.raises(ValidationError):
        QuestionInput(text="q", answer_type=AnswerType.single_select, options=["Days", "   "])


def test_options_that_collide_case_insensitively_are_refused():
    """Answers are matched to options case-insensitively, so "days" alongside "Days" is a
    choice the respondent can never land on and a count that can never be right."""
    with pytest.raises(ValidationError):
        QuestionInput(text="q", answer_type=AnswerType.single_select, options=["Days", "Days"])
    with pytest.raises(ValidationError):
        QuestionInput(text="q", answer_type=AnswerType.single_select, options=["Days", "days"])
    kept = QuestionInput(
        text="q", answer_type=AnswerType.single_select, options=[" Days ", "Nights"]
    )
    assert kept.options == ["Days", "Nights"]
