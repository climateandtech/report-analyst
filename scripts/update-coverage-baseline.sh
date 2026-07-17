#!/usr/bin/env bash
# Refresh scripts/coverage-baseline.json from the last quality-gate coverage JSON run.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python3"
[[ -x "$PY" ]] || PY="$(command -v python3)"
COV_JSON="${ROOT}/.qg-coverage/coverage.json"
BASELINE="${ROOT}/scripts/coverage-baseline.json"
PREFIX="${QG_COV_MONOREPO_PREFIX:-report-analyst/}"

if [[ ! -f "$COV_JSON" ]]; then
  echo "Missing $COV_JSON — run quality gate on changed report-analyst files first." >&2
  exit 1
fi

exec "$PY" "$ROOT/scripts/update_coverage_baseline.py" \
  --coverage-json "$COV_JSON" \
  --baseline "$BASELINE" \
  --monorepo-prefix "$PREFIX" \
  "$@"
