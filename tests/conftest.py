"""
Shared pytest fixtures for event router tests
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import yaml

# Add project root and parent directory to Python path
# This allows tests to import report_analyst and report_analyst_jobs
project_root = Path(__file__).parent.parent
parent_dir = project_root.parent

for path in [str(project_root), str(parent_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Make report_analyst_jobs import optional
try:
    from report_analyst_jobs.event_router import IGNORE_ACTION, EventRouter

    REPORT_ANALYST_JOBS_AVAILABLE = True
except ImportError:
    REPORT_ANALYST_JOBS_AVAILABLE = False
    # Create dummy objects to avoid NameError
    IGNORE_ACTION = None
    EventRouter = None


@pytest.fixture
def event_router_config():
    """Default event router configuration for tests"""
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
        "handlers": {},
    }


@pytest.fixture
def event_router_yaml_file(event_router_config, tmp_path):
    """Create temporary YAML file for event router configuration"""
    yaml_file = tmp_path / "event_routing.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(event_router_config, f)
    return yaml_file


@pytest.fixture
def mock_nats_connection():
    """Mock NATS connection for tests"""
    mock_nc = AsyncMock()
    mock_js = AsyncMock()
    mock_nc.jetstream.return_value = mock_js
    return mock_nc, mock_js


@pytest.fixture
def event_router_with_mocks(event_router_yaml_file, mock_nats_connection):
    """Event router with mocked NATS connection"""
    if not REPORT_ANALYST_JOBS_AVAILABLE:
        pytest.skip("report_analyst_jobs not available - skipping event router tests")

    mock_nc, mock_js = mock_nats_connection

    router = EventRouter.from_yaml(yaml_path=event_router_yaml_file)
    router.nc = mock_nc
    router.js = mock_js

    return router


@pytest.fixture
def mock_nats_message():
    """Factory for creating mock NATS messages"""

    def _create_message(subject: str, data: dict):
        mock_msg = AsyncMock()
        mock_msg.subject = subject
        mock_msg.data = json.dumps(data).encode()
        mock_msg.ack = AsyncMock()
        return mock_msg

    return _create_message
