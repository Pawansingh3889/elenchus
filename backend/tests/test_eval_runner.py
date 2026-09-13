"""Evaluation runs: a scenario driven through the real engine, checked, and held to its cap.

The model is faked at the client boundary with one that books a priced call, so every run
spends something and the cap is exercised for real. The runner is awaited directly instead
of launched in the background, so each test sees the batch finish.
"""

from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.errors import ForbiddenError, ValidationError
from app.evaluation.runner import EVALUATION_AUTHOR, EVALUATION_RESPONDENT
from app.evaluation.scenarios import Check, Scenario, base_checks, q
from app.evaluation.schemas import MIN_CAP_USD, EvalStartRequest
from app.evaluation.service import EvaluationService
from app.llm import ledger
from app.llm.client import LLMError
from app.templates.enums import SurveyAudience
from app.templates.models import SurveyTemplate
from app.users.models import Band, Function, User
from tests.fakes import FakeLLM, move_on, record


class MeteredLLM(FakeLLM):
    """Books every call as a timed local call, so a run always costs something."""

    def _book(self, *, status: int, error: str | None, request: dict[str, Any]) -> None:
        ledger.record(
            tier=4,
            model="local-3b",
            op="tool_turn",
            usage=None if error else {"prompt_tokens": 1000, "completion_tokens": 20},
            latency_ms=1200,
            status=status,
            error=error,
            request=request,
        )


def _one_question(key: str) -> Scenario:
    return Scenario(
        key=key,
        title="One short answer",
        survey_title="Role Check",
        questions=[q("What is your role?", "short_text")],
        respond=lambda question, last, seen, turn: "line lead",
        check=lambda t: [
            *base_checks(t),
            Check("the role was recorded", any("text" in a["value"] for a in t.answers), False),
        ],
    )


CATALOGUE = {"first": _one_question("first"), "second": _one_question("second")}


@pytest_asyncio.fixture
async def admin(session):
    user = User(
        email="eval-runner-admin@plant.dev",
        display_name="Eval Runner Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


def _service(session, engine, make_llm, pending) -> EvaluationService:
    return EvaluationService(
        session,
        sessions=async_sessionmaker(engine, expire_on_commit=False),
        make_llm=make_llm,
        catalogue=CATALOGUE,
        launch=pending.append,
    )


def _answering(tier: int) -> FakeLLM:
    return MeteredLLM(record("line lead"), move_on("Thanks."))


async def test_a_scenario_runs_through_the_engine_and_keeps_its_checks(session, engine, admin):
    pending: list = []
    service = _service(session, engine, _answering, pending)

    queued = await service.start_eval(
        admin, EvalStartRequest(scenarios=["first"], tier=1, cap_usd=5.0)
    )
    assert [run.status for run in queued] == ["queued"]
    await pending[0]

    (done,) = await service.eval_runs(admin)
    assert done.status == "completed", done.error
    assert (done.turns, done.answers, done.hard_failures) == (1, 1, 0)
    assert done.model == "local-3b" and done.cost_usd > 0 and done.run_id is not None
    assert done.prompt_version.startswith("conduct_v")
    assert "run reached completed" in [check.name for check in done.checks]

    # The evaluation accounts hold no job, and the survey is aimed at the respondent alone.
    emails = (EVALUATION_AUTHOR[0], EVALUATION_RESPONDENT[0])
    accounts = (await session.scalars(select(User).where(User.email.in_(emails)))).all()
    assert len(accounts) == 2 and all(u.function is None and u.band is None for u in accounts)
    template = await session.get(SurveyTemplate, done.template_id)
    respondent = next(u for u in accounts if u.email == EVALUATION_RESPONDENT[0])
    assert template.audience is SurveyAudience.person
    assert template.audience_user_id == respondent.id


async def test_the_cap_stops_the_run_that_reaches_it_and_the_rest_never_start(
    session, engine, admin
):
    pending: list = []
    service = _service(session, engine, _answering, pending)
    await service.start_eval(
        admin, EvalStartRequest(scenarios=["first", "second"], tier=1, cap_usd=MIN_CAP_USD)
    )
    await pending[0]

    first, second = sorted(await service.eval_runs(admin), key=lambda run: run.position)
    assert first.status == "capped" and first.turns == 1 and first.cost_usd > 0
    assert second.status == "capped" and second.turns == 0 and second.run_id is None


async def test_a_failing_scenario_is_recorded_and_the_batch_carries_on(session, engine, admin):
    calls = {"n": 0}

    def flaky(tier: int) -> FakeLLM:
        calls["n"] += 1
        if calls["n"] == 2:  # the first call is start_eval checking the tier
            return MeteredLLM(LLMError("tier down"))
        return MeteredLLM(record("line lead"), move_on("Thanks."))

    pending: list = []
    service = _service(session, engine, flaky, pending)
    await service.start_eval(
        admin, EvalStartRequest(scenarios=["first", "second"], tier=1, cap_usd=5.0)
    )
    await pending[0]

    first, second = sorted(await service.eval_runs(admin), key=lambda run: run.position)
    assert first.status == "failed" and "tier down" in (first.error or "")
    assert second.status == "completed", second.error


async def test_a_batch_is_refused_before_anything_is_queued(session, engine, admin):
    pending: list = []

    def off(tier: int) -> FakeLLM:
        raise LLMError(f"Tier {tier} is not enabled on this deployment.")

    service = _service(session, engine, _answering, pending)
    with pytest.raises(ValidationError, match="No such scenario"):
        await service.start_eval(admin, EvalStartRequest(scenarios=["nope"], tier=1, cap_usd=1))
    with pytest.raises(ValidationError, match="once"):
        await service.start_eval(
            admin, EvalStartRequest(scenarios=["first", "first"], tier=1, cap_usd=1)
        )
    with pytest.raises(ValidationError, match="No conduct prompt"):
        await service.start_eval(
            admin,
            EvalStartRequest(scenarios=["first"], tier=1, prompt_version="conduct_v999", cap_usd=1),
        )
    with pytest.raises(ValidationError, match="not enabled"):
        await _service(session, engine, off, pending).start_eval(
            admin, EvalStartRequest(scenarios=["first"], tier=3, cap_usd=1)
        )
    assert pending == [] and await service.eval_runs(admin) == []


def test_a_cap_outside_what_one_batch_may_spend_is_refused():
    with pytest.raises(ValueError):
        EvalStartRequest(scenarios=["first"], tier=1, cap_usd=0)
    # Below what the column holds exactly, which once stored a cap as zero.
    with pytest.raises(ValueError):
        EvalStartRequest(scenarios=["first"], tier=1, cap_usd=MIN_CAP_USD / 10)
    with pytest.raises(ValueError):
        EvalStartRequest(scenarios=["first"], tier=1, cap_usd=26)


async def test_options_list_scenarios_tiers_and_prompt_versions(session, engine, admin):
    options = await _service(session, engine, _answering, []).eval_options(admin)
    assert [s.key for s in options.scenarios] == ["first", "second"]
    assert "conduct_v7" in options.prompt_versions and "conduct_v8" in options.prompt_versions
    assert options.active_prompt.startswith("conduct_v")


async def test_only_admins_run_evaluations(session, engine, author):
    service = _service(session, engine, _answering, [])
    with pytest.raises(ForbiddenError):
        await service.eval_options(author)
    with pytest.raises(ForbiddenError):
        await service.start_eval(author, EvalStartRequest(scenarios=["first"], tier=1, cap_usd=1))
    with pytest.raises(ForbiddenError):
        await service.eval_runs(author)
