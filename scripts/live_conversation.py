"""Drive a real conversation end to end against the live Anthropic API.

The test suite is mocked at the LLM client boundary, deliberately: it asserts what the
engine offers, accepts and refuses, and it runs without a key. What it cannot assert is
whether a real model, given those rails, behaves well inside them. A fake LLM does what
the test tells it to, so it never tries to work around the engine's design.

This script is what closes that gap, and it has earned its place: it found a fabricated
rating, a `"placeholder"` string written to unlock a tool, a date resolved two years wrong,
a discarded free-text answer, and an invented value on a question the respondent was free
to skip. None of those were visible to the mocked suite.

    python scripts/live_conversation.py            # ten questions, every answer type
    python scripts/live_conversation.py evasive    # five questions, uncooperative replies

Needs a funded ANTHROPIC_API_KEY in .env and a running stack (docker compose up).
"""

import json
import sys
import urllib.error
import urllib.request

API = "http://localhost:8000/api/v1"
AUTHOR = "00000000-0000-0000-0000-0000000000a1"
RESPONDENT = "00000000-0000-0000-0000-0000000000b1"

# Cooperative, but phrased the way people speak rather than the way forms expect: a
# relative date, a number hedged across a sentence, and two selects answered in the
# respondent's own words. One reply arrives after a follow-up rather than before it.
BROAD = {
    "prompt": (
        "An onboarding experience survey for people who joined the company in the last "
        "year. Ten questions, one of each kind where you can: their job title as short "
        "text, which date they started as a date, how many days of induction they got as "
        "a number, how they would rate the first week as a rating, which team they joined "
        "as a single select, which parts of onboarding they used as a multi select, "
        "whether they were given a buddy as yes/no, what went well as long text, what "
        "they would change as long text, and how likely they are to still be here in two "
        "years as a rating. Allow follow-ups on the two open-ended questions and on the "
        "first-week rating. Make the buddy question and the two-year question optional."
    ),
    "replies": [
        "data analyst, on the reporting side",
        "i started on the 3rd of march this year",
        "two days i think, maybe three including the IT bit",
        "yeah it was alright, solid 4",
        "reporting and insight",
        "the handbook and the buddy scheme, and there was a slack channel too",
        "yeah i had one",
        "the team were really welcoming, people made time for me",
        "less of the generic corporate video honestly",
        "the compliance modules were the same ones everyone does regardless of role",
        "hard to say really",
        "probably a 3",
        "that's me done",
        "nothing else",
    ],
}

# Deliberately uncooperative: vague, then a refusal, an out-of-range rating, and a select
# answered with something that maps to nothing. Every reply here should end as an honest
# unanswerable rather than a value the respondent never gave.
EVASIVE = {
    "prompt": (
        "A short check-in for warehouse staff about the new shift handover process. Five "
        "questions: their role, how well handover is working as a rating, what one thing "
        "they would change, which shift they usually work as a single select, and whether "
        "they would recommend the new process. Allow follow-ups on the open-ended ones."
    ),
    "replies": [
        "i sort of run the line i guess",
        "mostly making sure the handover actually happens",
        "honestly it's been a bit of a mess",
        "rather not say",
        "eleven out of five",
        "4",
        "yeah fine",
        "no",
        "not really",
        "that's all",
    ],
}

SCENARIOS = {"broad": BROAD, "evasive": EVASIVE}


def call(method: str, path: str, user: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{API}{path}", data=data, method=method)
    request.add_header("X-User-Id", user)
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        print(f"\n  HTTP {exc.code} on {method} {path}\n  {exc.read().decode()}\n")
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"\n  cannot reach {API} ({exc.reason}). Is the stack up?\n")
        sys.exit(1)


def describe(question: dict) -> str:
    marks = ("  +follow-ups" if question["allow_follow_ups"] else "") + (
        "" if question["required"] else "  (optional)"
    )
    options = f"  {question['options']}" if question["options"] else ""
    write_in = "  +write-in" if question["allow_other"] else ""
    return (
        f"    {question['position']}. [{question['answer_type']}] "
        f"{question['text']}{options}{write_in}{marks}"
    )


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "broad"
    if name not in SCENARIOS:
        print(f"unknown scenario {name!r}; choose from {', '.join(SCENARIOS)}")
        sys.exit(2)
    scenario = SCENARIOS[name]

    print(f"=== generating ({name}) ===")
    template = call("POST", "/templates/generate", AUTHOR, {"prompt": scenario["prompt"]})
    print(f"  {template['title']}")
    for question in template["questions"]:
        print(describe(question))

    call("POST", f"/templates/{template['id']}/publish", AUTHOR)
    print("\n=== conducting ===")
    run = call("POST", "/runs", RESPONDENT, {"template_id": template["id"]})
    print(f"  assistant: {run['messages'][-1]['content']}")

    for reply in scenario["replies"]:
        if run["status"] != "in_progress":
            break
        print(f"  respondent: {reply}")
        run = call("POST", f"/runs/{run['id']}/messages", RESPONDENT, {"content": reply})
        print(f"  assistant: {run['messages'][-1]['content']}")
        print(f"             [{run['answered']} of {run['total']} answered]")

    print(f"\n=== run {run['status']} ===")
    detail = call("GET", f"/templates/{template['id']}/runs/{run['id']}", AUTHOR)
    for answer in detail["answers"]:
        kind = " (follow-up)" if answer["kind"] == "follow_up" else ""
        print(f"  {answer['question_text']}{kind}\n    -> {answer['value']}")


if __name__ == "__main__":
    main()
