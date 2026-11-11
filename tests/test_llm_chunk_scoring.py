"""Unit tests for LLM chunk relevance scoring.

Hypothesis: score_chunk_relevance / score_chunk_relevance_batch must call
``llm.achat(messages=[ChatMessage, ...])`` the same way analysis does.
Calling ``achat(prompt=...)`` matches neither LlamaIndex OpenAI nor a
messages-only stub, so production silently returns 0.0 for every chunk.
"""

from __future__ import annotations

from typing import Any, List, Sequence
from unittest.mock import Mock

import pytest
from llama_index.core.llms import ChatMessage, MessageRole

from report_analyst.core.analyzer import DocumentAnalyzer


class MessagesOnlyLLM:
    """Stand-in for LlamaIndex OpenAI: ``achat`` requires ``messages``."""

    model = "gpt-4o-mini-test"

    def __init__(self, content: str = "0.85"):
        self.content = content
        self.calls: List[dict[str, Any]] = []

    async def achat(self, messages: Sequence[ChatMessage], **kwargs: Any):
        if "prompt" in kwargs:
            raise TypeError("missing a required argument: 'messages'")
        if messages is None:
            raise TypeError("missing a required argument: 'messages'")
        self.calls.append({"messages": list(messages), "kwargs": kwargs})
        return Mock(message=Mock(content=self.content))


@pytest.fixture
def scoring_analyzer(tmp_path, monkeypatch):
    """Minimal DocumentAnalyzer with local storage and no real API keys."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_MODEL", "gpt-4o-mini")
    DocumentAnalyzer.reset_instance()
    analyzer = DocumentAnalyzer()
    analyzer.storage_path = tmp_path / "storage"
    analyzer.cache_path = analyzer.storage_path / "cache"
    analyzer.llm_cache_path = analyzer.storage_path / "llm_cache"
    analyzer.storage_path.mkdir(parents=True, exist_ok=True)
    analyzer.cache_path.mkdir(parents=True, exist_ok=True)
    analyzer.llm_cache_path.mkdir(parents=True, exist_ok=True)
    analyzer.llm = MessagesOnlyLLM("0.85")
    yield analyzer
    DocumentAnalyzer.reset_instance()


@pytest.mark.asyncio
async def test_score_chunk_relevance_requires_achat_messages(scoring_analyzer):
    """Failing on main: achat(prompt=...) is swallowed and returns 0.0."""
    score = await scoring_analyzer.score_chunk_relevance(
        "What GHG targets does the organisation disclose?",
        "Intensity target of 0.13 t CO2e per ton by 2035.",
    )
    assert score == pytest.approx(0.85)
    assert scoring_analyzer.llm.calls, "expected achat to be invoked"
    messages = scoring_analyzer.llm.calls[0]["messages"]
    assert all(isinstance(m, ChatMessage) for m in messages)
    assert messages[0].role in {MessageRole.SYSTEM, MessageRole.USER}


@pytest.mark.asyncio
async def test_score_chunk_relevance_batch_requires_achat_messages(scoring_analyzer):
    """Failing on main: batch scoring also uses achat(prompt=...)."""
    scoring_analyzer.llm = MessagesOnlyLLM("0.9\n0.2")
    chunks = [
        {"text": "0.13 t CO2e/t by 2035 with interim 0.17 by 2030."},
        {"text": "The board meets quarterly to discuss strategy."},
    ]
    scores = await scoring_analyzer.score_chunk_relevance_batch(
        "What GHG targets does the organisation disclose?",
        chunks,
        single_call=True,
    )
    assert scores == pytest.approx([0.9, 0.2])
    messages = scoring_analyzer.llm.calls[0]["messages"]
    joined = "\n".join(m.content for m in messages)
    assert "[CHUNK 1]" in joined
    assert "[CHUNK 2]" in joined


@pytest.mark.asyncio
async def test_score_chunk_relevance_must_not_accept_silent_zero(scoring_analyzer):
    """Replace the weak 0<=score<=1 assertion that greenlit the bug."""
    scoring_analyzer.llm = MessagesOnlyLLM("0.72")
    score = await scoring_analyzer.score_chunk_relevance("q?", "specific metric 42%")
    assert score == pytest.approx(0.72)


@pytest.mark.asyncio
async def test_analyze_chunks_passes_llm_score_into_prompt(scoring_analyzer):
    """Hypothesis: answer prompt must show llm_score as relevance, not always 0.0."""
    captured: dict[str, Any] = {}

    async def fake_achat(messages, **kwargs):
        captured["messages"] = messages
        return Mock(
            message=Mock(
                content=(
                    '{"ANSWER":"ok","SCORE":"5","EVIDENCE":[{"text":"e","chunk":1}],'
                    '"GAPS":[],"SOURCES":[1]}'
                )
            )
        )

    scoring_analyzer.llm = Mock(model="gpt-4o-mini-test")
    scoring_analyzer.llm.achat = fake_achat
    question = {"text": "What targets?", "guidelines": "- Focus on targets"}
    chunks = [
        {"text": "0.13 t CO2e by 2035", "score": 0.79, "llm_score": 1.0, "metadata": {}},
        {"text": "index table page 212", "score": 0.81, "llm_score": 0.2, "metadata": {}},
    ]
    await scoring_analyzer._analyze_chunks(question, chunks, use_llm_scoring=True)
    content = "\n".join(m.content for m in captured["messages"] if hasattr(m, "content"))
    assert "Relevance Score: 1.000" in content
    assert "Relevance Score: 0.200" in content
