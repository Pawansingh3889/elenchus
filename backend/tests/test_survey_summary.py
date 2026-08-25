"""The author-facing recap of a whole survey.

The per-run summary's tests cover the gates it shares. What is tested here is what is
different: that the model never supplies a number, that the shape is fixed at a
headline, three findings, three suggestions, and an engine-written caveat, that a
suggestion is grounded in what a respondent proposed rather than the model's own advice,
and that a cache describing a moving set of responses does not go on being served after
they move.
"""

import pytest

from app.conduct.engine import ConductEngine
from app.errors import ConflictError, NotFoundError
from app.llm.client import ToolTurn
from app.runs.survey_summary import SurveySummaryService
from app.templates.enums import AnswerType
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from tests.fakes import FakeLLM, move_on, record

_QUOTE = "the guillotine drops out every other week"


def _recap(**overrides) -> ToolTurn:
    payload = {
        "headline": "The line stops most often at the guillotine, and nobody logs it.",
        "findings": [
            {"statement": "Most respondents named the same machine", "question_position": 0},
            {"statement": "Almost nobody reported the stoppage", "question_position": 1},
        ],
    }
    payload.update(overrides)
    return ToolTurn(text="", tool_name="summarise_survey", tool_input=payload)


def _faithful() -> ToolTurn:
    return ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={"headline_supported": True, "unsupported_findings": []},
    )


def _headline_refused(*problems: str) -> ToolTurn:
    return ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={"headline_supported": False, "problems": list(problems)},
    )


def _finding_refused(*indices: int) -> ToolTurn:
    return ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={
            "headline_supported": True,
            "unsupported_findings": list(indices),
            "problems": ["finding says most, but the tally does not show most"],
        },
    )


def _suggestion_refused(*indices: int) -> ToolTurn:
    return ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={
            "headline_supported": True,
            "unsupported_suggestions": list(indices),
            "problems": ["suggestion recommends something no respondent proposed"],
        },
    )


async def _surveyed(session, author, respondent):
    """A published two-question survey with one completed response."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Machine downtime",
            questions=[
                QuestionInput(
                    text="Which machine stops most often?", answer_type=AnswerType.short_text
                ),
                QuestionInput(text="Did you report it?", answer_type=AnswerType.yes_no),
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)
    run = await ConductEngine(session, llm=FakeLLM(record(_QUOTE), move_on())).handle_message(
        run.id, _QUOTE, respondent
    )
    await ConductEngine(session, llm=FakeLLM(record(False), move_on())).handle_message(
        run.id, "no", respondent
    )
    return template


async def test_recaps_a_survey_and_attaches_the_real_counts(session, author, respondent):
    """The point of `question_position`: the model says what the pattern is, and the
    numbers beside it are read out of the database rather than written by it."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(_recap(), _faithful())

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert recap.headline.startswith("The line stops")
    assert recap.runs_included == 1
    machine, reported = recap.findings
    assert machine.question_text == "Which machine stops most often?"
    assert machine.answered == 1
    assert [(c["label"], c["count"]) for c in reported.counts] == [("yes", 0), ("no", 1)]


async def test_a_finding_carrying_a_figure_is_refused(session, author, respondent):
    """The rail this recap is built on. A number the model wrote is a number nobody
    checked, and this codebase has already shipped one: a rating of 5 on a scale of 1 to 5
    summarised as "5 out of 10", where the value was real and only the scale invented."""
    template = await _surveyed(session, author, respondent)
    bad = _recap(findings=[{"statement": "7 of 8 named the guillotine", "question_position": 0}])
    llm = FakeLLM(bad, _recap(), _faithful())

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    # Rejected and redrafted rather than stored: the retry is the existing schema nudge.
    assert "figures" in llm.messages_seen[1][-1]["content"]
    assert all(not any(ch.isdigit() for ch in f.statement) for f in recap.findings)


async def test_a_finding_pointed_at_no_such_question_keeps_its_words(session, author, respondent):
    """Unpointed rather than dropped. The pattern may be real and only the reference
    wrong; attaching another question's tally to it would not be."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(
        _recap(findings=[{"statement": "Most named the same machine", "question_position": 9}]),
        _faithful(),
    )

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert recap.findings[0].statement == "Most named the same machine"
    assert recap.findings[0].question_position is None
    assert recap.findings[0].counts == []


async def test_a_stored_recap_is_reused_while_it_is_still_true(session, author, respondent):
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(_recap(), _faithful())
    await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    again = FakeLLM()  # any call would raise
    recap = await SurveySummaryService(session, llm=again).summarise(template.id, author)

    assert again.calls == 0
    assert recap.runs_included == 1


async def test_a_new_response_makes_the_stored_recap_wrong_not_stale(
    session, author, respondent, other_respondent
):
    """The difference from the per-run summary, and the reason this cache is conditional.
    A completed run never changes; a survey's responses keep arriving. Serving prose
    written from one response after a second has landed is serving wrong numbers, and
    nothing in the words would say so."""
    template = await _surveyed(session, author, respondent)
    await SurveySummaryService(session, llm=FakeLLM(_recap(), _faithful())).summarise(
        template.id, author
    )

    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, other_respondent)
    run = await ConductEngine(session, llm=FakeLLM(record("the press"), move_on())).handle_message(
        run.id, "the press", respondent=other_respondent
    )
    await ConductEngine(session, llm=FakeLLM(record(True), move_on())).handle_message(
        run.id, "yes", other_respondent
    )

    regenerated = FakeLLM(_recap(), _faithful())
    recap = await SurveySummaryService(session, llm=regenerated).summarise(template.id, author)

    assert regenerated.calls == 2  # it wrote a new one rather than serving the old
    assert recap.runs_included == 2


async def test_the_stored_recap_reads_back_without_a_model_call(session, author, respondent):
    """Reading a recap must not cost what writing one costs. Until this existed the only
    way to see a recap was to generate it, so a page that navigated away and back paid a
    model call to read prose already sitting in the column."""
    template = await _surveyed(session, author, respondent)
    await SurveySummaryService(session, llm=FakeLLM(_recap(), _faithful())).summarise(
        template.id, author
    )

    reader = FakeLLM()  # any call would raise
    status = await SurveySummaryService(session, llm=reader).stored(template.id, author)

    assert reader.calls == 0
    assert status.absence is None
    assert status.recap is not None
    assert status.recap.runs_included == 1
    assert status.recap.findings[0].question_text == "Which machine stops most often?"


async def test_a_survey_nobody_has_summarised_reads_as_never_generated(session, author, respondent):
    """Not a 404: a survey with responses and no recap is healthy, and the page invites
    a first one rather than reporting a missing resource."""
    template = await _surveyed(session, author, respondent)

    status = await SurveySummaryService(session, llm=FakeLLM()).stored(template.id, author)

    assert status.recap is None
    assert status.absence == "never_generated"


async def test_a_recap_the_results_moved_past_reads_as_outdated(
    session, author, respondent, other_respondent
):
    """The absence the page most needs to distinguish: a recap exists, it is simply no
    longer true of the numbers, and saying so is different from offering a first one."""
    template = await _surveyed(session, author, respondent)
    await SurveySummaryService(session, llm=FakeLLM(_recap(), _faithful())).summarise(
        template.id, author
    )

    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, other_respondent)
    run = await ConductEngine(session, llm=FakeLLM(record("the press"), move_on())).handle_message(
        run.id, "the press", respondent=other_respondent
    )
    await ConductEngine(session, llm=FakeLLM(record(True), move_on())).handle_message(
        run.id, "yes", other_respondent
    )

    status = await SurveySummaryService(session, llm=FakeLLM()).stored(template.id, author)

    assert status.recap is None
    assert status.absence == "outdated"


async def test_the_recap_carries_what_wrote_it(session, author, respondent):
    """Provenance was stored from the start and readable only by opening the column. A
    recap that reads worse than it used to may be a prompt change or a model change, and
    the author looking at it can now see which."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(_recap(), _faithful())

    written = await SurveySummaryService(session, llm=llm).summarise(template.id, author)
    read_back = await SurveySummaryService(session, llm=FakeLLM()).stored(template.id, author)

    assert written.prompt_version == "summarise_survey_v4"
    assert written.verify_prompt_version == "verify_survey_summary_v4"
    assert read_back.recap is not None
    assert read_back.recap.prompt_version == "summarise_survey_v4"
    assert read_back.recap.verify_prompt_version == "verify_survey_summary_v4"


async def test_reading_a_recap_of_someone_elses_survey_is_a_404(
    session, author, other_author, respondent
):
    """The read inherits the boundary the numbers have, because it goes through the same
    report() call that owns the ownership check."""
    template = await _surveyed(session, author, respondent)

    with pytest.raises(NotFoundError):
        await SurveySummaryService(session, llm=FakeLLM()).stored(template.id, other_author)


async def test_a_survey_nobody_has_finished_is_refused(session, author, respondent):
    """No responses is not a thin recap, it is no recap. Generating one would spend a
    model call to say nothing and leave prose above an empty page."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Nobody yet",
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )
    await svc.publish(template.id, author)

    with pytest.raises(ConflictError):
        await SurveySummaryService(session, llm=FakeLLM()).summarise(template.id, author)


async def test_a_recap_the_checker_refuses_twice_is_not_stored(session, author, respondent):
    """Nothing is stored, for the reason the run summary stores nothing: an unsupported
    recap sitting above the real numbers is worse than no recap at all."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(
        _recap(),
        _headline_refused("says most respondents named it, but only one answered"),
        _recap(),
        _headline_refused("still says most"),
    )

    with pytest.raises(ConflictError) as exc:
        await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    # A conflict, not an LLM failure. Every model call succeeded and the recap was
    # refused on its merits, so telling the author the assistant is briefly unavailable
    # would send them to retry something that fails identically, and would swallow the
    # only useful part: why it was refused.
    assert "still says most" in str(exc.value)  # the checker's own words reach the author
    await session.refresh(template)
    assert template.summary is None


async def test_another_author_cannot_recap_someone_elses_survey(
    session, author, other_author, respondent
):
    """The recap inherits exactly the boundary the numbers have: it is built from
    report(), which refuses first."""
    template = await _surveyed(session, author, respondent)

    with pytest.raises(NotFoundError):
        await SurveySummaryService(session, llm=FakeLLM()).summarise(template.id, other_author)


async def test_a_finding_the_checker_will_not_stand_behind_is_dropped(session, author, respondent):
    """One wrong finding costs one finding, not the recap.

    The all-or-nothing verdict the run summary uses is right for a run summary, whose
    claims stand together. A recap is independent findings, and refusing the lot means a
    *mistaken* checker costs the author everything: a live run threw a recap away because
    "the tally for Q9 shows 7 said yes and 1 said no, which does not support a majority
    belief", and seven of eight is a majority. A gate whose false positives cost the whole
    feature is a gate that gets switched off.
    """
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(_recap(), _finding_refused(1), _recap(), _finding_refused(1))

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert [f.statement for f in recap.findings] == ["Most respondents named the same machine"]
    assert recap.headline  # the rest of it stands


async def test_an_out_of_range_index_from_the_checker_drops_nothing(session, author, respondent):
    """The checker is a model and can name a finding that is not there. Ignored rather
    than trusted: an index nobody can act on must not silently take a real finding with
    it by landing on the wrong one."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(_recap(), _finding_refused(9), _recap(), _finding_refused(9))

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert len(recap.findings) == 2


async def test_findings_past_the_cap_are_trimmed_rather_than_refused(session, author, respondent):
    """A live run once lost a sound recap twice because the model returned one item
    more than a cap allowed, and the author was told the assistant was unavailable
    while nothing was. Trim the tail, serve the rest."""
    template = await _surveyed(session, author, respondent)
    finding = {"statement": "Most respondents named the same machine", "question_position": 0}
    llm = FakeLLM(_recap(findings=[finding] * 8), _faithful())

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert len(recap.findings) == 3
    assert llm.calls == 2  # no schema retry was needed


async def test_a_suggestion_is_recapped_with_the_real_counts(session, author, respondent):
    """`suggestions` gets the same treatment as `findings`: the model names the pattern
    and the question it draws on, the tally beside it comes from the database."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(
        _recap(
            suggestions=[
                {"statement": "Log every stoppage at the guillotine", "question_position": 0}
            ]
        ),
        _faithful(),
    )

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert len(recap.suggestions) == 1
    suggestion = recap.suggestions[0]
    assert suggestion.statement == "Log every stoppage at the guillotine"
    assert suggestion.question_text == "Which machine stops most often?"
    assert suggestion.answered == 1


async def test_a_suggestion_carrying_a_figure_is_refused(session, author, respondent):
    """A suggestion shares `Finding`'s no-digits rule: a fix stated as a number is a
    number nobody checked, exactly the failure mode `findings` is built to refuse."""
    template = await _surveyed(session, author, respondent)
    bad = _recap(
        suggestions=[{"statement": "Check the guillotine every 2 hours", "question_position": 0}]
    )
    llm = FakeLLM(bad, _recap(), _faithful())

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert "figures" in llm.messages_seen[1][-1]["content"]
    assert all(not any(ch.isdigit() for ch in s.statement) for s in recap.suggestions)


async def test_a_suggestion_the_checker_will_not_stand_behind_is_dropped(
    session, author, respondent
):
    """The same independence `findings` gets: a suggestion nobody actually proposed is
    dropped on its own rather than voiding a recap that is otherwise sound."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(
        _recap(
            suggestions=[
                {"statement": "Log every stoppage", "question_position": 0},
                {"statement": "Buy a new guillotine", "question_position": 0},
            ]
        ),
        _suggestion_refused(1),
        _recap(
            suggestions=[
                {"statement": "Log every stoppage", "question_position": 0},
                {"statement": "Buy a new guillotine", "question_position": 0},
            ]
        ),
        _suggestion_refused(1),
    )

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert [s.statement for s in recap.suggestions] == ["Log every stoppage"]
    assert recap.headline  # the rest of it stands


async def test_suggestions_past_the_cap_are_trimmed_rather_than_refused(
    session, author, respondent
):
    """Findings and suggestions are capped independently, on the same trim-the-tail
    rule: an over-long list past its cap loses only its tail, not the whole recap."""
    template = await _surveyed(session, author, respondent)
    suggestion = {"statement": "Log every stoppage at the guillotine", "question_position": 0}
    llm = FakeLLM(_recap(suggestions=[suggestion] * 8), _faithful())

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert len(recap.suggestions) == 3
    assert llm.calls == 2  # no schema retry was needed


async def test_the_caveat_is_the_engines_numbers(session, author, respondent):
    """The line that qualifies the findings is computed, never written: identical
    shape every recap, and nothing in it a model could get wrong. Reach is 2 here
    because the author and the respondent both hold jobs and the survey is aimed at
    everyone."""
    template = await _surveyed(session, author, respondent)
    llm = FakeLLM(_recap(), _faithful())

    recap = await SurveySummaryService(session, llm=llm).summarise(template.id, author)

    assert recap.caveat == "1 of 2 answered."
    stored = await SurveySummaryService(session, llm=FakeLLM()).stored(template.id, author)
    assert stored.recap is not None
    assert stored.recap.caveat == "1 of 2 answered."


def test_the_caveat_names_a_mostly_declined_question():
    """The qualifier, exercised directly: it appears only when it is true, so the
    ordinary recap stays one clause long.

    It used to have a second clause naming runs that answered an earlier version, which
    the report excluded. Versions are gone and nothing is excluded, so a caveat about an
    exclusion that cannot happen would be worse than no caveat at all."""
    from uuid import uuid4

    from app.runs.schemas import QuestionReport, SurveyReport
    from app.runs.survey_summary import _caveat

    def question(position: int, answered: int, declined: int) -> QuestionReport:
        return QuestionReport(
            id=uuid4(),
            position=position,
            text=f"Q{position}",
            answer_type="short_text",
            answered=answered,
            declined=declined,
            counts=[],
            average=None,
            low=None,
            high=None,
            verbatim=[],
            follow_ups=[],
            probed=0,
        )

    def report(**kw) -> SurveyReport:
        base = dict(
            template_id=uuid4(),
            title="T",
            runs_total=3,
            runs_completed=3,
            reach=8,
            people_started=4,
            people_completed=3,
            questions=[],
        )
        return SurveyReport(**{**base, **kw})

    assert _caveat(report()) == "3 of 8 answered."
    assert (
        _caveat(report(questions=[question(0, 3, 0), question(2, 1, 2)]))
        == "3 of 8 answered; question 3 was mostly declined."
    )


async def test_a_recap_written_under_an_older_shape_reads_as_outdated(session, author, respondent):
    """The stored document is the cache and its only natural expiry is the response
    count, so a recap written under the old shape (quotes, six findings, no caveat)
    would otherwise be served into a page that renders today's for as long as nobody
    else answered. The prompt version is part of the reuse condition instead."""
    template = await _surveyed(session, author, respondent)
    await SurveySummaryService(session, llm=FakeLLM(_recap(), _faithful())).summarise(
        template.id, author
    )
    await session.refresh(template)
    template.summary = {**template.summary, "prompt_version": "summarise_survey_v1"}
    await session.commit()

    status = await SurveySummaryService(session, llm=FakeLLM()).stored(template.id, author)

    assert status.recap is None
    assert status.absence == "outdated"
