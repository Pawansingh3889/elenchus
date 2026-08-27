#!/usr/bin/env bash
# Reset the stack to a known demo state, in about a minute.
#
# Leaves the database holding: a published survey with a respondent part-way
# through it, the refusal you get for trying to edit a published survey, a survey
# demonstrating conditional visibility with a completed run that skipped a
# question, and the curated sample dataset the seed loads. Safe to re-run.
#
# This used to walk through versioning: publish, edit, publish again, and show an
# in-flight run still being asked the questions it started on. Versions were
# removed on 16 Aug 2026 and publishing became a freeze on 17 Aug, so that walk
# now describes a product that does not exist. Worse, it did not fail politely:
# the edit returns 409, `curl -sf` exits non-zero, and `set -e` killed the script
# half way, leaving a demo that looked built and was not.
#
#   ./scripts/demo_reset.sh            wipe the volume and bring the whole stack up
#   ./scripts/demo_reset.sh --db-only  wipe only the database, leave servers running
#
# Use --db-only when you are running the backend and frontend yourself (uv run
# uvicorn / pnpm dev): the full reset starts the compose frontend, which will
# fight a dev server for port 3000.
set -euo pipefail

cd "$(dirname "$0")/.."
API=http://localhost:8000/api/v1
AVA=00000000-0000-0000-0000-0000000000a1      # author
ROSA=00000000-0000-0000-0000-0000000000b1     # respondent
REMY=00000000-0000-0000-0000-0000000000b3     # respondent

DB_ONLY=${1:-}
# Podman is the verified path on Fedora; Docker works the same, and a podman-docker
# shim makes `docker` delegate to podman, so preferring it is safe either way.
RUNTIME=docker
command -v docker >/dev/null 2>&1 || RUNTIME=podman
COMPOSE="$RUNTIME compose"

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }
post() { curl -sf -X POST "$1" -H "X-User-Id: $2" -H 'Content-Type: application/json' --data "${3:-}"; }
id_of() { python3 -c "import sys,json;print(json.load(sys.stdin)['id'])"; }

if [[ "$DB_ONLY" == "--db-only" ]]; then
  say "Wiping the database (leaving your servers alone)"
  # `compose ps -q` returns nothing under podman-compose, so find it by name instead.
  # Anchored on this project's compose name rather than a bare `grep postgres`: the next
  # line is a DROP DATABASE, and matching any running container with "postgres" in its
  # name means a second project's database is one naming coincidence away from being the
  # one that gets rebuilt. A destructive command should name its target.
  PG=$($RUNTIME ps --format '{{.Names}}' 2>/dev/null | grep -m1 -E '^elenchus[-_]postgres' || true)
  [[ -n "$PG" ]] || {
    echo "this project's postgres is not running (expected a container named" >&2
    echo "elenchus_postgres_1 or elenchus-postgres-1); start it with 'make stack-up'" >&2
    exit 1
  }
  $RUNTIME exec "$PG" psql -U elenchus -d postgres \
    -c "DROP DATABASE IF EXISTS elenchus WITH (FORCE);" -c "CREATE DATABASE elenchus;" >/dev/null
  ( cd backend
    export DATABASE_URL=postgresql+asyncpg://elenchus:elenchus@localhost:5432/elenchus
    uv run alembic upgrade head >/dev/null
    uv run python -m app.seed >/dev/null )
  # No backend restart needed: the engine sets pool_pre_ping, so pooled connections
  # killed by the DROP are detected and replaced on next use.
  echo "  database rebuilt from migrations and seeded"
else
  say "Wiping the volume and rebuilding the stack"
  $COMPOSE down -v >/dev/null 2>&1 || true
  $COMPOSE up -d >/dev/null 2>&1
  echo "  stack up, migrations applied, users and sample data seeded"
fi

until curl -sf "$API/health" >/dev/null 2>&1; do sleep 1; done

say "Publishing a survey"
TEMPLATE=$(post "$API/templates" "$AVA" '{
  "title": "Onboarding check-in",
  "description": "How the first few weeks went.",
  "questions": [
    {"text":"What is your role?","answer_type":"short_text","options":[],"allow_other":false,"required":true,"allow_follow_ups":true},
    {"text":"How well did onboarding prepare you?","answer_type":"rating","options":[],"allow_other":false,"required":true,"allow_follow_ups":false},
    {"text":"Which shift do you usually work?","answer_type":"single_select","options":["Days","Nights","Rotating"],"allow_other":true,"required":true,"allow_follow_ups":false}
  ]}' | id_of)
post "$API/templates/$TEMPLATE/publish" "$AVA" >/dev/null
echo "  $TEMPLATE published (3 questions)"

say "A respondent starts answering it"
RUN=$(post "$API/runs" "$ROSA" "{\"template_id\":\"$TEMPLATE\"}" | id_of)
echo "  run $RUN open, shows as Continue on Rosa's home"

# Deliberately expects a refusal, so it cannot use `post`: that is `curl -sf`, which
# exits non-zero on a 4xx and would take `set -e` with it. The point of showing it at
# all is that the rule is the demo. Nobody's answer can be re-pointed at a question they
# were not asked, so the survey Rosa is part-way through cannot change under her.
say "The author tries to rewrite it, and cannot"
EDIT=$(curl -s -o /tmp/demo_edit.$$ -w '%{http_code}' -X PUT "$API/templates/$TEMPLATE" \
  -H "X-User-Id: $AVA" -H 'Content-Type: application/json' --data '{
  "title": "Onboarding check-in",
  "description": "How the first few weeks went.",
  "audience": "everyone",
  "questions": [
    {"text":"What is your role?","answer_type":"short_text","options":[],"allow_other":false,"required":true,"allow_follow_ups":true},
    {"text":"Would you recommend the onboarding to a new starter?","answer_type":"yes_no","options":[],"allow_other":false,"required":true,"allow_follow_ups":false}
  ]}')
if [[ "$EDIT" == "409" ]]; then
  python3 -c "import sys,json;print('  refused:', json.load(open(sys.argv[1]))['error']['message'])" "/tmp/demo_edit.$$"
else
  echo "  UNEXPECTED: editing a published survey answered $EDIT, not 409" >&2
  cat "/tmp/demo_edit.$$" >&2
fi
rm -f "/tmp/demo_edit.$$"

say "A survey whose second question only applies to some respondents"
COND=$(post "$API/templates" "$AVA" '{
  "title": "Site induction",
  "description": "Shows a question only when it applies.",
  "questions": [
    {"text":"What is your role on site?","answer_type":"single_select","options":["Quality Manager","Line Operator"],"allow_other":false,"required":true,"allow_follow_ups":false},
    {"text":"Which quality outcomes are you accountable for?","answer_type":"long_text","options":[],"allow_other":false,"required":true,"allow_follow_ups":true,"show_when":{"question":0,"op":"is","value":"Quality Manager"}},
    {"text":"Rate the induction","answer_type":"rating","options":[],"allow_other":false,"required":true,"allow_follow_ups":false}
  ]}' | id_of)
post "$API/templates/$COND/publish" "$AVA" >/dev/null
echo "  $COND published — q2 shows only when q1 is Quality Manager"

# Needs a model. Without one the demo still stands up; only this run is missing.
say "A respondent whose answer skips that question"
if CRUN=$(post "$API/runs" "$REMY" "{\"template_id\":\"$COND\"}" | id_of 2>/dev/null); then
  for msg in "i'm a line operator" "4" "4"; do
    STATUS=$(curl -sf "$API/runs/$CRUN" -H "X-User-Id: $REMY" | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])")
    [[ "$STATUS" == "completed" ]] && break
    post "$API/runs/$CRUN/messages" "$REMY" "{\"content\":\"$msg\"}" >/dev/null 2>&1 || {
      echo "  (no working LLM configured — skipping this run)"; break; }
  done
  # respondent_label, not respondent_name: answers became anonymous on 12 Aug 2026 and
  # the field carries a pseudonym now. The old name sat behind `2>/dev/null || true`, so
  # the KeyError it raised printed nothing whatsoever and this section simply looked like
  # it had found nothing to report. A shape change should be noisy, so the error is
  # visible and only the exit status is forgiven.
  curl -sf "$API/templates/$COND/runs" -H "X-User-Id: $AVA" | python3 -c "
import sys, json
runs = json.load(sys.stdin)
if not runs:
    print('  (no run recorded: this one needs a working LLM tier)')
for r in runs:
    print(f\"  {r['respondent_label']} finished at {r['answered']} of {r['total']}, so the conditional question was skipped\")
" || echo "  (could not read the run list, see the error above)" >&2
fi

cat <<EOF

Ready. The AI summary is deliberately left ungenerated so it can be run live.

Sign in at http://localhost:3000/signin by typing the address. It used to be a
picker in the top bar; that became a page, and an address is what it asks for.

  Author      http://localhost:3000                              ava@elenchus.dev
  Builder     http://localhost:3000/templates/$COND
  Results     http://localhost:3000/templates/$COND/results
  Respondent  http://localhost:3000/respond                      rosa@elenchus.dev
  Continue    http://localhost:3000/runs/$RUN

  To show a follow-up firing, answer "What is your role?" vaguely
  ("bit of everything really") — that question permits probing.
EOF
