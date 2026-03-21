"""
pgvector Support for PostgreSQL

Provides vector type and similarity search functions for PostgreSQL with pgvector extension.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def check_pgvector_available(connection) -> bool:
    """
    Check if pgvector extension is available in the database.

    Args:
        connection: SQLAlchemy connection object

    Returns:
        True if pgvector is available, False otherwise
    """
    try:
        from sqlalchemy import text

        result = connection.execute(
            text(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                )
                """
            )
        )
        available = result.fetchone()[0]
        if available:
            logger.info("pgvector extension is available")
        else:
            logger.info("pgvector extension is not available")
        return available
    except Exception as e:
        logger.warning(f"Error checking pgvector availability: {e}")
        return False


def setup_pgvector_extension(connection) -> bool:
    """
    Attempt to create pgvector extension (requires superuser privileges).

    Args:
        connection: SQLAlchemy connection object

    Returns:
        True if extension was created or already exists, False otherwise
    """
    try:
        from sqlalchemy import text

        # Check if already exists
        if check_pgvector_available(connection):
            return True

        # Try to create extension
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()
        logger.info("pgvector extension created successfully")
        return True
    except Exception as e:
        logger.warning(f"Could not create pgvector extension (may require superuser): {e}")
        return False


def create_vector_type(dimension: Optional[int] = None):
    """
    Create a SQLAlchemy type for pgvector.

    Args:
        dimension: Optional dimension for the vector type

    Returns:
        SQLAlchemy TypeEngine for vector type
    """
    from sqlalchemy import Text, TypeDecorator

    class VectorType(TypeDecorator):
        """Custom type for pgvector vector column"""

        impl = Text
        cache_ok = True

        def load_dialect_impl(self, dialect):
            if dialect.name == "postgresql":
                # Use raw SQL to create vector type
                return dialect.type_descriptor(Text())
            return dialect.type_descriptor(Text())

        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            # Convert numpy array or list to string format for pgvector
            if hasattr(value, "tolist"):
                value = value.tolist()
            # pgvector expects format: [1,2,3]
            return str(value).replace(" ", "")

        def process_result_value(self, value, dialect):
            if value is None:
                return None
            # Parse string format back to list
            import ast

            return ast.literal_eval(value)

    return VectorType()


def get_vector_distance_func(embedding_column_name: str, query_vector, distance_type: str = "cosine"):
    """
    Get SQL expression for vector distance calculation.

    Args:
        embedding_column_name: Name of the embedding column
        query_vector: Query vector (numpy array or list)
        distance_type: Type of distance ('cosine', 'l2', 'inner_product')

    Returns:
        Tuple of (SQL expression string, parameters dict) for use in ORDER BY clause
    """
    # Convert query vector to string format for pgvector
    if hasattr(query_vector, "tolist"):
        query_vector = query_vector.tolist()
    query_str = str(query_vector).replace(" ", "")

    # Map distance type to pgvector operator
    operators = {
        "cosine": "<=>",  # Cosine distance
        "l2": "<->",  # L2 distance
        "inner_product": "<#>",  # Inner product (negative)
    }

    if distance_type not in operators:
        logger.warning(f"Unknown distance type {distance_type}, using cosine")
        distance_type = "cosine"

    operator = operators[distance_type]

    # Return SQL expression for ORDER BY
    # Format: embedding <=> '[1,2,3]'::vector
    sql_expr = f"{embedding_column_name} {operator} :query_vector::vector"
    return sql_expr, {"query_vector": query_str}
