# pass@k Eval Test — Solution

## Problem

The spec (`pass@k_eval_test.md`) asked to:
1. Copy 2 tasks from the `4.8opus_tasks` folder (`harbor_4.8opus_tasks_v3`).
2. Run a baseline eval on those 2 tasks with **Qwen3.5-9B**, **8 attempts** per task.
3. Verify **pass@k for k = 1, 2, 3, 4, 8** all produce valid results.

## Changes made

No production code changes were needed — the eval runner (`evaluate_baseline.py`)
was already updated earlier this session to default to `ks = [1, 2, 3, 4, 8]`
(previously `[1, 2, 3, 4, 10]`; pass@10 is undefined for n=8 attempts, pass@8 is
the max computable metric).

Artifacts created:
- **`harbor_tasks_passk_test/`** — the 2-task eval dataset, copied from
  `harbor_4.8opus_tasks_v3/`:
  - `task_000000_6a6f5dd1` — category *performance optimization*, difficulty `hard`
  - `task_000000_78c5d962` — category *security scanning*, difficulty `hard`
  - Two distinct categories were chosen for coverage. Both tasks were verified
    to contain the full required file set (`task.toml`, `instruction.md`,
    `environment/{Dockerfile,task.json,test_initial_state.py}`,
    `tests/{test.sh,test_final_state.py}`), and both Dockerfiles already carry
    the `# syntax=docker/dockerfile:1` directive (the known heredoc-build fix).
- **`baseline_results/passk_eval_test_9b/`** — 16 harbor trial dirs (2 tasks × 8 attempts).
- **`output/passk_eval_test_9b.{json,md}`** — pass@k summaries.
- **`harbor_logs/passk_eval_test_9b.log`** — run log.

## Behavior summary

Command run (backgrounded):
```bash
.venv/bin/python evaluate_baseline.py \
  --dataset-path harbor_tasks_passk_test \
  --model Qwen/Qwen3.5-9B \
  --n-attempts 8 \
  --n-concurrent 4 \
  --jobs-dir baseline_results \
  --job-name passk_eval_test_9b \
  --vllm-base-url http://localhost:8006/v1
```

- Qwen3.5-9B is served by vLLM on ports 8000/8006/8007; the eval pointed at
  **8006**. The `--ae VLLM_BASE_URL=...` flag (plus this session's earlier
  `generator/__init__.py` + `endless_harbor/endless_agent.py` fix) routes the
  agent's LLM calls to the correct server.
- `--n-concurrent 4` keeps Docker network/address-pool pressure low (16 trials
  total, ≤4 concurrent).
- All 16 trials completed: **0 exceptions, 0 build failures**. Docker images
  built cleanly (heredoc directive present). Agents ran substantively
  (7–38 episodes per trial).

### Results

| Metric | Value |
|--------|-------|
| Total tasks | 2 |
| Tasks solved | 0 |
| pass@1 | 0.0000 |
| pass@2 | 0.0000 |
| pass@3 | 0.0000 |
| pass@4 | 0.0000 |
| pass@8 | 0.0000 |

All five pass@k metrics (k=1,2,3,4,8) are **present and valid**. The 0.0 values
are a legitimate outcome: Qwen3.5-9B solved neither `hard` task in any of its 8
attempts (0 successes → pass@k = 0 for every k by the unbiased estimator). The
zeros are genuine agent failures, not a routing or scoring artifact — every trial
has `reward=0.0` with a real episode count.

## Verification

- **All 5 metrics computed:** `output/passk_eval_test_9b.md` and `.json` both list
  pass@1/2/3/4/8 in the aggregate and per-task tables.
- **Trials are real:** `find baseline_results/passk_eval_test_9b -mindepth 2 -name result.json | wc -l` → 16;
  every trial has `verifier_result.rewards.reward = 0.0` and `n_episodes` between 7 and 38.
- **Estimator sanity:** for n=8, c=0 the unbiased pass@k estimator returns 0.0 for
  all k (confirmed via `compute_pass_at_k(8, 0)`); for c≥1 it returns non-zero and
  pass@8 = 1.0, so the metric is well-defined at k=8 (it was N/A at k=10).
- **Re-run:** rebuild the summaries from existing trials without re-running the
  agent via `generator/collect_harbor_results.py --jobs-dir baseline_results/passk_eval_test_9b`,
  or re-run end-to-end with the command above.
