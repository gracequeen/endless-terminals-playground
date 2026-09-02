#!/usr/bin/env bash
# Runs base model + all 4 checkpoint evals sequentially, logging everything.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$REPO/harbor_logs" "$REPO/output/terminal-bench-eval"
LOG="$REPO/harbor_logs/eval_all_$(date +%Y%m%d_%H%M%S).log"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

# On any exit (clean or error) copy the full log to output/
_on_exit() {
    EXIT_CODE=$?
    OUT_LOG="$REPO/output/terminal-bench-eval/run_log_$(date +%Y%m%d_%H%M%S).log"
    cp "$LOG" "$OUT_LOG" 2>/dev/null || true
    if [[ $EXIT_CODE -ne 0 ]]; then
        echo "[$(date +%H:%M:%S)] ERROR: script exited with code $EXIT_CODE" >> "$OUT_LOG"
        echo "Log saved to: $OUT_LOG"
    fi
}
trap _on_exit EXIT

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

# ── write summary to output/ ──────────────────────────────────────────────────
VENV="$REPO/.venv"
if [[ ! -d "$VENV" ]]; then VENV="$(cd "$REPO/../../.." && pwd)/.venv"; fi

mkdir -p "$REPO/output/terminal-bench-eval"
SUMMARY="$REPO/output/terminal-bench-eval/terminal_bench_qwen3.5-4b_grpo_p5_$(date +%Y%m%d).md"

{
    echo "# Terminal-Bench: Qwen3.5-4B GRPO (p5) vs Base"
    echo ""
    echo "**Date:** $(date -u '+%Y-%m-%d %H:%M UTC')"
    echo "**Dataset:** terminal-bench/terminal-bench@latest (74 tasks)"
    echo "**Model:** Qwen/Qwen3.5-4B"
    echo "**Training:** GRPO on 8192-task harbor dataset, p5.48xlarge (8x H100)"
    echo "**S3:** s3://endless-terminals-training/20260726_8192deduped-task_harbor-grpo_qwen3.5-4b_p5_Xsteps"
    echo ""
    echo "## Results"
    echo ""
    echo "| Run | Step | pass@1 |"
    echo "|-----|------|--------|"

    # Base model
    BASE_AGG="$REPO/solution_tb/tb-base-qwen3.5-4b/aggregate_pass_at_k.json"
    if [[ -f "$BASE_AGG" ]]; then
        P1=$("$VENV/bin/python" -c "import json; d=json.load(open('$BASE_AGG')); print(f\"{d.get('pass@1',0):.3f}\")" 2>/dev/null || echo "n/a")
    else
        P1="n/a"
    fi
    echo "| base | — | $P1 |"

    # Checkpoints
    for STEP in 200 220 240 260; do
        AGG="$REPO/solution_tb/tb-ckpt-step${STEP}/aggregate_pass_at_k.json"
        if [[ -f "$AGG" ]]; then
            P1=$("$VENV/bin/python" -c "import json; d=json.load(open('$AGG')); print(f\"{d.get('pass@1',0):.3f}\")" 2>/dev/null || echo "n/a")
        else
            P1="n/a"
        fi
        echo "| checkpoint | $STEP | $P1 |"
    done

    echo ""
    echo "## Per-run result dirs"
    echo ""
    for JOB in tb-base-qwen3.5-4b tb-ckpt-step200 tb-ckpt-step220 tb-ckpt-step240 tb-ckpt-step260; do
        N=$(find "$REPO/solution_tb/$JOB" -name "result.json" 2>/dev/null | wc -l)
        PASS=$(find "$REPO/solution_tb/$JOB" -name "result.json" 2>/dev/null \
            | xargs grep -l '"reward": 1' 2>/dev/null | wc -l)
        echo "- \`solution_tb/$JOB\`: $N trials, $PASS passed"
    done

    echo ""
    echo "## Log"
    echo "\`\`\`"
    tail -50 "$LOG" 2>/dev/null || true
    echo "\`\`\`"
} > "$SUMMARY"

log "Summary written to: $SUMMARY"

