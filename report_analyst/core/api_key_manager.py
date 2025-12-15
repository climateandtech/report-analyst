"""
API Key Management Service

Manages API keys in session state and environment variables without storing them persistently.
Keys are only kept in memory for the current session.
"""

import os
from typing import Optional


class APIKeyManager:
    """Service to manage API keys in session state and environment without persistence"""

    @staticmethod
    def set_api_key(key_name: str, value: Optional[str], session_state: dict) -> None:
        """
        Set an API key in session state and environment variables.

        Args:
            key_name: The environment variable name (e.g., 'OPENAI_API_KEY')
            value: The API key value (None to clear)
            session_state: Streamlit session state dictionary
        """
        # Store in session state (temporary, per session)
        session_key = f"api_key_{key_name.lower()}"
        if value:
            session_state[session_key] = value
            # Set in environment for current process
            os.environ[key_name] = value
        else:
            # Clear from session state
            if session_key in session_state:
                del session_state[session_key]
            # Remove from environment if it was set by us
            if key_name in os.environ:
                # Only remove if it was set in this session (not from .env file)
                # We can't easily track this, so we'll leave env vars that might
                # have been set externally. The session state value takes precedence.
                pass

    @staticmethod
    def get_api_key(key_name: str, session_state: dict) -> Optional[str]:
        """
        Get an API key from session state or environment.

        Priority:
        1. Session state (user-entered value)
        2. Environment variable (from .env or system)

        Args:
            key_name: The environment variable name (e.g., 'OPENAI_API_KEY')
            session_state: Streamlit session state dictionary

        Returns:
            The API key value or None
        """
        session_key = f"api_key_{key_name.lower()}"
        # Check session state first (user-entered value takes precedence)
        if session_key in session_state:
            return session_state[session_key]
        # Fall back to environment variable
        return os.getenv(key_name)

    @staticmethod
    def sync_api_keys_to_env(session_state: dict) -> None:
        """
        Sync all API keys from session state to environment variables.
        Called at startup to ensure environment has current values.

        Args:
            session_state: Streamlit session state dictionary
        """
        api_key_names = ["OPENAI_API_KEY", "GOOGLE_API_KEY"]
        for key_name in api_key_names:
            session_key = f"api_key_{key_name.lower()}"
            if session_key in session_state:
                value = session_state[session_key]
                if value:
                    os.environ[key_name] = value
