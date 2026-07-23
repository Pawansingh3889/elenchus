# Changelog

All notable changes to the ViewOps Survey Service, from the first commit onward.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The project is not yet versioned, so entries are grouped by date. Newest first.

## 2026-07-23 — Hardening, docs, and resilience

### Added
- **Optional OpenAI-compatible backup LLM with failover** (PR #4). A second LLM
  client (`app/llm/backup.py`) speaks the OpenAI Chat Completions API, so any
  compatible endpoint (self-hosted Nemotron/Hermes, vLLM, NIM, OpenRouter, Ollama)
  can stand in when the Anthropic primary is unavailable. `FailoverLLM` tries the
  primary and falls back only on a typed error; `get_llm()` wires primary-only,
  backup-only, or primary-with-failover from settings
  (`LLM_BACKUP_ENABLED` / `_BASE_URL` / `_API_KEY` / `_MODEL`).
- **Application overview doc** (`docs/OVERVIEW.md`, PR #3) — a plain-English tour of
  what the app does, its two halves (authoring and conducting), and what it outputs.
- **Manual live-conduct check** — a workflow runnable from GitHub Actions or VS Code.
- **Scripted stress suite** — the eight conduct stress scenarios as a replayable test.

### Changed
- The conduct engine and template generator now resolve their LLM through the new
  `get_llm()` factory instead of constructing the Anthropic client directly.

### Fixed
- **Compose bind mounts fail under rootless Podman on Fedora/RHEL** (PR #2). Added the
  `:z` SELinux relabel to the `./backend` and `./frontend` mounts so the containers can
  read them; a no-op on Docker and on hosts without SELinux.

### Tests
- Offline coverage for the backup provider: failover selection and the
  OpenAI-compatible translation, driven by `httpx.MockTransport` (no network, no key).

### Repository maintenance
- Deleted 14 stale/merged branches, leaving `main` as the single source of truth.
- Verified the project is intact and current on `main`.

## 2026-07-22 — Long-survey polish and editor tooling

### Fixed
- **A catch-all option silently overwrote a real answer** — a live run recorded
  `{"option": "Other"}` and lost the respondent's actual team. Catch-all options are now
  turned into a proper write-in so the real answer is captured.
- Conduct engine: prompt the model to **probe rather than infer** a missing value, and
  allow a follow-up **before** an answer is recorded.
- Date the conversation correctly and respect optional questions on longer surveys.

### Added
- Dates on each row of the template list.
- A committed live-conversation harness for exercising the conduct engine end to end.

### Changed / tooling
- Editor niceties: pytest discovery in the IDE, and a debugger that frees port 8000 itself.

## 2026-07-21 — Core build (authoring, conducting, results)

### Added
- **Scaffold**: FastAPI backend + async SQLAlchemy + Alembic, PostgreSQL, and a
  Next.js frontend, all in a docker-compose dev stack.
- **Auth**: typed errors, a thin dev-auth dependency (`X-User-Id`), and seeded users.
- **Templates**: draft CRUD and publishing to **immutable versions**.
- **LLM authoring**: natural-language template generation via a schema-constrained
  tool call.
- **Builder UI**: template builder with live preview and NL generation.
- **Conduct engine**: a deterministic engine that owns which question is current,
  completion, and the follow-up budget; the model chooses one validated action per turn.
- **Conversational runner** (frontend) for respondents, plus a typed API client and
  queries for runs.
- **Results**: authors can read runs back (structured answers + full transcript), with
  a responses view; follow-ups are attached to the question they probed.
- CORS for the browser app, a health endpoint response model, a demo-reset script,
  shared editor config, and a developer guide.

### Fixed
- Render upstream Anthropic API failures as **typed errors**; bound API calls with an
  explicit timeout; log raw model output when a turn fails.
- **Authorization**: scope surveys and responses to the author who created them.
- **Follow-up budget is spent when a probe is asked** (not when answered), closing an
  endless-probe loophole.
- Transcript/answer ordering stamped client-side so same-transaction rows don't tie.
- Various web fixes: surface 4xx instead of retrying into a blank page; surface template
  creation failures.

### Tests
- Template CRUD, publish, and version immutability.
- Conduct: advancement, caps, malformed model output, and republishing leaving an
  in-flight run alone.
- The answer-validation contract across all eight answer types.
- Results: reading responses back, the template boundary, and follow-up ordering.
- Authorization: one author cannot reach another's surveys or responses.
- A shared LLM fake and published-survey fixture so tests run without an API key.

### CI
- Run the full suite (ruff, black, mypy, pytest) on every push and pull request.

## 2026-07-20 — Project kickoff

### Added
- The ViewOps survey trial brief pack (requirements, architecture, and spec).
