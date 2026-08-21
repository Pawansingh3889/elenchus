"""Pydantic v2 request/response schemas for templates."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.templates.enums import (
    AnswerType,
    FollowUpPolicy,
    ShowWhenOp,
    SurveyAudience,
    TemplateStatus,
)
from app.units import can_convert, is_known_unit

SELECT_TYPES = {AnswerType.single_select, AnswerType.multi_select}


class ShowWhen(BaseModel):
    """A question's visibility condition (SPEC.md 2.2 stretch 2).

    ``question`` is the **0-based position** of an earlier question, not its id. Draft
    edits replace every question row, so ids do not survive a save — a condition keyed
    on one would break the moment the author edited anything. Positions are stable
    within a draft, and frozen for good once a version is published.
    """

    question: int = Field(ge=0)
    op: ShowWhenOp
    value: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def _value_has_content(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("show_when value cannot be blank")
        return text


class QuestionInput(BaseModel):
    text: str = Field(min_length=1)
    answer_type: AnswerType
    options: list[str] = Field(default_factory=list)
    allow_other: bool = False
    required: bool = True
    # Default to probing when the answer is unclear: the follow-up is this product's
    # differentiator, so a survey that omits the setting should get it, not "never".
    follow_up_policy: FollowUpPolicy = FollowUpPolicy.when_unclear
    show_when: ShowWhen | None = None
    # The unit a numeric answer is in, and an optional second unit to also display
    # (e.g. °C with °F). Both nullable; most questions are not measured quantities.
    unit: str | None = None
    display_unit: str | None = None

    @field_validator("text")
    @classmethod
    def _text_has_content(cls, value: str) -> str:
        # min_length counts characters, not content: "   " passes it and renders as a
        # question with nothing to read.
        text = value.strip()
        if not text:
            raise ValueError("question text cannot be blank")
        return text

    @field_validator("options")
    @classmethod
    def _options_are_distinct_and_readable(cls, values: list[str]) -> list[str]:
        """Options are matched case-insensitively when an answer comes back, so anything
        that collides under that rule is a choice the respondent can never land on."""
        options: list[str] = []
        seen: set[str] = set()
        for value in values:
            option = value.strip()
            if not option:
                raise ValueError("an option cannot be blank")
            if option.casefold() in seen:
                raise ValueError(f"duplicate option '{option}'")
            seen.add(option.casefold())
            options.append(option)
        return options

    @model_validator(mode="after")
    def _check_options(self) -> "QuestionInput":
        if self.answer_type in SELECT_TYPES:
            if not self.options:
                raise ValueError(f"{self.answer_type.value} requires at least one option")
        elif self.options:
            raise ValueError(f"{self.answer_type.value} must not carry options")
        if self.unit and not is_known_unit(self.unit):
            raise ValueError(f"unknown unit {self.unit!r}")
        if self.display_unit:
            if not is_known_unit(self.display_unit):
                raise ValueError(f"unknown display unit {self.display_unit!r}")
            if not can_convert(self.unit, self.display_unit):
                raise ValueError("display unit must share a dimension with the unit")
        return self


class AudienceTarget(BaseModel):
    """Who a survey is for, as the two fields that only mean anything together.

    A base class rather than two copies of the pair, because the rule binding them is the
    interesting part and a second copy of it is a second thing to forget. Both the builder
    and the AI draft request carry it.
    """

    # Defaulted on a new draft, where "nothing said yet" honestly means everyone on the
    # floor. Required on an update: see TemplateUpdate.
    audience: SurveyAudience = SurveyAudience.everyone
    # The one person, and only when `audience` is `person`.
    audience_user_id: UUID | None = None

    @model_validator(mode="after")
    def _person_and_id_agree(self) -> "AudienceTarget":
        """The pair is valid together or not at all, and saying so is a 422 rather than a
        row nobody can explain later.

        Both halves are wrong in their own way. `person` with no id is a survey aimed at
        somebody unnamed, which nobody can answer and which the dashboard would show with
        a reach of zero. An id with any other audience is a target that silently does
        nothing, and would go on doing nothing after the audience changed to `person`.
        """
        if self.audience is SurveyAudience.person and self.audience_user_id is None:
            raise ValueError("A survey aimed at one person must name them.")
        if self.audience is not SurveyAudience.person and self.audience_user_id is not None:
            raise ValueError("Only a survey aimed at one person may name a person.")
        return self


class TemplateWrite(AudienceTarget):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    # The workplace, for the interviewer rather than the respondent. See SurveyTemplate.
    # Optional everywhere, including on an update: unlike the settings above there is no
    # value that is true of a survey whose author has not written one, so None keeps
    # meaning "not described" rather than becoming a thing an update can silently clear.
    setting: str | None = Field(default=None, max_length=2000)
    questions: list[QuestionInput] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def _title_has_content(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title cannot be blank")
        return title

    @model_validator(mode="after")
    def _conditions_can_actually_be_evaluated(self) -> "TemplateWrite":
        """A condition must point backwards at a question that can answer it.

        The engine walks questions in order and decides visibility from answers already
        recorded, so a condition on a later question — or on itself — could never be
        true and would silently hide the question forever. Cheaper to refuse the survey
        than to ship one with a question nobody can reach.
        """
        for position, question in enumerate(self.questions):
            condition = question.show_when
            if condition is None:
                continue
            if condition.question >= position:
                raise ValueError(
                    f"question {position + 1} is shown by a condition on question "
                    f"{condition.question + 1}, which is not earlier in the survey"
                )
            referenced = self.questions[condition.question]
            if referenced.options:
                # The value is compared against what was recorded, and a select can only
                # ever record one of its own options (or a write-in). A value that is
                # neither is a typo the author will otherwise only discover by running
                # the survey and finding the question never appears.
                allowed = {o.casefold() for o in referenced.options}
                if condition.value.casefold() not in allowed and not referenced.allow_other:
                    raise ValueError(
                        f"question {position + 1}'s condition wants "
                        f"{condition.value!r}, which is not an option on question "
                        f"{condition.question + 1} ({', '.join(referenced.options)})"
                    )
            elif referenced.answer_type is AnswerType.yes_no:
                # A yes/no question records a boolean, which app.templates.visibility
                # renders as "yes"/"true" or "no"/"false". Anything else can never match.
                # Worth checking precisely because this is the branch a select falls into
                # the moment its type is changed: the options go, the stale value stays,
                # and without this the draft saves and the question is simply never shown
                # again. A condition that can never be true is the exact failure the rest
                # of this validator exists to prevent, so it must not survive here either.
                if condition.value.casefold() not in {"yes", "no", "true", "false"}:
                    raise ValueError(
                        f"question {position + 1}'s condition wants "
                        f"{condition.value!r}, but question {condition.question + 1} is "
                        "a yes/no question and can only answer 'yes' or 'no'"
                    )
        return self


# Create and update share the same shape (a full draft), but stay distinct types
# so the API and future divergence read clearly.
class TemplateCreate(TemplateWrite):
    pass


class TemplateUpdate(TemplateWrite):
    """A full replacement of the draft, so the settings it carries are not optional.

    An update replaces every column it names, and a field with a default is named on
    every request whether the client sent it or not. The builder never sent `audience`,
    so each save quietly reset an HR survey to the whole respondent pool: no error, no
    trace in the row, and a different set of people able to answer it. Requiring the
    settings here turns "the client forgot" into a 422 the caller can see, rather than a
    silent change to who a survey is for.

    Create keeps the defaults. A brand-new draft with no opinion yet is a real state;
    an update that has lost one is not.
    """

    audience: SurveyAudience


class GenerateRequest(AudienceTarget):
    """A description to draft from, plus who the result is for.

    The audience is the author's rather than the model's: see
    GenerationService.generate_draft for why it overrides the drafted value.
    """

    prompt: str = Field(min_length=1, max_length=4000)


class RefineRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=4000)


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    text: str
    answer_type: AnswerType
    options: list[str]
    allow_other: bool
    required: bool
    follow_up_policy: FollowUpPolicy
    show_when: ShowWhen | None = None
    unit: str | None = None
    display_unit: str | None = None


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: TemplateStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    audience: SurveyAudience
    # Read back as well as written. Without it the builder can load a survey aimed at a
    # person, fail to see who, and save it back naming nobody, which is the update path
    # of the bug the check constraint caught on the way in.
    audience_user_id: UUID | None = None
    setting: str | None
    questions: list[QuestionRead]


class GeneratedTemplate(BaseModel):
    """A drafted or refined template plus the model's short note on what it did."""

    template: TemplateRead
    note: str


class TemplateSummary(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: TemplateStatus
    updated_at: datetime
    closed_at: datetime | None = None
    audience: SurveyAudience = SurveyAudience.everyone
    audience_user_id: UUID | None = None
    question_count: int
    # Only populated for the published list a respondent chooses from; a draft has no
    # meaningful estimate because it is not what anyone will be asked.
    estimated_minutes: int | None = None
    # Whether this reader has already completed it. Defaulted, so the author's own drafts
    # list is unaffected: it is only ever true on the respondent's invitation list.
    answered: bool = False
