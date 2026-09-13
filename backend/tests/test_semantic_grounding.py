"""Semantic grounding in the engine, and the embedding lens.

The gate's rule is tried from both sides: an option the word check refuses is accepted
only when switched on and only when it is the closest of its question's options to what
was said, by the configured margin; an option that is not the closest stays refused, and
an embeddings outage leaves the refusal standing. Withdrawal must take the vectors with it,
and the lens serves the committed measurement with the headroom around its margin.
"""

import pytest_asyncio

from app.conduct.engine import ConductEngine, _unrecordable
from app.config import get_settings
from app.embeddings.models import EmbeddingVector
from app.embeddings.repository import EmbeddingRepository
from app.embeddings.service import EmbeddingService, digest
from app.runs.enums import MessageRole
from app.runs.models import RunMessage
from app.templates.enums import AnswerType, FollowUpPolicy
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from app.trace.enums import SpanKind
from app.trace.repository import SpanRepository
from app.users.models import Band, Function, User
from tests.fakes import FakeEmbedder, FakeLLM, move_on, record

SAID = "these days I work on the filleting line most shifts"


def _switched_on(monkeypatch, margin: float = 0.2) -> None:
    patched = get_settings().model_copy(
        update={"grounding_semantic_enabled": True, "grounding_similarity_margin": margin}
    )
    monkeypatch.setattr("app.conduct.engine.get_settings", lambda: patched)


@pytest_asyncio.fixture
async def department_survey(session, author):
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Where you work",
            questions=[
                QuestionInput(
                    text="Which department do you work in?",
                    answer_type=AnswerType.single_select,
                    options=["Processing", "Dispatch", "Maintenance"],
                    follow_up_policy=FollowUpPolicy.never,
                ),
                QuestionInput(text="Rate your shift", answer_type=AnswerType.rating),
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    return template


@pytest_asyncio.fixture
async def admin(session):
    user = User(
        email="embed-admin@plant.dev",
        display_name="Embed Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


async def _started(session, respondent, survey):
    return await ConductEngine(session, llm=FakeLLM()).start_run(survey.id, respondent)


async def _having_said(session, run, text: str = SAID):
    await session.refresh(run, ["messages"])
    run.messages.append(RunMessage(role=MessageRole.user, content=text))
    return run


# ------------------------------------------------------------------ the gate


def test_the_word_check_refuses_the_o12_case_on_its_own():
    question = {
        "answer_type": "single_select",
        "options": ["Processing", "Dispatch"],
        "allow_other": False,
        "required": True,
    }
    state = {"scripted_recorded": False, "scripted_value": None}
    # The raw value as the model sends it: the option's text.
    assert _unrecordable(question, state, "Processing", [SAID]) is not None
    # The same option, measured as the closest in meaning, is grounded.
    assert _unrecordable(question, state, "Processing", [SAID], frozenset({"Processing"})) is None


async def test_switched_on_the_closest_option_is_accepted_and_its_margin_is_on_the_span(
    session, respondent, department_survey, monkeypatch
):
    _switched_on(monkeypatch, margin=0.2)
    run = await _started(session, respondent, department_survey)
    embedder = FakeEmbedder(
        {
            SAID: [1.0, 0.0, 0.0],
            "Processing": [0.95, 0.1, 0.0],
            "Dispatch": [0.0, 1.0, 0.0],
            "Maintenance": [0.0, 0.0, 1.0],
        }
    )
    llm = FakeLLM(record("Processing"), move_on("Thanks."))
    run = await ConductEngine(session, llm=llm, embedder=embedder).handle_message(
        run.id, SAID, respondent
    )

    assert run.answers[0].value == {"option": "Processing"}
    spans = await SpanRepository(session).for_run(run.id)
    first = next(
        s for s in sorted(spans, key=lambda s: s.started_at) if s.kind is SpanKind.validation
    )
    assert first.attrs["outcome"] == "accepted"
    assert first.attrs["semantic_support"] == ["Processing"]
    assert first.attrs["margin"]["Processing"] > 0.2
    assert set(first.attrs["similarity"]) == {"Processing", "Dispatch", "Maintenance"}
    assert embedder.calls == [[SAID, "Processing", "Dispatch", "Maintenance"]]


async def test_switched_on_an_option_that_is_not_the_closest_gets_a_negative_margin(
    session, respondent, department_survey, monkeypatch
):
    _switched_on(monkeypatch, margin=0.2)
    run = await _having_said(session, await _started(session, respondent, department_survey))
    vectors = {
        SAID: [1.0, 0.0, 0.0],
        "Processing": [0.9, 0.1, 0.0],
        "Dispatch": [0.1, 1.0, 0.0],
        "Maintenance": [0.0, 0.0, 1.0],
    }
    engine = ConductEngine(session, llm=FakeLLM(), embedder=FakeEmbedder(vectors))
    question = (await engine.questions(run))[0]

    similarity, margins = await engine._option_margins(question, record("Dispatch"), run)

    assert set(similarity) == {"Processing", "Dispatch", "Maintenance"}
    assert list(margins) == ["Dispatch"]
    assert margins["Dispatch"] < 0


async def test_an_option_the_word_check_accepts_is_never_embedded(
    session, respondent, department_survey, monkeypatch
):
    _switched_on(monkeypatch)
    run = await _having_said(
        session, await _started(session, respondent, department_survey), "I work in dispatch"
    )
    embedder = FakeEmbedder()
    engine = ConductEngine(session, llm=FakeLLM(), embedder=embedder)
    question = (await engine.questions(run))[0]

    assert await engine._option_margins(question, record("dispatch"), run) == ({}, {})
    assert embedder.calls == []


async def test_an_embeddings_outage_leaves_the_refusal_standing(
    session, respondent, department_survey, monkeypatch
):
    _switched_on(monkeypatch)
    run = await _having_said(session, await _started(session, respondent, department_survey))
    engine = ConductEngine(session, llm=FakeLLM(), embedder=FakeEmbedder(fail=True))
    question = (await engine.questions(run))[0]
    assert await engine._option_margins(question, record("Processing"), run) == ({}, {})


async def test_switched_off_no_embedding_is_ever_asked_for(session, respondent, department_survey):
    run = await _having_said(session, await _started(session, respondent, department_survey))
    embedder = FakeEmbedder()
    engine = ConductEngine(session, llm=FakeLLM(), embedder=embedder)
    question = (await engine.questions(run))[0]
    assert await engine._option_margins(question, record("Processing"), run) == ({}, {})
    assert embedder.calls == []


async def test_withdrawing_a_run_deletes_the_vectors_of_what_was_said(
    session, respondent, published
):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead on nights", respondent)
    session.add(
        EmbeddingVector(
            digest=digest("line lead on nights"), model="any", dimensions=2, vector=[1.0, 0.0]
        )
    )
    await session.commit()

    await ConductEngine(session, llm=FakeLLM()).delete_run(run.id, respondent)

    assert await EmbeddingRepository(session).cached("any", [digest("line lead on nights")]) == {}


async def test_the_grounding_report_serves_the_measurement_with_its_headroom(session, admin):
    report = await EmbeddingService(session).grounding(admin)
    assert report.recommended_margin is not None
    assert report.highest_negative_margin is not None and report.lowest_positive_margin is not None
    assert report.highest_negative_margin < report.recommended_margin
    assert report.recommended_margin <= report.lowest_positive_margin
    assert report.sweep and len(report.judged) == report.pairs
