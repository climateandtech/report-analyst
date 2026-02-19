"""initial_schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-12-14 01:00:00.000000

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Document chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("chunk_overlap", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), default=datetime.now),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_path", "chunk_text", "chunk_size", "chunk_overlap"),
    )

    # Questions table
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.Column("question_set", sa.Text(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=True),
        sa.Column("guidelines", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "question_set"),
    )

    # Analysis cache table
    op.create_table(
        "analysis_cache",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("chunk_overlap", sa.Integer(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("question_set", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), default=datetime.now),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "file_path",
            "question_id",
            "chunk_size",
            "chunk_overlap",
            "top_k",
            "model",
            "question_set",
        ),
    )

    # Question analysis table
    op.create_table(
        "question_analysis",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("analysis_result", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), default=1),
        sa.Column("created_at", sa.DateTime(), default=datetime.now),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_path", "question_id", "model", "top_k", "version"),
    )

    # Chunk relevance table
    op.create_table(
        "chunk_relevance",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("question_analysis_id", sa.Integer(), nullable=False),
        sa.Column("document_chunk_id", sa.Integer(), nullable=False),
        sa.Column("chunk_order", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("llm_score", sa.Float(), nullable=True),
        sa.Column("is_evidence", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("evidence_order", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["question_analysis_id"], ["question_analysis.id"]),
        sa.ForeignKeyConstraint(["document_chunk_id"], ["document_chunks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_analysis_id", "document_chunk_id"),
    )

    # Stored files table (for PostgreSQL file storage)
    op.create_table(
        "stored_files",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), default=datetime.now),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_file_path", "document_chunks", ["file_path"], unique=False)
    op.create_index(
        "idx_chunk_params",
        "document_chunks",
        ["chunk_size", "chunk_overlap"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("idx_chunk_params", table_name="document_chunks")
    op.drop_index("idx_file_path", table_name="document_chunks")
    op.drop_table("chunk_relevance")
    op.drop_table("question_analysis")
    op.drop_table("analysis_cache")
    op.drop_table("questions")
    op.drop_table("document_chunks")
    op.drop_table("stored_files")
