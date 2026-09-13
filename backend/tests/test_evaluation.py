"""Evaluation: labels are the truth, the judge is scored against them, and both are private.

The judge is faked at the LLM boundary as every model is; what is tested is what the
backend owes: labels upsert and cascade, the rates and intervals are the right arithmetic,
a judging is kept whole or not at all, and only administrators see any of it.
"""

import json
import math
from typing import Any

import pytest
import pytest_asyncio

from app.conduct.engine import ConductEngine
from app.errors import ForbiddenError, NotFoundError
from app.evaluation.enums import LabelVerdict
from app.evaluation.schemas import LabelRequest
from app.evaluation.service import EvaluationService
from app.evaluation.stats import MIN_LABELLED, wilson
from app.llm import ledger
from app.llm.client import LLMError
from app.users.models import Band, Function, User
from tests.fakes import FakeLLM, move_on, record


@pytest_asyncio.fixture
async def admin(session):
    user = User(
        email="eval-admin@plant.dev",
        display_name="Eval Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


def _answer(question: str, value: dict, said: list[str], judge: bool | None, invented=False):
    return {
        "question_text": question,
        "answer_type": "short_text",
        "options": [],
        "allow_other": False,
        "kind": "scripted",
        "value": value,
        "said": said,
        "judge": {"supported": judge, "why": None if judge is None else "reason"},
        "invented": invented,
    }


@pytest.fixture
def corpus(tmp_path):
    answers = [
        _answer("Role?", {"text": "Line lead"}, ["line lead"], judge=True),
        _answer("Team?", {"text": "Packing"}, ["no idea"], judge=False, invented=True),
        _answer("Shift?", {"text": "Nights"}, ["nights"], judge=False),
        _answer("Buddy?", {"yes_no": True}, ["4"], judge=True),
    ]
    (tmp_path / "broad-1.json").write_text(
        json.dumps({"scenario": "broad", "model": "gpt-5.5", "answers": answers}),
        encoding="utf-8",
    )
    return tmp_path


def test_the_wilson_interval_matches_worked_values():
    assert wilson(0, 0) is None
    low, high = wilson(5, 10)
    assert math.isclose(low, 0.2366, abs_tol=1e-4) and math.isclose(high, 0.7634, abs_tol=1e-4)
    # Near the edge the bounds stay inside [0, 1], which the normal approximation does not.
    low, high = wilson(0, 3)
    assert low == 0.0 and 0 < high < 1
    with pytest.raises(ValueError):
        wilson(4, 3)


async def test_corpus_answers_are_queued_with_the_files_own_marks(session, admin, corpus):
    items = await EvaluationService(session, corpus_dir=corpus).items(admin, "corpus", False)

    assert [item.key for item in items] == [f"corpus:broad-1:{i}" for i in range(4)]
    assert items[1].marked_invented and items[1].judge_supported is False
    assert items[0].said == ["line lead"] and items[0].label is None


async def test_a_label_replaces_the_last_one_and_leaves_the_unlabelled_queue(
    session, admin, corpus
):
    service = EvaluationService(session, corpus_dir=corpus)
    await service.label(admin, "corpus:broad-1:1", LabelRequest(verdict=LabelVerdict.unsure))
    item = await service.label(
        admin, "corpus:broad-1:1", LabelRequest(verdict=LabelVerdict.invented, note="no team given")
    )

    assert (item.label, item.note) == (LabelVerdict.invented, "no team given")
    queue = await service.items(admin, "corpus", True)
    assert "corpus:broad-1:1" not in [i.key for i in queue] and len(queue) == 3
    with pytest.raises(NotFoundError):
        await service.label(admin, "corpus:broad-1:9", LabelRequest(verdict=LabelVerdict.supported))


async def test_the_report_scores_the_judge_only_against_peoples_labels(session, admin, corpus):
    service = EvaluationService(session, corpus_dir=corpus)
    for key, verdict in (
        ("corpus:broad-1:0", LabelVerdict.supported),  # judge agreed
        ("corpus:broad-1:1", LabelVerdict.invented),  # judge caught it
        ("corpus:broad-1:2", LabelVerdict.supported),  # judge cried wolf
        ("corpus:broad-1:3", LabelVerdict.invented),  # judge missed it
    ):
        await service.label(admin, key, LabelRequest(verdict=verdict))

    overall = (await service.faithfulness(admin)).overall

    assert (overall.labelled, overall.supported, overall.invented) == (4, 2, 2)
    assert (overall.invention_rate.numerator, overall.invention_rate.denominator) == (2, 4)
    assert (overall.judge_precision.numerator, overall.judge_precision.denominator) == (1, 2)
    assert (overall.judge_recall.numerator, overall.judge_recall.denominator) == (1, 2)
    assert (overall.judge_false_alarms.numerator, overall.judge_false_alarms.denominator) == (1, 2)
    assert overall.invention_rate.too_few and MIN_LABELLED == 20
    assert overall.invention_rate.low is not None and overall.invention_rate.low < 0.5


class JudgeLLM:
    """Answers the judge's tool call with scripted verdicts, booked like a real call."""

    def __init__(self, verdicts: list[dict[str, Any]]) -> None:
        self.verdicts = verdicts
        self.prompts: list[dict[str, Any]] = []

    async def tool_call(self, **kwargs: Any) -> dict[str, Any]:
        self.prompts.append(kwargs)
        ledger.record(
            tier=1,
            model="gpt-5.5",
            op="tool_call",
            usage={"prompt_tokens": 1200, "completion_tokens": 80},
            latency_ms=900,
            status=200,
        )
        return {"verdicts": self.verdicts}

    async def tool_turn(self, **_: Any) -> Any:
        raise AssertionError("the judge never takes a conversational turn")


async def _answered(session, respondent, published) -> str:
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."), serves_as=(1, "gpt-5.5"))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead on nights", respondent)
    return str(run.id)


async def test_a_run_is_judged_whole_priced_and_shown_beside_its_answers(
    session, respondent, published, admin, tmp_path
):
    run_id = await _answered(session, respondent, published)
    llm = JudgeLLM([{"index": 0, "supported": True, "why": "they said line lead"}])
    service = EvaluationService(session, llm=llm, corpus_dir=tmp_path)

    judging = await service.judge_run(admin, run_id)

    assert (judging.answers, judging.flagged, judging.prompt_version) == (1, 0, "judge_answers_v1")
    assert judging.model == "gpt-5.5" and judging.cost_usd > 0
    sent = json.loads(llm.prompts[0]["prompt"])
    assert sent["respondent_messages"] == ["line lead on nights"]
    (item,) = await service.items(admin, "runs", False)
    assert item.judge_supported is True and item.judge_prompt == "judge_answers_v1"
    assert item.said == ["line lead on nights"] and item.model == "gpt-5.5"


async def test_a_judge_that_skips_an_answer_keeps_nothing(
    session, respondent, published, admin, tmp_path
):
    run_id = await _answered(session, respondent, published)
    service = EvaluationService(session, llm=JudgeLLM([]), corpus_dir=tmp_path)
    with pytest.raises(LLMError, match="without a verdict"):
        await service.judge_run(admin, run_id)
    (item,) = await service.items(admin, "runs", False)
    assert item.judge_supported is None


async def test_withdrawing_a_run_takes_its_labels_and_verdicts(
    session, respondent, published, admin, tmp_path
):
    run_id = await _answered(session, respondent, published)
    llm = JudgeLLM([{"index": 0, "supported": False, "why": "no"}])
    service = EvaluationService(session, llm=llm, corpus_dir=tmp_path)
    await service.judge_run(admin, run_id)
    (item,) = await service.items(admin, "runs", False)
    await service.label(admin, item.key, LabelRequest(verdict=LabelVerdict.supported))

    await ConductEngine(session, llm=FakeLLM()).delete_run(run_id, respondent)

    assert await service.items(admin, "runs", False) == []
    report = await service.faithfulness(admin)
    assert report.overall.labelled == 0


async def test_only_admins_see_evaluation(session, author, corpus):
    service = EvaluationService(session, corpus_dir=corpus)
    with pytest.raises(ForbiddenError):
        await service.items(author, "corpus", False)
    with pytest.raises(ForbiddenError):
        await service.label(
            author, "corpus:broad-1:0", LabelRequest(verdict=LabelVerdict.supported)
        )
    with pytest.raises(ForbiddenError):
        await service.faithfulness(author)
    with pytest.raises(ForbiddenError):
        await service.judge_run(author, "00000000-0000-0000-0000-000000000000")
