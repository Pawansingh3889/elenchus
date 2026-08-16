"""Load the curated sample dataset into a database.

Idempotent and keyed on the fixtures' stable ids: rows already present are skipped, so
running it repeatedly (as the dev seed does on every boot) is safe. User keys are
resolved to seeded users by email local-part, so the loader never hard-codes user ids.

Timestamps are stamped deterministically from a fixed base — the committed data must not
depend on wall-clock time — spacing messages and answers one second apart to preserve
transcript order.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.runs.models import Answer, RunMessage, SurveyRun
from app.sample_data import SAMPLE_RUNS, SAMPLE_SURVEYS, SURVEY_BY_KEY, RunFixture, SurveyFixture
from app.templates.enums import AnswerType, FollowUpPolicy, TemplateStatus
from app.templates.models import SurveyQuestion, SurveyTemplate
from app.users.models import User

# A fixed, timezone-aware base so seeded timestamps are reproducible across machines.
_BASE = datetime(2026, 7, 20, 9, 0, 0, tzinfo=UTC)


async def load_sample_data(session: AsyncSession) -> tuple[int, int]:
    """Insert any missing sample surveys and runs. Returns (surveys_added, runs_added)."""
    users = {
        user.email.split("@", 1)[0]: user.id
        for user in (await session.execute(select(User))).scalars()
    }

    surveys_added = 0
    for survey in SAMPLE_SURVEYS:
        if await session.get(SurveyTemplate, UUID(survey["template_id"])) is None:
            _insert_survey(session, survey, users)
            surveys_added += 1

    runs_added = 0
    for index, run in enumerate(SAMPLE_RUNS):
        if await session.get(SurveyRun, UUID(run["run_id"])) is None:
            _insert_run(session, run, users, base=_BASE + timedelta(hours=index))
            runs_added += 1

    await session.commit()
    return surveys_added, runs_added


def _user(users: dict[str, UUID], key: str) -> UUID:
    if key not in users:
        raise LookupError(f"sample data references unknown user '{key}'; seed users first")
    return users[key]


def _insert_survey(session: AsyncSession, survey: SurveyFixture, users: dict[str, UUID]) -> None:
    definition = survey["version"]["definition"]
    template = SurveyTemplate(
        id=UUID(survey["template_id"]),
        title=survey["title"],
        description=survey["description"],
        status=TemplateStatus.published,
        created_by=_user(users, survey["created_by"]),
    )
    # The questions come from the fixture's definition block, which is where they have
    # always lived. It used to be a frozen snapshot beside the draft; it is now simply
    # the fixture's record of the questions, and there is one copy in the database.
    for question in definition["questions"]:
        template.questions.append(
            SurveyQuestion(
                id=UUID(question["id"]),
                position=question["position"],
                text=question["text"],
                answer_type=AnswerType(question["answer_type"]),
                options=question["options"],
                allow_other=question["allow_other"],
                required=question["required"],
                follow_up_policy=FollowUpPolicy(question["follow_up_policy"]),
            )
        )
    # Published, with the fixture's own publication details rather than a snapshot row.
    # An explicit stamp, not `template.created_at`: that column has a server default and
    # is still None until the flush, so copying it here left every sample survey looking
    # unpublished and its results 404ing.
    template.published_at = datetime.now(UTC)
    template.published_by = _user(users, survey["version"]["published_by"])
    session.add(template)


def _insert_run(
    session: AsyncSession, run: RunFixture, users: dict[str, UUID], base: datetime
) -> None:
    respondent = _user(users, run["respondent"])
    template_id = UUID(SURVEY_BY_KEY[run["survey_key"]]["template_id"])
    completed_at = base + timedelta(minutes=5) if run["completed"] else None
    survey_run = SurveyRun(
        id=UUID(run["run_id"]),
        template_id=template_id,
        respondent_id=respondent,
        status=RunStatus(run["status"]),
        current_question_index=run["current_question_index"],
        probes_asked=run["probes_asked"],
        started_at=base,
        completed_at=completed_at,
    )
    for offset, message in enumerate(run["messages"], start=1):
        survey_run.messages.append(
            RunMessage(
                role=MessageRole(message["role"]),
                content=message["content"],
                created_at=base + timedelta(seconds=offset),
            )
        )
    for offset, answer in enumerate(run["answers"], start=1):
        survey_run.answers.append(
            Answer(
                question_id=UUID(answer["question_id"]),
                kind=AnswerKind(answer["kind"]),
                question_text=answer["question_text"],
                value=answer["value"],
                answered_by=respondent,
                answered_at=base + timedelta(seconds=offset),
            )
        )
    session.add(survey_run)
