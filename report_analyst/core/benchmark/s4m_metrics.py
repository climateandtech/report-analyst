# app/core/benchmark/s4m_metrics.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Iterable
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class S4MMetrics:
    """Metrics for S4M dataset evaluation"""
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    f1_at_k: Dict[int, float]
    ndcg_at_k: Dict[int, float]
    accuracy: Optional[float] = None
    confusion_matrix: Optional[Dict[str, int]] = None


def evaluate_s4m_classification(
    df: pd.DataFrame,
    ground_truth_col: str,
    model_pred_col: str,
    relevance_threshold: float = 1.0,
    k_values: Iterable[int] = (1, 3, 5, 10),
    group_by: Optional[List[str]] = None,
) -> S4MMetrics:
    """
    Evaluate classification/labeling performance for S4M dataset.
    
    This treats the task as a ranking problem where chunks are ranked by
    model prediction scores, and we evaluate against ground truth labels.
    
    Metrics are calculated per (criteria, company) pair and then macro-averaged,
    similar to ClimRetrieve's per-query evaluation.
    
    Ground truth and model predictions are discrete labels (0, 1, 2).
    Model predictions are rounded to nearest integer if continuous.
    
    Args:
        df: DataFrame with chunk text, ground truth, and model predictions
        ground_truth_col: Column name for ground truth labels (relevance/usefulness)
        model_pred_col: Column name for model predictions/scores
        relevance_threshold: Threshold for considering a label as "relevant" (default: 1.0, meaning >= 1)
        k_values: K values for Precision@K, Recall@K, etc.
        group_by: Columns to group by (default: ["criteria", "company"])
    
    Returns:
        S4MMetrics with computed scores (macro-averaged across groups)
    """
    k_values = sorted(set(int(k) for k in k_values))
    
    # Log the grouping being used
    logger.debug(f"evaluate_s4m_classification called with group_by={group_by}")
    
    # Default grouping: criteria and company
    if group_by is None:
        group_by = ["criteria", "company"]
        logger.debug(f"Using default grouping: {group_by}")
    
    # Handle empty list (global evaluation - no grouping)
    if group_by == []:
        # Treat entire dataset as one group
        group_by = None
        logger.debug("Using global evaluation (no grouping)")
    
    if group_by is not None:
        logger.info(f"Evaluating with grouping: {group_by}")
    else:
        logger.info("Evaluating globally (no grouping)")
    
    # Ensure we have the required columns (only if grouping is used)
    if group_by is not None:
        required_cols = [ground_truth_col, model_pred_col] + group_by
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Available: {list(df.columns)}")
    
    # Convert to numeric, handling any non-numeric values
    df = df.copy()
    
    # Process ground truth: convert to integer (discrete labels 0, 1, 2)
    df[ground_truth_col] = pd.to_numeric(df[ground_truth_col], errors="coerce").fillna(0.0)
    df[ground_truth_col] = df[ground_truth_col].round().astype(int)
    # Clamp to valid range [0, 2]
    df[ground_truth_col] = df[ground_truth_col].clip(lower=0, upper=2)
    
    # Process model predictions: keep original continuous scores for ranking
    # We'll round them later for metric calculation, but need original for proper ranking
    df[model_pred_col] = pd.to_numeric(df[model_pred_col], errors="coerce").fillna(0.0)
    
    # Create a copy of original scores for ranking (before rounding)
    df["_original_pred_score"] = df[model_pred_col].copy()
    
    # Round predictions for metric calculation (after we've used original for ranking)
    df[model_pred_col] = df[model_pred_col].round().astype(int)
    df[model_pred_col] = df[model_pred_col].clip(lower=0, upper=2)
    
    # Create binary relevance (1 if >= threshold, 0 otherwise)
    # For discrete labels: threshold 1.0 means labels 1 and 2 are relevant
    df["gt_binary"] = (df[ground_truth_col] >= relevance_threshold).astype(int)
    df["pred_binary"] = (df[model_pred_col] >= relevance_threshold).astype(int)
    
    # Sort by ORIGINAL continuous model prediction score (descending) within each group
    # This ensures proper ranking even when scores round to the same integer
    if group_by is not None:
        df = df.sort_values(
            by=group_by + ["_original_pred_score"],
            ascending=[True] * len(group_by) + [False],
            kind="mergesort",
        )
    else:
        # Global evaluation - sort by score only
        df = df.sort_values(
            by=["_original_pred_score"],
            ascending=[False],
            kind="mergesort",
        )
    
    # Ground-truth totals per group (from labels, not from results)
    gt = df.copy()
    gt["is_rel"] = gt["gt_binary"] == 1
    
    # Build ground truth relevance scores per group for proper IDCG calculation
    if group_by is not None:
        total_relevant = (
            gt.groupby(group_by)["is_rel"].sum().astype(int)
        )
        gt_relevance_per_group = {}
        for group_key, g in df.groupby(group_by, sort=False):
            gt_relevance_per_group[group_key] = g[ground_truth_col].tolist()
        groups = df.groupby(group_by, sort=False)
    else:
        # Global evaluation - treat entire dataset as one group
        total_relevant = pd.Series([gt["is_rel"].sum().astype(int)], index=[None])
        gt_relevance_per_group = {None: df[ground_truth_col].tolist()}
        groups = [(None, df)]
    
    # Prepare accumulators for per-group values
    prec_per_k = {k: [] for k in k_values}
    rec_per_k = {k: [] for k in k_values}
    f1_per_k = {k: [] for k in k_values}
    ndcg_per_k = {k: [] for k in k_values}
    
    # Evaluate each group (or entire dataset if no grouping)
    num_groups_processed = 0
    for group_key, g in groups:
        num_groups_processed += 1
        logger.debug(f"Processing group {num_groups_processed}: {group_key} ({len(g)} rows)")
        
        # CRITICAL: Ensure rows within group are sorted by prediction score (descending)
        # groupby preserves DataFrame order, but we need to ensure it's sorted by score
        g_sorted = g.sort_values(by="_original_pred_score", ascending=False, kind="mergesort")
        
        rels_ranked = g_sorted[ground_truth_col].tolist()
        bin_ranked = [1 if r >= relevance_threshold else 0 for r in rels_ranked]
        
        # Debug: Log first few scores in group
        if num_groups_processed <= 3:  # Only log first 3 groups to avoid spam
            logger.debug(f"  Group {group_key} - Top 3 scores: {g_sorted['_original_pred_score'].head(3).tolist()}")
            logger.debug(f"  Group {group_key} - Top 3 relevance: {g_sorted[ground_truth_col].head(3).tolist()}")
        
        # Get total relevant items for this group
        # Handle both single column (scalar key) and multiple columns (tuple key)
        try:
            # Try direct indexing first (works for both scalar and tuple keys)
            if group_key in total_relevant.index:
                gt_rel = int(total_relevant.loc[group_key])
            else:
                # Fallback: calculate directly from this group's ground truth
                gt_rel = int(g["gt_binary"].sum())
        except (KeyError, TypeError):
            # If indexing fails, calculate directly from this group
            gt_rel = int(g["gt_binary"].sum())
        
        # Get all ground truth relevance scores for this group (for proper IDCG)
        all_gt_relevance = gt_relevance_per_group.get(group_key, [])
        
        for k in k_values:
            if k <= 0:
                continue
            
            hits_k = int(sum(bin_ranked[:k]))
            precision_k = hits_k / float(k) if k > 0 else 0.0
            
            if gt_rel > 0:
                recall_k = hits_k / float(gt_rel)
            else:
                recall_k = 0.0
            
            if precision_k + recall_k > 0:
                f1_k = 2 * precision_k * recall_k / (precision_k + recall_k)
            else:
                f1_k = 0.0
            
            ndcg_k = _ndcg_at_k(rels_ranked, k=k, all_gt_relevance=all_gt_relevance)
            
            prec_per_k[k].append(precision_k)
            rec_per_k[k].append(recall_k)
            f1_per_k[k].append(f1_k)
            ndcg_per_k[k].append(ndcg_k)
    
    logger.info(f"Processed {num_groups_processed} groups for evaluation")
    
    # Log per-group metrics summary (only for first K value to avoid spam)
    if num_groups_processed > 0 and len(k_values) > 0:
        first_k = k_values[0]
        if len(prec_per_k.get(first_k, [])) > 0:
            logger.debug(f"Per-group precision@{first_k} range: [{min(prec_per_k[first_k]):.4f}, {max(prec_per_k[first_k]):.4f}]")
    
    # Macro average across groups
    precision_at_k = {k: float(np.mean(prec_per_k[k])) if prec_per_k[k] else 0.0 for k in k_values}
    recall_at_k = {k: float(np.mean(rec_per_k[k])) if rec_per_k[k] else 0.0 for k in k_values}
    f1_at_k = {k: float(np.mean(f1_per_k[k])) if f1_per_k[k] else 0.0 for k in k_values}
    ndcg_at_k = {k: float(np.mean(ndcg_per_k[k])) if ndcg_per_k[k] else 0.0 for k in k_values}
    
    # Calculate accuracy using discrete labels (exact match) - global across all items
    accuracy = float((df[ground_truth_col] == df[model_pred_col]).mean())
    
    # Confusion matrix for discrete classification (0, 1, 2) - global across all items
    confusion_matrix = {}
    for gt_label in [0, 1, 2]:
        for pred_label in [0, 1, 2]:
            key = f"GT_{gt_label}_PRED_{pred_label}"
            count = int(((df[ground_truth_col] == gt_label) & (df[model_pred_col] == pred_label)).sum())
            confusion_matrix[key] = count
    
    # Also calculate binary confusion matrix (relevant vs not relevant) - global
    binary_confusion = {
        "TP": int(((df["gt_binary"] == 1) & (df["pred_binary"] == 1)).sum()),
        "TN": int(((df["gt_binary"] == 0) & (df["pred_binary"] == 0)).sum()),
        "FP": int(((df["gt_binary"] == 0) & (df["pred_binary"] == 1)).sum()),
        "FN": int(((df["gt_binary"] == 1) & (df["pred_binary"] == 0)).sum()),
    }
    confusion_matrix.update(binary_confusion)
    
    return S4MMetrics(
        precision_at_k=precision_at_k,
        recall_at_k=recall_at_k,
        f1_at_k=f1_at_k,
        ndcg_at_k=ndcg_at_k,
        accuracy=accuracy,
        confusion_matrix=confusion_matrix
    )


def evaluate_s4m_multiple_models(
    df: pd.DataFrame,
    ground_truth_col: str,
    model_cols: List[str],
    relevance_threshold: float = 1.0,
    k_values: Iterable[int] = (1, 3, 5, 10),
    group_by: Optional[List[str]] = None,
) -> Dict[str, S4MMetrics]:
    """
    Evaluate multiple models on S4M dataset.
    
    Metrics are calculated per (criteria, company) pair and macro-averaged.
    
    Args:
        df: DataFrame with chunk text, ground truth, and multiple model predictions
        ground_truth_col: Column name for ground truth labels
        model_cols: List of column names for different model predictions
        relevance_threshold: Threshold for considering a label as "relevant"
        k_values: K values for metrics
        group_by: Columns to group by (default: ["criteria", "company"])
    
    Returns:
        Dictionary mapping model name to S4MMetrics
    """
    results = {}
    
    for model_col in model_cols:
        if model_col not in df.columns:
            continue
        
        try:
            metrics = evaluate_s4m_classification(
                df=df,
                ground_truth_col=ground_truth_col,
                model_pred_col=model_col,
                relevance_threshold=relevance_threshold,
                k_values=k_values,
                group_by=group_by,
            )
            results[model_col] = metrics
        except Exception as e:
            print(f"Error evaluating model {model_col}: {e}")
            continue
    
    return results


def _ndcg_at_k(rels_ranked: List[int], k: int, all_gt_relevance: List[int] = None) -> float:
    """
    Compute nDCG@K for ranking evaluation with discrete labels (0, 1, 2).
    
    Args:
        rels_ranked: Relevance scores of items in ranking order (discrete: 0, 1, 2)
        k: Cutoff value
        all_gt_relevance: All ground truth relevance scores (for proper IDCG)
    
    Returns:
        nDCG@K score
    """
    if k <= 0:
        return 0.0
    
    rels_k = rels_ranked[:k]
    
    # Calculate DCG using linear gain (for discrete labels 0, 1, 2)
    dcg_k = 0.0
    for i, rel in enumerate(rels_k, start=1):
        gain = float(rel)  # Use linear gain: label value directly
        dcg_k += gain / np.log2(i + 1)
    
    # Calculate IDCG (ideal DCG) - sorted in descending order
    if all_gt_relevance is not None:
        ideal = sorted(all_gt_relevance, reverse=True)[:k]
    else:
        ideal = sorted(rels_ranked, reverse=True)[:k]
    
    idcg_k = 0.0
    for i, rel in enumerate(ideal, start=1):
        gain = float(rel)
        idcg_k += gain / np.log2(i + 1)
    
    if idcg_k == 0.0:
        return 0.0
    
    return float(dcg_k / idcg_k)

