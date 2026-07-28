#!/usr/bin/env bash
# Reset the stack to a known demo state, in about a minute.
#
# Leaves the database holding: the versioning walkthrough (one survey published
# twice, with a respondent part-way through version 1), a survey demonstrating
# conditional visibility with a completed run that skipped a question, and the
# curated sample dataset the seed loads. Safe to re-run.
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
  PG=$($RUNTIME ps --format '{{.Names}}' 2>/dev/null | grep -m1 postgres || true)
  [[ -n "$PG" ]] || { echo "postgres is not running; start it first" >&2; exit 1; }
  $RUNTIME exec "$PG" psql -U viewops -d postgres \
    -c "DROP DATABASE IF EXISTS viewops WITH (FORCE);" -c "CREATE DATABASE viewops;" >/dev/null
  ( cd backend
    export DATABASE_URL=postgresql+asyncpg://viewops:viewops@localhost:5432/viewops
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

say "Publishing version 1 of the survey"
TEMPLATE=$(post "$API/templates" "$AVA" '{
  "title": "Onboarding check-in",
  "description": "How the first few weeks went.",
  "questions": [
    {"text":"What is your role?","answer_type":"short_text","options":[],"allow_other":false,"required":true,"allow_follow_ups":true},
    {"text":"How well did onboarding prepare you?","answer_type":"rating","options":[],"allow_other":false,"required":true,"allow_follow_ups":false},
    {"text":"Which shift do you usually work?","answer_type":"single_select","options":["Days","Nights","Rotating"],"allow_other":true,"required":true,"allow_follow_ups":false}
  ]}' | id_of)
post "$API/templates/$TEMPLATE/publish" "$AVA" >/dev/null
echo "  $TEMPLATE published as v1 (3 questions)"

say "A respondent starts answering v1"
RUN=$(post "$API/runs" "$ROSA" "{\"template_id\":\"$TEMPLATE\"}" | id_of)
echo "  run $RUN open on v1 — shows as Continue on Rosa's home"

say "The author rewrites the survey and publishes v2"
curl -sf -X PUT "$API/templates/$TEMPLATE" -H "X-User-Id: $AVA" -H 'Content-Type: application/json' --data '{
  "title": "Onboarding check-in",
  "description": "How the first few weeks went.",
  "questions": [
    {"text":"What is your role?","answer_type":"short_text","options":[],"allow_other":false,"required":true,"allow_follow_ups":true},
    {"text":"Would you recommend the onboarding to a new starter?","answer_type":"yes_no","options":[],"allow_other":false,"required":true,"allow_follow_ups":false}
  ]}' >/dev/null
VERSION=$(post "$API/templates/$TEMPLATE/publish" "$AVA" | python3 -c "import sys,json;print(json.load(sys.stdin)['version'])")
echo "  published as v$VERSION (2 questions, one of them new)"

say "The in-flight run is untouched by the republish"
curl -sf "$API/runs/$RUN" -H "X-User-Id: $ROSA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('  still asking:', d['current_question']['text'])
print('  still counting:', d['total'], 'questions (v1), not 2 (v2)')
"

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
  curl -sf "$API/templates/$COND/runs" -H "X-User-Id: $AVA" | python3 -c "
import sys, json
runs = json.load(sys.stdin)
for r in runs:
    print(f\"  {r['respondent_name']} finished at {r['answered']} of {r['total']} — the conditional question was skipped\")
" 2>/dev/null || true
fi

cat <<EOF

Ready. The AI summary is deliberately left ungenerated so it can be run live.

  Author      http://localhost:3000                              pick Ava Author
  Builder     http://localhost:3000/templates/$COND
  Results     http://localhost:3000/templates/$COND/results
  Respondent  http://localhost:3000/respond                      pick Rosa Respondent
  Continue    http://localhost:3000/runs/$RUN

  To show a follow-up firing, answer "What is your role?" vaguely
  ("bit of everything really") — that question permits probing.
EOF
