#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from report_analyst.core.benchmark.climretrieve_io import load_inputs
from report_analyst.core.benchmark.climretrieve_metrics import evaluate_climretrieve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True, help="Path to ClimRetrieve Report-Level labels CSV")
    
    # Strategy-based or direct file path (mutually exclusive group)
    strategy_group = parser.add_mutually_exclusive_group(required=True)
    strategy_group.add_argument("--strategy", help="Strategy name (e.g., IR, question, IR_three). "
                                                     "Results file will be constructed as {strategy}_results.csv in --results-dir")
    strategy_group.add_argument("--results", help="Path to ClimRetrieve model run results CSV (direct file path)")
    
    parser.add_argument("--results-dir", default="data/climretrieve/results",
                       help="Directory containing result files when using --strategy (default: data/climretrieve/results)")
    parser.add_argument("--results-pattern", default="results_{strategy}.csv",
                       help="File name pattern for strategy-based results (default: results_{strategy}.csv). "
                            "Use {strategy} placeholder. Matches ClimRetrieve output format.")
    
    parser.add_argument("--score-col", default="score", help="Score column name in results CSV")
    parser.add_argument("--paragraph-col", default="paragraph", help="Paragraph/chunk column name in results CSV")
    parser.add_argument("--k", default="1,3,5,10", help="Comma-separated K values")
    parser.add_argument("--thr", type=int, default=1, help="Relevance threshold (>=thr is relevant)")
    parser.add_argument("--gain", default="exp", choices=["exp", "linear"], help="nDCG gain scheme")
    args = parser.parse_args()

    # Determine results file path
    if args.strategy:
        # Construct path from strategy
        results_path = Path(args.results_dir) / args.results_pattern.format(strategy=args.strategy)
        if not results_path.exists():
            # Try alternative patterns (try results_{strategy}.csv first as it's most common)
            alt_patterns = [
                f"results_{args.strategy}.csv",
                f"embedding_results_{args.strategy}.csv",
                f"embedding_results{args.strategy}.csv",
                f"{args.strategy}_results.csv",
                f"{args.strategy}.csv",
            ]
            found = False
            for pattern in alt_patterns:
                alt_path = Path(args.results_dir) / pattern
                if alt_path.exists():
                    results_path = alt_path
                    found = True
                    break
            if not found:
                raise FileNotFoundError(
                    f"Results file not found for strategy '{args.strategy}' in {args.results_dir}. "
                    f"Tried: {args.results_pattern.format(strategy=args.strategy)} and common alternatives."
                )
        results_csv = str(results_path)
    else:
        # Use direct path
        results_csv = args.results
        if not Path(results_csv).exists():
            raise FileNotFoundError(f"Results file not found: {results_csv}")

    k_values = [int(x.strip()) for x in args.k.split(",") if x.strip()]

    inputs = load_inputs(
        labels_csv=args.labels,
        results_csv=results_csv,
        score_col=args.score_col,
        paragraph_col=args.paragraph_col,
    )

    metrics = evaluate_climretrieve(
        labels=inputs.labels,
        results=inputs.results,
        k_values=k_values,
        relevance_threshold=args.thr,
        gain_scheme=args.gain,
    )

    print("=== ClimRetrieve Benchmark (one model run) ===")
    print(f"labels:  {args.labels}")
    if args.strategy:
        print(f"strategy: {args.strategy}")
        print(f"results:  {results_csv}")
    else:
        print(f"results:  {args.results}")
    print(f"K:       {k_values}")
    print(f"thr:     {args.thr}")
    print(f"gain:    {args.gain}")
    print()

    print("Precision@K:", metrics.precision_at_k)
    print("Recall@K:   ", metrics.recall_at_k)
    print("F1@K:       ", metrics.f1_at_k)
    print("nDCG@K:     ", metrics.ndcg_at_k)


if __name__ == "__main__":
    main()

# #python Experiments/ra_style/run_embedding_reportlvl.py     
# --reportlevel Experiments/ra_style/Report-Level-Dataset/ClimRetrieve_ReportLevel_V1.csv     
# --k "1,3,5,10"     
# --model nomic-embed-text     
# --out Experiments/ra_style/embedding_results.csv

#python3 scripts/benchmark_climretrieve_one_model.py \ --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_150.csv \ --results data/climretrieve/results/text-embedding-3-small__150.csv \ --score-col score \ --paragraph-col paragraph \ --k 1,3,5,10 \ --thr 1 \ --gain exp


