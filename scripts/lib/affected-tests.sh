#!/usr/bin/env bash
# Map changed backend paths to pytest targets and run with coverage on affected app modules.
# Self-contained copy (kept in sync with platform repo's scripts/lib/affected-tests.sh).
set -euo pipefail

_lib="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/coverage-regression.sh
source "$_lib/coverage-regression.sh"

qg_summary_start() {
  echo "=== AGENT_TEST_SUMMARY_START ==="
  echo "SCOPE: Fix ONLY failures caused by paths YOU changed in this chat."
  echo "       Do NOT fix ruff/tests for other agent sessions or unrelated dirty files."
}
qg_summary_end() { echo "=== AGENT_TEST_SUMMARY_END ==="; }

# Normalize monorepo or standalone path to backend-relative (app/... or tests/...).
qg_backend_rel() {
  local p="$1"
  local app_prefix="${2:-app}"
  p="${p#ct-platform/backend/}"
  p="${p#backend/}"
  p="${p#report-analyst/}"
  echo "$p"
}

_qg_unique_append() {
  local item="$1"
  local list_name="$2"
  local existing
  eval "existing=(\"\${${list_name}[@]:-}\")"
  for existing in "${existing[@]}"; do
    [[ "$existing" == "$item" ]] && return 0
  done
  eval "${list_name}+=(\"\$item\")"
}

_qg_unique_append_test() {
  local backend_root="$1"
  local test_rel="$2"
  local direct="${3:-0}"
  [[ -z "$test_rel" || ! -f "$backend_root/$test_rel" ]] && return 0
  if [[ "$direct" -eq 0 ]] && ! _qg_test_eligible_for_gate "$test_rel"; then
    return 0
  fi
  _qg_unique_append "$test_rel" QG_AFFECTED_TESTS
}

# Gate runs unit tests only (-m "not functional/integration/e2e"). Do not list tests that
# need those markers — pytest still imports them at collection time.
_qg_test_eligible_for_gate() {
  local test_rel="$1"
  [[ "$test_rel" =~ _functional\.py$ ]] && return 1
  [[ "$test_rel" =~ _integration\.py$ ]] && return 1
  [[ "$test_rel" =~ ^tests/e2e/ ]] && return 1
  return 0
}

_qg_search_tests_importing() {
  local backend_root="$1"
  local pattern="$2"
  if command -v rg >/dev/null 2>&1; then
    rg -l --glob 'tests/**/*.py' -e "$pattern" "$backend_root/tests" 2>/dev/null || true
  else
    grep -rl --include='test_*.py' "$pattern" "$backend_root/tests" 2>/dev/null || true
  fi
}

# Discover pytest files and --cov modules for changed backend paths.
# Sets: QG_AFFECTED_TESTS[], QG_AFFECTED_COV[], QG_AFFECTED_APP_FILES[]
qg_discover_affected_tests() {
  local backend_root="$1"
  local app_prefix="${2:-app}"
  shift 2
  local -a changed=("$@")

  QG_AFFECTED_TESTS=()
  QG_AFFECTED_COV=()
  QG_AFFECTED_APP_FILES=()

  local p rel dot_mod mod_suffix test_guess hit
  for p in "${changed[@]}"; do
    rel="$(qg_backend_rel "$p" "$app_prefix")"

    if [[ "$rel" =~ ^tests/test_.*\.py$ ]]; then
      _qg_unique_append_test "$backend_root" "$rel" 1
      continue
    fi

    if [[ ! "$rel" =~ ^${app_prefix}/.+\.py$ ]]; then
      continue
    fi
    if [[ "$rel" =~ ^${app_prefix}/alembic/ ]]; then
      continue
    fi
    _qg_unique_append "$rel" QG_AFFECTED_APP_FILES

    dot_mod="${rel%.py}"
    dot_mod="${dot_mod//\//.}"
    _qg_unique_append "--cov=${dot_mod}" QG_AFFECTED_COV

    mod_suffix="${rel#${app_prefix}/}"
    mod_suffix="${mod_suffix%.py}"
    test_guess="tests/test_${mod_suffix//\//_}.py"
    if [[ -f "$backend_root/$test_guess" ]]; then
      _qg_unique_append_test "$backend_root" "$test_guess"
    fi
    test_guess="tests/test_$(basename "$rel" .py).py"
    if [[ -f "$backend_root/$test_guess" ]]; then
      _qg_unique_append_test "$backend_root" "$test_guess"
    fi

    if ! _qg_skip_import_grep "$mod_suffix"; then
      while IFS= read -r hit; do
        [[ -z "$hit" ]] && continue
        hit="${hit#"$backend_root"/}"
        _qg_unique_append_test "$backend_root" "$hit"
      done < <(
        _qg_search_tests_importing "$backend_root" "from ${dot_mod} import"
        _qg_search_tests_importing "$backend_root" "from ${dot_mod} "
        _qg_search_tests_importing "$backend_root" "import ${dot_mod}"
      )
    fi
  done
}

_qg_python() {
  local backend_root="${1:-}"
  if [[ -n "$backend_root" && -x "$backend_root/venv/bin/python3" ]]; then
    echo "$backend_root/venv/bin/python3"
    return 0
  fi
  if declare -F qg_resolve_python >/dev/null 2>&1; then
    qg_resolve_python || return 1
    printf '%s\n' "${QG_PYTHON[@]}"
    return 0
  fi
  command -v python3
}

# Package hubs — import grep matches most of tests/; use naming convention only.
_qg_skip_import_grep() {
  local mod_suffix="$1"
  case "$mod_suffix" in
    main|models|crud|auth|auth_routes|database|config|dependencies|schemas|schemas.__init__) return 0 ;;
  esac
  [[ "$mod_suffix" != */* ]]
}

qg_pytest_cov_available() {
  local py="${1:-}"
  [[ -z "$py" ]] && py="$(_qg_python)"
  "$py" - <<'PY' >/dev/null 2>&1
import pytest_cov  # noqa: F401
PY
}

# Run affected unit tests; print delimited summary for agent hooks. Returns pytest exit code.
qg_run_affected_pytest() {
  local backend_root="$1"
  local app_prefix="${2:-app}"
  shift 2
  local -a changed=("$@")
  local markers="${QG_PYTEST_MARKERS:-not e2e and not integration and not functional}"

  # qg_resolve_python uses ROOT: ct-platform for backend/, or project root for report-analyst/.
  if [[ "$backend_root" == */backend ]]; then
    export ROOT="$(cd "$(dirname "$backend_root")" && pwd)"
  else
    export ROOT="$backend_root"
  fi

  if [[ ${#changed[@]} -eq 0 ]]; then
    return 0
  fi

  qg_discover_affected_tests "$backend_root" "$app_prefix" "${changed[@]}"

  if [[ ${#QG_AFFECTED_TESTS[@]} -eq 0 ]]; then
    if [[ ${#QG_AFFECTED_APP_FILES[@]} -gt 0 ]]; then
      echo "quality-gate: no pytest files mapped to changed app modules:" >&2
      printf '  %s\n' "${QG_AFFECTED_APP_FILES[@]}" >&2
      qg_summary_start
      echo "FAIL: no affected tests found for changed app files"
      printf '%s\n' "${QG_AFFECTED_APP_FILES[@]}"
      qg_summary_end
      return 1
    fi
    return 0
  fi

  local py
  py="$(_qg_python "$backend_root")"
  if [[ -z "$py" || ! -x "$py" ]]; then
    echo "quality-gate: python3 not found" >&2
    return 2
  fi
  echo "quality-gate: python: $py" >&2
  if ! "$py" -c "import pytest" >/dev/null 2>&1; then
    echo "quality-gate: pytest not installed (cd backend && python -m venv venv && ./venv/bin/pip install -r tests/requirements-test.txt -r requirements-dev-bootstrap.txt)" >&2
    return 2
  fi
  if [[ "$app_prefix" == app ]]; then
    if ! "$py" -c "import passlib" >/dev/null 2>&1; then
      echo "quality-gate: passlib missing — run: $py -m pip install -r requirements-dev-bootstrap.txt" >&2
      return 2
    fi
    if ! "$py" -c "import openai" >/dev/null 2>&1; then
      echo "quality-gate: openai missing — run: $py -m pip install -r requirements-dev-bootstrap.txt" >&2
      return 2
    fi
  fi

  local -a cov_args=()
  local cov_dir="$backend_root/.qg-coverage"
  if qg_pytest_cov_available "$py" && [[ ${#QG_AFFECTED_COV[@]} -gt 0 ]]; then
    mkdir -p "$cov_dir"
    cov_args=(
      --cov-report=term-missing:skip-covered
      --cov-report=xml:"$cov_dir/coverage.xml"
      --cov-report=json:"$cov_dir/coverage.json"
    )
    cov_args+=("${QG_AFFECTED_COV[@]}")
  elif [[ ${#QG_AFFECTED_COV[@]} -gt 0 ]]; then
    echo "quality-gate: pytest-cov not installed — running tests without coverage (pip install pytest-cov)" >&2
  fi

  echo "quality-gate: affected tests: ${QG_AFFECTED_TESTS[*]}" >&2
  [[ ${#QG_AFFECTED_COV[@]} -gt 0 ]] && echo "quality-gate: coverage modules: ${QG_AFFECTED_COV[*]#--cov=}" >&2

  local out rc
  out="$(mktemp)"
  set +e
  (
    cd "$backend_root"
    if [[ ${#cov_args[@]} -gt 0 ]]; then
      "$py" -m pytest \
        -m "$markers" \
        --tb=short \
        -ra \
        "${cov_args[@]}" \
        "${QG_AFFECTED_TESTS[@]}"
    else
      "$py" -m pytest \
        -m "$markers" \
        --tb=short \
        -ra \
        "${QG_AFFECTED_TESTS[@]}"
    fi
  ) 2>&1 | tee "$out"
  rc="${PIPESTATUS[0]}"
  set -e

  local regress_out=""
  local cov_rc=0
  if [[ "$rc" -eq 0 && ${#QG_AFFECTED_APP_FILES[@]} -gt 0 && ${#cov_args[@]} -gt 0 ]]; then
    regress_out="$(mktemp)"
    set +e
    qg_run_coverage_regression "$backend_root" "$py" "${QG_AFFECTED_APP_FILES[@]}" >"$regress_out" 2>&1
    cov_rc=$?
    set -e
    if [[ "$cov_rc" -ne 0 ]]; then
      rc="$cov_rc"
    fi
  fi

  qg_summary_start
  echo "pytest exit code: $rc"
  echo "tests: ${QG_AFFECTED_TESTS[*]}"
  [[ ${#QG_AFFECTED_COV[@]} -gt 0 ]] && echo "coverage: ${QG_AFFECTED_COV[*]#--cov=}"
  cat "$out"
  if [[ -n "$regress_out" && -f "$regress_out" ]]; then
    echo ""
    cat "$regress_out"
  fi
  qg_summary_end
  rm -f "$out"
  [[ -n "$regress_out" ]] && rm -f "$regress_out"
  return "$rc"
}
