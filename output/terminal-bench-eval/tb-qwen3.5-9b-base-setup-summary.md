# Terminal-Bench Eval — Qwen3.5-9B (base) — Setup & Run Summary

**Date:** 2026-09-03
**Branch:** `benchmark-tb-qwen` (off `update-eval`)
**Job:** `tb-base-qwen3.5-9b` → results in `solution_tb/tb-base-qwen3.5-9b/`
**Status at write time:** eval running (vLLM up, 5 task containers active, agent issuing requests, 0 connection errors).

## Environment

`.venv` (Python 3.13) via `uv sync --extra harbor` + `uv pip install vllm ninja`:

| Component | Version |
|---|---|
| harbor | 0.3.0 |
| terminal-bench | 0.2.18 |
| transformers | 5.5.4 |
| vLLM / torch | 0.28.0 / 2.13.0+cu130 |
| docker compose | v2.27.1 |
| Hardware | 4× A10G (23 GB, SM 8.6), driver CUDA 13.2 |

Did **not** run the full `install_sky.sh` SkyRL build — Harbor eval client + local vLLM only.

## Model server

Qwen3.5-9B served on `localhost:8000` (TP=2 on GPUs 0,1), confirmed answering chat completions. It is a hybrid mamba+attention model (`Qwen3_5ForConditionalGeneration`) and a thinking model (emits "Thinking Process:…").

## Blocker fixed: JIT-compile with no matching CUDA toolkit

The model JIT-compiles CUDA kernels at load, but the box has no system CUDA toolkit (`/usr/local/cuda` absent, no system `nvcc`). Three sequential failures at engine init, each fixed:

1. **`Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist`**
   → Point `CUDA_HOME` at the torch-bundled cu13 wheel (`.venv/lib/python3.13/site-packages/nvidia/cu13`, ships nvcc 13.3 + libcudart). Also `ln -sf lib lib64` inside that dir (linker wants `lib64`). Same pattern as `install_sky.sh`'s `CUDA_HOME` fallback.

2. **`[Errno 2] No such file or directory: 'ninja'`**
   → `uv pip install ninja`; put `.venv/bin` on the launch PATH so the JIT build subprocess finds it.

3. **`error "CUDA compiler and CUDA toolkit headers are incompatible"`** (FlashInfer JIT of the sampling kernel — its bundled CCCL headers clash with cu13 `cooperative_groups`)
   → Disable FlashInfer: `VLLM_USE_FLASHINFER_SAMPLER=0` + `VLLM_ATTENTION_BACKEND=FLASH_ATTN`. Clear the poisoned cache first: `rm -rf ~/.cache/flashinfer`.

### Working launch command

```bash
CU13="$PWD/.venv/lib/python3.13/site-packages/nvidia/cu13"
ln -sf lib "$CU13/lib64"   # once
CUDA_VISIBLE_DEVICES=0,1 env \
  CUDA_HOME="$CU13" PATH="$PWD/.venv/bin:$CU13/bin:$PATH" \
  LD_LIBRARY_PATH="$CU13/lib:$LD_LIBRARY_PATH" \
  VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_ATTENTION_BACKEND=FLASH_ATTN \
  .venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3.5-9B --served-model-name Qwen/Qwen3.5-9B \
  --port 8000 --api-key nokey --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.90 --enable-prefix-caching --no-enable-log-requests
```

### Two gotchas

- vLLM 0.28 renamed `--disable-log-requests` → `--no-enable-log-requests` (old flag errors at arg parse).
- Must serve on **port 8000** with **served-model-name = the HF id**. `run_terminal_bench.sh --mode base` does not start a server — it points `EndlessAgent` at whatever is already serving. The agent's `generator.chat_completion_batch` treats `--model` as an endpoint only if it starts with `http://`; otherwise it hardcodes `localhost:8000/v1` and sends the model *name* in the request.

## Eval launch

```bash
bash scripts/run_terminal_bench.sh \
  --mode base --model Qwen/Qwen3.5-9B \
  --job-name tb-base-qwen3.5-9b --n-concurrent 5
```

Runs in tmux session `endless`. Monitor / collect:

- Attach: `tmux attach -t endless`
- Log: `tail -f harbor_logs/tb_run_tb-base-qwen3.5-9b.log`
- Results (pass@k): `python generator/collect_harbor_results.py --jobs-dir solution_tb`
