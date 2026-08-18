#!/bin/bash
# Evaluate Qwen3.5-4B and Qwen3.5-9B on easy tasks (harbor_tasks_easy/).
# Uses existing vLLM servers:
#   4B: ports 8001, 8002  (2 shards)
#   9B: ports 8000, 8006, 8007  (3 shards)
# n_attempts=8, pass@k for k=1,2,3,4,8
set -euo pipefail

REPO="/home/ec2-user/endless-terminals-playground"
LOG_DIR="$REPO/harbor_logs"
JOBS_DIR="$REPO/baseline_results"
OUTPUT_DIR="$REPO/output"
N_ATTEMPTS=8
N_CONCURRENT=8
PASS_AT_K="--pass-at-k 1 --pass-at-k 2 --pass-at-k 3 --pass-at-k 4 --pass-at-k 8"

mkdir -p "$LOG_DIR"

echo "=============================================="
echo "Easy task baseline eval"
echo "  4B: ports 8001 8002  (2 shards)"
echo "  9B: ports 8000 8006 8007  (3 shards)"
echo "  n_attempts=$N_ATTEMPTS  n_concurrent=$N_CONCURRENT"
echo "=============================================="

PIDS=()
LABELS=()

# --- Qwen3.5-4B shards ---
for i in 0 1; do
    PORT=$((8001 + i))
    SHARD_PATH="$REPO/harbor_tasks_easy_4b_shard${i}"
    JOB="Qwen_Qwen3-5-4B__easy_shard${i}__n${N_ATTEMPTS}"
    LOG="$LOG_DIR/eval_4b_easy_shard${i}.log"
    echo "Launching 4B shard $i (port $PORT): $JOB"
    "$REPO/.venv/bin/python" "$REPO/evaluate_baseline.py" \
        --dataset-path "$SHARD_PATH" \
        --model "Qwen/Qwen3.5-4B" \
        --n-attempts "$N_ATTEMPTS" \
        --n-concurrent "$N_CONCURRENT" \
        --jobs-dir "$JOBS_DIR" \
        --job-name "$JOB" \
        --output-dir "$OUTPUT_DIR" \
        --vllm-base-url "http://localhost:${PORT}/v1" \
        $PASS_AT_K \
        >> "$LOG" 2>&1 &
    PIDS+=($!)
    LABELS+=("4B shard $i")
    echo "  PID=${PIDS[-1]}  log=$LOG"
done

# --- Qwen3.5-9B shards ---
PORTS_9B=(8000 8006 8007)
for i in 0 1 2; do
    PORT="${PORTS_9B[$i]}"
    SHARD_PATH="$REPO/harbor_tasks_easy_9b_shard${i}"
    JOB="Qwen_Qwen3-5-9B__easy_shard${i}__n${N_ATTEMPTS}"
    LOG="$LOG_DIR/eval_9b_easy_shard${i}.log"
    echo "Launching 9B shard $i (port $PORT): $JOB"
    "$REPO/.venv/bin/python" "$REPO/evaluate_baseline.py" \
        --dataset-path "$SHARD_PATH" \
        --model "Qwen/Qwen3.5-9B" \
        --n-attempts "$N_ATTEMPTS" \
        --n-concurrent "$N_CONCURRENT" \
        --jobs-dir "$JOBS_DIR" \
        --job-name "$JOB" \
        --output-dir "$OUTPUT_DIR" \
        --vllm-base-url "http://localhost:${PORT}/v1" \
        $PASS_AT_K \
        >> "$LOG" 2>&1 &
    PIDS+=($!)
    LABELS+=("9B shard $i")
    echo "  PID=${PIDS[-1]}  log=$LOG"
done

echo ""
echo "All 5 eval jobs launched. Waiting for completion..."
echo "Monitor: tail -f harbor_logs/eval_4b_easy_shard*.log harbor_logs/eval_9b_easy_shard*.log"
echo ""

FAILED=0
for i in "${!PIDS[@]}"; do
    PID="${PIDS[$i]}"
    LABEL="${LABELS[$i]}"
    if wait "$PID"; then
        echo "  [OK] $LABEL"
    else
        echo "  [FAIL] $LABEL (exit code $?)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=============================================="
echo "All easy eval jobs complete. Failed: $FAILED / ${#PIDS[@]}"
echo "Results in: $OUTPUT_DIR/"
echo "=============================================="

# Merge shards and compute combined metrics
echo ""
echo "Merging shard results..."
"$REPO/.venv/bin/python" - <<'PYEOF'
import json
from pathlib import Path
from math import comb

REPO = Path("/home/ec2-user/endless-terminals-playground")
OUTPUT_DIR = REPO / "output"
JOBS_DIR = REPO / "baseline_results"
N = 8
KS = [1, 2, 3, 4, 8]

def compute_pass_at_k(n, c):
    results = {}
    for k in range(1, n + 1):
        if c == 0:
            results[k] = 0.0
        else:
            results[k] = 1.0 - (comb(n - c, k) / comb(n, k))
    return results

for model_tag, shards, model_id in [
    ("4B", [0, 1], "Qwen/Qwen3.5-4B"),
    ("9B", [0, 1, 2], "Qwen/Qwen3.5-9B"),
]:
    model_slug = "Qwen_Qwen3-5-4B" if model_tag == "4B" else "Qwen_Qwen3-5-9B"
    per_task = {}

    for i in shards:
        job_name = f"{model_slug}__easy_shard{i}__n{N}"
        job_dir = JOBS_DIR / job_name
        if not job_dir.exists():
            print(f"[Warning] Missing: {job_dir}")
            continue
        for trial_dir in sorted(job_dir.iterdir()):
            result_file = trial_dir / "result.json"
            if not trial_dir.is_dir() or not result_file.exists():
                continue
            try:
                result = json.loads(result_file.read_text())
            except Exception:
                continue
            task_name = result.get("task_name")
            if not task_name:
                continue
            vr = result.get("verifier_result") or {}
            reward = float((vr.get("rewards") or {}).get("reward", 0.0))
            per_task.setdefault(task_name, []).append(reward)

    if not per_task:
        print(f"[Warning] No results found for {model_tag}")
        continue

    agg = {"total_tasks": len(per_task), "tasks_solved": 0}
    pass_at_k_sums = {k: 0.0 for k in KS}
    task_results = {}
    for task, rewards in sorted(per_task.items()):
        n = len(rewards)
        c = sum(1 for r in rewards if r >= 1.0)
        if c > 0:
            agg["tasks_solved"] += 1
        pk = compute_pass_at_k(n, c)
        task_results[task] = {"n": n, "successes": c, "pass_at_k": {k: pk.get(k) for k in KS}}
        for k in KS:
            if pk.get(k) is not None:
                pass_at_k_sums[k] += pk[k]

    total = agg["total_tasks"]
    for k in KS:
        agg[f"pass@{k}"] = pass_at_k_sums[k] / total if total > 0 else None

    summary = {
        "model": model_id,
        "dataset": "harbor_tasks_easy (1607 tasks, difficulty=easy from v3_internet_access_config)",
        "n_attempts": N,
        "aggregate": agg,
        "per_task": task_results,
    }
    out_name = f"{model_slug}__easy__n{N}"
    (OUTPUT_DIR / f"{out_name}.json").write_text(json.dumps(summary, indent=2))

    lines = [
        f"# Baseline Eval: {model_id}",
        f"",
        f"**Dataset:** easy tasks from harbor_4.8opus_tasks_v3_internet_access_config (difficulty=easy, 1607 tasks)  ",
        f"**Attempts (n):** {N}  ",
        f"",
        f"## Aggregate Results",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total tasks | {agg['total_tasks']} |",
        f"| Tasks solved | {agg['tasks_solved']} |",
    ]
    for k in KS:
        v = agg.get(f"pass@{k}")
        lines.append(f"| pass@{k} | {v:.4f} |" if v is not None else f"| pass@{k} | N/A |")
    lines += [
        f"",
        f"## Per-Task Results",
        f"",
        f"| Task | n | Successes | pass@1 | pass@2 | pass@3 | pass@4 | pass@8 |",
        f"|------|---|-----------|--------|--------|--------|--------|--------|",
    ]
    for task, t in sorted(task_results.items()):
        pk = t["pass_at_k"]
        cells = " | ".join(f"{pk.get(k):.3f}" if pk.get(k) is not None else "N/A" for k in KS)
        lines.append(f"| {task} | {t['n']} | {t['successes']} | {cells} |")
    (OUTPUT_DIR / f"{out_name}.md").write_text("\n".join(lines))

    print(f"\n=== {model_id} — easy tasks (n={N}) ===")
    print(f"  Total tasks:  {agg['total_tasks']}")
    print(f"  Tasks solved: {agg['tasks_solved']}")
    for k in KS:
        v = agg.get(f"pass@{k}")
        print(f"  pass@{k}: {v:.4f}" if v is not None else f"  pass@{k}: N/A")
    print(f"  Saved: {OUTPUT_DIR}/{out_name}.json")

PYEOF

echo "Done."
