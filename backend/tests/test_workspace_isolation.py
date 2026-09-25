"""Two companies with identical jobs and cache keys, tested under PostgreSQL RLS."""

from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import oauth
from app.auth.dependencies import (
    get_current_user,
    require_admin,
    require_author,
    require_results_reader,
)
from app.conduct.engine import ConductEngine
from app.config import get_settings
from app.db.base import Base
from app.embeddings.models import EmbeddingVector
from app.embeddings.repository import EmbeddingRepository
from app.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.evaluation.enums import LabelVerdict
from app.evaluation.repository import EvaluationRepository
from app.evaluation.runner import EVALUATION_AUTHOR, EVALUATION_RESPONDENT
from app.interp.repository import InterpRepository
from app.prompts.models import PromptVersion
from app.prompts.repository import PromptRepository
from app.runs.service import ResultsService
from app.templates.enums import AnswerType
from app.templates.models import SurveyTemplate
from app.templates.repository import TemplateRepository
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from app.trace.models import LLMRequest, LLMSpan
from app.trace.repository import SpanRepository
from app.trace.service import LensService
from app.users.models import Band, Function, User, WorkspaceRole
from app.users.repository import UserRepository
from app.workspaces.context import current_workspace
from app.workspaces.models import LEGACY_WORKSPACE_ID, Workspace
from app.workspaces.repository import WorkspaceRepository
from migrations.metadata import migration_metadata
from tests.conftest import TEST_URL
from tests.fakes import FakeLLM, move_on, record
from tests.test_lens import _MeteredLLM


@dataclass
class Company:
    workspace: UUID
    admin: User
    survey: UUID
    run: UUID


@pytest_asyncio.fixture
async def strict_engine(engine):
    # No default workspace, one pooled connection, and no BYPASSRLS. Reusing this
    # connection across companies exercises the failure mode transaction scope prevents.
    strict = create_async_engine(
        TEST_URL,
        pool_size=1,
        max_overflow=2,
        connect_args={"server_settings": {"role": "elenchus_test_runtime"}},
    )
    yield strict
    await strict.dispose()


@pytest_asyncio.fixture
async def companies(strict_engine):
    result = []
    for i, workspace in enumerate((LEGACY_WORKSPACE_ID, uuid4())):
        async with AsyncSession(
            strict_engine, expire_on_commit=False, info={"workspace_id": workspace}
        ) as session:
            if i:
                session.add(Workspace(id=workspace, name=f"Company {i}"))
                await session.commit()
            admin = User(
                email=f"admin-{i}@example.test",
                display_name=f"Admin {i}",
                function=Function.it,
                band=Band.manager,
                workspace_role=WorkspaceRole.owner,
            )
            session.add(admin)
            await session.commit()
            service = TemplateService(session)
            survey = await service.create_draft(
                TemplateCreate(
                    title=f"Private {i}",
                    questions=[
                        QuestionInput(text="What is your role?", answer_type=AnswerType.short_text),
                        QuestionInput(text="Any suggestions?", answer_type=AnswerType.long_text),
                    ],
                ),
                admin,
            )
            await service.publish(survey.id, admin)
            run = await ConductEngine(session, llm=FakeLLM()).start_run(survey.id, admin)
            await ConductEngine(
                session,
                llm=_MeteredLLM(record("Line lead"), move_on("Thanks.")),
            ).handle_message(run.id, "Line lead", admin)
            session.add(
                PromptVersion(
                    family="conduct",
                    name="conduct_v999",
                    body=f"Private prompt {i}",
                    created_by=admin.id,
                )
            )
            await EmbeddingRepository(session).store(
                [
                    EmbeddingVector(digest="a" * 64, model="test", dimensions=1, vector=[float(i)]),
                ]
            )
            await EvaluationRepository(session).label_corpus(
                "same-fixture",
                0,
                LabelVerdict.supported if i == 0 else LabelVerdict.invented,
                f"Private label {i}",
                admin.id,
                datetime.now(UTC),
            )
            await session.commit()
            result.append(Company(workspace, admin, survey.id, run.id))
    return result


async def test_runtime_cannot_bypass_row_policies(strict_engine):
    async with AsyncSession(strict_engine) as session:
        await WorkspaceRepository(session).verify_runtime_role()
        rows = (
            await session.execute(
                text(
                    "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relnamespace = 'public'::regnamespace AND relkind = 'r' "
                    "AND relname <> 'alembic_version'"
                )
            )
        ).all()
        assert {r[0] for r in rows} == set(Base.metadata.tables)
        assert all(enabled and forced for _, enabled, forced in rows)


async def test_autogenerate_preserves_tenant_constraints_without_changing_orm(engine):
    metadata = migration_metadata()
    assert metadata is not Base.metadata
    for name in Base.metadata.tables:
        assert not any(
            constraint.name and str(constraint.name).endswith("_workspace")
            for constraint in Base.metadata.tables[name].foreign_key_constraints
        )

    def compare(connection):
        return compare_metadata(MigrationContext.configure(connection), metadata)

    async with engine.connect() as connection:
        differences = await connection.run_sync(compare)
    tenant_names = {
        constraint.name
        for table in metadata.tables.values()
        for constraint in table.constraints
        if constraint.name
        and (
            str(constraint.name).endswith("_workspace")
            or str(constraint.name).endswith("_workspace_id_id")
        )
    }
    assert len(tenant_names) == 46
    removed = {
        difference[1].name
        for difference in differences
        if isinstance(difference, tuple) and difference[0] in ("remove_fk", "remove_constraint")
    }
    assert not removed & tenant_names, differences


@pytest.mark.parametrize("index", [0, 1])
async def test_company_admin_sees_only_own_directory_results_traces_and_prompts(
    strict_engine, companies, index
):
    own, other = companies[index], companies[1 - index]
    async with AsyncSession(strict_engine, info={"workspace_id": own.workspace}) as session:
        assert [u.id for u in await UserRepository(session).list_all()] == [own.admin.id]
        assert await TemplateRepository(session).get(other.survey) is None
        assert [r.id for r, _ in await TemplateRepository(session).list_summaries(None)] == [
            own.survey
        ]
        results = ResultsService(session)
        assert [row.id for row in await results.dashboard(own.admin)] == [own.survey]
        with pytest.raises(NotFoundError):
            await results.get_run(other.survey, other.run, own.admin)
        with pytest.raises(NotFoundError):
            await results.answers_matrix(other.survey, own.admin)
        assert [row.run_id for row in await LensService(session).runs(own.admin)] == [own.run]
        assert (await LensService(session).strip(own.admin)).runs == 1
        assert await SpanRepository(session).for_run(other.run) == []
        assert await InterpRepository(session).captured(other.survey, other.run) == []
        assert await session.scalar(select(func.count()).select_from(LLMRequest)) == 2
        assert all(s.workspace_id == own.workspace for s in await session.scalars(select(LLMSpan)))
        version = await PromptRepository(session).version("conduct_v999")
        assert version is not None and version.body == f"Private prompt {index}"
        labels = await EvaluationRepository(session).corpus_labels()
        assert labels[("same-fixture", 0)].note == f"Private label {index}"


async def test_cache_reuse_and_withdrawal_never_cross_companies(strict_engine, companies):
    a, b = companies
    for company, expected in ((a, [0.0]), (b, [1.0])):
        async with AsyncSession(strict_engine, info={"workspace_id": company.workspace}) as session:
            assert await EmbeddingRepository(session).cached("test", ["a" * 64]) == {
                "a" * 64: expected
            }
    async with AsyncSession(strict_engine, info={"workspace_id": a.workspace}) as session:
        await EmbeddingRepository(session).delete_digests(["a" * 64])
        await session.commit()
    async with AsyncSession(strict_engine, info={"workspace_id": b.workspace}) as session:
        assert await EmbeddingRepository(session).cached("test", ["a" * 64]) == {"a" * 64: [1.0]}


async def test_explicit_roles_gate_surfaces_and_audited_analyst_access(strict_engine, companies):
    company = companies[0]
    async with AsyncSession(
        strict_engine, expire_on_commit=False, info={"workspace_id": company.workspace}
    ) as session:
        author = User(
            email="role-author@example.test",
            display_name="Role Author",
            function=Function.hr,
            band=Band.manager,
            workspace_role=WorkspaceRole.author,
        )
        analyst = User(
            email="role-analyst@example.test",
            display_name="Role Analyst",
            function=Function.hr,
            band=Band.operative,
            workspace_role=WorkspaceRole.analyst,
        )
        respondent = User(
            email="role-respondent@example.test",
            display_name="Role Respondent",
            function=Function.production,
            band=Band.operative,
            workspace_role=WorkspaceRole.respondent,
        )
        session.add_all([author, analyst, respondent])
        await session.commit()
        assert await require_author(author) is author
        with pytest.raises(ForbiddenError):
            await require_author(respondent)
        with pytest.raises(ForbiddenError):
            await require_admin(author)
        assert await require_results_reader(analyst) is analyst

        template = await TemplateService(session).create_draft(
            TemplateCreate(
                title="Assigned survey",
                questions=[QuestionInput(text="What changed?", answer_type=AnswerType.short_text)],
            ),
            author,
        )
        with pytest.raises(NotFoundError):
            await ResultsService(session).list_runs(template.id, analyst)
        await TemplateService(session).assign_analyst(template.id, analyst.id, company.admin)
        assert await ResultsService(session).list_runs(template.id, analyst) == []
        history = await TemplateRepository(session).access_history(template.id)
        assert [(row.action, row.analyst_id, row.changed_by) for row in history] == [
            ("assigned", analyst.id, company.admin.id)
        ]
        await TemplateService(session).remove_analyst(template.id, analyst.id, company.admin)
        with pytest.raises(NotFoundError):
            await ResultsService(session).list_runs(template.id, analyst)
        history = await TemplateRepository(session).access_history(template.id)
        assert [row.action for row in history] == ["removed", "assigned"]


async def test_unscoped_reads_and_writes_fail_closed_after_pool_reuse(strict_engine, companies):
    for company in companies:
        async with AsyncSession(strict_engine, info={"workspace_id": company.workspace}) as session:
            assert await session.scalar(select(func.count()).select_from(User)) == 1
            await session.commit()
    async with AsyncSession(strict_engine) as session:
        assert await session.scalar(select(func.count()).select_from(User)) == 0
        assert await session.scalar(select(func.count()).select_from(SurveyTemplate)) == 0
        session.add(User(email="unscoped@example.test", display_name="Unscoped"))
        with pytest.raises(DBAPIError):
            await session.commit()


async def test_authentication_resolves_workspace_then_clears_bootstrap_hints(
    strict_engine, companies
):
    for company in companies:
        async with AsyncSession(strict_engine, expire_on_commit=False) as session:
            user = await get_current_user(
                x_user_id=company.admin.id,
                elenchus_session=None,
                session=session,
            )
            assert user.workspace_id == company.workspace
            assert session.info["workspace_id"] == company.workspace
            assert await session.scalar(text("SELECT current_setting('app.actor_id')")) == ""
            await session.commit()
            assert [u.id for u in await UserRepository(session).list_all()] == [company.admin.id]
            await session.rollback()
            assert await session.scalar(select(func.count()).select_from(User)) == 1


async def test_verified_email_bootstrap_is_limited_to_one_account(strict_engine, companies):
    company = companies[1]
    async with AsyncSession(strict_engine) as session:
        assert await WorkspaceRepository(session).resolve_identity(email=company.admin.email)
        assert [u.id for u in await UserRepository(session).list_all()] == [company.admin.id]
        assert await session.scalar(text("SELECT current_setting('app.verified_email')")) == ""


async def test_session_cannot_switch_company_after_loading_objects(strict_engine, companies):
    a, b = companies
    async with AsyncSession(strict_engine, info={"workspace_id": a.workspace}) as session:
        await session.get(User, a.admin.id)
        with pytest.raises(UnauthorizedError):
            await WorkspaceRepository(session).bind(b.workspace)


async def test_microsoft_bootstrap_uses_prelinked_identity_and_clears_hint(
    strict_engine, companies
):
    company = companies[1]
    subject = str(uuid4())
    async with AsyncSession(strict_engine, info={"workspace_id": company.workspace}) as session:
        await session.execute(
            update(User).where(User.id == company.admin.id).values(microsoft_id=subject)
        )
        await session.commit()
    async with AsyncSession(strict_engine) as session:
        assert not await WorkspaceRepository(session).resolve_identity(microsoft_id="unknown")
        assert await session.scalar(select(func.count()).select_from(User)) == 0
        assert await WorkspaceRepository(session).resolve_identity(microsoft_id=subject)
        assert session.info["workspace_id"] == company.workspace
        assert [u.id for u in await UserRepository(session).list_all()] == [company.admin.id]
        assert await session.scalar(text("SELECT current_setting('app.microsoft_id')")) == ""


@pytest.mark.parametrize("operation", ["update", "delete"])
async def test_known_foreign_ids_do_not_allow_mutation(strict_engine, companies, operation):
    a, b = companies
    async with AsyncSession(strict_engine, info={"workspace_id": a.workspace}) as session:
        stmt = (
            update(SurveyTemplate).values(title="Intrusion")
            if operation == "update"
            else delete(SurveyTemplate)
        )
        changed = await session.execute(
            stmt.where(SurveyTemplate.id == b.survey).returning(SurveyTemplate.id)
        )
        assert changed.all() == []
        await session.commit()
    async with AsyncSession(strict_engine, info={"workspace_id": b.workspace}) as session:
        survey = await TemplateRepository(session).get(b.survey)
        assert survey is not None and survey.title == "Private 1"


async def test_cannot_create_own_row_referencing_another_company_user(strict_engine, companies):
    a, b = companies
    async with AsyncSession(strict_engine, info={"workspace_id": a.workspace}) as session:
        session.add(SurveyTemplate(title="Wrong owner", created_by=b.admin.id))
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_cannot_insert_a_row_with_another_company_owner(strict_engine, companies):
    a, b = companies
    async with AsyncSession(strict_engine, info={"workspace_id": a.workspace}) as session:
        session.add(
            User(
                email="wrong-owner@example.test",
                display_name="Wrong owner",
                workspace_id=b.workspace,
            )
        )
        with pytest.raises(DBAPIError):
            await session.commit()


async def test_evaluation_service_accounts_are_private_to_each_workspace(strict_engine, companies):
    account_ids = []
    for company in companies:
        async with AsyncSession(strict_engine, info={"workspace_id": company.workspace}) as session:
            author, respondent = await EvaluationRepository(session).evaluation_accounts(
                EVALUATION_AUTHOR,
                EVALUATION_RESPONDENT,
            )
            assert author.workspace_id == respondent.workspace_id == company.workspace
            account_ids.extend([author.id, respondent.id])
            await session.commit()
    assert len(set(account_ids)) == 4


async def test_production_cookie_selects_company_without_accepting_header_override(
    strict_engine, companies, monkeypatch
):
    a, b = companies
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("SESSION_SECRET", "workspace-cookie-test-secret")
    get_settings.cache_clear()
    try:
        async with AsyncSession(strict_engine) as session:
            user = await get_current_user(
                x_user_id=b.admin.id,
                elenchus_session=oauth.sign(str(a.admin.id), 60),
                session=session,
            )
            assert user.workspace_id == a.workspace
            assert await session.get(User, b.admin.id) is None
    finally:
        get_settings.cache_clear()


async def test_http_directory_and_guessed_survey_id_use_authenticated_company(
    strict_engine, companies, monkeypatch
):
    from app.main import app

    monkeypatch.setattr(
        "app.db.session.SessionFactory", async_sessionmaker(strict_engine, expire_on_commit=False)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        for index, own in enumerate(companies):
            other = companies[1 - index]
            headers = {"X-User-Id": str(own.admin.id), "X-Workspace-Id": str(other.workspace)}
            directory = await client.get("/api/v1/people", headers=headers)
            assert directory.status_code == 200
            assert [row["id"] for row in directory.json()] == [str(own.admin.id)]
            response = await client.get(f"/api/v1/templates/{other.survey}", headers=headers)
            assert response.status_code == 404
            assert current_workspace.get() is None


async def test_production_guard_refuses_superuser_credentials(engine):
    admin = create_async_engine(TEST_URL)
    try:
        async with AsyncSession(admin) as session:
            with pytest.raises(RuntimeError, match="non-superuser"):
                await WorkspaceRepository(session).verify_runtime_role()
    finally:
        await admin.dispose()


async def test_downgrade_refuses_to_merge_two_companies(strict_engine, companies):
    revision = import_module("migrations.versions.ab47d902e631_workspace_isolation")
    admin = create_async_engine(TEST_URL)

    def downgrade(connection):
        with Operations.context(MigrationContext.configure(connection)):
            revision.downgrade()

    try:
        async with admin.begin() as connection:
            with pytest.raises(RuntimeError, match="multi-company"):
                await connection.run_sync(downgrade)
            assert await connection.scalar(text("SELECT count(*) FROM workspaces")) == 2
    finally:
        await admin.dispose()
