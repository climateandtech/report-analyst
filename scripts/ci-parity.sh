#!/usr/bin/env bash
# Local checks aligned with .github/workflows/ci.yml (test job) + Coolify docker build.
#
# Usage:
#   ./scripts/ci-parity.sh before-push     # fast: packaging tests + fresh pip resolve (Docker slim)
#   ./scripts/ci-parity.sh pytest          # full pytest suite (same as CI test job)
#   ./scripts/ci-parity.sh deps            # pip install -r requirements* in python:3.12-slim only
#   ./scripts/ci-parity.sh docker-build    # full image build (slow; closest to Coolify)
#
# QG: quality-gate.sh full runs `before-push` when requirements.txt or Dockerfile changed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

log() { echo "$@" >&2; }

_SLIM_IMAGE="${CI_PARITY_PYTHON_IMAGE:-python:3.12-slim}"

_run_deps_in_slim() {
  if ! command -v docker >/dev/null 2>&1; then
    log "ci-parity: docker not found — install Docker or run on CI"
    exit 2
  fi
  log "=== ci-parity: pip install (matches Dockerfile layers in ${_SLIM_IMAGE}) ==="
  docker run --rm -v "$ROOT:/src:ro" -w /src "${_SLIM_IMAGE}" bash -ec '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
      build-essential cmake libpoppler-cpp-dev libsqlite3-dev pkg-config curl >/dev/null
    pip install --no-cache-dir -r requirements.txt
    pip install --no-cache-dir -r report_analyst_enterprise/requirements.txt
    pip install --no-cache-dir -r report_analyst_api/requirements.txt
    pip install --no-cache-dir -r report_analyst_search_backend/requirements.txt
    pip install --no-cache-dir "nats-py>=2.7.0" "aiohttp>=3.9.0" "pandas>=2.0.0" "numpy>=1.24.0"
    echo "ci-parity: slim pip install OK"
  '
}

_run_packaging_tests() {
  log "=== ci-parity: Dockerfile / schema packaging tests ==="
  local py="${CI_PARITY_PYTHON:-python3}"
  if [[ -x "$ROOT/venv/bin/python" ]]; then
    py="$ROOT/venv/bin/python"
  fi
  PYTHONPATH=. "$py" -m pytest tests/test_dockerfile_packaging.py -q --tb=short
}

_run_pytest_ci() {
  log "=== ci-parity: full pytest (CI test job) ==="
  local py="${CI_PARITY_PYTHON:-python3}"
  if [[ -x "$ROOT/venv/bin/python" ]]; then
    py="$ROOT/venv/bin/python"
  fi
  PYTHONPATH=. "$py" -m pytest tests/ -v --tb=short
}

_run_docker_build() {
  if ! command -v docker >/dev/null 2>&1; then
    log "ci-parity: docker not found"
    exit 2
  fi
  log "=== ci-parity: docker build . ==="
  docker build -t report-analyst:ci-parity "$ROOT"
  log "=== ci-parity: schema inside image ==="
  docker run --rm report-analyst:ci-parity python -c "
from pathlib import Path
p = Path('/app/docs/contracts/questionset-document.v1.schema.json')
assert p.is_file(), p
from report_analyst.core.questionset_validation import load_v1_schema
load_v1_schema()
print('image schema OK')
"
}

CMD="${1:-before-push}"
case "$CMD" in
  before-push)
    _run_packaging_tests
    _run_deps_in_slim
    ;;
  deps) _run_deps_in_slim ;;
  pytest) _run_pytest_ci ;;
  docker-build) _run_docker_build ;;
  *)
    log "unknown command: $CMD (before-push | deps | pytest | docker-build)"
    exit 2
    ;;
esac

log "ci-parity: OK ($CMD)"