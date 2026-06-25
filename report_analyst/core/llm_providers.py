"""LLM provider module for different language model integrations."""

import logging
import os
from collections.abc import Iterable
from typing import Any, Optional

import tiktoken
from llama_index.llms.gemini import Gemini

# LlamaIndex LLM imports
from llama_index.llms.openai import OpenAI

# Setup logging
logger = logging.getLogger(__name__)


def _tiktoken_encoding_name_for_model(model_name: str) -> str:
    """Resolve a tiktoken encoding when ``encoding_for_model`` has no catalog entry."""
    explicit = os.getenv("OPENAI_TIKTOKEN_ENCODING", "").strip()
    if explicit:
        return explicit

    lowered = model_name.lower()
    if lowered.startswith("gpt-5") or "4o" in lowered:
        return "o200k_base"
    if lowered.startswith("gpt-4") or lowered.startswith("gpt-3.5"):
        return "cl100k_base"
    return "o200k_base"


def _tiktoken_encoding_for_model(model_name: str) -> tiktoken.Encoding:
    """Return tiktoken encoding for an OpenAI model ID, with fallback for new IDs."""
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding_name = _tiktoken_encoding_name_for_model(model_name)
        logger.warning(
            "tiktoken has no mapping for %r; using %s (override via OPENAI_TIKTOKEN_ENCODING)",
            model_name,
            encoding_name,
        )
        return tiktoken.get_encoding(encoding_name)


class ReportAnalystOpenAI(OpenAI):
    """OpenAI LLM with tiktoken fallback for model IDs ahead of tiktoken releases."""

    @property
    def _tokenizer(self) -> tiktoken.Encoding:
        return _tiktoken_encoding_for_model(self._get_model_name())


def _ensure_openai_model_registered(model_name: str) -> None:
    """Register one OpenAI model ID with LlamaIndex when absent from its whitelist."""
    try:
        from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS
    except ImportError:
        return

    if model_name in ALL_AVAILABLE_MODELS:
        return

    context_window = int(os.getenv("OPENAI_MODEL_CONTEXT_WINDOW", "128000"))
    ALL_AVAILABLE_MODELS[model_name] = context_window
    logger.info(
        "Registered OpenAI model %r with LlamaIndex (context_window=%s)",
        model_name,
        context_window,
    )


def register_openai_model_ids(model_ids: Iterable[str]) -> None:
    """Register configured OpenAI chat model IDs with LlamaIndex's whitelist."""
    for model_id in model_ids:
        if model_id.startswith("gpt-"):
            _ensure_openai_model_registered(model_id)


def centralized_llm_requested() -> bool:
    use_backend = os.getenv("USE_BACKEND", "false").lower() == "true"
    use_centralized = os.getenv("USE_CENTRALIZED_LLM", "false").lower() == "true"
    use_full = os.getenv("USE_FULL_BACKEND_ANALYSIS", "false").lower() == "true"
    return use_backend and (use_centralized or use_full)


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
        RuntimeError: If centralized LLM is enabled (must use NATSLLMChatAdapter)
    """
    if centralized_llm_requested():
        raise RuntimeError(
            "Centralized LLM mode is active (USE_BACKEND + USE_CENTRALIZED_LLM). "
            "Local OpenAI/Gemini clients are disabled; use DocumentAnalyzer with NATS LLM."
        )

    # OpenAI models
    if model_name.startswith("gpt-"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error(f"Cannot initialize OpenAI model '{model_name}' - OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models")

        _ensure_openai_model_registered(model_name)
        return ReportAnalystOpenAI(
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
