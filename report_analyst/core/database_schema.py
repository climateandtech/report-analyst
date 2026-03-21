"""
Database Schema Definitions using SQLAlchemy

Defines all tables for the analysis cache system.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
)

# Create metadata object
metadata = MetaData()

# Document chunks table
document_chunks = Table(
    "document_chunks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_path", Text, nullable=False),
    Column("chunk_text", Text, nullable=False),
    Column("chunk_size", Integer, nullable=False),
    Column("chunk_overlap", Integer, nullable=False),
    Column("embedding", LargeBinary, nullable=True),  # BLOB/BYTEA
    Column("metadata", Text, nullable=True),  # JSON stored as text
    Column("created_at", DateTime, default=datetime.now),
    UniqueConstraint("file_path", "chunk_text", "chunk_size", "chunk_overlap"),
)

# Questions table
questions = Table(
    "questions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("question_id", Text, nullable=False),
    Column("question_set", Text, nullable=False),
    Column("question_text", Text, nullable=True),
    Column("guidelines", Text, nullable=True),
    UniqueConstraint("question_id", "question_set"),
)

# Analysis cache table
analysis_cache = Table(
    "analysis_cache",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_path", Text, nullable=False),
    Column("question_id", Text, nullable=False),
    Column("chunk_size", Integer, nullable=False),
    Column("chunk_overlap", Integer, nullable=False),
    Column("top_k", Integer, nullable=False),
    Column("model", Text, nullable=False),
    Column("question_set", Text, nullable=False),
    Column("result", Text, nullable=False),  # JSON stored as text
    Column("created_at", DateTime, default=datetime.now),
    UniqueConstraint(
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
question_analysis = Table(
    "question_analysis",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_path", Text, nullable=False),
    Column("question_id", Integer, ForeignKey("questions.id"), nullable=False),
    Column("model", Text, nullable=False),
    Column("top_k", Integer, nullable=False),
    Column("analysis_result", Text, nullable=False),  # JSON stored as text
    Column("version", Integer, default=1),
    Column("created_at", DateTime, default=datetime.now),
    UniqueConstraint("file_path", "question_id", "model", "top_k", "version"),
)

# Chunk relevance table
chunk_relevance = Table(
    "chunk_relevance",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "question_analysis_id",
        Integer,
        ForeignKey("question_analysis.id"),
        nullable=False,
    ),
    Column("document_chunk_id", Integer, ForeignKey("document_chunks.id"), nullable=False),
    Column("chunk_order", Integer, nullable=False),
    Column("similarity_score", Float, nullable=True),
    Column("llm_score", Float, nullable=True),
    Column("is_evidence", Boolean, nullable=False, default=False),
    Column("evidence_order", Integer, nullable=True),
    Column("metadata", Text, nullable=True),  # JSON stored as text
    UniqueConstraint("question_analysis_id", "document_chunk_id"),
)

# Indexes (defined separately for clarity)
# Note: SQLAlchemy doesn't support "IF NOT EXISTS" in CREATE INDEX directly,
# so we'll handle these in init_db() using raw SQL
indexes = [
    # Index on file_path for document_chunks
    "CREATE INDEX IF NOT EXISTS idx_file_path ON document_chunks(file_path)",
    # Index on chunk parameters
    "CREATE INDEX IF NOT EXISTS idx_chunk_params ON document_chunks(chunk_size, chunk_overlap)",
]
