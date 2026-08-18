#!/bin/bash
# Run baseline eval for one model across all 5 datagen_test subsets sequentially.
# Usage: run_baseline_all.sh <model_id>
set -euo pipefail

MODEL="${1:-Qwen/Qwen2.5-3B}"
REPO="/home/ec2-user/endless-terminals-playground"
DATASETS=(
    "$REPO/harbor_tasks_datagen_test/p1_difficulty"
    "$REPO/harbor_tasks_datagen_test/p3_complexity_axes"
    "$REPO/harbor_tasks_datagen_test/p4_domain_personas"
    "$REPO/harbor_tasks_datagen_test/p5_fixtures"
    "$REPO/harbor_tasks_datagen_test/p_200_hard_4_5"
)
N_ATTEMPTS=4
N_CONCURRENT=8
JOBS_DIR="$REPO/baseline_results"
LOG_DIR="$REPO/harbor_logs"
mkdir -p "$LOG_DIR"

echo "=============================="
echo "Model: $MODEL"
echo "Datasets: ${#DATASETS[@]}"
echo "n-attempts: $N_ATTEMPTS  n-concurrent: $N_CONCURRENT"
echo "=============================="

for DATASET in "${DATASETS[@]}"; do
    DNAME=$(basename "$DATASET")
    MODEL_SLUG=$(echo "$MODEL" | tr '/' '_' | tr '.' '-')
    JOB="${MODEL_SLUG}__${DNAME}"
    LOG="$LOG_DIR/eval_${JOB}.log"

    echo ""
    echo ">>> Starting: $DNAME  (job=$JOB)"
    echo "    Log: $LOG"

    "$REPO/.venv/bin/python" "$REPO/evaluate_baseline.py" \
        --dataset-path "$DATASET" \
        --model "$MODEL" \
        --n-attempts "$N_ATTEMPTS" \
        --n-concurrent "$N_CONCURRENT" \
        --jobs-dir "$JOBS_DIR" \
        --job-name "$JOB" \
        --output-dir "$REPO/output" \
        2>&1 | tee "$LOG"

    echo ">>> Done: $DNAME"
done

echo ""
echo "=============================="
echo "All datasets complete for $MODEL"
echo "=============================="
