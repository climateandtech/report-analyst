"""
Tests for analyze and reanalyze question functionality in streamlit_app.py using AppTest.
"""

# import tempfile
# from pathlib import Path
from pathlib import Path
from unittest.mock import Mock

import pytest
from pypdf import PdfWriter
from streamlit.testing.v1 import AppTest

from report_analyst.streamlit_app import ReportAnalyzer, get_uploaded_files_history


@pytest.fixture
def test_pdf_in_app_temp():
    """Create a valid temporary PDF in the app's temp directory."""
    app_temp = Path("temp")
    app_temp.mkdir(exist_ok=True)

    pdf_path = app_temp / "test_report.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with pdf_path.open("wb") as file:
        writer.write(file)

    yield pdf_path

    # Remove only the file created by this test.
    pdf_path.unlink(missing_ok=True)


def test_process_document_with_all_keywords():
    "Test the process_document() function if the pre_retrieved_chunk keyword is unexpected"

    # Create ReportAnalyst instance to use the wrapper function
    report_analyzer = object.__new__(ReportAnalyzer)
    report_analyzer.analyzer = Mock()
    chunks = [{"text": "test chunk"}]

    # Calling function where pre_retrived_chunks is unexpected
    report_analyzer.process_document(
        file_path=" ",
        selected_questions=[],
        use_llm_scoring=False,
        single_call=True,
        force_recompute=False,
        pre_retrieved_chunk=chunks,
    )

    report_analyzer.analyzer.process_document.assert_called_once()


# with tempfile.TemporaryDirectory() as temp_dir:
#         test_pdf = Path(temp_dir) / "test.pdf"
#         test_pdf.write_bytes(
#             b"%PDF-1.4\n%Test PDF\n1 0 obj\n
#             << /Type /Catalog /Pages 2 0 R >>\nendobj\n
#             2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n
# << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n
# 0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
#         )

#         # Set temp directory in environment
#         import os

#         original_temp = os.environ.get("TEMP_DIR", None)
#         os.environ["TEMP_DIR"] = str(temp_dir)


def test_analyze_button_without_openai_call(mocked_report_analyzer, test_pdf_in_app_temp):
    report_analyzer, calls = mocked_report_analyzer

    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.session_state["nav_page"] = "Report Analyst"
    at.session_state["analyzer"] = report_analyzer

    at.run(timeout=10)

    assert not at.exception

    # Find the generated PDF in the app file list.
    files = get_uploaded_files_history()

    test_file = next(file for file in files if file["name"] == test_pdf_in_app_temp.name)

    # The selectbox stores the full file dictionary, not only its name.
    at.session_state["previous_file"] = test_file
    at.run(timeout=10)

    assert at.session_state["previous_file"]["name"] == test_pdf_in_app_temp.name

    at.button(key="select_all_tcfd").click().run(timeout=10)
    at.button(key="analyze_button").click().run(timeout=10)

    assert len(at.error) == 0, [e.value for e in at.error]
    assert not at.error
    assert not at.exception

    assert len(calls) == 1
    assert calls[0]["selected_questions"]
    assert calls[0]["force_recompute"] is False
    assert calls[0]["pre_retrieved_chunks"] is None
    assert Path(calls[0]["file_path"]).name == test_pdf_in_app_temp.name


def test_reanalyze_button_without_openai_call(mocked_report_analyzer, test_pdf_in_app_temp):
    report_analyzer, calls = mocked_report_analyzer

    at = AppTest.from_file("report_analyst/streamlit_app.py")
    at.session_state["nav_page"] = "Report Analyst"
    at.session_state["analyzer"] = report_analyzer

    at.run(timeout=10)

    assert not at.exception

    # Find the generated PDF in the app file list.
    files = get_uploaded_files_history()

    test_file = next(file for file in files if file["name"] == test_pdf_in_app_temp.name)

    # The selectbox stores the full file dictionary, not only its name.
    at.session_state["previous_file"] = test_file
    at.run(timeout=10)

    assert at.session_state["previous_file"]["name"] == test_pdf_in_app_temp.name

    at.button(key="select_all_tcfd").click().run(timeout=10)
    at.button(key="reanalyze_button").click().run(timeout=10)

    assert len(at.error) == 0, [e.value for e in at.error]
    assert not at.exception
    assert len(calls) == 1
    assert calls[0]["selected_questions"]
    assert calls[0]["force_recompute"] is True
    assert calls[0]["pre_retrieved_chunks"] is None
