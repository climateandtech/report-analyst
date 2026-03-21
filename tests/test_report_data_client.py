"""
Tests for ReportDataClient

Unit tests for the sustainability report data client with URN-based identification.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from report_analyst.core.report_data_client import (
    ReportDataClient,
    ReportResource,
    get_backend_service_for_urn,
    get_chunks_for_backend_resource,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_backend_resources():
    """Mock backend API responses"""
    return [
        {
            "id": "test-resource-1",
            "filename": "test_report.pdf",
            "created_at": "2024-01-01T00:00:00Z",
            "file_size": 1024,
            "status": "processed",
        }
    ]


@pytest.fixture
def backend_config():
    """Create test backend configuration"""
    from report_analyst_search_backend.config import BackendConfig

    return BackendConfig(use_backend=True, backend_url="http://localhost:8000")


def test_report_resource_urn_parsing():
    """Test parsing backend URNs"""
    resource = ReportResource(name="test.pdf", uri="urn:report-analyst:backend:localhost:8000:abc-123")
    parsed = resource.parse_backend_urn()
    assert parsed is not None
    assert parsed["host"] == "localhost:8000"
    assert parsed["resource_id"] == "abc-123"


def test_report_resource_resolve_to_http_url():
    """Test resolving URN to HTTP URL"""
    resource = ReportResource(name="test.pdf", uri="urn:report-analyst:backend:localhost:8000:abc-123")
    url = resource.resolve_to_http_url()
    assert url == "http://localhost:8000/resources/abc-123"


def test_report_resource_is_backend_resource():
    """Test backend resource detection"""
    backend_resource = ReportResource(name="test.pdf", uri="urn:report-analyst:backend:localhost:8000:abc-123")
    local_resource = ReportResource(name="test.pdf", uri="file:///path/to/file.pdf")

    assert backend_resource.is_backend_resource is True
    assert local_resource.is_backend_resource is False


def test_report_data_client_list_local_reports(temp_dir):
    """Test listing local PDF files"""
    # Create a minimal valid PDF file
    test_pdf = temp_dir / "test_report.pdf"
    # Write minimal PDF header
    test_pdf.write_bytes(
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
    )

    client = ReportDataClient(temp_dir=temp_dir)
    resources = client._list_local_reports()

    assert len(resources) == 1
    assert resources[0].name == "test_report.pdf"
    assert resources[0].uri.startswith("file://")
    assert resources[0].is_local_resource is True


def test_report_data_client_list_backend_reports(backend_config, mock_backend_resources):
    """Test listing backend resources"""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = ReportDataClient()
        resources = client._list_backend_reports(backend_config)

        assert len(resources) == 1
        assert resources[0].uri.startswith("urn:report-analyst:backend:")
        assert "test-resource-1" in resources[0].uri
        assert resources[0].name == "test_report.pdf"


def test_report_data_client_combined_listing(temp_dir, backend_config, mock_backend_resources):
    """Test listing from both local and backend sources"""
    # Create local PDF
    test_pdf = temp_dir / "local_report.pdf"
    test_pdf.write_bytes(
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
    )

    # Mock backend response
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = ReportDataClient(temp_dir=temp_dir)
        resources = client.list_reports(backend_configs=[backend_config])

        # Should have both local and backend resources
        assert len(resources) >= 2
        # Check sorting by date (most recent first)
        dates = [r.date for r in resources if r.date is not None]
        assert dates == sorted(dates, reverse=True)


def test_get_backend_service_for_urn(backend_config):
    """Test getting BackendService from URN"""
    urn = "urn:report-analyst:backend:localhost:8000:abc-123"
    service = get_backend_service_for_urn(urn, [backend_config])
    assert service is not None
    assert service.config.backend_url == "http://localhost:8000"


def test_get_backend_service_for_urn_invalid():
    """Test getting BackendService with invalid URN"""
    from report_analyst_search_backend.config import BackendConfig

    backend_config = BackendConfig(use_backend=True, backend_url="http://localhost:8000")
    invalid_urn = "file:///path/to/file.pdf"
    service = get_backend_service_for_urn(invalid_urn, [backend_config])
    assert service is None


def test_get_chunks_for_backend_resource(backend_config):
    """Test getting chunks for backend resource"""
    urn = "urn:report-analyst:backend:localhost:8000:abc-123"
    mock_chunks = [
        {
            "chunk_id": "chunk-1",
            "chunk_text": "Test chunk text",
            "chunk_metadata": {},
            "similarity_score": 0.9,
            "resource_id": "abc-123",
        }
    ]

    with patch("report_analyst.core.report_data_client.get_backend_service_for_urn") as mock_get_service:
        mock_service = Mock()
        mock_service.get_chunks.return_value = mock_chunks
        mock_get_service.return_value = mock_service

        chunks = get_chunks_for_backend_resource(urn, [backend_config])

        assert chunks == mock_chunks
        mock_service.get_chunks.assert_called_once_with("abc-123")


def test_report_data_client_error_handling(backend_config):
    """Test that errors are handled gracefully"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        client = ReportDataClient()
        resources = client._list_backend_reports(backend_config)

        # Should return empty list on error, not crash
        assert resources == []


def test_report_resource_urn_with_colons_in_resource_id():
    """Test URN parsing with resource IDs that contain colons"""
    # Some UUIDs or IDs might have colons
    resource = ReportResource(
        name="test.pdf",
        uri="urn:report-analyst:backend:localhost:8000:abc:123:def",
    )
    parsed = resource.parse_backend_urn()
    assert parsed is not None
    assert parsed["host"] == "localhost:8000"
    assert parsed["resource_id"] == "abc:123:def"  # Should preserve all parts after host


def test_report_resource_local_file_uri():
    """Test local file URI handling"""
    resource = ReportResource(name="test.pdf", uri="file:///absolute/path/to/file.pdf")
    assert resource.is_local_resource is True
    assert resource.is_backend_resource is False
    assert resource.parse_backend_urn() is None
