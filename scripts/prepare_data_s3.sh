#!/bin/bash
set -e

# Prepares training parquet from two data sources:
#   1. harbor_tasks_claude4.5_opus + harbor_4.5opus_tasks_4.6sonnet_solutions (4 batches)
#   2. harbor_4.6opus_tasks_8192_part1-2/harbor_tasks_8192 + harbor_4.6opus_tasks_8192_4.6sonnet_solutions (flat)
# Run from project root: bash scripts/prepare_data_s3.sh

cd "$(dirname "$0")/.."
source /tmp/sky/bin/activate

S3_BUCKET="s3://endless-terminals-training"
S3_DATA="$S3_BUCKET/data"
S3_PREPARED="$S3_BUCKET/prepared_data"
WORK_DIR="/tmp/data_work"
TASKS_BASE="/home/ec2-user/xin/harbor_tasks"
OUTPUT_DIR="$WORK_DIR/parquet"

mkdir -p "$OUTPUT_DIR" "$TASKS_BASE"

# ============================================================
# SOURCE 1: Claude 4.5 Opus tasks + Claude 4.6 Sonnet solutions (4 batches)
# ============================================================
BATCHES="part2_2-1 part2_2-2 part2_2-3 part2_2-4"

for BATCH in $BATCHES; do
  echo ""
  echo "=========================================="
  echo "Processing 4.5opus batch: $BATCH"
  echo "=========================================="

  TASKS_DIR="$TASKS_BASE/tasks_$BATCH"
  JOBS_DIR="$WORK_DIR/jobs_$BATCH"

  mkdir -p "$TASKS_DIR" "$JOBS_DIR"

  echo "[1/4] Downloading tasks..."
  aws s3 sync "$S3_DATA/harbor_tasks_claude4.5_opus/harbor_tasks_$BATCH/" "$TASKS_DIR/" --no-progress

  echo "[2/4] Downloading solutions..."
  aws s3 sync "$S3_DATA/harbor_4.5opus_tasks_4.6sonnet_solutions/harbor_tasks_$BATCH/" "$JOBS_DIR/" --no-progress
  echo '{}' > "$JOBS_DIR/config.json"

  echo "[3/4] Merging solutions into tasks..."
  python3.13 collect_harbor_results.py --jobs-dir "$JOBS_DIR" --tasks-dir "$TASKS_DIR"

  echo "[4/4] Preparing parquet..."
  python3.13 train/prepare_endless.py     --task-dir "$TASKS_DIR"     --output-dir "$OUTPUT_DIR/4.5opus_$BATCH"

  echo "Batch $BATCH done. Train: $(python3.13 -c "import pandas as pd; df=pd.read_parquet('$OUTPUT_DIR/4.5opus_$BATCH/train.parquet'); print(len(df))") rows"

  rm -rf "$JOBS_DIR"
  echo "Cleaned up jobs for $BATCH (tasks kept at $TASKS_DIR)"
done

# ============================================================
# SOURCE 2: Claude 4.6 Opus 8192 tasks + solutions (flat structure, part 1)
# ============================================================
echo ""
echo "=========================================="
echo "Processing 8192 tasks (part 1)"
echo "=========================================="

TASKS_8192_DIR="$TASKS_BASE/tasks_8192"
JOBS_8192_DIR="$WORK_DIR/jobs_8192"

mkdir -p "$TASKS_8192_DIR" "$JOBS_8192_DIR"

echo "[1/4] Downloading 8192 tasks..."
aws s3 sync "$S3_DATA/harbor_4.6opus_tasks_8192_part1-2/harbor_tasks_8192/" "$TASKS_8192_DIR/" --no-progress

echo "[2/4] Downloading 8192 solutions..."
aws s3 sync "$S3_DATA/harbor_4.6opus_tasks_8192_part1-2/harbor_4.6opus_tasks_8192_4.6sonnet_solutions/" "$JOBS_8192_DIR/" --no-progress
echo '{}' > "$JOBS_8192_DIR/config.json"

echo "[3/4] Merging solutions into tasks..."
python3.13 collect_harbor_results.py --jobs-dir "$JOBS_8192_DIR" --tasks-dir "$TASKS_8192_DIR"

echo "[4/4] Preparing parquet..."
python3.13 train/prepare_endless.py   --task-dir "$TASKS_8192_DIR"   --output-dir "$OUTPUT_DIR/8192"

echo "8192 done. Train: $(python3.13 -c "import pandas as pd; df=pd.read_parquet('$OUTPUT_DIR/8192/train.parquet'); print(len(df))") rows"

rm -rf "$JOBS_8192_DIR"
echo "Cleaned up 8192 jobs (tasks kept at $TASKS_8192_DIR)"

# ============================================================
# Merge all parquets — 90/10 train/val split
# ============================================================
echo ""
echo "=========================================="
echo "Merging all batches into final parquet..."
echo "=========================================="
python3.13 - << 'PYEOF'
import pandas as pd
import os
from pathlib import Path

output_dir = "/tmp/data_work/parquet"
final_dir = "/tmp/data_work/final"
os.makedirs(final_dir, exist_ok=True)

train_dfs, val_dfs = [], []
for batch_dir in sorted(Path(output_dir).iterdir()):
    train_f = batch_dir / "train.parquet"
    val_f = batch_dir / "validation.parquet"
    if train_f.exists():
        train_dfs.append(pd.read_parquet(train_f))
    if val_f.exists():
        val_dfs.append(pd.read_parquet(val_f))

all_data = pd.concat(train_dfs + val_dfs, ignore_index=True).sample(frac=1, random_state=42)
split = int(len(all_data) * 0.9)
train = all_data[:split]
val = all_data[split:]

train.to_parquet(f"{final_dir}/train_4.5opus-8192-task_4.6sonnet-sol_combined.parquet", index=False)
val.to_parquet(f"{final_dir}/validation_4.5opus-8192-task_4.6sonnet-sol_combined.parquet", index=False)
print(f"Final train: {len(train)} rows, val: {len(val)} rows")
PYEOF

# Upload final parquet to S3
echo "Uploading parquet to S3..."
aws s3 sync /tmp/data_work/final/ "$S3_PREPARED/" --no-progress

echo ""
echo "Done! Parquet available at $S3_PREPARED/"
