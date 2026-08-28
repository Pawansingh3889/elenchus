"""The batch lane: JSONL shape, submission, collection, and ledger booking.

No network: the provider's files/batches endpoints are mocked with an
httpx transport, the same pattern test_openai_compatible uses. What is
under test is the lane's discipline — a spec-shaped file, a completed
batch collected with every answered row in the ledger at the batch rate,
and the failure modes named rather than swallowed.
"""

import json
from pathlib import Path
from typing import Any

import anyio
import httpx
import pytest

from app.config import get_settings
from app.llm import ledger
from app.llm.batch import BatchError, BatchJob, BatchLane, build_jsonl, parse_results


@pytest.fixture
def priced_tier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Tier 1 priced at the OpenAI-ish $2.50/$10 per Mtok, ledger in tmp.

    Env plus cache_clear, the same pattern test_llm_service uses: get_settings
    is cached, and a developer's .env would otherwise leak a real tier into a
    test that means to describe this exact machine.
    """

    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("LLM_LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("LLM_TIER1_ENABLED", "true")
    monkeypatch.setenv("LLM_TIER1_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_TIER1_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_TIER1_PRICE_IN_PER_MTOK", "2.5")
    monkeypatch.setenv("LLM_TIER1_PRICE_OUT_PER_MTOK", "10.0")
    get_settings.cache_clear()
    yield ledger_path
    get_settings.cache_clear()


def _local_tier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A tier on our own hardware: no batch queue applies, and a batch row
    priced from latency_ms=0 would book as free, which the ledger forbids."""

    monkeypatch.setenv("LLM_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    monkeypatch.setenv("LLM_TIER1_ENABLED", "true")
    monkeypatch.setenv("LLM_TIER1_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_TIER1_MODEL", "a-local-model")
    monkeypatch.setenv("LLM_TIER1_LOCAL", "true")
    get_settings.cache_clear()


def _jobs() -> list[BatchJob]:
    return [
        BatchJob(
            custom_id="run-1",
            payload={"model": "gpt-test", "messages": [{"role": "user", "content": "score this"}]},
            op="batch_eval",
        ),
        BatchJob(
            custom_id="run-2",
            payload={"model": "gpt-test", "messages": [{"role": "user", "content": "score that"}]},
            op="batch_eval",
        ),
    ]


def _output_line(custom_id: str, prompt_tokens: int, completion_tokens: int) -> str:
    return json.dumps(
        {
            "id": f"resp-{custom_id}",
            "custom_id": custom_id,
            "response": {
                "status_code": 200,
                "request_id": f"req-{custom_id}",
                "body": {
                    "choices": [{"message": {"role": "assistant", "content": "judgement"}}],
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    },
                },
            },
        }
    )


def test_build_jsonl_matches_the_provider_spec():
    content = build_jsonl(_jobs()).decode("utf-8")
    rows = [json.loads(line) for line in content.splitlines()]
    assert rows[0]["custom_id"] == "run-1"
    assert rows[0]["method"] == "POST"
    assert rows[0]["url"] == "/v1/chat/completions"
    assert rows[0]["body"]["model"] == "gpt-test"


def test_build_jsonl_rejects_empty_duplicate_and_model_less():
    with pytest.raises(BatchError, match="no jobs"):
        build_jsonl([])
    with pytest.raises(BatchError, match="Duplicated custom_id"):
        build_jsonl([_jobs()[0], _jobs()[0]])
    blank = BatchJob(custom_id="", payload={"model": "gpt-test"})
    with pytest.raises(BatchError, match="custom_id"):
        build_jsonl([blank])
    no_model = BatchJob(custom_id="run-1", payload={"messages": []})
    with pytest.raises(BatchError, match="no model"):
        build_jsonl([no_model])


def test_parse_results_maps_answers_and_failures():
    text = "\n".join(
        [
            _output_line("run-1", 100, 20),
            json.dumps({"custom_id": "run-2", "error": {"code": "model_error", "message": "boom"}}),
            "not json at all",
        ]
    )
    succeeded, failed = parse_results(text)
    assert [s.custom_id for s in succeeded] == ["run-1"]
    assert succeeded[0].content == "judgement"
    assert succeeded[0].usage["prompt_tokens"] == 100
    assert [f.custom_id for f in failed] == ["run-2", ""]
    assert "boom" in failed[0].detail
    assert "unparseable" in failed[1].detail


def _provider_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, state: dict[str, Any]):
    """A stub of the provider's files/batches surface, capturing requests."""

    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/v1/files" and request.method == "POST":
            assert request.headers["content-type"].startswith("multipart/form-data")
            body = request.read()
            seen["upload_bytes"] = len(body)
            seen["upload_has_batch_purpose"] = b"batch" in body
            return httpx.Response(200, json={"id": "file-1"})
        if path == "/v1/batches" and request.method == "POST":
            seen["create_body"] = json.loads(request.read())
            return httpx.Response(200, json={"id": state["batch_id"]})
        if path == f"/v1/batches/{state['batch_id']}" and request.method == "GET":
            return httpx.Response(200, json=state["batch_status"])
        if path == f"/v1/files/{state['output_file_id']}/content":
            return httpx.Response(200, text=state["output_text"])
        return httpx.Response(404, json={"error": {"message": f"unknown path {path}"}})

    return seen, httpx.MockTransport(handler)


async def test_submit_and_collect_book_rows_at_the_batch_rate(
    tmp_path: Path, priced_tier: Path, monkeypatch: pytest.MonkeyPatch
):

    state: dict[str, Any] = {
        "batch_id": "batch-1",
        "output_file_id": "file-out-1",
        "batch_status": {"status": "completed", "output_file_id": "file-out-1"},
        "output_text": _output_line("run-1", 1_000_000, 100_000) + "\n",
    }
    seen, transport = _provider_app(monkeypatch, tmp_path, state)
    lane = BatchLane(
        base_url="https://api.openai.com/v1",
        api_key="key",
        model="gpt-test",
        tier=1,
        transport=transport,
    )

    batch_id = await lane.submit(_jobs())
    assert batch_id == "batch-1"
    assert seen["upload_has_batch_purpose"] is True
    assert seen["create_body"]["input_file_id"] == "file-1"
    assert seen["create_body"]["endpoint"] == "/v1/chat/completions"
    assert seen["create_body"]["completion_window"] == "24h"

    collection = await lane.collect(batch_id)
    assert [r.custom_id for r in collection.succeeded] == ["run-1"]
    assert collection.failed == []
    assert collection.booked_rows == 1

    ledger_text = await anyio.Path(priced_tier).read_text()
    rows = [json.loads(row) for row in ledger_text.splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["op"] == "batch"
    assert row["tier"] == 1
    assert row["prompt_tokens"] == 1_000_000

    # The tokens stay as reported; the price is the provider's batch half rate.
    realtime = (1_000_000 / 1_000_000 * 2.5) + (100_000 / 1_000_000 * 10.0)
    assert row["cost_usd"] == round(realtime * 0.5, 8)


async def test_collect_refuses_a_batch_that_is_not_finished(
    tmp_path: Path, priced_tier: Path, monkeypatch: pytest.MonkeyPatch
):
    state: dict[str, Any] = {
        "batch_id": "batch-2",
        "output_file_id": "file-out",
        "batch_status": {"status": "in_progress"},
        "output_text": "",
    }
    _, transport = _provider_app(monkeypatch, tmp_path, state)
    lane = BatchLane(
        base_url="https://api.openai.com/v1",
        api_key="k",
        model="gpt-test",
        tier=1,
        transport=transport,
    )
    with pytest.raises(BatchError, match="not finished"):
        await lane.collect("batch-2")


async def test_collect_names_a_failed_or_expired_batch(
    tmp_path: Path, priced_tier: Path, monkeypatch: pytest.MonkeyPatch
):
    state: dict[str, Any] = {
        "batch_id": "batch-3",
        "output_file_id": "file-out",
        "batch_status": {"status": "expired", "error": {"message": "outlived the window"}},
        "output_text": "",
    }
    _, transport = _provider_app(monkeypatch, tmp_path, state)
    lane = BatchLane(
        base_url="https://api.openai.com/v1",
        api_key="k",
        model="gpt-test",
        tier=1,
        transport=transport,
    )
    with pytest.raises(BatchError, match="expired"):
        await lane.collect("batch-3")


async def test_lane_refuses_a_local_tier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _local_tier(tmp_path, monkeypatch)
    with pytest.raises(BatchError, match="hosted, priced tier"):
        BatchLane(
            base_url="http://localhost:11434/v1", api_key="", model="local", tier=1, transport=None
        )


async def test_provider_without_a_batch_queue_fails_loudly(
    tmp_path: Path, priced_tier: Path, monkeypatch: pytest.MonkeyPatch
):

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"message": "no such endpoint"}})

    lane = BatchLane(
        base_url="https://api.openai.com/v1",
        api_key="k",
        model="gpt-test",
        tier=1,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(BatchError, match="upload was rejected"):
        await lane.submit(_jobs())


def test_ledger_default_multiplier_leaves_rows_untouched(
    priced_tier: Path,
):
    ledger.record(
        tier=1,
        model="gpt-test",
        op="tool_turn",
        usage={"prompt_tokens": 1_000_000, "completion_tokens": 100_000},
        latency_ms=0,
        status=200,
        error=None,
    )
    row = json.loads(priced_tier.read_text().splitlines()[0])
    realtime = (1_000_000 / 1_000_000 * 2.5) + (100_000 / 1_000_000 * 10.0)
    assert row["cost_usd"] == round(realtime, 8)
