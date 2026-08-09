"""Who a survey is for, and when that can still change.

The audience is part of what was published, like the questions. A survey that collects
Finance answers and is then pointed at HR ends up with one set of results drawn from two
populations, and nothing in the data records that it moved.
"""

import pytest
from pydantic import ValidationError

from app.errors import ConflictError
from app.templates.enums import AnswerType, SurveyAudience
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.templates.service import TemplateService
from tests.builders import update_of


def _draft(title: str, audience: SurveyAudience) -> TemplateCreate:
    return TemplateCreate(
        title=title,
        audience=audience,
        questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
    )


async def test_a_survey_defaults_to_the_respondent_pool(session, author):
    """What every survey written before audiences existed was, so saying nothing keeps
    the old behaviour rather than quietly narrowing it."""
    template = await TemplateService(session).create_draft(
        TemplateCreate(
            title="Unaimed",
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )
    assert template.audience is SurveyAudience.respondents


async def test_an_audience_can_be_chosen_and_changed_while_it_is_a_draft(session, author):
    svc = TemplateService(session)
    template = await svc.create_draft(_draft("Finance check", SurveyAudience.finance), author)
    assert template.audience is SurveyAudience.finance

    updated = await svc.update_draft(
        template.id,
        update_of(
            template,
            audience=SurveyAudience.hr,
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )
    assert updated.audience is SurveyAudience.hr


async def test_the_audience_is_frozen_once_published(session, author):
    svc = TemplateService(session)
    template = await svc.create_draft(_draft("Finance check", SurveyAudience.finance), author)
    await svc.publish(template.id, author)

    with pytest.raises(ConflictError) as caught:
        await svc.update_draft(
            template.id,
            update_of(
                template,
                audience=SurveyAudience.hr,
                questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
            ),
            author,
        )
    assert "audience cannot change" in caught.value.message


async def test_a_published_survey_can_still_be_edited_otherwise(session, author):
    """The freeze is on the audience alone. Republishing with new questions is the
    versioning story the whole app is built around, and it must not be collateral."""
    svc = TemplateService(session)
    template = await svc.create_draft(_draft("Finance check", SurveyAudience.finance), author)
    await svc.publish(template.id, author)

    updated = await svc.update_draft(
        template.id,
        update_of(
            template,
            title="Finance check, rewritten",
            questions=[
                QuestionInput(text="Anything?", answer_type=AnswerType.short_text),
                QuestionInput(text="Anything else?", answer_type=AnswerType.short_text),
            ],
        ),
        author,
    )
    assert updated.title == "Finance check, rewritten"
    assert len(updated.questions) == 2


async def test_an_update_that_omits_the_audience_is_refused_not_defaulted():
    """The bug this change exists for.

    The builder never sent `audience`, and the field defaulted, so every save rewrote an
    HR survey as one for the whole respondent pool: no error, no trace in the row, and a
    different set of people able to answer it. An update replaces the draft, so a setting
    it does not carry is one it is clearing. Saying so is the caller's job.
    """
    with pytest.raises(ValidationError, match="audience"):
        TemplateUpdate(
            title="Finance check",
            allowed_answer_types=[],
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        )


async def test_creating_a_draft_may_still_leave_the_audience_unsaid():
    """The default is honest on a create: a survey nobody has aimed yet is for the
    respondent pool, which is what every survey written before audiences existed was."""
    draft = TemplateCreate(
        title="New", questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)]
    )
    assert draft.audience is SurveyAudience.respondents


async def test_a_save_that_carries_the_audience_leaves_it_alone(session, author):
    """The round trip the builder now performs: read what is there, send it back with
    the change on top, and the survey is still aimed where the author aimed it."""
    svc = TemplateService(session)
    template = await svc.create_draft(_draft("Finance check", SurveyAudience.finance), author)

    updated = await svc.update_draft(
        template.id,
        update_of(template, title="Finance check, renamed"),
        author,
    )
    assert updated.audience is SurveyAudience.finance
    assert updated.title == "Finance check, renamed"
