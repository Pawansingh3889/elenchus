"""Issue scoped passes, admit guests and manually approve customer access."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import oauth
from app.config import get_settings
from app.db.session import SessionFactory, engine
from app.demo.models import PLATFORM_WORKSPACE_ID, DemoAccess, DemoRegistry
from app.demo.policy import active, check_access
from app.demo.repository import DemoRepository
from app.demo.schemas import (
    AccessRead,
    ActivateCustomer,
    Entered,
    IssuePass,
    OperatorRead,
    OperatorWorkspace,
    PassRead,
    ShareRead,
    SurveyEntryRead,
)
from app.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.templates.enums import SurveyAudience, TemplateStatus
from app.templates.repository import TemplateRepository
from app.templates.service import TemplateService
from app.users.models import AccountChange, User, WorkspaceRole
from app.users.repository import UserRepository
from app.users.schemas import UserRead
from app.users.service import UserService
from app.workspaces.models import Workspace, WorkspaceAccessChange
from app.workspaces.repository import WorkspaceRepository

DISCLOSURE = (
    "We do not ask for your name or email. The survey author can read your answers and "
    "conversation under a participant label. Your words may identify you, so avoid personal "
    "details. Responses are retained for the workspace's stated retention period."
)


def require_operator(user: User) -> None:
    if user.email.casefold() not in get_settings().admin_email_set:
        raise ForbiddenError("Only a configured KapkotiSolution operator can manage demo access.")


def enabled() -> None:
    if not get_settings().demo_enabled:
        raise ForbiddenError("Private demo access is not enabled on this deployment yet.")


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class DemoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DemoRepository(session)

    async def issue(self, data: IssuePass, operator: User) -> PassRead:
        require_operator(operator)
        enabled()
        oauth.sign("configuration-check", 1)
        workspace_id, owner_id = uuid4(), uuid4()
        token = f"{workspace_id}.{secrets.token_urlsafe(32)}"
        expires = datetime.now(UTC) + timedelta(days=14)
        # Both scoped sessions share one transaction: no orphaned account or directory row.
        try:
            async with engine.begin() as connection:
                async with SessionFactory(
                    bind=connection, info={"workspace_id": workspace_id}
                ) as tenant:
                    repo = DemoRepository(tenant)
                    repo.add(Workspace(id=workspace_id, name=data.company))
                    await tenant.flush()
                    owner = User(
                        id=owner_id,
                        email=data.email.casefold(),
                        display_name=data.name,
                        workspace_role=WorkspaceRole.owner,
                    )
                    UserRepository(tenant).add(owner)
                    await tenant.flush()
                    repo.add(
                        DemoAccess(owner_id=owner_id, pass_digest=digest(token), expires_at=expires)
                    )
                    UserRepository(tenant).add_change(
                        AccountChange(
                            user_id=owner_id,
                            change={"kind": "demo_created", "operator": operator.email},
                        )
                    )
                    await tenant.flush()
                async with SessionFactory(
                    bind=connection, info={"workspace_id": PLATFORM_WORKSPACE_ID}
                ) as platform:
                    repo = DemoRepository(platform)
                    await repo.ensure_platform()
                    repo.add(
                        DemoRegistry(
                            id=workspace_id,
                            company=data.company,
                            contact_email=data.email.casefold(),
                            issued_by=operator.email,
                        )
                    )
                    await platform.flush()
        except IntegrityError as exc:
            raise ConflictError(
                "That email already has an account. Use its existing workspace."
            ) from exc
        return PassRead(workspace_id=workspace_id, pass_token=token, expires_at=expires)

    async def enter(self, token: str) -> Entered:
        enabled()
        try:
            workspace_id = UUID(token.split(".", 1)[0])
        except ValueError as exc:
            raise UnauthorizedError("This demo pass is invalid or no longer available.") from exc
        await WorkspaceRepository(self.session).bind(workspace_id)
        access = await self.repo.access(lock=True)
        if access is None or not secrets.compare_digest(access.pass_digest, digest(token)):
            raise UnauthorizedError("This demo pass is invalid or no longer available.")
        if access.revoked_at is not None:
            raise ForbiddenError(
                "This workspace's access has been revoked. Contact KapkotiSolution."
            )
        owner = await UserRepository(self.session).get(access.owner_id)
        if owner is None:
            raise UnauthorizedError("This demo account no longer exists.")
        if access.activated_at is None:
            access.activated_at = datetime.now(UTC)
        await UserService(self.session).record_sign_in(owner, "demo_pass", created=False)
        return Entered(user=UserRead.of(owner))

    async def state(self) -> AccessRead:
        workspace = await WorkspaceRepository(self.session).get_workspace()
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        access = await self.repo.access()
        if access is None:
            return AccessRead(
                workspace_id=workspace.id,
                company=workspace.name,
                mode="standard",
                active=True,
                expires_at=None,
                surveys_created=0,
                survey_limit=None,
                question_limit=None,
                session_limit_per_survey=None,
                product=None,
                monthly_response_allowance=None,
                sessions_started_this_month=0,
            )
        is_active = True
        try:
            active(access)
        except ForbiddenError:
            is_active = False
        customer = access.customer_product is not None
        usage = await self.repo.usage_count(datetime.now(UTC).date().replace(day=1))
        return AccessRead(
            workspace_id=workspace.id,
            company=workspace.name,
            mode="customer" if customer else "demo",
            active=is_active,
            expires_at=access.customer_until if customer else access.expires_at,
            surveys_created=access.surveys_created,
            survey_limit=None if customer else 3,
            question_limit=None if customer else 10,
            session_limit_per_survey=None if customer else 20,
            product=access.customer_product,
            monthly_response_allowance=access.monthly_response_allowance,
            sessions_started_this_month=usage,
        )

    async def share(self, template_id: UUID, author: User) -> ShareRead:
        access = await check_access(self.session)
        if access is None:
            raise ForbiddenError("Survey links require a demo or activated customer workspace.")
        template = await TemplateService(self.session).get_draft(template_id, author)
        if (
            template.status is not TemplateStatus.published
            or template.audience is not SurveyAudience.signed_in
        ):
            raise ConflictError("Publish this survey to the signed-in audience before sharing.")
        expires = (
            min(
                datetime.now(UTC) + timedelta(days=14),
                access.customer_until or datetime.max.replace(tzinfo=UTC),
            )
            if access.customer_product
            else access.expires_at
        )
        token = oauth.sign(
            f"survey:{author.workspace_id}:{template_id}",
            max(1, int((expires - datetime.now(UTC)).total_seconds())),
        )
        return ShareRead(token=token, expires_at=expires)

    async def _shared_template(self, token: str) -> tuple[UUID, SurveyEntryRead]:
        enabled()
        payload = oauth.unsign(token)
        try:
            kind, workspace, template = (payload or "").split(":")
            if kind != "survey":
                raise ValueError
            workspace_id, template_id = UUID(workspace), UUID(template)
        except ValueError as exc:
            raise UnauthorizedError("This survey link is invalid or has expired.") from exc
        await WorkspaceRepository(self.session).bind(workspace_id)
        access = await check_access(self.session)
        if access is None:
            raise NotFoundError("This survey link is no longer available.")
        row = await TemplateRepository(self.session).get(template_id)
        if (
            row is None
            or row.status is not TemplateStatus.published
            or row.audience is not SurveyAudience.signed_in
        ):
            raise NotFoundError("This survey is no longer accepting new responses.")
        workspace_row = await WorkspaceRepository(self.session).get_workspace()
        assert workspace_row is not None
        disclosure = (
            DISCLOSURE + " This workspace currently retains responses for "
            f"{workspace_row.response_retention_days} days."
        )
        return template_id, SurveyEntryRead(
            title=row.title,
            description=row.description,
            questions=len(row.questions),
            remaining_sessions=(
                None if access.customer_product else max(0, 20 - row.sessions_started)
            ),
            disclosure=disclosure,
        )

    async def preview(self, token: str) -> SurveyEntryRead:
        _, preview = await self._shared_template(token)
        return preview

    async def enter_survey(self, token: str, cookie: str | None) -> Entered:
        from app.conduct.engine import ConductEngine

        template_id, preview = await self._shared_template(token)
        users = UserRepository(self.session)
        existing: User | None = None
        if cookie:
            signed = oauth.unsign(cookie)
            try:
                existing = await users.get(UUID(signed)) if signed else None
            except ValueError:
                existing = None
        if existing is not None and existing.demo_survey_id == template_id:
            return Entered(user=UserRead.of(existing), template_id=template_id)
        if preview.remaining_sessions == 0:
            raise ConflictError("This survey has reached its demo respondent allowance.")
        guest_id = uuid4()
        guest = User(
            id=guest_id,
            email=f"{guest_id}@participant.invalid",
            display_name="Participant",
            workspace_role=WorkspaceRole.respondent,
            demo_survey_id=template_id,
        )
        users.add(guest)
        await self.session.flush()
        run = await ConductEngine(self.session).start_run(template_id, guest)
        return Entered(user=UserRead.of(guest), template_id=template_id, run_id=run.id)

    async def revoke(self, workspace_id: UUID, operator: User) -> None:
        require_operator(operator)
        async with SessionFactory(info={"workspace_id": PLATFORM_WORKSPACE_ID}) as platform:
            if not await DemoRepository(platform).registered(workspace_id):
                raise NotFoundError("This workspace is not in the demo directory.")
        async with SessionFactory(info={"workspace_id": workspace_id}) as tenant:
            access = await DemoRepository(tenant).access(lock=True)
            if access is None:
                raise NotFoundError("Demo workspace not found.")
            access.revoked_at = datetime.now(UTC)
            WorkspaceRepository(tenant).add_access_change(
                WorkspaceAccessChange(
                    email=operator.email,
                    access_kind="demo",
                    action="revoked",
                    details={"operator": operator.email},
                )
            )
            await tenant.commit()

    async def activate(
        self, workspace_id: UUID, data: ActivateCustomer, operator: User
    ) -> PassRead:
        require_operator(operator)
        if data.valid_until is not None and data.valid_until <= datetime.now(UTC):
            raise ConflictError("The verified subscription must currently be active.")
        async with SessionFactory(info={"workspace_id": PLATFORM_WORKSPACE_ID}) as platform:
            if not await DemoRepository(platform).registered(workspace_id):
                raise NotFoundError("This workspace is not in the demo directory.")
        async with SessionFactory(info={"workspace_id": workspace_id}) as tenant:
            access = await DemoRepository(tenant).access(lock=True)
            if access is None:
                raise NotFoundError("Demo workspace not found.")
            token = f"{workspace_id}.{secrets.token_urlsafe(32)}"
            access.customer_product = data.product.strip()
            access.customer_until = data.valid_until
            access.monthly_response_allowance = data.monthly_response_allowance
            access.approved_by = operator.email
            access.pass_digest = digest(token)
            access.revoked_at = None
            owner = await UserRepository(tenant).get(access.owner_id)
            assert owner is not None
            WorkspaceRepository(tenant).add_access_change(
                WorkspaceAccessChange(
                    email=owner.email,
                    access_kind="product",
                    action="activated",
                    details={**data.model_dump(mode="json"), "operator": operator.email},
                )
            )
            await tenant.commit()
            return PassRead(
                workspace_id=workspace_id, pass_token=token, expires_at=data.valid_until
            )

    async def operator_state(self, operator: User) -> OperatorRead:
        require_operator(operator)
        month = datetime.now(UTC).date().replace(day=1)
        async with SessionFactory(info={"workspace_id": PLATFORM_WORKSPACE_ID}) as platform:
            repo = DemoRepository(platform)
            registrations = await repo.registry()
            spend = await repo.spend_rows(month)
            charged = await repo.charged(month)
        workspaces = []
        for registered in registrations:
            async with SessionFactory(info={"workspace_id": registered.id}) as tenant:
                access = await DemoRepository(tenant).access()
                if access is None:
                    raise NotFoundError("A registered demo workspace is missing its access record.")
                workspaces.append(
                    OperatorWorkspace(
                        workspace_id=registered.id,
                        company=registered.company,
                        email=registered.contact_email,
                        issued_at=registered.issued_at,
                        activated_at=access.activated_at,
                        access=await DemoService(tenant).state(),
                    )
                )
        return OperatorRead(
            workspaces=workspaces,
            month=month.isoformat(),
            budget_usd=get_settings().demo_monthly_budget_usd,
            charged_or_reserved_usd=float(charged),
            known_spend_usd=float(
                sum(row.actual_usd for row in spend if row.actual_usd is not None)
            ),
            uncertain_attempts=sum(row.actual_usd is None for row in spend),
            attempts=len(spend),
            failed_attempts=sum(row.failed is True for row in spend),
        )
