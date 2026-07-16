#!/bin/bash
set -e

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

# Download task directories
TASKS_DIR="/home/ec2-user/xin/harbor_tasks"
HERODOC_TASKS_DIR="/home/ec2-user/xin/harbor_tasks/tasks_herodoc_3k"

if [ ! -d "$TASKS_DIR" ] || [ -z "$(ls -A $TASKS_DIR 2>/dev/null)" ]; then
  echo "Downloading 4.5opus tasks from S3..."
  mkdir -p "$TASKS_DIR"
  aws s3 sync s3://endless-terminals-training/data/harbor_tasks_claude4.5_opus/ "$TASKS_DIR/" --no-progress
else
  echo "Using existing 4.5opus tasks ($(find $TASKS_DIR -name 'instruction.md' | wc -l) tasks)"
fi

if [ ! -d "$HERODOC_TASKS_DIR" ] || [ -z "$(ls -A $HERODOC_TASKS_DIR 2>/dev/null)" ]; then
  echo "Downloading herodoc-fixed 3k tasks from S3..."
  mkdir -p "$HERODOC_TASKS_DIR"
  aws s3 sync s3://endless-terminals-training/data/harbor_4.6opus_tasks_herodoc_fixed_3k/ "$HERODOC_TASKS_DIR/" --no-progress
else
  echo "Using existing herodoc tasks ($(find $HERODOC_TASKS_DIR -name 'instruction.md' | wc -l) tasks)"
fi

# Download combined parquet
DATA_DIR="/home/ec2-user/xin/data_harbor_qwen3_5_4b"
mkdir -p "$DATA_DIR"
echo "Downloading combined parquet from S3..."
aws s3 cp s3://endless-terminals-training/prepared_data/train_4.5opus-8192-task_4.6sonnet-sol_combined.parquet "$DATA_DIR/train.parquet"
aws s3 cp s3://endless-terminals-training/prepared_data/validation_4.5opus-8192-task_4.6sonnet-sol_combined.parquet "$DATA_DIR/validation.parquet"
echo "Parquet ready."

# Generate task dir lists from parquet
TRAIN_TASK_DIRS=$(python3.13 -c "
import pandas as pd, json
df = pd.read_parquet('$DATA_DIR/train.parquet')
dirs = list(df['extra_info'].apply(lambda x: x['task_dir']).unique())
print(json.dumps(dirs))
")
VAL_TASK_DIRS=$(python3.13 -c "
import pandas as pd, json
df = pd.read_parquet('$DATA_DIR/validation.parquet')
dirs = list(df['extra_info'].apply(lambda x: x['task_dir']).unique())
print(json.dumps(dirs))
")

# Checkpoint dirs
CKPT_DIR="/home/ec2-user/xin/checkpoints_harbor_qwen3_5_4b"
S3_CKPT="s3://endless-terminals-training/$(date +%Y%m%d)_4.5opus-4.6opus-task_harbor-miniswe_grpo_qwen3.5-4b_Xsteps"

if [ -f "$CKPT_DIR/latest_ckpt_global_step.txt" ]; then
  RESUME_MODE=latest
  echo "Resuming from latest checkpoint."
else
  RESUME_MODE=null
  echo "Starting fresh."
fi

LOG_FILE="$CKPT_DIR/train_debug.log"
mkdir -p "$CKPT_DIR"

# Background uploader
(
  UPLOADED=""
  while true; do
    for step_dir in "$CKPT_DIR"/global_step_*/; do
      [ -d "$step_dir" ] || continue
      step=$(basename "$step_dir")
      if [ -f "$step_dir/trainer_state.pt" ] && ! echo "$UPLOADED" | grep -q "$step"; then
        echo "[uploader] Uploading $step to S3..."
        aws s3 sync "$step_dir" "$S3_CKPT/$step/" --no-progress --quiet
        latest=$(cat "$CKPT_DIR/latest_ckpt_global_step.txt" 2>/dev/null)
        if [ "$step" != "global_step_$latest" ]; then
          rm -rf "$step_dir"
          echo "[uploader] $step deleted from disk"
        else
          echo "[uploader] $step kept on disk (latest)"
        fi
        UPLOADED="$UPLOADED $step"
      fi
    done
    sleep 30
  done
) &
UPLOADER_PID=$!

# Background log syncer
(
  while true; do
    sleep 300
    aws s3 cp "$LOG_FILE" "$S3_CKPT/train_debug.log" --quiet 2>/dev/null
    aws s3 sync "/home/ec2-user/xin/exports_harbor_qwen3_5_4b/" "$S3_CKPT/evals/" --quiet 2>/dev/null
  done
) &
LOG_SYNC_PID=$!

# Run training
# p4d.24xlarge: 8x A100 40GB
# 4B model fits on 4 GPUs with TP=4, leaving 4 GPUs for ref model
cd SkyRL
RAY_memory_usage_threshold=0.99 \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
HF_HOME=/tmp/hf_cache \
WANDB_MODE=offline \
SKYRL_DUMP_INFRA_LOG_TO_STDOUT=1 \
VLLM_ATTENTION_BACKEND=TORCH_SDPA \
MSWEA_API_KEY=nokey \
python -m examples.train_integrations.harbor.entrypoints.main_harbor \
  "data.train_data=$TRAIN_TASK_DIRS" \
  "data.val_data=$VAL_TASK_DIRS" \
  trainer.policy.model.path=Qwen/Qwen3.5-4B \
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
  trainer.micro_forward_batch_size_per_gpu=2 \
  trainer.micro_train_batch_size_per_gpu=2 \
  trainer.max_prompt_length=4096 \
  trainer.algorithm.max_seq_len=8192 \
  trainer.max_training_steps=100 \
  trainer.update_epochs_per_batch=2 \
  trainer.ckpt_interval=50 \
  trainer.eval_interval=20 \
  trainer.eval_batch_size=10 \
  trainer.max_ckpts_to_keep=1 \
  trainer.logger=console \
  "trainer.project_name=simrl-sky-endless" \
  "trainer.run_name=endless-grpo-qwen3.5-4b-harbor-miniswe" \
  "trainer.ckpt_path=$CKPT_DIR" \
  "trainer.export_path=/home/ec2-user/xin/exports_harbor_qwen3_5_4b" \
  trainer.resume_mode=$RESUME_MODE \
  generator.inference_engine.num_engines=1 \
  generator.inference_engine.tensor_parallel_size=8 \
  generator.inference_engine.run_engines_locally=true \
  generator.inference_engine.backend=vllm \
  generator.inference_engine.weight_sync_backend=nccl \
  generator.inference_engine.async_engine=true \
  generator.inference_engine.enforce_eager=true \
  generator.inference_engine.gpu_memory_utilization=0.45 \
  generator.inference_engine.served_model_name=Qwen3.5-4B \
  generator.n_samples_per_prompt=4 \
  generator.max_turns=8 \
  generator.step_wise_trajectories=true \
  generator.merge_stepwise_output=true \
  "generator.sampling_params.max_generate_length=2048" \
  "generator.sampling_params.temperature=0.6" \
  2>&1 | tee "$LOG_FILE"
cd ..

kill $UPLOADER_PID 2>/dev/null
kill $LOG_SYNC_PID 2>/dev/null

echo "Uploading final log and evals to S3..."
aws s3 cp "$LOG_FILE" "$S3_CKPT/train_debug.log" --no-progress
aws s3 sync "/home/ec2-user/xin/exports_harbor_qwen3_5_4b/" "$S3_CKPT/evals/" --no-progress
echo "Training complete. All metrics uploaded to S3."
