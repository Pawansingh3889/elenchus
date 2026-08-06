"""Locale negotiation and the message catalogue.

The error *code* is the contract and stays English; the sentence beside it follows the
caller. These tests pin both halves of that, because getting it backwards, translating
the code, breaks every consumer silently.
"""

import pytest

from app.i18n import DEFAULT_LOCALE, MESSAGES, SUPPORTED, parse_locale, translate


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("es", "es"),
        ("ar", "ar"),
        # A region subtag is still the language: es-MX is Spanish.
        ("es-MX", "es"),
        ("en-GB", "en"),
        # The real shape a browser sends, weights and all. The first supported tag wins.
        ("ar-EG,ar;q=0.9,en;q=0.8", "ar"),
        # Unsupported, absent and malformed all land on English rather than raising: a
        # wrong language is recoverable, a 500 while reporting an error is not.
        ("de", "en"),
        ("", "en"),
        (None, "en"),
        (";;;", "en"),
        ("   ", "en"),
    ],
)
def test_locale_negotiation(header: str | None, expected: str) -> None:
    assert parse_locale(header) == expected


def test_every_supported_locale_covers_every_message() -> None:
    """A locale that is offered in the picker but missing a message would fall back
    silently, giving a respondent one English sentence in an otherwise Arabic page."""
    missing = [
        f"{message_id}/{locale}"
        for message_id, by_locale in MESSAGES.items()
        for locale in SUPPORTED
        if locale not in by_locale
    ]
    assert not missing, f"untranslated: {missing}"


def test_an_unknown_locale_falls_back_rather_than_failing() -> None:
    assert translate("llm_unavailable", "de") == MESSAGES["llm_unavailable"][DEFAULT_LOCALE]


def test_an_unknown_message_id_raises() -> None:
    """Returning the id would reach a respondent as "llm_unavailable", which reads as a
    crash. Better to fail where the mistake is."""
    with pytest.raises(KeyError):
        translate("no_such_message", "en")


def test_the_translations_are_actually_different() -> None:
    """Guards against a copy-paste that leaves English in a translated slot, which is
    invisible to every check except reading it."""
    for message_id, by_locale in MESSAGES.items():
        english = by_locale["en"]
        for locale, text in by_locale.items():
            if locale != "en":
                assert text != english, f"{message_id}/{locale} is still English"
