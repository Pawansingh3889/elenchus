# Elenchus commercial product plan

Consolidated on 18 September 2026 from the voice planning session on this device.
This document separates the requested direction, proposed choices, and completed work.
It is a product roadmap, not a claim that the commercial features are implemented.

Working update, 21 September 2026: the audit branch adds database-enforced company
isolation and scoped cost-ledger reads. Deployment and remaining limitations are in
[WORKSPACE_ISOLATION.md](WORKSPACE_ISOLATION.md). The current
[commercial contract](COMMERCIAL_READINESS.md) records owner-only spending approval,
owner/admin-only analyst assignment, and owner-configurable 90-day response retention.
These policies still require implementation; the isolation foundation is not a launch.

## 1. Goal and working approach

Turn Elenchus into a subscription survey product. Improve the customer-facing design
first, then build a complete customer journey and continue improving the underlying
survey intelligence.

Work in small stages and explain the concepts and implementation decisions as we go.
The product should help customers understand what to ask, conduct useful conversations,
and trace findings back to what respondents actually said.

Requested direction:

- Make Elenchus commercially usable through subscriptions.
- Provide design demos that can be compared before choosing a direction.
- Support multiple survey categories with shared specialist capabilities.
- Offer a short needs conversation before a visitor chooses a subscription.
- Keep the roadmap and design references in the repository for continued improvement.

Still proposals: final design (the current app theme stays as-is; the three design
concepts in `docs/design/` remain reference only, not adopted), tier details, pricing,
allowances, and specialist implementation sequence. No launch date was agreed. The first
customer segment is settled: employee feedback (§4).

## 2. Customer journey

**Discover Elenchus → optional needs conversation → tailored survey preview → explained
plan recommendation → signup and subscription → survey workspace → publish and share →
collect answers → review results → manage plan and usage.**

Visitors can skip the conversation and browse templates or pricing directly. The
conversation should demonstrate the product before asking someone to pay.

### Free needs conversation

Ask one question at a time, skip information already supplied, and let the visitor
correct the resulting summary. Learn:

| Question | What it informs |
|---|---|
| What decision are you trying to make? | Survey goal and question design |
| Who do you want to hear from? | Category, terminology, and audience |
| Can you invite those people yourself? | Whether respondent recruitment is needed |
| Roughly how many responses, and how often? | Usage requirements and recurring versus one-off fit |
| Will other people help manage the surveys? | Workspace and collaboration requirements |

The result should contain an editable goal summary, a suggested survey with sample
questions and estimated respondent time, and a plan recommendation with clear reasons.
Offer actions to edit the survey, compare plans, or try a limited demo.

Start with text chat. Voice interaction can follow later; the voice planning session
did not establish voice input as a launch requirement.

### Recommendation rules

The LLM interprets needs and drafts the survey. Application rules compare those needs
with the actual plan catalog and recommend the lowest-cost suitable plan.

- Never invent prices, allowances, or available features.
- Explain when no plan fits.
- Keep participant recruitment and its cost separate from the software subscription.
- Do not automatically steer a one-off need into a recurring subscription.

## 3. Proposed subscription structure

| Offering | Proposed purpose | Status |
|---|---|---|
| Free entry experience | Needs conversation and a limited survey demo | Scope and limits undecided |
| Starter | An individual running occasional surveys | Proposed paid tier; price and allowances undecided |
| Team | Shared workspaces, collaboration, and higher usage | Proposed paid tier; price, seats, and allowances undecided |
| Enterprise, later | Custom arrangements where customer demand justifies them | Deferred |

Survey categories should be available across both paid plans. Differentiate plans by
usage and collaboration, rather than charging separately for each category or specialist.
Set prices and limits after measuring operating costs and validating customer demand.

Pollfish, Typeform, and SurveySparrow were discussed as comparison products. The research
questions are how they explain audience selection, survey creation, conversational
follow-ups, usage limits, and costs. Competitor prices are not recorded as current facts
here and must be checked before a pricing decision.

## 4. Survey categories

| Category | Example uses | Proposed sequence |
|---|---|---|
| Employee feedback | Onboarding, engagement, workplace improvements | **Selected pilot category** |
| Customer experience | Satisfaction, service feedback, churn reasons | Candidate expansion |
| Product research | Concept testing, feature feedback, usability interviews | Candidate expansion |
| Market research | Audience studies and purchase preferences | Later; recruitment remains a separate concern |

Employee feedback is the selected pilot category: the existing project already has
workplace concepts, and it is the starting point Stage 2 of the roadmap builds against.
Complete its full journey (draft, review, publish, interview, results) before expanding
to another category.

The pilot release contract is recorded in [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md).
It settles the initial tenancy shape: multiple customer companies, one private workspace
per company, one company per account, and up to 100 simultaneous respondents overall.
Respondents use a shared link followed by verified email sign-in, and the address must be
invited or on an approved employee roster. Workspace roles are owner, admin, author,
analyst, and respondent. Factory jobs describe audiences only.

Publishing freezes the survey. A changed survey is duplicated, and a survey with any run
cannot be deleted. Subscription usage is a monthly allowance of completed responses plus
seats. Once the allowance is exhausted, new starts stop, active sessions finish, and an
explicit owner-approved top-up is required.

## 5. Shared specialist capabilities

A category describes a customer's goal. A specialist performs a job that can serve
several categories. There is no requirement for a separate autonomous agent or model
for every field.

| Specialist | Job | Required control |
|---|---|---|
| Survey designer | Turn a research goal into draft questions | Customer reviews before publishing |
| Interviewer | Ask questions and useful follow-ups | Existing conduct engine controls sequence and accepted answers |
| Analyst | Group themes and explain results | Findings link back to recorded responses |
| Quality reviewer | Flag leading questions and unsupported conclusions | Model judgments stay advisory |

Begin with bounded, testable model steps and category-specific guidance. Reuse existing
generation, conducting, and analysis capabilities where they fit. Add independent agent
behavior only when evaluation demonstrates a useful improvement.

The LLM supplies language and reasoning. Application code owns permissions, budgets,
validation, state changes, and database writes. Preserve the existing engine's authority.

## 6. Design scope

The first design milestone covers the entry conversation and recommendation, followed by:

- **Workspace:** survey list, clear statuses, and an obvious create-survey action.
- **Builder:** questions and settings beside a live respondent preview.
- **Respondent experience:** readable mobile conversation with clear progress.
- **Results:** findings supported by answers, clear counts, and exports.
- **Plan and usage:** understandable allowances, plan comparison, and subscription management.

Three interactive workspace concepts were created with sample data:

| Direction | Character |
|---|---|
| A: Clear and focused | Minimal layout, precise spacing, blue accents |
| B: Warm and conversational | Soft surfaces, editorial typography, natural tones |
| C: Research studio | Compact layout, structured evidence, violet accents |

The demo includes design switching, a build/preview screen, sample rating follow-ups,
and illustrative results. It does not implement the needs conversation, checkout, or
production survey authoring. No final direction is recorded in the recovered session.

The existing browser is primarily the respondent path, with administrative lens pages;
survey authoring is through the API. A commercial self-service builder is a planned
scope change that will require the project guidance to be updated when implemented.

## 7. Delivery roadmap

| Stage | Deliverable | Evidence needed before moving on |
|---|---|---|
| 1. Product design | Choose a visual direction and create a clickable journey from needs conversation through preview, recommendation, workspace, and results | A potential customer can understand and complete the journey |
| 2. One complete category | Draft, review, publish, interview, and results for the selected pilot category | Real pilot users obtain useful, evidence-backed results |
| 3. Subscription pilot | Verified sign-in, isolated customer workspaces, billing, usage limits, cancellation, and operating-cost measurement | Customer data stays separated, access and billing rules work, and costs support the proposed plans |
| 4. Shared specialists | Incrementally add or improve designer, analyst, and quality-review steps around the existing interviewer | Each addition improves quality or saves time at an acceptable measured cost |
| 5. More categories | Reuse the core with tailored questions, terminology, and reporting | Demonstrated demand and evaluation examples for each new category |

The subscription pilot is the first paid milestone. Design and category validation
prepare that milestone; they do not require building every specialist or category first.

## 8. Progress at consolidation

| Item | Evidence and status |
|---|---|
| Core survey engine and respondent flow | Existing repository capabilities |
| Tracing, cost views, embeddings, and evaluation | Merged work through [PR #75](https://github.com/Pawansingh3889/elenchus/pull/75); the local checkout does not yet contain merged PRs #73 to #75 |
| IAM-style role grants | [PR #76](https://github.com/Pawansingh3889/elenchus/pull/76) is open; this is separate from customer workspace isolation and subscription enforcement |
| Three design concepts | Preserved at [design/elenchus-directions.html](design/elenchus-directions.html); not integrated into the product |
| Consolidated commercial plan | Captured in this document |
| Editable demos saved in the repository | Done — see the design concepts row above |
| Needs conversation and plan recommendation | Proposed; no implementation found in the recovered work |
| Commercial self-service workspace and builder | Proposed; not delivered by the design demo |
| Sign-in, customer isolation, billing, and subscription enforcement | Commercial launch requirements; not established as complete by this progress review |

This is a dated progress snapshot, not a fresh test or deployment report. The current
uncommitted Docker startup changes are separate from this product plan.

## 9. Next actions and unresolved choices

- [x] Recover the voice-session plan and consolidate it into a repository Markdown file.
- [x] Preserve the existing HTML concept under `docs/design/`, with a standalone browser
  preview and editing instructions.
- [x] Choose or combine design directions A, B, and C: none of them — the current app
  theme (§1) stays as the design; A/B/C remain preserved as reference only.
- [x] Choose the first customer segment: employee feedback (§4). Identifying actual
  pilot users is still open.
- [ ] Build a clickable needs-conversation and recommendation demo using clearly labeled
  sample plans, without presenting undecided prices as real offers.
- [ ] Confirm the first category's end-to-end scope before production implementation.
- [ ] Measure costs and decide Starter and Team prices, response allowances, and seat limits.
- [ ] Specify sign-in, customer workspace isolation, billing, cancellation, and usage enforcement.
- [ ] Evaluate each specialist improvement before expanding to more categories.

## 10. Source and related documents

Recovered source: the local voice conversation on 18 September 2026, approximately
07:59 to 08:15 IST. It records the commercial direction, design demos, roadmap, and
request to add those references to the repository.

Source session identifier: `01a0b24b-3760-7120-8602-2d97696b81a1`.

Original design artifact, preserved as a standalone page at
[design/elenchus-directions.html](design/elenchus-directions.html): open it directly in
any browser, no build step or server. It was originally an embedded ChatGPT-widget
fragment (the `window.openai` / `Tweak` hooks in its script are optional-chained no-ops
outside that host), so the live-tweak side panel and state persistence between reloads
do not apply here — the design switching, view tabs and rating buttons all work as
before. Editing instructions are in a comment at the top of the file. It was previously
only on this device, at
`~/.codex/visualizations/2026/09/18/01a0b24b-3760-7120-8602-2d97696b81a1/elenchus-directions.html`.

Related project references:

- [Current product overview](OVERVIEW.md)
- [Access and results](ACCESS_AND_RESULTS.md)
- [Known defects](DEFECTS.md)
- [Development and verification checks](CHECKS.md)
- [Project guide](../CLAUDE.md)
- [Original trial brief](../trial-brief/README.md)

Keep proposed features here until implemented. Update the progress table when work is
verified, record settled product choices explicitly, and leave technical release history
in [CHANGELOG.md](../CHANGELOG.md).
