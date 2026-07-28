"""
Full roundtrip test for backend resource workflow

Tests the complete flow:
1. List backend resources via ReportDataClient
2. Select a backend resource (URN)
3. Retrieve chunks from backend
4. Use chunks for analysis
5. Verify cache compatibility
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.cache_manager import CacheManager
from report_analyst.core.report_data_client import (
    ReportDataClient,
    ReportResource,
    get_chunks_for_backend_resource,
)
from report_analyst_search_backend.backend_service import BackendService
from report_analyst_search_backend.config import BackendConfig


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def backend_config():
    """Create test backend configuration"""
    return BackendConfig(use_backend=True, backend_url="http://localhost:8000")


@pytest.fixture
def mock_backend_resources():
    """Mock backend API responses for resources"""
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
def mock_backend_chunks():
    """Mock backend chunks response"""
    return [
        {
            "chunk_id": "chunk-1",
            "chunk_text": "This is a test chunk about sustainability reporting and climate risk.",
            "chunk_metadata": {"page": 1, "source": "test_report.pdf"},
            "similarity_score": 0.9,
            "resource_id": "test-resource-1",
        },
        {
            "chunk_id": "chunk-2",
            "chunk_text": "Another chunk with relevant information about emissions and targets.",
            "chunk_metadata": {"page": 2, "source": "test_report.pdf"},
            "similarity_score": 0.8,
            "resource_id": "test-resource-1",
        },
    ]


def test_full_roundtrip_list_and_select_backend_resource(backend_config, mock_backend_resources):
    """Test Step 1 & 2: List backend resources and verify URN format"""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Step 1: List resources via ReportDataClient
        client = ReportDataClient()
        resources = client.list_reports(backend_configs=[backend_config])

        # Verify backend resource is listed
        assert len(resources) >= 1
        backend_resource = next((r for r in resources if r.is_backend_resource), None)
        assert backend_resource is not None

        # Step 2: Verify URN format
        assert backend_resource.uri.startswith("urn:report-analyst:backend:")
        assert "test-resource-1" in backend_resource.uri
        assert backend_resource.name == "test_report.pdf"

        # Verify URN parsing
        parsed = backend_resource.parse_backend_urn()
        assert parsed is not None
        assert parsed["host"] == "localhost:8000"
        assert parsed["resource_id"] == "test-resource-1"


def test_full_roundtrip_retrieve_chunks(backend_config, mock_backend_chunks):
    """Test Step 3: Retrieve chunks from backend resource"""
    urn = "urn:report-analyst:backend:localhost:8000:test-resource-1"

    with patch("requests.post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "resource": {"id": "test-resource-1"},
                    "chunks": [
                        {
                            "chunk": {
                                "id": "chunk-1",
                                "chunk_text": mock_backend_chunks[0]["chunk_text"],
                                "chunk_metadata": mock_backend_chunks[0]["chunk_metadata"],
                            },
                            "similarity": mock_backend_chunks[0]["similarity_score"],
                        },
                        {
                            "chunk": {
                                "id": "chunk-2",
                                "chunk_text": mock_backend_chunks[1]["chunk_text"],
                                "chunk_metadata": mock_backend_chunks[1]["chunk_metadata"],
                            },
                            "similarity": mock_backend_chunks[1]["similarity_score"],
                        },
                    ],
                }
            ],
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Retrieve chunks
        chunks = get_chunks_for_backend_resource(urn, [backend_config])

        # Verify chunks retrieved
        assert chunks is not None
        assert len(chunks) == 2
        assert chunks[0]["chunk_text"] == mock_backend_chunks[0]["chunk_text"]
        assert chunks[1]["chunk_text"] == mock_backend_chunks[1]["chunk_text"]


def test_full_roundtrip_analyzer_with_backend_chunks(temp_dir, backend_config, mock_backend_chunks):
    """Test Step 4: Use backend chunks in analyzer"""
    # Create cache manager
    cache_path = temp_dir / "cache"
    cache_path.mkdir()
    cache_manager = CacheManager(db_path=cache_path / "test.db")
    cache_manager.init_db()

    # Create analyzer (singleton pattern)
    analyzer = DocumentAnalyzer()
    # Patch the cache manager
    analyzer.cache_manager = cache_manager
    analyzer.question_set = "tcfd"
    analyzer.default_model = "gpt-3.5-turbo-1106"

    # Convert backend chunks to analyzer format with mock embeddings
    import numpy as np

    backend_chunks = [
        {
            "chunk_id": "chunk-1",
            "chunk_text": mock_backend_chunks[0]["chunk_text"],
            "chunk_metadata": mock_backend_chunks[0]["chunk_metadata"],
            "similarity_score": mock_backend_chunks[0]["similarity_score"],
            "resource_id": "test-resource-1",
        },
        {
            "chunk_id": "chunk-2",
            "chunk_text": mock_backend_chunks[1]["chunk_text"],
            "chunk_metadata": mock_backend_chunks[1]["chunk_metadata"],
            "similarity_score": mock_backend_chunks[1]["similarity_score"],
            "resource_id": "test-resource-1",
        },
    ]

    # Convert to analyzer format with embeddings (required by cache manager)
    analyzer_chunks = [
        {
            "text": chunk["chunk_text"],
            "metadata": chunk["chunk_metadata"],
            "embedding": np.random.rand(1536).tolist(),  # Mock embedding
        }
        for chunk in backend_chunks
    ]

    urn = "urn:report-analyst:backend:localhost:8000:test-resource-1"

    # Test cache key generation for URN
    cache_key = analyzer._get_cache_key(urn)
    assert cache_key is not None
    assert "backend" in cache_key
    assert "test-resource-1" in cache_key

    # Verify chunks can be saved to cache with URN
    cache_manager.save_document_chunks(
        file_path=urn,
        chunks=analyzer_chunks,
        chunk_size=500,
        chunk_overlap=20,
    )

    # Verify chunks can be retrieved from cache
    cached_chunks = cache_manager.get_document_chunks(
        file_path=urn,
        chunk_size=500,
        chunk_overlap=20,
    )
    assert len(cached_chunks) == 2
    assert cached_chunks[0]["text"] == analyzer_chunks[0]["text"]


def test_full_roundtrip_cache_compatibility(temp_dir, backend_config):
    """Test Step 5: Verify cache compatibility between local files and URNs"""
    cache_path = temp_dir / "cache"
    cache_path.mkdir()
    cache_manager = CacheManager(db_path=cache_path / "test.db")
    cache_manager.init_db()

    # Create test chunks with mock embeddings (required by cache manager)
    import numpy as np

    test_chunks = [
        {
            "text": "Test chunk 1",
            "metadata": {"page": 1},
            "embedding": np.random.rand(1536).tolist(),  # Mock embedding
        },
        {
            "text": "Test chunk 2",
            "metadata": {"page": 2},
            "embedding": np.random.rand(1536).tolist(),  # Mock embedding
        },
    ]

    # Test with local file path (backwards compatibility)
    local_file_path = str(temp_dir / "test.pdf")
    cache_manager.save_document_chunks(
        file_path=local_file_path,
        chunks=test_chunks,
        chunk_size=500,
        chunk_overlap=20,
    )

    local_cached = cache_manager.get_document_chunks(
        file_path=local_file_path,
        chunk_size=500,
        chunk_overlap=20,
    )
    assert len(local_cached) == 2

    # Test with URN (new functionality)
    urn = "urn:report-analyst:backend:localhost:8000:test-resource-1"
    cache_manager.save_document_chunks(
        file_path=urn,
        chunks=test_chunks,
        chunk_size=500,
        chunk_overlap=20,
    )

    urn_cached = cache_manager.get_document_chunks(
        file_path=urn,
        chunk_size=500,
        chunk_overlap=20,
    )
    assert len(urn_cached) == 2

    # Verify they don't interfere with each other
    assert local_cached[0]["text"] == test_chunks[0]["text"]
    assert urn_cached[0]["text"] == test_chunks[0]["text"]


def test_full_roundtrip_combined_local_and_backend(temp_dir, backend_config, mock_backend_resources):
    """Test combined listing of local and backend resources"""
    # Create local PDF
    test_pdf = temp_dir / "local_report.pdf"
    test_pdf.write_bytes(
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
    )

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_backend_resources
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # List combined resources
        client = ReportDataClient(temp_dir=temp_dir)
        resources = client.list_reports(backend_configs=[backend_config])

        # Should have both local and backend
        local_resources = [r for r in resources if r.is_local_resource]
        backend_resources = [r for r in resources if r.is_backend_resource]

        assert len(local_resources) >= 1
        assert len(backend_resources) >= 1

        # Verify formats
        assert local_resources[0].uri.startswith("file://")
        assert backend_resources[0].uri.startswith("urn:report-analyst:backend:")

        # Verify sorting (most recent first)
        dates = [r.date for r in resources if r.date is not None]
        assert dates == sorted(dates, reverse=True)
