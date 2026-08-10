"""Template business logic: the draft lifecycle and publishing.

Publishing freezes the current draft into a new immutable version (n+1). The draft
keeps evolving afterwards; respondents only ever see published versions.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin_by_config, may_answer, may_list
from app.config import get_settings
from app.errors import ConflictError, NotFoundError
from app.templates.enums import TemplateStatus
from app.templates.estimate import estimated_minutes
from app.templates.models import SurveyQuestion, SurveyTemplate, SurveyTemplateVersion
from app.templates.repository import TemplateRepository
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.templates.snapshot import questions_of
from app.users.models import User

logger = logging.getLogger("app.templates")


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TemplateRepository(session)

    async def create_draft(self, data: TemplateCreate, author: User) -> SurveyTemplate:
        template = SurveyTemplate(
            title=data.title,
            description=data.description,
            audience=data.audience,
            setting=data.setting,
            created_by=author.id,
        )
        template.questions = [_to_question(q, i) for i, q in enumerate(data.questions)]
        self.repo.add(template)
        await self.session.commit()
        return await self._get_or_404(template.id, author)

    async def get_draft(self, template_id: UUID, author: User) -> SurveyTemplate:
        return await self._get_or_404(template_id, author)

    async def list_drafts(
        self, status: TemplateStatus | None, author: User
    ) -> list[tuple[SurveyTemplate, int]]:
        """An author's own workspace. Already scoped to them in the query; filtered again
        here so the one rule decides, rather than the query agreeing with it by luck."""
        admin = is_admin_by_config(author)
        return [
            row
            for row in await self.repo.list_summaries(status, created_by=author.id)
            if may_list(author, row[0].audience, row[0].created_by, admin)
        ]

    async def list_published(self, user: User) -> list[tuple[SurveyTemplate, int, int, bool]]:
        """Every published survey this user may actually start, with the count and time
        estimate they will face, read from the published version rather than the evolving
        draft.

        Filtered by may_answer rather than may_list, because this list is an invitation:
        every row on it is something the reader is about to be offered a Start button for.
        Before audiences existed this method took no user at all and returned everything
        published, which is precisely the bug audiences were introduced to fix."""
        admin = is_admin_by_config(user)
        rows = await self.repo.list_published_latest()
        # One query for the lot, not one per row. A survey this person has finished still
        # belongs on the list: hiding it looks like the survey disappeared, and the point
        # is to tell them they have already done it.
        answered = await self.repo.completed_by(user.id)
        return [
            (template, len(questions), estimated_minutes(questions), template.id in answered)
            for template, definition in rows
            if may_answer(user, template.audience, template.created_by, admin)
            for questions in [questions_of(definition)]
        ]

    async def update_draft(
        self, template_id: UUID, data: TemplateUpdate, author: User
    ) -> SurveyTemplate:
        template = await self._get_or_404(template_id, author)
        # Frozen once published. The audience is part of what was published, like the
        # questions: a survey that starts collecting Finance answers and is then pointed
        # at HR ends up with one set of results drawn from two different populations, and
        # nothing in the data records that it moved.
        if data.audience is not template.audience and template.status is not TemplateStatus.draft:
            raise ConflictError(
                "A published survey's audience cannot change. Publish a new survey instead."
            )
        template.title = data.title
        template.description = data.description
        template.audience = data.audience
        template.setting = data.setting
        # Full replace of questions covers add / edit / reorder / delete. Delete the
        # old rows first so the (template_id, position) unique constraint can't clash.
        template.questions.clear()
        await self.session.flush()
        for i, q in enumerate(data.questions):
            template.questions.append(_to_question(q, i))
        await self.session.commit()
        return await self._get_or_404(template_id, author)

    async def delete_draft(self, template_id: UUID, author: User) -> None:
        template = await self._get_or_404(template_id, author)
        await self.repo.delete(template)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Cannot delete a template that has published versions.") from exc

    async def publish(self, template_id: UUID, author: User) -> SurveyTemplateVersion:
        template = await self._get_or_404(template_id, author)
        if not template.questions:
            raise ConflictError("Cannot publish a template with no questions.")
        version = SurveyTemplateVersion(
            template_id=template.id,
            version=await self.repo.next_version(template_id),
            definition=_snapshot(template),
            published_by=author.id,
        )
        self.repo.add_version(version)
        template.status = TemplateStatus.published
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def close(self, template_id: UUID, author: User) -> SurveyTemplate:
        """Stop this survey taking new answers. Runs already in progress are untouched.

        Only a published survey can be closed. Closing a draft would be closing something
        that never opened, and closing a closed one twice would move closed_at, which is
        the date an author will quote when they report the numbers.

        Nothing here reaches into the runs. The engine refuses to start a new one against
        a closed survey, and a conversation already under way finishes on its own terms:
        stopping mid-question would lose answers a respondent has already given, and for a
        chat that is a worse bargain than a final count that settles a few minutes late.
        """
        template = await self._get_or_404(template_id, author)
        if template.status is not TemplateStatus.published:
            raise ConflictError(
                f"Only a published survey can be closed; this one is {template.status.value}."
            )
        template.status = TemplateStatus.closed
        template.closed_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def _get_or_404(self, template_id: UUID, author: User) -> SurveyTemplate:
        template = await self.repo.get(template_id)
        if template is None:
            raise NotFoundError("Template not found.")
        # Someone else's template reads as absent rather than forbidden, so the API
        # can't be used to enumerate which ids exist. The rule itself lives in
        # app/access: this used to compare created_by here, which was the same rule
        # written in a second place and free to drift from the one the engine uses.
        decision = may_list(
            author, template.audience, template.created_by, is_admin_by_config(author)
        )
        if not decision:
            logger.info(
                "template hidden: template=%s user=%s reason=%s",
                template_id,
                author.id,
                decision.reason,
            )
            raise NotFoundError("Template not found.")
        return template


def _to_question(q: QuestionInput, position: int) -> SurveyQuestion:
    return SurveyQuestion(
        position=position,
        text=q.text,
        answer_type=q.answer_type,
        options=q.options,
        allow_other=q.allow_other,
        required=q.required,
        follow_up_policy=q.follow_up_policy,
        show_when=q.show_when.model_dump(mode="json") if q.show_when else None,
    )


def _snapshot(template: SurveyTemplate) -> dict[str, Any]:
    return {
        "title": template.title,
        "description": template.description,
        # Frozen with the questions: a run is conducted against the setting the
        # author published, not whatever the draft says by the time it is answered.
        #
        # Falls back to the deployment's own, because the plant does not change between
        # surveys and asking every author to retype it is how it ends up wrong on half
        # of them. Frozen here rather than read at conduct time for the same reason the
        # questions are: editing the deployment's description must not change how answers
        # already being given are read. A survey that carries its own keeps it.
        "setting": template.setting or get_settings().survey_setting or None,
        "questions": [
            {
                "id": str(q.id),
                "position": q.position,
                "text": q.text,
                "answer_type": q.answer_type.value,
                "options": q.options,
                "allow_other": q.allow_other,
                "required": q.required,
                "follow_up_policy": q.follow_up_policy.value,
                "show_when": q.show_when,
            }
            for q in sorted(template.questions, key=lambda x: x.position)
        ],
    }
