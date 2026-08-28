# Design: Large Instance Experiments — 4B and 9B

## 1. Motivation

All previous training runs used p5.48xlarge (8× H100 80GB). The OOM root cause is:

```
sequence_length × vocab_size (151k) × 4 bytes = huge backward pass allocation
```

On H100 80GB in colocated mode, we were forced into settings too constrained for stable GRPO:
- batch_size=4 (not enough reward variance)
- max_turns=6 (model can't finish complex tasks)
- max_generate_length=1024 (outputs may be truncated)

These constraints caused model collapse in the 20260723 run. Larger instances remove these constraints.

---

## 2. Instance Comparison

| Instance | GPU | Memory/GPU | Total Memory | Use case |
|----------|-----|-----------|--------------|----------|
| p5.48xlarge | 8× H100 80GB | 80 GB | 640 GB | Current — too constrained for stable GRPO |
| p5en.48xlarge | 8× H200 141GB | 141 GB | 1128 GB | **4B training — recommended** |
| b300*.48xlarge | 8× B300 288GB | 288 GB | 2304 GB | **9B training — recommended** |

> **Note on p5e**: specs are inconsistent between this doc and experiment logs — 20260808 ran on `p5e.48xlarge` and observed H200 141GB behavior. Treat p5e and p5en as equivalent until confirmed with AWS.

### 2.1. Why p5en for 4B

The 4B model has ~8GB of weights. The memory bottleneck is the backward pass log_softmax allocation:

```
max_seq_len × vocab_size × 4 bytes = 8192 × 151k × 4 ≈ 5 GB per sequence
```

p5en (141 GB/GPU) handles this comfortably and allows paper-equivalent settings (batch=16, turns=16, generate=2048) without OOM. p5 (80 GB) forces the too-small settings that caused the 20260723 collapse.

### 2.2. Why b300 for 9B

The 9B model has ~18 GB of weights. At paper-scale settings (batch=32, n_samples=16, turns=16), memory pressure is significant. b300 (288 GB/GPU) removes all memory constraints — every config in the ablation table below is safe, including paper-equivalent Test 4 (512 rollouts/step).

---

## 3. Models

### 3.1. 4B — Qwen3.5-4B on p5en

**Base eval avg_score**: 49% on deduped 8192 dataset

The 4B model solves roughly half the deduped tasks at baseline. This gives GRPO healthy reward variance — not too easy, not too hard. No dataset modification needed before running the ablation.

**Model path**: `Qwen/Qwen3.5-4B` (or instruct variant)

### 3.2. 9B — Qwen3.5-9B on b300

**Base eval avg_score**: 58% on deduped 8192 dataset (20260808 run)

However, avg_pass_at_4 = 95% during training rollouts on the same dataset — the model already solves nearly every task, leaving almost no GRPO gradient (std_reward ≈ 0). On the harder task set, measured pass@8 solvability was 6.2%, which is too sparse — with batch=16, expect only ~1 solvable task per step.

Before running the ablation for 9B, verify reward density on the target dataset:
- If avg_pass_at_4 > 80%: switch to harder tasks or implement partial rewards (Phase 7)
- If pass@8 < 20%: filter to only tasks with ≥1 pass in 8 attempts before training

**Model path**: `Qwen/Qwen3.5-9B` (or instruct variant)

---

## 4. Datasets

| Dataset | S3 Path (tasks) | Prepared Parquet | Solvable | Notes |
|---------|----------------|-----------------|----------|-------|
| v1 | `data/harbor_4.5opus_tasks/` | — | 457 | Claude 4.5 Opus tasks |
| v2 | `data/harbor_tasks_8192_deduped/` | — | 2,781 | Claude 4.6 Opus tasks, deduped |
| v3 (hard) | `data/harbor_4.8opus_tasks_v3_internet_access_config/` | — | 3,657 | Claude 4.8 Opus, internet access tasks |
| v3 easy (4B) | `data/harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_4b_shard{0,1}/` | — | 1,607 | Tasks easy for 4B model |
| v3 easy (9B) | `data/harbor_4.8opus_tasks_v3_easy_shards_for_eval/harbor_tasks_easy_9b_shard{0,1,2}/` | — | 1,607 | Tasks easy for 9B model |
| **v1+v2 combined** | | `prepared_data/train_combined_457_8192.parquet` / `val_combined_457_8192.parquet` | **3,238 train / 151 val** | Used in dryrun1–2D |
| **v1+v2+v3easy9B combined** | | `prepared_data/train_combined_v1v2v3easy9b.parquet` / `val_combined_v1v2v3easy9b.parquet` | **4,684 train / 312 val** | Used in dryrun3 |
| **v1+v2+v3hard combined** | | `prepared_data/train_combined_v1v2v3hard.parquet` / `val_combined_v1v2v3hard.parquet` | **6,529 train / 517 val** | Used in Phase 2 |

> "Easy for 4B" = tasks the 4B model can solve; "easy for 9B" = tasks the 9B model can solve (harder than 4B easy). Both are held-out eval sets, not training data.

---



## 5. Phase 1: Dry Run (20 steps)

**Goal**: Verify the setup is stable and reward signal is non-zero before committing to a full run.

**Model**: Qwen3.5-9B on p5en (H200 141GB)

---

### 5.1. dryrun1:
**Dataset**: Combined Original 457 + Deduped 8192 tasks
- Train: 3,238 tasks (457 + 2,781)
- Val: 151 tasks (51 + 100)
- S3: `s3://endless-terminals-training/prepared_data/train_combined_457_8192.parquet`
- Task dirs: `harbor_tasks_457/` + `harbor_tasks_8192_deduped/` on instance

**Config** (p5e baseline — conservative, known safe):

| Setting | Value |
|---------|-------|
| train_batch_size | 4 |
| n_samples_per_prompt | 4 |
| max_turns | 6 |
| max_generate_length | 1024 |
| max_seq_len | 4096 |
| gpu_memory_utilization | 0.35 |
| micro_train_batch_size_per_gpu | 1 |
| update_epochs_per_batch | 1 |

> **Critical**: `max_turns=6` must be set in both `generator.max_turns` (train script) AND `default.yaml → agent.kwargs.max_turns`. The dry run script sets both automatically.

**Run**:
```bash
bash scripts/prepare_combined_data.sh                        # step 1: download + combine datasets
bash scripts/train/train_harbor_qwen3_5_9b_dryrun.sh        # step 2: 20-step dry run
```

**Checkpointing**: every 5 steps, eval every 10 steps on 50 held-out tasks

**Metrics collected** (automatically via `scripts/collect_metrics.py`, uploaded to S3 every 30s):

Reward signal:

| Metric | Good | Bad |
|--------|------|-----|
| std_reward | > 0.1 consistently | Near 0 — all-pass or all-fail batches, no GRPO gradient |
| avg_pass@2 | Trending up from step 1 | Flat or dropping after step 10 |
| avg_reward | Slowly trending up | Flat throughout |

Stability:

| Metric | Good | Bad |
|--------|------|-----|
| policy_entropy | Stable or slowly declining | Sharp drop — entropy collapse |
| grad_norm | < 10, stable | Spiking above 50 (20260723 hit 64M at collapse) |
| policy_loss | Small, stable | Exploding (20260723 hit 2471 at step 186) |

Generation quality:

| Metric | Good | Bad |
|--------|------|-----|
| response_length | Well below 1024 | Hitting ceiling every step — model being cut off |
| sequence_length | Well below 4096 | Consistently at max |

**Per-task eval results**: saved per checkpoint as `eval_metrics.json` with individual pass/fail per task, enabling analysis of which task categories and difficulty levels the model solves. Output files: `training_metrics.json`, `eval_metrics.json`, `metrics_summary.json`.

**S3 output**: `s3://endless-terminals-training/<date>_combined-data_dryrun_grpo_qwen3.5-9b_20steps/`

**Decision rule**:
- If `std_reward ≈ 0` throughout → reward too sparse; filter to Opus-solvable tasks or implement partial rewards (Phase 7) before proceeding
- If `policy_entropy` drops sharply → collapse; check `default.yaml max_turns` matches `generator.max_turns`
- If both look healthy → proceed to Phase 3 ablation

**Result (2026-08-25, run `20260825_combined-data_dryrun_grpo_qwen3.5-9b_20steps` on p5en)**:

**S3**: `s3://endless-terminals-training/20260825_combined-data_dryrun_grpo_qwen3.5-9b_20steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun.sh`

- First run used `n_samples_per_prompt=4` — step 1 batch happened to draw all easy tasks → avg_pass_at_2=1.0, std_reward≈0. This was a bad batch, not a dataset problem.
- Fixed to `n_samples_per_prompt=2` (matching eval metric avg_pass_at_2). Re-ran same dataset.

**Training metrics (steps 1–20):**

| Metric | Value |
|--------|-------|
| std_reward (avg) | 0.37 |
| std_reward (range) | 0.33–0.50 (0.0 on 3/20 steps — all-pass batches, expected at batch_size=4) |
| avg_pass_at_2 (avg) | 0.74 |
| avg_pass_at_2 (range) | 0.25–1.0 (noisy — only 4 tasks/batch) |
| avg_response_length | ~530 tokens/turn (well below 1024 cap) |

**Eval metrics (step 20, 151 val tasks):**

| Metric | Value | Notes |
|--------|-------|-------|
| avg_score(pass@1) | **43.7%** | 1 attempt, solved within 6 turns |
| avg_score(pass@2) | N/A | Not measured — eval_n_samples_per_prompt=1 in this run |

> Note: SkyRL always runs eval on the final step regardless of `eval_interval` (hardcoded `or self.global_step == self.total_training_steps`). `eval_batch_size` is the dataloader batch size, not the number of eval tasks — all val tasks are always evaluated.
> For next run: set `trainer.eval_n_samples_per_prompt=2` so eval runs 2 independent attempts per task — making `avg_score(pass_any)` directly comparable to training's `avg_pass_at_2` (both measure "solved in at least 1 of 2 attempts"). Current eval used 1 attempt, making comparison invalid.

- **Decision**: combined 457+8192 dataset is suitable for 9B training on p5en. Proceed to next dry run with higher settings.


---

### 5.2. Next dry run — dryrun2:
**Next dry run config (p5en, before moving to b300):**

| Setting | Current dry run | Next dry run |
|---------|----------------|--------------|
| train_batch_size | 4 | 8 |
| n_samples_per_prompt | 2 | 2 |
| max_turns | 6 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 8192 |
| gpu_memory_utilization | 0.35 | 0.45 |
| micro_train_batch_size_per_gpu | 1 | 1 |

**S3**: `s3://endless-terminals-training/<date>_combined-data_dryrun2_grpo_qwen3.5-9b_20steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun2.sh`

**Result (2026-08-25, run `20260825_combined-data_dryrun2_grpo_qwen3.5-9b_20steps` on p5en):**

**S3**: `s3://endless-terminals-training/20260825_combined-data_dryrun2_grpo_qwen3.5-9b_20steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun2.sh`

**Training metrics (steps 1–20):**

| Metric | Value |
|--------|-------|
| std_reward (avg) | 0.41 |
| std_reward (range) | 0.24–0.50 (no zero-std steps — larger batch_size=8 eliminated the 3/20 zero-std steps from dryrun1) |
| avg_pass_at_2 (avg) | 0.83 |
| avg_pass_at_2 (range) | 0.625–1.0 |

**Eval metrics (step 20, 151 val tasks, 2 attempts per task):**

| Metric | Value | Notes |
|--------|-------|-------|
| avg_score(pass@2) | **2.65%** | 2 attempts × 8 turns each — at least 1 attempt solved the task |

> **Note**: pass@2 = 2.65% is not a model regression. 146/151 tasks have `stop_reason: error` with no actual model output — Docker containers crashed before the model was called. Root cause: `eval_n_samples_per_prompt=2` doubled Docker concurrency to `eval_batch_size × 2 = 50 × 2 = 100` simultaneous containers, overwhelming the Docker daemon. Fix for next run: use `eval_n_samples_per_prompt=1` (clean pass@1, comparable to dryrun1's 43.7%) or reduce `eval_batch_size` to ≤20 to cap concurrent containers at 40.

> **Note on max_seq_len vs max_turns**: for target b300 settings with max_turns=16 and max_generate_length=2048, max_seq_len must be raised to 16384–32768 to avoid truncating long trajectories. The 8192 limit in the next dry run is safe with max_turns=8.

> **Note on max_seq_len vs max_turns**: for target b300 settings with max_turns=16 and max_generate_length=2048, max_seq_len must be raised to 16384–32768 to avoid truncating long trajectories. The 8192 limit in the next dry run is safe with max_turns=8.


---

### 5.3. Next dry run — dryrun2B (Docker fix validation):

Same as dryrun2, with two changes to fix the Docker overload during eval:
1. `eval_batch_size`: 50 → **20** (caps concurrent containers at 20×2=40)
2. Docker cleanup loop running every minute during training+eval (kills dead/zombie containers)
3. `eval_n_samples_per_prompt`: keep at **2** (now safe with smaller batch + cleanup)

| Setting | Dryrun2 | Dryrun2B |
|---------|---------|---------|
| eval_batch_size | 50 | **20** |
| eval_n_samples_per_prompt | 2 (broken) | **2** (fixed) |
| Docker cleanup loop | not running | **running (every 1 min)** |
| Everything else | — | same |

**S3**: `s3://endless-terminals-training/20260825_combined-data_dryrun2b_grpo_qwen3.5-9b_10steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun2b.sh`

**Expected**: pass@2 eval metric should recover to ~43%+ (comparable to dryrun1 pass@1), confirming the fix works before proceeding to dryrun3.

**Result (2026-08-25, run `20260825_combined-data_dryrun2b_grpo_qwen3.5-9b_10steps` on p5en):**

**Training metrics (steps 1–10):**

| Metric | Value |
|--------|-------|
| std_reward (avg) | 0.45 |
| std_reward (range) | 0.39–0.50 (0 zero-std steps) |
| avg_pass_at_2 (avg) | 0.73 |
| avg_pass_at_2 (range) | 0.375–0.875 |
| policy_entropy | 0.145–0.188 (stable, no sharp drop) |
| grad_norm | 0.018–1.98 (healthy, no spikes) |
| response_length | 1021–11988 (step 5 spike at 11988; otherwise normal) |

No flags raised on any step.

**Eval metrics (step 10, 151 val tasks, 2 attempts per task):**

| Metric | Value | Notes |
|--------|-------|-------|
| pass@2 | **5.3%** (8/151) | At least 1 of 2 attempts solved the task (`pass_any` in collect_metrics.py) |

**Key anomaly**: 143/151 tasks show exactly 2 scores `[0.0, 0.0]` — the agent terminated after exactly 1 turn in each of the 2 attempts. Only 8 tasks ran full multi-turn trajectories (8–16 scores). This is a large regression from dryrun1's 43.7% base model eval.

**Possible causes**:
1. Docker containers still terminating after 1 turn — `eval_batch_size=20` reduced concurrency from 100→40 but may not have been sufficient, or a different failure mode (disk pressure, OOM) is killing containers after the first command.
2. Model regression from 10 training steps — unlikely given stable training metrics, but cannot rule out.

> Note: `collect_metrics.py`'s `avg_score_pass_at_2` checks whether the first 2 turn-level scores include a pass — not whether 2 independent attempts solved the task. With step-wise trajectories, this is a very early-turn metric, not the same as pass@2-attempts.

**Root cause identified**: Docker network pool exhaustion. Each Docker Compose project creates a new IPv4 subnet. Docker has ~30 default subnets. When eval containers fail mid-setup, Harbor exits the error path without calling `docker compose down` — leaving the network as a zombie. Zombie networks pile up across eval batches until the pool is full, causing all subsequent containers to fail immediately.

Error found in `train_debug.log`:
```
failed to create network task_004227_c47b1e7d__2hgsypp__env_default: Error response from daemon: 
could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network
```

During training this doesn't happen because Harbor always calls `docker compose down` on trial completion, cleaning up networks automatically. During eval failures, cleanup is skipped.

**Fix**: add `docker network prune -f` to the cleanup loop. This sweeps zombie networks before the pool exhausts.


---

### 5.4. Next dry run — dryrun2C:

Same as dryrun2B, with one change: add `docker network prune -f` to the cleanup loop to prevent IPv4 pool exhaustion.

| Setting | Dryrun2B | Dryrun2C |
|---------|---------|---------|
| docker network prune | ✗ | **✓ (every 1 min)** |
| Everything else | — | same |

**S3**: `s3://endless-terminals-training/20260826_combined-data_dryrun2c_grpo_qwen3.5-9b_10steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun2c.sh`

**Expected**: eval containers should no longer fail with network exhaustion → pass@2 recovers to ~65%+ (the true solve rate on good tasks).

**Result (2026-08-26, run `20260826_combined-data_dryrun2c_grpo_qwen3.5-9b_10steps` on p5en):**

**Training metrics (steps 1–10):**

| Metric | Value |
|--------|-------|
| std_reward (avg) | 0.42 |
| std_reward (range) | 0.24–0.50 (no zero-std steps) |
| avg_pass_at_2 (avg) | 0.78 |
| avg_pass_at_2 (range) | 0.50–1.0 |

**Eval metrics (step 10, 151 val tasks, 2 attempts per task):**

| Metric | Value | Notes |
|--------|-------|-------|
| avg_score(pass@2) | **4.6%** | 144/152 tasks still erroring |

> **Note**: Network prune fixed the IPv4 pool exhaustion (dryrun2b's error). New failure mode revealed: `Environment start timed out after 600 seconds` (112 occurrences) + `Docker compose command failed` (remaining IPv4 cases). Root cause: 40 simultaneous Docker builds during eval → CPU contention → builds queue up → 10-min timeout. Network fix removed the fast failure but uncovered the build contention.
>
> **Root cause (concurrency)**: Training runs 8 tasks × 2 samples = 16 concurrent containers and handles it via Harbor's retry (attempt 1/2 → attempt 2/2). Eval at 20×2=40 concurrent is 2.5× training. At that level, both retry attempts time out simultaneously — the system never reduces load between attempts. Reducing `eval_batch_size` to 8 (→ 16 concurrent, same as training) lets retries succeed.
>
> **Validation (dryrun2D)**: Before dryrun3, run 1-step validation with `eval_before_train=true`, `eval_batch_size=8`, `eval_n_samples_per_prompt=2` to confirm zero Docker errors at this concurrency.


---

### 5.5. Next dry run — dryrun2D (eval concurrency validation):

| Setting | Dryrun2C | Dryrun2D |
|---------|---------|---------|
| eval_batch_size | 20 | **8** (→ 16 concurrent containers) |
| eval_before_train | false | **true** (run eval immediately to validate) |
| TRAIN_STEPS | 10 | **1** (minimal — just enough to get an eval result) |
| eval_n_samples_per_prompt | 2 | **2** (keeping pass@2) |
| Everything else | — | same |

**S3**: `s3://endless-terminals-training/<date>_combined-data_dryrun2d_grpo_qwen3.5-9b_1steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun2d.sh`

**Expected**: zero `stop_reason: error` in eval; pass@2 recovers to ~65%+ (actual result: 76.8%).

**Result (2026-08-26, running):** In progress — 0 errors through 11/19 eval batches so far (batch_size=8 confirmed working).

**Result (2026-08-26, eval_before_train completed):**

| Metric | Value | Notes |
|--------|-------|-------|
| pass@2 (base model, step 0) | **76.8%** (116/151) | At least 1 of 2 attempts solved the task |
| Docker errors | **1/151** | 1 intrinsically broken task — not a Docker overload issue |
| Failed (ran, score=0) | 34/151 | Model attempted but didn't solve |

> Confirmed: `eval_batch_size=8` (→ 16 concurrent containers) is the fix. Compared to dryrun1 pass@1=43.7% — expected since pass@2 > pass@1 (two attempts vs one). Step 1 eval result pending (second eval currently running).


---
### 5.6. Next dry run — dryrun3:

| Setting | Dryrun2 | Dryrun3 |
|---------|---------|---------|
| train_batch_size | 8 | 8 |
| n_samples_per_prompt (training) | 2 | **8** |
| eval_n_samples_per_prompt | 2 (broken — Docker overload) | **2** (fixed — eval_batch_size=8) |
| eval_batch_size | 20 | **8** |
| max_turns | 8 | 8 |
| max_seq_len | 8192 | 8192 |
| gpu_memory_utilization | 0.45 | 0.45 |

**Training dataset (dryrun3):**

| Source | Tasks | Notes |
|--------|-------|-------|
| v1 | 457 | |
| v2 | 2,881 | |
| v3 easy (9B) — train split (90%) | ~1,446 | |
| **Total train** | **~4,784** | |

**Val dataset (dryrun3):**

| Source | Tasks | Notes |
|--------|-------|-------|
| v1 + v2 (existing) | 151 | 51 from v1 (~11%), 100 from v2 (~3.5%) |
| v3 easy (9B) — eval split (10%) | ~161 | harder than v1/v2 eval tasks |
| **Total val** | **~312** | |

> v3 easy (9B) tasks are "easy" only relative to v3 hard — v3 overall is hard (pass@4 ≈ 6-7% for 9B). Split 10% for eval (consistent with v1/v2 split ratios). v3 hard reserved for a later round.

**Metrics to track:**

| Metric | Where | Notes |
|--------|-------|-------|
| pass@1 | training | fraction of tasks where the 1st sample solved it |
| pass@2 | training | fraction of tasks with ≥1 of first 2 samples passing |
| pass@4 | training | fraction of tasks with ≥1 of first 4 samples passing |
| pass@8 | training | fraction of tasks with ≥1 of 8 samples passing (= avg_pass_at_8) |
| std_reward | training | > 0.1 consistently; key GRPO health signal |
| avg_score(pass@2) | eval (step 3) | 2 attempts per task, validated clean by dryrun2D |

> **Note on pass@1/2 vs pass@4/8**: vLLM async engine returns samples in order of completion — shorter responses finish first. Shorter = less thinking = usually wrong. Longer = more `<think>` tokens = more likely to solve the task. So pass@1 and pass@2 measure whether the quickest (least-reasoned) samples solved the task, not whether the model can solve it in 1–2 independent attempts. Expect pass@1 and pass@2 to be lower than pass@4/8 for this reason. The meaningful training signal is `pass@8` and `std_reward`.

**Goal**: Just 5 steps — enough to check if the v1+v2+v3easy9b dataset has the right difficulty for 9B. Key signals at step 1:
- `avg_pass_at_8` > 0.9 → too easy, switch to harder tasks
- `avg_pass_at_8` < 0.1 → too hard, expect sparse reward
- `std_reward` > 0.1 consistently → good signal, proceed to longer run

**Data prep**: Run `scripts/prepare_data_v3easy9b.sh` once before training to download v3 easy 9B tasks and generate combined parquets.

**S3**: `s3://endless-terminals-training/<date>_combined-data_dryrun3_grpo_qwen3.5-9b_5steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun3.sh`

**Result (2026-08-26, stopped early at 4 steps):**

**Training metrics:**

| Step | pass@8 | std_reward | error_trajectories | Notes |
|------|--------|-----------|-------------------|-------|
| 1 | 0.0 | 0.0 | 50/64 | Docker overload — response_length=1 (containers killed before generation) |
| 2 | 0.0 | 0.0 | 49/64 | Same |
| 3 | **0.125** | **0.242** | 53/64 | Real training signal |
| 4 | **0.125** | **0.211** | 53/64 | Stable |

> **Root cause**: No `MAX_CONCURRENCY` set → Harbor launched all 64 trials simultaneously (n_samples=8 × batch=8). Steps 1-2: too many containers crashed for gradient to be non-zero. Steps 3-4: ~11/64 survived, giving pass@8=0.125.
>
> **Dataset difficulty**: pass@8=0.125 on the v1+v2+v3easy9b combined dataset is good signal — not too easy, not too sparse.
>
> **Fix for dryrun3B**: add `generator.rate_limit.max_concurrency=16` to serialize 64 trials into batches of 16 (the validated safe threshold from dryrun2D).


---

### 5.7. Next dry run — dryrun3B:

| Setting | Dryrun3 | Dryrun3B |
|---------|---------|---------|
| TRAIN_STEPS | 5 (stopped at 4) | **3** |
| MAX_CONCURRENCY | none (64 concurrent) | **16** |
| Docker network pool | ~30 subnets (default /20) | **256+ subnets (/24, configured in daemon.json)** |
| Docker cleanup interval | 60s | **5s** |
| pass@1/2/4 logging | ✗ | **✓ (inline trainer patch in `train_harbor_qwen3_5_9b_dryrun3b.sh`)** |
| Everything else | — | same |

> **pass@k patch** (`PATCH_PASSATK=true` in dryrun3b): edits `SkyRL/skyrl/train/trainer.py` in-place to log `pass@1`, `pass@2`, `pass@4` in addition to `pass@n`. The patch is permanent (one-way file edit) — setting `PATCH_PASSATK=false` in a later script skips re-running it but does NOT revert it. With `n_samples=2`, the patch only adds `pass@1` (only k=1 < 2 qualifies) — `pass@2` is already logged by SkyRL natively. So for n_samples=2 runs, the patch is harmless but adds a noisy `pass@1` metric (always near 0 due to vLLM ordering).

> **Note on pass@1/2 vs pass@4/8**: vLLM async engine returns samples in order of completion — shorter responses finish first. Shorter = less thinking = usually wrong. Longer = more `<think>` tokens = more likely to solve the task. So pass@1 and pass@2 measure whether the quickest (least-reasoned) samples solved the task, not k independent random attempts. Expect pass@1/2 to be lower than pass@4/8. The meaningful training signal is `pass@8` and `std_reward`.
>
> - pass@1 = did the fastest sample (shortest thinking) solve it? → almost never → 0
> - pass@2 = did either of the 2 fastest solve it? → still rarely → 0
> - pass@4 = did any of first 4 solve it? → some, as longer responses start appearing
> - pass@8 = did any of all 8 solve it? → yes → the true solvability signal

> **Docker daemon config** (one-time instance setup, already applied on p5en):
> `/etc/docker/daemon.json` — added `default-address-pools` with `/24` subnets:
> ```json
> {"base": "172.17.0.0/12", "size": 24},
> {"base": "192.168.0.0/16", "size": 24}
> ```
> This gives 256+ available subnets vs the default ~30, preventing IPv4 pool exhaustion when zombie networks accumulate.
> Run `sudo systemctl restart docker` after editing (kills running containers — do before training).

**S3**: `s3://endless-terminals-training/20260826_combined-data_dryrun3b_grpo_qwen3.5-9b_3steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun3b.sh`

**Goal**: 3 steps with no Docker overload. If pass@8 > 0 on step 1 (no overload), proceed to full training.

**Result (2026-08-26):**

**Training metrics:**

| Step | pass@1 | pass@2 | pass@4 | pass@8 | std_reward | avg_raw_reward | errors | grad_norm |
|------|--------|--------|--------|--------|-----------|----------------|--------|-----------|
| 1 | 0.0 | 0.0 | 0.375 | **0.75** | 0.45 | 0.72 | 8/64 | 0.47 |
| 2 | 0.0 | 0.0 | 0.125 | **0.50** | 0.48 | 0.375 | 24/64 | 1.57 |
| 3 | 0.0 | 0.0 | 0.0 | **0.25** | 0.41 | 0.22 | 40/64 | 1.33 |

> Docker error count rising each step (8 → 24 → 40). IPv4 pool expansion + 5s cleanup helped but doesn't fully prevent accumulation over a long step. Needs investigation before a longer run.

**Eval metrics (step 3, 312 val tasks, 2 attempts per task):**

| Metric | Value | Notes |
|--------|-------|-------|
| avg_score_pass_any | **39.7%** (124/312) | Solved in at least 1 of 2 attempts within 8 turns |
| num_tasks | 312 | v1+v2 (151) + v3easy9b val split (~161) |

---

### 5.8. Next dry run — dryrun3C:

| Setting | Dryrun3B | Dryrun3C |
|---------|---------|---------|
| TRAIN_STEPS | 3 | **1** |
| n_samples_per_prompt | 8 | **2** |
| eval_before_train | false | false |
| pass@k patch | applied | not re-applied (already in trainer.py, harmless) |
| Everything else | — | same |

**Goal**: 1 step to confirm dataset difficulty is in the right range with a fair pass@2 signal.

> **Why pass@2 here differs from dryrun3b's pass@2**: With n_samples=8, vLLM returns samples ordered by completion speed — the first 2 are always the fastest/shortest responses (least reasoning = usually wrong), so pass@2 computed from those was always 0. With n_samples=2, there are only 2 samples total and no ordering bias — pass@2 is a genuine measure of whether the model solves the task in 2 independent attempts. The pass@2 from dryrun3c is the reliable difficulty signal.

**Decision criteria:**
- `pass@2` 0.3–0.7 → good difficulty, proceed to 200-step full training
- `pass@2` > 0.9 → too easy
- `pass@2` < 0.1 → too hard, reward too sparse

**S3**: `s3://endless-terminals-training/20260826_combined-data_dryrun3c_grpo_qwen3.5-9b_1steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_dryrun3c.sh`

**Result (2026-08-26)**:

Training (step 1):

| Metric | Value |
|--------|-------|
| avg_pass_at_2 | 0.625 |
| std_reward | 0.484 |
| avg_raw_reward | 0.625 |
| policy_kl | 0.134 |
| policy_entropy | 0.143 |
| grad_norm | 0.018 |
| num_error_trajectories | 2 |

Eval (312 val tasks, 2 attempts each):

| Metric | Value |
|--------|-------|
| avg_score_pass_any (solved in ≥1 of 2 attempts) | **41.7%** |
| avg_score_pass_at_1 (solved on turn 1) | 0.0% |
| avg_score_pass_at_2 (solved by turn 2) | 0.0% |

> pass@2 training = 0.625 → dataset difficulty is in the healthy range (0.3–0.7). Pass_any eval = 41.7% confirms the v1+v2+v3easy9b dataset is well-calibrated for 9B. ✅ Proceed to Phase 2 full training.

---

## 6. Phase 2: Full Training (200-300 steps)

**Goal**: Train a model that actually improves beyond baseline.

- Use full dataset (2781 training tasks, 100 val tasks for 4B; TBD for 9B based on task difficulty)
- Run 200-300 steps with checkpointing every 20 steps
- Save eval avg_score every 20 steps on 100 held-out tasks
- Upload checkpoints to S3 after each step, delete old ones to save disk

**Settings** (use the winning config from Phase 3 ablation as the starting point; these are the targets):

4B on p5en:

| Setting | Previous p5 (H100 80GB) | Target p5en |
|---------|------------------------|-------------|
| train_batch_size | 4 | 16 |
| n_samples_per_prompt | 4 | 8 |
| max_turns | 6 | 16 |
| max_generate_length | 1024 | 2048 |
| max_seq_len | 4096 | 8192 |
| gpu_memory_utilization | 0.10 | 0.40 |
| micro_train_batch_size_per_gpu | 1 | 2 |

9B on b300:

| Setting | 20260808 p5e baseline | Target b300 |
|---------|-----------------------|-------------|
| train_batch_size | 4 | 16 |
| n_samples_per_prompt | 4 | 8 |
| max_turns | 6 | 16 |
| max_generate_length | 1024 | 2048 |
| max_seq_len | 4096 | 8192 |
| gpu_memory_utilization | 0.35 | 0.60 |
| micro_train_batch_size_per_gpu | 1 | 2 |

**Success criteria**:
- 4B: eval avg_score at step 200 > 49% (base model) with clear upward trend
- 9B: eval avg_score at step 200 > 58% (base model) with clear upward trend; std_reward > 0.1 throughout

**Eval tracking**:
- Save per-task pass/fail results at every checkpoint, not just avg_score — this lets you analyze which categories or difficulty levels the model learns vs stays stuck on
- 100-200 eval tasks is fine; saving all results every checkpoint is cheap (10 checkpoints × 200 tasks = 2000 rows total)
- At the end, check: is the model only improving on easy tasks? Are certain task categories solved well while others are not? This breakdown is needed for paper analysis
- Extract checkpoints at steps ~100 and ~150 for terminal-bench eval to measure impact on external benchmarks

---

### 6.1. Phase 2 Run — v1+v2+v3hard, 200 steps

**S3**: `s3://endless-terminals-training/20260827_v1v2v3hard_phase2_grpo_qwen3.5-9b_200steps/`

**Script**: `scripts/train/train_harbor_qwen3_5_9b_phase2.sh`

**Model**: Qwen3.5-9B on p5en (H200 141GB)

**Dataset**: v1+v2+v3hard combined (6,529 train / 517 val)

**Config**:

| Setting | Value |
|---------|-------|
| train_batch_size | 8 |
| n_samples_per_prompt | 2 |
| eval_n_samples_per_prompt | 2 |
| max_turns | 8 |
| max_generate_length | 1024 |
| max_seq_len | 8192 |
| gpu_memory_utilization | 0.45 |
| MAX_CONCURRENCY | 16 |
| ckpt_interval | 10 |
| eval_interval | 10 |
| eval_batch_size | 8 |
| algorithm | GRPO |
| reward signal | pass@2 (solved in ≥1 of 2 attempts within 8 turns) |
| eval metric | avg_score_pass_any (solved in ≥1 of 2 attempts within 8 turns) |

**Training metrics:**

**Issue found (steps 1–10):** 75–87% of trajectories error per step. Step 10: complete failure — 0/16 trajectories complete, no gradient.

**Root cause:** terminus-2 installs tmux/asciinema at runtime when they are missing. v3 hard Dockerfiles add `ppa:deadsnakes/ppa` (for Python 3.11), which leaves a PPA source file in the image. At training time, containers have no internet — `apt-get update` tries to reach `ppa.launchpad.net`, fails, and aborts. The fallbacks (build tmux from GitHub, pip install asciinema) also need internet and also fail. v1/v2 Dockerfiles only have standard Ubuntu apt sources, which work without internet, so tmux installs fine at runtime there.

**Fix applied (2026-08-26):** Pre-install `tmux` and `asciinema` in all task Dockerfiles at image build time (when internet is available). Patched 18,179 Dockerfiles across all three datasets using `scripts/patch_dockerfiles_tmux.py`, inserting `RUN apt-get update && apt-get install -y tmux asciinema && rm -rf /var/lib/apt/lists/*` after the `FROM` line. Terminus-2's `tmux -V` check now passes on startup and the install path is never triggered.

**Next action:** Restart Phase 2 training with the patched Dockerfiles.

## 7. Phase 3: Hyperparameter Tuning (Ablation)

**Goal**: Identify which settings have the most impact on training stability and reward signal. Run a controlled ablation — one baseline plus three tests, each changing exactly one group of parameters. This isolates cause from effect.

**Duration**: 30 steps per test. Long enough to catch collapse (policy_entropy drop and grad_norm spike are usually visible by step 20-30) and see an early reward trend.

### 7.1. Baseline (same for both 4B and 9B)

| Setting | Value |
|---------|-------|
| train_batch_size | 8 |
| n_samples_per_prompt | 4 |
| max_turns | 8 |
| max_generate_length | 1024 |
| max_seq_len | 4096 |

---

### 7.2. Test 1 — More tasks per step

Only `train_batch_size` changes. Tests whether more tasks per step gives GRPO enough reward variance.

| Setting | Baseline | Test 1 |
|---------|----------|--------|
| train_batch_size | 8 | **16** |
| n_samples_per_prompt | 4 | 4 |
| max_turns | 8 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 4096 |

---

### 7.3. Test 2 — Longer episodes

Only `max_turns`, `max_generate_length`, and `max_seq_len` change. These three are changed together because increasing turns without increasing per-turn length is not useful.

Tests whether giving the model more turns and more tokens per command helps it finish complex tasks.

| Setting | Baseline | Test 2 |
|---------|----------|--------|
| train_batch_size | 8 | 8 |
| n_samples_per_prompt | 4 | 4 |
| max_turns | 8 | **16** |
| max_generate_length | 1024 | **2048** |
| max_seq_len | 4096 | **8192** |

> Remember: `max_turns` must be set in both `default.yaml` AND `generator.max_turns`. Mismatch causes 20k+ token sequences and OOM.

---

### 7.4. Test 3 — More samples per task

Only `n_samples_per_prompt` changes. Tests whether more within-task contrast improves GRPO gradient quality.

| Setting | Baseline | Test 3 |
|---------|----------|--------|
| train_batch_size | 8 | 8 |
| n_samples_per_prompt | 4 | **8** |
| max_turns | 8 | 8 |
| max_generate_length | 1024 | 1024 |
| max_seq_len | 4096 | 4096 |

---

### 7.5. Metrics

**Reward signal** — is GRPO getting anything to learn from?

| Metric | Good | Bad |
|--------|------|-----|
| std_reward | > 0.1 consistently | Near 0 every step — all-pass or all-fail batches |
| avg_pass@2 | Trending up from step 1 baseline | Flat or dropping after step 20 |
| avg_reward | Slowly trending up | Flat throughout |

`std_reward` is the single most important number. If it is near zero every step, the config is useless regardless of everything else. For 9B, also check avg_pass@2 at step 1 — if it is already 0.9+, the dataset is too easy before any training begins.

**Stability** — is training about to collapse?

| Metric | Good | Bad |
|--------|------|-----|
| policy_entropy | Stable or slowly declining | Sharp drop — entropy collapse |
| grad_norm | < 10, stable | Spiking above 50 (20260723 hit 64M at collapse) |
| policy_loss | Small, stable | Exploding (20260723 hit 2471 at step 186) |

**Generation quality** — is the model getting to use its turns?

| Metric | Good | Bad |
|--------|------|-----|
| response_length | Well below max_generate_length | Hitting the ceiling every step — model being cut off |
| sequence_length | Well below max_seq_len | Consistently at max — sequences being truncated |

> **Note**: Value Loss and Explained Variance are PPO/critic metrics. They do not appear in GRPO runs — ignore them.

### 7.6. Decision Rule

At step 30 for each test:
1. If `std_reward` is near 0 throughout → stop early, this config provides no GRPO signal
2. If `policy_entropy` is dropping sharply or `grad_norm` spikes → stop early, collapse in progress
3. If both look healthy → compare `avg_pass@2` trend; take the config with the clearest upward trend into Phase 2

If one test looks promising but inconclusive at step 30, extend that test to 50 steps. Do not extend all tests.

---

## 8. Key Risks

1. **9B near-ceiling on deduped dataset** — avg_pass_at_4 = 95% means std_reward ≈ 0, no GRPO signal. Mitigate: filter to harder tasks or implement partial rewards (Phase 7) before training.
2. **9B sparse reward on harder tasks** — measured pass@8 = 6.2% on the harder task set. With batch=16, expect only ~1 solvable task/step. Mitigate: filter training set to tasks with ≥1 pass in 8 attempts.
3. **Test leakage** — model reads `/tests/test_final_state.py` to game verifier. Check trial logs before full run (Experiment D from EXPERIMENTS.md).
4. **Disk space** — each 9B checkpoint is ~40 GB, 4B is ~8 GB. Use `max_ckpts_to_keep=1` and S3 uploader.

---

## 9. Phase 4: GRPO vs DPPO Comparison

**Motivation**: GRPO's core weakness is zero gradient when all samples in a batch pass or all fail — exactly the collapse pattern we saw in 20260723. DPPO (Distributed PPO) has a critic (value network) that estimates future returns and provides a training signal even when reward is sparse or all-zero.

| | GRPO | DPPO |
|--|------|------|
| Critic | No | Yes |
| Memory | Lower | ~2× (critic doubles parameters) |
| Gradient when all-fail | Zero | Non-zero (critic baseline) |
| Gradient when all-pass | Zero | Non-zero (critic baseline) |
| Stability | Needs reward variance | More stable, works with sparse reward |
| Harbor compatible | Yes | No — requires stateful GAE, use Direct Docker |

**On p5en (H200 141GB)**: critic memory is no longer a blocker. Running DPPO with a 9B model + critic becomes feasible.

**Proposed comparison experiment**:
1. Train 9B with GRPO on deduped 8192 dataset, 200 steps
2. Train 9B with DPPO on same dataset, same steps
3. Compare: reward curve stability, eval avg_score, collapse frequency

Note: DPPO requires Direct Docker approach (`train/sky_endless.py`), not Harbor — Harbor's step-wise trajectories are incompatible with GAE. This means switching back to stateless `bash -c` shell, which is less realistic than terminus-2's persistent shell.

---

## 10. Phase 5: DAPO instead of Vanilla GRPO

**Paper**: "DAPO: An Open-Source LLM Reinforcement Learning System at Scale" (Yu et al., 2025, arXiv:2503.14476, NeurIPS 2025)

**Problem it solves**: Vanilla GRPO wastes gradient steps on degenerate batches where all samples pass (std_reward=0) or all fail (std_reward=0). The 20260723 collapse was directly caused by this — most batches with batch_size=4 were all-fail, giving zero gradient for hundreds of steps.

**What DAPO adds**:
- **Dynamic sampling**: skip prompts where all G samples pass or all fail — only train on batches with 0 < |passing samples| < G. Eliminates zero-gradient steps entirely.
- **Decoupled clipping**: higher clip threshold for exploration, lower for exploitation — prevents entropy collapse
- **Token-level gradient loss**: normalizes loss by token count rather than sequence count — handles varying response lengths better
- **No KL divergence**: removes KL penalty, relies on clipping alone for stability

**Implementation**: Drop-in replacement for GRPO loss in SkyRL. Check if SkyRL already supports `filter_groups` or similar option; otherwise small patch to the GRPO trainer.

**Expected impact**: Eliminates the zero-gradient death spiral. Should significantly stabilize training compared to 20260723.

---

## 11. Phase 6: Curriculum Learning (Easy → Hard)

**Papers**:
- "DUMP: Automated Distribution-Level Curriculum Learning for RL-based LLM Post-training" (Wang et al., 2025, arXiv:2504.09710)
- "Curriculum Reinforcement Learning from Easy to Hard Tasks Improves LLM Reasoning" (Parashar et al., 2025, arXiv:2506.06632)

**Problem it solves**: Random task sampling means the model wastes steps on tasks it already solves (zero GRPO gradient) or tasks it can never solve (also zero gradient). The sweet spot is tasks where the model solves ~30-70% of attempts.

**How to tag task difficulty (for free)**:

Difficulty scores are already in the pipeline — the solvability filtering step ran Claude 4.6 Sonnet on each task multiple times. Those pass rates are the difficulty labels:

| Sonnet pass rate | Difficulty label |
|-----------------|-----------------|
| All attempts pass | Easy |
| ~75% pass | Easy-Medium |
| ~50% pass | Medium |
| ~25% pass | Medium-Hard |
| Only 1 attempt passes | Hard |

This data is already in the parquet files — `extra_info` column has per-task solution counts. No additional compute needed. Sonnet difficulty is more relevant than o3 anyway since we're training a model of comparable capability.

**What to try**:

1. **Simple version (immediate)**: Use existing baseline data — we know per-task pass/fail from the 4B and 3B 5-step runs. Bucket tasks into easy (4B solves >70%), medium (30-70%), hard (<30%). Start training on medium tasks, introduce hard tasks after 50 steps.

2. **DUMP version (principled)**: Track per-task advantage magnitude during training. Use UCB bandit to automatically up-sample tasks where the model is still improving and down-sample tasks where it has plateaued. No manual bucketing needed.

**Implementation**: Medium effort. Requires modifying the data sampler in `dataset.py` to support weighted sampling by difficulty bucket.

---

## 12. Phase 7: Turn-Level Credit Assignment (Partial Rewards)

**Papers**:
- "Reinforcing Multi-Turn Reasoning in LLM Agents via Turn-Level Reward Design" (Wei et al., 2025, arXiv:2505.11821)
- "iStar: Agentic Reinforcement Learning" (Liu et al., ICLR 2026) — implicit step rewards for agentic RL

**Problem it solves**: Current setup gives binary 0/1 reward after the full episode. If the model passes 4 out of 5 subtests it still gets 0 — same as passing nothing. This is extremely sparse signal and forces GRPO to guess which turns were responsible for failure.

**What to try**: Give partial reward based on how many pytest subtests pass:

```
reward = num_tests_passed / total_tests
```

For example, a task with 5 assertions: passing 3/5 → reward=0.6. This is almost free to implement — Harbor already supports soft rewards via `reward.json`. The verifier just needs to write a float instead of 0/1.

**Implementation**: Low effort. Modify `test.sh` in each task to count passing assertions and write a float to `reward.json`. No changes to SkyRL or Harbor needed.

**Expected impact**: Very high. Denser reward signal means GRPO gets useful gradient even from partially-solved tasks. Directly addresses the sparse reward problem that caused both the 20260629 PPO run and 20260723 GRPO run to flatline.

---

## 13. Prerequisites

Before starting Phase 1:
- [x] Confirm 9B model base eval avg_score on deduped 8192 tasks — done (58%, 20260808)
- [ ] Verify reward density on target dataset for 9B (check avg_pass_at_4 at step 1)
- [ ] Check trial logs for test leakage (cat /tests/ commands)
- [ ] Book p5en capacity block (4B)
- [ ] Book b300 capacity block (9B)
- [ ] Verify install_sky.sh works on p5en and b300 AMIs
