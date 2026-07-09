# Endless Terminals — Project Guide

## What is this project?

Endless Terminals trains an AI model to use the Linux terminal. The goal is a model that can solve real sysadmin tasks like fixing broken configs, setting up services, and running backups — entirely through terminal commands.

---

## The 3-Step Pipeline

### Step 1: Create Tasks

Claude generates thousands of realistic Linux terminal challenges. Each task includes:
- A task description ("As a sysadmin, you need to...")
- A Dockerfile that sets up the starting environment
- A pytest test that automatically checks if the task was completed correctly

We have ~10,000 tasks stored in S3 at `s3://endless-terminals-training/data/`.

### Step 2: Generate Answers (Solutions)

Claude 4.6 Sonnet attempts to solve each task by issuing commands one at a time inside a Docker container. When it finishes, the pytest test runs. Pass = solved (~10% pass rate).

Solutions are stored in S3 at `s3://endless-terminals-training/data/harbor_4.5opus_tasks_4.6sonnet_solutions/`.

> **Important:** Pre-generated solutions are only used to **filter which tasks to include** in training — tasks where at least one solution succeeded are kept, the rest are discarded. The actual training always runs the model **live** inside Docker containers and gets rewards from the verifier. The solution trajectories are NOT replayed during training.

### Step 3: Train a Model

We take the solvable tasks and train using RL:
1. Model generates terminal commands for a task
2. Commands run inside a Docker container
3. Verifier checks if task is solved → reward 1 (pass) or 0 (fail)
4. Model updates its weights based on the reward

---

## How to Run Training

```bash
# 1. Set up the environment (~20 min)
cd /home/ec2-user/xin/endless-terminals-playground
bash scripts/install_sky.sh

# 2. Prepare training data from S3 (run once, produces combined parquet)
bash scripts/prepare_data_s3.sh

# 3. Run training (inside tmux)
tmux new -s train
bash scripts/train_harbor_qwen3_5_9b.sh   # 9B Harbor GRPO
# OR
bash scripts/train_qwen3b.sh               # 3B direct Docker PPO
```

---

## Two Training Approaches

### Approach 1: Direct Docker (3B PPO)
- Uses `train/sky_endless.py` + `train/main_endless.py`
- Each command runs in a fresh `bash -c` — no persistent shell state
- Pre-generated solutions used only to filter solvable tasks (via `prepare_data_s3.sh`)
- Model runs live in Docker, reward from verifier
- Script: `scripts/train_qwen3b.sh`

### Approach 2: Harbor + mini-swe-agent (9B GRPO)
- Uses `SkyRL/examples/train_integrations/harbor/`
- Harbor manages Docker containers with `mini-swe-agent`
- Pre-generated solutions used only to filter solvable tasks (via `prepare_data_s3.sh`)
- Model runs live in Harbor/Docker, reward from Harbor verifier
- Script: `scripts/train_harbor_qwen3_5_9b.sh`
- Agent config: `SkyRL/examples/train_integrations/harbor/harbor_trial_config/default.yaml`

> **Note:** Both approaches run the model live — neither replays pre-generated solution trajectories. Solutions only determine which tasks to include in training.

---

## S3 Data Layout

```
s3://endless-terminals-training/
├── data/
│   ├── harbor_tasks_claude4.5_opus/              # Task definitions (~10k tasks)
│   ├── harbor_4.5opus_tasks_4.6sonnet_solutions/ # Solutions from Claude 4.6 Sonnet
│   ├── harbor_4.6opus_tasks_herodoc_fixed_3k/    # 1k herodoc-fixed tasks
│   ├── harbor_4.6opus_tasks_herodoc_fixed_3k_solutions/ # Solutions for herodoc tasks
│   └── prepared_data/                            # Combined parquet files
├── 20260629_4.5opus-task_4.6sonnet-sol_457tasks_ppo_qwen2.5-3b_228steps/
└── 20260702_4.5opus-task_harbor-miniswe_grpo_qwen3.5-9b_Xsteps/
```

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/install_sky.sh` | Set up training environment on new instance |
| `scripts/prepare_data_s3.sh` | Download tasks+solutions, generate combined parquet |
| `scripts/train_qwen3b.sh` | PPO training for Qwen2.5-3B (direct Docker) |
| `scripts/train_harbor_qwen3_5_9b.sh` | GRPO training for Qwen3.5-9B (Harbor + mini-swe-agent) |
| `scripts/train_qwen3_5_9b.sh` | PPO training for Qwen3.5-9B (direct Docker) |
| `scripts/_apply_patches.py` | Fix SkyRL compatibility issues + set mini-swe-agent |
| `train/sky_endless.py` | Connects RL trainer to Docker containers (direct approach) |
| `train/prepare_endless.py` | Convert task+solution data to parquet |
| `train/main_endless.py` | Training entry point (direct Docker) |
| `SkyRL/examples/train_integrations/harbor/entrypoints/main_harbor.py` | Training entry point (Harbor) |
| `SkyRL/examples/train_integrations/harbor/harbor_trial_config/default.yaml` | Harbor agent config |

---

## Known Issues & Lessons Learned

1. **Sparse reward signal** — Only ~10% of tasks are solvable. More data with higher pass rate would improve training.
2. **Disk space** — Each checkpoint is ~20GB. Use `max_ckpts_to_keep=1` and S3 uploader.
3. **Docker heredoc syntax** — Add `# syntax=docker/dockerfile:1` to all Dockerfiles.
4. **Instance IP changes** — Update `~/.ssh/config` with the new IP on restart.
5. **mini-swe-agent setup (TODO)** — `mini-swe-agent` runs as a CLI tool inside the Docker container and needs to call an external LLM API. To use it with local vLLM you need:
   - `OPENAI_API_KEY=nokey` (any dummy value)
   - `OPENAI_BASE_URL=http://<host_ip>:<vllm_port>/v1` pointing to your vLLM server
   - `cost_limit` set to a non-zero value (e.g. `"999"`)
   - Docker container must be able to reach the host IP (add host IP to `extra_allowed_hosts` in `default.yaml`)
   - These are set in `default.yaml` under `agent.kwargs`
   
   **Current status:** Using `terminus-2` which works reliably with local vLLM. Mini-swe-agent can be revisited after training completes.
   
   **Reference:** https://www.harborframework.com/docs/agents#existing-agents
6. **Harbor requires GRPO** — Harbor step-wise training is incompatible with GAE (PPO). Use GRPO.
7. **Docker Compose v2** — Harbor requires `docker compose` (v2). Install: `sudo mkdir -p /usr/local/lib/docker/cli-plugins && sudo curl -SL https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose && sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose`
