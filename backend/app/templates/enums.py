"""Controlled vocabularies for templates and questions."""

import enum


class SurveyAudience(str, enum.Enum):
    """Who a survey is for. Exactly one, and fixed once the survey is published.

    `respondents` means the whole respondent pool, which is what every survey written
    before this existed was, and so it is the default: nothing already published changes
    reach. The rest name a creator department, and a survey aimed at one is answered by
    the creators in it rather than by respondents.

    Deliberately a separate enum from CreatorDepartment even though three values match.
    They answer different questions, "which part of the business is this person in" and
    "who is this survey for", and merging them would mean a survey could be aimed at
    `admin` as though that were a team to survey.
    """

    respondents = "respondents"
    hr = "hr"
    operations = "operations"
    finance = "finance"
    technical = "technical"


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


class FollowUpPolicy(str, enum.Enum):
    """Whether the interviewer probes this question, and how hard.

    Replaces the boolean ``allow_follow_ups``, which could only grant permission. That
    was enough for "you may probe if the answer is unusable" and had no way to say "the
    elaboration *is* the answer here", so a model reading the two cases saw one case. A
    live survey with four probe-enabled questions asked eight people ninety-odd turns of
    questions and never once followed up, which was the prompt behaving exactly as
    written: the budget is a ceiling, and a complete answer needs no probe.

    ``always_once`` is the missing sentence. It is enforced by the engine withholding
    ``record_answer`` rather than by asking the model more firmly, because CLAUDE.md
    already says the engine owns how many follow-ups are spent, and until now whether
    any were spent at all was the model's call.
    """

    never = "never"
    when_unclear = "when_unclear"
    always_once = "always_once"


# The scale a rating is on. Here rather than in the validator that enforces it, because
# reading an answer needs it as much as writing one does: a stored 5 means nothing without
# it, and anything that has to say so out loud must say the same number the gate enforces.
# Both app.conduct and app.runs already depend on app.templates, so this is the one place
# both can read it from without either domain reaching into the other.
RATING_MIN = 1
RATING_MAX = 5
