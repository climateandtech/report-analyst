"""Tests for All Results chunk search modes."""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from report_analyst.consolidated_results_view import render_consolidated_chunk_search


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
    analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = []
    return analyzer


def test_text_only_chunks_skip_similarity_controls(mock_analyzer, monkeypatch):
    text_only = [{"text": "Scope 1 disclosure.", "embedding": None, "chunk_size": 500, "chunk_overlap": 20}]
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = text_only

    subheaders: list[str] = []
    captions: list[str] = []
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.subheader", lambda t: subheaders.append(t))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.caption", lambda t: captions.append(t))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.selectbox", Mock(side_effect=AssertionError("no similarity UI")))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.text_input", Mock(side_effect=AssertionError("no similarity UI")))
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.dataframe", Mock())
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.info", Mock())

    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "/tmp/report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert subheaders == ["Document Chunks"]
    assert any("Embed" in c for c in captions)


def test_embedded_chunks_show_similarity_search(mock_analyzer, monkeypatch):
    embedded = [
        {
            "text": "Scope 1 disclosure.",
            "embedding": np.array([1.0, 0.0], dtype=np.float32),
            "chunk_size": 500,
            "chunk_overlap": 20,
        }
    ]
    mock_analyzer.analyzer.cache_manager.resolve_document_chunks.return_value = embedded

    subheaders: list[str] = []
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.subheader", lambda t: subheaders.append(t))
    col = Mock()
    col.__enter__ = Mock(return_value=col)
    col.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.columns", lambda n: (col, col))
    monkeypatch.setattr(
        "report_analyst.consolidated_results_view.st.selectbox",
        Mock(return_value="None"),
    )
    monkeypatch.setattr(
        "report_analyst.consolidated_results_view.st.text_input",
        Mock(return_value=""),
    )
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.dataframe", Mock())
    monkeypatch.setattr("report_analyst.consolidated_results_view.st.info", Mock())

    assert render_consolidated_chunk_search(mock_analyzer, "tcfd", "/tmp/report.pdf", {"chunk_size": 500, "chunk_overlap": 20})
    assert subheaders == ["Similarity Search"]
