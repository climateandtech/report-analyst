"""
OpenRouter OAuth PKCE flow for one-click AI access.

Allows users to connect their OpenRouter account without manually copying API keys.
Uses PKCE (Proof Key for Code Exchange) for secure authorization.
"""

import base64
import hashlib
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_AUTH_URL = "https://openrouter.ai/auth"
OPENROUTER_EXCHANGE_URL = "https://openrouter.ai/api/v1/auth/keys"


def _get_state_file() -> Path:
    """Get path to OAuth state storage file."""
    storage = Path(__file__).parent.parent.parent / "storage"
    storage.mkdir(parents=True, exist_ok=True)
    return storage / "openrouter_oauth_state.json"


def _load_state() -> dict:
    """Load OAuth state from file."""
    path = _get_state_file()
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load OAuth state: {e}")
        return {}


def _save_state(data: dict) -> None:
    """Save OAuth state to file."""
    path = _get_state_file()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def generate_pkce() -> Tuple[str, str]:
    """
    Generate PKCE code_verifier and code_challenge (S256).

    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return code_verifier, code_challenge


def store_oauth_state(state: str, code_verifier: str) -> None:
    """Store OAuth state and code_verifier for callback."""
    data = _load_state()
    data[state] = {
        "code_verifier": code_verifier,
        "code_challenge_method": "S256",
    }
    _save_state(data)


def get_and_clear_oauth_state(state: str) -> Optional[dict]:
    """Retrieve and remove OAuth state. Returns None if not found."""
    data = _load_state()
    entry = data.pop(state, None)
    if entry:
        _save_state(data)
    return entry


def get_auth_url(callback_url: str) -> Tuple[str, str]:
    """
    Build OpenRouter auth URL and return (url, state).

    Caller must store state with code_verifier before redirecting user.

    Returns:
        Tuple of (auth_url, state)
    """
    state = secrets.token_urlsafe(16)
    code_verifier, code_challenge = generate_pkce()
    store_oauth_state(state, code_verifier)
    params = {
        "callback_url": callback_url,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    url = f"{OPENROUTER_AUTH_URL}?callback_url={callback_url}&code_challenge={code_challenge}&code_challenge_method=S256"
    return url, state


def exchange_code_for_key(
    code: str,
    code_verifier: str,
    code_challenge_method: str = "S256",
) -> str:
    """
    Exchange authorization code for OpenRouter API key.

    Args:
        code: Authorization code from OpenRouter callback
        code_verifier: PKCE code verifier
        code_challenge_method: Method used (S256 or plain)

    Returns:
        OpenRouter API key

    Raises:
        httpx.HTTPStatusError: On exchange failure
        ValueError: If response has no key
    """
    payload = {
        "code": code,
        "code_verifier": code_verifier,
        "code_challenge_method": code_challenge_method,
    }
    with httpx.Client() as client:
        resp = client.post(
            OPENROUTER_EXCHANGE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
    key = data.get("key")
    if not key:
        raise ValueError("OpenRouter exchange response missing 'key'")
    return key
