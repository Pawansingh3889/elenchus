"""The LLM spend ledger: what a call cost, and where that record ends up.

The point of these is arithmetic and honesty. A cost that is silently zero, or a token
count invented because a provider sent none, would look exactly like a working ledger
right up until someone tried to compare two models with it.
"""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.config import get_settings
from app.llm import ledger
from app.llm.ledger import TierEconomics, cost_usd


@pytest.fixture
def ledger_file(tmp_path, monkeypatch):
    """Point the ledger at a temp file and clear the settings cache around it.

    ``tier=4`` throughout this module means the local tier; conftest configures it as one
    for the whole suite, since it stopped being local by default when the Ollama service
    was removed.
    """
    path = tmp_path / "ledger.jsonl"
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_LEDGER_PATH", str(path))
    yield path
    get_settings.cache_clear()


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ------------------------------------------------------------------ pricing


def test_a_hosted_tier_is_priced_per_token() -> None:
    hosted = TierEconomics(
        params_b=70.0, local=False, price_in_per_mtok=0.5, price_out_per_mtok=1.5
    )
    # 1M in at $0.50 plus 1M out at $1.50.
    assert cost_usd(hosted, 1_000_000, 1_000_000, latency_ms=1234) == 2.0


def test_a_hosted_tiers_price_ignores_how_long_it_took() -> None:
    """Latency is recorded for every call, but it only *prices* a local one. A hosted
    tier charges for tokens whether it answered in a second or in a minute."""
    hosted = TierEconomics(params_b=8.0, local=False, price_in_per_mtok=1.0, price_out_per_mtok=1.0)
    quick = cost_usd(hosted, 1000, 1000, latency_ms=100)
    slow = cost_usd(hosted, 1000, 1000, latency_ms=100_000)
    assert quick == slow


def test_a_local_tier_is_priced_by_the_clock(ledger_file, monkeypatch) -> None:
    """A local tier bills no tokens. Pricing it per token reports every locally served
    run as free, which is the one number that is certainly wrong: it consumed the
    machine for as long as the call took."""
    get_settings.cache_clear()
    monkeypatch.setenv("HARDWARE_WATTS", "200")
    monkeypatch.setenv("ELECTRICITY_PRICE_PER_KWH", "0.30")
    local = TierEconomics(params_b=3.0, local=True, price_in_per_mtok=0, price_out_per_mtok=0)
    # One hour at 200W is 0.2 kWh, at $0.30 -> $0.06.
    assert cost_usd(local, 1000, 50, latency_ms=3_600_000) == pytest.approx(0.06)


def test_a_local_tier_costs_something_even_with_no_usage_reported(ledger_file, monkeypatch) -> None:
    """Ollama often returns no usage block. That must not make the call free, because
    the electricity was spent whether or not the tokens were counted."""
    get_settings.cache_clear()
    monkeypatch.setenv("HARDWARE_WATTS", "200")
    monkeypatch.setenv("ELECTRICITY_PRICE_PER_KWH", "0.30")
    local = TierEconomics(params_b=3.0, local=True, price_in_per_mtok=0, price_out_per_mtok=0)
    assert cost_usd(local, None, None, latency_ms=3_600_000) == pytest.approx(0.06)


def test_a_hosted_call_with_no_usage_costs_unknown_rather_than_zero() -> None:
    """Zero would sum into the run's rollup and understate it. None says so."""
    hosted = TierEconomics(params_b=8.0, local=False, price_in_per_mtok=1.0, price_out_per_mtok=1.0)
    assert cost_usd(hosted, None, None, latency_ms=500) is None


def test_an_unconfigured_tier_prices_nothing() -> None:
    """Distinct from a free tier, which is configured and genuinely costs 0."""
    assert cost_usd(None, 1000, 1000, latency_ms=500) is None
    assert ledger.economics_for(0) is None
    assert ledger.economics_for(9) is None


# ------------------------------------------------------------------ the record


def test_a_call_is_written_as_one_json_line(ledger_file) -> None:
    ledger.record(
        tier=4,
        model="llama3.2:3b",
        op="tool_turn",
        usage={"prompt_tokens": 1840, "completion_tokens": 96},
        latency_ms=30891,
        status=200,
    )
    (entry,) = _lines(ledger_file)
    assert entry["model"] == "llama3.2:3b"
    assert entry["op"] == "tool_turn"
    assert entry["tier"] == 4
    assert entry["prompt_tokens"] == 1840
    assert entry["completion_tokens"] == 96
    assert entry["latency_ms"] == 30891
    assert entry["status"] == 200
    # The axis the whole exercise turns on: the same token count means one thing from a
    # 3B model and another from a 70B one.
    assert entry["params_b"] == 3.0
    assert entry["local"] is True


def test_a_provider_that_sends_no_usage_records_nulls_not_zeros(ledger_file) -> None:
    """Zero tokens and unknown tokens are different facts, and averaging over a file that
    conflates them is how a model comes to look twice as efficient as it is."""
    ledger.record(tier=4, model="m", op="tool_turn", usage=None, latency_ms=10, status=200)
    (entry,) = _lines(ledger_file)
    assert entry["prompt_tokens"] is None
    assert entry["completion_tokens"] is None


def test_a_malformed_usage_block_does_not_reach_the_file(ledger_file) -> None:
    """Usage is metadata, so a tier sending a string where a count belongs records None
    rather than failing the survey. The tool call in the same response is validated."""
    ledger.record(
        tier=4,
        model="m",
        op="tool_turn",
        usage={"prompt_tokens": "lots", "completion_tokens": None},
        latency_ms=10,
        status=200,
    )
    (entry,) = _lines(ledger_file)
    assert entry["prompt_tokens"] is None
    assert entry["completion_tokens"] is None


def test_calls_append_rather_than_overwrite(ledger_file) -> None:
    for index in range(3):
        ledger.record(
            tier=4, model=f"m{index}", op="tool_turn", usage=None, latency_ms=1, status=200
        )
    assert [entry["model"] for entry in _lines(ledger_file)] == ["m0", "m1", "m2"]


def test_a_ledger_that_cannot_be_written_does_not_break_the_turn(tmp_path, monkeypatch) -> None:
    """The record is the point of the module, but it is not worth the conversation."""
    get_settings.cache_clear()
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("", encoding="utf-8")
    monkeypatch.setenv("LLM_LEDGER_PATH", str(blocker / "ledger.jsonl"))
    ledger.record(tier=4, model="m", op="tool_turn", usage=None, latency_ms=1, status=200)
    get_settings.cache_clear()


# ------------------------------------------------------------------ the rollup


def test_measuring_accumulates_every_call_in_the_block(ledger_file) -> None:
    with ledger.measuring(uuid4()) as spend:
        for _ in range(3):
            ledger.record(
                tier=4,
                model="llama3.2:3b",
                op="tool_turn",
                usage={"prompt_tokens": 100, "completion_tokens": 10},
                latency_ms=1000,
                status=200,
            )
    assert spend.calls == 3
    assert spend.prompt_tokens == 300
    assert spend.completion_tokens == 30
    assert spend.cost_usd > 0  # local tier, priced by the clock


def test_the_run_id_is_stamped_on_every_call_in_the_block(ledger_file) -> None:
    """What makes the file answerable per survey rather than only in aggregate."""
    run_id = uuid4()
    with ledger.measuring(run_id):
        ledger.record(tier=4, model="m", op="tool_turn", usage=None, latency_ms=1, status=200)
    ledger.record(tier=4, model="m", op="tool_call", usage=None, latency_ms=1, status=200)

    inside, outside = _lines(ledger_file)
    assert inside["run_id"] == str(run_id)
    assert outside["run_id"] is None  # a call outside any run is not attributed to one


def test_the_accumulator_does_not_leak_past_its_block(ledger_file) -> None:
    """Two runs served by the same worker must not inherit each other's spend."""
    with ledger.measuring(uuid4()) as first:
        ledger.record(tier=4, model="m", op="tool_turn", usage=None, latency_ms=1000, status=200)
    with ledger.measuring(uuid4()) as second:
        pass
    assert first.calls == 1
    assert second.calls == 0


def test_an_unpriced_hosted_tier_says_so_once_and_names_itself(ledger_file, caplog) -> None:
    """Zero is a legitimate price and also what an unconfigured tier looks like. The
    ledger cannot tell them apart, so it records 0.0 and says so, naming the tier so
    the operator knows which LLM_TIER<n> to price, rather than letting months of calls
    accumulate as costless."""
    ledger._UNPRICED_WARNED.clear()
    usage = {"prompt_tokens": 1000, "completion_tokens": 100}
    with caplog.at_level("WARNING", logger="app.llm.ledger"):
        ledger.record(tier=2, model="m", op="tool_turn", usage=usage, latency_ms=500, status=200)
        ledger.record(tier=2, model="m", op="tool_turn", usage=usage, latency_ms=500, status=200)
    warned = [r.getMessage() for r in caplog.records if "no price configured" in r.getMessage()]
    assert len(warned) == 1
    assert "tier 2" in warned[0] and "LLM_TIER2_PRICE_IN_PER_MTOK" in warned[0]


def test_a_priced_tier_is_not_warned_about(ledger_file, caplog, monkeypatch) -> None:
    from app.config import get_settings

    ledger._UNPRICED_WARNED.clear()
    monkeypatch.setenv("LLM_TIER2_PRICE_IN_PER_MTOK", "0.5")
    get_settings.cache_clear()
    usage = {"prompt_tokens": 1000, "completion_tokens": 100}
    with caplog.at_level("WARNING", logger="app.llm.ledger"):
        ledger.record(tier=2, model="m", op="tool_turn", usage=usage, latency_ms=500, status=200)
    assert not [r for r in caplog.records if "no price configured" in r.getMessage()]
    get_settings.cache_clear()


def test_a_local_tier_is_not_warned_about(ledger_file, caplog) -> None:
    """It is priced by the clock, so zero token prices are correct, not missing."""
    ledger._UNPRICED_WARNED.clear()
    with caplog.at_level("WARNING", logger="app.llm.ledger"):
        ledger.record(tier=4, model="m", op="tool_turn", usage=None, latency_ms=500, status=200)
    assert not [r for r in caplog.records if "no price configured" in r.getMessage()]


# ------------------------------------------------------------ unknown is not zero


def test_an_unmetered_hosted_call_is_counted_not_zeroed(ledger_file) -> None:
    """`cost or 0.0` folded "the provider reported nothing" into "it cost nothing" and
    the rollup understated itself with no marker. Unknowns are counted instead."""
    ledger._UNPRICED_WARNED.clear()
    with ledger.measuring(uuid4()) as spend:
        ledger.record(tier=2, model="m", op="tool_turn", usage=None, latency_ms=500, status=200)
    assert spend.calls == 1
    assert spend.unmetered_calls == 1
    assert spend.cost_usd == 0.0  # nothing KNOWN was spent; the counter says why


def test_a_local_call_without_usage_still_accumulates_its_clock_cost(ledger_file) -> None:
    """Tokens unknown, cost known: the electricity was spent whether or not the
    provider counted tokens, so the cost lands and the unmetered counter still says
    the token figures are incomplete."""
    with ledger.measuring(uuid4()) as spend:
        ledger.record(
            tier=4, model="m", op="tool_turn", usage=None, latency_ms=3_600_000, status=200
        )
    assert spend.cost_usd > 0
    assert spend.unmetered_calls == 1
    assert spend.prompt_tokens == 0


def test_a_fully_metered_call_is_not_flagged(ledger_file) -> None:
    usage = {"prompt_tokens": 100, "completion_tokens": 10}
    with ledger.measuring(uuid4()) as spend:
        ledger.record(tier=4, model="m", op="tool_turn", usage=usage, latency_ms=1000, status=200)
    assert spend.unmetered_calls == 0
