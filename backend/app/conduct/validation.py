"""Validate a model-supplied answer against the question's answer type.

This is the engine's gate: nothing reaches the database until it validates here, so a
confused model can never corrupt a run.
"""

import math
import re
from datetime import date
from difflib import SequenceMatcher
from typing import Any

from app.errors import AppError


class AnswerValidationError(AppError):
    status_code = 422
    code = "answer_invalid"


# How much of a recorded free-text answer must be traceable to what the respondent
# actually said. Not 1.0: the model legitimately merges several messages into one answer
# and tidies the joins, and a live run produced a good answer built from two separate
# turns. Not low either, or an invented sentence sharing a few words passes. 0.6 splits
# the two cases observed in practice by a wide margin, the good merge scoring above 0.9
# and an invented answer scoring 0.
_GROUNDING_THRESHOLD = 0.6

# Close enough to count as the same word, so fixing a typo or an inflection is not
# treated as invention. "systm" against "system" scores 0.91.
_SAME_WORD = 0.85

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

# Below this many words in the latest message, a selection is not judged at all. A
# respondent pointing at the list rather than describing an answer writes something short:
# "the second one" is three, "that one" is two. A reply that has wandered off the list to
# describe something the author never offered runs longer, and the live failure this gate
# exists for was seven. Set where those two populations separate, and deliberately on the
# lenient side of it.
_POSITIONAL_WORDS = 4


def _content_words(text: str) -> list[str]:
    """Words worth comparing, casefolded. Punctuation and digits are dropped: they carry
    no evidence of authorship, and a rating written back as "4" would otherwise count."""
    return [w.casefold() for w in _WORD.findall(text) if len(w) > 2]


def ungrounded_text(recorded: str, said: list[str]) -> str | None:
    """Why this free-text answer is not the respondent's, or None if it is.

    The engine's gates prove an answer has the right *shape*. Nothing proved it had the
    right *source*, and a live run showed why that matters: sent a message that was not
    an answer at all, the model wrote a plausible one and it was stored as the
    respondent's words, indistinguishable from a real reply. Summaries already refuse
    invented quotes; this is the same rule one layer earlier, where the invention gets in.

    Deliberately lenient about wording and strict about substance. Words are matched
    fuzzily so tidying survives, and the whole check is skipped when there is too little
    text to judge, because a one-word answer offers no evidence either way and refusing
    it would block real respondents to catch nobody.
    """
    words = _content_words(recorded)
    if len(words) < 3:
        return None

    pool = [w for message in said for w in _content_words(message)]
    if not pool:
        return "the respondent has not said anything this answer could be drawn from"

    matched = sum(
        1
        for word in words
        if word in pool
        or any(SequenceMatcher(None, word, other).ratio() >= _SAME_WORD for other in pool)
    )
    if matched / len(words) >= _GROUNDING_THRESHOLD:
        return None
    return (
        "that answer is not what the respondent said: record their own words, or if "
        "their message did not answer the question, ask a follow-up or flag it "
        "unanswerable instead of composing an answer for them"
    )


def ungrounded_choice(chosen: str, said: list[str]) -> str | None:
    """Why this selected option is not the respondent's, or None if it could be.

    The live failure this exists for. Asked "Where would AI help you most?", a respondent
    answered "training new starters, thats where wed feel it" and the engine recorded
    "Nowhere I can see". Not a near miss: the stored answer says the opposite of what they
    said, and an author reading the results would count them as seeing no use for it.

    An option is picked from a list the author wrote, so unlike free text it cannot be
    invented wholesale. What it can be is *wrong*, and wrong in a way nothing else notices,
    because the value is always a legitimate member of the list and passes every shape
    check there is.

    So the test is support rather than authorship: at least one substantial word of the
    chosen option has to appear, fuzzily, in what the respondent actually typed. "Tried it
    once or twice" is supported by "not much really, tried it once or twice". "Nowhere I
    can see" is supported by nothing in a sentence about training new starters.

    Skipped when the latest message is too short to judge, which is a sharper problem here
    than it is for prose. A respondent may answer positionally: "the second one", "b",
    "that one". Those support no option by word, and refusing them would block a real
    person to catch nobody. A terse reference is short; a description that has wandered off
    the list is not, which is what _POSITIONAL_WORDS separates. Judged on the latest message
    because that is where the choice was made, while the pool of what they said is the whole
    run, which is the lenient side of both decisions.

    The hole this leaves is a short answer that is genuinely off-list, "training", say. That
    is the side to be wrong on: the other side records an answer nobody gave.
    """
    option_words = _content_words(chosen)
    pool = [w for message in said for w in _content_words(message)]
    if not option_words or not said or len(_content_words(said[-1])) < _POSITIONAL_WORDS:
        return None

    supported = any(
        word in pool
        or any(SequenceMatcher(None, word, other).ratio() >= _SAME_WORD for other in pool)
        for word in option_words
    )
    if supported:
        return None
    return (
        f"nothing the respondent said supports the option {chosen!r}: choose the option "
        "they actually described, record their own words as a write-in if the list has "
        "nothing for them, or flag it unanswerable"
    )


def ungrounded_yes_no(said: list[str]) -> str | None:
    """Why this yes/no is not the respondent's, or None if it could be.

    Free text is not the only shape that can be invented. A live run answered "Would you
    recommend the new handover process?" from the single message "4" and stored yes, which
    reads in the author's results as a recommendation nobody made. A bare number carries no
    yes and no no.

    Judged on the latest message alone, unlike `ungrounded_text`, which pools the whole run.
    That pool is the right leniency for prose, where the model legitimately merges earlier
    turns, but it cannot work here: every respondent types words eventually, so a run-wide
    check passes the moment anyone says anything, and the live case above would have slipped
    straight through it.

    The test is "any letters at all", not `_content_words`, which drops words of two letters
    or fewer. A plain "no" is two letters, and a yes or no is a single character in Chinese
    and Japanese; keying on content words would refuse those real answers.
    """
    if said and _WORD.search(said[-1]):
        return None
    return (
        "the respondent's message contains no words, so it says neither yes nor no: ask "
        "a follow-up or flag it unanswerable instead of reading one into it"
    )


# What a JSON serializer can actually emit for a number. int()/float() alone are too
# permissive as a gate: they also parse Python-isms no serializer produces — "4_000",
# "nan", "Infinity", full-width digits ("４") — which would then sail through the type
# checks below wearing a numeric disguise. ASCII flag because \d otherwise matches any
# Unicode decimal digit.
_JSON_NUMBER = re.compile(r"[+-]?\d+(\.\d+)?([eE][+-]?\d+)?", re.ASCII)


def _coerce(answer_type: str, raw: Any) -> Any:
    """Undo pure serialization artifacts, never semantic guesses.

    Weak models habitually stringify tool arguments ('"4"' for 4, '"true"' for true)
    or emit integral floats (4.0). Those carry the exact same information as the typed
    value, so coercing them is lossless. Natural language ("four", "yes") stays
    rejected — mapping words to values is the model's job, checked by the gate below.
    """
    if answer_type in ("rating", "number") and isinstance(raw, str):
        text = raw.strip()
        if _JSON_NUMBER.fullmatch(text):
            try:
                raw = int(text)  # int first: float would round 2**53+1
            except ValueError:
                parsed = float(text)
                # Fall through so "4.0" gets the same integral-float rule as 4.0.
                raw = int(parsed) if parsed.is_integer() else parsed
    if answer_type == "rating" and isinstance(raw, float) and raw.is_integer():
        return int(raw)
    if answer_type == "yes_no" and isinstance(raw, str):
        lowered = raw.strip().casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return raw


def _canonical_option(raw: str, options: list[str]) -> str | None:
    """Case/whitespace-insensitive match to an option, returning its canonical text."""
    key = raw.strip().casefold()
    for option in options:
        if option.strip().casefold() == key:
            return option
    return None


def validate_answer(question: dict[str, Any], raw: Any) -> dict[str, Any]:
    """Return the normalised value to store, or raise AnswerValidationError."""
    answer_type = question["answer_type"]
    options: list[str] = question["options"]
    allow_other = question["allow_other"]
    raw = _coerce(answer_type, raw)

    if answer_type == "yes_no":
        if not isinstance(raw, bool):
            raise AnswerValidationError("yes_no expects true or false")
        return {"yes_no": raw}

    if answer_type == "rating":
        if isinstance(raw, bool) or not isinstance(raw, int) or not 1 <= raw <= 5:
            raise AnswerValidationError("rating expects a whole number from 1 to 5")
        return {"rating": raw}

    if answer_type == "number":
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise AnswerValidationError("number expects a numeric value")
        # NaN and infinity pass the isinstance check; stored, they poison every
        # average on the results page (and NaN is not even legal JSON).
        if isinstance(raw, float) and not math.isfinite(raw):
            raise AnswerValidationError("number must be finite")
        return {"number": raw}

    if answer_type in ("short_text", "long_text"):
        if not isinstance(raw, str) or not raw.strip():
            raise AnswerValidationError(f"{answer_type} expects non-empty text")
        return {"text": raw.strip()}

    if answer_type == "date":
        if not isinstance(raw, str):
            raise AnswerValidationError("date expects an ISO YYYY-MM-DD string")
        # Enforce the dashed form specifically: fromisoformat also accepts compact
        # ("20260303") and week-date ("2026-W10-2") forms, which would fragment the
        # same day across shapes in the results.
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            raise AnswerValidationError("date must be a valid YYYY-MM-DD string")
        try:
            parsed = date.fromisoformat(raw)
        except ValueError as exc:
            raise AnswerValidationError("date must be a valid YYYY-MM-DD string") from exc
        return {"date": parsed.isoformat()}

    if answer_type == "single_select":
        if not isinstance(raw, str):
            raise AnswerValidationError("single_select expects the option text")
        # A case/whitespace near-miss ("days" for "Days") is the option, not a write-in;
        # matching it canonically keeps the author's results aggregatable.
        canonical = _canonical_option(raw, options)
        if canonical is not None:
            return {"option": canonical}
        if allow_other:
            # A write-in is text: same non-empty-and-trimmed rule the text answers enforce.
            write_in = raw.strip()
            if not write_in:
                raise AnswerValidationError("a write-in answer needs text")
            return {"other": write_in}
        raise AnswerValidationError(f"'{raw}' is not one of {options} and 'other' is not allowed")

    if answer_type == "multi_select":
        if not isinstance(raw, list) or not raw:
            raise AnswerValidationError("multi_select expects a non-empty list of option texts")
        chosen: list[str] = []
        other: list[str] = []
        for value in raw:
            if not isinstance(value, str):
                raise AnswerValidationError("multi_select values must be strings")
            canonical = _canonical_option(value, options)
            if canonical is not None:
                # ["Email", "email"] is Email chosen once; canonicalising and then
                # storing both would double-count the option in the results.
                if canonical not in chosen:
                    chosen.append(canonical)
            elif allow_other:
                write_in = value.strip()
                if not write_in:
                    raise AnswerValidationError("a write-in answer needs text")
                if write_in not in other:
                    other.append(write_in)
            else:
                raise AnswerValidationError(
                    f"'{value}' is not one of {options} and 'other' is not allowed"
                )
        result: dict[str, Any] = {"options": chosen}
        if other:
            result["other"] = other
        return result

    raise AnswerValidationError(f"unsupported answer type '{answer_type}'")
