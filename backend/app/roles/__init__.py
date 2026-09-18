"""Named permission bundles a person can carry alongside their job.

The job (function + band + hats, see `app.users.models`) stays the one source of what
somebody's *position* lets them do. A role is a second, independent source: an admin
names a set of `Permission`s once ("Survey Auditor" = read every survey's rows) and
attaches or detaches it from any account, the way an AWS IAM policy is attached to a
user without describing their place in an org chart.

Additive only, by design. A granted permission can only ever widen what `app.access`
allows; nothing here can take away what the job already grants, and there is no
explicit-deny. Real policy evaluation (allow/deny precedence, conditions, resource
scoping) is exactly the complexity CLAUDE.md already rejected once when it passed on
Oso, OpenFGA, SpiceDB, Cerbos and pycasbin for `app.access` itself — this stays a set
union so it can be read as easily as the rules it extends.
"""
