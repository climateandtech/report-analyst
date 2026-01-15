"""
Test that validates the full CI linting workflow.

This test runs the same linting checks that CI runs to catch issues early.
"""

import subprocess
import sys
from pathlib import Path


def test_black_formatting():
    """Test that all files are formatted with black"""
    # Black will use pyproject.toml exclusions automatically
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    # Filter out node_modules and venv2 errors as they should be excluded
    stderr = result.stderr
    stdout = result.stdout
    # Check if the only failures are in excluded directories
    if result.returncode != 0:
        # Check if errors are only in excluded paths
        excluded_paths = ["node_modules", "venv2", ".git", "report_analyst_enterprise"]
        error_lines = (stderr + stdout).split("\n")
        relevant_errors = [
            line
            for line in error_lines
            if "would reformat" in line.lower()
            and not any(excluded in line for excluded in excluded_paths)
        ]
        if relevant_errors:
            assert (
                False
            ), f"Black formatting check failed:\n{result.stdout}\n{result.stderr}"


def test_isort_imports():
    """Test that all imports are sorted with isort"""
    # isort will use pyproject.toml skip settings automatically
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check-only", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    # Filter out venv2 and node_modules errors as they should be excluded
    if result.returncode != 0:
        stderr = result.stderr
        # Check if errors are only in excluded paths
        excluded_paths = ["venv2", "node_modules", "report_analyst_enterprise", ".git", "__pycache__"]
        error_lines = stderr.split("\n")
        relevant_errors = [
            line
            for line in error_lines
            if "ERROR:" in line
            and not any(excluded in line for excluded in excluded_paths)
        ]
        if relevant_errors:
            assert (
                False
            ), f"isort import check failed:\n{result.stdout}\n{result.stderr}"


def test_streamlit_app_imports():
    """Test that streamlit_app.py can be imported without errors"""
    try:
        # This will catch import errors like missing modules
        import report_analyst.streamlit_app  # noqa: F401
    except ImportError as e:
        raise AssertionError(f"Failed to import streamlit_app: {e}")
