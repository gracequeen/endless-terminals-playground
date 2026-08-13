# baseline_eval_local_tasks

Run baseline pass@1 and pass@4 evaluation for local Qwen models on a Harbor task dataset.

## Inputs
- Task dataset directory (Harbor format, downloaded from S3)
- Model list (e.g. Qwen/Qwen2.5-3B, Qwen/Qwen3.5-4B, Qwen/Qwen3-4B)
- n_attempts (number of trials per task, e.g. 8)
- n_concurrent (parallel trials per eval job)

## Steps

1. **Download dataset** from S3 to `harbor_tasks_datagen_test/<dataset_name>/`
2. **Ensure models are cached** — download via `huggingface_hub.snapshot_download` if not present
3. **Start vLLM servers** — one per model, each on a dedicated GPU and port:
   - `CUDA_VISIBLE_DEVICES=<GPU> /opt/pytorch/bin/vllm serve <MODEL> --port <PORT> --tensor-parallel-size 1 --gpu-memory-utilization 0.6 --max-model-len 8192 --enforce-eager --served-model-name <MODEL>`
   - With correct `PATH` and `LD_LIBRARY_PATH` for `/opt/pytorch`
   - Wait for HTTP readiness on each port before proceeding
4. **Launch eval jobs in parallel** — one per model via `evaluate_baseline.py`:
   - `--dataset-path`, `--model`, `--n-attempts`, `--n-concurrent`, `--vllm-base-url`, `--output-dir output/datagen_test`, `--job-name <MODEL_SLUG>__<DATASET>__n<N>`
5. **Monitor progress** — trial counts in `baseline_results/<job_name>/`, output files in `output/datagen_test/`
6. **Handle issues**:
   - Docker network pool exhaustion: kill stale containers (`docker ps` age filter), then `docker network prune -f`
   - `EnvironmentStartTimeoutError`: re-run with `--environment-build-timeout-multiplier 12` for affected tasks (isolation logic now built into `evaluate_baseline.py`)
7. **Collect results** — JSON + Markdown summaries written to `output/datagen_test/<job_name>.json/.md`

## Success criteria
- All trial counts reach `n_tasks × n_attempts`
- Output JSON files present for each model
- pass@1 and pass@4 reported in aggregate and per-task
