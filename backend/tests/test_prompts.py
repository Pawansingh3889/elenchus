"""Conduct prompt versions: saved as new versions, activated from the next turn, never edited.

Each rule is tested by trying to break it: an identical save, an empty one, a name from
another family, a non-administrator, and a turn that must run on exactly the text and name
that were activated.
"""

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.conduct.engine import PROMPT_VERSION, ConductEngine
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.llm.prompts import load_prompt
from app.prompts.schemas import PromptVersionWrite
from app.prompts.service import PromptAdminService
from app.trace.repository import SpanRepository
from app.users.models import Band, Function, User
from tests.fakes import FakeLLM, move_on, record


@pytest_asyncio.fixture
async def admin(session):
    user = User(
        email="prompt-admin@plant.dev",
        display_name="Prompt Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


async def test_the_code_default_is_live_until_someone_activates_another(session, admin):
    family = await PromptAdminService(session).family(admin, "conduct")
    assert family.active == family.default == PROMPT_VERSION
    assert PROMPT_VERSION in [v.name for v in family.versions if v.source == "file"]
    assert [v.name for v in family.versions if v.active] == [PROMPT_VERSION]


async def test_saving_adds_the_next_version_without_activating_it(session, admin):
    prompts = PromptAdminService(session)
    first = await prompts.save(admin, "conduct", "Ask one question at a time. v-next", "shorter")
    second = await prompts.save(admin, "conduct", "Ask one question at a time. v-after", None)

    saved = [v for v in second.versions if v.source == "database"]
    assert [v.name for v in saved] == ["conduct_v9", "conduct_v10"]
    assert saved[0].note == "shorter" and saved[0].created_by_name == "Prompt Admin"
    assert first.active == second.active == PROMPT_VERSION


async def test_an_identical_save_is_refused(session, admin):
    prompts = PromptAdminService(session)
    with pytest.raises(ConflictError, match="identical to conduct_v8"):
        await prompts.save(admin, "conduct", load_prompt(PROMPT_VERSION), None)


def test_an_empty_prompt_never_reaches_the_service():
    with pytest.raises(PydanticValidationError):
        PromptVersionWrite(body="")


async def test_a_turn_runs_on_the_activated_text_and_records_its_name(
    session, admin, respondent, published
):
    prompts = PromptAdminService(session)
    await prompts.save(admin, "conduct", "MARKER-PROMPT: ask one question at a time.", None)
    await prompts.activate(admin, "conduct", "conduct_v9")

    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    assert all(b.startswith("MARKER-PROMPT") for b in llm.briefings)
    assert run.messages[-1].prompt_version == "conduct_v9"
    spans = await SpanRepository(session).for_run(run.id)
    assert {s.prompt_version for s in spans} == {"conduct_v9"}


async def test_rolling_back_is_activating_an_older_version(session, admin, respondent, published):
    prompts = PromptAdminService(session)
    await prompts.save(admin, "conduct", "MARKER-PROMPT: new wording.", None)
    await prompts.activate(admin, "conduct", "conduct_v9")
    family = await prompts.activate(admin, "conduct", PROMPT_VERSION)
    assert family.active == PROMPT_VERSION

    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    assert all(b.startswith(load_prompt(PROMPT_VERSION)[:40]) for b in llm.briefings)


async def test_only_known_conduct_versions_can_be_activated(session, admin):
    prompts = PromptAdminService(session)
    with pytest.raises(NotFoundError):
        await prompts.activate(admin, "conduct", "conduct_v99")
    with pytest.raises(NotFoundError):
        await prompts.activate(admin, "conduct", "generate_template_v5")
    with pytest.raises(NotFoundError, match="only conduct"):
        await prompts.family(admin, "generate_template")


async def test_only_admins_touch_prompts(session, author):
    prompts = PromptAdminService(session)
    with pytest.raises(ForbiddenError):
        await prompts.family(author, "conduct")
    with pytest.raises(ForbiddenError):
        await prompts.save(author, "conduct", "anything", None)
    with pytest.raises(ForbiddenError):
        await prompts.activate(author, "conduct", PROMPT_VERSION)
