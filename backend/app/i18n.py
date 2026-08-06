"""Locale-aware text for the messages a respondent or author actually reads.

Only the messages a person sees are here. Typed error *codes* stay English and stay
stable, because they are the API's contract: a client switches on ``llm_unavailable``,
and translating that would break every consumer to no one's benefit. What gets
translated is the sentence rendered beside it.

The locale arrives as ``Accept-Language``, which the browser client sets from the
language picker. Parsing is deliberately shallow: the header's full grammar allows
quality weights and multiple entries, and this reads the first tag and matches on its
primary subtag, so "ar-EG,ar;q=0.9,en;q=0.8" resolves to Arabic. Anything unrecognised
falls back to English rather than failing, because a message in the wrong language is
recoverable and a 500 while reporting an error is not.
"""

from __future__ import annotations

DEFAULT_LOCALE = "en"

# Keyed by message id, then locale. A locale missing an id falls back to English, which
# is checked by a test rather than left to chance.
MESSAGES: dict[str, dict[str, str]] = {
    "llm_unavailable": {
        "en": "The assistant is briefly unavailable. Please try again in a moment.",
        "es": (
            "El asistente no está disponible por un momento. "
            "Inténtalo de nuevo en unos instantes."
        ),
        "ar": "المساعد غير متاح مؤقتًا. يرجى المحاولة مرة أخرى بعد قليل.",
    },
    "database_unavailable": {
        "en": "The service cannot reach its database right now. Please try again in a moment.",
        "es": (
            "El servicio no puede conectar con su base de datos ahora mismo. "
            "Inténtalo de nuevo en unos instantes."
        ),
        "ar": "لا يستطيع النظام الوصول إلى قاعدة بياناته حاليًا. يرجى المحاولة مرة أخرى بعد قليل.",
    },
}

SUPPORTED = ("en", "es", "ar")


def parse_locale(accept_language: str | None) -> str:
    """The best supported locale for an Accept-Language header.

    Matches on the primary subtag, so "es-MX" is Spanish and "en-GB" is English, and
    returns the default for anything unsupported or absent.
    """
    if not accept_language:
        return DEFAULT_LOCALE
    for entry in accept_language.split(","):
        tag = entry.split(";")[0].strip().lower()
        if not tag:
            continue
        primary = tag.split("-")[0]
        if primary in SUPPORTED:
            return primary
    return DEFAULT_LOCALE


def translate(message_id: str, locale: str) -> str:
    """The message in the requested locale, falling back to English.

    A missing id is a programming error and raises: the alternative is returning the id
    itself, which reaches a respondent as "llm_unavailable" and reads as a crash.
    """
    by_locale = MESSAGES[message_id]
    return by_locale.get(locale, by_locale[DEFAULT_LOCALE])
