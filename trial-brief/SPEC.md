# Survey Service — Functional Specification

Version 1.0 · 2026-07-20

## 1. Purpose

A self-contained, embeddable survey service. It must be **repeatable**: designed as a module with a clean HTTP API so the host platform can later mount it in many places (onboarding, audits, feedback, clarification prompts). Nothing in it may assume it is the whole product.

Two personas:

- **Author** (admin) — creates, edits and publishes survey templates.
- **Respondent** (end-user) — completes a published survey conversationally.

## 2. Scope

### 2.1 Must have

**A. Template authoring — builder**
- Create/edit/delete draft templates: title, description, and an ordered list of questions.
- Question fields: `text`, `answer_type`, `options` (for select types), `allow_other` (write-in on select types), `required`, `allow_follow_ups` (whether the LLM may probe this answer).
- Answer types (controlled list, exactly these): `single_select · multi_select · yes_no · short_text · long_text · rating (1–5) · number · date`.
- Reorder and delete questions. A live preview of the conversational rendering is strongly recommended (see the demo HTML).
- **Publish**: publishing snapshots the template into an immutable version (see data model). Drafts can keep evolving; respondents only ever see published versions. Re-publishing creates version n+1.

**B. Template authoring — natural language**
- The author describes the survey in free text ("An onboarding survey for factory staff: role, systems they use daily, their biggest data frustrations…").
- The LLM returns a complete draft template via a **schema-constrained tool call** (see ARCHITECTURE.md §LLM) — never free-text parsed into a template.
- The draft lands in the builder for review and editing before publish. NL creation and hand-building are two entrances to the same template — not two systems.

**C. Conversational conduct**
- A respondent starts a **run** against a published template version.
- Chat UI, one question at a time: assistant message + input affordance matched to the answer type (option chips for selects/yes-no, star row for rating, text box otherwise, date/number inputs). Free-text replies to select questions are allowed — the LLM maps them to an option or the `other` write-in.
- The LLM phrases questions naturally and conversationally (it may rephrase, acknowledge the previous answer, keep a warm tone) but **must ask every required template question** and record every answer against its question.
- **Follow-ups:** where a question has `allow_follow_ups` and the answer merits it (vague, surprising, or high-signal), the LLM may ask up to **2** follow-up questions before moving on. Follow-ups are stored as answers linked to the parent question, flagged as `follow_up`. The engine — not the model — enforces the cap.
- On the last answer: a closing message and the run is marked completed.
- A refresh must not lose progress: run state lives server-side; reloading the page resumes at the current question.

**D. Persistence & results**
- Everything in Postgres. Every answer stamped with `answered_by` (the respondent user), `answered_at`, and the template version it was answered against.
- The full conversation transcript is stored per run.
- A minimal results view for authors: list runs per template (respondent, status, started/completed), drill into one run to see structured answers + transcript.

**E. Users**
- A `users` table and seed data (a few authors and respondents). Authentication is out of scope: a dev-auth mechanism (e.g. user picker → `X-User-Id` header) is fine **provided** it is isolated behind a single auth dependency that a real identity provider could replace without touching feature code. This is an explicit trial simplification, not a hidden fallback — say so in the code.

### 2.2 Stretch (only if must-haves are done and solid — in a 4-day trial we don't expect these)

In rough priority order:
1. **AI summary on completion** — the LLM produces a structured summary of a completed run (key facts, notable quotes), stored with the run and shown in results.
2. **Conditional visibility** — a declarative `show_when: {question, op, value}` per question (as in the demo HTML). No jump-routing.
3. **Save & continue later** — an explicit "finish later" affordance; the run reappears on the respondent's home.
4. **Estimated completion time** shown before starting, computed from question count/types.

### 2.3 Explicitly out of scope — do not build

Skills/knowledge-library integration, governance lifecycles (owners, reviewers, certification), review cadences, many-to-many output mapping, prefill from profiles/SSO, answer piping tokens, repeat-for-each loops, media answer types (voice/video/image/signature/location/drawing/upload), notifications/assignment/reminders, duplicate or contradiction detection, embeddings/semantic search, multi-tenancy, real authentication. If you finish everything, deepen quality — don't widen scope.

## 3. Data model (required shape — refine details as you see fit)

- `users` — id (uuid), email, display_name, role (`author` | `respondent`), created_at.
- `survey_templates` — id, title, description, status (`draft` | `published` | `archived`), created_by → users, created_at, updated_at. Holds the *editable draft*, with its questions in `survey_questions`.
- `survey_questions` — id, template_id, position, text, answer_type, options (jsonb), allow_other, required, allow_follow_ups.
- `survey_template_versions` — id, template_id, version (int, unique per template), definition (jsonb snapshot of title/description/questions at publish time), published_at, published_by. **Immutable.** Runs reference this table so later edits can never mutate what a respondent answered.
- `survey_runs` — id, template_version_id, respondent_id → users, status (`in_progress` | `completed` | `abandoned`), current_question index/id, started_at, completed_at, summary (jsonb, stretch).
- `answers` — id, run_id, question_id (from the version snapshot), kind (`scripted` | `follow_up`), question_text (denormalised — required for follow-ups, whose text the LLM invented), value (jsonb, shaped per answer_type), answered_by, answered_at.
- `run_messages` — id, run_id, role (`assistant` | `user`), content, created_at, optional answer_id.

Alembic migrations from the first table. No `create_all` in app code.

## 4. API surface (indicative)

All under `/api/v1`, OpenAPI-documented, Pydantic v2 request/response schemas.

```
POST   /templates                    create draft
GET    /templates                    list (filter by status)
GET    /templates/{id}               draft + questions
PUT    /templates/{id}               update draft (title/description/questions)
POST   /templates/{id}/publish       snapshot → new immutable version
POST   /templates/generate           NL prompt → draft template (LLM)
GET    /templates/{id}/runs          results list (author)
GET    /runs/{id}                    run state, answers, transcript
POST   /runs                         start a run {template_id} → first assistant message
POST   /runs/{id}/messages           respondent turn → assistant reply / completion
```

## 5. Acceptance criteria (the demo script, effectively)

1. Author types an NL description → a sensible multi-question draft appears in the builder.
2. Author edits it (reword a question, change a type, add an option, reorder), publishes; publishing a second time produces version 2, and an in-flight run on version 1 is unaffected.
3. Respondent completes the survey conversationally; a free-text reply to a select question is correctly mapped to an option; at least one follow-up fires on an `allow_follow_ups` question and the cap of 2 is enforced by the engine.
4. Mid-run page refresh resumes at the current question with history intact.
5. The results view shows the completed run: every scripted question answered, follow-ups attached to their parent, every answer stamped with respondent + timestamp + template version.
6. Malformed LLM output (force it if you must, in a test) never corrupts a run — the engine rejects it and retries or fails loudly.
