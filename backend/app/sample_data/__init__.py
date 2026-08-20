"""Curated sample dataset: realistic surveys and conducted runs, drawn from real use.

The JSON files here are the committed source of truth. ``surveys.json`` holds six
published surveys (title, description, and the frozen version definition); ``runs.json``
holds eight conducted runs with their verbatim transcripts and recorded answers.

Everything refers to seed users by key (the email local-part, e.g. ``remy``), so the
data stays readable and portable across databases. See ``README.md`` for the shape and
how to regenerate it.

Used by ``app.seed`` to give a fresh database meaningful content, and by the test suite
as golden data driven through the conduct engine and the results/export paths.
"""

import json
from pathlib import Path
from typing import Any, TypedDict

_DATA_DIR = Path(__file__).parent


class VersionFixture(TypedDict):
    version_id: str
    number: int
    published_by: str
    definition: dict[str, Any]


class SurveyFixture(TypedDict):
    key: str
    template_id: str
    title: str
    description: str | None
    created_by: str
    version: VersionFixture


class MessageFixture(TypedDict):
    role: str
    content: str


class AnswerFixture(TypedDict):
    question_id: str
    kind: str
    question_text: str
    value: dict[str, Any]


class RunFixture(TypedDict):
    run_id: str
    survey_key: str
    respondent: str
    status: str
    current_question_index: int
    probes_asked: dict[str, int]
    completed: bool
    messages: list[MessageFixture]
    answers: list[AnswerFixture]


def _load(name: str) -> Any:
    return json.loads((_DATA_DIR / name).read_text(encoding="utf-8"))


SAMPLE_SURVEYS: list[SurveyFixture] = _load("surveys.json")
SAMPLE_RUNS: list[RunFixture] = _load("runs.json")

SURVEY_BY_KEY: dict[str, SurveyFixture] = {s["key"]: s for s in SAMPLE_SURVEYS}


def survey_for_run(run: RunFixture) -> SurveyFixture:
    """The survey a run was conducted against."""
    return SURVEY_BY_KEY[run["survey_key"]]


__all__ = [
    "SAMPLE_SURVEYS",
    "SAMPLE_RUNS",
    "SURVEY_BY_KEY",
    "SurveyFixture",
    "RunFixture",
    "AnswerFixture",
    "MessageFixture",
    "survey_for_run",
]
