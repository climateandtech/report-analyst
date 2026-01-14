"""
Tests for automatic document.ready event processing

Tests the flow where:
1. Backend publishes document.ready event
2. Worker automatically receives it
3. Worker pulls chunks from backend (or uses provided chunks)
4. Worker runs analysis
5. Worker stores results back to backend

Note: These tests use NATSJobCoordinator directly. For end-to-end tests
with event router, see test_document_ready_e2e_router.py
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from report_analyst_jobs.nats_integration import (
    DocumentReadyEvent,
    DocumentReadyProcessingConfig,
    NATSJobCoordinator,
)


@pytest.fixture
def mock_chunks():
    """Sample chunks from backend"""
    return [
        {
            "id": "chunk-1",
            "text": "This is a test chunk about climate change.",
            "metadata": {"page": 1, "source": "test.pdf"},
        },
        {
            "id": "chunk-2",
            "text": "Another chunk about sustainability reporting.",
            "metadata": {"page": 2, "source": "test.pdf"},
        },
    ]


@pytest.fixture
def mock_analysis_result():
    """Sample analysis result"""
    return {
        "answers": {
            "tcfd_1": {
                "ANSWER": "Test answer",
                "SCORE": 0.8,
                "EVIDENCE": ["chunk-1"],
            }
        },
        "top_chunks": ["chunk-1"],
    }


@pytest.mark.asyncio
async def test_process_document_ready_event(mock_chunks, mock_analysis_result):
    """Test processing a document.ready event with default config (pull chunks)"""
    coordinator = NATSJobCoordinator()

    # Mock NATS connection
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    coordinator.nc = mock_nc
    coordinator.js = mock_js

    # Mock search backend client
    coordinator.search_backend = Mock()
    coordinator.search_backend.base_url = "http://localhost:8000"
    coordinator.search_backend.get_resource_chunks = AsyncMock(return_value=mock_chunks)

    # Mock _get_chunks_for_resource (which calls get_resource_chunks)
    coordinator._get_chunks_for_resource = AsyncMock(return_value=mock_chunks)

    # Mock _run_analysis
    coordinator._run_analysis = AsyncMock(return_value=mock_analysis_result)

    # Mock _store_analysis_to_backend
    coordinator._store_analysis_to_backend = AsyncMock()

    # Create config with default settings (pull_chunks=True)
    config = DocumentReadyProcessingConfig(
        pull_chunks=True,
        question_set="tcfd",
        analysis_config={"model": "gpt-4o-mini"},
        store_to_backend=True,
    )

    # Create a mock message
    event = DocumentReadyEvent(
        resource_id="test-resource-123",
        document_url="http://example.com/test.pdf",
        chunks_count=2,
        status="ready",
    )
    mock_msg = AsyncMock()
    mock_msg.data = json.dumps(
        {
            "resource_id": event.resource_id,
            "document_url": event.document_url,
            "chunks_count": event.chunks_count,
            "status": event.status,
        }
    ).encode()
    mock_msg.ack = AsyncMock()

    # Process the event
    await coordinator._handle_document_ready(mock_msg, config)

    # Verify chunks were retrieved
    coordinator._get_chunks_for_resource.assert_called_once_with(
        "test-resource-123", "search", None
    )

    # Verify analysis was run
    coordinator._run_analysis.assert_called_once_with(
        mock_chunks, "tcfd", {"model": "gpt-4o-mini"}
    )

    # Verify results were stored
    coordinator._store_analysis_to_backend.assert_called_once_with(
        "test-resource-123", mock_analysis_result, "tcfd"
    )

    # Verify message was acked
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_process_document_ready_with_provided_chunks(mock_analysis_result):
    """Test processing document.ready event with chunks provided in event (pull_chunks=False)"""
    coordinator = NATSJobCoordinator()

    # Mock NATS connection
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    coordinator.nc = mock_nc
    coordinator.js = mock_js

    # Mock _get_chunks_for_resource to verify it's NOT called
    coordinator._get_chunks_for_resource = AsyncMock()

    # Mock _run_analysis
    coordinator._run_analysis = AsyncMock(return_value=mock_analysis_result)

    # Mock _store_analysis_to_backend
    coordinator._store_analysis_to_backend = AsyncMock()

    # Create config with pull_chunks=False (use provided chunks)
    config = DocumentReadyProcessingConfig(
        pull_chunks=False,
        question_set="tcfd",
        analysis_config={"model": "gpt-4o-mini"},
        store_to_backend=True,
    )

    # Create event with chunks included
    provided_chunks = [
        {"id": "chunk-1", "text": "Test chunk 1", "metadata": {}},
        {"id": "chunk-2", "text": "Test chunk 2", "metadata": {}},
    ]
    event = DocumentReadyEvent(
        resource_id="test-resource-123",
        document_url="http://example.com/test.pdf",
        chunks_count=2,
        status="ready",
        chunks=provided_chunks,
    )
    mock_msg = AsyncMock()
    mock_msg.data = json.dumps(
        {
            "resource_id": event.resource_id,
            "document_url": event.document_url,
            "chunks_count": event.chunks_count,
            "status": event.status,
            "chunks": provided_chunks,
        }
    ).encode()
    mock_msg.ack = AsyncMock()

    # Process the event
    await coordinator._handle_document_ready(mock_msg, config)

    # Verify chunks were NOT pulled from backend
    coordinator._get_chunks_for_resource.assert_not_called()

    # Verify analysis was run with provided chunks
    coordinator._run_analysis.assert_called_once_with(
        provided_chunks, "tcfd", {"model": "gpt-4o-mini"}
    )

    # Verify results were stored
    coordinator._store_analysis_to_backend.assert_called_once_with(
        "test-resource-123", mock_analysis_result, "tcfd"
    )

    # Verify message was acked
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_process_document_ready_no_chunks():
    """Test handling document.ready when no chunks are found"""
    coordinator = NATSJobCoordinator()

    # Mock NATS connection
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    coordinator.nc = mock_nc
    coordinator.js = mock_js

    # Mock search backend client - return empty chunks
    coordinator.search_backend = Mock()
    coordinator.search_backend.base_url = "http://localhost:8000"
    coordinator._get_chunks_for_resource = AsyncMock(return_value=[])

    # Create config
    config = DocumentReadyProcessingConfig(
        pull_chunks=True,
        question_set="tcfd",
        ack_on_error=True,
    )

    # Create a mock message
    event = DocumentReadyEvent(
        resource_id="test-resource-123",
        document_url="http://example.com/test.pdf",
        chunks_count=0,
        status="ready",
    )
    mock_msg = AsyncMock()
    mock_msg.data = json.dumps(
        {
            "resource_id": event.resource_id,
            "document_url": event.document_url,
            "chunks_count": event.chunks_count,
            "status": event.status,
        }
    ).encode()
    mock_msg.ack = AsyncMock()

    # Process the event
    await coordinator._handle_document_ready(mock_msg, config)

    # Verify message was acked even though no chunks
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_store_analysis_to_backend(mock_analysis_result):
    """Test storing analysis results to backend"""
    coordinator = NATSJobCoordinator()
    coordinator.search_backend = Mock()
    coordinator.search_backend.base_url = "http://localhost:8000"

    with patch(
        "report_analyst_search_backend.backend_service.BackendService.store_analysis_results"
    ) as mock_store:
        mock_store.return_value = "stored-result-id-123"

        await coordinator._store_analysis_to_backend(
            "test-resource-123",
            mock_analysis_result,
            "tcfd",
        )

        # Verify store was called
        mock_store.assert_called_once()
        call_args = mock_store.call_args
        assert call_args[0][0] == "test-resource-123"  # resource_id
        assert call_args[0][1] == mock_analysis_result  # analysis_result
        assert call_args[0][2] == "tcfd"  # question_set
        assert "source" in call_args[0][3]  # metadata


@pytest.mark.asyncio
async def test_config_options():
    """Test various configuration options"""
    # Test default config
    config1 = DocumentReadyProcessingConfig()
    assert config1.pull_chunks is True
    assert config1.store_to_backend is True
    assert config1.question_set == "tcfd"

    # Test custom config
    config2 = DocumentReadyProcessingConfig(
        pull_chunks=False,
        store_to_backend=False,
        question_set="custom",
        chunk_retrieval_method="direct",
        max_chunks=100,
    )
    assert config2.pull_chunks is False
    assert config2.store_to_backend is False
    assert config2.question_set == "custom"
    assert config2.chunk_retrieval_method == "direct"
    assert config2.max_chunks == 100

    # Test to_dict
    config_dict = config2.to_dict()
    assert config_dict["pull_chunks"] is False
    assert config_dict["chunk_retrieval_method"] == "direct"
    assert config_dict["max_chunks"] == 100
