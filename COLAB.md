# Using report-analyst in Google Colab

This document describes how to install and use the report-analyst package as a library in Google Colab (or any notebook environment).

## Install

**Library only (e.g. Google Colab, notebooks):**

```bash
pip install .
```

Or from Git (if this package lives in a repo subdirectory):

```bash
pip install 'git+https://github.com/<your-org>/<repo>.git#subdirectory=report-analyst'
```

**Full app and backend (Streamlit UI, search backend):** use the full dependency set:

```bash
pip install -r requirements.txt
```

## Using in Google Colab

1. Install the package in a Colab cell:

```python
!pip install git+https://github.com/<your-org>/<repo>.git#subdirectory=report-analyst
```

(Replace `<your-org>` and `<repo>` with your repository. If the repo root is the `report-analyst` folder, use `pip install git+https://github.com/<your-org>/<repo>.git` without `#subdirectory=report-analyst`.)

2. Import and use the benchmark APIs:

```python
from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import load_flexible_dataset_from_csv
from report_analyst.core.benchmark import error_analysis

# Load ground truth and benchmark results from CSV
ground_truth = load_flexible_dataset_from_csv(csv_path="ground_truth.csv")
benchmark_results = load_flexible_dataset_from_csv(csv_path="benchmark_results.csv")

# Run evaluation
engine = EvaluationEngine()
metrics = engine.compare_datasets(ground_truth, benchmark_results, k_values=[1, 5, 10])

# Build error analysis DataFrame
df = error_analysis.build_error_analysis_dataframe(
    ground_truth_dataset=ground_truth,
    benchmark_dataset=benchmark_results,
    top_k=10,
)
```

## Scripts

Scripts in `scripts/` (e.g. `align_benchmark_datasets.py`, `find_missing_relevant_parts.py`) are not installed as commands. To run them, clone the repo and run from the project root (e.g. `python scripts/find_missing_relevant_parts.py ...`), or copy the script into your notebook. `find_missing_relevant_parts` imports from `report_analyst`, so after installing the package it will work when run from a cloned repo.
