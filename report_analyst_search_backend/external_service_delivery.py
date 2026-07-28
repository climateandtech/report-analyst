"""
External Service Result Delivery

Delivers analysis results to external services via multiple methods:
- NATS: Publish to external.service.analysis.response
- HTTP Poll: Store results, accessible via GET endpoint
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import nats
from nats.js import JetStreamContext

logger = logging.getLogger(__name__)


class ExternalServiceDelivery:
    """Delivers analysis results to external services via multiple methods"""

    def __init__(self, nats_url: Optional[str] = None):
        """
        Initialize result delivery system.

        Args:
            nats_url: NATS server URL (defaults to env var)
        """
        self.nats_url = nats_url or os.getenv("NATS_URL", "nats://localhost:4222")
        self.nc = None
        self.js = None
        # In-memory storage for poll-based results (in production, use database)
        self._result_storage: Dict[str, Dict[str, Any]] = {}

    async def connect_nats(self):
        """Connect to NATS server"""
        if not self.nc or not self.nc.is_connected:
            try:
                self.nc = await nats.connect(self.nats_url)
                self.js = self.nc.jetstream()
                logger.info("Connected to NATS for result delivery")
            except Exception as e:
                logger.error(f"Failed to connect to NATS: {e}")
                raise

    async def disconnect_nats(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()
            self.nc = None
            self.js = None
            logger.info("Disconnected from NATS")

    async def deliver_results(
        self,
        service_id: str,
        request_id: str,
        external_request_id: str,
        results: Dict[str, Any],  # answers + top_chunks
        response_method: str,  # "nats" or "poll"
        status: str = "completed",  # "completed" or "failed"
        error: Optional[str] = None,
    ) -> bool:
        """
        Deliver results via configured method.

        Args:
            service_id: External service identifier
            request_id: Analysis request identifier
            external_request_id: Original request ID from external service
            results: Analysis results (answers + top_chunks)
            response_method: Delivery method ("nats" or "poll")
            status: Result status ("completed" or "failed")
            error: Error message if status is "failed"

        Returns:
            True if delivery successful
        """
        response_data = {
            "request_id": request_id,
            "service_id": service_id,
            "external_request_id": external_request_id,
            "status": status,
            "answers": results.get("answers", []),
            "top_chunks": results.get("top_chunks", []),
            "error": error,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if response_method == "nats":
            return await self._deliver_via_nats(response_data)
        elif response_method == "poll":
            return await self._deliver_via_poll(request_id, response_data)
        else:
            logger.error(f"Unknown response method: {response_method}")
            return False

    async def _deliver_via_nats(self, response_data: Dict[str, Any]) -> bool:
        """Deliver results via NATS"""
        try:
            await self.connect_nats()

            message_data = json.dumps(response_data).encode()
            await self.js.publish("external.service.analysis.response", message_data)
            logger.info(
                f"Published analysis results via NATS: " f"{response_data['service_id']}/{response_data['request_id']}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to deliver results via NATS: {e}")
            return False

    async def _deliver_via_poll(self, request_id: str, response_data: Dict[str, Any]) -> bool:
        """Store results for HTTP polling"""
        try:
            # Store results in memory (in production, use database)
            self._result_storage[request_id] = response_data
            logger.info(f"Stored analysis results for polling: {request_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store results for polling: {e}")
            return False

    def get_results(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored results for HTTP polling.

        Args:
            request_id: Analysis request identifier

        Returns:
            Analysis results if available, None otherwise
        """
        return self._result_storage.get(request_id)

    def clear_results(self, request_id: str):
        """Clear stored results (cleanup)"""
        self._result_storage.pop(request_id, None)
