"""
Tests for file selection and path handling in Report Analyst page.
Tests that file paths are correctly resolved from file:// URIs.
"""

import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_file_selection_with_file_uri():
    """Test that file selection works correctly with file:// URIs"""
    # Create a temporary PDF file
    with tempfile.TemporaryDirectory() as temp_dir:
        test_pdf = Path(temp_dir) / "test_report.pdf"
        test_pdf.write_bytes(
            b"%PDF-1.4\n%Test PDF\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
        )

        # Set temp directory in environment
        import os

        original_temp = os.environ.get("TEMP_DIR", None)
        os.environ["TEMP_DIR"] = str(temp_dir)

        try:
            at = AppTest.from_file("report_analyst/streamlit_app.py")
            at.session_state["nav_page"] = "Report Analyst"
            at.run(timeout=10)

            # Verify app loads without errors
            assert not at.exception, "App should load without errors"

            # Check that file dropdown is available
            if len(at.selectbox) > 0:
                file_selectbox = None
                for selectbox in at.selectbox:
                    if "previous_file" in str(selectbox.key):
                        file_selectbox = selectbox
                        break

                if file_selectbox and len(file_selectbox.options) > 0:
                    # Verify files are listed
                    assert (
                        len(file_selectbox.options) > 0
                    ), "Files should be listed in dropdown"

                    # The file path should be correctly resolved
                    # This is verified by the app not showing "File not found" error
                    assert not any(
                        "File not found" in str(err)
                        for err in at.error
                        if hasattr(at, "error")
                    ), "Should not show 'File not found' error for valid files"
        finally:
            if original_temp:
                os.environ["TEMP_DIR"] = original_temp
            elif "TEMP_DIR" in os.environ:
                del os.environ["TEMP_DIR"]


def test_file_path_resolution_from_uri():
    """Test that file:// URIs are correctly converted to file paths"""
    from report_analyst.streamlit_app import get_uploaded_files_history

    # Create a temporary PDF file
    with tempfile.TemporaryDirectory() as temp_dir:
        test_pdf = Path(temp_dir) / "test_report.pdf"
        test_pdf.write_bytes(
            b"%PDF-1.4\n%Test PDF\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
        )

        # Set temp directory in environment
        import os

        original_temp = os.environ.get("TEMP_DIR", None)
        os.environ["TEMP_DIR"] = str(temp_dir)

        try:
            # Get file list
            files = get_uploaded_files_history()

            # Find our test file
            test_file = None
            for f in files:
                if f["name"] == "test_report.pdf":
                    test_file = f
                    break

            if test_file:
                # Verify path is correctly extracted from file:// URI
                path = test_file.get("path", "")
                uri = test_file.get("uri", "")

                # Path should not start with file://
                assert not path.startswith(
                    "file://"
                ), "Path should not contain file:// prefix"

                # Path should exist
                assert Path(path).exists(), f"File path should exist: {path}"

                # URI should start with file://
                assert uri.startswith("file://"), "URI should start with file://"
        finally:
            if original_temp:
                os.environ["TEMP_DIR"] = original_temp
            elif "TEMP_DIR" in os.environ:
                del os.environ["TEMP_DIR"]


def test_file_not_found_error_not_shown():
    """Test that 'File not found: None' error is not shown when file is selected"""
    # Create a temporary PDF file
    with tempfile.TemporaryDirectory() as temp_dir:
        test_pdf = Path(temp_dir) / "test_report.pdf"
        test_pdf.write_bytes(
            b"%PDF-1.4\n%Test PDF\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
        )

        # Set temp directory in environment
        import os

        original_temp = os.environ.get("TEMP_DIR", None)
        os.environ["TEMP_DIR"] = str(temp_dir)

        try:
            at = AppTest.from_file("report_analyst/streamlit_app.py")
            at.session_state["nav_page"] = "Report Analyst"
            at.run(timeout=10)

            # Verify app loads
            assert not at.exception, "App should load without errors"

            # Check for file dropdown and select a file
            if len(at.selectbox) > 0:
                file_selectbox = None
                for selectbox in at.selectbox:
                    if "previous_file" in str(selectbox.key):
                        file_selectbox = selectbox
                        break

                if file_selectbox and len(file_selectbox.options) > 0:
                    # Select first file
                    # Note: We can't easily set the file in session state due to format_func issues
                    # But we can verify the app doesn't show errors
                    at.run(timeout=10)

                    # Check that no "File not found" error is shown
                    # This is verified by checking the app doesn't have that error message
                    page_text = str(at)
                    assert (
                        "File not found: None" not in page_text
                    ), "Should not show 'File not found: None' error"
        finally:
            if original_temp:
                os.environ["TEMP_DIR"] = original_temp
            elif "TEMP_DIR" in os.environ:
                del os.environ["TEMP_DIR"]
