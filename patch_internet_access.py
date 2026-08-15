#!/usr/bin/env python3
"""Patch task.toml files in a dataset copy with allow_internet settings.

- Flagged tasks (from scan CSV): allow_internet = true  (explicit)
- All other tasks:               allow_internet = false

Usage:
    python patch_internet_access.py
"""
from pathlib import Path
import tomllib
import toml
import pandas as pd

DATASET_DIR = Path("/home/ec2-user/endless-terminals-playground/harbor_4.8opus_tasks_v3_internet_access_config")
SCAN_CSV    = Path("/home/ec2-user/endless-terminals-playground/internet_scan_results.csv")

# Load flagged task names
flagged = set(pd.read_csv(SCAN_CSV)["task"].tolist())
print(f"Flagged tasks (allow_internet=true):  {len(flagged)}")

task_dirs = sorted(d for d in DATASET_DIR.iterdir() if d.is_dir())
print(f"Total tasks in dataset copy:          {len(task_dirs)}")

patched_true = 0
patched_false = 0
errors = 0

for task_dir in task_dirs:
    toml_path = task_dir / "task.toml"
    if not toml_path.exists():
        continue

    try:
        cfg = tomllib.loads(toml_path.read_text())
    except Exception as e:
        print(f"  WARN parse error {task_dir.name}: {e}")
        errors += 1
        continue

    allow = task_dir.name in flagged
    cfg.setdefault("environment", {})["allow_internet"] = allow

    toml_path.write_text(toml.dumps(cfg))
    if allow:
        patched_true += 1
    else:
        patched_false += 1

print(f"\nPatched allow_internet=true:  {patched_true}")
print(f"Patched allow_internet=false: {patched_false}")
print(f"Errors:                       {errors}")
print("\nDone. Original dataset untouched.")
