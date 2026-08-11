"""The curated sample dataset as golden data.

Three angles: the fixtures are internally consistent; the completed conversations
replay through the conduct engine and reproduce their recorded answers; and the whole
set loads into a database and reads back through the results and export paths. Together
these turn real conducted runs into regression coverage.
"""

from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio

from app.conduct.engine import ConductEngine
from app.conduct.validation import validate_answer
from app.llm.client import ToolTurn
from app.runs.enums import RunStatus
from app.runs.service import ResultsService
from app.sample_data import SAMPLE_RUNS, SAMPLE_SURVEYS, survey_for_run
from app.sample_data.loader import load_sample_data
from app.seed import SEED_USERS
from app.users.models import User, UserRole
from tests.fakes import FakeLLM, move_on, record

AUTHOR_KEYS = {"ava", "arjun"}


@pytest_asyncio.fixture
async def seeded_users(session) -> dict[str, UUID]:
    """The stable seed users the dataset refers to, keyed by email local-part."""
    for uid, email, name, role, department in SEED_USERS:
        session.add(User(id=uid, email=email, display_name=name, role=role, department=department))
    await session.flush()
    return {row[1].split("@", 1)[0]: row[0] for row in SEED_USERS}


def _derive_raw(value: dict[str, Any]) -> Any:
    """Invert a stored answer value back to the raw the model would have sent."""
    for key in ("yes_no", "rating", "number", "text", "date", "option"):
        if key in value:
            return value[key]
    if "options" in value:
        return list(value["options"]) + list(value.get("other", []))
    if "other" in value:  # a single_select write-in
        return value["other"]
    raise AssertionError(f"cannot derive a raw answer from {value}")


# --- integrity: the fixtures are internally consistent -------------------------


def test_every_run_points_at_a_known_survey_and_respondent():
    for run in SAMPLE_RUNS:
        survey = survey_for_run(run)  # raises if the survey_key is unknown
        assert survey["version"]["definition"]["questions"], "survey has no questions"
        # The cleanup: no author is ever used as a respondent.
        assert run["respondent"] not in AUTHOR_KEYS


def test_answers_reference_questions_in_the_survey_definition():
    for run in SAMPLE_RUNS:
        question_ids = {q["id"] for q in survey_for_run(run)["version"]["definition"]["questions"]}
        for answer in run["answers"]:
            assert answer["question_id"] in question_ids


def test_stored_answer_values_still_validate():
    """Every scripted, answered value round-trips through the current validator."""
    for run in SAMPLE_RUNS:
        questions = {q["id"]: q for q in survey_for_run(run)["version"]["definition"]["questions"]}
        for answer in run["answers"]:
            value = answer["value"]
            if answer["kind"] != "scripted" or "unanswerable" in value:
                continue  # declines and model-invented probes don't go through the gate
            question = questions[answer["question_id"]]
            assert validate_answer(question, _derive_raw(value)) == value


def test_completed_runs_reached_the_end():
    for run in SAMPLE_RUNS:
        if run["status"] != "completed":
            continue
        total = len(survey_for_run(run)["version"]["definition"]["questions"])
        assert run["completed"] is True
        assert run["current_question_index"] == total


def test_transcripts_only_use_known_roles():
    for run in SAMPLE_RUNS:
        assert {m["role"] for m in run["messages"]} <= {"assistant", "user"}


# --- replay: the engine reproduces the recorded conversations ------------------

REPLAYABLE = [
    run
    for run in SAMPLE_RUNS
    if run["status"] == "completed" and all(a["kind"] == "scripted" for a in run["answers"])
]


@pytest.mark.parametrize("run", REPLAYABLE, ids=lambda r: r["survey_key"])
async def test_replaying_a_recorded_run_reproduces_its_answers(session, seeded_users, run):
    await load_sample_data(session)
    survey = survey_for_run(run)
    # Replayed by a respondent other than the one the fixture records. Loading the sample
    # data gives that person their one response to this survey, and one response per
    # person is the rule now, so starting a live run as them is refused. Who answers does
    # not change what the engine records, which is the whole of what this asserts.
    others = [
        email.split("@", 1)[0]
        for _, email, _, role, _ in SEED_USERS
        if role is UserRole.respondent and email.split("@", 1)[0] != run["respondent"]
    ]
    respondent = await session.get(User, seeded_users[others[0]])

    engine = ConductEngine(session, llm=FakeLLM())
    live = await engine.start_run(UUID(survey["template_id"]), respondent)
    for answer in run["answers"]:
        value = answer["value"]
        if "unanswerable" in value:
            turn = ToolTurn(
                text="", tool_name="flag_unanswerable", tool_input={"reason": value["unanswerable"]}
            )
            llm = FakeLLM(turn)
        else:
            llm = FakeLLM(record(_derive_raw(value)), move_on())
        # The respondent says what the fixture records. This used to send the literal
        # word "reply" for every turn, which made the replay unable to exercise the
        # grounding gate at all: a recorded answer must be traceable to what was really
        # typed, and "reply" traces to nothing. Saying the answer keeps the replay a
        # replay rather than a shape check with a placeholder attached.
        spoken = str(_derive_raw(value)) if "unanswerable" not in value else "reply"
        live = await ConductEngine(session, llm=llm).handle_message(live.id, spoken, respondent)

    assert live.status is RunStatus.completed
    assert [(a.kind.value, a.value) for a in live.answers] == [
        (a["kind"], a["value"]) for a in run["answers"]
    ]


# --- load: the whole set reads back through the real paths ---------------------


async def test_load_is_idempotent(session, seeded_users):
    assert await load_sample_data(session) == (len(SAMPLE_SURVEYS), len(SAMPLE_RUNS))
    assert await load_sample_data(session) == (0, 0)


async def test_loaded_runs_are_readable_by_their_author(session, seeded_users):
    await load_sample_data(session)
    results = ResultsService(session)
    for survey in SAMPLE_SURVEYS:
        author = await session.get(User, seeded_users[survey["created_by"]])
        summaries = await results.list_runs(UUID(survey["template_id"]), author)
        expected = sum(1 for r in SAMPLE_RUNS if r["survey_key"] == survey["key"])
        assert len(summaries) == expected


async def test_the_in_progress_run_can_be_resumed(session, seeded_users):
    await load_sample_data(session)
    in_progress = next(r for r in SAMPLE_RUNS if r["status"] == "in_progress")
    respondent = await session.get(User, seeded_users[in_progress["respondent"]])

    run = await ConductEngine(session, llm=FakeLLM()).load(UUID(in_progress["run_id"]), respondent)

    assert run.status is RunStatus.in_progress
    assert run.current_question_index == in_progress["current_question_index"]


async def test_the_sample_data_reads_back_as_answers(session, seeded_users):
    """The fixtures are meant to give a new author something to look at, so the check is
    that they arrive through the author-facing path, not merely that the rows loaded.

    Asked of the report since the export was removed. Same question of the same data: the
    report is now the only place the sample answers are read back in aggregate."""
    await load_sample_data(session)
    onboarding = next(s for s in SAMPLE_SURVEYS if s["key"] == "new-hire-onboarding")
    author = await session.get(User, seeded_users[onboarding["created_by"]])

    report = await ResultsService(session).report(UUID(onboarding["template_id"]), author)

    assert report.title == onboarding["title"]
    assert report.runs_total, "expected the sample runs to be counted"
    assert any(q.answered for q in report.questions), "expected at least one answered question"
