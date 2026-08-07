"""The AI summary of a completed run.

The summary is author-facing and acted on, so the tests that matter are the gates
between the model and the stored column, not that a happy path returns a string.
"""

import pytest

from app.conduct.engine import ConductEngine
from app.errors import ConflictError, NotFoundError
from app.llm.client import LLMError, ToolTurn
from app.runs.summary import RunSummaryService
from tests.fakes import FakeLLM, move_on, record

_QUOTE = "we still count stock on paper every Friday"


def _summary(**overrides) -> ToolTurn:
    payload = {
        "headline": "Two years in and still counting stock on paper.",
        "key_facts": ["Works as a line lead", "Weekly stock counts are manual"],
        "notable_quotes": [{"question": "What's your role?", "quote": _QUOTE}],
    }
    payload.update(overrides)
    return ToolTurn(text="", tool_name="summarise_run", tool_input=payload)


def _faithful() -> ToolTurn:
    return ToolTurn(text="", tool_name="report_verdict", tool_input={"faithful": True})


def _unfaithful(*problems: str) -> ToolTurn:
    return ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={"faithful": False, "problems": list(problems)},
    )


async def _completed(session, respondent, published):
    """A finished two-question run whose first answer contains the quotable sentence."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    engine = ConductEngine(session, llm=FakeLLM(record(_QUOTE), move_on()))
    run = await engine.handle_message(run.id, _QUOTE, respondent)
    engine = ConductEngine(session, llm=FakeLLM(record(4), move_on()))
    return await engine.handle_message(run.id, "4", respondent)


async def test_the_summariser_keeps_its_failover(session, author, respondent, published):
    """The writer and the checker have no nudged retry, so a chatty turn must fall to
    the next tier rather than ending the request. They keep the cascading default; only
    the conduct engine opts out of it."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(_summary(), _faithful())

    await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert llm.cascade_flags == [True, True]


async def test_summarises_a_completed_run_and_stores_it(session, author, respondent, published):
    run = await _completed(session, respondent, published)
    llm = FakeLLM(_summary(), _faithful())

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert content.headline.startswith("Two years in")
    assert content.key_facts == ["Works as a line lead", "Weekly stock counts are manual"]
    assert [q.quote for q in content.notable_quotes] == [_QUOTE]
    await session.refresh(run)
    assert run.summary["headline"] == content.headline
    assert run.summary["prompt_version"] == "summarise_run_v1"
    assert run.summary["verify_prompt_version"] == "verify_summary_v1"
    assert run.summary["generated_at"]


async def test_a_stored_summary_is_not_regenerated(session, author, respondent, published):
    """Generation costs model calls, so the column is the cache: one pass, then none."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(_summary(), _faithful())
    service = RunSummaryService(session, llm=llm)

    first = await service.summarise(published.id, run.id, author)
    second = await service.summarise(published.id, run.id, author)

    assert llm.calls == 2  # one draft, one verdict, and nothing for the second read
    assert first == second


async def test_refresh_regenerates_over_a_stored_summary(session, author, respondent, published):
    run = await _completed(session, respondent, published)
    llm = FakeLLM(
        _summary(),
        _faithful(),
        _summary(headline="A second look at the same run."),
        _faithful(),
    )
    service = RunSummaryService(session, llm=llm)

    await service.summarise(published.id, run.id, author)
    again = await service.summarise(published.id, run.id, author, refresh=True)

    assert llm.calls == 4
    assert again.headline == "A second look at the same run."


async def test_an_unfinished_run_is_refused(session, author, respondent, published):
    """Summarising a half-answered run would describe a response the respondent is still
    giving, and would cache that description as if it were final."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(_summary())

    with pytest.raises(ConflictError, match="completed"):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)
    assert llm.calls == 0  # refused before spending a model call


async def test_an_invented_quote_is_dropped_but_the_summary_survives(
    session, author, respondent, published
):
    """A quote the respondent never said is indistinguishable from a real one once it is
    rendered beside their answers. The rest of the summary is usually sound, so drop the
    quote rather than lose the whole thing."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(
        _summary(
            notable_quotes=[
                {"question": "What's your role?", "quote": _QUOTE},
                {"question": "Rate your onboarding", "quote": "the training was a shambles"},
            ]
        ),
        _faithful(),
    )

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert [q.quote for q in content.notable_quotes] == [_QUOTE]


async def test_a_quote_reflowed_by_the_model_is_kept(session, author, respondent, published):
    """Models re-wrap long quotes across lines and normalise spacing. That is not
    invention, and matching on raw bytes would throw away every genuine long quote."""
    run = await _completed(session, respondent, published)
    reflowed = _QUOTE.replace(" ", "\n  ").upper()
    llm = FakeLLM(_summary(notable_quotes=[{"question": "Q", "quote": reflowed}]), _faithful())

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert len(content.notable_quotes) == 1


async def test_stringified_lists_from_a_weak_model_are_decoded(
    session, author, respondent, published
):
    """Backup models emit the right list wrapped in a string; that is a serialization
    artifact, not a content problem."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(
        _summary(key_facts='["Works as a line lead", "Counts stock by hand"]'), _faithful()
    )

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert content.key_facts == ["Works as a line lead", "Counts stock by hand"]


async def test_an_invalid_summary_is_retried_once_then_fails_loudly(
    session, author, respondent, published
):
    run = await _completed(session, respondent, published)
    recovers = FakeLLM(_summary(headline="   "), _summary(), _faithful())

    content = await RunSummaryService(session, llm=recovers).summarise(published.id, run.id, author)
    assert recovers.calls == 3
    assert content.headline.startswith("Two years in")
    assert "rejected" in recovers.messages_seen[1][-1]["content"]

    stubborn = FakeLLM(_summary(headline=""))
    with pytest.raises(LLMError, match="after one retry"):
        await RunSummaryService(session, llm=stubborn).summarise(
            published.id, run.id, author, refresh=True
        )


async def test_another_author_cannot_summarise_someone_elses_run(
    session, author, other_author, respondent, published
):
    run = await _completed(session, respondent, published)
    llm = FakeLLM(_summary())

    with pytest.raises(NotFoundError):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, other_author)
    assert llm.calls == 0


async def test_the_checker_reads_fresh_context(session, author, respondent, published):
    """The checker's turn carries the answers and the candidate, and nothing of how the
    draft was made: not the writer's briefing, not the drafting conversation."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(_summary(), _faithful())

    await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert llm.offered == [["summarise_run"], ["report_verdict"]]
    (brief,) = llm.messages_seen[1]  # a single user message, no drafting history
    assert _QUOTE in brief["content"]
    assert "Two years in" in brief["content"]
    assert "Summarise it" not in brief["content"]
    assert "You had no part in writing it" in llm.briefings[1]


async def test_an_unsupported_summary_is_redrafted_with_the_checkers_notes(
    session, author, respondent, published
):
    """An unfaithful verdict goes back to the writer through the same channel a schema
    rejection uses, and the redraft is checked again from scratch."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(
        _summary(headline="Promoted to shift manager last spring."),
        _unfaithful("the headline reports a promotion the respondent never mentioned"),
        _summary(),
        _faithful(),
    )

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert content.headline.startswith("Two years in")
    assert llm.calls == 4
    redraft_note = llm.messages_seen[2][-1]["content"]
    assert "rejected" in redraft_note
    assert "promotion" in redraft_note


async def test_a_summary_the_checker_refuses_twice_is_not_stored(
    session, author, respondent, published
):
    """After the one send-back the gate is a hard no: an unsupported summary rendered
    beside the answers is worse than the author reading the answers themselves."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(
        _summary(),
        _unfaithful("the second fact is not in the answers"),
        _summary(),
        _unfaithful("the second fact is not in the answers"),
    )

    with pytest.raises(LLMError, match="could not be verified"):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    await session.refresh(run)
    assert run.summary is None


async def test_a_refusal_without_notes_is_an_invalid_verdict(
    session, author, respondent, published
):
    """'Fail, no reason given' cannot be sent back as notes, so it is rejected as a
    verdict rather than quietly treated as either answer."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(_summary(), _unfaithful())

    with pytest.raises(LLMError, match="invalid verdict"):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)


async def test_a_stringified_problems_list_is_decoded(session, author, respondent, published):
    """The same weak-model serialization slip the summary fields get absorbed for."""
    run = await _completed(session, respondent, published)
    stringified = ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={"faithful": False, "problems": '["the headline overreaches"]'},
    )
    llm = FakeLLM(_summary(), stringified, _summary(), _faithful())

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert llm.calls == 4
    assert "overreaches" in llm.messages_seen[2][-1]["content"]
    assert content.headline.startswith("Two years in")


async def test_the_redraft_after_reviewer_notes_still_gets_its_schema_retry(
    session, author, respondent, published
):
    """Reviewer notes and the schema retry are separate budgets. They used to share one
    variable, so the post-verification redraft arrived looking like it had already
    spent its retry and failed on its first malformed field."""
    run = await _completed(session, respondent, published)
    llm = FakeLLM(
        _summary(),  # draft 1: valid
        _unfaithful("the headline overstates the answers"),  # checker rejects it
        _summary(headline=""),  # redraft 1: schema-invalid (blank headline)
        _summary(headline="Counting stock on paper, two years in."),  # its retry: valid
        _faithful(),  # checker passes the corrected redraft
    )

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    assert content.headline == "Counting stock on paper, two years in."
    assert llm.calls == 5


async def test_summary_spend_lands_on_the_run(session, author, respondent, published):
    """The summary's calls are the largest a run ever makes; booked with run_id=null
    they were excluded from exactly the question the rollup exists to answer."""
    from app.llm import ledger

    class _MeteredSummaryLLM(FakeLLM):
        async def tool_turn(self, **kwargs):
            turn = await super().tool_turn(**kwargs)
            ledger.record(
                tier=4,
                model="llama3.2:3b",
                op="tool_turn",
                usage={"prompt_tokens": 900, "completion_tokens": 120},
                latency_ms=2000,
                status=200,
            )
            return turn

    run = await _completed(session, respondent, published)
    before = run.llm_calls

    llm = _MeteredSummaryLLM(_summary(), _faithful())
    await RunSummaryService(session, llm=llm).summarise(published.id, run.id, author)

    await session.refresh(run)
    assert run.llm_calls == before + 2  # the writer and the checker
    assert run.llm_prompt_tokens >= 1800
    assert run.llm_cost_usd > 0
