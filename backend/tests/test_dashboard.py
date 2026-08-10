"""The author's dashboard: every survey they own, and how each one is going.

The counts are the whole payload, so they are aggregated in the database. These tests are
about what the numbers mean rather than how they are produced, with one exception: the
survey nobody has answered has to appear, because an outer join is easy to get wrong in a
way that silently hides exactly the surveys an author is most likely to be checking on.
"""

import pytest

from app.conduct.engine import ConductEngine
from app.runs.service import ResultsService
from app.templates.enums import AnswerType, TemplateStatus
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from tests.fakes import FakeLLM
from tests.fakes import move_on as _move_on
from tests.fakes import record as _record

move_on = _move_on
record = _record


async def test_a_survey_nobody_has_answered_still_appears(session, author, published):
    rows = await ResultsService(session).dashboard(author)
    assert [r.title for r in rows] == ["Onboarding check-in"]
    assert rows[0].started == 0
    assert rows[0].completed == 0
    assert rows[0].last_started_at is None


async def test_completion_rate_is_none_rather_than_zero_when_nobody_started(
    session, author, published
):
    """0.0 would read as everyone abandoning. Nobody has answered, which is a different
    fact and the one an author needs on a survey they have just published."""
    rows = await ResultsService(session).dashboard(author)
    assert rows[0].completion_rate is None


async def test_counts_split_in_progress_from_completed(session, author, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)

    rows = await ResultsService(session).dashboard(author)
    assert (rows[0].started, rows[0].in_progress, rows[0].completed) == (1, 1, 0)
    assert rows[0].completion_rate == 0.0
    assert rows[0].last_started_at is not None

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    run = await ConductEngine(session, llm=FakeLLM(_record(4))).handle_message(
        run.id, "4", respondent
    )

    rows = await ResultsService(session).dashboard(author)
    assert (rows[0].started, rows[0].in_progress, rows[0].completed) == (1, 0, 1)
    assert rows[0].completion_rate == 1.0
    assert rows[0].last_completed_at is not None


async def test_closing_shows_on_the_dashboard(session, author, published):
    await TemplateService(session).close(published.id, author)
    rows = await ResultsService(session).dashboard(author)
    assert rows[0].status is TemplateStatus.closed
    assert rows[0].closed_at is not None


async def test_another_authors_survey_is_not_listed(session, author, other_author, published):
    """Scoped in the query, so someone else's survey is never loaded at all."""
    assert await ResultsService(session).dashboard(other_author) == []
    assert len(await ResultsService(session).dashboard(author)) == 1


async def test_a_draft_that_was_never_published_is_listed(session, author, published):
    """An author's dashboard is their surveys, not just the live ones. A draft with no
    version has no runs and joins to nothing, which is the row an inner join would drop."""
    await TemplateService(session).create_draft(
        TemplateCreate(
            title="Still a draft",
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )
    rows = await ResultsService(session).dashboard(author)
    assert {r.title for r in rows} == {"Onboarding check-in", "Still a draft"}
    draft = next(r for r in rows if r.title == "Still a draft")
    assert draft.started == 0
    assert draft.status is TemplateStatus.draft


async def test_the_dashboard_counts_people_as_well_as_runs(
    session, author, respondent, other_respondent, published
):
    """Two questions, two numbers. Runs answer "how is this going"; people answer "how
    many of the people it was for have answered", and one respondent with four runs read
    as four people until the engine started refusing a second."""
    for who in (respondent, other_respondent):
        run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, who)
        for answer in ("line lead", 4):
            run = await ConductEngine(
                session, llm=FakeLLM(record(answer), move_on())
            ).handle_message(run.id, str(answer), who)

    row = next(r for r in await ResultsService(session).dashboard(author) if r.id == published.id)

    assert (row.started, row.completed) == (2, 2)
    assert (row.people_started, row.people_completed) == (2, 2)
    # The audience is every respondent that exists, which here is the two who answered.
    assert row.reach == 2
    assert row.response_rate == pytest.approx(1.0)


async def test_a_survey_aimed_at_nobody_has_no_rate(session, author, published):
    """None rather than 0. A survey aimed at a team with nobody in it has no response
    rate, and 0% would read as everyone refusing rather than as nobody being asked.

    This survey is aimed at respondents and no respondent exists in this test, so the
    empty audience is real rather than constructed."""
    row = next(r for r in await ResultsService(session).dashboard(author) if r.id == published.id)

    assert row.reach == 0
    assert row.response_rate is None
