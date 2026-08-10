"""Who may see, answer, and read a survey. One home for the rule, and only one.

Every service asks these functions; none of them re-derives the answer. That is the whole
point of the module: the same rule written in three places is three rules that agree today
and disagree after the first change nobody propagated. `scripts/check_access_consulted.py`
fails the build if a service hands out surveys, runs or answers without asking here.

Pure functions over values. No session, no queries, no imports from a repository, so the
rules can be read in one sitting and tested exhaustively without a database. That also
keeps the dependency arrows sane: everything imports access, access imports almost nothing.

The rules, in one paragraph. A survey is aimed at exactly one audience: the respondent
pool, or one creator department. Its author may always reach their own work. An admin may
reach everything, and admin comes from the email allowlist in settings rather than from a
department, so it is granted without a database edit and logged whenever it is what let a
request through. Everyone else is judged on the audience: a respondent may answer a survey
aimed at respondents, a creator may answer one aimed at their own department. Reading is
narrower than answering. Individual rows stay with the author and admin, because being in
the audience means you were asked, not that you may read what your colleagues said. The
audience department may read totals.

Ambiguity fails closed. A survey with no audience, or a creator with no department, is
visible to its author and admin alone, and the caller is told which piece was missing
rather than being handed a quiet default. The dangerous failure here is not a refusal, it
is a survey shown to people it was not meant for.
"""

from app.access.rules import (
    NOBODY,
    AccessDecision,
    in_audience,
    is_admin,
    is_admin_by_config,
    may_answer,
    may_list,
    may_read_rows,
    may_read_totals,
)

__all__ = [
    "NOBODY",
    "AccessDecision",
    "is_admin",
    "is_admin_by_config",
    "in_audience",
    "may_answer",
    "may_list",
    "may_read_rows",
    "may_read_totals",
]
