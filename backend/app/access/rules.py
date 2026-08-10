"""The access rules themselves. See app/access/__init__.py for what they mean and why."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from app.templates.enums import SurveyAudience
from app.users.models import CreatorDepartment, User, UserRole

logger = logging.getLogger("app.access")

# Which department may answer a survey aimed at each audience. `respondents` is absent on
# purpose: no department answers it, respondents do, and mapping it to something would be
# inventing a creator team called "respondents".
_AUDIENCE_DEPARTMENT: dict[SurveyAudience, CreatorDepartment] = {
    SurveyAudience.hr: CreatorDepartment.hr,
    SurveyAudience.operations: CreatorDepartment.operations,
    SurveyAudience.finance: CreatorDepartment.finance,
    SurveyAudience.technical: CreatorDepartment.technical,
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
    """Whether this user is an administrator, by email allowlist rather than by column.

    Case-folded, because an allowlist that fails on Pawan@example.com when it was written
    pawan@example.com is a lockout waiting to happen, and email casing is not meaningful
    in the local part in practice.

    Logged when it grants. The allowlist is configuration, which is easy to change and
    hard to audit afterwards, so the record of what it let through lives in the log.
    """
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


def may_list(
    user: User, audience: SurveyAudience | None, created_by: UUID, admin: bool
) -> AccessDecision:
    """Whether this survey appears in this user's lists at all.

    Existence is information. A survey titled "Finance restructure feedback" tells you
    something before a single answer is given, so a survey nobody may answer is also a
    survey nobody may see the name of.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    if audience is None:
        return AccessDecision(False, "survey has no audience, so only its author can see it")
    return may_answer(user, audience, created_by, admin)


def may_answer(
    user: User, audience: SurveyAudience | None, created_by: UUID, admin: bool
) -> AccessDecision:
    """Whether this user may start or continue a run of this survey.

    Note what this replaced: a check that the caller's role was `respondent`. That was
    never the real question, and it becomes wrong the moment a survey can be aimed at a
    department, because the people in that department are creators.
    """
    if audience is None:
        return AccessDecision(False, "survey has no audience")

    if audience is SurveyAudience.respondents:
        if user.role is UserRole.respondent:
            return AccessDecision(True, "respondent, and the survey is aimed at respondents")
        # A creator may answer a respondent-aimed survey only if it is their own, which is
        # how an author tries their own survey without a second account.
        if _owns(user, created_by):
            return AccessDecision(True, "author testing their own survey")
        return AccessDecision(False, "this survey is for respondents")

    wanted = _AUDIENCE_DEPARTMENT[audience]
    if user.role is not UserRole.author:
        return AccessDecision(False, f"this survey is for the {wanted.value} team")
    if user.department is None:
        return AccessDecision(False, "your account has no department, so it cannot be matched")
    if user.department is wanted:
        return AccessDecision(True, f"member of {wanted.value}")
    if admin:
        return AccessDecision(True, "admin")
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    return AccessDecision(False, f"this survey is for the {wanted.value} team")


# A created_by that can match no user, so `may_answer`'s owner branch cannot fire. Named
# once here rather than invented per call site, which is how the second caller invents a
# slightly different one.
NOBODY: Final[UUID] = UUID(int=0)


def in_audience(user: User, audience: SurveyAudience | None) -> AccessDecision:
    """Whether this user is one of the people a survey was written *for*.

    `may_answer` with both escape hatches shut: not the author testing their own survey,
    not an admin. Those two are how a survey gets answered by someone it was not aimed
    at, which is exactly what a denominator must not count.

    Deliberately a call to the rule rather than a copy of it. The audience question is
    asked in two places now, and the second must not be a paraphrase in SQL that drifts
    from this one with nothing to catch it: the guard in check_access_consulted.py checks
    that the question was asked, never that it was asked correctly.

    Do not refactor this and `may_answer` to share a core. `may_answer` refuses
    non-authors and department-less authors *before* it consults `admin`, and hoisting
    that order would quietly let a respondent-role admin through.
    """
    return may_answer(user, audience, NOBODY, admin=False)


def may_read_rows(user: User, created_by: UUID, admin: bool) -> AccessDecision:
    """Whether this user may read individual runs and answers.

    Deliberately narrower than `may_answer` and deliberately not about the audience. Being
    asked a question does not entitle you to read what your colleagues answered, and in a
    workplace survey that distinction is the difference between honest answers and careful
    ones.
    """
    if _owns(user, created_by):
        return AccessDecision(True, "author of this survey")
    if admin:
        return AccessDecision(True, "admin")
    return AccessDecision(False, "only the author and an admin can read individual responses")


def may_read_totals(
    user: User, audience: SurveyAudience | None, created_by: UUID, admin: bool
) -> AccessDecision:
    """Whether this user may read counts and distributions, without the rows behind them.

    Anyone who may answer may also see how it is going in aggregate. There is no
    suppression threshold: a filtered total over a group of two is, in effect, those two
    people's answers. That was decided knowingly, and the threshold is one constant away
    when it is wanted.
    """
    if may_read_rows(user, created_by, admin):
        return AccessDecision(True, "may read rows, so may read totals")
    return may_answer(user, audience, created_by, admin)
