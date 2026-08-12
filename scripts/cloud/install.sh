#!/usr/bin/env bash
# Idempotent dependency refresh for the Cloud Agent environment.
# Installs system packages (PostgreSQL 16, Python venv support), the API's
# Python dependencies, and the web app's node modules. Safe to re-run.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

export DEBIAN_FRONTEND=noninteractive

echo "[install] apt packages (postgresql-16, python venv)"
sudo apt-get update -qq
sudo apt-get install -y -qq postgresql postgresql-contrib python3.12-venv

echo "[install] python virtualenv + API deps"
if [ ! -d .venv ]; then
  python3.12 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r apps/api/requirements.txt

echo "[install] web dependencies"
if [ -f apps/web/package-lock.json ]; then
  npm --prefix apps/web ci
else
  npm --prefix apps/web install
fi

echo "[install] done"
