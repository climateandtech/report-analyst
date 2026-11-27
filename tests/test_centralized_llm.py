"""Centralized LLM mode: fail-closed local OpenAI, NATS adapter for .achat()."""

from __future__ import annotations

import asyncio
import builtins
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Minimal stubs so we can test llm_providers / adapter without full DocumentAnalyzer import chain
if "nats" not in sys.modules:
    sys.modules["nats"] = MagicMock()


@pytest.fixture
def centralized_env(monkeypatch):
    monkeypatch.setenv("USE_BACKEND", "true")
    monkeypatch.setenv("USE_CENTRALIZED_LLM", "true")
    monkeypatch.setenv("USE_FULL_BACKEND_ANALYSIS", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_get_llm_fails_closed_when_centralized(centralized_env):
    """Hypothesis: get_llm() must not build OpenAI client in centralized mode."""
    from report_analyst.core.llm_providers import get_llm

    with pytest.raises(RuntimeError, match="Centralized LLM"):
        get_llm("gpt-4o-mini")


@pytest.mark.asyncio
async def test_nats_llm_adapter_achat_uses_per_request_reply_subject():
    """Hypothesis: adapter waits on llm.response.{request_id}, not broadcast llm.response."""
    pytest.importorskip("llama_index.core")
    from report_analyst_enterprise.nats_llm_adapter import NATSLLMChatAdapter

    request_id_holder = []

    mock_nc = MagicMock()
    mock_js = MagicMock()
    mock_nc.jetstream.return_value = mock_js
    mock_nc.is_connected = True
    mock_nc.drain = AsyncMock()
    mock_nc.close = AsyncMock()

    async def fake_subscribe(subject, cb=None):
        async def deliver():
            if cb and subject.startswith("llm.response."):
                rid = subject.split(".", 2)[-1]
                request_id_holder.append(rid)
                msg = MagicMock()
                msg.data = json.dumps(
                    {
                        "request_id": rid,
                        "response": "platform says hi",
                        "error": None,
                    }
                ).encode()
                await cb(msg)

        asyncio.get_event_loop().call_soon(lambda: asyncio.create_task(deliver()))
        sub_mock = MagicMock()
        sub_mock.unsubscribe = AsyncMock()
        return sub_mock

    mock_nc.subscribe = AsyncMock(side_effect=fake_subscribe)
    mock_js.publish = AsyncMock()

    adapter = NATSLLMChatAdapter(model="gemma3-4b", nats_url="nats://localhost:4222")
    adapter._nc = mock_nc

    response = await adapter.achat(prompt="Hello")
    assert response.message.content == "platform says hi"
    assert request_id_holder
    publish_args = mock_js.publish.call_args
    assert publish_args[0][0] == "llm.request"
    payload = json.loads(publish_args[0][1].decode())
    assert payload["reply_subject"] == f"llm.response.{payload['request_id']}"
    assert payload["id"] == payload["request_id"]


def test_document_analyzer_centralized_initializes_embeddings(monkeypatch):
    """Centralized LLM uses NATS for chat; embeddings stay on local OpenAI for retrieval."""
    from report_analyst.core.analyzer import DocumentAnalyzer

    monkeypatch.setenv("USE_BACKEND", "true")
    monkeypatch.setenv("USE_CENTRALIZED_LLM", "true")
    monkeypatch.setenv("USE_FULL_BACKEND_ANALYSIS", "false")
    DocumentAnalyzer.reset_instance()

    with patch("report_analyst_enterprise.nats_llm_adapter.NATSLLMChatAdapter") as nats_cls:
        nats_cls.return_value = MagicMock(name="NATSLLM")
        with patch.object(DocumentAnalyzer, "_initialize_embeddings_client") as emb_init:
            analyzer = DocumentAnalyzer()

    assert analyzer.llm is nats_cls.return_value
    emb_init.assert_called_once()


def test_initialize_embeddings_client_without_key(monkeypatch):
    """Centralized mode without OPENAI_API_KEY keeps embeddings unset."""
    from report_analyst.core.analyzer import DocumentAnalyzer
    from report_analyst.core.api_key_manager import APIKeyManager

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    analyzer = DocumentAnalyzer.__new__(DocumentAnalyzer)
    with patch.object(APIKeyManager, "is_configured_key", return_value=False):
        analyzer._initialize_embeddings_client()
    assert analyzer.embeddings is None


def test_centralized_missing_enterprise_package_raises(monkeypatch):
    """Missing enterprise extra fails fast with a clear import error."""
    from report_analyst.core.analyzer import DocumentAnalyzer

    monkeypatch.setenv("USE_BACKEND", "true")
    monkeypatch.setenv("USE_CENTRALIZED_LLM", "true")
    monkeypatch.setenv("USE_FULL_BACKEND_ANALYSIS", "false")
    DocumentAnalyzer.reset_instance()
    original_import = builtins.__import__

    def block_enterprise(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "report_analyst_enterprise.nats_llm_adapter" or (
            name == "report_analyst_enterprise" and fromlist and "nats_llm_adapter" in fromlist
        ):
            raise ImportError("enterprise missing")
        return original_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=block_enterprise):
        with pytest.raises(ImportError, match="enterprise package"):
            DocumentAnalyzer()
