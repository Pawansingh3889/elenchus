"""Natural-language template generation.

The author describes a survey; the LLM drafts it through a schema-constrained tool
call. The engine validates the result and, on failure, retries once with the error
before failing loudly (ARCHITECTURE.md: validate then act). A valid draft is persisted
so it lands in the same builder a hand-built one would.
"""

import logging
from typing import Any

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient, LLMError, LLMProtocol
from app.llm.prompts import load_prompt
from app.templates.models import SurveyTemplate
from app.templates.schemas import TemplateCreate
from app.templates.service import TemplateService
from app.users.models import User

logger = logging.getLogger("app.templates.generation")

MAX_GENERATED_QUESTIONS = 20

_TOOL_NAME = "draft_survey_template"
_TOOL_DESCRIPTION = "Return a complete survey template as structured data."
_TOOL_SCHEMA: dict[str, Any] = TemplateCreate.model_json_schema()


class GenerationService:
    def __init__(self, session: AsyncSession, llm: LLMProtocol | None = None) -> None:
        self.session = session
        self.llm: LLMProtocol = llm or LLMClient()
        self.templates = TemplateService(session)

    async def generate_draft(self, prompt: str, author: User) -> SurveyTemplate:
        system = load_prompt("generate_template_v1")
        template_in = await self._draft(system, prompt, previous_error=None)
        return await self.templates.create_draft(_without_catch_alls(template_in), author)

    async def _draft(self, system: str, prompt: str, previous_error: str | None) -> TemplateCreate:
        user = (
            prompt
            if previous_error is None
            else f"{prompt}\n\nYour previous attempt was rejected: {previous_error}\n"
            "Return a corrected template."
        )
        raw = await self.llm.tool_call(
            system=system,
            prompt=user,
            tool_name=_TOOL_NAME,
            tool_description=_TOOL_DESCRIPTION,
            input_schema=_TOOL_SCHEMA,
        )
        error = _validation_error(raw)
        if error is None:
            return TemplateCreate.model_validate(raw)
        if previous_error is None:
            logger.warning("generated template rejected, retrying: raw=%r error=%s", raw, error)
            return await self._draft(system, prompt, previous_error=error)
        # The rejection reason describes the fault but not the draft, so keep the raw
        # payload before failing (ARCHITECTURE.md 3.3).
        logger.error("template generation failed after one retry: raw=%r error=%s", raw, error)
        raise LLMError(f"Model returned an invalid template after one retry: {error}")


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
        if len(kept) != len(question.options):
            logger.info("replaced catch-all options with allow_other: %r", question.text)
            question.options = kept
            question.allow_other = True
    return template_in


def _validation_error(raw: dict[str, Any]) -> str | None:
    try:
        template_in = TemplateCreate.model_validate(raw)
    except PydanticValidationError as exc:
        return str(exc)
    if len(template_in.questions) > MAX_GENERATED_QUESTIONS:
        return f"too many questions (max {MAX_GENERATED_QUESTIONS})"
    return None
