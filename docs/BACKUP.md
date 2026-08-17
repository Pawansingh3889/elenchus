# Backups, and how we know they work

A survey's answers are the only copy of what somebody said. This file is what stands
between that and a bad afternoon.

It is written to the **3-2-1-1-0** rule, which is the current form of the old 3-2-1 and
the one CISA endorses in its ransomware guidance: **3** copies, on **2** kinds of media,
**1** off site, **1** immutable, and **0** errors on the last restore test that somebody
actually ran. The last two digits are the ones people skip and the ones that decide
whether any of this was real.

## Why this matters more here than in most apps

Two decisions raise the stakes, both taken deliberately and both recorded in CLAUDE.md.

**A published survey cannot be edited**, so the answers under it were given to exactly
the questions stored beside them. That property is worth having and worth being able to
restore.

**A survey with answers cannot be deleted**, but one without them can, permanently. That
is the operation backups are worst at undoing, because a restore brings back the whole
database at a moment in time rather than one row out of it. If somebody deletes the wrong
survey, the honest answer is point-in-time recovery to just before it, and losing
everything after: which is why the RPO below is minutes rather than a day.

## What is backed up

| | |
| --- | --- |
| **The database** | Every survey, question, run, answer, transcript, account and audit row. This is the irreplaceable part. |
| **The LLM spend ledger** | `backend/var/llm_ledger.jsonl`, append-only. Rebuildable from nothing, so it rides along rather than driving the design. |
| **Not the code** | It is in git, which is already three copies on two media off site. |
| **Not `.env`** | Secrets belong in a password manager, not in a backup that gets copied around. Restoring a database into a deployment with no `.env` fails loudly, which is correct. |

## How it works

**Continuous archiving.** Postgres writes a write-ahead log; every completed segment is
shipped to object storage as it closes. A nightly base backup plus that stream is what
makes point-in-time recovery possible: "restore the state at 14:32, just before the
delete" is a real command rather than a wish.

**pgBackRest** does the shipping. It is the general-purpose choice for a deployment this
size: block-level incremental backups, parallel restore, and repository encryption, and
after a maintenance scare in spring 2026 it is now funded by six sponsors rather than
one, which is a better bus factor than it had.

**Object storage with a lock.** The repository lives in S3-compatible storage with object
lock switched on, so a compromised admin account or a careless script cannot delete the
backups. This is the immutable copy: the difference between a backup and a backup that
survives the incident it exists for.

## Restoring

Two shapes, and the second is the one that matters.

```bash
# Everything, as of the last backup.
pgbackrest --stanza=elenchus restore

# To a moment: the state just before somebody deleted the wrong thing.
pgbackrest --stanza=elenchus \
  --type=time --target="2026-08-17 14:32:00+01" restore
```

Postgres then replays the log up to that instant. Everything after it is gone, which is
the trade PITR makes and the reason a delete is refused once anybody has answered.

## Proving it, which is the whole point

A backup nobody has restored is a belief, not a backup. `.github/workflows/restore-test.yml`
runs weekly and on demand:

1. Fetches the latest backup into a scratch Postgres.
2. Asserts `alembic current` matches the head the code expects, because a backup that
   restores into a schema the application cannot run against has restored nothing useful.
3. Counts rows in the tables that carry answers and fails if any is empty, since an empty
   restore succeeds quietly and is the failure mode nobody notices.
4. Fails the workflow loudly on any of it.

That is the **0** in 3-2-1-1-0, and it is the same instinct as `make gate-proof` in this
repo: a check nobody has watched fail is decoration.

## What is not done yet

Honest list, because a document describing intentions as though they were code is worse
than no document.

- **The object storage bucket and its credentials do not exist.** Everything below the
  configuration in `docker-compose.prod.yml` is written and untested against a real
  repository. It needs a bucket, a key, and object lock enabled.
- **The retention policy is a guess**: 30 days of PITR and 12 monthly fulls. BRCGS ties
  record retention to product shelf life plus customer requirements, so the plant's own
  standard should replace that number rather than this file inventing one.
- **Nobody has run a restore.** Until the workflow above goes green once, this document
  describes a plan.
