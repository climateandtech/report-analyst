"""Tests for tiktoken fallback and Gemini adapter in LLM provider factory."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from report_analyst.core import llm_providers


def test_get_llm_gpt_54_mini_tokenizer_falls_back_to_o200k_base(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_TIKTOKEN_ENCODING", raising=False)

    from report_analyst.core.llm_providers import get_llm

    llm = get_llm("gpt-5.4-mini")
    assert llm._tokenizer.name == "o200k_base"


def test_get_llm_tokenizer_respects_openai_tiktoken_encoding_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_TIKTOKEN_ENCODING", "cl100k_base")

    from report_analyst.core.llm_providers import get_llm

    llm = get_llm("gpt-5.4-mini")
    assert llm._tokenizer.name == "cl100k_base"


@pytest.mark.parametrize(
    ("requested_model", "google_model"),
    [
        ("gemini-2.5-flash", "gemini-2.5-flash"),
        ("models/gemini-2.5-flash", "gemini-2.5-flash"),
    ],
)
def test_get_llm_uses_google_genai_adapter(monkeypatch, requested_model, google_model):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    google_genai = Mock()
    monkeypatch.setattr(llm_providers, "GoogleGenAI", google_genai)

    llm_providers.get_llm(requested_model, temperature=0.2)

    google_genai.assert_called_once_with(
        model=google_model,
        api_key="test-google-key",
        temperature=0.2,
    )


def test_get_llm_requires_google_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        llm_providers.get_llm("gemini-2.5-flash")
