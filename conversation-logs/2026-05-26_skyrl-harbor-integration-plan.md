# SkyRL + Harbor Integration Plan

**Date**: 2026-05-26
**Project**: endless-terminals-playground

## Question

How to wire up SkyRL PPO training using the HarborGenerator loop against the 100 local Docker-based tasks in `harbor_tasks/`, running on a single T4 GPU.

## Solution

Use SkyRL's `HarborGenerator` pattern (from `examples/train_integrations/harbor/`) verbatim, adapted for:
- Local Docker instead of Daytona
- Single T4 (15GB VRAM) instead of multi-GPU cluster
- `harbor_tasks/` directory instead of HuggingFace download

## Plan Steps

1. **Wait for flash-attn build → install skyrl-train + skyrl-gym**
   - `torch==2.11.0+cu130` already installed (matches system CUDA 13.0)
   - `MAX_JOBS=4 uv pip install flash-attn --no-build-isolation` running in background

2. **Copy SkyRL Harbor integration into `train/harbor/`**
   - `harbor_generator.py` — `HarborGenerator` + `HarborExp` (implements `GeneratorInterface`)
   - `dataset.py` — `HarborTaskDataset` (scans dirs for `instruction.md`)
   - `entrypoints/main_harbor.py` — Hydra training entrypoint

3. **Write `train/harbor/harbor_trial_config/t4.yaml`**
   - `environment.type: docker` (local Docker, not daytona)
   - `agent.max_turns: 16`, `timeout: 300`
   - T4 resource limits: `cpus: 1`, `memory_mb: 2048`

4. **Write `scripts/run_harbor_t4.sh`**
   - 1 GPU policy, 1 inference engine, `TP_SIZE=1`
   - `DATA_DIR=harbor_tasks/`
   - `n_samples_per_prompt=4`
   - `float16`, `enforce_eager=true`, `gpu_memory_utilization=0.5`
   - Model: `Qwen/Qwen3-1.7B` or `Llama-3.2-3B-Instruct`

5. **Smoke test** — 1 batch, confirm reward flows Harbor → SkyRL

## Key Architecture

```
harbor_tasks/
  task_000000_*/
    instruction.md        # HarborTaskDataset reads this
    task.toml
    environment/
      Dockerfile
    tests/
      test.sh             # writes reward to /logs/verifier/reward.txt
      test_final_state.py
```

```
HarborTaskDataset  →  HarborGenerator  →  Harbor Trial (Docker)
      ↓                     ↓                      ↓
  task paths          async generate()        agent loop
                           ↓                      ↓
                     tokenized output       reward from test.sh
                           ↓
                      PPO trainer
```

## Key Adaptation vs Upstream

| Upstream (CodeContests) | Ours (harbor_tasks) |
|------------------------|---------------------|
| `environment.type: daytona` | `environment.type: docker` |
| HuggingFace download | Local `harbor_tasks/` |
| 8 GPUs, Qwen3-8B | 1 T4, Qwen3-1.7B |
| `n_samples=8` | `n_samples=4` |
| `max_turns=32` | `max_turns=16` |

## Branch

All work on `grace-skyrl` branch (forked from `clean`).

## Key Takeaways

- SkyRL's Harbor integration only needs `GeneratorInterface.generate()` — trainer is untouched
- `HarborTaskDataset` just needs dirs with `instruction.md` — our tasks already have this
- T4 doesn't support bfloat16 or CUDA graphs → `float16` + `enforce_eager=true`
- `flash_attn: false` in trainer config (T4 is sm75, flash-attn needs sm80+)
- Rate limiting: `max_concurrency` should match Docker container capacity on the instance
