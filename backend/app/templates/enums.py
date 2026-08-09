"""Controlled vocabularies for templates and questions."""

import enum


class TemplateStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    # The study is over: no new run may start, and the runs already in progress finish.
    # Distinct from archived, which is only "hide this from my list" and says nothing
    # about whether the survey is still taking answers.
    closed = "closed"
    archived = "archived"


class ShowWhenOp(str, enum.Enum):
    """The two comparisons the demo builder offers. Deliberately not extended: every
    extra operator is another thing the author can get subtly wrong, and the brief says
    conditional visibility, not routing."""

    is_ = "is"
    is_not = "is_not"


class AnswerType(str, enum.Enum):
    single_select = "single_select"
    multi_select = "multi_select"
    yes_no = "yes_no"
    short_text = "short_text"
    long_text = "long_text"
    rating = "rating"
    number = "number"
    date = "date"
