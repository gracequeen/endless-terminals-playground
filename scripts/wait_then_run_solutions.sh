#!/usr/bin/env bash
# Wait for task generation process to finish, then launch harbor solution run.
# Usage: bash scripts/wait_then_run_solutions.sh <gen_pid>

set -euo pipefail

GEN_PID="${1:?Usage: $0 <gen_pid>}"
TASK_DIR="harbor_tasks_herodoc_fixed_3k"
JOBS_DIR="solution_grace/claude4.6_sonnet/herodoc_fixed_3k"
JOB_NAME="herodoc_fixed_3k"

echo "[$(date -u)] Waiting for task generation (PID $GEN_PID) to finish..."
while kill -0 "$GEN_PID" 2>/dev/null; do
    sleep 1800
done
echo "[$(date -u)] Task generation complete. Launching harbor solution run..."

.venv/bin/harbor run \
    --agent-import-path aicore_agent:AICoreTerminus2 \
    --model claude_4_6 \
    --path "$TASK_DIR" \
    --n-attempts 8 \
    --jobs-dir "$JOBS_DIR" \
    --n-concurrent 10 \
    --job-name "$JOB_NAME"

echo "[$(date -u)] Harbor solution run complete."
