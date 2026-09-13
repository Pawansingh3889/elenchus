"""The LLM spend ledger: one durable record per model call, and what it cost.

Two readers, deliberately one writer. The JSONL file is for offline analysis, where a
question like "did the 3B local model answer as well as the hosted tier, and at what
cost?" needs rows rather than log lines. The rollup on ``survey_runs`` is for the app, so
the cost of a conversation can be read without parsing a file.

Cost is computed here, at the moment of the call, rather than derived later from the
tokens. The price of a call is a fact about when it was made: tariffs and per-token rates
change, and a ledger that recomputed history against today's rate would quietly restate
what last month's experiment cost.

This module owns no transport and no session. It is imported by the one client that does
own the HTTP calls, and by the conduct engine, which reads the rollup back.
"""

import inspect
import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.config import get_settings

logger = logging.getLogger("app.llm.ledger")

SECONDS_PER_HOUR = 3600.0
WATTS_PER_KILOWATT = 1000.0
TOKENS_PER_MILLION = 1_000_000.0
# Enough places to keep a single cheap call from rounding to zero: a 30-second local turn
# at 200W and £0.25/kWh is about $0.0004, and at 6dp that is still four significant
# figures. Rounding at all is deliberate, so a float's tail does not reach the file.
COST_PLACES = 8


@dataclass
class Spend:
    """What the model calls inside one block added up to, for the run rollup.

    The token and cost figures are sums of what was *reported*; ``unmetered_calls``
    counts the calls that reported nothing, so a total of $0.03 over 6 calls with 2
    unmetered reads as "at least", not "exactly". Folding unknowns in as zero would
    make a hosted tier that omits usage look free next to a local one that is priced
    by the clock.
    """

    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    unmetered_calls: int = 0
    # Which tier and model actually answered, last one wins. The chain tries tiers in
    # order and a turn may be retried, so "who served this" is only known once the block
    # is done: it is the last call that came back with a usable body, and that is the one
    # whose words the respondent read. None while nothing has answered yet, and still None
    # after a block where every tier failed, which is the honest record of a turn nobody
    # served rather than a guess at tier 1.
    last_tier: int | None = None
    last_model: str | None = None


_SPEND: ContextVar[Spend | None] = ContextVar("llm_spend", default=None)
_RUN_ID: ContextVar[str | None] = ContextVar("llm_run_id", default=None)
_PROMPT: ContextVar[str | None] = ContextVar("llm_prompt", default=None)
_SOURCE_FILE: ContextVar[str | None] = ContextVar("llm_source_file", default=None)
_SOURCE_LINE: ContextVar[int | None] = ContextVar("llm_source_line", default=None)


@contextmanager
def measuring(run_id: UUID | None = None) -> Iterator[Spend]:
    """Collect the spend of every model call made inside this block.

    A context variable rather than an argument threaded through ``LLMProtocol``. That
    protocol is the seam a provider is swapped at, and widening it so the transport can
    be told which run it is serving would put run bookkeeping into the contract every
    future client has to implement, for a field none of them would use.

    Nesting is safe and the tokens are reset on the way out, so a turn that fails partway
    leaves no accumulator behind for the next request on the same worker.
    """
    spend = Spend()
    spend_token = _SPEND.set(spend)
    run_token = _RUN_ID.set(str(run_id) if run_id is not None else None)
    try:
        yield spend
    finally:
        _SPEND.reset(spend_token)
        _RUN_ID.reset(run_token)


@contextmanager
def using_prompt(name: str) -> Iterator[None]:
    """Name the prompt every model call made inside this block is running under.

    A context variable for the same reason ``measuring`` is one: ``LLMProtocol`` is the
    seam a provider is swapped at, and threading a prompt name through it would put
    authoring bookkeeping into a transport contract that has no use for it.

    Without this the ledger records which *model* served a call and never which prompt
    asked it, so a version bump leaves the whole history unattributable: every row before
    and after reads identically, and "which version regressed this" cannot be answered
    from the file that exists to answer it.
    """
    token = _PROMPT.set(name)
    try:
        yield
    finally:
        _PROMPT.reset(token)


@contextmanager
def from_call_site() -> Iterator[None]:
    """Capture the source file and line number where the LLM call is made.

    This provides code-level transparency for each LLM call, allowing admins to drill
    down from token usage to the exact code location that triggered the call. This is
    essential for debugging, optimization, and understanding which parts of the codebase
    are driving LLM usage and costs.
    """
    # Get the calling frame (skip this function's frame)
    frame = inspect.currentframe()
    source_file = None
    source_line = None

    if frame and frame.f_back:
        # Get the filename and line number from the caller's frame
        filename = frame.f_back.f_code.co_filename
        lineno = frame.f_back.f_lineno

        # Make the path relative to the project root for cleaner display
        try:
            from app.config import get_settings

            settings = get_settings()
            project_root = getattr(settings, "project_root", None)

            if project_root and filename.startswith(project_root):
                source_file = filename[len(project_root) :].lstrip("/")
            else:
                # Try to make it relative to backend/ if no project root
                if "backend/" in filename:
                    source_file = filename.split("backend/")[-1]
                else:
                    # As a last resort, just use the basename
                    source_file = filename.split("/")[-1]
        except Exception:
            # Fallback to basename on any error
            source_file = filename.split("/")[-1]

        source_line = lineno

    file_token = _SOURCE_FILE.set(source_file)
    line_token = _SOURCE_LINE.set(source_line)
    try:
        yield
    finally:
        _SOURCE_FILE.reset(file_token)
        _SOURCE_LINE.reset(line_token)


@dataclass(frozen=True)
class TierEconomics:
    """What a tier costs and what is serving it, as configured."""

    params_b: float
    local: bool
    # None when unstated, which settings only allow on a local or disabled tier.
    price_in_per_mtok: float | None
    price_out_per_mtok: float | None
    # Optional: None prices cached input at the full input rate.
    price_cached_in_per_mtok: float | None = None


def economics_for(tier: int) -> TierEconomics | None:
    """The configured economics for a tier, or None when the tier is not one of ours.

    Returning None rather than a zeroed record matters: zero is a real price (a free
    hosted tier), and "not configured" has to stay distinguishable from "free" or the
    ledger cannot tell an unpriced call from a costless one.
    """
    if not 1 <= tier <= 4:
        return None
    settings = get_settings()
    prefix = f"llm_tier{tier}"
    return TierEconomics(
        params_b=getattr(settings, f"{prefix}_params_b"),
        local=getattr(settings, f"{prefix}_local"),
        price_in_per_mtok=getattr(settings, f"{prefix}_price_in_per_mtok"),
        price_out_per_mtok=getattr(settings, f"{prefix}_price_out_per_mtok"),
        price_cached_in_per_mtok=getattr(settings, f"{prefix}_price_cached_in_per_mtok"),
    )


def cost_usd(
    economics: TierEconomics | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    latency_ms: int,
    cached_tokens: int | None = None,
) -> float | None:
    """What one call cost: metered per token on a hosted tier, per second on your own.

    A local tier bills no tokens, and pricing it per token would report every locally
    served run as free. What it actually consumes is the machine, for as long as the call
    takes, so it is priced from wall clock against the configured draw and tariff.

    That figure is energy alone. Amortised hardware, if you want it counted, belongs in
    the same rate, which is why the draw is one number in settings rather than a
    calculation spread through here.

    None means genuinely unknown: an unconfigured or unpriced tier, or a hosted provider
    that returned no usage block. Unknown is recorded as unknown rather than as zero, because
    a zero would sum into the rollup and understate what the run cost.
    """
    if economics is None:
        return None
    if economics.local:
        settings = get_settings()
        hours = latency_ms / 1000.0 / SECONDS_PER_HOUR
        kilowatts = settings.hardware_watts / WATTS_PER_KILOWATT
        return round(hours * kilowatts * settings.electricity_price_per_kwh, COST_PLACES)
    if economics.price_in_per_mtok is None or economics.price_out_per_mtok is None:
        return None
    if prompt_tokens is None or completion_tokens is None:
        return None
    # Cached input is part of prompt_tokens, not added to it, and is billed at its own
    # rate where the tier has one. A count the provider did not send, or one larger than
    # the prompt it belongs to, is not trusted: those tokens pay the full input rate,
    # which overstates the call rather than inventing a discount.
    cached = (
        cached_tokens if cached_tokens is not None and 0 <= cached_tokens <= prompt_tokens else 0
    )
    cached_rate = (
        economics.price_in_per_mtok
        if economics.price_cached_in_per_mtok is None
        else economics.price_cached_in_per_mtok
    )
    return round(
        (prompt_tokens - cached) / TOKENS_PER_MILLION * economics.price_in_per_mtok
        + cached / TOKENS_PER_MILLION * cached_rate
        + completion_tokens / TOKENS_PER_MILLION * economics.price_out_per_mtok,
        COST_PLACES,
    )


def record(
    *,
    tier: int,
    model: str,
    op: str,
    usage: Any,
    latency_ms: int,
    status: int,
    error: str | None = None,
    first_token_ms: int | None = None,
) -> None:
    """Append one call attempt to the ledger, and add it to the enclosing run's spend.

    Failures are attempts too: ``status`` carries the HTTP code the tier answered with
    (0 when nothing answered at all) and ``error`` a short account of what went wrong.
    Without those rows an afternoon of 429s pushing traffic to a priced tier would be
    invisible in the very file that exists to explain the spend.
    """
    economics = economics_for(tier)
    prompt_tokens = _token_count(usage, "prompt_tokens")
    completion_tokens = _token_count(usage, "completion_tokens")
    cached_tokens = _detail_count(usage, "prompt_tokens_details", "cached_tokens")
    reasoning_tokens = _detail_count(usage, "completion_tokens_details", "reasoning_tokens")
    cost = cost_usd(economics, prompt_tokens, completion_tokens, latency_ms, cached_tokens)

    _append(
        {
            "ts": datetime.now(UTC).isoformat(),
            "run_id": _RUN_ID.get(),
            "op": op,
            # Which prompt version asked. ``op`` says what kind of call it was
            # ("tool_turn"), never which authored text drove it, and those are different
            # questions the moment a prompt is versioned up.
            "prompt": _PROMPT.get(),
            "tier": tier,
            "model": model,
            # The parameter count is configuration because no provider reports it, and it
            # is the axis the whole exercise turns on: tokens and latency mean one thing
            # from a 3B model and another from a 70B one.
            "params_b": economics.params_b if economics else None,
            "local": economics.local if economics else None,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            # Both inside the counts above rather than beside them: cached tokens are part
            # of the prompt, billed cheaper, and reasoning tokens are part of the
            # completion, billed the same. Recorded because they explain a cost and a
            # latency the two totals cannot: a long prompt that was mostly cached, or a
            # short answer that took seconds of thinking.
            "cached_tokens": cached_tokens,
            "reasoning_tokens": reasoning_tokens,
            "latency_ms": latency_ms,
            # How long before the model produced anything, of the latency above. None when
            # the tier answered in one piece or nothing arrived, which is unknown, not 0.
            # The gap between the two is the time spent writing; the rest was reading the
            # prompt and, on a reasoning model, thinking.
            "first_token_ms": first_token_ms,
            "status": status,
            "error": error,
            "cost_usd": cost,
            # Code-level transparency: where in the codebase this call originated
            "source_file": _SOURCE_FILE.get(),
            "source_line": _SOURCE_LINE.get(),
        }
    )

    spend = _SPEND.get()
    if spend is None:
        return
    spend.calls += 1
    # A call with no error came back with a usable body, which is a sharper test than a
    # 2xx: the transport succeeded on some of the rows that carry an error too. Attempts
    # that failed leave the previous answer standing rather than overwriting it with the
    # tier that could not serve, because what is wanted here is who *did*.
    if error is None:
        spend.last_tier = tier
        spend.last_model = model
    # Known figures accumulate; unknown ones are counted, never invented. `or 0` here
    # would fold "the provider reported nothing" into "it cost nothing", and the run's
    # rollup would understate itself with no marker that anything went unmeasured:
    # the exact conflation cost_usd() returns None to prevent.
    if prompt_tokens is not None:
        spend.prompt_tokens += prompt_tokens
    if completion_tokens is not None:
        spend.completion_tokens += completion_tokens
    if cost is not None:
        spend.cost_usd += cost
    if cost is None or prompt_tokens is None or completion_tokens is None:
        spend.unmetered_calls += 1


def _token_count(usage: Any, key: str) -> int | None:
    """A token count from the provider's optional usage block.

    Tolerant on purpose, and this is not a no-fallbacks shrug. Usage is metadata the
    system records and never acts on, unlike the tool call in the same response, which is
    validated and fails loudly. A tier that omits it, or sends a string, records None,
    which is the honest answer and keeps a survey running.
    """
    if not isinstance(usage, dict):
        return None
    value = usage.get(key)
    return value if isinstance(value, int) else None


def _detail_count(usage: Any, block: str, key: str) -> int | None:
    """A count from one of the usage block's nested details, or None when absent.

    ``prompt_tokens_details.cached_tokens`` and ``completion_tokens_details.
    reasoning_tokens`` are the shapes OpenAI and OpenRouter send. Tolerant for the same
    reason ``_token_count`` is: this is metadata, recorded and never acted on.
    """
    if not isinstance(usage, dict):
        return None
    details = usage.get(block)
    if not isinstance(details, dict):
        return None
    value = details.get(key)
    return value if isinstance(value, int) else None


def _append(entry: dict[str, Any]) -> None:
    """One record, one line, one write, in append mode.

    A write below PIPE_BUF lands atomically on POSIX, so concurrent requests interleave
    whole lines rather than shredding each other's. Synchronous on purpose: the call this
    describes took seconds, so a sub-millisecond append costs nothing measurable, and
    handing it to a thread would only add a way to lose records at shutdown.

    A ledger failure must never take down a survey. The record is the point of this
    module, but it is not worth the conversation, so a write error is logged loudly and
    the turn continues.
    """
    path = Path(get_settings().llm_ledger_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError as exc:
        logger.warning("could not append to the LLM ledger at %s: %r", path, exc)
