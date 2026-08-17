"""Template business logic: the draft lifecycle and publishing.

Publishing freezes the current draft into a new immutable version (n+1). The draft
keeps evolving afterwards; respondents only ever see published versions.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin_by_config, may_answer, may_edit, may_list, reads_all_surveys
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.templates.enums import TemplateStatus
from app.templates.estimate import estimated_minutes
from app.templates.models import SurveyQuestion, SurveyTemplate
from app.templates.reading import questions_of
from app.templates.repository import TemplateRepository
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.users.models import User
from app.users.repository import UserRepository

logger = logging.getLogger("app.templates")


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TemplateRepository(session)
        # Departments and colleagues live in the users domain, and the access rules are
        # pure functions that cannot go and fetch them. Same pattern as RunService.
        self.users = UserRepository(session)

    async def create_draft(self, data: TemplateCreate, author: User) -> SurveyTemplate:
        template = SurveyTemplate(
            title=data.title,
            description=data.description,
            audience=data.audience,
            # Carried with the audience, never separately: the pair is validated together
            # on the schema and enforced together by a check constraint, and dropping this
            # line writes a survey aimed at a person it does not name.
            audience_user_id=data.audience_user_id,
            setting=data.setting,
            created_by=author.id,
        )
        template.questions = [_to_question(q, i) for i, q in enumerate(data.questions)]
        self.repo.add(template)
        await self.session.commit()
        return await self._get_or_404(template.id, author)

    async def get_draft(self, template_id: UUID, author: User) -> SurveyTemplate:
        return await self._get_or_404(template_id, author)

    async def list_drafts(
        self, status: TemplateStatus | None, author: User
    ) -> list[tuple[SurveyTemplate, int]]:
        """An author's workspace, and their function's.

        Scoped in the query to the author plus everyone in their function, then filtered
        again here so the one rule decides rather than the query agreeing with it by luck.
        The query has to be widened as well as the rule: a survey a colleague made is not
        in `created_by = me`, so no amount of filtering would have let it through. An
        executive's scope is every creator, for the same reason in the other direction:
        `reads_all_surveys` grants them the lot, and a query still scoped to their own
        function would silently show them a sliver of it."""
        admin = is_admin_by_config(author)
        functions = await self.users.functions_by_id()
        creators = (
            set(functions)
            if reads_all_surveys(author)
            else {author.id} | await self.users.ids_in_function(author.function)
        )
        return [
            row
            for row in await self.repo.list_summaries(status, created_by_in=creators)
            if may_list(
                author,
                row[0].audience,
                row[0].created_by,
                admin,
                target=row[0].audience_user_id,
                creator_function=functions.get(row[0].created_by),
            )
        ]

    async def list_published(self, user: User) -> list[tuple[SurveyTemplate, int, int, bool]]:
        """Every published survey this user may actually start, with the count and time
        estimate they will face. It used to read the published version rather than the
        evolving draft; with versions gone there is one set of questions, so the gap
        between what is advertised and what is asked closes by construction.

        Filtered by may_answer rather than may_list, because this list is an invitation:
        every row on it is something the reader is about to be offered a Start button for.
        Before audiences existed this method took no user at all and returned everything
        published, which is precisely the bug audiences were introduced to fix."""
        admin = is_admin_by_config(user)
        templates = await self.repo.list_published()
        # One query for the lot, not one per row. A survey this person has finished still
        # belongs on the list: hiding it looks like the survey disappeared, and the point
        # is to tell them they have already done it.
        answered = await self.repo.completed_by(user.id)
        return [
            (template, len(questions), estimated_minutes(questions), template.id in answered)
            for template in templates
            if may_answer(
                user,
                template.audience,
                template.created_by,
                admin,
                target=template.audience_user_id,
            )
            for questions in [questions_of(template)]
        ]

    async def update_draft(
        self, template_id: UUID, data: TemplateUpdate, author: User
    ) -> SurveyTemplate:
        template = await self._get_for_edit_or_404(template_id, author)
        # Frozen once published, wholly, not just its audience.
        #
        # This restores by a different route what dropping versions gave up. There, the
        # published copy was frozen and the draft went on evolving; here there is one
        # definition and publishing is what freezes it. Either way the property that
        # matters holds: nobody's answer is re-pointed at a question they were not asked,
        # and a survey collecting answers cannot change under the people giving them.
        #
        # A survey that needs different questions is a new survey, which also keeps the
        # two sets of answers apart instead of blending populations under one title.
        if template.status is not TemplateStatus.draft:
            raise ConflictError(
                "A published survey cannot be edited. Close it and publish a new one instead."
            )
        template.title = data.title
        template.description = data.description
        template.audience = data.audience
        template.audience_user_id = data.audience_user_id
        template.setting = data.setting
        # Full replace of questions covers add / edit / reorder / delete. Delete the
        # old rows first so the (template_id, position) unique constraint can't clash.
        template.questions.clear()
        await self.session.flush()
        for i, q in enumerate(data.questions):
            template.questions.append(_to_question(q, i))
        await self.session.commit()
        return await self._get_for_edit_or_404(template_id, author)

    async def delete_survey(self, template_id: UUID, author: User) -> None:
        """Erase a survey entirely: the survey, its questions, and nothing else.

        Permanent by design and by request, so this is deliberately narrow: it refuses
        the moment anybody has answered. A survey with responses holds the only copy of
        what those people said, and a click that destroys it is not something a backup
        undoes, because restoring brings back the whole database at a moment in time
        rather than one survey out of it. Closing is what retires a survey that has
        answers; deleting is for the ones that never collected any.

        The count is the gate rather than the status: a draft nobody could answer and a
        published survey nobody did are the same situation, and a closed survey with
        answers is still a record.
        """
        template = await self._get_for_edit_or_404(template_id, author)
        answered = await self.repo.run_count(template_id)
        if answered:
            raise ConflictError(
                f"{answered} "
                + ("person has" if answered == 1 else "people have")
                + " answered this survey, so it cannot be deleted. Close it instead."
            )
        await self.repo.delete(template)
        await self.session.commit()

    async def publish(self, template_id: UUID, author: User) -> SurveyTemplate:
        """Open this survey for answers.

        A status change, and nothing more. It used to freeze the draft into an immutable
        version, and dropping that was asked for directly on 16 Aug 2026: what it bought
        was that a published survey could not change under the people answering it, and
        what it cost was a second definition to keep in step. The cost of losing it is
        recorded in CLAUDE.md rather than left for a reader to discover, because from
        here an edit to a published survey changes the question earlier answers were
        given to, and each answer's own `question_text` is the only record of the wording
        it was asked under.

        `published_at` and `published_by` are set once, on the first publish. Re-opening
        a survey is not a new publication, and moving the date would rewrite when it went
        out.
        """
        template = await self._get_for_edit_or_404(template_id, author)
        if not template.questions:
            raise ConflictError("Cannot publish a template with no questions.")
        template.status = TemplateStatus.published
        if template.published_at is None:
            template.published_at = datetime.now(UTC)
            template.published_by = author.id
        await self.session.commit()
        # Re-read rather than refresh: a commit expires everything, and `refresh` brings
        # back the columns while leaving `questions` unloaded, which is both a lazy load
        # waiting to happen and a response body missing the questions it promises.
        return await self._get_for_edit_or_404(template_id, author)

    async def close(self, template_id: UUID, author: User) -> SurveyTemplate:
        """Stop this survey taking new answers. Runs already in progress are untouched.

        Only a published survey can be closed. Closing a draft would be closing something
        that never opened, and closing a closed one twice would move closed_at, which is
        the date an author will quote when they report the numbers.

        Nothing here reaches into the runs. The engine refuses to start a new one against
        a closed survey, and a conversation already under way finishes on its own terms:
        stopping mid-question would lose answers a respondent has already given, and for a
        chat that is a worse bargain than a final count that settles a few minutes late.
        """
        template = await self._get_for_edit_or_404(template_id, author)
        if template.status is not TemplateStatus.published:
            raise ConflictError(
                f"Only a published survey can be closed; this one is {template.status.value}."
            )
        template.status = TemplateStatus.closed
        template.closed_at = datetime.now(UTC)
        await self.session.commit()
        # Re-read rather than refresh: a commit expires everything, and `refresh` brings
        # back the columns while leaving `questions` unloaded, which is both a lazy load
        # waiting to happen and a response body missing the questions it promises.
        return await self._get_for_edit_or_404(template_id, author)

    async def _get_or_404(self, template_id: UUID, author: User) -> SurveyTemplate:
        template = await self.repo.get(template_id)
        if template is None:
            raise NotFoundError("Template not found.")
        # Someone else's template reads as absent rather than forbidden, so the API
        # can't be used to enumerate which ids exist. The rule itself lives in
        # app/access: this used to compare created_by here, which was the same rule
        # written in a second place and free to drift from the one the engine uses.
        functions = await self.users.functions_by_id()
        decision = may_list(
            author,
            template.audience,
            template.created_by,
            is_admin_by_config(author),
            target=template.audience_user_id,
            creator_function=functions.get(template.created_by),
        )
        if not decision:
            logger.info(
                "template hidden: template=%s user=%s reason=%s",
                template_id,
                author.id,
                decision.reason,
            )
            raise NotFoundError("Template not found.")
        return template

    async def _get_for_edit_or_404(self, template_id: UUID, author: User) -> SurveyTemplate:
        """The same fetch, asking whether this user may *change* the survey.

        Separate from `_get_or_404` because the two questions came apart the moment a
        department colleague could see somebody else's work. Every mutation used to reach
        for the listing rule, so widening that rule for reading widened it for writing at
        the same time, and a colleague could rename and publish a survey in another
        author's name without either of them noticing.

        Still a 404 rather than a 403 on refusal, but only after `_get_or_404` has already
        agreed the survey is visible: a colleague who can see it and cannot change it
        should be told it exists, so the refusal here is about the action, not the row.
        """
        template = await self._get_or_404(template_id, author)
        decision = may_edit(author, template.created_by, is_admin_by_config(author))
        if not decision:
            logger.info(
                "template edit refused: template=%s user=%s reason=%s",
                template_id,
                author.id,
                decision.reason,
            )
            raise ForbiddenError(decision.reason)
        return template


def _to_question(q: QuestionInput, position: int) -> SurveyQuestion:
    return SurveyQuestion(
        position=position,
        text=q.text,
        answer_type=q.answer_type,
        options=q.options,
        allow_other=q.allow_other,
        required=q.required,
        follow_up_policy=q.follow_up_policy,
        show_when=q.show_when.model_dump(mode="json") if q.show_when else None,
    )
