# collect_harbor_results.py — pass@k verification & Qwen3.5-9B run result

**Date:** 2026-09-03
**Branch:** `benchmark-tb-qwen`
**Files:** `generator/collect_harbor_results.py` (patched), `solution_tb/tb-base-qwen3.5-9b-5tasks-4trials/`

---

## 1. Actual model result (real data)

**Qwen3.5-9B (base) on terminal-bench — 5 tasks × 4 trials, concurrency 8:**

| Task | passed | pass@1 | pass@4 |
|---|---|---|---|
| biped-contact-dynamics | 0/4 | 0.000 | 0.000 |
| ks-solver-cpp | 0/4 | 0.000 | 0.000 |
| layout-config-recreation2 | 0/4 | 0.000 | 0.000 |
| mp-checkpoint-consolidation | 0/4 | 0.000 | 0.000 |
| photonic-waveguide-routing | 0/4 | 0.000 | 0.000 |
| **Average** | **0/20** | **0.000** | **0.000** |

All 20 real trials scored reward 0.0 (matches Harbor's own final summary: `reward = 0.0 → 20`).
These 5 are the first 5 tasks (hardest-looking) out of **66 total** terminal-bench tasks —
a small, hard, non-representative slice, not the model's overall benchmark score.

---

## 2. Collector verification (synthetic data — NOT model results)

The patched collector was validated on **fabricated** trial data with a mix of passes and
failures, because the real run was all-zeros and could not exercise the pass@k math (0.000
is trivially correct regardless of the formula). The collector's output was checked against
hand-computed values using the unbiased pass@k estimator (Chen et al., 2021):

    pass@k = 1 − C(n−c, k) / C(n, k)      # n = trials, c = successes, C = "n choose k"

Synthetic tasks and expected vs. actual:

- **taskA**: 2/4 pass → pass@1 = 0.500, pass@4 = 1.000  ✓
- **taskB**: 1/4 pass → pass@1 = 0.250, pass@2 = 1 − C(3,2)/C(4,2) = 1 − 3/6 = 0.500, pass@4 = 1.000  ✓
- **taskC**: 1/4 pass, incl. one crashed trial with no `verifier_result` that correctly
  fell back to `reward.txt` = 0 (counted as a non-pass)  ✓

Aggregate (averaged over the 3 synthetic tasks):

- **pass@1** = (0.5 + 0.25 + 0.25) / 3 = **0.333**  ✓
- **pass@2** = (0.833 + 0.5 + 0.5) / 3 = **0.611**  ✓   (taskA: 1 − C(2,2)/C(4,2) = 1 − 1/6 = 0.833)
- **pass@4** = (1 + 1 + 1) / 3 = **1.000**  ✓

> These 0.333 / 0.611 / 1.000 numbers are TEST INPUTS proving the collector is correct.
> They are NOT the model's scores. The synthetic data was deleted after the test.

---

## 3. What the patch fixed

The old collector only *reported* metrics as a side-effect of copying trials into a local
`--tasks-dir`. Terminal-bench is a registry dataset with no local task dir, so every task hit
"task directory not found" and it printed **"No results collected"** despite valid rewards.

Patch (decouples metrics from copying):
- **`summarize_task()`** always computes pass@k from the collected trials; copying trials into
  `<task>/solution/` is now best-effort and never blocks metrics.
- **`_read_reward()`** reads the true per-trial signal from `result.json →
  verifier_result.rewards.reward`, falls back to `verifier/reward.txt`, then `0.0`
  (a crashed trial correctly counts as a non-pass).
- **Aggregation** averages each pass@k only over tasks with ≥ k trials (annotated when a
  subset), instead of using `min(num_runs)` as a global k-ceiling.

Run it:

    .venv/bin/python generator/collect_harbor_results.py --jobs-dir solution_tb
