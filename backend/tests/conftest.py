"""Test fixtures: a real Postgres test database whose schema comes from the migrations.

Uses the compose Postgres (a separate ``elenchus_test`` database), so repository and
service logic is exercised against the real engine, not a stand-in. The schema is built
once per session by ``alembic upgrade head`` and each test starts from truncated tables:
a suite whose schema came from ``Base.metadata`` was testing the models rather than the
migrations, which is precisely what ``check_no_create_all`` forbids, and this conftest
sat in that guard's blind spot until the guard learned to see the ``run_sync`` idiom.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.db.base import Base
from app.embeddings import models as _embeddings  # noqa: F401
from app.prompts import models as _prompts  # noqa: F401
from app.runs import models as _runs  # noqa: F401  (register tables on metadata)
from app.templates import models as _templates  # noqa: F401
from app.templates.enums import AnswerType, FollowUpPolicy
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from app.trace import models as _trace  # noqa: F401
from app.users.models import Band, Function, User

ADMIN_URL = "postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus"
TEST_URL = "postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus_test"
BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True, scope="session")
def _ledger_to_a_temp_file(tmp_path_factory):
    """Keep the suite out of the real spend ledger.

    ``LLM_LEDGER_PATH`` defaults to a path relative to the backend directory, which is
    where pytest runs from. Without this, every test that drives the LLM client appends
    invented calls to the same file real runs are measured in, so ``make gate`` quietly
    corrupts the data set the ledger exists to build. Found by running the suite and then
    reading the file: it was full of ``nemotron-test`` at tier 0.

    Session-scoped and autouse because the damage is silent and any test can cause it.
    """
    path = tmp_path_factory.mktemp("ledger") / "llm_ledger.jsonl"
    previous = os.environ.get("LLM_LEDGER_PATH")
    os.environ["LLM_LEDGER_PATH"] = str(path)
    get_settings.cache_clear()
    yield
    if previous is None:
        os.environ.pop("LLM_LEDGER_PATH", None)
    else:
        os.environ["LLM_LEDGER_PATH"] = previous
    get_settings.cache_clear()


@pytest.fixture(autouse=True, scope="session")
def _a_tier_that_costs_something(_ledger_to_a_temp_file):
    """Give the suite one tier whose calls have a non-zero price.

    Several tests assert that spend reaches a run at all, which needs some tier that is
    not free. That used to come free with the defaults: tier 4 was the shipped Ollama and
    carried ``local=True``, so its calls priced from the clock. The service was removed on
    8 Aug 2026 and the slot now defaults hosted with zero prices like every other, which
    made those assertions read ``0 > 0``.

    Set here rather than per test so the suite states its assumption once, and so no test
    silently depends on whatever the shipped defaults happen to be next.
    """
    previous = {name: os.environ.get(name) for name in ("LLM_TIER4_LOCAL", "LLM_TIER4_PARAMS_B")}
    os.environ["LLM_TIER4_LOCAL"] = "true"
    os.environ["LLM_TIER4_PARAMS_B"] = "3"
    get_settings.cache_clear()
    yield
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def _migrated_test_schema():
    """Build the test schema from the migrations, once per session.

    A subprocess rather than the Alembic API, because the async ``migrations/env.py``
    ends in ``asyncio.run`` and cannot nest inside a pytest event loop; a sync
    session-scoped fixture runs outside any loop, so its own ``asyncio.run`` for the
    database reset is safe. The schema is dropped first so a table left behind by an
    older branch cannot make an upgrade pass that would fail on a clean install.
    """

    async def reset_database() -> None:
        admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
        async with admin.connect() as conn:
            found = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = 'elenchus_test'")
            )
            if not found:
                await conn.execute(text("CREATE DATABASE elenchus_test"))
        await admin.dispose()
        eng = create_async_engine(TEST_URL, isolation_level="AUTOCOMMIT")
        async with eng.connect() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
        await eng.dispose()

    asyncio.run(reset_database())
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": TEST_URL},
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "alembic upgrade head failed on the test database, so the suite cannot "
            f"run:\n{result.stdout}\n{result.stderr}"
        )


@pytest_asyncio.fixture
async def engine(_migrated_test_schema):
    eng = create_async_engine(TEST_URL)
    async with eng.begin() as conn:
        # Isolation between tests is truncation, not re-creation: the schema itself came
        # from the migrations above and stays put for the whole session. One statement,
        # CASCADE for the foreign keys.
        tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess


@pytest_asyncio.fixture
async def author(session):
    """Someone who may build surveys: manager band, in an office function (HR).

    HR rather than production so the colleague tests stay sharp: this author's
    function-mates are other office managers, not the floor they survey.
    """
    user = User(
        email="author@test.dev",
        display_name="Test Author",
        function=Function.hr,
        band=Band.manager,
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def other_author(session):
    """A second author in a different function, for proving one author cannot reach
    another's work: finance and HR do not share, by the silo decision."""
    user = User(
        email="other@test.dev",
        display_name="Other Author",
        function=Function.finance,
        band=Band.manager,
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def respondent(session):
    """Someone who answers surveys, and who therefore holds a job on the floor.

    The job is what grants the right to answer now, so an account with no job cannot
    answer anything, including a survey aimed at everyone. That is the rule working
    rather than a fixture detail: an account belonging to nobody on any ladder is not
    part of any audience.
    """
    user = User(
        email="respondent@test.dev",
        display_name="Test Respondent",
        function=Function.production,
        band=Band.operative,
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def ungrouped_respondent(session):
    """Someone with an account and no job on any ladder, for the refusal path."""
    user = User(email="ungrouped@test.dev", display_name="Ungrouped")
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def published_yes_no(session, author):
    """A published survey whose first question is yes/no and permits follow-ups.

    Its own fixture because the interesting case is a probe hanging off a question
    whose type cannot express prose: that is where a real run recorded `true` against
    "could you describe the issues you've encountered?".
    """
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Support check",
            questions=[
                QuestionInput(
                    text="Have you encountered any issues with our AI product?",
                    answer_type=AnswerType.yes_no,
                    follow_up_policy=FollowUpPolicy.when_unclear,
                ),
                QuestionInput(text="Rate the support you received", answer_type=AnswerType.rating),
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    return template


@pytest_asyncio.fixture
async def published_multi_select(session, author):
    """A published survey whose first question is a multi-select with write-ins allowed.

    Its own fixture because this is where a probe most often re-asks the author's own
    question: a long option list is read out a few at a time, and the answer to "was that
    at unloading or at the checks?" is a selection from the same list the scripted answer
    came from. Modelled on the live survey where that answer was filed as an uncounted
    follow-up and the chart disagreed with its own transcript.
    """
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Chill chain check",
            questions=[
                QuestionInput(
                    text="Where have you seen product above the chill specification?",
                    answer_type=AnswerType.multi_select,
                    options=[
                        "Vehicle unloading at intake",
                        "Intake checks before booking in",
                        "Marshalling for dispatch",
                    ],
                    allow_other=True,
                    follow_up_policy=FollowUpPolicy.when_unclear,
                ),
                QuestionInput(text="Rate the chill chain", answer_type=AnswerType.rating),
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    return template


@pytest_asyncio.fixture
async def published(session, author):
    """A published two-question survey: q0 permits follow-ups, q1 is a rating that does not."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Onboarding check-in",
            questions=[
                QuestionInput(
                    text="What's your role?",
                    answer_type=AnswerType.short_text,
                    follow_up_policy=FollowUpPolicy.when_unclear,
                ),
                QuestionInput(
                    text="Rate your onboarding",
                    answer_type=AnswerType.rating,
                    follow_up_policy=FollowUpPolicy.never,
                ),
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    return template


@pytest_asyncio.fixture
async def other_respondent(session):
    """A second respondent, for proving one cannot resume another's run.

    On a different rung from the first, so that a test which needs two people who are
    both on the floor gets them, and a test about audience boundaries has one to hand.
    """
    user = User(
        email="second@test.dev",
        display_name="Second Respondent",
        function=Function.production,
        band=Band.line_leader,
    )
    session.add(user)
    await session.flush()
    return user
