"""Embeddings client must pick up OPENAI_API_KEY changes mid-session."""

from __future__ import annotations

from report_analyst.core.analyzer import DocumentAnalyzer


class _FakeSettings:
    embed_model = None


def test_ensure_embeddings_client_refreshes_when_api_key_changes(monkeypatch):
    analyzer = object.__new__(DocumentAnalyzer)
    analyzer.embeddings = None
    analyzer._embeddings_api_key = None

    created_keys: list[str] = []

    class FakeEmbedding:
        def __init__(self, api_key=None, **kwargs):
            self.api_key = api_key
            created_keys.append(api_key)

    monkeypatch.setattr("report_analyst.core.analyzer.OpenAIEmbedding", FakeEmbedding)
    monkeypatch.setattr("report_analyst.core.analyzer.Settings", _FakeSettings)

    monkeypatch.setenv("OPENAI_API_KEY", "key-old")
    analyzer._ensure_embeddings_client()
    assert created_keys == ["key-old"]

    monkeypatch.setenv("OPENAI_API_KEY", "key-new")
    analyzer._ensure_embeddings_client()
    assert created_keys == ["key-old", "key-new"]
    assert analyzer.embeddings.api_key == "key-new"
