"""Natural-language template generation.

The author describes a survey; the LLM drafts it through a schema-constrained tool
call. The engine validates the result and, on failure, retries once with the error
before failing loudly (ARCHITECTURE.md: validate then act). A valid draft is persisted
so it lands in the same builder a hand-built one would.
"""

import logging
import re
from typing import Any
from uuid import UUID

from pydantic import Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ValidationError
from app.llm import ledger
from app.llm.client import LLMError, LLMProtocol
from app.llm.decoding import decode_stringified
from app.llm.factory import get_llm
from app.llm.prompts import load_prompt
from app.templates.enums import AnswerType, FollowUpPolicy, SurveyAudience
from app.templates.models import SurveyTemplate
from app.templates.schemas import TemplateCreate, TemplateUpdate
from app.templates.service import TemplateService
from app.users.models import User

logger = logging.getLogger("app.templates.generation")

MAX_GENERATED_QUESTIONS = 20

# The two prompts this module drafts under. Named constants rather than the literals they
# used to be at the call sites, so the ledger can record which one asked for a draft: `op`
# says "tool_turn" for both, and a generate and a refine are not the same call to anyone
# reading the file later. `check_prompts_versioned.py` knows both names.
GENERATE_PROMPT_VERSION = "generate_template_v4"
REFINE_PROMPT_VERSION = "refine_template_v5"

# What the model may draft. Free text is excluded, always: a drafted survey is conducted
# by an interviewer that has to judge whether a reply answered the question, and an open
# box is where that judgement is hardest and where invented answers cost the most. Closed
# questions with a write-in carry the part the option list could not anticipate.
#
# A rule about drafting, not about surveys. An author who wants a text question adds one
# on the question card and nothing objects: this constrains what the model writes on your
# behalf, not what you may ask for yourself.
FREE_TEXT = (AnswerType.short_text, AnswerType.long_text)
DRAFTABLE = [t for t in AnswerType if t not in FREE_TEXT]


class _DraftToolInput(TemplateCreate):
    """The generation tool's input — the template plus a short note. The note is a schema
    field, not free prose, because a forced tool call suppresses spoken text: asking for a
    sentence "alongside" the call reliably yields nothing, so it has to be part of the
    structured output. Validated back as a plain ``TemplateCreate`` (the note is ignored)."""

    note: str = Field(
        default="",
        description="One or two sentences for the author: your main design choices, "
        "or what you changed.",
    )


_TOOL_NAME = "draft_survey_template"
_TOOL_DESCRIPTION = "Return a complete survey template as structured data, plus a short note."


def _tool(expected_count: int | None = None) -> dict[str, Any]:
    """The draft tool, with the questions array pinned when the brief names a count.

    A live run returned 11 questions against a brief that asked for exactly 10, twice
    (defect O2). The bound in the schema is what a constrained decoder can hold the
    model to; ``_validation_error`` is what actually holds the line, because not every
    provider enforces minItems/maxItems.
    """
    schema = _DraftToolInput.model_json_schema()
    if expected_count is not None:
        schema["properties"]["questions"]["minItems"] = expected_count
        schema["properties"]["questions"]["maxItems"] = expected_count
    return {"name": _TOOL_NAME, "description": _TOOL_DESCRIPTION, "input_schema": schema}


# Word numbers a brief plausibly writes a count in. Stops at twenty, which is also
# MAX_GENERATED_QUESTIONS: past that, people write digits.
_WORD_NUMBERS: dict[str, int] = {
    w: n
    for n, w in enumerate(
        "one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
        "fifteen sixteen seventeen eighteen nineteen twenty".split(),
        start=1,
    )
}

# "about 10 questions" is not a promise to hold the model to. Softeners before the
# number, or hedges after it, make the count advisory and the bound is skipped.
# "first"/"next" and friends are here because "the first 3 questions should be about
# safety" scopes three questions, it does not order a three-question survey.
_SOFTENERS = (
    r"(?:about|around|roughly|approximately|approx\.?|some|say|maybe|"
    r"up to|at most|at least|no more than|fewer than|less than|more than|over|under|"
    r"first|last|final|initial|next|another)"
)
# "2 questions per shift" and "2 questions each" size a section, not the survey.
_HEDGES_AFTER = r"^\s*(?:or so|or more|or fewer|or less|max\b|maximum|tops|ish\b|per\b|each\b)"
# A number that is the far end of a range ("8-10 questions", "between 8 and 10
# questions") is not an exact ask either.
_RANGE_BEFORE = r"\d\s*(?:-|–|to|and|or)\s*$"

_COUNT = re.compile(
    rf"(?<![\w-])(\d{{1,2}}|{'|'.join(_WORD_NUMBERS)})[\s-]+questions?\b",
    re.IGNORECASE,
)


def _requested_question_count(brief: str) -> int | None:
    """The question count the brief pins, or None when it names none or is not exact.

    Conservative on purpose, in both directions. A missed match leaves today's
    behaviour, which is the model reading the brief; a false match rejects drafts the
    author never asked to bound. So a softened count ("about ten questions"), a range,
    or two different counts in one brief ("10 questions on safety and 2 on kit") all
    return None, and only an unambiguous single count becomes a bound.
    """
    counts: set[int] = set()
    for match in _COUNT.finditer(brief):
        token = match.group(1).lower()
        count = int(token) if token.isdigit() else _WORD_NUMBERS[token]
        if count == 0:
            continue
        before = brief[max(0, match.start() - 24) : match.start()].lower()
        after = brief[match.end() : match.end() + 12].lower()
        if re.search(rf"{_SOFTENERS}\s*$", before) or re.search(_RANGE_BEFORE, before):
            continue
        if re.search(_HEDGES_AFTER, after):
            continue
        counts.add(count)
    if len(counts) != 1:
        return None
    return counts.pop()


class GenerationService:
    def __init__(self, session: AsyncSession, llm: LLMProtocol | None = None) -> None:
        self.session = session
        self.llm: LLMProtocol = llm or get_llm()
        self.templates = TemplateService(session)

    async def generate_draft(
        self,
        prompt: str,
        author: User,
        audience: SurveyAudience = SurveyAudience.everyone,
        audience_user_id: UUID | None = None,
    ) -> tuple[SurveyTemplate, str]:
        """Draft a new survey from a description. Returns the saved draft and the model's
        short note on what it built.

        The audience is the author's, not the model's. `_DraftToolInput` extends
        `TemplateCreate`, so `audience` sits in the tool schema and the model can fill it
        in, yet no prompt file mentions the field or what the values mean. That leaves who
        may answer a survey decided by a model that was told nothing about the question,
        which is the same failure the `TemplateUpdate` docstring records. Overriding after
        the draft returns keeps one answer to "who is this for", and it is the author's."""
        requested = _requested_question_count(prompt)
        if requested is not None and requested > MAX_GENERATED_QUESTIONS:
            # Refused before any model call: with the bound in the schema and the cap in
            # the validator, a brief past the cap could only ever fail after two paid
            # calls, with an error about the model rather than the brief.
            raise ValidationError(
                f"The brief asks for {requested} questions and drafting supports at most "
                f"{MAX_GENERATED_QUESTIONS}. Ask for fewer, or add the rest by hand in "
                "the builder."
            )
        system = load_prompt(GENERATE_PROMPT_VERSION)
        with ledger.using_prompt(GENERATE_PROMPT_VERSION):
            template_in, note = await self._draft(
                system,
                [{"role": "user", "content": f"{prompt}\n\n{_policy()}"}],
                previous_error=None,
                expected_count=requested,
            )
        drafted = _without_catch_alls(template_in).model_copy(
            update={"audience": audience, "audience_user_id": audience_user_id}
        )
        template = await self.templates.create_draft(drafted, author)
        return template, note

    async def refine_draft(
        self, template_id: UUID, instruction: str, author: User
    ) -> tuple[SurveyTemplate, str]:
        """Apply a follow-up instruction to an existing draft and return it revised, plus
        the model's note on what changed. The whole survey is re-drafted and re-validated,
        so a follow-up can never leave the draft in an invalid shape."""
        current = await self.templates.get_draft(template_id, author)
        system = load_prompt(REFINE_PROMPT_VERSION)
        message = (
            f"{_describe(current)}\n{_policy()}\n\nRequested change: {instruction}\n\n"
            "Return the complete revised survey."
        )
        with ledger.using_prompt(REFINE_PROMPT_VERSION):
            template_in, note = await self._draft(
                system,
                [{"role": "user", "content": message}],
                previous_error=None,
                # The author's own text questions, which a refine returns and must not be
                # rejected for returning.
                kept=frozenset(q.text for q in current.questions if q.answer_type in FREE_TEXT),
            )
        # The settings the brief never shows, restored from the stored draft rather than
        # trusted back. The tool schema carries them because it extends TemplateCreate,
        # so the model returns a guess (usually the schema defaults), and update_draft
        # replaces every column it names: left alone, a refine deleted the setting and
        # re-aimed the survey at whoever the guess said. They are the author's decisions,
        # exactly as generate_draft already rules for `audience`, and restoring them also
        # keeps a refine of a published survey clear of update_draft's audience guard,
        # which a wrong guess used to trip as a 409.
        revised = _without_catch_alls(template_in).model_copy(
            update={
                "audience": current.audience,
                "audience_user_id": current.audience_user_id,
                "setting": current.setting,
            }
        )
        updated = await self.templates.update_draft(template_id, _to_update(revised), author)
        return updated, note

    async def _draft(
        self,
        system: str,
        messages: list[dict[str, str]],
        previous_error: str | None,
        kept: frozenset[str] = frozenset(),
        expected_count: int | None = None,
    ) -> tuple[TemplateCreate, str]:
        turn_messages = (
            messages
            if previous_error is None
            else [
                *messages,
                {
                    "role": "user",
                    "content": f"Your previous attempt was rejected: {previous_error}\n"
                    "Return a corrected survey.",
                },
            ]
        )
        turn = await self.llm.tool_turn(
            system=system, messages=turn_messages, tools=[_tool(expected_count)], max_tokens=4096
        )
        raw = _decode_stringified_fields(turn.tool_input)
        # Prefer the schema's note field; fall back to any spoken text a model does emit.
        note = str(raw.get("note") or turn.text or "").strip()
        error = _validation_error(raw, kept, expected_count)
        if error is None:
            return TemplateCreate.model_validate(raw), note
        if previous_error is None:
            logger.warning("generated template rejected, retrying: raw=%r error=%s", raw, error)
            return await self._draft(
                system, messages, previous_error=error, kept=kept, expected_count=expected_count
            )
        # The rejection reason describes the fault but not the draft, so keep the raw
        # payload before failing (ARCHITECTURE.md 3.3).
        logger.error("template generation failed after one retry: raw=%r error=%s", raw, error)
        raise LLMError(f"Model returned an invalid template after one retry: {error}")


def _decode_stringified_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Undo one JSON-encoding of the structured fields, a common small-model slip.

    Weaker backup models frequently emit ``"questions": "[{...}]"`` — the right list,
    wrapped in a string. That is a serialization artifact, not a content problem, so
    decode it (and the same slip on each question's ``options``) before validation.
    Anything that does not parse to the expected container type is left untouched for
    the validator to reject, so real junk still fails loudly.
    """

    def repaired_question(question: Any) -> Any:
        if not isinstance(question, dict):
            question = decode_stringified(question, dict)
        if not isinstance(question, dict) or "options" not in question:
            return question  # leave absent keys absent: the schema defaults
        # Options only mean anything on the select types. Small models decorate rating
        # questions with options like [1, 2, 3, 4, 5], which the schema (list[str])
        # rightly refuses — dropping them is lossless, so do that instead of burning
        # the retry.
        if question.get("answer_type") not in ("single_select", "multi_select"):
            return {**question, "options": []}
        return {**question, "options": decode_stringified(question["options"], list)}

    repaired = dict(raw)
    if "questions" in repaired:
        repaired["questions"] = decode_stringified(repaired["questions"], list)
    if isinstance(repaired.get("questions"), list):
        repaired["questions"] = [repaired_question(q) for q in repaired["questions"]]
    return repaired


_CATCH_ALL_OPTIONS = frozenset(
    {
        "other",
        "other (please specify)",
        "none of the above",
        "not applicable",
        "n/a",
        "prefer not to say",
    }
)


def _without_catch_alls(template_in: TemplateCreate) -> TemplateCreate:
    """Turn a literal "Other" option into the ``allow_other`` write-in it should have been.

    The prompt asks for this, but a catch-all silently discards the one part of an answer
    the author could not anticipate, so it is worth guaranteeing rather than hoping for.
    A live run recorded ``{'option': 'Other'}`` and lost the respondent's actual team.
    """
    for question in template_in.questions:
        kept = [o for o in question.options if o.strip().lower() not in _CATCH_ALL_OPTIONS]
        if len(kept) == len(question.options):
            continue
        if not kept:
            # Every option was a catch-all. Stripping them would leave a select with no
            # options — which the schema refuses on the way in, but assignment here runs
            # after validation and so is never re-checked. The invalid draft would reach
            # the builder, and the engine would offer the question with no enum at all,
            # quietly turning multiple choice into free text. Leave it for the author.
            logger.info("kept catch-all options, nothing else to offer: %r", question.text)
            continue
        logger.info("replaced catch-all options with allow_other: %r", question.text)
        question.options = kept
        question.allow_other = True
    return template_in


def _to_update(template_in: TemplateCreate) -> TemplateUpdate:
    """Create and Update share a shape, but the service takes the Update type for edits."""
    return TemplateUpdate.model_validate(template_in.model_dump())


def _describe(template: SurveyTemplate) -> str:
    """Render the current draft as plain text for the model to revise.

    Everything the model is trusted to revise has to appear here. A refine returns the
    COMPLETE survey and ``update_draft`` replaces every row with it, so any attribute
    this omits is not "left alone", it is deleted. ``show_when`` was omitted, and so
    every conditional-visibility rule in a draft was silently dropped the first time
    the author asked for any unrelated change.

    The deliberate exceptions are ``audience``, ``audience_user_id`` and ``setting``,
    which ``refine_draft`` restores from the stored draft after the model answers.
    They lost data the same way ``show_when`` did, but the fix is the opposite one:
    they are the author's decisions rather than prose to revise, so showing them to
    the model would only invite it to change them.
    """
    lines = [
        f"Title: {template.title}",
        f"Description: {template.description or '(none)'}",
        "Questions:",
    ]
    for i, question in enumerate(sorted(template.questions, key=lambda q: q.position), start=1):
        parts = [f"{i}. [{question.answer_type.value}] {question.text}"]
        if question.options:
            parts.append(f"options: {', '.join(question.options)}")
        if question.allow_other:
            parts.append("allows a write-in")
        if not question.required:
            parts.append("optional")
        if question.follow_up_policy is not FollowUpPolicy.never:
            parts.append(f"follow-ups: {question.follow_up_policy.value}")
        if question.show_when:
            # Numbered as the listing numbers them, from 1. show_when stores the
            # 0-based position, and handing the model a number that does not match
            # what it is reading invites it to repoint the condition at the wrong
            # question, which is a quieter fault than losing it.
            condition = question.show_when
            parts.append(
                f"shown only if Q{int(condition['question']) + 1} "
                f"{condition['op']} \"{condition['value']}\""
            )
        lines.append("  " + " · ".join(parts))
    return "\n".join(lines)


def _policy() -> str:
    """The drafting rule, stated to the model before it answers.

    Told up front it usually complies, which saves the retry for a real mistake; the
    check in ``_free_text_drafted`` is what actually holds the line.
    """
    permitted = ", ".join(t.value for t in DRAFTABLE)
    return (
        f"Answer types allowed: ONLY {permitted}. Free text is not available in this "
        "survey. A question that wants an open answer is asked as a select with real "
        "options and a write-in, so what the list does not anticipate is still captured; "
        "it is not converted into a rating, which produces a question nobody can answer."
    )


def _free_text_drafted(template_in: TemplateCreate, kept: frozenset[str]) -> str | None:
    """Why this draft introduces free text, or None.

    Introduces, not contains. An author may add a text question by hand and nothing
    objects to that: the rule constrains what the model writes on their behalf. A refine
    returns the COMPLETE survey, so a blanket check would reject the survey for carrying
    the author's own question back unchanged, and the author would find their question
    deleted or their refine failing. ``kept`` is the free-text a question already had, by
    text, so returning it is fine and inventing a new one is not.
    """
    offenders = [
        f"question {i + 1} is {q.answer_type.value}"
        for i, q in enumerate(template_in.questions)
        if q.answer_type in FREE_TEXT and q.text not in kept
    ]
    if not offenders:
        return None
    return (
        f"{'; '.join(offenders)}. Free text is not available: ask it as a select with "
        "real options and a write-in, or leave the question out. Any short_text or "
        "long_text already in the survey was written by the author; keep it as it is."
    )


def _validation_error(
    raw: dict[str, Any], kept: frozenset[str], expected_count: int | None = None
) -> str | None:
    try:
        template_in = TemplateCreate.model_validate(raw)
    except PydanticValidationError as exc:
        return str(exc)
    if not template_in.questions:
        # A weaker model (e.g. a free auto-routed one) can return a technically valid,
        # empty tool call — a title with no questions. Schema-valid, useless; burn the
        # retry rather than persist a survey with nothing to answer.
        return "no questions"
    if len(template_in.questions) > MAX_GENERATED_QUESTIONS:
        return f"too many questions (max {MAX_GENERATED_QUESTIONS})"
    if expected_count is not None and len(template_in.questions) != expected_count:
        # The half of defect O2 this module can hold: the schema bound above steers, and
        # this is what refuses a draft that ignored the brief's count anyway.
        return (
            f"the brief asks for exactly {expected_count} questions and this draft has "
            f"{len(template_in.questions)}"
        )
    # Last, so the rejection an author never sees is about content rather than shape.
    return _free_text_drafted(template_in, kept)
