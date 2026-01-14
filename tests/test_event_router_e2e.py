"""
End-to-End Tests for Event Router

Tests the complete flow:
1. Load routing configuration from YAML
2. Connect to NATS (mocked)
3. Receive events
4. Route to correct handlers
5. Execute handlers
6. Handle ignore actions
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from report_analyst_jobs.event_router import IGNORE_ACTION, EventContext, EventRouter


@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration for testing"""
    return {
        "routing": [
            {
                "pattern": "document.ready",
                "action": "handle_document_ready",
                "description": "Process document ready events",
                "enabled": True,
                "priority": 10,
            },
            {
                "pattern": "document.upload",
                "action": "ignore",
                "description": "Ignore document uploads",
                "enabled": True,
                "priority": 5,
            },
            {
                "pattern": "document.*",
                "action": "ignore",
                "description": "Ignore other document events",
                "enabled": True,
                "priority": 1,
            },
            {
                "pattern": "analysis.job.submit",
                "action": "handle_analysis_job",
                "description": "Process analysis jobs",
                "enabled": True,
                "priority": 10,
            },
        ],
        "handlers": {
            "handle_document_ready": "tests.test_event_router_e2e.handler_document_ready",
            "handle_analysis_job": "tests.test_event_router_e2e.handler_analysis_job",
        },
    }


@pytest.fixture
def temp_yaml_file(sample_yaml_config, tmp_path):
    """Create temporary YAML file for testing"""
    yaml_file = tmp_path / "test_event_routing.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(sample_yaml_config, f)
    return yaml_file


# Test handlers (will be imported by the router)
# Note: Names don't start with "test_" to avoid pytest treating them as test functions
handler_calls = []


async def handler_document_ready(ctx: EventContext):
    """Handler for document.ready events"""
    handler_calls.append(("document.ready", ctx.data))
    await ctx.message.ack()


async def handler_analysis_job(ctx: EventContext):
    """Handler for analysis.job.submit events"""
    handler_calls.append(("analysis.job.submit", ctx.data))
    await ctx.message.ack()


@pytest.mark.asyncio
async def test_e2e_yaml_load_and_route(temp_yaml_file, sample_yaml_config):
    """Test end-to-end: Load YAML, route events, execute handlers"""
    # Clear handler calls
    handler_calls.clear()

    # Create router from YAML
    router = EventRouter.from_yaml(
        yaml_path=temp_yaml_file,
        handler_registry={
            "handle_document_ready": handler_document_ready,
            "handle_analysis_job": handler_analysis_job,
        },
    )

    # Verify rules loaded
    rules = router.get_rules()
    assert len(rules) == 4

    # Mock NATS connection
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    router.nc = mock_nc
    router.js = mock_js

    # Test 1: Handle document.ready event (should call handler)
    mock_msg1 = AsyncMock()
    mock_msg1.subject = "document.ready"
    mock_msg1.data = json.dumps({"resource_id": "test-123", "status": "ready"}).encode()
    mock_msg1.ack = AsyncMock()

    await router._handle_message(mock_msg1)

    # Verify handler was called
    assert len(handler_calls) == 1
    assert handler_calls[0][0] == "document.ready"
    assert handler_calls[0][1]["resource_id"] == "test-123"
    mock_msg1.ack.assert_called_once()

    # Test 2: Handle document.upload event (should ignore)
    handler_calls.clear()
    mock_msg2 = AsyncMock()
    mock_msg2.subject = "document.upload"
    mock_msg2.data = json.dumps({"resource_id": "test-456"}).encode()
    mock_msg2.ack = AsyncMock()

    await router._handle_message(mock_msg2)

    # Verify handler was NOT called (ignored)
    assert len(handler_calls) == 0
    mock_msg2.ack.assert_called_once()  # Should still ack

    # Test 3: Handle analysis.job.submit event (should call handler)
    handler_calls.clear()
    mock_msg3 = AsyncMock()
    mock_msg3.subject = "analysis.job.submit"
    mock_msg3.data = json.dumps({"job_id": "job-789", "status": "pending"}).encode()
    mock_msg3.ack = AsyncMock()

    await router._handle_message(mock_msg3)

    # Verify handler was called
    assert len(handler_calls) == 1
    assert handler_calls[0][0] == "analysis.job.submit"
    assert handler_calls[0][1]["job_id"] == "job-789"
    mock_msg3.ack.assert_called_once()

    # Test 4: Handle document.other event (should match wildcard and ignore)
    handler_calls.clear()
    mock_msg4 = AsyncMock()
    mock_msg4.subject = "document.other"
    mock_msg4.data = json.dumps({"resource_id": "test-999"}).encode()
    mock_msg4.ack = AsyncMock()

    await router._handle_message(mock_msg4)

    # Verify handler was NOT called (matched wildcard ignore rule)
    assert len(handler_calls) == 0
    mock_msg4.ack.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_priority_ordering(temp_yaml_file):
    """Test that priority ordering works correctly in end-to-end flow"""
    handler_calls.clear()

    router = EventRouter.from_yaml(
        yaml_path=temp_yaml_file,
        handler_registry={
            "handle_document_ready": handler_document_ready,
        },
    )

    # Mock NATS
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    router.nc = mock_nc
    router.js = mock_js

    # document.ready should match the specific rule (priority 10) not the wildcard (priority 1)
    mock_msg = AsyncMock()
    mock_msg.subject = "document.ready"
    mock_msg.data = json.dumps({"resource_id": "test-priority"}).encode()
    mock_msg.ack = AsyncMock()

    await router._handle_message(mock_msg)

    # Should have called handler (specific rule, not wildcard ignore)
    assert len(handler_calls) == 1
    assert handler_calls[0][0] == "document.ready"


@pytest.mark.asyncio
async def test_e2e_disabled_rule(temp_yaml_file):
    """Test that disabled rules are skipped in end-to-end flow"""
    # Create YAML with disabled rule
    config = {
        "routing": [
            {
                "pattern": "document.ready",
                "action": "handle_document_ready",
                "enabled": False,  # Disabled
                "priority": 10,
            },
            {
                "pattern": "document.*",
                "action": "ignore",
                "enabled": True,
                "priority": 1,
            },
        ],
        "handlers": {},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_path = f.name

    try:
        router = EventRouter.from_yaml(
            yaml_path=yaml_path,
            handler_registry={"handle_document_ready": handler_document_ready},
        )

        # Mock NATS
        mock_nc = AsyncMock()
        mock_js = AsyncMock()
        router.nc = mock_nc
        router.js = mock_js

        handler_calls.clear()

        # document.ready should match wildcard ignore (specific rule is disabled)
        mock_msg = AsyncMock()
        mock_msg.subject = "document.ready"
        mock_msg.data = json.dumps({"resource_id": "test-disabled"}).encode()
        mock_msg.ack = AsyncMock()

        await router._handle_message(mock_msg)

        # Should be ignored (matched wildcard, not disabled specific rule)
        assert len(handler_calls) == 0
        mock_msg.ack.assert_called_once()
    finally:
        Path(yaml_path).unlink()


@pytest.mark.asyncio
async def test_e2e_error_handling(temp_yaml_file):
    """Test error handling in end-to-end flow"""
    handler_calls.clear()

    router = EventRouter.from_yaml(
        yaml_path=temp_yaml_file,
        handler_registry={
            "handle_document_ready": handler_document_ready,
        },
    )

    # Mock NATS
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    router.nc = mock_nc
    router.js = mock_js

    # Test 1: Invalid JSON
    mock_msg1 = AsyncMock()
    mock_msg1.subject = "document.ready"
    mock_msg1.data = b"invalid json"
    mock_msg1.ack = AsyncMock()

    await router._handle_message(mock_msg1)

    # Should ack even on error
    mock_msg1.ack.assert_called_once()
    assert len(handler_calls) == 0

    # Test 2: Handler raises exception
    async def failing_handler(ctx: EventContext):
        raise Exception("Handler failed")

    router.rules[0].action = failing_handler

    handler_calls.clear()
    mock_msg2 = AsyncMock()
    mock_msg2.subject = "document.ready"
    mock_msg2.data = json.dumps({"resource_id": "test-error"}).encode()
    mock_msg2.ack = AsyncMock()

    await router._handle_message(mock_msg2)

    # Should ack even on handler error
    mock_msg2.ack.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_routing_table_inspection(temp_yaml_file):
    """Test that routing table can be inspected after YAML load"""
    router = EventRouter.from_yaml(
        yaml_path=temp_yaml_file,
        handler_registry={
            "handle_document_ready": handler_document_ready,
            "handle_analysis_job": handler_analysis_job,
        },
    )

    table = router.get_routing_table()

    assert len(table) == 4
    # Check that table has expected structure
    assert all("pattern" in rule for rule in table)
    assert all("action" in rule for rule in table)
    assert all("description" in rule for rule in table)
    assert all("enabled" in rule for rule in table)
    assert all("priority" in rule for rule in table)

    # Check specific rules
    document_ready_rule = next(r for r in table if r["pattern"] == "document.ready")
    assert document_ready_rule["action"] == "handler"
    assert document_ready_rule["enabled"] is True
    assert document_ready_rule["priority"] == 10

    document_upload_rule = next(r for r in table if r["pattern"] == "document.upload")
    assert document_upload_rule["action"] == IGNORE_ACTION
    assert document_upload_rule["enabled"] is True
