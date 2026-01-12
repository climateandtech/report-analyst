# app/core/benchmark/climretrieve_metrics.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ClimRetrieveMetrics:
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    f1_at_k: Dict[int, float]
    ndcg_at_k: Dict[int, float]


def _dcg(rels: List[int], gain_scheme: str = "exp") -> float:
    """
    DCG with either:
      - exp gain: (2^rel - 1) / log2(i+1)
      - linear gain: rel / log2(i+1)

    NOTE: To get IDENTICAL results, match ClimRetrieve’s exact DCG definition.
    """
    dcg = 0.0
    for i, rel in enumerate(rels, start=1):
        if gain_scheme == "exp":
            gain = (2 ** rel) - 1
        elif gain_scheme == "linear":
            gain = rel
        else:
            raise ValueError(f"Unknown gain_scheme={gain_scheme}")
        dcg += gain / np.log2(i + 1)
    return float(dcg)


def _ndcg_at_k(rels_ranked: List[int], k: int, gain_scheme: str = "exp", all_gt_relevance: List[int] = None) -> float:
    """
    Compute nDCG@K.
    
    Args:
        rels_ranked: Relevance scores of retrieved items in ranking order
        k: Cutoff value
        gain_scheme: "exp" or "linear"
        all_gt_relevance: All relevance scores from ground truth (for proper IDCG calculation)
                          If None, falls back to using only retrieved items (incorrect but backward compatible)
    """
    rels_k = rels_ranked[:k]
    dcg_k = _dcg(rels_k, gain_scheme=gain_scheme)

    # For IDCG, use all ground truth relevance scores if provided, otherwise use retrieved only
    if all_gt_relevance is not None:
        ideal = sorted(all_gt_relevance, reverse=True)[:k]
    else:
        # Fallback: use only retrieved items (incorrect but backward compatible)
        ideal = sorted(rels_ranked, reverse=True)[:k]
    idcg_k = _dcg(ideal, gain_scheme=gain_scheme)

    if idcg_k == 0.0:
        return 0.0
    return dcg_k / idcg_k


def evaluate_climretrieve(
    labels: pd.DataFrame,
    results: pd.DataFrame,
    k_values: Iterable[int] = (1, 3, 5, 10),
    relevance_threshold: int = 1,
    gain_scheme: str = "exp",
) -> ClimRetrieveMetrics:
    """
    labels: report/question/paragraph/relevance (0..3)
    results: report/question/paragraph/score (higher better)

    Returns macro-averaged metrics across (report, question).
    """
    k_values = sorted(set(int(k) for k in k_values))

    # Join: bring relevance labels onto retrieved results
    merged = results.merge(
        labels[["report", "question", "paragraph", "relevance"]],
        on=["report", "question", "paragraph"],
        how="left",
    )
    merged["relevance"] = merged["relevance"].fillna(0).astype(int)

    # Stable sort: within each (report, question), highest score first
    merged = merged.sort_values(
        by=["report", "question", "score"],
        ascending=[True, True, False],
        kind="mergesort",
    )

    # Ground-truth totals per query (from labels, not from results)
    gt = labels.copy()
    gt["is_rel"] = gt["relevance"] >= relevance_threshold
    total_relevant = (
        gt.groupby(["report", "question"])["is_rel"].sum().astype(int)
    )
    
    # Build ground truth relevance scores per query for proper IDCG calculation
    gt_relevance_per_query = {}
    for (report, question), g in labels.groupby(["report", "question"], sort=False):
        gt_relevance_per_query[(report, question)] = g["relevance"].tolist()

    # Prepare accumulators for per-query values
    prec_per_k = {k: [] for k in k_values}
    rec_per_k = {k: [] for k in k_values}
    f1_per_k = {k: [] for k in k_values}
    ndcg_per_k = {k: [] for k in k_values}

    # Evaluate each query group
    for (report, question), g in merged.groupby(["report", "question"], sort=False):
        rels_ranked = g["relevance"].tolist()
        bin_ranked = [1 if r >= relevance_threshold else 0 for r in rels_ranked]

        gt_rel = int(total_relevant.get((report, question), 0))
        
        # Get all ground truth relevance scores for this query (for proper IDCG)
        all_gt_relevance = gt_relevance_per_query.get((report, question), [])

        for k in k_values:
            hits_k = int(sum(bin_ranked[:k]))
            precision_k = hits_k / float(k)

            if gt_rel > 0:
                recall_k = hits_k / float(gt_rel)
            else:
                recall_k = 0.0

            if precision_k + recall_k > 0:
                f1_k = 2 * precision_k * recall_k / (precision_k + recall_k)
            else:
                f1_k = 0.0

            ndcg_k = _ndcg_at_k(rels_ranked, k=k, gain_scheme=gain_scheme, all_gt_relevance=all_gt_relevance)

            prec_per_k[k].append(precision_k)
            rec_per_k[k].append(recall_k)
            f1_per_k[k].append(f1_k)
            ndcg_per_k[k].append(ndcg_k)

    # Macro average across queries
    precision_at_k = {k: float(np.mean(prec_per_k[k])) if prec_per_k[k] else 0.0 for k in k_values}
    recall_at_k = {k: float(np.mean(rec_per_k[k])) if rec_per_k[k] else 0.0 for k in k_values}
    f1_at_k = {k: float(np.mean(f1_per_k[k])) if f1_per_k[k] else 0.0 for k in k_values}
    ndcg_at_k = {k: float(np.mean(ndcg_per_k[k])) if ndcg_per_k[k] else 0.0 for k in k_values}

    return ClimRetrieveMetrics(
        precision_at_k=precision_at_k,
        recall_at_k=recall_at_k,
        f1_at_k=f1_at_k,
        ndcg_at_k=ndcg_at_k,
    )
