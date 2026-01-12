# How to Run ClimRetrieve Benchmark for Different Strategies

This guide explains how to run the benchmark experiment to get metrics for different strategies.

## Prerequisites

1. **Labels file** (ground truth): `data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv`
2. **Result files** (your model outputs): Should be in `Experiments/Embedding_Experiment/` with names like:
   - `results_IR.csv`
   - `results_question.csv`
   - `results_IR_three.csv`
   - etc.

## Method 1: Run Single Strategy

Run the benchmark for one strategy at a time:

```bash
# Basic usage - IR strategy
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR \
    --k 1,3,5,10 \
    --thr 1 \
    --gain exp

# Another strategy - IR_three
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR_three \
    --k 1,3,5,10

# Custom results directory
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy question \
    --results-dir /path/to/your/results \
    --k 1,3,5,10
```

### Parameters Explained

- `--labels`: Path to the ground truth labels CSV file
- `--strategy`: Strategy name (must match your result file name: `results_{strategy}.csv`)
- `--results-dir`: Directory containing result files (default: `Experiments/Embedding_Experiment`)
- `--k`: Comma-separated K values for evaluation (default: `1,3,5,10`)
- `--thr`: Relevance threshold - items with relevance >= this are considered relevant (default: `1`)
- `--gain`: nDCG gain scheme - "exp" or "linear" (default: "exp")

### Output

The script prints metrics for each K value:
- **Precision@K**: Percentage of retrieved items that are relevant
- **Recall@K**: Percentage of relevant items that were retrieved
- **F1@K**: Harmonic mean of Precision and Recall
- **nDCG@K**: Normalized Discounted Cumulative Gain

Example output:
```
=== ClimRetrieve Benchmark (one model run) ===
labels:  data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv
strategy: IR_three
results:  Experiments/Embedding_Experiment/results_IR_three.csv
K:       [1, 3, 5, 10]
thr:     1
gain:    exp

Precision@K: {1: 0.45, 3: 0.38, 5: 0.35, 10: 0.32}
Recall@K:    {1: 0.12, 3: 0.28, 5: 0.42, 10: 0.58}
F1@K:        {1: 0.19, 3: 0.32, 5: 0.38, 10: 0.41}
nDCG@K:      {1: 0.42, 3: 0.51, 5: 0.55, 10: 0.59}
```

## Method 2: Run Multiple Strategies (Bash Script)

Use the provided script to run benchmarks for multiple strategies at once:

```bash
# Run with default strategies (IR, question, IR_three)
./scripts/run_benchmark_all_strategies.sh

# Run with specific strategies as arguments
./scripts/run_benchmark_all_strategies.sh IR question IR_three IR_two

# Or edit the script to change default strategies
# Edit the STRATEGIES array in the script
```

### Customizing the Script

You can customize the script by setting environment variables:

```bash
# Set custom paths/values via environment variables
export LABELS_FILE="data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv"
export RESULTS_DIR="Experiments/Embedding_Experiment"
export K_VALUES="1,3,5,10"
export THRESHOLD="1"
export GAIN_SCHEME="exp"

# Then run with strategies
./scripts/run_benchmark_all_strategies.sh IR question IR_three
```

Or edit the script directly to change defaults (see the `# Default values` section in the script).

## Method 3: Run Multiple Strategies (Python Loop)

Create a simple Python script to run multiple strategies:

```python
#!/usr/bin/env python3
import subprocess
import sys

strategies = ["IR", "question", "IR_three", "IR_two"]
labels_file = "data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv"
results_dir = "Experiments/Embedding_Experiment"
k_values = "1,3,5,10"

for strategy in strategies:
    print(f"\n{'='*60}")
    print(f"Evaluating strategy: {strategy}")
    print('='*60)
    
    cmd = [
        sys.executable,
        "scripts/benchmark_climretrieve_one_model.py",
        "--labels", labels_file,
        "--strategy", strategy,
        "--results-dir", results_dir,
        "--k", k_values,
        "--thr", "1",
        "--gain", "exp"
    ]
    
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"ERROR: Failed to evaluate {strategy}")
```

Save as `run_multiple_strategies.py` and run:
```bash
python3 run_multiple_strategies.py
```

## Method 4: Using Direct File Paths

If your files don't follow the `results_{strategy}.csv` naming pattern, you can use direct file paths:

```bash
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results Experiments/Embedding_Experiment/custom_filename.csv \
    --k 1,3,5,10
```

## Common Workflow

1. **Generate result files** using your ClimRetrieve experiment:
   ```bash
   python -m Experiments.Embedding_Experiment.run_embedding_reportlvl \
       --reportlevel Report-Level-Dataset/ClimRetrieve_ReportLevel_V1.csv \
       --query-strategy IR_three \
       --out Experiments/Embedding_Experiment/results_IR_three.csv
   ```

2. **Run benchmark** for that strategy:
   ```bash
   python3 scripts/benchmark_climretrieve_one_model.py \
       --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
       --strategy IR_three \
       --k 1,3,5,10
   ```

3. **Repeat** for other strategies, or use the bash script to run all at once.

## Troubleshooting

### File Not Found Error

If you get an error like:
```
FileNotFoundError: Results file not found for strategy 'IR_three' in Experiments/Embedding_Experiment
```

**Solutions**:
1. Check that your result files exist in the results directory
2. Verify the file naming matches `results_{strategy}.csv`
3. Use `--results-dir` to point to the correct directory
4. Or use `--results` with the direct file path

### Missing Columns Error

If you get:
```
ValueError: Results file missing columns: {'score'}...
```

**Solutions**:
1. Check your CSV file has the required columns: `report`, `question`, `paragraph`, `score`
2. Use `--score-col` and `--paragraph-col` to specify custom column names:
   ```bash
   python3 scripts/benchmark_climretrieve_one_model.py \
       --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
       --strategy IR_three \
       --score-col similarity_score \
       --paragraph-col chunk_id
   ```

## Comparing Strategies

To compare multiple strategies, you can:

1. **Run each strategy separately** and note the metrics
2. **Use the bash script** to run all at once and compare outputs
3. **Save outputs to files** for later comparison:
   ```bash
   python3 scripts/benchmark_climretrieve_one_model.py \
       --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
       --strategy IR_three \
       --k 1,3,5,10 > results_IR_three_metrics.txt
   ```

## Quick Reference

```bash
# Single strategy (simplest)
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR_three

# Multiple strategies (automated)
./scripts/run_benchmark_all_strategies.sh

# Custom file path
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels path/to/labels.csv \
    --results path/to/results.csv
```

