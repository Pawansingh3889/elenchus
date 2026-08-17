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
    GeneratedTemplate,
    GenerateRequest,
    RefineRequest,
    TemplateCreate,
    TemplateRead,
    TemplateSummary,
    TemplateUpdate,
)
from app.templates.service import TemplateService
from app.users.models import User

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


def _summary(
    template: SurveyTemplate,
    question_count: int,
    estimated_minutes: int | None = None,
    answered: bool = False,
) -> TemplateSummary:
    return TemplateSummary(
        id=template.id,
        title=template.title,
        description=template.description,
        status=template.status,
        updated_at=template.updated_at,
        closed_at=template.closed_at,
        audience=template.audience,
        question_count=question_count,
        estimated_minutes=estimated_minutes,
        answered=answered,
    )


@router.post("", response_model=TemplateRead, status_code=HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    template = await TemplateService(session).create_draft(data, author)
    return TemplateRead.model_validate(template)


@router.post("/generate", response_model=GeneratedTemplate, status_code=HTTP_201_CREATED)
async def generate_template(
    data: GenerateRequest,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> GeneratedTemplate:
    template, note = await GenerationService(session).generate_draft(
        data.prompt, author, data.audience, data.audience_user_id
    )
    return GeneratedTemplate(template=TemplateRead.model_validate(template), note=note)


@router.get("", response_model=list[TemplateSummary])
async def list_templates(
    status: TemplateStatus | None = None,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> list[TemplateSummary]:
    rows = await TemplateService(session).list_drafts(status, author)
    return [_summary(t, n) for t, n in rows]


# Declared before /{template_id} so the literal path wins the match. Open to any
# signed-in user: a published survey is what a respondent is meant to be able to answer.
@router.get("/published", response_model=list[TemplateSummary])
async def list_published(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TemplateSummary]:
    rows = await TemplateService(session).list_published(user)
    return [_summary(t, n, minutes, answered) for t, n, minutes, answered in rows]


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    template = await TemplateService(session).get_draft(template_id, author)
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
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> None:
    await TemplateService(session).delete_survey(template_id, author)


@router.post("/{template_id}/refine", response_model=GeneratedTemplate)
async def refine_template(
    template_id: UUID,
    data: RefineRequest,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> GeneratedTemplate:
    template, note = await GenerationService(session).refine_draft(
        template_id, data.instruction, author
    )
    return GeneratedTemplate(template=TemplateRead.model_validate(template), note=note)


@router.post("/{template_id}/publish", response_model=TemplateRead)
async def publish_template(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    """Open the survey for answers, and return it.

    200 rather than 201: publishing creates nothing now. It used to mint a frozen
    version row, which is what the 201 described.
    """
    template = await TemplateService(session).publish(template_id, author)
    return TemplateRead.model_validate(template)


@router.post("/{template_id}/close", response_model=TemplateRead)
async def close_template(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    """Stop the survey taking new answers. Conversations already under way finish."""
    template = await TemplateService(session).close(template_id, author)
    return TemplateRead.model_validate(template)
