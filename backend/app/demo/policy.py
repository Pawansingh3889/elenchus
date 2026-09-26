"""Shared access checks, applied before work at every creation and conducting entry."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.demo.models import DemoAccess
from app.demo.repository import DemoRepository
from app.errors import AppError, ForbiddenError, NotFoundError, ValidationError
from app.users.models import User


class AllowanceError(AppError):
    status_code = 429
    code = "allowance_exhausted"


def active(access: DemoAccess) -> None:
    now = datetime.now(UTC)
    if access.revoked_at is not None:
        raise ForbiddenError("This workspace's access has been revoked. Contact KapkotiSolution.")
    until = access.customer_until if access.customer_product else access.expires_at
    if until is not None and until <= now:
        raise ForbiddenError(
            "This workspace's access has expired. Stored results remain available."
        )


async def check_access(session: AsyncSession) -> DemoAccess | None:
    access = await DemoRepository(session).access()
    if access is not None:
        active(access)
    return access


async def check_draft(
    session: AsyncSession, questions: int | None = None, *, create: bool = False
) -> None:
    access = await DemoRepository(session).access(lock=create)
    if access is None:
        return
    active(access)
    if not access.customer_product:
        if questions is not None and questions > 10:
            raise ValidationError("A demo survey can contain at most ten questions.")
        if create and access.surveys_created >= 3:
            raise AllowanceError(
                "All three demo surveys have been used. Existing results remain available."
            )


async def count_survey(session: AsyncSession) -> None:
    access = await DemoRepository(session).access(lock=True)
    if access is not None:
        access.surveys_created += 1


async def admit_session(session: AsyncSession, template_id: UUID, respondent: User) -> None:
    if respondent.demo_survey_id is not None and respondent.demo_survey_id != template_id:
        raise ForbiddenError("This participant session is limited to its invited survey.")
    repo = DemoRepository(session)
    access = await repo.access(lock=True)
    if access is None:
        return
    active(access)
    template = await repo.lock_template(template_id)
    if template is None:
        raise NotFoundError("Survey not found.")
    if not access.customer_product and template.sessions_started >= 20:
        raise AllowanceError("This demo survey has reached its twenty respondent sessions.")
    month = datetime.now(UTC).date().replace(day=1)
    usage = await repo.usage(month)
    if access.customer_product:
        if access.monthly_response_allowance is None:
            raise ForbiddenError("The customer response allowance has not been configured.")
        if usage.sessions_started >= access.monthly_response_allowance:
            raise AllowanceError("This workspace has used its monthly response-session allowance.")
    template.sessions_started += 1
    usage.sessions_started += 1
