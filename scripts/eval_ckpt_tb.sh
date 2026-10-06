#!/usr/bin/env bash
# Evaluate an FSDP checkpoint on TerminalBench 2.1 through SkyRL + Harbor.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "$REPO" == */.claude/worktrees/* ]]; then
    MAIN_REPO="${REPO%%/.claude/worktrees/*}"
else
    MAIN_REPO="$REPO"
fi

CHECKPOINT="$MAIN_REPO/checkpoints"
TB_DIR="$MAIN_REPO/terminal-bench-2-1"
SKYRL_DIR="$MAIN_REPO/SkyRL"
SKY_ENV="/tmp/sky"
OUTPUT_ROOT="$MAIN_REPO/eval_tb_ckpt"
S3_BASE="s3://endless-terminals-training/terminal-bench"
MODEL="Qwen/Qwen3.5-9B"
N_SAMPLES=2
MAX_CONCURRENCY=32
MAX_OUTPUT_TOKENS=4096
RUN_NAME=""
TEST_MODE=0
DRY_RUN=0

usage() {
    cat <<EOF
Usage: $0 [options]

Options:
  --checkpoint DIR   SkyRL checkpoint root (default: $CHECKPOINT)
  --tb-dir DIR       Downloaded TerminalBench 2.1 root (default: $TB_DIR)
  --skyrl-dir DIR    SkyRL checkout (default: $SKYRL_DIR)
  --sky-env DIR      SkyRL virtual environment (default: $SKY_ENV)
  --output-dir DIR   Local run output root (default: $OUTPUT_ROOT)
  --run-name NAME    Run directory name (default: generated from model/mode/time)
  --n-samples N      Solution trials per task (default: $N_SAMPLES)
  --test             Evaluate only the first two sorted TB2.1 tasks
  --dry-run          Validate inputs and print the command without launching SkyRL
  -h, --help         Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --checkpoint) CHECKPOINT="$2"; shift 2 ;;
        --tb-dir) TB_DIR="$2"; shift 2 ;;
        --skyrl-dir) SKYRL_DIR="$2"; shift 2 ;;
        --sky-env) SKY_ENV="$2"; shift 2 ;;
        --output-dir) OUTPUT_ROOT="$2"; shift 2 ;;
        --run-name) RUN_NAME="$2"; shift 2 ;;
        --n-samples) N_SAMPLES="$2"; shift 2 ;;
        --test) TEST_MODE=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

for required_dir in "$CHECKPOINT" "$CHECKPOINT/policy" "$TB_DIR" "$SKYRL_DIR" "$SKY_ENV"; do
    [[ -d "$required_dir" ]] || { echo "Missing required directory: $required_dir" >&2; exit 1; }
done
[[ -f "$CHECKPOINT/trainer_state.pt" ]] || { echo "Missing trainer state: $CHECKPOINT/trainer_state.pt" >&2; exit 1; }
[[ -f "$CHECKPOINT/data.pt" ]] || { echo "Missing data state: $CHECKPOINT/data.pt" >&2; exit 1; }
[[ -x "$SKY_ENV/bin/python" ]] || { echo "Missing SkyRL Python: $SKY_ENV/bin/python" >&2; exit 1; }
[[ "$N_SAMPLES" =~ ^[1-9][0-9]*$ ]] || { echo "--n-samples must be a positive integer" >&2; exit 2; }

mapfile -t MODEL_SHARDS < <(find "$CHECKPOINT/policy" -maxdepth 1 -type f -name 'model_world_size_8_rank_*.pt' | LC_ALL=C sort)
[[ ${#MODEL_SHARDS[@]} -eq 8 ]] || { echo "Expected 8 FSDP model shards, found ${#MODEL_SHARDS[@]}" >&2; exit 1; }

mapfile -t ALL_TASKS < <(find "$TB_DIR" -type f -name instruction.md -printf '%h\n' | LC_ALL=C sort)
[[ ${#ALL_TASKS[@]} -eq 89 ]] || { echo "Expected 89 TerminalBench 2.1 tasks, found ${#ALL_TASKS[@]}" >&2; exit 1; }
for task_dir in "${ALL_TASKS[@]}"; do
    [[ -f "$task_dir/task.toml" ]] || { echo "Missing task.toml: $task_dir" >&2; exit 1; }
done

if [[ $TEST_MODE -eq 1 ]]; then
    TASKS=("${ALL_TASKS[@]:0:2}")
    MODE_NAME="test2"
else
    TASKS=("${ALL_TASKS[@]}")
    MODE_NAME="full89"
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_NAME="${RUN_NAME:-qwen3.5-9b-fsdp-$(basename "$CHECKPOINT")-tb2.1-${MODE_NAME}-${TIMESTAMP}}"
[[ "$RUN_NAME" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "--run-name may contain only letters, numbers, dot, underscore, and hyphen" >&2; exit 2; }

RUN_DIR="$OUTPUT_ROOT/$RUN_NAME"
TRAIN_TASKS_JSON="$RUN_DIR/train-tasks.json"
EVAL_TASKS_JSON="$RUN_DIR/eval-tasks.json"
TRIALS_DIR="$RUN_DIR/trials"
EXPORT_DIR="$RUN_DIR/exports"
SCRATCH_CKPT_DIR="$RUN_DIR/checkpoint-unused"
ARCHIVE_DIR="$RUN_DIR/s3-artifacts"
LOG_FILE="$RUN_DIR/eval.log"
S3_RUN_URI="${S3_BASE%/}/$RUN_NAME"
CHECKPOINT_STEP="$("$SKY_ENV/bin/python" -c 'import sys, torch; print(torch.load(sys.argv[1], map_location="cpu", weights_only=False)["global_step"])' "$CHECKPOINT/trainer_state.pt")"
[[ "$CHECKPOINT_STEP" =~ ^[0-9]+$ ]] || { echo "Invalid checkpoint global step: $CHECKPOINT_STEP" >&2; exit 1; }
RESUME_CHECKPOINT="$RUN_DIR/global_step_$CHECKPOINT_STEP"
TRAIN_BATCH_SIZE=8
EVAL_BATCH_SIZE=8
if [[ ${#TASKS[@]} -lt $EVAL_BATCH_SIZE ]]; then
    EVAL_BATCH_SIZE=${#TASKS[@]}
fi

SKYRL_CMD=(
    "$SKY_ENV/bin/python" -m examples.train_integrations.harbor.entrypoints.main_harbor
    "data.train_data=[$TRAIN_TASKS_JSON]"
    "data.val_data=[$EVAL_TASKS_JSON]"
    "trainer.policy.model.path=$MODEL"
    trainer.strategy=fsdp
    trainer.algorithm.advantage_estimator=grpo
    trainer.placement.colocate_all=true
    trainer.placement.policy_num_gpus_per_node=8
    trainer.placement.ref_num_gpus_per_node=8
    trainer.flash_attn=false
    trainer.remove_microbatch_padding=false
    trainer.policy.use_torch_compile=false
    trainer.gradient_checkpointing=true
    "trainer.train_batch_size=$TRAIN_BATCH_SIZE"
    "trainer.policy_mini_batch_size=$TRAIN_BATCH_SIZE"
    trainer.micro_forward_batch_size_per_gpu=1
    trainer.micro_train_batch_size_per_gpu=1
    trainer.max_prompt_length=4096
    trainer.algorithm.max_seq_len=8192
    trainer.epochs=0
    trainer.ckpt_interval=999
    trainer.eval_interval=1
    trainer.eval_before_train=true
    "trainer.eval_batch_size=$EVAL_BATCH_SIZE"
    trainer.dump_eval_results=true
    trainer.max_ckpts_to_keep=1
    trainer.logger=console
    "trainer.project_name=endless-terminals"
    "trainer.run_name=$RUN_NAME"
    "trainer.ckpt_path=$SCRATCH_CKPT_DIR"
    "trainer.export_path=$EXPORT_DIR"
    trainer.resume_mode=from_path
    "trainer.resume_path=$RESUME_CHECKPOINT"
    generator.inference_engine.num_engines=1
    generator.inference_engine.tensor_parallel_size=8
    generator.inference_engine.run_engines_locally=true
    generator.inference_engine.backend=vllm
    generator.inference_engine.weight_sync_backend=nccl
    generator.inference_engine.async_engine=true
    generator.inference_engine.enforce_eager=true
    generator.inference_engine.gpu_memory_utilization=0.45
    generator.inference_engine.served_model_name=Qwen3.5-9B
    "generator.n_samples_per_prompt=$N_SAMPLES"
    "generator.eval_n_samples_per_prompt=$N_SAMPLES"
    generator.max_turns=8
    generator.step_wise_trajectories=true
    generator.merge_stepwise_output=true
    generator.rate_limit.enabled=true
    "generator.rate_limit.max_concurrency=$MAX_CONCURRENCY"
    "generator.sampling_params.max_generate_length=$MAX_OUTPUT_TOKENS"
    "generator.eval_sampling_params.max_generate_length=$MAX_OUTPUT_TOKENS"
    "harbor_trial_config.trials_dir=$TRIALS_DIR"
    harbor_trial_config.environment.delete=true
    harbor_trial_config.agent.kwargs.max_turns=8
    harbor_trial_config.agent.kwargs.trajectory_config.raw_content=true
)

echo "TerminalBench checkpoint evaluation"
echo "  mode:       $MODE_NAME"
echo "  tasks:      ${#TASKS[@]}"
echo "  trials:     $N_SAMPLES per task"
echo "  concurrency:$MAX_CONCURRENCY"
echo "  max output: $MAX_OUTPUT_TOKENS tokens"
echo "  checkpoint: $CHECKPOINT"
echo "  resume as:  $RESUME_CHECKPOINT"
echo "  SkyRL:      $SKYRL_DIR"
echo "  output:     $RUN_DIR"
echo "  S3:         $S3_RUN_URI"
if [[ $TEST_MODE -eq 1 ]]; then
    printf '  selected:   %s\n' "${TASKS[@]}"
fi

echo "Checking runtime imports..."
RUNTIME_OK=1
if ! "$SKY_ENV/bin/python" -c 'import harbor, numpy, ray, torch, transformers, vllm' 2>/dev/null; then
    RUNTIME_OK=0
    echo "  SkyRL environment is missing one or more required packages." >&2
fi

AWS_OK=1
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    AWS_OK=0
    echo "  AWS credentials are unavailable or expired; run 'aws login' before evaluation." >&2
fi

if pgrep -f '[r]un_docker_cleanup_loop.sh' >/dev/null; then
    echo "Docker cleanup loop is running; stop it before TerminalBench evaluation to protect cached images." >&2
    exit 1
fi

printf 'SkyRL command: '
printf '%q ' "${SKYRL_CMD[@]}"
printf '\n'

if [[ $DRY_RUN -eq 1 ]]; then
    echo "Dry run complete; no evaluation or upload was started."
    [[ $RUNTIME_OK -eq 1 && $AWS_OK -eq 1 ]] || exit 1
    exit 0
fi

[[ $RUNTIME_OK -eq 1 ]] || exit 1
[[ $AWS_OK -eq 1 ]] || exit 1
command -v docker >/dev/null || { echo "docker is required" >&2; exit 1; }
command -v nvidia-smi >/dev/null || { echo "nvidia-smi is required" >&2; exit 1; }
[[ "$(nvidia-smi --query-gpu=index --format=csv,noheader | wc -l)" -eq 8 ]] || { echo "Expected 8 visible GPUs" >&2; exit 1; }

mkdir -p "$RUN_DIR" "$TRIALS_DIR" "$EXPORT_DIR" "$SCRATCH_CKPT_DIR" "$ARCHIVE_DIR"
if [[ -e "$RESUME_CHECKPOINT" || -L "$RESUME_CHECKPOINT" ]]; then
    [[ "$RESUME_CHECKPOINT" -ef "$CHECKPOINT" ]] || {
        echo "Checkpoint alias already exists with a different target: $RESUME_CHECKPOINT" >&2
        exit 1
    }
else
    ln -s "$CHECKPOINT" "$RESUME_CHECKPOINT"
fi
"$SKY_ENV/bin/python" - "$TRAIN_TASKS_JSON" "$EVAL_TASKS_JSON" "$TRAIN_BATCH_SIZE" "${TASKS[@]}" <<'PY'
import json
import sys
from pathlib import Path

train_path, eval_path = map(Path, sys.argv[1:3])
train_batch_size = int(sys.argv[3])
tasks = sys.argv[4:]
train_tasks = tasks if len(tasks) >= train_batch_size else [
    tasks[index % len(tasks)] for index in range(train_batch_size)
]
train_path.write_text(json.dumps(train_tasks, indent=2) + "\n")
eval_path.write_text(json.dumps(tasks, indent=2) + "\n")
PY

archive_and_upload() {
    "$SKY_ENV/bin/python" "$REPO/scripts/archive_tb_trials.py" \
        --trials-dir "$TRIALS_DIR" \
        --archive-dir "$ARCHIVE_DIR" \
        --run-name "$RUN_NAME" \
        --checkpoint "$CHECKPOINT" \
        --model "$MODEL" \
        --dataset terminal-bench/terminal-bench-2-1 \
        --mode "$MODE_NAME" \
        --n-samples "$N_SAMPLES"
    aws s3 sync "$ARCHIVE_DIR/" "$S3_RUN_URI/" --only-show-errors
}

UPLOAD_STOP_FILE="$RUN_DIR/.incremental-upload-stop"
rm -f "$UPLOAD_STOP_FILE"
(
    while [[ ! -f "$UPLOAD_STOP_FILE" ]]; do
        archive_and_upload || echo "Incremental upload failed; retrying in 10 seconds." >&2
        sleep 10
    done
    archive_and_upload
) &
UPLOADER_PID=$!

cd "$SKYRL_DIR"
set +e
RAY_memory_usage_threshold=0.99 \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
HF_HOME=/tmp/hf_cache \
WANDB_MODE=offline \
SKYRL_DUMP_INFRA_LOG_TO_STDOUT=1 \
VLLM_ATTENTION_BACKEND=TORCH_SDPA \
FLASHINFER_DISABLE_VERSION_CHECK=1 \
MSWEA_API_KEY=nokey \
"${SKYRL_CMD[@]}" 2>&1 | tee "$LOG_FILE"
EVAL_STATUS=${PIPESTATUS[0]}
set -e

touch "$UPLOAD_STOP_FILE"
UPLOAD_STATUS=0
wait "$UPLOADER_PID" || UPLOAD_STATUS=$?
rm -f "$UPLOAD_STOP_FILE"
if [[ $UPLOAD_STATUS -eq 0 ]]; then
    echo "Uploaded trial artifacts to $S3_RUN_URI/"
else
    echo "Final trial artifact upload failed." >&2
fi

[[ $EVAL_STATUS -eq 0 ]] || exit "$EVAL_STATUS"
exit "$UPLOAD_STATUS"
