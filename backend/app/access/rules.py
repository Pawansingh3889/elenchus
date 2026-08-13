"""The access rules themselves. See app/access/__init__.py for what they mean and why."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from app.templates.enums import SurveyAudience
from app.users.models import CreatorDepartment, RespondentGroup, User

logger = logging.getLogger("app.access")

# Which group may answer a survey aimed at each audience. `everyone` and `person` are
# absent on purpose: neither is a group, and mapping them to one would invent a group
# called "everyone" and a group of one.
_AUDIENCE_GROUP: dict[SurveyAudience, RespondentGroup] = {
    SurveyAudience.operatives: RespondentGroup.operatives,
    SurveyAudience.line_leaders: RespondentGroup.line_leaders,
    SurveyAudience.supervisors: RespondentGroup.supervisors,
    SurveyAudience.shift_managers: RespondentGroup.shift_managers,
    SurveyAudience.managers: RespondentGroup.managers,
    SurveyAudience.qa: RespondentGroup.qa,
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


def is_admin(user: User, admin_emails: frozenset[str]) -> bool:
    """Whether this user is an administrator: by IT department, or by email allowlist.

    The department route was asked for directly and reverses the earlier rule that admin
    never comes from a column. It is worth being clear-eyed about what that costs: a
    `UPDATE users SET department = 'it'` is now a grant of administration, where before
    the database could not confer it at all. The allowlist is kept alongside rather than
    replaced, so an administrator who does not work in IT is still expressible.

    Case-folded, because an allowlist that fails on Pawan@example.com when it was written
    pawan@example.com is a lockout waiting to happen, and email casing is not meaningful
    in the local part in practice.

    Logged when it grants, and logged differently per route. Both are easy to change and
    hard to audit afterwards, so which one let a caller through lives in the log.
    """
    if user.department is CreatorDepartment.it:
        logger.info("admin granted by department: user=%s", user.id)
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


def _colleague(user: User, creator_department: CreatorDepartment | None) -> bool:
    """Whether this user is in the same department as whoever made the survey.

    Both sides must actually have a department. `None is None` would otherwise make every
    person without one a colleague of every other, which is the whole respondent pool
    reading each other's surveys.
    """
    return (
        user.department is not None
        and creator_department is not None
        and user.department is creator_department
    )


def may_list(
    user: User,
    audience: SurveyAudience | None,
    created_by: UUID,
    admin: bool,
    *,
    target: UUID | None = None,
    creator_department: CreatorDepartment | None = None,
) -> AccessDecision:
    """Whether this survey appears in this user's lists at all.

    Existence is information. A survey titled "Finance restructure feedback" tells you
    something before a single answer is given, so a survey nobody may answer is also a
    survey nobody may see the name of.

    A department colleague sees it too, so that work does not stop when the author who
    made it is on leave. What that costs is worth naming: answers are then read by people
    the respondent never dealt with, which is a wider audience for their words than the
    pseudonymity elsewhere in this system might suggest to them.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    if _colleague(user, creator_department):
        return AccessDecision(True, f"colleague in {user.department.value}")  # type: ignore[union-attr]
    if audience is None:
        return AccessDecision(False, "survey has no audience, so only its author can see it")
    return may_answer(user, audience, created_by, admin, target=target)


def may_answer(
    user: User,
    audience: SurveyAudience | None,
    created_by: UUID,
    admin: bool,
    *,
    target: UUID | None = None,
) -> AccessDecision:
    """Whether this user may start or continue a run of this survey.

    Note what this replaced, twice over. It was once a check that the caller's role was
    `respondent`; then a check on the creator department a survey named. Neither survives,
    because the people in the senior groups hold author accounts: a line leader signs in
    with Teams and is a creator by `role`, and refusing them a survey aimed at line
    leaders on that basis would be refusing exactly the people it was written for.

    So the question is membership, and `role` is not consulted here at all.
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
        if user.groups:
            return AccessDecision(True, "in a plant group, and the survey is for everyone")
        # Not "every account": an administration or service login belongs to nobody on the
        # floor, and counting it would put people in a denominator who were never asked.
        if _owns(user, created_by):
            return AccessDecision(True, "author testing their own survey")
        if admin:
            return AccessDecision(True, "admin")
        return AccessDecision(False, "your account is not in any group")

    wanted = _AUDIENCE_GROUP[audience]
    if wanted in user.groups:
        return AccessDecision(True, f"member of {wanted.value}")
    if admin:
        return AccessDecision(True, "admin")
    if _owns(user, created_by):
        return AccessDecision(True, "author testing their own survey")
    return AccessDecision(False, f"this survey is for {wanted.value}")


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
    the survey through the listing rule, so widening that rule for department colleagues
    silently handed them the write path too. A colleague could rename and publish a
    survey in somebody else's name, which is a good deal more than being able to read it.

    Not about the audience at all. Being asked a question, or being able to read what
    came back, has never implied being able to change what is being asked.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    return AccessDecision(False, "only the author and an admin can change this survey")


def may_read_rows(
    user: User,
    created_by: UUID,
    admin: bool,
    *,
    creator_department: CreatorDepartment | None = None,
) -> AccessDecision:
    """Whether this user may read individual runs and answers.

    Deliberately narrower than `may_answer` and deliberately not about the audience. Being
    asked a question does not entitle you to read what your colleagues answered, and in a
    workplace survey that distinction is the difference between honest answers and careful
    ones.

    A department colleague may, which was asked for so that a survey does not become
    unreadable when one person is away. It widens who reads a respondent's words beyond
    the one author they might have pictured.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    if _colleague(user, creator_department):
        return AccessDecision(True, f"colleague in {user.department.value}")  # type: ignore[union-attr]
    return AccessDecision(False, "only the author, their department and an admin can read these")


def may_read_totals(
    user: User,
    audience: SurveyAudience | None,
    created_by: UUID,
    admin: bool,
    *,
    target: UUID | None = None,
    creator_department: CreatorDepartment | None = None,
) -> AccessDecision:
    """Whether this user may read counts and distributions, without the rows behind them.

    Anyone who may answer may also see how it is going in aggregate. There is no
    suppression threshold: a filtered total over a group of two is, in effect, those two
    people's answers. That was decided knowingly, and the threshold is one constant away
    when it is wanted.
    """
    if may_read_rows(user, created_by, admin, creator_department=creator_department):
        return AccessDecision(True, "may read rows, so may read totals")
    return may_answer(user, audience, created_by, admin, target=target)
