import logging
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd
from sklearn.metrics import (
    brier_score_loss,
    classification_report,
    f1_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


def minmax_normalize(series: pd.Series) -> np.ndarray:
    """Min-max normalize a score series to [0, 1].

    If all values are identical, returns an array of 0.5 (uninformative probability).
    """
    arr = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    if arr.size == 0:
        return arr
    min_val = np.nanmin(arr)
    max_val = np.nanmax(arr)
    if not np.isfinite(min_val) or not np.isfinite(max_val):
        return np.zeros_like(arr, dtype=float)
    if max_val == min_val:
        return np.full_like(arr, 0.5, dtype=float)
    return (arr - min_val) / (max_val - min_val)


def expected_calibration_error(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 100
) -> float:
    """Compute Expected Calibration Error (ECE) for binary labels and probabilities."""
    if y_true.size == 0:
        return 0.0

    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(y_prob, bins) - 1

    ece = 0.0
    n = len(y_true)

    for b in range(n_bins):
        mask = bin_ids == b
        if np.any(mask):
            acc = y_true[mask].mean()
            conf = y_prob[mask].mean()
            ece += (mask.sum() / n) * abs(acc - conf)

    return float(ece)


def _compute_metrics_for_pair(
    df: pd.DataFrame,
    ground_truth_col: str,
    score_col: str,
    n_bins: int = 100,
) -> Dict[str, float]:
    """Compute calibration and F1 metrics for a single (ground_truth, score) pair."""
    if ground_truth_col not in df.columns or score_col not in df.columns:
        raise ValueError(
            f"Columns '{ground_truth_col}' and/or '{score_col}' not found in DataFrame"
        )

    mask = df[ground_truth_col].notna() & df[score_col].notna()
    if not mask.any():
        logger.warning(
            "No overlapping non-NaN rows for columns '%s' and '%s'",
            ground_truth_col,
            score_col,
        )
        return {
            "ground_truth": ground_truth_col,
            "prediction": score_col,
            "ece": np.nan,
            "ece2": np.nan,
            "brier": np.nan,
            "brier2": np.nan,
            "auroc": np.nan,
            "f1": np.nan,
            "f1_1": np.nan,
            "f2_2": np.nan,
        }

    y_true = pd.to_numeric(df.loc[mask, ground_truth_col], errors="coerce").astype(int)
    y_score_raw = pd.to_numeric(df.loc[mask, score_col], errors="coerce")

    # Binary ground truth versions
    y_true_bin1 = (y_true > 0).astype(int).to_numpy()
    y_true_bin2 = (y_true > 1).astype(int).to_numpy()

    # Scores and thresholds
    y_score_minmax = minmax_normalize(y_score_raw)
    y_score_ordinal = np.where(
        y_score_raw > 1,
        2,
        np.where(y_score_raw > 0, 1, 0),
    ).astype(int)
    y_score_bin1 = (y_score_raw > 0).astype(int).to_numpy()
    y_score_bin2 = (y_score_raw > 1).astype(int).to_numpy()

    # Calibration scores (handle edge cases defensively)
    ece = expected_calibration_error(y_true_bin1, y_score_minmax, n_bins=n_bins)
    ece2 = expected_calibration_error(y_true_bin2, y_score_minmax, n_bins=n_bins)
    try:
        brier = brier_score_loss(y_true_bin1, y_score_minmax)
    except ValueError:
        brier = np.nan
    try:
        brier2 = brier_score_loss(y_true_bin2, y_score_minmax)
    except ValueError:
        brier2 = np.nan

    # AUC can fail if only one class is present
    try:
        auroc = roc_auc_score(y_true_bin1, y_score_minmax)
    except ValueError:
        auroc = np.nan

    # F1 scores
    f1_macro = f1_score(y_true, y_score_ordinal, average="macro")
    f1_1 = f1_score(y_true_bin1, y_score_bin1)
    f1_2 = f1_score(y_true_bin2, y_score_bin2)

    return {
        "ground_truth": ground_truth_col,
        "prediction": score_col,
        "ece": float(ece),
        "ece2": float(ece2),
        "brier": float(brier),
        "brier2": float(brier2),
        "auroc": float(auroc),
        "f1": float(f1_macro),
        "f1_1": float(f1_1),
        "f2_2": float(f1_2),
    }


def compute_calibration_metrics(
    df: pd.DataFrame,
    ground_truth_col: str,
    score_cols: Iterable[str],
    n_bins: int = 100,
) -> pd.DataFrame:
    """Compute calibration metrics for multiple score columns.

    Returns a DataFrame with one row per (ground_truth, prediction) pair.
    """
    rows: List[Dict[str, float]] = []
    for col in score_cols:
        try:
            row = _compute_metrics_for_pair(
                df=df,
                ground_truth_col=ground_truth_col,
                score_col=col,
                n_bins=n_bins,
            )
            rows.append(row)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Failed to compute calibration metrics for ground_truth=%s, prediction=%s: %s",
                ground_truth_col,
                col,
                exc,
            )
            rows.append(
                {
                    "ground_truth": ground_truth_col,
                    "prediction": col,
                    "ece": np.nan,
                    "ece2": np.nan,
                    "brier": np.nan,
                    "brier2": np.nan,
                    "auroc": np.nan,
                    "f1": np.nan,
                    "f1_1": np.nan,
                    "f2_2": np.nan,
                }
            )

    return pd.DataFrame(rows)


def compute_classification_report(
    df: pd.DataFrame,
    ground_truth_col: str,
    score_col: str,
) -> Dict:
    """Compute a 3-class classification report from ground-truth labels and scores.

    Uses the same 2/1/0 thresholding on the score column as in the notebook.
    """
    if ground_truth_col not in df.columns or score_col not in df.columns:
        raise ValueError(
            f"Columns '{ground_truth_col}' and/or '{score_col}' not found in DataFrame"
        )

    mask = df[ground_truth_col].notna() & df[score_col].notna()
    if not mask.any():
        return {}

    y_true = (
        pd.to_numeric(df.loc[mask, ground_truth_col], errors="coerce")
        .astype(int)
        .to_numpy()
    )
    y_score = pd.to_numeric(df.loc[mask, score_col], errors="coerce")
    y_pred = np.where(
        y_score > 1,
        2,
        np.where(y_score > 0, 1, 0),
    ).astype(int)

    # Choose human-friendly target names
    if ground_truth_col == "usefulness":
        target_names = ["not useful (0)", "partially useful (1)", "useful (2)"]
    else:
        target_names = ["irrelevant (0)", "partially relevant (1)", "relevant (2)"]

    report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2],
        target_names=target_names,
        digits=3,
        output_dict=True,
        zero_division=0,
    )
    return report


__all__ = [
    "minmax_normalize",
    "expected_calibration_error",
    "compute_calibration_metrics",
    "compute_classification_report",
]
