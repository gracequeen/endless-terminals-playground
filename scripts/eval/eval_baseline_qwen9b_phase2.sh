#!/bin/bash
# Baseline eval for Qwen3.5-9B (base, untrained) on all 6 dataset splits:
#   train_v1 (sampled 500), train_v2 (sampled 500), train_v3 (sampled 500)
#   val_v1 (51), val_v2 (100), val_v3 (~366)
# Runs eval_before_train (no weight updates) for each split separately.
#
# Prereq: run scripts/prepare_data_v3hard.sh to produce task_dirs_*.json files.
set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
source /tmp/sky/bin/activate

if [ -d "/usr/local/cuda" ] && [ -f "/usr/local/cuda/bin/nvcc" ]; then
  export CUDA_HOME=/usr/local/cuda
else
  NVCC_PATH=$(which nvcc 2>/dev/null || true)
  if [ -n "$NVCC_PATH" ]; then
    export CUDA_HOME=$(dirname $(dirname "$NVCC_PATH"))
  fi
fi
[ -n "$CUDA_HOME" ] && export PATH="$CUDA_HOME/bin:$PATH"
rm -rf ~/.cache/flashinfer

DATA_DIR="/home/ec2-user/xin/data_harbor_combined"
BASE_DIR="/home/ec2-user/xin/baseline_qwen9b_splits"
S3_BASE="s3://endless-terminals-training/baselines/qwen3.5-9b-base_splits"

mkdir -p "$BASE_DIR"
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker network prune -f
nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | xargs -r kill -9 2>/dev/null || true
sleep 3
export FLASHINFER_DISABLE_VERSION_CHECK=1

MODE="${MODE:-val}"  # val | train | all
case "$MODE" in
  val)   SPLITS="val_v1 val_v2 val_v3" ;;
  train) SPLITS="train_v1 train_v2 train_v3" ;;
  *)     SPLITS="val_v1 val_v2 val_v3 train_v1 train_v2 train_v3" ;;
esac

for SPLIT in $SPLITS; do
  JSON="$DATA_DIR/task_dirs_${SPLIT}.json"
  if [ ! -f "$JSON" ]; then
    echo "Skip $SPLIT: $JSON not found. Run prepare_data_v3hard.sh first."
    continue
  fi

  CKPT_DIR="$BASE_DIR/${SPLIT}_ckpt"
  EXPORT_DIR="$BASE_DIR/${SPLIT}_export"
  S3_DEST="$S3_BASE/$SPLIT"
  mkdir -p "$CKPT_DIR" "$EXPORT_DIR"

  echo ""
  echo "=== Evaluating split: $SPLIT ==="

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
    generator.eval_n_samples_per_prompt=2 \
    trainer.max_ckpts_to_keep=1 \
    trainer.logger=console \
    "trainer.project_name=simrl-sky-endless" \
    "trainer.run_name=baseline-qwen3.5-9b-${SPLIT}" \
    "trainer.ckpt_path=$CKPT_DIR" \
    "trainer.export_path=$EXPORT_DIR" \
    trainer.resume_mode=none \
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
    2>&1 | tee "$CKPT_DIR/eval_log.log"
  cd "$REPO_ROOT"

  python scripts/collect_metrics.py \
    --log "$CKPT_DIR/eval_log.log" \
    --export-dir "$EXPORT_DIR" \
    --out-dir "$CKPT_DIR/metrics" \
    --s3-prefix "$S3_DEST/metrics"

  aws s3 cp "$CKPT_DIR/eval_log.log" "$S3_DEST/eval_log.log" --no-progress
  aws s3 sync "$EXPORT_DIR/" "$S3_DEST/evals/" --no-progress
  echo "Done $SPLIT → $S3_DEST"
done

echo ""
echo "=== All splits done. Results at: $S3_BASE ==="
