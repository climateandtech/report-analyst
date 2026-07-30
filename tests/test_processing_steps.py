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


class FakeSessionState(dict):
    def get(self, key, default=None):
        return super().get(key, default)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


def make_run_analysis_session(**overrides):
    base = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "llm_model": "gpt-4o-mini",
        "question_set": "tcfd",
        "force_recompute": False,
        "new_llm_scoring": False,
        "new_chunk_size": 500,
        "new_overlap": 20,
        "new_top_k": 5,
        "new_llm_model": "gpt-4o-mini",
        "new_question_set": "tcfd",
    }
    base.update(overrides)
    return FakeSessionState(base)


def patch_streamlit_app(monkeypatch, **session_overrides):
    import report_analyst.streamlit_app as app

    fake_st = make_run_analysis_session(**session_overrides)
    monkeypatch.setattr(app, "st", Mock(session_state=fake_st))
    return app, fake_st


async def _async_status_events(*statuses):
    for status in statuses:
        yield {"status": status}


@pytest.fixture(autouse=True)
def _isolate_streamlit_module(monkeypatch):
    """Reset streamlit_app.st between tests so random order does not leak mocks."""
    import streamlit as real_streamlit
    import report_analyst.streamlit_app as app

    monkeypatch.setattr(app, "st", real_streamlit, raising=False)


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
async def test_process_document_chunk_step_reuses_cached_chunks(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "cached-chunk.pdf")
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))
    analyzer.cache_manager.save_text_only_chunks(
        file_path=file_path,
        chunks=[{"text": "From cache.", "metadata": {"page": 1}}],
        chunk_size=500,
        chunk_overlap=20,
    )

    with patch.object(analyzer, "_create_text_chunks", side_effect=AssertionError("should not re-chunk")):
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[],
            max_processing_step="chunk",
        )

    assert any("Completed Chunk" in e.get("status", "") for e in events)


@pytest.mark.asyncio
async def test_process_document_chunk_step_uses_text_chunks_not_embedded_create(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "new-chunk.pdf")
    text_chunks = [{"text": "Fresh chunk.", "metadata": {}, "embedding": None}]
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer, "_create_text_chunks", return_value=text_chunks) as mock_text, patch.object(
        analyzer, "_create_chunks", side_effect=AssertionError("chunk step must not embed")
    ):
        await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[],
            max_processing_step="chunk",
        )

    mock_text.assert_called_once()


@pytest.mark.asyncio
async def test_process_document_embed_step_skips_reembed_when_already_embedded(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "already-embedded.pdf")
    embedded = [
        {
            "text": "Has embedding.",
            "metadata": {},
            "embedding": np.array([0.1, 0.2], dtype=np.float32),
        }
    ]
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer, "_add_embeddings_to_chunks", side_effect=AssertionError("should not re-embed")
    ):
        events = await _collect_process_events(
            analyzer,
            file_path=file_path,
            selected_questions=[],
            max_processing_step="embed",
        )

    assert any("Completed Embed" in e.get("status", "") for e in events)


@pytest.mark.asyncio
async def test_process_document_answer_step_requires_questions(analyzer, clean_db, tmp_path):
    file_path = str(tmp_path / "answer-no-questions.pdf")
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
            max_processing_step="answer",
        )

    assert any("Select at least one question" in e.get("error", "") for e in events)


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

    original = app.st.session_state
    app.st.session_state = FakeSessionState({"processing_steps_slider": slider})
    try:
        assert app.processing_step_needs_questions() is needs_questions
    finally:
        app.st.session_state = original


@pytest.mark.parametrize(
    ("step", "partial"),
    [
        ("Chunk", True),
        ("Embed", True),
        ("Map", False),
        ("Answer", False),
    ],
)
def test_is_partial_processing_step(step, partial):
    import report_analyst.streamlit_app as app

    assert app.is_partial_processing_step(step) is partial
    assert app.processing_step_needs_questions_for(step) is not partial


def test_chunk_with_selected_questions_is_partial_not_full_answer():
    """Regression: Chunk + selected questions must not take the Map/Answer LLM path."""
    import report_analyst.streamlit_app as app

    assert app.is_partial_processing_step("Chunk") is True
    assert app.processing_step_needs_questions_for("Chunk") is False


def test_display_cached_document_chunks_renders_rows(monkeypatch):
    import report_analyst.streamlit_app as app

    report_analyzer = Mock()
    report_analyzer.cache_manager.get_document_chunks.return_value = [
        {"text": "Paragraph one.", "embedding": None},
        {"text": "Paragraph two.", "embedding": object()},
    ]

    dataframe_calls: list = []

    def capture_dataframe(df, **kwargs):
        dataframe_calls.append(df)
        return Mock()

    monkeypatch.setattr(app.st, "subheader", Mock())
    monkeypatch.setattr(app.st, "info", Mock())
    monkeypatch.setattr(app.st, "warning", Mock())
    monkeypatch.setattr(app.st, "dataframe", capture_dataframe)
    monkeypatch.setattr(app.st, "column_config", Mock(NumberColumn=Mock, TextColumn=Mock, CheckboxColumn=Mock))

    count, embedded = app.display_cached_document_chunks(
        report_analyzer,
        "/tmp/report.pdf",
        chunk_size=500,
        chunk_overlap=20,
    )

    assert count == 2
    assert embedded == 1
    assert len(dataframe_calls) == 1
    assert list(dataframe_calls[0]["Text"]) == ["Paragraph one.", "Paragraph two."]


@pytest.mark.asyncio
async def test_report_analyzer_analyze_document_forwards_max_processing_step(clean_db, tmp_path):
    """analyze_document must pass max_processing_step through to process_document."""
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "forward-step.pdf")

    async def fake_process_document(*args, **kwargs):
        yield {"status": f"Completed {kwargs.get('max_processing_step')} step"}

    wrapper = Mock()
    wrapper.analyzer = Mock(process_document=fake_process_document, question_set="tcfd")

    events = []
    async for event in app.ReportAnalyzer.analyze_document(
        wrapper,
        file_path,
        {"tcfd_1": {"number": 1, "text": "Q1"}},
        ["tcfd_1"],
        max_processing_step="chunk",
    ):
        events.append(event)

    assert any("chunk" in e.get("status", "") for e in events)


@pytest.mark.asyncio
async def test_analyze_document_and_display_chunk_step_does_not_default_to_answer(
    monkeypatch, clean_db, tmp_path
):
    """Regression: analyze_document_and_display without max_processing_step ran full Answer (OpenAI 401)."""
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "display-chunk.pdf")
    captured: dict = {}

    async def fake_analyze_document(*args, **kwargs):
        captured["max_processing_step"] = kwargs.get("max_processing_step")
        yield {"status": "Completed Chunk step (2 chunks)"}

    fake_st = make_run_analysis_session(
        results={"answers": {}},
        current_question_set="tcfd",
        analyzed_files=set(),
        force_recompute=True,
    )

    report_analyzer = Mock()
    report_analyzer.analyze_document = fake_analyze_document
    report_analyzer.cache_manager = Mock(get_analysis=Mock(return_value={}))

    monkeypatch.setattr(app, "st", Mock(session_state=fake_st, empty=Mock(return_value=Mock())))
    monkeypatch.setattr(app, "generate_file_key", Mock(return_value="test_key"))

    await app.analyze_document_and_display(
        report_analyzer,
        file_path=file_path,
        questions={"tcfd_1": {"number": 1, "text": "Q1"}},
        selected_questions=["tcfd_1"],
        force_recompute=True,
        max_processing_step="chunk",
    )

    assert captured.get("max_processing_step") == "chunk"


@pytest.mark.asyncio
async def test_run_analysis_chunk_step_ignores_stale_analysis_cache(monkeypatch, tmp_path):
    """Regression: empty question_ids analysis_cache hit hid chunks on Chunk/Embed reruns."""
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "cached-chunks.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.analyzer.chunk_params = {"chunk_size": 500, "chunk_overlap": 20}
    report_analyzer.cache_manager.get_analysis.return_value = {"tcfd_1": {"result": {"ANSWER": "Yes"}}}
    report_analyzer.cache_manager.get_document_chunks.return_value = [
        {"text": "Cached chunk text.", "embedding": None},
    ]

    display_calls: list = []

    def capture_display(*args, **kwargs):
        display_calls.append(kwargs)
        return 1, 1

    monkeypatch.setattr(app, "st", Mock(session_state=make_run_analysis_session()))
    monkeypatch.setattr(app, "display_cached_document_chunks", capture_display)

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=[],
        progress_text=progress,
        max_processing_step="chunk",
    )

    report_analyzer.cache_manager.get_analysis.assert_not_called()
    assert display_calls
    progress.success.assert_called_once()
    assert "stored chunks" in progress.success.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_analyze_document_and_display_default_max_step_is_answer(monkeypatch, tmp_path):
    """Document prior default: omitting max_processing_step means full Answer pipeline."""
    import report_analyst.streamlit_app as app

    captured: dict = {}

    async def fake_analyze_document(*args, **kwargs):
        captured["max_processing_step"] = kwargs.get("max_processing_step")
        yield {"status": "done"}

    fake_st = make_run_analysis_session(
        results={"answers": {}},
        current_question_set="tcfd",
        analyzed_files=set(),
        force_recompute=True,
    )

    report_analyzer = Mock()
    report_analyzer.analyze_document = fake_analyze_document
    report_analyzer.cache_manager = Mock(get_analysis=Mock(return_value={}))

    monkeypatch.setattr(app, "st", Mock(session_state=fake_st, empty=Mock(return_value=Mock())))

    await app.analyze_document_and_display(
        report_analyzer,
        file_path=str(tmp_path / "full.pdf"),
        questions={"tcfd_1": {"number": 1, "text": "Q1"}},
        selected_questions=["tcfd_1"],
        force_recompute=True,
    )

    assert captured.get("max_processing_step") == "answer"


def test_get_max_processing_step_reads_streamlit_slider():
    import report_analyst.streamlit_app as app

    original = app.st.session_state
    app.st.session_state = FakeSessionState({"processing_steps_slider": "Chunk"})
    try:
        assert app.get_max_processing_step() == "chunk"
        assert app.processing_step_needs_questions() is False
    finally:
        app.st.session_state = original


@pytest.mark.parametrize("slider", ["Chunk", "Embed", "Map", "Answer"])
def test_get_max_processing_step_normalizes_all_slider_values(slider):
    import report_analyst.streamlit_app as app

    original = app.st.session_state
    app.st.session_state = FakeSessionState({"processing_steps_slider": slider})
    try:
        assert app.get_max_processing_step() == slider.lower()
    finally:
        app.st.session_state = original


def test_display_cached_document_chunks_empty_returns_zero(monkeypatch):
    import report_analyst.streamlit_app as app

    report_analyzer = Mock()
    report_analyzer.cache_manager.get_document_chunks.return_value = []
    monkeypatch.setattr(app.st, "warning", Mock())

    count, embedded = app.display_cached_document_chunks(report_analyzer, "/tmp/missing.pdf")

    assert count == 0
    assert embedded == 0
    app.st.warning.assert_called_once()


def test_display_cached_document_chunks_uses_chunk_text_fallback(monkeypatch):
    import report_analyst.streamlit_app as app

    report_analyzer = Mock()
    report_analyzer.cache_manager.get_document_chunks.return_value = [{"chunk_text": "Legacy text.", "embedding": None}]

    captured: list = []

    def capture_dataframe(df, **kwargs):
        captured.append(df)

    monkeypatch.setattr(app.st, "subheader", Mock())
    monkeypatch.setattr(app.st, "info", Mock())
    monkeypatch.setattr(app.st, "dataframe", capture_dataframe)
    monkeypatch.setattr(app.st, "column_config", Mock(NumberColumn=Mock, TextColumn=Mock, CheckboxColumn=Mock))

    count, embedded = app.display_cached_document_chunks(report_analyzer, "/tmp/report.pdf")

    assert count == 1
    assert embedded == 0
    assert captured[0]["Text"].iloc[0] == "Legacy text."


@pytest.mark.asyncio
@pytest.mark.parametrize("step", ["chunk", "embed"])
async def test_run_analysis_partial_step_shows_cached_document_chunks(monkeypatch, tmp_path, step):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / f"cached-{step}.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.analyzer.chunk_params = {"chunk_size": 500, "chunk_overlap": 20}
    report_analyzer.cache_manager.get_document_chunks.return_value = [
        {"text": "Cached chunk.", "embedding": object() if step == "embed" else None},
    ]

    display_calls: list = []

    monkeypatch.setattr(app, "st", Mock(session_state=make_run_analysis_session()))
    monkeypatch.setattr(
        app,
        "display_cached_document_chunks",
        lambda *a, **k: display_calls.append(k) or (1, 1 if step == "embed" else 0),
    )

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=[],
        progress_text=progress,
        max_processing_step=step,
    )

    report_analyzer.cache_manager.get_analysis.assert_not_called()
    assert display_calls
    progress.success.assert_called_once()


@pytest.mark.asyncio
async def test_run_analysis_embed_step_reruns_when_only_text_chunks_cached(monkeypatch, tmp_path):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "needs-embed.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.analyzer.chunk_params = {"chunk_size": 500, "chunk_overlap": 20}
    report_analyzer.cache_manager.get_document_chunks.return_value = [
        {"text": "Text only.", "embedding": None},
    ]

    async def fake_process_document(*args, **kwargs):
        async for event in _async_status_events("Completed Embed step (1 chunks)"):
            yield event

    report_analyzer.process_document = fake_process_document
    display_calls: list = []

    monkeypatch.setattr(app, "st", Mock(session_state=make_run_analysis_session()))
    monkeypatch.setattr(app, "display_cached_document_chunks", lambda *a, **k: display_calls.append(1) or (1, 1))

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=[],
        progress_text=progress,
        max_processing_step="embed",
    )

    progress.info.assert_any_call("Starting analysis...")
    assert display_calls


@pytest.mark.asyncio
async def test_run_analysis_chunk_force_recompute_runs_process_document(monkeypatch, tmp_path):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "force-chunk.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.analyzer.chunk_params = {"chunk_size": 500, "chunk_overlap": 20}
    report_analyzer.cache_manager.get_document_chunks.return_value = [
        {"text": "Old cache.", "embedding": None},
    ]

    async def fake_process_document(*args, **kwargs):
        async for event in _async_status_events("Completed Chunk step (2 chunks)"):
            yield event

    report_analyzer.process_document = fake_process_document
    display_mock = Mock(return_value=(2, 0))
    monkeypatch.setattr(app, "st", Mock(session_state=make_run_analysis_session(force_recompute=True)))
    monkeypatch.setattr(app, "display_cached_document_chunks", display_mock)

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=[],
        progress_text=progress,
        max_processing_step="chunk",
    )

    progress.info.assert_any_call("Starting analysis...")
    display_mock.assert_called_once()


@pytest.mark.asyncio
async def test_run_analysis_answer_cache_hit_returns_without_process(monkeypatch, tmp_path):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "answer-cached.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.cache_manager.get_analysis.return_value = {
        "tcfd_1": {"result": {"ANSWER": "Yes", "SCORE": 0.9}},
    }

    fake_st = make_run_analysis_session()
    monkeypatch.setattr(app, "st", Mock(session_state=fake_st))

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=["tcfd_1"],
        progress_text=progress,
        max_processing_step="answer",
    )

    report_analyzer.process_document.assert_not_called()
    progress.success.assert_called_once_with("Found stored results!")
    assert fake_st["results"]["tcfd_1"]["result"]["ANSWER"] == "Yes"


@pytest.mark.asyncio
async def test_run_analysis_answer_uses_full_question_ids_without_double_prefix(monkeypatch, tmp_path):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "answer-ids.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.cache_manager.get_analysis.return_value = {}

    async def fake_process_document(*args, **kwargs):
        yield {"question_number": 1, "result": {"ANSWER": "Done", "SCORE": 1.0}}

    report_analyzer.process_document = fake_process_document

    monkeypatch.setattr(app, "st", Mock(session_state=make_run_analysis_session(force_recompute=True)))

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=["tcfd_1", "tcfd_2"],
        progress_text=progress,
        max_processing_step="answer",
    )

    report_analyzer.cache_manager.get_analysis.assert_called()
    call_kwargs = report_analyzer.cache_manager.get_analysis.call_args_list[0].kwargs
    assert call_kwargs["question_ids"] == ["tcfd_1", "tcfd_2"]


@pytest.mark.asyncio
async def test_run_analysis_answer_prefixes_numeric_question_ids(monkeypatch, tmp_path):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "answer-numeric.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.cache_manager.get_analysis.return_value = {}

    async def fake_process_document(*args, **kwargs):
        if False:
            yield {}

    report_analyzer.process_document = fake_process_document
    patch_streamlit_app(monkeypatch, force_recompute=True)

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=["1", "2"],
        progress_text=progress,
        max_processing_step="answer",
    )

    call_kwargs = report_analyzer.cache_manager.get_analysis.call_args_list[0].kwargs
    assert call_kwargs["question_ids"] == ["tcfd_1", "tcfd_2"]


@pytest.mark.asyncio
async def test_run_analysis_answer_cache_miss_runs_process_and_completes(monkeypatch, tmp_path):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "answer-run.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.cache_manager.get_analysis.side_effect = [{}, {"tcfd_1": {"result": {"ANSWER": "Done"}}}]

    async def fake_process_document(*args, **kwargs):
        yield {"question_number": 1, "result": {"ANSWER": "Done", "SCORE": 1.0}}

    report_analyzer.process_document = fake_process_document
    monkeypatch.setattr(app, "st", Mock(session_state=make_run_analysis_session(force_recompute=True)))

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=["tcfd_1"],
        progress_text=progress,
        max_processing_step="answer",
    )

    progress.success.assert_called_with("Analysis complete!")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("max_step", "expected"),
    [
        ("chunk", "chunk"),
        ("embed", "embed"),
        ("map", "map"),
        ("answer", "answer"),
    ],
)
async def test_report_analyzer_analyze_document_forwards_all_processing_steps(
    max_step, expected, clean_db, tmp_path
):
    import report_analyst.streamlit_app as app

    captured: dict = {}

    async def fake_process_document(*args, **kwargs):
        captured["max_processing_step"] = kwargs.get("max_processing_step")
        yield {"status": "ok"}

    wrapper = Mock()
    wrapper.analyzer = Mock(process_document=fake_process_document, question_set="tcfd")

    async for _ in app.ReportAnalyzer.analyze_document(
        wrapper,
        str(tmp_path / "doc.pdf"),
        {"tcfd_1": {"number": 1, "text": "Q1"}},
        ["tcfd_1"],
        max_processing_step=max_step,
    ):
        pass

    assert captured["max_processing_step"] == expected


@pytest.mark.asyncio
async def test_analyze_document_and_display_respects_cached_answers_without_force_recompute(monkeypatch, tmp_path):
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "display-cache.pdf")
    report_analyzer = Mock()
    report_analyzer.cache_manager.get_analysis.return_value = {
        "tcfd_1": {"result": {"ANSWER": "Cached"}},
    }

    async def fail_analyze_document(*args, **kwargs):
        raise AssertionError("should not re-analyze when cache hit")

    report_analyzer.analyze_document = fail_analyze_document

    fake_st = make_run_analysis_session(
        results={"answers": {}},
        current_question_set="tcfd",
        analyzed_files=set(),
        force_recompute=False,
    )

    monkeypatch.setattr(app, "st", Mock(session_state=fake_st, info=Mock(), empty=Mock(return_value=Mock())))
    monkeypatch.setattr(app, "generate_file_key", Mock(return_value="file_key"))
    monkeypatch.setattr(app, "create_analysis_dataframes", Mock(return_value=(Mock(), Mock())))

    await app.analyze_document_and_display(
        report_analyzer,
        file_path=file_path,
        questions={"tcfd_1": {"number": 1, "text": "Q1"}},
        selected_questions=["tcfd_1"],
        max_processing_step="answer",
    )

    assert fake_st["results"]["answers"]["tcfd_1"]["result"]["ANSWER"] == "Cached"


@pytest.mark.asyncio
async def test_report_analyzer_process_document_forwards_pre_retrieved_chunks_and_max_step():
    import report_analyst.streamlit_app as app

    captured: dict = {}

    async def fake_process_document(*args, **kwargs):
        captured["pre_retrieved_chunks"] = kwargs.get("pre_retrieved_chunks")
        captured["max_processing_step"] = kwargs.get("max_processing_step")
        yield {"status": "done"}

    report_analyzer = app.ReportAnalyzer()
    report_analyzer.analyzer.process_document = fake_process_document
    pre_chunks = [{"text": "chunk one"}]

    async for _ in report_analyzer.process_document(
        file_path="test.pdf",
        selected_questions=[1],
        pre_retrieved_chunks=pre_chunks,
        max_processing_step="chunk",
    ):
        pass

    assert captured["pre_retrieved_chunks"] == pre_chunks
    assert captured["max_processing_step"] == "chunk"


@pytest.mark.asyncio
async def test_run_analysis_embed_failure_does_not_show_success(monkeypatch, tmp_path):
    """Regression: OpenAI embed errors must not be followed by a success banner."""
    import report_analyst.streamlit_app as app

    file_path = str(tmp_path / "embed-fail.pdf")
    progress = Mock()
    report_analyzer = Mock()
    report_analyzer.analyzer.chunk_params = {"chunk_size": 500, "chunk_overlap": 20}
    report_analyzer.cache_manager.get_document_chunks.return_value = [
        {"text": "Chunk without embedding.", "embedding": None},
    ]

    async def fake_process_document(*args, **kwargs):
        yield {"error": "Error processing document: Incorrect API key"}

    report_analyzer.process_document = fake_process_document
    monkeypatch.setattr(app, "st", Mock(session_state=make_run_analysis_session(force_recompute=True)))
    monkeypatch.setattr(app, "display_cached_document_chunks", Mock(return_value=(1, 0)))

    await app.run_analysis(
        report_analyzer,
        file_path=file_path,
        selected_questions=[],
        progress_text=progress,
        max_processing_step="embed",
    )

    progress.error.assert_called()
    progress.success.assert_not_called()
