#!/bin/bash
# Run one dataset per GPU in parallel for a given model.
# Each GPU gets its own vLLM server on a unique port.
#
# Usage: run_parallel_eval.sh <model_id> <n_attempts> <start_gpu> <start_port>
# Example:
#   # 4B on GPUs 2-6 starting at port 8002, 8 attempts:
#   bash run_parallel_eval.sh "Qwen/Qwen3.5-4B" 8 2 8002
#
#   # 3B on GPUs 2-6 starting at port 8002, 8 attempts:
#   bash run_parallel_eval.sh "Qwen/Qwen2.5-3B" 8 2 8002
set -euo pipefail

MODEL="${1:-Qwen/Qwen3.5-4B}"
N_ATTEMPTS="${2:-8}"
START_GPU="${3:-2}"
START_PORT="${4:-8002}"
N_CONCURRENT=8

REPO="/home/ec2-user/endless-terminals-playground"
DATASETS=(
    "$REPO/harbor_tasks_datagen_test/p1_difficulty"
    "$REPO/harbor_tasks_datagen_test/p3_complexity_axes"
    "$REPO/harbor_tasks_datagen_test/p4_domain_personas"
    "$REPO/harbor_tasks_datagen_test/p5_fixtures"
    "$REPO/harbor_tasks_datagen_test/p_200_hard_4_5"
)
LOG_DIR="$REPO/harbor_logs"
JOBS_DIR="$REPO/baseline_results"
mkdir -p "$LOG_DIR"

MODEL_SLUG=$(echo "$MODEL" | tr '/' '_' | tr '.' '-')
NUM_DATASETS=${#DATASETS[@]}

echo "=============================================="
echo "Parallel eval: $MODEL"
echo "n_attempts: $N_ATTEMPTS  n_concurrent: $N_CONCURRENT"
echo "Datasets: $NUM_DATASETS  GPUs: ${START_GPU}-$((START_GPU + NUM_DATASETS - 1))"
echo "Ports: ${START_PORT}-$((START_PORT + NUM_DATASETS - 1))"
echo "=============================================="

# Start all vLLM servers first
VLLM_PIDS=()
for i in $(seq 0 $((NUM_DATASETS - 1))); do
    GPU=$((START_GPU + i))
    PORT=$((START_PORT + i))
    DATASET="${DATASETS[$i]}"
    DNAME=$(basename "$DATASET")
    VLLM_LOG="$LOG_DIR/vllm_${MODEL_SLUG}_gpu${GPU}_${DNAME}.log"

    echo "Starting vLLM: GPU=$GPU PORT=$PORT model=$MODEL"
    CUDA_VISIBLE_DEVICES=$GPU \
        PATH="/opt/pytorch/bin:$HOME/.local/bin:$PATH" \
        LD_LIBRARY_PATH="/opt/pytorch/cuda/lib:${LD_LIBRARY_PATH:-}" \
        /opt/pytorch/bin/vllm serve "$MODEL" \
            --port "$PORT" \
            --tensor-parallel-size 1 \
            --gpu-memory-utilization 0.6 \
            --max-model-len 8192 \
            --enforce-eager \
            --served-model-name "$MODEL" \
        >> "$VLLM_LOG" 2>&1 &
    VLLM_PIDS+=($!)
done

echo ""
echo "Waiting for all ${NUM_DATASETS} vLLM servers to be ready..."

# Wait for each server to be ready
for i in $(seq 0 $((NUM_DATASETS - 1))); do
    PORT=$((START_PORT + i))
    PID=${VLLM_PIDS[$i]}
    echo -n "  Waiting for port $PORT (PID=$PID)..."
    for attempt in $(seq 1 150); do
        if ! kill -0 $PID 2>/dev/null; then
            echo " DIED (check logs)"
            break
        fi
        if curl -s "http://localhost:${PORT}/v1/models" 2>/dev/null | grep -q "Qwen"; then
            echo " ready (${attempt}s * 2)"
            break
        fi
        sleep 2
    done
done

echo ""
echo "Launching eval jobs in parallel..."

# Launch all eval jobs in parallel
EVAL_PIDS=()
for i in $(seq 0 $((NUM_DATASETS - 1))); do
    GPU=$((START_GPU + i))
    PORT=$((START_PORT + i))
    DATASET="${DATASETS[$i]}"
    DNAME=$(basename "$DATASET")
    JOB="${MODEL_SLUG}__${DNAME}__n${N_ATTEMPTS}"
    EVAL_LOG="$LOG_DIR/eval_${JOB}.log"
    VLLM_URL="http://localhost:${PORT}/v1"

    echo "  Launching: $DNAME  port=$PORT  job=$JOB"
    "$REPO/.venv/bin/python" "$REPO/evaluate_baseline.py" \
        --dataset-path "$DATASET" \
        --model "$MODEL" \
        --n-attempts "$N_ATTEMPTS" \
        --n-concurrent "$N_CONCURRENT" \
        --jobs-dir "$JOBS_DIR" \
        --job-name "$JOB" \
        --output-dir "$REPO/output" \
        --vllm-base-url "$VLLM_URL" \
        >> "$EVAL_LOG" 2>&1 &
    EVAL_PIDS+=($!)
    echo "    PID=${EVAL_PIDS[-1]}  log=$EVAL_LOG"
done

echo ""
echo "All eval jobs launched. Waiting for completion..."
echo "Monitor with: tail -f harbor_logs/eval_${MODEL_SLUG}__*.log"
echo ""

# Wait for all eval jobs to finish
FAILED=0
for i in $(seq 0 $((NUM_DATASETS - 1))); do
    PID=${EVAL_PIDS[$i]}
    DATASET="${DATASETS[$i]}"
    DNAME=$(basename "$DATASET")
    if wait $PID; then
        echo "  [OK] $DNAME"
    else
        echo "  [FAIL] $DNAME (exit code $?)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=============================================="
echo "All evals complete for $MODEL"
echo "Failed: $FAILED / $NUM_DATASETS"
echo "Results in: $REPO/output/"
echo "=============================================="

# Stop all vLLM servers started by this script
echo "Stopping vLLM servers..."
for PID in "${VLLM_PIDS[@]}"; do
    kill "$PID" 2>/dev/null || true
done

# Also kill child processes of vLLM (EngineCore workers)
for i in $(seq 0 $((NUM_DATASETS - 1))); do
    PORT=$((START_PORT + i))
    pkill -f "vllm serve.*--port ${PORT}" 2>/dev/null || true
done

echo "Done."
