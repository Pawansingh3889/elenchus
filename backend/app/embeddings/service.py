"""Vectors cached by text hash, and the answer map, themes and near duplicates over them.

Admins only, asked in every method: these reads return what respondents typed.
"""

import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin
from app.config import get_settings
from app.embeddings.math import cosine, kmeans, near_duplicates, project_2d
from app.embeddings.models import EmbeddingVector
from app.embeddings.repository import EmbeddingRepository
from app.embeddings.schemas import (
    AnswerMap,
    DuplicatePair,
    DuplicateReport,
    EmbeddingCost,
    GroundingJudged,
    GroundingReport,
    MapPoint,
    MapQuestion,
    SweepPoint,
    Theme,
    ThemeQuestion,
    ThemeReport,
)
from app.errors import ForbiddenError, NotFoundError
from app.llm import ledger
from app.llm.client import EmbedderProtocol
from app.llm.factory import get_embedder
from app.users.models import User

ADMINS_ONLY = "The embedding lens is for administrators: it shows what respondents typed."
DUPLICATE_THRESHOLD = 0.95
MEASUREMENT = Path(__file__).parent / "measurements" / "grounding.json"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _recorded(value: dict[str, Any]) -> str:
    if isinstance(value.get("option"), str):
        return str(value["option"])
    if isinstance(value.get("options"), list):
        return ", ".join(str(o) for o in value["options"]) or "nothing chosen"
    if "unanswerable" in value:
        return "unanswerable"
    if isinstance(value.get("yes_no"), bool):
        return "yes" if value["yes_no"] else "no"
    if "rating" in value:
        return f"rating {value['rating']}"
    if "text" in value or "other" in value:
        return "free text"
    return ", ".join(sorted(value)) or "empty"


def _free_text(value: dict[str, Any]) -> str | None:
    for key in ("text", "other", "unanswerable"):
        if isinstance(value.get(key), str) and value[key].strip():
            return str(value[key]).strip()
    return None


class EmbeddingService:
    def __init__(self, session: AsyncSession, embedder: EmbedderProtocol | None = None) -> None:
        self.session = session
        self.repo = EmbeddingRepository(session)
        self._embedder = embedder
        # What this service has spent, across every vectors() call one report makes.
        self._asked: set[str] = set()
        self._fetched: set[str] = set()
        self._spend = ledger.Spend()
        self._embedding_ms = 0

    @property
    def embedder(self) -> EmbedderProtocol:
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    async def vectors(self, texts: list[str]) -> list[list[float]]:
        """One vector per text, from the cache where it can, one call for the rest."""
        model = self.embedder.model
        keys = [digest(t) for t in texts]
        known = await self.repo.cached(model, sorted(set(keys)))
        missing = sorted({t for t, k in zip(texts, keys, strict=True) if k not in known})
        self._asked.update(keys)
        if missing:
            started = time.monotonic()
            with ledger.measuring() as spend:
                fresh = await self.embedder.embed(missing)
            self._embedding_ms += int((time.monotonic() - started) * 1000)
            self._spend.calls += spend.calls
            self._spend.prompt_tokens += spend.prompt_tokens
            self._spend.cost_usd += spend.cost_usd
            self._spend.unmetered_calls += spend.unmetered_calls
            self._fetched.update(digest(t) for t in missing)
            rows = []
            for text, vector in zip(missing, fresh, strict=True):
                known[digest(text)] = vector
                rows.append(
                    EmbeddingVector(
                        digest=digest(text), model=model, dimensions=len(vector), vector=vector
                    )
                )
            await self.repo.store(rows)
            await self.session.commit()
        return [known[k] for k in keys]

    def _cost(self) -> EmbeddingCost:
        return EmbeddingCost(
            texts=len(self._asked),
            cached=len(self._asked - self._fetched),
            embedded=len(self._fetched),
            calls=self._spend.calls,
            prompt_tokens=self._spend.prompt_tokens,
            cost_usd=round(self._spend.cost_usd, ledger.COST_PLACES),
            unmetered_calls=self._spend.unmetered_calls,
            duration_ms=self._embedding_ms,
        )

    async def _title(self, survey_id: UUID) -> str:
        title = await self.repo.survey_title(survey_id)
        if title is None:
            raise NotFoundError("No survey with that id.")
        return title

    async def answer_map(self, viewer: User, survey_id: UUID) -> AnswerMap:
        """Each answer placed by the meaning of what the respondent said to produce it.

        An answer is paired with its run's latest respondent message before it was recorded,
        because answers do not store the message they came from. A follow-up answer and the
        scripted one before it can share a message; both are drawn, since both were recorded.
        """
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        title = await self._title(survey_id)
        messages: dict[UUID, list[Any]] = defaultdict(list)
        for row in await self.repo.respondent_messages(survey_id):
            messages[row.run_id].append(row)
        by_question: dict[int, list[tuple[Any, Any, str]]] = defaultdict(list)
        questions: dict[int, Any] = {}
        unplaced = 0
        for answer, question in await self.repo.answers(survey_id):
            before = [m for m in messages[answer.run_id] if m.created_at <= answer.answered_at]
            if not before:
                unplaced += 1
                continue
            by_question[question.position].append((answer, question, before[-1].content))
            questions[question.position] = question
        vectors = await self.vectors(
            sorted({said for items in by_question.values() for _, _, said in items})
        )
        lookup = dict(
            zip(
                sorted({said for items in by_question.values() for _, _, said in items}),
                vectors,
                strict=True,
            )
        )
        result = []
        for position in sorted(by_question):
            items = by_question[position]
            points = project_2d([lookup[said] for _, _, said in items])
            rows = []
            for index, ((answer, _, said), (x, y)) in enumerate(zip(items, points, strict=True)):
                ranked = sorted(
                    (j for j in range(len(items)) if j != index),
                    key=lambda j: -cosine(lookup[said], lookup[items[j][2]]),
                )
                rows.append(
                    MapPoint(
                        answer_id=answer.id,
                        run_id=answer.run_id,
                        kind=answer.kind.value,
                        recorded=_recorded(answer.value),
                        said=said,
                        x=x,
                        y=y,
                        neighbours=[items[j][0].id for j in ranked[:3]],
                    )
                )
            q = questions[position]
            result.append(
                MapQuestion(
                    position=position, text=q.text, answer_type=q.answer_type.value, points=rows
                )
            )
        return AnswerMap(
            survey_title=title,
            model=self.embedder.model,
            unplaced=unplaced,
            questions=result,
            cost=self._cost(),
        )

    async def themes(self, viewer: User, survey_id: UUID) -> ThemeReport:
        """Free-text answers per question, grouped by meaning, largest group first."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        title = await self._title(survey_id)
        texts: dict[int, list[tuple[str, UUID]]] = defaultdict(list)
        questions: dict[int, Any] = {}
        for answer, question in await self.repo.answers(survey_id):
            text = _free_text(answer.value)
            if text is not None:
                texts[question.position].append((text, answer.run_id))
                questions[question.position] = question
        result = []
        for position in sorted(texts):
            items = texts[position]
            vectors = await self.vectors([t for t, _ in items])
            # Roughly one theme per three answers, never more than four: a theme of one is a
            # quote, and more than four groups over a survey's answers is noise.
            k = 1 if len(items) < 4 else min(4, len(items) // 3)
            groups = kmeans(vectors, k)
            themes = []
            for group in sorted(set(groups)):
                members = [i for i, g in enumerate(groups) if g == group]
                dims = len(vectors[0])
                centre = [sum(vectors[i][d] for i in members) / len(members) for d in range(dims)]
                if math.sqrt(sum(c * c for c in centre)) == 0:
                    representative = items[members[0]][0]
                else:
                    representative = items[max(members, key=lambda i: cosine(vectors[i], centre))][
                        0
                    ]
                themes.append(
                    Theme(
                        size=len(members),
                        runs=len({items[i][1] for i in members}),
                        representative=representative,
                        members=[items[i][0] for i in members],
                    )
                )
            q = questions[position]
            result.append(
                ThemeQuestion(
                    position=position,
                    text=q.text,
                    texts=len(items),
                    themes=sorted(themes, key=lambda t: -t.size),
                )
            )
        return ThemeReport(
            survey_title=title, model=self.embedder.model, questions=result, cost=self._cost()
        )

    async def duplicates(self, viewer: User, survey_id: UUID) -> DuplicateReport:
        """Near-identical things said in different runs, where copied answers show up."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        title = await self._title(survey_id)
        seen: dict[tuple[str, UUID], None] = {}
        for row in await self.repo.respondent_messages(survey_id):
            if len(row.content.split()) >= 3:  # "yes" matching "yes" is not a finding
                seen[(row.content, row.run_id)] = None
        items = list(seen)
        vectors = await self.vectors([text for text, _ in items])
        pairs = [
            DuplicatePair(
                first=items[i][0],
                second=items[j][0],
                first_run=items[i][1],
                second_run=items[j][1],
                similarity=round(score, 4),
            )
            for i, j, score in near_duplicates(vectors, DUPLICATE_THRESHOLD)
            if items[i][1] != items[j][1]
        ]
        return DuplicateReport(
            survey_title=title,
            model=self.embedder.model,
            threshold=DUPLICATE_THRESHOLD,
            texts=len(items),
            pairs=pairs,
            cost=self._cost(),
        )

    async def grounding(self, viewer: User) -> GroundingReport:
        """The committed measurement, beside the deployment's live grounding settings."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        if not MEASUREMENT.exists():
            raise NotFoundError("No grounding measurement has been run yet.")
        raw = json.loads(MEASUREMENT.read_text(encoding="utf-8"))
        settings = get_settings()
        at = raw["at_recommended"]
        room = raw["headroom"]
        return GroundingReport(
            measured_at=raw["measured_at"],
            model=raw["model"],
            pairs=raw["pairs"],
            negatives=raw["negatives"],
            word_false_accepts=raw["word_check"]["false_accepts"],
            word_false_refusals=raw["word_check"]["false_refusals"],
            recommended_margin=raw["recommended_margin"],
            at_recommended_false_accepts=None if at is None else at["false_accepts"],
            at_recommended_false_refusals=None if at is None else at["false_refusals"],
            highest_negative_margin=None if room is None else room["highest_negative"],
            lowest_positive_margin=None if room is None else room["lowest_positive"],
            sweep=[SweepPoint(**row) for row in raw["sweep"]],
            judged=[GroundingJudged(**item) for item in raw["judged"]],
            semantic_enabled=settings.grounding_semantic_enabled,
            configured_margin=settings.grounding_similarity_margin,
        )
