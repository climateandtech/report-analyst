"""LLM provider module for different language model integrations."""

import logging
import os
from typing import Any, Optional

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI

# LlamaIndex LLM imports
from llama_index.llms.openai import OpenAI

# Setup logging
logger = logging.getLogger(__name__)

# One HTTP timeout is enough for embed/LLM. LlamaIndex defaults also retry
# RateLimitError 10 times, including permanent insufficient_quota (429).
OPENAI_REQUEST_TIMEOUT_SECONDS = 60.0
OPENAI_MAX_RETRIES = 0

_PERMANENT_QUOTA_CODES = frozenset({"insufficient_quota", "credit_balance_exhausted"})


def is_permanent_openai_quota_error(exc: BaseException) -> bool:
    """True for billing/quota 429s that will never succeed on retry."""
    code = getattr(exc, "code", None)
    body = getattr(exc, "body", None)
    err = body.get("error") if isinstance(body, dict) else None
    if isinstance(err, dict):
        code = code or err.get("code")
        if err.get("type") == "insufficient_quota":
            return True
    return code in _PERMANENT_QUOTA_CODES


def build_openai_embedding(
    *,
    api_key: str,
    api_base: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs: Any,
) -> OpenAIEmbedding:
    """OpenAI embeddings client that fails fast on permanent API errors."""
    embed_kwargs = {
        "api_key": api_key,
        "api_base": api_base if api_base is not None else os.getenv("OPENAI_API_BASE"),
        "model_name": model_name or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
        "embed_batch_size": 100,
        "timeout": OPENAI_REQUEST_TIMEOUT_SECONDS,
        "max_retries": OPENAI_MAX_RETRIES,
        **kwargs,
    }
    return OpenAIEmbedding(**embed_kwargs)


def get_llm(model_name: str, cache_dir: Optional[str] = None, **kwargs) -> Any:
    """
    Factory function to get LLM implementations based on model name.

    Args:
        model_name: Name of the model to use (e.g., "gpt-4o", "gemini-flash-2.0")
        cache_dir: Optional directory for LLM response caching
        **kwargs: Additional keyword arguments to pass to the LLM constructor

    Returns:
        Initialized LLM instance

    Raises:
        ValueError: If the API key for the selected model is not available
        ValueError: If the model type is not supported
    """
    # OpenAI models
    if model_name.startswith("gpt-"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error(f"Cannot initialize OpenAI model '{model_name}' - OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models")

        llm_kwargs = {
            "model": model_name,
            "api_key": api_key,
            "api_base": os.getenv("OPENAI_API_BASE"),
            "cache_dir": cache_dir,
            "timeout": OPENAI_REQUEST_TIMEOUT_SECONDS,
            "max_retries": OPENAI_MAX_RETRIES,
            **kwargs,
        }
        return OpenAI(**llm_kwargs)

    # Gemini models
    elif model_name.startswith("gemini-") or model_name.startswith("models/gemini-"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error(f"Cannot initialize Gemini model '{model_name}' - GOOGLE_API_KEY environment variable is not set")
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")

        google_model_name = model_name.removeprefix("models/")
        logger.info(f"Initializing Gemini model: {google_model_name}")
        return GoogleGenAI(model=google_model_name, api_key=api_key, **kwargs)

    else:
        logger.error(f"Unsupported model type: {model_name}")
        raise ValueError(f"Unsupported model: {model_name}")
