#!/usr/bin/env bash
# Repo-level quality gate for report-analyst (primary enforcement for all editors).
set -euo pipefail

QG_STRICT="${QG_STRICT:-1}"

MODE="${1:-full}"
shift || true

BASE_REF="${BASE_REF:-}"
SKIP_PYTEST=0
PATHS_FILE=""
SINGLE_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE_REF="$2"; shift 2 ;;
    --paths-file) PATHS_FILE="$2"; shift 2 ;;
    --skip-pytest) SKIP_PYTEST=1; shift ;;
    quick|full) MODE="$1"; shift ;;
    *)
      SINGLE_FILE="$1"
      shift
      ;;
  esac
done

if [[ -z "$BASE_REF" ]]; then
  BASE_REF="${GITHUB_BASE_REF:+origin/$GITHUB_BASE_REF}"
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
# shellcheck source=lib/git-changed.sh
source "$ROOT/scripts/lib/git-changed.sh"
# shellcheck source=lib/resolve-tools.sh
source "$ROOT/scripts/lib/resolve-tools.sh"
# shellcheck source=lib/affected-tests.sh
source "$ROOT/scripts/lib/affected-tests.sh"
qg_setup_path "$ROOT" "$REPO_ROOT"

FAILED=0
log() { echo "$@" >&2; }

require_cmd() {
  local cmd="$1"
  local hint="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    return 0
  fi
  log "quality-gate: required command not found: $cmd ($hint)"
  exit 2
}

CHANGED=()
if [[ -n "$PATHS_FILE" ]]; then
  while IFS= read -r _line; do
    [[ -n "$_line" ]] && CHANGED+=("$_line")
  done < <(qg_collect_paths_file "$PATHS_FILE" | grep -E '^report-analyst/' || true)
elif [[ -n "$SINGLE_FILE" ]]; then
  while IFS= read -r _line; do
    [[ -n "$_line" ]] && CHANGED+=("$_line")
  done < <(qg_collect_changed "$BASE_REF" "$SINGLE_FILE" | grep -E '^report-analyst/' || true)
else
  while IFS= read -r _line; do
    [[ -n "$_line" ]] && CHANGED+=("$_line")
  done < <(qg_collect_changed "$BASE_REF" "" | grep -E '^report-analyst/' || true)
fi

if [[ ${#CHANGED[@]} -eq 0 ]]; then
  if [[ "$MODE" == quick ]]; then
    log "quality-gate: no report-analyst changes"
    exit 0
  fi
  log "quality-gate: OK ($MODE, no report-analyst changes)"
  exit 0
fi

if [[ -n "$PATHS_FILE" ]]; then
  log "quality-gate: session-scoped — fix ONLY failures for paths you touched in this chat:"
  for p in "${CHANGED[@]}"; do
    log "  $p"
  done
fi

py_files=()
for p in "${CHANGED[@]}"; do
  if [[ "$p" =~ ^report-analyst/report_analyst/.*\.py$ || "$p" =~ ^report-analyst/tests/.*\.py$ ]]; then
    py_files+=("${p#report-analyst/}")
  fi
done

if [[ ${#py_files[@]} -gt 0 ]]; then
  log "=== report-analyst: ruff (changed files) ==="
  if ! qg_require_ruff; then
    exit 2
  fi
  BASE_REF="$BASE_REF" "$ROOT/scripts/lint-changed.sh" "${py_files[@]}" || FAILED=1
fi

if [[ "$FAILED" -ne 0 ]]; then
  log "=== pytest skipped: fix ruff/lint on touched files first ==="
elif [[ "$SKIP_PYTEST" -eq 0 && ${#CHANGED[@]} -gt 0 ]]; then
  ra_py_changes=()
  for p in "${CHANGED[@]}"; do
    if [[ "$p" =~ ^report-analyst/(report_analyst|tests)/.*\.py$ ]]; then
      ra_py_changes+=("$p")
    fi
  done
  if [[ ${#ra_py_changes[@]} -gt 0 ]]; then
    log "=== report-analyst: pytest (affected tests + coverage) ==="
    require_cmd python3 "python3 required"
    qg_run_affected_pytest "$ROOT" report_analyst "${ra_py_changes[@]}" || FAILED=1
  fi
fi

if [[ "$FAILED" -ne 0 ]]; then
  if [[ -n "$PATHS_FILE" ]]; then
    log "quality-gate: FAILED — fix ONLY your session paths above; ignore other agent sessions"
  else
    log "quality-gate: FAILED"
  fi
  exit 1
fi
log "quality-gate: OK ($MODE)"
exit 0
