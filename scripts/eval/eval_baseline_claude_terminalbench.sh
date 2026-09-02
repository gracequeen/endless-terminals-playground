#!/bin/bash
# TerminalBench baseline for Claude Opus (4.6) via AICore.
# run_terminal_bench.sh uses EndlessAgent (vLLM-based) and doesn't support AICore,
# so we call Harbor directly here.
set -e
cd "$(dirname "$0")/../.."
source .venv/bin/activate

JOBS_DIR="solution_tb_baseline"
JOB_NAME="tb-baseline-claude-opus"
N_CONCURRENT=5
S3_DEST="s3://endless-terminals-training/baselines/claude-opus_terminalbench"

mkdir -p "$JOBS_DIR" harbor_logs
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker network prune -f

echo "Running TerminalBench eval with Claude Opus..."
PYTHONPATH="$PWD/generator:$PYTHONPATH" .venv/bin/harbor run \
  -d terminal-bench/terminal-bench@latest \
  --agent-import-path aicore_agent:AICoreTerminus2 \
  --model claude_opus \
  --n-concurrent $N_CONCURRENT \
  --jobs-dir "$JOBS_DIR" \
  --job-name "$JOB_NAME" \
  2>&1 | tee harbor_logs/tb_run_${JOB_NAME}.log

echo "Collecting results..."
python3 -c "
import json, sys
from pathlib import Path

job_dir = Path('$JOBS_DIR/$JOB_NAME')
results = [json.loads(f.read_text()) for f in sorted(job_dir.rglob('result.json'))]
total = len(results)
if total == 0:
    print('No results found'); sys.exit(0)

passed = sum(1 for r in results if float((r.get('verifier_result') or {}).get('rewards', {}).get('reward', 0)) >= 1.0)
print(f'Tasks: {total}, Passed: {passed}, Solve rate: {passed/total:.3f}')

summary = {'total': total, 'passed': passed, 'solve_rate': passed/total}
Path('$JOBS_DIR/summary.json').write_text(json.dumps(summary, indent=2))
print('Written: $JOBS_DIR/summary.json')
"

echo "Uploading to S3..."
aws s3 sync "$JOBS_DIR/" "$S3_DEST/" --no-progress
echo "Done. Results at: $S3_DEST"
