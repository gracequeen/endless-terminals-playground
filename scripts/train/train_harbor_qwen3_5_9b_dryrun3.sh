#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
source /tmp/sky/bin/activate

# Locate CUDA_HOME
if [ -d "/usr/local/cuda" ] && [ -f "/usr/local/cuda/bin/nvcc" ]; then
  export CUDA_HOME=/usr/local/cuda
elif [ -f "/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13/bin/nvcc" ]; then
  export CUDA_HOME=/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13
else
  NVCC_PATH=$(which nvcc 2>/dev/null || true)
  [ -n "$NVCC_PATH" ] && export CUDA_HOME=$(dirname $(dirname "$NVCC_PATH")) || { echo "ERROR: nvcc not found" >&2; exit 1; }
fi
export PATH="$CUDA_HOME/bin:$PATH"
echo "Using CUDA_HOME=$CUDA_HOME"
rm -rf ~/.cache/flashinfer

# ── config ─────────────────────────────────────────────────────────────────
MAX_TURNS=8          # must match default.yaml agent.kwargs.max_turns below
TRAIN_STEPS=5
CKPT_INTERVAL=5
EVAL_INTERVAL=5
EVAL_BATCH=8         # 8×2=16 concurrent containers — matches training concurrency (validated in dryrun2D)

TASKS_DIR_457="/home/ec2-user/xin/harbor_tasks_457"
TASKS_DIR_8192="/home/ec2-user/xin/harbor_tasks_8192_deduped"
TASKS_DIR_V3="/home/ec2-user/xin/harbor_tasks_easy_9b"
DATA_DIR="/home/ec2-user/xin/data_harbor_combined"
CKPT_DIR="/home/ec2-user/xin/checkpoints_harbor_qwen3_5_9b_dryrun3"
EXPORT_DIR="/home/ec2-user/xin/exports_harbor_qwen3_5_9b_dryrun3"
METRICS_DIR="/home/ec2-user/xin/metrics_dryrun3"
S3_CKPT="s3://endless-terminals-training/$(date +%Y%m%d)_combined-data_dryrun3_grpo_qwen3.5-9b_${TRAIN_STEPS}steps"

mkdir -p "$CKPT_DIR" "$EXPORT_DIR" "$METRICS_DIR" "$DATA_DIR"

export FLASHINFER_DISABLE_VERSION_CHECK=1

# ── Docker cleanup loop (every 60s) ────────────────────────────────────────
(
  while true; do
    sleep 60
    docker ps -aq --filter "status=exited" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -aq --filter "status=dead" | xargs -r docker rm -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
  done
) &
DOCKER_CLEANUP_PID=$!

# ── download tasks ──────────────────────────────────────────────────────────
if [ ! -d "$TASKS_DIR_457" ] || [ -z "$(ls -A $TASKS_DIR_457 2>/dev/null)" ]; then
  echo "Downloading 457 tasks..."
  mkdir -p "$TASKS_DIR_457"
  for part in 1 2 3 4; do
    aws s3 sync \
      "s3://endless-terminals-training/data/harbor_4.5opus_tasks/harbor_tasks_claude4.5_opus/harbor_tasks_part2_2-${part}/" \
      "$TASKS_DIR_457/" --no-progress
  done
else
  echo "Using existing 457 tasks"
fi

if [ ! -d "$TASKS_DIR_8192" ] || [ -z "$(ls -A $TASKS_DIR_8192 2>/dev/null)" ]; then
  echo "Downloading 8192 deduped tasks..."
  mkdir -p "$TASKS_DIR_8192"
  aws s3 sync s3://endless-terminals-training/data/harbor_tasks_8192_deduped/ \
    "$TASKS_DIR_8192/" --no-progress
else
  echo "Using existing 8192 tasks"
fi

if [ ! -d "$TASKS_DIR_V3" ] || [ -z "$(ls -A $TASKS_DIR_V3 2>/dev/null)" ]; then
  echo "Downloading v3 easy 9B tasks..."
  mkdir -p "$TASKS_DIR_V3"
  for shard in 0 1 2; do
    aws s3 sync \
      "s3://endless-terminals-training/data/harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_9b_shard${shard}/" \
      "$TASKS_DIR_V3/" --no-progress
  done
else
  echo "Using existing v3 easy 9B tasks"
fi

# ── download combined parquets ──────────────────────────────────────────────
echo "Downloading combined parquets..."
aws s3 cp s3://endless-terminals-training/prepared_data/train_combined_v1v2v3easy9b.parquet \
  "$DATA_DIR/train_combined_v1v2v3easy9b.parquet" --no-progress
aws s3 cp s3://endless-terminals-training/prepared_data/val_combined_v1v2v3easy9b.parquet \
  "$DATA_DIR/val_combined_v1v2v3easy9b.parquet" --no-progress

# ── write task dir lists to JSON files ──────────────────────────────────────
python3.13 -c "
import pandas as pd, json
df = pd.read_parquet('$DATA_DIR/train_combined_v1v2v3easy9b.parquet')
dirs = list(df['extra_info'].apply(lambda x: x['task_dir']).unique())
with open('$DATA_DIR/train_task_dirs_v3.json', 'w') as f:
    json.dump(dirs, f)
print(f'Train: {len(dirs)} task dirs → $DATA_DIR/train_task_dirs_v3.json')
"
python3.13 -c "
import pandas as pd, json
df = pd.read_parquet('$DATA_DIR/val_combined_v1v2v3easy9b.parquet')
dirs = list(df['extra_info'].apply(lambda x: x['task_dir']).unique())
with open('$DATA_DIR/val_task_dirs_v3.json', 'w') as f:
    json.dump(dirs, f)
print(f'Val: {len(dirs)} task dirs → $DATA_DIR/val_task_dirs_v3.json')
"

# ── set max_turns in default.yaml ───────────────────────────────────────────
python3.13 - "$MAX_TURNS" <<'PYEOF'
import sys, yaml
max_turns = int(sys.argv[1])
path = "SkyRL/examples/train_integrations/harbor/harbor_trial_config/default.yaml"
with open(path) as f:
    cfg = yaml.safe_load(f)
cfg.setdefault("agent", {}).setdefault("kwargs", {})["max_turns"] = max_turns
with open(path, "w") as f:
    yaml.dump(cfg, f, default_flow_style=False)
print(f"Set default.yaml agent.kwargs.max_turns={max_turns}")
PYEOF

LOG_FILE="$CKPT_DIR/train_debug.log"

# ── optional: patch trainer.py to log pass@1/2/4 in addition to pass@n ──────
# Set PATCH_PASSATK=false to skip (e.g. if n_samples < 4 or already patched)
if [ "${PATCH_PASSATK:-true}" = "true" ]; then
python3.13 <<'PYEOF'
from pathlib import Path
TRAINER = Path("SkyRL/skyrl/train/trainer.py")
OLD = '''\
        reward_metrics = {
            f"reward/avg_pass_at_{n_samples_per_prompt}": overall_metrics["pass_at_n"],
            "reward/avg_raw_reward": overall_metrics["avg_score"],
            "reward/std_reward": overall_metrics.get("std_reward", 0.0),
            "reward/mean_positive_reward": overall_metrics["mean_positive_reward"],
        }'''
NEW = '''\
        _raw_rewards = generator_output["rewards"]
        _uid_to_rewards: dict = {}
        for _i, _uid in enumerate(uids):
            _r = _raw_rewards[_i]
            _uid_to_rewards.setdefault(_uid, []).append(_r[-1] if isinstance(_r, list) else _r)
        _pass_at_k = {
            f"reward/avg_pass_at_{_k}": sum(
                1 for _v in _uid_to_rewards.values() if any(_r > 0 for _r in _v[:_k])
            ) / len(_uid_to_rewards)
            for _k in [1, 2, 4]
            if _k < n_samples_per_prompt
        }
        reward_metrics = {
            f"reward/avg_pass_at_{n_samples_per_prompt}": overall_metrics["pass_at_n"],
            **_pass_at_k,
            "reward/avg_raw_reward": overall_metrics["avg_score"],
            "reward/std_reward": overall_metrics.get("std_reward", 0.0),
            "reward/mean_positive_reward": overall_metrics["mean_positive_reward"],
        }'''
text = TRAINER.read_text()
if NEW in text:
    print("pass@k patch already applied")
elif OLD not in text:
    print("WARNING: pass@k patch target not found — skipping")
else:
    TRAINER.write_text(text.replace(OLD, NEW, 1))
    print("Applied pass@k patch to trainer.py")
PYEOF
fi

# ── background: upload checkpoints ─────────────────────────────────────────
(
  UPLOADED=""
  while true; do
    for step_dir in "$CKPT_DIR"/global_step_*/; do
      [ -d "$step_dir" ] || continue
      step=$(basename "$step_dir")
      if [ -f "$step_dir/trainer_state.pt" ] && ! echo "$UPLOADED" | grep -q "$step"; then
        echo "[uploader] Uploading $step..."
        aws s3 sync "$step_dir" "$S3_CKPT/$step/" --no-progress --quiet
        latest=$(cat "$CKPT_DIR/latest_ckpt_global_step.txt" 2>/dev/null)
        if [ -n "$latest" ] && [ "$step" != "global_step_$latest" ]; then
          rm -rf "$step_dir"
          echo "[uploader] $step deleted from disk"
        fi
        UPLOADED="$UPLOADED $step"
      fi
    done
    sleep 30
  done
) &
UPLOADER_PID=$!

# ── background: collect and upload metrics every 30s ───────────────────────
(
  while true; do
    sleep 30
    python3.13 scripts/collect_metrics.py \
      --log "$LOG_FILE" \
      --export-dir "$EXPORT_DIR" \
      --out-dir "$METRICS_DIR" \
      --s3-prefix "$S3_CKPT/metrics" 2>/dev/null || true
  done
) &
METRICS_PID=$!

# ── background: sync log ───────────────────────────────────────────────────
(
  while true; do
    sleep 60
    aws s3 cp "$LOG_FILE" "$S3_CKPT/train_debug.log" --quiet 2>/dev/null || true
    aws s3 sync "$EXPORT_DIR/" "$S3_CKPT/evals/" --quiet 2>/dev/null || true
  done
) &
LOG_SYNC_PID=$!

# ── run training ────────────────────────────────────────────────────────────
cd SkyRL
RAY_memory_usage_threshold=0.99 \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
HF_HOME=/tmp/hf_cache \
WANDB_MODE=offline \
SKYRL_DUMP_INFRA_LOG_TO_STDOUT=1 \
VLLM_ATTENTION_BACKEND=TORCH_SDPA \
MSWEA_API_KEY=nokey \
python -m examples.train_integrations.harbor.entrypoints.main_harbor \
  "data.train_data=[$DATA_DIR/train_task_dirs_v3.json]" \
  "data.val_data=[$DATA_DIR/val_task_dirs_v3.json]" \
  trainer.policy.model.path=Qwen/Qwen3.5-9B \
  trainer.strategy=fsdp \
  trainer.algorithm.advantage_estimator=grpo \
  trainer.placement.colocate_all=true \
  trainer.placement.policy_num_gpus_per_node=8 \
  trainer.placement.ref_num_gpus_per_node=8 \
  trainer.flash_attn=false \
  trainer.remove_microbatch_padding=false \
  trainer.policy.use_torch_compile=false \
  trainer.gradient_checkpointing=true \
  trainer.train_batch_size=8 \
  trainer.policy_mini_batch_size=8 \
  trainer.micro_forward_batch_size_per_gpu=1 \
  trainer.micro_train_batch_size_per_gpu=1 \
  trainer.max_prompt_length=4096 \
  trainer.algorithm.max_seq_len=8192 \
  trainer.max_training_steps=$TRAIN_STEPS \
  trainer.update_epochs_per_batch=1 \
  trainer.ckpt_interval=$CKPT_INTERVAL \
  trainer.eval_interval=$EVAL_INTERVAL \
  trainer.eval_before_train=false \
  trainer.eval_batch_size=$EVAL_BATCH \
  trainer.max_ckpts_to_keep=2 \
  trainer.logger=console \
  "trainer.project_name=simrl-sky-endless" \
  "trainer.run_name=endless-grpo-qwen3.5-9b-dryrun3-5steps" \
  "trainer.ckpt_path=$CKPT_DIR" \
  "trainer.export_path=$EXPORT_DIR" \
  trainer.resume_mode=null \
  generator.inference_engine.num_engines=1 \
  generator.inference_engine.tensor_parallel_size=8 \
  generator.inference_engine.run_engines_locally=true \
  generator.inference_engine.backend=vllm \
  generator.inference_engine.weight_sync_backend=nccl \
  generator.inference_engine.async_engine=true \
  generator.inference_engine.enforce_eager=true \
  generator.inference_engine.gpu_memory_utilization=0.45 \
  generator.inference_engine.served_model_name=Qwen3.5-9B \
  generator.n_samples_per_prompt=8 \
  generator.eval_n_samples_per_prompt=2 \
  generator.max_turns=$MAX_TURNS \
  generator.step_wise_trajectories=true \
  generator.merge_stepwise_output=true \
  "generator.sampling_params.max_generate_length=1024" \
  "generator.sampling_params.temperature=0.6" \
  2>&1 | tee "$LOG_FILE"
cd ..

kill $UPLOADER_PID $METRICS_PID $LOG_SYNC_PID $DOCKER_CLEANUP_PID 2>/dev/null

# ── final metrics collection ────────────────────────────────────────────────
echo "Running final metrics collection..."
python3.13 scripts/collect_metrics.py \
  --log "$LOG_FILE" \
  --export-dir "$EXPORT_DIR" \
  --out-dir "$METRICS_DIR" \
  --s3-prefix "$S3_CKPT/metrics"

echo "Uploading final log and evals..."
aws s3 cp "$LOG_FILE" "$S3_CKPT/train_debug.log" --no-progress
aws s3 sync "$EXPORT_DIR/" "$S3_CKPT/evals/" --no-progress
echo "Dryrun3 complete. Results at: $S3_CKPT"
