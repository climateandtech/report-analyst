# Using report-analyst in Google Colab

This guide explains how to use the **benchmarking and diagnostics** parts of
`report-analyst` from Google Colab (or any notebook environment).

You can use it to:

- **Evaluate retrieval systems from CSV files** (Precision@K, Recall@K, F1@K,
  NDCG@K, MAP, MRR).
- **Generate detailed error-analysis tables** for retrieved chunks.
- **Align heterogeneous benchmark CSVs** (e.g. ClimRetrieve) to a common
  internal schema using YAML configs.
- **Run PDF chunk subset diagnostics** to understand how different chunk sizes
  relate to each other.

The examples below focus on **offline evaluation and diagnostics**. They do not
run the Streamlit UI or the full backend.

## 1. Installation in Colab

Install directly from GitHub. For a clean install (e.g. after changing branches), you can uninstall and clear the pip cache first:

```python
!pip uninstall report-analyst -y
!pip cache purge
```

Then install from your repo and branch (replace `<org>`, `<repo>`, and `<branch>` with your values):

```python
# Public repo – no token needed
!pip install --no-cache-dir "git+https://github.com/<org>/<repo>.git@<branch>#subdirectory=report-analyst"
```

If the repo is **private**, use a GitHub personal access token. Store it in Colab secrets or as an environment variable (e.g. `GITHUB_TOKEN`) and do **not** commit it:

```python
import os
token = os.environ.get("GITHUB_TOKEN", "")  # or from Colab secrets
if token:
    !pip install --no-cache-dir "git+https://{token}@github.com/<org>/<repo>.git@<branch>#subdirectory=report-analyst"
else:
    !pip install --no-cache-dir "git+https://github.com/<org>/<repo>.git@<branch>#subdirectory=report-analyst"
```

If the package lives at the repo root (no `report-analyst` subdirectory), omit `#subdirectory=report-analyst`.

Optional boilerplate imports:

```python
import pandas as pd
from pathlib import Path

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import load_flexible_dataset_from_csv
from report_analyst.core.benchmark import error_analysis
from report_analyst.core.benchmark.dataset_mapper import (
    DatasetMapperFactory,
    list_available_dataset_ids,
)
```

If your CSVs are on Google Drive, mount it first:

```python
from google.colab import drive
drive.mount("/content/drive")
```

### Loading datasets from a Git repository

You can load ground truth and benchmark CSVs from raw GitHub URLs. Use **raw** URLs (e.g. `raw.githubusercontent.com`), not blob/view URLs, so you get CSV content, not HTML.

**Public repo:**

```python
import requests

GROUND_TRUTH_URL = "https://raw.githubusercontent.com/<org>/<repo>/<branch>/path/to/your_ground_truth.csv"
BENCHMARK_URL   = "https://raw.githubusercontent.com/<org>/<repo>/<branch>/path/to/your_benchmark.csv"

ground_truth_csv = requests.get(GROUND_TRUTH_URL).text
benchmark_csv    = requests.get(BENCHMARK_URL).text
```

**Private repo:** pass your token in the `Authorization` header (use Colab secrets or env, never hardcode):

```python
import os
import requests

token = os.environ.get("GITHUB_TOKEN", "")  # set in Colab environment or secrets
headers = {"Authorization": f"token {token}"} if token else {}

ground_truth_csv = requests.get(GROUND_TRUTH_URL, headers=headers).text
benchmark_csv    = requests.get(BENCHMARK_URL, headers=headers).text
```

Then pass these **strings** to `load_flexible_dataset_from_csv` using `csv_content=`, as in section 2.

**Alternative – clone the repo:** if you prefer a local path, clone the repo (with token in the URL for private repos) and pass file paths to the loader instead of `csv_content`.

## 2. Core workflow: evaluate retrieval from CSVs

Load ground truth and benchmark from CSV **content** (strings from URLs or file reads), then evaluate with the flexible-dataset API. Use `compare_flexible_datasets`, not `compare_datasets`.

```python
from pathlib import Path
import pandas as pd

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import load_flexible_dataset_from_csv

# If you loaded CSV strings from URLs (section 1), use csv_content=
ground_truth_ds = load_flexible_dataset_from_csv(
    csv_content=ground_truth_csv,
    dataset_name="ground_truth",
)
benchmark_ds = load_flexible_dataset_from_csv(
    csv_content=benchmark_csv,
    dataset_name="benchmark",
)

# If you have local paths instead:
# ground_truth_ds = load_flexible_dataset_from_csv(csv_path="ground_truth_aligned.csv", dataset_name="ground_truth")
# benchmark_ds   = load_flexible_dataset_from_csv(csv_path="benchmark_aligned.csv", dataset_name="benchmark")

engine = EvaluationEngine()
k_values = [1, 3, 5, 10]
metrics = engine.compare_flexible_datasets(ground_truth_ds, benchmark_ds, k_values=k_values)

# Build a metrics table (pivot)
rows = []
for k, v in metrics.precision_at_k.items():
    rows.append({"k": k, "metric": "precision", "value": v})
for k, v in metrics.recall_at_k.items():
    rows.append({"k": k, "metric": "recall", "value": v})
for k, v in metrics.f1_at_k.items():
    rows.append({"k": k, "metric": "f1", "value": v})
for k, v in metrics.ndcg_at_k.items():
    rows.append({"k": k, "metric": "ndcg", "value": v})
rows.append({"k": None, "metric": "MAP", "value": metrics.mean_average_precision})
rows.append({"k": None, "metric": "MRR", "value": metrics.mean_reciprocal_rank})

metrics_df = pd.DataFrame(rows)
metrics_df.pivot(index="metric", columns="k", values="value").round(4)
```

## 3. Error analysis in notebooks

You can build a detailed, per-chunk error-analysis table similar to what the
Streamlit app exports, but directly inside a notebook.

Use the flexible version of the helper so you can pass the same
`BenchmarkDataset` objects used above:

```python
from report_analyst.core.benchmark import error_analysis

top_k = 10
df_error = error_analysis.build_error_analysis_dataframe_from_flexible(
    ground_truth_dataset=ground_truth_ds,
    benchmark_dataset=benchmark_ds,
    top_k=top_k,
)

# Inspect the first rows
display(df_error.head())

# Example: show only non-relevant retrieved chunks for manual inspection
df_false_positives = df_error[df_error["is_really_relevant"] == False]
display(df_false_positives.head())
```

Columns in `df_error` include (depending on your data):

- `report_name`, `question_id`, `question`
- `relevant_part_text` (from ground truth)
- `retrieved_chunk_text` (from benchmark)
- `position_in_top_k`, `model_score`
- `expert_relevance_label`, `is_really_relevant`
- `chunk_id`, `query_id` (identifiers)

## 4. Dataset alignment via DatasetMapper

If your raw CSVs do not yet match the internal benchmark schema, you can align
them using the same mapping logic that powers the CLI and Streamlit UI.

Each dataset has a YAML config under `report_analyst/config/datasets/`. For
example, `climretrieve.yaml` defines how to map the ClimRetrieve CSVs.

```python
import pandas as pd
from report_analyst.core.benchmark.dataset_mapper import (
    DatasetMapperFactory,
    list_available_dataset_ids,
)

print("Available dataset mapping IDs:", list_available_dataset_ids())

dataset_id = "climretrieve"  # or another ID present in config/datasets
mapper = DatasetMapperFactory.get_mapper(dataset_id)

# Raw CSVs from the original benchmark
df_gt_raw = pd.read_csv("climretrieve_ground_truth.csv")
df_bm_raw = pd.read_csv("climretrieve_benchmark.csv")

# Align to the internal schema
df_gt_aligned = mapper.align_ground_truth(df_gt_raw)
df_bm_aligned = mapper.align_benchmark(df_bm_raw)

display(df_gt_aligned.head())
display(df_bm_aligned.head())

# Optionally, save aligned CSVs for later reuse
df_gt_aligned.to_csv("ground_truth_aligned.csv", index=False)
df_bm_aligned.to_csv("benchmark_results_aligned.csv", index=False)
```

You can then feed the aligned CSVs into the evaluation workflow described in
section 2.

## 5. Chunk subset analysis (optional diagnostic)

You can inspect how different chunk sizes relate to each other for a given PDF,
using the same `SentenceSplitter` logic as the analyzer but without embeddings.
This is independent from the IR metrics in `EvaluationEngine`, but can help you
understand whether smaller chunks are strict refinements or often fully
contained inside larger chunks.

### From Python

```python
from report_analyst.core.benchmark.chunk_subset_analysis import (
    analyze_pdf_chunk_subsets,
    analyze_multiple_pdfs_chunk_subsets,
)

# Single PDF, subset ratios between sizes 250, 440, 770
result = analyze_pdf_chunk_subsets(
    pdf_path="my_report.pdf",
    chunk_sizes=[250, 440, 770],
    chunk_overlap=20,
)

# result.summary is a pandas DataFrame with:
#   chunk_size_small, chunk_size_large, num_small, num_large,
#   num_small_subsets, subset_ratio
display(result.summary)

# Multiple PDFs (aggregated statistics across all files)
multi_result = analyze_multiple_pdfs_chunk_subsets(
    pdf_paths=["report1.pdf", "report2.pdf"],
    chunk_sizes=[250, 440, 770],
    chunk_overlap=20,
)
display(multi_result.summary)
```

## 6. Scripts and local usage

Scripts in `scripts/` (for example `align_benchmark_datasets.py`,
`evaluate_benchmark_from_csv.py`, `find_missing_relevant_parts.py`) are **not**
installed as commands when you `pip install` the library.

To run them directly you should:

1. Clone the repository locally.
2. Create a virtual environment and install dependencies.
3. Run the scripts from the project root, for example:

   ```bash
   python scripts/evaluate_benchmark_from_csv.py \
     --reference path/to/ground_truth_aligned.csv \
     --input path/to/benchmark_results_aligned.csv \
     --k-values 1 3 5 10
   ```

In Colab, it is usually more convenient to **call the underlying Python
functions directly** (as shown in the examples above) instead of invoking these
scripts via shell commands.
