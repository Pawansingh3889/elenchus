"""The lens reads: admins only, and totals that add up to the spans under them."""

from typing import Any

import pytest
import pytest_asyncio

from app.conduct.engine import ConductEngine
from app.errors import ForbiddenError, NotFoundError
from app.llm import ledger
from app.llm.client import LLMError, ToolTurn
from app.trace.service import LensService
from app.users.models import Band, Function, User
from tests.fakes import FakeLLM, move_on, record


class _MeteredLLM(FakeLLM):
    """Books every call the way the real client does: tokens, cached tokens, a first
    token and a latency, on tier 4, which the suite prices by the clock."""

    def _book(self, *, status: int, error: str | None, request: dict[str, Any]) -> None:
        ledger.record(
            tier=4,
            model="local-3b",
            op="tool_turn",
            usage=(
                None
                if error
                else {
                    "prompt_tokens": 1000,
                    "completion_tokens": 20,
                    "prompt_tokens_details": {"cached_tokens": 600},
                }
            ),
            latency_ms=1200,
            first_token_ms=None if error else 1100,
            status=status,
            error=error,
            request=request,
        )


@pytest_asyncio.fixture
async def admin(session):
    """Administration is the IT function, at any band."""
    user = User(
        email="lens-admin@plant.dev",
        display_name="Lens Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


async def _one_good_turn(session, respondent, published, *turns: ToolTurn):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = _MeteredLLM(*(turns or (record("Line lead"), move_on("Thanks."))))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    return run


async def test_a_traced_run_adds_up_to_its_spans(session, respondent, published, admin):
    run = await _one_good_turn(session, respondent, published)

    (traced,) = await LensService(session).runs(admin)

    assert traced.run_id == run.id
    assert traced.survey_title == published.title
    assert (traced.turns, traced.decisions, traced.retries) == (1, 2, 0)
    assert (traced.attempts, traced.failed_attempts, traced.unmetered_attempts) == (2, 0, 0)
    assert (traced.prompt_tokens, traced.completion_tokens, traced.cached_tokens) == (
        2000,
        40,
        1200,
    )
    assert traced.cost_usd is not None and traced.cost_usd > 0
    assert traced.first_token_ms_p50 == 1100


async def test_a_retry_is_counted_on_its_run(session, respondent, published, admin):
    await _one_good_turn(
        session,
        respondent,
        published,
        ToolTurn(text="", tool_name="delete_everything", tool_input={}),
        record("Line lead"),
        move_on("Thanks."),
    )
    (traced,) = await LensService(session).runs(admin)
    assert traced.retries == 1
    assert traced.decisions == 3


async def test_the_strip_totals_each_tier_including_failed_attempts(
    session, respondent, published, admin
):
    run = await _one_good_turn(session, respondent, published)
    run_id = run.id  # read now: the rollback below expires every loaded object
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=_MeteredLLM(LLMError("tier down"))).handle_message(
            run_id, "and another thing", respondent
        )
    await session.rollback()
    await session.refresh(admin)  # the rollback expired it, and the service reads its job

    strip = await LensService(session).strip(admin)

    assert (strip.runs, strip.turns, strip.retries) == (1, 2, 0)
    (tier,) = strip.tiers
    assert (tier.tier, tier.model) == (4, "local-3b")
    assert (tier.attempts, tier.failed_attempts, tier.unmetered_attempts) == (3, 1, 1)
    assert tier.latency_ms_p50 == 1200
    # The failed attempt has no first token, and the percentile skips it rather than
    # reading it as zero.
    assert tier.first_token_ms_p50 == 1100


async def test_only_admins_read_the_lens(session, respondent, published, author):
    run = await _one_good_turn(session, respondent, published)
    lens = LensService(session)
    with pytest.raises(ForbiddenError):
        await lens.runs(author)
    with pytest.raises(ForbiddenError):
        await lens.spans(run.id, author)
    with pytest.raises(ForbiddenError):
        await lens.strip(author)


async def test_a_run_without_a_trace_is_not_found(session, respondent, published, admin):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    with pytest.raises(NotFoundError, match="no trace"):
        await LensService(session).spans(run.id, admin)


# ------------------------------------------------------------------ factor rows


async def test_attempt_rows_are_placed_in_their_turn_and_marked_as_retries(
    session, respondent, published, admin
):
    run = await _one_good_turn(
        session,
        respondent,
        published,
        ToolTurn(text="", tool_name="delete_everything", tool_input={}),
        record("Line lead"),
        move_on("Thanks."),
    )
    rows = await LensService(session).attempts(admin, None, None)

    assert [row.retry for row in rows] == [False, True, False]
    assert {row.turn_number for row in rows} == {1}
    assert {row.run_id for row in rows} == {run.id}
    assert all(row.survey_title == published.title for row in rows)
    assert all(row.first_token_ms == 1100 and row.cached_tokens == 600 for row in rows)


async def test_decision_rows_carry_the_check_and_their_own_cost(
    session, respondent, published, admin
):
    await _one_good_turn(
        session,
        respondent,
        published,
        ToolTurn(text="", tool_name="delete_everything", tool_input={}),
        record("Line lead"),
        move_on("Thanks."),
    )
    refused, retry, move = await LensService(session).decisions(admin, None, None)

    assert (refused.picked, refused.outcome) == ("delete_everything", "refused")
    assert refused.reason is not None and "not available" in refused.reason
    assert refused.resolved_to == "record_answer"
    assert (retry.retry, retry.picked, retry.outcome) == (True, "record_answer", "accepted")
    # Each ask counts only its own attempt, so the refusal's cost is not the retry's.
    assert (refused.attempts, retry.attempts, move.attempts) == (1, 1, 1)
    assert refused.cost_usd is not None and refused.cost_usd == retry.cost_usd
    assert refused.recorded_this_turn is False and move.recorded_this_turn is True
    assert "record_answer" in refused.tools_offered


async def test_factor_rows_narrow_to_a_survey_or_a_run(session, respondent, published, admin):
    run = await _one_good_turn(session, respondent, published)
    lens = LensService(session)
    assert len(await lens.attempts(admin, published.id, None)) == 2
    assert len(await lens.decisions(admin, None, run.id)) == 2
    other_survey = run.id  # any id that is not a survey id matches nothing
    assert await lens.attempts(admin, other_survey, None) == []


async def test_only_admins_read_factor_rows(session, respondent, published, author):
    await _one_good_turn(session, respondent, published)
    lens = LensService(session)
    with pytest.raises(ForbiddenError):
        await lens.attempts(author, None, None)
    with pytest.raises(ForbiddenError):
        await lens.decisions(author, None, None)


async def test_traced_runs_name_their_survey_for_the_filter(session, respondent, published, admin):
    await _one_good_turn(session, respondent, published)
    (traced,) = await LensService(session).runs(admin)
    assert traced.template_id == published.id


# ------------------------------------------------------------------ correlations


async def test_correlations_flag_a_small_sample_and_never_invent_an_interval(
    session, respondent, published, admin
):
    await _one_good_turn(session, respondent, published)
    matrix = await LensService(session).correlations(admin, None, None)

    assert matrix.min_samples == 20
    assert len(matrix.cells) == len(matrix.factors) * len(matrix.outcomes)
    cell = next(c for c in matrix.cells if (c.factor, c.outcome) == ("tokens_in", "first_token_ms"))
    assert cell.n == 2 and cell.too_few
    assert cell.ci_low is None and cell.ci_high is None
    # Every call in this turn had the same tokens in: no rank order, so no coefficient.
    assert cell.rho is None and cell.no_variation


async def test_only_admins_read_correlations(session, respondent, published, author):
    await _one_good_turn(session, respondent, published)
    with pytest.raises(ForbiddenError):
        await LensService(session).correlations(author, None, None)
