"""Template routes. Thin: resolve the author, call one service method, shape output."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth.dependencies import get_current_user, require_author
from app.db.session import get_session
from app.templates.enums import TemplateStatus
from app.templates.generation import GenerationService
from app.templates.models import SurveyTemplate
from app.templates.schemas import (
    GenerateRequest,
    TemplateCreate,
    TemplateRead,
    TemplateSummary,
    TemplateUpdate,
    TemplateVersionRead,
)
from app.templates.service import TemplateService
from app.users.models import User

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


def _summary(template: SurveyTemplate, question_count: int) -> TemplateSummary:
    return TemplateSummary(
        id=template.id,
        title=template.title,
        description=template.description,
        status=template.status,
        updated_at=template.updated_at,
        question_count=question_count,
    )


@router.post("", response_model=TemplateRead, status_code=HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    template = await TemplateService(session).create_draft(data, author)
    return TemplateRead.model_validate(template)


@router.post("/generate", response_model=TemplateRead, status_code=HTTP_201_CREATED)
async def generate_template(
    data: GenerateRequest,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    template = await GenerationService(session).generate_draft(data.prompt, author)
    return TemplateRead.model_validate(template)


@router.get("", response_model=list[TemplateSummary])
async def list_templates(
    status: TemplateStatus | None = None,
    _: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> list[TemplateSummary]:
    rows = await TemplateService(session).list_drafts(status)
    return [_summary(t, n) for t, n in rows]


# Declared before /{template_id} so the literal path wins the match. Open to any
# signed-in user: a published survey is what a respondent is meant to be able to answer.
@router.get("/published", response_model=list[TemplateSummary])
async def list_published(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TemplateSummary]:
    rows = await TemplateService(session).list_drafts(TemplateStatus.published)
    return [_summary(t, n) for t, n in rows]


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: UUID,
    _: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    template = await TemplateService(session).get_draft(template_id)
    return TemplateRead.model_validate(template)


@router.put("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    template = await TemplateService(session).update_draft(template_id, data, author)
    return TemplateRead.model_validate(template)


@router.delete("/{template_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    _: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> None:
    await TemplateService(session).delete_draft(template_id)


@router.post(
    "/{template_id}/publish", response_model=TemplateVersionRead, status_code=HTTP_201_CREATED
)
async def publish_template(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateVersionRead:
    version = await TemplateService(session).publish(template_id, author)
    return TemplateVersionRead.model_validate(version)
