#!/usr/bin/env python3
"""
Unified benchmarking script that works with both ClimRetrieve and S4M datasets.

This script automatically detects the dataset format and applies appropriate evaluation.
"""

import sys
from pathlib import Path
import argparse
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.benchmark.unified_metrics import (
    evaluate_unified,
    DatasetFormat,
    evaluate_multiple_models,
)
from app.core.benchmark.climretrieve_io import load_inputs


def main():
    parser = argparse.ArgumentParser(
        description="Unified benchmark evaluation for ClimRetrieve and S4M datasets"
    )
    
    # Dataset format selection
    format_group = parser.add_mutually_exclusive_group(required=True)
    format_group.add_argument(
        "--climretrieve",
        action="store_true",
        help="Use ClimRetrieve format (separate labels and results files)"
    )
    format_group.add_argument(
        "--s4m",
        action="store_true",
        help="Use S4M format (single DataFrame with GT and predictions)"
    )
    
    # ClimRetrieve arguments
    parser.add_argument("--labels", help="Labels CSV (ClimRetrieve format)")
    parser.add_argument("--results", help="Results CSV (ClimRetrieve format)")
    parser.add_argument("--strategy", help="Strategy name (for auto-resolving results path)")
    parser.add_argument("--results-dir", default="data/climretrieve/results", help="Results directory")
    parser.add_argument("--results-pattern", default="results_{strategy}.csv", help="Results file pattern")
    parser.add_argument("--score-col", default="score", help="Score column name")
    parser.add_argument("--paragraph-col", default="paragraph", help="Paragraph column name")
    
    # S4M arguments
    parser.add_argument("--data", help="Data CSV/Excel file (S4M format)")
    parser.add_argument("--ground-truth-col", help="Ground truth column name (S4M)")
    parser.add_argument("--model-col", help="Model prediction column name (S4M, single model)")
    parser.add_argument("--model-cols", nargs="+", help="Model prediction columns (S4M, multiple models)")
    parser.add_argument("--sheet", help="Sheet name if Excel file")
    
    # Common arguments
    parser.add_argument("--k", default="1,3,5,10", help="Comma-separated K values")
    parser.add_argument("--threshold", type=float, default=1.0, help="Relevance threshold")
    parser.add_argument("--gain", default="auto", choices=["auto", "exp", "linear"], help="nDCG gain scheme")
    
    args = parser.parse_args()
    
    # Parse K values
    k_values = [int(k.strip()) for k in args.k.split(",")]
    
    # Route based on format
    if args.climretrieve:
        # ClimRetrieve format
        if not args.labels:
            parser.error("--labels required for ClimRetrieve format")
        
        # Resolve results path
        if args.results:
            results_path = args.results
        elif args.strategy:
            # Try to find results file using pattern
            results_dir = Path(args.results_dir)
            patterns = [
                args.results_pattern.format(strategy=args.strategy),
                f"results_{args.strategy}.csv",
                f"embedding_results_{args.strategy}.csv",
                f"embedding_results{args.strategy}.csv",
                f"{args.strategy}_results.csv",
                f"{args.strategy}.csv",
            ]
            
            # Also try variations: IR_three -> IR3, IR3 -> IR_three, etc.
            strategy_variations = []
            if "_" in args.strategy:
                # IR_three -> IR3, IR_three -> IRthree
                strategy_variations.append(args.strategy.replace("_", ""))
                # IR_three -> IR3 (replace _three with 3, _two with 2, etc.)
                if args.strategy.endswith("_three"):
                    strategy_variations.append(args.strategy.replace("_three", "3"))
                elif args.strategy.endswith("_two"):
                    strategy_variations.append(args.strategy.replace("_two", "2"))
                elif args.strategy.endswith("_one"):
                    strategy_variations.append(args.strategy.replace("_one", "1"))
            else:
                # IR3 -> IR_three, IR3 -> IR_3
                if args.strategy.endswith("3"):
                    strategy_variations.append(args.strategy.replace("3", "_three"))
                    strategy_variations.append(args.strategy.replace("3", "_3"))
                elif args.strategy.endswith("2"):
                    strategy_variations.append(args.strategy.replace("2", "_two"))
                    strategy_variations.append(args.strategy.replace("2", "_2"))
                elif args.strategy.endswith("1"):
                    strategy_variations.append(args.strategy.replace("1", "_one"))
                    strategy_variations.append(args.strategy.replace("1", "_1"))
            
            # Add patterns for variations
            for var in strategy_variations:
                patterns.extend([
                    f"results_{var}.csv",
                    f"embedding_results_{var}.csv",
                    f"embedding_results{var}.csv",
                    f"{var}_results.csv",
                    f"{var}.csv",
                ])
            
            results_path = None
            for pattern in patterns:
                candidate = results_dir / pattern
                if candidate.exists():
                    results_path = candidate
                    break
            
            if results_path is None:
                # List available files for better error message
                available_files = list(results_dir.glob("*.csv"))
                available_names = [f.name for f in available_files] if available_files else []
                print(f"Error: Could not find results file for strategy '{args.strategy}'")
                print(f"Searched in: {results_dir}")
                print(f"Patterns tried: {patterns[:15]}... (showing first 15)")
                print(f"Available files: {available_names}")
                return 1
        else:
            parser.error("Either --results or --strategy required for ClimRetrieve format")
        
        print(f"Loading ClimRetrieve dataset...")
        print(f"  Labels: {args.labels}")
        print(f"  Results: {results_path}")
        
        # Load data
        inputs = load_inputs(
            labels_csv=args.labels,
            results_csv=results_path,
            score_col=args.score_col,
            paragraph_col=args.paragraph_col,
        )
        
        # Evaluate
        metrics = evaluate_unified(
            labels=inputs.labels,
            results=inputs.results,
            dataset_format=DatasetFormat.CLIMRETRIEVE,
            k_values=k_values,
            relevance_threshold=int(args.threshold),
            gain_scheme=args.gain if args.gain != "auto" else "exp",
            score_col=args.score_col,
            paragraph_col=args.paragraph_col,
        )
        
        print(f"\nEvaluating ClimRetrieve benchmark...")
        if args.strategy:
            print(f"Strategy: {args.strategy}")
    
    elif args.s4m:
        # S4M format
        if not args.data:
            parser.error("--data required for S4M format")
        if not args.ground_truth_col:
            parser.error("--ground-truth-col required for S4M format")
        
        if not args.model_col and not args.model_cols:
            parser.error("Either --model-col or --model-cols required for S4M format")
        
        print(f"Loading S4M dataset...")
        print(f"  Data: {args.data}")
        
        # Load data
        data_path = Path(args.data)
        if data_path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(data_path, sheet_name=args.sheet)
        else:
            df = pd.read_csv(data_path)
        
        print(f"  Loaded {len(df)} rows")
        print(f"  Ground truth column: {args.ground_truth_col}")
        
        # Evaluate single or multiple models
        if args.model_cols:
            print(f"  Evaluating {len(args.model_cols)} models...")
            metrics_dict = evaluate_multiple_models(
                df=df,
                ground_truth_col=args.ground_truth_col,
                model_cols=args.model_cols,
                k_values=k_values,
                relevance_threshold=args.threshold,
                gain_scheme=args.gain,
            )
            
            # Print comparison table
            print(f"\n{'Model':<50} {'K':<4} {'Precision@K':<12} {'Recall@K':<12} {'F1@K':<12} {'nDCG@K':<12}")
            print("-" * 100)
            for model_name, metrics in metrics_dict.items():
                for k in k_values:
                    print(f"{model_name:<50} {k:<4} {metrics.precision_at_k.get(k, 0):<12.4f} "
                          f"{metrics.recall_at_k.get(k, 0):<12.4f} {metrics.f1_at_k.get(k, 0):<12.4f} "
                          f"{metrics.ndcg_at_k.get(k, 0):<12.4f}")
            
            return 0
        else:
            print(f"  Model column: {args.model_col}")
            metrics = evaluate_unified(
                combined_df=df,
                ground_truth_col=args.ground_truth_col,
                model_pred_col=args.model_col,
                dataset_format=DatasetFormat.S4M,
                k_values=k_values,
                relevance_threshold=args.threshold,
                gain_scheme=args.gain,
            )
    
    # Print results
    print(f"\n{'='*70}")
    print("EVALUATION RESULTS")
    print(f"{'='*70}")
    print(f"K values: {k_values}")
    print(f"Threshold: {args.threshold}")
    print(f"Gain scheme: {args.gain}")
    print()
    print(f"Precision@K: {metrics.precision_at_k}")
    print(f"Recall@K:    {metrics.recall_at_k}")
    print(f"F1@K:        {metrics.f1_at_k}")
    print(f"nDCG@K:      {metrics.ndcg_at_k}")
    
    if metrics.accuracy is not None:
        print(f"Accuracy:    {metrics.accuracy:.4f}")
    
    if metrics.confusion_matrix:
        print(f"\nConfusion Matrix:")
        for key, value in sorted(metrics.confusion_matrix.items()):
            print(f"  {key}: {value}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

