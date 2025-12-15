import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from report_analyst.core.database_manager import DatabaseManager

# Import our database schema
from report_analyst.core.database_schema import metadata as db_metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment or use DatabaseManager
database_url = os.getenv("DATABASE_URL")
if database_url is None:
    # Use DatabaseManager to get default URL (SQLite)
    db_manager = DatabaseManager()
    database_url = db_manager.database_url
else:
    # Validate it's a valid URL format
    db_manager = DatabaseManager(database_url)

# Set the database URL in config
config.set_main_option("sqlalchemy.url", database_url)

from datetime import datetime

# Combine metadata from database_schema and file_storage
from sqlalchemy import Column, DateTime, LargeBinary, MetaData, String, Table, Text

# Use the database_schema metadata as base
target_metadata = db_metadata

# Add stored_files table to the metadata (from file_storage.py)
# This table is created dynamically in file_storage, so we define it here for migrations
if "stored_files" not in target_metadata.tables:
    stored_files = Table(
        "stored_files",
        target_metadata,
        Column("id", String(36), primary_key=True),  # UUID as string
        Column("filename", Text, nullable=False),
        Column("file_data", LargeBinary, nullable=False),  # BYTEA in PostgreSQL
        Column("content_type", Text, nullable=True),
        Column("file_size", Text, nullable=False),  # Store as string for large files
        Column("created_at", DateTime, default=datetime.now),
    )

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
