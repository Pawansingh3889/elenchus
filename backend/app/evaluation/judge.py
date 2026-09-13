"""A second model reads a finished run and says, per recorded answer, whether it was said.

Soft by design, as the live check's judge is: its verdicts are stored and scored against
people's labels, and never decide anything on their own. It answers through a structured
tool call, and a reply that skips or repeats an answer is refused rather than half-kept,
because a partial set of verdicts would count the skipped answers as unjudged and quietly
flatter the judge's recall.
"""

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.llm.client import LLMError, LLMProtocol
from app.llm.prompts import load_prompt

JUDGE_PROMPT_VERSION = "judge_answers_v1"

VERDICTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "supported": {"type": "boolean"},
                    "why": {"type": "string"},
                },
                "required": ["index", "supported", "why"],
            },
        }
    },
    "required": ["verdicts"],
}


@dataclass(frozen=True)
class Verdict:
    index: int
    supported: bool
    why: str


async def ask_judge(
    llm: LLMProtocol, *, said: list[str], recorded: list[dict[str, Any]], today: date
) -> list[Verdict]:
    """One verdict per recorded answer, in the order given."""
    arguments = await llm.tool_call(
        system=load_prompt(JUDGE_PROMPT_VERSION),
        prompt=json.dumps(
            {
                "today": today.isoformat(),
                "respondent_messages": said,
                "recorded_answers": recorded,
            },
            indent=2,
            ensure_ascii=False,
        ),
        tool_name="record_verdicts",
        tool_description="Record one verdict for every recorded answer, by its index.",
        input_schema=VERDICTS_SCHEMA,
    )
    raw = arguments.get("verdicts")
    if not isinstance(raw, list):
        raise LLMError("The judge returned no list of verdicts.")
    verdicts: dict[int, Verdict] = {}
    for item in raw:
        index = item.get("index") if isinstance(item, dict) else None
        supported = item.get("supported") if isinstance(item, dict) else None
        why = item.get("why") if isinstance(item, dict) else None
        if not isinstance(index, int) or not 0 <= index < len(recorded):
            raise LLMError(f"The judge named an answer that does not exist: {index!r}.")
        if index in verdicts:
            raise LLMError(f"The judge gave answer {index} two verdicts.")
        if not isinstance(supported, bool) or not isinstance(why, str):
            raise LLMError(f"The judge's verdict on answer {index} is malformed.")
        verdicts[index] = Verdict(index=index, supported=supported, why=why)
    missing = sorted(set(range(len(recorded))) - verdicts.keys())
    if missing:
        raise LLMError(f"The judge left answers {missing} without a verdict.")
    return [verdicts[index] for index in range(len(recorded))]
