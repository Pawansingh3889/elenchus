"""get_llm_report's aggregation: the numbers it derives from raw ledger lines.

Only what this file added is covered here: the op-level breakdown, grouped across
every run rather than one at a time, with the source files that logged each op. The
ledger's own writing side is covered in test_ledger.py.
"""

import json
from uuid import uuid4

import pytest

from app.config import get_settings
from app.llm.service import get_llm_ledger, get_llm_report, get_llm_run_entries

WORKSPACE = uuid4()


@pytest.fixture
def ledger_file(tmp_path, monkeypatch):
    path = tmp_path / "ledger.jsonl"
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_LEDGER_PATH", str(path))
    yield path
    get_settings.cache_clear()


def _write(path, *entries) -> None:
    with path.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps({"workspace_id": str(WORKSPACE), **e}) + "\n")


def test_no_ledger_file_reports_no_ops(ledger_file) -> None:
    report = get_llm_report(WORKSPACE)
    assert report.ops == []


def test_two_calls_with_the_same_op_are_one_bucket(ledger_file) -> None:
    _write(
        ledger_file,
        {
            "ts": "2026-08-25T10:00:00Z",
            "run_id": "run-1",
            "op": "tool_turn",
            "model": "gpt-5.5",
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "latency_ms": 500,
            "source_file": "app/conduct/engine.py",
        },
        {
            "ts": "2026-08-25T10:00:05Z",
            "run_id": "run-1",
            "op": "tool_turn",
            "model": "gpt-5.5",
            "prompt_tokens": 200,
            "completion_tokens": 30,
            "latency_ms": 700,
            "source_file": "app/conduct/engine.py",
        },
    )
    report = get_llm_report(WORKSPACE)
    assert len(report.ops) == 1
    op = report.ops[0]
    assert op.op == "tool_turn"
    assert op.calls == 2
    assert op.total_prompt_tokens == 300
    assert op.total_completion_tokens == 50
    assert op.total_context_tokens == 350
    assert op.avg_latency_ms == 600
    assert op.error_count == 0
    assert op.source_files == ["app/conduct/engine.py"]


def test_different_ops_are_separate_buckets(ledger_file) -> None:
    _write(
        ledger_file,
        {"ts": "t1", "run_id": "run-1", "op": "tool_turn", "model": "m", "prompt_tokens": 10},
        {"ts": "t2", "run_id": "run-1", "op": "generate", "model": "m", "prompt_tokens": 20},
    )
    report = get_llm_report(WORKSPACE)
    ops_by_name = {o.op: o for o in report.ops}
    assert set(ops_by_name) == {"tool_turn", "generate"}
    assert ops_by_name["tool_turn"].calls == 1
    assert ops_by_name["generate"].calls == 1


def test_an_entry_with_no_op_is_not_bucketed(ledger_file) -> None:
    _write(ledger_file, {"ts": "t1", "run_id": "run-1", "model": "m", "prompt_tokens": 10})
    report = get_llm_report(WORKSPACE)
    assert report.ops == []
    assert report.total_prompt_tokens == 10


def test_an_op_seen_from_two_call_sites_names_both_files(ledger_file) -> None:
    _write(
        ledger_file,
        {"ts": "t1", "run_id": "run-1", "op": "tool_turn", "model": "m", "source_file": "b.py"},
        {"ts": "t2", "run_id": "run-2", "op": "tool_turn", "model": "m", "source_file": "a.py"},
    )
    report = get_llm_report(WORKSPACE)
    assert report.ops[0].source_files == ["a.py", "b.py"]


def test_an_errored_call_counts_toward_the_ops_error_count(ledger_file) -> None:
    _write(
        ledger_file,
        {"ts": "t1", "run_id": "run-1", "op": "tool_turn", "model": "m", "error": "timeout"},
    )
    report = get_llm_report(WORKSPACE)
    assert report.ops[0].error_count == 1


def test_ops_are_ordered_by_call_count_descending(ledger_file) -> None:
    _write(
        ledger_file,
        {"ts": "t1", "run_id": "r", "op": "rare", "model": "m"},
        {"ts": "t2", "run_id": "r", "op": "common", "model": "m"},
        {"ts": "t3", "run_id": "r", "op": "common", "model": "m"},
    )
    report = get_llm_report(WORKSPACE)
    assert [o.op for o in report.ops] == ["common", "rare"]


def test_all_ledger_views_exclude_other_companies_and_unattributed_history(ledger_file):
    _write(
        ledger_file,
        {"ts": "t1", "run_id": "own", "prompt_tokens": 10},
        {"ts": "t2", "run_id": "foreign", "workspace_id": str(uuid4()), "prompt_tokens": 900},
        {"ts": "t3", "run_id": "legacy", "workspace_id": None, "prompt_tokens": 800},
    )
    assert get_llm_report(WORKSPACE).total_prompt_tokens == 10
    assert get_llm_ledger(WORKSPACE).total_entries == 1
    assert len(get_llm_run_entries("own", WORKSPACE)) == 1
    assert get_llm_run_entries("foreign", WORKSPACE) == []
    assert get_llm_run_entries("legacy", WORKSPACE) == []
