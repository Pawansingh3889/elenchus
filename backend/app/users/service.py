"""Account business logic: creating people, and changing what they are.

This is the screen-side of the job model. `role` used to be a stored column written by
the seed and then by this service; it is gone, and what an administrator writes now is
the job itself (function, band, hats). Who may author, who administers, and who is in
which audience all derive from that, so the form states facts about the org chart and
the rights follow.

The rules about which shapes of account are allowed live on the schemas, not here, because
they are properties of the row rather than of the transaction. What lives here is
everything that needs to look at the *rest* of the table: whether an address is taken, and
whether the caller is about to lock themselves out.
"""

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import in_audience, is_admin_by_config, may_author
from app.errors import ConflictError, NotFoundError
from app.templates.enums import SurveyAudience, TemplateStatus
from app.templates.repository import TemplateRepository
from app.users.models import AccountChange, User, UserHat
from app.users.repository import UserRepository
from app.users.schemas import (
    AccountChangeRead,
    AccountCreate,
    AccountImpact,
    AccountSnapshot,
    AccountUpdate,
    SurveyImpact,
)

logger = logging.getLogger("app.users")


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def reach_by_audience(self) -> dict[SurveyAudience, int]:
        """How many people each audience is, right now.

        Moved here from the results service the day the publish dialog started asking
        the same question, because "how many people is this audience" is a question
        about users and there must be one answer to it: the dashboard, the report and
        the publish confirmation now all read this number from this method, so they
        cannot drift apart.

        Live on purpose, and that is a recorded decision rather than an oversight: the
        audience of a survey is whoever holds the job *today*, so somebody hired on
        Tuesday is asked Monday's survey, and every denominator moves when a job does.
        The guardrails around that are the admin edit preview and the account audit
        log, not a frozen snapshot.

        The rule is asked, not paraphrased: `in_audience` is `may_answer` with the
        author and admin escape hatches shut, so this cannot drift from the rule that
        decides who may actually answer. Writing the same thing in SQL would be a second
        copy with nothing to catch it diverging.

        Every user is loaded and the predicate run per audience over them, which is one
        query and a few hundred comparisons for a plant's staff list, and the wrong
        shape at ten thousand users. The escape hatch when that day comes is one grouped
        query, asking the rule once per job shape instead of once per person. Author-side
        only, deliberately: nothing on the respondent path calls this, so the break-time
        burst never pays for it.
        """
        users = await self.repo.list_all()
        return {
            audience: sum(1 for user in users if in_audience(user, audience))
            # `person` is skipped: its reach is one by definition and depends on which
            # person, so a single entry here would be a number that is wrong for every
            # survey. The dashboard supplies it directly.
            for audience in SurveyAudience
            if audience is not SurveyAudience.person
        }

    async def create_account(self, data: AccountCreate, admin: User) -> User:
        """Create an account, stamped with the administrator who asked for it."""
        await self._refuse_taken_identifiers(data.email, data.microsoft_id, editing=None)
        user = User(
            email=data.email,
            display_name=data.display_name,
            function=data.function,
            band=data.band,
            microsoft_id=data.microsoft_id,
            created_by=admin.id,
            hat_rows=[UserHat(hat=h) for h in data.hats],
        )
        self.repo.add(user)
        # Flushed so the user id exists to be written into the audit row, and the row
        # rides the same commit: an account cannot exist without its "created" entry,
        # and a refused create leaves no entry behind.
        await self.session.flush()
        self._record(user, before=None, admin=admin)
        await self._commit_or_conflict()
        logger.info(
            "account created: user=%s job=%s/%s by=%s",
            user.id,
            data.function.value,
            data.band.value,
            admin.id,
        )
        return user

    async def replace_account(self, user_id: UUID, data: AccountUpdate, admin: User) -> User:
        """Replace everything an administrator controls about one account.

        A full replacement rather than a patch, matching `AccountUpdate`. Note what that
        buys on the hats specifically: assigning the collection is what *removes* the
        hats that are no longer listed, and `cascade="all, delete-orphan"` on the
        relationship turns that into the deletes. A patch that only ever added would make
        taking a responsibility off somebody impossible through this screen.
        """
        user = await self.repo.get(user_id)
        if user is None:
            raise NotFoundError("No such account.")

        await self._refuse_taken_identifiers(None, data.microsoft_id, editing=user.id)

        before = AccountSnapshot.of(user)
        user.display_name = data.display_name
        user.function = data.function
        user.band = data.band
        user.microsoft_id = data.microsoft_id
        user.hat_rows = [UserHat(hat=h) for h in data.hats]

        self._refuse_self_lockout(user, admin)

        # Only a save that changed something earns a row: PUT is a full replacement, so
        # pressing Save on an untouched form is a legitimate no-op, and logging it would
        # bury the edits that moved a reach number under entries that moved nothing.
        if AccountSnapshot.of(user) != before:
            self._record(user, before=before, admin=admin)

        await self._commit_or_conflict()
        logger.info(
            "account changed: user=%s job=%s/%s by=%s",
            user.id,
            data.function.value,
            data.band.value,
            admin.id,
        )
        return user

    def _record(self, user: User, *, before: AccountSnapshot | None, admin: User) -> None:
        """Append the audit row for one create or edit, inside the caller's transaction.

        In-transaction is the property that makes the log trustworthy: a change and its
        record commit together or not at all, so the log cannot claim an edit that was
        rolled back, and an edit cannot land unrecorded.
        """
        self.repo.add_change(
            AccountChange(
                user_id=user.id,
                changed_by=admin.id,
                change={
                    "kind": "created" if before is None else "updated",
                    "before": before.model_dump(mode="json") if before else None,
                    "after": AccountSnapshot.of(user).model_dump(mode="json"),
                },
            )
        )

    async def history(self, user_id: UUID) -> list[AccountChangeRead]:
        """This account's audit rows, for the screen that shows what happened to it.

        Snapshots are served as the row stores them, old vocabulary and all: rows from
        before the job model say `role` and `groups`, and rewriting or refusing history
        would defeat the point of keeping it.
        """
        if await self.repo.get(user_id) is None:
            raise NotFoundError("No such account.")
        return [
            AccountChangeRead(
                id=change.id,
                changed_at=change.changed_at,
                changed_by=change.changed_by,
                changed_by_name=editor_name,
                kind=change.change["kind"],
                before=change.change["before"],
                after=change.change["after"],
            )
            for change, editor_name in await self.repo.history_for(user_id)
        ]

    async def preview_change(self, user_id: UUID, data: AccountUpdate) -> AccountImpact:
        """What saving this edit would do to who can answer what, before it is saved.

        The what-if half of the live-reach guardrail. The rule is asked twice per open
        survey, once for the person as they are and once for a detached User built from
        the form, and never paraphrased: the same `in_audience` that decides answering
        decides the preview, so the two cannot disagree.

        Only surveys where this person flips in or out are reported. Reach moves by
        exactly one when they do, so `reach_after` is arithmetic on the shared count
        rather than a second census.

        Surveys aimed at one person are skipped because they cannot flip: the target is
        an id, and no change of job makes this user a different person.

        Read-only by construction. The hypothetical user is never added to the session,
        and nothing here writes; the save that follows re-checks everything it enforces.
        """
        user = await self.repo.get(user_id)
        if user is None:
            raise NotFoundError("No such account.")

        hypothetical = User(
            id=user.id,
            email=user.email,
            display_name=data.display_name,
            function=data.function,
            band=data.band,
            hat_rows=[UserHat(hat=h) for h in data.hats],
        )

        reach = await self.reach_by_audience()
        surveys: list[SurveyImpact] = []
        open_rows = await TemplateRepository(self.session).list_summaries(TemplateStatus.published)
        for template, _question_count in open_rows:
            if template.audience is None or template.audience is SurveyAudience.person:
                continue
            was_in = bool(in_audience(user, template.audience))
            now_in = bool(in_audience(hypothetical, template.audience))
            if was_in == now_in:
                continue
            reach_before = reach.get(template.audience, 0)
            surveys.append(
                SurveyImpact(
                    template_id=template.id,
                    title=template.title,
                    audience=template.audience,
                    now_in=now_in,
                    reach_before=reach_before,
                    reach_after=reach_before + (1 if now_in else -1),
                )
            )

        return AccountImpact(
            function_before=user.function,
            function_after=data.function,
            band_before=user.band,
            band_after=data.band,
            may_author_before=may_author(user),
            may_author_after=may_author(hypothetical),
            hats_added=sorted(set(data.hats) - user.hats, key=lambda h: h.value),
            hats_removed=sorted(user.hats - set(data.hats), key=lambda h: h.value),
            surveys=surveys,
        )

    def _refuse_self_lockout(self, user: User, admin: User) -> None:
        """An administrator may not edit away their own administration.

        The state this prevents is not merely annoying, it is unrecoverable from inside
        the app: the last administrator moves themselves out of IT, and from then on
        nobody can create an account or grant anyone else the function that would let
        them. Fixing it means reaching the database directly, which is the thing this
        screen exists to stop being necessary.

        Only their *own* account, and only administration. An administrator moving
        themselves down a band keeps the admin routes, which is enough to undo it, and
        one administrator removing another's is a real thing to be able to do.
        """
        if user.id != admin.id:
            return
        if is_admin_by_config(user):
            return
        raise ConflictError(
            "That would remove your own administrator access, and nobody else could give "
            "it back from here. Ask another administrator to make the change."
        )

    async def _refuse_taken_identifiers(
        self, email: str | None, microsoft_id: str | None, *, editing: UUID | None
    ) -> None:
        """Check before writing, so the reply names the field rather than the constraint.

        The database is still the authority: `_commit_or_conflict` catches the same
        collision arriving between this check and the flush. This exists for the message,
        not for the guarantee.
        """
        if email is not None:
            existing = await self.repo.get_by_email(email)
            if existing is not None and existing.id != editing:
                raise ConflictError(f"{email} already has an account.")
        if microsoft_id is not None:
            existing = await self.repo.get_by_microsoft_id(microsoft_id)
            if existing is not None and existing.id != editing:
                raise ConflictError(
                    "Another account already carries that Microsoft id, and two accounts "
                    "sharing one would be two people sharing an identity."
                )

    async def _commit_or_conflict(self) -> None:
        """Commit, turning a lost race on either unique index into the same 409.

        Two administrators creating the same address at once both pass the check above and
        one of them loses at the index. Without this the loser gets a 500 naming a
        constraint, for a situation the caller can understand and act on.
        """
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            logger.info("account write lost a race on a unique index: %s", exc)
            raise ConflictError(
                "That email address or Microsoft id was taken while you were filling this "
                "in. Check the directory and try again."
            ) from exc
