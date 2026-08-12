#!/usr/bin/env bash
# Smoke health probes — no credentials required.
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"

curl -sf "${API_BASE}/health" >/dev/null
curl -sf "${API_BASE}/health/ready" >/dev/null
echo "smoke ok: ${API_BASE}/health and /health/ready"
