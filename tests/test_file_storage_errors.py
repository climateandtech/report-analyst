"""Unit tests for PostgreSQL file storage error paths (no live DB required)."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from report_analyst.core.file_storage import (
    FileStorageError,
    PostgreSQLFileStorage,
    get_file_storage,
)


def _storage_with_failing_conn():
    storage = PostgreSQLFileStorage.__new__(PostgreSQLFileStorage)
    storage.db_manager = MagicMock()
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute.side_effect = SQLAlchemyError("db down")
    storage.db_manager.get_connection.return_value = conn
    storage.db_manager.get_engine.side_effect = SQLAlchemyError("engine down")
    return storage


def test_init_table_raises_file_storage_error_on_sqlalchemy_error():
    storage = _storage_with_failing_conn()
    with pytest.raises(FileStorageError, match="Failed to initialize"):
        storage._init_table()


def test_store_retrieve_info_delete_find_handle_sqlalchemy_errors():
    storage = _storage_with_failing_conn()

    with pytest.raises(FileStorageError, match="Failed to store"):
        storage.store_file(b"data", "a.pdf")

    with pytest.raises(FileStorageError, match="Failed to retrieve"):
        storage.retrieve_file("id-1")

    assert storage.get_file_info("id-1") is None
    assert storage.delete_file("id-1") is False
    assert storage.find_by_filename("a.pdf") is None


def test_save_to_temp_returns_none_on_storage_error(tmp_path):
    storage = PostgreSQLFileStorage.__new__(PostgreSQLFileStorage)
    storage.db_manager = MagicMock()
    storage.get_file_info = MagicMock(side_effect=FileStorageError("boom"))
    assert storage.save_to_temp("id-1", temp_dir=tmp_path) is None


def test_get_file_storage_returns_none_when_ctor_raises(monkeypatch):
    monkeypatch.setenv("USE_POSTGRES_FILE_STORAGE", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    with patch(
        "report_analyst.core.file_storage.PostgreSQLFileStorage",
        side_effect=FileStorageError("unavailable"),
    ):
        assert get_file_storage() is None
