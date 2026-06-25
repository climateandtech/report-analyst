"""Functional contract tests — real DocumentAnalyzer init, mock only LLM/embed/network boundaries."""

from __future__ import annotations

import inspect

import pytest

from analyzer_init_helpers import (
    create_document_analyzer_via_init,
    reset_document_analyzer_singleton,
)
from report_analyst.core.api_key_manager import APIKeyManager


@pytest.fixture(autouse=True)
def _isolate_analyzer_singleton():
    reset_document_analyzer_singleton()
    yield
    reset_document_analyzer_singleton()


def test_document_analyzer_init_does_not_shadow_llm_model_name_method(monkeypatch, tmp_path):
    analyzer, _ = create_document_analyzer_via_init(monkeypatch, tmp_path)

    assert isinstance(analyzer._llm_client_model, str)
    assert callable(analyzer._llm_model_name)
    assert analyzer._llm_model_name() == analyzer._llm_client_model


def test_ensure_llm_client_without_args_after_document_analyzer_init(monkeypatch, tmp_path):
    """Regression: Answer step calls _ensure_llm_client() with no args after __init__."""
    analyzer, _ = create_document_analyzer_via_init(monkeypatch, tmp_path)

    analyzer._ensure_llm_client()


def test_ensure_llm_client_refreshes_llm_after_key_change_post_init(monkeypatch, tmp_path):
    analyzer, llm_mock = create_document_analyzer_via_init(monkeypatch, tmp_path, openai_key="sk-old-key")
    created_models: list[str] = []

    def tracking_get_llm(model_name, cache_dir=None, **kwargs):
        created_models.append(model_name)
        llm_mock.model = model_name
        return llm_mock

    monkeypatch.setattr("report_analyst.core.analyzer.get_llm", tracking_get_llm)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-new-key")

    analyzer._ensure_llm_client()

    assert created_models == ["gpt-4o-mini"]


@pytest.mark.asyncio
async def test_analyze_chunks_calls_ensure_llm_client_before_achat(monkeypatch, tmp_path):
    """Answer path must refresh LLM client before achat (not just on explicit model change)."""
    analyzer, llm_mock = create_document_analyzer_via_init(monkeypatch, tmp_path)
    ensure_calls = 0
    original_ensure = analyzer._ensure_llm_client

    def counting_ensure(model_name=None):
        nonlocal ensure_calls
        ensure_calls += 1
        return original_ensure(model_name)

    monkeypatch.setattr(analyzer, "_ensure_llm_client", counting_ensure)

    question = {"text": "What is the board role?", "guidelines": ""}
    chunks = [{"text": "Board oversees climate risks.", "metadata": {}, "score": 0.9}]

    await analyzer._analyze_chunks(question, chunks, use_llm_scoring=False)

    assert ensure_calls >= 1
    llm_mock.achat.assert_awaited_once()


def test_openai_sdk_client_uses_base_url_not_api_base():
    """Contract: installed openai.OpenAI kwargs must match APIKeyManager (base_url not api_base)."""
    from openai import OpenAI

    params = inspect.signature(OpenAI.__init__).parameters
    assert "base_url" in params
    assert "api_base" not in params


def test_openai_models_list_has_no_limit_param():
    from openai.resources.models import Models

    params = inspect.signature(Models.list).parameters
    assert "limit" not in params


def test_api_key_manager_openai_client_kwargs_match_sdk(monkeypatch):
    captured: dict = {}

    class FakePage:
        def __iter__(self):
            yield type("M", (), {"id": "gpt-4o-mini"})()

    class FakeModels:
        def list(self, **_kwargs):
            return FakePage()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.models = FakeModels()

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)
    monkeypatch.setattr("openai.AuthenticationError", Exception)
    monkeypatch.setenv("OPENAI_API_BASE", "https://example.invalid/v1")

    result = APIKeyManager.test_openai_api_key("sk-contract-test")

    assert result["ok"] is True
    assert captured["api_key"] == "sk-contract-test"
    assert captured["base_url"] == "https://example.invalid/v1"
    assert "api_base" not in captured
