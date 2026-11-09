"""add PDF source annotations

Revision ID: 002_source_annotations
Revises: 001_initial_schema
Create Date: 2026-09-14 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "002_source_annotations"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_annotations",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("document_id", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("span_start", sa.Integer(), nullable=False),
        sa.Column("span_end", sa.Integer(), nullable=False),
        sa.Column("selected_text", sa.Text(), nullable=False),
        sa.Column("rects", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_source_annotations_document_id",
        "source_annotations",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_source_annotations_document_id", table_name="source_annotations")
    op.drop_table("source_annotations")
