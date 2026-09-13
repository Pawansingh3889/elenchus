"""The lens reads: admins only, and totals that add up to the spans under them."""

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

    def _book(self, *, status: int, error: str | None) -> None:
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
