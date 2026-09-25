"""Evaluation runs: scripted scenarios driven through the real engine, in the background.

A batch is a list of scenarios run one after another, each pinned to one tier and one
conduct prompt version, under one spend cap. Each scenario builds its own survey aimed at
the evaluation respondent alone, holds the scripted conversation turn by turn, and checks
the finished transcript. A scenario with a brief has its survey drafted by the same pinned
tier first, and the draft's cost is the run's. Cost is read from the run's rollup after
every turn, plus any draft: a run that reaches what is left of the cap stops there as
capped, and the scenarios after it never start. A scenario that fails is recorded with its
error and the batch carries on.

The runner opens its own sessions, because it outlives the request that started it.
"""

import asyncio
import json
import logging
import time
from collections import Counter
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.conduct.engine import ConductEngine
from app.evaluation.enums import EvalRunStatus
from app.evaluation.models import EvalRun
from app.evaluation.repository import EvaluationRepository
from app.evaluation.scenarios import Scenario, Transcript, max_turns
from app.llm import ledger
from app.llm.client import LLMProtocol
from app.runs.enums import MessageRole, RunStatus
from app.templates.enums import SurveyAudience
from app.templates.generation import GenerationService
from app.templates.schemas import TemplateCreate
from app.templates.service import TemplateService
from app.workspaces.context import workspace_scope

logger = logging.getLogger(__name__)

EVALUATION_AUTHOR = ("evaluation-author@elenchus.dev", "Evaluation author")
EVALUATION_RESPONDENT = ("evaluation-respondent@elenchus.dev", "Evaluation respondent")

# Held so a running batch is not garbage-collected out from under itself.
_RUNNING: set[asyncio.Task[None]] = set()


def launch(work: Coroutine[Any, Any, None]) -> None:
    task = asyncio.get_running_loop().create_task(work)
    _RUNNING.add(task)
    task.add_done_callback(_RUNNING.discard)


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


async def run_batch(
    sessions: async_sessionmaker[AsyncSession],
    batch_id: UUID,
    make_llm: Callable[[int], LLMProtocol],
    catalogue: dict[str, Scenario],
    *,
    workspace_id: UUID,
) -> None:
    with workspace_scope(workspace_id):
        await _run_batch(sessions, batch_id, make_llm, catalogue, workspace_id=workspace_id)


async def _run_batch(
    sessions: async_sessionmaker[AsyncSession],
    batch_id: UUID,
    make_llm: Callable[[int], LLMProtocol],
    catalogue: dict[str, Scenario],
    *,
    workspace_id: UUID,
) -> None:
    async with sessions(info={"workspace_id": workspace_id}) as session:
        ids = [row.id for row in await EvaluationRepository(session).eval_runs_in_batch(batch_id)]
    spent = 0.0
    for eval_run_id in ids:
        async with sessions(info={"workspace_id": workspace_id}) as session:
            row = await EvaluationRepository(session).eval_run(eval_run_id)
            if row is None:
                continue
            remaining = float(row.cap_usd) - spent
            if remaining <= 0:
                row.status = EvalRunStatus.capped
                row.error = "The batch had spent its cap before this scenario started."
                row.finished_at = datetime.now(UTC)
                await session.commit()
                continue
        try:
            async with sessions(info={"workspace_id": workspace_id}) as session:
                spent += await _run_one(session, eval_run_id, make_llm, catalogue, remaining)
        except Exception as exc:
            logger.exception("evaluation run failed: eval_run=%s", eval_run_id)
            async with sessions(info={"workspace_id": workspace_id}) as session:
                row = await EvaluationRepository(session).eval_run(eval_run_id)
                if row is not None:
                    row.status = EvalRunStatus.failed
                    row.error = f"{type(exc).__name__}: {exc}"[:500]
                    row.finished_at = datetime.now(UTC)
                    spent += float(row.cost_usd)
                    await session.commit()


async def _run_one(
    session: AsyncSession,
    eval_run_id: UUID,
    make_llm: Callable[[int], LLMProtocol],
    catalogue: dict[str, Scenario],
    remaining: float,
) -> float:
    """Hold one scenario's conversation and check it. Returns what it spent."""
    repo = EvaluationRepository(session)
    row = await repo.eval_run(eval_run_id)
    assert row is not None, "a queued row is only removed with its batch"
    scenario = catalogue[row.scenario]
    started = time.monotonic()
    row.status = EvalRunStatus.running
    row.started_at = row.heartbeat_at = datetime.now(UTC)
    await session.commit()

    author, respondent = await repo.evaluation_accounts(EVALUATION_AUTHOR, EVALUATION_RESPONDENT)
    llm = make_llm(row.tier)
    templates = TemplateService(session)
    drafting = Decimal(0)
    drafting_unmetered = 0
    if scenario.brief is not None:
        # The pinned tier drafts the survey. Its cost is measured here, because no survey
        # run exists yet to roll it into, and it counts against the cap like any turn.
        with ledger.measuring() as spend:
            template, _ = await GenerationService(session, llm=llm).generate_draft(
                scenario.brief, author, SurveyAudience.person, respondent.id
            )
        template_id = template.id
        drafting = Decimal(str(spend.cost_usd))
        drafting_unmetered = spend.unmetered_calls
        row.template_id = template_id
        row.cost_usd, row.unmetered_calls = drafting, drafting_unmetered
        row.heartbeat_at = datetime.now(UTC)
        await session.commit()
        if float(drafting) >= remaining:
            row.status = EvalRunStatus.capped
            row.error = "The batch's cap was reached while drafting this scenario's survey."
            row.duration_ms = int((time.monotonic() - started) * 1000)
            row.finished_at = datetime.now(UTC)
            await session.commit()
            return float(drafting)
    else:
        template = await templates.create_draft(
            TemplateCreate(
                title=f"{scenario.survey_title} (evaluation)",
                description=f"Built by the {scenario.key} evaluation scenario.",
                audience=SurveyAudience.person,
                audience_user_id=respondent.id,
                questions=scenario.questions,
            ),
            author,
        )
        template_id = template.id
    await templates.publish(template_id, author)
    engine = ConductEngine(session, llm=llm, prompt_version=row.prompt_version)
    run = await engine.start_run(template_id, respondent)
    row.template_id, row.run_id = template_id, run.id
    await session.commit()

    transcript = Transcript(questions=await engine.questions(run), today=run.started_at.date())
    seen: dict[str, int] = {}
    capped = False
    for turn in range(max_turns(scenario, len(transcript.questions))):
        if run.status is not RunStatus.in_progress:
            break
        questions = await engine.questions(run)
        if run.current_question_index >= len(questions):
            break
        current = questions[run.current_question_index]
        transcript.positions.append(run.current_question_index)
        seen[current["id"]] = seen.get(current["id"], 0) + 1
        said = [m for m in _in_order(run.messages) if m.role is MessageRole.assistant]
        reply = scenario.respond(
            current, said[-1].content if said else "", seen[current["id"]], turn
        )
        run = await engine.handle_message(run.id, reply, respondent)
        row.turns = turn + 1
        row.cost_usd = run.llm_cost_usd + drafting
        row.unmetered_calls = run.llm_unmetered_calls + drafting_unmetered
        row.heartbeat_at = datetime.now(UTC)
        await session.commit()
        if float(run.llm_cost_usd + drafting) >= remaining:
            capped = True
            break

    transcript.answers = [
        {
            "question_id": str(answer.question_id),
            "kind": answer.kind.value,
            "value": answer.value,
            "question_text": answer.question_text,
        }
        for answer in sorted(run.answers, key=lambda a: a.answered_at)
    ]
    messages = _in_order(run.messages)
    transcript.messages = [{"role": m.role.value, "content": m.content} for m in messages]
    transcript.status = run.status.value
    checks = scenario.check(transcript)
    models = Counter(m.model for m in messages if m.role is MessageRole.assistant and m.model)

    row.checks = [
        {"name": c.name, "ok": c.ok, "hard": c.hard, "detail": _jsonable(c.detail)} for c in checks
    ]
    row.hard_failures = sum(1 for c in checks if c.hard and not c.ok)
    row.soft_failures = sum(1 for c in checks if not c.hard and not c.ok)
    row.answers = len(transcript.answers)
    row.model = models.most_common(1)[0][0] if models else None
    row.status = EvalRunStatus.capped if capped else EvalRunStatus.completed
    if capped:
        row.error = "The batch's cap was reached during this scenario."
    row.duration_ms = int((time.monotonic() - started) * 1000)
    row.finished_at = datetime.now(UTC)
    await session.commit()
    return float(run.llm_cost_usd + drafting)


def _in_order(messages: list[Any]) -> list[Any]:
    return sorted(messages, key=lambda m: m.created_at)


def queued_rows(
    batch_id: UUID,
    scenarios: list[str],
    *,
    tier: int,
    prompt_version: str,
    cap_usd: Any,
    created_by: UUID,
    at: datetime,
) -> list[EvalRun]:
    return [
        EvalRun(
            batch_id=batch_id,
            position=position,
            scenario=key,
            tier=tier,
            prompt_version=prompt_version,
            status=EvalRunStatus.queued,
            cap_usd=cap_usd,
            checks=[],
            created_by=created_by,
            queued_at=at,
        )
        for position, key in enumerate(scenarios)
    ]
