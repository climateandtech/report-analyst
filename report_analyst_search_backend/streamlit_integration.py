"""
Streamlit Integration for Search Backend

Deprecated: This module has been refactored into cleaner components.
Use the config and flow_orchestrator modules instead.
"""

import logging

from .backend_service import BackendService, create_backend_service

# Re-export the clean components for backward compatibility
from .config import BackendConfig, configure_backend_integration, display_config_status
from .flow_orchestrator import create_flow_orchestrator, needs_local_analysis

logger = logging.getLogger(__name__)


# Deprecated function - use new architecture
def streamlit_enhanced_flow(uploaded_file, config):
    """Deprecated: Use FlowOrchestrator instead"""
    logger.warning("streamlit_enhanced_flow is deprecated. Use FlowOrchestrator.process_document() instead.")
    return None


# Deprecated function - use new architecture
def streamlit_full_backend_flow(uploaded_file, config):
    """Deprecated: Use FlowOrchestrator instead"""
    logger.warning("streamlit_full_backend_flow is deprecated. Use FlowOrchestrator.complete_backend_analysis() instead.")
    return None


# Keep a few convenience functions for backward compatibility
def upload_pdf_to_backend(file_bytes: bytes, filename: str, backend_url: str = "http://localhost:8000"):
    """Deprecated: Use BackendService.upload_pdf() instead"""
    logger.warning("upload_pdf_to_backend is deprecated. Use BackendService.upload_pdf() instead.")
    return None


def wait_for_processing_polling(resource_id: str, backend_url: str = "http://localhost:8000", timeout: int = 120):
    """Deprecated: Use BackendService.wait_for_processing() instead"""
    logger.warning("wait_for_processing_polling is deprecated. Use BackendService.wait_for_processing() instead.")
    return False


def get_backend_chunks(resource_id: str, backend_url: str = "http://localhost:8000"):
    """Deprecated: Use BackendService.get_chunks() instead"""
    logger.warning("get_backend_chunks is deprecated. Use BackendService.get_chunks() instead.")
    return []


def streamlit_backend_flow(uploaded_file, backend_url: str = "http://localhost:8000"):
    """Deprecated: Use FlowOrchestrator.process_document() instead"""
    logger.warning("streamlit_backend_flow is deprecated. Use FlowOrchestrator.process_document() instead.")
    return None


def use_centralized_llm_for_analysis(question: str, context_chunks, config):
    """Deprecated: Use FlowOrchestrator.analyze_document() instead"""
    logger.warning("use_centralized_llm_for_analysis is deprecated. Use FlowOrchestrator.analyze_document() instead.")
    return None


def store_analysis_in_data_lake(analysis_results, config, experiment_id=None):
    """Deprecated: Use FlowOrchestrator.analyze_document() instead"""
    logger.warning("store_analysis_in_data_lake is deprecated. Use FlowOrchestrator.analyze_document() instead.")
    return False


def submit_analysis_job_to_backend(
    resource_id: str,
    question_set: str,
    config,
    backend_url: str = "http://localhost:8000",
):
    """Deprecated: Use BackendService.submit_analysis_job() instead"""
    logger.warning("submit_analysis_job_to_backend is deprecated. Use BackendService.submit_analysis_job() instead.")
    return None


def wait_for_analysis_completion(analysis_job_id: str, backend_url: str = "http://localhost:8000", timeout: int = 300):
    """Deprecated: Use BackendService.wait_for_analysis() instead"""
    logger.warning("wait_for_analysis_completion is deprecated. Use BackendService.wait_for_analysis() instead.")
    return None


def get_stored_analysis_results(
    analysis_job_id: str = None,
    resource_id: str = None,
    backend_url: str = "http://localhost:8000",
):
    """Deprecated: Use BackendService.get_analysis_results() instead"""
    logger.warning("get_stored_analysis_results is deprecated. Use BackendService.get_analysis_results() instead.")
    return None
