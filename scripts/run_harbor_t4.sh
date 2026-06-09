#!/usr/bin/env bash
# PPO training with SkyRL + Harbor on a single T4 GPU (15 GB)
# Model: Qwen/Qwen3.5-0.8B
# Dataset: harbor_tasks/ split via data/harbor_split.json (80 train / 5 eval / 15 test)
set -ex

export PATH="$HOME/.local/bin:$PATH"
export HF_HUB_ENABLE_HF_TRANSFER=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VLLM_USE_V1=0          # vLLM v1 engine crashes on T4; use v0
export VLLM_DISABLE_CUMEM=1   # disable cumem allocator to avoid wake_up OOM on T4

PYTHON="$(cd "$(dirname "$0")/.." && pwd)/.venv/bin/python3"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

MODEL="Qwen/Qwen3.5-0.8B"
MODEL_SHORT="Qwen3.5-0.8B"
RUN_NAME="harbor-ppo-t4-${MODEL_SHORT}"
CKPT_DIR="/tmp/skyrl_ckpts/${RUN_NAME}"
TRIALS_DIR="/tmp/harbor_trials/${RUN_NAME}"
MANIFEST="$REPO_DIR/data/harbor_split.json"
RESULTS_DIR="$REPO_DIR/results/${RUN_NAME}"

N_SAMPLES=4
MAX_MODEL_LEN=4096
MINI_BATCH_SIZE=4
EPOCHS=10
LR=1.0e-6
EVAL_INTERVAL=50

mkdir -p "$RESULTS_DIR"

# ---------------------------------------------------------------------------
# Build train/eval data lists from split manifest
# ---------------------------------------------------------------------------
TRAIN_DATA=$($PYTHON -c "
import json, sys
from pathlib import Path
manifest = json.load(open('$MANIFEST'))
task_dir = Path('$REPO_DIR/harbor_tasks')
paths = [str(task_dir / name) for name in manifest['train']]
print('[' + ','.join(repr(p) for p in paths) + ']')
")

VAL_DATA=$($PYTHON -c "
import json, sys
from pathlib import Path
manifest = json.load(open('$MANIFEST'))
task_dir = Path('$REPO_DIR/harbor_tasks')
paths = [str(task_dir / name) for name in manifest['eval']]
print('[' + ','.join(repr(p) for p in paths) + ']')
")

# ---------------------------------------------------------------------------
# Log experiment config
# ---------------------------------------------------------------------------
$PYTHON train/harbor/log_experiment.py \
  --model "$MODEL" \
  --manifest "$MANIFEST" \
  --output "$RESULTS_DIR/experiment_config.json" \
  --phase train \
  --run-name "$RUN_NAME" \
  --extra \
    trainer.epochs=$EPOCHS \
    trainer.train_batch_size=$MINI_BATCH_SIZE \
    trainer.policy.optimizer_config.lr=$LR \
    generator.n_samples_per_prompt=$N_SAMPLES \
    generator.inference_engine.gpu_memory_utilization=0.30 \
    trainer.algorithm.advantage_estimator=grpo \
    trainer.algorithm.max_seq_len=$MAX_MODEL_LEN \
    harbor_trial_config.agent.kwargs.max_turns=16 \
    harbor_trial_config.environment.type=docker

# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------
$PYTHON -m train.harbor.entrypoints.main_harbor \
  "data.train_data=$TRAIN_DATA" \
  "data.val_data=$VAL_DATA" \
  trainer.policy.model.path="$MODEL" \
  generator.inference_engine.served_model_name="$MODEL_SHORT" \
  harbor_trial_config.trials_dir="$TRIALS_DIR" \
  harbor_trial_config.environment.type=docker \
  harbor_trial_config.agent.kwargs.max_turns=16 \
  harbor_trial_config.agent.kwargs.model_info.max_input_tokens=$MAX_MODEL_LEN \
  harbor_trial_config.agent.kwargs.model_info.max_output_tokens=$MAX_MODEL_LEN \
  trainer.placement.colocate_all=true \
  trainer.strategy=fsdp \
  trainer.placement.policy_num_nodes=1 \
  trainer.placement.ref_num_nodes=1 \
  trainer.placement.policy_num_gpus_per_node=1 \
  trainer.placement.ref_num_gpus_per_node=1 \
  generator.inference_engine.num_engines=1 \
  generator.inference_engine.tensor_parallel_size=1 \
  generator.inference_engine.backend=vllm \
  generator.inference_engine.run_engines_locally=true \
  generator.inference_engine.weight_sync_backend=nccl \
  generator.inference_engine.async_engine=true \
  generator.inference_engine.gpu_memory_utilization=0.30 \
  generator.inference_engine.enforce_eager=true \
  generator.inference_engine.vllm_v1_disable_multiproc=true \
  generator.inference_engine.engine_init_kwargs.max_model_len=$MAX_MODEL_LEN \
  generator.inference_engine.engine_init_kwargs.dtype=float16 \
  generator.inference_engine.engine_init_kwargs.disable_custom_all_reduce=true \
  generator.inference_engine.enable_http_endpoint=true \
  generator.inference_engine.http_endpoint_host=127.0.0.1 \
  generator.inference_engine.http_endpoint_port=8000 \
  generator.step_wise_trajectories=true \
  generator.merge_stepwise_output=true \
  generator.n_samples_per_prompt=$N_SAMPLES \
  generator.eval_n_samples_per_prompt=1 \
  generator.apply_overlong_filtering=true \
  generator.batched=false \
  generator.rate_limit.enabled=true \
  generator.rate_limit.max_concurrency=8 \
  trainer.algorithm.advantage_estimator=grpo \
  trainer.algorithm.loss_reduction=token_mean \
  trainer.algorithm.use_kl_loss=false \
  trainer.algorithm.max_seq_len=$MAX_MODEL_LEN \
  trainer.eval_interval=$EVAL_INTERVAL \
  trainer.eval_before_train=false \
  trainer.epochs=$EPOCHS \
  trainer.update_epochs_per_batch=1 \
  trainer.train_batch_size=$MINI_BATCH_SIZE \
  trainer.policy_mini_batch_size=$MINI_BATCH_SIZE \
  trainer.micro_forward_batch_size_per_gpu=1 \
  trainer.micro_train_batch_size_per_gpu=1 \
  trainer.eval_batch_size=5 \
  trainer.remove_microbatch_padding=false \
  trainer.ckpt_interval=5 \
  trainer.max_ckpts_to_keep=3 \
  trainer.hf_save_interval=10 \
  trainer.ckpt_path="$CKPT_DIR" \
  trainer.export_path="$CKPT_DIR/hf_export" \
  trainer.policy.optimizer_config.lr=$LR \
  trainer.logger=console \
  trainer.project_name=harbor_ppo_t4 \
  trainer.run_name="$RUN_NAME" \
  trainer.resume_mode=latest \
  "$@"
