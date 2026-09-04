#!/bin/bash
set -e

# Baseline eval script for Qwen2.5-3B on p5.48xlarge
# Purpose: measure base model pass rate on 2781-task deduped dataset
# to compare with Qwen3.5-4B's 62.5% baseline

cd "$(dirname "$0")/.."
source /tmp/sky/bin/activate

# Locate CUDA_HOME
if [ -d "/usr/local/cuda" ] && [ -f "/usr/local/cuda/bin/nvcc" ]; then
  export CUDA_HOME=/usr/local/cuda
elif [ -f "/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13/bin/nvcc" ]; then
  export CUDA_HOME=/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13
else
  NVCC_PATH=$(which nvcc 2>/dev/null || true)
  if [ -n "$NVCC_PATH" ]; then
    export CUDA_HOME=$(dirname $(dirname "$NVCC_PATH"))
  else
    echo "ERROR: Could not find nvcc." >&2
    exit 1
  fi
fi
export PATH="$CUDA_HOME/bin:$PATH"
echo "Using CUDA_HOME=$CUDA_HOME"
rm -rf ~/.cache/flashinfer

# Download task directories (reuse existing if present)
TASKS_DEDUPED_DIR="/home/ec2-user/xin/harbor_tasks/tasks_8192_deduped"
TASKS_COUNT=$(find "$TASKS_DEDUPED_DIR" -name 'instruction.md' 2>/dev/null | wc -l)
if [ "$TASKS_COUNT" -lt 10 ]; then
  echo "Downloading deduped 8192 tasks from S3..."
  mkdir -p "$TASKS_DEDUPED_DIR"
  aws configure set region us-west-1
  aws s3 sync s3://endless-terminals-training/data/harbor_tasks_8192_deduped/ "$TASKS_DEDUPED_DIR/" --no-progress
  TASKS_COUNT=$(find "$TASKS_DEDUPED_DIR" -name 'instruction.md' 2>/dev/null | wc -l)
  echo "Downloaded $TASKS_COUNT tasks."
else
  echo "Using existing deduped tasks ($TASKS_COUNT tasks)"
fi

# Download parquet
DATA_DIR="/home/ec2-user/xin/data_harbor_qwen2_5_3b_p5"
mkdir -p "$DATA_DIR"
echo "Downloading deduped parquet from S3..."
aws s3 cp s3://endless-terminals-training/prepared_data/train_8192_deduped_4929tasks.parquet "$DATA_DIR/train.parquet"
aws s3 cp s3://endless-terminals-training/prepared_data/validation_8192_deduped_4929tasks.parquet "$DATA_DIR/validation.parquet"
echo "Parquet ready."

# Write task dir lists to JSON files
TRAIN_DIRS_FILE="/tmp/train_task_dirs_3b.json"
VAL_DIRS_FILE="/tmp/val_task_dirs_3b.json"
python3.13 -c "
import pandas as pd, json
df = pd.read_parquet('$DATA_DIR/train.parquet')
dirs = list(df['extra_info'].apply(lambda x: x['task_dir']).unique())
json.dump(dirs, open('$TRAIN_DIRS_FILE','w'))
print('Train tasks:', len(dirs))
"
python3.13 -c "
import pandas as pd, json
df = pd.read_parquet('$DATA_DIR/validation.parquet')
dirs = list(df['extra_info'].apply(lambda x: x['task_dir']).unique())
json.dump(dirs, open('$VAL_DIRS_FILE','w'))
print('Val tasks:', len(dirs))
"

# Checkpoint dirs
CKPT_DIR="/home/ec2-user/xin/checkpoints_harbor_qwen2_5_3b_baseline"
EXPORT_DIR="/home/ec2-user/xin/exports_harbor_qwen2_5_3b_baseline"
S3_CKPT="s3://endless-terminals-training/$(date +%Y%m%d)_8192deduped-task_harbor-grpo_qwen2.5-3b_p5_baseline"

LOG_FILE="$CKPT_DIR/train_debug.log"
mkdir -p "$CKPT_DIR"
mkdir -p "$EXPORT_DIR"

# Background log syncer
(
  while true; do
    sleep 300
    aws s3 cp "$LOG_FILE" "$S3_CKPT/train_debug.log" --quiet 2>/dev/null
    # Sync first 5 trials per step to S3 for inspection
    aws s3 sync ~/trials/ "$S3_CKPT/trials/" --quiet 2>/dev/null
  done
) &
LOG_SYNC_PID=$!

# Background Docker cleaner
(
  while true; do
    sleep 1800
    docker builder prune -f --filter until=1h > /dev/null 2>&1
    docker image prune -f --filter until=2h > /dev/null 2>&1
    docker network prune -f > /dev/null 2>&1
  done
) &
DOCKER_CLEAN_PID=$!

# Run just 5 steps to measure baseline pass rate
cd SkyRL
RAY_memory_usage_threshold=0.99 \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
HF_HOME=/tmp/hf_cache \
WANDB_MODE=offline \
SKYRL_DUMP_INFRA_LOG_TO_STDOUT=1 \
VLLM_ATTENTION_BACKEND=TORCH_SDPA \
VLLM_USE_FLASHINFER_SAMPLER=0 \
MSWEA_API_KEY=nokey \
python -m examples.train_integrations.harbor.entrypoints.main_harbor \
  "data.train_data=[\"$TRAIN_DIRS_FILE\"]" \
  "data.val_data=[\"$VAL_DIRS_FILE\"]" \
  trainer.policy.model.path=Qwen/Qwen2.5-3B-Instruct \
  trainer.strategy=fsdp \
  trainer.algorithm.advantage_estimator=grpo \
  trainer.placement.colocate_all=true \
  trainer.placement.policy_num_gpus_per_node=8 \
  trainer.placement.policy_num_nodes=1 \
  trainer.placement.ref_num_gpus_per_node=8 \
  trainer.placement.ref_num_nodes=1 \
  trainer.flash_attn=false \
  trainer.use_sample_packing=false \
  trainer.policy.use_torch_compile=false \
  trainer.gradient_checkpointing=true \
  trainer.train_batch_size=8 \
  trainer.policy_mini_batch_size=8 \
  trainer.micro_forward_batch_size_per_gpu=1 \
  trainer.micro_train_batch_size_per_gpu=1 \
  trainer.max_prompt_length=4096 \
  trainer.algorithm.max_seq_len=4096 \
  trainer.max_training_steps=5 \
  trainer.update_epochs_per_batch=1 \
  trainer.ckpt_interval=100 \
  trainer.eval_interval=100 \
  trainer.eval_batch_size=10 \
  trainer.eval_before_train=false \
  trainer.max_ckpts_to_keep=1 \
  trainer.logger=console \
  "trainer.project_name=simrl-sky-endless" \
  "trainer.run_name=qwen2.5-3b-baseline-deduped" \
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
  generator.inference_engine.gpu_memory_utilization=0.10 \
  generator.inference_engine.served_model_name=Qwen2.5-3B-Instruct \
  generator.n_samples_per_prompt=4 \
  generator.max_turns=6 \
  generator.step_wise_trajectories=true \
  generator.merge_stepwise_output=true \
  "generator.sampling_params.max_generate_length=1024" \
  "generator.sampling_params.temperature=0.6" \
  2>&1 | tee "$LOG_FILE"
cd ..

kill $LOG_SYNC_PID 2>/dev/null
kill $DOCKER_CLEAN_PID 2>/dev/null

echo "Uploading final log and trials to S3..."
aws s3 cp "$LOG_FILE" "$S3_CKPT/train_debug.log" --no-progress
aws s3 sync ~/trials/ "$S3_CKPT/trials/" --no-progress
echo "Done. Check avg_pass_at_4 in the log to compare with Qwen3.5-4B's 62.5%."
