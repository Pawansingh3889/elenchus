# Elenchus Survey Service — Project Guide

Standing instructions for *how* we build this service. The brief in `trial-brief/`
is the source of truth for *what*; this file is the source of truth for *how*.

## What this is

A standalone, embeddable survey service, in two halves:

- **Authoring** — an author builds a survey template either by describing it in natural
  language (the LLM drafts it via a schema-constrained tool call) or by hand in a builder
  UI. Both edit the same draft. Publishing opens the survey for answers.
- **Conducting** — a respondent completes a published survey through a conversational,
  LLM-driven chat. The engine owns state; the model is a constrained collaborator.

## Non-negotiable architecture (from ARCHITECTURE.md)

- **Backend**: Python 3.12, FastAPI, fully async. SQLAlchemy 2.x async + Alembic.
  PostgreSQL. Pydantic v2 on every request/response body.
- **Layering**: `routes → services → repositories → models`. Routes are thin (parse,
  resolve the current user, call one service method, shape the response). Services own
  business logic and transactions. Repositories own every query. No ORM/session access
  above the repository layer.
- **Organise by domain**, not by layer: `app/users`, `app/templates`, `app/runs`,
  `app/conduct`, `app/llm`, `app/auth`.
- **Frontend**: Next.js App Router + TypeScript. TanStack Query for all server state.
  Zustand only for local UI state.
- **LLM on rails**: every model output the system acts on returns through a
  schema-constrained tool call, validated before use. The conduct engine — not the model —
  owns which question is current, whether the run is complete, and how many follow-ups are
  spent. Prompts are versioned files under `backend/app/llm/prompts/`. One LLM client
  module owns the HTTP calls, timeouts, and token logging.
- **No fallbacks**: missing or invalid data fails loudly with a typed error and the correct
  HTTP status. No `.get(x, default)` shrugs over required data.

## Data model

See SPEC.md §3. Tables: `users`, `survey_templates`, `survey_questions`,
`survey_runs`, `answers`, `run_messages`, and `llm_spans` (the trace of every turn, see
`app/trace/models.py`).
Alembic migrations from the first table; no `create_all` in application code.

## Conventions

- **Commits**: conventional and atomic, on `feature/<slug>` branches merged to main.
  Commit only when a unit is complete and verified (builds, migration applies, tests pass).
- **Backend quality**: `make gate` clean, which is `ruff` + `black` + `mypy` + import
  contracts + guards + the suite, and is what CI runs. `pytest` + `pytest-asyncio`; the
  conduct engine and publish/versioning logic are the test priorities. The LLM is mocked at
  the client-wrapper boundary so tests run without an API key.
- **Frontend quality**: `make front-gate` clean, which is `tsc --noEmit` + `eslint` +
  `vitest`, run inside the frontend container because there is no node on the host.
  Frontend tests are written when something breaks, so each one names a bug that
  actually happened rather than a failure someone imagined. There is no browser
  suite: rendering is verified by looking at the rendered page (screenshot, computed
  styles), not by a runner.
- **Secrets**: `.env` is git-ignored, `.env.example` is committed. No provider key ever
  enters the repo.
- **Prompts as code**: versioned under `backend/app/llm/prompts/`, loaded by name + version.

## Decisions log

- **Python 3.12** (not the host's 3.14) for stable wheels on asyncpg and friends; pinned via uv.
- **uv** for backend dependency management, **pnpm** for the frontend. Lockfiles committed.
- **Native Postgres enums** for the controlled lists (role, template status, answer type,
  run status, answer kind, message role) — the schema enforces the vocabularies, not just
  the app layer.
- **Architecture rules are executable, and every gate is proven.** The layering in
  this file is enforced by import-linter contracts and by guards under
  `backend/scripts/`, not by review alone. `tests/test_gates.py` plants a violation
  for each guard and asserts it is rejected, because a gate nobody has watched reject
  anything is decoration. Guards fail when they cannot run, rather than passing having
  checked nothing. `make gate` is exactly what CI runs. Adopted from a sibling
  project on 6 Aug 2026.
- **One provider protocol, no vendored SDK.** Every LLM tier is reached over the OpenAI
  Chat Completions API through a single `httpx` client, so adding a provider is config
  rather than code. The Anthropic SDK and its client were removed on 6 Aug 2026; the
  chain is OpenAI, Groq, then OpenRouter, in that order.
- **The live check writes everything down, and judges itself.** Real conversations are the
  only thing that finds fabrication, and a live finding neither keeps nor reproduces. So
  every run captures its transcript to `backend/tests/live_runs/`, and the mocked suite
  replays those runs on every push: answers accepted live must stay accepted, and answers a
  human marks `"invented"` must be refused. A second model pass judges each recorded answer
  during the run, but its verdicts are soft everywhere and are never ground truth for a
  test, because it is a model and it produced false positives in two distinct classes on
  the day it was written. Adopted 9 Aug 2026. Do not promote the judge to a hard failure
  without a measured false-positive rate to point at.
- **Nothing is served locally.** The compose stack ran an Ollama as tier 4 until
  8 Aug 2026. It was removed: three hosted tiers cover failover, and the weights cost
  1.9 GB and a cold-load penalty to carry. Tier 4 survives as an empty slot any
  OpenAI-compatible server can fill from `.env`, so this is config to undo, not code.
  Do not reintroduce an inference service to the stack without a reason that names
  what the hosted tiers cannot do.
- **Frontend decisions live in `frontend/CLAUDE.md`**, which loads when working under that
  directory. The Tailwind layering rule, the class guard and the unified Results page are
  there: each only bites while editing frontend files, and this file is in context for
  every session including the ones that never open it.
- **One job per person, and every right derives from it.** Built 13 Aug 2026, replacing
  the three vocabularies this section used to describe (`role`, `CreatorDepartment`,
  `RespondentGroup` with its membership table), after the org chart showed the flaw:
  the membership table recorded a line leader who was also QA, a job the plant does not
  contain. A person now holds one job, a `function` (production, quality,
  health_safety, technical, planning, hr, finance, supply_chain, it, executive) crossed
  with an ordered `band` (operative, line_leader, supervisor, manager, head, director),
  plus zero or more `hats` (health_safety first: a supervisor with H&S duties keeps
  their job and carries the hat). One job per person is the schema's version of an RBAC
  separation-of-duty constraint, so the impossible overlap cannot be recorded again.
  Everything else is derived in `app/access` and stored nowhere: **authoring is band >=
  manager** (the `role` column is gone, and `require_author`'s name survives its
  contents); audiences are predicates over the job (`qa` is the whole quality ladder,
  `health_safety` is the function or the hat, `managers` is the band anywhere,
  `everyone` is anyone with a job, which now includes the office, decided knowingly);
  colleagues are the authoring bands of one function, symmetric and silo'd per office
  function; the executive function reads every survey and edits none; and the
  audience's own seniors do **not** read surveys aimed at their team, so HR can survey
  a team candidly about its own management. IT still grants admin at any band and the
  allowlist stays beside it. `microsoft_id` is a sign-in method and decides nothing,
  which dissolves the stored-role contradiction the old entries recorded: line leaders
  hold ERP logins without that making them authors. The admin screen writes jobs and
  hats; the reach preview warns on band and hat edits the way it warned on group edits,
  and carries `may_author_before/after` so the browser never re-derives band order. The
  migration remaps by an explicit seed map plus generic rules, deliberately leaves
  Adaeze's local IT grant alone, and serves old `account_changes` rows in their old
  vocabulary, because an audit trail that rewrites history is not one. Grounded in the
  NIST RBAC model (role hierarchy plus static separation of duty) and ordinary
  job-architecture practice; `tests/test_access_rules.py` is the matrix that pins it.
- **Reach is live, and the guardrails are a witness, not a freeze.** Decided 13 Aug 2026,
  against snapshotting audiences into published versions: who a survey is for is whoever
  holds the job today, so a new starter is asked Monday's survey and every denominator
  moves when a job does. What makes that honest is that changes are seen and
  recorded: the publish dialog shows the live headcount beside the audience; an admin
  edit that would move an open survey's reach shows exactly which surveys and by how much
  before saving (warn and proceed, never block, because people genuinely change jobs);
  and `account_changes` is an append-only audit table written in the same transaction as
  every create and edit, so "why did the completion rate drop on Tuesday" has an answer
  with a name on it. Open-source engines were evaluated for this on 13 Aug and rejected
  with reasons: Oso's library is deprecated, OpenFGA/SpiceDB/Cerbos are always-on
  services against the no-local-services decision, and pycasbin would replace the pure,
  reasoned `app/access` with a PERM DSL while providing none of the guardrails, which
  are change-management, not authorization. Do not re-litigate that without new facts.
  One number to keep in mind: reach and preview iterate every user and open survey per
  request, which is fine at plant size and author-side only, so the break-time burst
  (the whole floor answering at once, the reason `DB_POOL_SIZE`/`DB_POOL_MAX_OVERFLOW`
  exist and are forwarded in compose) never pays for them.
- **Seed ids are forever, and the seed refuses impostors.** Two ids reused from a retired
  generation of `SEED_USERS` were still occupied in databases seeded before 10 Aug; the
  insert silently skipped and the membership loop decorated the strangers holding them.
  New seed users take fresh c-block ids, `seed()` raises when an id's email disagrees,
  and `test_the_seed_only_decorates_its_own_users` pins the shape.
- **Signing in is an address, not a list.** `POST /api/v1/dev/identify` added 13 Aug 2026,
  because the app could not be entered at all from a clean browser: listing users requires
  a caller, a caller is an id under the header shim, and that list was the only source of
  an id. Every page told you to pick a user in a dropdown that could never be filled, and
  only a leftover localStorage entry hid it. The endpoint is unauthenticated of necessity,
  so **its mount is its only protection**: registered beside the picker and only outside
  production, pinned by a test. Knowing an address is therefore enough to act as somebody,
  which is the honest state of authentication here until a real provider replaces
  `get_current_user`. Do not move it out from behind that branch, and do not "fix" the
  deadlock by unauthenticating the user list: that hands out every id, which is every
  credential.
- **A survey has one definition, and editing it is live.** Removed
  `survey_template_versions` on 16 Aug 2026, asked for directly. Publishing was a
  snapshot: the draft froze into an immutable version, runs named the version they
  started on, and the report counted only the latest, excluding earlier runs and saying
  how many. That is all gone. A run names the survey, the engine reads the questions and
  the setting at each turn, and every run counts.

  **What it costs, stated because it is the kind of thing that surfaces later as a
  mystery.** An author editing a published survey changes the question that earlier
  answers were given to; a respondent mid-conversation gets the new questions at the next
  turn; the report scores old answers against new wording; and a stored recap can outlive
  the questions it described, because the reuse key could once include the version and
  now cannot. The only surviving record of what somebody was actually asked is the
  `question_text` copied onto each answer row at the moment it was recorded, which is why
  that column matters more than it did.

  **What replaced it.** `survey_templates.published_at` and `published_by`, set once on
  the first publish, so "when did this go out and who sent it" still has an answer.
  `app/templates/reading.py` replaced `snapshot.py` and keeps its job: one place turns a
  survey into the dicts every reader consumes, so no reader guesses what a missing field
  means. The publish dialog says plainly that later edits change the survey for everyone,
  including anyone part-way through, rather than promising a freeze that no longer
  happens.

  For a BRCGS-adjacent product this is the trade worth re-examining first if audit
  evidence ever matters: an auditor asking "what exactly was this person asked" is now
  answered by one column rather than by an immutable row.
- **Publishing freezes a survey, and only an unanswered one can be deleted.** Asked for
  directly on 17 Aug 2026, a day after versions were removed, and the two together are
  coherent rather than contradictory: versions froze a *copy* while the draft evolved,
  and this freezes the *survey* itself. Either way nobody's answer is re-pointed at a
  question they were not asked. A survey that needs different questions is a new survey,
  which also keeps two sets of answers from blending under one title.

  **Delete is permanent and therefore narrow.** It removes the survey and its questions
  outright, and it refuses the moment any run exists, of any status: an abandoned
  half-conversation is still something a person said. This is not a soft delete; there is
  no tombstone and no purge job. The gate is the run count rather than the status,
  because a draft nobody could answer and a published survey nobody did are the same
  situation.

  **Backups do not make deletion safe, which is why the rule is a rule.** A restore
  brings back the whole database at a moment in time, not one survey out of it, so
  recovering a wrongly deleted survey costs every answer given since. See
  `docs/BACKUP.md`: continuous WAL archiving to immutable object storage, on the
  3-2-1-1-0 rule, with a weekly restore test that fails loudly, because a check nobody
  has watched fail is decoration. The bucket does not exist yet and nothing has been
  restored, which that document says plainly.

