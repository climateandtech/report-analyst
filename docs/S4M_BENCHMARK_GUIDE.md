# S4M Dataset Benchmarking Guide

## Overview

The S4M dataset contains chunks with ground truth labels (`relevance`/`usefulness`) and predictions from multiple models. This guide explains how to benchmark these models and calculate metrics.

## Dataset Location

The default S4M dataset is located at:
- **File**: `data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv`
- **Note**: The filename contains spaces and a dash, so always use quotes when specifying the path

## Dataset Structure

Your S4M dataset should have:
- **Ground truth columns**: `relevance`, `usefulness` (or similar)
- **Model prediction columns**: Various columns with model predictions/scores
- **Chunk text**: `chunk_text` or similar column
- **Other metadata**: company, industry, criteria, etc.

## Two Evaluation Workflows

S4M benchmarking supports **two different workflows** depending on what you have:

### Workflow 1: Direct Model Predictions (No Embeddings Needed)

**When to use**: You already have model prediction scores in your dataset (e.g., from LLM scoring, rule-based systems, or pre-computed scores).

**What you need**:
- Dataset with ground truth labels (`relevance`/`usefulness`)
- Dataset with model prediction columns (scores or labels)

**Script**: `benchmark_s4m.py` - Directly evaluates existing predictions

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

### Workflow 2: Embedding-Based Similarity (Generate Embeddings)

**When to use**: You want to evaluate embedding-based similarity between chunks and criteria descriptions.

**What you need**:
- Dataset with chunk text and criteria descriptions
- Ground truth labels (`relevance`/`usefulness`)

**Scripts**: 
1. `report_analyst/core/benchmark/s4m_embed_and_compare_criteria.py` - Generate embeddings and similarity scores
2. `s4m_evaluate_embeddings_against_ground_truth.py` - Evaluate similarity scores

```
Chunk Text + Criteria Descriptions
      ↓
  Embed chunks and criteria descriptions
      ↓
  Compute cosine similarity scores
      ↓
  Rank chunks by similarity score
      ↓
  Compare with ground truth labels
      ↓
  Calculate Precision@K, Recall@K, F1@K, nDCG@K
```

## How Criteria Are Handled

In the embedding-based workflow, criteria are handled as follows:

1. **Criteria Descriptions**: Each chunk is associated with a criteria (e.g., "GHG Emissions", "Water Usage") and has a description explaining what that criteria means.

2. **Embedding Process**:
   - Chunks are embedded using the configured embedding model (OpenAI or Ollama)
   - Criteria descriptions are embedded using the same model
   - Each chunk is compared to **its own criteria description** (not all criteria)

3. **Similarity Calculation**:
   - Cosine similarity is computed between each chunk embedding and its corresponding criteria description embedding
   - This produces a similarity score (0-1) indicating how semantically similar the chunk is to the criteria

4. **Evaluation**:
   - Chunks are ranked by similarity score (highest first)
   - This ranking is compared against ground truth labels
   - Metrics measure how well the embedding-based ranking matches human-labeled relevance

## Complete Workflows

### Workflow 1: Direct Model Evaluation (Skip Embeddings)

If your dataset already contains model prediction scores, use this workflow:

#### Step 1: Run Benchmark

```bash
# Single model
python3 scripts/benchmark_s4m.py \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --model-col "relevance_score_gpt-4.1-nano-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 1.0

# Multiple models comparison
python3 scripts/benchmark_s4m.py \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --model-cols \
        "relevance_score_gpt-4.1-nano-2025-04-14" \
        "relevance_score_gpt-4.1-mini-2025-04-14" \
        "relevance_score_gpt-4.1-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 1.0
```

**That's it!** No embeddings needed - the script directly evaluates your existing predictions.

### Workflow 2: Embedding-Based Evaluation (Generate Embeddings)

If you want to evaluate embedding-based similarity, follow these steps:

#### Step 1: Generate Embeddings and Similarity Scores

```bash
# Compute embeddings and similarity scores
python3 -m report_analyst.core.benchmark.s4m_embed_and_compare_criteria \
    --input "data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv" \
    --chunk-col "chunk_text" \
    --criteria-col "criteria" \
    --description-col "description" \
    --output "data/s4m/results/chunks_with_criteria_similarities.csv" \
    --save-embeddings \
    --batch-size 100
```

**What this does**:
- Embeds all chunks using the configured embedding model
- Embeds all criteria descriptions
- Computes cosine similarity between each chunk and its corresponding criteria description
- Saves results to CSV with a new `embedding_similarity_score` column
- Optionally saves embeddings to disk for reuse (`--save-embeddings`)

**Output files**:
- `chunks_with_criteria_similarities.csv` - Chunks with similarity scores
- `chunk_embeddings.csv` - Saved chunk embeddings (if `--save-embeddings`)
- `criteria_embeddings.csv` - Saved criteria embeddings (if `--save-embeddings`)

#### Step 2: Evaluate Similarity Scores Against Ground Truth

```bash
# Evaluate embedding-based similarity scores
python3 scripts/s4m_evaluate_embeddings_against_ground_truth.py \
    --input "data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --output "data/s4m/results/embedding_evaluation_results.csv" \
    --k 1,3,5,10 \
    --threshold 1.0
```

**What this does**:
- Loads the dataset (or uses pre-computed similarity scores)
- Ranks chunks by similarity score
- Compares ranking against ground truth labels
- Calculates Precision@K, Recall@K, F1@K, nDCG@K metrics
- Outputs results to CSV or text format

**Alternative**: Use pre-computed similarity scores from Step 1:

```bash
python3 scripts/s4m_evaluate_embeddings_against_ground_truth.py \
    --input "data/s4m/results/chunks_with_criteria_similarities.csv" \
    --ground-truth-col "relevance" \
    --similarity-col "embedding_similarity_score" \
    --output "data/s4m/results/embedding_evaluation_results.csv" \
    --k 1,3,5,10
```

#### Step 3: Reuse Embeddings (Optional)

If you've already computed embeddings, you can skip embedding computation:

```bash
# Use pre-computed embeddings
python3 -m report_analyst.core.benchmark.s4m_embed_and_compare_criteria \
    --input "data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv" \
    --chunk-embeddings-file "data/s4m/results/chunk_embeddings.csv" \
    --criteria-embeddings-file "data/s4m/results/criteria_embeddings.csv" \
    --output "data/s4m/results/chunks_with_criteria_similarities.csv"
```

This saves time and API costs by reusing previously computed embeddings.

## Usage Examples

### Basic Usage: Single Model (Direct Evaluation)

```bash
python3 scripts/benchmark_s4m.py \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --model-col "relevance_score_gpt-4.1-nano-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 1.0
```

### Multiple Models Comparison

```bash
python3 scripts/benchmark_s4m.py \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --model-cols \
        "relevance_score_gpt-4.1-nano-2025-04-14" \
        "relevance_score_gpt-4.1-mini-2025-04-14" \
        "relevance_score_gpt-4.1-2025-04-14" \
    --k 1,3,5,10 \
    --threshold 1.0
```

### Auto-Detect Model Columns

If you don't specify model columns, the script will auto-detect all columns except the ground truth column:

```bash
python3 scripts/benchmark_s4m.py \
    --data "data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv" \
    --ground-truth-col "relevance" \
    --k 1,3,5,10 \
    --threshold 1.0
```

## Parameters

### `benchmark_s4m.py` Parameters

- `--data`: Path to your S4M dataset (CSV or Excel). **Note**: The default dataset is `data/s4m/test_data_labelled_naive.xlsx - Sheet1.csv` (CSV file with spaces in filename, use quotes)
- `--ground-truth-col`: Column name for ground truth labels (e.g., "relevance" or "usefulness")
- `--model-col`: Single model column name (for single model evaluation)
- `--model-cols`: Multiple model column names (for comparison)
- `--k`: Comma-separated K values (default: "1,3,5,10")
- `--threshold`: Relevance threshold (default: 1.0) - values >= threshold are considered "relevant"
- `--sheet`: Sheet name if Excel file (optional, uses first sheet by default)
- `--group-by`: Columns to group by (e.g., `criteria company`). Default: `['criteria', 'company']`
- `--no-grouping`: Use global evaluation (no grouping)

### `s4m_embed_and_compare_criteria` Parameters

- `--input`: Path to input CSV/Excel file with chunks and criteria
- `--chunk-col`: Column name for chunk text (default: "chunk_text")
- `--criteria-col`: Column name for criteria name (default: "criteria")
- `--description-col`: Column name for criteria description (default: "description")
- `--output`: Path to output CSV file with similarity scores
- `--chunk-embeddings-file`: Path to pre-computed chunk embeddings CSV (optional)
- `--criteria-embeddings-file`: Path to pre-computed criteria embeddings CSV (optional)
- `--save-embeddings`: Save computed embeddings to disk for reuse
- `--batch-size`: Batch size for embedding computation (default: 100)

### `s4m_evaluate_embeddings_against_ground_truth.py` Parameters

- `--input`: Path to input CSV/Excel file (with similarity scores or will compute them)
- `--ground-truth-col`: Column name for ground truth labels (e.g., "relevance")
- `--similarity-col`: Column name for similarity scores (default: "embedding_similarity_score")
- `--output`: Path to output file (CSV or TXT format)
- `--k`: Comma-separated K values (default: "1,3,5,10")
- `--threshold`: Relevance threshold (default: 1.0)
- `--chunk-col`: Column name for chunk text (if computing embeddings)
- `--criteria-col`: Column name for criteria (if computing embeddings)
- `--description-col`: Column name for criteria description (if computing embeddings)

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
Threshold: 1.0
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
Threshold: 1.0
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
from report_analyst.core.benchmark.s4m_metrics import evaluate_s4m_multiple_models

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

## Evaluation Logic Explained

### How Metrics Are Calculated

1. **Ranking**: Chunks are ranked by their prediction/similarity score (highest first)

2. **Grouping** (if enabled):
   - Default: Groups by `['criteria', 'company']`
   - Metrics are calculated **per group**, then **macro-averaged** across all groups
   - This ensures fair evaluation across different criteria and companies

3. **Relevance Threshold**:
   - Values >= threshold are considered "relevant"
   - Default threshold: 1.0 (meaning labels 1 and 2 are relevant, 0 is not)

4. **Top-K Metrics**:
   - **Precision@K**: Of the top K chunks, how many are relevant?
   - **Recall@K**: Of all relevant chunks, how many are in the top K?
   - **F1@K**: Harmonic mean of Precision@K and Recall@K
   - **nDCG@K**: Ranking quality metric (considers position of relevant items)

5. **Macro-Averaging**:
   - Metrics are calculated for each group separately
   - Then averaged across all groups
   - This prevents large groups from dominating the results

### When to Use Grouping vs Global Evaluation

- **With Grouping** (default): Use when you want to evaluate performance per criteria-company pair. This is more granular and prevents bias from imbalanced data.
- **Without Grouping** (`--no-grouping`): Use when you want to evaluate the model's overall ranking performance across the entire dataset.

## Related Scripts

The S4M benchmarking system includes three main scripts:

1. **`scripts/benchmark_s4m.py`** - Direct evaluation of existing model predictions (Workflow 1)
2. **`report_analyst/core/benchmark/s4m_embed_and_compare_criteria.py`** - Generate embeddings and compute similarity scores (Workflow 2, Step 1)
3. **`scripts/s4m_evaluate_embeddings_against_ground_truth.py`** - Evaluate embedding-based similarity scores (Workflow 2, Step 2)

## Configuration

### Embedding Model Configuration

Embeddings are configured via environment variables (`.env` or `ok.env.local`):

```bash
# OpenAI embeddings
OPENAI_API_KEY=your_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# OR Ollama embeddings (local)
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_EMBEDDING_MODEL=ollama/nomic-embed-text
```

The embedding model is automatically selected based on your configuration. OpenAI is used by default if an API key is available.

## Next Steps

1. **Choose your workflow**: Direct evaluation or embedding-based evaluation
2. **Run benchmark** on your dataset
3. **Compare different models** or embedding configurations
4. **Adjust threshold** to optimize for your use case
5. **Experiment with grouping** to understand performance per criteria/company
6. **Integrate into Streamlit UI** for interactive comparison
