"""
log_experiment.py — writes a structured experiment config JSON before a run.

Records hyperparameters, dataset split paths, model info, and timestamps.
Called at the start of run_harbor_t4.sh to produce results/experiment_config.json.

Usage:
    python3 train/harbor/log_experiment.py \
        --model Qwen/Qwen3.5-0.8B \
        --manifest data/harbor_split.json \
        --output results/experiment_config.json \
        --phase pre_train \
        --extra trainer.epochs=10 trainer.train_batch_size=4
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=REPO_ROOT,
        ).decode().strip()
    except Exception:
        return "unknown"


def gpu_info() -> str:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def load_split_summary(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {}
    with manifest_path.open() as fh:
        m = json.load(fh)
    meta = m.get("metadata", {})
    return {
        "manifest": str(manifest_path.resolve()),
        "seed": meta.get("seed"),
        "total_tasks": meta.get("total"),
        "task_dir": meta.get("task_dir"),
        "counts": {
            "train": len(m.get("train", [])),
            "eval": len(m.get("eval", [])),
            "test": len(m.get("test", [])),
        },
        "difficulty_counts": meta.get("difficulty_counts", {}),
        "split_fractions": meta.get("split_fractions", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--manifest", default="data/harbor_split.json")
    parser.add_argument("--output", default="results/experiment_config.json")
    parser.add_argument("--phase", default="pre_train",
                        choices=["pre_train", "train", "post_train", "eval"],
                        help="Which phase this config belongs to")
    parser.add_argument("--run-name", default="")
    parser.add_argument("--extra", nargs="*", default=[],
                        help="Extra key=value pairs to include in hyperparameters")
    args = parser.parse_args()

    hyperparams: dict = {}
    for kv in (args.extra or []):
        if "=" in kv:
            k, v = kv.split("=", 1)
            # Try to parse as number
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            hyperparams[k] = v

    config = {
        "phase": args.phase,
        "run_name": args.run_name or f"{args.phase}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": {
            "name": args.model,
            "source": "huggingface",
        },
        "dataset": load_split_summary(Path(args.manifest)),
        "hyperparameters": hyperparams,
        "environment": {
            "git_sha": git_sha(),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "gpu": gpu_info(),
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # If file exists, append as a list of phase configs
    existing = []
    if out_path.exists():
        try:
            existing_data = json.loads(out_path.read_text())
            if isinstance(existing_data, list):
                existing = existing_data
            else:
                existing = [existing_data]
        except json.JSONDecodeError:
            pass
    existing.append(config)

    with out_path.open("w") as fh:
        json.dump(existing, fh, indent=2)

    print(f"[log_experiment] phase={args.phase} model={args.model} → {out_path}")


if __name__ == "__main__":
    main()
