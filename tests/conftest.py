"""
Shared pytest fixtures for all tests.

Provides test environment configuration and common fixtures.
"""

# Load .env first so OPENBLAS_NUM_THREADS=1 is set before any NumPy/OpenBLAS import (avoids SIGSEGV on macOS ARM)
import os
from pathlib import Path

_conftest_dir = Path(__file__).resolve().parent
_env = _conftest_dir.parent / ".env"
if _env.exists():
    from dotenv import load_dotenv

    load_dotenv(_env)
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import json
import tempfile
from unittest.mock import AsyncMock, Mock

import pytest
import yaml

from report_analyst_jobs.event_router import IGNORE_ACTION, EventRouter

# =============================================================================
# Test Environment Configuration
# =============================================================================
# Override environment variables for test isolation
# These are set before any test imports happen


def _setup_test_environment():
    """Configure test environment variables.

    This sets up isolated test configuration to avoid affecting production data.
    Tests can override these values using pytest fixtures or monkeypatch.
    """
    test_env = {
        # Use separate test database
        "TEST_DATABASE_URL": os.getenv("TEST_DATABASE_URL", "postgresql://analyst:analyst@localhost:5432/reports_test"),
        # Disable enterprise features by default in tests
        "USE_S3_UPLOAD": os.getenv("TEST_USE_S3_UPLOAD", "false"),
        # Use test storage path
        "TEST_STORAGE_PATH": os.getenv("TEST_STORAGE_PATH", "storage_test"),
    }
    return test_env


TEST_ENV = _setup_test_environment()


def pytest_configure(config):
    """Pytest hook to configure test environment."""
    # Register custom markers
    config.addinivalue_line("markers", "postgres: mark test as requiring PostgreSQL")
    config.addinivalue_line("markers", "integration: mark test as integration test")


# =============================================================================
# PostgreSQL Test Database Configuration
# =============================================================================
# Uses a dedicated test database (test_reports) with transaction rollback
# for test isolation. Each test runs in a transaction that is rolled back
# after the test, keeping the database clean.


def _get_test_database_url():
    """Get the test database URL from environment.

    Uses TEST_DATABASE_URL if set, otherwise constructs from PGHOST/PGPORT/etc.
    """
    # First check for explicit TEST_DATABASE_URL
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        return url

    # Construct from PG* environment variables
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "analyst")
    password = os.getenv("PGPASSWORD", "analyst")
    dbname = os.getenv("TEST_PGDATABASE", "test_reports")

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def _test_database_connection(url):
    """Test if we can connect to the database."""
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a SQLAlchemy engine for the test database.

    Session-scoped to reuse the connection pool across all tests.
    """
    from sqlalchemy import create_engine, text

    url = _get_test_database_url()

    if not _test_database_connection(url):
        pytest.skip(f"Cannot connect to test database: {url}")
        return None

    engine = create_engine(url)

    # Set up schema once at the start of the test session
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS stored_files (
                id VARCHAR(36) PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_data BYTEA NOT NULL,
                content_type VARCHAR(100),
                file_size VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )
        conn.commit()

    yield engine

    engine.dispose()


@pytest.fixture(scope="function")
def test_db_connection(test_db_engine):
    """Provide a database connection with transaction rollback.

    Each test runs in a transaction that is rolled back after the test,
    ensuring complete test isolation without affecting other tests.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()

    yield connection

    # Rollback the transaction after each test
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_database_url(test_db_engine):
    """Get the test database URL."""
    return _get_test_database_url()


@pytest.fixture
def postgres_available(test_database_url):
    """Fixture that skips test if PostgreSQL is not available."""
    if not test_database_url:
        pytest.skip("PostgreSQL test database not available")
    return test_database_url


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
