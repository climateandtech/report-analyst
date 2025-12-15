"""
Tests for PostgreSQL file storage service.

Tests that files can be stored and retrieved from PostgreSQL.
"""

import os

import pytest

from report_analyst.core.file_storage import (
    FileStorageError,
    PostgreSQLFileStorage,
    get_file_storage,
)


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("DATABASE_URL").startswith(("postgresql://", "postgres://")),
    reason="PostgreSQL not configured",
)
def test_postgres_file_storage_store_and_retrieve():
    """Test storing and retrieving a file from PostgreSQL"""
    database_url = os.getenv("DATABASE_URL")
    storage = PostgreSQLFileStorage(database_url)

    # Test file content
    test_content = b"Test file content for PostgreSQL storage"
    filename = "test_file.pdf"

    # Store file
    file_id = storage.store_file(test_content, filename, "application/pdf")
    assert file_id is not None
    assert len(file_id) == 36  # UUID length

    # Retrieve file
    retrieved_content = storage.retrieve_file(file_id)
    assert retrieved_content == test_content

    # Get file info
    file_info = storage.get_file_info(file_id)
    assert file_info is not None
    assert file_info["filename"] == filename
    assert file_info["content_type"] == "application/pdf"
    assert file_info["file_size"] == len(test_content)

    # Clean up
    storage.delete_file(file_id)


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("DATABASE_URL").startswith(("postgresql://", "postgres://")),
    reason="PostgreSQL not configured",
)
def test_postgres_file_storage_delete():
    """Test deleting a file from PostgreSQL"""
    database_url = os.getenv("DATABASE_URL")
    storage = PostgreSQLFileStorage(database_url)

    # Store file
    test_content = b"Test file to delete"
    file_id = storage.store_file(test_content, "delete_test.pdf")

    # Delete file
    deleted = storage.delete_file(file_id)
    assert deleted is True

    # Verify file is gone
    retrieved = storage.retrieve_file(file_id)
    assert retrieved is None


def test_get_file_storage_without_postgres():
    """Test that get_file_storage returns None when PostgreSQL is not configured"""
    # Temporarily unset DATABASE_URL
    original_url = os.environ.get("DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

    # Unset USE_POSTGRES_FILE_STORAGE
    original_setting = os.environ.get("USE_POSTGRES_FILE_STORAGE")
    if "USE_POSTGRES_FILE_STORAGE" in os.environ:
        del os.environ["USE_POSTGRES_FILE_STORAGE"]

    try:
        storage = get_file_storage()
        assert storage is None
    finally:
        # Restore original values
        if original_url:
            os.environ["DATABASE_URL"] = original_url
        if original_setting:
            os.environ["USE_POSTGRES_FILE_STORAGE"] = original_setting


def test_postgres_file_storage_requires_postgres():
    """Test that PostgreSQLFileStorage raises error for SQLite"""
    # Use SQLite URL
    sqlite_url = "sqlite:///test.db"

    with pytest.raises(FileStorageError, match="PostgreSQL"):
        PostgreSQLFileStorage(sqlite_url)
