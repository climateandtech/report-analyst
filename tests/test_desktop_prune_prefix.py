"""The desktop prefix prune drops unused files and keeps runtime imports."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desktop"))

from prune_prefix import prune, removal_targets


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _prefix(tmp_path: Path) -> Path:
    prefix = tmp_path / "python"
    site = prefix / "lib" / "python3.12" / "site-packages"
    _write(site / "pandas" / "core" / "frame.py", "class DataFrame: pass\n")
    _write(site / "pandas" / "tests" / "test_frame.py", "def test_frame(): pass\n")
    _write(site / "pandas" / "__pycache__" / "core.pyc", "bytecode")
    _write(site / "nltk" / "test" / "test_tokenize.py", "def test_tokenize(): pass\n")
    _write(site / "mypkg" / "test" / "helper.py", "def helper(): pass\n")
    _write(site / "fitz" / "__init__.py", "print('fitz')\n")
    _write(site / "fitz_old" / "__init__.py", "print('old')\n")
    _write(site / "fitz_old" / "libmupdf.dylib", "binary")
    _write(site / "pip" / "__init__.py", "print('pip')\n")
    _write(site / "pip-1.0.dist-info" / "METADATA", "Name: pip\n")
    _write(site / "setuptools" / "__init__.py", "print('setuptools')\n")
    _write(site / "pyarrow" / "include" / "arrow.h", "header")
    _write(site / "pyarrow" / "libarrow.dylib", "binary")
    _write(prefix / "share" / "jupyter" / "nbextensions" / "a.js", "js")
    _write(prefix / "lib" / "python3.12" / "ensurepip" / "__init__.py", "print('ensure')\n")
    _write(prefix / "lib" / "python3.12" / "encodings" / "__pycache__" / "utf_8.pyc", "bytecode")
    return prefix


def test_prune_removes_bytecode_tests_and_unused_tools(tmp_path: Path):
    """Bytecode, suites, pip, Jupyter, headers, and legacy PyMuPDF go away."""
    prefix = _prefix(tmp_path)
    site = prefix / "lib" / "python3.12" / "site-packages"

    removed = prune(prefix)

    assert removed > 0
    assert not (site / "pandas" / "tests").exists()
    assert not (site / "pandas" / "__pycache__").exists()
    assert not (site / "nltk" / "test").exists()
    assert not (site / "pip").exists()
    assert not (site / "pip-1.0.dist-info").exists()
    assert not (site / "fitz_old").exists()
    assert not (site / "pyarrow" / "include").exists()
    assert not (prefix / "share" / "jupyter").exists()
    assert not (prefix / "lib" / "python3.12" / "ensurepip").exists()
    assert not (prefix / "lib" / "python3.12" / "encodings" / "__pycache__").exists()


def test_prune_keeps_runtime_modules(tmp_path: Path):
    """Packages the app imports, including setuptools, stay in the prefix."""
    prefix = _prefix(tmp_path)
    site = prefix / "lib" / "python3.12" / "site-packages"

    prune(prefix)

    assert (site / "pandas" / "core" / "frame.py").is_file()
    assert (site / "mypkg" / "test" / "helper.py").is_file()
    assert (site / "fitz" / "__init__.py").is_file()
    assert (site / "setuptools" / "__init__.py").is_file()
    assert (site / "pyarrow" / "libarrow.dylib").is_file()


def test_prune_keeps_fitz_old_when_current_fitz_is_absent(tmp_path: Path):
    """The legacy module is the PDF importer when the new fitz package is missing."""
    prefix = tmp_path / "python"
    site = prefix / "lib" / "python3.12" / "site-packages"
    _write(site / "fitz_old" / "__init__.py", "print('old')\n")

    prune(prefix)

    assert (site / "fitz_old" / "__init__.py").is_file()


def test_prune_does_not_follow_symlinks_outside_the_prefix(tmp_path: Path):
    """A bytecode cache that points outside the prefix is not a delete target."""
    prefix = _prefix(tmp_path)
    outside = tmp_path / "outside"
    _write(outside / "keep.txt", "keep")
    link = prefix / "lib" / "python3.12" / "site-packages" / "pandas" / "__pycache__"
    for child in link.iterdir():
        child.unlink()
    link.rmdir()
    link.symlink_to(outside)

    targets = removal_targets(prefix)
    prune(prefix)

    assert outside not in targets
    assert (outside / "keep.txt").is_file()
    assert link.is_symlink()
