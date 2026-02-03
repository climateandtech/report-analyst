# Unified Benchmarking Guide

## Overview

The unified benchmarking system supports both **ClimRetrieve** and **S4M** dataset formats with a single interface. It automatically detects the dataset format and applies appropriate evaluation logic.

## Features

- ✅ **Automatic format detection** - Detects ClimRetrieve vs S4M format
- ✅ **Unified API** - Same function works for both formats
- ✅ **Backward compatible** - Existing scripts still work
- ✅ **Flexible** - Supports various column names and configurations

## Dataset Formats

### ClimRetrieve Format (Retrieval-based Evaluation)
- **Method**: Retrieval task - scores can be from embeddings, string matching (BM25/IR), or other methods
- **Structure**: Separate labels and results files
- **Grouping**: Grouped by (report, question) - macro-averaged metrics
- **Labels**: `report`, `question`, `paragraph`, `relevance` (0-3)
- **Results**: `report`, `question`, `paragraph`, `score` (retrieval score - can be from any method)
- **Score Type**: Retrieval score (higher = better match, regardless of method)
- **Matching**: Exact string matching on (report, question, paragraph) to match results to labels
- **Evaluation**: Query-based retrieval evaluation (doesn't care how scores were generated)

### S4M Format (Direct Classification)
- **Method**: Direct classification/labeling (no embeddings)
- **Structure**: Single DataFrame with both ground truth and predictions
- **Grouping**: Global ranking (not grouped by query)
- **Labels**: Discrete values (0, 1, 2)
- **Results**: Model prediction columns alongside ground truth
- **Score Type**: Classification scores/labels (0, 1, 2)
- **Evaluation**: Global classification evaluation

## Usage

### Python API

#### ClimRetrieve Format (Retrieval-based Evaluation)

```python
from app.core.benchmark.unified_metrics import evaluate_unified, DatasetFormat
from app.core.benchmark.climretrieve_io import load_inputs

# Load data
# Results contain retrieval scores (can be from embeddings, string matching, or other methods)
# The evaluation uses exact string matching on (report, question, paragraph) to match results to labels
inputs = load_inputs(
    labels_csv="data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv",
    results_csv="data/climretrieve/results/results_IR_three.csv",  # Contains retrieval scores
)

# Evaluate (retrieval-based evaluation)
# Note: Scores can be from embeddings, BM25, keyword matching, etc.
# The evaluation matches results to labels using exact string matching on identifiers
metrics = evaluate_unified(
    labels=inputs.labels,
    results=inputs.results,  # Results with retrieval scores (any method)
    dataset_format=DatasetFormat.CLIMRETRIEVE,  # or "climretrieve"
    k_values=[1, 3, 5, 10],
    relevance_threshold=1,
    gain_scheme="exp",  # Exponential gain (common for retrieval tasks)
)

print(f"Precision@10: {metrics.precision_at_k[10]}")
print(f"Recall@10: {metrics.recall_at_k[10]}")
```

#### S4M Format (Direct Classification)

```python
import pandas as pd
from app.core.benchmark.unified_metrics import evaluate_unified, DatasetFormat

# Load data
# Contains direct classification scores (no retrieval, no embeddings)
# Direct comparison - no string matching needed
df = pd.read_csv("data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv")

# Evaluate single model (direct classification, no retrieval)
metrics = evaluate_unified(
    combined_df=df,
    ground_truth_col="relevance",
    model_pred_col="relevance_score_gpt-4.1-nano-2025-04-14",  # Classification scores
    dataset_format=DatasetFormat.S4M,  # or "s4m"
    k_values=[1, 3, 5, 10],
    relevance_threshold=1.0,
    gain_scheme="auto",  # Auto-selects linear gain for classification
)

print(f"Precision@10: {metrics.precision_at_k[10]}")
print(f"Recall@10: {metrics.recall_at_k[10]}")
print(f"Accuracy: {metrics.accuracy}")  # Available for classification tasks
```

#### Auto-Detection

```python
# Auto-detect format
metrics = evaluate_unified(
    labels=labels_df,  # If provided, assumes ClimRetrieve
    results=results_df,  # If provided, assumes ClimRetrieve
    # OR
    combined_df=combined_df,  # If provided, assumes S4M
    ground_truth_col="relevance",
    model_pred_col="model_score",
    dataset_format=DatasetFormat.AUTO,  # Auto-detect
    k_values=[1, 3, 5, 10],
)
```

#### Multiple Models (S4M)

```python
from app.core.benchmark.unified_metrics import evaluate_multiple_models

# Evaluate multiple models
metrics_dict = evaluate_multiple_models(
    df=df,
    ground_truth_col="relevance",
    model_cols=[
        "relevance_score_gpt-4.1-nano-2025-04-14",
        "relevance_score_gpt-4.1-mini-2025-04-14",
        "relevance_score_gpt-4.1-2025-04-14",
    ],
    k_values=[1, 3, 5, 10],
    relevance_threshold=1.0,
)

# Compare models
for model_name, metrics in metrics_dict.items():
    print(f"{model_name}: Precision@10 = {metrics.precision_at_k[10]}")
```

### Command Line

#### ClimRetrieve Format

```bash
python3 scripts/benchmark_unified.py \
    --climretrieve \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR_three \
    --results-dir data/climretrieve/results \
    --k 1,3,5,10 \
    --threshold 1 \
    --gain exp
```

#### S4M Format (Single Model)

```bash
python3 scripts/benchmark_unified.py \
    --s4m \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --model-col "relevance_score_gpt-4.1-nano-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 1.0 \
    --gain auto
```

#### S4M Format (Multiple Models)

```bash
python3 scripts/benchmark_unified.py \
    --s4m \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --model-cols \
        "relevance_score_gpt-4.1-nano-2025-04-14" \
        "relevance_score_gpt-4.1-mini-2025-04-14" \
        "relevance_score_gpt-4.1-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 1.0
```

## Parameters

### Common Parameters

- `k_values`: List of K values for metrics (e.g., `[1, 3, 5, 10]`)
- `relevance_threshold`: Threshold for binary relevance
  - ClimRetrieve: Integer (default: 1)
  - S4M: Float (default: 1.0)
- `gain_scheme`: nDCG gain scheme
  - `"auto"`: Auto-select based on format (exp for ClimRetrieve, linear for S4M)
  - `"exp"`: Exponential gain `(2^rel - 1)`
  - `"linear"`: Linear gain `rel`

### ClimRetrieve-Specific

- `score_col`: Score column name (default: `"score"`)
- `paragraph_col`: Paragraph column name (default: `"paragraph"`)

### S4M-Specific

- `round_predictions`: Round predictions to integers (default: `True`)
- `label_range`: Valid label range tuple (default: `(0, 2)`)

## Metrics Returned

All formats return `UnifiedMetrics` with:

```python
@dataclass
class UnifiedMetrics:
    precision_at_k: Dict[int, float]  # Precision@K for each K
    recall_at_k: Dict[int, float]     # Recall@K for each K
    f1_at_k: Dict[int, float]         # F1@K for each K
    ndcg_at_k: Dict[int, float]       # nDCG@K for each K
    accuracy: Optional[float]         # Classification accuracy (S4M only)
    confusion_matrix: Optional[Dict]  # Confusion matrix (S4M only)
```

## Format Detection Logic

The system detects format based on:

1. **ClimRetrieve**: If `labels` and `results` DataFrames are provided with `report`, `question`, `paragraph` columns
2. **S4M**: If `combined_df` is provided without `report`/`question` grouping, or explicitly specified

## Backward Compatibility

Existing scripts continue to work:

- `scripts/benchmark_climretrieve_one_model.py` - ClimRetrieve-specific (still works)
- `scripts/benchmark_s4m.py` - S4M-specific (still works)
- `report_analyst/core/benchmark/s4m_embed_and_compare_criteria.py` - S4M embedding and similarity calculation
- `scripts/s4m_evaluate_embeddings_against_ground_truth.py` - S4M evaluation script
- `scripts/plot_climretrieve_results.py` - ClimRetrieve results visualization
- `scripts/run_climretrieve_benchmark_all_strategies.sh` - ClimRetrieve batch evaluation script
- `app.core.benchmark.climretrieve_metrics.evaluate_climretrieve()` - Still works
- `app.core.benchmark.s4m_metrics.evaluate_s4m_classification()` - Still works

## Migration Guide

### From ClimRetrieve-specific code:

```python
# Old
from app.core.benchmark.climretrieve_metrics import evaluate_climretrieve
metrics = evaluate_climretrieve(labels, results, k_values=[1,3,5,10])

# New (unified)
from app.core.benchmark.unified_metrics import evaluate_unified, DatasetFormat
metrics = evaluate_unified(
    labels=labels,
    results=results,
    dataset_format=DatasetFormat.CLIMRETRIEVE,
    k_values=[1,3,5,10]
)
```

### From S4M-specific code:

```python
# Old
from app.core.benchmark.s4m_metrics import evaluate_s4m_classification
metrics = evaluate_s4m_classification(df, "relevance", "model_score", k_values=[1,3,5,10])

# New (unified)
from app.core.benchmark.unified_metrics import evaluate_unified, DatasetFormat
metrics = evaluate_unified(
    combined_df=df,
    ground_truth_col="relevance",
    model_pred_col="model_score",
    dataset_format=DatasetFormat.S4M,
    k_values=[1,3,5,10]
)
```

## Examples

See:
- `scripts/benchmark_unified.py` - Unified command-line script (works with both)
- `scripts/benchmark_climretrieve_one_model.py` - ClimRetrieve-specific script
- `scripts/benchmark_s4m.py` - S4M-specific script
- `report_analyst/core/benchmark/s4m_embed_and_compare_criteria.py` - S4M embedding and similarity calculation
- `scripts/s4m_evaluate_embeddings_against_ground_truth.py` - S4M evaluation script
- `scripts/plot_climretrieve_results.py` - ClimRetrieve results visualization
- `scripts/run_climretrieve_benchmark_all_strategies.sh` - ClimRetrieve batch evaluation script

## Summary

The unified system provides:
- ✅ Single API for both formats
- ✅ Automatic format detection
- ✅ Backward compatibility
- ✅ Flexible configuration
- ✅ Consistent metrics output

Use `evaluate_unified()` for new code, or continue using format-specific functions for existing code.
