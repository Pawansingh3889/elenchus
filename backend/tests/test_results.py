"""Reading results back: what an author gets, and what they are refused.

Results cross respondents by design, so the boundary that matters here is the template
a run belongs to, not the person who answered it.
"""

from uuid import UUID, uuid4

import pytest

from app.conduct.engine import ConductEngine
from app.errors import NotFoundError
from app.llm.client import ToolTurn
from app.runs.enums import AnswerKind, RunStatus
from app.runs.models import REPLY_PREFIX
from app.runs.service import ResultsService
from app.templates.enums import AnswerType
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from tests.builders import update_of
from tests.fakes import FakeLLM, follow_up, move_on, record, reply


async def _answer_first(session, run, respondent):
    llm = FakeLLM(record("Line lead"), move_on())
    return await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)


async def test_lists_who_answered_and_how_far_they_got(session, author, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    summaries = await ResultsService(session).list_runs(published.id, author)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.id == run.id
    assert summary.respondent_label == "Respondent 1"
    assert summary.status is RunStatus.in_progress
    assert (summary.answered, summary.total) == (1, 2)
    assert summary.completed_at is None


async def test_a_run_is_re_scored_when_the_author_rewrites_the_survey(
    session, author, respondent, published
):
    """The author rewrites the survey mid-run, and the response IS re-scored.

    This is the cost of dropping versions, pinned so nobody meets it by surprise. The
    test it replaces asserted the opposite and was the guarantee: a run answered the
    questions frozen at publish, and an author editing afterwards could not change what
    an existing response was scored against. Now there is one definition, so the run's
    total follows the edit, and the only record of what was actually asked is the
    `question_text` stored on each answer row.
    """
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    svc = TemplateService(session)
    await svc.update_draft(
        published.id,
        update_of(
            published,
            title="Rewritten",
            questions=[QuestionInput(text="One question now", answer_type=AnswerType.long_text)],
        ),
        author,
    )
    await svc.publish(published.id, author)

    summary = (await ResultsService(session).list_runs(published.id, author))[0]
    # One question now, so the run that answered two is measured against one.
    assert summary.total == 1


async def test_detail_returns_the_answers_and_the_transcript(
    session, author, respondent, published
):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    detail = await ResultsService(session).get_run(published.id, run.id, author)

    assert detail.respondent_label == "Respondent 1"
    assert [a.question_text for a in detail.answers] == ["What's your role?"]
    assert detail.answers[0].value == {"text": "Line lead"}
    assert [m.role.value for m in detail.messages] == ["assistant", "user", "assistant"]


async def test_a_follow_up_is_ordered_under_the_question_it_probed(
    session, author, respondent, published
):
    """Results attach a follow-up to its parent, so ordering and the shared id both matter."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    probe = FakeLLM(record("Line lead"), follow_up("What does that involve day to day?"))
    run = await ConductEngine(session, llm=probe).handle_message(run.id, "line lead", respondent)
    reply = FakeLLM(record("Running the handover"), move_on())
    await ConductEngine(session, llm=reply).handle_message(run.id, "the handover", respondent)

    answers = (await ResultsService(session).get_run(published.id, run.id, author)).answers

    assert [a.kind.value for a in answers] == ["scripted", "follow_up"]
    assert answers[0].question_id == answers[1].question_id  # the follow-up's parent
    assert answers[0].answered_at < answers[1].answered_at
    assert answers[1].question_text == "What does that involve day to day?"


async def test_a_run_from_another_template_is_not_found(session, author, respondent, published):
    other = await TemplateService(session).create_draft(
        TemplateCreate(
            title="A different survey",
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )
    await TemplateService(session).publish(other.id, author)
    stray = await ConductEngine(session, llm=FakeLLM()).start_run(other.id, respondent)

    with pytest.raises(NotFoundError):
        await ResultsService(session).get_run(published.id, stray.id, author)


async def test_missing_template_is_not_found(session, author, published):
    with pytest.raises(NotFoundError):
        await ResultsService(session).list_runs(uuid4(), author)


def test_every_answer_shape_flattens_to_a_readable_cell():
    from app.runs.service import flatten_answer

    assert flatten_answer({"text": "Line lead"}) == "Line lead"
    assert flatten_answer({"rating": 4}) == "4"
    assert flatten_answer({"yes_no": False}) == "no"
    assert flatten_answer({"option": "Days"}) == "Days"
    assert flatten_answer({"options": ["A", "B"], "other": ["C"]}) == "A; B; (other) C"
    assert flatten_answer({"other": "Split shift"}) == "(other) Split shift"
    assert flatten_answer({"unanswerable": "declined"}) == "(declined) declined"
    assert flatten_answer({"mystery": 1}) == '{"mystery": 1}'  # future shapes never crash


async def test_follow_up_spend_is_visible_even_when_no_follow_up_answer_exists(
    session, author, respondent, published
):
    """The case that motivated exposing this at all.

    A probe is charged when the engine issues it, and a probe often draws out the
    scripted answer itself — so the run records one scripted answer and no follow-up
    row. Counting follow-up answers would report "never probed", which is how a live
    acceptance walkthrough twice concluded the feature was broken when it was not.
    """
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    probed = FakeLLM(follow_up("Which line do you run?"))
    run = await ConductEngine(session, llm=probed).handle_message(run.id, "bit of both", respondent)

    detail = await ResultsService(session).get_run(published.id, run.id, author)
    question_id = UUID(next(iter(run.probes_asked)))

    assert not [a for a in detail.answers if a.kind is AnswerKind.follow_up]
    assert detail.follow_ups_asked == {question_id: 1}


async def test_replies_are_not_reported_as_follow_ups(session, author, respondent, published):
    """Replies share the probes JSONB under a prefix. That is storage, not survey data,
    and an author counting follow-ups must not see it."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    chatty = FakeLLM(reply("It means your job title."))
    run = await ConductEngine(session, llm=chatty).handle_message(
        run.id, "what do you mean?", respondent
    )

    detail = await ResultsService(session).get_run(published.id, run.id, author)

    assert any(k.startswith(REPLY_PREFIX) for k in run.probes_asked)  # it was stored
    assert detail.follow_ups_asked == {}  # but never surfaced


async def test_a_run_that_was_never_probed_reports_nothing(session, author, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    detail = await ResultsService(session).get_run(published.id, run.id, author)

    assert detail.follow_ups_asked == {}


async def _reportable(session, author):
    """A published survey with one question of each shape the report tallies."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Hygiene on the floor",
            questions=[
                QuestionInput(
                    text="Which aspects need improvement?",
                    answer_type=AnswerType.multi_select,
                    options=["Cleaning", "Waste", "PPE"],
                    allow_other=True,
                ),
                QuestionInput(
                    text="Are practices followed consistently?", answer_type=AnswerType.yes_no
                ),
                QuestionInput(text="Rate the hygiene overall", answer_type=AnswerType.rating),
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    return template


async def _answer_all(session, template, respondent, values):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)
    for value in values:
        llm = FakeLLM(record(value), move_on())
        run = await ConductEngine(session, llm=llm).handle_message(run.id, str(value), respondent)
    return run


async def test_the_report_tallies_every_question(session, author, respondent, other_respondent):
    """The question a survey is run to answer, which nothing here could answer before:
    what did people say. The dashboard counts runs and the results page shows one person
    at a time; an author with forty respondents opened forty runs or a spreadsheet."""
    template = await _reportable(session, author)
    await _answer_all(session, template, respondent, [["Cleaning", "Waste"], True, 4])
    await _answer_all(session, template, other_respondent, [["Cleaning"], False, 2])

    report = await ResultsService(session).report(template.id, author)

    assert report.runs_total == 2
    aspects, consistent, rated = report.questions
    # The author's order, and every option present: a zero is a finding, a missing row
    # reads as an option nobody was offered.
    assert [(c.label, c.count) for c in aspects.counts] == [
        ("Cleaning", 2),
        ("Waste", 1),
        ("PPE", 0),
    ]
    assert [(c.label, c.count) for c in consistent.counts] == [("yes", 1), ("no", 1)]
    assert rated.average == 3.0
    assert [(c.label, c.count) for c in rated.counts if c.count] == [("2", 1), ("4", 1)]


async def test_a_write_in_is_counted_and_kept_verbatim(session, author, respondent):
    """The part the option list could not anticipate. Counted as its own row rather than
    folded into an option, and kept word for word rather than grouped: what someone meant
    is a judgement, and this page is the numbers."""
    template = await _reportable(session, author)
    await _answer_all(
        session, template, respondent, [["Cleaning", "drains blocked again"], True, 3]
    )

    aspects = (await ResultsService(session).report(template.id, author)).questions[0]

    write_ins = [c for c in aspects.counts if c.write_in]
    assert [(c.label, c.count) for c in write_ins] == [("drains blocked again", 1)]
    assert aspects.verbatim == ["drains blocked again"]


async def test_a_declined_question_is_counted_apart_from_an_answered_one(
    session, author, respondent
):
    """A question everyone skipped and a question nobody reached are different findings,
    and averaging over the wrong denominator is how a survey gets quoted wrongly."""
    template = await _reportable(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)
    declining = FakeLLM(
        ToolTurn(
            text="No problem.",
            tool_name="flag_unanswerable",
            tool_input={"reason": "would rather not say"},
        )
    )
    await ConductEngine(session, llm=declining).handle_message(run.id, "pass", respondent)

    aspects = (await ResultsService(session).report(template.id, author)).questions[0]
    assert (aspects.answered, aspects.declined) == (0, 1)
    assert all(c.count == 0 for c in aspects.counts)


async def test_runs_against_an_older_version_are_excluded_and_counted(
    session, author, respondent, other_respondent
):
    """A republish gives every question a new id, so those answers are not answers to
    these questions. Folding them in would quietly change what a number means, so they
    are left out and the omission is put on the page."""
    template = await _reportable(session, author)
    await _answer_all(session, template, respondent, [["Cleaning"], True, 5])

    svc = TemplateService(session)
    draft = await svc.get_draft(template.id, author)
    await svc.update_draft(
        template.id,
        update_of(
            draft,
            questions=[
                QuestionInput(
                    text="Which aspects need improvement?",
                    answer_type=AnswerType.multi_select,
                    options=["Cleaning", "Waste", "PPE"],
                    allow_other=True,
                )
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    await _answer_all(session, template, other_respondent, [["PPE"]])

    report = await ResultsService(session).report(template.id, author)
    # Both runs count. Before, the earlier one was excluded and reported as excluded,
    # because it had answered different questions under different ids; there is one set
    # of questions now, so there is nothing to exclude and nothing to say about it.
    assert report.runs_total == 2
    assert [(c.label, c.count) for c in report.questions[0].counts] == [
        ("Cleaning", 0),
        ("Waste", 0),
        ("PPE", 1),
    ]


async def test_the_report_shows_what_a_probe_drew_out(session, author, respondent, published):
    """The report counted scripted answers and discarded every follow-up, so the part of
    the conversation an author most wants to read was visible only in the export and one
    run at a time. A live survey asked eight people whether they had reported a heat
    problem: four said yes, and the page could say nothing about what happened next."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    probing = FakeLLM(follow_up("What does that involve day to day?", "Line lead"))
    run = await ConductEngine(session, llm=probing).handle_message(run.id, "line lead", respondent)
    elaborating = FakeLLM(record("stock counts and rotas, mostly"), move_on())
    run = await ConductEngine(session, llm=elaborating).handle_message(
        run.id, "stock counts and rotas, mostly", respondent
    )
    await ConductEngine(session, llm=FakeLLM(record(4), move_on())).handle_message(
        run.id, "4", respondent
    )

    role, rated = (await ResultsService(session).report(published.id, author)).questions

    assert role.verbatim == ["Line lead"]  # the scripted answer, as before
    assert role.follow_ups == ["stock counts and rotas, mostly"]
    assert role.answered == 1
    assert role.probed == 1
    # Counting runs, not probes, so it reads against `answered` on the same scale.
    assert rated.probed == 0
    assert rated.follow_ups == []


async def test_a_follow_up_never_joins_the_tally(session, author, respondent, published_yes_no):
    """A probe answers a question the model wrote, in whatever shape that question needed.
    On a yes/no it comes back as prose, and letting it near `counts` would invent a third
    row in a two-row tally."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published_yes_no.id, respondent)
    probing = FakeLLM(follow_up("Which issues have you hit?", True))
    run = await ConductEngine(session, llm=probing).handle_message(run.id, "yes", respondent)
    elaborating = FakeLLM(record("the scanner keeps dropping out"), move_on())
    run = await ConductEngine(session, llm=elaborating).handle_message(
        run.id, "the scanner keeps dropping out", respondent
    )
    await ConductEngine(session, llm=FakeLLM(record(3), move_on())).handle_message(
        run.id, "3", respondent
    )

    issues, rated = (await ResultsService(session).report(published_yes_no.id, author)).questions

    assert [(c.label, c.count) for c in issues.counts] == [("yes", 1), ("no", 0)]
    assert issues.follow_ups == ["the scanner keeps dropping out"]
    assert issues.probed == 1
    # The probe is prose on a rated question elsewhere in the survey too: no average moves.
    assert rated.average == 3.0


async def test_a_declined_probe_is_counted_but_not_quoted(session, author, respondent, published):
    """ "Would rather not say" is not words the respondent gave to the question. It stays
    out of the quotes on the same rule the tallies use, but the run still counts as
    probed: asked and declined is a finding, and silence would read as never asked."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    probing = FakeLLM(follow_up("What does that involve?", "Line lead"))
    run = await ConductEngine(session, llm=probing).handle_message(run.id, "line lead", respondent)
    declining = FakeLLM(
        ToolTurn(
            text="",
            tool_name="flag_unanswerable",
            tool_input={"question_id": "x", "reason": "would rather not say"},
        )
    )
    run = await ConductEngine(session, llm=declining).handle_message(
        run.id, "rather not", respondent
    )
    await ConductEngine(session, llm=FakeLLM(record(4), move_on())).handle_message(
        run.id, "4", respondent
    )

    role = (await ResultsService(session).report(published.id, author)).questions[0]

    assert role.follow_ups == []
    assert role.probed == 1
    assert role.answered == 1  # the scripted answer banked before the probe survives


async def test_a_report_needs_a_published_version(session, author):
    """An unpublished draft has no frozen questions to count against, and inventing an
    empty report would read as a survey nobody answered rather than one never asked."""
    template = await TemplateService(session).create_draft(
        TemplateCreate(
            title="Not published",
            questions=[QuestionInput(text="q", answer_type=AnswerType.yes_no)],
        ),
        author,
    )
    with pytest.raises(NotFoundError):
        await ResultsService(session).report(template.id, author)


async def test_the_report_is_scoped_to_the_owning_author(session, author, other_author):
    template = await _reportable(session, author)
    with pytest.raises(NotFoundError):
        await ResultsService(session).report(template.id, other_author)


async def test_a_number_question_reports_its_spread_not_just_an_average(
    session, author, respondent, other_respondent
):
    """An average was the whole of what a number question reported, and it hides the
    difference between everyone saying twenty and half saying five while half say forty.
    A rating has its counts to show shape; a number had nothing else at all."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Downtime",
            questions=[
                QuestionInput(
                    text="How many minutes does the line wait?", answer_type=AnswerType.number
                )
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    for who, value in ((respondent, 10), (other_respondent, 45)):
        run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, who)
        await ConductEngine(session, llm=FakeLLM(record(value), move_on())).handle_message(
            run.id, str(value), who
        )

    question = (await ResultsService(session).report(template.id, author)).questions[0]

    assert question.answered == 2
    assert question.average == 27.5
    assert (question.low, question.high) == (10, 45)


# ------------------------------------------------------------------ who said it


async def test_the_author_sees_a_number_rather_than_a_name(
    session, author, respondent, other_respondent, published
):
    """Agreed 10 Aug: no names on answers. The author still needs to tell one person's
    answers from another's, which a number does; what it does not do is tell them which
    colleague said the thing about their employer."""
    first = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, first, respondent)
    second = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, other_respondent)
    await _answer_first(session, second, other_respondent)

    summaries = await ResultsService(session).list_runs(published.id, author)
    labels = {s.id: s.respondent_label for s in summaries}

    assert labels[first.id] == "Respondent 1"
    assert labels[second.id] == "Respondent 2"
    assert not any("Respondent " in s.respondent_label[len("Respondent ") :] for s in summaries)


async def test_the_number_is_the_order_people_answered_in(
    session, author, respondent, other_respondent, published
):
    """Ordered by first run rather than by name or id, so it reads as a sequence rather
    than an arbitrary permutation, and so it does not change when a display name does."""
    second_to_answer = await ConductEngine(session, llm=FakeLLM()).start_run(
        published.id, other_respondent
    )
    await _answer_first(session, second_to_answer, other_respondent)
    first_to_answer = await ConductEngine(session, llm=FakeLLM()).start_run(
        published.id, respondent
    )
    await _answer_first(session, first_to_answer, respondent)

    labels = {
        s.id: s.respondent_label
        for s in await ResultsService(session).list_runs(published.id, author)
    }
    assert labels[second_to_answer.id] == "Respondent 1"
    assert labels[first_to_answer.id] == "Respondent 2"


async def test_the_same_person_carries_one_label_across_list_and_detail(
    session, author, respondent, other_respondent, published
):
    """The label is only worth having if it is stable. An author reading the list, opening
    a response and going back must be looking at the same person throughout, or the
    numbering is worse than no numbering: they would trust it and be wrong."""
    first = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, first, respondent)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, other_respondent)
    await _answer_first(session, run, other_respondent)

    service = ResultsService(session)
    from_list = next(s for s in await service.list_runs(published.id, author) if s.id == run.id)
    from_detail = await service.get_run(published.id, run.id, author)

    assert from_list.respondent_label == from_detail.respondent_label == "Respondent 2"


async def test_the_matrix_puts_every_answer_beside_the_person_who_gave_it(
    session, author, respondent, other_respondent
):
    """The question the report cannot answer. Per-question tallies say what each question
    found; they cannot say whether the people who picked one thing also picked another,
    and reconstructing that took one request per run."""
    template = await _reportable(session, author)
    await _answer_all(session, template, respondent, [["Cleaning", "Waste"], True, 4])
    await _answer_all(session, template, other_respondent, [["Cleaning"], False, 2])

    matrix = await ResultsService(session).answers_matrix(template.id, author)

    assert [q.text for q in matrix.questions] == [
        "Which aspects need improvement?",
        "Are practices followed consistently?",
        "Rate the hygiene overall",
    ]
    # The author's option list travels with the question, so a slice can offer an option
    # nobody picked rather than only what happens to be in the data.
    assert matrix.questions[0].options == ["Cleaning", "Waste", "PPE"]
    # Newest first, the order the run list already uses. The numbering is by when each
    # person first answered, so the labels run backwards down a newest-first table and
    # that is the same person either way round.
    assert [r.respondent_label for r in matrix.runs] == ["Respondent 2", "Respondent 1"]

    # The join itself: one person's answers, in one place, unaggregated.
    first = next(r for r in matrix.runs if r.respondent_label == "Respondent 1")
    by_question = {str(a.question_id): a.value for a in first.answers}
    aspects, consistent, rated = (str(q.id) for q in matrix.questions)
    assert by_question[aspects]["options"] == ["Cleaning", "Waste"]
    assert by_question[consistent]["yes_no"] is True
    assert by_question[rated]["rating"] == 4


async def test_the_matrix_carries_raw_values_not_printable_ones(session, author, respondent):
    """A slice keys on the stored shape. Flattened to strings, "Cleaning" the option and
    "Cleaning" typed as a write-in would land in one bucket, which is the distinction the
    tallies are most careful about."""
    template = await _reportable(session, author)
    await _answer_all(
        session, template, respondent, [["Cleaning", "drains blocked again"], True, 3]
    )

    matrix = await ResultsService(session).answers_matrix(template.id, author)

    aspects = next(a for a in matrix.runs[0].answers if a.question_id == matrix.questions[0].id)
    assert aspects.value["options"] == ["Cleaning"]
    assert aspects.value["other"] == ["drains blocked again"]


async def test_the_matrix_includes_unfinished_runs_and_says_so(
    session, author, respondent, other_respondent, published
):
    """The report tallies answers from runs still in progress, so the matrix must describe
    the same people. A matrix over completed runs only would produce sliced totals that
    disagreed with the unsliced ones printed beside them."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    matrix = await ResultsService(session).answers_matrix(published.id, author)

    assert [r.status for r in matrix.runs] == [RunStatus.in_progress]
    assert matrix.runs[0].completed_at is None
    assert len(matrix.runs[0].answers) == 1


async def test_the_matrix_carries_follow_up_answers_with_their_kind(
    session, author, respondent, published
):
    """A follow-up answers a question the model wrote, so it can never join a tally. It is
    still what the respondent elaborated, and the client shows it beside the answer it
    came from, so it travels with its kind rather than being dropped."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    probing = FakeLLM(follow_up("What does that involve day to day?", "Line lead"))
    run = await ConductEngine(session, llm=probing).handle_message(run.id, "line lead", respondent)
    elaborating = FakeLLM(record("stock counts and rotas, mostly"), move_on())
    await ConductEngine(session, llm=elaborating).handle_message(
        run.id, "stock counts and rotas, mostly", respondent
    )

    matrix = await ResultsService(session).answers_matrix(published.id, author)

    answers = matrix.runs[0].answers
    assert [a.kind for a in answers] == [AnswerKind.scripted, AnswerKind.follow_up]
    # The model's own question travels with it, because the author reading the probe
    # needs to know what was asked to make sense of what came back.
    assert answers[1].question_text == "What does that involve day to day?"


async def test_the_matrix_covers_every_run_now_that_versions_are_gone(
    session, author, respondent, other_respondent, published
):
    """The report's rule, and for the report's reason.

    It used to be the opposite: a run that answered different questions under different
    ids could not join these columns, so it was left out and named. With one definition
    per survey there are no other ids, so every run joins the matrix, including one that
    answered questions the author has since rewritten. The columns are the survey as it
    stands; an older run simply has nothing under the new ones."""
    stale = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, stale, respondent)

    svc = TemplateService(session)
    await svc.update_draft(
        published.id,
        update_of(
            published,
            questions=[QuestionInput(text="One question now", answer_type=AnswerType.long_text)],
        ),
        author,
    )
    await svc.publish(published.id, author)
    current = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, other_respondent)
    llm = FakeLLM(record("a fresh answer"), move_on())
    await ConductEngine(session, llm=llm).handle_message(
        current.id, "a fresh answer", other_respondent
    )

    matrix = await ResultsService(session).answers_matrix(published.id, author)

    assert {r.run_id for r in matrix.runs} == {stale.id, current.id}


async def test_the_matrix_labels_match_the_run_list(
    session, author, respondent, other_respondent, published
):
    """The label is the survey's own pseudonym and also the key the recap's quote gate
    matches on. An author moving between the table and a response must be looking at the
    same person, or the numbering is worse than none: they would trust it and be wrong."""
    first = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, first, respondent)
    second = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, other_respondent)
    await _answer_first(session, second, other_respondent)

    service = ResultsService(session)
    from_list = {s.id: s.respondent_label for s in await service.list_runs(published.id, author)}
    matrix = await service.answers_matrix(published.id, author)

    assert {r.run_id: r.respondent_label for r in matrix.runs} == from_list


async def test_the_matrix_is_scoped_to_the_owning_author(session, author, other_author, published):
    """Every answer in the survey with the respondent beside it is the most attribution
    dense payload in the API, so it inherits exactly the boundary the numbers have."""
    with pytest.raises(NotFoundError):
        await ResultsService(session).answers_matrix(published.id, other_author)


async def test_a_matrix_needs_a_published_version(session, author):
    template = await TemplateService(session).create_draft(
        TemplateCreate(
            title="Draft only",
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )

    with pytest.raises(NotFoundError):
        await ResultsService(session).answers_matrix(template.id, author)
