#!/usr/bin/env python3
"""
Script to align ground truth and benchmark datasets for consistent evaluation.

Ensures consistency via:
- query_id: Generated from (document, question) pair
- chunk_id: Generated from context/relevant_text using hash (for matching)
- score: Relevance label (2, 1, 0) from ground truth

Handles ClimRetrieve-style datasets:
- Ground truth: document, question, context, relevant, page number, relevance label
- Benchmark results: paragraph, report, question, relevant_text, relevance_score, label
"""

import argparse
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def generate_query_id(document: str, question: str, separator: str = "|||") -> str:
    """
    Generate a consistent query_id from document and question.

    Args:
        document: Document/report name
        question: Question text
        separator: Separator between document and question

    Returns:
        query_id string
    """
    # Normalize: strip whitespace, handle None/NaN
    doc = str(document).strip() if pd.notna(document) else ""
    q = str(question).strip() if pd.notna(question) else ""
    return f"{doc}{separator}{q}"


def generate_chunk_id(text: str, prefix: str = "") -> str:
    """
    Generate a consistent chunk_id from text content using MD5 hash.

    Args:
        text: Text content to hash
        prefix: Optional prefix for chunk_id

    Returns:
        chunk_id string (16-character hex hash)
    """
    if pd.isna(text) or not str(text).strip():
        # Generate a hash from the string representation for empty/NaN
        text_str = str(text) if pd.notna(text) else "empty"
        hash_val = hashlib.md5(text_str.encode()).hexdigest()[:16]
        return f"{prefix}{hash_val}" if prefix else hash_val

    # Normalize text: strip whitespace, lowercase for consistency
    normalized = str(text).strip()
    hash_val = hashlib.md5(normalized.encode()).hexdigest()[:16]
    return f"{prefix}{hash_val}" if prefix else hash_val


def transform_ground_truth(
    df: pd.DataFrame,
    document_col: str = "document",
    question_col: str = "question",
    context_col: str = "context",
    relevant_col: Optional[str] = None,
    page_col: Optional[str] = None,
    relevance_label_col: str = "relevance_label",
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Transform ground truth dataset to consistent format.

    Expected columns:
    - document: Report/document name
    - question: Question text
    - context: Context text (1 sentence before + 1 after relevant part)
    - relevant: Most relevant chunks (optional, alternative to context)
    - page_number: Page number (optional)
    - relevance_label: Relevance label (2, 1, 0)

    Output columns:
    - query_id: Generated from (document, question)
    - chunk_id: Generated from relevant text hash (preferred) or context text hash (fallback)
    - position: Position/rank (1-indexed, per query)
    - score: Relevance label converted to numeric (2, 1, 0)
    - relevance_label: Original relevance label column (preserved)
    - context: Original context text (preserved, if used for chunk_id)
    - relevant: Original relevant text (preserved, if used for chunk_id)
    - document: Original document name (preserved)
    - question: Original question text (preserved)

    Args:
        df: Input DataFrame
        document_col: Column name for document/report
        question_col: Column name for question
        context_col: Column name for context text
        relevant_col: Column name for relevant text (alternative to context)
        page_col: Column name for page number (optional)
        relevance_label_col: Column name for relevance label
        output_path: Optional path to save transformed CSV

    Returns:
        Transformed DataFrame
    """
    logger.info(f"Transforming ground truth dataset ({len(df)} rows)")

    # Detect column names (case-insensitive)
    df_cols_lower = {col.lower(): col for col in df.columns}

    # Map expected columns
    doc_col = df_cols_lower.get(document_col.lower()) or df_cols_lower.get("document")
    q_col = df_cols_lower.get(question_col.lower()) or df_cols_lower.get("question")
    ctx_col = (
        df_cols_lower.get(context_col.lower())
        or df_cols_lower.get("context")
        or df_cols_lower.get("relevant")
    )
    rel_col = (
        df_cols_lower.get(relevant_col.lower()) if relevant_col else None
    ) or df_cols_lower.get("relevant")
    page_num_col = (
        (df_cols_lower.get(page_col.lower()) if page_col else None)
        or df_cols_lower.get("page_number")
        or df_cols_lower.get("page")
    )
    label_col = (
        df_cols_lower.get(relevance_label_col.lower())
        or df_cols_lower.get("relevance_label")
        or df_cols_lower.get("source relevance score")  # Check for "Source Relevance Score"
        or df_cols_lower.get("relevance")
        or df_cols_lower.get("label")
    )

    # Validate required columns
    if not doc_col:
        raise ValueError(
            f"Could not find document column. Available: {list(df.columns)}"
        )
    if not q_col:
        raise ValueError(
            f"Could not find question column. Available: {list(df.columns)}"
        )
    if not ctx_col and not rel_col:
        raise ValueError(
            f"Could not find context or relevant column. Available: {list(df.columns)}"
        )
    if not label_col:
        logger.warning(
            f"Could not find relevance label column. Will default to score=1.0. Available: {list(df.columns)}"
        )

    # Use relevant column first (preferred), then context as fallback for chunk_id
    # This ensures chunk_id matches the actual relevant part text, not the context with surrounding sentences
    text_col = rel_col or ctx_col
    if text_col == rel_col:
        logger.info("Using 'relevant' column for chunk_id generation (preferred for matching with benchmark relevant_text)")
    elif text_col == ctx_col:
        logger.info("Using 'context' column for chunk_id generation (fallback, 'relevant' column not found)")

    # Generate query_id
    df["query_id"] = df.apply(
        lambda row: generate_query_id(row[doc_col], row[q_col]), axis=1
    )

    # Generate chunk_id from relevant text (or context if relevant not available)
    # This should match the relevant_text used in benchmark dataset for relevant_part_id
    df["chunk_id"] = df[text_col].apply(lambda x: generate_chunk_id(x))

    # Generate position (1-indexed, per query)
    df["position"] = df.groupby("query_id").cumcount() + 1

    # Map relevance label to score
    if label_col:
        logger.info(f"Using column '{label_col}' for score generation")
        # Convert label to numeric, handling various formats
        def parse_label(val):
            if pd.isna(val):
                return 1.0  # Default to 1.0 if missing
            val_str = str(val).strip().lower()
            # Try to parse as number
            try:
                num_val = float(val_str)
                return num_val
            except ValueError:
                # Handle text labels
                if val_str in ["yes", "y", "true", "relevant", "high"]:
                    return 2.0
                elif val_str in ["maybe", "partial", "medium"]:
                    return 1.0
                elif val_str in ["no", "n", "false", "irrelevant", "low"]:
                    return 0.0
                else:
                    return 1.0  # Default

        df["score"] = df[label_col].apply(parse_label)
        # Log score distribution for verification
        score_counts = df["score"].value_counts().sort_index()
        logger.info(f"Score distribution: {dict(score_counts)}")
        logger.info(f"Score range: {df['score'].min()} to {df['score'].max()}")
    else:
        logger.warning("No relevance label column found, defaulting all scores to 1.0")
        df["score"] = 1.0  # Default score

    # Select output columns
    output_cols = ["query_id", "chunk_id", "position", "score"]
    # Preserve original columns for reference
    preserve_cols = [doc_col, q_col]
    # Preserve the text column used for chunk_id (relevant or context)
    if text_col:
        preserve_cols.append(text_col)
    # Also preserve the other text column if it exists (for reference)
    if rel_col and rel_col != text_col and rel_col in df.columns:
        preserve_cols.append(rel_col)
    if ctx_col and ctx_col != text_col and ctx_col in df.columns:
        preserve_cols.append(ctx_col)
    if page_num_col:
        preserve_cols.append(page_num_col)
    # Preserve relevance_label column if it exists (user requested this)
    if label_col and label_col in df.columns:
        preserve_cols.append(label_col)
    # Rename preserved columns to standard names
    rename_map = {
        doc_col: "document",
        q_col: "question",
    }
    # Rename the text column used for chunk_id
    if text_col == rel_col:
        rename_map[text_col] = "relevant"
    elif text_col == ctx_col:
        rename_map[text_col] = "context"
    # Rename the other text column if preserved
    if rel_col and rel_col != text_col and rel_col in preserve_cols:
        rename_map[rel_col] = "relevant"
    if ctx_col and ctx_col != text_col and ctx_col in preserve_cols:
        rename_map[ctx_col] = "context"
    if page_num_col:
        rename_map[page_num_col] = "page_number"
    if label_col and label_col in df.columns:
        rename_map[label_col] = "relevance_label"

    df_output = df[output_cols + preserve_cols].copy()
    df_output = df_output.rename(columns=rename_map)

    logger.info(
        f"Transformed ground truth: {len(df_output)} rows, "
        f"{df_output['query_id'].nunique()} unique queries, "
        f"{df_output['chunk_id'].nunique()} unique chunks"
    )

    if output_path:
        df_output.to_csv(output_path, index=False)
        logger.info(f"Saved transformed ground truth to: {output_path}")

    return df_output


def transform_benchmark_results(
    df: pd.DataFrame,
    report_col: str = "report",
    question_col: str = "question",
    paragraph_col: str = "paragraph",
    relevant_text_col: str = "relevant_text",
    relevance_score_col: Optional[str] = None,
    label_col: Optional[str] = None,
    number_col: Optional[str] = None,
    ground_truth_df: Optional[pd.DataFrame] = None,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Transform benchmark results dataset to consistent format.

    Expected columns:
    - report: Report/document name
    - question: Question text
    - paragraph: Retrieved chunk text
    - relevant_text: Best matching relevant part from ground truth (for chunk_id matching)
    - relevance_score: Similarity score between paragraph and relevant_text (optional)
    - label: Relevance label (2, 1, 0) (optional)
    - number: Paragraph number/index (optional)

    Output columns:
    - query_id: Generated from (report, question)
    - chunk_id: Generated from relevant_text (if available) or paragraph text
    - position: Position/rank (1-indexed, per query) or from number column
    - score: Optional relevance score (from relevance_score or label)
    - relevance_label: Original relevance label column (preserved if exists)
    - paragraph: Original paragraph text (preserved)
    - report: Original report name (preserved)
    - question: Original question text (preserved)
    - relevant_text: Original relevant_text (preserved)

    Args:
        df: Input DataFrame
        report_col: Column name for report/document
        question_col: Column name for question
        paragraph_col: Column name for paragraph/chunk text
        relevant_text_col: Column name for relevant text (for matching with ground truth)
        relevance_score_col: Column name for relevance score (optional)
        label_col: Column name for relevance label (optional)
        number_col: Column name for paragraph number (optional)
        ground_truth_df: Optional ground truth DataFrame for chunk_id matching
        output_path: Optional path to save transformed CSV

    Returns:
        Transformed DataFrame
    """
    logger.info(f"Transforming benchmark results dataset ({len(df)} rows)")

    # Detect column names (case-insensitive)
    df_cols_lower = {col.lower(): col for col in df.columns}

    # Map expected columns
    report_col_actual = (
        df_cols_lower.get(report_col.lower())
        or df_cols_lower.get("report")
        or df_cols_lower.get("document")
    )
    q_col = df_cols_lower.get(question_col.lower()) or df_cols_lower.get("question")
    para_col = (
        df_cols_lower.get(paragraph_col.lower())
        or df_cols_lower.get("paragraph")
        or df_cols_lower.get("chunk")
    )
    rel_text_col = (
        df_cols_lower.get(relevant_text_col.lower())
        or df_cols_lower.get("relevant_text")
        or df_cols_lower.get("relevant")
    )
    rel_score_col = (
        (
            df_cols_lower.get(relevance_score_col.lower())
            if relevance_score_col
            else None
        )
        or df_cols_lower.get("relevance_score")
        or df_cols_lower.get("sim_text_relevance")
    )
    label_col_actual = (
        (df_cols_lower.get(label_col.lower()) if label_col else None)
        or df_cols_lower.get("label")
        or df_cols_lower.get("relevance")
    )
    num_col = (
        (df_cols_lower.get(number_col.lower()) if number_col else None)
        or df_cols_lower.get("number")
        or df_cols_lower.get("paragraph_number")
    )

    # Validate required columns
    if not report_col_actual:
        raise ValueError(f"Could not find report column. Available: {list(df.columns)}")
    if not q_col:
        raise ValueError(
            f"Could not find question column. Available: {list(df.columns)}"
        )
    if not para_col:
        raise ValueError(
            f"Could not find paragraph column. Available: {list(df.columns)}"
        )

    # Generate query_id
    df["query_id"] = df.apply(
        lambda row: generate_query_id(row[report_col_actual], row[q_col]), axis=1
    )

    # Generate chunk_id from paragraph (unique identifier for each retrieved paragraph)
    df["chunk_id"] = df[para_col].apply(lambda x: generate_chunk_id(x))
    logger.info(
        "Using paragraph for chunk_id generation (unique per retrieved paragraph)"
    )

    # Generate relevant_part_id from relevant_text (for matching to ground truth relevant parts)
    if rel_text_col and rel_text_col in df.columns:
        df["relevant_part_id"] = df[rel_text_col].apply(lambda x: generate_chunk_id(x))
        logger.info(
            "Using relevant_text for relevant_part_id generation (for ground truth matching)"
        )
    else:
        # If no relevant_text, use paragraph as fallback (paragraph itself is the relevant part)
        df["relevant_part_id"] = df["chunk_id"]
        logger.info("No relevant_text found, using chunk_id as relevant_part_id")

    # Generate position
    if num_col and num_col in df.columns:
        # Use number column if available
        df["position"] = (
            pd.to_numeric(df[num_col], errors="coerce").fillna(0).astype(int)
        )
        # Ensure 1-indexed
        df["position"] = df["position"].apply(lambda x: max(1, x))
        logger.info("Using number column for position")
    else:
        # Generate position from row order per query
        df["position"] = df.groupby("query_id").cumcount() + 1
        logger.info("Using row order for position")

    # Optional: Add score column.
    # Preference order:
    #   1) Explicit label column (e.g. 'relevance' with values 0/1/2)
    #   2) Numeric relevance/similarity score (e.g. 'sim_text_relevance')
    if label_col_actual and label_col_actual in df.columns:
        # Parse label similar to ground truth. This lets numeric labels (0,1,2)
        # pass through unchanged, while still supporting textual labels.
        def parse_label(val):
            if pd.isna(val):
                return 0.0
            val_str = str(val).strip().lower()
            try:
                return float(val_str)
            except ValueError:
                if val_str in ["yes", "y", "true", "relevant", "high"]:
                    return 2.0
                elif val_str in ["maybe", "partial", "medium"]:
                    return 1.0
                elif val_str in ["no", "n", "false", "irrelevant", "low"]:
                    return 0.0
                else:
                    return 0.0

        df["score"] = df[label_col_actual].apply(parse_label)
        logger.info("Using label column for score")
    elif rel_score_col and rel_score_col in df.columns:
        df["score"] = pd.to_numeric(df[rel_score_col], errors="coerce").fillna(0.0)
        logger.info("Using numeric relevance score column for score")
    else:
        # No score column - evaluation will use ground truth scores only
        logger.info(
            "No score column found - evaluation will use ground truth scores only"
        )

    # Detect similarity score columns from report level dataset
    relevant_text_sim_col = df_cols_lower.get("relevant_text_sim")
    sim_text_relevance_col = df_cols_lower.get("sim_text_relevance")

    # Select output columns
    output_cols = ["query_id", "chunk_id", "relevant_part_id", "position"]
    if "score" in df.columns:
        output_cols.append("score")

    # Preserve original columns
    preserve_cols = [report_col_actual, q_col, para_col]
    if rel_text_col and rel_text_col in df.columns:
        preserve_cols.append(rel_text_col)
    # Preserve relevance_label column if it exists (for consistency with ground truth)
    if label_col_actual and label_col_actual in df.columns:
        preserve_cols.append(label_col_actual)
    # Add similarity score columns if they exist
    if relevant_text_sim_col and relevant_text_sim_col in df.columns:
        preserve_cols.append(relevant_text_sim_col)
    if sim_text_relevance_col and sim_text_relevance_col in df.columns:
        preserve_cols.append(sim_text_relevance_col)

    # Rename preserved columns
    rename_map = {
        report_col_actual: "report",
        q_col: "question",
        para_col: "paragraph",
    }
    if rel_text_col and rel_text_col in df.columns:
        rename_map[rel_text_col] = "relevant_text"
    if label_col_actual and label_col_actual in df.columns:
        rename_map[label_col_actual] = "relevance_label"
    if relevant_text_sim_col and relevant_text_sim_col in df.columns:
        rename_map[relevant_text_sim_col] = "relevant_text_sim"
    if sim_text_relevance_col and sim_text_relevance_col in df.columns:
        rename_map[sim_text_relevance_col] = "sim_text_relevance"

    df_output = df[output_cols + preserve_cols].copy()
    df_output = df_output.rename(columns=rename_map)

    logger.info(
        f"Transformed benchmark results: {len(df_output)} rows, "
        f"{df_output['query_id'].nunique()} unique queries, "
        f"{df_output['chunk_id'].nunique()} unique chunks"
    )

    if output_path:
        df_output.to_csv(output_path, index=False)
        logger.info(f"Saved transformed benchmark results to: {output_path}")

    return df_output


def main():
    parser = argparse.ArgumentParser(
        description="Align ground truth and benchmark datasets for consistent evaluation"
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        required=True,
        help="Path to ground truth dataset (CSV or Excel)",
    )
    parser.add_argument(
        "--benchmark-results",
        type=str,
        required=True,
        help="Path to benchmark results dataset (CSV)",
    )
    parser.add_argument(
        "--output-ground-truth",
        type=str,
        help="Output path for transformed ground truth CSV (default: <input>_aligned.csv)",
    )
    parser.add_argument(
        "--output-benchmark",
        type=str,
        help="Output path for transformed benchmark CSV (default: <input>_aligned.csv)",
    )
    parser.add_argument(
        "--document-col",
        type=str,
        default="document",
        help="Column name for document in ground truth (default: document)",
    )
    parser.add_argument(
        "--question-col",
        type=str,
        default="question",
        help="Column name for question in both datasets (default: question)",
    )
    parser.add_argument(
        "--context-col",
        type=str,
        default="context",
        help="Column name for context in ground truth (default: context)",
    )
    parser.add_argument(
        "--relevance-label-col",
        type=str,
        default="relevance_label",
        help="Column name for relevance label in ground truth (default: relevance_label)",
    )

    args = parser.parse_args()

    # Load ground truth
    gt_path = Path(args.ground_truth)
    logger.info(f"Loading ground truth from: {gt_path}")
    if gt_path.suffix in [".xlsx", ".xls"]:
        df_gt = pd.read_excel(gt_path)
    else:
        df_gt = pd.read_csv(gt_path)

    # Transform ground truth
    output_gt_path = args.output_ground_truth or str(gt_path).replace(
        ".csv", "_aligned.csv"
    ).replace(".xlsx", "_aligned.csv").replace(".xls", "_aligned.csv")
    df_gt_transformed = transform_ground_truth(
        df_gt,
        document_col=args.document_col,
        question_col=args.question_col,
        context_col=args.context_col,
        relevance_label_col=args.relevance_label_col,
        output_path=output_gt_path,
    )

    # Load benchmark results
    benchmark_path = Path(args.benchmark_results)
    logger.info(f"Loading benchmark results from: {benchmark_path}")
    df_benchmark = pd.read_csv(benchmark_path)

    # Transform benchmark results
    output_benchmark_path = args.output_benchmark or str(benchmark_path).replace(
        ".csv", "_aligned.csv"
    )
    df_benchmark_transformed = transform_benchmark_results(
        df_benchmark,
        report_col="report",
        question_col=args.question_col,
        paragraph_col="paragraph",
        relevant_text_col="relevant_text",
        ground_truth_df=df_gt_transformed,
        output_path=output_benchmark_path,
    )

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Alignment Summary")
    logger.info("=" * 60)
    logger.info(f"Ground truth queries: {df_gt_transformed['query_id'].nunique()}")
    logger.info(f"Benchmark queries: {df_benchmark_transformed['query_id'].nunique()}")
    common_queries = set(df_gt_transformed["query_id"]).intersection(
        set(df_benchmark_transformed["query_id"])
    )
    logger.info(f"Common queries: {len(common_queries)}")
    logger.info(f"\nTransformed files:")
    logger.info(f"  Ground truth: {output_gt_path}")
    logger.info(f"  Benchmark: {output_benchmark_path}")
    logger.info(
        "\nThese files are ready for evaluation using evaluate_benchmark_from_csv.py"
    )


if __name__ == "__main__":
    main()
