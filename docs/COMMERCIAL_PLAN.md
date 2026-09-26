# Elenchus commercial plan

Agreed 26 September 2026. These decisions replace the earlier standalone subscription
proposal and unrestricted free-signup positioning. Planned features are not shipped claims.

## Offer

Elenchus is an employee-feedback product in the KapkotiSolution family. There is no
separate Elenchus subscription. Visitors get a complete survey journey in a private demo.
Customers of any paid KapkotiSolution product, including future products, qualify for
company-wide Elenchus access at no extra product charge.

- An active subscription qualifies while active; a one-time purchase qualifies permanently.
- The operator verifies the purchase and activates the workspace manually initially.
- Full access includes all features and unlimited survey creation, with a monthly
  response-session allowance explicitly agreed at activation. A session counts when
  admitted, including unfinished and later withdrawn sessions. No default allowance is advertised.
- A lapsed entitlement stops new activity; it does not silently delete results.
- Existing data is preserved. Demo workspaces are separate from existing customer data.

## Demo rules

| Decision | Agreed rule |
| --- | --- |
| Public entry | Interactive sample walkthrough without signing in |
| Real entry | Personal pass or link issued manually by the operator |
| Identity boundary | One private workspace per pass; no shared administrator credential |
| Surveys | Three successfully created surveys total per workspace |
| Counting | Draft creation and duplication count; editing and failed creation do not |
| Deletion | Deleting a survey never restores a slot |
| Questions | At most ten per survey |
| Respondents | At most twenty respondent sessions per survey, including abandoned sessions |
| Duration | Fourteen days from issue |
| Invitations | Real respondents enter through a survey link without signing in |
| Privacy | Identities hidden from authors; names and emails are not requested from respondents |
| Remaining exposure | People can identify themselves in their own words; disclose this |
| At the creation limit | Existing surveys and results remain usable within other limits |
| After expiry | Preserve stored results; block new creation, sessions and paid AI work |
| Global AI budget | US$10 per UTC calendar month across all demo workspaces |
| Renewal | No reset by deleting a survey or clearing browser storage |

Enforce allowances in shared backend operations, including direct API calls. Serialize
concurrent reservations. Keep quota usage when content is withdrawn or purged. Reserve
cost before each provider attempt, including retries, failover, generation, conversations
and summaries. Refuse unpriced calls; unknown usage is not free. The application spending
ceiling depends on correct configured rates; configure a provider spending limit too.

## Complete journey

1. **Discover:** product purpose, interactive sample, demo rules and customer eligibility.
2. **Enter:** redeem a personal pass; see remaining allowance, expiry and data disclosure.
3. **Describe:** state the decision, employee audience and survey goal.
4. **Draft:** generate or write questions; review wording, answer types and follow-ups.
5. **Publish:** freeze questions and create a respondent link; explain privacy and limits.
6. **Respond:** a conversation without separate account setup; saved turns, progress,
   resumption, withdrawal and clear provider errors.
7. **Inspect:** participation and question-level results, including incomplete and
   declined answers, with denominators stated.
8. **Summarise:** request a recap, inspect its evidence and distinguish employee
   suggestions from AI-proposed next steps.
9. **Export:** CSV or print/save the report as PDF, preserving scope and privacy.
10. **Continue:** operator verifies a qualifying purchase, records the response allowance
    and activates company access. Preserve demo work when activating the same workspace.

## Customer dashboard and KPIs

Every metric names its scope, sample count and coverage. Unknown is not zero. Charts
have readable values and accessible tables. Public sample charts are labelled illustrative.

| Measure | Definition and boundary |
| --- | --- |
| Survey allowance | Lifetime successfully created demo surveys / three |
| Sessions started | Admitted sessions; abandoned and withdrawn sessions still consume quota |
| Responses completed | Sessions the engine marked complete |
| Completion rate | Completed / started within the same reporting population |
| Response rate | Completed eligible people / known invited people; unavailable for an open link with unknown reach |
| Response time | Median elapsed time for completed responses; breaks may be included |
| Question coverage | Usable and declined answers shown separately; branching can leave questions unasked |
| Ratings | Distribution and sample count beside the average; preserve the actual scale |
| Themes | Supported themes with source answers; overlapping themes are not exclusive percentages |
| Recap freshness | Generation time and responses included; flag when results change |

## Summarisation

Build on the existing run and survey summary services.

- Short executive recap, themes linked to the question and supporting answers.
- Compute figures in code; never ask the model to invent a denominator.
- Preserve minority views, conflicting evidence and sample limitations.
- Keep respondent suggestions separate from labelled AI-proposed actions.
- Proposed actions reference the findings that motivated them and require human judgement.
- Verify quotes exactly; check factual claims against recorded responses.
- Show provenance, generation time and response coverage, including in exports.
- Neutralise spreadsheet formula injection in respondent-controlled export text.

Cross-survey comparisons and tracking completed actions are later phases. Compare only
compatible questions and cohorts; a change of wording is not evidence of a trend.

## Private operator dashboard

Reuse the lens for provider detail. Operator business data stays behind operator access.

| Measure | Definition |
| --- | --- |
| Passes issued / activated | Unique issued passes and first successful redemption |
| Activation rate | Activated demo workspaces / issued demo workspaces |
| First value (later) | Workspace has a published survey and a completed response |
| Customer unlocks | Workspaces activated after a verified qualifying purchase |
| Conversion (later) | Activated demos later unlocked / activated demos, with cohort and time window |
| AI expenditure | Known spend plus uncertain/outstanding reservations against the US$10 monthly ceiling |
| Cost per completion (later) | Known operational spend / completed responses, with pricing coverage |
| Reliability | Attempt totals, failures and uncertain reservations; detailed latency and retry analysis remains in the lens |

## Commercial page and visual direction

Replace the homepage with deep plum, warm ivory, charcoal and restrained apricot accents.
Use the existing fonts, plain CSS and chart tools. Preserve contrast, keyboard operation,
mobile layouts and reduced-motion support.

Show the product proposition, interactive end-to-end journey, sample KPI dashboard with
evidence drilldowns, summary example, demo allowances, customer eligibility, FAQ and
phased roadmap. Clearly distinguish live features, illustrative data and planned work.
Do not expose operator credentials, private metrics or an authentication bypass.

## Delivery sequence

| Stage | Deliverable | Acceptance |
| --- | --- | --- |
| 1 | Commercial page, interactive samples and agreed plan | Responsive page, working controls, accurate offer/status |
| 2 | Private passes, isolation, quotas and budget | Expired/revoked passes fail; concurrent quotas and tenant boundaries hold |
| 3 | Browser builder, respondent entry and results | Create, edit, publish, share, answer and read real saved results |
| 4 | Summaries, evidence, CSV and PDF | Quotes exist, source links resolve, counts agree, exports preserve scope |
| 5 | Manual activation and operator reporting | Explicit allowances, verified eligibility, audited activation, no self-upgrade |
| 6, later | Chatbot issuing demo passes | Verified contact workflow, bounded issuance and recorded consent |

Before live access: apply migrations with the deployment role, run required gates and
browser checks, configure the authentication secret, provider rates and spending ceiling,
confirm origins, and establish backup/restore evidence. Use mocked model calls in tests;
the demo spending ceiling does not authorise unattended paid evaluation batches.

## Later: chatbot issuing demo passes

Collect email, name, company, role and survey goal. Explain limits and storage, and verify
control of the email before issuing a pass. Optional marketing consent is separate from
access. Application rules deduplicate requests, decide eligibility, create the workspace
and issue the pass. The model helps ask questions; it cannot increase quotas, bypass
limits or unlock customer entitlements. Reuse the manual pass-issuance operation.

Shared sign-on, payment checkout, standalone Elenchus plans, cross-survey comparisons and
action tracking are outside the initial demo. The chatbot is explicitly a later phase.
