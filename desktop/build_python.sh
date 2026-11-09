#!/usr/bin/env bash
# Download python-build-standalone and pip-install the desktop requirements into that prefix.
# No virtualenv: a venv's pyvenv.cfg stores an absolute path and breaks after the prefix is moved.
set -euo pipefail

DESKTOP_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DESKTOP_DIR/.." && pwd)"
PREFIX="$DESKTOP_DIR/python"
RELEASE="20261013"
PY_VERSION="3.12.15"

uname_s="$(uname -s)"
uname_m="$(uname -m)"
case "$uname_s" in
  Darwin)
    case "$uname_m" in
      arm64) triple="aarch64-apple-darwin" ;;
      x86_64) triple="x86_64-apple-darwin" ;;
      *) echo "Unsupported macOS arch: $uname_m" >&2; exit 1 ;;
    esac
    ;;
  MINGW*|MSYS*|CYGWIN*)
    case "$uname_m" in
      x86_64|amd64|AMD64) triple="x86_64-pc-windows-msvc" ;;
      *) echo "Unsupported Windows arch: $uname_m" >&2; exit 1 ;;
    esac
    ;;
  Linux)
    echo "Linux builds are outside this proof of concept." >&2
    exit 1
    ;;
  *)
    echo "Unsupported OS: $uname_s" >&2
    exit 1
    ;;
esac

asset="cpython-${PY_VERSION}%2B${RELEASE}-${triple}-install_only.tar.gz"
url="https://github.com/astral-sh/python-build-standalone/releases/download/${RELEASE}/${asset}"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "Downloading $url"
curl -fL --retry 3 -o "$work/python.tar.gz" "$url"
rm -rf "$PREFIX"
mkdir -p "$DESKTOP_DIR"
tar -xzf "$work/python.tar.gz" -C "$work"

if [[ -d "$work/python" ]]; then
  mv "$work/python" "$PREFIX"
elif [[ -x "$work/bin/python3" || -x "$work/python.exe" ]]; then
  mkdir -p "$PREFIX"
  shopt -s dotglob
  mv "$work"/* "$PREFIX/"
else
  echo "Standalone archive did not contain a python prefix." >&2
  exit 1
fi

if [[ -x "$PREFIX/bin/python3" ]]; then
  PY="$PREFIX/bin/python3"
elif [[ -x "$PREFIX/python.exe" ]]; then
  PY="$PREFIX/python.exe"
else
  echo "No interpreter in $PREFIX" >&2
  exit 1
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$REPO_ROOT/requirements-desktop.txt"
PYTHONDONTWRITEBYTECODE=1 "$PY" "$DESKTOP_DIR/prune_prefix.py" "$PREFIX"
"$PY" "$DESKTOP_DIR/check_prefix_paths.py" "$PREFIX"
echo "Desktop Python prefix ready at $PREFIX"
