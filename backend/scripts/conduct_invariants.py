"""What must be true of any conversation the engine conducted, checked from its trace.

These used to live inside ``scripts/live_conversation.py``, which meant they only ever
ran during a paid live run: a developer with an API key, on purpose, a few times a week.
Every probe-sequencing defect in docs/DEFECTS.md (20, 22, and the open O4) was found that
way, by a person watching a real conversation, because nothing else was looking.

So the trace of each captured run is written into its fixture and these run over the
corpus on every push, for free. Exactly the trick ``tests/test_live_replay.py`` plays for
the grounding gates, one layer up: there, recorded answers are replayed through today's
validators; here, recorded conversations are replayed through today's invariants.

Stdlib only, and no import from ``app``. The live harness runs on plain ``python3``
against the HTTP API (see .github/workflows/live-conduct.yml), so anything it shares with
the suite has to survive without the backend's virtualenv.

An invariant returns ``(name, ok, detail)``. The caller decides what a failure means: the
live harness folds it into its own hard/soft reporting, the test suite fails on it.
"""

from __future__ import annotations

from typing import Any

# The engine's MAX_FOLLOW_UPS, stated here rather than imported for the reason above. A
# copy of a constant is a thing that can drift, so tests/test_behaviour_replay.py asserts
# the two agree; that assertion is the whole reason this is safe to duplicate.
EXPECTED_FOLLOW_UP_CAP = 3

Check = tuple[str, bool, Any]


def _follow_up_counts(answers: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for answer in answers:
        if answer.get("kind") == "follow_up":
            key = str(answer.get("question_id"))
            counts[key] = counts.get(key, 0) + 1
    return counts


def place_keeping(trace: dict[str, Any]) -> Check:
    """The survey moves forward one question at a time, or stays put, and never past the
    end.

    A backwards step means the engine let the model re-open a question already answered,
    which is the door ``_rejection`` exists to shut. A jump of two means a question was
    skipped without a visibility rule deciding so, and the author would read it as
    unanswered by everyone.
    """
    positions = [int(p) for p in trace.get("positions", [])]
    total = int(trace.get("total", 0))
    steps = [b - a for a, b in zip(positions, positions[1:], strict=False)]
    ok = all(step in (0, 1) for step in steps) and all(0 <= p < total for p in positions)
    return ("the question index advances by at most one per message", ok, positions)


def follow_up_cap(trace: dict[str, Any]) -> Check:
    """No question is probed more than the cap allows.

    The budget is spent when a probe is *issued*, so a respondent who never answers one
    must still exhaust it. Without that, a model can probe forever, each probe another
    paid call with the whole transcript resent.
    """
    counts = _follow_up_counts(trace.get("answers", []))
    over = {qid: n for qid, n in counts.items() if n > EXPECTED_FOLLOW_UP_CAP}
    return (
        f"follow-ups per question stayed within {EXPECTED_FOLLOW_UP_CAP}",
        not over,
        over or counts,
    )


def forced_probes_were_asked(trace: dict[str, Any]) -> Check:
    """Every ``always_once`` question drew a follow-up answer.

    Defect 20: across 8 runs and ~90 model turns the engine asked no follow-up at all,
    because ``allow_follow_ups`` could grant permission but not express intent. The policy
    is enforced by withholding ``record_answer``, and this is what proves it still is.
    """
    forced = [
        str(q["id"])
        for q in trace.get("questions", [])
        if q.get("follow_up_policy") == "always_once"
    ]
    answered = {
        str(a.get("question_id")) for a in trace.get("answers", []) if a.get("kind") == "follow_up"
    }
    missed = [qid for qid in forced if qid not in answered]
    return ("every always_once question recorded a follow-up answer", not missed, missed)


def the_answer_before_the_probe_survived(trace: dict[str, Any]) -> Check:
    """A probed question still holds the scripted answer it had before the probe.

    Defect 22: the force lapsed the moment the probe was issued, so ``move_on`` returned
    on the turn the answer arrived and 3 of 16 forced probes threw their answer away. The
    trade this catches is the worst one available: an author's follow-up bought with the
    answer they already had.
    """
    forced = [
        str(q["id"])
        for q in trace.get("questions", [])
        if q.get("follow_up_policy") == "always_once"
    ]
    scripted = {
        str(a.get("question_id")) for a in trace.get("answers", []) if a.get("kind") == "scripted"
    }
    lost = [qid for qid in forced if qid not in scripted]
    return ("the answer given before a forced probe was kept", not lost, lost)


def one_scripted_answer_per_question(trace: dict[str, Any]) -> Check:
    """A question carries at most one scripted answer.

    Two means a double-clicked send got through the row lock, and the author's results
    read "2 of 2 answered" on a run whose second question was never asked.
    """
    counts: dict[str, int] = {}
    for answer in trace.get("answers", []):
        if answer.get("kind") == "scripted":
            key = str(answer.get("question_id"))
            counts[key] = counts.get(key, 0) + 1
    doubled = {qid: n for qid, n in counts.items() if n > 1}
    return ("each question holds at most one scripted answer", not doubled, doubled)


ALL = (
    place_keeping,
    follow_up_cap,
    forced_probes_were_asked,
    the_answer_before_the_probe_survived,
    one_scripted_answer_per_question,
)


def check_all(trace: dict[str, Any]) -> list[Check]:
    """Every invariant against one trace, in a fixed order."""
    return [invariant(trace) for invariant in ALL]
