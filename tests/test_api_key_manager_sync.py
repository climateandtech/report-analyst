"""Session API key overrides must reach os.environ before client refresh."""

from __future__ import annotations

from report_analyst.core.api_key_manager import APIKeyManager


def test_sync_api_keys_to_env_applies_session_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    session_state = {"api_key_openai_api_key": "session-key"}

    APIKeyManager.sync_api_keys_to_env(session_state)

    assert __import__("os").getenv("OPENAI_API_KEY") == "session-key"
    assert APIKeyManager.get_api_key("OPENAI_API_KEY", session_state) == "session-key"
