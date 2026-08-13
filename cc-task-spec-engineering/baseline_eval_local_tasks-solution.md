# Solution: baseline_eval_local_tasks

## Problem

Run baseline pass@1 and pass@4 evaluation for local Qwen models on harbor_tasks_v3_test
(165 tasks), using vLLM-served models and Harbor for orchestration.

## What Was Done

### 1. Dataset
Downloaded from S3:
```bash
aws s3 sync s3://endless-terminals-training/data/harbor_tasks_datagen_test/harbor_tasks_v3_test/ \
    harbor_tasks_datagen_test/harbor_tasks_v3_test/ --region us-west-1
```
165 tasks downloaded.

### 2. Models
| Model | Status |
|-------|--------|
| Qwen/Qwen2.5-3B | Already cached |
| Qwen/Qwen3.5-4B | Already cached |
| Qwen/Qwen3-4B | Downloaded via `huggingface_hub.snapshot_download('Qwen/Qwen3-4B')` |

### 3. vLLM Servers
| Model | GPU | Port |
|-------|-----|------|
| Qwen/Qwen2.5-3B | 6 | 8006 |
| Qwen/Qwen2.5-3B | 7 | 8007 |
| Qwen/Qwen3.5-4B | 1 | 8001 |
| Qwen/Qwen3.5-4B | 2 | 8002 |
| Qwen/Qwen3-4B | 3 | 8003 |

Started with:
```bash
CUDA_VISIBLE_DEVICES=<GPU> \
  PATH="/opt/pytorch/bin:$HOME/.local/bin:$PATH" \
  LD_LIBRARY_PATH="/opt/pytorch/cuda/lib:${LD_LIBRARY_PATH}" \
  /opt/pytorch/bin/vllm serve "<MODEL>" \
    --port <PORT> --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.6 --max-model-len 8192 \
    --enforce-eager --served-model-name "<MODEL>"
```

### 4. Eval Jobs
3 parallel jobs launched via `evaluate_baseline.py`:
```bash
.venv/bin/python evaluate_baseline.py \
    --dataset-path harbor_tasks_datagen_test/harbor_tasks_v3_test \
    --model <MODEL> \
    --n-attempts 8 \
    --n-concurrent 8 \
    --jobs-dir baseline_results \
    --job-name <MODEL_SLUG>__harbor_tasks_v3_test__n8 \
    --output-dir output/datagen_test \
    --vllm-base-url http://localhost:<PORT>/v1
```

Job names:
- `Qwen_Qwen2-5-3B__harbor_tasks_v3_test__n8`
- `Qwen_Qwen3-5-4B__harbor_tasks_v3_test__n8`
- `Qwen_Qwen3-4B__harbor_tasks_v3_test__n8`

### 5. Issues Encountered

**Docker network pool exhaustion**
- 29 zombie containers from previous datagen_test runs consumed all bridge networks
- Fix: `docker ps --format "{{.Names}}\t{{.RunningFor}}" | grep "hours ago" | awk '{print $1}' | xargs docker rm -f`
- Then: `docker network prune -f`

**EnvironmentStartTimeoutError on 3 tasks**
- `task_000054_487e083a` — SQLite 500k-row seed at build time
- `task_000086_d35c9498` — Git repo + Grafana JSON history
- `task_000160_6e6faca5` — Large JSONL audit log export
- All have `build_timeout_sec = 600.0` but setup exceeds 10 min
- Fix: killed stuck containers manually; isolation logic added to `evaluate_baseline.py`
  (see `environment-start-timeout-fix-solution.md`)

### 6. Results
Output files in `output/datagen_test/`:
- `Qwen_Qwen2-5-3B__harbor_tasks_v3_test__n8.json/.md`
- `Qwen_Qwen3-5-4B__harbor_tasks_v3_test__n8.json/.md`
- `Qwen_Qwen3-4B__harbor_tasks_v3_test__n8.json/.md`

## Key Scripts & Files
- `evaluate_baseline.py` — main eval runner
- `scripts/start_vllm.sh` — vLLM server launcher
- `scripts/run_parallel_eval.sh` — parallel multi-GPU launcher
- `output/datagen-findings/environment-start-timeout.md` — timeout finding
- `cc-tasks-solutions/environment-start-timeout-fix-solution.md` — timeout fix solution
