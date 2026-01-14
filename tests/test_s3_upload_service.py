"""
Tests for S3 Upload Service

Tests for enterprise S3+NATS upload functionality.
Currently has 0% coverage - adding comprehensive tests.
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from report_analyst_search_backend.config import BackendConfig
from report_analyst_search_backend.s3_upload_service import (
    S3UploadService,
    S3UploadServiceError,
)


@pytest.fixture
def backend_config():
    """Create test backend configuration"""
    return BackendConfig(
        use_backend=True,
        backend_url="http://localhost:8000",
    )


@pytest.fixture
def s3_service(backend_config):
    """Create S3 upload service"""
    return S3UploadService(backend_config)


@pytest.fixture
def sample_pdf_bytes():
    """Sample PDF file bytes"""
    return b"%PDF-1.4\n%Test PDF\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 0\ntrailer\n<<\n/Size 0\n/Root 1 0 R\n>>\nstartxref\n0\n%%EOF"


class TestS3UploadService:
    """Tests for S3UploadService"""

    def test_s3_upload_service_initialization(self, s3_service):
        """Test service initialization"""
        assert s3_service is not None
        assert s3_service.config is not None
        assert s3_service.timeout == 120

    def test_get_s3_bucket(self, s3_service):
        """Test getting S3 bucket name"""
        with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
            bucket = s3_service._get_s3_bucket()
            assert bucket == "test-bucket"

        # Test default
        with patch.dict(os.environ, {}, clear=True):
            bucket = s3_service._get_s3_bucket()
            assert bucket == "documents"

    @pytest.mark.asyncio
    async def test_upload_to_s3(self, s3_service, sample_pdf_bytes):
        """Test uploading file to S3"""
        with patch("boto3.client") as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client

            with patch.dict(
                os.environ,
                {
                    "S3_ENDPOINT_URL": "http://s3.example.com",
                    "AWS_ACCESS_KEY_ID": "test-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret",
                    "AWS_DEFAULT_REGION": "us-east-1",
                },
            ):
                s3_service.s3_client = mock_s3_client
                s3_service.s3_bucket = "test-bucket"

                s3_url = await s3_service._upload_to_s3(
                    sample_pdf_bytes, "test-key", "test.pdf"
                )

                assert s3_url is not None
                assert "s3.example.com" in s3_url
                assert "test-bucket" in s3_url
                mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_pdf_via_s3_nats(self, s3_service, sample_pdf_bytes):
        """Test full S3+NATS upload flow"""
        with patch.object(s3_service, "_upload_to_s3") as mock_upload:
            mock_upload.return_value = "http://s3.example.com/bucket/key.pdf"

            with patch.object(s3_service, "connect") as mock_connect:
                with patch.object(s3_service, "js") as mock_js:
                    mock_js.publish = AsyncMock()
                    mock_ack = Mock()
                    mock_js.publish.return_value = mock_ack
                    s3_service.nc = Mock()
                    s3_service.nc.close = AsyncMock()

                    with patch.dict(
                        os.environ,
                        {
                            "NATS_URL": "nats://localhost:4222",
                        },
                    ):
                        with patch("nats.connect") as mock_nats_connect:
                            mock_nc = AsyncMock()
                            mock_nc.jetstream.return_value = mock_js
                            mock_nats_connect.return_value = mock_nc

                            result = await s3_service.upload_pdf_via_s3_nats(
                                sample_pdf_bytes, "test.pdf"
                            )

                            assert result is not None
                            assert isinstance(result, str)  # request_id

    @pytest.mark.asyncio
    async def test_s3_upload_error_handling(self, s3_service, sample_pdf_bytes):
        """Test error handling during S3 upload"""
        with patch.object(s3_service, "_upload_to_s3") as mock_upload:
            mock_upload.side_effect = Exception("S3 upload failed")

            with pytest.raises(S3UploadServiceError):
                await s3_service.upload_pdf_via_s3_nats(sample_pdf_bytes, "test.pdf")

    @pytest.mark.asyncio
    async def test_s3_cleanup_on_error(self, s3_service):
        """Test cleanup of S3 object on error"""
        with patch("boto3.client") as mock_boto3:
            mock_s3_client = Mock()
            mock_boto3.return_value = mock_s3_client

            with patch.dict(
                os.environ,
                {
                    "S3_ENDPOINT_URL": "http://s3.example.com",
                    "AWS_ACCESS_KEY_ID": "test-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret",
                },
            ):
                s3_service.s3_client = mock_s3_client
                s3_service.s3_bucket = "test-bucket"

                await s3_service._cleanup_s3_object("test-key")

                mock_s3_client.delete_object.assert_called_once_with(
                    Bucket="test-bucket", Key="test-key"
                )

    def test_is_available(self):
        """Test availability check"""
        # Test when available
        with patch.dict(
            os.environ,
            {
                "AWS_ACCESS_KEY_ID": "test-key",
                "AWS_SECRET_ACCESS_KEY": "test-secret",
                "S3_BUCKET_NAME": "test-bucket",
            },
        ):
            assert S3UploadService.is_available() is True

        # Test when not available (missing credentials)
        with patch.dict(os.environ, {}, clear=True):
            assert S3UploadService.is_available() is False

        # Test when boto3 not available
        with patch("report_analyst_search_backend.s3_upload_service.boto3", None):
            assert S3UploadService.is_available() is False
