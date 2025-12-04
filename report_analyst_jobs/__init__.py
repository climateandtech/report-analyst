"""
Report Analyst Jobs - Universal Analysis Toolkit

Clean, modular analysis functions for different deployment scenarios.
"""

# Core analysis functions
from .core_analysis import (
    AnalysisConfig,
    AnalysisRequest,
    AnalysisResult,
    analyze_document_core,
    create_analysis_request,
    format_analysis_for_display,
    validate_analysis_request,
)

# Advanced integrations (optional)
try:
    from .data_lake_integration import DataLakeClient, DataMetadata, DeploymentConfig
    from .llm_integration import LLMRequest, LLMResponse, NATSLLMClient
    from .search_backend_integration import SearchBackendClient

    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

__version__ = "1.0.0"
__all__ = [
    "AnalysisConfig",
    "AnalysisRequest",
    "AnalysisResult",
    "analyze_document_core",
    "create_analysis_request",
    "format_analysis_for_display",
    "validate_analysis_request",
    "ADVANCED_FEATURES_AVAILABLE",
]
