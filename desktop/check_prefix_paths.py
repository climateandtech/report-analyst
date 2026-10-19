"""Fail if pip left this machine's prefix path under the Python library tree.

Shebangs in bin/ and Scripts/ are expected to contain the prefix. The desktop
shell launches `python -m streamlit`, so those scripts are not on the import path.
"""

from __future__ import annotations

import sys
from pathlib import Path

TEXT_SUFFIXES = {".py", ".pth", ".txt", ".json", ".cfg", ".typed", ".ini"}


def library_roots(prefix: Path) -> list[Path]:
    """Return lib dirs whose contents must stay relocatable."""
    roots = []
    seen: set[tuple[int, int]] = set()
    for name in ("lib", "Lib"):
        candidate = prefix / name
        if not candidate.is_dir():
            continue
        stat = candidate.stat()
        key = (stat.st_dev, stat.st_ino)
        if key in seen:
            continue
        seen.add(key)
        roots.append(candidate)
    return roots


def offending_files(prefix: Path) -> list[Path]:
    """Return library files that embed the absolute prefix path."""
    needles = {str(prefix).encode(), str(prefix).replace("/", "\\").encode()}
    found: list[Path] = []
    for root in library_roots(prefix):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            if path.suffix not in TEXT_SUFFIXES:
                continue
            if path.stat().st_size > 2_000_000:
                continue
            data = path.read_bytes()
            if any(needle in data for needle in needles):
                found.append(path)
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_prefix_paths.py PREFIX", file=sys.stderr)
        return 2
    prefix = Path(argv[1]).resolve()
    found = offending_files(prefix)
    if found:
        print(f"absolute prefix path remains under {prefix}:", file=sys.stderr)
        for path in found[:50]:
            print(path, file=sys.stderr)
        return 1
    print(f"prefix library tree has no absolute path to {prefix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
