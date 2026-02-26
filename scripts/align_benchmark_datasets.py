#!/usr/bin/env python3
"""
Script to align ground truth and benchmark datasets for consistent evaluation.

This CLI is now a thin wrapper over the DatasetMapper abstraction in
report_analyst.core.benchmark.dataset_mapper so that the same logic can be
used from both the command line and the Streamlit app.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from report_analyst.core.benchmark.dataset_mapper import DatasetMapperFactory

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Align ground truth and benchmark datasets for consistent evaluation"
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="climretrieve",
        help="Dataset identifier used to select the mapping configuration (default: climretrieve)",
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

    args = parser.parse_args()

    dataset_id: str = args.dataset_id
    mapper = DatasetMapperFactory.get_mapper(dataset_id)
    logger.info("Using dataset mapper for '%s'", dataset_id)

    # Load ground truth
    gt_path = Path(args.ground_truth)
    logger.info("Loading ground truth from: %s", gt_path)
    if gt_path.suffix in [".xlsx", ".xls"]:
        df_gt = pd.read_excel(gt_path)
    else:
        df_gt = pd.read_csv(gt_path)

    # Align ground truth
    output_gt_path = args.output_ground_truth or str(gt_path).replace(
        ".csv", "_aligned.csv"
    ).replace(".xlsx", "_aligned.csv").replace(".xls", "_aligned.csv")
    df_gt_aligned = mapper.align_ground_truth(df_gt)
    df_gt_aligned.to_csv(output_gt_path, index=False)
    logger.info("Saved transformed ground truth to: %s", output_gt_path)

    # Load benchmark results
    benchmark_path = Path(args.benchmark_results)
    logger.info("Loading benchmark results from: %s", benchmark_path)
    df_benchmark = pd.read_csv(benchmark_path)

    # Align benchmark results
    output_benchmark_path = args.output_benchmark or str(benchmark_path).replace(
        ".csv", "_aligned.csv"
    )
    df_benchmark_aligned = mapper.align_benchmark(df_benchmark)
    df_benchmark_aligned.to_csv(output_benchmark_path, index=False)
    logger.info("Saved transformed benchmark results to: %s", output_benchmark_path)

    # Summary
    logger.info("\n%s", "=" * 60)
    logger.info("Alignment Summary")
    logger.info("%s", "=" * 60)
    logger.info("Ground truth queries: %d", df_gt_aligned["query_id"].nunique())
    logger.info("Benchmark queries: %d", df_benchmark_aligned["query_id"].nunique())
    common_queries = set(df_gt_aligned["query_id"]).intersection(
        set(df_benchmark_aligned["query_id"])
    )
    logger.info("Common queries: %d", len(common_queries))
    logger.info("\nTransformed files:")
    logger.info("  Ground truth: %s", output_gt_path)
    logger.info("  Benchmark: %s", output_benchmark_path)
    logger.info(
        "\nThese files are ready for evaluation using evaluate_benchmark_from_csv.py"
    )


if __name__ == "__main__":
    main()
