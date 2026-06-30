"""Deduplicate Harbor-format task directories by topic similarity.

Reads instruction.md from each task in --input-dir, embeds them with
all-MiniLM-L6-v2, and copies unique tasks (cosine similarity < threshold
to all already-kept tasks) into --output-dir.

Usage:
    python dedup_harbor_tasks.py --input-dir harbor_tasks --output-dir harbor_tasks_deduped
    python dedup_harbor_tasks.py --input-dir harbor_tasks --output-dir harbor_tasks_deduped --threshold 0.80
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import List, Tuple

import numpy as np
from tqdm import tqdm


def _load_tasks(input_dir: Path) -> List[Tuple[Path, str]]:
    """Return (task_dir, description) for every valid task in input_dir."""
    tasks = []
    for d in sorted(input_dir.iterdir()):
        if not (d.is_dir() and re.match(r"task_\d+_", d.name)):
            continue
        instruction = d / "instruction.md"
        if not instruction.exists():
            continue
        text = instruction.read_text(encoding="utf-8").strip()
        if text:
            tasks.append((d, text))
    return tasks


def _embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def deduplicate_tasks(
    input_dir: Path,
    output_dir: Path,
    threshold: float = 0.85,
) -> dict:
    """Copy unique tasks from input_dir to output_dir.

    A task is a duplicate if its description's cosine similarity to any
    already-accepted task meets or exceeds threshold.

    Writes output_dir/dedup_report.json with per-task decisions.
    """
    tasks = _load_tasks(input_dir)
    if not tasks:
        print(f"No tasks found in {input_dir}")
        return {"input": 0, "kept": 0, "dropped": 0}

    print(f"Loaded {len(tasks)} tasks from {input_dir}")
    print("Loading embedding model ...")
    model = _embedding_model()

    descriptions = [desc for _, desc in tasks]
    print(f"Encoding {len(descriptions)} descriptions ...")
    embs = model.encode(descriptions, normalize_embeddings=True, show_progress_bar=True)

    kept_indices: List[int] = []
    kept_embs: List[np.ndarray] = []
    # For each task: {"task", "status", "description"} plus dup-specific fields
    records: List[dict] = []

    for i, emb in enumerate(tqdm(embs, desc="Deduplicating")):
        task_name = tasks[i][0].name
        desc = descriptions[i]
        if kept_embs:
            ref = np.stack(kept_embs)
            scores = ref @ emb
            best_pos = int(scores.argmax())
            best_sim = float(scores[best_pos])
            if best_sim >= threshold:
                records.append({
                    "task": task_name,
                    "status": "dropped",
                    "description": desc,
                    "duplicate_of": tasks[kept_indices[best_pos]][0].name,
                    "similarity": round(best_sim, 4),
                })
                continue
        kept_indices.append(i)
        kept_embs.append(emb)
        records.append({
            "task": task_name,
            "status": "kept",
            "description": desc,
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    for rank, i in enumerate(kept_indices):
        src = tasks[i][0]
        dst = output_dir / f"task_{rank:06d}_{src.name.split('_', 2)[-1]}"
        shutil.copytree(src, dst)

    dropped = len(tasks) - len(kept_indices)
    summary = {
        "input": len(tasks),
        "kept": len(kept_indices),
        "dropped": dropped,
        "threshold": threshold,
        "output_dir": str(output_dir),
        "tasks": records,
    }
    report_path = output_dir / "dedup_report.json"
    report_path.write_text(json.dumps(summary, indent=4), encoding="utf-8")
    print(f"\nKept {len(kept_indices)}/{len(tasks)} tasks ({dropped} dropped as near-duplicates)")
    print(f"Report written to {report_path}")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Deduplicate Harbor task directories by topic similarity."
    )
    ap.add_argument("--input-dir", type=Path, required=True, help="Directory of raw tasks")
    ap.add_argument("--output-dir", type=Path, required=True, help="Destination for unique tasks")
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Cosine similarity threshold above which a task is considered a duplicate (default: 0.85)",
    )
    args = ap.parse_args()

    if not args.input_dir.exists():
        ap.error(f"--input-dir does not exist: {args.input_dir}")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        ap.error(f"--output-dir already exists and is non-empty: {args.output_dir}")

    summary = deduplicate_tasks(args.input_dir, args.output_dir, threshold=args.threshold)
    print(json.dumps({k: v for k, v in summary.items() if k != "tasks"}, indent=4))


if __name__ == "__main__":
    main()
