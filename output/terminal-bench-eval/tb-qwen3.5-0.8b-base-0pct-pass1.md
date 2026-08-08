# Terminal-Bench Eval — Qwen3.5-0.8B Baseline

**Date:** 2026-08-07  
**Job:** `tb-base-qwen3-5-0-8b-v3`  
**Results dir:** `solution_tb/tb-base-qwen3-5-0-8b-v3/`  
**Solutions:** `solution_tb/tb-base-qwen3-5-0-8b-v3/<task-name>/result.json` → `agent_result.metadata.all_messages` (full conversation per trial)

## Summary

| Metric | Value |
|---|---|
| Model | `Qwen/Qwen3.5-0.8B` (base, no fine-tuning) |
| Dataset | `terminal-bench/terminal-bench@latest` (74 tasks) |
| Agent | `EndlessAgent` (echos-style, vLLM @ localhost:8000) |
| Duration | 42.5 min |
| Tasks attempted | 74 |
| Trials completed | 60 |
| Errors | 14 |
| **Pass@1** | **0.0%** (0 / 74) |

## Error Breakdown

| Exception | Count |
|---|---|
| `RewardFileNotFoundError` | 10 |
| `RuntimeError` | 3 |
| `ProcessLookupError` | 1 |

`RewardFileNotFoundError` means the verifier ran but produced no reward file — typically the agent's commands didn't produce verifiable output within the timeout. The 3 `RuntimeError` and 1 `ProcessLookupError` are likely GPU-heavy tasks (e.g. `jax-speedrun-gpu`, `fp8-rmsnorm-gemm`) where the Docker environment timed out building or running.

## Observations

- **0% pass rate is expected** for a 0.8B base (untrained) model on terminal-bench. These are expert-level terminal tasks (ML training, CUDA kernels, formal proofs, FreeCAD, etc.) requiring multi-step reasoning and domain knowledge well beyond this model size.
- The model ran 64 turns max per task and used the echos-style `<command>...</command>` / `<action>done</action>` format. The 0.8B base model does not reliably follow this structured output format.
- All 60 completed tasks scored `reward = 0.0` — no partial credit on any task.

## Infrastructure Notes

- **vLLM 0.26.0** installed into project venv (`.venv/`); required `LIBRARY_PATH` and `CUDA_HOME` pointing to `/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13` due to non-standard CUDA install.
- **Docker Compose v2** was not installed; installed to `~/.docker/cli-plugins/` (v2.24.6).
- Harbor's `DockerEnvironment.supports_gpus` patched to `True` in the venv; GPU tasks use a `docker-compose-gpu.yaml` overlay with `nvidia` device reservations.
- One-line fix to `scripts/run_terminal_bench.sh`: tmux window names now replace `.` with `-` to avoid pane selector ambiguity.

## Next Steps

- Run same eval after RL training to measure improvement (pass@1 > 0% = signal).
- Consider using `Qwen3.5-0.8B-Instruct` for baseline — the instruct variant follows structured output format more reliably and would give a fairer comparison point.
