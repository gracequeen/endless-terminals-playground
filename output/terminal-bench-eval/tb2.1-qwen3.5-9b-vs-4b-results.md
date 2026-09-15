# Terminal-Bench-2-1 Results — Qwen3.5 9B vs 4B (base models)

**Branch:** `benchmark-tb-qwen`
**Dataset:** `terminal-bench/terminal-bench-2-1` (89 tasks)
**Agent:** `endless_harbor.endless_agent:EndlessAgent`
**Serving:** local vLLM 0.28.0, TP=2 per model (9B on GPUs 0,1 :8000; 4B on GPUs 2,3 :8001)
**Estimator:** unbiased pass@k (Chen et al., 2021), crashed/infra-failed trials excluded from denominator

---

## Run 2 — 16 attempts/task (2026-09-04)

**Config:** 16 attempts/task, concurrency 32, `max_completion_tokens=4096`, `--no-delete`

| Metric | **Qwen3.5-9B** | **Qwen3.5-4B** |
|---|---|---|
| pass@1 | **0.134** | 0.090 |
| pass@2 | **0.189** | 0.135 |
| pass@4 | **0.243** | 0.188 |
| pass@8 | **0.294** | 0.240 |
| Tasks solved (≥1 pass) | **31 / 89** | 25 / 89 |
| Valid trials | 1392 / 1425 | 1398 / 1425 |
| Excluded (infra crashes) | 33 | 27 |

### Notes

- **9B leads across all k**; gap widens vs 8-attempt run (both had 27 solved at k=8; now 31 vs 25).
- **9B-only solves** (not by 4B): crack-7z-hash, pypi-server, vulnerable-secret, log-summary-date-ranges, sanitize-git-repo, tune-mjcf
- **4B-only solves** (not by 9B): fix-ocaml-gc (9/16 — stronger than 9B!), hf-model-inference (7/16 vs 9B's 4/16), configure-git-webserver, pytorch-model-cli, polyglot-rust-c
- **9B top performers (16 attempts):** modernize-scientific-stack (16/16), kv-store-grpc (15/15), openssl-selfsigned-cert (13/16), git-leak-recovery (12/16), sqlite-with-gcov (10/16), portfolio-optimization (15/16)
- **4B top performers (16 attempts):** kv-store-grpc (15/16), modernize-scientific-stack (15/16), sqlite-with-gcov (10/16), fix-ocaml-gc (9/16), portfolio-optimization (11/15)

### Artifacts

| Artifact | Location |
|---|---|
| 9B per-task pass@k | `scripts/passk_score.py solution_tb/tb-base-qwen3.5-9b-tb2.1-FULL-16x32` |
| 4B per-task pass@k | `scripts/passk_score.py solution_tb/tb-base-qwen3.5-4b-tb2.1-FULL-16x32` |
| 9B raw trials | `solution_tb/tb-base-qwen3.5-9b-tb2.1-FULL-16x32/` |
| 4B raw trials | `solution_tb/tb-base-qwen3.5-4b-tb2.1-FULL-16x32/` |

---

## Run 1 — 8 attempts/task (2026-09-03)

**Config:** 8 attempts/task, concurrency 32, `max_completion_tokens=4096`, `--no-delete`

| Metric | **Qwen3.5-9B** | **Qwen3.5-4B** |
|---|---|---|
| pass@1 | **0.144** | 0.094 |
| pass@2 | **0.202** | 0.146 |
| pass@4 | **0.256** | 0.219 |
| pass@8 | **0.303** | 0.303 |
| Tasks solved (≥1 pass) | 27 / 89 | 27 / 89 |
| Valid trials | 699 / 712 | 696 / 712 |
| Excluded (infra crashes) | 13 | 16 |

### Notes

- **9B leads at low k** (~53% higher pass@1), **converge at pass@8 (both 0.303)** — 4B reaches 9B's coverage with more attempts.
- **Task overlap:** 21 solved by both; 6 only by 9B (extract-elf, git-multibranch, log-summary-date-ranges, overfull-hbox, pypi-server, vulnerable-secret); 6 only by 4B (configure-git-webserver, fix-code-vulnerability, fix-ocaml-gc, model-extraction-relu-logits, polyglot-rust-c, pytorch-model-cli).

### Artifacts

| Artifact | Location |
|---|---|
| 9B raw trials | `solution_tb/tb-base-qwen3.5-9b-tb2.1-FULL-8x32/` |
| 4B raw trials | `solution_tb/tb-base-qwen3.5-4b-tb2.1-FULL-8x32/` |

---

## Crashes / infra notes

- **0 image-pull crashes** on all runs — `--no-delete` preserved all 89 task images throughout (Harbor's default `docker compose down --rmi all` per-trial teardown evicts images; `--no-delete` uses plain `down`).
- Excluded crashes were transient **container-name conflicts** (`already in use by container`), a minor `--no-delete` side-effect — non-cascading, excluded from pass@k denominator.

## Context: why earlier runs scored 0.000

Initial runs scored 0.000 due to `max_completion_tokens=2048` truncating 100% of thinking-model
responses before they emitted a parseable action. Raising to 4096 unlocked real performance.
Other fixes: 4B `tokenizer_model` kwarg (URL-endpoint tokenizer crash), Docker network address-pool
raised (~4096 networks), all 89 images pre-pulled + backed up to `~/tb2_1_images_backup/`,
no docker cleanup loop during eval.

## Image backup

| Artifact | Location |
|---|---|
| 89 images backed up | `~/tb2_1_images_backup/images/` |
| Scorer (standalone) | `scripts/passk_score.py` |
