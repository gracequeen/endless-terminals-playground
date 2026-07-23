# Training Experiments

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

## 20260716 — Qwen3.5-4B GRPO (Harbor + terminus-2)

| Field | Value |
|-------|-------|
| **Experiment name** | TBD |
| **Task generation model** | Claude 4.6 Opus (8192 token context) |
| **Solution generation model** | Claude 4.6 Sonnet |
| **Training tasks** | 1882 (from harbor_tasks_8192 part 1, filtered by solvability) |
| **Val tasks** | 210 |
| **Algorithm** | GRPO |
| **Agent** | terminus-2 |
| **Environment** | Harbor + Docker |
| **Base model** | Qwen/Qwen3.5-4B |
| **Total steps** | 100 |
| **Checkpoint interval** | Every 50 steps |
| **Eval interval** | Every 20 steps |
| **Batch size** | 8 tasks × 4 samples = 32 rollouts/step |
| **GPUs** | 8× A100 40GB (p4d.24xlarge) |
| **Max turns per rollout** | 32 (Harbor terminus-2) |
| **Max seq len** | 8192 tokens |
| **gpu_memory_utilization** | 0.45 |

### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training script | `scripts/train_harbor_qwen3_5_4b_p4d.sh` |
| Training data | `s3://endless-terminals-training/prepared_data/train_4.5opus-8192-task_4.6sonnet-sol_combined.parquet` |

### Notes

- First 4B model experiment
- New dataset: harbor_4.6opus_tasks_8192 (8192 token context tasks, part 1)
- Dataset pass@1: 56.5% (2092/3310 tasks solvable) — much stronger signal than previous ~10%
- Branch: `tc/harbor-grpo-miniswe-9b`

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
- Increased gpu_memory_utilization to 0.55 to fit model on smaller A10G GPUs
- Cluster setup: Ray head on instance 1 (172.31.12.35), worker on instance 2 (172.31.9.61)
- Status: in progress
