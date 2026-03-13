"""LLM provider module for different language model integrations."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from llama_index.llms.gemini import Gemini

# LlamaIndex LLM imports
from llama_index.llms.openai import OpenAI

# Setup logging
logger = logging.getLogger(__name__)

# OpenRouter API base - used when OPENAI_API_BASE points to OpenRouter
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


def _is_openrouter() -> bool:
    """Check if we're using OpenRouter (via api_base or explicit flag)."""
    api_base = os.getenv("OPENAI_API_BASE")
    use_openrouter = os.getenv("USE_OPENROUTER_OAUTH", "false").lower() == "true"
    return use_openrouter or (api_base and "openrouter.ai" in api_base)


def get_llm(model_name: str, cache_dir: Optional[str] = None, **kwargs) -> Any:
    """
    Factory function to get LLM implementations based on model name.

    Args:
        model_name: Name of the model to use (e.g., "gpt-4o", "openai/gpt-4o-mini")
        cache_dir: Optional directory for LLM response caching
        **kwargs: Additional keyword arguments to pass to the LLM constructor

    Returns:
        Initialized LLM instance

    Raises:
        ValueError: If the API key for the selected model is not available
        ValueError: If the model type is not supported
    """
    # OpenRouter: uses OpenAI-compatible API with openrouter.ai base
    if _is_openrouter():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error(
                f"Cannot initialize OpenRouter model '{model_name}' - " "OPENAI_API_KEY not set (connect via OpenRouter OAuth)"
            )
            raise ValueError("Connect OpenRouter to get AI access. No API key available.")
        api_base = os.getenv("OPENAI_API_BASE", OPENROUTER_API_BASE)
        # OpenRouter model IDs: openai/gpt-4o-mini, anthropic/claude-3-haiku, etc.
        if not model_name.startswith(("openai/", "anthropic/", "google/", "meta/")):
            openrouter_model = f"openai/{model_name}" if "gpt" in model_name else model_name
        else:
            openrouter_model = model_name
        return OpenAI(
            model=openrouter_model,
            api_key=api_key,
            api_base=api_base,
            cache_dir=cache_dir,
            **kwargs,
        )

    # OpenAI models (direct)
    if model_name.startswith("gpt-"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error(f"Cannot initialize OpenAI model '{model_name}' - OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models")

        return OpenAI(
            model=model_name,
            api_key=api_key,
            api_base=os.getenv("OPENAI_API_BASE"),
            cache_dir=cache_dir,
            **kwargs,
        )

    # Gemini models
    elif model_name.startswith("gemini-") or model_name.startswith("models/gemini-"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error(f"Cannot initialize Gemini model '{model_name}' - GOOGLE_API_KEY environment variable is not set")
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")

        # Use the full model path if provided, otherwise prefix with "models/"
        full_model_name = model_name
        if not model_name.startswith("models/"):
            full_model_name = f"models/{model_name}"

        logger.info(f"Initializing Gemini model: {full_model_name}")
        return Gemini(model=full_model_name, api_key=api_key, **kwargs)

    else:
        logger.error(f"Unsupported model type: {model_name}")
        raise ValueError(f"Unsupported model: {model_name}")
