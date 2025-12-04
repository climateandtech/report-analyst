"""
Local Job Executor

Simple local executor for development and testing.
Executes jobs in-process without any message queuing.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .interfaces import (
    ExecutionBackend,
    JobDefinition,
    JobExecutor,
    JobHandler,
    JobResult,
    JobStatus,
)

logger = logging.getLogger(__name__)


class LocalJobExecutor(JobExecutor):
    """Local job executor for development and testing"""

    def __init__(self):
        self.job_handlers: Dict[str, JobHandler] = {}
        self.job_storage: Dict[str, JobResult] = {}
        self.job_tasks: Dict[str, asyncio.Task] = {}

    def register_handler(self, job_type: str, handler: JobHandler):
        """Register a job handler for a specific job type"""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered local handler for job type: {job_type}")

    async def submit_job(self, job: JobDefinition) -> str:
        """Submit a job for local execution"""

        # Create initial job result
        job_result = JobResult(
            job_id=job.job_id, status=JobStatus.PENDING, started_at=datetime.utcnow()
        )
        self.job_storage[job.job_id] = job_result

        # Start job execution task
        task = asyncio.create_task(self._execute_job(job))
        self.job_tasks[job.job_id] = task

        logger.info(f"Submitted job {job.job_id} for local execution")
        return job.job_id

    async def get_job_status(self, job_id: str) -> JobResult:
        """Get job status"""
        if job_id in self.job_storage:
            return self.job_storage[job_id]

        return JobResult(job_id=job_id, status=JobStatus.FAILED, error="Job not found")

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        if job_id in self.job_tasks:
            task = self.job_tasks[job_id]
            if not task.done():
                task.cancel()

                # Update job result
                if job_id in self.job_storage:
                    job_result = self.job_storage[job_id]
                    job_result.status = JobStatus.CANCELLED
                    job_result.completed_at = datetime.utcnow()

                logger.info(f"Cancelled local job {job_id}")
                return True

        return False

    async def list_jobs(self, status: Optional[JobStatus] = None) -> List[JobResult]:
        """List jobs"""
        jobs = list(self.job_storage.values())
        if status:
            jobs = [job for job in jobs if job.status == status]
        return jobs

    @property
    def backend_type(self) -> ExecutionBackend:
        return ExecutionBackend.LOCAL

    async def _execute_job(self, job: JobDefinition):
        """Execute a job locally"""
        try:
            # Update status to processing
            job_result = self.job_storage[job.job_id]
            job_result.status = JobStatus.PROCESSING
            job_result.started_at = datetime.utcnow()

            # Find handler
            if job.job_type not in self.job_handlers:
                raise ValueError(f"No handler registered for job type: {job.job_type}")

            handler = self.job_handlers[job.job_type]

            # Execute job
            result = await handler.execute(job)

            # Update result
            result.completed_at = datetime.utcnow()
            self.job_storage[job.job_id] = result

            logger.info(f"Completed local job {job.job_id} with status {result.status}")

        except asyncio.CancelledError:
            # Job was cancelled
            job_result = self.job_storage[job.job_id]
            job_result.status = JobStatus.CANCELLED
            job_result.completed_at = datetime.utcnow()
            logger.info(f"Local job {job.job_id} was cancelled")

        except Exception as e:
            # Job failed
            job_result = self.job_storage[job.job_id]
            job_result.status = JobStatus.FAILED
            job_result.error = str(e)
            job_result.completed_at = datetime.utcnow()
            logger.error(f"Local job {job.job_id} failed: {e}")

        finally:
            # Clean up task reference
            if job.job_id in self.job_tasks:
                del self.job_tasks[job.job_id]
