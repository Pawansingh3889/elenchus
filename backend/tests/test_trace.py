"""Every turn leaves a tree: what it asked the model, what each call cost, what the engine
decided about each answer.

Each promise is tested by trying to break it: a refusal that must link to its retry, a
turn that fails and must still keep its record, a withdrawal that must take the spans
with it.
"""

import pytest

from app.conduct.engine import ConductEngine
from app.llm import ledger
from app.llm.client import LLMError, ToolTurn
from app.trace.enums import SpanKind
from app.trace.models import LLMSpan
from app.trace.repository import SpanRepository
from tests.fakes import FakeLLM, move_on, record

# ------------------------------------------------------------------ the ledger's half


def test_spans_outside_a_trace_are_dropped_and_inside_are_linked() -> None:
    with ledger.span("turn", "untraced"):
        pass  # nothing is collecting, and nothing needs to branch for it
    with ledger.tracing() as spans:
        with ledger.span("turn", "t") as turn:
            with ledger.span("decision", "d") as decision:
                pass
    assert [s.name for s in spans] == ["t", "d"]
    assert turn.parent_id is None
    assert decision.parent_id == turn.id


def test_a_span_keeps_the_exception_that_ended_it() -> None:
    with ledger.tracing() as spans:
        with pytest.raises(RuntimeError), ledger.span("decision", "d"):
            raise RuntimeError("boom")
    assert spans[0].error == "RuntimeError: boom"


def test_an_unknown_span_kind_fails_loudly() -> None:
    with pytest.raises(ValueError, match="unknown span kind"), ledger.span("guess", "x"):
        pass


def test_an_attempt_is_booked_under_the_span_that_was_open() -> None:
    usage = {"prompt_tokens": 10, "completion_tokens": 2}
    with ledger.tracing() as spans, ledger.span("decision", "d") as decision:
        ledger.record(
            tier=4,
            model="m",
            op="tool_turn",
            usage=usage,
            latency_ms=250,
            first_token_ms=200,
            status=200,
        )
    attempt = spans[1]
    assert attempt.kind == "attempt"
    assert attempt.parent_id == decision.id
    assert (attempt.duration_ms, attempt.first_token_ms, attempt.prompt_tokens) == (250, 200, 10)


# ------------------------------------------------------------------ the engine's half


def _of(spans: list[LLMSpan], kind: SpanKind) -> list[LLMSpan]:
    return sorted((s for s in spans if s.kind is kind), key=lambda s: s.started_at)


async def _started(session, respondent, published):
    return await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)


async def test_a_turn_leaves_a_tree_of_decisions_attempts_and_checks(
    session, respondent, published
):
    run = await _started(session, respondent, published)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."), serves_as=(1, "gpt-5.5"))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    spans = await SpanRepository(session).for_run(run.id)
    (turn,) = _of(spans, SpanKind.turn)
    decisions = _of(spans, SpanKind.decision)
    attempts = _of(spans, SpanKind.attempt)
    checks = _of(spans, SpanKind.validation)

    assert turn.parent_id is None
    assert [d.attrs["resolved_to"] for d in decisions] == ["record_answer", "move_on"]
    assert all(d.parent_id == turn.id for d in decisions)
    assert "record_answer" in decisions[0].attrs["tools_offered"]
    assert [a.parent_id for a in attempts] == [d.id for d in decisions]
    assert {(a.tier, a.model, a.status) for a in attempts} == {(1, "gpt-5.5", 200)}
    assert [(c.parent_id, c.attrs["outcome"]) for c in checks] == [
        (d.id, "accepted") for d in decisions
    ]


async def test_a_refused_action_links_to_the_retry_it_caused(session, respondent, published):
    run = await _started(session, respondent, published)
    llm = FakeLLM(
        ToolTurn(text="", tool_name="delete_everything", tool_input={}),
        record("Line lead"),
        move_on("Thanks."),
        serves_as=(1, "gpt-5.5"),
    )
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    spans = await SpanRepository(session).for_run(run.id)
    (refusal,) = [s for s in _of(spans, SpanKind.validation) if s.attrs["outcome"] == "refused"]
    assert refusal.attrs["tool"] == "delete_everything"
    assert "not available" in refusal.attrs["reason"]
    asked = next(s for s in spans if s.id == refusal.parent_id)
    (retry,) = [s for s in _of(spans, SpanKind.decision) if s.parent_id == asked.id]
    assert retry.attrs["retry"] is True
    # The refused ask resolved to what its retry chose, and the retry's cost sits under it.
    assert asked.attrs["resolved_to"] == "record_answer"
    assert [a.parent_id for a in _of(spans, SpanKind.attempt)][:2] == [asked.id, retry.id]


async def test_a_turn_that_fails_still_keeps_its_trace(session, respondent, published):
    """The turn commits nothing. Its spans are written in their own transaction, and are
    the only record of which tier failed and how."""
    run = await _started(session, respondent, published)
    llm = FakeLLM(LLMError("tier down"), serves_as=(1, "gpt-5.5"))
    run_id = run.id  # read now: the rollback below expires every loaded object
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run_id, "line lead", respondent)
    await session.rollback()

    spans = await SpanRepository(session).for_run(run_id)
    (turn,) = _of(spans, SpanKind.turn)
    assert turn.error is not None and turn.error.startswith("LLMError")
    (attempt,) = _of(spans, SpanKind.attempt)
    assert attempt.status == 0
    assert attempt.error is not None and "tier down" in attempt.error


async def test_withdrawing_a_run_takes_its_trace_with_it(session, respondent, published):
    run = await _started(session, respondent, published)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."), serves_as=(1, "gpt-5.5"))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    assert await SpanRepository(session).for_run(run.id)

    await ConductEngine(session, llm=FakeLLM()).delete_run(run.id, respondent)

    assert await SpanRepository(session).for_run(run.id) == []
