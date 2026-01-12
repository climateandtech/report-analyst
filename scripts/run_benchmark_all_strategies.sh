#!/bin/bash
# Script to run ClimRetrieve benchmark for multiple strategies
# Usage: ./run_benchmark_all_strategies.sh [strategy1] [strategy2] ...
#        Or edit the STRATEGIES array below to set default strategies

# Default values (edit these if needed)
LABELS_FILE="${LABELS_FILE:-data/climretrieve/labels/ClimRetrieve_ReportLevel_V1.csv}"
RESULTS_DIR="${RESULTS_DIR:-Experiments/Embedding_Experiment}"
K_VALUES="${K_VALUES:-1,3,5,10}"
THRESHOLD="${THRESHOLD:-1}"
GAIN_SCHEME="${GAIN_SCHEME:-exp}"

# Get strategies from command line arguments, or use defaults
if [ $# -gt 0 ]; then
    STRATEGIES=("$@")
else
    # Default strategies - edit this list based on your needs
    STRATEGIES=("IR" "question" "IR_three")
fi

echo "=========================================="
echo "ClimRetrieve Benchmark - Multiple Strategies"
echo "=========================================="
echo "Labels file: $LABELS_FILE"
echo "Results directory: $RESULTS_DIR"
echo "K values: $K_VALUES"
echo "Threshold: $THRESHOLD"
echo "Gain scheme: $GAIN_SCHEME"
echo "Strategies to evaluate: ${STRATEGIES[*]}"
echo "=========================================="
echo ""

# Check if labels file exists
if [ ! -f "$LABELS_FILE" ]; then
    echo "ERROR: Labels file not found: $LABELS_FILE"
    exit 1
fi

# Check if results directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo "ERROR: Results directory not found: $RESULTS_DIR"
    exit 1
fi

# Run benchmark for each strategy
for strategy in "${STRATEGIES[@]}"; do
    echo ""
    echo "----------------------------------------"
    echo "Evaluating strategy: $strategy"
    echo "----------------------------------------"
    
    python3 scripts/benchmark_climretrieve_one_model.py \
        --labels "$LABELS_FILE" \
        --strategy "$strategy" \
        --results-dir "$RESULTS_DIR" \
        --k "$K_VALUES" \
        --thr "$THRESHOLD" \
        --gain "$GAIN_SCHEME"
    
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to evaluate strategy: $strategy"
    fi
    
    echo ""
done

echo "=========================================="
echo "All strategies evaluated!"
echo "=========================================="

