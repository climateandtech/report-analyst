import sqlite3

from alembic import command
from alembic.config import Config


def test_migrations_create_the_source_tags_table(monkeypatch, tmp_path):
    database = tmp_path / "migrated.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database}")

    command.upgrade(Config("alembic.ini"), "head")

    with sqlite3.connect(database) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(source_tags)")]
    assert columns == ["id", "source_id", "document_id", "concept", "value", "unit", "decimals", "created_at"]
