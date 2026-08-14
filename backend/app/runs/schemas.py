"""Read schemas for runs.

The transcript and answer shapes live here with the models they describe; conducting
and results both read them.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.templates.enums import AnswerType, TemplateStatus


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: MessageRole
    content: str
    created_at: datetime


class MessageDetailRead(MessageRead):
    """A transcript message with its provenance, for the author reading results.

    Separate from ``MessageRead`` because that one is also the respondent's own chat
    payload (``conduct.schemas.RunRead``), and which provider served their interview is
    not theirs to be told. Nothing here is secret; it is simply operational detail on a
    payload sent to whoever answers a survey, and the narrower schema costs one class.

    All three are optional because the column is: a respondent's message and the engine's
    opening line were not produced by a model, and neither was anything recorded before
    these columns existed.
    """

    prompt_version: str | None = None
    model: str | None = None
    tier: int | None = None


class AnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: UUID
    kind: AnswerKind
    question_text: str
    value: dict[str, Any]
    answered_at: datetime


class RunSummary(BaseModel):
    id: UUID
    respondent_label: str
    status: RunStatus
    version: int
    answered: int
    total: int
    started_at: datetime
    completed_at: datetime | None


class RunDetail(BaseModel):
    id: UUID
    respondent_label: str
    status: RunStatus
    version: int
    started_at: datetime
    completed_at: datetime | None
    messages: list[MessageDetailRead]
    answers: list[AnswerRead]
    # Follow-ups the engine issued, per question id. The cap is spent when a probe is
    # asked, not when a reply to one is recorded, so this is the only faithful record of
    # follow-up spend: a probe that drew out the scripted answer itself leaves no
    # follow-up answer row behind, and the results view would show no sign of it.
    follow_ups_asked: dict[UUID, int] = Field(default_factory=dict)
    # Null until an author asks for one; the stretch AI summary is generated on request,
    # not as a side effect of the respondent finishing.
    summary: dict[str, Any] | None = None


class DashboardRow(BaseModel):
    """One survey as the author's dashboard shows it: what it is, and how it is going."""

    id: UUID
    title: str
    status: TemplateStatus
    updated_at: datetime
    closed_at: datetime | None

    # Runs. "Of the people who turned up, how many finished" is still worth asking, and
    # not the same question as the one below.
    started: int
    completed: int
    in_progress: int
    abandoned: int
    # People. How many the survey is for, and how many of them have answered. Separate
    # fields rather than corrected versions of the ones above, because both questions are
    # real: after the one-answer-per-person guard the two converge for new data, and rows
    # written before it keep their history.
    reach: int
    people_started: int
    people_completed: int
    last_started_at: datetime | None
    last_completed_at: datetime | None

    @computed_field  # type: ignore[prop-decorator]  # pydantic needs the property last
    @property
    def response_rate(self) -> float | None:
        """Of the people this survey is for, how many have finished it.

        None when the audience resolves to nobody, never 0: a survey aimed at an empty
        team has no rate, and 0% would read as everyone refusing.

        Note it can exceed 1. An author testing their own respondent-aimed survey has a
        run and is not in the audience, so two answers against a reach of one is a real
        state. Reported rather than clamped: hiding it would mean quietly dropping a real
        answer from a real person out of the count.
        """
        return self.people_completed / self.reach if self.reach else None

    @computed_field  # type: ignore[prop-decorator]  # pydantic needs the property last
    @property
    def completion_rate(self) -> float | None:
        """Completed as a share of started, or None when nobody has started.

        A property rather than a stored column: it is arithmetic on two numbers already
        here, and computing it in SQL would mean deciding there what 0/0 means. None says
        "no answer yet" honestly, where 0.0 would read as "everyone abandoned".
        """
        return self.completed / self.started if self.started else None


class OptionCount(BaseModel):
    """One row of a select question's tally. `label` is the option as the author wrote
    it, or the respondent's own words for a write-in."""

    label: str
    count: int
    write_in: bool = False


class QuestionReport(BaseModel):
    """One question, as the whole survey answered it.

    `answered` counts the runs that gave a usable answer; `declined` counts the ones the
    engine recorded as unanswerable. They are reported apart because a question everyone
    skipped and a question nobody reached are different findings, and averaging over the
    wrong denominator is how a survey gets quoted wrongly.
    """

    id: UUID
    position: int
    text: str
    answer_type: AnswerType
    answered: int
    declined: int
    # Selects, yes/no and ratings: the tally, in the author's option order, write-ins last.
    counts: list[OptionCount] = Field(default_factory=list)
    # How many times anything was picked, across everyone who answered. On every type but
    # `multi_select` this equals `answered`, because one person makes one choice. On a
    # multi-select it does not, and the gap is the whole reason this field exists: three
    # people picking two options each is six selections from three people, so a single
    # percentage cannot describe both. `answered` is the denominator for "what share of
    # people said this" and `selections` for "what share of the picks was this", and a
    # page showing only one of them is quoting the question wrongly.
    selections: int = 0
    # Ratings and numbers only. None when nobody answered, rather than 0, which would
    # read as everyone scoring zero.
    average: float | None = None
    # The spread, for the same two types. An average alone is the whole of what a number
    # question reported, and "22.5 minutes" hides whether that is everyone saying twenty
    # or half saying five and half saying forty. A rating has its counts to show shape; a
    # number has nothing else at all.
    low: float | None = None
    high: float | None = None
    # Free text and write-ins, verbatim and in full. Counted on the page, shown on click:
    # nothing here is grouped or characterised, because that is a judgement about what
    # someone meant and this page is the numbers.
    verbatim: list[str] = Field(default_factory=list)
    # What the probes drew out, and how many runs were probed. Their own fields rather
    # than folded into the two above, for the reason `answered` and `declined` are apart:
    # a follow-up answers a question the model wrote, not the author's, so it can never
    # join a tally the author's option list defines. On a rating question a probe answers
    # in prose by design, and adding it to `counts` or `average` would corrupt the one
    # number the page exists to show.
    #
    # `probed` counts runs, not probes, so it reads against `answered` on the same scale.
    # One run can be probed up to MAX_FOLLOW_UPS times on one question, so the list below
    # is usually longer than this number.
    follow_ups: list[str] = Field(default_factory=list)
    probed: int = 0


class MatrixQuestion(BaseModel):
    """One question as the matrix indexes it: enough to render a column and to slice on.

    The author's option list comes with it, because a slice offers the options the
    question offered, including any nobody picked. Slicing on what happens to appear in
    the data would hide exactly the empty option that is a finding.
    """

    id: UUID
    position: int
    text: str
    answer_type: AnswerType
    options: list[str] = Field(default_factory=list)


class MatrixRun(BaseModel):
    """One response, with its answers unaggregated.

    ``respondent_label`` is the survey's own pseudonym, numbered within this template so
    a person cannot be followed between surveys. It is also the key the recap's quote
    gate matches on, so its format is load-bearing and not display text to reformat.
    """

    run_id: UUID
    respondent_label: str
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None
    answers: list[AnswerRead] = Field(default_factory=list)


class AnswersMatrix(BaseModel):
    """Every answer on the current version, by respondent, with nothing tallied.

    The report answers "what did people say" one question at a time, which cannot answer
    "did the people who said X also say Y" — the question an author actually has, and one
    that previously took a request per run to reconstruct. The join exists here instead,
    once, and the client slices it.

    Raw ``value`` dicts rather than printable strings: a slice keys on the stored shape,
    and "yes" the option and "yes" the write-in must not collapse into one bucket, which
    is the same distinction the tallies are careful about.

    Runs of every status are included, carrying ``status``, because the report tallies
    answers from unfinished runs on the current version too. A matrix over completed runs
    only would produce sliced totals that disagreed with the unsliced ones beside them.
    """

    template_id: UUID
    title: str
    version: int
    questions: list[MatrixQuestion]
    runs: list[MatrixRun]
    # Excluded and counted, exactly as the report treats them: their questions are not
    # these questions, so their answers cannot join these columns.
    runs_on_earlier_versions: int


class SurveyReport(BaseModel):
    """What the survey found, question by question."""

    template_id: UUID
    title: str
    version: int
    runs_total: int
    runs_completed: int
    # People rather than runs: how many the survey is for, how many opened it, how many
    # finished. The tallies below count one vote per run, so before the guard a survey
    # answered four times by one person tallied four votes.
    reach: int
    people_started: int
    people_completed: int
    # Runs answered against an earlier published version. Their questions are not these
    # questions, so their answers are not counted here rather than being folded in and
    # quietly changing what a number means. Named so the omission is visible.
    runs_on_earlier_versions: int
    questions: list[QuestionReport]
