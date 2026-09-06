"""
utility/val_parquet_to_tasks.py

Prepares a local Harbor-compatible task directory from a val parquet file.

For each parquet:
  1. Reads task basenames from extra_info.task_dir
  2. Searches across multiple local source dirs (in priority order) for each task
  3. Creates a named output dir (named after the parquet) containing symlinks
     to the local task dirs — ready for `harbor run --path <output_dir>`

Source dirs searched per parquet (in order, first match wins):
  val_combined_457_8192:
    harbor_tasks_8192_deduped/
    harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-{1,2,3,4}/

  val_combined_v1v2v3easy9b:
    harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_9b_shard{0,1,2}/
    harbor_tasks_8192_deduped/
    harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-{1,2,3,4}/

  val_combined_v1v2v3hard:
    harbor_4.8opus_tasks_v3_internet_access_config/
    harbor_tasks_8192_deduped/
    harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-{1,2,3,4}/

Usage (CLI):
  python utility/val_parquet_to_tasks.py \\
      --parquet data/val_combined_457_8192.parquet

Python API:
  from utility.val_parquet_to_tasks import prepare_val_tasks
  out_dir = prepare_val_tasks("data/val_combined_457_8192.parquet")
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

# Default local base dir for task data
DEFAULT_BASE_DIR = "/home/ec2-user/endless-terminals-playground/data"

# V1 part subdirs (relative to base_dir)
_V1_PARTS = [
    "harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-1",
    "harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-2",
    "harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-3",
    "harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-4",
]

# V3 easy 9B shard subdirs (relative to base_dir)
_V3_EASY_9B_SHARDS = [
    "harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_9b_shard0",
    "harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_9b_shard1",
    "harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_9b_shard2",
]

# Search order per parquet stem (first match wins for each task)
SEARCH_SUBDIRS: dict[str, list[str]] = {
    "val_combined_457_8192": [
        "harbor_tasks_8192_deduped",
        *_V1_PARTS,
    ],
    "val_combined_v1v2v3easy9b": [
        "harbor_tasks_easy_9b",
        "harbor_tasks_8192_deduped",
        *_V1_PARTS,
    ],
    "val_combined_v1v2v3hard": [
        "harbor_4.8opus_tasks_v3_internet_access_config",
        "harbor_tasks_8192_deduped",
        *_V1_PARTS,
    ],
}


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


def _find_task(name: str, search_dirs: list[Path]) -> Path | None:
    """Return the first directory that contains a task subdir named `name`."""
    for d in search_dirs:
        candidate = d / name
        if candidate.is_dir():
            return candidate
    return None


def prepare_val_tasks(
    parquet_path: str | Path,
    out_dir: str | Path | None = None,
    base_dir: str | Path = DEFAULT_BASE_DIR,
    dry_run: bool = False,
) -> Path:
    """
    Prepare a Harbor-compatible local task directory from a val parquet.

    Searches across multiple local source dirs for each task (see SEARCH_SUBDIRS),
    then creates `out_dir` containing symlinks. Returns the resolved out_dir path.

    Args:
        parquet_path: Path to the val parquet file.
        out_dir:      Where to create the Harbor dataset dir. Defaults to
                      <base_dir>/harbor_tasks_<parquet_stem>.
        base_dir:     Local root containing task data dirs.
        dry_run:      If True, only print what would be done.

    Returns:
        Path to the output dataset directory (pass to `harbor run --path`).
    """
    parquet_path = Path(parquet_path).resolve()
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet not found: {parquet_path}")

    stem = parquet_path.stem
    if stem not in SEARCH_SUBDIRS:
        raise ValueError(f"Unsupported parquet '{stem}'. Supported: {list(SEARCH_SUBDIRS.keys())}")

    base_dir = Path(base_dir).resolve()
    search_dirs = [base_dir / s for s in SEARCH_SUBDIRS[stem]]

    if out_dir is None:
        out_dir = base_dir / f"harbor_tasks_{stem}"
    out_dir = Path(out_dir).resolve()

    print(f"[prepare_val_tasks] parquet: {parquet_path.name}")
    print(f"  base dir:   {base_dir}")
    print(f"  search dirs ({len(search_dirs)}):")
    for d in search_dirs:
        exists = "OK" if d.is_dir() else "MISSING"
        print(f"    [{exists}] {d}")
    print(f"  output dir: {out_dir}")

    task_names = _task_basenames(parquet_path)
    print(f"  tasks in parquet: {len(task_names)}")

    if dry_run:
        found = sum(1 for t in task_names if _find_task(t, search_dirs) is not None)
        print(f"  [dry-run] would symlink {found}/{len(task_names)} tasks")
        print(f"  Done → {out_dir}")
        return out_dir

    out_dir.mkdir(parents=True, exist_ok=True)
    linked = 0
    missing = []
    for name in task_names:
        src = _find_task(name, search_dirs)
        dst = out_dir / name
        if src is None:
            missing.append(name)
            continue
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        dst.symlink_to(src)
        linked += 1

    print(f"  Symlinked {linked}/{len(task_names)} task dirs into {out_dir}")
    if missing:
        print(f"  WARNING: {len(missing)} tasks not found in any search dir: {missing[:5]}{'...' if len(missing) > 5 else ''}")

    print(f"  Done → {out_dir}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare a Harbor task directory from a val parquet file."
    )
    parser.add_argument("--parquet", required=True, help="Path to val parquet file")
    parser.add_argument("--out-dir", default=None, help="Output Harbor dataset dir (default: <base-dir>/harbor_tasks_<stem>)")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help=f"Local root for task data dirs (default: {DEFAULT_BASE_DIR})")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without creating symlinks")
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
