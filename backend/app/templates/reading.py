"""One shape for a survey's questions, for everyone who reads them.

Replaces `snapshot.py`, which read the same shape out of a version's frozen JSONB
definition. Versions are gone (see CLAUDE.md, 16 Aug 2026), so the source is now the
live `SurveyQuestion` rows, and what survives the change is the reason that module
existed at all.

That reason was never the JSON. It was that every reader used to decide for itself what
a missing key meant, and they did not agree: with no `required` key, `engine._briefing`
told the model a question was required while `router._to_read` told the browser it was
optional. The same question, at the same moment, mandatory to the interviewer and
skippable to the respondent. There were fourteen such defaults across six files.

So this module keeps the job: one place turns a survey into the dicts the engine and the
report consume, and every reader downstream can subscript freely. Dicts rather than
models, because the engine's signatures are `dict[str, Any]` and the point is the single
shape, not a rewrite of everything behind it.

What is different now, and worth saying plainly: these questions are live. A reader that
holds them across an author's edit is holding stale data, where a frozen version could
be held forever. Read them at the moment you need them.
"""

from typing import Any

from app.templates.models import SurveyQuestion, SurveyTemplate


def _question_to_dict(question: SurveyQuestion) -> dict[str, Any]:
    """One question, in the shape every reader expects.

    Explicit rather than a generic column dump, because the keys here are a contract
    with the conduct engine and the report: adding a column should not silently change
    what the interviewer is told, and removing one should fail here rather than surface
    as a missing key three modules away.
    """
    return {
        "id": str(question.id),
        "position": question.position,
        "text": question.text,
        "answer_type": question.answer_type.value,
        "options": list(question.options or []),
        "allow_other": bool(question.allow_other),
        "required": bool(question.required),
        "follow_up_policy": question.follow_up_policy.value,
        "show_when": question.show_when,
    }


def questions_of(template: SurveyTemplate) -> list[dict[str, Any]]:
    """This survey's questions, position-sorted.

    Sorted here rather than trusted from the relationship, because position is what the
    engine walks and the ordering of a loaded collection is a property of the query
    rather than of the data.
    """
    return [_question_to_dict(q) for q in sorted(template.questions, key=lambda q: q.position)]


def setting_of(template: SurveyTemplate) -> str | None:
    """The workplace the author described, or None if they described none.

    Read here rather than subscripted at the call site, for the reason at the top of
    this module: a missing value must mean one thing everywhere. A blank or
    whitespace-only value reads as None too, because an author who cleared the box has
    described nothing, and passing "" down would put an empty heading in the briefing
    that announces a setting and then does not give one.
    """
    raw = template.setting
    if not isinstance(raw, str):
        return None
    return raw.strip() or None
