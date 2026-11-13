import base64
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import OperationalError

from report_analyst.core.analyzer import compute_file_hash
from report_analyst.core.cache_manager import CacheManager
from report_analyst.core.esrs_taxonomy import TaxonomyUnavailableError
from report_analyst.models.source_tag import SourceTag
from report_analyst.models.taxonomy import Taxonomy, TaxonomyConcept
from report_analyst.streamlit_app import _get_pdf_viewer_results, display_pdf_viewer
from report_analyst_enterprise.components.streamlit_component.backend.pdf_viewer import (
    _pdf_source,
    pdf_viewer,
)


def test_streamlit_bridge_forwards_source_annotation_changes():
    component_html = (
        Path(__file__).resolve().parents[1]
        / "report_analyst_enterprise/components/streamlit_component/frontend/public/index.html"
    ).read_text()

    assert 'viewer.addEventListener("source-annotation-change"' in component_html
    assert 'sendMessage("streamlit:setComponentValue"' in component_html


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
        result = pdf_viewer(
            pdf_path=str(pdf_path),
            chunks_data={
                "q1": [{"text": "Evidence", "is_evidence": True, "chunk_order": 0}],
                "q2": [{"text": "Retrieved", "is_evidence": False, "chunk_order": 1}],
            },
            questions_data={"q1": "First question", "q2": "Second question"},
            document_id="document-hash",
            unmapped_chunks=[
                {
                    "chunk_text": "Unmapped",
                    "chunk_metadata": {"page_number": 3},
                    "embedding": object(),
                }
            ],
            annotations=[{"id": "source-1"}],
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
    assert kwargs["documentId"] == "document-hash"
    assert kwargs["annotations"] == [{"id": "source-1"}]
    assert result is component.return_value


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
            document_id=None,
        )

    assert component.call_args.kwargs["sourceError"].startswith("PDF file not found:")


def test_display_pdf_viewer_opens_for_unmapped_chunks():
    component = Mock(return_value=None)

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
            cache_manager=Mock(),
        )

    assert component.call_args.kwargs["chunks_data"] == {}
    assert component.call_args.kwargs["unmapped_chunks"][0]["text"] == "Unmapped chunk"
    assert component.call_args.kwargs["questions_data"] == {
        "q1": "First question",
        "q2": "Second question",
    }


def test_display_pdf_viewer_opens_without_analysis():
    component = Mock(return_value=None)

    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()) as expander,
        patch("report_analyst.streamlit_app.pdf_viewer", component),
        patch("report_analyst.streamlit_app.display_concept_search"),
    ):
        display_pdf_viewer(
            file_path="report.pdf",
            results={},
            questions={"q1": {"text": "First question"}},
            raw_chunks=[],
            cache_manager=Mock(),
        )

    expander.assert_called_once_with("PDF Viewer with Chunks", expanded=True)
    component.assert_called_once()
    assert component.call_args.kwargs["chunks_data"] == {}
    assert component.call_args.kwargs["unmapped_chunks"] == []


def test_display_pdf_viewer_shows_the_concept_search_with_the_saved_sources(pdf_path):
    cache_manager = storage()
    cache_manager.get_source_annotations.return_value = [{"id": "source-1"}]

    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()),
        patch("report_analyst.streamlit_app.pdf_viewer", Mock(return_value=None)),
        patch("report_analyst.streamlit_app.display_concept_search") as concept_search,
    ):
        display_pdf_viewer(file_path=str(pdf_path), results={}, questions={}, cache_manager=cache_manager)

    concept_search.assert_called_once_with([{"id": "source-1", "tags": []}], cache_manager)


def storage():
    """Storage with no saved sources or tags."""
    return Mock(get_source_annotations=Mock(return_value=[]), get_source_tags=Mock(return_value=[]))


@pytest.fixture
def pdf_path(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"%PDF-source")
    return path


def _source_event(document_id, action="create", **annotation):
    return {
        "action": action,
        "annotation": {
            "id": "source-1",
            "document_id": document_id,
            "page": 1,
            "span_start": 0,
            "span_end": 8,
            "selected_text": "Evidence",
            "rects": [{"x": 1, "y": 2, "width": 3, "height": 4}],
            **annotation,
        },
    }


def _render_viewer_twice(pdf_path, event, cache_manager):
    """Render, then rerun: the component keeps returning its last value."""
    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()),
        patch("report_analyst.streamlit_app.st.empty") as placeholder,
        patch("report_analyst.streamlit_app.st.rerun") as rerun,
        patch("report_analyst.streamlit_app.st.session_state", {}),
        patch("report_analyst.streamlit_app.pdf_viewer", return_value=event),
    ):
        for _ in range(2):
            display_pdf_viewer(str(pdf_path), {}, {}, cache_manager)
    return placeholder.return_value.error, rerun


def test_display_pdf_viewer_passes_saved_sources_to_the_viewer(pdf_path):
    document_id = compute_file_hash(str(pdf_path))
    cache_manager = storage()
    cache_manager.get_source_annotations.return_value = [{"id": "source-1"}]

    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()),
        patch("report_analyst.streamlit_app.pdf_viewer", return_value=None) as component,
    ):
        display_pdf_viewer(str(pdf_path), {}, {}, cache_manager)

    cache_manager.get_source_annotations.assert_called_once_with(document_id)
    assert component.call_args.kwargs["document_id"] == document_id
    assert component.call_args.kwargs["annotations"] == [{"id": "source-1", "tags": []}]


TAXONOMY = Taxonomy(
    identifier="https://example.org/build",
    name="Sample ESRS Taxonomy",
    version="2026-08-30",
    concepts=[
        TaxonomyConcept(
            name="esrs:Scope1",
            label="Gross scope 1 GHG emissions",
            kind="number",
            data_type="dtr-types:ghgEmissionsItemType",
            period_type="duration",
        )
    ],
)
TAG = SourceTag(
    id="tag-1",
    source_id="source-1",
    document_id="document-hash",
    concept="esrs:Scope1",
    value="1240",
    unit="tCO2e",
    decimals=0,
)


def _viewer_sources(pdf_path):
    cache_manager = storage()
    cache_manager.get_source_annotations.return_value = [{"id": "source-1"}, {"id": "source-2"}]
    cache_manager.get_source_tags.return_value = [TAG]
    with (
        patch("report_analyst.streamlit_app.st.expander", return_value=nullcontext()),
        patch("report_analyst.streamlit_app.pdf_viewer", return_value=None) as component,
        patch("report_analyst.streamlit_app.display_concept_search"),
    ):
        display_pdf_viewer(str(pdf_path), {}, {}, cache_manager)
    return component.call_args.kwargs["annotations"]


def test_display_pdf_viewer_gives_each_source_its_tags(pdf_path):
    with patch("report_analyst.streamlit_app.current_taxonomy", return_value=TAXONOMY):
        sources = _viewer_sources(pdf_path)

    assert sources == [
        {"id": "source-1", "tags": [{"id": "tag-1", "text": "Gross scope 1 GHG emissions: 1240 tCO2e"}]},
        {"id": "source-2", "tags": []},
    ]


def test_display_pdf_viewer_names_tags_by_concept_without_a_taxonomy(pdf_path):
    with patch("report_analyst.streamlit_app.current_taxonomy", side_effect=TaxonomyUnavailableError("Not set up.")):
        sources = _viewer_sources(pdf_path)

    assert sources[0]["tags"] == [{"id": "tag-1", "text": "esrs:Scope1: 1240 tCO2e"}]


def test_display_pdf_viewer_saves_a_new_source_anchor_once(pdf_path):
    event = _source_event(compute_file_hash(str(pdf_path)))
    cache_manager = storage()

    _, rerun = _render_viewer_twice(pdf_path, event, cache_manager)

    cache_manager.save_source_annotation.assert_called_once_with(event["annotation"])
    rerun.assert_called_once_with()


def test_display_pdf_viewer_deletes_a_saved_source_anchor_once(pdf_path):
    document_id = compute_file_hash(str(pdf_path))
    cache_manager = storage()

    _, rerun = _render_viewer_twice(pdf_path, _source_event(document_id, action="delete"), cache_manager)

    cache_manager.delete_source_annotation.assert_called_once_with("source-1", document_id)
    rerun.assert_called_once_with()


def test_display_pdf_viewer_deletes_a_tag_once(pdf_path):
    document_id = compute_file_hash(str(pdf_path))
    cache_manager = storage()
    event = {"action": "delete_tag", "annotation": {"id": "tag-1", "document_id": document_id}}

    _, rerun = _render_viewer_twice(pdf_path, event, cache_manager)

    cache_manager.delete_source_tag.assert_called_once_with("tag-1", document_id)
    cache_manager.delete_source_annotation.assert_not_called()
    rerun.assert_called_once_with()


def test_display_pdf_viewer_ignores_an_event_from_an_earlier_upload(pdf_path):
    cache_manager = storage()

    error, rerun = _render_viewer_twice(pdf_path, _source_event("earlier-upload"), cache_manager)

    cache_manager.save_source_annotation.assert_not_called()
    error.assert_not_called()
    rerun.assert_not_called()


@pytest.mark.parametrize(
    ("action", "method", "message"),
    [
        ("create", "save_source_annotation", "Could not save this evidence. Select the text and add it again."),
        ("delete", "delete_source_annotation", "Could not remove this evidence. Reload the page and try again."),
        ("delete_tag", "delete_source_tag", "Could not remove this tag. Reload the page and try again."),
    ],
)
def test_display_pdf_viewer_reports_a_failed_change_once(pdf_path, action, method, message):
    cache_manager = storage()
    change = getattr(cache_manager, method)
    change.side_effect = OperationalError("write", {}, Exception("database is locked"))
    event = _source_event(compute_file_hash(str(pdf_path)), action=action)

    error, rerun = _render_viewer_twice(pdf_path, event, cache_manager)

    change.assert_called_once()
    error.assert_called_once_with(message)
    rerun.assert_not_called()


def test_display_pdf_viewer_reports_an_invalid_source_anchor(pdf_path, tmp_path):
    document_id = compute_file_hash(str(pdf_path))
    cache_manager = CacheManager(str(tmp_path / "cache.db"))

    error, rerun = _render_viewer_twice(pdf_path, _source_event(document_id, rects=[]), cache_manager)

    error.assert_called_once_with("Could not save this evidence. Select the text and add it again.")
    rerun.assert_not_called()
    assert cache_manager.get_source_annotations(document_id) == []


def _viewer_results(results, cache_manager):
    return _get_pdf_viewer_results("report.pdf", {"question_set": "tcfd"}, results, cache_manager)


def test_pdf_viewer_keeps_analyzed_evidence_after_component_rerun():
    results = {"tcfd_1": {"chunks": [{"text": "Existing evidence", "is_evidence": True}]}}
    cache_manager = Mock()

    with (
        patch("report_analyst.streamlit_app.generate_file_key", return_value="report-config"),
        patch("report_analyst.streamlit_app.st.session_state", {}),
    ):
        assert _viewer_results(results, cache_manager) == results
        assert _viewer_results({}, cache_manager) == results

    cache_manager.get_analysis.assert_not_called()


def test_pdf_viewer_loads_cached_analysis_when_opened():
    results = {"tcfd_1": {"chunks": [{"text": "Cached evidence", "is_evidence": True}]}}
    cache_manager = Mock()
    cache_manager.get_analysis.return_value = results

    with (
        patch("report_analyst.streamlit_app.generate_file_key", return_value="report-config"),
        patch("report_analyst.streamlit_app.st.session_state", {}),
    ):
        assert _viewer_results({}, cache_manager) == results
        assert _viewer_results({}, cache_manager) == results

    cache_manager.get_analysis.assert_called_once_with(file_path="report.pdf", config={"question_set": "tcfd"})
