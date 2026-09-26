"""Thin routes for private passes, public survey links and operator actions."""

from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import oauth
from app.auth.dependencies import get_current_user, require_author
from app.config import get_settings
from app.db.session import get_session
from app.demo.schemas import (
    AccessRead,
    ActivateCustomer,
    Entered,
    EnterPass,
    EnterSurvey,
    IssuePass,
    OperatorRead,
    PassRead,
    ShareRead,
    SurveyEntryRead,
)
from app.demo.service import DemoService
from app.users.models import User

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


class DemoOptions(BaseModel):
    enabled: bool


def _cookie(response: Response, user_id: UUID) -> None:
    response.set_cookie(
        oauth.SESSION_COOKIE,
        oauth.sign(str(user_id), oauth.SESSION_MAX_AGE),
        max_age=oauth.SESSION_MAX_AGE,
        httponly=True,
        path="/",
        secure=get_settings().app_env == "prod",
        samesite="none" if get_settings().app_env == "prod" else "lax",
    )
    response.headers["Cache-Control"] = "no-store"


@router.get("/options", response_model=DemoOptions)
async def options() -> DemoOptions:
    return DemoOptions(enabled=get_settings().demo_enabled)


@router.post("/enter", response_model=Entered)
async def enter(
    data: EnterPass, response: Response, session: AsyncSession = Depends(get_session)
) -> Entered:
    entered = await DemoService(session).enter(data.token)
    _cookie(response, entered.user.id)
    return entered


@router.get("/access", response_model=AccessRead)
async def access(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> AccessRead:
    return await DemoService(session).state()


@router.post("/surveys/{template_id}/share", response_model=ShareRead)
async def share(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> ShareRead:
    return await DemoService(session).share(template_id, author)


@router.post("/survey-preview", response_model=SurveyEntryRead)
async def preview(data: EnterPass, session: AsyncSession = Depends(get_session)) -> SurveyEntryRead:
    return await DemoService(session).preview(data.token)


@router.post("/survey-enter", response_model=Entered)
async def survey_enter(
    data: EnterSurvey,
    response: Response,
    elenchus_session: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> Entered:
    entered = await DemoService(session).enter_survey(data.token, elenchus_session)
    _cookie(response, entered.user.id)
    return entered


@router.get("/operator", response_model=OperatorRead)
async def operator(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> OperatorRead:
    return await DemoService(session).operator_state(user)


@router.post("/passes", response_model=PassRead, status_code=201)
async def issue(
    data: IssuePass,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PassRead:
    return await DemoService(session).issue(data, user)


@router.post("/workspaces/{workspace_id}/activate", response_model=PassRead)
async def activate(
    workspace_id: UUID,
    data: ActivateCustomer,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PassRead:
    return await DemoService(session).activate(workspace_id, data, user)


@router.post("/workspaces/{workspace_id}/revoke", status_code=204)
async def revoke(
    workspace_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    await DemoService(session).revoke(workspace_id, user)
