"""
Migration Utilities

Helper functions for checking migration status and managing database migrations.
"""

import logging
import os
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


def get_alembic_config(database_url: Optional[str] = None) -> Config:
    """
    Get Alembic configuration.

    Args:
        database_url: Database connection string. If None, uses environment variable.

    Returns:
        Alembic Config object
    """
    alembic_ini_path = os.getenv("ALEMBIC_CONFIG", "alembic.ini")
    config = Config(alembic_ini_path)

    # Set database URL if provided
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)
    elif os.getenv("DATABASE_URL"):
        config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

    return config


def get_current_revision(database_url: Optional[str] = None) -> Optional[str]:
    """
    Get the current database revision.

    Args:
        database_url: Database connection string. If None, uses environment variable.

    Returns:
        Current revision string, or None if no migrations have been applied
    """
    try:
        config = get_alembic_config(database_url)

        # Get database manager to create engine
        if database_url:
            db_manager = DatabaseManager(database_url)
        else:
            db_manager = DatabaseManager()

        engine = db_manager.get_engine()

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            return current_rev
    except Exception as e:
        logger.error(f"Error getting current revision: {str(e)}")
        return None


def get_head_revision() -> Optional[str]:
    """
    Get the head (latest) migration revision.

    Returns:
        Head revision string, or None if no migrations exist
    """
    try:
        config = get_alembic_config()
        script = ScriptDirectory.from_config(config)
        head = script.get_current_head()
        return head
    except Exception as e:
        logger.error(f"Error getting head revision: {str(e)}")
        return None


def needs_migration(database_url: Optional[str] = None) -> bool:
    """
    Check if database needs migration.

    Args:
        database_url: Database connection string. If None, uses environment variable.

    Returns:
        True if migration is needed, False otherwise
    """
    try:
        current_rev = get_current_revision(database_url)
        head_rev = get_head_revision()

        if head_rev is None:
            # No migrations exist
            return False

        if current_rev is None:
            # Database has no migrations applied
            return True

        return current_rev != head_rev
    except Exception as e:
        logger.error(f"Error checking migration status: {str(e)}")
        return False


def check_migration_status(database_url: Optional[str] = None) -> dict:
    """
    Check migration status and return detailed information.

    Args:
        database_url: Database connection string. If None, uses environment variable.

    Returns:
        Dictionary with migration status information
    """
    try:
        current_rev = get_current_revision(database_url)
        head_rev = get_head_revision()

        return {
            "current_revision": current_rev,
            "head_revision": head_rev,
            "is_up_to_date": (current_rev == head_rev if (current_rev and head_rev) else False),
            "needs_migration": needs_migration(database_url),
        }
    except Exception as e:
        logger.error(f"Error checking migration status: {str(e)}")
        return {
            "current_revision": None,
            "head_revision": None,
            "is_up_to_date": False,
            "needs_migration": False,
            "error": str(e),
        }


def run_migrations(database_url: Optional[str] = None, revision: str = "head") -> bool:
    """
    Run database migrations.

    Args:
        database_url: Database connection string. If None, uses environment variable.
        revision: Target revision (default: "head")

    Returns:
        True if successful, False otherwise
    """
    try:
        config = get_alembic_config(database_url)
        command.upgrade(config, revision)
        logger.info(f"Successfully upgraded database to revision: {revision}")
        return True
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        return False
