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

        logger.info("Connected to NATS LLM service (per-request reply on llm.response.{id})")

    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()

    async def analyze_question(self, question: str, context_chunks: List[str], model: str = "gpt-4o-mini") -> str:
        """
        Analyze a question against context chunks using search backend LLM.

        This replaces direct LLM calls in report-analyst.
        """
        # Build prompt for question analysis
        context = "\n\n".join([f"Chunk {i+1}: {chunk}" for i, chunk in enumerate(context_chunks)])

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

        content = "\n\n".join([f"Section {i+1}: {chunk}" for i, chunk in enumerate(chunks)])

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
        """Send LLM request and wait for response on llm.response.{request_id}."""
        reply_subject = f"llm.response.{request.id}"
        future: asyncio.Future = asyncio.get_event_loop().create_future()

        async def on_reply(msg):
            try:
                data = json.loads(msg.data.decode())
                if data.get("request_id") != request.id:
                    return
                if data.get("error"):
                    if not future.done():
                        future.set_exception(RuntimeError(data["error"]))
                elif not future.done():
                    future.set_result(data.get("response", ""))
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)

        sub = await self.nc.subscribe(reply_subject, cb=on_reply)
        payload = {
            **asdict(request),
            "request_id": request.id,
            "reply_subject": reply_subject,
        }
        try:
            await self.js.publish("llm.request", json.dumps(payload, default=str).encode())
            return await asyncio.wait_for(future, timeout=120.0)
        except asyncio.TimeoutError:
            raise Exception("LLM request timed out") from None
        finally:
            await sub.unsubscribe()


class NATSLLMWorker:
    """
    Deprecated: LLM processing runs on ct-platform (app/llm_consumer.py), not in RA.
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "NATSLLMWorker was removed from report-analyst. "
            "Platform backend handles llm.request via llm_consumer."
        )


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
    asyncio.run(example_llm_usage())
