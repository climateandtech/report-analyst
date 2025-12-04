"""
Plugin Discovery System

This module handles discovery and loading of optional modules like API and
search backend integration, following a modular architecture pattern.
"""

import logging
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)


def discover_document_sources() -> Dict[str, Type]:
    """
    Discover available document sources including optional integrations.

    Returns:
        Dict mapping source names to their implementation classes
    """
    from .document_sources import LocalDocumentSource

    sources = {"local": LocalDocumentSource}

    # Try to load search backend integration
    try:
        from report_analyst_search_backend import SearchBackendSource

        from .config import config

        # Create factory function that uses configuration
        def create_search_backend_source():
            backend_config = config.get_search_backend_config()
            return SearchBackendSource(backend_config["url"], backend_config["api_key"])

        sources["search_backend"] = create_search_backend_source
        logger.info("Search backend integration available")
    except ImportError:
        logger.debug("Search backend integration not installed")

    return sources


def discover_api_module() -> Optional[Any]:
    """
    Discover and return the FastAPI app if the API module is available.

    Returns:
        FastAPI app instance or None if not available
    """
    try:
        from report_analyst_api import app

        logger.info("API module available")
        return app
    except ImportError:
        logger.debug("API module not installed")
        return None


def get_available_integrations() -> Dict[str, bool]:
    """
    Check which optional integrations are available.

    Returns:
        Dict mapping integration names to availability status
    """
    integrations = {}

    # Check API module
    try:
        import report_analyst_api

        integrations["api"] = True
    except ImportError:
        integrations["api"] = False

    # Check search backend integration
    try:
        import report_analyst_search_backend

        integrations["search_backend"] = True
    except ImportError:
        integrations["search_backend"] = False

    return integrations
