import hashlib
import logging
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared ID helpers (moved from scripts/align_benchmark_datasets.py)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Core transformation helpers (adapted from align_benchmark_datasets.py)
# ---------------------------------------------------------------------------


def transform_ground_truth(
    df: pd.DataFrame,
    document_col: str = "document",
    question_col: str = "question",
    context_col: str = "context",
    relevant_col: Optional[str] = None,
    page_col: Optional[str] = None,
    relevance_label_col: str = "relevance_label",
) -> pd.DataFrame:
    """
    Transform ground truth dataset to consistent format.

    This is a slightly refactored version of the original helper in
    scripts/align_benchmark_datasets.py, without any file I/O. It returns
    an aligned DataFrame ready for evaluation.
    """
    logger.info("Transforming ground truth dataset (%d rows)", len(df))

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
        or df_cols_lower.get("source relevance score")
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
            "Could not find relevance label column. Will default to score=1.0. "
            "Available: %s",
            list(df.columns),
        )

    # Use relevant column first (preferred), then context as fallback for chunk_id
    text_col = rel_col or ctx_col
    if text_col == rel_col:
        logger.info(
            "Using 'relevant' column for chunk_id generation "
            "(preferred for matching with benchmark relevant_text)"
        )
    elif text_col == ctx_col:
        logger.info(
            "Using 'context' column for chunk_id generation "
            "(fallback, 'relevant' column not found)"
        )

    # Generate query_id
    df = df.copy()
    df["query_id"] = df.apply(
        lambda row: generate_query_id(row[doc_col], row[q_col]), axis=1
    )

    # Generate chunk_id from relevant text (or context if relevant not available)
    df["chunk_id"] = df[text_col].apply(lambda x: generate_chunk_id(x))

    # Generate position (1-indexed, per query)
    df["position"] = df.groupby("query_id").cumcount() + 1

    # Map relevance label to score
    if label_col:

        def parse_label(val: Any) -> float:
            if pd.isna(val):
                return 1.0
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
                return 1.0

        df["score"] = df[label_col].apply(parse_label)
        logger.info(
            "Ground truth score distribution: %s",
            dict(df["score"].value_counts().sort_index()),
        )
    else:
        logger.warning("No relevance label column found, defaulting all scores to 1.0")
        df["score"] = 1.0

    # Select output columns and rename preserved ones
    output_cols = ["query_id", "chunk_id", "position", "score"]
    preserve_cols = [doc_col, q_col]
    if text_col:
        preserve_cols.append(text_col)
    if rel_col and rel_col != text_col and rel_col in df.columns:
        preserve_cols.append(rel_col)
    if ctx_col and ctx_col != text_col and ctx_col in df.columns:
        preserve_cols.append(ctx_col)
    if page_num_col:
        preserve_cols.append(page_num_col)
    if label_col and label_col in df.columns:
        preserve_cols.append(label_col)

    rename_map: Dict[str, str] = {
        doc_col: "document",
        q_col: "question",
    }
    if text_col == rel_col:
        rename_map[text_col] = "relevant"
    elif text_col == ctx_col:
        rename_map[text_col] = "context"
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
        "Transformed ground truth: %d rows, %d queries, %d chunks",
        len(df_output),
        df_output["query_id"].nunique(),
        df_output["chunk_id"].nunique(),
    )
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
) -> pd.DataFrame:
    """
    Transform benchmark results dataset to consistent format.

    This is a refactored version of the original helper in
    scripts/align_benchmark_datasets.py, without any file I/O. It returns
    an aligned DataFrame ready for evaluation.
    """
    logger.info("Transforming benchmark results dataset (%d rows)", len(df))

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

    df = df.copy()

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
        df["relevant_part_id"] = df["chunk_id"]
        logger.info("No relevant_text found, using chunk_id as relevant_part_id")

    # Generate position
    if num_col and num_col in df.columns:
        df["position"] = (
            pd.to_numeric(df[num_col], errors="coerce").fillna(0).astype(int)
        )
        df["position"] = df["position"].apply(lambda x: max(1, x))
        logger.info("Using number column for position")
    else:
        df["position"] = df.groupby("query_id").cumcount() + 1
        logger.info("Using row order for position")

    # Optional score column (label preferred, then numeric relevance score)
    if label_col_actual and label_col_actual in df.columns:

        def parse_label(val: Any) -> float:
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

        df["score"] = df[label_col_actual].apply(parse_label)
        logger.info("Using label column for score")
    elif rel_score_col and rel_score_col in df.columns:
        df["score"] = pd.to_numeric(df[rel_score_col], errors="coerce").fillna(0.0)
        logger.info("Using numeric relevance score column for score")
    else:
        logger.info(
            "No score column found - evaluation will rely on ground truth scores only"
        )

    # Detect similarity score columns from report level dataset
    relevant_text_sim_col = df_cols_lower.get("relevant_text_sim")
    sim_text_relevance_col = df_cols_lower.get("sim_text_relevance")

    output_cols = ["query_id", "chunk_id", "relevant_part_id", "position"]
    if "score" in df.columns:
        output_cols.append("score")

    preserve_cols = [report_col_actual, q_col, para_col]
    if rel_text_col and rel_text_col in df.columns:
        preserve_cols.append(rel_text_col)
    if label_col_actual and label_col_actual in df.columns:
        preserve_cols.append(label_col_actual)
    if relevant_text_sim_col and relevant_text_sim_col in df.columns:
        preserve_cols.append(relevant_text_sim_col)
    if sim_text_relevance_col and sim_text_relevance_col in df.columns:
        preserve_cols.append(sim_text_relevance_col)

    rename_map: Dict[str, str] = {
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
        "Transformed benchmark results: %d rows, %d queries, %d chunks",
        len(df_output),
        df_output["query_id"].nunique(),
        df_output["chunk_id"].nunique(),
    )
    return df_output


# ---------------------------------------------------------------------------
# Dataset mapper abstraction and factory
# ---------------------------------------------------------------------------


class DatasetMapper:
    """Base class for dataset mappers."""

    def __init__(self, dataset_id: str, config: Optional[Dict[str, Any]] = None):
        self.dataset_id = dataset_id
        self.config = config or {}

    def align_ground_truth(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def align_benchmark(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class DefaultDatasetMapper(DatasetMapper):
    """Default mapper that uses YAML column mappings and shared helpers."""

    def align_ground_truth(self, df: pd.DataFrame) -> pd.DataFrame:
        gt_cfg = (self.config.get("ground_truth") or {}).get("columns", {})

        return transform_ground_truth(
            df,
            document_col=gt_cfg.get("document", "document"),
            question_col=gt_cfg.get("question", "question"),
            context_col=gt_cfg.get("context", "context"),
            relevant_col=gt_cfg.get("relevant"),
            page_col=gt_cfg.get("page_number"),
            relevance_label_col=gt_cfg.get("relevance_label", "relevance_label"),
        )

    def align_benchmark(self, df: pd.DataFrame) -> pd.DataFrame:
        bm_cfg = (self.config.get("benchmark") or {}).get("columns", {})

        return transform_benchmark_results(
            df,
            report_col=bm_cfg.get("report_id", "report"),
            question_col=bm_cfg.get("question", "question"),
            paragraph_col=bm_cfg.get("paragraph", "paragraph"),
            relevant_text_col=bm_cfg.get("relevant_text", "relevant_text"),
            relevance_score_col=bm_cfg.get("relevance_score"),
            label_col=bm_cfg.get("relevance_label"),
            number_col=bm_cfg.get("number"),
        )


def _load_yaml_config(dataset_id: str) -> Dict[str, Any]:
    """Load YAML config for a dataset_id from package data."""
    # Expected location: report_analyst/config/datasets/{dataset_id}.yaml
    base_dir = Path(__file__).resolve().parents[2]  # .../report_analyst
    cfg_path = base_dir / "config" / "datasets" / f"{dataset_id}.yaml"

    if not cfg_path.exists():
        logger.warning(
            "No dataset mapping config found for '%s' at %s", dataset_id, cfg_path
        )
        return {"id": dataset_id}

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    if "id" not in cfg:
        cfg["id"] = dataset_id
    return cfg


class DatasetMapperFactory:
    """Factory to construct DatasetMapper instances from YAML configs."""

    @staticmethod
    def get_mapper(dataset_id: str) -> DatasetMapper:
        cfg = _load_yaml_config(dataset_id)
        mapper_class_path = cfg.get("mapper_class")

        if mapper_class_path:
            try:
                module_path, class_name = mapper_class_path.rsplit(".", 1)
                module = import_module(module_path)
                cls: Type[DatasetMapper] = getattr(module, class_name)
                return cls(dataset_id, cfg)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to import custom mapper '%s' for dataset '%s': %s",
                    mapper_class_path,
                    dataset_id,
                    exc,
                )

        # Fallback to default mapper
        return DefaultDatasetMapper(dataset_id, cfg)


def list_available_dataset_ids() -> List[str]:
    """Return dataset IDs for which a YAML mapping config is available."""
    base_dir = Path(__file__).resolve().parents[2] / "config" / "datasets"
    if not base_dir.exists():
        return []
    return sorted(p.stem for p in base_dir.glob("*.yaml"))


__all__ = [
    "generate_query_id",
    "generate_chunk_id",
    "transform_ground_truth",
    "transform_benchmark_results",
    "DatasetMapper",
    "DefaultDatasetMapper",
    "DatasetMapperFactory",
    "list_available_dataset_ids",
]
