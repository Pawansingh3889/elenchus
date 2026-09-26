"""Every query on embedding vectors, and on the answers and messages the lens embeds."""

from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.models import EmbeddingVector
from app.runs.enums import MessageRole
from app.runs.models import Answer, RunMessage, SurveyRun
from app.templates.models import SurveyQuestion, SurveyTemplate


class EmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def cached(self, model: str, digests: list[str]) -> dict[str, list[float]]:
        if not digests:
            return {}
        stmt = select(EmbeddingVector.digest, EmbeddingVector.vector).where(
            EmbeddingVector.model == model, EmbeddingVector.digest.in_(digests)
        )
        return {digest: list(vector) for digest, vector in (await self.session.execute(stmt)).all()}

    async def store(self, rows: list[EmbeddingVector]) -> None:
        """Insert vectors, leaving alone any that another request stored first.

        Two views of a fresh survey can embed the same text at the same moment. The unique
        key on digest and model would then fail the slower one for storing exactly what is
        already there, so a conflict is skipped rather than raised: the stored vector is the
        same text through the same model.
        """
        if not rows:
            return
        stmt = (
            insert(EmbeddingVector)
            .values(
                [
                    {
                        "digest": row.digest,
                        "model": row.model,
                        "dimensions": row.dimensions,
                        "vector": row.vector,
                    }
                    for row in rows
                ]
            )
            .on_conflict_do_nothing(index_elements=["workspace_id", "digest", "model"])
        )
        await self.session.execute(stmt)

    async def delete_digests(self, digests: list[str]) -> None:
        """Every model's vector for these texts. Explicit, as withdrawal requires."""
        if digests:
            await self.session.execute(
                delete(EmbeddingVector).where(EmbeddingVector.digest.in_(digests))
            )

    async def survey_title(self, survey_id: UUID) -> str | None:
        stmt = select(SurveyTemplate.title).where(SurveyTemplate.id == survey_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def answers(self, survey_id: UUID) -> list[Row[tuple[Answer, SurveyQuestion]]]:
        """Every answer to the survey with its question, oldest first."""
        stmt = (
            select(Answer, SurveyQuestion)
            .join(SurveyRun, SurveyRun.id == Answer.run_id)
            .join(SurveyQuestion, SurveyQuestion.id == Answer.question_id)
            .where(SurveyRun.template_id == survey_id)
            .order_by(Answer.answered_at)
        )
        return list((await self.session.execute(stmt)).all())

    async def respondent_messages(self, survey_id: UUID) -> list[Row[Any]]:
        """What respondents typed in this survey's runs, oldest first."""
        stmt = (
            select(RunMessage.run_id, RunMessage.content, RunMessage.created_at)
            .join(SurveyRun, SurveyRun.id == RunMessage.run_id)
            .where(SurveyRun.template_id == survey_id, RunMessage.role == MessageRole.user)
            .order_by(RunMessage.created_at)
        )
        return list((await self.session.execute(stmt)).all())

    async def run_texts(self, run_id: UUID) -> list[str]:
        """Everything a run holds that could have been embedded: messages and answer values."""
        messages = select(RunMessage.content).where(
            RunMessage.run_id == run_id, RunMessage.role == MessageRole.user
        )
        values = select(Answer.value).where(Answer.run_id == run_id)
        texts = [content for (content,) in (await self.session.execute(messages)).all()]
        for (value,) in (await self.session.execute(values)).all():
            texts.extend(str(v) for v in value.values() if isinstance(v, str))
        return texts
