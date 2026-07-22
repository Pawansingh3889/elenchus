"""The conduct engine.

Deterministic by construction. The engine decides which question is current, whether the
run is complete, and how many follow-ups remain — every one of those from the database,
never from the model. The model chooses exactly one validated action per turn and phrases
what to say. Nothing reaches the run until it has validated.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.conduct.repository import RunRepository
from app.conduct.validation import AnswerValidationError, validate_answer
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.llm.client import LLMClient, LLMError, LLMProtocol, ToolTurn
from app.llm.prompts import load_prompt
from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.runs.models import Answer, RunMessage, SurveyRun
from app.users.models import User

logger = logging.getLogger("app.conduct")

MAX_FOLLOW_UPS = 2
MAX_MODEL_TURNS = 3  # per respondent message
_REJECTED = "run=%s question=%s tool=%s raw_input=%r raw_text=%r error=%s"
CLOSING_FALLBACK = "That's everything — thank you, your answers are saved."

RECORD = "record_answer"
FOLLOW_UP = "ask_follow_up"
UNANSWERABLE = "flag_unanswerable"
MOVE_ON = "move_on"


class ConductEngine:
    def __init__(self, session: AsyncSession, llm: LLMProtocol | None = None) -> None:
        self.session = session
        self._llm = llm
        self.repo = RunRepository(session)

    @property
    def llm(self) -> LLMProtocol:
        """Built on first use: starting and reading a run needs no model at all."""
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    # ---------------------------------------------------------------- lifecycle

    async def start_run(self, template_id: UUID, respondent: User) -> SurveyRun:
        version = await self.repo.latest_version(template_id)
        if version is None:
            raise ConflictError("This template has no published version to answer.")
        questions = _questions_of(version.definition)
        if not questions:
            raise ConflictError("The published version has no questions.")

        run = SurveyRun(template_version_id=version.id, respondent_id=respondent.id)
        run.messages.append(
            RunMessage(
                role=MessageRole.assistant,
                content=_opening_text(version.definition, questions[0]),
            )
        )
        self.repo.add(run)
        await self.session.commit()
        return await self.load(run.id, respondent)

    async def load(self, run_id: UUID, respondent: User) -> SurveyRun:
        run = await self.repo.get(run_id)
        if run is None:
            raise NotFoundError("Run not found.")
        if run.respondent_id != respondent.id:
            raise ForbiddenError("This run belongs to another respondent.")
        return run

    async def questions(self, run: SurveyRun) -> list[dict[str, Any]]:
        version = await self.repo.get_version(run.template_version_id)
        if version is None:
            raise NotFoundError("The run's template version is missing.")
        return _questions_of(version.definition)

    async def handle_message(self, run_id: UUID, content: str, respondent: User) -> SurveyRun:
        run = await self.load(run_id, respondent)
        if run.status is not RunStatus.in_progress:
            raise ConflictError("This run is already finished.")
        questions = await self.questions(run)

        run.messages.append(RunMessage(role=MessageRole.user, content=content))
        await self.session.flush()

        utterance = await self._turn_loop(run, questions)
        run.messages.append(RunMessage(role=MessageRole.assistant, content=utterance))
        await self.session.commit()
        return await self.load(run_id, respondent)

    # ------------------------------------------------------------------- engine

    async def _turn_loop(self, run: SurveyRun, questions: list[dict[str, Any]]) -> str:
        recorded = False
        for _ in range(MAX_MODEL_TURNS):
            question = questions[run.current_question_index]
            state = await self._state(run, question)
            # One respondent message yields at most one answer, so recording is
            # withdrawn for the rest of the turn. Without this the model can record
            # repeatedly, and since recording neither advances nor spends a probe the
            # loop runs out of turns on a message that was never invalid.
            state["recorded_this_turn"] = recorded
            tools = _tools_for(question, state)
            turn = await self._decide(run, questions, question, state, tools, None)
            if turn.tool_name == RECORD:
                recorded = True
            utterance = await self._apply(run, questions, question, state, turn)
            if utterance is not None:
                return utterance
        raise LLMError("The model did not settle on an action for this turn.")

    async def _decide(
        self,
        run: SurveyRun,
        questions: list[dict[str, Any]],
        question: dict[str, Any],
        state: dict[str, Any],
        tools: list[dict[str, Any]],
        previous_error: str | None,
    ) -> ToolTurn:
        briefing = _briefing(questions, run.current_question_index, question, state, previous_error)
        turn = await self.llm.tool_turn(
            system=load_prompt("conduct_v1") + "\n\n" + briefing,
            messages=_transcript(run),
            tools=tools,
        )
        error = _rejection(question, state, tools, turn)
        if error is None:
            return turn
        if previous_error is None:
            logger.warning(
                "model action rejected, retrying: " + _REJECTED,
                run.id,
                question["id"],
                turn.tool_name,
                turn.tool_input,
                turn.text,
                error,
            )
            return await self._decide(run, questions, question, state, tools, error)
        # Second failure: the raw output is the only thing that explains why, so it is
        # logged before the turn fails (ARCHITECTURE.md 3.3).
        logger.error(
            "conduct turn failed after one retry: " + _REJECTED,
            run.id,
            question["id"],
            turn.tool_name,
            turn.tool_input,
            turn.text,
            error,
        )
        raise LLMError(f"Model produced an invalid action after one retry: {error}")

    async def _apply(
        self,
        run: SurveyRun,
        questions: list[dict[str, Any]],
        question: dict[str, Any],
        state: dict[str, Any],
        turn: ToolTurn,
    ) -> str | None:
        """Apply a validated action. Returns the assistant's utterance, or None to loop."""
        if turn.tool_name == FOLLOW_UP:
            # Spend the budget here, when the probe is issued. Reassigned rather than
            # mutated so SQLAlchemy sees the change to the JSONB column.
            key = question["id"]
            run.probes_asked = {**run.probes_asked, key: run.probes_asked.get(key, 0) + 1}
            await self.session.flush()
            return str(turn.tool_input["follow_up_text"]).strip()

        if turn.tool_name == RECORD:
            scripted = not state["scripted_recorded"]
            run.answers.append(
                Answer(
                    question_id=UUID(question["id"]),
                    kind=AnswerKind.scripted if scripted else AnswerKind.follow_up,
                    question_text=question["text"] if scripted else _last_assistant(run),
                    value=validate_answer(question, turn.tool_input["value"]),
                    answered_by=run.respondent_id,
                )
            )
            await self.session.flush()
            if _may_probe(question, state["follow_ups_used"]):
                return None  # let the model decide: probe again, or move on
            return self._advance(run, questions, turn)

        if turn.tool_name == UNANSWERABLE:
            # Declining the question itself is a scripted answer; declining a probe is a
            # follow-up answer, and carries the wording the model invented for it.
            declined_probe = state["scripted_recorded"]
            run.answers.append(
                Answer(
                    question_id=UUID(question["id"]),
                    kind=AnswerKind.follow_up if declined_probe else AnswerKind.scripted,
                    question_text=_last_assistant(run) if declined_probe else question["text"],
                    value={"unanswerable": str(turn.tool_input.get("reason", "")).strip()},
                    answered_by=run.respondent_id,
                )
            )
            await self.session.flush()
            return self._advance(run, questions, turn)

        return self._advance(run, questions, turn)  # move_on

    def _advance(self, run: SurveyRun, questions: list[dict[str, Any]], turn: ToolTurn) -> str:
        run.current_question_index += 1
        if run.current_question_index >= len(questions):
            run.status = RunStatus.completed
            run.completed_at = datetime.now(UTC)
            return turn.text or CLOSING_FALLBACK
        return turn.text or questions[run.current_question_index]["text"]

    async def _state(self, run: SurveyRun, question: dict[str, Any]) -> dict[str, Any]:
        scripted = await self.repo.count_answers(run.id, UUID(question["id"]), AnswerKind.scripted)
        return {
            "scripted_recorded": scripted > 0,
            "follow_ups_used": run.probes_asked.get(question["id"], 0),
        }


# ------------------------------------------------------------------- helpers


def _questions_of(definition: dict[str, Any]) -> list[dict[str, Any]]:
    questions = definition.get("questions") or []
    return sorted(questions, key=lambda q: q["position"])


def _may_probe(question: dict[str, Any], follow_ups_used: int) -> bool:
    return bool(question.get("allow_follow_ups")) and follow_ups_used < MAX_FOLLOW_UPS


def _opening_text(definition: dict[str, Any], first: dict[str, Any]) -> str:
    return f"Thanks for taking {definition['title']}. {first['text']}"


def _last_assistant(run: SurveyRun) -> str:
    for message in reversed(run.messages):
        if message.role is MessageRole.assistant:
            return message.content
    return "Follow-up"


def _transcript(run: SurveyRun) -> list[dict[str, str]]:
    return [
        {"role": "assistant" if m.role is MessageRole.assistant else "user", "content": m.content}
        for m in run.messages
    ]


def _tools_for(question: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    """Only offer the actions that are legal right now — the engine's first gate."""
    question_id = {"type": "string", "description": "The current question's id."}
    tools: list[dict[str, Any]] = []
    if not state.get("recorded_this_turn"):
        tools.append(
            {
                "name": RECORD,
                "description": "Record the respondent's answer to what you just asked.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question_id": question_id,
                        "value": {"description": "The answer, shaped for the question's type."},
                    },
                    "required": ["question_id", "value"],
                },
            }
        )
    # Probing is not gated on an answer existing. Requiring one first meant a model that
    # wanted to clarify a vague reply had to record something to unlock the tool, and it
    # duly invented plausible values to get there. The cap still bounds it.
    if _may_probe(question, state["follow_ups_used"]):
        tools.append(
            {
                "name": FOLLOW_UP,
                "description": (
                    "Ask one short follow-up: to probe an answer just given, or to ask "
                    "plainly for an answer the reply did not contain."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question_id": question_id,
                        "follow_up_text": {"type": "string"},
                    },
                    "required": ["question_id", "follow_up_text"],
                },
            }
        )
    if state["scripted_recorded"]:
        tools.append(
            {
                "name": MOVE_ON,
                "description": "Nothing worth probing; go to the next question.",
                "input_schema": {
                    "type": "object",
                    "properties": {"question_id": question_id},
                    "required": ["question_id"],
                },
            }
        )
    # Always available: a respondent can decline the question itself, and equally can
    # decline a follow-up. Offering this only before the scripted answer left the model
    # with no way to say "they declined" once a probe was outstanding.
    tools.append(
        {
            "name": UNANSWERABLE,
            "description": (
                "The respondent declined or cannot answer what you just asked, whether "
                "that was the question itself or a follow-up. The survey moves on."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"question_id": question_id, "reason": {"type": "string"}},
                "required": ["question_id", "reason"],
            },
        }
    )
    return tools


def _rejection(
    question: dict[str, Any],
    state: dict[str, Any],
    tools: list[dict[str, Any]],
    turn: ToolTurn,
) -> str | None:
    """Second gate: re-check the chosen action in code, whatever was offered."""
    allowed = {t["name"] for t in tools}
    if turn.tool_name not in allowed:
        return f"'{turn.tool_name}' is not available now; choose one of {sorted(allowed)}"

    if turn.tool_name == FOLLOW_UP:
        if not _may_probe(question, state["follow_ups_used"]):
            return "follow-ups are not permitted for this question, or the limit is spent"
        if not str(turn.tool_input.get("follow_up_text", "")).strip():
            return "follow_up_text must not be empty"
        return None

    if turn.tool_name == RECORD:
        if "value" not in turn.tool_input:
            return "record_answer requires a value"
        try:
            validate_answer(question, turn.tool_input["value"])
        except AnswerValidationError as exc:
            return exc.message
        return None

    if turn.tool_name == UNANSWERABLE and not str(turn.tool_input.get("reason", "")).strip():
        return "flag_unanswerable requires a reason"
    return None


def _briefing(
    questions: list[dict[str, Any]],
    index: int,
    question: dict[str, Any],
    state: dict[str, Any],
    previous_error: str | None,
) -> str:
    nxt = questions[index + 1]["text"] if index + 1 < len(questions) else None
    lines = [
        "ENGINE STATE (authoritative — do not contradict it):",
        f"- Question {index + 1} of {len(questions)}: {question['text']}",
        f"- Answer type: {question['answer_type']}",
    ]
    if question.get("options"):
        lines.append(f"- Options: {question['options']}")
        lines.append(f"- Free-text 'other' allowed: {bool(question.get('allow_other'))}")
    if question["answer_type"] == "date":
        # Without this the model has no clock, and resolves "this year" against its
        # training data. A live run turned "the 3rd of March this year" into 2024-03-03.
        lines.append(f"- Today's date is {datetime.now(UTC).date().isoformat()}")
    lines.append(
        "- This question is required"
        if question.get("required", True)
        else "- This question is OPTIONAL: if they deflect, let it go rather than pressing"
    )
    lines.append(f"- Answer already recorded: {state['scripted_recorded']}")
    lines.append(
        f"- Follow-ups asked so far: {state['follow_ups_used']} of {MAX_FOLLOW_UPS}"
        if question.get("allow_follow_ups")
        else "- Follow-ups: not permitted for this question"
    )
    lines.append(
        f"- Next question: {nxt}" if nxt else "- This is the final question; close warmly."
    )
    if previous_error:
        lines.append(f"- Your previous tool call was REJECTED: {previous_error}. Choose again.")
    return "\n".join(lines)
