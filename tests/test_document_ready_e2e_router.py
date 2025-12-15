"""
End-to-End Test for document.ready Flow with Event Router

Tests the complete flow:
1. Backend publishes document.ready event to NATS
2. Event router receives and routes it
3. Handler pulls chunks from backend
4. Handler runs analysis
5. Handler stores results back to backend
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from report_analyst_jobs.event_router import EventContext, EventRouter
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


@pytest.fixture
def document_ready_handler(mock_chunks, mock_analysis_result):
    """Create a handler for document.ready events that uses NATSJobCoordinator"""
    coordinator = NATSJobCoordinator()

    # Mock search backend client
    coordinator.search_backend = Mock()
    coordinator.search_backend.base_url = "http://localhost:8000"
    coordinator._get_chunks_for_resource = AsyncMock(return_value=mock_chunks)
    coordinator._run_analysis = AsyncMock(return_value=mock_analysis_result)
    coordinator._store_analysis_to_backend = AsyncMock()

    # Create config
    config = DocumentReadyProcessingConfig(
        pull_chunks=True,
        question_set="tcfd",
        analysis_config={"model": "gpt-4o-mini"},
        store_to_backend=True,
    )

    async def handler(ctx: EventContext):
        """Handler that processes document.ready events"""
        event = DocumentReadyEvent(**ctx.data)
        await coordinator._handle_document_ready(ctx.message, config)

    return handler, coordinator


@pytest.mark.asyncio
async def test_e2e_document_ready_flow_with_router(
    event_router_yaml_file,
    mock_nats_connection,
    document_ready_handler,
    mock_chunks,
    mock_analysis_result,
):
    """End-to-end test: document.ready event → router → handler → full processing"""
    handler, coordinator = document_ready_handler

    # Create router with handler
    router = EventRouter.from_yaml(
        yaml_path=event_router_yaml_file,
        handler_registry={"handle_document_ready": handler},
    )

    # Mock NATS connection
    mock_nc, mock_js = mock_nats_connection
    router.nc = mock_nc
    router.js = mock_js

    # Create document.ready event message
    event_data = {
        "resource_id": "test-resource-123",
        "document_url": "http://example.com/test.pdf",
        "chunks_count": 2,
        "status": "ready",
    }
    mock_msg = AsyncMock()
    mock_msg.subject = "document.ready"
    mock_msg.data = json.dumps(event_data).encode()
    mock_msg.ack = AsyncMock()

    # Process through router
    await router._handle_message(mock_msg)

    # Verify full flow executed:
    # 1. Chunks were retrieved
    coordinator._get_chunks_for_resource.assert_called_once_with("test-resource-123", "search", None)

    # 2. Analysis was run
    coordinator._run_analysis.assert_called_once_with(mock_chunks, "tcfd", {"model": "gpt-4o-mini"})

    # 3. Results were stored
    coordinator._store_analysis_to_backend.assert_called_once_with("test-resource-123", mock_analysis_result, "tcfd")

    # 4. Message was acked
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_document_ready_ignore_with_router(
    event_router_yaml_file,
    mock_nats_connection,
):
    """Test that document.upload events are ignored via router"""
    # Create router with ignore rule for document.upload
    router = EventRouter.from_yaml(
        yaml_path=event_router_yaml_file,
        handler_registry={},
    )

    # Add ignore rule for document.upload
    router.add_rule("document.upload", "ignore", priority=5)

    # Mock NATS
    mock_nc, mock_js = mock_nats_connection
    router.nc = mock_nc
    router.js = mock_js

    # Create document.upload event (should be ignored)
    mock_msg = AsyncMock()
    mock_msg.subject = "document.upload"
    mock_msg.data = json.dumps({"resource_id": "test-456"}).encode()
    mock_msg.ack = AsyncMock()

    # Process through router
    await router._handle_message(mock_msg)

    # Should be acked but not processed
    mock_msg.ack.assert_called_once()
    # No handlers should have been called (we didn't register any for upload)


@pytest.mark.asyncio
async def test_e2e_document_ready_with_provided_chunks(
    event_router_yaml_file,
    mock_nats_connection,
    mock_analysis_result,
):
    """Test document.ready flow with chunks provided in event (no pulling)"""
    coordinator = NATSJobCoordinator()
    coordinator._get_chunks_for_resource = AsyncMock()  # Should not be called
    coordinator._run_analysis = AsyncMock(return_value=mock_analysis_result)
    coordinator._store_analysis_to_backend = AsyncMock()

    config = DocumentReadyProcessingConfig(
        pull_chunks=False,  # Don't pull, use provided chunks
        question_set="tcfd",
        analysis_config={"model": "gpt-4o-mini"},
        store_to_backend=True,
    )

    async def handler(ctx: EventContext):
        event = DocumentReadyEvent(**ctx.data)
        await coordinator._handle_document_ready(ctx.message, config)

    router = EventRouter.from_yaml(
        yaml_path=event_router_yaml_file,
        handler_registry={"handle_document_ready": handler},
    )

    mock_nc, mock_js = mock_nats_connection
    router.nc = mock_nc
    router.js = mock_js

    # Event with chunks included
    provided_chunks = [
        {"id": "chunk-1", "text": "Test chunk 1", "metadata": {}},
        {"id": "chunk-2", "text": "Test chunk 2", "metadata": {}},
    ]
    event_data = {
        "resource_id": "test-resource-123",
        "document_url": "http://example.com/test.pdf",
        "chunks_count": 2,
        "status": "ready",
        "chunks": provided_chunks,
    }

    mock_msg = AsyncMock()
    mock_msg.subject = "document.ready"
    mock_msg.data = json.dumps(event_data).encode()
    mock_msg.ack = AsyncMock()

    await router._handle_message(mock_msg)

    # Verify chunks were NOT pulled
    coordinator._get_chunks_for_resource.assert_not_called()

    # Verify analysis was run with provided chunks
    coordinator._run_analysis.assert_called_once_with(provided_chunks, "tcfd", {"model": "gpt-4o-mini"})

    # Verify results stored
    coordinator._store_analysis_to_backend.assert_called_once()
    mock_msg.ack.assert_called_once()
