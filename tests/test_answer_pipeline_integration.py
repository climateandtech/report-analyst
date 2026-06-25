"""Answer pipeline integration — real DocumentAnalyzer + CacheManager, stub LLM/API only."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from analyzer_init_helpers import create_document_analyzer_via_init, reset_document_analyzer_singleton
from report_analyst.core.cache_manager import CacheManager


@pytest.fixture(scope="session")
def _integration_db_template():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "analysis_template.db"
    CacheManager(str(db_path))
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def integration_db(_integration_db_template):
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / f"analysis_{uuid.uuid4().hex}.db"
    shutil.copy2(_integration_db_template, db_path)
    yield db_path
    shutil.rmtree(temp_dir)


def _analysis_config(model: str = "gpt-4o-mini") -> dict:
    return {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": model,
        "question_set": "tcfd",
    }


async def _collect_events(analyzer, **kwargs):
    events = []
    async for event in analyzer.process_document(**kwargs):
        events.append(event)
    return events


@pytest.fixture(autouse=True)
def _reset_singleton():
    reset_document_analyzer_singleton()
    yield
    reset_document_analyzer_singleton()


@pytest.mark.asyncio
async def test_answer_pipeline_persists_llm_result_when_achat_succeeds(monkeypatch, tmp_path, integration_db):
    analyzer, llm_mock = create_document_analyzer_via_init(monkeypatch, tmp_path)
    analyzer.cache_manager = CacheManager(db_path=str(integration_db))
    analyzer.llm = llm_mock

    file_path = str(tmp_path / "report.pdf")
    chunks = [
        {
            "text": "The board oversees climate-related risks.",
            "metadata": {"page": 1},
            "embedding": np.array([0.7, 0.8], dtype=np.float32),
        }
    ]
    analyzer.cache_manager.save_document_chunks(
        file_path=file_path,
        chunks=chunks,
        chunk_size=500,
        chunk_overlap=20,
    )

    llm_mock.achat = AsyncMock(
        return_value=Mock(
            message=Mock(
                content='{"ANSWER":"Board provides oversight.","SCORE":0.9,"EVIDENCE":[],"GAPS":[],"SOURCES":[]}'
            )
        )
    )

    with patch.object(
        analyzer,
        "get_question_by_number",
        return_value={"text": "How does the board oversee climate-related risks?", "guidelines": ""},
    ):
        events = await _collect_events(
            analyzer,
            file_path=file_path,
            selected_questions=[1],
            max_processing_step="answer",
            force_recompute=True,
        )

    assert any(e.get("question_number") == 1 for e in events)
    assert not any("error" in e for e in events)

    config = _analysis_config()
    cached = analyzer.cache_manager.get_analysis(file_path, config, question_ids=["tcfd_1"])
    assert "tcfd_1" in cached
    assert cached["tcfd_1"]["result"]["ANSWER"] == "Board provides oversight."
    assert not cached["tcfd_1"]["result"]["ANSWER"].startswith("Error analyzing document:")


@pytest.mark.asyncio
async def test_answer_pipeline_does_not_persist_when_achat_raises(monkeypatch, tmp_path, integration_db):
    analyzer, llm_mock = create_document_analyzer_via_init(monkeypatch, tmp_path)
    analyzer.cache_manager = CacheManager(db_path=str(integration_db))
    analyzer.llm = llm_mock

    file_path = str(tmp_path / "report.pdf")
    chunks = [
        {
            "text": "Evidence paragraph.",
            "metadata": {"page": 2},
            "embedding": np.array([0.3, 0.4], dtype=np.float32),
        }
    ]
    analyzer.cache_manager.save_document_chunks(
        file_path=file_path,
        chunks=chunks,
        chunk_size=500,
        chunk_overlap=20,
    )

    llm_mock.achat = AsyncMock(side_effect=TypeError("'str' object is not callable"))

    with patch.object(
        analyzer,
        "get_question_by_number",
        return_value={"text": "Board oversight?", "guidelines": ""},
    ):
        events = await _collect_events(
            analyzer,
            file_path=file_path,
            selected_questions=[1],
            max_processing_step="answer",
            force_recompute=True,
        )

    assert any("error" in e for e in events)
    cached = analyzer.cache_manager.get_analysis(file_path, _analysis_config(), question_ids=["tcfd_1"])
    assert cached == {}


@pytest.mark.asyncio
async def test_ensure_llm_client_after_real_init_does_not_shadow_method(monkeypatch, tmp_path):
    """Regression: real __init__ + no-arg _ensure_llm_client (Answer path)."""
    analyzer, _ = create_document_analyzer_via_init(monkeypatch, tmp_path)
    assert callable(analyzer._llm_model_name)
    analyzer._ensure_llm_client()
