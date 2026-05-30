#!/usr/bin/env bash
# Lint changed Python under report-analyst with ruff.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
# shellcheck source=lib/resolve-tools.sh
source "$ROOT/scripts/lib/resolve-tools.sh"
qg_setup_path "$ROOT" "$REPO_ROOT"
cd "$ROOT"

git_root() {
  git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null \
    || git -C "$REPO_ROOT" rev-parse --show-toplevel 2>/dev/null || true
}

collect_changed() {
  local base_ref="${BASE_REF:-}"
  local git_root
  git_root="$(git_root)"
  if [[ -z "$git_root" ]]; then return; fi

  if [[ -n "$base_ref" ]] && git -C "$git_root" rev-parse --verify "$base_ref" >/dev/null 2>&1; then
    git -C "$git_root" diff --name-only "${base_ref}...HEAD" 2>/dev/null || true
  else
    {
      git -C "$git_root" diff --name-only HEAD 2>/dev/null || true
      git -C "$git_root" diff --cached --name-only 2>/dev/null || true
      git -C "$git_root" ls-files --others --exclude-standard 2>/dev/null || true
    }
  fi | sort -u
}

FILES=()
while IFS= read -r _line; do
  [[ -n "$_line" ]] && FILES+=("$_line")
done < <(
  if [[ $# -gt 0 ]]; then
    printf '%s\n' "$@"
  else
    collect_changed \
      | grep -E '^(report-analyst/)?(report_analyst|tests)/.*\.py$' \
      | sed -E 's|^report-analyst/||' \
      | sort -u
  fi
)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "lint-changed: no report-analyst Python files to check"
  exit 0
fi

if ! qg_require_ruff; then
  echo "lint-changed: ruff not available (pip install ruff)" >&2
  exit 2
fi

echo "lint-changed: ruff check ${#FILES[@]} file(s)"
qg_run_ruff check "${FILES[@]}"
