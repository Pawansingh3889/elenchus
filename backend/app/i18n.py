"""Locale-aware text for the messages a respondent or author actually reads.

Only the messages a person sees are here. Typed error *codes* stay English and stay
stable, because they are the API's contract: a client switches on ``llm_unavailable``,
and translating that would break every consumer to no one's benefit. What gets
translated is the sentence rendered beside it.

The locale arrives as ``Accept-Language``, which the browser client sets from the
language picker. Parsing is deliberately shallow: the header's full grammar allows
quality weights and multiple entries, and this reads the first tag and matches on its
primary subtag, so "pl-PL,pl;q=0.9,en;q=0.8" resolves to Polish. Anything unrecognised
falls back to English rather than failing, because a message in the wrong language is
recoverable and a 500 while reporting an error is not.
"""

from __future__ import annotations

DEFAULT_LOCALE = "en"

# Keyed by message id, then locale. A locale missing an id falls back to English, which
# is checked by a test rather than left to chance.
#
# The catalogue holds two kinds of locale, and only one is offered. SUPPORTED below is
# the offering: what the picker shows and what a NEW run can be conducted in. The
# retired tags (fr/pt/hi/bn/ar/he/ur, withdrawn from the picker on 7 Aug 2026) stay in
# the catalogue and in LANGUAGE_NAMES because ``survey_runs.language`` is fixed at
# start_run for the life of the run: a respondent halfway through a French interview
# resumes in French, whatever the picker offers today. Their entries can go only when
# no run in the database carries the tag.
MESSAGES: dict[str, dict[str, str]] = {
    "llm_unavailable": {
        "en": "The assistant is briefly unavailable. Please try again in a moment.",
        "de": "Der Assistent ist kurzzeitig nicht verfügbar. Bitte versuchen Sie es gleich erneut.",
        "fil": "Pansamantalang hindi available ang assistant. Subukan ulit maya-maya.",
        "pl": "Asystent jest chwilowo niedostępny. Spróbuj ponownie za moment.",
        "lv": "Asistents īslaicīgi nav pieejams. Lūdzu, mēģiniet vēlreiz pēc brīža.",
        "lt": "Asistentas laikinai nepasiekiamas. Bandykite dar kartą po akimirkos.",
        "ro": "Asistentul este indisponibil pentru scurt timp. Încearcă din nou într-o clipă.",
        "es": (
            "El asistente no está disponible por un momento. "
            "Inténtalo de nuevo en unos instantes."
        ),
        # Retired locales, kept for in-flight runs.
        "fr": "L'assistant est momentanément indisponible. Réessayez dans un instant.",
        "pt": "O assistente está momentaneamente indisponível. Tente novamente daqui a pouco.",
        "hi": "सहायक कुछ देर के लिए उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें।",
        "bn": "সহায়কটি কিছুক্ষণের জন্য অনুপলব্ধ। অনুগ্রহ করে একটু পরে আবার চেষ্টা করুন।",
        "he": "העוזר אינו זמין לרגע. נסה שוב בעוד רגע.",
        "ur": "معاون عارضی طور پر دستیاب نہیں۔ براہِ کرم تھوڑی دیر بعد دوبارہ کوشش کریں۔",
        "ar": "المساعد غير متاح مؤقتًا. يرجى المحاولة مرة أخرى بعد قليل.",
    },
    "closing": {
        "en": "That's everything, thank you. Your answers are saved.",
        "de": "Das war alles, danke. Ihre Antworten sind gespeichert.",
        "fil": "Iyon na lahat, salamat. Naka-save na ang iyong mga sagot.",
        "pl": "To wszystko, dziękujemy. Twoje odpowiedzi są zapisane.",
        "lv": "Tas ir viss, paldies. Jūsu atbildes ir saglabātas.",
        "lt": "Tai viskas, ačiū. Jūsų atsakymai įrašyti.",
        "ro": "Asta e tot, mulțumim. Răspunsurile tale sunt salvate.",
        "es": "Eso es todo, gracias. Tus respuestas están guardadas.",
        # Retired locales, kept for in-flight runs.
        "fr": "C'est tout, merci. Vos réponses sont enregistrées.",
        "pt": "É tudo, obrigado. As suas respostas estão guardadas.",
        "hi": "बस इतना ही, धन्यवाद। आपके उत्तर सहेजे गए हैं।",
        "bn": "এটুকুই, ধন্যবাদ। আপনার উত্তর সংরক্ষিত হয়েছে।",
        "he": "זה הכול, תודה. התשובות שלך נשמרו.",
        "ur": "بس اتنا ہی، شکریہ۔ آپ کے جوابات محفوظ ہو گئے۔",
        "ar": "هذا كل شيء، شكرًا لك. تم حفظ إجاباتك.",
    },
    # One sentence for all three identifier kinds rather than one per kind. The kind is
    # logged for the operator; the respondent needs to know what to remove, and naming
    # the categories does that without the catalogue carrying three near-identical
    # entries in fifteen locales, each a chance to get a translation subtly wrong.
    "pii_in_message": {
        "en": (
            "Please leave personal details like email addresses, phone numbers or ID "
            "numbers out of your answer, then send it again."
        ),
        "de": (
            "Bitte lassen Sie persönliche Angaben wie E-Mail-Adressen, Telefonnummern "
            "oder Ausweisnummern aus Ihrer Antwort weg und senden Sie sie erneut."
        ),
        "fil": (
            "Pakiusap, huwag isama ang personal na detalye tulad ng email address, "
            "numero ng telepono o ID number. Ipadala muli ang iyong sagot nang wala ang "
            "mga ito."
        ),
        "pl": (
            "Nie podawaj danych osobowych, takich jak adresy e-mail, numery telefonu "
            "czy numery identyfikacyjne. Wyślij odpowiedź ponownie bez nich."
        ),
        "lv": (
            "Lūdzu, neiekļaujiet personas datus, piemēram, e-pasta adreses, tālruņa "
            "numurus vai identifikācijas numurus. Nosūtiet atbildi vēlreiz bez tiem."
        ),
        "lt": (
            "Prašome nenurodyti asmens duomenų, tokių kaip el. pašto adresai, telefono "
            "numeriai ar asmens kodai. Išsiųskite atsakymą dar kartą be jų."
        ),
        "ro": (
            "Te rugăm să nu incluzi date personale precum adrese de e-mail, numere de "
            "telefon sau numere de identificare. Trimite răspunsul din nou fără ele."
        ),
        "es": (
            "No incluyas datos personales como direcciones de correo electrónico, "
            "números de teléfono o números de identificación. Envía tu respuesta de "
            "nuevo sin ellos."
        ),
        # Retired locales, kept for in-flight runs.
        "fr": (
            "Merci de ne pas inclure de données personnelles comme des adresses e-mail, "
            "des numéros de téléphone ou des numéros d'identification. Renvoyez votre "
            "réponse sans elles."
        ),
        "pt": (
            "Não inclua dados pessoais como endereços de e-mail, números de telefone ou "
            "números de identificação. Envie a sua resposta novamente sem eles."
        ),
        "hi": (
            "कृपया अपने उत्तर में ईमेल पता, फ़ोन नंबर या पहचान संख्या जैसी निजी जानकारी शामिल न करें। "
            "इनके बिना उत्तर दोबारा भेजें।"
        ),
        "bn": (
            "অনুগ্রহ করে আপনার উত্তরে ইমেল ঠিকানা, ফোন নম্বর বা পরিচয় নম্বরের মতো ব্যক্তিগত তথ্য "
            "দেবেন না। সেগুলি ছাড়া উত্তরটি আবার পাঠান।"
        ),
        "he": (
            "אנא אל תכללו פרטים אישיים כמו כתובות אימייל, מספרי טלפון או מספרי זהות. "
            "שלחו את התשובה שוב בלעדיהם."
        ),
        "ur": (
            "براہِ کرم اپنے جواب میں ای میل پتہ، فون نمبر یا شناختی نمبر جیسی ذاتی معلومات "
            "شامل نہ کریں۔ ان کے بغیر جواب دوبارہ بھیجیں۔"
        ),
        "ar": (
            "يرجى عدم تضمين بيانات شخصية مثل عناوين البريد الإلكتروني أو أرقام الهاتف أو "
            "أرقام الهوية. أعد إرسال إجابتك بدونها."
        ),
    },
    "database_unavailable": {
        "en": "The service cannot reach its database right now. Please try again in a moment.",
        "de": (
            "Der Dienst erreicht seine Datenbank gerade nicht. "
            "Bitte versuchen Sie es gleich erneut."
        ),
        "fil": "Hindi maabot ng serbisyo ang database nito ngayon. Subukan ulit maya-maya.",
        "pl": (
            "Usługa nie może teraz połączyć się ze swoją bazą danych. "
            "Spróbuj ponownie za moment."
        ),
        "lv": (
            "Pakalpojums pašlaik nevar sasniegt savu datubāzi. "
            "Lūdzu, mēģiniet vēlreiz pēc brīža."
        ),
        "lt": "Paslauga šiuo metu nepasiekia savo duomenų bazės. Bandykite dar kartą po akimirkos.",
        "ro": "Serviciul nu poate accesa baza de date acum. Încearcă din nou într-o clipă.",
        "es": (
            "El servicio no puede conectar con su base de datos ahora mismo. "
            "Inténtalo de nuevo en unos instantes."
        ),
        # Retired locales, kept for in-flight runs.
        "fr": "Le service ne peut pas joindre sa base de données. Réessayez dans un instant.",
        "pt": "O serviço não consegue aceder à base de dados. Tente novamente daqui a pouco.",
        "hi": "सेवा अभी अपने डेटाबेस तक नहीं पहुँच पा रही। कृपया थोड़ी देर बाद प्रयास करें।",
        "bn": "সেবাটি এখন তার ডেটাবেসে পৌঁছাতে পারছে না। একটু পরে আবার চেষ্টা করুন।",
        "he": "השירות אינו מצליח להגיע למסד הנתונים כרגע. נסה שוב בעוד רגע.",
        "ur": "سروس اس وقت اپنے ڈیٹابیس تک نہیں پہنچ پا رہی۔ تھوڑی دیر بعد کوشش کریں۔",
        "ar": "لا يستطيع النظام الوصول إلى قاعدة بياناته حاليًا. يرجى المحاولة مرة أخرى بعد قليل.",
    },
}

# The offering: what the picker shows and what a new run may be conducted in. Must match
# frontend/lib/i18n/index.ts LOCALES, which tests/test_i18n.py enforces by reading that
# file; a tag offered there but missing here would conduct the run in English with no
# error to explain why. Retired tags live on in MESSAGES/LANGUAGE_NAMES above and below,
# but never here: parse_locale is what stops NEW runs starting in them.
SUPPORTED = ("en", "es", "de", "pl", "lv", "lt", "ro", "fil")

# Every tag any run has ever been conducted in, for the coverage test: a tag on a stored
# run that lost its catalogue entries would resume in the wrong language silently.
SERVED = SUPPORTED + ("fr", "pt", "hi", "bn", "ar", "he", "ur")


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


# Language names rather than codes. A model handles "Latvian" more reliably than "lv",
# and an unlisted code is passed through as-is so adding a locale to the UI needs no
# change here: the worst case is the model receiving a tag it can still recognise.
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "de": "German",
    "pl": "Polish",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "ro": "Romanian",
    "fil": "Filipino",
    # Retired from the picker, still named: a run started in one of these resumes in it,
    # and "Reply in French" steers a model far more reliably than "Reply in fr".
    "fr": "French",
    "pt": "Portuguese",
    "hi": "Hindi",
    "bn": "Bengali",
    "ur": "Urdu",
    "ar": "Arabic",
    "he": "Hebrew",
}


def language_note(language: str) -> str:
    """The instruction that makes a run happen in the respondent's language.

    Kept out of the prompt file and injected per run, because the prompt is versioned
    and shared: one file per language would multiply every future prompt edit by the
    number of locales, and they would drift apart within a release.

    The second half is the load-bearing half. Question text and options are the
    author's, stored in the author's language, and an option is the key an answer is
    recorded under: `_canonical_option` matches what comes back against that exact
    text. Translate an option on the way out and the model will translate it on the way
    back, and the answer will match nothing.
    """
    name = LANGUAGE_NAMES.get(language, language)
    if name == "English":
        return "Speak English."
    return (
        f"## Reply in {name}\n\n"
        f"The survey above may be written in another language. That is the author's "
        f"language, not the respondent's, and you do not mirror it.\n\n"
        f"Speak {name}. Everything you say to the respondent is in {name}: questions, "
        f"follow-ups and acknowledgements. Read their answers in whatever language they "
        f"write, including English.\n\n"
        f"Two things stay exactly as given, whatever language you are speaking. When you "
        f"put a question to the respondent you may render it in {name}, but when you call "
        f"a tool, any option value you pass back must be copied character for character "
        f"from the options listed in the briefing, untranslated. Those strings are how the "
        f"answer is stored and matched; a translated one matches nothing and the answer is "
        f"lost.\n\n"
        f"Before you write, check: is what you are about to say in {name}?"
    )
