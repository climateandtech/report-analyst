import base64
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

from report_analyst.streamlit_app import display_pdf_viewer
from report_analyst_enterprise.components.streamlit_component.backend.pdf_viewer import (
    _pdf_source,
    pdf_viewer,
)


def test_streamlit_bridge_does_not_forward_chunk_clicks():
    component_html = (
        Path(__file__).resolve().parents[1]
        / "report_analyst_enterprise/components/streamlit_component/frontend/public/index.html"
    ).read_text()

    assert "streamlit:setComponentValue" not in component_html


def test_pdf_source_encodes_a_local_pdf(tmp_path):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"%PDF-test")

    pdf_data, source_error = _pdf_source(str(pdf_path))

    assert source_error is None
    assert pdf_data == "data:application/pdf;base64," + base64.b64encode(b"%PDF-test").decode("ascii")


def test_pdf_source_returns_a_clear_error_for_a_missing_file(tmp_path):
    pdf_data, source_error = _pdf_source(str(tmp_path / "missing.pdf"))

    assert pdf_data is None
    assert source_error.startswith("PDF file not found:")


def test_pdf_viewer_passes_chunks_and_questions(tmp_path):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"%PDF-test")
    component = Mock()

    with patch(
        "report_analyst_enterprise.components.streamlit_component.backend.pdf_viewer._COMPONENT",
        component,
    ):
        pdf_viewer(
            pdf_path=str(pdf_path),
            chunks_data={
                "q1": [{"text": "Evidence", "is_evidence": True, "chunk_order": 0}],
                "q2": [{"text": "Retrieved", "is_evidence": False, "chunk_order": 1}],
            },
            questions_data={"q1": "First question", "q2": "Second question"},
            unmapped_chunks=[
                {
                    "chunk_text": "Unmapped",
                    "chunk_metadata": {"page_number": 3},
                    "embedding": object(),
                }
            ],
            key="viewer",
        )

    kwargs = component.call_args.kwargs
    chunks = kwargs["chunks"]
    questions = kwargs["questions"]
    assert [chunk["question_id"] for chunk in chunks] == ["q1", "q2", None]
    assert [chunk["text"] for chunk in chunks] == ["Evidence", "Retrieved", "Unmapped"]
    assert chunks[2] == {
        "text": "Unmapped",
        "metadata": {"page_number": 3},
        "question_id": None,
    }
    assert questions == [
        {"question_id": "q1", "text": "First question"},
        {"question_id": "q2", "text": "Second question"},
    ]
    assert kwargs["sourceError"] is None


def test_pdf_viewer_passes_source_error_to_the_component(tmp_path):
    component = Mock()

    with patch(
        "report_analyst_enterprise.components.streamlit_component.backend.pdf_viewer._COMPONENT",
        component,
    ):
        pdf_viewer(
            pdf_path=str(tmp_path / "missing.pdf"),
            chunks_data={},
            questions_data={},
        )

    assert component.call_args.kwargs["sourceError"].startswith("PDF file not found:")


def test_display_pdf_viewer_opens_for_unmapped_chunks():
    component = Mock()

    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()),
        patch("report_analyst.streamlit_app.pdf_viewer", component),
    ):
        display_pdf_viewer(
            file_path="report.pdf",
            results={},
            questions={
                "q1": {"text": "First question"},
                "q2": {"text": "Second question"},
            },
            raw_chunks=[{"text": "Unmapped chunk", "metadata": {"page_number": 1}}],
        )

    assert component.call_args.kwargs["chunks_data"] == {}
    assert component.call_args.kwargs["unmapped_chunks"][0]["text"] == "Unmapped chunk"
    assert component.call_args.kwargs["questions_data"] == {
        "q1": "First question",
        "q2": "Second question",
    }


def test_display_pdf_viewer_opens_without_analysis():
    component = Mock()

    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()) as expander,
        patch("report_analyst.streamlit_app.pdf_viewer", component),
    ):
        display_pdf_viewer(
            file_path="report.pdf",
            results={},
            questions={"q1": {"text": "First question"}},
            raw_chunks=[],
        )

    expander.assert_called_once_with("PDF Viewer with Chunks", expanded=True)
    component.assert_called_once()
    assert component.call_args.kwargs["chunks_data"] == {}
    assert component.call_args.kwargs["unmapped_chunks"] == []


def test_display_pdf_viewer_survives_component_errors():
    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()),
        patch("report_analyst.streamlit_app.pdf_viewer", side_effect=RuntimeError("boom")),
        patch("report_analyst.streamlit_app.st.error") as error,
    ):
        display_pdf_viewer(
            file_path="report.pdf",
            results=None,
            questions=None,
            raw_chunks=None,
        )

    error.assert_called_once()
    assert "Error rendering PDF viewer" in error.call_args.args[0]
