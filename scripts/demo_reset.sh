#!/usr/bin/env bash
# Reset the stack to a known demo state, in about 40 seconds.
#
# Leaves the database holding one survey published twice and one respondent
# part-way through version 1, which is the state the versioning walkthrough
# starts from. Safe to re-run: it wipes the volume first.
set -euo pipefail

cd "$(dirname "$0")/.."
API=http://localhost:8000/api/v1
AVA=00000000-0000-0000-0000-0000000000a1      # author
ROSA=00000000-0000-0000-0000-0000000000b1     # respondent

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }
post() { curl -sf -X POST "$1" -H "X-User-Id: $2" -H 'Content-Type: application/json' --data "${3:-}"; }

say "Wiping the database and rebuilding"
docker compose down -v >/dev/null 2>&1
docker compose up -d >/dev/null 2>&1
until curl -sf "$API/health" >/dev/null 2>&1; do sleep 1; done
echo "  stack up, migrations applied, users seeded"

say "Publishing version 1 of the survey"
TEMPLATE=$(post "$API/templates" "$AVA" '{
  "title": "Onboarding check-in",
  "description": "How the first few weeks went.",
  "questions": [
    {"text":"What is your role?","answer_type":"short_text","options":[],"allow_other":false,"required":true,"allow_follow_ups":true},
    {"text":"How well did onboarding prepare you?","answer_type":"rating","options":[],"allow_other":false,"required":true,"allow_follow_ups":false},
    {"text":"Which shift do you usually work?","answer_type":"single_select","options":["Days","Nights","Rotating"],"allow_other":true,"required":true,"allow_follow_ups":false}
  ]}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
post "$API/templates/$TEMPLATE/publish" "$AVA" >/dev/null
echo "  $TEMPLATE published as v1 (3 questions)"

say "A respondent starts answering v1"
RUN=$(post "$API/runs" "$ROSA" "{\"template_id\":\"$TEMPLATE\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "  run $RUN open on v1"

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

cat <<EOF

Ready.
  Author     http://localhost:3000            pick Ava Author
  Respondent http://localhost:3000/runs/$RUN  pick Rosa Respondent
  Results    http://localhost:3000/templates/$TEMPLATE/results
EOF
