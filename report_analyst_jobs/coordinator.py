"""
Job Coordinator

Central coordinator that manages job execution across NATS and local backends.
AWS integration is handled separately through the universal analysis toolkit.
"""

import logging
from typing import Any, Dict, List, Optional

from .analysis_handler import DocumentAnalysisHandler
from .interfaces import (
    ExecutionBackend,
    JobDefinition,
    JobExecutor,
    JobHandler,
    JobResult,
    JobStatus,
)
from .local_executor import LocalJobExecutor
from .nats_executor import NATSJobExecutor

logger = logging.getLogger(__name__)


class JobCoordinator:
    """Central coordinator for job execution"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.executors: Dict[ExecutionBackend, JobExecutor] = {}
        self.handlers: Dict[str, JobHandler] = {}
        self.default_backend = ExecutionBackend.LOCAL

        # Initialize executors
        self._initialize_executors()

        # Register default handlers
        self._register_default_handlers()

    def _initialize_executors(self):
        """Initialize available executors"""

        # Try to initialize NATS executor
        if self.config.get("enable_nats", True):
            try:
                nats_config = self.config.get("nats", {})
                nats_executor = NATSJobExecutor(
                    nats_url=nats_config.get("url", "nats://localhost:4222"),
                    stream_name=nats_config.get("stream", "JOBS"),
                    consumer_name=nats_config.get(
                        "consumer", "report-analyst-consumer"
                    ),
                )
                self.executors[ExecutionBackend.NATS] = nats_executor
                self.default_backend = ExecutionBackend.NATS
                logger.info("NATS executor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize NATS executor: {e}")

        # Always initialize local executor as fallback
        local_executor = LocalJobExecutor()
        self.executors[ExecutionBackend.LOCAL] = local_executor
        logger.info("Local executor initialized")

        # Set default based on what's available
        if ExecutionBackend.NATS not in self.executors:
            self.default_backend = ExecutionBackend.LOCAL

    def _register_default_handlers(self):
        """Register default job handlers"""
        analysis_handler = DocumentAnalysisHandler()
        for job_type in analysis_handler.get_supported_job_types():
            self.register_handler(job_type, analysis_handler)

    def register_handler(self, job_type: str, handler: JobHandler):
        """Register a job handler for a specific job type"""
        self.handlers[job_type] = handler

        # Register with all executors that support it
        for executor in self.executors.values():
            if hasattr(executor, "register_handler"):
                executor.register_handler(job_type, handler)

    async def submit_job(
        self, job: JobDefinition, backend: Optional[ExecutionBackend] = None
    ) -> str:
        """Submit a job for execution"""

        # Determine backend
        if backend is None:
            backend = self.default_backend

        if backend not in self.executors:
            raise ValueError(f"Backend {backend} not available")

        # Submit to executor
        executor = self.executors[backend]
        job_id = await executor.submit_job(job)

        logger.info(f"Submitted job {job_id} to {backend} backend")
        return job_id

    async def get_job_status(self, job_id: str) -> JobResult:
        """Get job status from any backend"""

        # Try each backend until we find the job
        for backend, executor in self.executors.items():
            try:
                result = await executor.get_job_status(job_id)
                if result.status != JobStatus.FAILED or result.error != "Job not found":
                    return result
            except Exception as e:
                logger.debug(f"Failed to get job status from {backend}: {e}")

        # Job not found in any backend
        return JobResult(
            job_id=job_id, status=JobStatus.FAILED, error="Job not found in any backend"
        )

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job in any backend"""

        for backend, executor in self.executors.items():
            try:
                if await executor.cancel_job(job_id):
                    logger.info(f"Cancelled job {job_id} in {backend} backend")
                    return True
            except Exception as e:
                logger.debug(f"Failed to cancel job in {backend}: {e}")

        return False

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        backend: Optional[ExecutionBackend] = None,
    ) -> List[JobResult]:
        """List jobs from one or all backends"""

        if backend:
            if backend not in self.executors:
                return []
            return await self.executors[backend].list_jobs(status)

        # Collect from all backends
        all_jobs = []
        for backend, executor in self.executors.items():
            try:
                jobs = await executor.list_jobs(status)
                all_jobs.extend(jobs)
            except Exception as e:
                logger.debug(f"Failed to list jobs from {backend}: {e}")

        return all_jobs

    async def start_workers(self, backends: Optional[List[ExecutionBackend]] = None):
        """Start workers for specified backends"""

        if backends is None:
            backends = list(self.executors.keys())

        for backend in backends:
            if backend not in self.executors:
                logger.warning(f"Backend {backend} not available")
                continue

            executor = self.executors[backend]

            # Start worker if executor supports it
            if hasattr(executor, "start_worker"):
                try:
                    await executor.start_worker()
                    logger.info(f"Started worker for {backend} backend")
                except Exception as e:
                    logger.error(f"Failed to start worker for {backend}: {e}")

    def get_available_backends(self) -> List[ExecutionBackend]:
        """Get list of available execution backends"""
        return list(self.executors.keys())

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about configured backends"""
        info = {
            "available_backends": [backend.value for backend in self.executors.keys()],
            "default_backend": self.default_backend.value,
            "nats_available": ExecutionBackend.NATS in self.executors,
            "local_available": ExecutionBackend.LOCAL in self.executors,
            "configuration": self.config,
        }
        return info


# Factory function for easy setup
def create_job_coordinator(config: Dict[str, Any] = None) -> JobCoordinator:
    """Create a job coordinator with default configuration"""

    if config is None:
        config = {
            "enable_nats": True,
            "nats": {
                "url": "nats://localhost:4222",
                "stream": "JOBS",
                "consumer": "report-analyst-consumer",
            },
        }

    return JobCoordinator(config)


# Sample configurations
SAMPLE_CONFIGS = {
    # NATS-enabled configuration
    "nats_enabled": {
        "enable_nats": True,
        "nats": {
            "url": "nats://localhost:4222",
            "stream": "JOBS",
            "consumer": "report-analyst-consumer",
        },
    },
    # Local-only configuration
    "local_only": {"enable_nats": False},
    # Production NATS configuration
    "production": {
        "enable_nats": True,
        "nats": {
            "url": "nats://nats-cluster:4222",
            "stream": "PROD_JOBS",
            "consumer": "report-analyst-prod-consumer",
        },
    },
}
