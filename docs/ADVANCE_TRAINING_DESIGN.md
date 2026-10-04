# Training Design

> Method and future-phase design for the large-instance experiments. Motivation, instances, models, datasets, and the Phase 1/2 run logs live in [DESIGN_LARGE_INSTANCE.md](DESIGN_LARGE_INSTANCE.md).

## 7. Phase 3: Hyperparameter Tuning (Ablation)

**Goal**: Identify which settings have the most impact on training stability and reward signal. Run a controlled ablation — one baseline plus three tests, each changing exactly one group of parameters. This isolates cause from effect.

**Duration**: 30 steps per test. Long enough to catch collapse (policy_entropy drop and grad_norm spike are usually visible by step 20-30) and see an early reward trend.

### 7.1. Baseline (same for both 4B and 9B)

| Setting | Value |
|---------|-------|
| train_batch_size | 8 |
| n_samples_per_prompt | 4 |
| max_turns | 8 |
| max_generate_length | 1024 |
| max_seq_len | 4096 |

---

### 7.2. Test 1 — More tasks per step

Only `train_batch_size` changes. Tests whether more tasks per step gives GRPO enough reward variance.

| Setting | Baseline | Test 1 |
|---------|----------|--------|
| train_batch_size | 8 | **16** |
| n_samples_per_prompt | 4 | 4 |
| max_turns | 8 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 4096 |

---

### 7.3. Test 2 — Longer episodes

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

### 7.4. Test 3 — More samples per task

Only `n_samples_per_prompt` changes. Tests whether more within-task contrast improves GRPO gradient quality.

| Setting | Baseline | Test 3 |
|---------|----------|--------|
| train_batch_size | 8 | 8 |
| n_samples_per_prompt | 4 | **8** |
| max_turns | 8 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 4096 |

---

### 7.5. Metrics

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

### 7.6. Decision Rule

At step 30 for each test:
1. If `std_reward` is near 0 throughout → stop early, this config provides no GRPO signal
2. If `policy_entropy` is dropping sharply or `grad_norm` spikes → stop early, collapse in progress
3. If both look healthy → compare `avg_pass@2` trend; take the config with the clearest upward trend into Phase 2

If one test looks promising but inconclusive at step 30, extend that test to 50 steps. Do not extend all tests.

---

## 8. Key Risks

1. **9B near-ceiling on deduped dataset** — avg_pass_at_4 = 95% means std_reward ≈ 0, no GRPO signal. Mitigate: filter to harder tasks or implement partial rewards (Phase 7) before training.
2. **9B sparse reward on harder tasks** — measured pass@8 = 6.2% on the harder task set. With batch=16, expect only ~1 solvable task/step. Mitigate: filter training set to tasks with ≥1 pass in 8 attempts.
3. **Test leakage** — model reads `/tests/test_final_state.py` to game verifier. Check trial logs before full run (Experiment D from EXPERIMENTS.md).
4. **Disk space** — each 9B checkpoint is ~40 GB, 4B is ~8 GB. Use `max_ckpts_to_keep=1` and S3 uploader.

---

## 9. Phase 4: GRPO vs DPPO Comparison

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

## 10. Phase 5: DAPO instead of Vanilla GRPO

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

## 11. Phase 6: Curriculum Learning (Easy → Hard)

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

## 12. Phase 7: Turn-Level Credit Assignment (Partial Rewards)

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

## 13. Prerequisites

Before starting Phase 1:
- [x] Confirm 9B model base eval avg_score on deduped 8192 tasks — done (58%, 20260808)
- [ ] Verify reward density on target dataset for 9B (check avg_pass_at_4 at step 1)
- [ ] Check trial logs for test leakage (cat /tests/ commands)
- [ ] Book p5en capacity block (4B)
- [ ] Book b300 capacity block (9B)
- [ ] Verify install_sky.sh works on p5en and b300 AMIs
