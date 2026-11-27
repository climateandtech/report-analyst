from unittest.mock import Mock

import pytest

from report_analyst.core import llm_providers


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


def test_get_llm_openai_uses_fail_fast_retries(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    openai_cls = Mock()
    monkeypatch.setattr(llm_providers, "OpenAI", openai_cls)

    llm_providers.get_llm("gpt-4o-mini")

    kwargs = openai_cls.call_args.kwargs
    assert kwargs["timeout"] == llm_providers.OPENAI_REQUEST_TIMEOUT_SECONDS
    assert kwargs["max_retries"] == llm_providers.OPENAI_MAX_RETRIES
