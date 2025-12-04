"""
NATS Job Executor

Executes jobs using NATS as the coordination layer.
Supports JetStream for persistence and guaranteed delivery.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import nats
    from nats.js.api import ConsumerConfig, StreamConfig

    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

from .interfaces import (
    ExecutionBackend,
    JobDefinition,
    JobExecutor,
    JobHandler,
    JobResult,
    JobStatus,
)

logger = logging.getLogger(__name__)


class NATSJobExecutor(JobExecutor):
    """NATS-based job executor using JetStream"""

    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        stream_name: str = "JOBS",
        consumer_name: str = "report-analyst-consumer",
    ):

        if not NATS_AVAILABLE:
            raise ImportError("NATS not available. Install with: pip install nats-py")

        self.nats_url = nats_url
        self.stream_name = stream_name
        self.consumer_name = consumer_name
        self.nc = None
        self.js = None
        self.job_handlers: Dict[str, JobHandler] = {}
        self.job_storage: Dict[str, JobResult] = {}  # In-memory for now

    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.nats_url)
            self.js = self.nc.jetstream()

            # Create job stream if it doesn't exist
            try:
                await self.js.stream_info(self.stream_name)
            except:
                await self.js.add_stream(
                    StreamConfig(
                        name=self.stream_name,
                        subjects=[f"{self.stream_name}.>"],
                        retention="limits",
                        max_msgs=10000,
                        max_age=86400,  # 24 hours
                    )
                )

            logger.info(f"Connected to NATS at {self.nats_url}")

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()

    def register_handler(self, job_type: str, handler: JobHandler):
        """Register a job handler for a specific job type"""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    async def submit_job(self, job: JobDefinition) -> str:
        """Submit a job to NATS for execution"""
        if not self.js:
            await self.connect()

        # Create initial job result
        job_result = JobResult(job_id=job.job_id, status=JobStatus.PENDING)
        self.job_storage[job.job_id] = job_result

        # Publish job to NATS
        subject = f"{self.stream_name}.{job.job_type}"
        message = json.dumps(job.to_dict()).encode()

        try:
            await self.js.publish(subject, message)
            logger.info(f"Submitted job {job.job_id} to NATS")
            return job.job_id
        except Exception as e:
            job_result.status = JobStatus.FAILED
            job_result.error = str(e)
            logger.error(f"Failed to submit job {job.job_id}: {e}")
            raise

    async def get_job_status(self, job_id: str) -> JobResult:
        """Get job status and result"""
        if job_id in self.job_storage:
            return self.job_storage[job_id]

        # Job not found
        return JobResult(job_id=job_id, status=JobStatus.FAILED, error="Job not found")

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (mark as cancelled)"""
        if job_id in self.job_storage:
            job_result = self.job_storage[job_id]
            if job_result.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
                job_result.status = JobStatus.CANCELLED
                job_result.completed_at = datetime.utcnow()
                return True
        return False

    async def list_jobs(self, status: Optional[JobStatus] = None) -> List[JobResult]:
        """List jobs with optional status filter"""
        jobs = list(self.job_storage.values())
        if status:
            jobs = [job for job in jobs if job.status == status]
        return jobs

    @property
    def backend_type(self) -> ExecutionBackend:
        return ExecutionBackend.NATS

    async def start_worker(self):
        """Start the job worker that processes jobs from NATS"""
        if not self.js:
            await self.connect()

        # Create consumer for processing jobs
        try:
            await self.js.consumer_info(self.stream_name, self.consumer_name)
        except:
            await self.js.add_consumer(
                self.stream_name,
                ConsumerConfig(
                    durable_name=self.consumer_name,
                    filter_subject=f"{self.stream_name}.>",
                    ack_policy="explicit",
                ),
            )

        # Subscribe to process jobs
        psub = await self.js.pull_subscribe(f"{self.stream_name}.>", self.consumer_name)

        logger.info(f"Started NATS worker for stream {self.stream_name}")

        while True:
            try:
                # Fetch messages
                msgs = await psub.fetch(1, timeout=1.0)

                for msg in msgs:
                    await self._process_message(msg)

            except nats.errors.TimeoutError:
                # No messages, continue
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, msg):
        """Process a single job message"""
        try:
            # Parse job from message
            job_data = json.loads(msg.data.decode())
            job = JobDefinition.from_dict(job_data)

            logger.info(f"Processing job {job.job_id} of type {job.job_type}")

            # Update job status
            if job.job_id in self.job_storage:
                job_result = self.job_storage[job.job_id]
                job_result.status = JobStatus.PROCESSING
                job_result.started_at = datetime.utcnow()

            # Find handler for job type
            if job.job_type not in self.job_handlers:
                error = f"No handler registered for job type: {job.job_type}"
                logger.error(error)

                if job.job_id in self.job_storage:
                    job_result = self.job_storage[job.job_id]
                    job_result.status = JobStatus.FAILED
                    job_result.error = error
                    job_result.completed_at = datetime.utcnow()

                await msg.ack()
                return

            # Execute job
            handler = self.job_handlers[job.job_type]
            result = await handler.execute(job)

            # Store result
            result.completed_at = datetime.utcnow()
            self.job_storage[job.job_id] = result

            logger.info(f"Completed job {job.job_id} with status {result.status}")

            # Acknowledge message
            await msg.ack()

        except Exception as e:
            logger.error(f"Failed to process message: {e}")

            # Mark job as failed if we can
            try:
                job_data = json.loads(msg.data.decode())
                job_id = job_data.get("job_id")
                if job_id and job_id in self.job_storage:
                    job_result = self.job_storage[job_id]
                    job_result.status = JobStatus.FAILED
                    job_result.error = str(e)
                    job_result.completed_at = datetime.utcnow()
            except:
                pass

            # Negative acknowledge to retry
            await msg.nak()


class NATSConfigurationProvider:
    """NATS-based configuration provider using key-value store"""

    def __init__(self, nats_executor: NATSJobExecutor, bucket_name: str = "CONFIG"):
        self.nats_executor = nats_executor
        self.bucket_name = bucket_name
        self.kv = None

    async def _get_kv(self):
        """Get or create key-value bucket"""
        if not self.kv:
            if not self.nats_executor.js:
                await self.nats_executor.connect()

            try:
                self.kv = await self.nats_executor.js.key_value(self.bucket_name)
            except:
                # Create bucket if it doesn't exist
                await self.nats_executor.js.create_key_value(bucket=self.bucket_name)
                self.kv = await self.nats_executor.js.key_value(self.bucket_name)

    async def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        """Get configuration by key"""
        await self._get_kv()

        try:
            entry = await self.kv.get(key)
            return json.loads(entry.value.decode())
        except:
            return None

    async def set_config(self, key: str, value: Dict[str, Any]) -> bool:
        """Set configuration value"""
        await self._get_kv()

        try:
            await self.kv.put(key, json.dumps(value).encode())
            return True
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False

    async def watch_config(self, key_pattern: str, callback):
        """Watch for configuration changes"""
        await self._get_kv()

        # This would need more implementation for watching
        # NATS KV supports watchers
        pass
