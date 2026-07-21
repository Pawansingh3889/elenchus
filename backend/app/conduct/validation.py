"""Validate a model-supplied answer against the question's answer type.

This is the engine's gate: nothing reaches the database until it validates here, so a
confused model can never corrupt a run.
"""

from datetime import date
from typing import Any

from app.errors import AppError


class AnswerValidationError(AppError):
    status_code = 422
    code = "answer_invalid"


def validate_answer(question: dict[str, Any], raw: Any) -> dict[str, Any]:
    """Return the normalised value to store, or raise AnswerValidationError."""
    answer_type = question["answer_type"]
    options: list[str] = question.get("options") or []
    allow_other = bool(question.get("allow_other"))

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
        return {"number": raw}

    if answer_type in ("short_text", "long_text"):
        if not isinstance(raw, str) or not raw.strip():
            raise AnswerValidationError(f"{answer_type} expects non-empty text")
        return {"text": raw.strip()}

    if answer_type == "date":
        if not isinstance(raw, str):
            raise AnswerValidationError("date expects an ISO YYYY-MM-DD string")
        try:
            date.fromisoformat(raw)
        except ValueError as exc:
            raise AnswerValidationError("date must be a valid YYYY-MM-DD string") from exc
        return {"date": raw}

    if answer_type == "single_select":
        if not isinstance(raw, str):
            raise AnswerValidationError("single_select expects the option text")
        if raw in options:
            return {"option": raw}
        if allow_other:
            return {"other": raw}
        raise AnswerValidationError(f"'{raw}' is not one of {options} and 'other' is not allowed")

    if answer_type == "multi_select":
        if not isinstance(raw, list) or not raw:
            raise AnswerValidationError("multi_select expects a non-empty list of option texts")
        chosen: list[str] = []
        other: list[str] = []
        for value in raw:
            if not isinstance(value, str):
                raise AnswerValidationError("multi_select values must be strings")
            if value in options:
                chosen.append(value)
            elif allow_other:
                other.append(value)
            else:
                raise AnswerValidationError(
                    f"'{value}' is not one of {options} and 'other' is not allowed"
                )
        result: dict[str, Any] = {"options": chosen}
        if other:
            result["other"] = other
        return result

    raise AnswerValidationError(f"unsupported answer type '{answer_type}'")
