#!/usr/bin/env bash
# Run Harbor evaluation on a val parquet dataset.
#
# Prepares a local task directory from the parquet (downloading S3 task dirs
# as needed), then runs `harbor run --path` in a tmux window.
#
# Two modes:
#   --mode base        Run the base model directly from HF hub via vLLM
#   --mode checkpoint  Load an HF-format checkpoint, spin up vLLM, then eval
#
# Usage:
#   # Base model eval on val_combined_457_8192
#   bash scripts/eval/eval_val_parquet.sh \
#       --mode base \
#       --model Qwen/Qwen3.5-4B \
#       --parquet data/val_combined_457_8192.parquet
#
#   # Base model eval on val_combined_v1v2v3easy9b
#   bash scripts/eval/eval_val_parquet.sh \
#       --mode base \
#       --model Qwen/Qwen3.5-9B \
#       --parquet data/val_combined_v1v2v3easy9b.parquet \
#       --job-name my-eval-9b-easy
#
#   # Post-training checkpoint eval
#   bash scripts/eval/eval_val_parquet.sh \
#       --mode checkpoint \
#       --model Qwen/Qwen3.5-4B \
#       --checkpoint /path/to/exports/global_step_100 \
#       --parquet data/val_combined_457_8192.parquet
#
# Results land in solution_val/<job-name>/.
# Collect pass@k: python generator/collect_harbor_results.py --jobs-dir solution_val

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="$REPO/.venv"
if [[ ! -d "$VENV" ]]; then
    VENV="$(cd "$REPO/../../.." && pwd)/.venv"
fi

SESSION="endless"
LOG_DIR="$REPO/harbor_logs"
JOBS_DIR="solution_val"
N_CONCURRENT=4
N_ATTEMPTS=4
AGENT="endless_harbor.endless_agent:EndlessAgent"
VLLM_PORT=8100
VLLM_API_KEY="nokey"
BASE_DIR="$HOME/endless-terminals-playground/data"

MODE=""
MODEL=""
CHECKPOINT=""
PARQUET=""
JOB_NAME=""

usage() {
    cat <<EOF
Usage: $0 --mode <base|checkpoint> --model <model> --parquet <file> [options]

Required:
  --mode base|checkpoint   Eval mode
  --model MODEL            HF model name (e.g. Qwen/Qwen3.5-4B)
  --parquet FILE           Path to val parquet file (data/val_combined_*.parquet)

For checkpoint mode:
  --checkpoint DIR         Path to HF-format checkpoint dir (trainer.export_path/global_step_N)

Optional:
  --job-name NAME          Job name (default: val-<mode>-<model-basename>-<parquet-stem>)
  --n-concurrent N         Concurrent Harbor tasks (default: $N_CONCURRENT)
  --n-attempts K           Attempts per task, feeds pass@k (default: $N_ATTEMPTS)
  --jobs-dir DIR           Results directory (default: $JOBS_DIR)
  --base-dir DIR           Local root for downloaded task dirs (default: $BASE_DIR)
  --vllm-port PORT         Local vLLM port for checkpoint mode (default: $VLLM_PORT)
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)         MODE="$2";         shift 2 ;;
        --model)        MODEL="$2";        shift 2 ;;
        --checkpoint)   CHECKPOINT="$2";   shift 2 ;;
        --parquet)      PARQUET="$2";      shift 2 ;;
        --job-name)     JOB_NAME="$2";     shift 2 ;;
        --n-concurrent) N_CONCURRENT="$2"; shift 2 ;;
        --n-attempts)   N_ATTEMPTS="$2";   shift 2 ;;
        --jobs-dir)     JOBS_DIR="$2";     shift 2 ;;
        --base-dir)     BASE_DIR="$2";     shift 2 ;;
        --vllm-port)    VLLM_PORT="$2";    shift 2 ;;
        --help|-h)      usage ;;
        *) echo "Unknown arg: $1"; usage ;;
    esac
done

[[ -z "$MODE" ]]    && echo "Error: --mode is required"    && usage
[[ -z "$MODEL" ]]   && echo "Error: --model is required"   && usage
[[ -z "$PARQUET" ]] && echo "Error: --parquet is required" && usage
[[ ! -f "$PARQUET" ]] && echo "Error: parquet not found: $PARQUET" && exit 1

MODEL_BASENAME="$(basename "$MODEL")"
PARQUET_STEM="$(basename "$PARQUET" .parquet)"
JOB_NAME="${JOB_NAME:-val-${MODE}-${MODEL_BASENAME}-${PARQUET_STEM}}"
LOG_FILE="$LOG_DIR/val_run_${JOB_NAME}.log"
mkdir -p "$LOG_DIR" "$REPO/$JOBS_DIR"

# ── validate mode ─────────────────────────────────────────────────────────────
if [[ "$MODE" == "checkpoint" ]]; then
    [[ -z "$CHECKPOINT" ]] && echo "Error: --checkpoint required for checkpoint mode" && usage
    [[ ! -d "$CHECKPOINT" ]] && echo "Error: checkpoint dir not found: $CHECKPOINT" && exit 1
    MODEL_OR_ENDPOINT="http://localhost:${VLLM_PORT}/v1"
elif [[ "$MODE" == "base" ]]; then
    MODEL_OR_ENDPOINT="$MODEL"
else
    echo "Error: --mode must be 'base' or 'checkpoint'"
    usage
fi

# ── prepare local task directory from parquet ─────────────────────────────────
TASK_DIR="$REPO/data/harbor_tasks_${PARQUET_STEM}"
echo "Preparing local task directory from parquet..."
$VENV/bin/python utility/val_parquet_to_tasks.py \
    --parquet "$PARQUET" \
    --out-dir "$TASK_DIR" \
    --base-dir "$BASE_DIR"
echo "Task directory: $TASK_DIR"

# ── build harbor run command ──────────────────────────────────────────────────
TOKENIZER_KWARG=""
if [[ "$MODE" == "checkpoint" ]]; then
    TOKENIZER_KWARG="--ak tokenizer_model=$MODEL"
fi

ATTEMPTS_ARG="--n-attempts $N_ATTEMPTS"

HARBOR_CMD="$VENV/bin/harbor run \
  --path $TASK_DIR \
  --agent-import-path $AGENT \
  --model $MODEL_OR_ENDPOINT \
  --n-concurrent $N_CONCURRENT \
  --jobs-dir $JOBS_DIR \
  --job-name $JOB_NAME \
  $ATTEMPTS_ARG \
  $TOKENIZER_KWARG"

# ── print summary ─────────────────────────────────────────────────────────────
echo "=================================================="
echo "Val Parquet Evaluation"
echo "=================================================="
echo "Mode:         $MODE"
echo "Model:        $MODEL"
echo "Parquet:      $PARQUET"
echo "Task dir:     $TASK_DIR"
if [[ "$MODE" == "checkpoint" ]]; then
    echo "Checkpoint:   $CHECKPOINT"
    echo "vLLM port:    $VLLM_PORT"
fi
echo "Concurrent:   $N_CONCURRENT"
echo "Attempts:     $N_ATTEMPTS"
echo "Job name:     $JOB_NAME"
echo "Results dir:  $JOBS_DIR"
echo "Log:          $LOG_FILE"
echo "=================================================="

# ── ensure tmux session ───────────────────────────────────────────────────────
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux new-session -d -s "$SESSION" -n "main" -c "$REPO"
fi

# ── build the full command to run inside tmux ─────────────────────────────────
if [[ "$MODE" == "checkpoint" ]]; then
    FULL_CMD=$(cat <<TMUXCMD
cd $REPO
echo "[val-eval] Starting vLLM server from checkpoint: $CHECKPOINT"
CUDA_VISIBLE_DEVICES=1,2,3 $VENV/bin/python -m vllm.entrypoints.openai.api_server \
  --model "$CHECKPOINT" \
  --served-model-name "$MODEL_BASENAME" \
  --port $VLLM_PORT \
  --api-key $VLLM_API_KEY \
  --trust-remote-code \
  --gpu-memory-utilization 0.85 &
VLLM_PID=\$!
echo "[val-eval] vLLM PID: \$VLLM_PID — waiting for server to be ready..."

WAIT_SECS=0
until curl -sf http://localhost:$VLLM_PORT/health >/dev/null 2>&1; do
    sleep 5; WAIT_SECS=\$((WAIT_SECS + 5))
    if ! kill -0 \$VLLM_PID 2>/dev/null; then
        echo "[val-eval] ERROR: vLLM process died after \${WAIT_SECS}s — aborting eval."
        exit 1
    fi
    if [[ \$WAIT_SECS -ge 600 ]]; then
        echo "[val-eval] ERROR: vLLM did not become ready after 600s — killing and aborting."
        kill \$VLLM_PID 2>/dev/null || true
        exit 1
    fi
done
echo "[val-eval] vLLM server ready. Running Harbor eval..."
$HARBOR_CMD 2>&1 | tee $LOG_FILE
echo "[val-eval] Harbor eval done. Stopping vLLM server (PID \$VLLM_PID)..."
kill \$VLLM_PID 2>/dev/null || true
TMUXCMD
)
else
    FULL_CMD="cd $REPO && $HARBOR_CMD 2>&1 | tee $LOG_FILE"
fi

# ── launch in tmux window ─────────────────────────────────────────────────────
WINDOW_NAME="val-${JOB_NAME//\./-}"
WINDOW_IDX=$(tmux new-window -t "$SESSION" -n "$WINDOW_NAME" -c "$REPO" -P -F "#{window_index}")
tmux send-keys -t "$SESSION:$WINDOW_IDX" "$FULL_CMD" Enter

echo ""
echo "Started in tmux window '$WINDOW_NAME' of session '$SESSION'."
echo ""
echo "  Attach:  tmux attach -t $SESSION"
echo "  Switch:  tmux select-window -t $SESSION:$WINDOW_NAME"
echo "  Logs:    tail -f $LOG_FILE"
echo ""
echo "After completion, collect results with:"
echo "  python generator/collect_harbor_results.py --jobs-dir $JOBS_DIR"
