#!/usr/bin/env bash
# Download FSDP checkpoints from S3, convert to HF format, and run terminal-bench eval.
#
# For each checkpoint step:
#   1. Download FSDP model shards from S3 (skipping optimizer shards)
#   2. Convert FSDP shards -> HF safetensors via train/convert_fsdp_to_hf.py
#   3. Run terminal-bench eval via scripts/run_terminal_bench.sh
#   4. Clean up raw shards to save disk space
#
# Usage:
#   bash scripts/eval_checkpoints.sh \
#       --s3-path s3://endless-terminals-training/20260726_8192deduped-task_harbor-grpo_qwen3.5-4b_p5_Xsteps \
#       --model Qwen/Qwen3.5-4B \
#       --steps "200 220 240 260"
#
# Results land in solution_tb/<job-name>/ per step.
# Collect all: python generator/collect_harbor_results.py --jobs-dir solution_tb

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${REPO}/.venv/bin/python"
WORK_DIR="/home/ec2-user/ckpt_eval"   # scratch space for downloads + HF conversion
JOBS_DIR="solution_tb"
N_CONCURRENT=10
STEPS=""
S3_PATH=""
MODEL=""
JOB_PREFIX="tb-ckpt"

usage() {
    cat <<EOF
Usage: $0 --s3-path S3_PATH --model MODEL [options]

Required:
  --s3-path S3_PATH    S3 prefix containing global_step_N/ dirs
  --model MODEL        Base HF model name (e.g. Qwen/Qwen3.5-4B)

Optional:
  --steps "N N N"      Space-separated step numbers (default: auto-detect from S3)
  --job-prefix PREFIX  Prefix for terminal-bench job names (default: $JOB_PREFIX)
  --work-dir DIR       Local scratch dir for downloads/conversion (default: $WORK_DIR)
  --jobs-dir DIR       Terminal-bench results dir (default: $JOBS_DIR)
  --n-concurrent N     Concurrent Harbor tasks per eval (default: $N_CONCURRENT)
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --s3-path)      S3_PATH="$2";      shift 2 ;;
        --model)        MODEL="$2";        shift 2 ;;
        --steps)        STEPS="$2";        shift 2 ;;
        --job-prefix)   JOB_PREFIX="$2";   shift 2 ;;
        --work-dir)     WORK_DIR="$2";     shift 2 ;;
        --jobs-dir)     JOBS_DIR="$2";     shift 2 ;;
        --n-concurrent) N_CONCURRENT="$2"; shift 2 ;;
        --help|-h)      usage ;;
        *) echo "Unknown arg: $1"; usage ;;
    esac
done

[[ -z "$S3_PATH" ]] && echo "Error: --s3-path is required" && usage
[[ -z "$MODEL"   ]] && echo "Error: --model is required"   && usage

S3_PATH="${S3_PATH%/}"   # strip trailing slash

# ── auto-detect steps from S3 if not provided ────────────────────────────────
if [[ -z "$STEPS" ]]; then
    echo "[eval-ckpts] Auto-detecting steps from S3..."
    STEPS=$(aws s3 ls "${S3_PATH}/" \
        | grep -oP 'global_step_\K[0-9]+' \
        | sort -n \
        | tr '\n' ' ')
    [[ -z "$STEPS" ]] && echo "Error: no global_step_N/ dirs found at ${S3_PATH}/" && exit 1
    echo "[eval-ckpts] Found steps: $STEPS"
fi

mkdir -p "$WORK_DIR"

# ── process each step ─────────────────────────────────────────────────────────
for STEP in $STEPS; do
    echo ""
    echo "============================================================"
    echo "[eval-ckpts] Processing global_step_${STEP}"
    echo "============================================================"

    S3_POLICY="${S3_PATH}/global_step_${STEP}/policy"
    LOCAL_FSDP="${WORK_DIR}/global_step_${STEP}/policy"
    LOCAL_HF="${WORK_DIR}/global_step_${STEP}/hf"
    JOB_NAME="${JOB_PREFIX}-step${STEP}"

    # ── skip if already evaluated ─────────────────────────────────────────────
    RESULT_DIR="${REPO}/${JOBS_DIR}/${JOB_NAME}"
    if [[ -d "$RESULT_DIR" ]]; then
        echo "[eval-ckpts] step ${STEP}: results dir already exists ($RESULT_DIR), skipping."
        continue
    fi

    # ── 1. download FSDP shards (skip optimizer shards — large, not needed) ──
    echo "[eval-ckpts] step ${STEP}: downloading model shards from S3..."
    mkdir -p "$LOCAL_FSDP"
    aws s3 sync "${S3_POLICY}/" "${LOCAL_FSDP}/" \
        --no-progress \
        --exclude "optim_*"

    echo "[eval-ckpts] step ${STEP}: download complete."
    du -sh "$LOCAL_FSDP"

    # ── 2. convert FSDP -> HF ─────────────────────────────────────────────────
    echo "[eval-ckpts] step ${STEP}: converting FSDP shards to HF format..."
    mkdir -p "$LOCAL_HF"
    "$PYTHON" "${REPO}/train/convert_fsdp_to_hf.py" \
        --backend fsdp \
        --hf_model_path "$MODEL" \
        --local_dir "${LOCAL_FSDP}" \
        --target_dir "${LOCAL_HF}"

    echo "[eval-ckpts] step ${STEP}: HF checkpoint written to ${LOCAL_HF}"
    ls "$LOCAL_HF"

    # ── 3. clean up FSDP shards to free disk ─────────────────────────────────
    echo "[eval-ckpts] step ${STEP}: cleaning up FSDP shards..."
    rm -rf "$LOCAL_FSDP"

    # ── 4. run terminal-bench eval ────────────────────────────────────────────
    echo "[eval-ckpts] step ${STEP}: launching terminal-bench eval (job: ${JOB_NAME})..."
    bash "${REPO}/scripts/run_terminal_bench.sh" \
        --mode checkpoint \
        --checkpoint "$LOCAL_HF" \
        --model "$MODEL" \
        --job-name "$JOB_NAME" \
        --jobs-dir "$JOBS_DIR" \
        --n-concurrent "$N_CONCURRENT"

    echo "[eval-ckpts] step ${STEP}: eval launched in tmux. Waiting for completion..."

    # Wait for Harbor job to finish (poll result dir for terminal-bench tasks)
    POLL_INTERVAL=60
    MAX_WAIT=7200   # 2 hours per step
    ELAPSED=0
    while true; do
        # Harbor writes result.json per trial; count completed ones
        DONE=$(find "$RESULT_DIR" -name "result.json" 2>/dev/null | wc -l)
        if [[ $DONE -gt 0 ]]; then
            # Wait until count is stable for two poll cycles (eval finished)
            sleep "$POLL_INTERVAL"
            DONE2=$(find "$RESULT_DIR" -name "result.json" 2>/dev/null | wc -l)
            if [[ $DONE -eq $DONE2 ]]; then
                echo "[eval-ckpts] step ${STEP}: eval complete ($DONE tasks)."
                break
            fi
        fi
        if [[ $ELAPSED -ge $MAX_WAIT ]]; then
            echo "[eval-ckpts] WARNING: step ${STEP} eval timed out after ${MAX_WAIT}s."
            break
        fi
        sleep "$POLL_INTERVAL"
        ELAPSED=$((ELAPSED + POLL_INTERVAL))
    done

    # ── 5. clean up HF checkpoint to free disk ────────────────────────────────
    echo "[eval-ckpts] step ${STEP}: cleaning up HF checkpoint..."
    rm -rf "$LOCAL_HF"

    echo "[eval-ckpts] step ${STEP}: done."
done

# ── collect aggregate results ─────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "[eval-ckpts] All steps done. Collecting results..."
echo "============================================================"
cd "$REPO"
"$REPO/.venv/bin/python" "$REPO/generator/collect_harbor_results.py" --jobs-dir "$JOBS_DIR"

SUMMARY_FILE="${REPO}/${JOBS_DIR}/eval_checkpoints_summary.txt"
{
    echo "Checkpoint eval summary"
    echo "S3 path: ${S3_PATH}"
    echo "Model:   ${MODEL}"
    echo "Steps:   ${STEPS}"
    echo "Date:    $(date -u)"
    echo ""
    for STEP in $STEPS; do
        JOB_NAME="${JOB_PREFIX}-step${STEP}"
        AGG="${REPO}/${JOBS_DIR}/${JOB_NAME}/aggregate_pass_at_k.json"
        if [[ -f "$AGG" ]]; then
            PASS1=$("$REPO/.venv/bin/python" -c "import json; d=json.load(open('$AGG')); print(d.get('pass@1', 'n/a'))" 2>/dev/null || echo "n/a")
            echo "  step ${STEP}: pass@1 = ${PASS1}"
        else
            echo "  step ${STEP}: no aggregate results"
        fi
    done
} | tee "$SUMMARY_FILE"

echo ""
echo "Summary written to: $SUMMARY_FILE"
echo "Full results in:    ${REPO}/${JOBS_DIR}/"
