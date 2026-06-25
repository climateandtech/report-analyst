"""Tests for document processing step pipeline (Chunk / Embed / Map / Answer)."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from report_analyst.core.analyzer import (
    DocumentAnalyzer,
    normalize_processing_step,
    processing_step_rank,
)
from report_analyst.core.cache_manager import CacheManager


@pytest.fixture(scope="session")
def _processing_steps_db_template():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "analysis_template.db"
    CacheManager(str(db_path))
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def clean_db(_processing_steps_db_template):
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / f"analysis_{uuid.uuid4().hex}.db"
    shutil.copy2(_processing_steps_db_template, db_path)
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def analyzer(monkeypatch, clean_db):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_ORGANIZATION", "test-org")
    monkeypatch.setenv("USE_BACKEND", "false")
    with patch("llama_index.embeddings.openai.OpenAIEmbedding"), patch(
        "report_analyst.core.llm_providers.get_llm"
    ) as mock_get_llm:
        mock_get_llm.return_value = Mock(model="gpt-4o-mini", achat=AsyncMock())
        doc_analyzer = DocumentAnalyzer()
        doc_analyzer.cache_manager = CacheManager(db_path=str(clean_db))
        doc_analyzer.llm = Mock(model="gpt-4o-mini", achat=AsyncMock())
        yield doc_analyzer


async def _collect_process_events(analyzer, **kwargs):
    events = []
    async for event in analyzer.process_document(**kwargs):
        events.append(event)
    return events


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Chunk", "chunk"),
        ("Embed", "embed"),
        ("Map", "map"),
        ("Answer", "answer"),
        ("chunk", "chunk"),
        (None, "answer"),
        ("", "answer"),
    ],
)
def test_normalize_processing_step_maps_ui_labels(raw, expected):
    assert normalize_processing_step(raw) == expected


def test_processing_step_rank_order():
    assert processing_step_rank("chunk") < processing_step_rank("embed")
    assert processing_step_rank("embed") < processing_step_rank("map")
    assert processing_step_rank("map") < processing_step_rank("answer")


def test_save_text_only_chunks_persists_rows_without_embeddings(clean_db, tmp_path):
    cache = CacheManager(db_path=str(clean_db))
    file_path = str(tmp_path / "report.pdf")
    chunks = [{"text": "Board oversight section.", "metadata": {"page": 1}}]

    cache.save_text_only_chunks(
        file_path=file_path,
        chunks=chunks,
        chunk_size=500,
        chunk_overlap=20,
    )

    stored = cache.get_chunks_without_embeddings(file_path, chunk_size=500, chunk_overlap=20)
    assert len(stored) == 1
    assert stored[0]["text"] == "Board oversight section."
    assert stored[0]["embedding"] is None


@pytest.mark.asyncio
async def test_process_document_chunk_step_stops_before_llm(analyzer, clean_db, tmp_path):
    """Hypothesis: Chunk-only must not invoke chat LLM even when questions are selected."""
    file_path = str(tmp_path / "chunk-only.pdf")
    text_chunks = [{"text": "Climate risk paragraph.", "metadata": {"page": 1}, "embedding": None}]

    analyzer.llm = Mock(achat=AsyncMock())
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer, "_create_text_chunks", return_value=text_chunks):
        events = []
        async for event in analyzer.process_document(
            file_path,
            selected_questions=[1],
            max_processing_step="chunk",
        ):
            events.append(event)

    analyzer.llm.achat.assert_not_called()
    statuses = [e.get("status", "") for e in events if "status" in e]
    assert any("Completed Chunk" in s for s in statuses)
    assert not any("error" in e for e in events)


@pytest.mark.asyncio
async def test_process_document_map_step_skips_answer_llm(analyzer, clean_db, tmp_path):
    """Hypothesis: Map step ranks chunks but must not call _analyze_chunks / achat."""
    file_path = str(tmp_path / "map-only.pdf")
    embedded = [
        {
            "text": "Scope 1 emissions disclosure.",
            "metadata": {"page": 2},
            "embedding": np.array([0.1, 0.2, 0.3], dtype=np.float32),
        }
    ]

    analyzer.llm = Mock(achat=AsyncMock())
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer, "_get_similar_chunks", AsyncMock(return_value=embedded)
    ), patch.object(analyzer, "_analyze_chunks", AsyncMock()) as mock_analyze, patch.object(
        analyzer, "get_question_by_number", return_value={"text": "What are Scope 1 emissions?", "guidelines": ""}
    ):
        events = []
        async for event in analyzer.process_document(
            file_path,
            selected_questions=[1],
            max_processing_step="map",
        ):
            events.append(event)

    mock_analyze.assert_not_called()
    analyzer.llm.achat.assert_not_called()
    assert any("Completed Map" in e.get("status", "") for e in events)


@pytest.mark.asyncio
async def test_process_document_embed_step_upgrades_text_chunks(analyzer, clean_db, tmp_path):
    """Hypothesis: Embed step adds embeddings to text-only cache rows and stops before questions."""
    file_path = str(tmp_path / "embed-only.pdf")
    text_only = [{"text": "Paragraph awaiting embeddings.", "metadata": {"page": 1}, "embedding": None}]
    embedded = [
        {
            "text": "Paragraph awaiting embeddings.",
            "metadata": {"page": 1},
            "embedding": np.array([0.4, 0.5, 0.6], dtype=np.float32),
        }
    ]

    analyzer.llm = Mock(achat=AsyncMock())
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=text_only), patch.object(
        analyzer, "_add_embeddings_to_chunks", return_value=embedded
    ) as mock_embed, patch.object(analyzer.cache_manager, "save_document_chunks") as mock_save, patch.object(
        analyzer, "_analyze_chunks", AsyncMock()
    ) as mock_analyze:
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[1],
            max_processing_step="embed",
        )

    mock_embed.assert_called_once_with(text_only)
    mock_save.assert_called_once()
    mock_analyze.assert_not_called()
    analyzer.llm.achat.assert_not_called()
    assert any("Completed Embed" in e.get("status", "") for e in events)


@pytest.mark.asyncio
async def test_process_document_chunk_step_allows_empty_question_list(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "chunk-no-questions.pdf")
    text_chunks = [{"text": "No questions needed.", "metadata": {}, "embedding": None}]

    analyzer.llm = Mock(achat=AsyncMock())
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer, "_create_text_chunks", return_value=text_chunks):
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[],
            max_processing_step="chunk",
        )

    assert not any("error" in e for e in events)
    assert any("Completed Chunk" in e.get("status", "") for e in events)


@pytest.mark.asyncio
async def test_process_document_embed_step_allows_empty_question_list(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "embed-no-questions.pdf")
    embedded = [
        {
            "text": "Already embedded.",
            "metadata": {},
            "embedding": np.array([0.1, 0.2], dtype=np.float32),
        }
    ]

    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded):
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[],
            max_processing_step="embed",
        )

    assert not any("error" in e for e in events)
    assert any("Completed Embed" in e.get("status", "") for e in events)


@pytest.mark.asyncio
async def test_process_document_map_step_requires_questions(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "map-no-questions.pdf")
    embedded = [
        {
            "text": "Embedded chunk.",
            "metadata": {},
            "embedding": np.array([0.2, 0.3], dtype=np.float32),
        }
    ]
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded):
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[],
            max_processing_step="map",
        )

    assert any("Select at least one question" in e.get("error", "") for e in events)


@pytest.mark.asyncio
async def test_process_document_answer_step_calls_analyze_chunks(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "full-answer.pdf")
    embedded = [
        {
            "text": "Evidence paragraph.",
            "metadata": {"page": 3},
            "embedding": np.array([0.7, 0.8], dtype=np.float32),
        }
    ]
    analyze_result = {"ANSWER": "Yes", "SCORE": 0.9, "EVIDENCE": []}

    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer, "_get_similar_chunks", AsyncMock(return_value=embedded)
    ), patch.object(
        analyzer, "get_question_by_number", return_value={"text": "Board oversight?", "guidelines": ""}
    ), patch.object(
        analyzer, "_analyze_chunks", AsyncMock(return_value=analyze_result)
    ) as mock_analyze, patch.object(
        analyzer.cache_manager, "save_analysis"
    ):
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[1],
            max_processing_step="answer",
        )

    mock_analyze.assert_called_once()
    assert any(e.get("question_number") == 1 for e in events)


@pytest.mark.asyncio
async def test_process_document_map_with_llm_scoring_uses_scoring_not_answer(analyzer, clean_db, tmp_path):
    """Map + LLM scoring may call scoring batch, but must not run full answer analysis."""
    file_path = str(tmp_path / "map-scoring.pdf")
    embedded = [
        {
            "text": "Metric disclosure.",
            "metadata": {},
            "embedding": np.array([0.3, 0.4], dtype=np.float32),
        }
    ]

    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer, "_get_similar_chunks", AsyncMock(return_value=embedded)
    ), patch.object(analyzer, "get_question_by_number", return_value={"text": "Emissions?", "guidelines": ""}), patch.object(
        analyzer, "score_chunk_relevance_batch", AsyncMock(return_value=[0.85])
    ) as mock_score_batch, patch.object(
        analyzer, "_analyze_chunks", AsyncMock()
    ) as mock_analyze:
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[1],
            use_llm_scoring=True,
            max_processing_step="map",
        )

    mock_score_batch.assert_called_once()
    mock_analyze.assert_not_called()
    assert any("Completed Map" in e.get("status", "") for e in events)


@pytest.mark.parametrize(
    ("slider", "needs_questions"),
    [
        ("Chunk", False),
        ("Embed", False),
        ("Map", True),
        ("Answer", True),
    ],
)
def test_processing_step_needs_questions(slider, needs_questions):
    import report_analyst.streamlit_app as app

    class FakeSessionState(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    original = app.st.session_state
    app.st.session_state = FakeSessionState({"processing_steps_slider": slider})
    try:
        assert app.processing_step_needs_questions() is needs_questions
    finally:
        app.st.session_state = original


def test_get_max_processing_step_reads_streamlit_slider():
    import report_analyst.streamlit_app as app

    class FakeSessionState(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    original = app.st.session_state
    app.st.session_state = FakeSessionState({"processing_steps_slider": "Chunk"})
    try:
        assert app.get_max_processing_step() == "chunk"
        assert app.processing_step_needs_questions() is False
    finally:
        app.st.session_state = original
