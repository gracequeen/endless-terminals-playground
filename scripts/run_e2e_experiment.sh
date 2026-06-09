#!/usr/bin/env bash
# End-to-end experiment: pre-eval → train → post-eval → compare pass@1
#
# Usage:
#   bash scripts/run_e2e_experiment.sh
#
# Outputs (in results/harbor-ppo-t4-Qwen3.5-0.8B/):
#   experiment_config.json   — hyperparams, dataset, git sha
#   pre_train_test_eval.json — pass@1 on test set BEFORE training
#   post_train_test_eval.json — pass@1 on test set AFTER training
#   comparison.json          — delta pass@1 summary
set -e

export PATH="$HOME/.local/bin:$PATH"
export HF_HUB_ENABLE_HF_TRANSFER=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VLLM_USE_V1=0

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

MODEL="Qwen/Qwen3.5-0.8B"
MODEL_SHORT="Qwen3.5-0.8B"
RUN_NAME="harbor-ppo-t4-${MODEL_SHORT}"
CKPT_DIR="/tmp/skyrl_ckpts/${RUN_NAME}"
MANIFEST="$REPO_DIR/data/harbor_split.json"
RESULTS_DIR="$REPO_DIR/results/${RUN_NAME}"
VLLM_PORT=8001   # separate port from training vLLM (port 8000)
VLLM_API_BASE="http://127.0.0.1:${VLLM_PORT}/v1"

MAX_MODEL_LEN=4096
EVAL_MAX_TURNS=8
EVAL_CONCURRENCY=4

mkdir -p "$RESULTS_DIR"

# ---------------------------------------------------------------------------
# Helper: start a standalone vLLM server, wait until ready, return PID
# ---------------------------------------------------------------------------
start_vllm() {
    local model_path="$1"
    echo "[e2e] Starting vLLM server for $model_path on port $VLLM_PORT ..."
    python3 -m vllm.entrypoints.openai.api_server \
        --model "$model_path" \
        --dtype float16 \
        --port "$VLLM_PORT" \
        --max-model-len "$MAX_MODEL_LEN" \
        --enforce-eager \
        --disable-custom-all-reduce \
        --gpu-memory-utilization 0.6 \
        > "$RESULTS_DIR/vllm_server.log" 2>&1 &
    VLLM_PID=$!

    echo "[e2e] Waiting for vLLM to be ready (PID=$VLLM_PID)..."
    for i in $(seq 1 60); do
        if curl -sf "${VLLM_API_BASE}/models" > /dev/null 2>&1; then
            echo "[e2e] vLLM ready."
            return 0
        fi
        sleep 5
    done
    echo "[e2e] ERROR: vLLM did not start within 5 minutes." >&2
    kill "$VLLM_PID" 2>/dev/null || true
    exit 1
}

stop_vllm() {
    if [ -n "${VLLM_PID:-}" ]; then
        echo "[e2e] Stopping vLLM server (PID=$VLLM_PID)..."
        kill "$VLLM_PID" 2>/dev/null || true
        wait "$VLLM_PID" 2>/dev/null || true
        VLLM_PID=""
    fi
}

# ---------------------------------------------------------------------------
# Log experiment config (pre-train phase)
# ---------------------------------------------------------------------------
echo "[e2e] === Phase 0: Logging experiment config ==="
python3 train/harbor/log_experiment.py \
    --model "$MODEL" \
    --manifest "$MANIFEST" \
    --output "$RESULTS_DIR/experiment_config.json" \
    --phase pre_train \
    --run-name "$RUN_NAME" \
    --extra \
        eval.split=test \
        eval.max_turns=$EVAL_MAX_TURNS \
        eval.temperature=0.0 \
        eval.max_concurrency=$EVAL_CONCURRENCY \
        eval.max_input_tokens=$MAX_MODEL_LEN

# ---------------------------------------------------------------------------
# Phase 1: Pre-training eval on test set (base model)
# ---------------------------------------------------------------------------
echo "[e2e] === Phase 1: Pre-training eval (base model, test split) ==="
start_vllm "$MODEL"

python3 train/harbor/eval_harbor.py \
    --split test \
    --model "$MODEL_SHORT" \
    --api-base "$VLLM_API_BASE" \
    --manifest "$MANIFEST" \
    --task-dir harbor_tasks \
    --output "$RESULTS_DIR/pre_train_test_eval.json" \
    --trials-dir "/tmp/harbor_eval_trials/pre_train" \
    --max-turns $EVAL_MAX_TURNS \
    --max-concurrency $EVAL_CONCURRENCY \
    --temperature 0.0 \
    --max-input-tokens $MAX_MODEL_LEN \
    --timeout 300

stop_vllm

python3 train/harbor/log_experiment.py \
    --model "$MODEL" \
    --manifest "$MANIFEST" \
    --output "$RESULTS_DIR/experiment_config.json" \
    --phase pre_train \
    --run-name "$RUN_NAME"

echo "[e2e] Pre-training eval complete. Results: $RESULTS_DIR/pre_train_test_eval.json"

# ---------------------------------------------------------------------------
# Phase 2: PPO Training
# ---------------------------------------------------------------------------
echo "[e2e] === Phase 2: PPO Training ==="
bash scripts/run_harbor_t4.sh

echo "[e2e] Training complete. Checkpoint: $CKPT_DIR"

# ---------------------------------------------------------------------------
# Phase 3: Post-training eval on test set (fine-tuned model)
# ---------------------------------------------------------------------------
echo "[e2e] === Phase 3: Post-training eval (fine-tuned, test split) ==="

# Use HF export path from training
HF_CKPT="$CKPT_DIR/hf_export"
if [ ! -d "$HF_CKPT" ]; then
    echo "[e2e] WARNING: HF export not found at $HF_CKPT, falling back to latest SkyRL checkpoint"
    HF_CKPT=$(ls -td "$CKPT_DIR"/step_* 2>/dev/null | head -1 || echo "$CKPT_DIR")
fi
echo "[e2e] Using checkpoint: $HF_CKPT"

start_vllm "$HF_CKPT"

python3 train/harbor/eval_harbor.py \
    --split test \
    --model "$MODEL_SHORT" \
    --api-base "$VLLM_API_BASE" \
    --manifest "$MANIFEST" \
    --task-dir harbor_tasks \
    --output "$RESULTS_DIR/post_train_test_eval.json" \
    --trials-dir "/tmp/harbor_eval_trials/post_train" \
    --max-turns $EVAL_MAX_TURNS \
    --max-concurrency $EVAL_CONCURRENCY \
    --temperature 0.0 \
    --max-input-tokens $MAX_MODEL_LEN \
    --timeout 300

stop_vllm

python3 train/harbor/log_experiment.py \
    --model "$HF_CKPT" \
    --manifest "$MANIFEST" \
    --output "$RESULTS_DIR/experiment_config.json" \
    --phase post_train \
    --run-name "$RUN_NAME"

# ---------------------------------------------------------------------------
# Phase 4: Compare pass@1
# ---------------------------------------------------------------------------
echo "[e2e] === Phase 4: Comparing pre vs post training ==="
python3 - <<'PYEOF'
import json
from pathlib import Path

results_dir = Path("results/harbor-ppo-t4-Qwen3.5-0.8B")
pre  = json.load(open(results_dir / "pre_train_test_eval.json"))
post = json.load(open(results_dir / "post_train_test_eval.json"))

pre_sum  = pre["summary"]
post_sum = post["summary"]

delta_pass = post_sum["pass_at_1"] - pre_sum["pass_at_1"]
delta_reward = post_sum["avg_reward"] - pre_sum["avg_reward"]

print("\n" + "="*60)
print("  EXPERIMENT RESULTS: Pre vs Post Training Pass@1")
print("="*60)
print(f"  {'Metric':<25} {'Pre':>10} {'Post':>10} {'Delta':>10}")
print(f"  {'-'*55}")
print(f"  {'pass@1':<25} {pre_sum['pass_at_1']:>10.3f} {post_sum['pass_at_1']:>10.3f} {delta_pass:>+10.3f}")
print(f"  {'avg_reward':<25} {pre_sum['avg_reward']:>10.3f} {post_sum['avg_reward']:>10.3f} {delta_reward:>+10.3f}")
print(f"  {'n_success / n_tasks':<25} {pre_sum['n_success']}/{pre_sum['n_tasks']:>6}  {post_sum['n_success']}/{post_sum['n_tasks']:>6}")
print(f"\n  By difficulty:")
all_diffs = sorted(set(list(pre_sum['by_difficulty'].keys()) + list(post_sum['by_difficulty'].keys())))
for diff in all_diffs:
    pre_d  = pre_sum['by_difficulty'].get(diff, {})
    post_d = post_sum['by_difficulty'].get(diff, {})
    pre_p  = pre_d.get('pass_at_1', 0.0)
    post_p = post_d.get('pass_at_1', 0.0)
    print(f"    {diff:<12}: {pre_p:.3f} → {post_p:.3f}  ({post_p-pre_p:+.3f})")
print("="*60)

comparison = {
    "model_base": pre["model"],
    "model_trained": post["model"],
    "pre_train": {
        "pass_at_1": pre_sum["pass_at_1"],
        "avg_reward": pre_sum["avg_reward"],
        "n_success": pre_sum["n_success"],
        "n_tasks": pre_sum["n_tasks"],
        "by_difficulty": pre_sum["by_difficulty"],
    },
    "post_train": {
        "pass_at_1": post_sum["pass_at_1"],
        "avg_reward": post_sum["avg_reward"],
        "n_success": post_sum["n_success"],
        "n_tasks": post_sum["n_tasks"],
        "by_difficulty": post_sum["by_difficulty"],
    },
    "delta": {
        "pass_at_1": delta_pass,
        "avg_reward": delta_reward,
    },
}

out = results_dir / "comparison.json"
with open(out, "w") as fh:
    json.dump(comparison, fh, indent=2)
print(f"\n  Full comparison written to {out}")
PYEOF

echo "[e2e] === Done. Results in $RESULTS_DIR ==="
echo "  pre_train_test_eval.json"
echo "  post_train_test_eval.json"
echo "  comparison.json"
echo "  experiment_config.json"
