#!/bin/sh
set -eu

sh scripts/migrate.sh
unset MIGRATION_DATABASE_URL
exec "$@"
