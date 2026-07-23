#!/bin/bash
set -e

# Prepares training parquet from the deduplicated 8192 task dataset.
# Tasks: s3://endless-terminals-training/data/harbor_tasks_8192_deduped/
# Solutions: s3://endless-terminals-training/data/harbor_tasks_solutions_local/
# Run from project root: bash scripts/prepare_data_deduped.sh

cd "$(dirname "$0")/.."
source /tmp/sky/bin/activate

S3_BUCKET="s3://endless-terminals-training"
S3_TASKS="$S3_BUCKET/data/harbor_tasks_8192_deduped"
S3_SOLUTIONS="$S3_BUCKET/data/harbor_tasks_solutions_local"
S3_PREPARED="$S3_BUCKET/prepared_data"

TASKS_DIR="/home/ec2-user/xin/harbor_tasks/tasks_8192_deduped"
OUTPUT_DIR="/tmp/data_work/parquet_deduped"
FINAL_DIR="/tmp/data_work/final_deduped"

mkdir -p "$TASKS_DIR" "$OUTPUT_DIR" "$FINAL_DIR"

echo "=========================================="
echo "Step 1: Downloading deduped tasks from S3..."
echo "=========================================="
aws s3 sync "$S3_TASKS/" "$TASKS_DIR/" --no-progress
TASK_COUNT=$(find "$TASKS_DIR" -name 'instruction.md' | wc -l)
echo "Downloaded $TASK_COUNT tasks."

echo ""
echo "=========================================="
echo "Step 2: Merging solutions into task dirs..."
echo "=========================================="
# Solutions are in harbor_4.6opus_tasks_8192_4.6sonnet_solutions/
# Solution folders named: task_000000_<hash>__<runid>
# Deduped task folders named: task_XXXXXX_<hash>
# Match by the 8-char hash suffix.

SOL_S3_PATH1="s3://endless-terminals-training/data/harbor_4.6opus_tasks_8192_part1-2/harbor_4.6opus_tasks_8192_4.6sonnet_solutions"
SOL_S3_PATH2="s3://endless-terminals-training/data/harbor_4.6opus_tasks_8192_part1-2/harbor_4.6opus_tasks_8192_part2_4.6sonnet_solutions"
SOLUTIONS_CACHE="/tmp/solutions_cache_8192"
mkdir -p "$SOLUTIONS_CACHE"

echo "Downloading solutions part 1 from S3..."
aws s3 sync "$SOL_S3_PATH1/" "$SOLUTIONS_CACHE/" --no-progress \
    --exclude "*" --include "*/result.json"

echo "Downloading solutions part 2 from S3..."
aws s3 sync "$SOL_S3_PATH2/" "$SOLUTIONS_CACHE/" --no-progress \
    --exclude "*" --include "*/result.json"

echo "Building hash -> solution mapping..."
python3.13 - << 'PYEOF'
import os, json, shutil
from pathlib import Path
from collections import defaultdict

tasks_dir = Path('/home/ec2-user/xin/harbor_tasks/tasks_8192_deduped')
sol_cache = Path('/tmp/solutions_cache_8192')

# Build index: hash -> list of result.json paths
hash_to_results = defaultdict(list)
for result_file in sol_cache.rglob('result.json'):
    # folder name: task_000000_<hash>__<runid>
    folder = result_file.parent.name
    parts = folder.split('__')[0]  # task_000000_<hash>
    task_hash = parts.split('_')[-1]  # <hash>
    hash_to_results[task_hash].append(result_file)

print(f'Unique task hashes with solutions: {len(hash_to_results)}')

# For each deduped task, find matching solutions and aggregate
merged = 0
missing = 0
for task_dir in sorted(tasks_dir.iterdir()):
    if not task_dir.is_dir() or task_dir.name == 'dedup_report.json':
        continue
    task_hash = task_dir.name.split('_')[-1]
    sol_dest = task_dir / 'solution' / 'solution.json'
    if sol_dest.exists():
        merged += 1
        continue

    results = hash_to_results.get(task_hash, [])
    if not results:
        missing += 1
        continue

    # Aggregate: count successes across all runs
    num_runs = len(results)
    num_success = 0
    pass_at_k = {}
    for r in results:
        try:
            d = json.loads(r.read_text())
            reward = d.get('verifier_result', {}).get('rewards', {}).get('reward', 0)
            if reward > 0:
                num_success += 1
        except Exception:
            pass

    sol_dest.parent.mkdir(parents=True, exist_ok=True)
    sol_dest.write_text(json.dumps({
        'num_runs': num_runs,
        'num_success': num_success,
        'pass_at_k': {'1': num_success / num_runs if num_runs else 0},
        'results': []
    }))
    merged += 1

print(f'Solutions merged: {merged}, missing: {missing}')
PYEOF

echo ""
echo "=========================================="
echo "Step 3: Generating parquet (solvable tasks only)..."
echo "=========================================="
python3.13 train/prepare_endless.py \
    --task-dir "$TASKS_DIR" \
    --output-dir "$OUTPUT_DIR"

TRAIN_ROWS=$(python3.13 -c "import pandas as pd; df=pd.read_parquet('$OUTPUT_DIR/train.parquet'); print(len(df))")
VAL_ROWS=$(python3.13 -c "import pandas as pd; df=pd.read_parquet('$OUTPUT_DIR/validation.parquet'); print(len(df))")
echo "Train rows: $TRAIN_ROWS, Val rows: $VAL_ROWS"

echo ""
echo "=========================================="
echo "Step 4: Uploading parquet to S3..."
echo "=========================================="
aws s3 cp "$OUTPUT_DIR/train.parquet" \
    "$S3_PREPARED/train_8192_deduped_4929tasks.parquet" --no-progress
aws s3 cp "$OUTPUT_DIR/validation.parquet" \
    "$S3_PREPARED/validation_8192_deduped_4929tasks.parquet" --no-progress

echo ""
echo "Done! Parquet available at:"
echo "  $S3_PREPARED/train_8192_deduped_4929tasks.parquet ($TRAIN_ROWS rows)"
echo "  $S3_PREPARED/validation_8192_deduped_4929tasks.parquet ($VAL_ROWS rows)"
