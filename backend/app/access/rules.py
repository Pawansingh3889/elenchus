"""The access rules themselves. See app/access/__init__.py for what they mean and why."""

from __future__ import annotations

import logging
from dataclasses import dataclass
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
