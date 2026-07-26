#!/usr/bin/env bash
# Regenerate .env from the committed, sops-encrypted .env.encrypted.
#
# Needs the age private key at ~/.config/sops/age/keys.txt (sops's default lookup
# path — see .sops.yaml). Refuses to overwrite an existing .env without --force,
# since .env is the live file docker-compose reads and local edits are easy to lose.
#
# Note: sops's dotenv round-trip drops pure blank lines (a known formatting quirk);
# every comment and KEY=VALUE line is preserved exactly.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env && "${1:-}" != "--force" ]]; then
  echo "error: .env already exists. Re-run with --force to overwrite it." >&2
  exit 1
fi

sops --decrypt --input-type dotenv --output-type dotenv .env.encrypted > .env
echo "wrote .env from .env.encrypted"
