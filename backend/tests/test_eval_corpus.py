"""get_eval_accuracy_report: the judge's verdicts on the captured corpus, by answer
type. Against a temp fixture directory, not the real backend/tests/live_runs/, so
this suite's numbers cannot drift out from under a fixture someone adds later.
"""

import json

from app.llm.eval_corpus import get_eval_accuracy_report


def _write_fixture(dir_, name: str, answers: list[dict]) -> None:
    (dir_ / f"{name}.json").write_text(
        json.dumps({"scenario": name, "model": "gpt-5.5", "answers": answers}),
        encoding="utf-8",
    )


def test_an_empty_directory_reports_nothing(tmp_path) -> None:
    report = get_eval_accuracy_report(tmp_path)
    assert report.total_fixtures == 0
    assert report.total_answers == 0
    assert report.by_answer_type == []


def test_a_missing_directory_reports_nothing(tmp_path) -> None:
    report = get_eval_accuracy_report(tmp_path / "does-not-exist")
    assert report.total_fixtures == 0


def test_one_supported_answer_is_judged_and_not_flagged(tmp_path) -> None:
    _write_fixture(
        tmp_path,
        "a",
        [{"answer_type": "rating", "judge": {"supported": True}, "invented": False}],
    )
    report = get_eval_accuracy_report(tmp_path)
    assert report.total_answers == 1
    assert report.judged == 1
    assert report.flagged == 0
    assert report.known_inventions == 0


def test_an_unsupported_answer_is_flagged(tmp_path) -> None:
    _write_fixture(
        tmp_path,
        "a",
        [{"answer_type": "short_text", "judge": {"supported": False}, "invented": True}],
    )
    report = get_eval_accuracy_report(tmp_path)
    assert report.flagged == 1
    assert report.known_inventions == 1


def test_an_answer_with_no_judge_verdict_is_not_counted_as_judged(tmp_path) -> None:
    _write_fixture(tmp_path, "a", [{"answer_type": "rating", "judge": {}}])
    report = get_eval_accuracy_report(tmp_path)
    assert report.total_answers == 1
    assert report.judged == 0
    assert report.flagged == 0


def test_answers_group_by_answer_type_across_fixtures(tmp_path) -> None:
    _write_fixture(tmp_path, "a", [{"answer_type": "rating", "judge": {"supported": True}}])
    _write_fixture(
        tmp_path,
        "b",
        [
            {"answer_type": "rating", "judge": {"supported": False}},
            {"answer_type": "short_text", "judge": {"supported": True}},
        ],
    )
    report = get_eval_accuracy_report(tmp_path)
    by_type = {s.answer_type: s for s in report.by_answer_type}
    assert by_type["rating"].total_answers == 2
    assert by_type["rating"].judged == 2
    assert by_type["rating"].flagged == 1
    assert by_type["short_text"].total_answers == 1
    assert report.total_fixtures == 2


def test_an_answer_missing_its_type_falls_back_to_unknown(tmp_path) -> None:
    _write_fixture(tmp_path, "a", [{"judge": {"supported": True}}])
    report = get_eval_accuracy_report(tmp_path)
    assert report.by_answer_type[0].answer_type == "unknown"


def test_answer_types_are_ordered_by_volume_descending(tmp_path) -> None:
    _write_fixture(
        tmp_path,
        "a",
        [
            {"answer_type": "rare", "judge": {}},
            {"answer_type": "common", "judge": {}},
            {"answer_type": "common", "judge": {}},
        ],
    )
    report = get_eval_accuracy_report(tmp_path)
    assert [s.answer_type for s in report.by_answer_type] == ["common", "rare"]


def test_a_malformed_fixture_file_is_skipped_not_fatal(tmp_path) -> None:
    (tmp_path / "broken.json").write_text("not json", encoding="utf-8")
    _write_fixture(tmp_path, "a", [{"answer_type": "rating", "judge": {"supported": True}}])
    report = get_eval_accuracy_report(tmp_path)
    assert report.total_fixtures == 1
    assert report.total_answers == 1
