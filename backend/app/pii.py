"""Personal identifiers, caught before a respondent's message reaches anything.

The engine's other gates all judge what the *model* produced. This one judges what the
respondent typed, and it runs first, because everything downstream is worse: the message
goes to a hosted provider, and it is stored in a transcript an author reads.

Deterministic on purpose, and narrow on purpose. What is here matches a shape that is
almost never anything else. What is deliberately absent matters more, because this
service asks a chilled-fish plant about batch codes and temperatures:

  no bare digit runs   A batch code is a long run of digits and is the subject matter.
                       A rule that flagged one would refuse the answer the survey exists
                       to collect, on every run, and the gate would be turned off within
                       a day.
  no postcodes         A respondent naming a site ("the DN31 line") writes something a
                       postcode rule matches, and site names are legitimate content.

The hole this leaves is a person's name in prose: "Ravi said the chiller was broken" is
personal data and no regex will ever catch it. That is the prompt's job, not this one's
(see ``conduct_v8.md``), and the two are complementary rather than alternatives: the
prompt shapes what the model records, and this stops the raw message leaving at all.
"""

import re

from app.errors import AppError


class PIIInMessageError(AppError):
    """A respondent's message carries a personal identifier, so it was not accepted.

    422 and typed, beside ``AnswerValidationError`` rather than in ``app.errors``: both
    are conduct's own judgements about content, and both are the caller's to fix by
    sending something else. The message rendered to the respondent is translated by the
    caller, which knows the run's language; the *kind* found is logged and never sent
    back, because a message quoting the number it objected to has just written it into
    another log line.
    """

    status_code = 422
    code = "pii_in_message"


# Local part, @, domain with a real TLD. Loose about the local part because real
# addresses are, strict about the tail because "sales@2pm" should not match.
_EMAIL = re.compile(r"[\w.+%-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")

# A UK National Insurance number, in the strict shape rather than "two letters, six
# digits, a letter". The loose form is also the shape of a stock code, and the excluded
# first and second letters (D, F, I, Q, U, V, plus O second) are what keep this from
# matching one. A suffix outside A-D is not an NI number at all.
_NI = re.compile(
    r"(?<![A-Za-z0-9])[ABCEGHJ-PRSTW-Z][ABCEGHJ-NPRSTW-Z]"
    r"\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D](?![A-Za-z0-9])",
    re.IGNORECASE,
)

# Candidate spans that could be a phone number, verified by digit count below. Two
# openings only: a leading ``+``, or a leading ``0``. Anything else is a bare digit run,
# which is the batch code case this deliberately does not touch.
_PHONE_CANDIDATE = re.compile(r"(?<![\w+])(?:\+\d[\d\s().-]{6,18}\d|0\d[\d\s().-]{7,18}\d)(?!\w)")

# What a real number's digits add up to. E.164 caps at 15; 8 is the shortest national
# number in use. A UK number written from a leading 0 is 10 or 11, so the domestic form
# is held to that, which keeps a date or a reference number out.
_INTERNATIONAL_DIGITS = range(8, 16)
_DOMESTIC_DIGITS = (10, 11)


def _is_phone(candidate: str) -> bool:
    digits = re.sub(r"\D", "", candidate)
    if candidate.lstrip().startswith("+"):
        return len(digits) in _INTERNATIONAL_DIGITS
    return len(digits) in _DOMESTIC_DIGITS


def problem(text: str) -> str | None:
    """The kind of personal identifier in this text, or None if there is none.

    Returns the kind rather than a sentence, and never the value. The caller turns it
    into something the respondent reads, in their run's language, and logs the kind so an
    operator can see the gate firing without the log becoming the second place the number
    is written down.
    """
    if _EMAIL.search(text):
        return "email address"
    if _NI.search(text):
        return "national insurance number"
    if any(_is_phone(m.group()) for m in _PHONE_CANDIDATE.finditer(text)):
        return "phone number"
    return None
