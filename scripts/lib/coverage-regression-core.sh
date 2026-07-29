#!/usr/bin/env bash
# Coverage regression: touched modules vs baseline + diff-cover on changed lines.
# Sourced by scripts/lib/coverage-regression.sh (set QG_COV_* before sourcing).
set -euo pipefail

qg_cov_regression_layout() {
  local repo_root="$1"
  if [[ -f "$repo_root/$QG_COV_STANDALONE_MARKER" ]]; then
    echo "standalone"
    return 0
  fi
  echo "monorepo"
}

qg_cov_regression_git_root() {
  local repo_root="$1"
  git -C "$repo_root" rev-parse --show-toplevel 2>/dev/null || echo "$repo_root"
}

qg_diff_cover_available() {
  local py="${1:-python3}"
  "$py" -c "import diff_cover" >/dev/null 2>&1
}

qg_cov_scripts_dir() {
  local repo_root="$1"
  if [[ -f "$repo_root/../scripts/check_coverage_regression.py" ]]; then
    echo "$(cd "$repo_root/.." && pwd)/scripts"
  else
    echo "$repo_root/scripts"
  fi
}

qg_run_coverage_regression() {
  local repo_root="$1"
  local py="$2"
  local base_ref="${BASE_REF:-}"
  local -a app_files=("${@:3}")
  local scripts_dir
  scripts_dir="$(qg_cov_scripts_dir "$repo_root")"

  if [[ ${#app_files[@]} -eq 0 ]]; then
    return 0
  fi

  local cov_dir="$repo_root/.qg-coverage"
  local cov_json="$cov_dir/coverage.json"
  local cov_xml="$cov_dir/coverage.xml"
  if [[ ! -f "$cov_json" ]]; then
    echo "quality-gate: coverage regression skipped (no $cov_json)" >&2
    return 0
  fi

  if ! qg_diff_cover_available "$py"; then
    echo "quality-gate: install diff-cover for changed-line checks (pip install diff-cover)" >&2
  fi

  local git_root layout baseline min_new max_drop diff_under
  git_root="$(qg_cov_regression_git_root "$repo_root")"
  layout="$(qg_cov_regression_layout "$repo_root")"
  baseline="$scripts_dir/coverage-baseline.json"
  min_new="${QG_COV_MIN_NEW:-80}"
  max_drop="${QG_COV_MAX_DROP:-0}"
  diff_under="${QG_DIFF_COVER_FAIL_UNDER:-90}"

  local -a cmd=(
    "$py" "$scripts_dir/check_coverage_regression.py"
    --coverage-json "$cov_json"
    --coverage-xml "$cov_xml"
    --baseline "$baseline"
    --repo-root "$repo_root"
    --git-root "$git_root"
    --layout "$layout"
    --monorepo-prefix "$QG_COV_MONOREPO_PREFIX"
    --min-new "$min_new"
    --max-drop "$max_drop"
    --diff-cover-fail-under "$diff_under"
  )
  if [[ -n "$base_ref" ]]; then
    cmd+=(--base-ref "$base_ref")
  fi
  local rel
  for rel in "${app_files[@]}"; do
    cmd+=(--app-file "$rel")
  done

  echo "quality-gate: coverage regression (modules + changed lines vs ${base_ref:-working tree})" >&2
  "${cmd[@]}"
}
