# What ViewOps Survey Service does

A short, functional tour of the application — what it is, what you can do with it,
and what it produces. For how to run or develop it, see the [README](../README.md)
and [DEVELOPING.md](DEVELOPING.md).

## In one sentence

ViewOps is a standalone, embeddable survey service where **authors** build survey
templates (by hand or by describing them to an LLM) and publish immutable versions,
and **respondents** complete those surveys through a conversational, LLM-driven chat
that stays on rails.

## The two halves

### 1. Authoring — building a survey
An author creates a survey template in one of two interchangeable ways:

- **By hand** in a builder UI — add questions, choose an answer type
  (short text, rating, single-select, etc.), mark questions required or optional,
  and allow follow-ups where useful.
- **By describing it in natural language** — the author types something like
  *"an onboarding check-in for new hires"* and the LLM drafts the questions via a
  schema-constrained tool call. Both paths edit the **same** draft.

**Publishing** freezes the current draft into an **immutable version**. The draft
keeps evolving separately, so you can publish v1, keep editing, and publish v2 later
without disturbing anyone already answering v1.

### 2. Conducting — answering a survey
A respondent opens a published survey and answers it in a **chat**. The experience is
conversational, but the engine — not the model — stays in control:

- The engine owns which question is current, whether the run is complete, and how many
  follow-ups have been spent (so a respondent can't be probed indefinitely).
- The LLM may ask a natural follow-up to clarify an answer, but every answer is
  **validated against the question's declared type** before it is recorded.
- Runs are **persisted and resumable** — a respondent can leave and come back to a
  half-finished survey.

## Who uses it

| Role | What they do |
|------|--------------|
| **Author** | Build/draft templates, publish versions, read the responses |
| **Respondent** | Complete a published survey through the chat runner |

(Dev auth is deliberately thin: each request identifies its caller with an
`X-User-Id` header; a real deployment swaps that for a proper identity provider.)

## What the application outputs

For every completed (or in-progress) survey run, an author can open the **Responses**
view for a template and see:

- **Structured answers** — each answer captured in the shape of its question type
  (e.g. a chosen option, a rating value, or free text), validated at capture time.
- **The full transcript** — the complete conversation between the respondent and the
  runner, in order, so you can see exactly how each answer was arrived at.
- **Follow-ups marked** — any question the model chose to ask as a follow-up is
  flagged, so authors can tell engine-driven questions from the ones they wrote.
- **Versioned context** — responses are tied to the immutable template version the
  respondent actually answered, so results stay meaningful even after the template
  changes.

## A typical end-to-end flow

1. An author signs in, drafts *"Onboarding check-in"* (by hand or with AI), and
   **publishes** it as version 1.
2. A respondent opens the survey and answers it in chat; the engine validates each
   answer and records the transcript.
3. The author edits the survey and **publishes version 2** — anyone mid-way through
   v1 is unaffected.
4. The author opens **Responses** and reads the structured answers plus the full
   transcript for each run.

## Design principles (why it behaves this way)

- **LLM on rails** — every model output the system acts on comes back through a
  schema-constrained tool call and is validated before use. The engine owns state;
  the model is a constrained collaborator.
- **Immutable published versions** — publishing snapshots the draft, so results are
  always tied to exactly what the respondent saw.
- **No silent fallbacks** — missing or invalid data fails loudly with a typed error
  and the correct HTTP status, rather than guessing a default.
- **Resilient to provider outages** — an optional backup model (any OpenAI-compatible
  endpoint) can be configured; the app uses the primary and switches to the backup only
  when the primary actually fails. The backup's answers pass through exactly the same
  validation as the primary's, so the on-rails guarantees are unchanged.
