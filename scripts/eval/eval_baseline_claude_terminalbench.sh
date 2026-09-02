#!/bin/bash
# TerminalBench baseline for Claude Opus (4.6) via AICore.
# run_terminal_bench.sh uses EndlessAgent (vLLM-based) and doesn't support AICore,
# so we call Harbor directly here.
set -e
cd "$(dirname "$0")/../.."
source .venv/bin/activate

JOBS_DIR="solution_tb_baseline"
JOB_NAME="tb-baseline-claude-opus"
N_CONCURRENT=10

mkdir -p "$JOBS_DIR"

echo "Running TerminalBench eval with Claude Opus..."
.venv/bin/harbor run \
  -d terminal-bench/terminal-bench@latest \
  --agent-import-path aicore_agent:AICoreTerminus2 \
  --model claude_opus \
  --n-concurrent $N_CONCURRENT \
  --jobs-dir "$JOBS_DIR" \
  --job-name "$JOB_NAME" \
  2>&1 | tee harbor_logs/tb_run_${JOB_NAME}.log

echo "Collect results with:"
echo "  python generator/collect_harbor_results.py --jobs-dir $JOBS_DIR"
