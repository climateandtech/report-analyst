"""Tests for tiktoken fallback in LLM provider factory."""

from __future__ import annotations


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
