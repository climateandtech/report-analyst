# S4M Dataset: What is Ground Truth?

## Ground Truth Definition

**Ground Truth** = Human/expert annotations that represent the "correct" or "true" labels for each chunk.

In your S4M dataset, the ground truth columns are:

### Primary Ground Truth Columns

1. **`relevance`** (Column 12)
   - Human/expert judgment of how relevant a chunk is
   - This is the **primary ground truth** for relevance evaluation
   - Values: Typically numeric (0-1, 0-3, or similar scale)

2. **`usefulness`** (Column 13)
   - Human/expert judgment of how useful a chunk is
   - Alternative/additional ground truth metric
   - Values: Typically numeric (0-1, 0-3, or similar scale)

### What Ground Truth Means

Ground truth represents:
- ✅ **Expert/human judgment** - Not automated, but human-labeled
- ✅ **The "correct" answer** - What the chunk should be labeled as
- ✅ **The standard for comparison** - Models are evaluated against this

## Ground Truth vs Model Predictions

### Ground Truth (Human Labels)
```
relevance          usefulness
    ↓                  ↓
Human/expert      Human/expert
annotations       annotations
```

### Model Predictions (Automated)
```
relevance_score_gpt-4.1-nano-2025-04-14
relevance_score_gpt-4.1-mini-2025-04-14
relevance_score_gpt-4.1-2025-04-14
usefulness_score_gpt-4.1-nano-2025-04-14
usefulness_score_gpt-4.1-mini-2025-04-14
usefulness_score_gpt-4.1-2025-04-14
    ↓
Model predictions
(what models think)
```

## How Evaluation Works

```
1. Ground Truth (relevance/usefulness)
   └─> "This chunk is relevant/useful" (human says)

2. Model Prediction (relevance_score_*)
   └─> "I think this chunk scores 0.85" (model says)

3. Comparison
   └─> How well does model prediction match ground truth?
   
4. Metrics
   └─> Precision, Recall, F1, nDCG measure the match quality
```

## Which Column to Use as Ground Truth?

### For Relevance Evaluation
```bash
--ground-truth-col "relevance"
```

### For Usefulness Evaluation
```bash
--ground-truth-col "usefulness"
```

### Both Can Be Evaluated Separately
You can run two separate evaluations:
1. Evaluate models against `relevance` ground truth
2. Evaluate models against `usefulness` ground truth

## Example: Understanding the Data

```
Chunk Text: "The company aims to reduce emissions by 50% by 2030"

Ground Truth:
  relevance: 1.0        ← Human says: "This is relevant"
  usefulness: 0.8       ← Human says: "This is useful"

Model Predictions:
  relevance_score_gpt-4.1-nano: 0.92  ← Model says: "I think it's 0.92 relevant"
  relevance_score_gpt-4.1-mini: 0.88   ← Model says: "I think it's 0.88 relevant"
  
Evaluation:
  Compare model scores (0.92, 0.88) against ground truth (1.0)
  Calculate how well models match human judgment
```

## Important Notes

1. **Ground truth is fixed** - It doesn't change based on model predictions
2. **Ground truth is authoritative** - It's the "correct" answer to compare against
3. **You can have multiple ground truth metrics** - `relevance` and `usefulness` are both valid
4. **Model predictions are variable** - Different models will have different scores

## In Your Dataset

Based on your column structure:

**Ground Truth Columns:**
- ✅ `relevance` - Use for relevance evaluation
- ✅ `usefulness` - Use for usefulness evaluation

**Model Prediction Columns (NOT ground truth):**
- ❌ `relevance_score_gpt-4.1-nano-2025-04-14` - Model prediction
- ❌ `relevance_score_gpt-4.1-mini-2025-04-14` - Model prediction
- ❌ `relevance_score_gpt-4.1-2025-04-14` - Model prediction
- ❌ `usefulness_score_*` - Model predictions

## Usage Example

```bash
# Evaluate models against relevance ground truth
python3 scripts/benchmark_s4m.py \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --model-cols \
        "relevance_score_gpt-4.1-nano-2025-04-14" \
        "relevance_score_gpt-4.1-mini-2025-04-14" \
    --k 1,3,5,10

# Evaluate models against usefulness ground truth
python3 scripts/benchmark_s4m.py \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "usefulness" \
    --model-cols \
        "usefulness_score_gpt-4.1-nano-2025-04-14" \
        "usefulness_score_gpt-4.1-mini-2025-04-14" \
    --k 1,3,5,10
```

## Summary

**Ground Truth = Human/Expert Labels**
- `relevance` column = Ground truth for relevance
- `usefulness` column = Ground truth for usefulness

**Model Predictions = Automated Scores**
- All `*_score_*` columns = Model predictions to evaluate

The benchmarking compares model predictions against ground truth to measure how well the models match human judgment.
