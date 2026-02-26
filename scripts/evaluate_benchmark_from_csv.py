#!/usr/bin/env python3
"""
Evaluate a benchmark results CSV against a ground-truth/reference CSV.

This is a thin CLI wrapper around the existing EvaluationEngine and
load_flexible_dataset_from_csv helper:

- Both reference and input datasets are CSV files.
- The loader supports flexible column names and auto-detects dataset type
  (information retrieval vs information extraction).
- Metrics are computed using the core EvaluationEngine logic:
  precision@K, recall@K, F1@K, NDCG@K, MAP and MRR.

Example usage:

    python -m scripts.evaluate_benchmark_from_csv \
        --reference path/to/reference.csv \
        --input path/to/results.csv \
        --k-values 1 3 5 10

The script prints a human-readable summary to stdout and can optionally
write the metrics to a JSON file for further analysis.
"""

import sys
from pathlib import Path

# Add project root to path when running directly (not as module)
# This must happen before importing report_analyst modules
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse
import json
from typing import List, Optional

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import (
    load_flexible_dataset_from_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate benchmark results from CSV against a ground-truth/reference CSV "
            "using the EvaluationEngine (precision@K, recall@K, F1@K, NDCG@K, MAP, MRR)."
        )
    )
    parser.add_argument(
        "--reference",
        "-r",
        required=True,
        help="Path to the reference (ground truth) CSV file.",
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the benchmark results CSV file to evaluate.",
    )
    parser.add_argument(
        "--k-values",
        "-k",
        nargs="*",
        type=int,
        default=None,
        help=(
            "Optional list of K values for metrics (e.g. -k 1 3 5 10). "
            "Defaults to EvaluationEngine.default_k_values."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Optional path to write metrics as JSON.",
    )

    return parser.parse_args()


def evaluate_from_csv(
    reference_csv: str, input_csv: str, k_values: Optional[List[int]] = None
):
    """Load datasets from CSV and run EvaluationEngine comparison."""
    reference = load_flexible_dataset_from_csv(csv_path=reference_csv)
    input_dataset = load_flexible_dataset_from_csv(csv_path=input_csv)

    engine = EvaluationEngine()
    metrics = engine.compare_flexible_datasets(
        reference, input_dataset, k_values=k_values
    )
    return metrics


def print_metrics(metrics, k_values: Optional[List[int]] = None) -> None:
    """Pretty-print evaluation metrics to stdout."""
    if k_values is None or not k_values:
        k_values = sorted(metrics.precision_at_k.keys())

    print("\n================ Benchmark Evaluation Metrics ================")

    # MAP and MRR
    print(f"\nOverall metrics:")
    print(f"  MAP (mean_average_precision): {metrics.mean_average_precision:.4f}")
    print(f"  MRR (mean_reciprocal_rank):  {metrics.mean_reciprocal_rank:.4f}")

    # Metrics at K
    print("\nMetrics at K:")
    header = f"{'K':>3} | {'Precision':>9} | {'Recall':>9} | {'F1':>9} | {'NDCG':>9}"
    print(header)
    print("-" * len(header))

    for k in sorted(k_values):
        p = metrics.precision_at_k.get(k, 0.0)
        r = metrics.recall_at_k.get(k, 0.0)
        f1 = metrics.f1_at_k.get(k, 0.0)
        ndcg = metrics.ndcg_at_k.get(k, 0.0)
        print(f"{k:>3} | {p:9.4f} | {r:9.4f} | {f1:9.4f} | {ndcg:9.4f}")

    print("\n==============================================================\n")


def main() -> None:
    args = parse_args()

    reference_path = str(Path(args.reference).resolve())
    input_path = str(Path(args.input).resolve())
    k_values = args.k_values

    print("Reference CSV:", reference_path)
    print("Input CSV:    ", input_path)
    if k_values:
        print("K values:      ", k_values)

    metrics = evaluate_from_csv(reference_path, input_path, k_values=k_values)

    print_metrics(metrics, k_values=k_values)

    # Optional JSON output
    if args.output:
        out_path = Path(args.output).resolve()
        data = {
            "precision_at_k": metrics.precision_at_k,
            "recall_at_k": metrics.recall_at_k,
            "f1_at_k": metrics.f1_at_k,
            "ndcg_at_k": metrics.ndcg_at_k,
            "mean_reciprocal_rank": metrics.mean_reciprocal_rank,
            "mean_average_precision": metrics.mean_average_precision,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Metrics written to: {out_path}")


if __name__ == "__main__":
    main()
