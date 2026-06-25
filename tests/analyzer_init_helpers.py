"""Helpers to exercise DocumentAnalyzer through real __init__ (mock only at LLM/embed boundaries)."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, Mock, patch

from report_analyst.core.analyzer import DocumentAnalyzer


def reset_document_analyzer_singleton() -> None:
    DocumentAnalyzer._instance = None
    DocumentAnalyzer._initialized = False


@contextmanager
def patched_llm_and_embedding_boundaries(llm_mock: Mock | None = None):
    """Patch get_llm and OpenAIEmbedding before DocumentAnalyzer() — no network."""
    if llm_mock is None:
        llm_mock = Mock(model="gpt-4o-mini")
        llm_mock.achat = AsyncMock(
            return_value=Mock(
                message=Mock(content='{"ANSWER":"ok","SCORE":1,"EVIDENCE":[],"GAPS":[],"SOURCES":[]}')
            )
        )

    def fake_get_llm(model_name, cache_dir=None, **kwargs):
        llm_mock.model = model_name
        return llm_mock

    with patch("llama_index.embeddings.openai.OpenAIEmbedding"), patch(
        "report_analyst.core.analyzer.get_llm", fake_get_llm
    ), patch("report_analyst.core.analyzer.IngestionCache", Mock(return_value=Mock())):
        yield llm_mock


def create_document_analyzer_via_init(monkeypatch, tmp_path, *, openai_key: str = "sk-test-init-key"):
    """Return (analyzer, llm_mock) after running DocumentAnalyzer.__init__."""
    reset_document_analyzer_singleton()
    monkeypatch.setenv("OPENAI_API_KEY", openai_key)
    monkeypatch.setenv("USE_BACKEND", "false")
    monkeypatch.setenv("USE_CENTRALIZED_LLM", "false")
    monkeypatch.setenv("USE_FULL_BACKEND_ANALYSIS", "false")

    with patched_llm_and_embedding_boundaries() as llm_mock:
        analyzer = DocumentAnalyzer()

    analyzer.llm = llm_mock
    analyzer.llm_cache_path = tmp_path / "llm_cache"
    analyzer.llm_cache_path.mkdir(parents=True, exist_ok=True)
    return analyzer, llm_mock
