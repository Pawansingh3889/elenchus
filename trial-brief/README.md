# Survey Service Trial Brief

> **Note added after the trial, not part of the original brief.** `DESIGN.md` and
> `reference/survey_builder_demo.html` set out the client's colour palette, typeface and
> template styling. They were removed from this repository and from its history at the
> client's request. References to them below are left as they were written; the files
> themselves are gone, and the application uses a neutral palette and a system typeface.

Welcome. This is a four-day trial project. You'll build a **standalone survey service** from scratch in a fresh repository. It is a real feature we intend to integrate into our platform, so treat it as production work, not a toy.

## What you're building (one paragraph)

A repeatable survey service with two halves. **Authoring:** an admin creates a survey template either by describing it in natural language (the LLM drafts it) or by hand in a builder UI — both land in the same editable template, which is then published. **Conducting:** an end-user completes a published survey through a sleek, conversational, chat-style experience driven by an LLM. The LLM asks the template's questions one at a time, can ask bounded follow-up questions when an answer warrants it, and every answer is validated, structured, and saved to Postgres linked to the responding user.

Full functional detail is in `SPEC.md`. The architecture you must follow is in `ARCHITECTURE.md`. The visual language is in `DESIGN.md`, with a static mock of the builder in `reference/survey_builder_demo.html`.

## Ground rules

- **Fresh repo, your own work.** You will not have access to our codebase. Everything you need is in this pack.
- **LLM-assisted development is expected.** Use Claude Code / Cursor / whatever you're fastest with. We care about the quality of what you ship *and* how well you direct the tools — keep your prompts/specs/plans in the repo (e.g. a `CLAUDE.md`, plan documents) so we can see your process.
- **Working software over feature count.** A smaller scope that runs end-to-end, with clean seams, beats a broad scope that half-works. The must-haves in `SPEC.md` are the bar; stretch goals are genuinely optional.
- **Commit as you go.** Conventional commits (`feat(scope): …`, `fix(scope): …`), small and frequent, on feature branches merged to main. Your git history is part of the assessment.

## Logistics

- **Duration:** 4 working days — **Tuesday 21 July to Friday 24 July 2026**.
- **Review call: Thursday 23 July.** A mid-trial check-in, not a demo. Come with: the stack running, the data model migrated, template CRUD and the builder working, and whatever questions or scope concerns you have. This is the moment to flag anything that threatens the must-haves; we'd rather re-scope on Thursday than hear about it on Friday.
- **Final demo: Friday 24 July** (time TBC — we'll confirm on the Thursday call).
- **LLM access:** use your own Anthropic API key for the conversational features. Keep it in env config; never commit it.
- **Questions:** batch them and ask early. Asking sharp questions on day 1 counts in your favour; discovering a blocking ambiguity on day 4 does not — the Thursday call is your backstop, not your first opportunity.

## The final demo (Friday 24 July)

Plan for ~45 minutes:

1. **Live run-through** — create a template via natural language, tweak it in the builder, publish it, complete it as an end-user (including at least one LLM follow-up question firing), then show the stored response in the results view / database.
2. **Architecture walkthrough** — layering, data model, how the conduct engine keeps the LLM on rails.
3. **Process walkthrough** — how you used LLM tooling: what you specced vs. prompted vs. wrote by hand, what you rejected, how you verified generated code.

## How you'll be assessed

| Area | What we're looking for |
|---|---|
| Working product | The must-have flows run end-to-end without hand-holding |
| Architecture adherence | The layering, conventions and "LLM on rails" rules in `ARCHITECTURE.md` are actually followed |
| Data modelling | Sensible schema, migrations, immutable published versions, answer attribution |
| LLM engineering | Schema-constrained tool calls, versioned prompts, deterministic control flow, graceful handling of bad model output |
| Code quality | Typed, modular, no dead code, no silent fallbacks, honest error handling |
| Tests | Core conduct-engine and service logic covered; not chasing a coverage number |
| Process & communication | Clear commits, visible planning, a demo that shows you understand what you built |

## Suggested pacing (yours to change)

- **Tue 21** — scaffold (compose stack, FastAPI app, Next.js app), data model + migrations, template CRUD API.
- **Wed 22** — builder UI (question list, types, options, reorder, publish) + start the natural-language generation (it shares the LLM plumbing the runner needs next).
- **Thu 23** — conversational runner: conduct engine, answer recording, persistence. *Review call today — see Logistics.*
- **Fri 24** — LLM follow-ups, results view, polish; final demo (time TBC).

Four days is deliberately tight: we do not expect stretch goals, and a lean-but-solid builder beats a rich one. If you're behind at the Thursday review call, tell us and we'll re-scope together — cut stretch goals and UI polish, not validation, migrations or tests.
