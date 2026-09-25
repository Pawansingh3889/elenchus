"""Deployment migrations must finish before the restricted API starts."""

import os
import subprocess
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("migration_exit", [0, 3])
def test_runtime_keeps_own_credentials_and_never_starts_after_failed_migration(
    tmp_path, migration_exit
):
    migrator = tmp_path / "alembic"
    migrator.write_text(
        '#!/bin/sh\n[ "$DATABASE_URL" = "deployment-database" ] || exit 9\n'
        f"exit {migration_exit}\n",
        encoding="utf-8",
    )
    migrator.chmod(0o700)
    runtime = tmp_path / "server"
    runtime.write_text(
        '#!/bin/sh\n[ "$DATABASE_URL" = "runtime-database" ] || exit 10\n'
        '[ -z "${MIGRATION_DATABASE_URL:-}" ] || exit 11\nprintf runtime-started\n',
        encoding="utf-8",
    )
    runtime.chmod(0o700)
    result = subprocess.run(
        ["sh", "scripts/start.sh", str(runtime)],
        cwd=BACKEND,
        env={
            **os.environ,
            "APP_ENV": "prod",
            "DATABASE_URL": "runtime-database",
            "MIGRATION_DATABASE_URL": "deployment-database",
            "PATH": f"{tmp_path}:/usr/bin:/bin",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == migration_exit
    assert result.stdout == ("runtime-started" if migration_exit == 0 else "")


def test_production_requires_explicit_migration_credentials():
    result = subprocess.run(
        ["sh", "scripts/migrate.sh"],
        cwd=BACKEND,
        env={**os.environ, "APP_ENV": "prod", "MIGRATION_DATABASE_URL": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "MIGRATION_DATABASE_URL is required" in result.stderr
