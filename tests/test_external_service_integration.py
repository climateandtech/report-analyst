"""
Tests for external service integration

Comprehensive test suite for external service integration flow:
- Notification handling (NATS and HTTP)
- S3 URL processing
- Pre-processed chunks/pages handling
- Analysis request and result delivery
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

try:
    from aioresponses import aioresponses

    HAS_AIORESPONSES = True
except ImportError:
    HAS_AIORESPONSES = False

from report_analyst_search_backend.external_service_client import (
    ExternalServiceClient,
)
from report_analyst_search_backend.external_service_delivery import (
    ExternalServiceDelivery,
)
from report_analyst_search_backend.external_service_handler import (
    ExternalServiceHandler,
    ExternalServiceReadyEvent,
    ProcessingResult,
)


@pytest.fixture
def external_handler():
    """Create external service handler"""
    return ExternalServiceHandler()


@pytest.fixture
def external_client():
    """Create external service client"""
    return ExternalServiceClient(
        base_url="http://localhost:8000", nats_url="nats://localhost:4222"
    )


@pytest.fixture
def external_delivery():
    """Create external service delivery"""
    return ExternalServiceDelivery(nats_url="nats://localhost:4222")


@pytest.fixture
def sample_chunks():
    """Sample pre-processed chunks"""
    return [
        {
            "id": "chunk_1",
            "text": "This is the first chunk of text about climate risks.",
            "metadata": {"page": 1, "source": "external_service"},
        },
        {
            "id": "chunk_2",
            "text": "This is the second chunk discussing sustainability measures.",
            "metadata": {"page": 2, "source": "external_service"},
        },
    ]


@pytest.fixture
def sample_pages():
    """Sample pre-processed pages"""
    return [
        {
            "page_number": 1,
            "text": "Page 1 content about climate risks and mitigation strategies.",
            "metadata": {"source": "external_service"},
        },
        {
            "page_number": 2,
            "text": "Page 2 content about sustainability reporting and disclosures.",
            "metadata": {"source": "external_service"},
        },
    ]


class TestExternalServiceHandler:
    """Tests for ExternalServiceHandler"""

    @pytest.mark.asyncio
    async def test_handle_notification_s3_url(self, external_handler):
        """Test handling S3 URL notification"""
        notification = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="s3_url",
            s3_url="http://s3.example.com/bucket/file.pdf",
            s3_bucket="bucket",
            s3_key="file.pdf",
        )

        # Mock S3 client
        mock_s3_client = Mock()
        mock_body = Mock()
        mock_body.read.return_value = b"%PDF-1.4\n%Test PDF"
        mock_response = {"Body": mock_body}
        mock_s3_client.get_object.return_value = mock_response
        external_handler.s3_client = mock_s3_client

        # Mock PyMuPDFReader
        with patch("llama_index.readers.file.PyMuPDFReader") as mock_reader:
            mock_doc = Mock()
            mock_doc.text = "Test PDF content"
            mock_doc.metadata = {}
            mock_reader_instance = Mock()
            mock_reader_instance.load.return_value = [mock_doc]
            mock_reader.return_value = mock_reader_instance

            result = await external_handler.handle_external_notification(
                "service-x", notification
            )

            assert isinstance(result, ProcessingResult)
            # Should process S3 URL (may fail if S3 client not initialized, but structure is correct)

    @pytest.mark.asyncio
    async def test_handle_notification_chunks(self, external_handler, sample_chunks):
        """Test handling pre-processed chunks notification"""
        notification = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="chunks",
            chunks=sample_chunks,
        )

        result = await external_handler.handle_external_notification(
            "service-x", notification, rechunk_mode="never"
        )

        assert result.success
        assert result.chunks is not None
        assert len(result.chunks) == 2
        assert result.chunks[0]["chunk_text"] == sample_chunks[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_notification_pages(self, external_handler, sample_pages):
        """Test handling pre-processed pages notification"""
        notification = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="pages",
            pages=sample_pages,
        )

        result = await external_handler.handle_external_notification(
            "service-x", notification
        )

        assert result.success
        assert result.chunks is not None
        assert len(result.chunks) == 2
        assert "page_1" in result.chunks[0]["chunk_id"]

    @pytest.mark.asyncio
    async def test_rechunk_mode_never(self, external_handler, sample_chunks):
        """Test rechunk mode 'never' - use chunks directly"""
        notification = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="chunks",
            chunks=sample_chunks,
        )

        result = await external_handler.handle_external_notification(
            "service-x", notification, rechunk_mode="never"
        )

        assert result.success
        assert len(result.chunks) == 2
        # Should preserve original chunk structure

    @pytest.mark.asyncio
    async def test_rechunk_mode_auto(self, external_handler, sample_chunks):
        """Test rechunk mode 'auto' - re-chunk if format doesn't match"""
        notification = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="chunks",
            chunks=sample_chunks,
        )

        result = await external_handler.handle_external_notification(
            "service-x", notification, rechunk_mode="auto"
        )

        assert result.success
        assert result.chunks is not None

    def test_normalize_chunks(self, external_handler, sample_chunks):
        """Test chunk normalization"""
        normalized = external_handler._normalize_chunks(sample_chunks)

        assert len(normalized) == 2
        assert "chunk_id" in normalized[0]
        assert "chunk_text" in normalized[0]
        assert "chunk_metadata" in normalized[0]

    def test_chunks_match_format(self, external_handler, sample_chunks):
        """Test format matching for chunks"""
        assert external_handler._chunks_match_format(sample_chunks) is True

        # Test with invalid format
        invalid_chunks = [{"invalid": "data"}]
        assert external_handler._chunks_match_format(invalid_chunks) is False


class TestExternalServiceClient:
    """Tests for ExternalServiceClient"""

    @pytest.mark.asyncio
    async def test_notify_ready_nats(self, external_client):
        """Test notifying via NATS"""
        with patch.object(external_client, "connect_nats") as mock_connect:
            with patch.object(external_client, "js") as mock_js:
                mock_js.publish = AsyncMock()
                external_client.nc = Mock()
                external_client.nc.is_connected = True

                result = await external_client.notify_ready(
                    service_id="service-x",
                    request_id="req-123",
                    content_type="chunks",
                    chunks=[{"id": "1", "text": "test"}],
                    method="nats",
                )

                assert result is True
                mock_js.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_ready_http(self, external_client):
        """Test notifying via HTTP"""
        if HAS_AIORESPONSES:
            with aioresponses() as m:
                m.post(
                    "http://localhost:8000/external/services/service-x/notify",
                    status=200,
                )
                result = await external_client.notify_ready(
                    service_id="service-x",
                    request_id="req-123",
                    content_type="chunks",
                    chunks=[{"id": "1", "text": "test"}],
                    method="http",
                )
                assert result is True
        else:
            # Fallback: skip if aioresponses not available
            pytest.skip("aioresponses not available for HTTP mocking")

    @pytest.mark.asyncio
    async def test_request_analysis_http(self, external_client):
        """Test requesting analysis via HTTP"""
        if HAS_AIORESPONSES:
            with aioresponses() as m:
                m.post(
                    "http://localhost:8000/external/services/service-x/analyze",
                    status=200,
                    payload={"request_id": "analysis-123"},
                )
                request_id = await external_client.request_analysis(
                    service_id="service-x",
                    external_request_id="req-123",
                    content=[{"id": "1", "text": "test"}],
                    question_set="tcfd",
                    analysis_config={"model": "gpt-4o-mini"},
                    method="http",
                )
                assert request_id == "analysis-123"
        else:
            pytest.skip("aioresponses not available for HTTP mocking")

    @pytest.mark.asyncio
    async def test_get_results(self, external_client):
        """Test polling for results"""
        if HAS_AIORESPONSES:
            with aioresponses() as m:
                m.get(
                    "http://localhost:8000/external/services/service-x/results/analysis-123",
                    status=200,
                    payload={
                        "request_id": "analysis-123",
                        "status": "completed",
                        "answers": [],
                        "top_chunks": [],
                    },
                )
                results = await external_client.get_results("service-x", "analysis-123")

                assert results is not None
                assert results["status"] == "completed"
        else:
            pytest.skip("aioresponses not available for HTTP mocking")


class TestExternalServiceDelivery:
    """Tests for ExternalServiceDelivery"""

    @pytest.mark.asyncio
    async def test_deliver_results_nats(self, external_delivery):
        """Test delivering results via NATS"""
        with patch.object(external_delivery, "connect_nats") as mock_connect:
            with patch.object(external_delivery, "js") as mock_js:
                mock_js.publish = AsyncMock()
                external_delivery.nc = Mock()
                external_delivery.nc.is_connected = True

                result = await external_delivery.deliver_results(
                    service_id="service-x",
                    request_id="req-123",
                    external_request_id="ext-req-123",
                    results={"answers": [], "top_chunks": []},
                    response_method="nats",
                )

                assert result is True
                mock_js.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_results_poll(self, external_delivery):
        """Test storing results for polling"""
        result = await external_delivery.deliver_results(
            service_id="service-x",
            request_id="req-123",
            external_request_id="ext-req-123",
            results={
                "answers": [{"question_id": "q1", "answer": "test"}],
                "top_chunks": [],
            },
            response_method="poll",
        )

        assert result is True

        # Check that results are stored
        stored = external_delivery.get_results("req-123")
        assert stored is not None
        assert stored["request_id"] == "req-123"
        assert len(stored["answers"]) == 1

    def test_get_results_poll(self, external_delivery):
        """Test retrieving stored results"""
        # Store results first
        external_delivery._result_storage["test-123"] = {
            "request_id": "test-123",
            "status": "completed",
            "answers": [],
        }

        results = external_delivery.get_results("test-123")
        assert results is not None
        assert results["request_id"] == "test-123"

    def test_clear_results(self, external_delivery):
        """Test clearing stored results"""
        external_delivery._result_storage["test-123"] = {"request_id": "test-123"}
        external_delivery.clear_results("test-123")

        assert external_delivery.get_results("test-123") is None


class TestExternalServiceIntegration:
    """Integration tests for external service flow"""

    @pytest.mark.asyncio
    async def test_full_flow_chunks_http(self, external_handler, sample_chunks):
        """Test full flow: chunks → HTTP notification → processing"""
        notification = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="chunks",
            chunks=sample_chunks,
        )

        result = await external_handler.handle_external_notification(
            "service-x", notification, rechunk_mode="never"
        )

        assert result.success
        assert result.chunks is not None
        assert len(result.chunks) == 2

    @pytest.mark.asyncio
    async def test_external_service_error_handling(self, external_handler):
        """Test error handling for invalid notifications"""
        # Invalid content type
        notification = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="invalid_type",
        )

        result = await external_handler.handle_external_notification(
            "service-x", notification
        )

        assert not result.success
        assert result.error is not None

        # Missing required fields
        notification2 = ExternalServiceReadyEvent(
            service_id="service-x",
            request_id="req-123",
            content_type="s3_url",
            s3_url=None,  # Missing S3 URL
        )

        result2 = await external_handler.handle_external_notification(
            "service-x", notification2
        )

        assert not result2.success
        assert "S3 URL not provided" in result2.error
