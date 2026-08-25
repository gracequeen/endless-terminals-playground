# Design: Large Instance Experiments — 4B and 9B

## Motivation

All previous training runs used p5.48xlarge (8× H100 80GB). The OOM root cause is:

```
sequence_length × vocab_size (151k) × 4 bytes = huge backward pass allocation
```

On H100 80GB in colocated mode, we were forced into settings too constrained for stable GRPO:
- batch_size=4 (not enough reward variance)
- max_turns=6 (model can't finish complex tasks)
- max_generate_length=1024 (outputs may be truncated)

These constraints caused model collapse in the 20260723 run. Larger instances remove these constraints.

---

## Instance Comparison

| Instance | GPU | Memory/GPU | Total Memory | Use case |
|----------|-----|-----------|--------------|----------|
| p5.48xlarge | 8× H100 80GB | 80 GB | 640 GB | Current — too constrained for stable GRPO |
| p5en.48xlarge | 8× H200 141GB | 141 GB | 1128 GB | **4B training — recommended** |
| b300*.48xlarge | 8× B300 288GB | 288 GB | 2304 GB | **9B training — recommended** |

> **Note on p5e**: specs are inconsistent between this doc and experiment logs — 20260808 ran on `p5e.48xlarge` and observed H200 141GB behavior. Treat p5e and p5en as equivalent until confirmed with AWS.

### Why p5en for 4B

The 4B model has ~8GB of weights. The memory bottleneck is the backward pass log_softmax allocation:

```
max_seq_len × vocab_size × 4 bytes = 8192 × 151k × 4 ≈ 5 GB per sequence
```

p5en (141 GB/GPU) handles this comfortably and allows paper-equivalent settings (batch=16, turns=16, generate=2048) without OOM. p5 (80 GB) forces the too-small settings that caused the 20260723 collapse.

### Why b300 for 9B

The 9B model has ~18 GB of weights. At paper-scale settings (batch=32, n_samples=16, turns=16), memory pressure is significant. b300 (288 GB/GPU) removes all memory constraints — every config in the ablation table below is safe, including paper-equivalent Test 4 (512 rollouts/step).

---

## Models

### 4B — Qwen3.5-4B on p5en

**Base eval avg_score**: 49% on deduped 8192 dataset

The 4B model solves roughly half the deduped tasks at baseline. This gives GRPO healthy reward variance — not too easy, not too hard. No dataset modification needed before running the ablation.

**Model path**: `Qwen/Qwen3.5-4B` (or instruct variant)

### 9B — Qwen3.5-9B on b300

**Base eval avg_score**: 58% on deduped 8192 dataset (20260808 run)

However, avg_pass_at_4 = 95% during training rollouts on the same dataset — the model already solves nearly every task, leaving almost no GRPO gradient (std_reward ≈ 0). On the harder task set, measured pass@8 solvability was 6.2%, which is too sparse — with batch=16, expect only ~1 solvable task per step.

Before running the ablation for 9B, verify reward density on the target dataset:
- If avg_pass_at_4 > 80%: switch to harder tasks or implement partial rewards (Phase 7)
- If pass@8 < 20%: filter to only tasks with ≥1 pass in 8 attempts before training

**Model path**: `Qwen/Qwen3.5-9B` (or instruct variant)

---

## Experiment Plan

### Phase 1: Dry Run (20 steps)

**Goal**: Verify the setup is stable and reward signal is non-zero before committing to a full run.

**Model**: Qwen3.5-9B on p5en (H200 141GB)

**Dataset**: Combined Original 457 + Deduped 8192 tasks
- Train: 3,238 tasks (457 + 2,781)
- Val: 151 tasks (51 + 100)
- S3: `s3://endless-terminals-training/prepared_data/train_combined_457_8192.parquet`
- Task dirs: `harbor_tasks_457/` + `harbor_tasks_8192_deduped/` on instance

**Config** (p5e baseline — conservative, known safe):

| Setting | Value |
|---------|-------|
| train_batch_size | 4 |
| n_samples_per_prompt | 4 |
| max_turns | 6 |
| max_generate_length | 1024 |
| max_seq_len | 4096 |
| gpu_memory_utilization | 0.35 |
| micro_train_batch_size_per_gpu | 1 |
| update_epochs_per_batch | 1 |

> **Critical**: `max_turns=6` must be set in both `generator.max_turns` (train script) AND `default.yaml → agent.kwargs.max_turns`. The dry run script sets both automatically.

**Run**:
```bash
bash scripts/prepare_combined_data.sh                        # step 1: download + combine datasets
bash scripts/train/train_harbor_qwen3_5_9b_dryrun.sh        # step 2: 20-step dry run
```

**Checkpointing**: every 5 steps, eval every 10 steps on 50 held-out tasks

**Metrics collected** (automatically via `scripts/collect_metrics.py`, uploaded to S3 every 30s):

Reward signal:

| Metric | Good | Bad |
|--------|------|-----|
| std_reward | > 0.1 consistently | Near 0 — all-pass or all-fail batches, no GRPO gradient |
| avg_pass@2 | Trending up from step 1 | Flat or dropping after step 10 |
| avg_reward | Slowly trending up | Flat throughout |

Stability:

| Metric | Good | Bad |
|--------|------|-----|
| policy_entropy | Stable or slowly declining | Sharp drop — entropy collapse |
| grad_norm | < 10, stable | Spiking above 50 (20260723 hit 64M at collapse) |
| policy_loss | Small, stable | Exploding (20260723 hit 2471 at step 186) |

Generation quality:

| Metric | Good | Bad |
|--------|------|-----|
| response_length | Well below 1024 | Hitting ceiling every step — model being cut off |
| sequence_length | Well below 4096 | Consistently at max |

**Per-task eval results**: saved per checkpoint as `eval_metrics.json` with individual pass/fail per task, enabling analysis of which task categories and difficulty levels the model solves. Output files: `training_metrics.json`, `eval_metrics.json`, `metrics_summary.json`.

**S3 output**: `s3://endless-terminals-training/<date>_combined-data_dryrun_grpo_qwen3.5-9b_20steps/`

**Decision rule**:
- If `std_reward ≈ 0` throughout → reward too sparse; filter to Opus-solvable tasks or implement partial rewards (Phase 7) before proceeding
- If `policy_entropy` drops sharply → collapse; check `default.yaml max_turns` matches `generator.max_turns`
- If both look healthy → proceed to Phase 3 ablation

**Result (2026-08-25, run `20260825_combined-data_dryrun_grpo_qwen3.5-9b_20steps` on p5en)**:

**S3**: `s3://endless-terminals-training/20260825_combined-data_dryrun_grpo_qwen3.5-9b_20steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun.sh`

- First run used `n_samples_per_prompt=4` — step 1 batch happened to draw all easy tasks → avg_pass_at_2=1.0, std_reward≈0. This was a bad batch, not a dataset problem.
- Fixed to `n_samples_per_prompt=2` (matching eval metric avg_pass_at_2). Re-ran same dataset.

**Training metrics (steps 1–20):**

| Metric | Value |
|--------|-------|
| std_reward (avg) | 0.37 |
| std_reward (range) | 0.33–0.50 (0.0 on 3/20 steps — all-pass batches, expected at batch_size=4) |
| avg_pass_at_2 (avg) | 0.74 |
| avg_pass_at_2 (range) | 0.25–1.0 (noisy — only 4 tasks/batch) |
| avg_response_length | ~530 tokens/turn (well below 1024 cap) |

**Eval metrics (step 20, 151 val tasks):**

| Metric | Value | Notes |
|--------|-------|-------|
| avg_score(pass@1) | **43.7%** | 1 attempt, solved within 6 turns |
| avg_score(pass@2) | N/A | Not measured — eval_n_samples_per_prompt=1 in this run |

> Note: SkyRL always runs eval on the final step regardless of `eval_interval` (hardcoded `or self.global_step == self.total_training_steps`). `eval_batch_size` is the dataloader batch size, not the number of eval tasks — all val tasks are always evaluated.
> For next run: set `trainer.eval_n_samples_per_prompt=2` so eval runs 2 independent attempts per task — making `avg_score(pass_any)` directly comparable to training's `avg_pass_at_2` (both measure "solved in at least 1 of 2 attempts"). Current eval used 1 attempt, making comparison invalid.

- **Decision**: combined 457+8192 dataset is suitable for 9B training on p5en. Proceed to next dry run with higher settings.

**Next dry run config (p5en, before moving to b300):**

| Setting | Current dry run | Next dry run |
|---------|----------------|--------------|
| train_batch_size | 4 | 8 |
| n_samples_per_prompt | 2 | 2 |
| max_turns | 6 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 8192 |
| gpu_memory_utilization | 0.35 | 0.45 |
| micro_train_batch_size_per_gpu | 1 | 1 |

**S3**: `s3://endless-terminals-training/<date>_combined-data_dryrun2_grpo_qwen3.5-9b_20steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun2.sh`

**Result (2026-08-25, dryrun2, in progress):**

**Training metrics (steps 1–16, updating):**

| Metric | Value |
|--------|-------|
| std_reward (avg) | 0.42 |
| std_reward (range) | 0.24–0.50 (no zero-std steps — larger batch_size=8 helping) |
| avg_pass_at_2 (avg) | 0.82 |
| avg_pass_at_2 (range) | 0.625–1.0 |

> **Note on max_seq_len vs max_turns**: for target b300 settings with max_turns=16 and max_generate_length=2048, max_seq_len must be raised to 16384–32768 to avoid truncating long trajectories. The 8192 limit in the next dry run is safe with max_turns=8.

### Phase 2: Full Training (200-300 steps)

**Goal**: Train a model that actually improves beyond baseline.

- Use full dataset (2781 training tasks, 100 val tasks for 4B; TBD for 9B based on task difficulty)
- Run 200-300 steps with checkpointing every 20 steps
- Save eval avg_score every 20 steps on 100 held-out tasks
- Upload checkpoints to S3 after each step, delete old ones to save disk

**Settings** (use the winning config from Phase 3 ablation as the starting point; these are the targets):

4B on p5en:

| Setting | Previous p5 (H100 80GB) | Target p5en |
|---------|------------------------|-------------|
| train_batch_size | 4 | 16 |
| n_samples_per_prompt | 4 | 8 |
| max_turns | 6 | 16 |
| max_generate_length | 1024 | 2048 |
| max_seq_len | 4096 | 8192 |
| gpu_memory_utilization | 0.10 | 0.40 |
| micro_train_batch_size_per_gpu | 1 | 2 |

9B on b300:

| Setting | 20260808 p5e baseline | Target b300 |
|---------|-----------------------|-------------|
| train_batch_size | 4 | 16 |
| n_samples_per_prompt | 4 | 8 |
| max_turns | 6 | 16 |
| max_generate_length | 1024 | 2048 |
| max_seq_len | 4096 | 8192 |
| gpu_memory_utilization | 0.35 | 0.60 |
| micro_train_batch_size_per_gpu | 1 | 2 |

**Success criteria**:
- 4B: eval avg_score at step 200 > 49% (base model) with clear upward trend
- 9B: eval avg_score at step 200 > 58% (base model) with clear upward trend; std_reward > 0.1 throughout

**Eval tracking**:
- Save per-task pass/fail results at every checkpoint, not just avg_score — this lets you analyze which categories or difficulty levels the model learns vs stays stuck on
- 100-200 eval tasks is fine; saving all results every checkpoint is cheap (10 checkpoints × 200 tasks = 2000 rows total)
- At the end, check: is the model only improving on easy tasks? Are certain task categories solved well while others are not? This breakdown is needed for paper analysis
- Extract checkpoints at steps ~100 and ~150 for terminal-bench eval to measure impact on external benchmarks

### Phase 3: Hyperparameter Tuning (Ablation)

**Goal**: Identify which settings have the most impact on training stability and reward signal. Run a controlled ablation — one baseline plus three tests, each changing exactly one group of parameters. This isolates cause from effect.

**Duration**: 30 steps per test. Long enough to catch collapse (policy_entropy drop and grad_norm spike are usually visible by step 20-30) and see an early reward trend.

#### Baseline (same for both 4B and 9B)

| Setting | Value |
|---------|-------|
| train_batch_size | 8 |
| n_samples_per_prompt | 4 |
| max_turns | 8 |
| max_generate_length | 1024 |
| max_seq_len | 4096 |

---

#### Test 1 — More tasks per step

Only `train_batch_size` changes. Tests whether more tasks per step gives GRPO enough reward variance.

| Setting | Baseline | Test 1 |
|---------|----------|--------|
| train_batch_size | 8 | **16** |
| n_samples_per_prompt | 4 | 4 |
| max_turns | 8 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 4096 |

---

#### Test 2 — Longer episodes

Only `max_turns`, `max_generate_length`, and `max_seq_len` change. These three are changed together because increasing turns without increasing per-turn length is not useful.

Tests whether giving the model more turns and more tokens per command helps it finish complex tasks.

| Setting | Baseline | Test 2 |
|---------|----------|--------|
| train_batch_size | 8 | 8 |
| n_samples_per_prompt | 4 | 4 |
| max_turns | 8 | **16** |
| max_generate_length | 1024 | **2048** |
| max_seq_len | 4096 | **8192** |

> Remember: `max_turns` must be set in both `default.yaml` AND `generator.max_turns`. Mismatch causes 20k+ token sequences and OOM.

---

#### Test 3 — More samples per task

Only `n_samples_per_prompt` changes. Tests whether more within-task contrast improves GRPO gradient quality.

| Setting | Baseline | Test 3 |
|---------|----------|--------|
| train_batch_size | 8 | 8 |
| n_samples_per_prompt | 4 | **8** |
| max_turns | 8 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 4096 |

---

#### Metrics

**Reward signal** — is GRPO getting anything to learn from?

| Metric | Good | Bad |
|--------|------|-----|
| std_reward | > 0.1 consistently | Near 0 every step — all-pass or all-fail batches |
| avg_pass@2 | Trending up from step 1 baseline | Flat or dropping after step 20 |
| avg_reward | Slowly trending up | Flat throughout |

`std_reward` is the single most important number. If it is near zero every step, the config is useless regardless of everything else. For 9B, also check avg_pass@2 at step 1 — if it is already 0.9+, the dataset is too easy before any training begins.

**Stability** — is training about to collapse?

| Metric | Good | Bad |
|--------|------|-----|
| policy_entropy | Stable or slowly declining | Sharp drop — entropy collapse |
| grad_norm | < 10, stable | Spiking above 50 (20260723 hit 64M at collapse) |
| policy_loss | Small, stable | Exploding (20260723 hit 2471 at step 186) |

**Generation quality** — is the model getting to use its turns?

| Metric | Good | Bad |
|--------|------|-----|
| response_length | Well below max_generate_length | Hitting the ceiling every step — model being cut off |
| sequence_length | Well below max_seq_len | Consistently at max — sequences being truncated |

> **Note**: Value Loss and Explained Variance are PPO/critic metrics. They do not appear in GRPO runs — ignore them.

#### Decision Rule

At step 30 for each test:
1. If `std_reward` is near 0 throughout → stop early, this config provides no GRPO signal
2. If `policy_entropy` is dropping sharply or `grad_norm` spikes → stop early, collapse in progress
3. If both look healthy → compare `avg_pass@2` trend; take the config with the clearest upward trend into Phase 2

If one test looks promising but inconclusive at step 30, extend that test to 50 steps. Do not extend all tests.

---

## Key Risks

1. **9B near-ceiling on deduped dataset** — avg_pass_at_4 = 95% means std_reward ≈ 0, no GRPO signal. Mitigate: filter to harder tasks or implement partial rewards (Phase 7) before training.
2. **9B sparse reward on harder tasks** — measured pass@8 = 6.2% on the harder task set. With batch=16, expect only ~1 solvable task/step. Mitigate: filter training set to tasks with ≥1 pass in 8 attempts.
3. **Test leakage** — model reads `/tests/test_final_state.py` to game verifier. Check trial logs before full run (Experiment D from EXPERIMENTS.md).
4. **Disk space** — each 9B checkpoint is ~40 GB, 4B is ~8 GB. Use `max_ckpts_to_keep=1` and S3 uploader.

---

## Phase 4: GRPO vs DPPO Comparison

**Motivation**: GRPO's core weakness is zero gradient when all samples in a batch pass or all fail — exactly the collapse pattern we saw in 20260723. DPPO (Distributed PPO) has a critic (value network) that estimates future returns and provides a training signal even when reward is sparse or all-zero.

| | GRPO | DPPO |
|--|------|------|
| Critic | No | Yes |
| Memory | Lower | ~2× (critic doubles parameters) |
| Gradient when all-fail | Zero | Non-zero (critic baseline) |
| Gradient when all-pass | Zero | Non-zero (critic baseline) |
| Stability | Needs reward variance | More stable, works with sparse reward |
| Harbor compatible | Yes | No — requires stateful GAE, use Direct Docker |

**On p5en (H200 141GB)**: critic memory is no longer a blocker. Running DPPO with a 9B model + critic becomes feasible.

**Proposed comparison experiment**:
1. Train 9B with GRPO on deduped 8192 dataset, 200 steps
2. Train 9B with DPPO on same dataset, same steps
3. Compare: reward curve stability, eval avg_score, collapse frequency

Note: DPPO requires Direct Docker approach (`train/sky_endless.py`), not Harbor — Harbor's step-wise trajectories are incompatible with GAE. This means switching back to stateless `bash -c` shell, which is less realistic than terminus-2's persistent shell.

---

## Phase 5: DAPO instead of Vanilla GRPO

**Paper**: "DAPO: An Open-Source LLM Reinforcement Learning System at Scale" (Yu et al., 2025, arXiv:2503.14476, NeurIPS 2025)

**Problem it solves**: Vanilla GRPO wastes gradient steps on degenerate batches where all samples pass (std_reward=0) or all fail (std_reward=0). The 20260723 collapse was directly caused by this — most batches with batch_size=4 were all-fail, giving zero gradient for hundreds of steps.

**What DAPO adds**:
- **Dynamic sampling**: skip prompts where all G samples pass or all fail — only train on batches with 0 < |passing samples| < G. Eliminates zero-gradient steps entirely.
- **Decoupled clipping**: higher clip threshold for exploration, lower for exploitation — prevents entropy collapse
- **Token-level gradient loss**: normalizes loss by token count rather than sequence count — handles varying response lengths better
- **No KL divergence**: removes KL penalty, relies on clipping alone for stability

**Implementation**: Drop-in replacement for GRPO loss in SkyRL. Check if SkyRL already supports `filter_groups` or similar option; otherwise small patch to the GRPO trainer.

**Expected impact**: Eliminates the zero-gradient death spiral. Should significantly stabilize training compared to 20260723.

---

## Phase 6: Curriculum Learning (Easy → Hard)

**Papers**:
- "DUMP: Automated Distribution-Level Curriculum Learning for RL-based LLM Post-training" (Wang et al., 2025, arXiv:2504.09710)
- "Curriculum Reinforcement Learning from Easy to Hard Tasks Improves LLM Reasoning" (Parashar et al., 2025, arXiv:2506.06632)

**Problem it solves**: Random task sampling means the model wastes steps on tasks it already solves (zero GRPO gradient) or tasks it can never solve (also zero gradient). The sweet spot is tasks where the model solves ~30-70% of attempts.

**How to tag task difficulty (for free)**:

Difficulty scores are already in the pipeline — the solvability filtering step ran Claude 4.6 Sonnet on each task multiple times. Those pass rates are the difficulty labels:

| Sonnet pass rate | Difficulty label |
|-----------------|-----------------|
| All attempts pass | Easy |
| ~75% pass | Easy-Medium |
| ~50% pass | Medium |
| ~25% pass | Medium-Hard |
| Only 1 attempt passes | Hard |

This data is already in the parquet files — `extra_info` column has per-task solution counts. No additional compute needed. Sonnet difficulty is more relevant than o3 anyway since we're training a model of comparable capability.

**What to try**:

1. **Simple version (immediate)**: Use existing baseline data — we know per-task pass/fail from the 4B and 3B 5-step runs. Bucket tasks into easy (4B solves >70%), medium (30-70%), hard (<30%). Start training on medium tasks, introduce hard tasks after 50 steps.

2. **DUMP version (principled)**: Track per-task advantage magnitude during training. Use UCB bandit to automatically up-sample tasks where the model is still improving and down-sample tasks where it has plateaued. No manual bucketing needed.

**Implementation**: Medium effort. Requires modifying the data sampler in `dataset.py` to support weighted sampling by difficulty bucket.

---

## Phase 7: Turn-Level Credit Assignment (Partial Rewards)

**Papers**:
- "Reinforcing Multi-Turn Reasoning in LLM Agents via Turn-Level Reward Design" (Wei et al., 2025, arXiv:2505.11821)
- "iStar: Agentic Reinforcement Learning" (Liu et al., ICLR 2026) — implicit step rewards for agentic RL

**Problem it solves**: Current setup gives binary 0/1 reward after the full episode. If the model passes 4 out of 5 subtests it still gets 0 — same as passing nothing. This is extremely sparse signal and forces GRPO to guess which turns were responsible for failure.

**What to try**: Give partial reward based on how many pytest subtests pass:

```
reward = num_tests_passed / total_tests
```

For example, a task with 5 assertions: passing 3/5 → reward=0.6. This is almost free to implement — Harbor already supports soft rewards via `reward.json`. The verifier just needs to write a float instead of 0/1.

**Implementation**: Low effort. Modify `test.sh` in each task to count passing assertions and write a float to `reward.json`. No changes to SkyRL or Harbor needed.

**Expected impact**: Very high. Denser reward signal means GRPO gets useful gradient even from partially-solved tasks. Directly addresses the sparse reward problem that caused both the 20260629 PPO run and 20260723 GRPO run to flatline.

---

## Prerequisites

Before starting Phase 1:
- [x] Confirm 9B model base eval avg_score on deduped 8192 tasks — done (58%, 20260808)
- [ ] Verify reward density on target dataset for 9B (check avg_pass_at_4 at step 1)
- [ ] Check trial logs for test leakage (cat /tests/ commands)
- [ ] Book p5en capacity block (4B)
- [ ] Book b300 capacity block (9B)
- [ ] Verify install_sky.sh works on p5en and b300 AMIs
