"""
utility/val_parquet_to_tasks.py

Prepares a local Harbor-compatible task directory from a val parquet file.

For each parquet:
  1. Reads task basenames from extra_info.task_dir
  2. Downloads missing task dirs from S3 into a local base dir
  3. Creates a named output dir (named after the parquet) containing symlinks
     to the local task dirs — ready for `harbor run --path <output_dir>`

Supported parquets and their S3 sources:
  val_combined_457_8192        → s3://endless-terminals-training/data/harbor_tasks_8192_deduped/
  val_combined_v1v2v3easy9b    → s3://endless-terminals-training/data/harbor_tasks_easy_9b/

Usage (CLI):
  python utility/val_parquet_to_tasks.py \\
      --parquet data/val_combined_457_8192.parquet \\
      --out-dir harbor_tasks_val_combined_457_8192

  python utility/val_parquet_to_tasks.py \\
      --parquet data/val_combined_v1v2v3easy9b.parquet \\
      --base-dir /home/ec2-user/xin \\
      --out-dir harbor_tasks_val_combined_v1v2v3easy9b

Python API:
  from utility.val_parquet_to_tasks import prepare_val_tasks
  out_dir = prepare_val_tasks("data/val_combined_457_8192.parquet")
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

# S3 source for each supported parquet stem
S3_SOURCES: dict[str, str] = {
    "val_combined_457_8192": "s3://endless-terminals-training/data/harbor_tasks_8192_deduped/",
    "val_combined_v1v2v3easy9b": "s3://endless-terminals-training/data/harbor_tasks_easy_9b/",
    "val_combined_v1v2v3hard": "s3://endless-terminals-training/data/harbor_4.8opus_tasks_v3_internet_access_config/",
}

# Default local base dir for downloaded task dirs
DEFAULT_BASE_DIR = "/home/ec2-user/xin"


def _task_basenames(parquet_path: str | Path) -> list[str]:
    """Return sorted unique task basenames from extra_info.task_dir."""
    df = pd.read_parquet(parquet_path)
    basenames = (
        df["extra_info"]
        .apply(lambda x: os.path.basename(x["task_dir"].rstrip("/")) if isinstance(x, dict) and x.get("task_dir") else None)
        .dropna()
        .unique()
        .tolist()
    )
    return sorted(basenames)


def _s3_key_for_parquet(parquet_stem: str) -> str:
    if parquet_stem not in S3_SOURCES:
        raise ValueError(
            f"Unsupported parquet '{parquet_stem}'. "
            f"Supported: {list(S3_SOURCES.keys())}"
        )
    return S3_SOURCES[parquet_stem]


def _local_tasks_dir(parquet_stem: str, base_dir: str | Path) -> Path:
    """Return the local directory where task dirs for this parquet live."""
    stem_to_subdir = {
        "val_combined_457_8192": "harbor_tasks_8192_deduped",
        "val_combined_v1v2v3easy9b": "harbor_tasks_easy_9b",
        "val_combined_v1v2v3hard": "harbor_tasks_v3hard",
    }
    subdir = stem_to_subdir[parquet_stem]
    return Path(base_dir) / subdir


def _sync_task_dirs(
    task_names: list[str],
    s3_prefix: str,
    local_tasks_dir: Path,
    dry_run: bool = False,
) -> int:
    """Download missing task dirs from S3. Returns count of tasks downloaded."""
    local_tasks_dir.mkdir(parents=True, exist_ok=True)
    missing = [t for t in task_names if not (local_tasks_dir / t).is_dir()]
    if not missing:
        print(f"  All {len(task_names)} task dirs already present in {local_tasks_dir}")
        return 0

    print(f"  {len(missing)} task dirs missing locally, attempting S3 sync from {s3_prefix} ...")
    if dry_run:
        print(f"  [dry-run] would sync {len(missing)} dirs")
        return len(missing)

    # Only sync individually (small sets). Skip bulk sync — a full bucket sync is
    # wasteful when the missing tasks simply don't exist under that S3 prefix.
    if len(missing) > 20:
        print(f"  Skipping S3 sync: {len(missing)} missing tasks likely not in this S3 prefix (naming mismatch). Use tasks already on disk.")
        return 0
    for name in missing:
        cmd = ["aws", "s3", "sync", f"{s3_prefix}{name}/", str(local_tasks_dir / name), "--no-progress"]
        subprocess.run(cmd, check=True)
    downloaded = sum(1 for t in missing if (local_tasks_dir / t).is_dir())
    print(f"  Downloaded {downloaded}/{len(missing)} task dirs")
    return downloaded


def prepare_val_tasks(
    parquet_path: str | Path,
    out_dir: str | Path | None = None,
    base_dir: str | Path = DEFAULT_BASE_DIR,
    dry_run: bool = False,
) -> Path:
    """
    Prepare a Harbor-compatible local task directory from a val parquet.

    Downloads missing task dirs from S3, then creates `out_dir` containing
    symlinks to the local task dirs. Returns the resolved out_dir path.

    Args:
        parquet_path: Path to the val parquet file.
        out_dir:      Where to create the Harbor dataset dir. Defaults to
                      harbor_tasks_<parquet_stem> next to the parquet file.
        base_dir:     Local root where task dirs are downloaded (default: /home/ec2-user/xin).
        dry_run:      If True, skip S3 download and symlink creation.

    Returns:
        Path to the output dataset directory (pass to `harbor run --path`).
    """
    parquet_path = Path(parquet_path).resolve()
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet not found: {parquet_path}")

    stem = parquet_path.stem
    s3_prefix = _s3_key_for_parquet(stem)
    local_tasks_dir = _local_tasks_dir(stem, base_dir)

    if out_dir is None:
        out_dir = parquet_path.parent / f"harbor_tasks_{stem}"
    out_dir = Path(out_dir).resolve()

    print(f"[prepare_val_tasks] parquet: {parquet_path.name}")
    print(f"  S3 source:       {s3_prefix}")
    print(f"  local tasks dir: {local_tasks_dir}")
    print(f"  output dir:      {out_dir}")

    task_names = _task_basenames(parquet_path)
    print(f"  tasks in parquet: {len(task_names)}")

    # Download missing task dirs from S3
    _sync_task_dirs(task_names, s3_prefix, local_tasks_dir, dry_run=dry_run)

    # Build output dir with symlinks to local task dirs
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        linked = 0
        missing_on_disk = 0
        for name in task_names:
            src = local_tasks_dir / name
            dst = out_dir / name
            if not src.is_dir():
                print(f"  WARNING: {name} not found on disk after sync, skipping")
                missing_on_disk += 1
                continue
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            dst.symlink_to(src)
            linked += 1
        print(f"  Symlinked {linked} task dirs into {out_dir}")
        if missing_on_disk:
            print(f"  WARNING: {missing_on_disk} tasks missing on disk (skipped)")

    print(f"  Done → {out_dir}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare a Harbor task directory from a val parquet file."
    )
    parser.add_argument("--parquet", required=True, help="Path to val parquet file")
    parser.add_argument("--out-dir", default=None, help="Output Harbor dataset dir (default: harbor_tasks_<stem> next to parquet)")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help=f"Local root for downloaded task dirs (default: {DEFAULT_BASE_DIR})")
    parser.add_argument("--dry-run", action="store_true", help="Skip S3 download and symlink creation")
    args = parser.parse_args()

    out = prepare_val_tasks(
        parquet_path=args.parquet,
        out_dir=args.out_dir,
        base_dir=args.base_dir,
        dry_run=args.dry_run,
    )
    print(f"\nReady for Harbor eval:\n  harbor run --path {out} ...")


if __name__ == "__main__":
    main()
