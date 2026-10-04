#!/bin/bash
# Prepare combined parquet using stratified 90/10 split by category for each dataset:
#   v1 (harbor_tasks_457) — solvable tasks from existing parquet
#   v2 (harbor_tasks_8192_deduped) — solvable tasks from existing parquet
#   v3hard (harbor_4.8opus_tasks_v3_internet_access_config) — solvable from filter file
#
# Each dataset is split independently by category (90% train, 10% val).
# Results are combined and uploaded to S3 as:
#   s3://endless-terminals-training/prepared_data/train_v1v2v3hard_stratified.parquet
#   s3://endless-terminals-training/prepared_data/val_v1v2v3hard_stratified.parquet
set -e
cd "$(dirname "$0")/.."
source /tmp/sky/bin/activate

TASKS_DIR_V1="/home/ec2-user/xin/harbor_tasks_457"
TASKS_DIR_V2="/home/ec2-user/xin/harbor_tasks_8192_deduped"
TASKS_DIR_V3HARD="/home/ec2-user/xin/harbor_tasks_v3hard"
DATA_DIR="/home/ec2-user/xin/data_harbor_combined"

mkdir -p "$DATA_DIR"

# ── ensure task dirs exist ───────────────────────────────────────────────────
for dir in "$TASKS_DIR_V1" "$TASKS_DIR_V2" "$TASKS_DIR_V3HARD"; do
  if [ -z "$(ls -A $dir 2>/dev/null)" ]; then
    echo "ERROR: $dir is empty or missing. Download tasks first." >&2
    exit 1
  fi
done

# ── download v1+v2 existing parquets (for solvable task list) ────────────────
if [ ! -f "$DATA_DIR/train_combined_457_8192.parquet" ]; then
  echo "Downloading v1+v2 parquets from S3..."
  aws s3 cp s3://endless-terminals-training/prepared_data/train_combined_457_8192.parquet \
    "$DATA_DIR/train_combined_457_8192.parquet" --no-progress --region us-east-1
  aws s3 cp s3://endless-terminals-training/prepared_data/val_combined_457_8192.parquet \
    "$DATA_DIR/val_combined_457_8192.parquet" --no-progress --region us-east-1
else
  echo "Using existing v1+v2 parquets"
fi

# ── download v3hard solvable filter file ─────────────────────────────────────
if [ ! -f "$DATA_DIR/tasks_with_pass_harbor_4.8opus_v3.txt" ]; then
  echo "Downloading v3hard solvable filter..."
  aws s3 cp s3://endless-terminals-training/data/tasks_with_pass_harbor_4.8opus_v3.txt \
    "$DATA_DIR/tasks_with_pass_harbor_4.8opus_v3.txt" --no-progress --region us-east-1
else
  echo "Using existing v3hard filter file"
fi

# ── stratified split + build parquets ────────────────────────────────────────
python3.13 - "$TASKS_DIR_V1" "$TASKS_DIR_V2" "$TASKS_DIR_V3HARD" "$DATA_DIR" <<'PYEOF'
import sys, os, tomllib, subprocess
import pandas as pd
import numpy as np
from collections import defaultdict

tasks_dir_v1    = sys.argv[1]
tasks_dir_v2    = sys.argv[2]
tasks_dir_v3    = sys.argv[3]
data_dir        = sys.argv[4]

SYSTEM_PROMPT = (
    "You are a highly capable Linux terminal agent operating strictly via a single-shell-command interface.\n"
    "Goal: Complete the user's task.\n\n"
    "Detailed Instructions:\n"
    "- Output exactly one of the following per turn after you think in the <think> </think> tags:\n"
    "  1) <command>THE_SINGLE_SHELL_COMMAND</command>\n"
    "  XOR (XOR means you can only respond with one of the two)\n"
    "  2) <action>done</action>\n"
    "- Don't use interactive commands and confirmations; use non-interactive flags.\n"
    "- Prefer simple, robust CLI tools; write files explicitly when needed.\n"
    "- If you believe the task is solved, emit <action>done</action>.\n"
    "- You should run commands interactively to see the output and then write the command. Don't just pipe the commands.\n"
    "- Only your first command in command tags will be executed. So don't respond with multiple commands.\n"
    "- Verify your solution once you are done. Eg: you can use cat to see the input and the output.\n"
    "- Do not just write long bash scripts. Write the commands that you would write in a terminal.\n"
    "- Only respond with one of <command>...</command> or <action>done</action> after you think in the <think> </think> tags.\n"
    "- Plan and simulate your actions in <think> </think> tags before you respond with <command>...</command>."
)

def get_category(task_path):
    toml_path = os.path.join(task_path, "task.toml")
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("metadata", {}).get("category", "unknown")
    except Exception:
        return "unknown"

def stratified_split(task_paths, rng):
    by_category = defaultdict(list)
    for path in task_paths:
        by_category[get_category(path)].append(path)

    train, val = [], []
    for cat in sorted(by_category.keys()):
        tasks = [by_category[cat][i] for i in rng.permutation(len(by_category[cat]))]
        n_val = max(1, round(len(tasks) * 0.1))
        val.extend(tasks[:n_val])
        train.extend(tasks[n_val:])
    return train, val

def build_rows(task_paths):
    rows = []
    for task_path in task_paths:
        instruction_file = os.path.join(task_path, "instruction.md")
        if not os.path.exists(instruction_file):
            print(f"  Warning: no instruction.md in {task_path}, skipping")
            continue
        with open(instruction_file) as f:
            description = f.read().strip()
        task_name = os.path.basename(task_path)
        rows.append({
            "description": description,
            "task_dir": task_name,
            "data_source": "endless",
            "prompt": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": description},
            ],
            "env_class": "endless",
            "reward_spec": {"method": "rule", "ground_truth": task_path},
            "extra_info": {"task_dir": task_path, "max_time": 300},
        })
    return rows

rng = np.random.default_rng(42)

# ── v1: solvable task paths from existing parquets ───────────────────────────
v1_paths = []
for split in ["train", "val"]:
    df = pd.read_parquet(os.path.join(data_dir, f"{split}_combined_457_8192.parquet"))
    paths = df["extra_info"].apply(lambda x: x.get("task_dir", "") if isinstance(x, dict) else "")
    v1_paths.extend(p for p in paths if "harbor_tasks_457" in p)
print(f"v1 solvable: {len(v1_paths)} tasks")

v1_train_paths, v1_val_paths = stratified_split(v1_paths, rng)
print(f"v1 split: {len(v1_train_paths)} train / {len(v1_val_paths)} val")

# ── v2: solvable task paths from existing parquets ───────────────────────────
v2_paths = []
for split in ["train", "val"]:
    df = pd.read_parquet(os.path.join(data_dir, f"{split}_combined_457_8192.parquet"))
    paths = df["extra_info"].apply(lambda x: x.get("task_dir", "") if isinstance(x, dict) else "")
    v2_paths.extend(p for p in paths if "harbor_tasks_8192" in p)
print(f"v2 solvable: {len(v2_paths)} tasks")

v2_train_paths, v2_val_paths = stratified_split(v2_paths, rng)
print(f"v2 split: {len(v2_train_paths)} train / {len(v2_val_paths)} val")

# ── v3hard: solvable tasks from filter file ───────────────────────────────────
filter_file = os.path.join(data_dir, "tasks_with_pass_harbor_4.8opus_v3.txt")
with open(filter_file) as f:
    v3_solvable = set(line.strip() for line in f if line.strip())
v3_paths = [
    os.path.join(tasks_dir_v3, d)
    for d in sorted(os.listdir(tasks_dir_v3))
    if d.startswith("task_") and d in v3_solvable
    and os.path.isdir(os.path.join(tasks_dir_v3, d))
]
print(f"v3hard solvable: {len(v3_paths)} tasks")

v3_train_paths, v3_val_paths = stratified_split(v3_paths, rng)
print(f"v3hard split: {len(v3_train_paths)} train / {len(v3_val_paths)} val")

# ── build and combine ─────────────────────────────────────────────────────────
train_df = pd.DataFrame(build_rows(v1_train_paths + v2_train_paths + v3_train_paths))
val_df   = pd.DataFrame(build_rows(v1_val_paths   + v2_val_paths   + v3_val_paths))

train_df = train_df.sample(frac=1, random_state=42).reset_index(drop=True)
val_df   = val_df.sample(frac=1, random_state=42).reset_index(drop=True)

train_path = os.path.join(data_dir, "train_v1v2v3hard_stratified.parquet")
val_path   = os.path.join(data_dir, "val_v1v2v3hard_stratified.parquet")
train_df.to_parquet(train_path, index=False)
val_df.to_parquet(val_path, index=False)

print(f"\nTrain: {len(v1_train_paths)} (v1) + {len(v2_train_paths)} (v2) + {len(v3_train_paths)} (v3hard) = {len(train_df)} total")
print(f"Val:   {len(v1_val_paths)} (v1) + {len(v2_val_paths)} (v2) + {len(v3_val_paths)} (v3hard) = {len(val_df)} total")
PYEOF

# ── upload to S3 ──────────────────────────────────────────────────────────────
echo "Uploading to S3..."
aws s3 cp "$DATA_DIR/train_v1v2v3hard_stratified.parquet" \
  s3://endless-terminals-training/prepared_data/train_v1v2v3hard_stratified.parquet --no-progress --region us-east-1
aws s3 cp "$DATA_DIR/val_v1v2v3hard_stratified.parquet" \
  s3://endless-terminals-training/prepared_data/val_v1v2v3hard_stratified.parquet --no-progress --region us-east-1

echo "=== Done ==="
echo "Train: $DATA_DIR/train_v1v2v3hard_stratified.parquet"
echo "Val:   $DATA_DIR/val_v1v2v3hard_stratified.parquet"
