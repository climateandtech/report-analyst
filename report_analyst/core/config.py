"""
Configuration System for Report Analyst

This module handles configuration loading from environment variables and settings files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for report analyst"""

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

    # Search Backend Configuration
    SEARCH_BACKEND_URL: Optional[str] = os.getenv("SEARCH_BACKEND_URL", "http://localhost:8001")
    SEARCH_BACKEND_API_KEY: Optional[str] = os.getenv("SEARCH_BACKEND_API_KEY")

    # Document Processing
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")
    INPUT_DIR: str = os.getenv("INPUT_DIR", "data/input")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "data/output")

    # Analysis Configuration
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "500"))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "20"))
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "5"))

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    @classmethod
    def get_search_backend_config(cls) -> Dict[str, Any]:
        """Get search backend configuration"""
        return {"url": cls.SEARCH_BACKEND_URL, "api_key": cls.SEARCH_BACKEND_API_KEY}

    @classmethod
    def is_search_backend_configured(cls) -> bool:
        """Check if search backend is configured"""
        return cls.SEARCH_BACKEND_URL is not None

    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Get LLM configuration"""
        return {
            "openai_api_key": cls.OPENAI_API_KEY,
            "google_api_key": cls.GOOGLE_API_KEY,
            "default_model": cls.DEFAULT_MODEL,
        }

    @classmethod
    def get_processing_config(cls) -> Dict[str, Any]:
        """Get document processing configuration"""
        return {
            "temp_dir": cls.TEMP_DIR,
            "input_dir": cls.INPUT_DIR,
            "output_dir": cls.OUTPUT_DIR,
            "chunk_size": cls.DEFAULT_CHUNK_SIZE,
            "chunk_overlap": cls.DEFAULT_CHUNK_OVERLAP,
            "top_k": cls.DEFAULT_TOP_K,
        }


# Global config instance
config = Config()
