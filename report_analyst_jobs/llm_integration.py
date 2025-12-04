"""
LLM Integration via NATS

This module allows report-analyst to use the search backend's LLM capabilities
(including Ollama) via NATS messaging, centralizing LLM management.

Flow:
1. Report-analyst sends LLM request to NATS
2. Search backend worker processes LLM request using its existing setup
3. Response sent back via NATS

Benefits:
- Centralized LLM management (models, costs, scaling)
- Use search backend's Ollama integration
- No duplicate LLM configurations
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import nats

logger = logging.getLogger(__name__)


class LLMRequestType(str, Enum):
    ANALYZE_QUESTION = "analyze_question"
    SUMMARIZE = "summarize"
    EXTRACT_KEYWORDS = "extract_keywords"
    CUSTOM = "custom"


@dataclass
class LLMRequest:
    """LLM request sent via NATS"""

    id: str
    request_type: LLMRequestType
    prompt: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMResponse:
    """LLM response received via NATS"""

    request_id: str
    response: str
    model_used: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class NATSLLMClient:
    """Client for sending LLM requests via NATS"""

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.js = None
        self.pending_requests = {}

    async def connect(self):
        """Connect to NATS"""
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()

        # Create LLM streams
        try:
            await self.js.add_stream(name="LLM_REQUESTS", subjects=["llm.*"])
        except Exception as e:
            logger.info(f"LLM stream may already exist: {e}")

        # Subscribe to responses
        await self.js.subscribe("llm.response", cb=self._handle_response)
        logger.info("Connected to NATS LLM service")

    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()

    async def analyze_question(
        self, question: str, context_chunks: List[str], model: str = "gpt-4o-mini"
    ) -> str:
        """
        Analyze a question against context chunks using search backend LLM.

        This replaces direct LLM calls in report-analyst.
        """
        # Build prompt for question analysis
        context = "\n\n".join(
            [f"Chunk {i+1}: {chunk}" for i, chunk in enumerate(context_chunks)]
        )

        prompt = f"""Please analyze the following question based on the provided context:

Question: {question}

Context:
{context}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain sufficient information to answer the question, please state that clearly.

Answer:"""

        system_prompt = """You are a helpful assistant analyzing documents. Provide accurate, detailed answers based only on the provided context. Be specific and cite relevant parts of the context when possible."""

        request = LLMRequest(
            id=str(uuid.uuid4()),
            request_type=LLMRequestType.ANALYZE_QUESTION,
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            metadata={
                "question": question,
                "chunk_count": len(context_chunks),
                "source": "report_analyst",
            },
        )

        return await self._send_request(request)

    async def summarize_chunks(
        self,
        chunks: List[str],
        summary_type: str = "general",
        model: str = "gpt-4o-mini",
    ) -> str:
        """Summarize document chunks using search backend LLM"""

        content = "\n\n".join(
            [f"Section {i+1}: {chunk}" for i, chunk in enumerate(chunks)]
        )

        prompt = f"""Please provide a {summary_type} summary of the following document sections:

{content}

Summary:"""

        system_prompt = f"You are a helpful assistant creating {summary_type} summaries. Be concise but comprehensive."

        request = LLMRequest(
            id=str(uuid.uuid4()),
            request_type=LLMRequestType.SUMMARIZE,
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            metadata={
                "summary_type": summary_type,
                "chunk_count": len(chunks),
                "source": "report_analyst",
            },
        )

        return await self._send_request(request)

    async def _send_request(self, request: LLMRequest) -> str:
        """Send LLM request and wait for response"""
        # Store request for response matching
        self.pending_requests[request.id] = asyncio.Event()

        # Send request
        await self.js.publish(
            "llm.request", json.dumps(asdict(request), default=str).encode()
        )

        # Wait for response (with timeout)
        try:
            await asyncio.wait_for(
                self.pending_requests[request.id].wait(), timeout=60.0
            )

            # Get response
            response_data = self.pending_requests.get(f"{request.id}_response")
            if response_data and not response_data.get("error"):
                return response_data["response"]
            else:
                error = (
                    response_data.get("error", "Unknown error")
                    if response_data
                    else "No response received"
                )
                raise Exception(f"LLM request failed: {error}")

        except asyncio.TimeoutError:
            raise Exception("LLM request timed out")
        finally:
            # Cleanup
            self.pending_requests.pop(request.id, None)
            self.pending_requests.pop(f"{request.id}_response", None)

    async def _handle_response(self, msg):
        """Handle LLM response from NATS"""
        try:
            response_data = json.loads(msg.data.decode())
            request_id = response_data.get("request_id")

            if request_id in self.pending_requests:
                # Store response data
                self.pending_requests[f"{request_id}_response"] = response_data
                # Signal completion
                self.pending_requests[request_id].set()

            await msg.ack()
        except Exception as e:
            logger.error(f"Error handling LLM response: {e}")


class NATSLLMWorker:
    """Worker that processes LLM requests using search backend capabilities"""

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.js = None

    async def connect(self):
        """Connect to NATS"""
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()
        logger.info("LLM worker connected to NATS")

    async def start_processing(self):
        """Start processing LLM requests"""
        await self.js.subscribe("llm.request", cb=self._process_request)
        logger.info("LLM worker started processing requests")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("LLM worker shutting down")

    async def _process_request(self, msg):
        """Process a single LLM request using search backend LLM"""
        try:
            request_data = json.loads(msg.data.decode())
            request = LLMRequest(**request_data)

            logger.info(f"Processing LLM request {request.id} - {request.request_type}")

            # Use search backend's LLM service
            response_text = await self._call_search_backend_llm(request)

            # Send response
            response = LLMResponse(
                request_id=request.id,
                response=response_text,
                model_used=request.model,
                processing_time=1.5,  # Could track actual time
            )

            await self.js.publish(
                "llm.response", json.dumps(asdict(response), default=str).encode()
            )

            await msg.ack()
            logger.info(f"LLM request {request.id} completed")

        except Exception as e:
            logger.error(f"Error processing LLM request: {e}")

            # Send error response
            error_response = LLMResponse(
                request_id=request.id,
                response="",
                model_used=request.model,
                error=str(e),
            )

            await self.js.publish(
                "llm.response", json.dumps(asdict(error_response), default=str).encode()
            )
            await msg.ack()

    async def _call_search_backend_llm(self, request: LLMRequest) -> str:
        """Call search backend's LLM service (Ollama or OpenAI)"""
        # Import search backend's LLM service
        # This would use the existing EmbeddingService or similar from search backend

        try:
            # For MVP, simulate using search backend's LLM logic
            # In reality, this would import and use:
            # from search.backend.app.services import EmbeddingService
            # service = EmbeddingService()
            # response = await service.generate_text(request.prompt, request.model)

            # Simulated response for now
            if request.request_type == LLMRequestType.ANALYZE_QUESTION:
                return f"Analysis for question using {request.model}: Based on the provided context, here is a comprehensive answer..."
            elif request.request_type == LLMRequestType.SUMMARIZE:
                return f"Summary using {request.model}: This document discusses key topics including..."
            else:
                return f"Response using {request.model}: {request.prompt[:100]}..."

        except Exception as e:
            logger.error(f"Search backend LLM call failed: {e}")
            raise


# Integration with existing analysis toolkit
async def get_llm_client() -> NATSLLMClient:
    """Get a connected LLM client for use in analysis toolkit"""
    client = NATSLLMClient()
    await client.connect()
    return client


# Example usage
async def example_llm_usage():
    """Example of using centralized LLM via NATS"""
    async with NATSLLMClient() as client:
        await client.connect()

        # Analyze a question
        answer = await client.analyze_question(
            question="What are the main climate risks mentioned?",
            context_chunks=[
                "Climate change poses significant risks to our operations...",
                "Physical risks include extreme weather events...",
            ],
            model="gpt-4o-mini",
        )

        print(f"Analysis result: {answer}")

        await client.disconnect()


if __name__ == "__main__":
    # Start LLM worker
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "worker":

        async def run_worker():
            worker = NATSLLMWorker()
            await worker.connect()
            await worker.start_processing()

        asyncio.run(run_worker())
    else:
        asyncio.run(example_llm_usage())
