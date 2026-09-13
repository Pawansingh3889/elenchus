"""A run can be pinned to a conduct prompt version, for evaluations that compare versions.

The pin must reach everything the active version reaches: the text the model is briefed
with, the version stamped on the reply, and the spans. A pin that changed the briefing but
left the stamp on the active version would record one prompt's behaviour under another's
name, which is the one mistake a comparison cannot survive.
"""

import pytest

from app.conduct.engine import PROMPT_VERSION, ConductEngine
from app.llm.prompts import PromptNotFoundError, load_prompt
from app.runs.enums import MessageRole
from app.trace.enums import SpanKind
from app.trace.repository import SpanRepository
from tests.fakes import FakeLLM, move_on, record

PINNED = "conduct_v7"


async def test_a_pinned_run_is_briefed_stamped_and_traced_with_the_pinned_version(
    session, respondent, published
):
    assert PINNED != PROMPT_VERSION, "the pin must differ from the default to prove anything"
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."), serves_as=(1, "gpt-5.5"))
    run = await ConductEngine(session, llm=llm, prompt_version=PINNED).handle_message(
        run.id, "line lead", respondent
    )

    assert llm.briefings[0].startswith(load_prompt(PINNED))
    replies = [m for m in run.messages if m.role is MessageRole.assistant and m.prompt_version]
    assert replies and all(m.prompt_version == PINNED for m in replies)
    spans = await SpanRepository(session).for_run(run.id)
    assert {s.prompt_version for s in spans if s.kind is SpanKind.attempt} == {PINNED}


async def test_an_unknown_pinned_version_fails_before_any_model_is_asked(
    session, respondent, published
):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    run_id = run.id
    llm = FakeLLM(record("Line lead"))
    with pytest.raises(PromptNotFoundError):
        await ConductEngine(session, llm=llm, prompt_version="conduct_v999").handle_message(
            run_id, "line lead", respondent
        )
    assert llm.calls == 0
