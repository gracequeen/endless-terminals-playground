#!/bin/bash
# Baseline eval for Claude Opus (4.6) on all 6 dataset splits:
#   train_v1 (~406 tasks, sampled 500), train_v2 (sampled 500), train_v3 (sampled 500)
#   val_v1 (51), val_v2 (100), val_v3 (~366)
# Uses Harbor CLI + AICore (AICoreTerminus2) — no vLLM needed.
#
# Prereq: run scripts/prepare_data_v3hard.sh to produce task_dirs_*.json files.
# Prereq: set AICORE_* env vars before running.
set -e

cd "$(dirname "$0")/../.."
source .venv/bin/activate

DATA_DIR="/home/ec2-user/xin/data_harbor_combined"
JOBS_DIR="/home/ec2-user/xin/baseline_claude_opus_splits"
S3_BASE="s3://endless-terminals-training/baselines/claude-opus_splits"
N_CONCURRENT=10

MODE="${MODE:-val}"  # val | train | all
case "$MODE" in
  val)   SPLITS="val_v1 val_v2 val_v3" ;;
  train) SPLITS="train_v1 train_v2 train_v3" ;;
  *)     SPLITS="val_v1 val_v2 val_v3 train_v1 train_v2 train_v3" ;;
esac

mkdir -p "$JOBS_DIR"
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker network prune -f

for SPLIT in $SPLITS; do
  JSON="$DATA_DIR/task_dirs_${SPLIT}.json"
  if [ ! -f "$JSON" ]; then
    echo "Skip $SPLIT: $JSON not found. Run prepare_data_v3hard.sh first."
    continue
  fi

  TASK_LINK_DIR="/tmp/harbor_claude_baseline_${SPLIT}"
  JOB_NAME="baseline_claude_${SPLIT}"
  S3_DEST="$S3_BASE/$SPLIT"

  echo ""
  echo "=== Evaluating split: $SPLIT ==="

  rm -rf "$TASK_LINK_DIR" && mkdir -p "$TASK_LINK_DIR"
  python3 -c "
import json, os
tasks = json.load(open('$JSON'))
linked = 0
for t in tasks:
    if os.path.isdir(t):
        link = os.path.join('$TASK_LINK_DIR', os.path.basename(t))
        if not os.path.exists(link):
            os.symlink(t, link)
        linked += 1
print(f'Linked {linked}/{len(tasks)} tasks to $TASK_LINK_DIR')
"

  PYTHONPATH="$PWD/generator:$PYTHONPATH" .venv/bin/harbor run \
    --agent-import-path aicore_agent:AICoreTerminus2 \
    --model claude_opus \
    --path "$TASK_LINK_DIR" \
    --n-attempts 2 \
    --jobs-dir "$JOBS_DIR" \
    --job-name "$JOB_NAME" \
    --n-concurrent $N_CONCURRENT \
    2>&1 | tee "$JOBS_DIR/${SPLIT}_log.log"

  # Collect solve rate
  python3.13 generator/collect_harbor_results.py \
    --jobs-dir "$JOBS_DIR/$JOB_NAME" \
    --out "$JOBS_DIR/${SPLIT}_results.json" || true

  aws s3 cp "$JOBS_DIR/${SPLIT}_log.log" "$S3_DEST/eval_log.log" --no-progress
  [ -f "$JOBS_DIR/${SPLIT}_results.json" ] && \
    aws s3 cp "$JOBS_DIR/${SPLIT}_results.json" "$S3_DEST/results.json" --no-progress
  echo "Done $SPLIT → $S3_DEST"
done

echo ""
echo "=== All splits done ==="
echo "Results at: $S3_BASE"
echo "Collect all results with:"
for SPLIT in $SPLITS; do
  echo "  python generator/collect_harbor_results.py --jobs-dir $JOBS_DIR/baseline_claude_${SPLIT}"
done
