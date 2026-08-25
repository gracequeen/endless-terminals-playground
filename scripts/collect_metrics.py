"""
Collects training metrics from SkyRL log and Harbor eval exports.
Writes structured JSON files and optionally uploads to S3.

Usage:
  python collect_metrics.py --log train_debug.log --export-dir exports/ --out-dir metrics/ [--s3-prefix s3://...]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ── regex patterns for SkyRL console log ─────────────────────────────────────
# Log format: each metric is on its own line as  'key/name': 'value',
# Step number appears as  'trainer/global_step': N,  (integer, no quotes)
# Metrics block is bounded by "Finished: 'step'" ... "Started: 'step'"

METRIC_RE = {
    "avg_pass_at_2":   re.compile(r"'reward/avg_pass_at_2':\s*'([\d.]+)'"),
    "avg_raw_reward":  re.compile(r"'loss/avg_final_rewards':\s*'([\d.]+)'"),
    "std_reward":      re.compile(r"'reward/std_reward':\s*'([\d.eE+\-]+)'"),
    "policy_loss":     re.compile(r"'policy/policy_loss':\s*'([-\d.eE+]+)'"),
    "policy_kl":       re.compile(r"'policy/policy_kl':\s*'([-\d.eE+]+)'"),
    "policy_entropy":  re.compile(r"'policy/policy_entropy':\s*'([-\d.eE+]+)'"),
    "grad_norm":       re.compile(r"'policy/grad_norm':\s*'([\d.eE+]+)'"),
    "response_length": re.compile(r"'policy/response_length':\s*'([\d.]+)'"),
    "sequence_length": re.compile(r"'policy/sequence_length':\s*'([\d.]+)'"),
}

STEP_RE = re.compile(r"'trainer/global_step':\s*(\d+)")
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def parse_training_log(log_path: str) -> list[dict]:
    """Parse SkyRL training log → list of per-step metric dicts."""
    steps = {}
    current_block: dict = {}
    in_metrics_block = False

    with open(log_path) as f:
        for line in f:
            clean = ANSI_RE.sub('', line)

            if "Finished: 'step'" in clean:
                in_metrics_block = True
                current_block = {}
                continue

            if "Started: 'step'" in clean:
                in_metrics_block = False
                continue

            if not in_metrics_block:
                continue

            step_m = STEP_RE.search(clean)
            if step_m:
                step_num = int(step_m.group(1))
                current_block["step"] = step_num
                steps[step_num] = dict(current_block)
                in_metrics_block = False
                continue

            for name, pattern in METRIC_RE.items():
                if name not in current_block:
                    m = pattern.search(clean)
                    if m:
                        current_block[name] = float(m.group(1))

    return sorted(steps.values(), key=lambda x: x["step"])


def parse_eval_exports(export_dir: str) -> dict[str, dict]:
    """
    Parse Harbor eval exports.

    Actual structure (confirmed from S3):
      export_dir/
        dumped_evals/
          global_step_N_evals/
            <encoded_task_path>.jsonl   ← one file per task

    Each JSONL file contains one line per attempt; each line is a JSON object
    with a 'score' field (0.0 or 1.0) and a 'data_source' field (task path).
    """
    results = {}
    dumped_dir = Path(export_dir) / "dumped_evals"
    if not dumped_dir.exists():
        return results

    for eval_dir in sorted(dumped_dir.iterdir()):
        if not eval_dir.is_dir():
            continue

        per_task: dict[str, list[float]] = {}

        for jsonl_file in sorted(eval_dir.glob("*.jsonl")):
            scores = []
            task_id = jsonl_file.stem  # fallback: encoded filename
            try:
                with open(jsonl_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        # use data_source as task_id if available (cleaner path)
                        if "data_source" in obj:
                            task_id = obj["data_source"]
                        scores.append(float(obj.get("score", 0)))
            except OSError:
                continue

            if scores:
                per_task[task_id] = scores

        if not per_task:
            continue

        # Filter out Harbor metadata keys (not real tasks)
        real_tasks = {k: v for k, v in per_task.items() if k != "aggregated_results"}
        if not real_tasks:
            continue

        # pass_any: task solved in any turn (the meaningful eval metric)
        # pass_at_1 / pass_at_2: solved on turn 1 or 2 (less useful for multi-turn)
        pass_any = sum(1 for scores in real_tasks.values() if any(s > 0 for s in scores)) / len(real_tasks)
        pass2 = sum(1 for scores in real_tasks.values() if any(s > 0 for s in scores[:2])) / len(real_tasks)
        pass1 = sum(1 for scores in real_tasks.values() if scores and scores[0] > 0) / len(real_tasks)

        results[eval_dir.name] = {
            "eval_dir": str(eval_dir),
            "per_task": real_tasks,
            "avg_score_pass_at_1": round(pass_any, 4),
            "avg_score_pass_at_2": round(pass2, 4),
            "num_tasks": len(real_tasks),
        }

    return results


def flag_metrics(step_metrics: list[dict]) -> list[dict]:
    """Add warning flags to each step based on thresholds."""
    flagged = []
    for m in step_metrics:
        flags = []
        if m.get("std_reward", 1) < 0.05:
            flags.append("std_reward_near_zero")
        if m.get("policy_entropy", 1) < 0.02:
            flags.append("entropy_collapse")
        if m.get("grad_norm", 0) > 50:
            flags.append("grad_norm_spike")
        if m.get("policy_loss", 0) > 100:
            flags.append("policy_loss_explosion")
        if m.get("avg_pass_at_2", 0) > 0.9:
            flags.append("near_ceiling")
        m = {**m, "flags": flags}
        flagged.append(m)
    return flagged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log",        required=True,  help="Path to train_debug.log")
    parser.add_argument("--export-dir", required=True,  help="Path to Harbor eval export dir")
    parser.add_argument("--out-dir",    required=True,  help="Output directory for JSON files")
    parser.add_argument("--s3-prefix",  default=None,   help="S3 prefix to upload results (optional)")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # training metrics
    training_metrics = []
    if os.path.exists(args.log):
        training_metrics = flag_metrics(parse_training_log(args.log))
        print(f"Parsed {len(training_metrics)} steps from training log")
    else:
        print(f"Warning: log file not found: {args.log}")

    training_out = os.path.join(args.out_dir, "training_metrics.json")
    with open(training_out, "w") as f:
        json.dump(training_metrics, f, indent=2)
    print(f"Written: {training_out}")

    # eval metrics
    eval_results = parse_eval_exports(args.export_dir)
    if eval_results:
        print(f"Parsed eval results from {len(eval_results)} eval checkpoints")
    else:
        print(f"No eval exports found in: {args.export_dir}")

    eval_out = os.path.join(args.out_dir, "eval_metrics.json")
    with open(eval_out, "w") as f:
        json.dump(eval_results, f, indent=2)
    print(f"Written: {eval_out}")

    # combined summary
    summary = {
        "num_training_steps": len(training_metrics),
        "num_evals": len(eval_results),
        "training_metrics": training_metrics,
        "eval_metrics": eval_results,
    }
    summary_out = os.path.join(args.out_dir, "metrics_summary.json")
    with open(summary_out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Written: {summary_out}")

    # upload to S3
    if args.s3_prefix:
        for fname in ["training_metrics.json", "eval_metrics.json", "metrics_summary.json"]:
            local = os.path.join(args.out_dir, fname)
            s3_dest = f"{args.s3_prefix.rstrip('/')}/{fname}"
            result = subprocess.run(["aws", "s3", "cp", local, s3_dest], capture_output=True)
            if result.returncode == 0:
                print(f"Uploaded: {s3_dest}")
            else:
                print(f"Warning: upload failed for {fname}: {result.stderr.decode()}", file=sys.stderr)


if __name__ == "__main__":
    main()
