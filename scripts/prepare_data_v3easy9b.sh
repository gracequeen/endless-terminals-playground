#!/bin/bash
# Prepare combined parquet for dryrun3:
#   train = v1 (457) + v2 (8192 deduped) + v3 easy 9B train split (90%)
#   val   = v1 + v2 val (existing 151 tasks) + v3 easy 9B val split (10%)
# Outputs uploaded to S3 as:
#   s3://endless-terminals-training/prepared_data/train_combined_v1v2v3easy9b.parquet
#   s3://endless-terminals-training/prepared_data/val_combined_v1v2v3easy9b.parquet
set -e
cd "$(dirname "$0")/.."
source /tmp/sky/bin/activate

TASKS_DIR_V3="/home/ec2-user/xin/harbor_tasks_easy_9b"
DATA_DIR="/home/ec2-user/xin/data_harbor_combined"

mkdir -p "$TASKS_DIR_V3" "$DATA_DIR"

# ── download v3 easy 9B task dirs ───────────────────────────────────────────
if [ -z "$(ls -A $TASKS_DIR_V3 2>/dev/null)" ]; then
  echo "Downloading v3 easy 9B tasks..."
  for shard in 0 1 2; do
    aws s3 sync \
      "s3://endless-terminals-training/data/harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_9b_shard${shard}/" \
      "$TASKS_DIR_V3/" --no-progress
  done
else
  echo "Using existing v3 easy 9B tasks"
fi
echo "v3 easy 9B: $(find $TASKS_DIR_V3 -maxdepth 1 -mindepth 1 -type d | wc -l) task dirs"

# ── ensure v1+v2 combined parquets are present ──────────────────────────────
if [ ! -f "$DATA_DIR/train_combined_457_8192.parquet" ]; then
  echo "Downloading existing v1+v2 combined parquets..."
  aws s3 cp s3://endless-terminals-training/prepared_data/train_combined_457_8192.parquet \
    "$DATA_DIR/train_combined_457_8192.parquet" --no-progress
  aws s3 cp s3://endless-terminals-training/prepared_data/val_combined_457_8192.parquet \
    "$DATA_DIR/val_combined_457_8192.parquet" --no-progress
else
  echo "Using existing v1+v2 combined parquets"
fi

# ── generate v3 easy 9B parquet and combine ──────────────────────────────────
python3.13 - "$TASKS_DIR_V3" "$DATA_DIR" <<'PYEOF'
import sys, os, json
import pandas as pd
import numpy as np

tasks_dir = sys.argv[1]
data_dir  = sys.argv[2]

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

def build_rows(task_dirs_list, tasks_base):
    rows = []
    for task_name in task_dirs_list:
        task_path = os.path.join(tasks_base, task_name)
        instruction_file = os.path.join(task_path, "instruction.md")
        if not os.path.exists(instruction_file):
            print(f"  Warning: no instruction.md in {task_name}, skipping")
            continue
        with open(instruction_file) as f:
            description = f.read().strip()
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

# Collect all v3 easy 9B task dirs, sort for reproducibility
all_tasks = sorted([
    d for d in os.listdir(tasks_dir)
    if os.path.isdir(os.path.join(tasks_dir, d)) and d.startswith("task_")
])
print(f"Found {len(all_tasks)} v3 easy 9B task dirs")

# 90/10 split (deterministic)
rng = np.random.default_rng(42)
indices = rng.permutation(len(all_tasks))
split = int(len(all_tasks) * 0.9)
train_tasks = [all_tasks[i] for i in indices[:split]]
val_tasks   = [all_tasks[i] for i in indices[split:]]
print(f"v3 easy 9B split: {len(train_tasks)} train / {len(val_tasks)} val")

# Build v3 easy 9B rows
train_v3 = pd.DataFrame(build_rows(train_tasks, tasks_dir))
val_v3   = pd.DataFrame(build_rows(val_tasks,   tasks_dir))

# Load existing v1+v2 combined parquets
train_v1v2 = pd.read_parquet(os.path.join(data_dir, "train_combined_457_8192.parquet"))
val_v1v2   = pd.read_parquet(os.path.join(data_dir, "val_combined_457_8192.parquet"))
print(f"v1+v2 train: {len(train_v1v2)} tasks")
print(f"v1+v2 val:   {len(val_v1v2)} tasks")

# Combine and shuffle
train_out = pd.concat([train_v1v2, train_v3], ignore_index=True).sample(frac=1, random_state=42)
val_out   = pd.concat([val_v1v2,   val_v3],   ignore_index=True).sample(frac=1, random_state=42)

train_path = os.path.join(data_dir, "train_combined_v1v2v3easy9b.parquet")
val_path   = os.path.join(data_dir, "val_combined_v1v2v3easy9b.parquet")
train_out.to_parquet(train_path, index=False)
val_out.to_parquet(val_path,   index=False)

print(f"Train: {len(train_v1v2)} (v1+v2) + {len(train_v3)} (v3easy9b) = {len(train_out)} total → train_combined_v1v2v3easy9b.parquet")
print(f"Val:   {len(val_v1v2)} (v1+v2) + {len(val_v3)} (v3easy9b) = {len(val_out)} total → val_combined_v1v2v3easy9b.parquet")
PYEOF

# ── upload to S3 ─────────────────────────────────────────────────────────────
echo "Uploading combined parquets to S3..."
aws s3 cp "$DATA_DIR/train_combined_v1v2v3easy9b.parquet" \
  s3://endless-terminals-training/prepared_data/train_combined_v1v2v3easy9b.parquet --no-progress
aws s3 cp "$DATA_DIR/val_combined_v1v2v3easy9b.parquet" \
  s3://endless-terminals-training/prepared_data/val_combined_v1v2v3easy9b.parquet --no-progress

echo "=== Done ==="
echo "Train: $DATA_DIR/train_combined_v1v2v3easy9b.parquet"
echo "Val:   $DATA_DIR/val_combined_v1v2v3easy9b.parquet"
