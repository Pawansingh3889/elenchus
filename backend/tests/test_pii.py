"""The deterministic gate on what a respondent types.

Two directions, and the second is the one that decides whether this ships. Catching an
email address is easy; not catching a batch code is the whole difficulty, because this
service asks a chilled-fish plant about batch codes and temperatures, and a gate that
refuses the survey's own subject matter gets switched off within a day.

So the negatives here are not invented. They are the messages real respondents sent,
replayed out of tests/live_runs, plus the shapes the domain is made of.
"""

import json
from pathlib import Path

import pytest

from app import pii

LIVE_RUNS = Path(__file__).parent / "live_runs"


# ------------------------------------------------------------------ what it catches


@pytest.mark.parametrize(
    "text",
    [
        "you can reach me on ravi.kapoor@example.com",
        "email me: R.Kapoor+work@sub.example.co.uk",
        "<ops@example.org> is the shift inbox",
    ],
)
def test_an_email_address_is_refused(text: str) -> None:
    assert pii.problem(text) == "email address"


@pytest.mark.parametrize(
    "text",
    [
        "call me on 07700 900123",
        "my mobile is 07700900123",
        "ring 0161 496 0123 and ask for me",
        "+44 7700 900123 any time",
        "+33 1 70 18 99 00",
    ],
)
def test_a_phone_number_is_refused(text: str) -> None:
    assert pii.problem(text) == "phone number"


@pytest.mark.parametrize(
    "text",
    ["my NI is JT 12 34 56 C", "ni number AB123456C", "it's nh 65 43 21 d i think"],
)
def test_a_national_insurance_number_is_refused(text: str) -> None:
    assert pii.problem(text) == "national insurance number"


def test_the_placeholder_hmrc_prints_is_not_a_real_number() -> None:
    """QQ123456C is the example on the forms, and it is on the forms precisely because
    QQ is never issued. Worth its own test: reaching for the documented example is the
    obvious way to write this gate's fixture, and it would have proved nothing."""
    assert pii.problem("my NI is QQ 12 34 56 C") is None


# ------------------------------------------------------------------ what it must not


@pytest.mark.parametrize(
    "text",
    [
        # The subject matter. A bare digit-run rule would refuse every one of these.
        "batch 4021998745 came in warm",
        "code 210398745612 on the pallet",
        "batch AB123456 then",
        "lot 0034567 was the one",
        # Readings and quantities, which is what the rest of the survey collects.
        "was around 6c",
        "reduce yield to 2%",
        "it went from -18 to -12 overnight",
        "training finish in 1 week",
        "4",
        "eleven out of five",
        # Dates and times, written the several ways people write them.
        "started 2026-08-12",
        "on 01/02/2026 the chiller failed",
        "it is worst after two in the afternoon, near the ovens",
        "delivery at 14:30 on 12.08.2026",
        # Site and equipment references, which a postcode rule would have caught. That
        # rule is deliberately absent; this is what it would have cost.
        "the DN31 line is the problem",
        "unit B12 keeps tripping",
    ],
)
def test_the_domains_own_language_is_not_refused(text: str) -> None:
    assert pii.problem(text) is None


def test_a_stock_code_shaped_like_an_ni_number_is_not_refused() -> None:
    """The strict shape is what buys this. D, F, I, Q, U and V cannot open a real NI
    number and O cannot be its second letter, so the codes that would otherwise collide
    with the loose "two letters, six digits, a letter" rule fall outside it."""
    for code in ("DF123456A", "IO123456B", "VU123456C"):
        assert pii.problem(f"the code is {code}") is None


def test_an_ni_suffix_outside_a_to_d_is_not_an_ni_number() -> None:
    assert pii.problem("reference AB123456Z") is None


def test_every_message_a_real_respondent_sent_passes_clean() -> None:
    """No false refusals, proved against the corpus rather than against imagination.

    Every one of these was typed by a person into a real conversation. A detector that
    refuses one of them would have refused that respondent, and this is the direction
    that catches a pattern tightened past what people actually write. The same trick
    test_live_replay.py runs for the grounding gates, one gate over.
    """
    fixtures = sorted(LIVE_RUNS.glob("*.json"))
    assert fixtures, f"nothing in {LIVE_RUNS} to check against"

    refused = []
    for path in fixtures:
        for said in json.loads(path.read_text(encoding="utf-8"))["respondent_messages"]:
            found = pii.problem(said)
            if found is not None:
                refused.append(f"{path.stem}: {found} in {said!r}")
    assert not refused, "real respondent messages refused: " + "; ".join(refused)


def test_an_empty_message_is_not_a_problem() -> None:
    assert pii.problem("") is None
