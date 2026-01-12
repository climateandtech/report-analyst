# Complete Guide: ClimRetrieve Benchmarking

## Overview: How Benchmarking Works

Benchmarking compares your retrieval system's results against expert-annotated ground truth labels to measure performance.

```
┌─────────────────────────────────────────────────────────────┐
│                    BENCHMARKING FLOW                         │
└─────────────────────────────────────────────────────────────┘

1. GROUND TRUTH (Labels)
   └─> Expert-annotated dataset
       Contains: report, question, paragraph, relevance (0-3)

2. YOUR RESULTS (Model Output)
   └─> Your retrieval system's output
       Contains: report, question, paragraph, score

3. EVALUATION
   └─> Compare results vs labels
       Calculate: Precision@K, Recall@K, F1@K, nDCG@K

4. METRICS OUTPUT
   └─> Performance scores for your system
```

## Required Files

### 1. Labels File (Ground Truth) - REQUIRED

**Location**: `data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`

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
- Or use existing one: `data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`

### 2. Results Files (Your Model Output) - REQUIRED

**Location**: `data/climretrieve/results/`

**What it is**: Your retrieval system's output for each strategy/experiment

**Required columns**:
- `report` - Document/report identifier (must match labels)
- `question` - Question text (must match labels)
- `paragraph` - Paragraph/chunk text or identifier (must match labels)
- `score` - Retrieval score (numeric, higher = better)

**Example structure**:
```csv
report,question,paragraph,score,position
2022 Microsoft Environmental Sustainability Report.pdf,"Do the environmental/sustainability targets...","How we workFor any organization's...",18.008659285716462,1
2022 Microsoft Environmental Sustainability Report.pdf,"Do the environmental/sustainability targets...","ForewordEnabling sustainability...",17.04235442308339,2
```

**File naming**: Can be any name, but common patterns:
- `results_{strategy}.csv` (e.g., `results_IR.csv`)
- `embedding_results_{strategy}.csv` (e.g., `embedding_results_IR3.csv`)

## What Files to Copy Into Report Analyst

### If Starting Fresh:

1. **Labels file** (ground truth):
   ```
   Copy: ClimRetrieve Report-Level labels CSV
   To:   data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
   ```

2. **Your result files** (one per strategy):
   ```
   Copy: Your retrieval results CSV files
   To:   data/climretrieve/results/
   
   Examples:
   - results_IR.csv
   - results_question.csv
   - results_IR_three.csv
   - embedding_results_IR3.csv (any name works)
   ```

### File Structure Should Look Like:

```
report-analyst-feature-benchmarking/
├── data/
│   └── climretrieve/
│       ├── labels/
│       │   └── ClimRetrieve_ReportLevel_V1.csv  ← Ground truth (1 file)
│       └── results/
│           ├── results_IR.csv                   ← Your results (many files)
│           ├── results_question.csv
│           ├── results_IR_three.csv
│           └── embedding_results_IR3.csv
├── scripts/
│   └── benchmark_climretrieve_one_model.py      ← Benchmark script
└── app/
    └── core/
        └── benchmark/
            ├── climretrieve_io.py               ← Data loading
            └── climretrieve_metrics.py          ← Evaluation logic
```

## Step-by-Step Workflow

### Step 1: Prepare Your Data

1. **Get labels file**:
   - Download ClimRetrieve Report-Level dataset
   - Place in: `data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`

2. **Generate your results**:
   - Run your retrieval system/experiment for each strategy
   - Each strategy should produce one CSV file
   - Save to: `data/climretrieve/results/`

### Step 2: Run Benchmark

```bash
# Single strategy
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/results_IR.csv \
    --k 1,3,5,10

# Or using strategy parameter (if filename matches pattern)
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR \
    --k 1,3,5,10
```

### Step 3: Interpret Results

The script outputs metrics for each K value:
- **Precision@K**: % of retrieved items that are relevant
- **Recall@K**: % of relevant items that were retrieved
- **F1@K**: Harmonic mean of Precision and Recall
- **nDCG@K**: Normalized Discounted Cumulative Gain (ranking quality)

## Data Matching Requirements

For benchmarking to work, your results must match the labels:

1. **report** column: Must match exactly (e.g., same filename format)
2. **question** column: Must match exactly (same question text)
3. **paragraph** column: Must match exactly (same paragraph/chunk identifier or text)

The evaluation joins results with labels on `(report, question, paragraph)`.

## Common Questions

### Q: Do I need to transform my data?

**A**: Your results CSV must have these columns:
- `report`, `question`, `paragraph` (or custom names via `--paragraph-col`)
- `score` (or custom name via `--score-col`)

The script handles the rest automatically.

### Q: Can I use different column names?

**A**: Yes! Use parameters:
```bash
--score-col similarity_score
--paragraph-col chunk_id
```

### Q: What if my files are in a different location?

**A**: Use full paths:
```bash
--labels /absolute/path/to/labels.csv
--results /absolute/path/to/results.csv
```

Or use `--results-dir` for the directory:
```bash
--results-dir /path/to/results/directory
```

### Q: How many result files do I need?

**A**: One file per strategy/experiment you want to evaluate. You can run the benchmark multiple times with different files.

## Example: Complete Workflow

```bash
# 1. Ensure labels file exists
ls data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv

# 2. List your result files
ls data/climretrieve/results/

# 3. Run benchmark for each strategy
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/results_IR.csv \
    --k 1,3,5,10 > metrics_IR.txt

python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/results_question.csv \
    --k 1,3,5,10 > metrics_question.txt

# 4. Compare results
cat metrics_IR.txt
cat metrics_question.txt
```

## Summary

**What you need to copy**:
1. ✅ **Labels file** (1 file): Ground truth annotations → `data/climretrieve/labels/`
2. ✅ **Results files** (many files): Your retrieval outputs → `data/climretrieve/results/`

**What the code does**:
1. Loads labels (ground truth)
2. Loads your results (model output)
3. Matches them by (report, question, paragraph)
4. Calculates metrics (Precision@K, Recall@K, F1@K, nDCG@K)
5. Outputs performance scores

**That's it!** The benchmark code is already in the repository - you just need the data files.
