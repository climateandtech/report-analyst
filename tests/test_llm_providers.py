"""Tests for LLM provider factory and LlamaIndex model registration."""

from __future__ import annotations

import pytest


def test_llamaindex_rejects_unregistered_model_name():
    """Document root cause: LlamaIndex whitelist lags OpenAI API model IDs."""
    from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS, openai_modelname_to_contextsize

    model = "gpt-9.9-unregistered-test-model"
    ALL_AVAILABLE_MODELS.pop(model, None)
    with pytest.raises(ValueError, match=f"Unknown model '{model}'"):
        openai_modelname_to_contextsize(model)


def test_ensure_openai_model_registered_allows_gpt_54_mini_metadata():
    from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS, openai_modelname_to_contextsize

    from report_analyst.core.llm_providers import _ensure_openai_model_registered

    prior = ALL_AVAILABLE_MODELS.pop("gpt-5.4-mini", None)
    try:
        _ensure_openai_model_registered("gpt-5.4-mini")
        assert openai_modelname_to_contextsize("gpt-5.4-mini") == 128000
    finally:
        if prior is not None:
            ALL_AVAILABLE_MODELS["gpt-5.4-mini"] = prior
        else:
            ALL_AVAILABLE_MODELS.pop("gpt-5.4-mini", None)


def test_get_llm_gpt_54_mini_exposes_metadata_without_unknown_model_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("USE_BACKEND", raising=False)
    monkeypatch.delenv("USE_CENTRALIZED_LLM", raising=False)

    from report_analyst.core.llm_providers import get_llm

    llm = get_llm("gpt-5.4-mini")
    assert llm.metadata.context_window == 128000


def test_get_openai_models_registers_env_models(monkeypatch):
    """Hypothesis: OPENAI_MODELS entries must be in LlamaIndex whitelist before use."""
    monkeypatch.setenv("OPENAI_MODELS", "gpt-env-registry-test-model")
    from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS, openai_modelname_to_contextsize

    model_id = "gpt-env-registry-test-model"
    ALL_AVAILABLE_MODELS.pop(model_id, None)

    import report_analyst.core.llm_models as llm_models

    assert llm_models.get_openai_models() == [model_id]
    assert openai_modelname_to_contextsize(model_id) == 128000


def test_get_openai_models_registers_default_gpt_54_mini(monkeypatch):
    from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS, openai_modelname_to_contextsize

    ALL_AVAILABLE_MODELS.pop("gpt-5.4-mini", None)

    import report_analyst.core.llm_models as llm_models

    llm_models.get_openai_models()
    assert openai_modelname_to_contextsize("gpt-5.4-mini") == 128000


def test_get_default_llm_model_registers_openai_api_model_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_MODEL", "gpt-env-default-selection-model")
    from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS, openai_modelname_to_contextsize

    model_id = "gpt-env-default-selection-model"
    ALL_AVAILABLE_MODELS.pop(model_id, None)

    import report_analyst.core.llm_models as llm_models

    assert llm_models.get_default_llm_model() == model_id
    assert openai_modelname_to_contextsize(model_id) == 128000


def test_get_llm_respects_openai_model_context_window_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL_CONTEXT_WINDOW", "200000")
    monkeypatch.delenv("USE_BACKEND", raising=False)

    from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS

    from report_analyst.core.llm_providers import get_llm

    model_id = "gpt-5.4-custom-test-model"
    ALL_AVAILABLE_MODELS.pop(model_id, None)
    try:
        llm = get_llm(model_id)
        assert llm.metadata.context_window == 200000
    finally:
        ALL_AVAILABLE_MODELS.pop(model_id, None)
