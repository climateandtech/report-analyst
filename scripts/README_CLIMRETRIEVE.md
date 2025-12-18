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
