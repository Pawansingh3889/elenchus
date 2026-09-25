"""Controlled vocabularies for templates and questions."""

import enum


class SurveyAudience(str, enum.Enum):
    """Who a survey is for. Exactly one, and fixed once the survey is published.

    Membership is derived from the job model, never stored: each value below is a
    predicate over (function, band, hats) in `app.access.rules`, so who a survey
    reaches follows the org chart as jobs change and there are no membership rows to
    drift. `everyone` is anyone who holds a job; it is deliberately not "every
    account", because a service or administration login belongs to nobody on any
    ladder and counting it would put people in a denominator who were never asked.

    The production ladder gets a value per band because that is how the floor is
    actually addressed (operatives, line leaders, supervisors, shift managers). `qa`
    is the whole quality function, ground QA to head. `health_safety` is the H&S
    function plus everyone carrying the H&S hat, because the duty is what the survey
    is about, not the ladder. `managers` is a band, not a function: manager and up,
    wherever they work.

    `person` is one named individual, carried in `survey_templates.audience_user_id`
    rather than here: an enum cannot hold a user id, and inventing a value per person
    would be a vocabulary that grows with the payroll. It exists for the case it was
    asked for, a survey about their first weeks aimed at the person who just joined.

    Still a separate enum from Function and Band even though several values echo
    them. They answer different questions, "what is this person's job" and "who is
    this survey for", and merging them would leave `person` and `everyone` sitting in
    a list of jobs.
    """

    everyone = "everyone"
    operatives = "operatives"
    line_leaders = "line_leaders"
    supervisors = "supervisors"
    shift_managers = "shift_managers"
    managers = "managers"
    qa = "qa"
    health_safety = "health_safety"
    # Anyone with an account in the workspace, job or not. Added 25 Sep 2026 for open
    # sign-up: a person who signed themselves in holds no job, so `everyone` never
    # reaches them, and this is the audience a free survey is aimed at.
    signed_in = "signed_in"
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
