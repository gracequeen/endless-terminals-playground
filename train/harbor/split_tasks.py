"""
split_tasks.py — stratified train/eval/test split for Harbor task directories.

Produces a manifest JSON; does not move or copy any files.

Usage:
    python train/harbor/split_tasks.py \
        --task-dir harbor_tasks \
        --seed 42 \
        --output data/harbor_split.json
"""

import argparse
import json
import random
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # fallback


SPLIT_FRACTIONS = {"train": 0.80, "eval": 0.05, "test": 0.15}


def read_difficulty(task_dir: Path) -> str:
    toml_path = task_dir / "task.toml"
    if not toml_path.exists():
        return "unknown"
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)
    return data.get("metadata", {}).get("difficulty", "unknown")


def collect_tasks(task_dir: Path) -> list[dict]:
    """Return list of {path, difficulty, name} for every valid task dir."""
    tasks = []
    for d in sorted(task_dir.iterdir()):  # sorted → deterministic order
        if d.is_dir() and (d / "instruction.md").exists():
            tasks.append({"path": str(d), "name": d.name, "difficulty": read_difficulty(d)})
    return tasks


def stratified_split(tasks: list[dict], seed: int) -> dict[str, list[dict]]:
    """Stratified shuffle-split by difficulty preserving global 80/5/15 counts."""
    rng = random.Random(seed)

    # Group by difficulty
    groups: dict[str, list[dict]] = {}
    for t in tasks:
        groups.setdefault(t["difficulty"], []).append(t)

    n_total = len(tasks)
    # Global target counts — ensure they sum exactly to n_total
    n_train = int(n_total * SPLIT_FRACTIONS["train"])
    n_eval = int(n_total * SPLIT_FRACTIONS["eval"])
    n_test = n_total - n_train - n_eval  # remainder to test

    splits: dict[str, list[dict]] = {"train": [], "eval": [], "test": []}

    for difficulty, group in groups.items():
        rng.shuffle(group)
        n = len(group)
        # Proportional share of each global target for this stratum
        g_train = round(n * n_train / n_total)
        g_eval = round(n * n_eval / n_total)
        g_test = n - g_train - g_eval  # remainder keeps total exact per stratum
        splits["train"].extend(group[:g_train])
        splits["eval"].extend(group[g_train : g_train + g_eval])
        splits["test"].extend(group[g_train + g_eval :])

    # Global counts may be off by ±1 per stratum due to rounding; redistribute
    # by moving items from over-represented to under-represented splits
    for src, tgt, target in [
        ("train", "test", n_train),
        ("eval", "test", n_eval),
    ]:
        while len(splits[src]) > target:
            splits["test"].append(splits[src].pop())
        while len(splits[src]) < target and splits["test"]:
            splits[src].append(splits["test"].pop())

    # Final shuffle so order within each split is random, not grouped by difficulty
    for key in splits:
        rng.shuffle(splits[key])

    return splits


def create_split(task_dir: Path, seed: int = 42) -> dict:
    """
    Build a stratified split from a task directory.

    Returns a dict with keys "train", "eval", "test" (lists of task directory
    names) and "metadata".
    """
    tasks = collect_tasks(task_dir)
    if not tasks:
        raise ValueError(f"No valid task directories found in '{task_dir}'")

    name_splits = stratified_split(tasks, seed)

    difficulty_counts: dict[str, int] = {}
    for t in tasks:
        difficulty_counts[t["difficulty"]] = difficulty_counts.get(t["difficulty"], 0) + 1

    return {
        "train": [t["name"] for t in name_splits["train"]],
        "eval": [t["name"] for t in name_splits["eval"]],
        "test": [t["name"] for t in name_splits["test"]],
        "metadata": {
            "seed": seed,
            "total": len(tasks),
            "task_dir": str(Path(task_dir).resolve()),
            "split_fractions": SPLIT_FRACTIONS,
            "counts": {k: len(v) for k, v in name_splits.items()},
            "difficulty_counts": difficulty_counts,
        },
    }


def print_summary(splits: dict[str, list[dict]], total: int) -> None:
    difficulties = sorted({t["difficulty"] for ts in splits.values() for t in ts})

    col_w = max(len(d) for d in difficulties + ["difficulty"]) + 2
    split_names = ["train", "eval", "test"]
    header = f"{'difficulty':<{col_w}}" + "".join(f"{s:>8}" for s in split_names) + f"{'total':>8}"
    print(header)
    print("-" * len(header))

    diff_totals = {d: 0 for d in difficulties}
    for diff in difficulties:
        row = f"{diff:<{col_w}}"
        for split in split_names:
            count = sum(1 for t in splits[split] if t["difficulty"] == diff)
            diff_totals[diff] += count
            row += f"{count:>8}"
        row += f"{diff_totals[diff]:>8}"
        print(row)

    print("-" * len(header))
    totals_row = f"{'total':<{col_w}}"
    for split in split_names:
        totals_row += f"{len(splits[split]):>8}"
    totals_row += f"{total:>8}"
    print(totals_row)


def main(task_dir: str | None = None, seed: int | None = None, output: str | None = None) -> None:
    parser = argparse.ArgumentParser(description="Stratified train/eval/test split for Harbor tasks.")
    parser.add_argument("--task-dir", default="harbor_tasks", help="Root directory containing task subdirs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", default="data/harbor_split.json", help="Output manifest JSON path")
    args = parser.parse_args([] if task_dir is not None else None)

    # Keyword args override CLI args (for programmatic use)
    if task_dir is not None:
        args.task_dir = task_dir
    if seed is not None:
        args.seed = seed
    if output is not None:
        args.output = output

    task_dir_path = Path(args.task_dir)
    if not task_dir_path.is_dir():
        print(f"error: task-dir '{task_dir_path}' does not exist or is not a directory", file=sys.stderr)
        sys.exit(1)

    tasks = collect_tasks(task_dir_path)
    if not tasks:
        print(f"error: no valid task directories found in '{task_dir_path}'", file=sys.stderr)
        sys.exit(1)

    splits = stratified_split(tasks, args.seed)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    difficulty_counts = {}
    for t in tasks:
        difficulty_counts[t["difficulty"]] = difficulty_counts.get(t["difficulty"], 0) + 1

    manifest = {
        "train": [t["name"] for t in splits["train"]],
        "eval": [t["name"] for t in splits["eval"]],
        "test": [t["name"] for t in splits["test"]],
        "metadata": {
            "seed": args.seed,
            "total": len(tasks),
            "task_dir": str(task_dir_path.resolve()),
            "split_fractions": SPLIT_FRACTIONS,
            "counts": {k: len(v) for k, v in splits.items()},
            "difficulty_counts": difficulty_counts,
        },
    }

    with output_path.open("w") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"Split {len(tasks)} tasks → {output_path}\n")
    print_summary(splits, len(tasks))


if __name__ == "__main__":
    main()
