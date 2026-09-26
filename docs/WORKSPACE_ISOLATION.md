# Workspace isolation and deployment

Status: implemented on the working audit branch, 21 September 2026. Not deployed.
This is a data-isolation foundation, not evidence that the commercial pilot is ready.
See [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md) for the remaining release gates.

## What the boundary covers

One account belongs to one company. Authentication resolves that existing account's
workspace; request bodies and workspace headers cannot choose it. All 19 customer-data
tables have a required `workspace_id`. PostgreSQL row-level security is enabled and
forced on those tables and on `workspaces`.

The boundary covers people and job histories, surveys, questions, runs, answers,
messages, traces, captured model requests, prompt versions, embedding caches,
interpretability results, human labels, and evaluation runs. Composite foreign keys
prevent a row in one company from naming another company's parent row. Trace links
remain intentionally foreign-key-free because trace writes use a separate transaction.

Workspace scope is transaction-local and reapplied from session state after commit or
rollback. A session cannot switch companies after binding. Background evaluations and
independent trace writes propagate the originating workspace explicitly. With the
restricted runtime role, an unscoped read returns no customer rows and an unscoped insert
fails. This protects against missing application filters, not an attacker with database
credentials or arbitrary SQL execution: trusted server code sets the PostgreSQL scope.

File-ledger entries record the workspace, and every customer-facing ledger reader filters
by it. Historical entries with no workspace are excluded, not assigned to whoever asks.
They are still on disk for an authorized operator to investigate. File storage, database
administrators, backups, and provider infrastructure remain separate access boundaries.

## Authentication bootstrap

Before ordinary queries, a narrow SELECT policy permits looking up exactly the account
identified by a validated session or provider identity. The temporary identity hint is
cleared immediately after lookup. No bootstrap hint authorizes writes.

- Production requires a signed session. `X-User-Id` is only a development shim.
- Google must explicitly return `email_verified: true`, matching an existing account.
- Microsoft must return the Graph object ID already linked in `users.microsoft_id`.
  Matching a mutable email or UPN does not link an account or permit sign-in. Existing
  Microsoft accounts without a trusted pre-linked ID will be refused until provisioned.
- Unknown identities never join a company from an email domain. They are refused unless
  `OPEN_SIGNUP_WORKSPACE_ID` is set, in which case they become respondents in that one
  workspace; an address that already has an account is never linked. Every sign-in is
  recorded in `sign_ins`.

A company's first account is made in the deployment's shell, because nobody can sign in
to make it:

```sh
python -m app.provision "Acme Foods" owner@acme.test "Ada Owner" \
    --function executive --band director [--microsoft-id <Entra object id>]
```

It creates the workspace and its owner in one transaction under the runtime role, records
the owner's creation with no actor, and leaves an address that already has an account
alone. The owner then creates everyone else from the admin screen.

Roster invitations, ownership verification for first-time Microsoft linking, and
shared-link entry still need complete product workflows. Do not enable development
authentication for real customers.

## Separate deployment and runtime credentials

Production requires both variables, supplied through the deployment's secret manager:

| Variable | Purpose | Required role properties |
| --- | --- | --- |
| `MIGRATION_DATABASE_URL` | Apply Alembic revisions | Own application schema objects and be authorized to migrate them |
| `DATABASE_URL` | Serve API requests | Non-owner, not superuser, no `BYPASSRLS`, no membership in the object-owner role |

The container startup script applies migrations first, refuses to start after a failed
migration, removes `MIGRATION_DATABASE_URL` from the server environment, then starts the
API. Production startup independently checks that the runtime role cannot bypass row
security, that it is not a member of the object-owner role, and that every mapped table
has enabled and forced row security. It does not verify policy expressions or every
grant; migration review and isolation tests are still required. The startup script is
not a replacement for separating secrets in a dedicated migration job in a hardened
deployment.

Example grant shape for an operator, after selecting the target database and provisioning
roles through the secret manager. These names are examples, not roles already installed:

```sql
ALTER ROLE elenchus_runtime NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE elenchus TO elenchus_runtime;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO elenchus_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO elenchus_runtime;
REVOKE ALL ON TABLE public.alembic_version FROM elenchus_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE elenchus_deploy IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO elenchus_runtime;
```

The deployment role must actually own existing tables and create future ones for these
default privileges to apply. Do not grant runtime membership in it, schema ownership,
`TRUNCATE`, or migration privileges. Review inherited grants and privileges on functions
as part of deployment. Do not paste passwords into SQL files or commit database URLs.

## Migrating existing data

Revision `ab47d902e631` assigns all pre-existing rows to the explicit legacy workspace
`00000000-0000-0000-0000-000000000001`. It does not infer company ownership from email,
job, or survey title. Before applying it to an existing deployment:

1. Verify a recoverable backup and rehearse migration against a restored copy.
2. Confirm all existing data belongs to one company. Mixed-company databases require an
   explicitly reviewed ownership mapping before this migration can be used.
3. Arrange a maintenance window for backfill and constraint creation. Duration has not
   been measured on production-sized data.
4. Apply migrations with deployment credentials and grant the runtime permissions.
5. Start the API with the restricted role and verify authentication and tenant isolation.
6. Provision additional companies only through a reviewed workflow; no customer-facing
   company provisioning endpoint exists yet.

Downgrade refuses databases containing anything other than one workspace. Do not remove
that check to force a rollback: dropping tenant ownership would combine customer data.

`migrations/metadata.py` provides a copied metadata view of the composite constraints for
Alembic autogenerate. The live ORM keeps its single-column relationships to avoid
ambiguous joins. Update the migration view when future revisions change tenant
constraints. Row policies are explicit migration SQL, not inferred by autogenerate.

## Local verification and limitations

`make gate` runs lint, formatting, typing, import contracts, guards, and the mocked-model
test suite against local PostgreSQL. Tests create a disposable test database, never use
a customer database as their target. Do not run two suites against that same database
concurrently.

The isolation regressions exercise two companies with identical jobs and cache keys,
known foreign IDs, pooled connection reuse, authentication bootstrap, signed-cookie
precedence, traces and results, cache deletion, labels, evaluation identities, clean
migration application, downgrade refusal, and autogenerate preservation. Startup tests check that
migration failure prevents server startup and deployment credentials are not retained in
the server environment. These checks use fake providers and incur no model charges.

Verification snapshot, 21 September 2026: the full backend gate passed with 1,247 tests
passed and 84 skipped. The focused isolation, OAuth, and startup suite passed 54 tests.
This is local verification, not a production deployment or a load-test result.

Still open: legacy role backfill and workspace provisioning, respondent disclosure,
verified-email entry, invitation/roster account provisioning, scheduled retention deletion,
billing, owner-only spending enforcement,
production restore evidence, and 100-respondent load evidence. Accounts without an
explicit workspace role continue through the compatibility job-based permission path.
The 90-day retention policy is implemented, but scheduled execution is not yet proven.
