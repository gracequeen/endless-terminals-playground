#!/usr/bin/env bash
# Unified task-generation + solution-generation pipeline with monitoring.
#
# Usage:
#   bash scripts/gen_and_solve.sh [OPTIONS]
#
# Mode (default: both):
#   --gen-only              Run task generation only
#   --sol-only              Run solution generation only (requires --task-out-dir)
#
# Options:
#   --num-tasks N           Number of tasks to generate (default: 1000)
#   --task-out-dir DIR      Output dir for generated tasks (default: harbor_tasks_<timestamp>)
#                           Required for --sol-only
#   --gen-concurrency N     LLM concurrency during task generation (default: 16)
#   --gen-batch-size N      Batch size for task generation (default: 16)
#   --gen-pipeline-depth N  Number of batches to run concurrently (default: 4)
#   --gen-model MODEL       Model for task generation (default: claude_opus)
#   --skip-build            Skip Docker build during task generation
#   --n-attempts N          Solution attempts per task (default: 8)
#   --sol-concurrency N     Concurrent harbor trials (default: 10)
#   --sol-model MODEL       Model for solution generation (default: claude_4_6)
#   --sol-subdir DIR        Subfolder under solution_grace/ (default: claude4.6_sonnet)
#   --job-name NAME         Harbor job name (default: <task-out-dir basename>)
#   --help                  Show this message

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

# ── Defaults ────────────────────────────────────────────────────────────────
MODE="both"           # both | gen-only | sol-only
NUM_TASKS=1000
TASK_OUT_DIR=""
GEN_CONCURRENCY=16
GEN_BATCH_SIZE=16
GEN_PIPELINE_DEPTH=4
GEN_MODEL="claude_opus"
SKIP_BUILD=""
N_ATTEMPTS=8
SOL_CONCURRENCY=10
SOL_MODEL="claude_4_6"          # newest claude sonnet in aicore
SOL_SUBDIR="claude4.6_sonnet"
JOB_NAME=""

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --gen-only)         MODE="gen-only";       shift ;;
        --sol-only)         MODE="sol-only";       shift ;;
        --num-tasks)        NUM_TASKS="$2";       shift 2 ;;
        --task-out-dir)     TASK_OUT_DIR="$2";    shift 2 ;;
        --gen-concurrency)  GEN_CONCURRENCY="$2"; shift 2 ;;
        --gen-batch-size)   GEN_BATCH_SIZE="$2";  shift 2 ;;
        --gen-pipeline-depth) GEN_PIPELINE_DEPTH="$2"; shift 2 ;;
        --gen-model)        GEN_MODEL="$2";       shift 2 ;;
        --skip-build)       SKIP_BUILD="--skip-build"; shift ;;
        --n-attempts)       N_ATTEMPTS="$2";      shift 2 ;;
        --sol-concurrency)  SOL_CONCURRENCY="$2"; shift 2 ;;
        --sol-model)        SOL_MODEL="$2";       shift 2 ;;
        --sol-subdir)       SOL_SUBDIR="$2";      shift 2 ;;
        --job-name)         JOB_NAME="$2";        shift 2 ;;
        --help)
            sed -n '3,30p' "$0"
            exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ── Validation ───────────────────────────────────────────────────────────────
if [[ "$MODE" == "sol-only" && -z "$TASK_OUT_DIR" ]]; then
    echo "Error: --sol-only requires --task-out-dir" >&2
    exit 1
fi


TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
if [[ -z "$TASK_OUT_DIR" ]]; then
    TASK_OUT_DIR="harbor_tasks_${TIMESTAMP}"
fi
if [[ -z "$JOB_NAME" ]]; then
    JOB_NAME="$(basename "$TASK_OUT_DIR")"
fi
JOBS_DIR="solution_grace/${SOL_SUBDIR}"
LOG_DIR="harbor_logs"
mkdir -p "$LOG_DIR"
GEN_LOG="$LOG_DIR/gen_${TIMESTAMP}.log"
SOL_LOG="$LOG_DIR/sol_${TIMESTAMP}.log"
MONITOR_LOG="$LOG_DIR/monitor_${TIMESTAMP}.log"

# ── Helpers ───────────────────────────────────────────────────────────────────
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$MONITOR_LOG"; }

check_gen_status() {
    local pid="$1"
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "dead"
        return
    fi
    local batches done tasks
    batches=$(grep -c "Valid templates:" "$GEN_LOG" 2>/dev/null || echo 0)
    tasks=$(ls "$TASK_OUT_DIR" 2>/dev/null | wc -l || echo 0)
    echo "alive — ${batches} batches done, ${tasks} tasks saved"
}

check_sol_status() {
    local pid="$1"
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "dead"
        return
    fi
    local completed total
    completed=$(find "$JOBS_DIR/$JOB_NAME" -name "reward.txt" 2>/dev/null | wc -l || echo 0)
    total=$(find "$JOBS_DIR/$JOB_NAME" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l || echo 0)
    echo "alive — ${completed}/${total} trials with reward"
}

# ── Step 1: Ensure Docker cleanup loop is running ────────────────────────────
log "Checking Docker cleanup loop..."
if pgrep -f "run_docker_cleanup_loop.sh" > /dev/null; then
    log "Docker cleanup loop already running (PID $(pgrep -f run_docker_cleanup_loop.sh | head -1))."
else
    log "Starting Docker cleanup loop..."
    mkdir -p harbor_logs
    nohup bash scripts/run_docker_cleanup_loop.sh >> harbor_logs/docker_cleanup.log 2>&1 &
    log "Docker cleanup loop started (PID $!)."
fi

# ── Step 2: Task generation ───────────────────────────────────────────────────
if [[ "$MODE" == "both" || "$MODE" == "gen-only" ]]; then
    log "Starting task generation: $NUM_TASKS tasks → $TASK_OUT_DIR"
    log "  gen-model=$GEN_MODEL  concurrency=$GEN_CONCURRENCY  batch-size=$GEN_BATCH_SIZE  pipeline-depth=$GEN_PIPELINE_DEPTH  ${SKIP_BUILD:+--skip-build}"

    nohup .venv/bin/python generate_harbor_tasks.py \
        --num-tasks "$NUM_TASKS" \
        --out-dir "$TASK_OUT_DIR" \
        --model "$GEN_MODEL" \
        --max-concurrency "$GEN_CONCURRENCY" \
        --batch-size "$GEN_BATCH_SIZE" \
        --pipeline-depth "$GEN_PIPELINE_DEPTH" \
        ${SKIP_BUILD} \
        >> "$GEN_LOG" 2>&1 &
    GEN_PID=$!
    log "Task generation PID: $GEN_PID  log: $GEN_LOG"

    sleep 300
    if kill -0 "$GEN_PID" 2>/dev/null; then
        STATUS=$(check_gen_status "$GEN_PID")
        log "[GEN] $STATUS — process alive, safe to leave."
    else
        log "[GEN] process exited within 5 min — check $GEN_LOG for errors."
    fi

    wait "$GEN_PID" || true
    log "Task generation complete. Tasks saved: $(ls "$TASK_OUT_DIR" 2>/dev/null | wc -l)"
fi

if [[ "$MODE" == "gen-only" ]]; then
    log "DONE: Task generation only — exiting."
    exit 0
fi

# ── Step 3: Solution generation ───────────────────────────────────────────────
log "Starting solution generation: $JOBS_DIR  job=$JOB_NAME"
log "  sol-model=$SOL_MODEL  n-attempts=$N_ATTEMPTS  concurrency=$SOL_CONCURRENCY"

nohup .venv/bin/harbor run \
    --agent-import-path generator.aicore_agent:AICoreTerminus2 \
    --model "$SOL_MODEL" \
    --path "$TASK_OUT_DIR" \
    --n-attempts "$N_ATTEMPTS" \
    --jobs-dir "$JOBS_DIR" \
    --n-concurrent "$SOL_CONCURRENCY" \
    --job-name "$JOB_NAME" \
    >> "$SOL_LOG" 2>&1 &
SOL_PID=$!
log "Solution generation PID: $SOL_PID  log: $SOL_LOG"

# ── Step 4: Monitor solution generation, ring when steady ────────────────────
PREV_COMPLETED=0
STEADY_COUNT=0
STEADY_THRESHOLD=3   # 3 consecutive checks with progress = steady
STEADY_REPORTED=0

while kill -0 "$SOL_PID" 2>/dev/null; do
    sleep "$MONITOR_INTERVAL"
    STATUS=$(check_sol_status "$SOL_PID")
    log "[SOL] $STATUS"

    COMPLETED=$(find "$JOBS_DIR/$JOB_NAME" -name "reward.txt" 2>/dev/null | wc -l || echo 0)
    if (( COMPLETED > PREV_COMPLETED )); then
        STEADY_COUNT=$(( STEADY_COUNT + 1 ))
    else
        STEADY_COUNT=0
    fi
    PREV_COMPLETED=$COMPLETED

    if (( STEADY_COUNT >= STEADY_THRESHOLD && STEADY_REPORTED == 0 )); then
        log "READY: Solution generation is steady and making progress — safe to leave."
        STEADY_REPORTED=1
    fi
done

log "Solution generation complete."
log "Final reward count: $(find "$JOBS_DIR/$JOB_NAME" -name "reward.txt" 2>/dev/null | wc -l)"
log "DONE: Full pipeline finished. Results in $JOBS_DIR/$JOB_NAME"
