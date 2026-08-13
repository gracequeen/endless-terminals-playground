#!/usr/bin/env python3
"""Check status of all active harbor solution generation jobs."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent / "solution_grace"
NOW = datetime.now(timezone.utc)

jobs = [
    ("claude4.5_sonnet", "harbor_tasks_part2_2-1"),
    ("claude4.5_sonnet", "harbor_tasks_part2_2-2"),
    ("claude4.5_sonnet", "harbor_tasks_part2_2-3"),
    ("claude4.5_sonnet", "harbor_tasks_part2_2-4"),
    ("claude4.6_sonnet", "harbor_tasks_part2_2-1"),
    ("claude4.6_sonnet", "harbor_tasks_part2_2-2"),
    ("claude4.6_sonnet", "harbor_tasks_part2_2-3"),
    ("claude4.6_sonnet", "harbor_tasks_part2_2-4"),
    ("claude4.6_opus",   "harbor_tasks_part2_2-1"),
    ("claude4.6_opus",   "harbor_tasks_part2_2-2"),
    ("claude4.6_opus",   "harbor_tasks_part2_2-3"),
    ("claude4.6_opus",   "harbor_tasks_part2_2-4"),
]

print(f"{'Model':<20} {'Job':<30} {'Progress':>10} {'Running':>8} {'Errors':>8} {'Rate/min':>10} {'Status':>12}")
print("-" * 105)

for folder, name in jobs:
    result_path = BASE / folder / name / "result.json"
    if not result_path.exists():
        continue
    try:
        with open(result_path) as f:
            d = json.load(f)
        started = datetime.fromisoformat(d["started_at"].rstrip("Z")).replace(tzinfo=timezone.utc)
        elapsed_min = (NOW - started).total_seconds() / 60
        s = d["stats"]
        done = s["n_completed_trials"] + s["n_errored_trials"]
        total = d["n_total_trials"]
        rate = done / elapsed_min if elapsed_min > 0 else 0
        remaining = max(0, total - done)
        eta_h = (remaining / rate / 60) if rate > 0 else float("inf")
        pct = 100 * done / total
        if s["n_running_trials"] > 0:
            status = f"ETA={eta_h:.1f}h"
        elif done >= total:
            status = "DONE"
        else:
            status = "STOPPED"
        print(f"{folder:<20} {name:<30} {f'{done}/{total} ({pct:.1f}%)':>10} {s['n_running_trials']:>8} {s['n_errored_trials']:>8} {rate:>10.1f} {status:>12}")
    except Exception as e:
        print(f"{folder:<20} {name:<30} ERROR: {e}")
