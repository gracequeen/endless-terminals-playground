# Training Experiments

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
| **Training tasks** | TBD (from harbor_tasks_8192 part 1, ~3.3k total, filtered by solvability) |
| **Val tasks** | TBD |
| **Algorithm** | GRPO |
| **Agent** | terminus-2 |
| **Environment** | Harbor + Docker |
| **Base model** | Qwen/Qwen3.5-4B |
| **Total steps** | 150 |
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
- Branch: `tc/harbor-grpo-miniswe-9b`
