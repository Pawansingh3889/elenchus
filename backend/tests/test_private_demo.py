"""Private passes must keep quotas, company boundaries and spending limits intact."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.auth import oauth
from app.config import get_settings
from app.db.session import get_session
from app.demo import budget
from app.demo import service as demo_service
from app.demo.models import PLATFORM_WORKSPACE_ID
from app.demo.policy import AllowanceError
from app.demo.repository import DemoRepository
from app.llm.ledger import TierEconomics
from app.main import app
from app.workspaces.context import workspace_scope
from tests.fakes import FakeLLM, move_on, record


@pytest.fixture
async def demo_runtime(engine, session, author, monkeypatch):
    await session.commit()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setenv("SESSION_SECRET", "private-demo-test-signing-secret")
    monkeypatch.setenv("DEMO_ENABLED", "true")
    monkeypatch.setenv("ADMIN_EMAILS", author.email)
    get_settings.cache_clear()
    monkeypatch.setattr(demo_service, "engine", engine)
    monkeypatch.setattr(demo_service, "SessionFactory", factory)
    monkeypatch.setattr(budget, "SessionFactory", factory)

    async def session_override():
        with workspace_scope(None):
            async with factory() as session:
                yield session

    app.dependency_overrides[get_session] = session_override
    yield factory
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def client(cookie=None):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        cookies={oauth.SESSION_COOKIE: cookie} if cookie else None,
    )


async def issue(operator, email="owner@demo.test"):
    response = await operator.post(
        "/api/v1/demo/passes",
        json={"company": "Demo company", "name": "Demo owner", "email": email},
    )
    assert response.status_code == 201, response.text
    return response.json()


def draft():
    return {
        "title": "Shift check",
        "audience": "signed_in",
        "questions": [
            {"text": "Did handover go well?", "answer_type": "yes_no", "follow_up_policy": "never"}
        ],
    }


async def test_private_demo_from_pass_to_results_cannot_escape_its_allowances(
    demo_runtime, author, monkeypatch
):
    monkeypatch.setattr("app.conduct.engine.get_llm", lambda: FakeLLM(record(True), move_on()))
    async with client(oauth.sign(str(author.id), 3600)) as operator:
        issued = await issue(operator)
        duplicate = await operator.post(
            "/api/v1/demo/passes",
            json={"company": "Duplicate", "name": "Owner", "email": "owner@demo.test"},
        )
        assert duplicate.status_code == 409
        directory = (await operator.get("/api/v1/demo/operator")).json()
        assert len(directory["workspaces"]) == 1
        async with client() as owner:
            entered = await owner.post("/api/v1/demo/enter", json={"token": issued["pass_token"]})
            assert entered.status_code == 200, entered.text
            assert entered.json()["user"]["may_author"] is True
            assert (await owner.get("/api/v1/demo/operator")).status_code == 403
            assert (
                await owner.post("/api/v1/demo/enter", json={"token": issued["pass_token"] + "x"})
            ).status_code == 401
            # Four concurrent creates contend for three lifetime slots.
            responses = await asyncio.gather(
                *[owner.post("/api/v1/templates", json=draft()) for _ in range(4)]
            )
            assert sorted(response.status_code for response in responses) == [201, 201, 201, 429]
            created = [response.json() for response in responses if response.status_code == 201]
            survey = created[0]["id"]
            assert (await owner.delete(f"/api/v1/templates/{created[1]['id']}")).status_code == 204
            assert (await owner.post("/api/v1/templates", json=draft())).status_code == 429
            excessive = {**draft(), "questions": draft()["questions"] * 11}
            assert (
                await owner.put(f"/api/v1/templates/{survey}", json=excessive)
            ).status_code == 422
            assert (await owner.post(f"/api/v1/templates/{survey}/publish")).status_code == 200
            sharing = await owner.post(f"/api/v1/demo/surveys/{survey}/share")
            assert sharing.status_code == 200, sharing.text
            token = sharing.json()["token"]
            async with client() as guest:
                response = await guest.post(
                    "/api/v1/demo/survey-enter", json={"token": token, "consent": True}
                )
                assert response.status_code == 200, response.text
                run_id = response.json()["run_id"]
                assert (await guest.get("/api/v1/dashboard")).status_code == 403
                assert (await guest.get("/api/v1/demo/operator")).status_code == 403
                assert (await guest.post("/api/v1/templates", json=draft())).status_code == 403
                answered = await guest.post(
                    f"/api/v1/runs/{run_id}/messages", json={"content": "Yes"}
                )
                assert answered.status_code == 200, answered.text
                assert answered.json()["status"] == "completed"
                assert len((await guest.get("/api/v1/templates/published")).json()) == 1
                report = (await owner.get(f"/api/v1/templates/{survey}/report")).json()
                assert report["runs_completed"] == 1
                assert report["questions"][0]["answered"] == 1

            # Creating participant accounts and starting their run is one quota transaction.
            async def join():
                async with client() as participant:
                    return await participant.post(
                        "/api/v1/demo/survey-enter", json={"token": token, "consent": True}
                    )

            admissions = await asyncio.gather(*(join() for _ in range(20)))
            assert sum(response.status_code == 200 for response in admissions) == 19
            assert sum(response.status_code in (409, 429) for response in admissions) == 1
            async with client(
                oauth.sign(f"survey:{issued['workspace_id']}:{survey}", 60)
            ) as invalid:
                assert (await invalid.get("/api/v1/me")).status_code == 401
            from uuid import UUID

            async with demo_runtime(info={"workspace_id": UUID(issued["workspace_id"])}) as tenant:
                access = await DemoRepository(tenant).access()
                access.expires_at = datetime.now(UTC) - timedelta(seconds=1)
                await tenant.commit()
            assert (
                await owner.post("/api/v1/demo/enter", json={"token": issued["pass_token"]})
            ).status_code == 200
            assert (await owner.get(f"/api/v1/templates/{survey}/report")).status_code == 200
            assert (await owner.post("/api/v1/templates", json=draft())).status_code == 403
            # Any verified product unlocks survey creation. No fixed response allowance is assumed.
            activation = await operator.post(
                f"/api/v1/demo/workspaces/{issued['workspace_id']}/activate",
                json={
                    "product": "Future KapkotiSolution product",
                    "purchase_type": "one_time",
                    "monthly_response_allowance": 21,
                    "purchase_verified": True,
                },
            )
            assert activation.status_code == 200, activation.text
            assert (await owner.post("/api/v1/templates", json=draft())).status_code == 201
            assert (
                await owner.post("/api/v1/demo/enter", json={"token": issued["pass_token"]})
            ).status_code == 401
            other = await issue(operator, "other@demo.test")
            async with client() as stranger:
                await stranger.post("/api/v1/demo/enter", json={"token": other["pass_token"]})
                assert (await stranger.get(f"/api/v1/templates/{survey}/report")).status_code == 404
            assert (
                await operator.post(f"/api/v1/demo/workspaces/{issued['workspace_id']}/revoke")
            ).status_code == 204
            assert (await owner.get(f"/api/v1/templates/{survey}/report")).status_code == 403


async def test_demo_reservations_keep_unknown_cost_and_serialize_the_global_cap(
    demo_runtime, author, monkeypatch
):
    from uuid import UUID

    async with client(oauth.sign(str(author.id), 3600)) as operator:
        issued = await issue(operator)
    workspace = UUID(issued["workspace_id"])
    economics = TierEconomics(local=False, params_b=0, price_in_per_mtok=1, price_out_per_mtok=1)
    payload = {"model": "mock-model", "messages": [], "max_completion_tokens": 10}
    with workspace_scope(workspace):
        async with budget.reserve_attempt(payload, economics) as result:
            result["usage"] = {"prompt_tokens": 100, "completion_tokens": 10}
        with pytest.raises(RuntimeError, match="transport failed"):
            async with budget.reserve_attempt(payload, economics):
                raise RuntimeError("transport failed")
    month = datetime.now(UTC).date().replace(day=1)
    async with demo_runtime(info={"workspace_id": PLATFORM_WORKSPACE_ID}) as platform:
        rows = await DemoRepository(platform).spend_rows(month)
        assert len(rows) == 2
        assert sum(row.actual_usd == Decimal("0.00011000") for row in rows) == 1
        failed = next(row for row in rows if row.failed)
        assert failed.actual_usd is None and failed.reserved_usd > 0
        current = await DemoRepository(platform).charged(month)
    monkeypatch.setenv("DEMO_MONTHLY_BUDGET_USD", str(current + failed.reserved_usd))
    get_settings.cache_clear()

    async def attempt():
        with workspace_scope(workspace):
            try:
                async with budget.reserve_attempt(payload, economics):
                    pass
                return "reserved"
            except AllowanceError:
                return "refused"

    assert sorted(await asyncio.gather(attempt(), attempt())) == ["refused", "reserved"]
