"""Replay how a real conversation *went*, not just what was said in it.

``test_live_replay.py`` replays recorded answers through today's validators, which
catches a gate tightened past what respondents actually write. It cannot catch the other
class entirely: whether the engine kept its place, spent its probe budget honestly, and
did not throw away an answer to ask about it. Those are properties of the sequence, and
until now they were only ever checked during a paid live run.

Two directions here, and both are needed.

  the invariants bite      Each one is handed a trace that violates it and must say so.
                           A checker nobody has watched reject anything is decoration,
                           which is the standard tests/test_gates.py holds the guards to
                           and there is no reason these are exempt.

  the corpus still holds   Every captured trace must satisfy every invariant. This is
                           vacuous while no fixture carries a trace, and becomes the real
                           regression suite the moment one does; the trace field is new,
                           so the runs recorded before it have none to replay.
"""

import json
from pathlib import Path

import conduct_invariants
import pytest
from conduct_invariants import EXPECTED_FOLLOW_UP_CAP, check_all

from app.conduct.engine import MAX_FOLLOW_UPS

LIVE_RUNS = Path(__file__).parent / "live_runs"
FIXTURES = sorted(LIVE_RUNS.glob("*.json"))


def _traced() -> list:
    """Every fixture carrying a trace, as parametrised cases.

    An empty corpus parametrises to pytest's own "got empty parameter set" skip, which
    reads in the output exactly like a test that ran. It has not run, and the reason
    matters: the trace field is newer than the runs recorded before it, so those have
    nothing to replay and the next capture fixes it. Said out loud rather than left to be
    inferred from a bare `s` in the progress line.
    """
    out = []
    for path in FIXTURES:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        trace = fixture.get("trace")
        if isinstance(trace, dict):
            out.append((path.stem, trace))
    if not out:
        return [
            pytest.param(
                "no traced fixture",
                {},
                marks=pytest.mark.skip(
                    reason=(
                        f"none of the {len(FIXTURES)} fixtures carries a trace yet; they "
                        "were captured before the field existed. Recapture with "
                        "scripts/live_conversation.py to give this something to replay."
                    )
                ),
            )
        ]
    return out


# A trace of a conversation that behaved: two questions, the first forcing a probe and
# getting one, the index never going backwards. Every planted violation below is this
# with exactly one thing wrong, so a failure names the thing rather than the fixture.
SOUND = {
    "total": 2,
    "positions": [0, 0, 1],
    "questions": [
        {"id": "q1", "position": 0, "follow_up_policy": "always_once"},
        {"id": "q2", "position": 1, "follow_up_policy": "never"},
    ],
    "answers": [
        {"question_id": "q1", "kind": "scripted"},
        {"question_id": "q1", "kind": "follow_up"},
        {"question_id": "q2", "kind": "scripted"},
    ],
}


def test_a_conversation_that_behaved_passes_every_invariant() -> None:
    """A checker that fails on everything is as useless as one that fails on nothing."""
    failed = [name for name, ok, _ in check_all(SOUND) if not ok]
    assert not failed, f"a sound trace was rejected by {failed}"


def test_a_backwards_jump_is_rejected() -> None:
    """The survey re-opening a question already answered is the door `_rejection` shuts.
    If the engine ever lets one through, the transcript shows it in the positions."""
    name, ok, _ = conduct_invariants.place_keeping({**SOUND, "positions": [0, 1, 0]})
    assert not ok, f"{name} accepted a backwards step"


def test_skipping_a_question_is_rejected() -> None:
    """Two at a time means a question was passed over without a visibility rule deciding
    so, and the author reads it as one nobody answered."""
    name, ok, _ = conduct_invariants.place_keeping({**SOUND, "positions": [0, 2]})
    assert not ok, f"{name} accepted a two-question jump"


def test_running_off_the_end_is_rejected() -> None:
    name, ok, _ = conduct_invariants.place_keeping({**SOUND, "positions": [0, 1, 2]})
    assert not ok, f"{name} accepted a position past the last question"


def test_probing_past_the_cap_is_rejected() -> None:
    """Defect territory: the budget is spent when a probe is issued, so a respondent who
    never answers one must still exhaust it. Without the cap a model probes forever, each
    probe another paid call with the whole transcript resent."""
    over = {
        **SOUND,
        "answers": SOUND["answers"]
        + [{"question_id": "q1", "kind": "follow_up"} for _ in range(EXPECTED_FOLLOW_UP_CAP)],
    }
    name, ok, _ = conduct_invariants.follow_up_cap(over)
    assert not ok, f"{name} accepted more probes than the cap allows"


def test_an_always_once_question_that_drew_no_probe_is_rejected() -> None:
    """Defect 20: 8 runs, ~90 model turns, no follow-up at all, because the old flag
    could grant permission but not express intent."""
    unprobed = {
        **SOUND,
        "answers": [a for a in SOUND["answers"] if a["kind"] != "follow_up"],
    }
    name, ok, _ = conduct_invariants.forced_probes_were_asked(unprobed)
    assert not ok, f"{name} accepted a forced question that was never probed"


def test_an_answer_lost_to_its_own_probe_is_rejected() -> None:
    """Defect 22: the force lapsed when the probe was issued, so `move_on` returned on the
    turn the answer arrived and 3 of 16 forced probes threw their answer away. The worst
    trade available: an author's follow-up bought with the answer they already had."""
    lost = {
        **SOUND,
        "answers": [
            a
            for a in SOUND["answers"]
            if not (a["question_id"] == "q1" and a["kind"] == "scripted")
        ],
    }
    name, ok, _ = conduct_invariants.the_answer_before_the_probe_survived(lost)
    assert not ok, f"{name} accepted a forced probe that lost the answer behind it"


def test_two_scripted_answers_on_one_question_are_rejected() -> None:
    """A double-clicked send getting past the row lock. The author's results then read
    "2 of 2 answered" on a run whose second question was never asked."""
    doubled = {**SOUND, "answers": SOUND["answers"] + [{"question_id": "q1", "kind": "scripted"}]}
    name, ok, _ = conduct_invariants.one_scripted_answer_per_question(doubled)
    assert not ok, f"{name} accepted two scripted answers on one question"


def test_the_shared_cap_matches_the_engines_own() -> None:
    """The invariants module states the cap rather than importing it, because the live
    harness runs on plain python3 with no backend virtualenv and cannot reach `app`. A
    copied constant is a constant that can drift, and this assertion is the entire reason
    copying it is safe: raise MAX_FOLLOW_UPS without raising the other and this fails."""
    assert EXPECTED_FOLLOW_UP_CAP == MAX_FOLLOW_UPS


@pytest.mark.parametrize("name,trace", _traced(), ids=lambda v: v if isinstance(v, str) else "")
def test_a_captured_conversation_still_satisfies_every_invariant(name: str, trace: dict) -> None:
    """The regression half. Every one of these is a conversation a real model conducted,
    and each stays a test of the engine's sequencing forever, for free, on every push."""
    failed = [check for check in check_all(trace) if not check[1]]
    assert not failed, f"{name} violates: " + "; ".join(f"{n} ({d})" for n, _, d in failed)
