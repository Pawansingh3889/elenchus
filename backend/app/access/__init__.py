"""Who may see, answer, and read a survey. One home for the rule, and only one.

Every service asks these functions; none of them re-derives the answer. That is the whole
point of the module: the same rule written in three places is three rules that agree today
and disagree after the first change nobody propagated. `scripts/check_access_consulted.py`
fails the build if a service hands out surveys, runs or answers without asking here.

Pure functions over values. No session, no queries, no imports from a repository, so the
rules can be read in one sitting and tested exhaustively without a database. That also
keeps the dependency arrows sane: everything imports access, access imports almost nothing.

The rules, in one paragraph. Every person holds one job, a (function, band) pair, plus
any hats; everything below derives from it. Manager band and up may author. A survey is
aimed at exactly one audience, and audience membership is a predicate over the job: the
production audiences are that function's bands, `qa` is the quality function,
`health_safety` is that function or the hat, `managers` is the authoring bands anywhere,
`everyone` is anyone with a job. An author always reaches their own work; colleagues are
the authoring bands of the author's own function and may read but never edit; the
executive function reads everything and edits nothing; an admin (IT function, or the
email allowlist) reaches everything. Reading rows is narrower than answering: being in
the audience means you were asked, not that you may read what your colleagues said, and
the audience's own seniors are deliberately not readers of surveys aimed at them.

Ambiguity fails closed. A survey with no audience, or an account with no job, is judged
by the narrowest branch that still holds, and the caller is told which piece was missing
rather than being handed a quiet default. The dangerous failure here is not a refusal, it
is a survey shown to people it was not meant for.
"""

from app.access.rules import (
    NOBODY,
    AccessDecision,
    in_audience,
    is_admin,
    is_admin_by_config,
    is_workspace_admin,
    is_workspace_owner,
    may_answer,
    may_author,
    may_edit,
    may_list,
    may_read_rows,
    may_read_totals,
    reads_all_surveys,
)

__all__ = [
    "NOBODY",
    "AccessDecision",
    "is_admin",
    "is_admin_by_config",
    "is_workspace_admin",
    "is_workspace_owner",
    "in_audience",
    "may_answer",
    "may_author",
    "may_edit",
    "may_list",
    "may_read_rows",
    "may_read_totals",
    "reads_all_surveys",
]
