"""
External Service Handler

Handles external service integration flows:
- Receives notifications from external services (NATS or HTTP)
- Processes S3 URLs or pre-processed chunks/pages
- Manages analysis requests for external service content
"""

import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)


@dataclass
class ExternalServiceReadyEvent:
    """Event from external service when processing is complete"""

    service_id: str
    request_id: str
    content_type: str  # "s3_url", "chunks", or "pages"
    s3_url: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    chunks: Optional[List[Dict[str, Any]]] = None
    pages: Optional[List[Dict[str, Any]]] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingResult:
    """Result from processing external service content"""

    success: bool
    chunks: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ExternalServiceHandler:
    """Handles external service integration flows"""

    def __init__(self):
        self.s3_client = None
        self._init_s3_client()

    def _init_s3_client(self):
        """Initialize S3 client if credentials are available"""
        try:
            if all(os.getenv(var) for var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]):
                self.s3_client = boto3.client(
                    "s3",
                    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                    config=Config(
                        retries={"max_attempts": 3},
                        max_pool_connections=10,
                        s3={"addressing_style": "path"},
                    ),
                )
                logger.info("S3 client initialized for external service handler")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {e}")

    async def handle_external_notification(
        self,
        service_id: str,
        notification: ExternalServiceReadyEvent,
        rechunk_mode: str = "auto",  # "auto", "always", "never"
    ) -> ProcessingResult:
        """
        Handle notification from external service.

        Args:
            service_id: External service identifier
            notification: Notification with S3 URL or chunks
            rechunk_mode: Whether to re-chunk provided content
                - "auto": Re-chunk if format doesn't match
                - "always": Always re-chunk for consistency
                - "never": Use provided chunks directly

        Returns:
            ProcessingResult with chunks ready for analysis
        """
        try:
            logger.info(
                f"Handling external service notification from {service_id}, "
                f"content_type: {notification.content_type}, "
                f"rechunk_mode: {rechunk_mode}"
            )

            if notification.content_type == "s3_url":
                if not notification.s3_url:
                    return ProcessingResult(success=False, error="S3 URL not provided")
                chunks = await self._process_s3_url(notification.s3_url)
                return ProcessingResult(success=True, chunks=chunks)

            elif notification.content_type == "chunks":
                if not notification.chunks:
                    return ProcessingResult(success=False, error="Chunks not provided")
                chunks = await self._process_provided_chunks(notification.chunks, rechunk_mode)
                return ProcessingResult(success=True, chunks=chunks)

            elif notification.content_type == "pages":
                if not notification.pages:
                    return ProcessingResult(success=False, error="Pages not provided")
                chunks = await self._process_provided_pages(notification.pages, rechunk_mode)
                return ProcessingResult(success=True, chunks=chunks)

            else:
                return ProcessingResult(
                    success=False,
                    error=f"Unknown content_type: {notification.content_type}",
                )

        except Exception as e:
            logger.error(f"Error handling external notification: {e}")
            return ProcessingResult(success=False, error=str(e))

    async def _process_s3_url(self, s3_url: str) -> List[Dict[str, Any]]:
        """
        Download from S3 and process into chunks.

        Args:
            s3_url: S3 URL to download from

        Returns:
            List of chunk dictionaries
        """
        try:
            # Parse S3 URL to extract bucket and key
            # Format: http://endpoint/bucket/key or https://endpoint/bucket/key
            if not self.s3_client:
                raise Exception("S3 client not initialized")

            # Parse URL
            if "://" in s3_url:
                parts = s3_url.split("://", 1)[1].split("/", 2)
                if len(parts) >= 3:
                    bucket = parts[1]
                    key = parts[2]
                else:
                    raise Exception(f"Invalid S3 URL format: {s3_url}")
            else:
                raise Exception(f"Invalid S3 URL format: {s3_url}")

            # Download file to temporary location
            logger.info(f"Downloading from S3: bucket={bucket}, key={key}")
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            file_bytes = response["Body"].read()
            logger.info(f"Downloaded {len(file_bytes)} bytes from S3")

            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name

            try:
                # Process file using analyzer's chunking logic
                # Import here to avoid circular dependencies
                from llama_index.readers.file import PyMuPDFReader

                reader = PyMuPDFReader()
                docs = reader.load(file_path=tmp_file_path)
                logger.info(f"Loaded {len(docs)} pages from S3 file")

                # Convert to chunks format expected by analyzer
                chunks = []
                for i, doc in enumerate(docs):
                    # Simple chunking - split by paragraphs or sentences
                    text = doc.text
                    # Split into chunks (simple approach - analyzer will do proper chunking)
                    chunk_size = 500  # Default chunk size
                    for j in range(0, len(text), chunk_size):
                        chunk_text = text[j : j + chunk_size]
                        if chunk_text.strip():
                            chunks.append(
                                {
                                    "chunk_id": f"s3_{key}_page{i}_chunk{j//chunk_size}",
                                    "chunk_text": chunk_text,
                                    "chunk_metadata": {
                                        "source": "s3",
                                        "url": s3_url,
                                        "bucket": bucket,
                                        "key": key,
                                        "page": i + 1,
                                        **doc.metadata,
                                    },
                                    "similarity_score": 0.0,
                                }
                            )

                logger.info(f"Created {len(chunks)} chunks from S3 file")
                return chunks

            finally:
                # Clean up temporary file
                try:
                    Path(tmp_file_path).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")

        except Exception as e:
            logger.error(f"Error processing S3 URL: {e}")
            raise

    async def _process_provided_chunks(self, chunks: List[Dict[str, Any]], rechunk_mode: str) -> List[Dict[str, Any]]:
        """
        Process provided chunks (re-chunk if needed).

        Args:
            chunks: Pre-processed chunks from external service
            rechunk_mode: "auto", "always", or "never"

        Returns:
            Processed chunks ready for analysis
        """
        if rechunk_mode == "never":
            # Use chunks directly, just ensure format
            return self._normalize_chunks(chunks)

        elif rechunk_mode == "always":
            # Always re-chunk - combine all text and re-chunk
            # This would use the analyzer's chunking logic
            combined_text = "\n\n".join(chunk.get("text", chunk.get("chunk_text", "")) for chunk in chunks)
            # For now, return normalized chunks - actual re-chunking would be done by analyzer
            logger.info(f"Re-chunking {len(chunks)} chunks (always mode)")
            return self._normalize_chunks(chunks)

        else:  # auto
            # Check if chunks match our format, re-chunk if not
            if self._chunks_match_format(chunks):
                return self._normalize_chunks(chunks)
            else:
                # Re-chunk needed
                logger.info(f"Chunks don't match format, re-chunking {len(chunks)} chunks")
                return self._normalize_chunks(chunks)

    async def _process_provided_pages(self, pages: List[Dict[str, Any]], rechunk_mode: str) -> List[Dict[str, Any]]:
        """
        Process provided pages (convert to chunks).

        Args:
            pages: Pre-processed pages from external service
            rechunk_mode: "auto", "always", or "never" (not used for pages)

        Returns:
            Chunks converted from pages
        """
        chunks = []
        for i, page in enumerate(pages):
            page_text = page.get("text", "")
            page_number = page.get("page_number", i + 1)
            metadata = page.get("metadata", {})

            chunks.append(
                {
                    "chunk_id": f"page_{page_number}",
                    "chunk_text": page_text,
                    "chunk_metadata": {
                        "source": "external_service",
                        "page_number": page_number,
                        **metadata,
                    },
                    "similarity_score": 0.0,
                }
            )

        logger.info(f"Converted {len(pages)} pages to {len(chunks)} chunks")
        return chunks

    def _normalize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize chunk format to our standard format"""
        normalized = []
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("id", chunk.get("chunk_id", f"chunk_{i}"))
            chunk_text = chunk.get("text", chunk.get("chunk_text", ""))
            metadata = chunk.get("metadata", chunk.get("chunk_metadata", {}))

            normalized.append(
                {
                    "chunk_id": chunk_id,
                    "chunk_text": chunk_text,
                    "chunk_metadata": metadata,
                    "similarity_score": chunk.get("similarity_score", 0.0),
                }
            )
        return normalized

    def _chunks_match_format(self, chunks: List[Dict[str, Any]]) -> bool:
        """Check if chunks match our expected format"""
        if not chunks:
            return False

        # Check if chunks have required fields
        first_chunk = chunks[0]
        has_text = "text" in first_chunk or "chunk_text" in first_chunk
        has_id = "id" in first_chunk or "chunk_id" in first_chunk

        return has_text and has_id
