#!/bin/bash
set -e
cd "$(dirname "$0")/.."

TASKS_DIR_457="/home/ec2-user/xin/harbor_tasks_457"
TASKS_DIR_8192="/home/ec2-user/xin/harbor_tasks_8192_deduped"
DATA_DIR="/home/ec2-user/xin/data_harbor_combined"

mkdir -p "$TASKS_DIR_457" "$TASKS_DIR_8192" "$DATA_DIR"

echo "=== Downloading original 457 tasks ==="
for part in 1 2 3 4; do
  aws s3 sync \
    "s3://endless-terminals-training/data/harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-${part}/" \
    "$TASKS_DIR_457/" --no-progress
done
echo "457 tasks: $(find $TASKS_DIR_457 -maxdepth 1 -mindepth 1 -type d | wc -l) task dirs"

echo "=== Downloading deduped 8192 tasks ==="
aws s3 sync s3://endless-terminals-training/data/harbor_tasks_8192_deduped/ \
  "$TASKS_DIR_8192/" --no-progress
echo "8192 tasks: $(find $TASKS_DIR_8192 -maxdepth 1 -mindepth 1 -type d | wc -l) task dirs"

echo "=== Downloading parquets ==="
aws s3 cp s3://endless-terminals-training/prepared_data/train_4.5opus-task_4.6sonnet-sol.parquet        "$DATA_DIR/train_457.parquet"  --no-progress
aws s3 cp s3://endless-terminals-training/prepared_data/validation_4.5opus-task_4.6sonnet-sol.parquet   "$DATA_DIR/val_457.parquet"    --no-progress
aws s3 cp s3://endless-terminals-training/prepared_data/train_8192_deduped_4929tasks.parquet            "$DATA_DIR/train_8192.parquet" --no-progress
aws s3 cp s3://endless-terminals-training/prepared_data/validation_8192_deduped_4929tasks.parquet       "$DATA_DIR/val_8192.parquet"   --no-progress

echo "=== Combining and fixing task_dir paths ==="
python3.13 - "$TASKS_DIR_457" "$TASKS_DIR_8192" "$DATA_DIR" <<'PYEOF'
import sys, os
import pandas as pd

tasks_dir_457  = sys.argv[1]
tasks_dir_8192 = sys.argv[2]
data_dir       = sys.argv[3]

def fix_paths(df, local_base):
    def fix_row(row):
        ei = row["extra_info"]
        rs = row["reward_spec"]
        task_name = os.path.basename(ei["task_dir"])
        new_path = os.path.join(local_base, task_name)
        row["extra_info"]  = {**ei, "task_dir": new_path}
        row["reward_spec"] = {**rs, "ground_truth": new_path}
        return row
    return df.apply(fix_row, axis=1)

splits = [
    ("train", "train_457.parquet", "train_8192.parquet", "train_combined_457_8192.parquet"),
    ("val",   "val_457.parquet",   "val_8192.parquet",   "val_combined_457_8192.parquet"),
]

for split, f457, f8192, out in splits:
    df_457  = fix_paths(pd.read_parquet(os.path.join(data_dir, f457)),  tasks_dir_457)
    df_8192 = fix_paths(pd.read_parquet(os.path.join(data_dir, f8192)), tasks_dir_8192)
    combined = pd.concat([df_457, df_8192], ignore_index=True).sample(frac=1, random_state=42)
    combined.to_parquet(os.path.join(data_dir, out), index=False)
    print(f"{split}: {len(df_457)} (457) + {len(df_8192)} (8192) = {len(combined)} total → {out}")
PYEOF

echo "=== Uploading combined parquets to S3 ==="
aws s3 cp "$DATA_DIR/train_combined_457_8192.parquet" \
  s3://endless-terminals-training/prepared_data/train_combined_457_8192.parquet --no-progress
aws s3 cp "$DATA_DIR/val_combined_457_8192.parquet" \
  s3://endless-terminals-training/prepared_data/val_combined_457_8192.parquet --no-progress

echo "=== Done ==="
echo "Train: $DATA_DIR/train_combined_457_8192.parquet"
echo "Val:   $DATA_DIR/val_combined_457_8192.parquet"
