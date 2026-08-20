"""Tests for canonical question ID resolution in the analyzer pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.cache_manager import CacheManager


@pytest.fixture
def analyzer(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    DocumentAnalyzer.reset_instance()
    with (
        patch("llama_index.embeddings.openai.OpenAIEmbedding"),
        patch("llama_index.core.Settings"),
    ):
        inst = DocumentAnalyzer()
        inst.use_backend_llm = False
        inst.llm = Mock(model="gpt-4o-mini")
        yield inst
    DocumentAnalyzer.reset_instance()


def _with_questions(analyzer, question_set: str, questions: dict):
    analyzer.question_set = question_set
    analyzer.questions = questions
    return analyzer


class TestQuestionIdPipeline:
    def test_resolve_full_id_esrs(self, analyzer):
        _with_questions(
            analyzer,
            "esrs_e1_climate_examples",
            {"esrs_e1_climate_examples_9": {"text": "Scope 1?", "guidelines": ""}},
        )
        qid, data = analyzer.resolve_question("esrs_e1_climate_examples_9")
        assert qid == "esrs_e1_climate_examples_9"
        assert data["text"] == "Scope 1?"

    def test_resolve_full_id_everest_ev_prefix(self, analyzer):
        _with_questions(analyzer, "everest", {"ev_1": {"text": "Everest Q1", "guidelines": ""}})
        qid, _ = analyzer.resolve_question("ev_1")
        assert qid == "ev_1"

    def test_resolve_legacy_int(self, analyzer):
        _with_questions(
            analyzer,
            "tcfd",
            {"tcfd_9": {"text": "Metrics?", "guidelines": ""}},
        )
        qid, _ = analyzer.resolve_question(9)
        assert qid == "tcfd_9"

    def test_normalize_dedupes_ids_and_legacy_numbers(self, analyzer):
        _with_questions(
            analyzer,
            "tcfd",
            {
                "tcfd_1": {"text": "Q1", "guidelines": ""},
                "tcfd_9": {"text": "Q9", "guidelines": ""},
            },
        )
        assert analyzer.normalize_question_ids(["tcfd_9", "tcfd_1", 1]) == ["tcfd_9", "tcfd_1"]


@pytest.mark.asyncio
async def test_process_document_caches_by_full_question_id(analyzer, tmp_path):
    file_path = str(tmp_path / "esrs.pdf")
    clean_db = tmp_path / "cache.db"
    embedded = [
        {
            "text": "Scope 1 total 1200 tCO2e.",
            "metadata": {"page": 1},
            "embedding": np.array([0.1, 0.2], dtype=np.float32),
        }
    ]
    _with_questions(
        analyzer,
        "esrs_e1_climate_examples",
        {"esrs_e1_climate_examples_9": {"text": "Scope 1?", "guidelines": ""}},
    )
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer, "_get_similar_chunks", AsyncMock(return_value=embedded)
    ), patch.object(
        analyzer, "_analyze_chunks", AsyncMock(return_value={"ANSWER": "1200 tCO2e", "EVIDENCE": []})
    ), patch.object(
        analyzer.cache_manager, "save_analysis"
    ) as mock_save:
        async for _ in analyzer.process_document(
            file_path=file_path,
            selected_questions=["esrs_e1_climate_examples_9"],
        ):
            pass

    assert mock_save.call_args.kwargs["question_id"] == "esrs_e1_climate_examples_9"


@pytest.mark.asyncio
async def test_process_document_legacy_int_resolves_to_canonical_id(analyzer, tmp_path):
    file_path = str(tmp_path / "legacy.pdf")
    clean_db = tmp_path / "cache.db"
    embedded = [{"text": "c", "metadata": {}, "embedding": np.array([0.5], dtype=np.float32)}]
    _with_questions(analyzer, "tcfd", {"tcfd_1": {"text": "Q1", "guidelines": ""}})
    analyzer.cache_manager = CacheManager(db_path=str(clean_db))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer, "_get_similar_chunks", AsyncMock(return_value=embedded)
    ), patch.object(analyzer, "_analyze_chunks", AsyncMock(return_value={"ANSWER": "Yes", "EVIDENCE": []})), patch.object(
        analyzer.cache_manager, "save_analysis"
    ) as mock_save:
        async for _ in analyzer.process_document(
            file_path=file_path,
            selected_questions=[1],
        ):
            pass

    assert mock_save.call_args.kwargs["question_id"] == "tcfd_1"
