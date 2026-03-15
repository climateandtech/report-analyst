from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from .dataset_mapper import generate_chunk_id, generate_query_id
from .dataset_normalizer import (
    make_chunk_id_from_text,
    make_query_id_from_columns,
    make_relevant_part_id_from_text,
)


logger = logging.getLogger(__name__)


@dataclass
class GroundTruthAlignConfig:
    document_col: Optional[str]
    question_col: str
    chunk_text_col: str
    relevant_part_col: Optional[str]
    label_cols: List[str]


@dataclass
class BenchmarkAlignConfig:
    document_col: Optional[str]
    question_col: Optional[str]
    query_id_col: Optional[str]
    chunk_text_col: str
    relevant_part_col: Optional[str]
    prediction_cols: List[str]
    ranking_score_col: Optional[str]


def align_ground_truth_flexible(
    df: pd.DataFrame, config: GroundTruthAlignConfig
) -> pd.DataFrame:
    """
    Align a raw ground truth DataFrame to the unified flexible schema.

    Output columns:
        - query_id
        - chunk_id
        - relevant_part_id (optional)
        - question
        - document (optional)
        - chunk_text
        - relevant_part_text (optional)
        - plus all label columns from config.label_cols
        - score (numeric) for ranking, derived from the first label column when present
    """
    if config.question_col not in df.columns:
        raise ValueError(
            f"Question/description column '{config.question_col}' not in DataFrame."
        )
    if config.chunk_text_col not in df.columns:
        raise ValueError(
            f"Chunk text column '{config.chunk_text_col}' not in DataFrame."
        )

    for col in config.label_cols:
        if col not in df.columns:
            raise ValueError(f"Label column '{col}' not in DataFrame.")

    if config.document_col and config.document_col not in df.columns:
        raise ValueError(f"Document column '{config.document_col}' not in DataFrame.")
    if config.relevant_part_col and config.relevant_part_col not in df.columns:
        raise ValueError(
            f"Relevant part column '{config.relevant_part_col}' not in DataFrame."
        )

    out = df.copy()

    # Core ID fields
    def _mk_qid(row):
        doc_val = (
            row[config.document_col] if config.document_col else None  # type: ignore[index]
        )
        return make_query_id_from_columns(doc_val, row[config.question_col])

    out["query_id"] = out.apply(_mk_qid, axis=1)
    out["chunk_id"] = out[config.chunk_text_col].apply(make_chunk_id_from_text)

    if config.relevant_part_col:
        out["relevant_part_text"] = out[config.relevant_part_col]
        out["relevant_part_id"] = out[config.relevant_part_col].apply(
            make_relevant_part_id_from_text
        )
    else:
        out["relevant_part_text"] = ""
        # Fallback: use chunk_id when no explicit relevant part is provided
        out["relevant_part_id"] = out["chunk_id"]

    # Human-readable text fields
    out["question"] = out[config.question_col].astype(str)
    if config.document_col:
        out["document"] = out[config.document_col].astype(str)
    else:
        out["document"] = ""
    out["chunk_text"] = out[config.chunk_text_col].astype(str)

    # Preserve label columns as-is
    for col in config.label_cols:
        out[col] = out[col]

    # Provide a numeric "score" column for ranking based on the first label column, if any
    if config.label_cols:
        primary_label = config.label_cols[0]

        def _parse_score(val: Any) -> float:
            try:
                return float(str(val).strip())
            except Exception:
                return 0.0

        out["score"] = out[primary_label].apply(_parse_score)

    # Select and order columns
    base_cols: List[str] = [
        "query_id",
        "chunk_id",
        "relevant_part_id",
        "question",
        "document",
        "chunk_text",
        "relevant_part_text",
    ]
    label_cols = [c for c in config.label_cols if c in out.columns]
    extra_cols = [c for c in ["score"] if c in out.columns]
    ordered_cols = base_cols + label_cols + extra_cols

    out_aligned = out[ordered_cols].copy()

    logger.info(
        "Aligned ground truth (flexible): %d rows, %d unique queries, %d unique chunks",
        len(out_aligned),
        out_aligned["query_id"].nunique(),
        out_aligned["chunk_id"].nunique(),
    )
    return out_aligned


def align_benchmark_flexible(
    df: pd.DataFrame, config: BenchmarkAlignConfig
) -> pd.DataFrame:
    """
    Align a raw benchmark results DataFrame to the unified flexible schema.

    Output columns:
        - query_id
        - chunk_id
        - relevant_part_id (optional)
        - chunk_text
        - relevant_part_text_pred (optional)
        - plus all prediction columns from config.prediction_cols
        - relevant_text_sim (optional) duplicated from ranking_score_col for reuse by ranking logic
    """
    if config.query_id_col:
        if config.query_id_col not in df.columns:
            raise ValueError(
                f"query_id column '{config.query_id_col}' not in DataFrame."
            )
    else:
        # If no explicit query_id column, require at least a question/description column
        if not config.question_col or config.question_col not in df.columns:
            raise ValueError(
                "Either an explicit query_id_col or a question/description column must be provided."
            )

    if config.chunk_text_col not in df.columns:
        raise ValueError(
            f"Chunk text column '{config.chunk_text_col}' not in DataFrame."
        )

    for col in config.prediction_cols:
        if col not in df.columns:
            raise ValueError(f"Prediction column '{col}' not in DataFrame.")

    if config.document_col and config.document_col not in df.columns:
        raise ValueError(f"Document column '{config.document_col}' not in DataFrame.")
    if config.relevant_part_col and config.relevant_part_col not in df.columns:
        raise ValueError(
            f"Relevant part column '{config.relevant_part_col}' not in DataFrame."
        )
    if config.ranking_score_col and config.ranking_score_col not in df.columns:
        raise ValueError(
            f"Ranking score column '{config.ranking_score_col}' not in DataFrame."
        )

    out = df.copy()

    # query_id: either reuse existing column or recompute from document/question
    if config.query_id_col:
        out["query_id"] = out[config.query_id_col].astype(str)
    else:

        def _mk_qid(row):
            doc_val = (
                row[config.document_col] if config.document_col else None  # type: ignore[index]
            )
            return make_query_id_from_columns(doc_val, row[config.question_col])  # type: ignore[index]

        out["query_id"] = out.apply(_mk_qid, axis=1)

    # chunk_id from chunk text
    out["chunk_id"] = out[config.chunk_text_col].apply(make_chunk_id_from_text)
    out["chunk_text"] = out[config.chunk_text_col].astype(str)

    # Optional predicted relevant part
    if config.relevant_part_col:
        out["relevant_part_text_pred"] = out[config.relevant_part_col].astype(str)
        out["relevant_part_id"] = out[config.relevant_part_col].apply(
            make_relevant_part_id_from_text
        )
    else:
        out["relevant_part_text_pred"] = ""
        out["relevant_part_id"] = out["chunk_id"]

    # Predictions / scores
    for col in config.prediction_cols:
        out[col] = out[col]

    # Optional ranking score column: duplicate into relevant_text_sim for reuse by ranking logic
    if config.ranking_score_col:
        out["relevant_text_sim"] = out[config.ranking_score_col]

    base_cols: List[str] = [
        "query_id",
        "chunk_id",
        "relevant_part_id",
        "chunk_text",
        "relevant_part_text_pred",
    ]
    pred_cols = [c for c in config.prediction_cols if c in out.columns]
    extra_cols: List[str] = []
    if "relevant_text_sim" in out.columns:
        extra_cols.append("relevant_text_sim")

    # Build final column order and remove duplicates while preserving order.
    # This is important when the chosen ranking_score_col is also one of the
    # prediction columns (e.g. 'relevant_text_sim'), to avoid duplicated
    # column names in the aligned DataFrame.
    ordered_cols_raw = base_cols + pred_cols + extra_cols
    seen_cols: set[str] = set()
    ordered_cols: List[str] = []
    for col in ordered_cols_raw:
        if col not in seen_cols:
            seen_cols.add(col)
            ordered_cols.append(col)

    out_aligned = out[ordered_cols].copy()

    logger.info(
        "Aligned benchmark (flexible): %d rows, %d unique queries, %d unique chunks",
        len(out_aligned),
        out_aligned["query_id"].nunique(),
        out_aligned["chunk_id"].nunique(),
    )
    return out_aligned


__all__ = [
    "GroundTruthAlignConfig",
    "BenchmarkAlignConfig",
    "align_ground_truth_flexible",
    "align_benchmark_flexible",
]
