#!/bin/bash
# Baseline eval for Claude Opus (4.6) on combined v1+v2+v3hard val set (517 tasks).
# Uses Harbor CLI + AICore (AICoreTerminus2) — no vLLM needed.
#
# Note: claude_opus = claude-4.6-opus (highest opus version configured in aicore_llm_access.py)
set -e

cd "$(dirname "$0")/../.."
source .venv/bin/activate

DATA_DIR="/home/ec2-user/xin/data_harbor_combined"
VAL_JSON="$DATA_DIR/val_task_dirs_v3hard.json"
TASK_LINK_DIR="/tmp/harbor_val_tasks_claude_baseline"
JOBS_DIR="/home/ec2-user/xin/baseline_claude_opus_phase2"
S3_DEST="s3://endless-terminals-training/baselines/claude-opus_v1v2v3hard_val"
JOB_NAME="baseline_claude_opus_v1v2v3hard"
N_CONCURRENT=10

mkdir -p "$JOBS_DIR"

# Create a temp directory with symlinks to the 517 val tasks
echo "Creating symlinks to val tasks..."
rm -rf "$TASK_LINK_DIR" && mkdir -p "$TASK_LINK_DIR"
python3 -c "
import json, os
tasks = json.load(open('$VAL_JSON'))
for t in tasks:
    name = os.path.basename(t)
    link = os.path.join('$TASK_LINK_DIR', name)
    if not os.path.exists(link):
        os.symlink(t, link)
print(f'Linked {len(tasks)} val tasks to $TASK_LINK_DIR')
"

echo "Running Harbor eval with Claude Opus..."
.venv/bin/harbor run \
  --agent-import-path aicore_agent:AICoreTerminus2 \
  --model claude_opus \
  --path "$TASK_LINK_DIR" \
  --n-attempts 2 \
  --jobs-dir "$JOBS_DIR" \
  --job-name "$JOB_NAME" \
  --n-concurrent $N_CONCURRENT \
  2>&1 | tee "$JOBS_DIR/eval_log.log"

# Collect results
echo "Collecting results..."
python scripts/collect_metrics.py \
  --log "$JOBS_DIR/eval_log.log" \
  --export-dir "$JOBS_DIR" \
  --out-dir "$JOBS_DIR/metrics" \
  --s3-prefix "$S3_DEST/metrics"

echo "Uploading to S3..."
aws s3 sync "$JOBS_DIR/" "$S3_DEST/" --no-progress
echo "Done. Results at: $S3_DEST"
