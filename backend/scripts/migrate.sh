#!/bin/sh
# Migrations use deployment credentials; the API uses its restricted runtime role.
set -eu

if [ "${APP_ENV:-dev}" = "prod" ] && [ -z "${MIGRATION_DATABASE_URL:-}" ]; then
    printf '%s\n' 'MIGRATION_DATABASE_URL is required in production.' >&2
    exit 1
fi

if [ -n "${MIGRATION_DATABASE_URL:-}" ]; then
    DATABASE_URL="$MIGRATION_DATABASE_URL" alembic upgrade head
else
    alembic upgrade head
fi
