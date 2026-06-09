#!/usr/bin/env bash
# PPO training with SkyRL + Harbor on a single T4 GPU (15 GB)
# Uses local Docker sandboxes against harbor_tasks/ directory
# Model: Qwen/Qwen2.5-1.5B-Instruct (fits in T4 with 0.5 GPU util for vLLM)
set -ex

export PATH="$HOME/.local/bin:$PATH"
export HF_HUB_ENABLE_HF_TRANSFER=1

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$REPO_DIR/harbor_tasks"

MODEL="Qwen/Qwen2.5-1.5B-Instruct"
MODEL_SHORT="Qwen2.5-1.5B"
RUN_NAME="harbor-ppo-t4-${MODEL_SHORT}"
CKPT_DIR="/tmp/skyrl_ckpts/${RUN_NAME}"
TRIALS_DIR="/tmp/harbor_trials/${RUN_NAME}"

N_SAMPLES=4
MAX_MODEL_LEN=8192
MINI_BATCH_SIZE=4

cd "$REPO_DIR"

uv run --isolated --extra fsdp --extra harbor \
  -m train.harbor.entrypoints.main_harbor \
  data.train_data="['$DATA_DIR']" \
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
  generator.inference_engine.gpu_memory_utilization=0.5 \
  generator.inference_engine.enforce_eager=true \
  generator.inference_engine.engine_init_kwargs.max_model_len=$MAX_MODEL_LEN \
  generator.inference_engine.engine_init_kwargs.dtype=float16 \
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
  trainer.epochs=10 \
  trainer.update_epochs_per_batch=1 \
  trainer.train_batch_size=$MINI_BATCH_SIZE \
  trainer.policy_mini_batch_size=$MINI_BATCH_SIZE \
  trainer.micro_forward_batch_size_per_gpu=1 \
  trainer.micro_train_batch_size_per_gpu=1 \
  trainer.eval_batch_size=8 \
  trainer.eval_before_train=false \
  trainer.eval_interval=50 \
  trainer.ckpt_interval=5 \
  trainer.max_ckpts_to_keep=3 \
  trainer.hf_save_interval=10 \
  trainer.ckpt_path="$CKPT_DIR" \
  trainer.policy.optimizer_config.lr=1.0e-6 \
  trainer.logger=console \
  trainer.project_name=harbor_ppo_t4 \
  trainer.run_name="$RUN_NAME" \
  trainer.resume_mode=latest \
  "$@"
