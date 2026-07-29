#!/usr/bin/env bash
# Resolve lint/test tools for quality-gate (hooks and minimal PATH environments).
# Self-contained copy (kept in sync with platform repo's scripts/lib/resolve-tools.sh).
set -euo pipefail

# Populated by qg_resolve_ruff: e.g. (ruff) or (python3 -m ruff) or (/path/to/python -m ruff)
QG_RUFF=()

qg_setup_path() {
  local root="${1:-.}"
  local repo_root="${2:-$(cd "$root/.." && pwd)}"

  local extra=(
    "$root/backend/venv/bin"
    "$root/venv/bin"
    "$root/.venv/bin"
    "$repo_root/.venv/bin"
    "$HOME/.local/bin"
    "/opt/homebrew/bin"
    "/usr/local/bin"
  )

  if [[ -d "${PYENV_ROOT:-$HOME/.pyenv}" ]]; then
    local pyenv_root="${PYENV_ROOT:-$HOME/.pyenv}"
    extra+=("$pyenv_root/bin" "$pyenv_root/shims")
    export PYENV_ROOT="$pyenv_root"
    if command -v pyenv >/dev/null 2>&1; then
      # shellcheck disable=SC2046
      eval "$(pyenv init - path 2>/dev/null)" || true
    fi
  fi

  if [[ -d "$HOME/.fnm/aliases/default/bin" ]]; then
    extra+=("$HOME/.fnm/aliases/default/bin")
  fi
  if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    source "$HOME/.nvm/nvm.sh" 2>/dev/null || true
  fi

  local dir venv_first=()
  for dir in "${extra[@]}"; do
    [[ -d "$dir" ]] && PATH="$dir:$PATH"
    if [[ "$dir" == */venv/bin || "$dir" == */.venv/bin ]]; then
      venv_first+=("$dir")
    fi
  done
  # Project venv must beat pyenv shims (hooks/CI use venv for pytest-cov, etc.).
  for dir in "${venv_first[@]}"; do
    PATH="$dir:$PATH"
  done
  export PATH
}

# Resolve python for pytest (prefer project venv).
qg_resolve_python() {
  QG_PYTHON=(python3)
  local root="${ROOT:-.}"
  local candidate
  for candidate in \
    "$root/backend/venv/bin/python3" \
    "$root/venv/bin/python3" \
    "$root/.venv/bin/python3" \
    "${REPO_ROOT:-}/.venv/bin/python3"; do
    if [[ -x "$candidate" ]]; then
      QG_PYTHON=("$candidate")
      return 0
    fi
  done
  command -v python3 >/dev/null 2>&1 || return 1
  QG_PYTHON=(python3)
  return 0
}

qg_run_python() {
  qg_resolve_python || return 1
  "${QG_PYTHON[@]}" "$@"
}

qg_has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

_qg_ruff_works() {
  "$@" --version >/dev/null 2>&1
}

# Resolve a working ruff invocation into QG_RUFF array. Returns 0 when found.
qg_resolve_ruff() {
  QG_RUFF=()
  local root="${ROOT:-.}"
  local repo_root="${REPO_ROOT:-$(cd "$root/.." && pwd)}"

  if qg_has_cmd ruff && _qg_ruff_works ruff; then
    QG_RUFF=(ruff)
    return 0
  fi

  local py
  for py in python3 python; do
    if qg_has_cmd "$py" && _qg_ruff_works "$py" -m ruff; then
      QG_RUFF=("$py" -m ruff)
      return 0
    fi
  done

  local candidate
  for candidate in \
    "$root/backend/venv/bin/ruff" \
    "$root/venv/bin/ruff" \
    "$root/.venv/bin/ruff" \
    "$repo_root/.venv/bin/ruff"; do
    if [[ -x "$candidate" ]] && _qg_ruff_works "$candidate"; then
      QG_RUFF=("$candidate")
      return 0
    fi
  done

  if qg_has_cmd pyenv; then
    local ver pybin
    while IFS= read -r ver; do
      [[ -z "$ver" ]] && continue
      pybin="${PYENV_ROOT:-$HOME/.pyenv}/versions/$ver/bin/python"
      if [[ -x "$pybin" ]] && _qg_ruff_works "$pybin" -m ruff; then
        QG_RUFF=("$pybin" -m ruff)
        return 0
      fi
    done < <(pyenv versions --bare 2>/dev/null || true)
  fi

  return 1
}

qg_run_ruff() {
  qg_resolve_ruff || return 1
  "${QG_RUFF[@]}" "$@"
}

qg_require_ruff() {
  if ! qg_resolve_ruff; then
    echo "quality-gate: ruff not available (pip install ruff or: pyenv shell 3.10.10)" >&2
    return 1
  fi
  return 0
}

qg_find_npm() {
  if qg_has_cmd npm; then
    command -v npm
    return 0
  fi
  return 1
}
