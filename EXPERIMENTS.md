# Training Experiments

## Baseline Comparison

2×2 across model size and dataset. All runs are base model behavior (no meaningful training — 5-step baseline only).

| Model | Dataset | avg_pass_at_4 step 1 | avg_pass_at_4 steps 1-5 | eval avg_score (pass@1) | Experiment |
|-------|---------|----------------------|--------------------------|--------------------------|------------|
| Qwen2.5-3B | Original 457 tasks | 0.0% | 15.0% (noisy) | 3.9% (51 tasks) | 20260731b |
| Qwen2.5-3B | Deduped 8192 tasks | 12.5% | 7.5% (noisy) | 6.0% (100 tasks) | 20260730 |
| Qwen3.5-4B | Original 457 tasks | 50.0% | 70.0% | 39.2% (51 tasks) | 20260731 |
| Qwen3.5-4B | Deduped 8192 tasks | 62.5% | 60.0% | 49.0% (100 tasks) | 20260723 |

**Key takeaways:**
- 4B vs 3B: ~10× higher eval avg_score on the same dataset — gap is model capability
- Original 457 vs deduped 8192: 4B eval avg_score is 39.2% on original 457 vs 49.0% on deduped 8192 — deduped 8192 tasks are actually easier for the 4B model despite being longer
- 3B avg_pass_at_4 is too noisy (batch=4, ~5% pass rate) to compare across datasets — use eval avg_score instead (3.9% vs 6.0%)

---

## Scripts Reference

### Single-node training
```bash
# 3B PPO direct Docker (single node)
bash scripts/train_qwen3b.sh

# 9B GRPO Harbor + terminus-2 (single node, p4d/p5)
bash scripts/train_harbor_qwen3_5_9b.sh

# 4B GRPO Harbor + terminus-2 (single node, p4d)
bash scripts/train_harbor_qwen3_5_4b_p4d.sh
```

### Multi-node distributed training (2x g5.48xlarge)
```bash
# 0. Install dependencies on a fresh instance (run once per instance)
bash scripts/install_sky.sh

# 1. Set up cluster (run once per session — installs deps, starts Ray, syncs PyTorch versions)
bash scripts/setup_cluster.sh

# 2. Launch training (run from Mac — SSHes into head node and starts training in tmux)
bash scripts/launch_training.sh

# 3. Watch logs (optional)
ssh -i ~/Desktop/distribution-training.pem ec2-user@<head_ip>
tmux attach -t training
```

### Data preparation
```bash
# Download tasks + solutions from S3, filter solvable tasks, produce combined parquet
bash scripts/prepare_data_s3.sh
```

### Key multi-node config (train_harbor_qwen3_5_4b_g5_2node.sh)
- `trainer.placement.colocate_all=false` — required for multi-node (colocate uses CUDA IPC which doesn't work across nodes)
- `generator.inference_engine.weight_sync_backend=broadcast` — uses NCCL broadcast instead of CUDA IPC
- `NCCL_SOCKET_IFNAME=ens5` — forces NCCL to use IPv4 interface on g5 instances
- PyTorch versions must match across nodes — `setup_cluster.sh` handles this automatically

---

## 20260629 — Qwen2.5-3B PPO

| Field | Value |
|-------|-------|
| **Experiment name** | 20260629_4.5opus-task_4.6sonnet-sol_457tasks_ppo_qwen2.5-3b_228steps |
| **Task generation model** | Claude 4.5 Opus |
| **Solution generation model** | Claude 4.6 Sonnet |
| **Training tasks** | 457 |
| **Val tasks** | 51 |
| **Agent** | Direct Docker (`train/sky_endless.py`) — stateless shell |
| **Algorithm** | PPO (GAE advantage estimator) |
| **Base model** | Qwen/Qwen2.5-3B-Instruct |
| **Epochs** | 2 |
| **Total steps** | 228 |
| **Batch size** | 4 tasks × 4 samples = 16 rollouts/step |
| **Max turns per rollout** | 8 |
| **Max prompt length** | 4096 tokens |
| **Learning rate** | 1e-6 |
| **Checkpoint interval** | Every 100 steps |
| **Eval interval** | Every 20 steps |

### Eval Metrics (Pass@1)

| Step | Pass@1 |
|------|--------|
| 0 (base model) | 7.8% |
| 10 | 3.9% |
| 20–200 | 5.9% |
| 220 | 3.9% |
| 228 (final) | 5.9% |

### Training Metrics (every 20 steps)

| Step | Mean Reward | Std Reward | Value Loss | Expl Variance | Entropy | Policy Loss |
|------|------------|------------|------------|----------------|---------|-------------|
| 20 | 0.0000 | 0.0000 | 0.0004 | -43862.8 | 0.1263 | -0.1618 |
| 40 | 0.0000 | 0.0000 | 0.0000 | -846.7 | 0.0907 | -0.1469 |
| 60 | 0.0000 | 0.0000 | 0.0000 | -1878.7 | 0.0922 | -0.0374 |
| 80 | 0.2500 | 0.4330 | 0.1242 | -479.0 | 0.1506 | 0.0476 |
| 100 | 0.0000 | 0.0000 | 0.0002 | -651.2 | 0.1307 | 0.1017 |
| 120 | 0.2500 | 0.4330 | 0.1266 | -514.5 | 0.1357 | 0.0669 |
| 140 | 0.2500 | 0.4330 | 0.1247 | -878.0 | 0.0650 | -0.3342 |
| 160 | 0.0000 | 0.0000 | 0.0000 | -243.6 | 0.1012 | 0.1904 |
| 180 | 0.0000 | 0.0000 | 0.0000 | -146.2 | 0.1237 | 0.0700 |
| 200 | 0.0000 | 0.0000 | 0.0009 | -208.2 | 0.1058 | 0.0312 |
| 220 | 0.0000 | 0.0000 | 0.0000 | -84.3 | 0.1053 | 0.3357 |
| 228 | 0.0000 | 0.0000 | 0.0000 | -100.2 | 0.1080 | 0.0041 |

### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training log (all steps) | `s3://endless-terminals-training/20260629_4.5opus-task_4.6sonnet-sol_457tasks_ppo_qwen2.5-3b_228steps/train_debug.log` |
| Eval results | `s3://endless-terminals-training/20260629_4.5opus-task_4.6sonnet-sol_457tasks_ppo_qwen2.5-3b_228steps/evals/` |
| Model checkpoint | `s3://endless-terminals-training/20260629_4.5opus-task_4.6sonnet-sol_457tasks_ppo_qwen2.5-3b_228steps/global_step_100/` |
| Training data | `s3://endless-terminals-training/prepared_data/` |

### Notes

- Reward signal is sparse — only ~10% of tasks solvable
- Explained variance very negative throughout (critic never learned well)
- Policy entropy stayed healthy (~0.1) — model kept exploring
- Best checkpoint is base model (step 0) at 7.8% — training did not improve beyond baseline
- Root cause: insufficient solvable tasks for strong RL signal

---

## 20260718 — Qwen3.5-4B GRPO on p4d: OOM Investigation

### Dataset Selection

- Source: s3://endless-terminals-training/data/harbor_4.6opus_tasks_8192_part1-2/
- Two parts available (~3310 tasks each), generated in parallel, identical quality
- Used part 1 only (harbor_tasks_8192/ + harbor_4.6opus_tasks_8192_4.6sonnet_solutions/)
- After solvability filtering via prepare_data_s3.sh: 1882 train / 210 val rows
- Dataset pass@1 (measured by Claude 4.6 Sonnet): 56.5% (2092/3310 tasks solvable)
- Key difference from previous datasets: tasks generated with 8192 token context, producing much longer trajectories (avg 3500+ tokens, max 10000+ tokens)

### OOM Attempts on p4d.24xlarge (8x A100 40GB)

All attempts failed with CUDA OOM during backward pass (policy training step).

| Attempt | train_batch_size | micro_train_batch_size_per_gpu | max_generate_length | max_seq_len | Result |
|---------|-----------------|-------------------------------|--------------------|-----------|----|
| 1 | 8 | 2 | 2048 | 8192 | OOM (batch_padded_seq_len: 10389) |
| 2 | 4 | 1 | 2048 | 8192 | OOM (batch_padded_seq_len: 8531) |
| 3 | 4 | 1 | 1024 | 10000 | OOM (tried to allocate 6.67 GiB, only 6.21 GiB free) |

Also attempted remove_microbatch_padding=true but requires flash_attn=true which is incompatible with our setup.

### Root Cause

The 8192-token context tasks produce trajectories of 8000-10000+ tokens (prompt + response). A100 40GB cannot hold the backward pass gradients for sequences this long, even at micro_batch_size=1.

### Resolution

Move 4B training to p5.48xlarge (8x H100 80GB) — double the GPU memory, no OOM with these sequence lengths.

### Observation: Zero Advantage

At step 1, reward/avg_pass_at_4=1.0 and avg_raw_advantages=0.0 — Qwen3.5-4B solved all tasks across all 4 samples, leaving no gradient signal for GRPO. Likely due to small batch (4 tasks) landing on easy tasks — needs more steps to confirm if systematic.

---

## 20260720 — Qwen3.5-4B GRPO on 2x g5.48xlarge (Distributed Training)

| Field | Value |
|-------|-------|
| **Experiment name** | `20260722_8192deduped-task_harbor-grpo_qwen3.5-4b_g5-2node_Xsteps` |
| **Task generation model** | Claude 4.6 Opus (8192 token context) |
| **Solution generation model** | Claude 4.6 Sonnet |
| **Training tasks** | 2781 (from 4929 deduplicated tasks, filtered by solvability) |
| **Val tasks** | 100 |
| **Dataset** | `harbor_tasks_8192_deduped` — 6682 → 4929 after dedup (threshold=0.85) |
| **Algorithm** | GRPO |
| **Agent** | terminus-2 |
| **Environment** | Harbor + Docker |
| **Base model** | Qwen/Qwen3.5-4B |
| **Total steps** | 100 (1 epoch) |
| **Checkpoint interval** | Every 20 steps |
| **Eval interval** | Every 20 steps |
| **Batch size** | 16 tasks × 4 samples = 64 rollouts/step |
| **Instances** | 2× g5.48xlarge |
| **GPUs** | 16× A10G 24GB total (8 per node) |
| **Max turns per rollout** | 8 |
| **Max seq len** | 8192 tokens |
| **gpu_memory_utilization** | 0.55 |
| **weight_sync_backend** | broadcast (NCCL, colocate_all=false) |

### Key fixes for multi-node

- Upgraded `nvidia-nccl-cu13` to 2.29.7 on both nodes (2.28.9 had `double free` crash)
- Set `CUDA_HOME` system-wide so FlashInfer JIT can find nvcc in Ray workers
- `VLLM_USE_FLASHINFER_SAMPLER=0` to avoid FlashInfer sampler JIT issues
- `colocate_all=false` + `weight_sync_backend=broadcast` — CUDA IPC doesn't work across nodes

### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training script | `scripts/train_harbor_qwen3_5_4b_g5_2node.sh` |
| Data prep script | `scripts/prepare_data_deduped.sh` |
| Checkpoints | `s3://endless-terminals-training/20260722_8192deduped-task_harbor-grpo_qwen3.5-4b_g5-2node_Xsteps/` |
| Training data | `s3://endless-terminals-training/prepared_data/train_8192_deduped_4929tasks.parquet` |

### Notes

- First distributed multi-node training run (2 instances)
- Ray cluster coordinates both nodes, FSDP shards model across all 16 GPUs
- A10G has less memory than A100 (24GB vs 40GB) but 2 nodes gives 16 GPUs total
- Cluster setup: Ray head on instance 1 (172.31.12.35), worker on instance 2 (172.31.9.61)
- Dataset: `harbor_tasks_8192_deduped` — 6682 → 4929 after dedup (threshold=0.85, 73.8% kept), 2781 solvable (56.4% pass rate)

### Result

**Abandoned due to persistent OOM on A10G 24GB GPUs.**

Training did briefly work — step 1 achieved `avg_pass_at_4: 0.1875` (18.75% pass rate), confirming the model can solve tasks and RL has a learning signal. However, steps with longer sequences consistently OOM during the ref model forward pass (`log_softmax` over vocabulary requires 8-14GB, exceeding available GPU memory).

### Issues encountered and resolved

1. **vLLM 0.21.0 worker extension conflict** — `start_weight_update`/`finish_weight_update` methods conflict with native vLLM methods. Fix: remove them from `NewInferenceWorkerWrap`, keep only `update_weights_chunk`.
2. **NCCL IPv6 routing** — NCCL defaulted to `fe80::` IPv6 which doesn't route between instances. Fix: `NCCL_SOCKET_IFNAME=ens5`, `NCCL_SOCKET_FAMILY=AF_INET`.
3. **NCCL version mismatch** — Instance 1 had NCCL 2.29.7, instance 2 had 2.28.9 (buggy `double free`). Fix: `pip install nvidia-nccl-cu13==2.29.7` on both.
4. **PyTorch version mismatch** — AMI versions differed. Fix: sync PyTorch in `setup_cluster.sh`.
5. **NCCLWeightTransferEngine conflict** — `colocate_all=true` forces CUDA IPC which doesn't work cross-node; new inference path's `NCCLWeightTransferEngine.trainer_init` conflicts. Fix: patch `broadcast_strategy.py` to use `init_custom_process_group` directly.
6. **FlashInfer JIT** — `CUDA_HOME` not set in Ray workers. Fix: set in `/etc/environment`.
7. **Docker network exhaustion** — 100+ networks accumulate, IP pool runs out. Fix: periodic `docker network prune -f`.
8. **Docker build cache filling disk** — 56GB cache from 2000+ builds. Fix: background `docker builder prune` every 30 min.
9. **Argument list too long** — 2781 task dirs passed as CLI args exceeds OS limit. Fix: pass JSON file path, patched `HarborTaskDataset` to load from JSON.

### Conclusion

A10G 24GB is too small for colocated RL training with a 4B model at 4096+ sequence lengths. Need ≥40GB per GPU. Moved to single-node p5.48xlarge (8× H100 80GB).

---

## 20260723 — Qwen3.5-4B GRPO on p5.48xlarge (Single Node)

| Field | Value |
|-------|-------|
| **Experiment name** | `20260723_8192deduped-task_harbor-grpo_qwen3.5-4b_p5_Xsteps` |
| **Task generation model** | Claude 4.6 Opus (8192 token context) |
| **Solution generation model** | Claude 4.6 Sonnet |
| **Training tasks** | 2781 (from 4929 deduplicated tasks, filtered by solvability) |
| **Val tasks** | 100 |
| **Dataset** | `harbor_tasks_8192_deduped` — 6682 → 4929 after dedup (threshold=0.85, 73.8% kept), 2781 solvable (56.4% pass rate) |
| **Algorithm** | GRPO |
| **Agent** | terminus-2 |
| **Environment** | Harbor + Docker |
| **Base model** | Qwen/Qwen3.5-4B |
| **Instance** | p5.48xlarge (8× H100 80GB) |
| **Batch size** | 4 tasks × 4 samples = 16 rollouts/step |
| **Max turns per rollout** | 8 |
| **Max generate length** | 1024 tokens |
| **Max seq len** | 4096 tokens (no truncation enforced by SkyRL) |
| **micro_forward_batch_size_per_gpu** | 1 |
| **micro_train_batch_size_per_gpu** | 1 |
| **gpu_memory_utilization** | 0.10 |
| **weight_sync_backend** | nccl (CUDA IPC on single node) |
| **colocate_all** | true |


### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training script | `scripts/train_harbor_qwen3_5_4b_p5.sh` |
| Checkpoints | `s3://endless-terminals-training/20260723_8192deduped-task_harbor-grpo_qwen3.5-4b_p5_Xsteps/` |
| Training data | `s3://endless-terminals-training/prepared_data/train_8192_deduped_4929tasks.parquet` |

### Notes

- Single node — no multi-node weight sync issues
- CUDA IPC weight sync works cleanly on single node
- Newer SkyRL version on p5 required fixing attribute name mismatch in `new_inference_worker_wrap.py` (`_skyrl_weight_update_active` → `_weight_update_active`)
- OOM resolved by reducing batch_size=4, gpu_memory_utilization=0.10, micro_batch=1, max_generate_length=1024

### Important: Two `max_turns` settings

There are **two separate** `max_turns` that must be set together:

1. **`generator.max_turns`** in the training script — controls SkyRL's step-wise trajectory collection (how many Harbor episodes per rollout)
2. **`default.yaml` → `agent.kwargs.max_turns`** — controls how many turns terminus-2 agent takes *within* a single episode

**The one that actually limits sequence length is `default.yaml`**. If `default.yaml` has `max_turns: 32` but the script has `generator.max_turns=8`, the agent still runs 32 turns internally producing 20k+ token sequences, causing OOM. Both must be set to the same value.

- Status: **abandoned** — model oscillates between recovery and collapse, never stabilizes

### Training Progress (avg pass_at_4 by block)

#### Early Training Stage 

| Step | avg_pass_at_4 | avg_raw_reward |
|------|---------------|----------------|
| 1 | 62.5% | 43.8% |
| 2 | 50.0% | 37.5% |
| 3 | 62.5% | 53.1% |
| 4 | 62.5% | 46.9% |
| 5 | 62.5% | 53.1% |
| 6 | 62.5% | 43.8% |
| 7 | 62.5% | 40.6% |
| 8 | 87.5% | 75.0% |
| 9 | 100% | 59.4% |

| Steps | Avg pass_at_4 | Non-zero batches | Notes |
|-------|---------------|------------------|-------|
| 61-80 | 3.7% | 3/20 | Post-512 damage, barely recovering |
| 81-100 | 5.0% | 4/20 | Still struggling |
| 101-120 | 15.0% | 7/20 | Starting to recover |
| 121-140 | 32.5% | 15/20 | Best period |
| 141-160 | 1.3% | 1/20 | Collapsed again |
| 161-180 | 20.0% | 11/20 | Partial recovery |
| 181-199 | 22.2% | 9/18 | Unstable, then collapsed to 0% |
| 201-243 | 0.0% | 0/43 | Fully collapsed, never recovered |

Overall avg training reward: 14.1% across steps 61-199, then 0% for steps 201-243. Total 181 steps ran.

### Eval Metrics (held-out validation tasks — model never trains on these)

Eval runs every 20 steps on 10 unseen tasks. `avg_score` = fraction of tasks solved.

| Step | avg_score |
|------|-----------|
| 20 | 2% |
| 40 | 2% |
| 60 | 54% |
| 80 | 1% |
| 100 | 0% |
| 120 | 30% |
| 200 | 0% |
| 220 | 0% |

### Why training failed to converge

**Root cause:** OOM forced us into settings too constrained for stable GRPO training, which led to an irrecoverable model collapse.

**Why the model couldn't recover once it started failing:**

Recovery requires the model to occasionally produce correct outputs (non-zero reward) so GRPO can reinforce them. But with our constrained settings:
- Only 4 tasks per batch → most batches are all-fail (0% reward) → zero gradient
- 6 turns → complex tasks can't be completed → fewer successes
- No KL penalty → nothing prevents the policy from drifting further into broken output patterns

The model entered a **death spiral**: bad outputs → 0 reward → no gradient → no improvement → bad outputs persist.

**Why we were forced into bad settings (the fundamental issue):**

Colocated mode on H100 80GB cannot handle the paper's settings (batch=16, turns=16, generate=2048) because of the vocabulary size × sequence length memory requirement during backward pass. Every config reduction (batch, turns, generate length) degraded training quality, making the death spiral easier to trigger and harder to escape.

| Setting | Paper | Ours | Impact |
|---------|-------|------|--------|
| train_batch_size | 16 | 4 | Less contrast for GRPO, high variance |
| max_turns | 16 | 6 | Model can't finish complex tasks |
| max_generate_length | 2048 | 1024 | Outputs may be truncated |
| micro_batch | 2 | 1 | Slower training |
| gpu_memory_utilization | 0.35+ | 0.10 | Less KV cache for inference |

### Root cause of OOM

The 4B model has a vocabulary of 151,665 tokens. During backward pass, `log_softmax` allocates `[sequence_length × vocab_size]`:

```
20,000 tokens × 151,665 vocab × 4 bytes = ~12GB for one operation
```

Plus gradients + activations + optimizer states already using 50-60GB → exceeds 80GB on long sequences. The issue isn't model size (4B is small) — it's **long sequences × large vocabulary** during backward pass.

### Conclusion

**H100 80GB in colocated mode cannot support the settings needed for effective GRPO training on long-sequence terminal tasks.** The paper's settings (batch=16, turns=16, generate=2048) require ~200GB per GPU during backward pass. We have 80GB.

To replicate the paper's results, might need either:
- **2× p5 nodes** — multi-node distributed (brings back weight sync issues)
- **Smaller vocabulary model** (e.g. LLaMA 32k vocab vs Qwen 151k) — 5× less memory for same sequence length

---

## Next-Step Experiments

### Goal: Avoid OOM by controlling trajectory length at the data level

The root cause of OOM is long multi-turn conversations (20k+ tokens) during backward pass. Instead of fighting memory limits with config reductions that degrade training quality, control the data so trajectories stay short.

### Experiment A: Filter out tasks that require long solutions

- Run the existing solution data and check which tasks had solutions > 8k tokens
- Remove those from training, keep only tasks solvable in ≤ 6 turns with short commands
- This preserves training quality (full batch size, full generate length) while staying within memory

### Experiment B: Cap observations in the task environment

- Truncate Docker command output to 500-1500 chars instead of letting it grow unbounded
- This keeps the conversation history short regardless of task complexity
- Downside: model loses information from long outputs (e.g. log files, error traces)
- Upside: guaranteed max sequence length regardless of task type

### Experiment C: Generate tasks that are short but hard

- Tasks that require few turns (short trajectory, no OOM) but the model still fails often
- Examples: tricky edge cases, precise configuration, exact formatting requirements
- Target: solvable in 4-6 commands but with low base model pass rate (<30%)
- This gives GRPO the contrast it needs (mix of pass/fail) while staying within memory

### Goal: Reduce base model pass rate to get better GRPO training signal

The 4B model has a 49-70% base pass rate — too high for effective GRPO training. When most tasks are already solved, std_reward is low and GRPO has little to learn from. We need tasks where the model fails ~50-70% of the time so each batch has a mix of pass and fail.

### Experiment D: Check and fix test leakage

- terminus-2 runs inside the same Docker container where `/tests/test_final_state.py` is mounted
- A smart model can read the test file and craft a solution to pass assertions without truly solving the task
- **Step 1**: Verify by inspecting trial solution logs — look for `cat /tests/` commands early in trajectories
- **Step 2**: If confirmed, fix by separating the agent and verifier environments:
  - Currently Harbor builds one Docker container and both the agent and verifier run inside it with `/tests` always present
  - The fix is to have the agent run in a container where `/tests` is not mounted, then run the verifier separately after the agent finishes
  - This requires modifying Harbor's Docker container lifecycle — either patch Harbor source to conditionally mount `/tests` only at verification time, or run a two-phase setup: agent container (no `/tests`) → commit container state → verifier container (same filesystem snapshot + `/tests` mounted)
  - An easier workaround: restructure each task's Dockerfile so tests are stored in a non-obvious path inside the image (e.g. baked into a binary or stored outside `/tests`) and only made available to `test.sh` via an environment variable the agent doesn't know about — but a sufficiently smart agent could still find them with `find /`
  - The only truly reliable fix is the two-phase container approach where `/tests` is never on the filesystem during agent execution


---

## 20260731 — Qwen3.5-4B GRPO Baseline on Original 457-Task Dataset

| Field | Value |
|-------|-------|
| **Experiment name** | `20260731_4.5opus-task_harbor-grpo_qwen3.5-4b_p5_orig457_5steps` |
| **Task generation model** | Claude 4.5 Opus |
| **Solution generation model** | Claude 4.6 Sonnet |
| **Training tasks** | 457 |
| **Val tasks** | 51 |
| **Dataset** | Same as 20260629 Qwen2.5-3B PPO run |
| **Algorithm** | GRPO |
| **Agent** | terminus-2 |
| **Environment** | Harbor + Docker |
| **Base model** | Qwen/Qwen3.5-4B |
| **Instance** | p5.48xlarge (8× H100 80GB) |
| **Total steps** | 5 (baseline measurement only) |
| **Batch size** | 4 tasks × 4 samples = 16 rollouts/step |
| **Max turns per rollout** | 6 |
| **Max generate length** | 1024 tokens |
| **Max seq len** | 4096 tokens |
| **gpu_memory_utilization** | 0.10 |
| **colocate_all** | true |
| **Script** | `scripts/train_harbor_qwen3_5_4b_orig457_p5.sh` |

### Purpose

Measure Qwen3.5-4B baseline pass rate on the original 457-task dataset (same data as 20260629 Qwen2.5-3B PPO). Compare: 4B vs 3B on the same tasks, and original 457-task dataset vs deduped 8192-task dataset.

### Training Metrics

| Step | avg_pass_at_4 | avg_raw_reward | std_reward | Policy Loss | Policy KL | Grad Norm | Entropy | Response Len | Tokens/s/GPU |
|------|---------------|----------------|------------|-------------|-----------|-----------|---------|--------------|--------------|
| 1 | 50.0% | 37.5% | 0.4841 | -0.0335 | 0.2371 | 2.1424 | 0.2253 | 1351 | 442 |
| 2 | 75.0% | 43.8% | 0.4961 | 0.0067 | 0.1976 | 2.7708 | 0.2028 | 1322 | 2455 |
| 3 | 75.0% | 75.0% | 0.4330 | 0.0000 | 0.3000 | 0.0273 | 0.2856 | 1121 | 1316 |
| 4 | 75.0% | 43.8% | 0.4961 | 0.0398 | 0.1943 | 2.9431 | 0.1857 | 3230 | 1329 |
| 5 | 75.0% | 50.0% | 0.5000 | -0.0153 | 0.2453 | 1.9940 | 0.2266 | 5135 | 2230 |


### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training log | `s3://endless-terminals-training/20260731_4.5opus-task_harbor-grpo_qwen3.5-4b_p5_orig457_5steps/train_debug.log` |
| Checkpoint | `~/xin/checkpoints_harbor_qwen3_5_4b_orig457/global_step_5/` (local only, not uploaded) |

### Conclusion

Qwen3.5-4B avg_pass_at_4 = **75%** on the original 457-task dataset vs **12.5%** for Qwen2.5-3B on the same data — 6× improvement from model capability alone. Also higher than the 4B's 62.5% on the deduped 8192-task dataset, confirming the original 457 tasks are easier. Entropy is notably higher (~0.22) than the deduped dataset run (~0.10), suggesting the model has more variance on these tasks.

---

## 20260730 — Qwen2.5-3B GRPO Baseline on Deduped 8192 Dataset

| Field | Value |
|-------|-------|
| **Experiment name** | `20260730_8192deduped-task_harbor-grpo_qwen2.5-3b_p5_baseline` |
| **Task generation model** | Claude 4.6 Opus (8192 token context) |
| **Solution generation model** | Claude 4.6 Sonnet |
| **Training tasks** | 2781 (from 4929 deduplicated tasks, filtered by solvability) |
| **Val tasks** | 100 |
| **Dataset** | `harbor_tasks_8192_deduped` — same as 20260723 Qwen3.5-4B run |
| **Algorithm** | GRPO |
| **Agent** | terminus-2 |
| **Environment** | Harbor + Docker |
| **Base model** | Qwen/Qwen2.5-3B-Instruct |
| **Instance** | p5.48xlarge (8× H100 80GB) |
| **Total steps** | 5 (baseline measurement only) |
| **Batch size** | 8 tasks × 4 samples = 32 rollouts/step |
| **Max turns per rollout** | 6 |
| **Max generate length** | 1024 tokens |
| **Max seq len** | 4096 tokens |
| **micro_forward_batch_size_per_gpu** | 1 |
| **micro_train_batch_size_per_gpu** | 1 |
| **gpu_memory_utilization** | 0.10 |
| **colocate_all** | true |
| **Script** | `scripts/eval_qwen2_5_3b_baseline_p5.sh` |

### Purpose

Compare Qwen2.5-3B vs Qwen3.5-4B baseline pass rate on the same deduped 8192 dataset. The 4B model achieved 62.5% avg_pass_at_4 at step 1 — this run determines whether that was due to model capability or dataset difficulty.

### Training Metrics

| Step | avg_pass_at_4 | avg_raw_reward | std_reward | Policy Loss | Policy KL | Grad Norm | Entropy | Response Len | Tokens/s/GPU |
|------|---------------|----------------|------------|-------------|-----------|-----------|---------|--------------|--------------|
| 1 | 12.5% | 3.1% | 0.1740 | 0.0356 | 0.1013 | 0.6792 | 0.1089 | 3770 | 1427 |
| 2 | 12.5% | 3.1% | 0.1740 | 0.0118 | 0.1135 | 0.8531 | 0.1181 | 3030 | 2138 |
| 3 | 12.5% | 9.4% | 0.2915 | 0.0015 | 0.1871 | 0.3430 | 0.1750 | 4399 | 2296 |
| 4 | 0.0% | 0.0% | 0.0000 | 0.0000 | 0.1883 | 0.0215 | 0.1838 | 6870 | 2154 |
| 5 | 0.0% | 0.0% | 0.0000 | 0.0000 | 0.1344 | 0.0146 | 0.1351 | 6342 | 1616 |

### Eval Metrics (run once after training, on 100 held-out tasks)

| Metric | Value |
|--------|-------|
| avg_score (100 tasks) | 6.0% |
| Per-task scores | All 0.0 except ~6 tasks |

### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training log | `s3://endless-terminals-training/20260730_8192deduped-task_harbor-grpo_qwen2.5-3b_p5_baseline/train_debug.log` |
| Trials (step 5) | `s3://endless-terminals-training/20260730_8192deduped-task_harbor-grpo_qwen2.5-3b_p5_baseline/trials/` |

### Conclusion

Qwen2.5-3B avg_pass_at_4 ≈ **12.5%** (steps 1–3), dropping to **0%** at steps 4–5, vs Qwen3.5-4B's consistent **62.5%**. The ~5× gap confirms the difference is **model capability**, not dataset difficulty.

---

## 20260731b — Qwen2.5-3B GRPO Baseline on Original 457-Task Dataset

| Field | Value |
|-------|-------|
| **Experiment name** | `20260731_4.5opus-task_harbor-grpo_qwen2.5-3b_p5_orig457_5steps` |
| **Task generation model** | Claude 4.5 Opus |
| **Solution generation model** | Claude 4.6 Sonnet |
| **Training tasks** | 457 |
| **Val tasks** | 51 |
| **Dataset** | Same as 20260629 and 20260731 |
| **Algorithm** | GRPO |
| **Agent** | terminus-2 |
| **Base model** | Qwen/Qwen2.5-3B-Instruct |
| **Instance** | p5.48xlarge (8× H100 80GB) |
| **Total steps** | 5 |
| **Batch size** | 4 tasks × 4 samples = 16 rollouts/step |
| **Max turns** | 6 |
| **Max generate length** | 1024 tokens |
| **Script** | `scripts/train_harbor_qwen2_5_3b_orig457_p5.sh` |

### Training Metrics

| Step | avg_pass_at_4 | avg_raw_reward | std_reward | Policy Loss | Policy KL | Grad Norm | Entropy | Response Len | Tokens/s/GPU |
|------|---------------|----------------|------------|-------------|-----------|-----------|---------|--------------|--------------|
| 1 | 0.0% | 0.0% | 0.0000 | 0.0000 | 0.1928 | 0.0193 | 0.1824 | 5642 | 1472 |
| 2 | 0.0% | 0.0% | 0.0000 | 0.0000 | 0.1579 | 0.0177 | 0.1513 | 4306 | 2549 |
| 3 | 50.0% | 43.8% | 0.4961 | -0.0322 | 0.2129 | 0.8498 | 0.2085 | 4148 | 2527 |
| 4 | 0.0% | 0.0% | 0.0000 | 0.0000 | 0.1805 | 0.0203 | 0.1748 | 5711 | 2590 |
| 5 | 25.0% | 18.8% | 0.3903 | -0.0111 | 0.1621 | 0.6845 | 0.1687 | 5335 | 1969 |

### Eval Metrics (51 held-out tasks)

| Metric | Value |
|--------|-------|
| avg_score (51 tasks) | 3.9% |

### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training log | `s3://endless-terminals-training/20260731_4.5opus-task_harbor-grpo_qwen2.5-3b_p5_orig457_5steps/train_debug.log` |

### Conclusion

Qwen2.5-3B avg_pass_at_4 is highly variable (0–50%) due to small batch size (4 tasks) — with only ~10% base pass rate, most batches are all-fail. eval avg_score = **3.9%** vs 4B's **39.2%** on the same tasks, confirming the 10× capability gap. Response length stays high (4000–5700 tokens) with zero reward, meaning the model generates long outputs without solving tasks.


## Key Constraints

**Harbor requires GRPO.** PPO is incompatible with Harbor's step-wise trajectories.

**Harbor + GRPO is the better setup** because terminus-2 runs a real persistent shell (state carries across commands), which is more realistic than Direct Docker's stateless `bash -c`. GRPO also uses less memory since there's no critic. The tradeoff: GRPO needs reward variance within each batch — if all 4 samples pass or all fail, gradient is zero. Batch size must be large enough to consistently get mixed results.

---
