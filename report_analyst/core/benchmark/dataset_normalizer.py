"""
Normalize a raw DataFrame to the benchmark schema (query_id, chunk_id, position, score, paragraph)
using user-selected column mappings. Used when CSV/Excel structure does not match the expected names.
"""

import hashlib
import logging
from typing import Any, Optional

import pandas as pd

from .dataset_mapper import generate_chunk_id, generate_query_id

logger = logging.getLogger(__name__)

# Position mode: use explicit column, infer from row order per query, or infer by sorting by score
POSITION_MODE_COLUMN = "column"
POSITION_MODE_ROW_ORDER = "row_order"
POSITION_MODE_SORT_BY_SCORE = "sort_by_score"


def _parse_score(val: Any) -> float:
    """Coerce a value to a numeric score (for label/prediction columns)."""
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip().lower()
    try:
        return float(val_str)
    except ValueError:
        if val_str in ["yes", "y", "true", "relevant", "high"]:
            return 2.0
        if val_str in ["maybe", "partial", "medium"]:
            return 1.0
        if val_str in ["no", "n", "false", "irrelevant", "low"]:
            return 0.0
        return 0.0


def _stable_query_id_from_text(text: str, max_len: int = 64) -> str:
    """Produce a stable query_id from a single text (e.g. description) when no document column."""
    if pd.isna(text) or not str(text).strip():
        return hashlib.md5(b"empty").hexdigest()[:16]
    s = str(text).strip()
    if len(s) <= max_len:
        return s
    return hashlib.md5(s.encode()).hexdigest()[:16]


def make_query_id_from_columns(
    document: Optional[Any], question: Any, max_len: int = 64
) -> str:
    """
    Helper to build a stable query_id from document/question-style fields.

    - If a document is provided, we delegate to generate_query_id(document, question)
      so that behaviour matches DatasetMapper / preset mappers.
    - If no document is provided, we fall back to a stable ID derived from the
      question/description text alone (using _stable_query_id_from_text).
    """
    if document is not None and str(document).strip():
        return generate_query_id(document, question)
    return _stable_query_id_from_text(question, max_len=max_len)


def make_chunk_id_from_text(text: Any) -> str:
    """
    Helper to build a chunk_id from raw text content.

    Uses generate_chunk_id under the hood and handles empty/NaN values by
    normalizing them to an empty string first.
    """
    return generate_chunk_id(str(text) if pd.notna(text) else "")


def make_relevant_part_id_from_text(text: Any) -> str:
    """
    Helper to build a relevant_part_id from a relevant span of text.

    This mirrors make_chunk_id_from_text so that relevant parts and full chunks
    share the same hashing logic. When no text is provided, we hash an empty
    string to get a deterministic ID.
    """
    return generate_chunk_id(str(text) if pd.notna(text) else "")


def normalize_dataframe_for_benchmark(
    df: pd.DataFrame,
    query_column: str,
    chunk_text_column: str,
    score_column: str,
    position_column: Optional[str] = None,
    document_column: Optional[str] = None,
    position_mode: str = POSITION_MODE_ROW_ORDER,
) -> pd.DataFrame:
    """
    Build a DataFrame with standard benchmark columns from raw data and column choices.

    Produces columns: query_id, chunk_id, position, score, paragraph, question,
    and optionally document. Used so that
    load_flexible_dataset_from_csv(csv_content=result.to_csv()) works without schema changes.

    Args:
        df: Raw DataFrame (e.g. from uploaded CSV/Excel).
        query_column: Column used as query/criteria (e.g. description, question).
        chunk_text_column: Column used as chunk text (e.g. chunk_text, paragraph).
        score_column: Column used as label or prediction score (e.g. relevance, usefulness, model column).
        position_column: Column for position/rank; used only when position_mode == "column".
        document_column: Optional document/report column; if set, query_id = generate_query_id(doc, query).
        position_mode: "column" | "row_order" | "sort_by_score".
            - column: use position_column (must be provided).
            - row_order: assign 1,2,3... by row order within each query_id.
            - sort_by_score: sort by score_column descending per query, then assign position.

    Returns:
        DataFrame with columns query_id, chunk_id, position, score, paragraph, question [, document].
    """
    if query_column not in df.columns:
        raise ValueError(
            f"Query column '{query_column}' not in DataFrame columns: {list(df.columns)}"
        )
    if chunk_text_column not in df.columns:
        raise ValueError(
            f"Chunk text column '{chunk_text_column}' not in DataFrame columns: {list(df.columns)}"
        )
    if score_column not in df.columns:
        raise ValueError(
            f"Score column '{score_column}' not in DataFrame columns: {list(df.columns)}"
        )
    if position_mode == POSITION_MODE_COLUMN and (
        not position_column or position_column not in df.columns
    ):
        raise ValueError(
            f"Position mode is 'column' but position column '{position_column}' missing or not in DataFrame"
        )
    if document_column is not None and document_column not in df.columns:
        raise ValueError(
            f"Document column '{document_column}' not in DataFrame columns: {list(df.columns)}"
        )

    out = df.copy()

    # query_id
    if document_column:
        out["query_id"] = out.apply(
            lambda row: generate_query_id(
                row.get(document_column) if pd.notna(row.get(document_column)) else "",
                row.get(query_column) if pd.notna(row.get(query_column)) else "",
            ),
            axis=1,
        )
    else:
        out["query_id"] = out[query_column].apply(
            lambda x: (
                _stable_query_id_from_text(x)
                if pd.notna(x)
                else _stable_query_id_from_text("")
            )
        )

    # chunk_id from chunk text
    out["chunk_id"] = out[chunk_text_column].apply(
        lambda x: generate_chunk_id(str(x) if pd.notna(x) else "")
    )

    # score (coerce to float)
    out["score"] = out[score_column].apply(_parse_score)

    # paragraph for matching/display
    out["paragraph"] = (
        out[chunk_text_column].where(out[chunk_text_column].notna(), "").astype(str)
    )

    # question text for error analysis / display (copy from query/criteria column)
    out["question"] = out[query_column].where(out[query_column].notna(), "").astype(str)

    # position
    if position_mode == POSITION_MODE_COLUMN and position_column:
        out["position"] = out[position_column].apply(
            lambda x: int(x) if pd.notna(x) and str(x).strip() else 1
        )
        out["position"] = out["position"].clip(lower=1)
    elif position_mode == POSITION_MODE_SORT_BY_SCORE:
        out = out.sort_values(["query_id", "score"], ascending=[True, False])
        out["position"] = out.groupby("query_id").cumcount() + 1
    else:
        # row_order: preserve order, assign position per query
        out["position"] = out.groupby("query_id").cumcount() + 1

    # optional document
    if document_column:
        out["document"] = out[document_column]

    # Keep only standard columns so loader sees a clean schema
    standard_cols = [
        "query_id",
        "chunk_id",
        "position",
        "score",
        "paragraph",
        "question",
    ]
    if document_column:
        standard_cols.append("document")
    out = out[standard_cols].copy()

    logger.info(
        "Normalized dataset: %d rows, %d unique queries, %d unique chunks",
        len(out),
        out["query_id"].nunique(),
        out["chunk_id"].nunique(),
    )
    return out
