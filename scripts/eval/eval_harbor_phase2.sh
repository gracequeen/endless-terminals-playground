#!/bin/bash
# Eval a phase2 checkpoint on val splits (v1, v2, v3) separately using Harbor + terminus-2
# Usage: bash scripts/eval_harbor_phase2.sh <checkpoint_dir>
# Example: bash scripts/eval_harbor_phase2.sh /home/ec2-user/xin/checkpoints_harbor_qwen3_5_9b_phase2/global_step_200
set -e

CHECKPOINT="${1:?Usage: $0 <checkpoint_dir>}"
STEP_NAME=$(basename "$CHECKPOINT")

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
source /tmp/sky/bin/activate

if [ -d "/usr/local/cuda" ] && [ -f "/usr/local/cuda/bin/nvcc" ]; then
  export CUDA_HOME=/usr/local/cuda
else
  NVCC_PATH=$(which nvcc 2>/dev/null || true)
  [ -n "$NVCC_PATH" ] && export CUDA_HOME=$(dirname $(dirname "$NVCC_PATH")) || { echo "ERROR: nvcc not found" >&2; exit 1; }
fi
export PATH="$CUDA_HOME/bin:$PATH"
rm -rf ~/.cache/flashinfer
export FLASHINFER_DISABLE_VERSION_CHECK=1

DATA_DIR="/home/ec2-user/xin/data_harbor_combined"
S3_BASE="s3://endless-terminals-training/20260827_v1v2v3hard_phase2_grpo_qwen3.5-9b_200steps/eval_${STEP_NAME}"

MODE="${MODE:-val}"
case "$MODE" in
  val)   SPLITS="${SPLITS:-val_v1 val_v2 val_v3}" ;;
  train) SPLITS="${SPLITS:-train_v1 train_v2 train_v3}" ;;
  *)     SPLITS="${SPLITS:-val_v1 val_v2 val_v3 train_v1 train_v2 train_v3}" ;;
esac

(
  while true; do
    sleep 5
    docker ps -aq --filter "status=exited" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -aq --filter "status=dead" | xargs -r docker rm -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
  done
) &
DOCKER_CLEANUP_PID=$!

for SPLIT in $SPLITS; do
  JSON="$DATA_DIR/task_dirs_${SPLIT}.json"
  if [ ! -f "$JSON" ]; then
    echo "Skip $SPLIT: $JSON not found. Run prepare_eval_splits.sh first."
    continue
  fi

  EXPORT_DIR="/home/ec2-user/xin/eval_exports_${STEP_NAME}_${SPLIT}"
  METRICS_DIR="/home/ec2-user/xin/eval_metrics_${STEP_NAME}_${SPLIT}"
  S3_DEST="$S3_BASE/$SPLIT"

  mkdir -p "$EXPORT_DIR" "$METRICS_DIR"

  echo ""
  echo "=== Evaluating $SPLIT (checkpoint: $STEP_NAME) ==="

  cd "$REPO_ROOT/SkyRL"
  RAY_memory_usage_threshold=0.99 \
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  HF_HOME=/tmp/hf_cache \
  WANDB_MODE=offline \
  SKYRL_DUMP_INFRA_LOG_TO_STDOUT=1 \
  VLLM_ATTENTION_BACKEND=TORCH_SDPA \
  MSWEA_API_KEY=nokey \
  python -m examples.train_integrations.harbor.entrypoints.main_harbor \
    "data.train_data=[$JSON]" \
    "data.val_data=[$JSON]" \
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
    trainer.max_ckpts_to_keep=1 \
    trainer.logger=console \
    "trainer.project_name=simrl-sky-endless" \
    "trainer.run_name=eval-phase2-${STEP_NAME}-${SPLIT}" \
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
    generator.rate_limit.max_concurrency=32 \
    "generator.sampling_params.max_generate_length=1024" \
    "generator.sampling_params.temperature=0.6" \
    2>&1 | tee "$METRICS_DIR/eval_log.log"
  cd "$REPO_ROOT"

  echo "Collecting metrics for $SPLIT..."
  python3.13 scripts/collect_metrics.py \
    --log "$METRICS_DIR/eval_log.log" \
    --export-dir "$EXPORT_DIR" \
    --out-dir "$METRICS_DIR" \
    --s3-prefix "$S3_DEST/metrics"

  echo "Uploading $SPLIT results to S3..."
  aws s3 cp "$METRICS_DIR/eval_log.log" "$S3_DEST/eval_log.log" --no-progress --region us-west-1
  aws s3 sync "$EXPORT_DIR/" "$S3_DEST/evals/" --no-progress --region us-west-1
  echo "Done $SPLIT → $S3_DEST"
done

kill $DOCKER_CLEANUP_PID 2>/dev/null

echo ""
echo "=== All splits done ==="
echo "Results at: $S3_BASE"
