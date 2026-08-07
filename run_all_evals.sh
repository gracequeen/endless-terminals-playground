#!/usr/bin/env bash
# Runs base model + all 4 checkpoint evals sequentially, logging everything.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
LOG="$REPO/harbor_logs/eval_all_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$REPO/harbor_logs"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

log "=== Starting all evals ==="
log "Repo: $REPO"
log "Log:  $LOG"

# 1. Base model (no checkpoint needed — direct HF hub)
log "--- [1/5] Base model: Qwen/Qwen3.5-4B ---"
bash "$REPO/scripts/run_terminal_bench.sh" \
    --mode base \
    --model Qwen/Qwen3.5-4B \
    --job-name tb-base-qwen3.5-4b \
    --jobs-dir solution_tb \
    2>&1 | tee -a "$LOG"

# Wait for base eval to finish by polling result.json count
log "Waiting for base eval to complete (polling solution_tb/tb-base-qwen3.5-4b)..."
POLL=60; ELAPSED=0; MAX_WAIT=7200
while true; do
    DONE=$(find "$REPO/solution_tb/tb-base-qwen3.5-4b" -name "result.json" 2>/dev/null | wc -l)
    if [[ $DONE -gt 0 ]]; then
        sleep $POLL
        DONE2=$(find "$REPO/solution_tb/tb-base-qwen3.5-4b" -name "result.json" 2>/dev/null | wc -l)
        if [[ $DONE -eq $DONE2 ]]; then log "Base eval complete ($DONE tasks)."; break; fi
    fi
    [[ $ELAPSED -ge $MAX_WAIT ]] && log "WARNING: base eval timed out." && break
    sleep $POLL; ELAPSED=$((ELAPSED + POLL))
done

# 2-5. Checkpoint evals
log "--- [2-5] Checkpoint evals: steps 200 220 240 260 ---"
bash "$REPO/scripts/eval_checkpoints.sh" \
    --s3-path s3://endless-terminals-training/20260726_8192deduped-task_harbor-grpo_qwen3.5-4b_p5_Xsteps \
    --model Qwen/Qwen3.5-4B \
    --steps "200 220 240 260" \
    --job-prefix tb-ckpt \
    --jobs-dir solution_tb \
    2>&1 | tee -a "$LOG"

log "=== All evals complete. Results in $REPO/solution_tb/ ==="
