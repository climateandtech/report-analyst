# S4M Dataset Benchmarking Guide

## Overview

The S4M dataset contains chunks with ground truth labels (`relevance`/`usefulness`) and predictions from multiple models. This guide explains how to benchmark these models and calculate metrics.

## Dataset Structure

Your S4M dataset should have:
- **Ground truth columns**: `relevance`, `usefulness` (or similar)
- **Model prediction columns**: Various columns with model predictions/scores
- **Chunk text**: `chunk_text` or similar column
- **Other metadata**: company, industry, criteria, etc.

## How It Works

The benchmarking treats this as a **ranking problem**:
1. Models rank chunks by their prediction scores
2. We evaluate how well the ranking matches ground truth labels
3. Metrics are calculated at different K values (top K chunks)

```
Ground Truth Labels          Model Predictions
(relevance/usefulness)       (model scores)
      ↓                            ↓
      └──────────┬─────────────────┘
                 ↓
         Rank chunks by model score
                 ↓
         Compare with ground truth
                 ↓
    Calculate Precision@K, Recall@K, F1@K, nDCG@K
```

## Usage

### Basic Usage: Single Model

```bash
python3 scripts/benchmark_s4m.py \
    --data data/s4m/test_data_labelled_naive.xlsx \
    --ground-truth-col "relevance" \
    --model-col "relevance_score_gpt-4.1-nano-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 0.5
```

### Multiple Models Comparison

```bash
python3 scripts/benchmark_s4m.py \
    --data data/s4m/test_data_labelled_naive.xlsx \
    --ground-truth-col "relevance" \
    --model-cols \
        "relevance_score_gpt-4.1-nano-2025-04-14" \
        "relevance_score_gpt-4.1-mini-2025-04-14" \
        "relevance_score_gpt-4.1-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 0.5
```

### Auto-Detect Model Columns

If you don't specify model columns, the script will auto-detect all columns except the ground truth column:

```bash
python3 scripts/benchmark_s4m.py \
    --data data/s4m/test_data_labelled_naive.xlsx \
    --ground-truth-col "relevance" \
    --k 1,3,5,10 \
    --threshold 0.5
```

## Parameters

- `--data`: Path to your S4M dataset (CSV or Excel)
- `--ground-truth-col`: Column name for ground truth labels (e.g., "relevance" or "usefulness")
- `--model-col`: Single model column name (for single model evaluation)
- `--model-cols`: Multiple model column names (for comparison)
- `--k`: Comma-separated K values (default: "1,3,5,10")
- `--threshold`: Relevance threshold (default: 0.5) - values >= threshold are considered "relevant"
- `--sheet`: Sheet name if Excel file (optional, uses first sheet by default)

## Metrics Explained

### Precision@K
- **Definition**: Of the top K chunks ranked by model, how many are actually relevant?
- **Formula**: (Relevant chunks in top K) / K
- **Range**: 0.0 to 1.0 (higher is better)

### Recall@K
- **Definition**: Of all relevant chunks, how many were found in the top K?
- **Formula**: (Relevant chunks in top K) / (Total relevant chunks)
- **Range**: 0.0 to 1.0 (higher is better)

### F1@K
- **Definition**: Harmonic mean of Precision@K and Recall@K
- **Formula**: 2 × (Precision@K × Recall@K) / (Precision@K + Recall@K)
- **Range**: 0.0 to 1.0 (higher is better)

### nDCG@K
- **Definition**: Normalized Discounted Cumulative Gain - measures ranking quality
- **Range**: 0.0 to 1.0 (higher is better)
- **Note**: Takes into account the position of relevant items (earlier = better)

### Accuracy (if binary classification)
- **Definition**: Overall classification accuracy
- **Formula**: (Correct predictions) / (Total predictions)
- **Only calculated if both ground truth and predictions are binary**

## Example Output

### Single Model
```
Evaluating model: relevance_score_gpt-4.1-nano-2025-04-14
============================================================
Ground truth column: relevance
Model column: relevance_score_gpt-4.1-nano-2025-04-14
Threshold: 0.5
K values: [1, 3, 5, 10]

Metrics:
  Precision@K: {1: 0.85, 3: 0.78, 5: 0.72, 10: 0.65}
  Recall@K:    {1: 0.12, 3: 0.28, 5: 0.42, 10: 0.58}
  F1@K:        {1: 0.21, 3: 0.41, 5: 0.53, 10: 0.61}
  nDCG@K:      {1: 0.82, 3: 0.85, 5: 0.87, 10: 0.89}
  Accuracy:    0.7234
  Confusion Matrix:
    TP: 1250
    TN: 8500
    FP: 320
    FN: 480
```

### Multiple Models Comparison
```
Evaluating 3 models
============================================================
Ground truth column: relevance
Model columns: ['model1', 'model2', 'model3']
Threshold: 0.5
K values: [1, 3, 5, 10]

Comparison Results:
Model    K  Precision@K  Recall@K    F1@K    nDCG@K
model1   1         0.85      0.12    0.21      0.82
model1   3         0.78      0.28    0.41      0.85
model2   1         0.82      0.11    0.19      0.80
model2   3         0.75      0.26    0.39      0.83
...
```

## Understanding the Results

### High Precision@K, Low Recall@K
- Model is very selective (only high-confidence predictions)
- But misses many relevant chunks
- **Solution**: Lower threshold or improve model sensitivity

### Low Precision@K, High Recall@K
- Model finds most relevant chunks
- But also includes many irrelevant ones
- **Solution**: Increase threshold or improve model specificity

### High nDCG@K
- Model ranks relevant chunks near the top
- Good for applications where order matters

## Integration with Streamlit

You can integrate this into your Streamlit app similar to ClimRetrieve benchmarking:

```python
from app.core.benchmark.s4m_metrics import evaluate_s4m_multiple_models

# In your Streamlit UI
metrics = evaluate_s4m_multiple_models(
    df=df,
    ground_truth_col="relevance",
    model_cols=["model1", "model2", "model3"],
    k_values=[1, 3, 5, 10]
)
```

## Troubleshooting

### "Missing required columns" Error
- Check that your ground truth column name is correct
- Verify model column names exist in the dataset
- Use `--model-cols` to explicitly specify columns

### All metrics are 0.0
- Check threshold value - might be too high/low
- Verify ground truth values are numeric
- Check that model predictions are numeric scores

### Excel file not loading
- Specify sheet name with `--sheet` parameter
- Ensure file is not corrupted
- Try converting to CSV first

## Next Steps

1. Run benchmark on your dataset
2. Compare different models
3. Adjust threshold to optimize for your use case
4. Integrate into Streamlit UI for interactive comparison
