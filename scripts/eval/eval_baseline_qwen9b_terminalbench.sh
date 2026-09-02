#!/bin/bash
# TerminalBench baseline for Qwen3.5-9B base model.
set -e
cd "$(dirname "$0")/../.."

bash scripts/run_terminal_bench.sh \
  --mode base \
  --model Qwen/Qwen3.5-9B \
  --job-name tb-baseline-qwen3.5-9b \
  --jobs-dir solution_tb_baseline \
  --n-concurrent 10

echo "Collect results with:"
echo "  python generator/collect_harbor_results.py --jobs-dir solution_tb_baseline"
