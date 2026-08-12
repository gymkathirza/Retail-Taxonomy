#!/usr/bin/env bash
# Run the Locust load test headless and write CSV + a text summary.
#
# Env vars (all optional):
#   HOST   target base URL              (default http://localhost:8000)
#   USERS  peak concurrent users        (default 50)
#   RATE   users spawned per second      (default 10)
#   TIME   test duration                 (default 30s)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

HOST="${HOST:-http://localhost:8000}"
USERS="${USERS:-50}"
RATE="${RATE:-10}"
TIME="${TIME:-30s}"

OUT_DIR="perf/results"
mkdir -p "$OUT_DIR"
PREFIX="$OUT_DIR/perf"

echo "Load test -> host=$HOST users=$USERS spawn-rate=$RATE duration=$TIME"

locust -f perf/locustfile.py \
  --headless \
  --host "$HOST" \
  --users "$USERS" \
  --spawn-rate "$RATE" \
  --run-time "$TIME" \
  --csv "$PREFIX" \
  --only-summary \
  | tee "$OUT_DIR/summary.txt"

echo
echo "CSV stats written to ${PREFIX}_stats.csv"
