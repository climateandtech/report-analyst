"""Prove insufficient_quota is a permanent error, not a hang/retry loop."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, Mock, patch

import httpx
import numpy as np
import pytest
from openai import RateLimitError

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.cache_manager import CacheManager
from report_analyst.core.llm_providers import (
    OPENAI_MAX_RETRIES,
    OPENAI_REQUEST_TIMEOUT_SECONDS,
    build_openai_embedding,
    is_permanent_openai_quota_error,
)

QUOTA_BODY = {
    "error": {
        "message": "You have no credits remaining.",
        "type": "insufficient_quota",
        "param": None,
        "code": "credit_balance_exhausted",
    }
}


def _quota_response() -> httpx.Response:
    request = httpx.Request("POST", "https://api.openai.com/v1/embeddings")
    return httpx.Response(429, json=QUOTA_BODY, request=request)


def _quota_error() -> RateLimitError:
    response = _quota_response()
    return RateLimitError("Error code: 429", response=response, body=QUOTA_BODY)


def _count_embed_http_calls(embed_client) -> tuple[int, str]:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] > 500:
            raise AssertionError("quota 429 retried more than 500 times (unbounded)")
        return _quota_response()

    embed_client._http_client = httpx.Client(transport=httpx.MockTransport(handler))
    embed_client._client = None
    try:
        embed_client.get_text_embedding("hello")
        status = "ok"
    except AssertionError:
        raise
    except Exception as exc:  # noqa: BLE001
        status = type(exc).__name__
    return calls["n"], status


def test_is_permanent_openai_quota_error_detects_credit_balance():
    assert is_permanent_openai_quota_error(_quota_error()) is True
    assert is_permanent_openai_quota_error(RuntimeError("network down")) is False


def test_default_embedding_quota_retries_are_bounded_not_endless(monkeypatch):
    """Hypothesis: stock OpenAIEmbedding retries quota 429 a finite number of times, then raises.

    Sleep is no-op so tenacity's 60s stop-after-delay does not cut the loop.
    That yields the full nested budget (10 LlamaIndex attempts x 11 OpenAI tries).
    Real sleep still stops (measured ~22 HTTP calls in ~93s), not an infinite loop.
    """
    from llama_index.embeddings.openai import OpenAIEmbedding

    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda seconds: slept.append(float(seconds)))
    embed = OpenAIEmbedding(api_key="sk-test", timeout=5.0, reuse_client=True)
    calls, status = _count_embed_http_calls(embed)
    assert status == "RateLimitError"
    assert calls == 110
    assert len(slept) == 109
    assert sum(slept) > 0


def test_build_openai_embedding_quota_exhausted_makes_one_http_call(monkeypatch):
    """Hypothesis: our client fails on the first insufficient_quota response."""
    monkeypatch.setattr(time, "sleep", lambda *_args, **_kwargs: None)
    embed = build_openai_embedding(api_key="sk-test")
    assert embed.timeout == OPENAI_REQUEST_TIMEOUT_SECONDS
    assert embed.max_retries == OPENAI_MAX_RETRIES
    calls, status = _count_embed_http_calls(embed)
    assert status == "RateLimitError"
    assert calls == 1


@pytest.fixture
def analyzer(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("USE_BACKEND", "false")
    monkeypatch.setenv("USE_CENTRALIZED_LLM", "false")
    DocumentAnalyzer.reset_instance()
    with patch("report_analyst.core.llm_providers.build_openai_embedding"), patch(
        "report_analyst.core.llm_providers.get_llm"
    ) as mock_get_llm:
        mock_get_llm.return_value = Mock(model="gpt-4o-mini", achat=AsyncMock())
        doc_analyzer = DocumentAnalyzer()
        doc_analyzer.cache_manager = CacheManager(db_path=str(tmp_path / "quota.db"))
        doc_analyzer.llm = Mock(model="gpt-4o-mini", achat=AsyncMock())
        doc_analyzer.use_backend_llm = False
        yield doc_analyzer
        DocumentAnalyzer.reset_instance()


@pytest.mark.asyncio
async def test_process_document_map_quota_exhausted_yields_error(analyzer, tmp_path):
    """Hypothesis: Map surfaces quota errors instead of completing with empty ranks."""
    file_path = str(tmp_path / "quota-map.pdf")
    embedded = [
        {
            "text": "Scope 1 emissions disclosure.",
            "metadata": {"page": 1},
            "embedding": np.array([0.1, 0.2, 0.3], dtype=np.float32),
        }
    ]
    analyzer.embeddings = Mock()
    analyzer.embeddings.get_text_embedding.side_effect = _quota_error()
    analyzer.cache_manager = CacheManager(db_path=str(analyzer.cache_manager.db_path))

    with patch.object(analyzer.cache_manager, "get_document_chunks", return_value=embedded), patch.object(
        analyzer,
        "get_question_by_number",
        return_value={"text": "What are Scope 1 emissions?", "guidelines": ""},
    ):
        events = []
        async for event in analyzer.process_document(
            file_path,
            selected_questions=[1],
            max_processing_step="map",
        ):
            events.append(event)

    assert analyzer.embeddings.get_text_embedding.call_count == 1
    assert any("error" in event for event in events)
    assert not any("Completed Map" in event.get("status", "") for event in events)
