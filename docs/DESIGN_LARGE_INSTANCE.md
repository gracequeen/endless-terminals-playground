# Design: Large Instance Experiments (p5e / p5en / b6i)

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

## Target Instances

| Instance | GPU | GPU Memory |
|----------|-----|-----------|
| p5e.48xlarge | 8× H100e 80GB | 640 GB total |
| p5en.48xlarge | 8× H200 141GB | 1128 GB total |
| b6i.48xlarge | 8× B200 192GB | 1536 GB total |

**Recommended: p5en.48xlarge** — 141 GB per GPU vs 80 GB on current p5. This allows paper-equivalent settings without OOM.

---

## Model: Qwen3.5-9B

Switch from 4B to 9B for two reasons:
1. **Higher base capability** — 9B model solves more tasks, giving GRPO better reward signal
2. **Better generalization** — larger models tend to learn more robust terminal skills

The 4B model already achieved 49% eval avg_score as a base model. A 9B model should be significantly higher, but still not so high that all tasks are trivially solved (we need ~30-70% pass rate for GRPO contrast).

**Model path**: `Qwen/Qwen3.5-9B` (or instruct variant)

---

## Proposed Settings on p5en (H200 141GB)

With 141 GB per GPU, we can run close to paper settings:

| Setting | Previous p5 (H100 80GB) | Proposed p5en (H200 141GB) |
|---------|------------------------|---------------------------|
| train_batch_size | 4 | 16 |
| max_turns | 6 | 16 |
| max_generate_length | 1024 | 2048 |
| max_seq_len | 4096 | 8192 |
| gpu_memory_utilization | 0.10 | 0.40 |
| micro_train_batch_size_per_gpu | 1 | 2 |

batch_size=16 means 64 rollouts per step (16 tasks × 4 samples), giving GRPO enough reward variance to learn stably.

---

## Experiment Plan

### Phase 1: Dry Run (~50 steps, ~100 tasks)

**Goal**: Verify the setup is stable before committing to a full run.

- Use a small subset of ~100 tasks from the deduped 8192 dataset
- Run 50 steps with proposed settings
- Check: no OOM, no collapse, reward stays non-zero, entropy stays healthy
- Metrics to watch: avg_pass_at_4, std_reward, policy_entropy, grad_norm

If std_reward is consistently near 0 (all tasks pass or all fail), adjust task selection or reduce batch size before proceeding.

### Phase 2: Full Training (200-300 steps)

**Goal**: Train a model that actually improves beyond baseline.

- Use full deduped 8192 dataset (2781 training tasks, 100 val tasks)
- Run 200-300 steps with checkpointing every 20 steps
- Save eval avg_score every 20 steps on 100 held-out tasks
- Upload checkpoints to S3 after each step, delete old ones to save disk

Success criterion: eval avg_score at step 200 > base model eval avg_score (49% for 4B; target >40% for 9B if base is lower, or clear upward trend if base is already high).

### Phase 3: Hyperparameter Tuning

**Goal**: Systematically find the settings that maximize training signal and stability without OOM. Run each config for 20-30 steps and compare reward stability before committing to a full run.

| Parameter | Current p5 | Conservative | Recommended | Aggressive | Notes |
|-----------|-----------|--------------|-------------|------------|-------|
| `max_turns` | 6 | 8 | 16 | 24 | Set in both `default.yaml` AND `generator.max_turns` |
| `train_batch_size` | 4 | 8 | 16 | 32 | Bigger = less chance of all-fail batch |
| `n_samples_per_prompt` | 4 | 4 | 8 | 16 | More = better within-task GRPO contrast |
| `max_generate_length` | 1024 | 1024 | 2048 | 4096 | Never use 512 — caused collapse in 20260723 |
| `max_seq_len` | 4096 | 4096 | 8192 | 16384 | Watch `policy/response_length` in log |
| `update_epochs_per_batch` | 1 | 1 | 2 | 4 | More = faster learning, higher overfit risk |
| `kl_coef` | 0.0 | 0.001 | 0.01 | 0.1 | Set to 0 if using DAPO (Phase 5) |
| `gpu_memory_utilization` | 0.10 | 0.30 | 0.40 | 0.55 | Higher = more KV cache for inference |
| `micro_train_batch_size_per_gpu` | 1 | 1 | 2 | 4 | Increase only if no OOM |
| `micro_forward_batch_size_per_gpu` | 1 | 1 | 2 | 4 | Increase only if no OOM |

**Recommended starting config for p5en dry run**: use the Recommended column values above. Start conservatively on max_turns and increase after confirming no OOM.

---

## Key Risks

1. **Base model pass rate too high** — if 9B solves >80% of tasks, GRPO has no contrast. Mitigate by filtering to harder tasks (Experiment E from EXPERIMENTS.md).
2. **Test leakage** — model reads `/tests/test_final_state.py` to game verifier. Check trial logs before full run (Experiment D from EXPERIMENTS.md).
3. **Disk space** — each 9B checkpoint is ~40GB. Use `max_ckpts_to_keep=1` and S3 uploader.

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
- [ ] Confirm 9B model base eval avg_score on deduped 8192 tasks (5-step baseline)
- [ ] Check trial logs for test leakage (cat /tests/ commands)
- [ ] Book p5en capacity block
- [ ] Verify install_sky.sh works on p5en AMI
