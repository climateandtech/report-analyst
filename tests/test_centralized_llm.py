"""Centralized LLM mode: fail-closed local OpenAI, NATS adapter for .achat()."""

from __future__ import annotations

import asyncio
import json
import sys
from unittest.mock import AsyncMock, MagicMock

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
    from report_analyst.core.nats_llm_adapter import NATSLLMChatAdapter

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
        sub = MagicMock()
        sub.unsubscribe = AsyncMock()
        return sub

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
