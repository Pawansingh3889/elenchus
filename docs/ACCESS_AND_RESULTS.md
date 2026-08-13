# Who can see what, and what the answers are worth

Two questions this service now has real answers to: which people a survey is for, and how
much you can trust a recorded answer. This is a record of what was built on 9 Aug 2026,
not a plan. Where something was decided and deliberately not built, it says so, because a
document that describes intentions as though they were code is worse than no document.

The file it replaces described a respondent panel with its own attributes and a
suppression threshold. Neither was built, and both were superseded.

## Who can see what

A survey is aimed at exactly one audience: the whole respondent pool, or one creator
department. Creators have a `department` beside their `role`, because what you may do and
which part of the business you are in are different questions, and merging them means a
person cannot both administer and work in Finance.

| | |
| --- | --- |
| Departments | `admin`, `hr`, `operations`, `finance`, `technical` |
| Audiences | `respondents`, `hr`, `operations`, `finance`, `technical` |
| Admin | The `ADMIN_EMAILS` allowlist, **or the `it` department** (see 13 Aug below) |

`app/access` holds the rule and nothing else holds it: pure functions over values, no
session and no queries, so it reads in one sitting and its tests need no database.

- **`may_answer`** replaced a check that the caller's role was `respondent`. That was never
  the real question, and became wrong the moment a survey could be aimed at a department,
  because the people in one are creators.
- **`may_list`** is as strict as `may_answer`, because existence is information. A survey
  called "Finance restructure feedback" tells you something before a single answer is
  given, so a survey you cannot answer is one you cannot see the name of.
- **`may_read_rows`** is narrower and deliberately not about the audience. Being asked a
  question does not entitle you to read what your colleagues answered, and in a workplace
  survey that distinction is the difference between honest answers and careful ones.
- **`may_read_totals`** is for anyone who may answer.

**Ambiguity fails closed and says which piece was missing.** A survey with no audience, or
a creator with no department, reaches nobody but its author and an admin. A bare refusal
would enforce the rule and tell whoever has to fix the deployment nothing.

Admin comes from configuration rather than a column so that granting it is not a database
edit and an admin keeps a real department. That is easy to change and hard to audit, so
`app.access` logs every request the allowlist is what let through.

### Aiming a survey

The audience is set when the survey is created and **frozen once published**, like the
questions. A survey that collects Finance answers and is then pointed at HR ends up with
one set of results drawn from two populations, with nothing recording that it moved.
Republishing with new questions is unaffected: that is the versioning story the app is
built around.

Defaulting to `respondents` is what keeps every survey written before audiences existed
reaching exactly who it always did.

## The survey lifecycle

`draft` → `published` → `closed`, with `archived` meaning something else entirely.

`archived` is "hide this from my list". `closed` is "the study is over and these numbers
are final". They read alike until the dashboard is busy, and an author closing a survey in
order to read its results should not have to hide it to do so.

**Closing stops new runs and leaves conversations already under way alone.** Stopping
mid-question would discard answers a respondent has already given, and for a chat that is
a worse bargain than a final count that settles a few minutes late.

## The author's dashboard

Every survey an author owns, with runs started, completed, in progress and abandoned, in
**one request and one query**. Listing templates and then counting each one's runs is an
N+1 that looks fine against five surveys and falls over on the hundredth.

Outer joins throughout, so a survey published but never answered, or never published at
all, appears with zeros rather than vanishing, which is the survey an author is most
likely to be checking on.

`completion_rate` is null when nobody has started, not zero. Zero reads as everyone
abandoning, which is a different fact and the wrong one on a survey published an hour ago.

## What stops an invented answer

Three gates, each added after a real model produced the failure it now refuses. All of
them judge *source*, which is a separate question from the shape checks in
`validate_answer`.

| Gate | The run that produced it |
| --- | --- |
| `ungrounded_text` | A message that was not an answer became a plausible answer in the author's results |
| `ungrounded_yes_no` | "Would you recommend the new handover process?" answered from the single message `4`, stored as yes |
| `ungrounded_choice` | "Where would AI help you most?" answered "training new starters", stored as "Nowhere I can see" |

The third is the instructive one. An option comes from a list the author wrote, so it
cannot be invented wholesale. What it can be is **wrong**, in the way nothing else
notices: the value is always a legitimate list member and passes every shape check there
is. The test is therefore support rather than authorship, and it is skipped when the
latest message is under four content words, because a respondent may answer positionally
("the second one") and refusing that blocks a real person to catch nobody.

The prompt caused that failure. The conduct prompt of the day said to "map it to the
closest option", which is exactly how "training new starters" became "Nowhere I can
see". The current one (`conduct_v7`) says the
opposite, and states the write-in mechanism, since a model told to use one wrote
`"Other: ..."` as though Other were a prefix.

**Follow-ups are capped at three**, and the prompt says a ceiling is not a target. The
engine enforces it whatever the model asks for, which is its own test.

## How the rules are kept

- **`scripts/check_access_consulted.py`** fails the build when survey data leaves a service
  without consulting `app/access`. A wrong rule is visible in review; a method that never
  asks is not, because it looks complete and returns the right type. It follows private
  helpers within a module, because that is where ownership is really settled, and a guard
  blind to delegation would teach people to write exemptions. An exemption is a sentence
  you have to write: `access-exempt:` with no reason is itself a violation.
- **`backend/tests/live_runs/`** keeps real transcripts, replayed by the mocked suite on
  every push, in two directions. Answers a real model produced and the engine accepted must
  still be accepted, which catches a gate tightened too far. Answers a human marked
  `invented` must be refused, which is how a live finding becomes permanent.
- `make gate` runs six guards and 435 tests, and `make gate-proof` plants a violation for
  each guard.

## Decided, and deliberately not built yet

- **Creators cannot answer anything.** `require_respondent` still guards the conduct
  routes, so a Finance creator cannot answer a Finance survey. The rule is built and
  tested; the door is shut. Opening it is an auth change.
- **Microsoft sign-in**, which is why `ADMIN_EMAILS` grants nobody today: no user has an
  address outside `@elenchus.dev`.
- **Respondent identity**: QR badge tokens, profiles, one response per person.
- **Free text is not retired.** New surveys are meant to use closed types only; the builder
  and the generator still offer `short_text` and `long_text`.
- **Answer constraints**: `min_value`, `max_value`, `max_choices`.
- **The results page**: headline and flags first, question detail below, sliceable by any
  closed answer, with write-ins grouped into suggested options and tracked across surveys.

## Decided against

- **A suppression threshold.** Results will be sliceable by any closed answer, so a filtered
  total over a group of two is in effect those two people's answers. This was declined
  knowingly. The slicing should be built so a threshold is one constant away.
- **A respondent panel with its own attributes.** Respondents are one pool. Creator
  departments are the only grouping that exists.

## 13 Aug 2026: accounts are made in the app

Everything above describes access once people exist. This is how they come to exist, and it
is a later change than the rest of this file, so read it as the correction it is.

Until now `users.role` was written by `app/seed.py` and by nothing else. The honest answer
to "who decides who can be an author" was "whoever can run the seed or reach the database",
which is a deploy action rather than a product one, and it left the plant unstaffable:
somebody in no group can be asked nothing at all, not even a survey aimed at everyone.

`POST` and `PUT /api/v1/admin/users` now create accounts and change what somebody is, and
`/people` is where an administrator does it. Both routes are guarded by `require_admin`,
which asks `is_admin` and therefore never consults `role`: an administrator whose own
account is a respondent must still reach the screen that would fix that.

Four shapes of account are refused, each because the access rules above would otherwise
read the row as something nobody meant:

- **An author with no department.** It decides who their colleagues are, and for `it`
  whether they administer the system.
- **A respondent with a department.** The one that matters most. `_colleague` makes anyone
  sharing a department a colleague and `may_read_rows` hands a colleague every individual
  answer, so this would quietly grant the raw answers to every survey that department ever
  ran.
- **A respondent in no group.** Nobody can survey them, which is the gap this work closed.
- **Two accounts on one address or one Entra id.** Addresses are case-folded on the way in,
  because `is_admin` folds when it matches the allowlist and the unique index does not.

An administrator cannot edit away their own administration. That state is unrecoverable
from inside the app: the last one moves out of `it` and nobody can grant it back.

**`role` is stored as sent, not derived from `microsoft_id`.** That was chosen knowingly
and it contradicts the direction recorded in `app/users/models.py`, where an Entra object
id is meant to decide `role` once real sign-in exists. So an author created here with no
Entra id may build surveys today and will stop being able to the day that derivation is
switched on. The form sets the Entra id for that reason, and `/people` marks every author
that lacks one. That marker is a warning, not a guarantee: nothing enforces the pair.

### Reach is live, and edits are witnessed

Who a survey is for is whoever is in its group at the moment of asking. That is a
decision, reaffirmed 13 Aug over freezing membership into published versions: a new
starter is asked Monday's survey, and every denominator, including a closed survey's
completion rate, moves when membership does. Three things make that honest:

- **The publish confirmation shows the live headcount** beside the audience, phrased as
  "right now", because that is what it is.
- **An admin edit that would move an open survey's reach shows the impact first**: which
  surveys, reach before and after, whether the person can still answer. Warn and
  proceed, never block. People genuinely leave teams; the number dropping is then true.
- **`account_changes` records every create and edit**, append-only, in the same
  transaction as the change, with before and after snapshots and the administrator's
  name. The edit dialog shows the recent rows. An account with no rows was made by the
  seed or will arrive from Entra: nobody in the app did it, and that too is information.

Authorization engines (Casbin, Oso, OpenFGA, SpiceDB, Cerbos) were evaluated for this
and rejected with reasons recorded in the project log: the guardrails above are
change-management around what the access rules read, which no engine ships, and
`app/access` stays the one place the rules live.
