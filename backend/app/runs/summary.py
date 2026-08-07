"""AI summary of a completed run (SPEC.md 2.2, stretch 1).

The author asks for it; the LLM returns it through a schema-constrained tool call; the
validated result is stored on ``survey_runs.summary`` so it is generated once. Three
gates sit between the model and the column: the schema, a check that every quote is a
verbatim span of something the respondent actually said, and a fresh-context checker
that reads the draft against the answers and either passes it or sends it back with
notes. A summary is an author-facing artifact they will act on, and an invented quote
is indistinguishable from a real one once it is rendered next to the answers.

The checker exists for what the first two gates cannot decide: whether the headline and
key facts are *supported*. A rule can prove a quote verbatim; only a reader can notice a
fact the respondent never gave. It runs in a separate call that sees the answers and the
candidate and nothing of how the draft was made, because a model marking its own
homework in its own context is suspiciously generous about it.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, NotFoundError
from app.i18n import language_note
from app.llm import ledger
from app.llm.client import LLMError, LLMProtocol
from app.llm.decoding import decode_stringified
from app.llm.factory import get_llm
from app.llm.prompts import load_prompt
from app.runs.enums import AnswerKind, RunStatus
from app.runs.models import Answer, SurveyRun, add_llm_spend
from app.runs.repository import ResultsRepository
from app.runs.service import flatten_answer
from app.templates.repository import TemplateRepository
from app.users.models import User

logger = logging.getLogger("app.runs.summary")

MAX_KEY_FACTS = 8
MAX_QUOTES = 5
MAX_PROBLEMS = 8
PROMPT_VERSION = "summarise_run_v1"
VERIFY_PROMPT_VERSION = "verify_summary_v1"


class Quote(BaseModel):
    question: str = Field(min_length=1)
    quote: str = Field(min_length=1)

    @field_validator("question", "quote")
    @classmethod
    def _has_content(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("cannot be blank")
        return text


class RunSummaryContent(BaseModel):
    """The stored shape. Only the headline is required: a run of three bare ratings has
    no facts worth listing and nothing worth quoting, and padding it would be invention."""

    headline: str = Field(min_length=1, max_length=300)
    key_facts: list[str] = Field(default_factory=list, max_length=MAX_KEY_FACTS)
    notable_quotes: list[Quote] = Field(default_factory=list, max_length=MAX_QUOTES)

    @field_validator("headline")
    @classmethod
    def _headline_has_content(cls, value: str) -> str:
        headline = value.strip()
        if not headline:
            raise ValueError("headline cannot be blank")
        return headline

    @field_validator("key_facts")
    @classmethod
    def _facts_are_readable(cls, values: list[str]) -> list[str]:
        facts: list[str] = []
        for value in values:
            fact = value.strip().lstrip("-•* ").strip()
            if not fact:
                raise ValueError("a key fact cannot be blank")
            facts.append(fact)
        return facts


class SummaryVerdict(BaseModel):
    """The checker's verdict on one candidate summary.

    ``problems`` is what the writer gets back, so an unfaithful verdict that names
    nothing actionable is itself invalid: "fail, no reason given" cannot be sent back
    as notes and cannot be acted on.
    """

    faithful: bool
    problems: list[str] = Field(default_factory=list, max_length=MAX_PROBLEMS)

    @field_validator("problems")
    @classmethod
    def _problems_are_readable(cls, values: list[str]) -> list[str]:
        problems: list[str] = []
        for value in values:
            problem = value.strip().lstrip("-•* ").strip()
            if not problem:
                raise ValueError("a problem cannot be blank")
            problems.append(problem)
        return problems

    @model_validator(mode="after")
    def _unfaithful_names_the_fault(self) -> "SummaryVerdict":
        if not self.faithful and not self.problems:
            raise ValueError("an unfaithful verdict must name at least one problem")
        return self


_TOOL: dict[str, Any] = {
    "name": "summarise_run",
    "description": "Return a structured summary of one completed survey response.",
    "input_schema": RunSummaryContent.model_json_schema(),
}

_VERIFY_TOOL: dict[str, Any] = {
    "name": "report_verdict",
    "description": "Report whether the candidate summary is supported by the answers.",
    "input_schema": SummaryVerdict.model_json_schema(),
}


class RunSummaryService:
    def __init__(
        self,
        session: AsyncSession,
        llm: LLMProtocol | None = None,
        verifier: LLMProtocol | None = None,
    ) -> None:
        self.session = session
        self._llm = llm
        self._verifier = verifier
        self.repo = ResultsRepository(session)
        self.templates = TemplateRepository(session)

    @property
    def llm(self) -> LLMProtocol:
        """Built on first use, so reading a stored summary needs no model."""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    @property
    def verifier(self) -> LLMProtocol:
        """The checker's client: the writer's chain unless a different one is injected.

        A separate seam because fresh context removes a model's generosity toward its
        own draft but not its blind spots; a different model family in this seat would
        remove some of those too.
        """
        if self._verifier is None:
            self._verifier = self.llm
        return self._verifier

    async def summarise(
        self, template_id: UUID, run_id: UUID, author: User, refresh: bool = False
    ) -> RunSummaryContent:
        run = await self._run_for_author(template_id, run_id, author)
        if run.summary is not None and not refresh:
            # Already generated. Re-validated rather than trusted: the column is JSONB
            # and a summary written by an older prompt version may not match this shape.
            try:
                return RunSummaryContent.model_validate(run.summary)
            except PydanticValidationError:
                logger.warning("stored summary no longer validates, regenerating: run=%s", run.id)

        if run.status is not RunStatus.completed:
            raise ConflictError("Only a completed run can be summarised.")
        if not run.answers:
            raise ConflictError("This run has no answers to summarise.")

        # Measured against this run like any conduct turn: the summary's calls are the
        # largest this run will ever make, and rows with run_id=null would exclude
        # exactly them from "what did this run cost".
        with ledger.measuring(run.id) as spend:
            content = await self._generate(run, reviewer_notes=None)
            verdict = await self._verify(run, content)
            if not verdict.faithful:
                # Send it back with the checker's notes, through the same channel a
                # schema rejection uses, and check the redraft from scratch.
                notes = "; ".join(verdict.problems)
                logger.warning(
                    "summary failed verification, redrafting: run=%s problems=%r",
                    run.id,
                    verdict.problems,
                )
                content = await self._generate(
                    run,
                    reviewer_notes=(
                        f"a reviewer compared it against the answers and found: {notes}"
                    ),
                )
                verdict = await self._verify(run, content)
        add_llm_spend(run, spend)
        if not verdict.faithful:
            # Nothing is stored: an unsupported summary rendered beside the answers is
            # worse than the author reading the answers themselves. Raising discards the
            # uncommitted rollup too; the ledger file keeps the calls that were made,
            # which is the record that survives failed work.
            logger.error(
                "summary failed verification twice: run=%s problems=%r",
                run.id,
                verdict.problems,
            )
            raise LLMError(
                "The summary could not be verified against the answers: "
                + "; ".join(verdict.problems)
            )
        run.summary = {
            **content.model_dump(),
            "prompt_version": PROMPT_VERSION,
            "verify_prompt_version": VERIFY_PROMPT_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        await self.session.commit()
        return content

    async def _generate(self, run: SurveyRun, reviewer_notes: str | None) -> RunSummaryContent:
        """One draft, with its own schema retry.

        ``reviewer_notes`` is the checker's feedback on a previous draft; the schema
        retry is a separate, per-draft budget. They used to share one variable, so the
        post-verification redraft arrived looking like it had already spent its retry
        and failed on its first malformed field, the only model call in the system
        denied the one nudge every other call gets.
        """
        rejected: str | None = None
        for _ in range(2):
            messages = [{"role": "user", "content": _transcript_for(run)}]
            feedback = "; ".join(filter(None, (reviewer_notes, rejected)))
            if feedback:
                messages.append(
                    {
                        "role": "user",
                        "content": f"Your previous summary was rejected: {feedback}\n"
                        "Return a corrected summary.",
                    }
                )
            turn = await self.llm.tool_turn(
                # Written in the language the run was conducted in. A summary is read
                # beside the answers it describes, and an English summary of an Arabic
                # conversation forces the author to translate one of the two themselves.
                system="\n\n".join((load_prompt(PROMPT_VERSION), language_note(run.language))),
                messages=messages,
                tools=[_TOOL],
                max_tokens=2048,
            )
            raw = _decode_stringified_fields(turn.tool_input)
            # Fabricated quotes are dropped before validation, never after: mutating a
            # validated model skips Pydantic's checks and can break its own invariants.
            raw = _without_invented_quotes(raw, run)
            try:
                return RunSummaryContent.model_validate(raw)
            except PydanticValidationError as exc:
                if rejected is not None:
                    # The rejection names the fault but not the payload, so keep it
                    # before failing (ARCHITECTURE.md 3.3).
                    logger.error(
                        "run summary failed after one retry: run=%s raw=%r error=%s",
                        run.id,
                        raw,
                        exc,
                    )
                    raise LLMError(
                        f"Model returned an invalid summary after one retry: {exc}"
                    ) from exc
                rejected = str(exc)
                logger.warning("run summary rejected, retrying: run=%s error=%s", run.id, exc)
        raise LLMError("unreachable")  # the loop either returns or raises

    async def _verify(self, run: SurveyRun, content: RunSummaryContent) -> SummaryVerdict:
        """Fresh context: the checker sees the answers and the candidate, and nothing of
        how the draft was made, neither the writer's briefing nor its earlier attempts.
        """
        turn = await self.verifier.tool_turn(
            # The checker reads the same language it is checking, or it cannot judge
            # whether a quote supports a claim.
            system="\n\n".join((load_prompt(VERIFY_PROMPT_VERSION), language_note(run.language))),
            messages=[{"role": "user", "content": _verification_brief(run, content)}],
            tools=[_VERIFY_TOOL],
            max_tokens=1024,
        )
        raw = dict(turn.tool_input)
        if "problems" in raw:
            raw["problems"] = decode_stringified(raw["problems"], list)
        try:
            return SummaryVerdict.model_validate(raw)
        except PydanticValidationError as exc:
            # A checker that cannot say what is wrong has not checked anything; failing
            # open here would make the gate decorative.
            logger.error("summary verdict rejected: run=%s raw=%r error=%s", run.id, raw, exc)
            raise LLMError(f"Checker returned an invalid verdict: {exc}") from exc

    async def _run_for_author(self, template_id: UUID, run_id: UUID, author: User) -> SurveyRun:
        """Same ownership rule as the rest of results: someone else's survey reads as
        absent rather than forbidden."""
        template = await self.templates.get(template_id)
        if template is None or template.created_by != author.id:
            raise NotFoundError("Template not found.")
        row = await self.repo.get_detail(run_id)
        if row is None:
            raise NotFoundError("Run not found.")
        run, version, _ = row
        if version.template_id != template_id:
            raise NotFoundError("That run belongs to a different template.")
        return cast("SurveyRun", run)  # unpacking a Row loses the element types


def _decode_stringified_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Undo one JSON-encoding of the list fields, the usual small-model slip."""
    decoded = dict(raw)
    for key in ("key_facts", "notable_quotes"):
        if key in decoded:
            decoded[key] = decode_stringified(decoded[key], list)
    if isinstance(decoded.get("notable_quotes"), list):
        decoded["notable_quotes"] = [decode_stringified(q, dict) for q in decoded["notable_quotes"]]
    return decoded


def _normalised(text: str) -> str:
    """Casefolded with runs of whitespace collapsed — models reflow quotes across lines
    and normalise spacing, which is not the same as inventing them."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def _without_invented_quotes(raw: dict[str, Any], run: SurveyRun) -> dict[str, Any]:
    """Drop any quote that is not a verbatim span of a recorded answer.

    Dropped rather than rejected: the rest of the summary is usually sound, and
    ``notable_quotes`` has no floor, so losing one costs the author nothing while
    keeping a fabricated one costs them a decision made on words nobody said.
    """
    quotes = raw.get("notable_quotes")
    if not isinstance(quotes, list) or not quotes:
        return raw
    said = "   ".join(_normalised(_answer_text(a)) for a in run.answers)
    kept: list[Any] = []
    for quote in quotes:
        text = quote.get("quote") if isinstance(quote, dict) else None
        if isinstance(text, str) and _normalised(text) and _normalised(text) in said:
            kept.append(quote)
        else:
            logger.warning("dropped an unsupported quote: run=%s quote=%r", run.id, text)
    return {**raw, "notable_quotes": kept}


def _answer_text(answer: Answer) -> str:
    return flatten_answer(answer.value)


def _answers_block(run: SurveyRun) -> str:
    """The answers as a model should see them: scripted questions with their follow-ups
    beneath, in the order they were given. The chat transcript is deliberately left out —
    it carries the model's own phrasing, which is not evidence of what the respondent said.

    Writer and checker are both fed from this one extract, so the checker judges the
    draft against exactly what the writer was given: never against more, which would fail
    sound drafts, and never against less, which would pass unsupported ones.
    """
    lines = []
    for answer in run.answers:
        prefix = "  follow-up" if answer.kind is AnswerKind.follow_up else "Q"
        lines.append(f"{prefix}: {answer.question_text}")
        lines.append(
            f"{'  ' if answer.kind is AnswerKind.follow_up else ''}A: {_answer_text(answer)}"
        )
    return "\n".join(lines)


def _transcript_for(run: SurveyRun) -> str:
    return f"Here is one completed response. Summarise it.\n\n{_answers_block(run)}"


def _verification_brief(run: SurveyRun, content: RunSummaryContent) -> str:
    summary = json.dumps(content.model_dump(), ensure_ascii=False, indent=2)
    return (
        "Here is one completed survey response, and a candidate summary of it.\n\n"
        f"Answers:\n{_answers_block(run)}\n\nCandidate summary:\n{summary}"
    )
