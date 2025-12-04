"""
Backend Service Layer

Clean abstraction for all search backend API interactions.
Handles PDF upload, processing monitoring, chunk retrieval, and analysis jobs.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st

from .config import BackendConfig

logger = logging.getLogger(__name__)


class BackendServiceError(Exception):
    """Custom exception for backend service errors"""

    pass


class BackendService:
    """Service for interacting with the search backend"""

    def __init__(self, config: BackendConfig):
        self.config = config
        self.timeout = 30

    async def upload_pdf(self, file_bytes: bytes, filename: str) -> str:
        """
        Upload PDF to search backend.

        Args:
            file_bytes: PDF file bytes
            filename: Original filename

        Returns:
            resource_id: Backend resource ID

        Raises:
            BackendServiceError: If upload fails
        """
        # Check if S3+NATS enterprise upload is available and enabled
        if self._should_use_s3_upload():
            try:
                from .s3_upload_service import S3UploadService
                s3_service = S3UploadService(self.config)
                return await s3_service.upload_pdf_via_s3_nats(file_bytes, filename)
            except Exception as e:
                # Fall back to HTTP upload if S3 fails
                logger.warning(f"S3+NATS upload failed, falling back to HTTP: {e}")
        
        # Default HTTP upload
        return await self._upload_via_http(file_bytes, filename)
    
    def _should_use_s3_upload(self) -> bool:
        """Check if S3+NATS upload should be used"""
        try:
            from .s3_upload_service import S3UploadService
            import os
            
            # Check if enterprise S3 upload is enabled and available
            s3_enabled = os.getenv('USE_S3_UPLOAD', '').lower() in ('true', '1', 'yes')
            return s3_enabled and S3UploadService.is_available()
        except ImportError:
            return False
    
    async def _upload_via_http(self, file_bytes: bytes, filename: str) -> str:
        """Upload PDF via HTTP (default method)"""
        try:
            # Create temporary URL for the file
            temp_url = f"streamlit://upload/{filename}"

            response = requests.post(
                f"{self.config.backend_url}/resources/text",
                data={
                    "url": temp_url,
                    "text": f"PDF file: {filename}",
                    "metadata": {
                        "source": "streamlit_upload",
                        "filename": filename,
                        "upload_time": datetime.utcnow().isoformat(),
                        "owner": self.config.owner,
                    },
                },
                timeout=self.timeout,
            )

            if response.status_code == 200:
                resource_data = response.json()
                return resource_data["id"]
            else:
                raise BackendServiceError(f"Upload failed: {response.status_code}")

        except requests.RequestException as e:
            raise BackendServiceError(f"Upload error: {str(e)}")

    def wait_for_processing(self, resource_id: str, timeout: int = 120) -> bool:
        """
        Wait for backend processing to complete with progress bar.

        Args:
            resource_id: Resource ID to monitor
            timeout: Max wait time in seconds

        Returns:
            bool: True if processing completed successfully
        """
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()

        while True:
            try:
                # Check resource status
                resources = self._get_resources()

                for resource in resources:
                    if resource["id"] == resource_id:
                        status = resource.get("status", "UNKNOWN")
                        status_text.text(f"📊 Processing status: {status}")

                        if status == "COMPLETED":
                            progress_bar.progress(100)
                            return True
                        elif status == "FAILED":
                            error_msg = resource.get("error_message", "Unknown error")
                            st.error(f"❌ Processing failed: {error_msg}")
                            return False

                        # Update progress
                        progress = self._get_progress_for_status(status)
                        progress_bar.progress(progress)

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    st.error(f"⏰ Processing timed out after {timeout} seconds")
                    return False

                time.sleep(3)

            except Exception as e:
                st.error(f"❌ Error checking status: {str(e)}")
                return False

    def get_chunks(self, resource_id: str) -> List[Dict[str, Any]]:
        """
        Get processed chunks from search backend.

        Args:
            resource_id: Resource ID

        Returns:
            List of chunk dictionaries
        """
        try:
            response = requests.post(
                f"{self.config.backend_url}/search/",
                json={"query": "document content", "top_k": 1000, "threshold": 0.0},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                search_results = response.json()
                chunks = []

                for result in search_results.get("results", []):
                    if result["resource"]["id"] == resource_id:
                        for chunk_data in result["chunks"]:
                            chunk = chunk_data["chunk"]
                            chunks.append(
                                {
                                    "chunk_id": chunk["id"],
                                    "chunk_text": chunk["chunk_text"],
                                    "chunk_metadata": chunk["chunk_metadata"],
                                    "similarity_score": chunk_data["similarity"],
                                    "resource_id": resource_id,
                                }
                            )

                return chunks
            else:
                raise BackendServiceError(
                    f"Failed to get chunks: {response.status_code}"
                )

        except requests.RequestException as e:
            raise BackendServiceError(f"Error getting chunks: {str(e)}")

    def submit_analysis_job(self, resource_id: str, question_set: str) -> str:
        """
        Submit analysis job to backend.

        Args:
            resource_id: Resource ID to analyze
            question_set: Question set to use

        Returns:
            analysis_job_id: Job ID for tracking
        """
        try:
            job_data = {
                "resource_id": resource_id,
                "question_set": question_set,
                "analysis_config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "use_centralized_llm": self.config.use_centralized_llm,
                    "deployment_type": self.config.deployment_type,
                    "owner": self.config.owner,
                    "experiment_name": self.config.experiment_name,
                },
                "metadata": {
                    "source": "streamlit",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            response = requests.post(
                f"{self.config.backend_url}/analysis/jobs/",
                json=job_data,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                job_result = response.json()
                return job_result.get("job_id")
            else:
                raise BackendServiceError(
                    f"Failed to submit analysis job: {response.status_code}"
                )

        except requests.RequestException as e:
            raise BackendServiceError(f"Error submitting analysis job: {str(e)}")

    def wait_for_analysis(
        self, analysis_job_id: str, timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Wait for analysis job to complete.

        Args:
            analysis_job_id: Analysis job ID
            timeout: Max wait time in seconds

        Returns:
            Analysis results
        """
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()

        while True:
            try:
                response = requests.get(
                    f"{self.config.backend_url}/analysis/jobs/{analysis_job_id}",
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data.get("status", "unknown")

                    status_text.text(f"🔬 Analysis status: {status}")

                    if status == "completed":
                        progress_bar.progress(100)
                        return job_data.get("results")
                    elif status == "failed":
                        error_msg = job_data.get("error", "Unknown error")
                        raise BackendServiceError(f"Analysis failed: {error_msg}")

                    # Update progress
                    progress = self._get_analysis_progress_for_status(status)
                    progress_bar.progress(progress)

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise BackendServiceError(
                        f"Analysis timed out after {timeout} seconds"
                    )

                time.sleep(5)

            except requests.RequestException as e:
                raise BackendServiceError(f"Error checking analysis status: {str(e)}")

    def get_analysis_results(
        self, analysis_job_id: str = None, resource_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get stored analysis results from backend database.

        Args:
            analysis_job_id: Analysis job ID (preferred)
            resource_id: Resource ID (fallback)

        Returns:
            Analysis results if found
        """
        try:
            # Try by job ID first
            if analysis_job_id:
                response = requests.get(
                    f"{self.config.backend_url}/analysis/jobs/{analysis_job_id}/results",
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    return response.json()

            # Fallback to resource ID
            if resource_id:
                response = requests.get(
                    f"{self.config.backend_url}/analysis/results",
                    params={"resource_id": resource_id},
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    results = response.json()
                    return results[0] if results else None

            return None

        except requests.RequestException as e:
            logger.error(f"Error retrieving analysis results: {e}")
            return None

    def _get_resources(self) -> List[Dict[str, Any]]:
        """Get all resources from backend"""
        try:
            response = requests.get(
                f"{self.config.backend_url}/resources/", timeout=self.timeout
            )
            return response.json() if response.status_code == 200 else []
        except requests.RequestException:
            return []

    def _get_progress_for_status(self, status: str) -> int:
        """Map processing status to progress percentage"""
        progress_map = {
            "PENDING": 10,
            "DOWNLOADING": 30,
            "CHUNKING": 60,
            "EMBEDDING": 80,
            "COMPLETED": 100,
        }
        return progress_map.get(status, 50)

    def _get_analysis_progress_for_status(self, status: str) -> int:
        """Map analysis status to progress percentage"""
        progress_map = {
            "pending": 10,
            "processing": 30,
            "analyzing": 60,
            "storing": 80,
            "completed": 100,
        }
        return progress_map.get(status, 50)


# Convenience functions for streamlit integration
def create_backend_service(config: BackendConfig) -> BackendService:
    """Create backend service from config"""
    return BackendService(config)


def handle_backend_error(error: BackendServiceError, context: str = ""):
    """Standard error handling for backend service errors"""
    error_msg = f"❌ {context} failed: {str(error)}" if context else f"❌ {str(error)}"
    st.error(error_msg)
    logger.error(f"Backend service error: {error}")
