"""
Tests for API Key Manager service.

Tests that API keys are managed correctly in session state and environment
without being persisted to disk.
"""

import os

from report_analyst.core.api_key_manager import APIKeyManager


def test_set_and_get_api_key():
    """Test setting and getting API keys"""
    session_state = {}

    # Set an API key
    APIKeyManager.set_api_key("OPENAI_API_KEY", "test-key-123", session_state)

    # Verify it's in session state
    assert session_state["api_key_openai_api_key"] == "test-key-123"

    # Verify it's in environment
    assert os.getenv("OPENAI_API_KEY") == "test-key-123"

    # Get the key back
    retrieved_key = APIKeyManager.get_api_key("OPENAI_API_KEY", session_state)
    assert retrieved_key == "test-key-123"


def test_get_api_key_from_env():
    """Test getting API key from environment when not in session state"""
    session_state = {}

    # Set in environment directly
    os.environ["OPENAI_API_KEY"] = "env-key-456"

    # Get should retrieve from environment
    retrieved_key = APIKeyManager.get_api_key("OPENAI_API_KEY", session_state)
    assert retrieved_key == "env-key-456"

    # Clean up
    del os.environ["OPENAI_API_KEY"]


def test_session_state_takes_precedence():
    """Test that session state value takes precedence over environment"""
    session_state = {}

    # Set in environment
    os.environ["OPENAI_API_KEY"] = "env-key-789"

    # Set in session state
    APIKeyManager.set_api_key("OPENAI_API_KEY", "session-key-789", session_state)

    # Get should return session state value
    retrieved_key = APIKeyManager.get_api_key("OPENAI_API_KEY", session_state)
    assert retrieved_key == "session-key-789"

    # Clean up
    del os.environ["OPENAI_API_KEY"]


def test_clear_api_key():
    """Test clearing an API key"""
    session_state = {}

    # Set a key
    APIKeyManager.set_api_key("OPENAI_API_KEY", "test-key-clear", session_state)
    assert session_state["api_key_openai_api_key"] == "test-key-clear"

    # Clear it
    APIKeyManager.set_api_key("OPENAI_API_KEY", None, session_state)

    # Should be removed from session state
    assert "api_key_openai_api_key" not in session_state


def test_sync_api_keys_to_env():
    """Test syncing API keys from session state to environment"""
    session_state = {
        "api_key_openai_api_key": "synced-openai-key",
        "api_key_google_api_key": "synced-google-key",
    }

    # Sync to environment
    APIKeyManager.sync_api_keys_to_env(session_state)

    # Verify they're in environment
    assert os.getenv("OPENAI_API_KEY") == "synced-openai-key"
    assert os.getenv("GOOGLE_API_KEY") == "synced-google-key"

    # Clean up
    del os.environ["OPENAI_API_KEY"]
    del os.environ["GOOGLE_API_KEY"]


def test_sync_only_existing_keys():
    """Test that sync only affects keys in session state"""
    session_state = {"api_key_openai_api_key": "only-openai-key"}

    # Set a Google key in environment
    os.environ["GOOGLE_API_KEY"] = "existing-google-key"

    # Sync
    APIKeyManager.sync_api_keys_to_env(session_state)

    # OpenAI should be synced
    assert os.getenv("OPENAI_API_KEY") == "only-openai-key"

    # Google should remain unchanged (not in session state)
    assert os.getenv("GOOGLE_API_KEY") == "existing-google-key"

    # Clean up
    del os.environ["OPENAI_API_KEY"]
    del os.environ["GOOGLE_API_KEY"]


def test_api_key_is_used_by_llm_provider():
    """Test that API key set via APIKeyManager is actually used by LLM providers"""
    import report_analyst.core.llm_providers as llm_module

    session_state = {}
    test_openai_key = "test-openai-key-12345"
    test_google_key = "test-google-key-67890"

    # Set keys via APIKeyManager
    APIKeyManager.set_api_key("OPENAI_API_KEY", test_openai_key, session_state)
    APIKeyManager.set_api_key("GOOGLE_API_KEY", test_google_key, session_state)

    # Verify keys are in environment
    assert os.getenv("OPENAI_API_KEY") == test_openai_key
    assert os.getenv("GOOGLE_API_KEY") == test_google_key

    # Verify that get_llm reads from os.getenv (which now has our key)
    # We can't actually initialize the LLM without a real key, but we can verify
    # that the function will use the key we set
    original_getenv = llm_module.os.getenv

    # Track what keys are accessed
    accessed_keys = []

    def tracking_getenv(key, default=None):
        if key in ["OPENAI_API_KEY", "GOOGLE_API_KEY"]:
            accessed_keys.append(key)
        return original_getenv(key, default)

    # Temporarily replace os.getenv in the module
    llm_module.os.getenv = tracking_getenv

    try:
        # Try to get an OpenAI LLM (will fail without real key, but we can check it reads the env)
        try:
            from report_analyst.core.llm_providers import get_llm

            get_llm("gpt-4o-mini")
        except (ValueError, Exception):
            # Expected to fail, but we check that it tried to read OPENAI_API_KEY
            pass

        # Verify it tried to read the API key from environment
        assert "OPENAI_API_KEY" in accessed_keys, "get_llm should read OPENAI_API_KEY from environment"
    finally:
        # Restore original
        llm_module.os.getenv = original_getenv

    # Clean up
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]


def test_api_key_from_session_state_overrides_env():
    """Test that API key in session state overrides environment variable for LLM"""
    session_state = {}

    # Set key in environment
    os.environ["OPENAI_API_KEY"] = "env-key-111"

    # Set different key in session state
    APIKeyManager.set_api_key("OPENAI_API_KEY", "session-key-222", session_state)

    # Environment should now have session state value
    assert os.getenv("OPENAI_API_KEY") == "session-key-222"

    # Get should return session state value
    retrieved = APIKeyManager.get_api_key("OPENAI_API_KEY", session_state)
    assert retrieved == "session-key-222"

    # Clean up
    del os.environ["OPENAI_API_KEY"]
