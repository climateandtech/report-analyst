"""
Database Manager using SQLAlchemy

Provides unified database interface for both SQLite and PostgreSQL.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections using SQLAlchemy."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            database_url: Database connection string. If None, uses SQLite default.
                - SQLite: sqlite:///path/to/db
                - PostgreSQL: postgresql://user:pass@host:port/db
        """
        if database_url is None:
            # Check DATABASE_URL environment variable first
            database_url = os.getenv("DATABASE_URL")
            if database_url is None:
                # Default to SQLite
                storage_path = os.getenv("STORAGE_PATH", "./storage")
                db_path = str(Path(storage_path) / "cache" / "analysis.db")
                # Ensure parent directory exists
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                database_url = f"sqlite:///{db_path}"

        self.database_url = database_url
        self._engine: Optional[Engine] = None
        self._is_postgres = database_url.startswith(("postgresql://", "postgres://"))

        logger.info(f"Initializing DatabaseManager with URL: {self._mask_url(database_url)}")
        logger.info(f"Database type: {'PostgreSQL' if self._is_postgres else 'SQLite'}")

    def _mask_url(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if "@" in url:
            parts = url.split("@")
            if len(parts) == 2:
                user_pass = parts[0].split("://")[-1]
                if ":" in user_pass:
                    user = user_pass.split(":")[0]
                    return url.replace(user_pass, f"{user}:***")
        return url

    def get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            # For SQLite, use check_same_thread=False for compatibility
            connect_args = {}
            if not self._is_postgres:
                connect_args["check_same_thread"] = False

            self._engine = create_engine(
                self.database_url,
                connect_args=connect_args,
                echo=False,  # Set to True for SQL debugging
            )
            logger.info("SQLAlchemy engine created")
        return self._engine

    @contextmanager
    def get_connection(self):
        """Get database connection (context manager)."""
        engine = self.get_engine()
        conn = engine.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: Optional[dict] = None):
        """Execute a query and return result."""
        with self.get_connection() as conn:
            result = conn.execute(text(query), params or {})
            return result

    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self._is_postgres

    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return not self._is_postgres
