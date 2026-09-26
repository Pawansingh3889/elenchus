# Commercial readiness contract

Status: working decision record, updated 21 September 2026.

This document records the first paid pilot rules and the telemetry contract that the
dashboard must implement. A row marked `Required` is not evidence that the feature is
already shipped.

## Pilot boundary

The first release serves employee feedback for up to 10 customer companies and 100
simultaneous respondents overall. Each account belongs to one company only during the
pilot. Each company has a private workspace.

Respondents enter through a shared survey link, then complete verified email sign-in.
Verification alone is insufficient: the address must already be invited or present on an
approved employee roster for that workspace. Unknown addresses are refused and are not
silently provisioned.

Workspace roles are `owner`, `admin`, `author`, `analyst`, and `respondent`. Factory jobs
describe survey audiences only. They do not grant workspace permissions. The survey
author and assigned analysts may read identified answers and transcripts. Owner and admin
access is allowed only when disclosed to respondents and recorded in an audit trail.

Publishing freezes the survey. Changes require duplicating it into a new survey. A survey
with any run cannot be deleted. These rules supersede older documentation describing live
editing or mutable publication versions.

Identified answers and transcripts have a 90-day default retention period, configurable
only by the owner. Shortening applies immediately to existing responses after explicit
confirmation. Expiry must delete answers, transcripts, captured model requests, and derived analyses. Keep
only non-identifying usage totals and deletion audit events, not respondent-level content
hidden behind pseudonyms. The clock starts at completion time for finished responses and
at the last respondent activity for unfinished responses. The survey deletion guard must
not prevent retention expiry.

## Subscription and allowance rules

The pilot charges for a monthly allowance of completed responses plus named staff seats
for owners, admins, authors, and analysts. Respondents use the response allowance and do
not consume paid staff seats. Currency, price, seat count, and allowance tiers remain
commercial decisions, not code defaults. Only the workspace owner can approve spending,
purchase top-ups, or change subscriptions. Admins can view usage.

When an allowance is exhausted:

1. New survey starts are blocked.
2. Active sessions may finish.
3. Completions from those active sessions are visible as allowance overrun and require an
   explicit owner-approved top-up before further starts.
4. The system must not silently create billable overage or silently discard a completion.

The billable event is one unique completed response. Retries, LLM attempts, validation
refusals, abandoned sessions, and failed sessions are operational cost, not additional
completed responses. They still appear in cost and reliability dashboards.

## Access matrix

| Capability | Owner | Admin | Author | Analyst | Respondent |
| --- | --- | --- | --- | --- | --- |
| Manage workspace and member access | Yes | Yes | No | No | No |
| Approve spending, top-ups, subscriptions | Yes | No | No | No | No |
| Invite or approve employee roster | Yes | Yes | No | No | No |
| Create and edit draft surveys | Yes | Yes | Yes | No | No |
| Publish or duplicate a survey | Yes | Yes | Yes, subject to product policy | No | No |
| Assign analysts, with every change audited | Yes | Yes | No | No | No |
| Read identified answers and transcripts | Yes, disclosed and audited | Yes, disclosed and audited | Own surveys | Assigned surveys | Own response only |
| Answer a survey | If eligible | If eligible | If eligible | If eligible | If eligible |
| Read billing and usage | Yes | Yes | No | No | No |

The respondent disclosure must name reader classes before the first answer is saved.
Dashboard aggregates must preserve the same permission checks and must not expose
respondent identity through metric labels.

## KPI and drilldown matrix

Every dashboard card carries its time window, workspace, survey, model or provider when
relevant, sample count, data coverage, and the next permitted drilldown. Null means
unknown. Zero means measured zero. `At least` means some contributing records were
unmetered.

| Domain | KPI | Definition | Denominator and exclusions | Drilldown |
| --- | --- | --- | --- | --- |
| Validation | Acceptance rate | Accepted checks / (accepted + refused checks) | No-action turns separate; missing spans excluded and reported | Workspace > survey > run > turn > decision > validation |
| Validation | First-pass acceptance | First-attempt accepted answers / answers with a first attempt | Retries remain visible | Same, then attempt history |
| Quality | Supported-answer rate | Human-supported / (supported + invented) | Unsure and unlabelled excluded; label coverage shown | Survey > run > answer > transcript |
| Evaluation | Clean-run rate | Eligible completed runs with no hard failure / eligible completed runs | Capped, failed, unfinished, and mismatched cohorts excluded and counted | Batch > scenario > run > hard check |
| Reliability | Request success rate | Successful provider attempts / all provider attempts | Include failures and failovers | Provider > model > attempt > error |
| Reliability | Completion rate | Completed runs / started runs | Abandoned and failed runs remain in denominator | Survey > run |
| Cost | Known provider cost | Sum of priced attempt costs | Unknown cost is not zero; show pricing coverage | Workspace > survey > run > attempt |
| Cost | Cost per completed response | Known operational cost / completed responses | Show cost coverage and completed count; include failed-run overhead | Month > survey > run |
| Cache | Cache call rate | Attempts with cached tokens > 0 / attempts reporting cache | Missing cache fields excluded and counted | Provider > model > attempt |
| Cache | Weighted cache token ratio | Sum cached tokens / sum prompt tokens for paired known rows | Never average per-call percentages | Provider > model > attempt |
| Cache | Cache reuse savings | Input price minus cached-input price for known tokens | Estimate only with known rates and tokens | Pricing version > attempt |
| Latency | Turn p50, p95, p99 | Percentile of respondent-visible turn duration | Raw observations, never average percentiles | Survey > run > turn |
| Latency | Provider p50, p95, p99 | Percentile of provider attempt duration | Separate first-token latency | Provider > model > attempt |
| Latency | Time to first token | Percentile of reported first-token time | Missing timing reported as missing | Provider > model > attempt |
| Traffic | Throughput | Requests or completions per fixed bucket | Bucket size and timezone shown | Workspace > survey > bucket |
| Traffic | Active concurrency | In-flight sessions measured as a gauge | Never infer from historical run status | Operator > worker > bucket |
| Spikes | Spike rate | Flagged eligible buckets / eligible buckets | Baseline and minimum volume required | Metric > workspace > bucket > events |
| Billing | Allowance usage | Unique completed responses / included allowance | Post-exhaustion active completions shown separately | Workspace > month > response event |

## Spike detection contract

Spikes cover the selected behaviours: errors, latency, cost, and traffic. The default
comparison is the current 5-minute bucket against the preceding 60-minute baseline,
excluding the current bucket. Every alert stores baseline, current value, absolute delta,
relative delta, minimum-volume decision, and detector version. A zero baseline produces
`insufficient baseline`, not an infinite percentage.

Thresholds are configuration until pilot data calibrates them and must be labelled
provisional. A spike is an alerting signal, not proof of cause.

## Telemetry fields required for implementation

Every billable or operational event needs `workspace_id`, optional `survey_id` and
`run_id`, `operation`, `request_id`, `event_id`, `provider`, `model`, prompt or policy
version, application version, observed timestamp, status, sanitized error class, pricing
version, and meter coverage. A run can be absent for generation, authentication,
billing, or workspace events. Raw transcript content belongs in protected storage, not
metric labels.

The current trace implementation is conduct-focused and joins lens rows to a run and
survey. It cannot yet support this complete contract. Generation, embeddings, evaluation,
interpretation, authentication, billing, and background work need common correlation and
workspace boundaries before their costs can be commercial truth.

## Live evaluation proposal, approval required

Run six pinned scenarios twice, for 12 runs total: numbers and dates, write-ins,
skip-heavy answers, prompt injection, probe-budget behaviour, and evasive answers. Use one
model snapshot, one conduct prompt version, no failover, synthetic employee inputs, and
hard scripted checks. Human faithfulness labels are separate and are not replaced by a
judge model.

For a planning estimate of 300 calls at 4,000 input and 500 output tokens, GPT-4o Mini
would cost about $0.27 at the published standard rates of $0.15 per million input tokens,
$0.075 cached input, and $0.60 output. A conservative envelope of 600 calls at 8,000
input and 1,000 output tokens is about $1.08. Proposed approval ceiling: $2, subject to
a per-call reserve guard and an explicitly configured model snapshot. These are estimates,
not authorization to spend. See the [official model pricing](https://developers.openai.com/api/docs/models/gpt-4o-mini).

The batch must stop before a call if its reserved worst-case cost would cross the cap,
reconcile every attempt including failures, and record the scenario cohort. The current
implementation has a post-turn cap check and should not run a paid batch until that
guard is moved before the call.

## Known release blockers

- Workspace isolation is implemented in the working branch with database row policies,
  tenant-consistent references, tenant cache keys, and scoped file-ledger reads. Deployment
  requires the restricted database role described in [WORKSPACE_ISOLATION.md](WORKSPACE_ISOLATION.md).
  Company provisioning and the workspace management interface remain to be built.
- Explicit workspace roles and survey-scoped analyst assignment are implemented on the
  working branch for accounts with a role. Legacy rows without a role still use the old
  job compatibility path until provisioning/backfill is completed.
- Invitation and approved-roster registries now exist with one-time invitation tokens and
  append-only access audits. Verified-email shared-link entry, automatic account
  provisioning from those records, disclosure, and audited owner/admin transcript access
  are not implemented end to end. Analyst grants now have an append-only audit trail and
  are restricted to workspace owners/admins.
- Owner-configurable retention, explicit confirmation for shortening, and the protected
  purge path are implemented on the working branch. Scheduled invocation, backup
  retention, and deletion notices still need production policy and evidence.
- Billing, idempotent completed-response events, allowance enforcement, top-ups, seats,
  and provider webhooks are absent.
- The frontend is respondent and lens focused. Commercial workspace, authoring, results,
  usage, and billing screens are not present.
- Backup configuration and a real restore test are not proven.
- The 100-respondent concurrency target needs a fake-provider load test and a transaction
  design that does not hold one database connection during an LLM call.

These blockers are the release gate. A green unit or architecture suite does not make
the product commercially ready while tenant isolation, identity, billing, and restore
evidence remain open.
