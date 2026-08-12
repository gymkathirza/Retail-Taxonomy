#!/usr/bin/env bash
# Unauthenticated liveness/readiness smoke check. Exits non-zero on failure.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "[smoke] GET ${BASE_URL}/health"
curl -fsS "${BASE_URL}/health" >/dev/null

echo "[smoke] GET ${BASE_URL}/health/ready"
curl -fsS "${BASE_URL}/health/ready" >/dev/null

echo "[smoke] OK"
