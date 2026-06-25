"""LLM client must pick up API key changes mid-session."""

from __future__ import annotations

from analyzer_init_helpers import create_document_analyzer_via_init, reset_document_analyzer_singleton
from report_analyst.core.analyzer import DocumentAnalyzer


def _bare_analyzer(tmp_path, **attrs) -> DocumentAnalyzer:
    analyzer = object.__new__(DocumentAnalyzer)
    analyzer.use_backend_llm = False
    analyzer.llm_cache_path = tmp_path / "llm_cache"
    analyzer.default_model = "gpt-4o-mini"
    analyzer.llm = None
    analyzer._llm_api_key = None
    analyzer._llm_client_model = None
    for key, value in attrs.items():
        setattr(analyzer, key, value)
    return analyzer


def test_ensure_llm_client_refreshes_when_openai_api_key_changes(monkeypatch, tmp_path):
    analyzer = _bare_analyzer(tmp_path)
    created: list[tuple[str, str | None]] = []

    def fake_get_llm(model_name, cache_dir=None, **kwargs):
        import os

        created.append((model_name, os.getenv("OPENAI_API_KEY")))
        return type("LLM", (), {"model": model_name})()

    monkeypatch.setattr("report_analyst.core.analyzer.get_llm", fake_get_llm)

    monkeypatch.setenv("OPENAI_API_KEY", "openai-old")
    analyzer._ensure_llm_client("gpt-4o-mini")
    assert created == [("gpt-4o-mini", "openai-old")]

    monkeypatch.setenv("OPENAI_API_KEY", "openai-new")
    analyzer._ensure_llm_client("gpt-4o-mini")
    assert created == [("gpt-4o-mini", "openai-old"), ("gpt-4o-mini", "openai-new")]


def test_ensure_llm_client_refreshes_when_google_api_key_changes(monkeypatch, tmp_path):
    analyzer = _bare_analyzer(tmp_path)
    created: list[tuple[str, str | None]] = []

    def fake_get_llm(model_name, cache_dir=None, **kwargs):
        import os

        key = os.getenv("GOOGLE_API_KEY") if model_name.startswith("gemini-") else os.getenv("OPENAI_API_KEY")
        created.append((model_name, key))
        return type("LLM", (), {"model": model_name})()

    monkeypatch.setattr("report_analyst.core.analyzer.get_llm", fake_get_llm)

    monkeypatch.setenv("GOOGLE_API_KEY", "google-old")
    analyzer._ensure_llm_client("gemini-2.0-flash")
    assert created == [("gemini-2.0-flash", "google-old")]

    monkeypatch.setenv("GOOGLE_API_KEY", "google-new")
    analyzer._ensure_llm_client("gemini-2.0-flash")
    assert created == [("gemini-2.0-flash", "google-old"), ("gemini-2.0-flash", "google-new")]


def test_ensure_llm_client_without_args_after_init_cache(monkeypatch, tmp_path):
    """Regression: cached model attr must not shadow _llm_model_name() method."""
    analyzer, _ = create_document_analyzer_via_init(monkeypatch, tmp_path)
    analyzer._ensure_llm_client()


def test_ensure_llm_client_without_args_after_bare_init_cache(monkeypatch, tmp_path):
    """Bare-object setup still documents the shadowing invariant when init is bypassed."""
    analyzer = _bare_analyzer(tmp_path)
    analyzer.llm = type("LLM", (), {"model": "gpt-4o-mini"})()
    analyzer._llm_client_model = "gpt-4o-mini"
    analyzer._llm_api_key = "sk-test"

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(
        "report_analyst.core.analyzer.get_llm",
        lambda model_name, cache_dir=None, **kwargs: type("LLM", (), {"model": model_name})(),
    )

    analyzer._ensure_llm_client()


def test_singleton_resets_when_instance_predates_ensure_llm_client():
    reset_document_analyzer_singleton()
    DocumentAnalyzer._instance = object.__new__(DocumentAnalyzer)
    DocumentAnalyzer._initialized = True

    fresh = DocumentAnalyzer()

    assert hasattr(fresh, "_ensure_llm_client")
    assert DocumentAnalyzer._instance is fresh
    reset_document_analyzer_singleton()


def test_update_llm_model_delegates_to_ensure_llm_client(monkeypatch, tmp_path):
    analyzer = _bare_analyzer(tmp_path)
    calls: list[str] = []

    def fake_ensure(model_name=None):
        calls.append(model_name)

    monkeypatch.setattr(analyzer, "_ensure_llm_client", fake_ensure)
    analyzer.update_llm_model("gpt-4o")
    assert calls == ["gpt-4o"]
