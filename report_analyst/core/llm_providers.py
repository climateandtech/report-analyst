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
            logger.error(
                f"Cannot initialize OpenAI model '{model_name}' - OPENAI_API_KEY environment variable is not set"
            )
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI models"
            )

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
            logger.error(
                f"Cannot initialize Gemini model '{model_name}' - GOOGLE_API_KEY environment variable is not set"
            )
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required for Gemini models"
            )

        # Use the full model path if provided, otherwise prefix with "models/"
        full_model_name = model_name
        if not model_name.startswith("models/"):
            full_model_name = f"models/{model_name}"

        logger.info(f"Initializing Gemini model: {full_model_name}")
        return Gemini(model=full_model_name, api_key=api_key, **kwargs)

    else:
        logger.error(f"Unsupported model type: {model_name}")
        raise ValueError(f"Unsupported model: {model_name}")
