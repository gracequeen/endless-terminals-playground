#!/usr/bin/env python3
"""Baseline evaluation script for local vLLM-served models on Harbor task datasets.

Runs pass@k evaluation using the EndlessAgent (vLLM-backed) via `harbor run`,
then computes and reports pass@k (default k=1,2,3,4,8) metrics per task and in aggregate.

Usage:
    # Start vLLM server first, then:
    .venv/bin/python evaluate_baseline.py \\
        --dataset-path harbor_tasks_datagen_test/p1_difficulty \\
        --model Qwen/Qwen2.5-3B-Instruct \\
        --n-attempts 4 \\
        --n-concurrent 8 \\
        --jobs-dir baseline_results \\
        --job-name qwen3b_p1

    # Multiple models:
    .venv/bin/python evaluate_baseline.py \\
        --dataset-path harbor_tasks_datagen_test/p1_difficulty \\
        --model Qwen/Qwen2.5-3B-Instruct \\
        --model Qwen/Qwen2.5-4B-Instruct \\
        --n-attempts 4 \\
        --jobs-dir baseline_results

    # Dry run (no harbor execution, just prints the plan):
    .venv/bin/python evaluate_baseline.py \\
        --dataset-path harbor_tasks_datagen_test/p1_difficulty \\
        --model Qwen/Qwen2.5-3B-Instruct \\
        --dry-run
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
from math import comb
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
HARBOR_BIN = REPO_ROOT / ".venv" / "bin" / "harbor"
AGENT_IMPORT_PATH = "endless_harbor.endless_agent:EndlessAgent"

# Tasks whose environment setup exceeds the default 600s timeout get isolated.
HEAVY_TASK_ISOLATION_TIMEOUT_SEC = 3600       # trigger isolation if build > 1hr
HEAVY_TASK_BUILD_TIMEOUT_MULTIPLIER = 12.0    # 12 × 600s = 7200s (2hrs)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# pass@k
# ---------------------------------------------------------------------------

def compute_pass_at_k(n: int, c: int) -> dict[int, float]:
    """Unbiased pass@k estimator (Chen et al., 2021)."""
    results: dict[int, float] = {}
    for k in range(1, n + 1):
        if c == 0:
            results[k] = 0.0
        else:
            results[k] = 1.0 - (comb(n - c, k) / comb(n, k))
    return results


# ---------------------------------------------------------------------------
# Parse harbor job results
# ---------------------------------------------------------------------------

def collect_trials(job_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Read trial result.json files and group by task name."""
    from collections import defaultdict
    tasks: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for trial_dir in sorted(job_dir.iterdir()):
        result_file = trial_dir / "result.json"
        if not trial_dir.is_dir() or not result_file.exists():
            continue
        try:
            result = json.loads(result_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        task_name = result.get("task_name")
        if not task_name:
            continue

        vr = result.get("verifier_result") or {}
        rewards = vr.get("rewards") or {}
        reward = float(rewards.get("reward", 0.0))

        tasks[task_name].append({"reward": reward, "result": result})

    return dict(tasks)


def compute_metrics(
    trials_by_task: dict[str, list[dict[str, Any]]],
    ks: list[int],
) -> dict[str, Any]:
    """Compute per-task and aggregate pass@k metrics."""
    per_task: dict[str, Any] = {}
    for task_name, trials in sorted(trials_by_task.items()):
        n = len(trials)
        c = sum(1 for t in trials if t["reward"] >= 1.0)
        pass_at_k = compute_pass_at_k(n, c)
        per_task[task_name] = {
            "n": n,
            "successes": c,
            "pass_at_k": {k: pass_at_k.get(k, None) for k in ks},
        }

    if not per_task:
        return {"per_task": {}, "aggregate": {}}

    total = len(per_task)
    agg: dict[str, Any] = {
        "total_tasks": total,
        "tasks_solved": sum(1 for v in per_task.values() if v["successes"] > 0),
    }
    for k in ks:
        values = [v["pass_at_k"][k] for v in per_task.values() if v["pass_at_k"][k] is not None]
        agg[f"pass@{k}"] = sum(values) / len(values) if values else None

    return {"per_task": per_task, "aggregate": agg}


# ---------------------------------------------------------------------------
# Heavy-task isolation
# ---------------------------------------------------------------------------

def detect_heavy_tasks(dataset_path: Path, jobs_dir: Path, job_name: str) -> set[str]:
    """Return task names whose previous trials hit EnvironmentStartTimeoutError."""
    heavy: list[str] = []
    job_dir = jobs_dir / job_name
    if not job_dir.exists():
        return set()

    for trial_dir in job_dir.iterdir():
        if not trial_dir.is_dir():
            continue
        exc_file = trial_dir / "exception.txt"
        if exc_file.exists() and "EnvironmentStartTimeoutError" in exc_file.read_text():
            # task name = first 3 underscore-separated parts of the trial dir name
            task_name = "_".join(trial_dir.name.split("_")[:3])
            heavy.append(task_name)

    return set(heavy)


def split_dataset(dataset_path: Path, heavy_task_names: set[str]) -> tuple[Path | None, Path | None]:
    """Split dataset_path into (normal_dir, heavy_dir) temp directories.

    Returns (None, None) if no split needed, or one of the pair is None if empty.
    """
    all_tasks = [t for t in sorted(dataset_path.iterdir()) if t.is_dir()]
    normal = [t for t in all_tasks if t.name not in heavy_task_names]
    heavy = [t for t in all_tasks if t.name in heavy_task_names]

    if not heavy:
        return dataset_path, None

    tmp = Path(tempfile.mkdtemp(prefix="eval_split_"))
    normal_dir = tmp / "normal"
    heavy_dir = tmp / "heavy"
    normal_dir.mkdir()
    heavy_dir.mkdir()

    for t in normal:
        (normal_dir / t.name).symlink_to(t.resolve())
    for t in heavy:
        (heavy_dir / t.name).symlink_to(t.resolve())

    logger.info(f"Dataset split: {len(normal)} normal tasks, {len(heavy)} heavy tasks")
    logger.info(f"Heavy tasks: {[t.name for t in heavy]}")
    return normal_dir, heavy_dir




def run_harbor(
    dataset_path: Path,
    model: str,
    n_attempts: int,
    n_concurrent: int,
    jobs_dir: Path,
    job_name: str,
    vllm_base_url: str,
    dry_run: bool,
    environment_build_timeout_multiplier: float | None = None,
) -> Path:
    """Invoke harbor run and return the job output directory.

    If a previous run left EnvironmentStartTimeoutError trials, the affected tasks
    are automatically re-run in an isolated job with n_concurrent=1 and a 2hr
    build timeout, in parallel with the normal batch — provided CPU headroom exists.
    """
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_dir = jobs_dir / job_name

    # Detect heavy tasks from any prior run of this job
    heavy_names = detect_heavy_tasks(dataset_path, jobs_dir, job_name)
    if heavy_names:
        cpu_count = os.cpu_count() or 1
        active_jobs = len(multiprocessing.active_children())
        has_headroom = (cpu_count - active_jobs) >= 2
        if has_headroom:
            print(f"\n[Isolation] {len(heavy_names)} heavy task(s) detected, isolating to separate job.")
            normal_dir, heavy_dir = split_dataset(dataset_path, heavy_names)
        else:
            print(
                f"\n[Isolation] {len(heavy_names)} heavy task(s) detected but no CPU headroom "
                f"(cpus={cpu_count}, active={active_jobs}). Running sequentially with extended timeout.",
                file=sys.stderr,
            )
            normal_dir, heavy_dir = dataset_path, None
            environment_build_timeout_multiplier = HEAVY_TASK_BUILD_TIMEOUT_MULTIPLIER
    else:
        normal_dir, heavy_dir = dataset_path, None

    def _run_one(path: Path, name: str, n_conc: int, timeout_mult: float | None) -> None:
        cmd = [
            str(HARBOR_BIN), "run",
            "--agent-import-path", AGENT_IMPORT_PATH,
            "--model", model,
            "--path", str(path),
            "--n-attempts", str(n_attempts),
            "--n-concurrent", str(n_conc),
            "--jobs-dir", str(jobs_dir),
            "--job-name", name,
            "--yes",
            "--ae", f"VLLM_BASE_URL={vllm_base_url}",
        ]
        if timeout_mult is not None:
            cmd += ["--environment-build-timeout-multiplier", str(timeout_mult)]

        print(f"\n{'='*60}")
        print(f"Harbor run: {name}")
        print(f"  dataset:      {path}")
        print(f"  n_concurrent: {n_conc}")
        print(f"  timeout_mult: {timeout_mult or 1.0}x  ({(timeout_mult or 1.0) * 600 / 60:.0f} min)")
        print(f"  command:      {' '.join(cmd)}")
        print("=" * 60)

        if dry_run:
            print("[DRY RUN] Skipping harbor execution.")
            (jobs_dir / name).mkdir(parents=True, exist_ok=True)
            return

        result = subprocess.run(cmd, cwd=REPO_ROOT, text=True)
        if result.returncode != 0:
            print(f"[Warning] harbor run '{name}' exited with code {result.returncode}", file=sys.stderr)

    if heavy_dir is not None:
        # Launch heavy job in a separate process so both run in parallel
        heavy_job_name = f"{job_name}__heavy"
        heavy_proc = multiprocessing.Process(
            target=_run_one,
            args=(heavy_dir, heavy_job_name, 1, HEAVY_TASK_BUILD_TIMEOUT_MULTIPLIER),
            daemon=True,
        )
        heavy_proc.start()
        print(f"[Isolation] Heavy job '{heavy_job_name}' started (PID={heavy_proc.pid}, n_concurrent=1, timeout={HEAVY_TASK_BUILD_TIMEOUT_MULTIPLIER}x)")

        # Run normal batch in this process
        _run_one(normal_dir, job_name, n_concurrent, environment_build_timeout_multiplier)

        print(f"[Isolation] Waiting for heavy job '{heavy_job_name}' to finish...")
        heavy_proc.join()

        # Merge heavy results back into main job dir
        heavy_job_dir = jobs_dir / heavy_job_name
        if heavy_job_dir.exists():
            job_dir.mkdir(parents=True, exist_ok=True)
            for trial in heavy_job_dir.iterdir():
                if trial.is_dir():
                    dest = job_dir / trial.name
                    if not dest.exists():
                        shutil.copytree(trial, dest)
            print(f"[Isolation] Merged heavy results into {job_dir}")

        # Clean up temp split dirs
        try:
            shutil.rmtree(normal_dir.parent)
        except Exception:
            pass
    else:
        _run_one(normal_dir, job_name, n_concurrent, environment_build_timeout_multiplier)

    return job_dir


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_metrics(model: str, metrics: dict[str, Any], ks: list[int]) -> None:
    agg = metrics["aggregate"]
    print(f"\nModel: {model}")
    print(f"  Tasks total:  {agg.get('total_tasks', 0)}")
    print(f"  Tasks solved: {agg.get('tasks_solved', 0)}")
    for k in ks:
        val = agg.get(f"pass@{k}")
        display = f"{val:.4f}" if val is not None else "N/A"
        print(f"  pass@{k:<2}:       {display}")


def write_summary(
    output_dir: Path,
    job_name: str,
    model: str,
    dataset_path: Path,
    n_attempts: int,
    metrics: dict[str, Any],
    ks: list[int],
    timestamp: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    agg = metrics["aggregate"]

    # JSON
    summary_json = {
        "job_name": job_name,
        "model": model,
        "dataset_path": str(dataset_path),
        "n_attempts": n_attempts,
        "timestamp": timestamp,
        "aggregate": agg,
        "per_task": metrics["per_task"],
    }
    json_path = output_dir / f"{job_name}.json"
    json_path.write_text(json.dumps(summary_json, indent=2))
    print(f"\nJSON summary: {json_path}")

    # Markdown
    lines = [
        f"# Baseline Eval: {model}",
        f"",
        f"**Job:** `{job_name}`  ",
        f"**Dataset:** `{dataset_path}`  ",
        f"**Attempts (n):** {n_attempts}  ",
        f"**Timestamp:** {timestamp}  ",
        f"",
        f"## Aggregate Results",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total tasks | {agg.get('total_tasks', 0)} |",
        f"| Tasks solved | {agg.get('tasks_solved', 0)} |",
    ]
    for k in ks:
        val = agg.get(f"pass@{k}")
        display = f"{val:.4f}" if val is not None else "N/A"
        lines.append(f"| pass@{k} | {display} |")

    k_headers = "".join(f" pass@{k} |" for k in ks)
    k_divider = "".join("--------|" for _ in ks)
    lines += [
        f"",
        f"## Per-Task Results",
        f"",
        f"| Task | n | Successes |{k_headers}",
        f"|------|---|-----------|{k_divider}",
    ]
    for task_name, t in sorted(metrics["per_task"].items()):
        cells = ""
        for k in ks:
            v = t["pass_at_k"].get(k)
            cells += f" {v:.3f} |" if v is not None else " N/A |"
        lines.append(f"| {task_name} | {t['n']} | {t['successes']} |{cells}")

    md_path = output_dir / f"{job_name}.md"
    md_path.write_text("\n".join(lines))
    print(f"Markdown summary: {md_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Baseline pass@k evaluation for vLLM-served models on Harbor tasks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument(
        "--dataset-path", required=True, type=Path,
        help="Path to Harbor task dataset directory (e.g. harbor_tasks_datagen_test/p1_difficulty)",
    )
    ap.add_argument(
        "--model", action="append", dest="models", required=True,
        metavar="MODEL",
        help="Model name(s) to evaluate (HuggingFace id or name served by vLLM). Repeat for multiple.",
    )
    ap.add_argument(
        "--n-attempts", type=int, default=4,
        help="Number of solution attempts per task (n for pass@k). Default: 4",
    )
    ap.add_argument(
        "--n-concurrent", type=int, default=4,
        help="Number of concurrent harbor trials. Default: 4",
    )
    ap.add_argument(
        "--jobs-dir", type=Path, default=Path("baseline_results"),
        help="Directory to store harbor job outputs. Default: baseline_results/",
    )
    ap.add_argument(
        "--job-name", type=str, default=None,
        help="Override job name (default: <model_slug>_<dataset_slug>_<timestamp>)",
    )
    ap.add_argument(
        "--vllm-base-url", type=str, default="http://localhost:8000/v1",
        help="Base URL of the running vLLM server. Default: http://localhost:8000/v1",
    )
    ap.add_argument(
        "--output-dir", type=Path, default=Path("output"),
        help="Directory to write summary JSON and Markdown. Default: output/",
    )
    ap.add_argument(
        "--pass-at-k", type=int, action="append", dest="ks", default=None,
        metavar="K",
        help="Which k values to report. Default: 1, 2, 3, 4, 8. Repeat to add more.",
    )
    ap.add_argument(
        "--environment-build-timeout-multiplier", type=float, default=None,
        dest="environment_build_timeout_multiplier",
        help="Multiply the default 600s environment build timeout (e.g. 5.0 = 50 min). "
             "Use for tasks with heavy setup like large DB seeding.",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Print harbor commands without running them (useful for testing).",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    dataset_path = args.dataset_path.resolve()
    if not dataset_path.exists():
        print(f"Error: dataset path does not exist: {dataset_path}", file=sys.stderr)
        sys.exit(1)

    if not HARBOR_BIN.exists() and not args.dry_run:
        print(
            f"Error: harbor not found at {HARBOR_BIN}.\n"
            "Run: uv sync --extra harbor",
            file=sys.stderr,
        )
        sys.exit(1)

    ks = sorted(set(args.ks)) if args.ks else [1, 2, 3, 4, 8]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    all_results: list[dict[str, Any]] = []

    for model in args.models:
        model_slug = model.replace("/", "_").replace(".", "-")
        dataset_slug = dataset_path.name
        job_name = args.job_name or f"{model_slug}__{dataset_slug}__{timestamp}"

        job_dir = run_harbor(
            dataset_path=dataset_path,
            model=model,
            n_attempts=args.n_attempts,
            n_concurrent=args.n_concurrent,
            jobs_dir=args.jobs_dir,
            job_name=job_name,
            vllm_base_url=args.vllm_base_url,
            dry_run=args.dry_run,
            environment_build_timeout_multiplier=args.environment_build_timeout_multiplier,
        )

        if args.dry_run:
            print(f"[DRY RUN] Would collect results from {job_dir}")
            continue

        print(f"\nCollecting results from {job_dir} ...")
        trials_by_task = collect_trials(job_dir)
        if not trials_by_task:
            print(f"[Warning] No trial results found in {job_dir}", file=sys.stderr)
            continue

        metrics = compute_metrics(trials_by_task, ks)
        print_metrics(model, metrics, ks)
        write_summary(
            output_dir=args.output_dir,
            job_name=job_name,
            model=model,
            dataset_path=dataset_path,
            n_attempts=args.n_attempts,
            metrics=metrics,
            ks=ks,
            timestamp=timestamp,
        )

        all_results.append({"model": model, "job_name": job_name, "metrics": metrics})

    # Multi-model comparison table
    if len(all_results) > 1:
        print(f"\n{'='*60}")
        print("Model Comparison")
        print("=" * 60)
        header = f"{'Model':<45}" + "".join(f"  pass@{k:<4}" for k in ks)
        print(header)
        print("-" * len(header))
        for r in all_results:
            agg = r["metrics"]["aggregate"]
            row = f"{r['model']:<45}"
            for k in ks:
                val = agg.get(f"pass@{k}")
                row += f"  {val:.4f}  " if val is not None else "  N/A    "
            print(row)

        # Write combined summary
        combined = {
            "timestamp": timestamp,
            "dataset_path": str(dataset_path),
            "n_attempts": args.n_attempts,
            "models": [
                {
                    "model": r["model"],
                    "job_name": r["job_name"],
                    "aggregate": r["metrics"]["aggregate"],
                }
                for r in all_results
            ],
        }
        combined_path = args.output_dir / f"baseline_comparison__{timestamp}.json"
        args.output_dir.mkdir(parents=True, exist_ok=True)
        combined_path.write_text(json.dumps(combined, indent=2))
        print(f"\nCombined comparison: {combined_path}")


if __name__ == "__main__":
    main()
