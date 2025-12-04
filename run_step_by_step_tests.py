#!/usr/bin/env python3
"""
Test runner for the step-by-step processing feature tests.

This script runs the comprehensive end-to-end tests for the Streamlit
step-by-step processing feature.

Usage:
    python run_step_by_step_tests.py [--verbose] [--specific-test TEST_NAME]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_tests(verbose=False, specific_test=None):
    """Run the step-by-step processing tests"""

    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Build the pytest command
    cmd = ["python", "-m", "pytest", "tests/test_streamlit_step_by_step.py"]

    if verbose:
        cmd.append("-v")
        cmd.append("-s")  # Don't capture output

    if specific_test:
        cmd.append(f"-k {specific_test}")

    # Add useful pytest options
    cmd.extend(
        [
            "--tb=short",  # Shorter traceback format
            "--disable-warnings",  # Disable warnings for cleaner output
            "--color=yes",  # Colored output
        ]
    )

    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Run step-by-step processing tests")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Run tests with verbose output"
    )
    parser.add_argument(
        "--specific-test", "-k", help="Run only tests matching this pattern"
    )
    parser.add_argument(
        "--list-tests", "-l", action="store_true", help="List all available tests"
    )

    args = parser.parse_args()

    if args.list_tests:
        print("Available tests:")
        print("- test_streamlit_app_initialization")
        print("- test_step_by_step_ui_elements")
        print("- test_step_dependency_logic")
        print("- test_file_upload_and_processing")
        print("- test_step_execution_flow")
        print("- test_results_display")
        print("- test_error_handling")
        print("- test_configuration_persistence")
        print("- test_async_processing_integration")
        print("- test_data_persistence_across_sessions")
        return 0

    # Check if required dependencies are installed
    try:
        import pytest
        import streamlit

        print(f"✓ Streamlit version: {streamlit.__version__}")
        print(f"✓ Pytest version: {pytest.__version__}")
    except ImportError as e:
        print(f"✗ Missing required dependency: {e}")
        print("Please install required dependencies with: pip install streamlit pytest")
        return 1

    # Set up environment for testing
    os.environ.setdefault("OPENAI_API_KEY", "test-key-12345")
    os.environ.setdefault("OPENAI_API_MODEL", "gpt-3.5-turbo")

    print("Starting step-by-step processing tests...")
    print("=" * 60)

    return run_tests(verbose=args.verbose, specific_test=args.specific_test)


if __name__ == "__main__":
    sys.exit(main())
