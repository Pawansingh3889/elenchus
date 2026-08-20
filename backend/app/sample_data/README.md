# Sample dataset

A small, curated set of realistic surveys and conducted runs, drawn from real use of
the service and cleaned up for reuse. It exists so a fresh database, a demo, and the
test suite all have meaningful content instead of empty tables.

The JSON files in this directory are the committed source of truth.

## What's in it

**`surveys.json`** — seven published surveys, each with its title, description, author,
and the questions (the shape `publish` snapshots used to freeze into a version):

| Key | Title | Answer types exercised |
| --- | --- | --- |
| `new-hire-onboarding` | New Hire Onboarding Survey | rating, short/long text |
| `team-lead` | Team Lead Survey | single_select, rating, number, text |
| `batch-code-temperature` | Batch Code and Temperature Management Survey | multi_select, single_select, number, yes_no, text |
| `factory-floor-compliance` | Factory Floor Compliance Survey for Supervisors | mixed, with a follow-up |
| `safety-equipment-ppe` | Safety Equipment and PPE Survey | select, text, yes_no |
| `shift-handover` | Shift Handover Survey | rating, text, yes_no |
| `ai-tools-plant` | AI tools in the plant | yes_no, rating, conditional multi_select, single_select with write-ins, always-once follow-ups |

**`runs.json`** — thirteen conducted runs with verbatim transcripts and recorded answers:

| Run against | Respondent | Status | Notes |
| --- | --- | --- | --- |
| `new-hire-onboarding` | remy | completed | includes a declined ("unanswerable") answer |
| `team-lead` | rosa | completed | one answer per type |
| `batch-code-temperature` | ravi | completed | includes a follow-up probe |
| `factory-floor-compliance` | ravi | in_progress | resume + follow-up coverage |
| `safety-equipment-ppe` | rosa, ravi | completed | write-in answers |
| `shift-handover` | remy, ravi | completed | probe drew out the scripted answer |
| `ai-tools-plant` | rosa, ravi, remy, noor, rohan | completed | vague rating declined, conditional question skipped, rewind, off-script chat steered back, write-ins kept |

Everything refers to users by **key** — the email local-part of a seed user
(`ava`, `arjun` are authors; `rosa`, `ravi`, `remy` are respondents). The loader
resolves keys to seeded user ids, so the data is portable across databases.

## How it's used

- **Seeding** — `app.seed` calls `load_sample_data(session)` after inserting users, so
  every boot yields a database with these surveys and runs. It is idempotent (keyed on
  the fixtures' stable ids), so re-running seeds nothing twice.
- **Tests** — `tests/test_sample_data.py` treats the runs as golden data: it checks the
  fixtures are internally consistent, replays the completed conversations through the
  conduct engine and asserts it reproduces the recorded answers, and loads everything
  into a database to exercise the results and export paths against real content.

## Shape

```jsonc
// surveys.json — one entry per survey
{
  "key": "team-lead",
  "template_id": "<uuid>",
  "title": "Team Lead Survey",
  "description": "…",
  "created_by": "arjun",                 // author key
  "version": {
    "version_id": "<uuid>",
    "number": 1,
    "published_by": "arjun",
    "definition": { "title": "…", "description": "…", "questions": [ /* … */ ] }
  }
}

// runs.json — one entry per conducted run
{
  "run_id": "<uuid>",
  "survey_key": "team-lead",
  "respondent": "rosa",                   // respondent key
  "status": "completed",                  // or "in_progress"
  "current_question_index": 6,
  "probes_asked": {},                     // follow-ups asked per question id
  "completed": true,
  "messages": [ { "role": "assistant", "content": "…" }, /* … */ ],
  "answers":  [ { "question_id": "<uuid>", "kind": "scripted",
                  "question_text": "…", "value": { "option": "Team Lead" } }, /* … */ ]
}
```

Answer `value` is stored shaped per answer type — `{"rating": 4}`, `{"text": "…"}`,
`{"option": "…"}`, `{"options": [...]}`, `{"yes_no": true}`, `{"number": 4}`, or a
declined `{"unanswerable": "…"}` — matching what the conduct engine writes.

## Regenerating

The data was extracted once from a live database and hand-curated (author-as-respondent
runs re-pointed to real respondents; empty runs dropped). It is not auto-generated on
build. To refresh it from a database, re-run the extraction and re-apply the same
cleaning, then commit the updated JSON.
