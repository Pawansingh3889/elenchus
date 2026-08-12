"""Replay real conversations against today's gates.

Every live run writes its transcript to tests/live_runs (see scripts/live_conversation.py).
This replays them in the mocked suite, on every push, for free. It exists because a live
finding does not keep: the invented yes that produced the yes/no gate could not be
reproduced against a real model minutes later, since the model answered in words the second
time. Captured, it is a test forever.

Two directions, and they prove different things.

  no false refusals   Every answer a real model produced and the engine accepted must
                      still be accepted. This runs on every saved run with no human
                      input, and it is the direction that catches a gate tightened too
                      far. Tightening is exactly what the yes/no work did, and a gate
                      that starts refusing real respondents fails here rather than in
                      production.

  known inventions    An answer a human marked "invented": true must be refused. This is
                      how a live finding becomes permanent. It needs the label because
                      nothing else can supply it: the judge is a model and gets things
                      wrong in both directions, so its verdict is recorded in the fixture
                      for a reader and never trusted here.

Adding one is `git add` on a file the script already wrote. Marking one
invented is editing a single field, and it should be done only after reading the
transcript.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from app.conduct.validation import (
    AnswerValidationError,
    ungrounded_choice,
    ungrounded_text,
    ungrounded_yes_no,
    validate_answer,
)

LIVE_RUNS = Path(__file__).parent / "live_runs"
FIXTURES = sorted(LIVE_RUNS.glob("*.json"))


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _grounding_problem(answer: dict[str, Any]) -> str | None:
    """The engine's source gate, applied exactly as app.conduct.engine applies it.

    Kept deliberately in step with `_rejection`. If the engine grows a branch and this does
    not, the corpus quietly stops replaying the shape that was just added, which is the
    moment a regression suite becomes decoration.
    """
    value = answer["value"]
    said = answer["said"]
    if isinstance(value.get("text"), str):
        return ungrounded_text(value["text"], said)
    if isinstance(value.get("yes_no"), bool):
        return ungrounded_yes_no(said)
    if isinstance(value.get("other"), str):
        return ungrounded_text(value["other"], said)
    if isinstance(value.get("option"), str):
        return ungrounded_choice(value["option"], said)
    for chosen in value.get("options", []) or []:
        problem = ungrounded_choice(chosen, said)
        if problem is not None:
            return problem
    return None


def _answers(kind: str | None = None) -> list[tuple[str, dict[str, Any]]]:
    out = []
    for path in FIXTURES:
        for index, answer in enumerate(_load(path)["answers"]):
            if kind == "invented" and not answer.get("invented"):
                continue
            if kind == "sound" and answer.get("invented"):
                continue
            out.append((f"{path.stem}[{index}]", answer))
    return out


def test_there_is_something_to_replay():
    """A replay suite with nothing to replay passes without checking anything, which is
    the failure mode this whole file exists to avoid elsewhere."""
    assert FIXTURES, f"nothing in {LIVE_RUNS}; capture a run with scripts/live_conversation.py"


def _ids(value: Any) -> str:
    return value if isinstance(value, str) else ""


@pytest.mark.parametrize("name,answer", _answers("sound"), ids=_ids)
def test_an_answer_a_real_model_produced_is_still_accepted(name: str, answer: dict[str, Any]):
    """No false refusals. Every one of these was accepted in a real conversation, so a gate
    that refuses one now has been tightened past what real respondents do."""
    problem = _grounding_problem(answer)
    assert problem is None, f"{name} was accepted live and is refused now: {problem}"


@pytest.mark.parametrize("name,answer", _answers("invented"), ids=_ids)
def test_a_known_invention_is_refused(name: str, answer: dict[str, Any]):
    """The other direction, and the one that turns a live finding into a permanent test."""
    problem = _grounding_problem(answer)
    assert problem is not None, f"{name} is a marked invention and got through"


@pytest.mark.parametrize("name,answer", _answers(), ids=_ids)
def test_a_recorded_value_still_has_a_shape_the_gate_accepts(name: str, answer: dict[str, Any]):
    """Shape, separately from source. An unanswerable is a refusal rather than a value, and
    a follow-up answer is judged by a different rule, so neither is replayed here."""
    value = answer["value"]
    if "unanswerable" in value or answer["kind"] != "scripted" or answer["answer_type"] is None:
        pytest.skip("not a scripted value answer")
    question = {
        "answer_type": answer["answer_type"],
        "options": answer["options"],
        "allow_other": answer["allow_other"],
    }
    try:
        validate_answer(question, _as_submitted(value))
    except AnswerValidationError as exc:
        pytest.fail(f"{name} was stored live and its shape is refused now: {exc.message}")


def _as_submitted(value: dict[str, Any]) -> Any:
    """The stored value turned back into what the model would have sent.

    Every shape but one stores a single key, so the value alone reconstructs it. A
    multi-select splits itself: chosen options under ``options`` and write-ins under
    ``other``, from one list the model sent. Taking the first key alone therefore replayed
    half the answer, and on a run where every item was a write-in it replayed an empty
    list and failed the gate over data the engine had accepted perfectly well.

    Found by the corpus rather than by reading: the shape needs a multi-select answered
    entirely in write-ins to show up, and there was none until this pass captured one.
    """
    if "options" in value:
        return list(value["options"]) + list(value.get("other", []))
    return next(iter(value.values()))
