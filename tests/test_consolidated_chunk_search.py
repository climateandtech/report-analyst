"""Tests for All Results chunk search modes."""

from unittest.mock import Mock

import numpy as np
import pytest

from report_analyst.consolidated_results_view import (
    render_consolidated_chunk_search,
    render_consolidated_report_view,
)


@pytest.fixture
def mock_analyzer():
    analyzer = Mock()
    analyzer.analyzer = Mock()
    analyzer.analyzer.question_set = "tcfd"
    analyzer.analyzer.questions = {"tcfd_1": {"text": "What are Scope 1 emissions?"}}
    analyzer.analyzer.use_backend_llm = False
    analyzer.analyzer.embeddings = Mock()
    analyzer.analyzer.embeddings.get_text_embedding.return_value = [1.0, 0.0]
    analyzer.analyzer._ensure_embeddings_client = Mock()
    analyzer.analyzer.update_question_set = Mock()
    analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = []
    analyzer.analyzer.cache_manager.get_analysis.return_value = None
    return analyzer


def _patch_streamlit(monkeypatch, *, selectbox="None", text_input=""):
    subheaders: list[str] = []
    captions: list[str] = []
    infos: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    successes: list[str] = []
    col = Mock()
    col.__enter__ = Mock(return_value=col)
    col.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.subheader", lambda t: subheaders.append(t))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.caption", lambda t: captions.append(t))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.columns", lambda n: (col, col))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.selectbox", Mock(return_value=selectbox))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.text_input", Mock(return_value=text_input))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.dataframe", Mock())
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.info", lambda t: infos.append(t))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.warning", lambda t: warnings.append(t))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.error", lambda t: errors.append(t))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.success", lambda t: successes.append(t))
    monkeypatch.setattr(
        "report_analyst.consolidated_results_view.st.column_config",
        Mock(NumberColumn=Mock, TextColumn=Mock, CheckboxColumn=Mock),
    )
    return {
        "subheaders": subheaders,
        "captions": captions,
        "infos": infos,
        "warnings": warnings,
        "errors": errors,
        "successes": successes,
    }


def _embedded_chunk(vec=(1.0, 0.0)):
    return {
        "text": "Scope 1 disclosure.",
        "embedding": np.array(vec, dtype=np.float32).tobytes(),
        "chunk_size": 500,
        "chunk_overlap": 20,
    }


def test_text_only_chunks_skip_similarity_controls(mock_analyzer, monkeypatch):
    text_only = [{"text": "Scope 1 disclosure.", "embedding": None, "chunk_size": 500, "chunk_overlap": 20}]
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = text_only
    ui = _patch_streamlit(monkeypatch)
    monkeypatch.setattr(
        "report_analyst.consolidated_results_view.st.selectbox",
        Mock(side_effect=AssertionError("no similarity UI")),
    )
    monkeypatch.setattr(
        "report_analyst.consolidated_results_view.st.text_input",
        Mock(side_effect=AssertionError("no similarity UI")),
    )

    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert ui["subheaders"] == ["Document Chunks"]
    assert any("Embed" in c for c in ui["captions"])


def test_embedded_chunks_show_similarity_search(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [_embedded_chunk()]
    ui = _patch_streamlit(monkeypatch)
    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert ui["subheaders"] == ["Similarity Search"]


def test_empty_chunks_warns_and_returns_false(mock_analyzer, monkeypatch):
    ui = _patch_streamlit(monkeypatch)
    assert not render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert ui["subheaders"] == ["Document Chunks"]
    assert ui["warnings"]


def test_similarity_ranks_with_selected_question(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.question_set = "other"
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [
        _embedded_chunk((1.0, 0.0)),
        _embedded_chunk((0.0, 1.0)),
    ]
    ui = _patch_streamlit(monkeypatch, selectbox="tcfd_1", text_input="")
    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    mock_analyzer.analyzer.update_question_set.assert_called_once_with("tcfd")
    assert ui["successes"]
    assert any("Using question" in i for i in ui["infos"])
    assert any("tcfd_1" in c for c in ui["captions"])


def test_similarity_ranks_with_custom_question(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [_embedded_chunk()]
    ui = _patch_streamlit(monkeypatch, selectbox="None", text_input="  custom query  ")
    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert any("custom question" in i for i in ui["infos"])
    assert ui["successes"]


def test_similarity_backend_llm_warns(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.use_backend_llm = True
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [_embedded_chunk()]
    ui = _patch_streamlit(monkeypatch, selectbox="tcfd_1")
    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert any("backend LLM" in w for w in ui["warnings"])


def test_similarity_runtime_error_warns(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer._ensure_embeddings_client.side_effect = RuntimeError("no key")
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [_embedded_chunk()]
    ui = _patch_streamlit(monkeypatch, selectbox="tcfd_1")
    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert "no key" in ui["warnings"][0]


def test_similarity_generic_exception_errors(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.embeddings.get_text_embedding.side_effect = ValueError("boom")
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [_embedded_chunk()]
    ui = _patch_streamlit(monkeypatch, selectbox="tcfd_1")
    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert any("boom" in e for e in ui["errors"])


def test_report_view_chunks_only_without_answers(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [
        {"text": "x", "embedding": None, "chunk_size": 500, "chunk_overlap": 20}
    ]
    ui = _patch_streamlit(monkeypatch)
    display = Mock()
    render_consolidated_report_view(
        mock_analyzer,
        "tcfd",
        "report.pdf",
        {"chunk_size": 500, "chunk_overlap": 20, "chunks_only": True},
        display_analysis_results=display,
    )
    assert any("No answer results" in i for i in ui["infos"])
    display.assert_not_called()


def test_report_view_warns_when_nothing_cached(mock_analyzer, monkeypatch):
    ui = _patch_streamlit(monkeypatch)
    render_consolidated_report_view(
        mock_analyzer,
        "tcfd",
        "report.pdf",
        {"chunk_size": 500, "chunk_overlap": 20},
        display_analysis_results=Mock(),
    )
    assert any("No stored results" in w for w in ui["warnings"])


def test_report_view_handles_chunk_search_exception(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.side_effect = RuntimeError("cache down")
    ui = _patch_streamlit(monkeypatch)
    render_consolidated_report_view(
        mock_analyzer,
        "tcfd",
        "report.pdf",
        {"chunk_size": 500, "chunk_overlap": 20, "chunks_only": True},
        display_analysis_results=Mock(),
    )
    assert any("No answer results" in i for i in ui["infos"])


def test_report_view_renders_cached_analysis(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.question_set = "other"
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [
        {"text": "x", "embedding": None, "chunk_size": 500, "chunk_overlap": 20}
    ]
    mock_analyzer.analyzer.cache_manager.get_analysis.return_value = {
        "tcfd_1": {
            "result": {
                "ANSWER": "Yes",
                "SCORE": "1.5",
                "EVIDENCE": [{"text": "ev"}],
                "GAPS": ["gap"],
                "SOURCES": [1, 2],
            },
            "chunks": [
                {
                    "text": "chunk",
                    "similarity_score": 0.9,
                    "llm_score": 0.8,
                    "is_evidence": True,
                    "chunk_order": 1,
                }
            ],
        },
        "bad": {"result": None},
    }
    _patch_streamlit(monkeypatch)
    display = Mock()
    render_consolidated_report_view(
        mock_analyzer,
        "tcfd",
        "report.pdf",
        {"chunk_size": 500, "chunk_overlap": 20},
        display_analysis_results=display,
    )
    mock_analyzer.analyzer.update_question_set.assert_called_with("tcfd")
    display.assert_called_once()
    analysis_df, chunks_df, file_key = display.call_args[0]
    assert file_key == "report_cs500"
    assert list(analysis_df["Question ID"]) == ["tcfd_1"]
    assert not chunks_df.empty


def test_report_view_warns_when_all_results_fail(mock_analyzer, monkeypatch):
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = [
        {"text": "x", "embedding": None, "chunk_size": 500, "chunk_overlap": 20}
    ]
    mock_analyzer.analyzer.cache_manager.get_analysis.return_value = {"bad": {"result": None}}
    ui = _patch_streamlit(monkeypatch)
    render_consolidated_report_view(
        mock_analyzer,
        "tcfd",
        "report.pdf",
        {"chunk_size": 500, "chunk_overlap": 20},
        display_analysis_results=Mock(),
    )
    assert any("No results found" in w for w in ui["warnings"])
