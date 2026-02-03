# app/core/benchmark/unified_metrics.py

"""
Unified evaluation metrics for both ClimRetrieve and S4M datasets.

This module provides flexible evaluation that automatically detects dataset format
and applies appropriate evaluation logic.

Key Differences:
- ClimRetrieve: Retrieval-based evaluation (scores can be from embeddings, string matching, or other methods)
  - Input: Separate labels (GT) and results (model outputs with retrieval scores)
  - Scores: Can be from embedding similarity, string matching (BM25/IR), or any retrieval method
  - Matching: Exact string matching on (report, question, paragraph) to match results to labels
  - Evaluation: Groups by (report, question) and macro-averages across queries
  
- S4M: Direct classification/labeling without retrieval
  - Input: Single DataFrame with ground truth labels and model predictions
  - Scores: Direct classification scores (0, 1, 2)
  - Matching: Direct comparison of predictions to ground truth (no string matching)
  - Evaluation: Global ranking across all items
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List, Optional, Tuple, Union
import pandas as pd
import numpy as np


class DatasetFormat(str, Enum):
    """
    Dataset format types
    
    - CLIMRETRIEVE: Retrieval-based evaluation (scores from embeddings, string matching, or other methods)
    - S4M: Direct classification (single DataFrame, global ranking)
    - AUTO: Auto-detect format
    """
    CLIMRETRIEVE = "climretrieve"  # Retrieval-based (scores can be from embeddings/IR/string matching), separate labels/results, grouped by query
    S4M = "s4m"  # Direct classification, single DataFrame, global ranking
    AUTO = "auto"  # Auto-detect format


@dataclass(frozen=True)
class UnifiedMetrics:
    """Unified metrics result for any dataset format"""
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    f1_at_k: Dict[int, float]
    ndcg_at_k: Dict[int, float]
    accuracy: Optional[float] = None
    confusion_matrix: Optional[Dict[str, int]] = None


def detect_dataset_format(
    labels: Optional[pd.DataFrame] = None,
    results: Optional[pd.DataFrame] = None,
    combined_df: Optional[pd.DataFrame] = None,
) -> DatasetFormat:
    """
    Auto-detect dataset format based on available data.
    
    ClimRetrieve (retrieval-based):
    - Separate labels and results files
    - Structure: report/question/paragraph with retrieval scores
    - Scores can come from: embeddings, string matching (BM25/IR), or any retrieval method
    - Matching: Exact string matching on (report, question, paragraph) to match results to labels
    
    S4M (direct classification):
    - Single DataFrame with both GT and predictions
    - No report/question grouping structure
    - Scores come from direct classification (not retrieval)
    - Matching: Direct comparison (no string matching needed)
    
    Args:
        labels: Separate labels DataFrame (ClimRetrieve format)
        results: Separate results DataFrame (ClimRetrieve format, contains embedding similarity scores)
        combined_df: Combined DataFrame with both GT and predictions (S4M format, direct classification)
    
    Returns:
        Detected DatasetFormat
    """
    # If we have separate labels and results, it's ClimRetrieve format (embedding-based)
    if labels is not None and results is not None:
        # Check for ClimRetrieve structure (report/question/paragraph indicates query-based retrieval)
        if all(col in labels.columns for col in ["report", "question", "paragraph", "relevance"]):
            if all(col in results.columns for col in ["report", "question", "paragraph"]):
                # Has score column indicating embedding similarity
                if "score" in results.columns or any("score" in col.lower() for col in results.columns):
                    return DatasetFormat.CLIMRETRIEVE
    
    # If we have combined DataFrame, check for S4M format (direct classification)
    if combined_df is not None:
        # S4M format: single DataFrame with ground truth and model prediction columns
        # Check if it has typical S4M structure (no report/question grouping)
        if "report" not in combined_df.columns or "question" not in combined_df.columns:
            return DatasetFormat.S4M
        # If it has report/question but also has model prediction columns, might be S4M
        # (we'll let the caller specify format explicitly)
    
    # Default to ClimRetrieve if we can't determine
    return DatasetFormat.CLIMRETRIEVE


def evaluate_unified(
    # ClimRetrieve format inputs (embedding-based retrieval)
    labels: Optional[pd.DataFrame] = None,
    results: Optional[pd.DataFrame] = None,
    # S4M format inputs (direct classification)
    combined_df: Optional[pd.DataFrame] = None,
    ground_truth_col: Optional[str] = None,
    model_pred_col: Optional[str] = None,
    # Format specification
    dataset_format: Union[DatasetFormat, str] = DatasetFormat.AUTO,
    # Common parameters
    k_values: Iterable[int] = (1, 3, 5, 10),
    relevance_threshold: Union[int, float] = 1,
    gain_scheme: str = "auto",  # "auto", "exp", "linear"
    # ClimRetrieve-specific (embedding-based)
    score_col: str = "score",  # Embedding similarity score
    paragraph_col: str = "paragraph",
    # S4M-specific (direct classification)
    round_predictions: bool = True,
    label_range: Optional[Tuple[int, int]] = None,
) -> UnifiedMetrics:
    """
    Unified evaluation function that works with both ClimRetrieve and S4M datasets.
    
    ClimRetrieve (Retrieval-based Evaluation):
    - Retrieval task: scores can be from embeddings, string matching (BM25/IR), or other methods
    - Matching: Uses exact string matching on (report, question, paragraph) to match results to labels
    - Scores represent retrieval quality (higher = better match, regardless of method)
    - Separate labels (GT) and results (model outputs with retrieval scores)
    - Evaluation grouped by (report, question) with macro-averaging
    
    S4M (Direct Classification):
    - Classification task: no retrieval involved
    - Matching: Direct comparison of predictions to ground truth labels
    - Scores represent classification confidence/labels (0, 1, 2)
    - Single DataFrame with both GT and model predictions
    - Global ranking evaluation (not grouped by query)
    
    Args:
        labels: Ground truth labels DataFrame (ClimRetrieve - retrieval-based)
        results: Model results DataFrame with retrieval scores (ClimRetrieve - can be from embeddings, string matching, or other methods)
        combined_df: Combined DataFrame with both GT and predictions (S4M - direct classification)
        ground_truth_col: Column name for ground truth (S4M format)
        model_pred_col: Column name for model predictions/classification scores (S4M format)
        dataset_format: Dataset format ("climretrieve", "s4m", or "auto")
        k_values: K values for metrics
        relevance_threshold: Threshold for binary relevance
        gain_scheme: nDCG gain scheme ("auto"=exp for ClimRetrieve, linear for S4M)
        score_col: Score column name (ClimRetrieve - retrieval score, any method)
        paragraph_col: Paragraph column name (ClimRetrieve)
        round_predictions: Whether to round predictions to integers (S4M - for discrete labels)
        label_range: Valid label range (min, max) for S4M (default: (0, 2))
    
    Returns:
        UnifiedMetrics with computed scores
    """
    # Auto-detect format if needed
    if dataset_format == DatasetFormat.AUTO or dataset_format == "auto":
        dataset_format = detect_dataset_format(labels, results, combined_df)
    
    # Convert string to enum if needed
    if isinstance(dataset_format, str):
        dataset_format = DatasetFormat(dataset_format)
    
    # Route to appropriate evaluation function
    if dataset_format == DatasetFormat.CLIMRETRIEVE:
        return _evaluate_climretrieve_format(
            labels=labels,
            results=results,
            k_values=k_values,
            relevance_threshold=int(relevance_threshold),
            gain_scheme=gain_scheme,
            score_col=score_col,
            paragraph_col=paragraph_col,
        )
    elif dataset_format == DatasetFormat.S4M:
        return _evaluate_s4m_format(
            df=combined_df,
            ground_truth_col=ground_truth_col,
            model_pred_col=model_pred_col,
            k_values=k_values,
            relevance_threshold=float(relevance_threshold),
            gain_scheme=gain_scheme,
            round_predictions=round_predictions,
            label_range=label_range,
        )
    else:
        raise ValueError(f"Unknown dataset format: {dataset_format}")


def _evaluate_climretrieve_format(
    labels: pd.DataFrame,
    results: pd.DataFrame,
    k_values: Iterable[int],
    relevance_threshold: int,
    gain_scheme: str,
    score_col: str,
    paragraph_col: str,
) -> UnifiedMetrics:
    """
    Evaluate ClimRetrieve format (retrieval-based evaluation).
    
    This format evaluates retrieval results where scores can come from:
    - Embedding similarity (e.g., semantic similarity)
    - String matching (e.g., BM25, TF-IDF, keyword matching)
    - Or any other retrieval method
    
    Matching: Uses exact string matching on (report, question, paragraph) to match
    results to labels. The evaluation doesn't care HOW scores were generated.
    
    Evaluation is grouped by (report, question) with macro-averaging across queries.
    """
    from .climretrieve_metrics import evaluate_climretrieve
    
    # Use ClimRetrieve evaluation (retrieval-based)
    # Results contain retrieval scores (from embeddings, string matching, or other methods)
    # Matching uses exact string matching on (report, question, paragraph)
    metrics = evaluate_climretrieve(
        labels=labels,
        results=results,
        k_values=k_values,
        relevance_threshold=relevance_threshold,
        gain_scheme=gain_scheme if gain_scheme != "auto" else "exp",  # Default: exponential for embeddings
    )
    
    # Convert to UnifiedMetrics
    return UnifiedMetrics(
        precision_at_k=metrics.precision_at_k,
        recall_at_k=metrics.recall_at_k,
        f1_at_k=metrics.f1_at_k,
        ndcg_at_k=metrics.ndcg_at_k,
        accuracy=None,  # ClimRetrieve doesn't compute accuracy (retrieval task)
        confusion_matrix=None,
    )


def _evaluate_s4m_format(
    df: pd.DataFrame,
    ground_truth_col: str,
    model_pred_col: str,
    k_values: Iterable[int],
    relevance_threshold: float,
    gain_scheme: str,
    round_predictions: bool,
    label_range: Optional[Tuple[int, int]],
) -> UnifiedMetrics:
    """
    Evaluate S4M format (direct classification, no retrieval).
    
    This format uses direct classification/labeling - no retrieval or embeddings involved.
    Model predictions are classification scores/labels (0, 1, 2).
    Matching: Direct comparison of predictions to ground truth (no string matching needed).
    Evaluation is global ranking across all items (not grouped by query).
    """
    from .s4m_metrics import evaluate_s4m_classification
    
    # Determine label range
    if label_range is None:
        label_range = (0, 2)  # Default for S4M
    
    # Use S4M evaluation (direct classification, no retrieval)
    # Model predictions are classification scores, not retrieval scores
    # Direct comparison - no string matching needed
    metrics = evaluate_s4m_classification(
        df=df,
        ground_truth_col=ground_truth_col,
        model_pred_col=model_pred_col,
        relevance_threshold=relevance_threshold,
        k_values=k_values,
    )
    
    # Convert to UnifiedMetrics
    return UnifiedMetrics(
        precision_at_k=metrics.precision_at_k,
        recall_at_k=metrics.recall_at_k,
        f1_at_k=metrics.f1_at_k,
        ndcg_at_k=metrics.ndcg_at_k,
        accuracy=metrics.accuracy,  # S4M computes accuracy (classification task)
        confusion_matrix=metrics.confusion_matrix,  # S4M includes confusion matrix
    )


def evaluate_multiple_models(
    # S4M format (multiple models in one DataFrame)
    df: pd.DataFrame,
    ground_truth_col: str,
    model_cols: List[str],
    k_values: Iterable[int] = (1, 3, 5, 10),
    relevance_threshold: float = 1.0,
    gain_scheme: str = "auto",
) -> Dict[str, UnifiedMetrics]:
    """
    Evaluate multiple models (S4M format only).
    
    Args:
        df: DataFrame with ground truth and multiple model predictions
        ground_truth_col: Column name for ground truth
        model_cols: List of model prediction column names
        k_values: K values for metrics
        relevance_threshold: Relevance threshold
        gain_scheme: nDCG gain scheme
    
    Returns:
        Dictionary mapping model name to UnifiedMetrics
    """
    results = {}
    
    for model_col in model_cols:
        if model_col not in df.columns:
            continue
        
        try:
            metrics = evaluate_unified(
                combined_df=df,
                ground_truth_col=ground_truth_col,
                model_pred_col=model_col,
                dataset_format=DatasetFormat.S4M,
                k_values=k_values,
                relevance_threshold=relevance_threshold,
                gain_scheme=gain_scheme,
            )
            results[model_col] = metrics
        except Exception as e:
            print(f"Error evaluating model {model_col}: {e}")
            continue
    
    return results


# Convenience functions for backward compatibility
def evaluate_climretrieve_unified(
    labels: pd.DataFrame,
    results: pd.DataFrame,
    k_values: Iterable[int] = (1, 3, 5, 10),
    relevance_threshold: int = 1,
    gain_scheme: str = "exp",
    score_col: str = "score",
    paragraph_col: str = "paragraph",
) -> UnifiedMetrics:
    """Convenience function for ClimRetrieve evaluation"""
    return evaluate_unified(
        labels=labels,
        results=results,
        dataset_format=DatasetFormat.CLIMRETRIEVE,
        k_values=k_values,
        relevance_threshold=relevance_threshold,
        gain_scheme=gain_scheme,
        score_col=score_col,
        paragraph_col=paragraph_col,
    )


def evaluate_s4m_unified(
    df: pd.DataFrame,
    ground_truth_col: str,
    model_pred_col: str,
    k_values: Iterable[int] = (1, 3, 5, 10),
    relevance_threshold: float = 1.0,
    gain_scheme: str = "auto",
) -> UnifiedMetrics:
    """Convenience function for S4M evaluation"""
    return evaluate_unified(
        combined_df=df,
        ground_truth_col=ground_truth_col,
        model_pred_col=model_pred_col,
        dataset_format=DatasetFormat.S4M,
        k_values=k_values,
        relevance_threshold=relevance_threshold,
        gain_scheme=gain_scheme,
    )

