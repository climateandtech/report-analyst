# Scripts Organization

This document provides an overview of all scripts in the `scripts/` folder, organized by purpose.

## ClimRetrieve Scripts

Scripts for evaluating retrieval performance on the ClimRetrieve dataset:

- **`benchmark_climretrieve_one_model.py`** - Evaluate pre-existing ClimRetrieve result files against ground truth
- **`test_climretrieve_benchmark.py`** - Test script for ClimRetrieve benchmark (downloads datasets, runs evaluation)
- **`plot_climretrieve_results.py`** - Visualize ClimRetrieve benchmark metrics (Precision@K, Recall@K, F1@K, nDCG@K, MAP, MRR)
- **`run_climretrieve_benchmark_all_strategies.sh`** - Bash script to run ClimRetrieve benchmark for multiple strategies (IR, IR3, question)

## S4M Scripts

Scripts for evaluating classification/ranking performance on the S4M dataset:

- **`benchmark_s4m.py`** - Main benchmarking script for S4M dataset (evaluates model predictions against ground truth)
- **`report_analyst/core/benchmark/s4m_embed_and_compare_criteria.py`** - Embed chunks and criteria descriptions, compute similarity scores
- **`s4m_evaluate_embeddings_against_ground_truth.py`** - Evaluate embedding-based similarity scores against ground truth labels

## Unified Scripts

Scripts that work with both ClimRetrieve and S4M datasets:

- **`benchmark_unified.py`** - Unified benchmarking script that automatically detects dataset format (ClimRetrieve or S4M) and applies appropriate evaluation

## Naming Convention

- **ClimRetrieve scripts**: Include `climretrieve` in the name or are clearly related to ClimRetrieve functionality
- **S4M scripts**: Prefixed with `s4m_` to clearly indicate they are for S4M dataset
- **Unified scripts**: Work with both datasets and are named generically

## Quick Reference

### ClimRetrieve
```bash
# Evaluate existing results
python3 scripts/benchmark_climretrieve_one_model.py --labels <path> --strategy IR

# Run all strategies
./scripts/run_climretrieve_benchmark_all_strategies.sh

# Plot results
python3 scripts/plot_climretrieve_results.py
```

### S4M
```bash
# Benchmark model predictions
python3 scripts/benchmark_s4m.py --data <path> --ground-truth-col relevance --model-col <col>

# Embed and compare
python3 -m report_analyst.core.benchmark.s4m_embed_and_compare_criteria --input <path> --output <path>

# Evaluate embeddings
python3 scripts/s4m_evaluate_embeddings_against_ground_truth.py --input <path> --ground-truth-col relevance
```

### Unified
```bash
# Auto-detect format
python3 scripts/benchmark_unified.py --format auto --labels <path> --results <path>
```
