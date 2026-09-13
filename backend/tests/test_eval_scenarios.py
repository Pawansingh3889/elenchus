"""The ported scenarios: every one builds, every scripted respondent answers, checks bite."""

from datetime import date
from uuid import uuid4

import pytest

from app.evaluation.scenarios import SCENARIOS, Transcript, max_turns, shape_ok


def _questions(key: str) -> list[dict]:
    return [
        {
            "id": str(uuid4()),
            "position": index,
            "text": question.text,
            "answer_type": question.answer_type.value,
            "options": question.options,
            "allow_other": question.allow_other,
            "required": question.required,
            "follow_up_policy": question.follow_up_policy.value,
        }
        for index, question in enumerate(SCENARIOS[key].questions)
    ]


def test_the_nine_scripted_scenarios_are_ported():
    assert sorted(SCENARIOS) == sorted(
        [
            "max_length",
            "skip_heavy",
            "write_ins",
            "numbers_dates",
            "injection",
            "out_of_order",
            "multi_answer",
            "forced_probe",
            "probe_budget",
        ]
    )


@pytest.mark.parametrize("key", sorted(SCENARIOS))
def test_every_scripted_respondent_answers_every_question(key):
    scenario = SCENARIOS[key]
    assert max_turns(scenario) == 3 * len(scenario.questions) + 10
    for turn, question in enumerate(_questions(key)):
        reply = scenario.respond(question, "Next question.", 1, turn)
        assert isinstance(reply, str) and reply.strip()


def test_the_numbers_checks_pass_a_sound_run_and_fail_a_broken_one():
    questions = _questions("numbers_dates")
    today = date(2026, 9, 13)
    sound = Transcript(
        questions=questions,
        positions=[0, 1, 2, 3],
        answers=[
            {
                "question_id": questions[0]["id"],
                "kind": "scripted",
                "value": {"date": "2026-09-09"},
                "question_text": "d",
            },
            {
                "question_id": questions[1]["id"],
                "kind": "scripted",
                "value": {"number": 3},
                "question_text": "n",
            },
            {
                "question_id": questions[2]["id"],
                "kind": "scripted",
                "value": {"rating": 4},
                "question_text": "r",
            },
            {
                "question_id": questions[3]["id"],
                "kind": "scripted",
                "value": {"unanswerable": "eleven out of ten"},
                "question_text": "c",
            },
        ],
        status="completed",
        today=today,
    )
    checks = SCENARIOS["numbers_dates"].check(sound)
    assert [c.name for c in checks if c.hard and not c.ok] == []

    broken = Transcript(
        questions=questions,
        positions=sound.positions,
        answers=[{**sound.answers[0], "value": {"date": "2025-09-09"}}, *sound.answers[1:]],
        status="completed",
        today=today,
    )
    failed = [c.name for c in SCENARIOS["numbers_dates"].check(broken) if c.hard and not c.ok]
    assert failed == ["relative date resolved to 2026-09-09 (not a past year)"]


def test_value_shapes_are_judged_by_answer_type():
    assert shape_ok("rating", {"rating": 5}) and not shape_ok("rating", {"rating": 6})
    assert not shape_ok("rating", {"rating": True})
    assert shape_ok("date", {"date": "2026-09-09"}) and not shape_ok("date", {"date": "ninth"})
    assert shape_ok("single_select", {"other": "crew"}) and shape_ok(
        "yes_no", {"unanswerable": "x"}
    )
