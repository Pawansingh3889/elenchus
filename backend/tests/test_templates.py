"""Service-level tests for template CRUD, publishing, and version immutability."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.errors import ConflictError, NotFoundError
from app.runs.enums import RunStatus
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


async def test_publishing_twice_does_not_move_the_publication_date(session, author):
    """Publishing is idempotent, and the date it records is the first one.

    Editing after publication is refused now, so the only way to publish twice is to
    press the button twice. Moving the date then would rewrite the answer to "when did
    this go out", which is the question the field exists for.
    """
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Orig", questions=[_q("q1")]), author)
    first = await svc.publish(t.id, author)
    stamped = first.published_at

    again = await svc.publish(t.id, author)
    assert again.published_at == stamped
    assert again.status is TemplateStatus.published


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


async def test_a_published_survey_cannot_be_edited(session, author):
    """The property that dropping versions gave up, restored by the other route.

    There, the published copy was frozen and the draft went on evolving. Here there is
    one definition and publishing freezes it, so either way nobody's answer is
    re-pointed at a question they were not asked.
    """
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Live", questions=[_q("q1")]), author)
    await svc.publish(t.id, author)
    with pytest.raises(ConflictError) as refused:
        await svc.update_draft(t.id, update_of(t, title="Changed"), author)
    assert "cannot be edited" in str(refused.value.message)


async def test_an_unanswered_survey_can_be_deleted_outright(session, author):
    """Published but unanswered is the same situation as a draft: nothing anybody said
    is in it."""
    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Nobody home", questions=[_q("q1")]), author)
    await svc.publish(t.id, author)
    await svc.delete_survey(t.id, author)
    with pytest.raises(NotFoundError):
        await svc.get_draft(t.id, author)


async def test_a_survey_with_answers_refuses_to_be_deleted(session, author, respondent):
    """The one that matters. A survey with responses holds the only copy of what those
    people said, and no backup undoes this selectively: a restore brings back the whole
    database at a moment in time, not one survey out of it."""
    from app.conduct.engine import ConductEngine
    from tests.fakes import FakeLLM

    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Answered", questions=[_q("q1")]), author)
    await svc.publish(t.id, author)
    await ConductEngine(session, llm=FakeLLM()).start_run(t.id, respondent)

    with pytest.raises(ConflictError) as refused:
        await svc.delete_survey(t.id, author)
    assert "cannot be deleted" in str(refused.value.message)
    # And it is still there, which is the whole point of refusing.
    assert (await svc.get_draft(t.id, author)).title == "Answered"


async def test_an_abandoned_half_conversation_still_protects_the_survey(
    session, author, respondent
):
    """Any run counts, not just finished ones: an abandoned conversation is still
    something a person said, and deleting on the grounds that nobody finished would
    destroy it."""
    from app.conduct.engine import ConductEngine
    from tests.fakes import FakeLLM

    svc = TemplateService(session)
    t = await svc.create_draft(TemplateCreate(title="Half", questions=[_q("q1")]), author)
    await svc.publish(t.id, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(t.id, respondent)
    run.status = RunStatus.abandoned
    await session.commit()

    with pytest.raises(ConflictError):
        await svc.delete_survey(t.id, author)
