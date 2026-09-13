"""Accuracy per model against its cost and latency, and whether Qwen's agreement means much.

Evaluation rows are seeded directly, because what is under test is the arithmetic over
finished runs, not the runner. The agreement test drives the engine with the fake model so
its spans are real, then stores a Qwen reading against them.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.conduct.engine import ConductEngine
from app.errors import ForbiddenError
from app.evaluation.enums import EvalRunStatus, LabelVerdict
from app.evaluation.models import EvalRun
from app.evaluation.schemas import LabelRequest
from app.evaluation.service import EvaluationService
from app.interp.models import InterpAnalysis
from app.runs.models import Answer
from app.trace.enums import SpanKind
from app.trace.models import LLMSpan
from app.users.models import Band, Function, User
from tests.fakes import FakeLLM, move_on, record
from tests.test_interp_lens import _analysis


@pytest_asyncio.fixture
async def admin(session):
    user = User(
        email="eval-compare-admin@plant.dev",
        display_name="Eval Compare Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


def _run(
    admin,
    scenario,
    status,
    *,
    model="gpt-5.5",
    prompt="conduct_v8",
    hard_failed=0,
    cost="0.08",
    duration=15000,
    turns=4,
) -> EvalRun:
    checks = [{"name": "run reached completed", "ok": True, "hard": True, "detail": None}]
    checks += [
        {"name": f"hard {i}", "ok": False, "hard": True, "detail": None} for i in range(hard_failed)
    ]
    checks += [{"name": "judge agrees", "ok": False, "hard": False, "detail": None}]
    return EvalRun(
        batch_id=uuid4(),
        position=0,
        scenario=scenario,
        tier=1,
        model=model,
        prompt_version=prompt,
        status=status,
        cap_usd=Decimal("1"),
        turns=turns,
        answers=turns,
        hard_failures=hard_failed,
        soft_failures=1,
        checks=checks,
        cost_usd=Decimal(cost),
        unmetered_calls=0,
        duration_ms=duration,
        created_by=admin.id,
        queued_at=datetime.now(UTC),
    )


async def test_accuracy_is_read_per_model_and_prompt_from_completed_runs_only(session, admin):
    session.add_all(
        [
            _run(admin, "numbers_dates", EvalRunStatus.completed),
            _run(
                admin,
                "numbers_dates",
                EvalRunStatus.completed,
                hard_failed=1,
                cost="0.10",
                duration=17000,
                turns=5,
            ),
            _run(admin, "injection", EvalRunStatus.completed, prompt="conduct_v7", cost="0.05"),
            _run(admin, "injection", EvalRunStatus.completed, model=None, cost="0.02"),
            _run(admin, "numbers_dates", EvalRunStatus.capped, cost="0.50"),
            _run(admin, "numbers_dates", EvalRunStatus.failed, cost="0.01"),
        ]
    )
    await session.commit()

    report = await EvaluationService(session).comparison(admin)

    assert (report.completed_runs, report.left_out) == (4, 2)
    groups = {group.name: group for group in report.groups}
    assert sorted(groups) == [
        "gpt-5.5 with conduct_v7",
        "gpt-5.5 with conduct_v8",
        "tier 1, model not recorded with conduct_v8",
    ]
    v8 = groups["gpt-5.5 with conduct_v8"]
    assert v8.runs == 2 and v8.scenarios == ["numbers_dates"]
    assert (v8.clean_runs.numerator, v8.clean_runs.denominator) == (1, 2)
    # Two hard checks passed of three; the soft check failing in every run is not accuracy.
    assert (v8.hard_checks.numerator, v8.hard_checks.denominator) == (2, 3)
    assert v8.clean_runs.too_few
    assert v8.cost_per_run.value == pytest.approx(0.09) and v8.cost_per_run.n == 2
    assert (v8.duration_ms.value, v8.turns.value) == (16000, 4.5)
    cells = {(cell.scenario, cell.group): cell for cell in report.cells}
    assert (
        cells[("numbers_dates", "gpt-5.5 with conduct_v8")].runs,
        cells[("numbers_dates", "gpt-5.5 with conduct_v8")].clean_runs,
    ) == (2, 1)
    assert report.agreement.analysed == 0 and report.agreement.agrees.value is None


async def test_qwen_agreement_is_read_beside_the_check_and_the_label(
    session, respondent, published, admin
):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."), serves_as=(1, "gpt-5.5"))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead on nights", respondent)

    spans = (await session.scalars(select(LLMSpan).where(LLMSpan.run_id == run.id))).all()
    checks = {s.parent_id: s.attrs for s in spans if s.kind is SpanKind.validation}
    attempts = {checks[s.parent_id]["tool"]: s for s in spans if s.kind is SpanKind.attempt}
    offered = ["record_answer", "move_on", "reply"]
    # Qwen would have replied where the hosted model recorded, and agrees on moving on.
    for tool, pick in (("record_answer", "reply"), ("move_on", "move_on")):
        session.add(
            InterpAnalysis(
                span_id=attempts[tool].id,
                run_id=run.id,
                model="Qwen/Qwen3-0.6B",
                revision="c1899de",
                device="cpu",
                target_tool=tool,
                result=_analysis(offered, pick),
                duration_ms=80000,
                created_at=datetime.now(UTC),
            )
        )
    (answer,) = (await session.scalars(select(Answer).where(Answer.run_id == run.id))).all()
    service = EvaluationService(session)
    await service.label(admin, f"answer:{answer.id}", LabelRequest(verdict=LabelVerdict.invented))
    await session.commit()

    agreement = (await service.comparison(admin)).agreement

    assert agreement.analysed == 2
    assert (agreement.agrees.numerator, agreement.agrees.denominator) == (1, 2)
    assert (agreement.when_accepted.numerator, agreement.when_accepted.denominator) == (1, 2)
    assert agreement.when_refused.denominator == 0 and agreement.when_refused.value is None
    assert (agreement.on_invented.numerator, agreement.on_invented.denominator) == (0, 1)
    assert agreement.on_supported.denominator == 0


async def test_only_admins_read_the_comparison(session, author):
    with pytest.raises(ForbiddenError):
        await EvaluationService(session).comparison(author)
