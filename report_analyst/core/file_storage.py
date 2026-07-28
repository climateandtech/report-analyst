"""
File Storage Service

Provides file storage abstraction with support for:
- Local filesystem (default)
- PostgreSQL (for Heroku deployments)
- S3 (enterprise feature)
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    text,
)

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class FileStorageError(Exception):
    """Exception raised for file storage errors"""

    pass


class PostgreSQLFileStorage:
    """Store files in PostgreSQL database as BYTEA/BLOB"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize PostgreSQL file storage.

        Args:
            database_url: Database connection string. If None, uses environment variable.
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
            if database_url is None:
                raise FileStorageError("DATABASE_URL not set for PostgreSQL file storage")

        self.db_manager = DatabaseManager(database_url)
        if not self.db_manager.is_postgres():
            raise FileStorageError("PostgreSQL file storage requires PostgreSQL database")

        # Check if we should use Alembic migrations instead of auto-creation
        use_alembic = os.getenv("USE_ALEMBIC_MIGRATIONS", "false").lower() == "true"
        if use_alembic:
            logger.info("Using Alembic migrations - skipping auto table creation for stored_files")
        else:
            self._init_table()

    def _init_table(self):
        """Initialize the stored_files table"""
        try:
            metadata = MetaData()
            stored_files = Table(
                "stored_files",
                metadata,
                Column("id", String(36), primary_key=True),  # UUID as string
                Column("filename", Text, nullable=False),
                Column("file_data", LargeBinary, nullable=False),  # BYTEA in PostgreSQL
                Column("content_type", Text, nullable=True),
                Column("file_size", Text, nullable=False),  # Store as string for large files
                Column("created_at", DateTime, default=datetime.now),
            )

            engine = self.db_manager.get_engine()
            metadata.create_all(engine, checkfirst=True)
            logger.info("stored_files table initialized")
        except Exception as e:
            logger.error(f"Error initializing stored_files table: {str(e)}")
            raise FileStorageError(f"Failed to initialize file storage table: {str(e)}")

    def store_file(self, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Store file in PostgreSQL and return file ID.

        Args:
            file_bytes: File content as bytes
            filename: Original filename
            content_type: MIME type (optional)

        Returns:
            file_id: Unique identifier for the stored file
        """
        try:
            file_id = str(uuid.uuid4())
            file_size = len(file_bytes)

            with self.db_manager.get_connection() as conn:
                # Use parameterized query for safety
                query = text(
                    """
                    INSERT INTO stored_files (id, filename, file_data, content_type, file_size, created_at)
                    VALUES (:id, :filename, :file_data, :content_type, :file_size, :created_at)
                """
                )
                conn.execute(
                    query,
                    {
                        "id": file_id,
                        "filename": filename,
                        "file_data": file_bytes,
                        "content_type": content_type or "application/pdf",
                        "file_size": str(file_size),
                        "created_at": datetime.now(),
                    },
                )
                conn.commit()

            logger.info(f"Stored file {filename} (ID: {file_id}, size: {file_size} bytes) in PostgreSQL")
            return file_id
        except Exception as e:
            logger.error(f"Error storing file in PostgreSQL: {str(e)}")
            raise FileStorageError(f"Failed to store file: {str(e)}")

    def retrieve_file(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve file from PostgreSQL.

        Args:
            file_id: Unique identifier for the stored file

        Returns:
            File content as bytes, or None if not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                query = text("SELECT file_data FROM stored_files WHERE id = :file_id")
                result = conn.execute(query, {"file_id": file_id})
                row = result.fetchone()

                if row:
                    return bytes(row[0])
                return None
        except Exception as e:
            logger.error(f"Error retrieving file {file_id} from PostgreSQL: {str(e)}")
            raise FileStorageError(f"Failed to retrieve file: {str(e)}")

    def get_file_info(self, file_id: str) -> Optional[dict]:
        """
        Get file metadata without retrieving the file data.

        Args:
            file_id: Unique identifier for the stored file

        Returns:
            Dictionary with file info, or None if not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                query = text(
                    """
                    SELECT filename, content_type, file_size, created_at
                    FROM stored_files WHERE id = :file_id
                """
                )
                result = conn.execute(query, {"file_id": file_id})
                row = result.fetchone()

                if row:
                    return {
                        "filename": row[0],
                        "content_type": row[1],
                        "file_size": int(row[2]) if row[2] else 0,
                        "created_at": row[3],
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting file info for {file_id}: {str(e)}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from PostgreSQL.

        Args:
            file_id: Unique identifier for the stored file

        Returns:
            True if deleted, False if not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                query = text("DELETE FROM stored_files WHERE id = :file_id")
                result = conn.execute(query, {"file_id": file_id})
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            return False

    def find_by_filename(self, filename: str) -> Optional[str]:
        """
        Find a file by filename and return its ID.

        Args:
            filename: Original filename to search for

        Returns:
            file_id if found, None otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                query = text("SELECT id FROM stored_files WHERE filename = :filename ORDER BY created_at DESC LIMIT 1")
                result = conn.execute(query, {"filename": filename})
                row = result.fetchone()
                if row:
                    return row[0]
                return None
        except Exception as e:
            logger.error(f"Error finding file by filename {filename}: {str(e)}")
            return None

    def save_to_temp(self, file_id: str, temp_dir: Path = Path("temp")) -> Optional[str]:
        """
        Retrieve file from PostgreSQL and save to temporary directory.

        Args:
            file_id: Unique identifier for the stored file
            temp_dir: Directory to save the file to

        Returns:
            Path to the temporary file, or None if not found
        """
        try:
            file_info = self.get_file_info(file_id)
            if not file_info:
                return None

            file_bytes = self.retrieve_file(file_id)
            if not file_bytes:
                return None

            # Create temp directory if it doesn't exist
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Save to temp file
            temp_path = temp_dir / file_info["filename"]
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            logger.info(f"Retrieved file {file_id} to {temp_path}")
            return str(temp_path)
        except Exception as e:
            logger.error(f"Error saving file {file_id} to temp: {str(e)}")
            return None


def get_file_storage(
    database_url: Optional[str] = None,
) -> Optional[PostgreSQLFileStorage]:
    """
    Get file storage instance if PostgreSQL is configured.

    Args:
        database_url: Database connection string (optional)

    Returns:
        PostgreSQLFileStorage instance if PostgreSQL is configured, None otherwise
    """
    try:
        # Check if PostgreSQL file storage is enabled
        use_postgres_storage = os.getenv("USE_POSTGRES_FILE_STORAGE", "false").lower() == "true"
        if not use_postgres_storage:
            return None

        # Check if we have a PostgreSQL database
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")

        if database_url and database_url.startswith(("postgresql://", "postgres://")):
            return PostgreSQLFileStorage(database_url)

        return None
    except Exception as e:
        logger.warning(f"PostgreSQL file storage not available: {str(e)}")
        return None
