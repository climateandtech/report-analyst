"""
Enterprise S3+NATS Upload Service for Report Analyst

This module provides S3+NATS upload functionality following the same pattern
as the PDF service. This is an enterprise feature that requires:
- AWS S3 credentials
- NATS server with JetStream
- Backend configured to handle document.upload messages

Usage:
    from .s3_upload_service import S3UploadService

    uploader = S3UploadService(config)
    resource_id = await uploader.upload_pdf_via_s3_nats(file_bytes, filename)
"""

import json
import uuid
from config.nats_config import config as nats_config
import os
import boto3
import nats
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.config import Config

from .config import BackendConfig

# Set up logging
logger = logging.getLogger(__name__)


class S3UploadServiceError(Exception):
    """Exception raised for S3 upload service errors"""

    pass


class S3UploadService:
    """
    Enterprise S3+NATS upload service.

    Follows the same pattern as the PDF service:
    1. Upload PDF to S3
    2. Publish lightweight control message via NATS
    3. Backend processes and responds via NATS
    """

    def __init__(self, config: BackendConfig):
        self.config = config
        self.s3_bucket = self._get_s3_bucket()
        self.timeout = 120
        self.nc = None
        self.js = None

    async def connect(self):
        """Connect to NATS if not already connected"""
        if not self.nc or not self.nc.is_connected:
            try:
                # Close any existing connection first
                if self.nc:
                    await self.nc.close()

                # Load NATS URL from environment (like working test)
                nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
                nats_token = os.getenv("NATS_TOKEN")

                if nats_token:
                    if "://" in nats_url:
                        protocol, rest = nats_url.split("://", 1)
                        nats_url = f"{protocol}://{nats_token}@{rest}"

                # Use minimal connection options (like CLI)
                self.nc = await nats.connect(nats_url)
                # Initialize JetStream (CLI --jetstream works)
                self.js = self.nc.jetstream()
                logger.info("✅ Connected to NATS with JetStream")
            except Exception as e:
                logger.error(f"❌ Failed to connect to NATS: {e}")
                raise S3UploadServiceError(f"NATS connection failed: {str(e)}")

    async def close(self):
        """Close NATS connection if open"""
        if self.nc:
            try:
                await self.nc.close()
                self.nc = None
                self.js = None
                logger.info("🔌 Disconnected from NATS")
            except Exception as e:
                logger.error(f"❌ Error closing NATS connection: {e}")

    async def upload_pdf_via_s3_nats(self, file_bytes: bytes, filename: str) -> str:
        """
        Upload PDF using S3+NATS pattern.

        Args:
            file_bytes: PDF file content as bytes
            filename: Original filename

        Returns:
            resource_id: Backend resource ID or request_id

        Raises:
            S3UploadServiceError: If upload fails
        """
        request_id = str(uuid.uuid4())
        s3_key = f"report-analyst-uploads/{request_id}.pdf"

        try:
            # 1. Upload to S3
            s3_url = await self._upload_to_s3(file_bytes, s3_key, filename)

            # 2. Ensure NATS connection and publish
            await self.connect()

            # 3. Publish control message
            control_message = {
                "request_id": request_id,
                "s3_bucket": self.s3_bucket,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "filename": filename,
                "timestamp": datetime.utcnow().isoformat(),
                "file_size": len(file_bytes),
                "source": "report-analyst",
                "processing_timeout": self.timeout,
            }

            # Use centralized subject pattern (backend will forward docs.* → docs.process.*)
            upload_pattern = nats_config["subject_patterns"]["upload"]
            subject = upload_pattern.format(request_id=request_id)

            # Simple NATS publish - reliable delivery
            message_data = json.dumps(control_message).encode()
            logger.info(
                f"🔍 Publishing {len(message_data)} bytes to subject: {subject}"
            )

            try:
                # Use JetStream publish (CLI --jetstream works)
                # Don't specify stream - let JetStream auto-route based on subject
                ack = await self.js.publish(subject, message_data)
                logger.info(f"📤 JetStream published message, ack: {ack}")

                # Close connection immediately (like CLI)
                await self.nc.close()
                self.nc = None
                self.js = None
                logger.info(f"✅ Published control message for {filename}")
                logger.info(f"🔌 Closed connection")

            except Exception as publish_error:
                logger.error(f"❌ NATS publish failed: {publish_error}")
                raise

            return request_id

        except Exception as e:
            # Cleanup S3 object on error
            try:
                await self._cleanup_s3_object(s3_key)
            except Exception as cleanup_e:
                logger.warning(f"⚠️ Failed to cleanup S3 object: {cleanup_e}")
            raise S3UploadServiceError(f"S3+NATS upload failed: {str(e)}")

    async def _upload_to_s3(self, file_bytes: bytes, s3_key: str, filename: str) -> str:
        """Upload file to S3 and return URL"""
        try:
            # Create S3 client with Hetzner configuration
            s3_client = boto3.client(
                "s3",
                endpoint_url=os.getenv("S3_ENDPOINT_URL"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_DEFAULT_REGION"),
                config=Config(
                    retries={"max_attempts": 3},
                    max_pool_connections=10,
                    s3={"addressing_style": "path"},  # Use path style for Hetzner
                ),
            )

            # Upload with metadata
            s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType="application/pdf",
                Metadata={
                    "original_filename": filename,
                    "uploaded_by": "report-analyst",
                    "upload_time": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"✅ Uploaded {filename} to S3")

            # Return S3 URL in path style
            endpoint = os.getenv("S3_ENDPOINT_URL").rstrip("/")
            return f"{endpoint}/{self.s3_bucket}/{s3_key}"

        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise S3UploadServiceError(f"S3 upload failed: {str(e)}")

    def _get_s3_bucket(self) -> str:
        """Get S3 bucket name from config or environment (matches backend/PDF service)"""
        return os.getenv("S3_BUCKET_NAME", "documents")

    async def _cleanup_s3_object(self, s3_key: str):
        """Clean up S3 object on error"""
        try:
            s3_client = boto3.client(
                "s3",
                endpoint_url=os.getenv("S3_ENDPOINT_URL"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_DEFAULT_REGION"),
                config=Config(
                    retries={"max_attempts": 3},
                    max_pool_connections=10,
                    s3={"addressing_style": "path"},  # Use path style for Hetzner
                ),
            )
            s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
            logger.info(f"✅ Cleaned up S3 object: {s3_key}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cleanup S3 object: {e}")

    @staticmethod
    def is_available() -> bool:
        """
        Check if S3+NATS upload is available.

        Returns:
            True if all required dependencies are available
        """
        try:
            import boto3
            import nats
            import os

            # Check for required environment variables (matches backend/PDF service)
            required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
            bucket = os.getenv("S3_BUCKET_NAME", "documents")
            return all(os.getenv(var) for var in required_vars) and bucket

        except ImportError:
            return False


# Convenience function for backward compatibility
async def upload_pdf_via_s3_nats(
    config: BackendConfig, file_bytes: bytes, filename: str
) -> str:
    """
    Convenience function to upload PDF via S3+NATS.

    Args:
        config: Report Analyst configuration
        file_bytes: PDF file content
        filename: Original filename

    Returns:
        resource_id: Backend resource ID
    """
    service = S3UploadService(config)
    try:
        return await service.upload_pdf_via_s3_nats(file_bytes, filename)
    finally:
        await service.close()  # Ensure connection is closed
