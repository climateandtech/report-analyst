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
from dataclasses import asdict, dataclass, field
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
    chunks: Optional[List[Dict[str, Any]]] = None
    """Optional: Pre-processed chunks included in event (if pull_chunks=False)"""

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


@dataclass
class DocumentReadyProcessingConfig:
    """
    Configuration for automatic document.ready event processing.

    Controls how document.ready events are handled:
    - Whether to pull chunks from backend or use provided chunks
    - Whether to run analysis
    - Whether to store results back to backend
    - Analysis configuration
    """

    # Chunk retrieval strategy
    pull_chunks: bool = True
    """Whether to pull chunks from backend. If False, chunks must be provided in event."""

    # Analysis configuration
    question_set: str = "tcfd"
    """Question set to use for analysis"""

    analysis_config: Dict[str, Any] = field(
        default_factory=lambda: {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
        }
    )
    """Analysis configuration (model, temperature, etc.)"""

    # Result storage
    store_to_backend: bool = True
    """Whether to store analysis results back to backend"""

    # Error handling
    ack_on_error: bool = True
    """Whether to acknowledge message even on error (prevents redelivery loops)"""

    # Chunk retrieval options (when pull_chunks=True)
    chunk_retrieval_method: str = "search"  # "search" or "direct"
    """Method to retrieve chunks: 'search' uses /search/ endpoint, 'direct' uses /resources/{id}/chunks"""

    max_chunks: Optional[int] = None
    """Maximum number of chunks to retrieve (None = no limit)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pull_chunks": self.pull_chunks,
            "question_set": self.question_set,
            "analysis_config": self.analysis_config,
            "store_to_backend": self.store_to_backend,
            "ack_on_error": self.ack_on_error,
            "chunk_retrieval_method": self.chunk_retrieval_method,
            "max_chunks": self.max_chunks,
        }


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
                                        "metadata": chunk_data["chunk"]["chunk_metadata"],
                                    }
                                )
                    logger.info(f"Retrieved {len(chunks)} chunks for resource {resource_id}")
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
    async def publish_document_ready(self, resource_id: str, document_url: str, chunks_count: int):
        """Publish document ready event (called from search backend)"""
        event = DocumentReadyEvent(
            resource_id=resource_id,
            document_url=document_url,
            chunks_count=chunks_count,
            status="ready",
        )

        await self.js.publish("document.ready", json.dumps(asdict(event), default=str).encode())

        logger.info(f"Published document ready event for resource {resource_id}")

    # For Clients to request analysis
    async def submit_analysis_job(self, resource_id: str, question_set: str, analysis_config: Dict[str, Any]) -> str:
        """Submit analysis job for a resource that's already processed"""
        job_id = str(uuid.uuid4())
        job = AnalysisJob(
            id=job_id,
            resource_id=resource_id,
            question_set=question_set,
            analysis_config=analysis_config,
        )

        # Send job to NATS
        await self.js.publish("analysis.job.submit", json.dumps(asdict(job), default=str).encode())

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

    # For Workers to automatically process document.ready events
    async def process_document_ready_events(
        self,
        config: Optional[DocumentReadyProcessingConfig] = None,
    ):
        """
        Automatically process document.ready events based on configuration.

        Args:
            config: DocumentReadyProcessingConfig with processing options.
                   If None, uses default configuration (pull chunks, run analysis, store results).
        """
        if config is None:
            config = DocumentReadyProcessingConfig()

        await self.js.subscribe("document.ready", cb=lambda msg: self._handle_document_ready(msg, config))
        logger.info(f"Started processing document.ready events from NATS with config: {config.to_dict()}")

        # Keep processing
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping document.ready processor")

    async def _handle_document_ready(
        self,
        msg,
        config: DocumentReadyProcessingConfig,
    ):
        """Handle a document.ready event based on configuration"""
        try:
            event_data = json.loads(msg.data.decode())
            event = DocumentReadyEvent(**event_data)

            logger.info(
                f"Received document.ready for resource {event.resource_id} "
                f"(config: pull_chunks={config.pull_chunks}, "
                f"store_to_backend={config.store_to_backend})"
            )

            # Step 1: Get chunks (pull from backend or use provided)
            chunks = None
            if config.pull_chunks:
                logger.info(f"Pulling chunks from backend for resource {event.resource_id}")
                chunks = await self._get_chunks_for_resource(
                    event.resource_id, config.chunk_retrieval_method, config.max_chunks
                )
                if not chunks:
                    logger.error(f"No chunks found for resource {event.resource_id}")
                    if config.ack_on_error:
                        await msg.ack()
                    return
                logger.info(f"Retrieved {len(chunks)} chunks for resource {event.resource_id}")
            else:
                # Check if chunks are provided in event metadata
                if hasattr(event, "chunks") and event.chunks:
                    chunks = event.chunks
                    logger.info(f"Using {len(chunks)} chunks provided in event")
                else:
                    logger.warning(f"No chunks provided and pull_chunks=False for resource {event.resource_id}")
                    if config.ack_on_error:
                        await msg.ack()
                    return

            # Step 2: Run analysis
            logger.info(f"Running analysis for resource {event.resource_id}")
            analysis_result = await self._run_analysis(chunks, config.question_set, config.analysis_config)

            # Step 3: Store results back to backend (if configured)
            if config.store_to_backend:
                logger.info(f"Storing analysis results back to backend for resource {event.resource_id}")
                await self._store_analysis_to_backend(event.resource_id, analysis_result, config.question_set)

            await msg.ack()
            logger.info(f"Successfully processed document.ready for resource {event.resource_id}")

        except Exception as e:
            logger.error(f"Error processing document.ready event: {e}", exc_info=True)
            if config.ack_on_error:
                await msg.ack()  # Ack even on error to avoid redelivery loops

    async def _get_chunks_for_resource(
        self,
        resource_id: str,
        method: str = "search",
        max_chunks: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get chunks for a resource using specified method.

        Args:
            resource_id: Resource ID
            method: "search" (use /search/ endpoint) or "direct" (use /resources/{id}/chunks)
            max_chunks: Maximum number of chunks to return (None = no limit)

        Returns:
            List of chunk dictionaries
        """
        if method == "direct":
            # Try direct endpoint first
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.search_backend.base_url}/resources/{resource_id}/chunks") as response:
                        if response.status == 200:
                            data = await response.json()
                            chunks = data.get("chunks", [])
                            if max_chunks:
                                chunks = chunks[:max_chunks]
                            return chunks
            except Exception as e:
                logger.warning(f"Direct chunk retrieval failed for {resource_id}, falling back to search: {e}")

        # Default: use search endpoint (existing method)
        chunks = await self.search_backend.get_resource_chunks(resource_id)
        if max_chunks and chunks:
            chunks = chunks[:max_chunks]
        return chunks

    async def _store_analysis_to_backend(
        self,
        resource_id: str,
        analysis_result: Dict[str, Any],
        question_set: str,
    ):
        """Store analysis results back to backend"""
        try:
            # Use BackendService to store results (synchronous, so run in executor)
            import asyncio

            from report_analyst_search_backend.backend_service import BackendService
            from report_analyst_search_backend.config import BackendConfig

            # Create BackendService from the base_url
            config = BackendConfig(use_backend=True, backend_url=self.search_backend.base_url)
            backend_service = BackendService(config)

            # Run synchronous store_analysis_results in executor
            loop = asyncio.get_event_loop()
            result_id = await loop.run_in_executor(
                None,
                backend_service.store_analysis_results,
                resource_id,
                analysis_result,
                question_set,
                {"source": "nats_auto_index"},
            )

            if result_id:
                logger.info(f"Stored analysis results for resource {resource_id}: {result_id}")
            else:
                logger.warning(f"Failed to store analysis results for resource {resource_id}")

        except Exception as e:
            logger.error(f"Error storing analysis to backend: {e}")

    async def _process_analysis_job(self, msg):
        """Process a single analysis job"""
        try:
            job_data = json.loads(msg.data.decode())
            job = AnalysisJob(**job_data)

            logger.info(f"Processing analysis job {job.id} for resource {job.resource_id}")

            # Update job status
            job.status = JobStatus.PROCESSING
            job.updated_at = datetime.utcnow()

            # Send status update
            await self.js.publish("analysis.job.status", json.dumps(asdict(job), default=str).encode())

            # Get chunks from search backend (already processed)
            chunks = await self.search_backend.get_resource_chunks(job.resource_id)

            # Run analysis using report analyst toolkit
            analysis_result = await self._run_analysis(chunks, job.question_set, job.analysis_config)

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
            await self.js.publish("analysis.job.completed", json.dumps(asdict(job), default=str).encode())

            await msg.ack()
            logger.info(f"Analysis job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Error processing analysis job {job.id}: {e}")

            # Mark job as failed
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.utcnow()

            await self.js.publish("analysis.job.failed", json.dumps(asdict(job), default=str).encode())

            await msg.ack()

    async def _run_analysis(self, chunks: List[Dict[str, Any]], question_set: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the actual analysis using report analyst toolkit"""
        # Import here to avoid circular imports
        from .analysis_toolkit import analyze_document_with_chunks

        # Convert chunks to the format expected by analysis toolkit
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append({"text": chunk["text"], "metadata": chunk["metadata"]})

        # Run analysis
        result = await analyze_document_with_chunks(chunks=formatted_chunks, question_set=question_set, config=config)

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

    async def notify_document_ready(self, resource_id: str, document_url: str, chunks_count: int):
        """Notify that document processing is complete"""
        await self.coordinator.publish_document_ready(resource_id, document_url, chunks_count)


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
        await self.coordinator.js.subscribe("analysis.job.completed", cb=self._handle_completed)
        await self.coordinator.js.subscribe("analysis.job.failed", cb=self._handle_failed)
        await self.coordinator.js.subscribe("analysis.job.status", cb=self._handle_status)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.coordinator.disconnect()

    async def analyze_resource(self, resource_id: str, question_set: str, analysis_config: Dict[str, Any]) -> str:
        """Submit analysis job for a resource that's already processed"""
        job_id = await self.coordinator.submit_analysis_job(resource_id, question_set, analysis_config)
        return job_id

    async def wait_for_completion(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for job completion"""
        start_time = datetime.utcnow()

        while True:
            if job_id in self.job_results:
                result = self.job_results[job_id]
                if result["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    return result

            if (datetime.utcnow() - start_time).seconds > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

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
