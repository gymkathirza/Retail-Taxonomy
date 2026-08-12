#!/usr/bin/env bash
# Per-boot reconciliation: start PostgreSQL, ensure the app role/database exist,
# apply migrations, and load the seed. Idempotent and safe across restarts.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://taxonomy:taxonomy@localhost:5432/taxonomy}"

echo "[start] starting PostgreSQL 16 cluster"
sudo pg_ctlcluster 16 main start || true

echo "[start] waiting for PostgreSQL readiness"
for _ in $(seq 1 30); do
  if sudo -u postgres pg_isready -q; then break; fi
  sleep 1
done

echo "[start] ensuring role + database"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='taxonomy'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE ROLE taxonomy LOGIN PASSWORD 'taxonomy';"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='taxonomy'" | grep -q 1 \
  || sudo -u postgres createdb -O taxonomy taxonomy

echo "[start] applying migrations"
# shellcheck disable=SC1091
source .venv/bin/activate
( cd apps/api && alembic upgrade head )

echo "[start] seeding taxonomy (idempotent)"
python scripts/seed.py

echo "[start] ready"
