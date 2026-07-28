"""
Tests for PostgreSQL file storage service.

Tests that files can be stored and retrieved from PostgreSQL.

These tests require a running PostgreSQL database. They will be skipped
if the test database is not available. Configure TEST_DATABASE_URL
environment variable to point to your test database.
"""

import os

import pytest

from report_analyst.core.file_storage import (
    FileStorageError,
    PostgreSQLFileStorage,
    get_file_storage,
)


@pytest.mark.postgres
def test_postgres_file_storage_store_and_retrieve(postgres_available):
    """Test storing and retrieving a file from PostgreSQL"""
    storage = PostgreSQLFileStorage(postgres_available)

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


@pytest.mark.postgres
def test_postgres_file_storage_delete(postgres_available):
    """Test deleting a file from PostgreSQL"""
    storage = PostgreSQLFileStorage(postgres_available)

    # Store file
    test_content = b"Test file to delete"
    file_id = storage.store_file(test_content, "delete_test.pdf")

    # Delete file
    deleted = storage.delete_file(file_id)
    assert deleted is True

    # Verify file is gone
    retrieved = storage.retrieve_file(file_id)
    assert retrieved is None


@pytest.mark.postgres
def test_postgres_file_storage_find_by_filename(postgres_available):
    """Test finding a file by filename in PostgreSQL"""
    storage = PostgreSQLFileStorage(postgres_available)

    # Store file
    test_content = b"Test file for find by filename"
    filename = "find_test_unique.pdf"
    file_id = storage.store_file(test_content, filename, "application/pdf")

    try:
        # Find by filename
        found_id = storage.find_by_filename(filename)
        assert found_id == file_id

        # Find non-existent file
        not_found = storage.find_by_filename("nonexistent_file.pdf")
        assert not_found is None
    finally:
        # Clean up
        storage.delete_file(file_id)


@pytest.mark.postgres
def test_postgres_file_storage_retrieve_existing(postgres_available):
    """Test the flow where a file already exists in PostgreSQL and is retrieved instead of re-uploaded"""
    storage = PostgreSQLFileStorage(postgres_available)

    # Store file first time
    test_content = b"Test content for existing file retrieval"
    filename = "existing_file_test.pdf"
    original_file_id = storage.store_file(test_content, filename, "application/pdf")

    try:
        # Simulate new session - find existing file by filename
        found_id = storage.find_by_filename(filename)
        assert found_id == original_file_id

        # Retrieve the file using the found ID
        temp_path = storage.save_to_temp(found_id)
        assert temp_path is not None
        assert filename in temp_path

        # Verify content matches
        with open(temp_path, "rb") as f:
            retrieved_content = f.read()
        assert retrieved_content == test_content

        # Clean up temp file
        import os

        if os.path.exists(temp_path):
            os.remove(temp_path)
    finally:
        # Clean up database
        storage.delete_file(original_file_id)


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
