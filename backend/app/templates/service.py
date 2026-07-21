"""Template business logic: the draft lifecycle and publishing.

Publishing freezes the current draft into a new immutable version (n+1). The draft
keeps evolving afterwards; respondents only ever see published versions.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, NotFoundError
from app.templates.enums import TemplateStatus
from app.templates.models import SurveyQuestion, SurveyTemplate, SurveyTemplateVersion
from app.templates.repository import TemplateRepository
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.users.models import User


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TemplateRepository(session)

    async def create_draft(self, data: TemplateCreate, author: User) -> SurveyTemplate:
        template = SurveyTemplate(
            title=data.title, description=data.description, created_by=author.id
        )
        template.questions = [_to_question(q, i) for i, q in enumerate(data.questions)]
        self.repo.add(template)
        await self.session.commit()
        return await self._get_or_404(template.id)

    async def get_draft(self, template_id: UUID) -> SurveyTemplate:
        return await self._get_or_404(template_id)

    async def list_drafts(self, status: TemplateStatus | None) -> list[tuple[SurveyTemplate, int]]:
        return await self.repo.list_summaries(status)

    async def update_draft(
        self, template_id: UUID, data: TemplateUpdate, author: User
    ) -> SurveyTemplate:
        template = await self._get_or_404(template_id)
        template.title = data.title
        template.description = data.description
        # Full replace of questions covers add / edit / reorder / delete. Delete the
        # old rows first so the (template_id, position) unique constraint can't clash.
        template.questions.clear()
        await self.session.flush()
        for i, q in enumerate(data.questions):
            template.questions.append(_to_question(q, i))
        await self.session.commit()
        return await self._get_or_404(template_id)

    async def delete_draft(self, template_id: UUID) -> None:
        template = await self._get_or_404(template_id)
        await self.repo.delete(template)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Cannot delete a template that has published versions.") from exc

    async def publish(self, template_id: UUID, author: User) -> SurveyTemplateVersion:
        template = await self._get_or_404(template_id)
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

    async def _get_or_404(self, template_id: UUID) -> SurveyTemplate:
        template = await self.repo.get(template_id)
        if template is None:
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
        allow_follow_ups=q.allow_follow_ups,
    )


def _snapshot(template: SurveyTemplate) -> dict[str, Any]:
    return {
        "title": template.title,
        "description": template.description,
        "questions": [
            {
                "id": str(q.id),
                "position": q.position,
                "text": q.text,
                "answer_type": q.answer_type.value,
                "options": q.options,
                "allow_other": q.allow_other,
                "required": q.required,
                "allow_follow_ups": q.allow_follow_ups,
            }
            for q in sorted(template.questions, key=lambda x: x.position)
        ],
    }
