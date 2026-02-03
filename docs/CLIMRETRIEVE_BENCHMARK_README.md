# ClimRetrieve Benchmark with Report Analyst

A comprehensive guide to calculating retrieval metrics for the ClimRetrieve dataset using the Report Analyst tools.

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Detailed Usage](#detailed-usage)
7. [How It Works](#how-it-works)
8. [Metrics Explained](#metrics-explained)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Usage](#advanced-usage)

---

## Overview

The ClimRetrieve benchmark evaluates information retrieval systems on climate-related corporate reports. This project provides tools to:

- **Generate embeddings** for paragraphs from ground truth data
- **Retrieve relevant paragraphs** using different query strategies (IR, IR3, question)
- **Calculate evaluation metrics** (Precision@K, Recall@K, F1@K, nDCG@K, MAP, MRR)
- **Compare strategies** and analyze retrieval performance

### Key Features

- ✅ **End-to-end workflow**: From embeddings to metrics in one command
- ✅ **Multiple query strategies**: IR, IR3, and question-based queries
- ✅ **Disk-based caching**: Embeddings are cached to avoid recomputation
- ✅ **Per-report indexing**: Efficient embedding management per report
- ✅ **Exact text matching**: Ensures accurate evaluation against ground truth
- ✅ **Comprehensive metrics**: Precision, Recall, F1, nDCG, MAP, MRR

---

## Project Structure

```
report-analyst/
├── scripts/run_climretrieve_benchmark.py  # Main entry point
├── report_analyst/
│   └── core/
│       └── benchmark/
│           ├── climretrieve_runner.py     # Core orchestration logic
│           ├── climretrieve_io.py         # Data loading utilities
│           ├── climretrieve_metrics.py   # Metrics calculation
│           └── climretrieve/
│               ├── labels/                # Ground truth dataset
│               │   └── ClimRetrieve_ReportLevel_V1.csv
│               ├── results/               # Generated results
│               │   ├── results_IR.csv
│               │   ├── results_IR3.csv
│               │   ├── results_question.csv
│               │   ├── evaluation_metrics.csv
│               │   └── evaluation_metrics.json
│               └── cache_embeddings/      # Cached embeddings (.npy files)
│
├── report_analyst/core/
│   ├── Embedding_Search_Queries/         # Query strategy files
│   │   ├── question_with_IR_150len.xlsx
│   │   └── question_with_IR_60len.xlsx
│   ├── reports/                           # PDF reports directory
│   │   └── climretrieve/
│   │       └── [PDF files]
│   └── analyzer.py                        # DocumentAnalyzer (used for chunking)
│
└── docs/
    └── CLIMRETRIEVE_BENCHMARK_README.md   # This file
```

---

## Prerequisites

### Required Files

#### 1. Ground Truth Dataset (Labels File) - REQUIRED

**Location**: `report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`

**What it is**: Expert-annotated ground truth dataset from ClimRetrieve benchmark

**Required columns**:
- `report` - Document/report identifier (e.g., "2022 Microsoft Environmental Sustainability Report.pdf")
- `question` - Question text
- `paragraph` - Paragraph/chunk text or identifier
- `relevance` - Relevance score (integer 0-3, where 3 = highly relevant)

**Example structure**:
```csv
report,question,paragraph,relevance
2022 Microsoft Environmental Sustainability Report.pdf,"Do the environmental/sustainability targets...","2022 Environmental Sustainability Report...",3.0
2022 Microsoft Environmental Sustainability Report.pdf,"Do the environmental/sustainability targets...","Color PaletteNames are TBC...",0.0
```

**Where to get it**:
- Download from ClimRetrieve repository
- Or use existing one: `report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`

#### 2. Query Files - REQUIRED (for generating new results)

**Location**: `report_analyst/core/Embedding_Search_Queries/`

**What it is**: Excel files containing query strategies for each question

**Required columns**: `question`, `IR`, `IR3` (or `IR_three`)

**Default file**: `question_with_IR_150len.xlsx`

**Example structure**:
```excel
question                    | IR                          | IR3        | IR_three
What is the company's...    | company climate strategy   | company climate strategy | ...
```

#### 3. PDF Reports - REQUIRED (for generating new results)

**Location**: `report_analyst/core/reports/climretrieve/`

**What it is**: PDF files for each report mentioned in ground truth

**Requirements**: One PDF per report mentioned in the ground truth dataset

#### 4. Results Files - REQUIRED (if using existing results)

**Location**: `data/climretrieve/results/` or `report_analyst/core/benchmark/climretrieve/results/`

**What it is**: Pre-computed retrieval results (if you already have them)

**Required columns**:
- `report` - Document/report identifier (must match labels)
- `question` - Question text (must match labels)
- `paragraph` - Paragraph/chunk text (must match labels)
- `score` - Retrieval score (numeric, higher = better)

**File naming**: Can be any name, but common patterns:
- `results_{strategy}.csv` (e.g., `results_IR.csv`)
- `embedding_results_{strategy}.csv` (e.g., `embedding_results_IR3.csv`)

**Note**: If you already have result files, you can skip embedding generation and use `--use-existing-results`

### Python Dependencies

```bash
pip install pandas numpy openpyxl requests
```

### Environment Variables

Create `ok.env.local` in the project root:

```bash
# For OpenAI embeddings (recommended)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
USE_OLLAMA_EMBEDDINGS=false

# OR for Ollama embeddings (local)
USE_OLLAMA_EMBEDDINGS=true
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434
```

**Note**: If using Ollama, ensure Ollama is running locally with the embedding model installed:
```bash
ollama pull nomic-embed-text
```

---

## Installation

1. **Clone or navigate to the project**:
   ```bash
   cd /path/to/report-analyst
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify file structure**:
   ```bash
   # Check ground truth exists
   ls report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv

   # Check query files exist
   ls report_analyst/core/Embedding_Search_Queries/

   # Check reports directory exists
   ls report_analyst/core/reports/climretrieve/
   ```

4. **Set up environment variables** (see [Prerequisites](#prerequisites))

---

## Quick Start

### Basic Usage

Run the benchmark with default settings:

```bash
python3 scripts/run_climretrieve_benchmark.py
```

This will:
- Load ground truth from `report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`
- Process all reports and generate embeddings
- Evaluate IR, IR3, and question strategies
- Calculate metrics for K values: 1, 3, 5, 10
- Save results to `report_analyst/core/benchmark/climretrieve/results/`

### Custom Strategies

```bash
python3 scripts/run_climretrieve_benchmark.py --strategies IR question
```

### Custom K Values

```bash
python3 scripts/run_climretrieve_benchmark.py --k 1,5,10,20
```

### Force Recompute

```bash
python3 scripts/run_climretrieve_benchmark.py --force-recompute
```

---

## Detailed Usage

### Command-Line Arguments

```bash
python3 scripts/run_climretrieve_benchmark.py [OPTIONS]
```

#### Query Strategy Options

- `--strategies`: Query strategies to evaluate (default: `IR IR3 question`)
  ```bash
  --strategies IR question
  ```

#### Evaluation Options

- `--k`: K values for evaluation, comma-separated (default: `1,3,5,10`)
  ```bash
  --k 1,3,5,10,20
  ```

- `--top-k`: Number of top chunks to retrieve per query (default: `10`)
  ```bash
  --top-k 20
  ```

#### Chunking Options

- `--chunk-size`: Chunk size for document processing (default: `350`)
  ```bash
  --chunk-size 500
  ```

- `--chunk-overlap`: Chunk overlap for document processing (default: `50`)
  ```bash
  --chunk-overlap 100
  ```

#### Path Options

- `--reports-dir`: Directory containing PDF reports
  ```bash
  --reports-dir /path/to/reports
  ```

- `--ground-truth`: Path to ground truth CSV file
  ```bash
  --ground-truth /path/to/labels.csv
  ```

- `--queries-dir`: Directory containing query Excel files
  ```bash
  --queries-dir /path/to/queries
  ```

- `--output-dir`: Directory to save results
  ```bash
  --output-dir /path/to/output
  ```

#### Caching Options

- `--skip-if-exists`: Skip computation if result files already exist (default: `True`)
  ```bash
  --skip-if-exists
  ```

- `--force-recompute`: Force recomputation even if results exist
  ```bash
  --force-recompute
  ```

- `--clear-embedding-cache`: Clear embedding cache before running
  ```bash
  --clear-embedding-cache
  ```

#### Using Existing Results

- `--use-existing-results`: Use existing results CSV files instead of generating new ones
  ```bash
  --use-existing-results --existing-results-dir data/climretrieve/results
  ```

- `--existing-results-dir`: Directory containing existing results CSV files (default: `data/climretrieve/results`)
  ```bash
  --existing-results-dir /path/to/existing/results
  ```

### Example Commands

#### Example 1: Full Evaluation with Custom Settings

```bash
python3 scripts/run_climretrieve_benchmark.py \
    --strategies IR IR3 question \
    --k 1,3,5,10,20 \
    --top-k 15 \
    --chunk-size 400 \
    --chunk-overlap 50 \
    --force-recompute
```

#### Example 2: Quick Test with Single Strategy

```bash
python3 scripts/run_climretrieve_benchmark.py \
    --strategies question \
    --k 1,5,10 \
    --top-k 5
```

#### Example 3: Using Existing Results

```bash
python3 scripts/run_climretrieve_benchmark.py \
    --use-existing-results \
    --existing-results-dir data/climretrieve/results \
    --strategies IR IR3 question
```

#### Example 4: Custom Paths

```bash
python3 scripts/run_climretrieve_benchmark.py \
    --reports-dir /custom/path/to/reports \
    --ground-truth /custom/path/to/labels.csv \
    --queries-dir /custom/path/to/queries \
    --output-dir /custom/path/to/output
```

---

## How It Works

### Workflow Overview

```
1. Load Ground Truth
   └── Read ClimRetrieve_ReportLevel_V1.csv
       └── Extract: report, question, paragraph, relevance

2. Load Query Strategies
   └── Read Excel files from Embedding_Search_Queries/
       └── Extract: question → IR, IR3, question queries

3. For Each Report:
   ├── Collect all paragraphs from ground truth for this report
   ├── Sanitize paragraphs (remove null bytes, collapse whitespace, truncate to 1500 chars)
   ├── Embed paragraphs (with disk caching)
   └── L2-normalize embeddings

4. For Each (Report, Question) Pair:
   ├── Get query text for strategy (IR/IR3/question)
   ├── Sanitize query text
   ├── Embed query
   ├── L2-normalize query embedding
   ├── Calculate cosine similarity (dot product of normalized vectors)
   ├── Retrieve top-K paragraphs
   └── Store results with original paragraph text

5. Format Results
   └── Create CSV files: results_IR.csv, results_IR3.csv, results_question.csv
       └── Columns: report, question, paragraph, score, rank

6. Evaluate Metrics
   ├── Load results CSV
   ├── Merge with ground truth on (report, question, paragraph)
   ├── Calculate metrics per query:
   │   ├── Precision@K
   │   ├── Recall@K
   │   ├── F1@K
   │   └── nDCG@K
   └── Macro-average across queries → Final metrics

7. Save Results
   └── evaluation_metrics.csv, evaluation_metrics.json
```

### Key Implementation Details

#### 1. Paragraph Pool Selection

- **Source**: Paragraphs come from the ground truth CSV file (not extracted from PDFs)
- **Rationale**: Ensures exact text matching for evaluation
- **Per-report indexing**: Separate embedding index for each report

#### 2. Text Sanitization

Before embedding, text is sanitized:
- Remove null bytes and control characters (except `\n` and `\t`)
- Collapse all whitespace to single spaces
- Hard truncate to 1500 characters

**Important**: Sanitization is applied **only for embedding**, not for matching. Original paragraph text is preserved for exact matching.

#### 3. Embedding Normalization

- **L2 normalization**: All embeddings are normalized to unit length
- **Formula**: `v_normalized = v / ||v||_2`
- **Purpose**: Enables cosine similarity via dot product

#### 4. Similarity Calculation

- **Method**: Cosine similarity via dot product
- **Formula**: `similarity = dot(query_embedding, paragraph_embedding)`
- **Range**: -1 to 1 (typically 0 to 1 for normalized embeddings)

#### 5. Caching Strategy

- **Disk-based caching**: Embeddings saved as `.npy` files
- **Cache key**: SHA1 hash of (model, base_url, paragraphs content, max_chars)
- **Location**: `report_analyst/core/benchmark/climretrieve/cache_embeddings/`
- **Benefits**: Avoids recomputation, saves time and API costs

#### 6. Matching Strategy

- **Exact text matching**: Merge on `(report, question, paragraph)` columns
- **No normalization**: Uses original paragraph text (not sanitized)
- **Rationale**: Ensures accurate relevance assignment from ground truth

---

## Metrics Explained

### Precision@K

**Definition**: Proportion of retrieved items in the top K that are relevant.

**Formula**: `Precision@K = (Number of relevant items in top K) / K`

**Interpretation**: Higher is better. Measures how many of the retrieved items are actually relevant.

**Example**: If K=10 and 7 of the top 10 retrieved paragraphs are relevant, Precision@10 = 0.7

### Recall@K

**Definition**: Proportion of all relevant items that are retrieved in the top K.

**Formula**: `Recall@K = (Number of relevant items in top K) / (Total number of relevant items)`

**Interpretation**: Higher is better. Measures how many of the relevant items were found.

**Example**: If there are 20 relevant paragraphs total and 12 are in the top 10, Recall@10 = 0.6

### F1@K

**Definition**: Harmonic mean of Precision@K and Recall@K.

**Formula**: `F1@K = 2 * (Precision@K * Recall@K) / (Precision@K + Recall@K)`

**Interpretation**: Higher is better. Balances precision and recall.

**Example**: If Precision@10 = 0.7 and Recall@10 = 0.6, F1@10 = 0.65

### nDCG@K (Normalized Discounted Cumulative Gain)

**Definition**: Measures ranking quality, considering position and relevance of retrieved items.

**Formula**:
```
DCG@K = Σ (relevance_i / log2(i + 1)) for i in 1..K
IDCG@K = Ideal DCG (sorted by relevance descending)
nDCG@K = DCG@K / IDCG@K
```

**Gain Scheme**:
- **Exponential** (default): `gain = (2^relevance) - 1`
- **Linear**: `gain = relevance`

**Interpretation**: Higher is better (0 to 1). Measures how well the ranking matches the ideal order.

**Example**: If relevant items appear early in the ranking, nDCG@K will be high.

### MAP (Mean Average Precision)

**Definition**: Average precision across all questions.

**Formula**: `MAP = (1/N) * Σ AveragePrecision_i for i in 1..N queries`

**Interpretation**: Higher is better. Measures overall retrieval quality across all queries.

### MRR (Mean Reciprocal Rank)

**Definition**: Average of reciprocal ranks of the first relevant item.

**Formula**: `MRR = (1/N) * Σ (1 / rank_of_first_relevant) for i in 1..N queries`

**Interpretation**: Higher is better. Measures how quickly the first relevant item is found.

### Relevance Threshold

- **Default**: `relevance_threshold = 1`
- **Meaning**: Items with relevance >= 1 are considered "relevant" for Precision/Recall/F1
- **Relevance Scale**: 0-3 (0=not relevant, 1=somewhat relevant, 2=relevant, 3=highly relevant)

---

## Configuration

### Default Paths

The script uses these default paths (relative to project root):

- **Ground Truth**: `report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`
- **Reports**: `report_analyst/core/reports/climretrieve/`
- **Queries**: `report_analyst/core/Embedding_Search_Queries/`
- **Output**: `report_analyst/core/benchmark/climretrieve/results/`
- **Embedding Cache**: `report_analyst/core/benchmark/climretrieve/cache_embeddings/`

### Default Parameters

- **Strategies**: `["IR", "IR3", "question"]`
- **K values**: `[1, 3, 5, 10]`
- **Top-K retrieval**: `10`
- **Chunk size**: `350`
- **Chunk overlap**: `50`
- **Relevance threshold**: `1`
- **nDCG gain scheme**: `"exp"` (exponential)
- **Max characters for embedding**: `1500`
- **Batch size** (OpenAI): `100` paragraphs per batch

### Environment Variables

See [Prerequisites](#prerequisites) for environment variable setup.

---

## Data Matching Requirements

For benchmarking to work correctly, your results must match the labels:

1. **`report` column**: Must match exactly (e.g., same filename format)
2. **`question` column**: Must match exactly (same question text)
3. **`paragraph` column**: Must match exactly (same paragraph/chunk identifier or text)

The evaluation joins results with labels on `(report, question, paragraph)` columns.

### File Preparation Checklist

**If Starting Fresh**:

1. ✅ **Labels file** (ground truth):
   ```
   Copy: ClimRetrieve Report-Level labels CSV
   To:   report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
   ```

2. ✅ **Query files** (for generating new results):
   ```
   Copy: Excel files with query strategies
   To:   report_analyst/core/Embedding_Search_Queries/
   ```

3. ✅ **PDF reports** (for generating new results):
   ```
   Copy: PDF files for each report
   To:   report_analyst/core/reports/climretrieve/
   ```

**If Using Existing Results**:

1. ✅ **Labels file** (ground truth):
   ```
   Copy: ClimRetrieve Report-Level labels CSV
   To:   report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
   ```

2. ✅ **Results files** (your model outputs):
   ```
   Copy: Your retrieval results CSV files
   To:   data/climretrieve/results/ or report_analyst/core/benchmark/climretrieve/results/
   
   Examples:
   - results_IR.csv
   - results_question.csv
   - results_IR3.csv
   - embedding_results_IR3.csv (any name works)
   ```

### Common Questions

#### Q: Do I need to transform my data?

**A**: Your results CSV must have these columns:
- `report`, `question`, `paragraph` (or custom names via `--paragraph-col`)
- `score` (or custom name via `--score-col`)

The script handles the rest automatically.

#### Q: Can I use different column names?

**A**: Yes! Use parameters:
```bash
--score-col similarity_score
--paragraph-col chunk_id
```

#### Q: What if my files are in a different location?

**A**: Use full paths:
```bash
--labels /absolute/path/to/labels.csv
--results /absolute/path/to/results.csv
```

Or use `--results-dir` for the directory:
```bash
--results-dir /path/to/results/directory
```

#### Q: How many result files do I need?

**A**: One file per strategy/experiment you want to evaluate. You can run the benchmark multiple times with different files.

#### Q: What's the difference between `run_climretrieve_benchmark.py` and `benchmark_climretrieve_one_model.py`?

**A**:
- **`run_climretrieve_benchmark.py`**: End-to-end workflow that generates embeddings, retrieves paragraphs, and calculates metrics. Use this if you want to generate results from scratch.
- **`benchmark_climretrieve_one_model.py`**: Evaluates pre-existing result files. Use this if you already have result CSV files from another system.

---

## Data Matching Requirements

For benchmarking to work correctly, your results must match the labels:

1. **`report` column**: Must match exactly (e.g., same filename format)
2. **`question` column**: Must match exactly (same question text)
3. **`paragraph` column**: Must match exactly (same paragraph/chunk identifier or text)

The evaluation joins results with labels on `(report, question, paragraph)` columns.

### File Preparation Checklist

**If Starting Fresh**:

1. ✅ **Labels file** (ground truth):
   ```
   Copy: ClimRetrieve Report-Level labels CSV
   To:   report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
   ```

2. ✅ **Query files** (for generating new results):
   ```
   Copy: Excel files with query strategies
   To:   report_analyst/core/Embedding_Search_Queries/
   ```

3. ✅ **PDF reports** (for generating new results):
   ```
   Copy: PDF files for each report
   To:   report_analyst/core/reports/climretrieve/
   ```

**If Using Existing Results**:

1. ✅ **Labels file** (ground truth):
   ```
   Copy: ClimRetrieve Report-Level labels CSV
   To:   report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
   ```

2. ✅ **Results files** (your model outputs):
   ```
   Copy: Your retrieval results CSV files
   To:   data/climretrieve/results/ or report_analyst/core/benchmark/climretrieve/results/
   
   Examples:
   - results_IR.csv
   - results_question.csv
   - results_IR3.csv
   - embedding_results_IR3.csv (any name works)
   ```

### Common Questions

#### Q: Do I need to transform my data?

**A**: Your results CSV must have these columns:
- `report`, `question`, `paragraph` (or custom names via `--paragraph-col`)
- `score` (or custom name via `--score-col`)

The script handles the rest automatically.

#### Q: Can I use different column names?

**A**: Yes! Use parameters:
```bash
--score-col similarity_score
--paragraph-col chunk_id
```

#### Q: What if my files are in a different location?

**A**: Use full paths:
```bash
--labels /absolute/path/to/labels.csv
--results /absolute/path/to/results.csv
```

Or use `--results-dir` for the directory:
```bash
--results-dir /path/to/results/directory
```

#### Q: How many result files do I need?

**A**: One file per strategy/experiment you want to evaluate. You can run the benchmark multiple times with different files.

#### Q: What's the difference between `run_climretrieve_benchmark.py` and `benchmark_climretrieve_one_model.py`?

**A**:
- **`run_climretrieve_benchmark.py`**: End-to-end workflow that generates embeddings, retrieves paragraphs, and calculates metrics. Use this if you want to generate results from scratch.
- **`benchmark_climretrieve_one_model.py`**: Evaluates pre-existing result files. Use this if you already have result CSV files from another system.

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'report_analyst'

**Solution**: Run from the project root directory:
```bash
cd /path/to/report-analyst
python3 scripts/run_climretrieve_benchmark.py
```

#### 2. FileNotFoundError: Ground truth file not found

**Solution**: Verify the file exists:
```bash
ls report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
```

Or specify custom path:
```bash
--ground-truth /path/to/your/labels.csv
```

#### 3. FileNotFoundError: Query file not found

**Solution**: Verify query files exist:
```bash
ls report_analyst/core/Embedding_Search_Queries/
```

The script looks for files with columns: `question`, `IR`, `IR3` (or `IR_three`)

#### 4. API Key Not Found

**Solution**: Check `ok.env.local` file:
```bash
cat ok.env.local
```

Ensure it contains:
```bash
OPENAI_API_KEY=your_key_here
```

#### 5. Ollama Connection Error

**Solution**: Ensure Ollama is running:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

#### 6. OpenAI Token Limit Exceeded

**Error**: `BadRequestError: Requested 354478 tokens, max 300000 tokens per request`

**Solution**: The script automatically batches embeddings (100 paragraphs per batch). If you still see this error, it may be due to very long paragraphs. The script truncates to 1500 characters, so this should be rare.

#### 7. All Metrics Are Zero

**Possible Causes**:
- Paragraph text mismatch between results and ground truth
- Missing relevance column in ground truth
- No matches found during merge

**Solution**: Check the merge statistics in the logs:
```
Matches found: X / Total rows: Y
```

If matches are low, verify:
- Paragraph text in results matches ground truth exactly (including whitespace)
- Ground truth CSV has `relevance` column
- Results CSV has `paragraph` column

#### 8. Results Are Different from Reference Implementation

**Check**:
1. **Paragraph deduplication**: Ensure you're not deduplicating paragraphs (the reference uses all paragraphs, including duplicates)
2. **Text normalization**: Ensure you're not normalizing paragraph text before matching (only sanitize for embedding)
3. **Embedding normalization**: Ensure L2 normalization is applied
4. **Query strategy**: Verify you're using the correct query text from Excel files

#### 9. File Not Found Error (benchmark_climretrieve_one_model.py)

**Error**: `FileNotFoundError: Results file not found for strategy 'IR3'`

**Solutions**:
1. Check that your result files exist in the results directory (default: `data/climretrieve/results`)
2. The script automatically tries multiple filename patterns, but if none match, verify your file naming
3. Use `--results-dir` to point to the correct directory if files are elsewhere
4. Use `--results-pattern` to specify a custom pattern (e.g., `embedding_results_{strategy}.csv`)
5. Or use `--results` with the direct file path to bypass pattern matching

#### 10. Missing Columns Error (benchmark_climretrieve_one_model.py)

**Error**: `ValueError: Results file missing columns: {'score'}...`

**Solutions**:
1. Check your CSV file has the required columns: `report`, `question`, `paragraph`, `score`
2. Use `--score-col` and `--paragraph-col` to specify custom column names:
   ```bash
   python3 scripts/benchmark_climretrieve_one_model.py \
       --labels report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
       --strategy IR3 \
       --score-col similarity_score \
       --paragraph-col chunk_id
   ```

---

## Advanced Usage

### Custom Query Strategy Generator

You can create a custom query strategy generator by subclassing `QueryStrategyGenerator`:

```python
from report_analyst.core.benchmark.climretrieve_runner import QueryStrategyGenerator

class MyQueryStrategyGenerator(QueryStrategyGenerator):
    def generate_ir_query(self, question: str) -> str:
        # Your custom IR query generation logic
        return "custom IR query"
    
    def generate_ir3_query(self, question: str) -> str:
        # Your custom IR3 query generation logic
        return "custom IR3 query"
    
    def generate_question_query(self, question: str) -> str:
        # Your custom question query generation logic
        return question
```

Then pass it to `ClimRetrieveRunner`:
```python
runner = ClimRetrieveRunner(query_strategy_generator=MyQueryStrategyGenerator())
```

### Programmatic Usage

You can use `ClimRetrieveRunner` programmatically:

```python
import asyncio
from pathlib import Path
from report_analyst.core.benchmark.climretrieve_runner import ClimRetrieveRunner

async def main():
    runner = ClimRetrieveRunner(
        reports_dir="path/to/reports",
        ground_truth_path="path/to/labels.csv",
        queries_dir="path/to/queries",
        output_dir="path/to/output",
        top_k=10,
        chunk_size=350,
        chunk_overlap=50,
    )
    
    metrics = await runner.run_evaluation(
        strategies=["IR", "IR3", "question"],
        k_values=[1, 3, 5, 10],
        skip_if_results_exist=False,
    )
    
    print(metrics)

asyncio.run(main())
```

### Analyzing Results

Results are saved in two formats:

1. **CSV**: `evaluation_metrics.csv` - Human-readable table
2. **JSON**: `evaluation_metrics.json` - Machine-readable format

Load and analyze:

```python
import pandas as pd
import json

# Load CSV
df = pd.read_csv("report_analyst/core/benchmark/climretrieve/results/evaluation_metrics.csv")
print(df)

# Load JSON
with open("report_analyst/core/benchmark/climretrieve/results/evaluation_metrics.json") as f:
    metrics = json.load(f)
    print(metrics)
```

### Comparing Strategies

To compare strategies, load the metrics and create visualizations:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("report_analyst/core/benchmark/climretrieve/results/evaluation_metrics.csv")

# Plot Precision@K for different strategies
for strategy in ["IR", "IR3", "question"]:
    strategy_df = df[df["strategy"] == strategy]
    plt.plot(strategy_df["k"], strategy_df["precision_at_k"], label=strategy)

plt.xlabel("K")
plt.ylabel("Precision@K")
plt.legend()
plt.title("Precision@K Comparison")
plt.show()
```

---

## Output Files

### Results CSV Files

For each strategy, a results CSV file is generated:
- `results_IR.csv`
- `results_IR3.csv`
- `results_question.csv`

**Format**:
```csv
report,question,paragraph,score,rank
report1.pdf,What is the company's climate strategy?,"Paragraph text...",0.85,1
report1.pdf,What is the company's climate strategy?,"Another paragraph...",0.82,2
...
```

### Metrics Files

- **`evaluation_metrics.csv`**: Table format with all metrics
- **`evaluation_metrics.json`**: JSON format with nested structure

**CSV Format**:
```csv
strategy,k,precision_at_k,recall_at_k,f1_at_k,ndcg_at_k,mean_average_precision,mean_reciprocal_rank
IR,1,0.45,0.12,0.19,0.42,0.35,0.28
IR,3,0.38,0.28,0.32,0.51,0.35,0.28
...
```

**JSON Format**:
```json
{
  "IR": {
    "precision_at_k": {1: 0.45, 3: 0.38, ...},
    "recall_at_k": {1: 0.12, 3: 0.28, ...},
    ...
  },
  ...
}
```

---

## Best Practices

1. **Use caching**: Don't clear embedding cache unless necessary (saves time and money)
2. **Start small**: Test with a single strategy first (`--strategies question`)
3. **Verify inputs**: Check that ground truth and query files are correct before running
4. **Monitor costs**: If using OpenAI, monitor API usage (embeddings are cached after first run)
5. **Compare strategies**: Run all strategies and compare metrics to find the best approach
6. **Check logs**: Review logs for warnings about low match rates or missing data

---

## Quick Reference

### Using run_climretrieve_benchmark.py (End-to-End)

```bash
# Basic usage - generates embeddings and calculates metrics
python3 scripts/run_climretrieve_benchmark.py

# Custom strategies and K values
python3 scripts/run_climretrieve_benchmark.py --strategies IR question --k 1,5,10

# Using existing results (skip embedding generation)
python3 scripts/run_climretrieve_benchmark.py --use-existing-results --existing-results-dir data/climretrieve/results
```

### Using benchmark_climretrieve_one_model.py (Evaluate Existing Results)

```bash
# Single strategy (simplest)
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR3

# Multiple strategies (automated)
for strategy in IR IR3 question; do
    python3 scripts/benchmark_climretrieve_one_model.py \
        --labels report_analyst/core/benchmark/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
        --strategy $strategy \
        --k 1,3,5,10
done

# Custom file path
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels path/to/labels.csv \
    --results path/to/results.csv
```

---

## References

- **ClimRetrieve Dataset**: [Link to dataset documentation]
- **Report Analyst Core**: `report_analyst/core/analyzer.py` - DocumentAnalyzer implementation
- **Benchmark Runner**: `report_analyst/core/benchmark/climretrieve_runner.py` - Core logic
- **Metrics Calculation**: `report_analyst/core/benchmark/climretrieve_metrics.py` - Metrics implementation
- **Alternative Script**: `scripts/benchmark_climretrieve_one_model.py` - For evaluating existing results
- **Visualization**: `scripts/plot_climretrieve_results.py` - Plot metrics visualization
- **Batch Script**: `scripts/run_climretrieve_benchmark_all_strategies.sh` - Run multiple strategies

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the logs for error messages
3. Verify file paths and formats match the expected structure
4. Check the [Common Questions](#common-questions) section

---

## License

[Your license information]

---

**Last Updated**: 2026-01-29

