#!/bin/bash
# Download all task dirs (v1, v2, v3) and generate per-split JSON files for eval.
# Run this once before any baseline eval script.
#
# Produces in $DATA_DIR:
#   task_dirs_{train,val}_{v1,v2,v3}.json  — 6 per-split lists (train sampled to 500)
#   task_dirs_{train,val}_combined.json    — all splits merged
set -e

cd "$(dirname "$0")/.."
source /tmp/sky/bin/activate

TASKS_DIR_V1="/home/ec2-user/xin/harbor_tasks_457"
TASKS_DIR_V2="/home/ec2-user/xin/harbor_tasks_8192_deduped"
TASKS_DIR_V3="/home/ec2-user/xin/harbor_tasks_v3hard"
DATA_DIR="/home/ec2-user/xin/data_harbor_combined"

mkdir -p "$TASKS_DIR_V1" "$TASKS_DIR_V2" "$TASKS_DIR_V3" "$DATA_DIR"

# ── sync all task dirs from S3 ────────────────────────────────────────────────
echo "Syncing v1 tasks..."
aws s3 sync s3://endless-terminals-training/data/harbor_4.5opus_tasks/ \
  "$TASKS_DIR_V1/" --no-progress
echo "v1: $(find $TASKS_DIR_V1 -maxdepth 1 -mindepth 1 -type d | wc -l) task dirs"

echo "Syncing v2 tasks..."
aws s3 sync s3://endless-terminals-training/data/harbor_tasks_8192_deduped/ \
  "$TASKS_DIR_V2/" --no-progress
echo "v2: $(find $TASKS_DIR_V2 -maxdepth 1 -mindepth 1 -type d | wc -l) task dirs"

echo "Syncing v3 tasks..."
aws s3 sync s3://endless-terminals-training/data/harbor_4.8opus_tasks_v3_internet_access_config/ \
  "$TASKS_DIR_V3/" --no-progress
echo "v3: $(find $TASKS_DIR_V3 -maxdepth 1 -mindepth 1 -type d | wc -l) task dirs"

# ── ensure v1+v2 parquets present (needed to read train/val splits) ───────────
if [ ! -f "$DATA_DIR/train_combined_457_8192.parquet" ]; then
  echo "Downloading v1+v2 parquets..."
  aws s3 cp s3://endless-terminals-training/prepared_data/train_combined_457_8192.parquet \
    "$DATA_DIR/train_combined_457_8192.parquet" --no-progress
  aws s3 cp s3://endless-terminals-training/prepared_data/val_combined_457_8192.parquet \
    "$DATA_DIR/val_combined_457_8192.parquet" --no-progress
fi

# ── generate per-split JSON files ────────────────────────────────────────────
python3.13 - "$TASKS_DIR_V1" "$TASKS_DIR_V2" "$TASKS_DIR_V3" "$DATA_DIR" <<'PYEOF'
import sys, os, json
import pandas as pd
import numpy as np

v1_dir  = sys.argv[1]
v2_dir  = sys.argv[2]
v3_dir  = sys.argv[3]
data_dir = sys.argv[4]

# ── scan disk for actual task dirs (has task.toml) ────────────────────────────
def find_task_dirs(base_dir):
    """Walk base_dir and return all dirs containing task.toml."""
    found = []
    for root, dirs, files in os.walk(base_dir):
        if 'task.toml' in files:
            found.append(root)
            dirs.clear()  # don't descend into task dirs
    return sorted(found)

print("Scanning v1 task dirs on disk...")
all_v1 = find_task_dirs(v1_dir)
print(f"  found {len(all_v1)} v1 tasks")

print("Scanning v2 task dirs on disk...")
all_v2 = find_task_dirs(v2_dir)
print(f"  found {len(all_v2)} v2 tasks")

# ── v1 + v2: read train/val splits from parquets to get task IDs ─────────────
train_v1v2 = pd.read_parquet(os.path.join(data_dir, "train_combined_457_8192.parquet"))
val_v1v2   = pd.read_parquet(os.path.join(data_dir, "val_combined_457_8192.parquet"))

def get_task_ids(df):
    ids = set()
    for ei in df['extra_info']:
        try:
            td = ei['task_dir'] if isinstance(ei, dict) else dict(ei)['task_dir']
            if td:
                ids.add(os.path.basename(td.rstrip('/')))
        except Exception:
            pass
    return ids

train_ids = get_task_ids(train_v1v2)
val_ids   = get_task_ids(val_v1v2)

# match scanned dirs to train/val by task basename
train_v1 = sorted(d for d in all_v1 if os.path.basename(d) in train_ids)
val_v1   = sorted(d for d in all_v1 if os.path.basename(d) in val_ids)
train_v2 = sorted(d for d in all_v2 if os.path.basename(d) in train_ids)
val_v2   = sorted(d for d in all_v2 if os.path.basename(d) in val_ids)

# ── v3: apply same deterministic 90/10 split as prepare_data_v3hard.sh ───────
filter_file = os.path.join(data_dir, "tasks_with_pass_harbor_4.8opus_v3.txt")
if not os.path.exists(filter_file):
    import subprocess
    subprocess.run(["aws", "s3", "cp",
        "s3://endless-terminals-training/data/tasks_with_pass_harbor_4.8opus_v3.txt",
        filter_file], check=True)
with open(filter_file) as f:
    solvable = set(line.strip() for line in f if line.strip())

print("Scanning v3 task dirs on disk...")
all_v3_paths = find_task_dirs(v3_dir)
all_v3_filtered = sorted(p for p in all_v3_paths if os.path.basename(p) in solvable)
print(f"  found {len(all_v3_filtered)} solvable v3 tasks")

rng = np.random.default_rng(42)
indices = rng.permutation(len(all_v3_filtered))
split = int(len(all_v3_filtered) * 0.9)
train_v3 = [all_v3_filtered[i] for i in indices[:split]]
val_v3   = [all_v3_filtered[i] for i in indices[split:]]

print(f"v1: {len(train_v1)} train / {len(val_v1)} val")
print(f"v2: {len(train_v2)} train / {len(val_v2)} val")
print(f"v3: {len(train_v3)} train / {len(val_v3)} val")

splits = {
    'train_v1':      train_v1,
    'train_v2':      train_v2,
    'train_v3':      train_v3,
    'val_v1':        val_v1,
    'val_v2':        val_v2,
    'val_v3':        val_v3,
    'train_combined': train_v1 + train_v2 + train_v3,
    'val_combined':   val_v1   + val_v2   + val_v3,
}

print("\nWriting JSON files:")
for name, dirs in splits.items():
    # filter to paths that exist on disk
    existing = [d for d in dirs if os.path.isdir(d)]
    path = os.path.join(data_dir, f'task_dirs_{name}.json')
    with open(path, 'w') as f:
        json.dump(existing, f, indent=2)
    print(f"  {name}: {len(existing)}/{len(dirs)} tasks on disk → {os.path.basename(path)}")
PYEOF

echo ""
echo "=== Done. JSON files written to $DATA_DIR ==="
