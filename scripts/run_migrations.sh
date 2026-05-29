#!/usr/bin/env bash
set -euo pipefail

# Usage: MIGRATIONS_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db ./scripts/run_migrations.sh
DB_URL=${MIGRATIONS_DATABASE_URL:-${DATABASE_URL:-}}
if [ -z "$DB_URL" ]; then
  echo "Provide MIGRATIONS_DATABASE_URL or DATABASE_URL" >&2
  exit 2
fi

export DATABASE_URL="$DB_URL"
echo "Running alembic upgrade head against $DB_URL"
alembic upgrade head