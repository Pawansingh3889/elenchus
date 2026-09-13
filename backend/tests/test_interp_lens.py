"""The interpretability lens: captured calls listed, read once, priced, and private.

The interp service is faked at its transport, as the LLM is at its client, so the suite
runs without a model. What is tested is what the backend owes: that an analysis explains
the tool the hosted model actually called, runs once, lands in the ledger and the table,
and goes when the run goes.
"""

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

from app.conduct.engine import ConductEngine
from app.config import get_settings
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.interp.repository import InterpRepository
from app.interp.schemas import Analysis
from app.interp.service import InterpService
from app.interp.transport import InterpNotConfiguredError, InterpTransport, InterpUnavailableError
from app.trace.enums import SpanKind
from app.trace.models import LLMSpan
from app.users.models import Band, Function, User
from tests.fakes import FakeLLM, move_on, record


def _analysis(names: list[str], pick: str) -> dict:
    others = (1.0 - 0.8) / max(len(names) - 1, 1)
    probabilities = {name: (0.8 if name == pick else others) for name in names}
    return Analysis.model_validate(
        {
            "model": "Qwen/Qwen3-0.6B",
            "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
            "device": "cpu",
            "dtype": "float32",
            "prompt_tokens": 120,
            "sections": [
                {
                    "key": "system",
                    "label": "System prompt",
                    "kind": "system",
                    "role": "system",
                    "tokens": 100,
                },
                {
                    "key": "template",
                    "label": "Chat template",
                    "kind": "template",
                    "role": None,
                    "tokens": 20,
                },
            ],
            "calls_a_tool": 0.9,
            "tools": [
                {"name": name, "logprob": -1.0, "probability": p}
                for name, p in probabilities.items()
            ],
            "pick": pick,
            "layers": [
                {"layer": 1, "norm": 10.0, "tool_probabilities": probabilities, "top_token": pick}
            ],
            "attention": [{"layer": 1, "shares": {"system": 0.7, "template": 0.3}}],
            "attended_tokens": [],
            "timings": {
                "render_ms": 1,
                "read_ms": 2,
                "tools_ms": 3,
                "total_ms": 6,
            },
        }
    ).model_dump(mode="json")


class FakeTransport:
    """Answers like the service, picking a fixed tool, and records what it was sent."""

    def __init__(self, pick: str = "record_answer") -> None:
        self.pick = pick
        self.payloads: list[dict] = []

    async def health(self) -> dict:
        return {"model": "Qwen/Qwen3-0.6B", "revision": "c1899de", "device": "cpu", "ready": True}

    async def analyse(self, payload: dict) -> dict:
        self.payloads.append(payload)
        names = [tool["function"]["name"] for tool in payload["tools"]]
        return _analysis(names, self.pick)

    async def attribute(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {
            "model": "Qwen/Qwen3-0.6B",
            "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
            "device": "cpu",
            "prompt_tokens": 120,
            "attribution": {
                "target": payload["target_tool"],
                "sections": {"system": {"positive": 0.6, "negative": -0.4}},
                "tokens": [],
                "respondent_words": [{"text": "lead", "score": 0.1}],
            },
            "render_ms": 1,
            "attribution_ms": 40,
            "total_ms": 41,
        }


@pytest_asyncio.fixture
async def admin(session):
    user = User(
        email="interp-admin@plant.dev",
        display_name="Interp Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


async def _traced_turn(session, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."), serves_as=(1, "gpt-5.5"))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    return run.id


def _switched_off(monkeypatch) -> None:
    patched = get_settings().model_copy(update={"interp_enabled": False})
    monkeypatch.setattr("app.interp.service.get_settings", lambda: patched)
    monkeypatch.setattr("app.interp.transport.get_settings", lambda: patched)


async def test_captured_calls_are_listed_with_what_the_hosted_model_picked(
    session, respondent, published, admin
):
    await _traced_turn(session, respondent, published)
    asks = await InterpService(session, FakeTransport()).asks(admin, None, None)

    assert [ask.hosted_pick for ask in asks] == ["record_answer", "move_on"]
    assert [ask.outcome for ask in asks] == ["accepted", "accepted"]
    assert all(ask.hosted_model == "gpt-5.5" and not ask.analysed for ask in asks)
    assert "record_answer" in asks[0].tools_offered


async def test_an_analysis_explains_the_hosted_pick_runs_once_and_is_priced(
    session, respondent, published, admin
):
    await _traced_turn(session, respondent, published)
    transport = FakeTransport()
    service = InterpService(session, transport)
    first = (await service.asks(admin, None, None))[0]

    stored = await service.analyse(admin, first.span_id)

    (sent,) = transport.payloads
    # A reading needs no target; the hosted pick is kept for the attribution that may follow.
    assert "target_tool" not in sent
    assert sent["messages"][0]["role"] == "system"
    assert stored.analysis.pick == "record_answer" and stored.target_tool == "record_answer"
    assert stored.attribution is None
    # A local reading is priced by the clock, never left as unknown.
    assert stored.cost_usd is not None and stored.hosted_model == "gpt-5.5"

    again = await InterpService(session, transport).analyse(admin, first.span_id)
    assert len(transport.payloads) == 1 and again.analysed_at == stored.analysed_at
    listed = (await service.asks(admin, None, None))[0]
    assert listed.analysed and listed.agrees is True
    assert listed.qwen_probability_of_hosted_pick == pytest.approx(0.8)


async def test_an_attribution_follows_a_reading_explains_the_hosted_pick_and_runs_once(
    session, respondent, published, admin
):
    await _traced_turn(session, respondent, published)
    transport = FakeTransport()
    service = InterpService(session, transport)
    first = (await service.asks(admin, None, None))[0]
    with pytest.raises(ConflictError, match="Read this call"):
        await service.attribute(admin, first.span_id)

    await service.analyse(admin, first.span_id)
    stored = await service.attribute(admin, first.span_id)

    assert transport.payloads[-1]["target_tool"] == "record_answer"
    assert stored.attribution is not None
    assert stored.attribution.result.attribution.target == "record_answer"
    assert stored.attribution.cost_usd is not None
    await service.attribute(admin, first.span_id)
    assert len(transport.payloads) == 2
    listed = (await service.asks(admin, None, None))[0]
    assert listed.attributed and listed.attribution_ms is not None


async def test_a_call_with_no_captured_prompt_cannot_be_read(session, admin):
    service = InterpService(session, FakeTransport())
    with pytest.raises(NotFoundError, match="No model call"):
        await service.analyse(admin, uuid4())
    uncaptured = LLMSpan(
        id=uuid4(),
        kind=SpanKind.attempt,
        name="tool_turn",
        started_at=datetime.now(UTC),
        duration_ms=10,
        attrs={},
    )
    session.add(uncaptured)
    await session.commit()
    with pytest.raises(NotFoundError, match="no captured prompt"):
        await service.analyse(admin, uncaptured.id)


async def test_switched_off_the_lens_says_so_rather_than_failing(
    session, respondent, published, admin, monkeypatch
):
    _switched_off(monkeypatch)
    await _traced_turn(session, respondent, published)
    service = InterpService(session)
    status = await service.status(admin)
    assert (status.enabled, status.reachable) == (False, False)
    first = (await service.asks(admin, None, None))[0]
    with pytest.raises(InterpNotConfiguredError):
        await service.analyse(admin, first.span_id)


async def test_withdrawing_a_run_deletes_what_was_read_from_it(
    session, respondent, published, admin
):
    run_id = await _traced_turn(session, respondent, published)
    service = InterpService(session, FakeTransport())
    first = (await service.asks(admin, None, None))[0]
    await service.analyse(admin, first.span_id)

    await ConductEngine(session, llm=FakeLLM()).delete_run(run_id, respondent)

    assert await InterpRepository(session).get(first.span_id) is None


async def test_only_admins_read_the_interpretability_lens(session, author):
    service = InterpService(session, FakeTransport())
    with pytest.raises(ForbiddenError):
        await service.status(author)
    with pytest.raises(ForbiddenError):
        await service.asks(author, None, None)
    with pytest.raises(ForbiddenError):
        await service.analysis(author, uuid4())
    with pytest.raises(ForbiddenError):
        await service.analyse(author, uuid4())
    with pytest.raises(ForbiddenError):
        await service.attribute(author, uuid4())


# ------------------------------------------------------------------ the transport


def _transport(handler) -> InterpTransport:
    return InterpTransport("http://interp.local:8765", "t" * 24, 5, httpx.MockTransport(handler))


async def test_each_way_the_service_fails_becomes_its_own_error():
    def refused(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(InterpUnavailableError, match="could not be reached"):
        await _transport(refused).analyse({})
    with pytest.raises(InterpUnavailableError, match="refused the token"):
        await _transport(lambda r: httpx.Response(401, json={"detail": "no"})).analyse({})
    with pytest.raises(ValidationError, match="refused this prompt: too long"):
        await _transport(lambda r: httpx.Response(413, json={"detail": "too long"})).analyse({})

    seen = {}

    def ok(request):
        seen["auth"] = request.headers["Authorization"]
        return httpx.Response(200, json={"pick": "move_on"})

    assert await _transport(ok).analyse({}) == {"pick": "move_on"}
    assert seen["auth"] == "Bearer " + "t" * 24
