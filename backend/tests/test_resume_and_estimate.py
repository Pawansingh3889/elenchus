"""Save-and-continue, and the time estimate (SPEC.md 2.2 stretch 3 and 4).

Both live on the respondent's home, and both describe a survey before it is answered —
so both must describe the *published version*, not the draft that has moved on since.
"""

from app.conduct.engine import ConductEngine
from app.templates.enums import AnswerType
from app.templates.estimate import estimated_minutes
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.templates.service import TemplateService
from tests.fakes import FakeLLM, move_on, record


def _q(text: str, answer_type: AnswerType = AnswerType.short_text, **kw) -> QuestionInput:
    return QuestionInput(text=text, answer_type=answer_type, **kw)


# ------------------------------------------------------------------ the estimate


def test_the_estimate_reflects_how_long_each_type_takes() -> None:
    """A screen of ratings and a screen of essays are not the same survey."""
    taps = [{"answer_type": "rating"} for _ in range(4)]
    essays = [{"answer_type": "long_text"} for _ in range(4)]
    assert estimated_minutes(taps) < estimated_minutes(essays)


def test_the_estimate_is_never_zero_minutes() -> None:
    """'0 minutes' reads as 'no time at all', which no survey is."""
    assert estimated_minutes([{"answer_type": "yes_no"}]) == 1
    assert estimated_minutes([]) == 1


def test_questions_that_may_be_probed_cost_more() -> None:
    """Enough questions to clear the rounding to whole minutes — at three the extra
    probing time is real but disappears into the same minute."""
    plain = [{"answer_type": "long_text"} for _ in range(8)]
    probed = [{"answer_type": "long_text", "allow_follow_ups": True} for _ in range(8)]
    assert estimated_minutes(probed) > estimated_minutes(plain)


def test_an_unknown_type_still_counts_as_a_question() -> None:
    """A version written by a future build must not estimate as if it were empty."""
    assert estimated_minutes([{"answer_type": "hologram"}]) >= 1


# ------------------------------------------------- the published list describes the version


async def test_the_published_list_describes_the_version_not_the_draft(session, author):
    """The draft keeps evolving after publication. Counting its questions advertised a
    survey that does not exist yet — three questions on the home page, two in the run."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(title="Drift", questions=[_q("one"), _q("two")]), author
    )
    await svc.publish(template.id, author)
    await svc.update_draft(
        template.id,
        TemplateUpdate(title="Drift", questions=[_q("one"), _q("two"), _q("three")]),
        author,
    )

    listed = [row for row in await svc.list_published() if row[0].id == template.id]
    _, question_count, minutes = listed[0]

    assert question_count == 2  # what a respondent is actually asked
    assert minutes >= 1


async def test_republishing_moves_the_list_on_to_the_new_version(session, author):
    svc = TemplateService(session)
    template = await svc.create_draft(TemplateCreate(title="Grow", questions=[_q("one")]), author)
    await svc.publish(template.id, author)
    await svc.update_draft(
        template.id, TemplateUpdate(title="Grow", questions=[_q("one"), _q("two")]), author
    )
    await svc.publish(template.id, author)

    listed = [row for row in await svc.list_published() if row[0].id == template.id]
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
