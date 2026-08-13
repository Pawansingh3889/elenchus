"""Builders for request bodies whose settings are required rather than defaulted.

``TemplateUpdate`` replaces the whole draft, so its template-level settings are not
optional: a caller that omits one is not "leaving it alone", it is clearing it. That is
what made the builder reset an HR survey to the respondent pool on every save.

The type says so now, which is right, and it means a test changing one thing has to
restate the settings it is not changing. ``update_of`` does that from the template it is
handed, so a test stays about the thing it is testing. It is also exactly what a client
has to do: read what is there, send it back with your change on top.
"""

from typing import Any

from app.templates.models import SurveyTemplate
from app.templates.schemas import QuestionInput, TemplateUpdate


def update_of(template: SurveyTemplate, **changes: Any) -> TemplateUpdate:
    """A full update carrying the template's current settings, with `changes` applied."""
    body: dict[str, Any] = {
        "title": template.title,
        "description": template.description,
        # The whole pair, and the setting with them: update replaces what it does not
        # restate, so a builder that skipped these would clear them in every test that
        # meant to change something else.
        "audience": template.audience,
        "audience_user_id": template.audience_user_id,
        "setting": template.setting,
        "questions": [
            QuestionInput(
                text=q.text,
                answer_type=q.answer_type,
                options=list(q.options),
                allow_other=q.allow_other,
                required=q.required,
                follow_up_policy=q.follow_up_policy,
                show_when=q.show_when,
            )
            for q in sorted(template.questions, key=lambda q: q.position)
        ],
    }
    return TemplateUpdate.model_validate(body | changes)
