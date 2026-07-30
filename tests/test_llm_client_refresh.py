"""LLM client must pick up API key changes mid-session."""

from __future__ import annotations

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
