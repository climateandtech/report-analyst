#!/usr/bin/env bash
# Start processes based on REPORT_ANALYST_RUNTIME:
#   core       — Streamlit only (default, customer deployments)
#   enterprise — Streamlit + FastAPI + NATS worker (internal Climate+Tech)
set -euo pipefail

RUNTIME="${REPORT_ANALYST_RUNTIME:-core}"
pids=()

cleanup() {
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT TERM INT

if [ "$RUNTIME" = "enterprise" ]; then
  echo "Starting enterprise runtime (Streamlit + API + NATS worker)"
  python report_analyst_jobs/nats_integration.py worker &
  pids+=($!)
  uvicorn report_analyst_api.main:app --host 0.0.0.0 --port 8001 &
  pids+=($!)
else
  echo "Starting core runtime (Streamlit only)"
fi

exec streamlit run report_analyst/streamlit_app.py \
  --server.port=8080 \
  --server.address=0.0.0.0
