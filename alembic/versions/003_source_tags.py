"""add tags on PDF sources

Revision ID: 003_source_tags
Revises: 002_source_annotations
Create Date: 2026-11-13 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "003_source_tags"
down_revision: Union[str, None] = "002_source_annotations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_tags",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("document_id", sa.Text(), nullable=False),
        sa.Column("concept", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("unit", sa.Text()),
        sa.Column("decimals", sa.Integer()),
        sa.Column("created_at", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_source_tags_document_id", "source_tags", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_source_tags_document_id", table_name="source_tags")
    op.drop_table("source_tags")
