"""
Test that validates the full CI linting workflow.

This test runs the same linting checks that CI runs to catch issues early.
"""

import subprocess
import sys
from pathlib import Path


def test_black_formatting():
    """Test that all files are formatted with black"""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"Black formatting check failed:\n{result.stdout}\n{result.stderr}"


def test_isort_imports():
    """Test that all imports are sorted with isort"""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check-only", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"isort import check failed:\n{result.stdout}\n{result.stderr}"


def test_streamlit_app_imports():
    """Test that streamlit_app.py can be imported without errors"""
    try:
        # This will catch import errors like missing modules
        import report_analyst.streamlit_app  # noqa: F401
    except ImportError as e:
        raise AssertionError(f"Failed to import streamlit_app: {e}")
