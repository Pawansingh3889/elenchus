import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from app.config import get_settings
from app.llm.schemas import LlmEntry, LlmModelStats, LlmReport, LlmRunSummary


@dataclass
class _ModelBucket:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    errors: int = 0


@dataclass
class _RunBucket:
    model: str = ""
    tier: int | None = None
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    errors: int = 0
    first_ts: str = ""
    last_ts: str = ""
    ops: set[str] = field(default_factory=set)


def get_llm_report() -> LlmReport:
    path = Path(get_settings().llm_ledger_path)
    if not path.exists():
        return LlmReport(
            total_entries=0,
            total_runs=0,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_cost_usd=0.0,
            avg_latency_ms=0.0,
            models=[],
            runs=[],
        )

    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not entries:
        return LlmReport(
            total_entries=0,
            total_runs=0,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_cost_usd=0.0,
            avg_latency_ms=0.0,
            models=[],
            runs=[],
        )

    total_prompt = 0
    total_completion = 0
    total_cost = 0.0
    total_latency = 0
    total_context = 0

    model_buckets: dict[tuple[str, int | None], _ModelBucket] = defaultdict(_ModelBucket)
    run_buckets: dict[str | None, _RunBucket] = defaultdict(_RunBucket)

    for e in entries:
        prompt = e.get("prompt_tokens") or 0
        completion = e.get("completion_tokens") or 0
        context = prompt + completion
        cost = e.get("cost_usd") or 0.0
        latency = e.get("latency_ms") or 0
        model = e.get("model", "unknown")
        tier = e.get("tier")
        run_id = e.get("run_id")
        ts = e.get("ts", "")
        has_error = e.get("error") is not None

        total_prompt += prompt
        total_completion += completion
        total_context += context
        total_cost += cost
        total_latency += latency

        key = (model, tier)
        b = model_buckets[key]
        b.calls += 1
        b.prompt_tokens += prompt
        b.completion_tokens += completion
        b.latency_ms += latency
        if has_error:
            b.errors += 1

        r = run_buckets[run_id]
        r.model = model
        r.tier = tier
        r.calls += 1
        r.prompt_tokens += prompt
        r.completion_tokens += completion
        r.latency_ms += latency
        if has_error:
            r.errors += 1
        op = e.get("op")
        if op:
            r.ops.add(op)
        if not r.first_ts or ts < r.first_ts:
            r.first_ts = ts
        if not r.last_ts or ts > r.last_ts:
            r.last_ts = ts

    models = []
    for (model, tier), b in sorted(model_buckets.items(), key=lambda x: -x[1].calls):
        models.append(
            LlmModelStats(
                model=model,
                tier=tier,
                calls=b.calls,
                total_prompt_tokens=b.prompt_tokens,
                total_completion_tokens=b.completion_tokens,
                total_context_tokens=b.prompt_tokens + b.completion_tokens,
                avg_latency_ms=b.latency_ms / b.calls if b.calls else 0,
                error_count=b.errors,
            )
        )

    runs = []
    for run_id, rb in sorted(run_buckets.items(), key=lambda x: x[1].last_ts):
        if run_id is None:
            continue
        runs.append(
            LlmRunSummary(
                run_id=run_id,
                model=rb.model,
                tier=rb.tier,
                calls=rb.calls,
                prompt_tokens=rb.prompt_tokens,
                completion_tokens=rb.completion_tokens,
                context_tokens=rb.prompt_tokens + rb.completion_tokens,
                avg_latency_ms=rb.latency_ms / rb.calls if rb.calls else 0,
                error_count=rb.errors,
                first_ts=rb.first_ts,
                last_ts=rb.last_ts,
                ops=sorted(rb.ops),
            )
        )

    n = len(entries)
    return LlmReport(
        total_entries=n,
        total_runs=len(runs),
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
        total_context_tokens=total_context,
        total_cost_usd=total_cost,
        avg_latency_ms=total_latency / n if n else 0,
        models=models,
        runs=runs,
    )


def get_llm_run_entries(run_id: str) -> list[LlmEntry]:
    path = Path(get_settings().llm_ledger_path)
    if not path.exists():
        return []

    results: list[LlmEntry] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("run_id") != run_id:
                continue
            results.append(
                LlmEntry(
                    ts=e.get("ts", ""),
                    op=e.get("op"),
                    tier=e.get("tier"),
                    model=e.get("model"),
                    prompt_tokens=e.get("prompt_tokens"),
                    completion_tokens=e.get("completion_tokens"),
                    context_tokens=(e.get("prompt_tokens") or 0)
                    + (e.get("completion_tokens") or 0),
                    latency_ms=e.get("latency_ms"),
                    status=e.get("status"),
                    error=e.get("error"),
                    cost_usd=e.get("cost_usd"),
                )
            )
    return sorted(results, key=lambda x: x.ts)
