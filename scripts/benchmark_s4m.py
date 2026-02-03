#!/usr/bin/env python3
"""
Script to benchmark S4M dataset with multiple model predictions.

Usage:
    # Single model with default grouping (by criteria and company)
    python scripts/benchmark_s4m.py \
        --data data/s4m/test_data_labelled_naive.xlsx \
        --ground-truth-col "relevance" \
        --model-col "model1" \
        --k 1,3,5,10
    
    # Single model with custom grouping
    python scripts/benchmark_s4m.py \
        --data data/s4m/test_data_labelled_naive.xlsx \
        --ground-truth-col "relevance" \
        --model-col "model1" \
        --group-by criteria company \
        --k 1,3,5,10
    
    # Single model without grouping (global evaluation)
    python scripts/benchmark_s4m.py \
        --data data/s4m/test_data_labelled_naive.xlsx \
        --ground-truth-col "relevance" \
        --model-col "model1" \
        --no-grouping \
        --k 1,3,5,10
    
    # Multiple models comparison
    python scripts/benchmark_s4m.py \
        --data data/s4m/test_data_labelled_naive.xlsx \
        --ground-truth-col "relevance" \
        --model-cols "model1" "model2" "model3" \
        --k 1,3,5,10 \
        --threshold 1.0
"""

import sys
from pathlib import Path
import argparse
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from report_analyst.core.benchmark.s4m_metrics import evaluate_s4m_multiple_models, evaluate_s4m_classification


def main():
    parser = argparse.ArgumentParser(description="Benchmark S4M dataset with model predictions")
    parser.add_argument("--data", required=True, help="Path to S4M dataset CSV/Excel file")
    parser.add_argument("--ground-truth-col", required=True, help="Column name for ground truth labels")
    parser.add_argument("--model-cols", nargs="+", help="Column names for model predictions (if multiple)")
    parser.add_argument("--model-col", help="Single model column name (alternative to --model-cols)")
    parser.add_argument("--k", default="1,3,5,10", help="Comma-separated K values")
    parser.add_argument("--threshold", type=float, default=1.0, help="Relevance threshold (default: 1.0, meaning labels >= 1 are relevant)")
    parser.add_argument("--sheet", help="Sheet name if Excel file (default: first sheet)")
    parser.add_argument("--group-by", nargs="*", help="Columns to group by (e.g., 'criteria company'). Default: ['criteria', 'company']. Use '--group-by' with no arguments for global evaluation (no grouping)")
    parser.add_argument("--no-grouping", action="store_true", help="Use global evaluation (no grouping). Equivalent to --group-by with no arguments")
    args = parser.parse_args()
    
    # Load data
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: File not found: {data_path}")
        return 1
    
    print(f"Loading data from: {data_path}")
    if data_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(data_path, sheet_name=args.sheet)
    else:
        df = pd.read_csv(data_path)
    
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print()
    
    # Parse K values
    k_values = [int(k.strip()) for k in args.k.split(",") if k.strip().isdigit()]
    
    # Determine model columns
    if args.model_cols:
        model_cols = args.model_cols
    elif args.model_col:
        model_cols = [args.model_col]
    else:
        # Auto-detect: find columns that are not ground truth
        exclude_cols = {args.ground_truth_col, "chunk", "chunk_text", "text", "paragraph"}
        model_cols = [col for col in df.columns if col not in exclude_cols and col != args.ground_truth_col]
        print(f"Auto-detected model columns: {model_cols}")
        print()
    
    if not model_cols:
        print("Error: No model columns specified or found")
        return 1
    
    # Parse group_by argument
    # If --no-grouping is set, use empty list (global evaluation)
    # If --group-by is provided with values, use those values
    # If --group-by is provided with no values (empty list), use empty list (global evaluation)
    # If --group-by is not provided, use None (default: ['criteria', 'company'])
    if args.no_grouping:
        group_by = []  # Empty list = global evaluation
        print("Using global evaluation (no grouping)")
    elif args.group_by is not None:
        if len(args.group_by) == 0:
            group_by = []  # Empty list = global evaluation
            print("Using global evaluation (no grouping)")
        else:
            group_by = args.group_by
            print(f"Using grouping: {group_by}")
    else:
        group_by = None  # None = default grouping ['criteria', 'company']
        print("Using default grouping: ['criteria', 'company']")
    print()
    
    # Evaluate
    if len(model_cols) == 1:
        # Single model evaluation
        print(f"Evaluating model: {model_cols[0]}")
        print("=" * 60)
        
        metrics = evaluate_s4m_classification(
            df=df,
            ground_truth_col=args.ground_truth_col,
            model_pred_col=model_cols[0],
            relevance_threshold=args.threshold,
            k_values=k_values,
            group_by=group_by,
        )
        
        print(f"Ground truth column: {args.ground_truth_col}")
        print(f"Model column: {model_cols[0]}")
        print(f"Threshold: {args.threshold}")
        print(f"K values: {k_values}")
        print()
        
        print("Metrics:")
        print(f"  Precision@K: {metrics.precision_at_k}")
        print(f"  Recall@K:    {metrics.recall_at_k}")
        print(f"  F1@K:        {metrics.f1_at_k}")
        print(f"  nDCG@K:      {metrics.ndcg_at_k}")
        
        if metrics.accuracy is not None:
            print(f"  Accuracy:    {metrics.accuracy:.4f}")
        
        if metrics.confusion_matrix:
            print(f"  Confusion Matrix:")
            for key, value in metrics.confusion_matrix.items():
                print(f"    {key}: {value}")
    
    else:
        # Multiple models evaluation
        print(f"Evaluating {len(model_cols)} models")
        print("=" * 60)
        
        results = evaluate_s4m_multiple_models(
            df=df,
            ground_truth_col=args.ground_truth_col,
            model_cols=model_cols,
            relevance_threshold=args.threshold,
            k_values=k_values,
            group_by=group_by,
        )
        
        print(f"Ground truth column: {args.ground_truth_col}")
        print(f"Model columns: {model_cols}")
        print(f"Threshold: {args.threshold}")
        print(f"K values: {k_values}")
        print()
        
        # Create comparison table
        comparison_data = []
        for model_name, metrics in results.items():
            for k in k_values:
                comparison_data.append({
                    "Model": model_name,
                    "K": k,
                    "Precision@K": metrics.precision_at_k.get(k, 0.0),
                    "Recall@K": metrics.recall_at_k.get(k, 0.0),
                    "F1@K": metrics.f1_at_k.get(k, 0.0),
                    "nDCG@K": metrics.ndcg_at_k.get(k, 0.0),
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        print("Comparison Results:")
        print(comparison_df.to_string(index=False))
        print()
        
        # Summary by model
        print("Summary by Model:")
        for model_name, metrics in results.items():
            print(f"\n{model_name}:")
            print(f"  Precision@K: {metrics.precision_at_k}")
            print(f"  Recall@K:    {metrics.recall_at_k}")
            print(f"  F1@K:        {metrics.f1_at_k}")
            print(f"  nDCG@K:      {metrics.ndcg_at_k}")
            if metrics.accuracy is not None:
                print(f"  Accuracy:    {metrics.accuracy:.4f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

