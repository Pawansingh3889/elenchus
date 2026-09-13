"""The embedding lens: vectors cached by hash, what each report spent, and who may read it."""

import pytest
import pytest_asyncio

from app.conduct.engine import ConductEngine
from app.embeddings.models import EmbeddingVector
from app.embeddings.repository import EmbeddingRepository
from app.embeddings.service import EmbeddingService, digest
from app.errors import ForbiddenError
from app.users.models import Band, Function, User
from tests.fakes import FakeEmbedder, FakeLLM, move_on, record


@pytest_asyncio.fixture
async def admin(session):
    user = User(
        email="embed-admin@plant.dev",
        display_name="Embed Admin",
        function=Function.it,
        band=Band.operative,
    )
    session.add(user)
    await session.commit()
    return user


# ------------------------------------------------------------------ the lens


async def test_vectors_are_cached_so_a_text_is_embedded_once(session):
    embedder = FakeEmbedder()
    service = EmbeddingService(session, embedder=embedder)
    first = await service.vectors(["alpha beta", "gamma"])
    second = await service.vectors(["gamma", "alpha beta"])
    assert first == [second[1], second[0]]
    assert embedder.calls == [["alpha beta", "gamma"]]


async def test_the_answer_map_pairs_each_answer_with_what_was_said(
    session, respondent, published, admin
):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead on nights", respondent)

    report = await EmbeddingService(session, embedder=FakeEmbedder()).answer_map(
        admin, published.id
    )

    (question,) = report.questions
    (point,) = question.points
    assert point.said == "line lead on nights"
    assert point.recorded == "free text"
    assert point.neighbours == []


async def test_near_duplicates_only_pair_different_runs(
    session, respondent, other_respondent, published, admin
):
    for who in (respondent, other_respondent):
        run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, who)
        llm = FakeLLM(record("Line lead"), move_on("Thanks."))
        await ConductEngine(session, llm=llm).handle_message(
            run.id, "i am a line lead on nights", who
        )

    report = await EmbeddingService(session, embedder=FakeEmbedder()).duplicates(
        admin, published.id
    )

    (pair,) = report.pairs
    assert pair.first_run != pair.second_run
    assert pair.similarity == pytest.approx(1.0)


async def test_only_admins_read_the_embedding_lens(session, published, author):
    service = EmbeddingService(session, embedder=FakeEmbedder())
    with pytest.raises(ForbiddenError):
        await service.answer_map(author, published.id)
    with pytest.raises(ForbiddenError):
        await service.themes(author, published.id)
    with pytest.raises(ForbiddenError):
        await service.duplicates(author, published.id)


async def test_the_cost_block_counts_what_was_embedded_and_what_the_cache_served(
    session, respondent, published, admin
):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on("Thanks."))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead on nights", respondent)

    first = await EmbeddingService(session, embedder=FakeEmbedder()).answer_map(admin, published.id)
    again = await EmbeddingService(session, embedder=FakeEmbedder()).answer_map(admin, published.id)

    assert (first.cost.texts, first.cost.embedded, first.cost.cached) == (1, 1, 0)
    # The second view reads the cache: nothing embedded, nothing spent, no time taken.
    assert (again.cost.texts, again.cost.embedded, again.cost.cached) == (1, 0, 1)
    assert again.cost.cost_usd == 0 and again.cost.duration_ms == 0


async def test_storing_a_vector_another_request_already_stored_is_not_an_error(session):
    repo = EmbeddingRepository(session)
    row = {"digest": digest("same text"), "model": "m", "dimensions": 2, "vector": [1.0, 0.0]}
    await repo.store([EmbeddingVector(**row)])
    await session.commit()
    # A concurrent view embedded the same text first; the unique key must not fail this one.
    await repo.store([EmbeddingVector(**row)])
    await session.commit()
    assert list(await repo.cached("m", [digest("same text")])) == [digest("same text")]
