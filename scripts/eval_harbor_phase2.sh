#!/bin/bash
# Eval a phase2 checkpoint on the val set using Harbor + terminus-2
# Usage: bash scripts/eval_harbor_phase2.sh <checkpoint_dir>
# Example: bash scripts/eval_harbor_phase2.sh /home/ec2-user/xin/checkpoints_harbor_qwen3_5_9b_phase2/global_step_200
set -e

CHECKPOINT="${1:?Usage: $0 <checkpoint_dir>}"
STEP_NAME=$(basename "$CHECKPOINT")

cd "$(dirname "$0")/.."
source /tmp/sky/bin/activate

if [ -d "/usr/local/cuda" ] && [ -f "/usr/local/cuda/bin/nvcc" ]; then
  export CUDA_HOME=/usr/local/cuda
else
  NVCC_PATH=$(which nvcc 2>/dev/null || true)
  [ -n "$NVCC_PATH" ] && export CUDA_HOME=$(dirname $(dirname "$NVCC_PATH")) || { echo "ERROR: nvcc not found" >&2; exit 1; }
fi
export PATH="$CUDA_HOME/bin:$PATH"
rm -rf ~/.cache/flashinfer

DATA_DIR="/home/ec2-user/xin/data_harbor_combined"
EXPORT_DIR="/home/ec2-user/xin/eval_exports_${STEP_NAME}"
METRICS_DIR="/home/ec2-user/xin/eval_metrics_${STEP_NAME}"
S3_DEST="s3://endless-terminals-training/20260827_v1v2v3hard_phase2_grpo_qwen3.5-9b_200steps/eval_${STEP_NAME}"

mkdir -p "$EXPORT_DIR" "$METRICS_DIR"
export FLASHINFER_DISABLE_VERSION_CHECK=1

(
  while true; do
    sleep 5
    docker ps -aq --filter "status=exited" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -aq --filter "status=dead" | xargs -r docker rm -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
  done
) &
DOCKER_CLEANUP_PID=$!

echo "Evaluating checkpoint: $CHECKPOINT"
cd SkyRL
RAY_memory_usage_threshold=0.99 \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
HF_HOME=/tmp/hf_cache \
WANDB_MODE=offline \
SKYRL_DUMP_INFRA_LOG_TO_STDOUT=1 \
VLLM_ATTENTION_BACKEND=TORCH_SDPA \
MSWEA_API_KEY=nokey \
python -m examples.train_integrations.harbor.entrypoints.main_harbor \
  "data.train_data=[$DATA_DIR/train_task_dirs_v3hard.json]" \
  "data.val_data=[$DATA_DIR/val_task_dirs_v3hard.json]" \
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
  trainer.max_training_steps=1 \
  trainer.ckpt_interval=999 \
  trainer.eval_interval=999 \
  trainer.eval_before_train=true \
  trainer.eval_batch_size=8 \
  trainer.max_ckpts_to_keep=0 \
  trainer.logger=console \
  "trainer.project_name=simrl-sky-endless" \
  "trainer.run_name=eval-phase2-${STEP_NAME}" \
  "trainer.ckpt_path=$EXPORT_DIR/ckpt_unused" \
  "trainer.export_path=$EXPORT_DIR" \
  trainer.resume_mode=from_path \
  "trainer.resume_path=$CHECKPOINT" \
  generator.inference_engine.num_engines=1 \
  generator.inference_engine.tensor_parallel_size=8 \
  generator.inference_engine.run_engines_locally=true \
  generator.inference_engine.backend=vllm \
  generator.inference_engine.weight_sync_backend=nccl \
  generator.inference_engine.async_engine=true \
  generator.inference_engine.enforce_eager=true \
  generator.inference_engine.gpu_memory_utilization=0.45 \
  generator.inference_engine.served_model_name=Qwen3.5-9B \
  generator.n_samples_per_prompt=2 \
  generator.eval_n_samples_per_prompt=2 \
  generator.max_turns=8 \
  generator.step_wise_trajectories=true \
  generator.merge_stepwise_output=true \
  generator.rate_limit.enabled=true \
  generator.rate_limit.max_concurrency=16 \
  "generator.sampling_params.max_generate_length=1024" \
  "generator.sampling_params.temperature=0.6" \
  2>&1 | tee "$METRICS_DIR/eval_log.log"
cd ..

kill $DOCKER_CLEANUP_PID 2>/dev/null

echo "Collecting metrics..."
python3.13 scripts/collect_metrics.py \
  --log "$METRICS_DIR/eval_log.log" \
  --export-dir "$EXPORT_DIR" \
  --out-dir "$METRICS_DIR" \
  --s3-prefix "$S3_DEST/metrics"

echo "Uploading results to S3..."
aws s3 cp "$METRICS_DIR/eval_log.log" "$S3_DEST/eval_log.log" --no-progress
aws s3 sync "$EXPORT_DIR/" "$S3_DEST/evals/" --no-progress

echo "Done. Results at: $S3_DEST"
