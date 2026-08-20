"""Extra coverage for Actwyser pipeline bugfix changed lines."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from report_analyst.core import analysis_result_utils as aru
from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.cache_manager import CacheManager
from report_analyst.core.llm_providers import _tiktoken_encoding_name_for_model


def test_result_payload_non_dict_and_nested():
    assert aru.result_payload("x") == {}
    assert aru.result_payload({"result": {"ANSWER": "a"}}) == {"ANSWER": "a"}
    assert aru.result_payload({"ANSWER": "flat"}) == {"ANSWER": "flat"}


def test_is_stored_analysis_error_branches():
    assert aru.is_stored_analysis_error(None) is False
    assert aru.is_stored_analysis_error({}) is False
    assert aru.is_stored_analysis_error({"analysis_status": "error"}) is True
    assert aru.is_stored_analysis_error({"error": "boom"}) is True


def test_analysis_error_message_prefers_error_field():
    assert aru.analysis_error_message({"error": "x"}) == "x"
    assert aru.analysis_error_message({"ANSWER": "y"}) == "y"


def test_filter_successful_analysis_results():
    results = {
        "a": {"result": {"ANSWER": "Error analyzing document: z"}},
        "b": {"result": {"ANSWER": "ok"}},
    }
    assert list(aru.filter_successful_analysis_results(results)) == ["b"]


def test_normalize_results_container_non_dict():
    assert aru.normalize_results_container(None) == {"answers": {}}
    assert aru.normalize_results_container([1]) == {"answers": {}}


def test_tiktoken_encoding_name_gpt4_and_default(monkeypatch):
    monkeypatch.delenv("OPENAI_TIKTOKEN_ENCODING", raising=False)
    assert _tiktoken_encoding_name_for_model("gpt-4-turbo") == "cl100k_base"
    assert _tiktoken_encoding_name_for_model("gpt-3.5-turbo") == "cl100k_base"
    assert _tiktoken_encoding_name_for_model("unknown-model") == "o200k_base"


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


def test_reset_singleton_if_stale_drops_old_instance():
    DocumentAnalyzer.reset_instance()
    stale = SimpleNamespace()  # missing _ensure_llm_client
    DocumentAnalyzer._instance = stale
    DocumentAnalyzer._initialized = True
    DocumentAnalyzer._reset_singleton_if_stale()
    assert DocumentAnalyzer._instance is None
    assert DocumentAnalyzer._initialized is False


def test_question_id_for_number_prefix_fallback(analyzer):
    analyzer.question_set = "climretrieve"
    analyzer.questions = {"climretr_2": {"text": "Q2", "guidelines": ""}}
    assert analyzer.question_id_for_number(2) == "climretr_2"
    assert analyzer.question_id_for_number(99) is None


def test_resolve_question_digit_string_and_missing(analyzer):
    analyzer.question_set = "tcfd"
    analyzer.questions = {"tcfd_3": {"text": "Q3", "guidelines": ""}}
    qid, data = analyzer.resolve_question("3")
    assert qid == "tcfd_3"
    assert data["text"] == "Q3"
    assert analyzer.resolve_question("missing_id") is None
    assert analyzer.resolve_question(99) is None


def test_normalize_skips_unresolved_and_reports_them(analyzer):
    analyzer.question_set = "tcfd"
    analyzer.questions = {"tcfd_1": {"text": "Q1", "guidelines": ""}}
    assert analyzer.normalize_question_ids(["nope", "tcfd_1", 1]) == ["tcfd_1"]
    assert analyzer.unresolved_question_refs(["nope", 2]) == ["nope", "2"]


def test_api_key_env_and_llm_model_name_helpers(analyzer, monkeypatch):
    with pytest.raises(ValueError, match="Unsupported model"):
        analyzer._api_key_env_for_model("claude-3")
    analyzer.llm = None
    assert analyzer._llm_model_name() == analyzer.default_model
    analyzer.use_backend_llm = True
    analyzer._ensure_llm_client("gpt-4o-mini")  # early return
    analyzer.use_backend_llm = False
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    analyzer.llm = Mock(model="gpt-4o-mini")
    analyzer._llm_api_key = "old"
    analyzer._llm_client_model = "other"
    analyzer._ensure_llm_client("gpt-4o-mini")
    assert analyzer.llm is None


def test_ensure_embeddings_client_requires_key_and_sets_client(analyzer, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="embeddings unavailable"):
        analyzer._ensure_embeddings_client()
    monkeypatch.setenv("OPENAI_API_KEY", "sk-new")
    with patch("report_analyst.core.analyzer.OpenAIEmbedding") as emb_cls, patch(
        "report_analyst.core.analyzer.Settings"
    ) as settings:
        emb_cls.return_value = Mock(name="emb")
        analyzer.embeddings = None
        analyzer._ensure_embeddings_client()
        assert analyzer.embeddings is emb_cls.return_value
        assert analyzer._embeddings_api_key == "sk-new"
        assert settings.embed_model is emb_cls.return_value


@pytest.mark.asyncio
async def test_process_document_empty_and_unresolved_selection(analyzer, tmp_path):
    file_path = str(tmp_path / "doc.pdf")
    embedded = [{"text": "c", "metadata": {}, "embedding": np.array([0.1], dtype=np.float32)}]
    analyzer.question_set = "tcfd"
    analyzer.questions = {"tcfd_1": {"text": "Q1", "guidelines": ""}}
    analyzer.cache_manager = CacheManager(db_path=str(tmp_path / "c.db"))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded):
        events = []
        async for ev in analyzer.process_document(file_path=file_path, selected_questions=[]):
            events.append(ev)
        assert any(e.get("error") == "Select at least one question to analyze." for e in events)

        events = []
        async for ev in analyzer.process_document(file_path=file_path, selected_questions=["missing"]):
            events.append(ev)
        assert any(e.get("error") == "Question missing not found" for e in events)


@pytest.mark.asyncio
async def test_process_document_resolve_none_mid_loop(analyzer, tmp_path):
    file_path = str(tmp_path / "doc.pdf")
    embedded = [{"text": "c", "metadata": {}, "embedding": np.array([0.1], dtype=np.float32)}]
    analyzer.question_set = "tcfd"
    analyzer.questions = {"tcfd_1": {"text": "Q1", "guidelines": ""}}
    analyzer.cache_manager = CacheManager(db_path=str(tmp_path / "c.db"))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer, "normalize_question_ids", return_value=["tcfd_1"]
    ), patch.object(analyzer, "unresolved_question_refs", return_value=[]), patch.object(
        analyzer, "resolve_question", return_value=None
    ):
        events = []
        async for ev in analyzer.process_document(file_path=file_path, selected_questions=["tcfd_1"]):
            events.append(ev)
        assert any(e.get("error") == "Question tcfd_1 not found" for e in events)


@pytest.mark.asyncio
async def test_score_chunk_relevance_batch_ensures_llm(analyzer):
    analyzer.llm = MagicMock()
    analyzer.llm.achat = AsyncMock(return_value=SimpleNamespace(message=SimpleNamespace(content="[1] 0.5")))
    with patch.object(analyzer, "_ensure_llm_client") as ensure:
        scores = await analyzer.score_chunk_relevance_batch("q", [{"text": "chunk"}], single_call=True)
        ensure.assert_called()
        assert isinstance(scores, list)


def test_load_questions_fallback_path(analyzer):
    """When question_loader returns no set, fall back to bundled YAML paths."""
    analyzer.question_set = "tcfd"
    mock_loader = MagicMock()
    mock_loader.get_question_set.return_value = None
    with patch(
        "report_analyst.core.question_loader.get_question_loader",
        return_value=mock_loader,
    ):
        questions = analyzer._load_questions()
        assert isinstance(questions, dict)
        assert len(questions) > 0
