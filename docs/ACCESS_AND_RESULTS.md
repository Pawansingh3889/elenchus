# Who can see what, and what the answers are worth

Two questions this service has real answers to: which people a survey is for, and how
much you can trust a recorded answer. This is a record of what is built, not a plan, and
it is updated when the model changes rather than appended to: a document that describes
retired code as current is worse than no document. The access model below is the one
adopted on 13 Aug 2026; what it replaced, and why, is at the [end](#history-the-models-this-replaced).

Everything in this file is enforced by `app/access`: pure functions over values, no
session and no queries, so the rules read in one sitting and their tests need no
database. `tests/test_access_rules.py` is the matrix that pins them.

## One job per person

Nobody has a stored role. Each person holds exactly one job: a `function` (production,
quality, health_safety, technical, planning, hr, finance, supply_chain, it, executive)
crossed with an ordered `band` (operative, line_leader, supervisor, manager, head,
director), plus zero or more `hats` (health_safety first: a supervisor with H&S duties
keeps their job and carries the hat).

One job per person is the schema's version of an RBAC separation-of-duty constraint. The
model exists because the thing it replaced could disagree with the org chart: a
membership table recorded a line leader who was also QA, a job the plant does not
contain. A join table can record that; one job cannot.

Every right derives from the job and is stored nowhere:

- **Authoring is band, not a column.** `may_author` is manager band and up, any
  function. The `role` column is gone; `require_author`'s name survives its contents.
- **`microsoft_id` is a sign-in method and decides nothing.** Line leaders hold ERP
  logins without that making them survey authors, which is the contradiction the stored
  role used to record.

## Who a survey is for

A survey is aimed at exactly one audience, and every audience except `person` is a
predicate over the job, evaluated live. There are no membership rows to drift:

| Audience | Who that is |
| --- | --- |
| `everyone` | Anyone who holds a job. Deliberately not "every account": a service or administration login belongs to nobody on any ladder, and counting it would put people in a denominator who were never asked |
| `operatives`, `line_leaders`, `supervisors`, `shift_managers` | One band of the production function each, because that is how the floor is addressed |
| `managers` | The manager bands and up, wherever they work |
| `qa` | The whole quality function, ground QA to head |
| `health_safety` | The H&S function, plus everyone carrying the H&S hat, because the duty is what the survey is about |
| `person` | One named individual, carried in `survey_templates.audience_user_id`. Exists for the case it was asked for: a first-weeks survey aimed at the person who just joined |

The audience value is set when the survey is created and fixed once published, like the
questions. Who is *in* it is whoever holds the job at the moment of asking: reach is
live, by decision, so a new starter is asked Monday's survey and every denominator moves
when a job does. What keeps that honest is in
[Reach is live, and edits are witnessed](#reach-is-live-and-edits-are-witnessed).

## Who sees what

Every rule returns an `AccessDecision`: allowed or not, and why. A bare bool would be
enough to enforce a rule and useless to debug one, so a refusal names its reason, and
the reason reaches the error message ("this survey is for the production line_leader
band", "your account holds no job on the plant"). Ambiguity fails closed and says which
piece was missing: a survey with no audience reaches nobody but its author and an admin,
with a reason that tells whoever has to fix the deployment where to look.

- **`may_answer`**: the job, read live, with two escape hatches so an author can test
  their own survey and an admin can unstick one. `in_audience` is the same question with
  both hatches shut, and it is what denominators count, so a survey is never "answered by"
  someone it was not aimed at.
- **`may_list`** is as strict as `may_answer`, because existence is information. A survey
  called "Finance restructure feedback" tells you something before a single answer is
  given, so a survey you cannot answer is one you cannot see the name of. Colleagues,
  leadership and admins see it too, since they may read what comes back.
- **`may_read_rows`**, individual runs and answers, is narrower and deliberately not
  about the audience. Being asked a question does not entitle you to read what your
  colleagues answered, and in a workplace survey that distinction is the difference
  between honest answers and careful ones. Rows go to the author, their function
  colleagues at authoring band (so a survey does not become unreadable when one person is
  away), site leadership and admins. The audience's own seniors get nothing here, by
  decision: HR surveying the QA team does not hand head QA the raw answers, or nobody
  could survey a team candidly about its own management.
- **`may_read_totals`**, counts and distributions without the rows behind them, is for
  anyone who may read rows or answer. There is no suppression threshold: a filtered
  total over a group of two is in effect those two people's answers, decided knowingly
  (see [Decided against](#decided-against)).
- **`may_edit`**, save, publish, close, summarise, is owner or admin only. Deliberately
  narrower than listing: colleagues read, they do not publish in somebody else's name.
- **The executive function reads every survey and edits none.** Site leadership
  oversight, decided deliberately: `reads_all_surveys` grants the read paths and
  `may_edit` has no executive branch. A factory manager who wants a survey changed asks
  the person whose name is on it.

**Colleagues** are the authoring bands of one function, symmetric and stopping there.
The band check matters: functions contain the floor, so "same function" alone would make
every production operative a colleague of the shift manager surveying them. Worth naming
what colleague access costs: answers are read by people the respondent never dealt with,
which is wider than the pseudonymity below might suggest to them.

**Roles** are a second, independent grant beside the job (`app.roles`). An admin defines
a named bundle of permissions (`survey_author`, `survey_edit`, `survey_list`,
`results_read_rows`, `results_read_totals`, `admin_all`) and attaches it to any account,
regardless of that account's function or band — an auditor who holds no job on the plant
at all can still be granted `results_read_rows`. Every rule above reads a role's grants
as one more way in, never a way to take something away: a role can only widen what the
job already allows. There is no explicit-deny and no resource scoping, on purpose —
see the decision log in the root `CLAUDE.md` for what that trades away and what it costs
against the one-job-per-person model above. Attaching or detaching a role writes to the
same `account_changes` audit table a band or hat edit does, so it is admin-only and
always has a name attached.

## What an answer is worth to the person who gave it

Responses carry pseudonyms, not names, on every read path including leadership's. The
transcripts are verbatim, so a respondent can still be identifiable by what they wrote;
the pseudonym is a floor, not anonymity. A respondent can withdraw their response
afterwards: the erasure route replaces their answers with a withdrawal marker, and the
counts that depended on those answers move, because a count that survives the withdrawal
of the answers behind it would be a fabrication.

## Administration

Admin comes from the IT function, or from the `ADMIN_EMAILS` allowlist, case-folded.
The function route was asked for directly, and it is worth being clear-eyed about the
cost: `UPDATE users SET function = 'it'` is now a grant of administration, where before
the database could not confer it. The allowlist stays alongside so an administrator who
does not work in IT is expressible. Both routes log when they grant, and log which one
did, because both are easy to change and hard to audit afterwards.

The seed ships no administrator on purpose: a committed seed with an admin in it would
hand administration to anyone who can read the repository. A fresh database is
administered by naming an address in `ADMIN_EMAILS`.

### Accounts are made in the app

`POST` and `PUT /api/v1/admin/users` create accounts and change what somebody is, jobs and
hats included. There has been no screen for it since the browser was cut to the respondent
path on 13 Sep 2026, so an administrator calls the API directly. Both
routes are guarded by `require_admin`, which asks `is_admin` and never the job it is
editing.

What the service refuses: a second account on one address or one Entra id (addresses are
case-folded on the way in, because `is_admin` folds when it matches the allowlist and
the unique index does not), and an edit through which an administrator would remove
their own administration, because the state where the last admin moved out of IT is
unrecoverable from inside the app.

### Reach is live, and edits are witnessed

Who a survey is for is whoever holds the job at the moment of asking. That was
reaffirmed 13 Aug over freezing membership into published versions, and three things
make it honest:

- **The publish confirmation shows the live headcount** beside the audience, phrased as
  "right now", because that is what it is.
- **An admin edit that would move an open survey's reach shows the impact first**: which
  surveys, reach before and after, whether the person can still answer, and
  `may_author_before/after` so the browser never re-derives band order. Warn and
  proceed, never block. People genuinely change jobs; the number dropping is then true.
- **`account_changes` records every create and edit**, append-only, in the same
  transaction as the change, with before and after snapshots and the administrator's
  name. The edit dialog shows the recent rows. An account with no rows was made by the
  seed or will arrive from Entra: nobody in the app did it, and that too is information.
  Rows written under retired vocabularies are served in those vocabularies, because an
  audit trail that rewrites history is not one.

Authorization engines (Casbin, Oso, OpenFGA, SpiceDB, Cerbos) were evaluated for this on
13 Aug and rejected with reasons recorded in the project log: the guardrails above are
change-management around what the access rules read, which no engine ships, and
`app/access` stays the one place the rules live. One number to keep in mind: reach and
the preview iterate every user and open survey per request, which is fine at plant size
and author-side only.

## The survey lifecycle

`draft` → `published` → `closed`, with `archived` meaning something else entirely.

`archived` is "hide this from my list". `closed` is "the study is over and these numbers
are final". They read alike until the dashboard is busy, and an author closing a survey
in order to read its results should not have to hide it to do so.

**Closing stops new runs and leaves conversations already under way alone.** Stopping
mid-question would discard answers a respondent has already given, and for a chat that
is a worse bargain than a final count that settles a few minutes late.

## The author's dashboard

Every survey an author owns, with runs started, completed, in progress and abandoned, in
**one request and one query**. Listing templates and then counting each one's runs is an
N+1 that looks fine against five surveys and falls over on the hundredth.

Outer joins throughout, so a survey published but never answered, or never published at
all, appears with zeros rather than vanishing, which is the survey an author is most
likely to be checking on.

`completion_rate` is null when nobody has started, not zero. Zero reads as everyone
abandoning, which is a different fact and the wrong one on a survey published an hour
ago.

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
see". The current one (`conduct_v8`) says the opposite, and states the write-in
mechanism, since a model told to use one wrote `"Other: ..."` as though Other were a
prefix.

**Follow-ups are capped at three**, and the prompt says a ceiling is not a target. The
engine enforces it whatever the model asks for, which is its own test.

## How the rules are kept

- **`scripts/check_access_consulted.py`** fails the build when survey data leaves a
  service without consulting `app/access`. A wrong rule is visible in review; a method
  that never asks is not, because it looks complete and returns the right type. It
  follows private helpers within a module, because that is where ownership is really
  settled, and a guard blind to delegation would teach people to write exemptions. An
  exemption is a sentence you have to write: `access-exempt:` with no reason is itself a
  violation.
- **`backend/tests/live_runs/`** keeps real transcripts, replayed by the mocked suite on
  every push, in two directions. Answers a real model produced and the engine accepted
  must still be accepted, which catches a gate tightened too far. Answers a human marked
  `invented` must be refused, which is how a live finding becomes permanent.
  `scripts/eval_report.py` ratchets the corpus's facts, so it cannot quietly shrink.
- `make gate` runs six guards, the eval ratchet and an 870-odd-test suite, and
  `make gate-proof` plants a violation for each guard.

## Decided, and deliberately not built yet

- **Microsoft sign-in.** `POST /api/v1/dev/identify` and the `X-User-Id` shim are the
  whole of authentication, so knowing an address is enough to act as somebody. The
  Entra ids on seeded authors are stand-ins for the login the authoring bands will hold.
- **Respondent identity for the floor**: QR badge tokens for people without logins.
- **Free text is not retired.** New surveys are meant to use closed types only; the
  builder and the generator still offer `short_text` and `long_text`.
- **Answer constraints**: `min_value`, `max_value`, `max_choices`.

## Decided against

- **A suppression threshold.** Results are sliceable by any closed answer, so a filtered
  total over a group of two is in effect those two people's answers. This was declined
  knowingly, and the slicing was built so a threshold is one constant away:
  `SLICE_MIN_GROUP` in `frontend/lib/slicing.ts`, currently 0, gates every sliced view.
- **A stored role, a membership table, or an authorization engine.** Each was tried or
  evaluated and each lost to the job model; see the history below.

## History: the models this replaced

Kept because the reasoning transfers, and because `account_changes` rows written under
these vocabularies still serve them.

- **9 Aug 2026: role plus creator department.** `users.role` said author or respondent;
  creators carried a `department` (admin, hr, operations, finance, technical) and
  audiences named those office teams. It broke on the plant's actual shape: the senior
  floor bands hold sign-in accounts, so the "creators cannot answer" rule refused every
  supervisor a survey aimed at supervisors.
- **13 Aug 2026, first half of the same day's work: plant groups plus a membership
  table.** Audiences became floor groups, membership a join table so groups could
  overlap, and departments grouped authors. The join table promptly recorded a line
  leader who was also QA, a job the plant does not contain, and "who may author" was
  still a stored fact that could disagree with the org chart.
- **13 Aug 2026: one job per person**, described above, replacing all three
  vocabularies. Grounded in the NIST RBAC model (role hierarchy plus static separation
  of duty) and ordinary job-architecture practice. The migration remapped by an explicit
  seed map plus generic rules, and old `account_changes` rows are served in their old
  vocabulary, because an audit trail that rewrites history is not one.
