# report_analyst/core/benchmark/climretrieve_io.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class ClimRetrieveInputs:
    labels: pd.DataFrame   # ground truth labels
    results: pd.DataFrame  # ranked retrieval results


def load_climretrieve_labels(labels_csv: str | Path) -> pd.DataFrame:
    """
    Load ClimRetrieve Report-Level dataset (ground truth).

    Required columns (typical ClimRetrieve naming):
      - report
      - question
      - paragraph
      - relevance   (0..3)

    Returns a DF with columns: report, question, paragraph, relevance
    """
    df = pd.read_csv(labels_csv)

    required = {"report", "question", "paragraph", "relevance"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Labels file missing columns: {missing}. Found: {list(df.columns)}")

    df = df[["report", "question", "paragraph", "relevance"]].copy()
    df["relevance"] = pd.to_numeric(df["relevance"], errors="coerce").fillna(0).astype(int)
    return df


def load_climretrieve_results(results_csv: str | Path,
                             score_col: str = "score",
                             paragraph_col: str = "paragraph") -> pd.DataFrame:
    """
    Load a ClimRetrieve model run output (system results).

    Minimal required columns:
      - report
      - question
      - <paragraph_col>  (the chunk identity used by ClimRetrieve in that results file)
      - <score_col>      (retrieval score; higher = better)

    Returns a DF with columns: report, question, paragraph, score
    """
    df = pd.read_csv(results_csv)

    required = {"report", "question", paragraph_col, score_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Results file missing columns: {missing}. Found: {list(df.columns)}. "
            f"Set score_col/paragraph_col correctly."
        )

    out = df[["report", "question", paragraph_col, score_col]].copy()
    out = out.rename(columns={paragraph_col: "paragraph", score_col: "score"})
    out["score"] = pd.to_numeric(out["score"], errors="coerce").fillna(float("-inf"))
    return out


def load_inputs(labels_csv: str | Path,
                results_csv: str | Path,
                score_col: str = "score",
                paragraph_col: str = "paragraph") -> ClimRetrieveInputs:
    labels = load_climretrieve_labels(labels_csv)
    results = load_climretrieve_results(results_csv, score_col=score_col, paragraph_col=paragraph_col)
    return ClimRetrieveInputs(labels=labels, results=results)
