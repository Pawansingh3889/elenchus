"""Controlled vocabularies for templates and questions."""

import enum


class SurveyAudience(str, enum.Enum):
    """Who a survey is for. Exactly one, and fixed once the survey is published.

    `everyone` is anyone in any plant-floor group, whatever kind of account they hold. It
    is deliberately not "every user": a manager with a Teams login is an author account
    and belongs in an all-staff survey, while a service or administration account does
    not, and membership is the line between them.

    The five in the middle each name a `RespondentGroup`. Who may answer one is decided by
    membership of that group and never by `role`, because the people in the senior groups
    hold author accounts.

    `person` is one named individual, carried in `survey_templates.audience_user_id`
    rather than here: an enum cannot hold a user id, and inventing a value per person
    would be a vocabulary that grows with the payroll. It exists for the case it was asked
    for, a survey about their first weeks aimed at the person who just joined.

    Note what this replaced. The values used to be `respondents` plus four creator
    departments, so a survey was aimed at an office team. Those four were remapped to
    `managers` when this vocabulary arrived, which rewrote what those surveys said they
    were for; that was decided knowingly rather than by accident.

    Still a separate enum from RespondentGroup even though five values match. They answer
    different questions, "what does this person do" and "who is this survey for", and
    merging them would leave `person` and `everyone` sitting in a list of job roles.
    """

    everyone = "everyone"
    operatives = "operatives"
    line_leaders = "line_leaders"
    supervisors = "supervisors"
    managers = "managers"
    qa = "qa"
    person = "person"


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
