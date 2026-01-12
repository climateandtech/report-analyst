# Quick Start: Running Benchmarks with Your Files

## Your Current Files

Your result files are in `data/climretrieve/results/` with these naming patterns:
- `embedding_results_IR3.csv` → strategy: `IR3`
- `embedding_resultsQuestion.csv` → strategy: `Question`
- `results_IR_all.csv` → strategy: `IR_all`
- `results_IR_simple.csv` → strategy: `IR_simple`

## Solution 1: Use Direct File Paths (Recommended)

Since your files don't follow a standard pattern, use `--results` with direct paths:

```bash
# For embedding_results_IR3.csv
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/embedding_results_IR3.csv \
    --k 1,3,5,10

# For embedding_resultsQuestion.csv
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/embedding_resultsQuestion.csv \
    --k 1,3,5,10

# For results_IR_all.csv
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_Experiment/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/results_IR_all.csv \
    --k 1,3,5,10

# For results_IR_simple.csv
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/results_IR_simple.csv \
    --k 1,3,5,10
```

## Solution 2: Use Strategy Parameter (If Pattern Matches)

The script now tries to match these patterns automatically:
- `results_{strategy}.csv`
- `embedding_results_{strategy}.csv`
- `embedding_results{strategy}.csv`

So you can try:

```bash
# This might work if file is named embedding_results_IR3.csv
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR3 \
    --k 1,3,5,10

# This might work if file is named embedding_resultsQuestion.csv
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy Question \
    --k 1,3,5,10
```

**Note**: The strategy name must match exactly what's in the filename (e.g., `IR3` not `IR_three`).

## Solution 3: Rename Files (Optional)

If you want to use consistent naming, rename your files:

```bash
# Rename to standard pattern
cd data/climretrieve/results/

# Option 1: Keep original names but create symlinks with standard names
ln -s embedding_results_IR3.csv results_IR3.csv
ln -s embedding_resultsQuestion.csv results_question.csv
ln -s results_IR_all.csv results_IR_all.csv
ln -s results_IR_simple.csv results_IR_simple.csv

# Then you can use:
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --strategy IR3 \
    --k 1,3,5,10
```

## Quick Test

Test with one file first:

```bash
python3 scripts/benchmark_climretrieve_one_model.py \
    --labels data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv \
    --results data/climretrieve/results/results_IR_simple.csv \
    --k 1,3,5,10
```

This should work immediately and show you the metrics!

