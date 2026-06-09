"""
eval_harbor.py — standalone pass@1 evaluator for Harbor tasks.

Runs Harbor trials directly (no Ray, no PPO) against a vLLM HTTP endpoint.
Used for pre-training and post-training evaluation to compare pass@1 scores.

Usage:
    # Start vLLM server first:
    python3 -m vllm.entrypoints.openai.api_server \
        --model Qwen/Qwen3.5-0.8B --dtype float16 --port 8000

    # Then run eval:
    python3 train/harbor/eval_harbor.py \
        --split test \
        --model Qwen/Qwen3.5-0.8B \
        --api-base http://127.0.0.1:8000/v1 \
        --manifest data/harbor_split.json \
        --task-dir harbor_tasks \
        --output results/pre_train_test_eval.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Summary computation (pure, no Harbor deps — importable for tests)
# ---------------------------------------------------------------------------

def compute_summary(task_results: list[dict]) -> dict:
    """Compute pass@1, avg_reward, num_turns summary from task result list."""
    if not task_results:
        return {"pass_at_1": 0.0, "avg_reward": 0.0, "avg_turns": 0.0,
                "n_tasks": 0, "n_success": 0, "by_difficulty": {}}

    n = len(task_results)
    n_success = sum(1 for r in task_results if r.get("reward", 0.0) > 0)
    avg_reward = sum(r.get("reward", 0.0) for r in task_results) / n
    avg_turns = sum(r.get("num_turns", 0) for r in task_results) / n

    # Group by difficulty
    by_diff: dict[str, list[dict]] = {}
    for r in task_results:
        diff = r.get("difficulty", "unknown")
        by_diff.setdefault(diff, []).append(r)

    by_difficulty = {}
    for diff, results in sorted(by_diff.items()):
        nd = len(results)
        ns = sum(1 for r in results if r.get("reward", 0.0) > 0)
        by_difficulty[diff] = {
            "n_tasks": nd,
            "n_success": ns,
            "pass_at_1": ns / nd if nd > 0 else 0.0,
            "avg_reward": sum(r.get("reward", 0.0) for r in results) / nd,
        }

    return {
        "pass_at_1": n_success / n,
        "avg_reward": avg_reward,
        "avg_turns": avg_turns,
        "n_tasks": n,
        "n_success": n_success,
        "by_difficulty": by_difficulty,
    }


def load_tasks_from_manifest(
    manifest_path: str | Path,
    split: str,
    task_dir: str | Path,
) -> list[dict]:
    """Return list of {name, path, difficulty} for tasks in the given split."""
    manifest_path = Path(manifest_path)
    task_dir = Path(task_dir)

    with manifest_path.open() as fh:
        manifest = json.load(fh)

    valid_splits = {"train", "eval", "test"}
    if split not in valid_splits:
        raise ValueError(f"split must be one of {valid_splits}, got {split!r}")

    entries = manifest[split]
    difficulty_map: dict[str, str] = {}
    for entry in manifest.get("train", []) + manifest.get("eval", []) + manifest.get("test", []):
        # entries are task names (strings)
        pass

    # Read difficulties from task.toml
    tasks = []
    for name in entries:
        path = task_dir / name
        difficulty = _read_difficulty(path)
        tasks.append({"name": name, "path": str(path.resolve()), "difficulty": difficulty})
    return tasks


def _read_difficulty(task_path: Path) -> str:
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return "unknown"
    toml_path = task_path / "task.toml"
    if not toml_path.exists():
        return "unknown"
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)
    return data.get("metadata", {}).get("difficulty", "unknown")


# ---------------------------------------------------------------------------
# Harbor trial runner
# ---------------------------------------------------------------------------

async def run_trial(
    task: dict,
    model_name: str,
    api_base: str,
    trials_dir: str,
    max_turns: int,
    temperature: float,
    max_input_tokens: int,
    timeout_sec: float,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Run a single Harbor trial and return result dict."""
    from harbor.trial.trial import Trial
    from harbor.models.trial.config import TrialConfig

    config = {
        "task": {"path": task["path"]},
        "trials_dir": trials_dir,
        "agent": {
            "name": "terminus-2",
            "model_name": f"hosted_vllm/{model_name}",
            "override_timeout_sec": timeout_sec,
            "kwargs": {
                "api_base": api_base,
                "session_id": uuid4().hex,
                "max_turns": max_turns,
                "temperature": temperature,
                "enable_summarize": False,
                "collect_rollout_details": False,
                "suppress_max_turns_warning": True,
                "model_info": {
                    "max_input_tokens": max_input_tokens,
                    "max_output_tokens": max_input_tokens,
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0,
                },
                "llm_kwargs": {"timeout": timeout_sec, "max_retries": 0, "top_p": 1.0},
            },
        },
        "environment": {
            "type": "docker",
            "override_cpus": 1,
            "override_memory_mb": 2048,
            "suppress_override_warnings": True,
        },
        "verifier": {"disable": False},
    }

    async with semaphore:
        try:
            trial_config = TrialConfig.model_validate(config)
            trial = await Trial.create(trial_config)
            result = await trial.run()

            reward = 0.0
            stop_reason = "complete"
            num_turns = 0

            if result.exception_info:
                stop_reason = result.exception_info.exception_type or "error"
            if result.verifier_result:
                reward = float(result.verifier_result.rewards.get("reward", 0.0))
            if result.agent_result and result.agent_result.metadata:
                num_turns = result.agent_result.metadata.get("n_episodes", 0)

            return {
                "name": task["name"],
                "difficulty": task["difficulty"],
                "reward": reward,
                "num_turns": num_turns,
                "stop_reason": stop_reason,
            }
        except Exception as e:
            return {
                "name": task["name"],
                "difficulty": task["difficulty"],
                "reward": 0.0,
                "num_turns": 0,
                "stop_reason": f"error: {e}",
            }


async def run_eval(
    tasks: list[dict],
    model_name: str,
    api_base: str,
    trials_dir: str,
    max_turns: int,
    temperature: float,
    max_input_tokens: int,
    timeout_sec: float,
    max_concurrency: int,
) -> list[dict]:
    """Run all trials concurrently (up to max_concurrency) and return results."""
    semaphore = asyncio.Semaphore(max_concurrency)
    coros = [
        run_trial(
            task=t,
            model_name=model_name,
            api_base=api_base,
            trials_dir=trials_dir,
            max_turns=max_turns,
            temperature=temperature,
            max_input_tokens=max_input_tokens,
            timeout_sec=timeout_sec,
            semaphore=semaphore,
        )
        for t in tasks
    ]
    results = await asyncio.gather(*coros)
    return list(results)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_results_table(task_results: list[dict], summary: dict) -> None:
    print(f"\n{'Task':<40} {'Difficulty':<12} {'Reward':>8} {'Turns':>6} {'Stop':<20}")
    print("-" * 90)
    for r in sorted(task_results, key=lambda x: x["difficulty"]):
        status = "✓" if r["reward"] > 0 else "✗"
        print(f"{status} {r['name']:<38} {r['difficulty']:<12} {r['reward']:>8.2f} "
              f"{r['num_turns']:>6} {r['stop_reason'][:20]:<20}")
    print("-" * 90)
    print(f"\n{'Summary':}")
    print(f"  pass@1:      {summary['pass_at_1']:.3f} ({summary['n_success']}/{summary['n_tasks']})")
    print(f"  avg_reward:  {summary['avg_reward']:.3f}")
    print(f"  avg_turns:   {summary['avg_turns']:.1f}")
    print(f"\n  By difficulty:")
    for diff, stats in summary["by_difficulty"].items():
        print(f"    {diff:<10}: pass@1={stats['pass_at_1']:.3f} "
              f"({stats['n_success']}/{stats['n_tasks']})")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a model on Harbor tasks (pass@1).")
    parser.add_argument("--split", choices=["train", "eval", "test"], default="test")
    parser.add_argument("--model", required=True, help="Model name as served by vLLM")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000/v1",
                        help="vLLM OpenAI-compatible API base URL")
    parser.add_argument("--manifest", default="data/harbor_split.json")
    parser.add_argument("--task-dir", default="harbor_tasks")
    parser.add_argument("--output", required=True, help="Path to write results JSON")
    parser.add_argument("--trials-dir", default="/tmp/harbor_eval_trials")
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Use 0.0 for deterministic greedy eval")
    parser.add_argument("--max-input-tokens", type=int, default=4096)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()

    tasks = load_tasks_from_manifest(args.manifest, args.split, args.task_dir)
    print(f"Evaluating {len(tasks)} tasks (split={args.split}) with model={args.model}")
    print(f"  api_base={args.api_base}, max_turns={args.max_turns}, "
          f"concurrency={args.max_concurrency}, temperature={args.temperature}")

    t0 = time.time()
    task_results = asyncio.run(run_eval(
        tasks=tasks,
        model_name=args.model,
        api_base=args.api_base,
        trials_dir=args.trials_dir,
        max_turns=args.max_turns,
        temperature=args.temperature,
        max_input_tokens=args.max_input_tokens,
        timeout_sec=args.timeout,
        max_concurrency=args.max_concurrency,
    ))
    elapsed = time.time() - t0

    summary = compute_summary(task_results)
    print_results_table(task_results, summary)
    print(f"\n  Total elapsed: {elapsed:.1f}s")

    output = {
        "split": args.split,
        "model": args.model,
        "api_base": args.api_base,
        "config": {
            "max_turns": args.max_turns,
            "temperature": args.temperature,
            "max_input_tokens": args.max_input_tokens,
            "max_concurrency": args.max_concurrency,
            "timeout_sec": args.timeout,
        },
        "elapsed_sec": elapsed,
        "tasks": task_results,
        "summary": summary,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        json.dump(output, fh, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
