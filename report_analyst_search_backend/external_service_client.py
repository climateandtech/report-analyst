"""
External Service Client

Client for external services to interact with Report Analyst.
Supports both NATS and HTTP communication methods.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import aiohttp
import nats
from nats.js import JetStreamContext

from .external_service_handler import ExternalServiceReadyEvent

logger = logging.getLogger(__name__)


class ExternalServiceClient:
    """Client for external services to interact with Report Analyst"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        nats_url: Optional[str] = None,
    ):
        """
        Initialize external service client.

        Args:
            base_url: Base URL for HTTP API (defaults to env var)
            nats_url: NATS server URL (defaults to env var)
        """
        self.base_url = base_url or os.getenv(
            "REPORT_ANALYST_API_URL", "http://localhost:8000"
        )
        self.nats_url = nats_url or os.getenv("NATS_URL", "nats://localhost:4222")
        self.nc = None
        self.js = None

    async def connect_nats(self):
        """Connect to NATS server"""
        if not self.nc or not self.nc.is_connected:
            try:
                self.nc = await nats.connect(self.nats_url)
                self.js = self.nc.jetstream()
                logger.info("Connected to NATS for external service client")
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

    async def notify_ready(
        self,
        service_id: str,
        request_id: str,
        content_type: str,  # "s3_url", "chunks", or "pages"
        s3_url: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
        chunks: Optional[List[Dict]] = None,
        pages: Optional[List[Dict]] = None,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        metadata: Optional[Dict] = None,
        method: str = "nats",  # "nats" or "http"
    ) -> bool:
        """
        Notify Report Analyst that external service processing is complete.

        Args:
            service_id: External service identifier
            request_id: Request identifier from external service
            content_type: Type of content ("s3_url", "chunks", or "pages")
            s3_url: S3 URL if content_type is "s3_url"
            s3_bucket: S3 bucket name
            s3_key: S3 object key
            chunks: Pre-processed chunks if content_type is "chunks"
            pages: Pre-processed pages if content_type is "pages"
            filename: Original filename
            file_size: File size in bytes
            metadata: Additional metadata
            method: Communication method ("nats" or "http")

        Returns:
            True if notification sent successfully
        """
        notification = ExternalServiceReadyEvent(
            service_id=service_id,
            request_id=request_id,
            content_type=content_type,
            s3_url=s3_url,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            chunks=chunks,
            pages=pages,
            filename=filename,
            file_size=file_size,
            metadata=metadata,
        )

        if method == "nats":
            return await self._notify_via_nats(notification)
        else:
            return await self._notify_via_http(notification)

    async def _notify_via_nats(self, notification: ExternalServiceReadyEvent) -> bool:
        """Send notification via NATS"""
        try:
            await self.connect_nats()

            # Convert to dict for JSON serialization
            notification_dict = {
                "service_id": notification.service_id,
                "request_id": notification.request_id,
                "content_type": notification.content_type,
                "s3_url": notification.s3_url,
                "s3_bucket": notification.s3_bucket,
                "s3_key": notification.s3_key,
                "chunks": notification.chunks,
                "pages": notification.pages,
                "filename": notification.filename,
                "file_size": notification.file_size,
                "metadata": notification.metadata,
            }

            message_data = json.dumps(notification_dict).encode()
            await self.js.publish("external.service.ready", message_data)
            logger.info(
                f"Published external service notification via NATS: "
                f"{notification.service_id}/{notification.request_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to notify via NATS: {e}")
            return False

    async def _notify_via_http(self, notification: ExternalServiceReadyEvent) -> bool:
        """Send notification via HTTP"""
        try:
            url = f"{self.base_url}/external/services/{notification.service_id}/notify"

            notification_dict = {
                "service_id": notification.service_id,
                "request_id": notification.request_id,
                "content_type": notification.content_type,
                "s3_url": notification.s3_url,
                "s3_bucket": notification.s3_bucket,
                "s3_key": notification.s3_key,
                "chunks": notification.chunks,
                "pages": notification.pages,
                "filename": notification.filename,
                "file_size": notification.file_size,
                "metadata": notification.metadata,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=notification_dict) as response:
                    if response.status == 200:
                        logger.info(
                            f"Sent external service notification via HTTP: "
                            f"{notification.service_id}/{notification.request_id}"
                        )
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"HTTP notification failed: {response.status} - {error_text}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Failed to notify via HTTP: {e}")
            return False

    async def request_analysis(
        self,
        service_id: str,
        external_request_id: str,
        content: Union[str, List[Dict]],  # S3 URL or chunks
        question_set: str,
        analysis_config: Dict[str, Any],
        response_method: str = "nats",  # "nats" or "poll"
        method: str = "http",  # "nats" or "http" for request
    ) -> Optional[str]:
        """
        Request analysis on external service content.

        Args:
            service_id: External service identifier
            external_request_id: Original request ID from external service
            content: S3 URL (str) or chunks (List[Dict])
            question_set: Question set identifier (e.g., "tcfd")
            analysis_config: Analysis configuration
            response_method: How to receive results ("nats" or "poll")
            method: How to send request ("nats" or "http")

        Returns:
            Analysis request ID if successful, None otherwise
        """
        # Determine content type
        if isinstance(content, str):
            content_type = "s3_url"
            s3_url = content
            chunks = None
        else:
            content_type = "chunks"
            s3_url = None
            chunks = content

        request_data = {
            "service_id": service_id,
            "external_request_id": external_request_id,
            "content_type": content_type,
            "s3_url": s3_url,
            "chunks": chunks,
            "question_set": question_set,
            "analysis_config": analysis_config,
            "response_method": response_method,
        }

        if method == "nats":
            return await self._request_analysis_via_nats(request_data)
        else:
            return await self._request_analysis_via_http(service_id, request_data)

    async def _request_analysis_via_nats(self, request_data: Dict) -> Optional[str]:
        """Request analysis via NATS"""
        try:
            await self.connect_nats()

            # Generate request ID
            import uuid

            request_id = str(uuid.uuid4())
            request_data["request_id"] = request_id

            message_data = json.dumps(request_data).encode()
            await self.js.publish("external.service.analysis.request", message_data)
            logger.info(f"Published analysis request via NATS: {request_id}")
            return request_id

        except Exception as e:
            logger.error(f"Failed to request analysis via NATS: {e}")
            return None

    async def _request_analysis_via_http(
        self, service_id: str, request_data: Dict
    ) -> Optional[str]:
        """Request analysis via HTTP"""
        try:
            url = f"{self.base_url}/external/services/{service_id}/analyze"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        request_id = result.get("request_id")
                        logger.info(
                            f"Submitted analysis request via HTTP: {request_id}"
                        )
                        return request_id
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"HTTP analysis request failed: {response.status} - {error_text}"
                        )
                        return None

        except Exception as e:
            logger.error(f"Failed to request analysis via HTTP: {e}")
            return None

    async def get_results(
        self, service_id: str, request_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Poll for analysis results.

        Args:
            service_id: External service identifier
            request_id: Analysis request identifier

        Returns:
            Analysis results if available, None otherwise
        """
        try:
            url = f"{self.base_url}/external/services/{service_id}/results/{request_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        results = await response.json()
                        logger.info(f"Retrieved analysis results: {request_id}")
                        return results
                    elif response.status == 404:
                        logger.info(f"Results not yet available: {request_id}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to get results: {response.status} - {error_text}"
                        )
                        return None

        except Exception as e:
            logger.error(f"Error polling for results: {e}")
            return None
