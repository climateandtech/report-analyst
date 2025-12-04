"""
NATS Integration MVP for Report Analyst Jobs

Flow:
1. Client → Search Backend REST API (upload PDF)
2. Search Backend → Celery job (PDF processing, chunking, embedding)
3. When PDF processing complete → Publish "document.ready" to NATS
4. NATS Worker → Receives "document.ready", runs analysis using existing chunks
5. Analysis complete → Publish results back via NATS
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import nats
from nats.js import JetStreamContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DocumentReadyEvent:
    """Event published when search backend finishes processing a document"""

    resource_id: str
    document_url: str
    chunks_count: int
    status: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AnalysisJob:
    """Represents an analysis job request"""

    id: str
    resource_id: str  # From search backend
    question_set: str
    analysis_config: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    updated_at: datetime = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class SearchBackendClient:
    """REST API client for search backend operations"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def get_resource_chunks(self, resource_id: str) -> List[Dict[str, Any]]:
        """Get chunks for a resource that's already processed"""
        async with aiohttp.ClientSession() as session:
            # Use search endpoint to get all chunks for this resource
            async with session.post(
                f"{self.base_url}/search/",
                json={"query": "document content", "top_k": 1000, "threshold": 0.0},
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    # Extract chunks from search results for this resource
                    chunks = []
                    for result in search_results.get("results", []):
                        if result["resource"]["id"] == resource_id:
                            for chunk_data in result["chunks"]:
                                chunks.append(
                                    {
                                        "id": chunk_data["chunk"]["id"],
                                        "text": chunk_data["chunk"]["chunk_text"],
                                        "metadata": chunk_data["chunk"][
                                            "chunk_metadata"
                                        ],
                                    }
                                )
                    logger.info(
                        f"Retrieved {len(chunks)} chunks for resource {resource_id}"
                    )
                    return chunks
                else:
                    raise Exception(f"Failed to get chunks: {response.status}")


class NATSJobCoordinator:
    """Coordinates analysis jobs via NATS messaging"""

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.js = None
        self.search_backend = SearchBackendClient()

    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.nats_url)
            self.js = self.nc.jetstream()

            # Create streams for document events and analysis jobs
            try:
                await self.js.add_stream(name="DOCUMENTS", subjects=["document.*"])
                await self.js.add_stream(name="ANALYSIS_JOBS", subjects=["analysis.*"])
            except Exception as e:
                logger.info(f"Streams may already exist: {e}")

            logger.info("Connected to NATS successfully")

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()
            logger.info("Disconnected from NATS")

    # For Search Backend to publish when PDF processing is complete
    async def publish_document_ready(
        self, resource_id: str, document_url: str, chunks_count: int
    ):
        """Publish document ready event (called from search backend)"""
        event = DocumentReadyEvent(
            resource_id=resource_id,
            document_url=document_url,
            chunks_count=chunks_count,
            status="ready",
        )

        await self.js.publish(
            "document.ready", json.dumps(asdict(event), default=str).encode()
        )

        logger.info(f"Published document ready event for resource {resource_id}")

    # For Clients to request analysis
    async def submit_analysis_job(
        self, resource_id: str, question_set: str, analysis_config: Dict[str, Any]
    ) -> str:
        """Submit analysis job for a resource that's already processed"""
        job_id = str(uuid.uuid4())
        job = AnalysisJob(
            id=job_id,
            resource_id=resource_id,
            question_set=question_set,
            analysis_config=analysis_config,
        )

        # Send job to NATS
        await self.js.publish(
            "analysis.job.submit", json.dumps(asdict(job), default=str).encode()
        )

        logger.info(f"Submitted analysis job {job_id} for resource {resource_id}")
        return job_id

    # For Workers to process analysis jobs
    async def process_analysis_jobs(self):
        """Process analysis jobs from NATS (runs on worker)"""
        await self.js.subscribe("analysis.job.submit", cb=self._process_analysis_job)
        logger.info("Started processing analysis jobs from NATS")

        # Keep processing
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping analysis job processor")

    async def _process_analysis_job(self, msg):
        """Process a single analysis job"""
        try:
            job_data = json.loads(msg.data.decode())
            job = AnalysisJob(**job_data)

            logger.info(
                f"Processing analysis job {job.id} for resource {job.resource_id}"
            )

            # Update job status
            job.status = JobStatus.PROCESSING
            job.updated_at = datetime.utcnow()

            # Send status update
            await self.js.publish(
                "analysis.job.status", json.dumps(asdict(job), default=str).encode()
            )

            # Get chunks from search backend (already processed)
            chunks = await self.search_backend.get_resource_chunks(job.resource_id)

            # Run analysis using report analyst toolkit
            analysis_result = await self._run_analysis(
                chunks, job.question_set, job.analysis_config
            )

            # Complete job
            job.status = JobStatus.COMPLETED
            job.result = {
                "resource_id": job.resource_id,
                "chunks_analyzed": len(chunks),
                "analysis_result": analysis_result,
                "completed_at": datetime.utcnow().isoformat(),
            }
            job.updated_at = datetime.utcnow()

            # Send completion notification
            await self.js.publish(
                "analysis.job.completed", json.dumps(asdict(job), default=str).encode()
            )

            await msg.ack()
            logger.info(f"Analysis job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Error processing analysis job {job.id}: {e}")

            # Mark job as failed
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.utcnow()

            await self.js.publish(
                "analysis.job.failed", json.dumps(asdict(job), default=str).encode()
            )

            await msg.ack()

    async def _run_analysis(
        self, chunks: List[Dict[str, Any]], question_set: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the actual analysis using report analyst toolkit"""
        # Import here to avoid circular imports
        from .analysis_toolkit import analyze_document_with_chunks

        # Convert chunks to the format expected by analysis toolkit
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append(
                {"text": chunk["text"], "metadata": chunk["metadata"]}
            )

        # Run analysis
        result = await analyze_document_with_chunks(
            chunks=formatted_chunks, question_set=question_set, config=config
        )

        return result


class NATSSearchBackendPublisher:
    """Used by search backend to publish events to NATS"""

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.coordinator = NATSJobCoordinator(nats_url)

    async def __aenter__(self):
        await self.coordinator.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.coordinator.disconnect()

    async def notify_document_ready(
        self, resource_id: str, document_url: str, chunks_count: int
    ):
        """Notify that document processing is complete"""
        await self.coordinator.publish_document_ready(
            resource_id, document_url, chunks_count
        )


class NATSAnalysisWorker:
    """Worker that processes analysis jobs from NATS"""

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.coordinator = NATSJobCoordinator(nats_url)

    async def start(self):
        """Start the worker"""
        await self.coordinator.connect()
        logger.info("NATS analysis worker started")
        await self.coordinator.process_analysis_jobs()

    async def stop(self):
        """Stop the worker"""
        await self.coordinator.disconnect()


class NATSAnalysisClient:
    """Client for submitting analysis jobs to NATS"""

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.coordinator = NATSJobCoordinator(nats_url)
        self.job_results = {}

    async def __aenter__(self):
        await self.coordinator.connect()
        # Subscribe to job results
        await self.coordinator.js.subscribe(
            "analysis.job.completed", cb=self._handle_completed
        )
        await self.coordinator.js.subscribe(
            "analysis.job.failed", cb=self._handle_failed
        )
        await self.coordinator.js.subscribe(
            "analysis.job.status", cb=self._handle_status
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.coordinator.disconnect()

    async def analyze_resource(
        self, resource_id: str, question_set: str, analysis_config: Dict[str, Any]
    ) -> str:
        """Submit analysis job for a resource that's already processed"""
        job_id = await self.coordinator.submit_analysis_job(
            resource_id, question_set, analysis_config
        )
        return job_id

    async def wait_for_completion(
        self, job_id: str, timeout: int = 300
    ) -> Dict[str, Any]:
        """Wait for job completion"""
        start_time = datetime.utcnow()

        while True:
            if job_id in self.job_results:
                result = self.job_results[job_id]
                if result["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    return result

            if (datetime.utcnow() - start_time).seconds > timeout:
                raise TimeoutError(
                    f"Job {job_id} did not complete within {timeout} seconds"
                )

            await asyncio.sleep(2)

    async def _handle_completed(self, msg):
        """Handle job completion"""
        job_data = json.loads(msg.data.decode())
        job = AnalysisJob(**job_data)
        self.job_results[job.id] = asdict(job)
        logger.info(f"Analysis job {job.id} completed")
        await msg.ack()

    async def _handle_failed(self, msg):
        """Handle job failure"""
        job_data = json.loads(msg.data.decode())
        job = AnalysisJob(**job_data)
        self.job_results[job.id] = asdict(job)
        logger.info(f"Analysis job {job.id} failed: {job.error}")
        await msg.ack()

    async def _handle_status(self, msg):
        """Handle job status updates"""
        job_data = json.loads(msg.data.decode())
        job = AnalysisJob(**job_data)
        self.job_results[job.id] = asdict(job)
        logger.info(f"Analysis job {job.id} status: {job.status}")
        await msg.ack()


# Example usage
async def example_submit_analysis():
    """Example: Submit analysis job for an existing resource"""
    async with NATSAnalysisClient() as client:
        # Assume we have a resource_id from search backend
        resource_id = "12345678-1234-1234-1234-123456789012"

        job_id = await client.analyze_resource(
            resource_id=resource_id,
            question_set="tcfd",
            analysis_config={"model": "gpt-4o-mini"},
        )

        print(f"Submitted analysis job: {job_id}")

        # Wait for completion
        result = await client.wait_for_completion(job_id)
        print(f"Analysis completed: {result['status']}")
        if result.get("result"):
            print(f"Analysis result: {result['result']}")


async def example_start_worker():
    """Example: Start a worker to process analysis jobs"""
    worker = NATSAnalysisWorker()
    await worker.start()


async def example_search_backend_notification():
    """Example: How search backend notifies when PDF processing is complete"""
    async with NATSSearchBackendPublisher() as publisher:
        await publisher.notify_document_ready(
            resource_id="12345678-1234-1234-1234-123456789012",
            document_url="https://example.com/document.pdf",
            chunks_count=42,
        )
        print("Document ready notification sent")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "worker":
            asyncio.run(example_start_worker())
        elif sys.argv[1] == "notify":
            asyncio.run(example_search_backend_notification())
        else:
            asyncio.run(example_submit_analysis())
    else:
        asyncio.run(example_submit_analysis())
