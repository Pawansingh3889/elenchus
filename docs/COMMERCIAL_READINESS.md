# Commercial release readiness

Updated 26 September 2026. [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) is the current offer
and delivery plan. It replaces the earlier standalone subscription, paid-seat and
verified-email respondent proposal.

## Current implementation

- Public interactive sample with clearly labelled illustrative responses and figures.
- Separate private workspaces created by an explicitly allowlisted operator.
- Bearer passes, signed survey invitations and HttpOnly sessions. Only pass digests are
  stored. Participant accounts are restricted to their invited survey. They supply no
  name or email; their words can still identify them, which the entry page discloses.
- Three lifetime demo surveys, ten questions each, twenty admitted sessions each and
  fourteen days of active access. Deletion does not reset allowances. Concurrent starts
  and creates are serialized in the database. Expired owner passes can still open
  retained results; revoked access is refused for existing sessions too.
- Browser authoring, publication, sharing, conversational responses, live result reads,
  source conversations, summary generation, CSV and native print/save-as-PDF.
- Manual activation after a verified purchase of any KapkotiSolution product. One-time
  purchases qualify permanently. Subscriptions use a paid-through date. Operators must
  explicitly set an agreed monthly respondent-session allowance; no default is implied.
- A shared US$10 monthly demo AI cap, enforced by committed reservations before every
  transport attempt. Unknown usage remains reserved. Correct provider prices are a
  deployment requirement. Customer activity is outside this shared demo cap.
- Forced tenant row policies on new tables and a tenant-consistent pass owner reference.
  Existing customer data remains in place; no database reset is part of release.

## Deployment inputs still required

1. Access to the selected production backend and frontend hosts, with their public URLs.
2. A restricted application database role and separate migration credentials, as described
   in [WORKSPACE_ISOLATION.md](WORKSPACE_ISOLATION.md).
3. A strong `SESSION_SECRET` and explicit operator addresses in `ADMIN_EMAILS`.
4. A working operator authentication method. Real Google and Microsoft OAuth have not
   been exercised without provider credentials. Demo owners and respondents do not need
   OAuth credentials to enter through their private pass or invitation.
5. A funded hosted model, configured token prices, provider limits and verified CORS/cookie
   behavior on the actual deployment domains. Local fake-provider checks do not prove
   real-provider behavior or third-party cookie compatibility.
6. Retention scheduling, published privacy/contact details, backup configuration and a
   successful restore exercise. The existing retention service must be scheduled; a
   written backup plan is not proof that a restore works.

Set `DEMO_ENABLED=true` only after the deployment is configured. Leave
`OPEN_SIGNUP_WORKSPACE_ID` unset for the pass-based offer unless a separate public
respondent workspace is deliberately needed. The development header and email shim
must remain absent in production.

## Release sequence

1. Apply the migration without erasing existing tables or accounts.
2. Deploy the frontend and backend from the same reviewed revision.
3. Sign in as an operator and issue one synthetic trial. Deliver its private link manually.
4. Create, edit, publish, answer and summarise a survey. Check saved evidence and exports.
5. Check the fourth survey is refused, a participant cannot author or read other results,
   and a separate company cannot read this survey.
6. Activate a verified synthetic customer record, check allowances, then revoke it.
7. Start the limited pilot and monitor activation, attempts, failures and budget coverage.

No paid model evaluation is authorized by this plan. Any separate live evaluation needs
an explicitly approved spend ceiling. The general 100-concurrent-respondent target is
not a measured capacity promise; the demo checks cover allowance races, not a load test.

## Later work

Automatic email verification and chatbot pass issuance; product entitlement webhooks;
cross-survey comparisons; action ownership and completion tracking; cohort conversion
and time-to-first-value reporting. Keep these labelled as planned on the public page.

The chatbot will collect contact details and intent. Application rules will verify email,
deduplicate applicants, enforce quotas and issue access. Model output cannot grant roles
or decide whether a purchase qualifies.
