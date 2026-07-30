# ClimRetrieve Benchmark Testing

This script downloads and tests ClimRetrieve benchmark datasets from GitHub.

## Datasets

- **Reference Dataset**: Expert-Annotated Relevant Sources Dataset
  - Location: `Expert-Annotated Relevant Sources Dataset/` in the ClimRetrieve repo
  - This is the ground truth dataset
  
- **Input Dataset**: Report-Level Dataset  
  - Location: `Report-Level Dataset/` in the ClimRetrieve repo
  - This is the dataset to evaluate against the reference

## Usage

### Basic Usage (Downloads and Tests)

```bash
python scripts/test_climretrieve_benchmark.py
```

This will:
1. Download datasets from GitHub to `data/climretrieve/`
2. Load both datasets
3. Run evaluation comparison
4. Display metrics

### Using Existing Files

If you already have the datasets downloaded:

```bash
python scripts/test_climretrieve_benchmark.py --skip-download
```

### Providing Custom Paths

```bash
python scripts/test_climretrieve_benchmark.py \
  --reference-path path/to/reference.csv \
  --input-path path/to/input.csv
```

### Custom K Values

```bash
python scripts/test_climretrieve_benchmark.py --k-values 1 5 10 20
```

## Generic CSV Evaluation Script

In addition to the ClimRetrieve-specific script, there is a generic helper for
evaluating **any** pair of benchmark datasets stored as CSV files:

- Script: `scripts/evaluate_benchmark_from_csv.py`
- Loader: `load_flexible_dataset_from_csv` (auto-detects IR vs IE datasets and
  handles flexible column names)
- Engine: `EvaluationEngine` (computes precision@K, recall@K, F1@K, NDCG@K,
  MAP, MRR)

### Expected CSV Formats

The flexible loader supports multiple column name variants and will
auto-detect the dataset type:

- **IR-style (information retrieval) datasets**  
  Typical columns:

  - `query_id` or `question_id` or `qid`
  - `chunk_id` or `chunk` or `cid`
  - `position` or `rank` or `order` (1-indexed)
  - `score` or `relevance_score` or `similarity_score`

- **IE-style (information extraction / QA) datasets**  
  Typical columns:

  - `question_id` or `query_id`
  - `answer` or `analysis` or `text` or `response`
  - Optional: `category` / `class` / `label` / `type`

Anything beyond these required fields is preserved as metadata but does not
affect the metrics.

### Usage with Local CSVs

Run the generic evaluator via `python -m`:

```bash
python -m scripts.evaluate_benchmark_from_csv \
  --reference path/to/reference.csv \
  --input path/to/results.csv \
  --k-values 1 3 5 10 \
  --output metrics.json
```

This will:

1. Load both CSVs with `load_flexible_dataset_from_csv`.
2. Use `EvaluationEngine.compare_flexible_datasets` to compute:
   - Precision@K, Recall@K, F1@K, NDCG@K
   - Mean Average Precision (MAP)
   - Mean Reciprocal Rank (MRR)
3. Print a human-readable table to stdout.
4. Optionally write the metrics as JSON to `--output` (one-level dict with
   per-K metrics and overall MAP/MRR).

## Output

The script will display:
- Dataset inspection (columns, sample rows)
- Loading progress
- Evaluation metrics:
  - Mean Average Precision (MAP)
  - Mean Reciprocal Rank (MRR)
  - Precision@K, Recall@K, F1@K, NDCG@K

## Data Directory

Datasets are stored in `data/climretrieve/` (ignored by git).

The script automatically:
- Creates the directory if it doesn't exist
- Downloads files if they don't exist
- Reuses existing files if present

## Requirements

- `requests` library (already in requirements.txt)
- Internet connection for downloading from GitHub
