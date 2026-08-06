"""Locale negotiation and the message catalogue.

The error *code* is the contract and stays English; the sentence beside it follows the
caller. These tests pin both halves of that, because getting it backwards, translating
the code, breaks every consumer silently.
"""

import pytest

from app.i18n import (
    DEFAULT_LOCALE,
    LANGUAGE_NAMES,
    MESSAGES,
    SUPPORTED,
    language_note,
    parse_locale,
    translate,
)


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
        # A real language the app does not offer. Kept as a language rather than
        # nonsense, because "unsupported" and "malformed" are different paths.
        ("ja", "en"),
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
    assert translate("llm_unavailable", "ja") == MESSAGES["llm_unavailable"][DEFAULT_LOCALE]


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


# --------------------------------------------------------------- language note


def test_english_gets_a_short_note_and_no_lecture() -> None:
    """The default path is most runs. A page of instructions about not translating
    options is noise when the survey and the respondent are already in English."""
    note = language_note("en")
    assert note == "Speak English."


def test_a_named_language_is_used_rather_than_its_code() -> None:
    """Models handle "Arabic" more reliably than "ar"."""
    note = language_note("ar")
    assert "Arabic" in note
    assert '"ar"' not in note


def test_an_unknown_code_is_passed_through_rather_than_failing() -> None:
    """Adding a locale to the picker must not require editing this table first. The
    worst case is the model receiving a tag it can still recognise."""
    assert "zu" in language_note("zu")


def test_the_note_forbids_translating_option_values() -> None:
    """The load-bearing half. Options are the author's text and the key an answer is
    stored under: _canonical_option matches what comes back against that exact string,
    so a translated option matches nothing and the answer is lost."""
    note = language_note("es")
    assert "character for character" in note
    assert "untranslated" in note


def test_every_locale_offered_in_the_ui_has_a_language_name() -> None:
    """A locale in the picker but missing here would reach the model as a bare code."""
    for locale in SUPPORTED:
        assert locale in LANGUAGE_NAMES
