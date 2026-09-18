"""The access rules themselves. See app/access/__init__.py for what they mean and why."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from app.roles.models import Permission
from app.templates.enums import SurveyAudience
from app.users.models import BAND_RANK, Band, Function, Hat, User

logger = logging.getLogger("app.access")

# The bands that may build surveys and read colleagues' results: manager and up. One
# constant, read through `may_author`, so "who is senior enough" is a single fact and
# not a comparison re-typed at every gate.
_AUTHORING_RANK: Final[int] = BAND_RANK[Band.manager]

# The production ladder, band by band. Each of these audiences is one band of one
# function because that is how the floor is addressed: a survey for line leaders is not
# for the operatives beside them or the supervisors above them.
_PRODUCTION_BAND: dict[SurveyAudience, Band] = {
    SurveyAudience.operatives: Band.operative,
    SurveyAudience.line_leaders: Band.line_leader,
    SurveyAudience.supervisors: Band.supervisor,
    SurveyAudience.shift_managers: Band.manager,
}


@dataclass(frozen=True)
class AccessDecision:
    """Allowed or not, and why. The reason is for the log and for the error message.

    A bare bool would be enough to enforce the rule and useless to debug it: "you cannot
    see this survey" and "this survey has no audience, so only its author can see it" are
    the same refusal to a caller and completely different problems to whoever has to fix
    the deployment.
    """

    allowed: bool
    reason: str

    def __bool__(self) -> bool:
        return self.allowed


def may_author(user: User) -> bool:
    """Whether this person may build surveys: manager band and up, any function, or a
    role that grants it outright.

    Derived from the job rather than stored, which is what deleted the `role` column.
    The old stored role could disagree with the org chart (an "author" respondent, a
    shift manager refused authoring), and the Entra id was meant to decide it even
    though line leaders hold ERP logins without being survey authors. The band answers
    the question the role column was guessing at.

    The role branch is deliberately inside this function rather than duplicated at
    every caller: `_colleague` and the `managers` audience both read `may_author`, so a
    role-granted `survey_author` permission makes its holder behave exactly as a
    manager-band person would everywhere that matters, which is one fact rather than
    one re-typed per call site.
    """
    return (user.band is not None and BAND_RANK[user.band] >= _AUTHORING_RANK) or (
        Permission.survey_author in user.granted_permissions
    )


def is_admin(user: User, admin_emails: frozenset[str]) -> bool:
    """Whether this user is an administrator: by IT function, or by email allowlist.

    The function route was asked for directly and reverses the earlier rule that admin
    never comes from a column. It is worth being clear-eyed about what that costs: a
    `UPDATE users SET function = 'it'` is now a grant of administration, where before
    the database could not confer it at all. The allowlist is kept alongside rather than
    replaced, so an administrator who does not work in IT is still expressible.

    Case-folded, because an allowlist that fails on Pawan@example.com when it was written
    pawan@example.com is a lockout waiting to happen, and email casing is not meaningful
    in the local part in practice.

    Logged when it grants, and logged differently per route. Both are easy to change and
    hard to audit afterwards, so which one let a caller through lives in the log.
    """
    if user.function is Function.it:
        logger.info("admin granted by function: user=%s", user.id)
        return True
    if Permission.admin_all in user.granted_permissions:
        # A third route to the same reach the function branch above already accepted
        # as a cost: `app.roles`' admin routes already require an existing admin to
        # create or attach a role carrying this, so nothing new can grant it that a
        # human administrator did not choose to.
        logger.info("admin granted by role: user=%s", user.id)
        return True
    granted = user.email.casefold() in {e.casefold() for e in admin_emails}
    if granted:
        logger.info("admin granted by allowlist: user=%s", user.id)
    return granted


def is_admin_by_config(user: User) -> bool:
    """`is_admin` against the configured allowlist, which is what callers actually want.

    Separate from `is_admin` so the rule stays a pure function of its inputs and remains
    testable without settings, while services get one call rather than each of them
    reaching for `get_settings()` and remembering which field holds the parsed set.
    """
    from app.config import get_settings

    return is_admin(user, get_settings().admin_email_set)


def _owns(user: User, created_by: UUID) -> bool:
    return created_by == user.id


def _colleague(user: User, creator_function: Function | None) -> bool:
    """Whether this user shares a function with whoever made the survey, at a band that
    may read it.

    Both sides must actually have a function: `None is None` would otherwise make every
    person without one a colleague of every other. The band check is the line that was
    easy to miss when functions replaced office departments: functions contain the
    floor, so "same function" alone would make every production operative a colleague
    of the shift manager surveying them, and `may_read_rows` hands a colleague every
    individual answer. Sharing is symmetric among the authoring bands of one function
    and stops there.
    """
    return (
        user.function is not None
        and creator_function is not None
        and user.function is creator_function
        and may_author(user)
    )


def reads_all_surveys(user: User) -> bool:
    """Whether this user reads everything: the executive function, at authoring band.

    Site leadership oversight, decided deliberately: the factory manager and the
    production director read every survey and its results, and edit none of them
    (`may_edit` has no executive branch). Read access only, so answers stay behind the
    same pseudonyms they wear for everyone else.

    Public because the list pages scope their *queries* to the surveys the caller could
    pass `may_list`, and an executive's scope is all of them: the query widening has to
    ask the same predicate the rule does, or the two drift.
    """
    return user.function is Function.executive and may_author(user)


def may_list(
    user: User,
    audience: SurveyAudience | None,
    created_by: UUID,
    admin: bool,
    *,
    target: UUID | None = None,
    creator_function: Function | None = None,
) -> AccessDecision:
    """Whether this survey appears in this user's lists at all.

    Existence is information. A survey titled "Finance restructure feedback" tells you
    something before a single answer is given, so a survey nobody may answer is also a
    survey nobody may see the name of.

    A function colleague sees it too, so that work does not stop when the author who
    made it is on leave. What that costs is worth naming: answers are then read by people
    the respondent never dealt with, which is a wider audience for their words than the
    pseudonymity elsewhere in this system might suggest to them.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    if Permission.survey_list in user.granted_permissions:
        return AccessDecision(True, "granted by role")
    if reads_all_surveys(user):
        return AccessDecision(True, "site leadership")
    if _colleague(user, creator_function):
        return AccessDecision(True, f"colleague in {user.function.value}")  # type: ignore[union-attr]
    if audience is None:
        return AccessDecision(False, "survey has no audience, so only its author can see it")
    return may_answer(user, audience, created_by, admin, target=target)


def _in_derived_audience(user: User, audience: SurveyAudience) -> AccessDecision:
    """Whether this job (and its hats) is inside one of the derived audiences.

    The membership half of `may_answer`, with no escape hatches: pure org chart. Every
    audience except `everyone` and `person` is decided here, from the job alone, which
    is the whole design: there are no membership rows to be out of date.
    """
    if audience in _PRODUCTION_BAND:
        wanted = _PRODUCTION_BAND[audience]
        if user.function is Function.production and user.band is wanted:
            return AccessDecision(True, f"production {wanted.value}")
        return AccessDecision(False, f"this survey is for the production {wanted.value} band")

    if audience is SurveyAudience.qa:
        if user.function is Function.quality:
            return AccessDecision(True, "in the quality function")
        return AccessDecision(False, "this survey is for the quality team")

    if audience is SurveyAudience.health_safety:
        if user.function is Function.health_safety:
            return AccessDecision(True, "in the health and safety function")
        if Hat.health_safety in user.hats:
            return AccessDecision(True, "carries the health and safety responsibility")
        return AccessDecision(False, "this survey is for people with health and safety duties")

    if audience is SurveyAudience.managers:
        if may_author(user):
            return AccessDecision(True, f"{user.band.value} band")  # type: ignore[union-attr]
        return AccessDecision(False, "this survey is for the manager bands and up")

    return AccessDecision(False, f"no membership rule for audience {audience.value}")


def may_answer(
    user: User,
    audience: SurveyAudience | None,
    created_by: UUID,
    admin: bool,
    *,
    target: UUID | None = None,
) -> AccessDecision:
    """Whether this user may start or continue a run of this survey.

    Note what this replaced, three times over. It was once a check that the caller's
    role was `respondent`; then a check on the creator department a survey named; then
    membership rows in a join table. None survives, because each could disagree with
    the org chart: the people in the senior bands hold sign-in accounts, and the
    membership table happily recorded a line leader as QA, which the plant's own
    structure says is not a job anyone holds.

    So the question is the job: function, band, and hats, read live.
    """
    if audience is None:
        return AccessDecision(False, "survey has no audience")

    if audience is SurveyAudience.person:
        if target is None:
            # Loudly, rather than falling through to a general rule: a survey aimed at a
            # person who was never named is a broken row, not a survey for nobody.
            return AccessDecision(False, "survey is aimed at one person but names nobody")
        if user.id == target:
            return AccessDecision(True, "the person this survey is for")
        if _owns(user, created_by):
            return AccessDecision(True, "author testing their own survey")
        if admin:
            return AccessDecision(True, "admin")
        return AccessDecision(False, "this survey is for one named person")

    if audience is SurveyAudience.everyone:
        if user.function is not None:
            return AccessDecision(True, "holds a job, and the survey is for everyone")
        # Not "every account": an administration or service login belongs to nobody on
        # any ladder, and counting it would put people in a denominator who were never
        # asked.
        if _owns(user, created_by):
            return AccessDecision(True, "author testing their own survey")
        if admin:
            return AccessDecision(True, "admin")
        return AccessDecision(False, "your account holds no job on the plant")

    membership = _in_derived_audience(user, audience)
    if membership:
        return membership
    if admin:
        return AccessDecision(True, "admin")
    if _owns(user, created_by):
        return AccessDecision(True, "author testing their own survey")
    return membership


# A created_by that can match no user, so `may_answer`'s owner branch cannot fire. Named
# once here rather than invented per call site, which is how the second caller invents a
# slightly different one.
NOBODY: Final[UUID] = UUID(int=0)


def in_audience(
    user: User, audience: SurveyAudience | None, *, target: UUID | None = None
) -> AccessDecision:
    """Whether this user is one of the people a survey was written *for*.

    `may_answer` with both escape hatches shut: not the author testing their own survey,
    not an admin. Those two are how a survey gets answered by someone it was not aimed
    at, which is exactly what a denominator must not count.

    Deliberately a call to the rule rather than a copy of it. The audience question is
    asked in two places now, and the second must not be a paraphrase in SQL that drifts
    from this one with nothing to catch it: the guard in check_access_consulted.py checks
    that the question was asked, never that it was asked correctly.

    Do not refactor this and `may_answer` to share a core. Every branch there consults the
    owner and admin hatches after the membership test, and hoisting them would let this
    function count people the survey was never aimed at.
    """
    return may_answer(user, audience, NOBODY, admin=False, target=target)


def may_edit(user: User, created_by: UUID, admin: bool) -> AccessDecision:
    """Whether this user may change the survey itself: save, publish, close, summarise.

    Owner or admin. Deliberately narrower than `may_list`, and this is the distinction
    that was missing rather than an extra one: every mutation guarded itself by fetching
    the survey through the listing rule, so widening that rule for colleagues silently
    handed them the write path too. A colleague could rename and publish a survey in
    somebody else's name, which is a good deal more than being able to read it.

    No executive branch either, for the same reason: oversight is reading, and a
    factory manager who wants a survey changed asks the person whose name is on it.

    Not about the audience at all. Being asked a question, or being able to read what
    came back, has never implied being able to change what is being asked.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    if Permission.survey_edit in user.granted_permissions:
        return AccessDecision(True, "granted by role")
    return AccessDecision(False, "only the author and an admin can change this survey")


def may_read_rows(
    user: User,
    created_by: UUID,
    admin: bool,
    *,
    creator_function: Function | None = None,
) -> AccessDecision:
    """Whether this user may read individual runs and answers.

    Deliberately narrower than `may_answer` and deliberately not about the audience. Being
    asked a question does not entitle you to read what your colleagues answered, and in a
    workplace survey that distinction is the difference between honest answers and careful
    ones. The audience's own seniors get nothing here either, by decision: HR surveying
    the QA team does not hand head QA the raw answers, or nobody could survey a team
    candidly about its own management.

    A function colleague at authoring band may, so that a survey does not become
    unreadable when one person is away. It widens who reads a respondent's words beyond
    the one author they might have pictured.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    if Permission.results_read_rows in user.granted_permissions:
        return AccessDecision(True, "granted by role")
    if reads_all_surveys(user):
        return AccessDecision(True, "site leadership")
    if _colleague(user, creator_function):
        return AccessDecision(True, f"colleague in {user.function.value}")  # type: ignore[union-attr]
    return AccessDecision(
        False, "only the author, their function's seniors, leadership and an admin can read these"
    )


def may_read_totals(
    user: User,
    audience: SurveyAudience | None,
    created_by: UUID,
    admin: bool,
    *,
    target: UUID | None = None,
    creator_function: Function | None = None,
) -> AccessDecision:
    """Whether this user may read counts and distributions, without the rows behind them.

    Anyone who may answer may also see how it is going in aggregate. There is no
    suppression threshold: a filtered total over a group of two is, in effect, those two
    people's answers. That was decided knowingly, and the threshold is one constant away
    when it is wanted.
    """
    if may_read_rows(user, created_by, admin, creator_function=creator_function):
        return AccessDecision(True, "may read rows, so may read totals")
    if Permission.results_read_totals in user.granted_permissions:
        return AccessDecision(True, "granted by role")
    return may_answer(user, audience, created_by, admin, target=target)
