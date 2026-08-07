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
    SERVED,
    SUPPORTED,
    language_note,
    parse_locale,
    translate,
)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("es", "es"),
        ("pl", "pl"),
        # A region subtag is still the language: es-MX is Spanish.
        ("es-MX", "es"),
        ("en-GB", "en"),
        # The real shape a browser sends, weights and all. The first supported tag wins.
        ("pl-PL,pl;q=0.9,en;q=0.8", "pl"),
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


def test_every_served_locale_covers_every_message() -> None:
    """SERVED, not just SUPPORTED: a run's language is fixed at start_run for its whole
    life, so a retired locale with a missing message would close a French conversation
    with an English sentence as silently as an offered one would."""
    missing = [
        f"{message_id}/{locale}"
        for message_id, by_locale in MESSAGES.items()
        for locale in SERVED
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
    """Models handle "Latvian" more reliably than "lv"."""
    note = language_note("lv")
    assert "Latvian" in note
    assert '"lv"' not in note


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


# ------------------------------------------------------- retired locales, live runs


def test_a_retired_locale_still_serves_the_run_that_carries_it() -> None:
    """fr was withdrawn from the picker, but survey_runs.language is fixed at start_run:
    a respondent halfway through a French interview resumes in French. The catalogue and
    the name table therefore outlive the offering."""
    assert "fr" not in SUPPORTED
    assert translate("closing", "fr") == "C'est tout, merci. Vos réponses sont enregistrées."
    assert "French" in language_note("fr")


def test_a_retired_locale_cannot_start_a_new_run() -> None:
    """The other half of retirement: parse_locale is the gate new runs pass through."""
    assert parse_locale("fr") == "en"
    assert parse_locale("fr-CA,fr;q=0.9") == "en"


def test_the_backend_offering_matches_the_frontend_picker() -> None:
    """The two rosters are maintained by hand in two languages; this is the gate the
    comment on SUPPORTED used to be. A tag offered in the picker but absent here
    conducts the run in English with no error to explain why; one here but not there
    is dead configuration."""
    import re
    from pathlib import Path

    index_ts = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "i18n" / "index.ts"
    source = index_ts.read_text(encoding="utf-8")
    match = re.search(r"export const LOCALES = \{(?P<body>.*?)\} as const", source, flags=re.S)
    assert match, "frontend LOCALES block not found; the roster gate is checking nothing"
    picker = set(re.findall(r"(\w+):\s*\{\s*label", match.group("body")))
    assert picker == set(SUPPORTED)
