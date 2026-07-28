"""
Database utilities for enterprise module.
"""

from .pgvector_support import (
    check_pgvector_available,
    create_vector_type,
    get_vector_distance_func,
    setup_pgvector_extension,
)

__all__ = [
    "check_pgvector_available",
    "create_vector_type",
    "get_vector_distance_func",
    "setup_pgvector_extension",
]
