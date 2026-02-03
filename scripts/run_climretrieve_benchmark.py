#!/usr/bin/env python3
"""
Run ClimRetrieve benchmark evaluation from embeddings to metrics.

This script:
1. Loads ground truth dataset
2. Processes reports from core/reports/
3. Loads queries from core/Embedding_Search_Queries/
4. Generates embeddings and retrieves chunks for each query strategy
5. Evaluates against ground truth and calculates metrics

Usage:
    python3 scripts/run_climretrieve_benchmark.py
    python3 scripts/run_climretrieve_benchmark.py --strategies IR IR3 question --k 1,3,5,10
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path (go up 2 levels from scripts/ to project root)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from report_analyst.core.benchmark.climretrieve_runner import ClimRetrieveRunner


async def main():
    """Run the full ClimRetrieve evaluation workflow."""
    parser = argparse.ArgumentParser(
        description="Run ClimRetrieve benchmark evaluation"
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["IR", "IR3", "question"],
        help="Query strategies to evaluate (default: IR IR3 question)",
    )
    parser.add_argument(
        "--k",
        default="1,3,5,10",
        help="K values for evaluation, comma-separated (default: 1,3,5,10)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top chunks to retrieve per query (default: 10)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=350,
        help="Chunk size for document processing (default: 350)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Chunk overlap for document processing (default: 50)",
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        help="Directory containing PDF reports (default: core/reports/)",
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        help="Path to ground truth CSV file (default: core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv)",
    )
    parser.add_argument(
        "--queries-dir",
        type=str,
        help="Directory containing query Excel files (default: core/Embedding_Search_Queries/)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save results (default: core/benchmark/climretrieve/results/)",
    )
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        default=True,
        help="Skip computation if result files already exist (default: True)",
    )
    parser.add_argument(
        "--force-recompute",
        action="store_true",
        default=False,
        help="Force recomputation even if results exist (overrides --skip-if-exists)",
    )
    parser.add_argument(
        "--clear-embedding-cache",
        action="store_true",
        default=False,
        help="Clear embedding cache before running (forces recomputation of all embeddings)",
    )
    parser.add_argument(
        "--use-existing-results",
        action="store_true",
        default=False,
        help="Use existing results CSV files from --existing-results-dir instead of generating new ones",
    )
    parser.add_argument(
        "--existing-results-dir",
        type=str,
        default="data/climretrieve/results",
        help="Directory containing existing results CSV files (default: data/climretrieve/results)",
    )

    args = parser.parse_args()
    
    # Determine skip_if_results_exist
    skip_if_results_exist = args.skip_if_exists and not args.force_recompute

    # Parse K values
    k_values = [int(k.strip()) for k in args.k.split(",") if k.strip().isdigit()]
    if not k_values:
        k_values = [1, 3, 5, 10]

    print("=" * 60)
    print("ClimRetrieve Benchmark Evaluation")
    print("=" * 60)
    print(f"Strategies: {args.strategies}")
    print(f"K values: {k_values}")
    print(f"Top-K retrieval: {args.top_k}")
    print(f"Chunk size: {args.chunk_size}, Overlap: {args.chunk_overlap}")
    print("=" * 60)

    # Initialize runner
    runner = ClimRetrieveRunner(
        reports_dir=args.reports_dir,
        ground_truth_path=args.ground_truth,
        queries_dir=args.queries_dir,
        output_dir=args.output_dir,
        top_k=args.top_k,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    
    # Clear embedding cache if requested
    if args.clear_embedding_cache:
        print("\nClearing embedding cache...")
        runner.clear_embedding_cache()
        print("Cache cleared. All embeddings will be recomputed.\n")

    # Run evaluation
    print("\nRunning evaluation...")
    if args.use_existing_results:
        print(f"Using existing results from: {args.existing_results_dir}")
    elif skip_if_results_exist:
        print("Note: Will skip computation if result files already exist")
    try:
        metrics = await runner.run_evaluation(
            strategies=args.strategies,
            k_values=k_values,
            skip_if_results_exist=skip_if_results_exist,
            use_existing_results=args.use_existing_results,
            existing_results_dir=Path(args.existing_results_dir) if args.use_existing_results else None,
        )

        # Print summary
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        for strategy, metric in metrics.items():
            print(f"\n{strategy.upper()} Strategy:")
            print(f"  Precision@K: {metric.precision_at_k}")
            print(f"  Recall@K:    {metric.recall_at_k}")
            print(f"  F1@K:        {metric.f1_at_k}")
            print(f"  nDCG@K:      {metric.ndcg_at_k}")
            if metric.mean_average_precision is not None:
                print(f"  MAP:         {metric.mean_average_precision:.4f}")
            if metric.mean_reciprocal_rank is not None:
                print(f"  MRR:         {metric.mean_reciprocal_rank:.4f}")

        print(f"\nResults saved to: {runner.output_dir}")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


