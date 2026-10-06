#!/usr/bin/env python3
"""Normalize Harbor trial outputs into task/trial directories for S3."""

import argparse
import json
import shutil
import tomllib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials-dir", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--n-samples", type=int, required=True)
    return parser.parse_args()


def safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "-" for c in value).strip("-")


def load_task_metadata(task_dir: Path) -> dict:
    task_toml = task_dir / "task.toml"
    if not task_toml.is_file():
        return {}
    with task_toml.open("rb") as handle:
        return tomllib.load(handle)


def reward_from(result: dict) -> float | None:
    verifier = result.get("verifier_result")
    if not verifier:
        return None
    reward = verifier.get("rewards", {}).get("reward")
    return float(reward) if reward is not None else None


def main() -> None:
    args = parse_args()
    args.archive_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_name": args.run_name,
        "checkpoint": args.checkpoint,
        "model": args.model,
        "dataset": args.dataset,
        "mode": args.mode,
        "n_samples_per_task": args.n_samples,
        "trials": [],
    }

    for source_result in sorted(args.trials_dir.glob("*/result.json")):
        result = json.loads(source_result.read_text())
        task_path_value = result.get("config", {}).get("task", {}).get("path")
        task_path = Path(task_path_value) if task_path_value else Path()
        metadata = load_task_metadata(task_path) if task_path_value else {}
        problem_name = (
            metadata.get("task", {}).get("name")
            or result.get("task_name")
            or task_path.parent.name
            or "unknown-task"
        )
        task_slug = safe_name(problem_name.split("/")[-1])
        trial_name = safe_name(result.get("trial_name") or source_result.parent.name)
        destination = args.archive_dir / task_slug / trial_name
        destination.mkdir(parents=True, exist_ok=True)

        source_solution = source_result.parent / "agent" / "trajectory.json"
        solution_path = destination / "solution.json"
        if source_solution.is_file():
            shutil.copy2(source_solution, solution_path)
            native_solution_path = destination / "agent" / "trajectory.json"
            native_solution_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_solution, native_solution_path)
            solution_source = str(source_solution)
            harbor_solution_path = "agent/trajectory.json"
        else:
            solution_path.write_text(
                json.dumps({"agent_result": result.get("agent_result")}, indent=2) + "\n"
            )
            solution_source = "result.json:agent_result"
            harbor_solution_path = None

        reward = reward_from(result)
        exception = result.get("exception_info")
        status = "error" if exception or reward is None else ("passed" if reward > 0 else "failed")
        normalized = {
            "schema_version": 1,
            "run": {
                "name": args.run_name,
                "checkpoint": args.checkpoint,
                "model": args.model,
                "dataset": args.dataset,
                "mode": args.mode,
                "n_samples_per_task": args.n_samples,
            },
            "problem": {
                "name": problem_name,
                "path": str(task_path) if task_path_value else None,
                "checksum": result.get("task_checksum"),
                "task": metadata.get("task", {}),
                "metadata": metadata.get("metadata", {}),
                "environment": metadata.get("environment", {}),
            },
            "trial": {
                "id": result.get("id"),
                "name": result.get("trial_name"),
                "started_at": result.get("started_at"),
                "finished_at": result.get("finished_at"),
                "agent": result.get("agent_info"),
                "exception": exception,
            },
            "outcome": {
                "status": status,
                "passed": status == "passed",
                "reward": reward,
                "verifier": result.get("verifier_result"),
            },
            "raw_solution": {
                "path": "solution.json",
                "harbor_path": harbor_solution_path,
                "source": solution_source,
            },
        }
        (destination / "result.json").write_text(json.dumps(normalized, indent=2) + "\n")
        shutil.copy2(source_result, destination / "harbor-result.json")
        manifest["trials"].append(
            {
                "problem": problem_name,
                "trial": result.get("trial_name"),
                "status": status,
                "reward": reward,
                "path": f"{task_slug}/{trial_name}",
            }
        )

    manifest["trial_count"] = len(manifest["trials"])
    manifest["passed_count"] = sum(t["status"] == "passed" for t in manifest["trials"])
    (args.archive_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        f"Archived {manifest['trial_count']} trials "
        f"({manifest['passed_count']} passed) to {args.archive_dir}"
    )


if __name__ == "__main__":
    main()
