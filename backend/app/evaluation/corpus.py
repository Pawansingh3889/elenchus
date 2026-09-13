"""The committed live-run corpus, as answers a person can label.

The fixtures under backend/tests/live_runs/ are what the replay tests and the eval ratchet
read, so they stay the source of truth for CI. This reads them as they are; labels made on
the lens live in the database until a script writes them back into the files.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.llm.eval_corpus import LIVE_RUNS_DIR


@dataclass(frozen=True)
class CorpusAnswer:
    fixture: str
    index: int
    scenario: str
    model: str
    captured_at: str | None
    question_text: str
    answer_type: str
    options: list[str]
    kind: str
    value: dict[str, Any]
    said: list[str]
    judge_supported: bool | None
    judge_why: str | None
    # The file's own hand-set mark, which the replay test enforces.
    marked_invented: bool


def load_corpus(directory: Path | None = None) -> list[CorpusAnswer]:
    """Every answer in every fixture, in file and answer order. Unreadable JSON fails loudly:
    a fixture that cannot be read is a broken test input, not an empty one."""
    directory = LIVE_RUNS_DIR if directory is None else directory
    answers = []
    for path in sorted(directory.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        for index, answer in enumerate(fixture["answers"]):
            judge = answer.get("judge") or {}
            answers.append(
                CorpusAnswer(
                    fixture=path.stem,
                    index=index,
                    scenario=str(fixture["scenario"]),
                    model=str(fixture["model"]),
                    captured_at=fixture.get("captured_at"),
                    question_text=str(answer["question_text"]),
                    answer_type=str(answer.get("answer_type") or "unknown"),
                    options=[str(option) for option in answer.get("options") or []],
                    kind=str(answer["kind"]),
                    value=dict(answer["value"]),
                    said=[str(message) for message in answer.get("said") or []],
                    judge_supported=judge.get("supported"),
                    judge_why=judge.get("why"),
                    marked_invented=bool(answer.get("invented")),
                )
            )
    return answers
