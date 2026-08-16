"""Save-and-continue, and the time estimate (SPEC.md 2.2 stretch 3 and 4).

Both live on the respondent's home, and both describe a survey before it is answered —
so both must describe the *published version*, not the draft that has moved on since.
"""

import pytest

from app.conduct.engine import ConductEngine
from app.errors import ConflictError
from app.runs.enums import RunStatus
from app.templates.enums import AnswerType
from app.templates.estimate import estimated_minutes
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from tests.builders import update_of
from tests.fakes import FakeLLM, move_on, record


def _q(text: str, answer_type: AnswerType = AnswerType.short_text, **kw) -> QuestionInput:
    return QuestionInput(text=text, answer_type=answer_type, **kw)


# ------------------------------------------------------------------ the estimate


def _snap(answer_type: str, **kw: object) -> dict[str, object]:
    """A complete snapshot question, as ``templates.snapshot.questions_of`` yields.

    These tests used to pass bare ``{"answer_type": ...}`` dicts. That worked only
    because the estimate defaulted every key it could not find, which is the habit
    ``snapshot.py`` exists to end — a fixture shaped like nothing the application ever
    produces cannot show that the real thing works.
    """
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "position": 0,
        "text": "q",
        "answer_type": answer_type,
        "options": [],
        "allow_other": False,
        "required": True,
        "follow_up_policy": "never",
        "show_when": None,
        **kw,
    }


def test_the_estimate_reflects_how_long_each_type_takes() -> None:
    """A screen of ratings and a screen of essays are not the same survey."""
    taps = [_snap("rating") for _ in range(4)]
    essays = [_snap("long_text") for _ in range(4)]
    assert estimated_minutes(taps) < estimated_minutes(essays)


def test_the_estimate_is_never_zero_minutes() -> None:
    """'0 minutes' reads as 'no time at all', which no survey is."""
    assert estimated_minutes([_snap("yes_no")]) == 1
    assert estimated_minutes([]) == 1


def test_questions_that_may_be_probed_cost_more() -> None:
    """Enough questions to clear the rounding to whole minutes — at three the extra
    probing time is real but disappears into the same minute."""
    plain = [_snap("long_text") for _ in range(8)]
    probed = [_snap("long_text", follow_up_policy="when_unclear") for _ in range(8)]
    assert estimated_minutes(probed) > estimated_minutes(plain)


def test_an_unknown_type_still_counts_as_a_question() -> None:
    """A version written by a future build must not estimate as if it were empty.

    Unreachable from the application now that ``questions_of`` validates
    ``answer_type`` against the enum — kept because the helper is worth being safe on
    its own terms, and a future caller may not come through that gate.
    """
    assert estimated_minutes([_snap("hologram")]) >= 1


# ------------------------------------------------- the published list describes the version


async def test_the_published_list_describes_the_survey_as_it_stands(session, author):
    """An edit after publication is what a respondent will be asked.

    This test used to assert the opposite, and it was the point of versions: the draft
    kept evolving after publication, so counting its questions advertised a survey that
    did not exist yet, three on the home page and two in the run. With one definition
    there is no gap to mind, and the list describes exactly what the runner will ask."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(title="Drift", questions=[_q("one"), _q("two")]), author
    )
    await svc.publish(template.id, author)
    await svc.update_draft(
        template.id,
        update_of(template, title="Drift", questions=[_q("one"), _q("two"), _q("three")]),
        author,
    )

    listed = [row for row in await svc.list_published(author) if row[0].id == template.id]
    _, question_count, minutes, _answered = listed[0]

    assert question_count == 3  # the edit is live, and it is what will be asked
    assert minutes >= 1


async def test_republishing_moves_the_list_on_to_the_new_version(session, author):
    svc = TemplateService(session)
    template = await svc.create_draft(TemplateCreate(title="Grow", questions=[_q("one")]), author)
    await svc.publish(template.id, author)
    await svc.update_draft(
        template.id, update_of(template, title="Grow", questions=[_q("one"), _q("two")]), author
    )
    await svc.publish(template.id, author)

    listed = [row for row in await svc.list_published(author) if row[0].id == template.id]
    assert listed[0][1] == 2


# ------------------------------------------------------------------ resuming


async def test_an_unfinished_run_is_offered_back_to_its_respondent(
    session, author, respondent, published
):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    await ConductEngine(session, llm=FakeLLM(record("Line lead"), move_on())).handle_message(
        run.id, "line lead", respondent
    )

    resumable = await ConductEngine(session).resumable(respondent)

    assert len(resumable) == 1
    found, template_id, title, answered, total = resumable[0]
    assert found.id == run.id
    assert template_id == published.id
    assert title == "Onboarding check-in"
    assert (answered, total) == (1, 2)  # where they left off


async def test_a_finished_run_is_not_offered_again(session, author, respondent, published):
    """Resuming a completed survey would let a respondent answer it twice."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    for reply, turn in (("line lead", record("Line lead")), ("4", record(4))):
        run = await ConductEngine(session, llm=FakeLLM(turn, move_on())).handle_message(
            run.id, reply, respondent
        )

    assert run.status.value == "completed"
    assert await ConductEngine(session).resumable(respondent) == []


async def test_one_respondent_never_sees_another_persons_run(
    session, author, respondent, other_respondent, published
):
    engine = ConductEngine(session, llm=FakeLLM())
    await engine.start_run(published.id, respondent)

    assert len(await ConductEngine(session).resumable(respondent)) == 1
    assert await ConductEngine(session).resumable(other_respondent) == []


async def test_starting_again_returns_the_run_already_under_way(session, respondent, published):
    """Start becomes Continue rather than opening a second run.

    The respond page already turned Start into Continue when an unfinished run existed,
    but that was an affordance and not a rule: a direct POST opened a second run and
    stranded the first half-answered. One respondent accumulated four runs on one survey
    this way, which the dashboard reported as four responses.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    first = await engine.start_run(published.id, respondent)
    await ConductEngine(session, llm=FakeLLM(record("Line lead"), move_on())).handle_message(
        first.id, "line lead", respondent
    )

    again = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)

    assert again.id == first.id
    assert len(again.answers) == 1  # the answer already given is still theirs


async def test_a_survey_already_answered_is_refused(session, respondent, published):
    """The other half. A finished run is the one response this person has, and starting
    over would let them answer twice and count twice."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    for answer in ("line lead", "4"):
        run = await ConductEngine(
            session, llm=FakeLLM(record(answer if answer != "4" else 4), move_on())
        ).handle_message(run.id, answer, respondent)
    assert run.status is RunStatus.completed

    with pytest.raises(ConflictError) as caught:
        await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    # Three conditions in start_run raise ConflictError, so the message proves which.
    assert "already answered" in caught.value.message.lower()


async def test_one_persons_answer_does_not_block_another(
    session, respondent, other_respondent, published
):
    """The guard is per person. A survey everyone is asked would otherwise be answerable
    once in total, which is the opposite of the point."""
    engine = ConductEngine(session, llm=FakeLLM())
    mine = await engine.start_run(published.id, respondent)
    theirs = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, other_respondent)

    assert mine.id != theirs.id


async def test_republishing_does_not_reopen_a_survey_already_answered(
    session, author, respondent, published
):
    """Keyed on the survey, not the version it was published as.

    A run belongs to the survey it answered. Keying on the version would mean an author
    fixing a typo and republishing silently reopens the survey to everyone who has been
    through it, and their second answers would land in the same results as their first.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    for answer in ("line lead", 4):
        run = await ConductEngine(session, llm=FakeLLM(record(answer), move_on())).handle_message(
            run.id, str(answer), respondent
        )
    assert run.status is RunStatus.completed

    svc = TemplateService(session)
    draft = await svc.get_draft(published.id, author)
    await svc.update_draft(published.id, update_of(draft, title="Onboarding check-in v2"), author)
    await svc.publish(published.id, author)

    with pytest.raises(ConflictError):
        await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)


async def test_a_survey_already_answered_is_marked_on_the_respondents_list(
    session, author, respondent, other_respondent, published
):
    """The list is an invitation, and after one-answer-per-person a Start button on a
    survey this reader has finished is a button that can only 409. The row stays: a
    survey that vanishes reads as a bug rather than as "you have already done it"."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    for answer in ("line lead", 4):
        run = await ConductEngine(session, llm=FakeLLM(record(answer), move_on())).handle_message(
            run.id, str(answer), respondent
        )
    assert run.status is RunStatus.completed

    svc = TemplateService(session)
    mine = {t.id: answered for t, _, _, answered in await svc.list_published(respondent)}
    theirs = {t.id: answered for t, _, _, answered in await svc.list_published(other_respondent)}

    assert mine[published.id] is True
    # Per person, not per survey: it is still an invitation for everyone else.
    assert theirs[published.id] is False


async def test_an_unfinished_run_does_not_mark_a_survey_answered(session, respondent, published):
    """Half-answered is not answered. They are meant to continue it, which is what the
    resumable list is for, and marking it answered would strip the way back in."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    await ConductEngine(session, llm=FakeLLM(record("Line lead"), move_on())).handle_message(
        run.id, "line lead", respondent
    )

    listed = {
        t.id: answered
        for t, _, _, answered in await TemplateService(session).list_published(respondent)
    }
    assert listed[published.id] is False
