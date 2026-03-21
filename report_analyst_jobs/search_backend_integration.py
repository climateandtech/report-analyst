"""
Search Backend Integration for NATS

This module provides integration functions for the search backend to publish
NATS events when document processing is complete.

Usage in search backend services.py:
    from report_analyst_jobs.search_backend_integration import notify_document_ready

    # At the end of your PDF processing Celery task:
    await notify_document_ready(resource_id, document_url, chunks_count)
"""

import asyncio
import logging
from typing import Optional

from .nats_integration import NATSSearchBackendPublisher

logger = logging.getLogger(__name__)


async def notify_document_ready(
    resource_id: str,
    document_url: str,
    chunks_count: int,
    nats_url: str = "nats://localhost:4222",
):
    """
    Notify NATS that a document has been processed and is ready for analysis.

    This function should be called at the end of the search backend's PDF processing
    when the document has been chunked and embedded.

    Args:
        resource_id: The resource ID from the search backend
        document_url: The original document URL
        chunks_count: Number of chunks created
        nats_url: NATS server URL
    """
    try:
        async with NATSSearchBackendPublisher(nats_url) as publisher:
            await publisher.notify_document_ready(resource_id, document_url, chunks_count)
            logger.info(f"Successfully notified NATS that document {resource_id} is ready")
    except Exception as e:
        logger.error(f"Failed to notify NATS about document {resource_id}: {e}")
        # Don't raise - this is a nice-to-have feature


def notify_document_ready_sync(
    resource_id: str,
    document_url: str,
    chunks_count: int,
    nats_url: str = "nats://localhost:4222",
):
    """
    Synchronous wrapper for notify_document_ready.

    Use this in synchronous contexts like Celery tasks.
    """
    try:
        asyncio.run(notify_document_ready(resource_id, document_url, chunks_count, nats_url))
    except Exception as e:
        logger.error(f"Failed to notify NATS about document {resource_id}: {e}")


class SearchBackendNATSIntegration:
    """
    Integration class for search backend to manage NATS connections.

    Use this if you want to maintain a persistent NATS connection
    instead of creating one for each notification.
    """

    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.publisher = None
        self._connected = False

    async def connect(self):
        """Connect to NATS"""
        if not self._connected:
            self.publisher = NATSSearchBackendPublisher(self.nats_url)
            await self.publisher.__aenter__()
            self._connected = True
            logger.info("Connected to NATS for search backend integration")

    async def disconnect(self):
        """Disconnect from NATS"""
        if self._connected and self.publisher:
            await self.publisher.__aexit__(None, None, None)
            self._connected = False
            logger.info("Disconnected from NATS")

    async def notify_document_ready(self, resource_id: str, document_url: str, chunks_count: int):
        """Notify that document is ready"""
        if not self._connected:
            await self.connect()

        await self.publisher.notify_document_ready(resource_id, document_url, chunks_count)
        logger.info(f"Notified NATS that document {resource_id} is ready")


# Example integration with search backend services.py
"""
Example usage in search backend services.py:

# Add this import at the top
from report_analyst_jobs.search_backend_integration import notify_document_ready_sync

# In your embed_chunks_service function (or wherever PDF processing completes):
def embed_chunks_service(db: Session, resource_id: uuid.UUID, batch_size: int = 10):
    logging.info(f"Starting embed_chunks_service for resource_id: {resource_id}")
    
    # ... existing embedding logic ...
    
    # After successful embedding, notify NATS
    try:
        resource = crud.get_resource(db, resource_id)
        if resource:
            chunks_count = len(resource.chunks)
            notify_document_ready_sync(
                resource_id=str(resource_id),
                document_url=resource.url,
                chunks_count=chunks_count
            )
            logging.info(f"Notified NATS that resource {resource_id} is ready for analysis")
    except Exception as e:
        logging.error(f"Failed to notify NATS: {e}")
        # Continue - this is not critical for the main processing
    
    return True

# Alternative async version for async services:
async def embed_chunks_service_async(db: Session, resource_id: uuid.UUID, batch_size: int = 10):
    logging.info(f"Starting embed_chunks_service for resource_id: {resource_id}")
    
    # ... existing embedding logic ...
    
    # After successful embedding, notify NATS
    try:
        resource = crud.get_resource(db, resource_id)
        if resource:
            chunks_count = len(resource.chunks)
            await notify_document_ready(
                resource_id=str(resource_id),
                document_url=resource.url,
                chunks_count=chunks_count
            )
            logging.info(f"Notified NATS that resource {resource_id} is ready for analysis")
    except Exception as e:
        logging.error(f"Failed to notify NATS: {e}")
        # Continue - this is not critical for the main processing
    
    return True
"""
