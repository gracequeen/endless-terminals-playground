#!/bin/bash
# TerminalBench baseline for Qwen3.5-4B base model.
set -e
cd "$(dirname "$0")/../.."

S3_DEST="s3://endless-terminals-training/baselines/qwen3.5-4b-base_terminalbench"

mkdir -p harbor_logs solution_tb_baseline_qwen4b
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker network prune -f

if [ -d "/usr/local/cuda" ] && [ -f "/usr/local/cuda/bin/nvcc" ]; then
  export CUDA_HOME=/usr/local/cuda
elif [ -f "/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13/bin/nvcc" ]; then
  export CUDA_HOME=/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13
else
  NVCC_PATH=$(which nvcc 2>/dev/null || true)
  [ -n "$NVCC_PATH" ] && export CUDA_HOME=$(dirname $(dirname "$NVCC_PATH")) || { echo "ERROR: nvcc not found" >&2; exit 1; }
fi
export PATH="$CUDA_HOME/bin:$PATH"
[ ! -e "$CUDA_HOME/lib64" ] && [ -d "$CUDA_HOME/lib" ] && ln -sf "$CUDA_HOME/lib" "$CUDA_HOME/lib64"
rm -rf ~/.cache/flashinfer

VLLM_PORT=8110
echo "Starting vLLM server for Qwen3.5-4B on port $VLLM_PORT..."
# Remove any existing job dir with stale config from previous runs
rm -rf solution_tb_baseline_qwen4b/tb-baseline-qwen3.5-4b
source /tmp/sky/bin/activate
CUDA_VISIBLE_DEVICES=2 VLLM_ATTENTION_BACKEND=TORCH_SDPA python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3.5-4B \
  --served-model-name Qwen3.5-4B \
  --port $VLLM_PORT \
  --api-key nokey \
  --trust-remote-code \
  --gpu-memory-utilization 0.85 \
  --enforce-eager \
  2>&1 | tee harbor_logs/vllm_qwen4b_tb.log &
VLLM_PID=$!

echo "Waiting for vLLM server to be ready..."
until curl -sf http://localhost:$VLLM_PORT/health >/dev/null 2>&1; do
  sleep 5
  if ! kill -0 $VLLM_PID 2>/dev/null; then echo "vLLM died, aborting"; exit 1; fi
done
echo "vLLM ready."

source .venv/bin/activate
OPENAI_API_KEY=nokey PYTHONPATH="$PWD/generator:$PYTHONPATH" .venv/bin/harbor run \
  -d terminal-bench/terminal-bench@latest \
  --agent-import-path endless_harbor.endless_agent:EndlessAgent \
  --model http://localhost:$VLLM_PORT/v1 \
  --n-concurrent 10 \
  --jobs-dir solution_tb_baseline_qwen4b \
  --job-name tb-baseline-qwen3.5-4b \
  2>&1 | tee harbor_logs/tb_run_tb-baseline-qwen3.5-4b.log

kill $VLLM_PID 2>/dev/null || true

echo "Collecting results..."
python3 -c "
import json, sys
from pathlib import Path

job_dir = Path('solution_tb_baseline_qwen4b/tb-baseline-qwen3.5-4b')
results = [json.loads(f.read_text()) for f in sorted(job_dir.rglob('result.json'))]
total = len(results)
if total == 0:
    print('No results found'); sys.exit(0)

passed = sum(1 for r in results if float((r.get('verifier_result') or {}).get('rewards', {}).get('reward', 0)) >= 1.0)
print(f'Tasks: {total}, Passed: {passed}, Solve rate: {passed/total:.3f}')

summary = {'total': total, 'passed': passed, 'solve_rate': passed/total}
Path('solution_tb_baseline_qwen4b/summary.json').write_text(json.dumps(summary, indent=2))
print('Written: solution_tb_baseline_qwen4b/summary.json')
"

echo "Uploading to S3..."
aws s3 sync solution_tb_baseline_qwen4b/ "$S3_DEST/" --no-progress
echo "Done. Results at: $S3_DEST"
