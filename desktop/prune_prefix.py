"""Drop files the desktop runtime does not import.

The shell sets PYTHONDONTWRITEBYTECODE, so bytecode caches are unused.
Test suites, pip, Jupyter data, PyArrow headers, and the legacy PyMuPDF
module are not on the import path of the analyst app. setuptools stays,
because llama-index still imports pkg_resources when it downloads a module.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def site_packages_dirs(prefix: Path) -> list[Path]:
    """Return site-packages directories inside a standalone prefix."""
    found: list[Path] = []
    for lib_name in ("lib", "Lib"):
        lib = prefix / lib_name
        if not lib.is_dir():
            continue
        direct = lib / "site-packages"
        if direct.is_dir() and not direct.is_symlink():
            found.append(direct)
        found.extend(
            path
            for path in lib.glob("python*/site-packages")
            if path.is_dir() and not path.is_symlink()
        )
    return found


def _inside(prefix: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(prefix.resolve())
    except ValueError:
        return False
    return True


def _is_named_test_suite(path: Path) -> bool:
    """A directory named test is a suite only when it holds test modules."""
    if path.name != "test" or not path.is_dir() or path.is_symlink():
        return False
    if (path / "conftest.py").is_file():
        return True
    return any(path.glob("test_*.py"))


def _is_pip_metadata(name: str) -> bool:
    return name.startswith("pip-") and (
        name.endswith(".dist-info") or name.endswith(".egg-info")
    )


def _pycache_dirs(prefix: Path) -> list[Path]:
    """Bytecode caches anywhere in the prefix, not only in site-packages."""
    found: list[Path] = []
    for dirpath, dirnames, _files in os.walk(prefix, followlinks=False):
        current = Path(dirpath)
        kept: list[str] = []
        for name in dirnames:
            child = current / name
            if name == "__pycache__" and not child.is_symlink() and _inside(prefix, child):
                found.append(child)
                continue
            kept.append(name)
        dirnames[:] = kept
    return found


def _is_site_target(site: Path, current: Path, name: str) -> bool:
    child = current / name
    if name == "tests":
        return True
    if _is_named_test_suite(child):
        return True
    if child == site / "pip" or (current == site and _is_pip_metadata(name)):
        return True
    if child == site / "pyarrow" / "include":
        return True
    return child == site / "fitz_old" and (site / "fitz" / "__init__.py").is_file()


def _stdlib_targets(prefix: Path) -> list[Path]:
    targets: list[Path] = []
    jupyter = prefix / "share" / "jupyter"
    if jupyter.is_dir() and not jupyter.is_symlink():
        targets.append(jupyter)
    for lib_name in ("lib", "Lib"):
        lib = prefix / lib_name
        if not lib.is_dir():
            continue
        for candidate in [lib / "ensurepip", *lib.glob("python*/ensurepip")]:
            if candidate.is_dir() and not candidate.is_symlink():
                targets.append(candidate)
    return targets


def removal_targets(prefix: Path) -> list[Path]:
    """Return directories that can be removed without changing imports."""
    prefix = prefix.resolve()
    selected = [path for path in _stdlib_targets(prefix) if _inside(prefix, path)]
    selected.extend(_pycache_dirs(prefix))
    for site in site_packages_dirs(prefix):
        for dirpath, dirnames, _files in os.walk(site, followlinks=False):
            current = Path(dirpath)
            kept: list[str] = []
            for name in dirnames:
                child = current / name
                if child.is_symlink() or not _is_site_target(site, current, name):
                    kept.append(name)
                    continue
                if _inside(prefix, child):
                    selected.append(child)
            dirnames[:] = kept
    return selected


def _directory_size(path: Path) -> int:
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path, followlinks=False):
        for name in filenames:
            file_path = Path(dirpath) / name
            if file_path.is_symlink():
                continue
            try:
                total += file_path.stat().st_size
            except OSError:
                continue
    return total


def prune(prefix: Path) -> int:
    """Delete unused prefix directories. Returns bytes removed."""
    removed = 0
    for path in removal_targets(prefix):
        if not path.is_dir() or path.is_symlink():
            continue
        removed += _directory_size(path)
        shutil.rmtree(path)
    return removed


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: prune_prefix.py PREFIX", file=sys.stderr)
        return 2
    prefix = Path(argv[1]).resolve()
    if not prefix.is_dir():
        print(f"prefix does not exist: {prefix}", file=sys.stderr)
        return 1
    removed = prune(prefix)
    print(f"pruned {removed / 1024 / 1024:.0f}MB from {prefix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
