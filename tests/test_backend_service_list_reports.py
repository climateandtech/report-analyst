"""
Tests for BackendService.list_reports()

Unit tests for backend service list_reports method with URN generation.
"""

from unittest.mock import Mock, patch

import pytest

from report_analyst_search_backend.backend_service import BackendService
from report_analyst_search_backend.config import BackendConfig


@pytest.fixture
def backend_config():
    """Create test backend configuration"""
    return BackendConfig(use_backend=True, backend_url="http://localhost:8000")


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
        },
        {
            "id": "test-resource-2",
            "filename": "another_report.pdf",
            "created_at": "2024-01-02T00:00:00Z",
            "file_size": 2048,
            "status": "completed",
        },
    ]


def test_backend_service_list_reports(backend_config, mock_backend_resources):
    """Test BackendService.list_reports()"""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        service = BackendService(backend_config)
        reports = service.list_reports()

        assert len(reports) == 2
        assert reports[0].uri == "urn:report-analyst:backend:localhost:8000:test-resource-1"
        assert reports[0].name == "test_report.pdf"
        assert reports[1].uri == "urn:report-analyst:backend:localhost:8000:test-resource-2"
        assert reports[1].name == "another_report.pdf"


def test_backend_service_list_reports_with_https(backend_config, mock_backend_resources):
    """Test URN generation with HTTPS backend URL"""
    backend_config.backend_url = "https://api.example.com"

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        service = BackendService(backend_config)
        reports = service.list_reports()

        assert len(reports) == 2
        # Should normalize URL (remove https://)
        assert reports[0].uri.startswith("urn:report-analyst:backend:api.example.com:")
        assert "https://" not in reports[0].uri


def test_backend_service_list_reports_with_port(backend_config, mock_backend_resources):
    """Test URN generation with port in backend URL"""
    backend_config.backend_url = "http://localhost:8080"

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        service = BackendService(backend_config)
        reports = service.list_reports()

        assert len(reports) == 2
        # Should preserve port in URN
        assert "localhost:8080" in reports[0].uri


def test_backend_service_list_reports_error_handling(backend_config):
    """Test error handling when backend unavailable"""
    import requests

    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Connection error")

        service = BackendService(backend_config)
        # Should handle gracefully, not crash
        reports = service.list_reports()
        assert reports == []  # Empty list on error


def test_backend_service_list_reports_empty_response(backend_config):
    """Test handling of empty backend response"""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        service = BackendService(backend_config)
        reports = service.list_reports()

        assert reports == []


def test_backend_service_normalize_backend_url():
    """Test URL normalization for URN"""
    backend_config = BackendConfig(use_backend=True, backend_url="https://api.example.com:443")
    service = BackendService(backend_config)

    normalized = service._normalize_backend_url("https://api.example.com:443")
    assert normalized == "api.example.com:443"
    assert "https://" not in normalized

    normalized = service._normalize_backend_url("http://localhost:8000")
    assert normalized == "localhost:8000"
    assert "http://" not in normalized


def test_backend_service_parse_date():
    """Test date parsing for timestamps"""
    backend_config = BackendConfig(use_backend=True, backend_url="http://localhost:8000")
    service = BackendService(backend_config)

    # Test ISO format with Z
    timestamp = service._parse_date("2024-01-01T00:00:00Z")
    assert timestamp is not None
    assert isinstance(timestamp, float)

    # Test ISO format without Z
    timestamp = service._parse_date("2024-01-01T00:00:00")
    assert timestamp is not None

    # Test None
    timestamp = service._parse_date(None)
    assert timestamp is None

    # Test invalid format
    timestamp = service._parse_date("invalid-date")
    assert timestamp is None


def test_backend_service_get_resources_public(backend_config, mock_backend_resources):
    """Test that get_resources() is now public"""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        service = BackendService(backend_config)
        resources = service.get_resources()

        assert len(resources) == 2
        assert resources[0]["id"] == "test-resource-1"
