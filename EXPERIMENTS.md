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

## 20260702 — Qwen3.5-9B GRPO (Harbor + mini-swe-agent)

| Field | Value |
|-------|-------|
| **Experiment name** | 20260702_4.5opus-4.6opus-task_harbor-miniswe_grpo_qwen3.5-9b_Xsteps |
| **Task generation model** | Claude 4.5 Opus + Claude 4.6 Opus (herodoc-fixed) |
| **Solution generation model** | Claude 4.6 Sonnet (used to filter solvable tasks via `prepare_data_s3.sh`) |
| **Training tasks** | ~6,100 (harbor_tasks_claude4.5_opus batches 1-3 + harbor_4.6opus_tasks_herodoc_fixed_3k) |
| **Val tasks** | ~1,000 (harbor_tasks_claude4.5_opus batch 4) |
| **Algorithm** | GRPO (required for Harbor step-wise training) |
| **Agent** | mini-swe-agent |
| **Environment** | Harbor + Docker |
| **Base model** | Qwen/Qwen3.5-9B |
| **Max steps** | 50 |
| **Batch size** | 4 tasks × 4 samples = 16 rollouts/step |
| **Max turns per rollout** | 8 |
| **Max seq len** | 8192 tokens |

### Key Differences from 3B Experiment

- Uses **Harbor framework** instead of direct Docker
- Uses **mini-swe-agent** — better for small models
- Uses **GRPO** instead of PPO — no critic, required for step-wise training
- Larger model (9B vs 3B)
- Combined data from two task sources

### S3 Artifacts

| Artifact | Location |
|----------|----------|
| Training log | `s3://endless-terminals-training/20260702_4.5opus-4.6opus-task_harbor-miniswe_grpo_qwen3.5-9b_Xsteps/train_debug.log` |
| Eval results | `s3://endless-terminals-training/20260702_4.5opus-4.6opus-task_harbor-miniswe_grpo_qwen3.5-9b_Xsteps/evals/` |
| Model checkpoints | `s3://endless-terminals-training/20260702_4.5opus-4.6opus-task_harbor-miniswe_grpo_qwen3.5-9b_Xsteps/global_step_*/` |
| Tasks on disk (4.5opus) | `/home/ec2-user/xin/harbor_tasks_4.5opus/` |
| Tasks on disk (herodoc 3k) | `/home/ec2-user/xin/harbor_tasks_herodoc_3k/` |

### Notes

- `mini-swe-agent` installed via `pip install harbor --upgrade` (added to `install_sky.sh`)
- Agent automatically patched via `scripts/_apply_patches.py`
- Training script: `scripts/train_harbor_qwen3_5_9b.sh`
- Branch: `tc/harbor-grpo-miniswe-9b`
