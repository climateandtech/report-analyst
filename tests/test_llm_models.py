"""Tests for env-configurable LLM model lists."""

import pytest

import report_analyst.core.llm_models as llm_models


@pytest.fixture(autouse=True)
def _clear_model_env(monkeypatch):
    for key in ("OPENAI_MODELS", "GEMINI_MODELS", "LLM_MODELS", "OPENAI_API_MODEL", "DEFAULT_MODEL", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def test_default_openai_models_include_gpt_54():
    models = llm_models.get_openai_models()
    assert models[0] == "gpt-5.4-mini"
    assert "gpt-5.4" in models
    assert "gpt-4o-mini" in models


def test_default_gemini_models_include_latest():
    models = llm_models.get_gemini_models()
    assert models[0] == "gemini-3.5-flash"
    assert "gemini-2.5-flash" in models
    assert "gemini-1.5-flash" in models


def test_openai_models_env_override(monkeypatch):
    monkeypatch.setenv("OPENAI_MODELS", "gpt-5.4-mini,custom-model")
    assert llm_models.get_openai_models() == ["gpt-5.4-mini", "custom-model"]


def test_gemini_models_env_override(monkeypatch):
    monkeypatch.setenv("GEMINI_MODELS", "gemini-3.5-flash")
    assert llm_models.get_gemini_models() == ["gemini-3.5-flash"]


def test_llm_models_combined_env_override(monkeypatch):
    monkeypatch.setenv("LLM_MODELS", "gpt-5.4,gemini-3.5-flash")
    assert llm_models.get_llm_models(include_gemini=False) == ["gpt-5.4", "gemini-3.5-flash"]


def test_llm_models_merges_gemini_when_key_set(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    models = llm_models.get_llm_models()
    assert models[0].startswith("gpt-")
    assert any(m.startswith("gemini-") for m in models)


def test_llm_models_omits_gemini_without_key(monkeypatch):
    models = llm_models.get_llm_models()
    assert all(not m.startswith("gemini-") for m in models)


def test_default_llm_model_from_openai_api_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_MODEL", "gpt-5.4-mini")
    assert llm_models.get_default_llm_model() == "gpt-5.4-mini"


def test_default_llm_model_falls_back_to_first_list_entry(monkeypatch):
    assert llm_models.get_default_llm_model() == "gpt-5.4-mini"


def test_models_for_api_shape(monkeypatch):
    rows = llm_models.get_models_for_api(include_gemini=False)
    assert rows[0]["id"] == "gpt-5.4-mini"
    assert "GPT" in rows[0]["name"]


def test_models_for_api_respects_openai_env(monkeypatch):
    monkeypatch.setenv("OPENAI_MODELS", "gpt-5.4-mini,gpt-4o-mini")
    rows = llm_models.get_models_for_api(include_gemini=False)
    assert [row["id"] for row in rows] == ["gpt-5.4-mini", "gpt-4o-mini"]
