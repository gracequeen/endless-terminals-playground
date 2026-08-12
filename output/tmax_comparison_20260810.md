# Endless Terminals vs TMax: Dataset Comparison & Improvement Plan

**Date:** 2026-08-10  
**Datasets:** `harbor_tasks_8192_deduped` (local, 4,929 tasks) vs `allenai/TMax-15K` (14,601) and `allenai/TMax-SFT-16.5K` (2,200)  
**Notebook:** `notebooks/tmax_comparison.ipynb`

---

## Part 1 — Field Mapping

Both datasets encode the same semantic content under different names:

| Ours | TMax | Meaning |
|---|---|---|
| `difficulty` | `task_complexity` | difficulty level |
| `category` | `domain` | topic area |
| `instruction.md` | `description` | task prompt |
| `solution/` files | `truth` | ground truth solution |
| `environment/Dockerfile` | `container_def` | container setup |
| `tests/test_final_state.py` | `test_final_state` | verifier |
| `environment/test_initial_state.py` | `test_initial_state` | env setup test |
| *(none)* | `skill_type` (29 types) | skill classification |
| *(none)* | `primitive_skills` (list) | fine-grained skill decomposition |
| *(none)* | `scenario` (73 types) | persona/role context |
| *(none)* | `language` | primary language (Python/Bash/C/C++/Go/Rust/multi) |

---

## Part 2 — Comparison

### 2.1 Size

| Dataset | Tasks |
|---|---|
| Endless Terminals (local, deduped) | 4,929 |
| TMax-15K | 14,601 |
| TMax-SFT-16.5K | 2,200 |

We are ~3× smaller than TMax-15K.

---

### 2.2 Difficulty / Complexity

Normalized TMax `task_complexity` strings to easy/medium/hard/intricate:

| Level | Ours | TMax-15K |
|---|---|---|
| easy | 35.8% | ~25% |
| medium | 54.2% | ~25% |
| hard | 10.0% | ~25% |
| intricate (30–60 cmd multi-stage) | **0%** | **~26%** |

We have no intricate tier. TMax's intricate tasks combine: environment setup, multi-file implementation, iterative refinement against a quantitative verifier, and a final integration step.

---

### 2.3 Domain Coverage

After semantically mapping our 61 fine-grained categories to TMax's 9 broad domains:

| Domain | Ours | TMax-15K |
|---|---|---|
| system_administration | **heavy** | ~10% |
| file_operations | **heavy** | ~11% |
| software_engineering | moderate | ~11% |
| debugging | moderate | ~11% |
| data_processing | low | ~11% |
| data_querying | low | ~12% |
| data_science | **very low** | ~12% |
| scientific_computing | **very low** | ~12% |
| security | low | ~10% |

We are dominated by sysadmin + file_operations (~50% combined). TMax is deliberately balanced at ~11% per domain.

---

### 2.4 Task Description / Instruction Length

| Dataset | Mean words | Median words |
|---|---|---|
| Endless Terminals | **94** | **102** |
| TMax-15K | **299** | **296** |

Our descriptions are ~3× shorter. TMax writes rich, scenario-embedded prompts with explicit persona context ("you are a data engineer building an ETL pipeline..."), multi-step framing, and quantitative success criteria stated inline. Ours are terse imperative instructions.

---

### 2.5 Verifier Complexity (assert count as proxy)

This is a meaningful complexity metric — more assertions = more thorough behavioral checking.

| Dataset | Mean asserts | Median | Max |
|---|---|---|---|
| Endless Terminals | **25.7** | **25** | 68 |
| TMax-15K | **8.6** | **8** | 35 |

**Surprising finding:** Our verifiers have ~3× more assert statements than TMax's. Our tests are longer (mean 245 lines vs TMax's 61 lines) and more exhaustive per task. This is a strength — our verifiers are rigorous. TMax trades verifier depth for breadth of coverage.

Our assert count scales with difficulty as expected (easy: 17, hard/medium: ~30), suggesting our difficulty labels are well-calibrated.

---

### 2.6 Solutions (ground truth)

| Dataset | Has solution |
|---|---|
| Endless Terminals | **0%** (0/4,929) |
| TMax-15K | **100%** (14,601/14,601) |

All our `solution/` directories are empty — solutions are generated separately via Harbor runs and stored elsewhere. TMax ships ground truth with every task (mean 2,003 chars). This is a significant gap for SFT use cases.

---

### 2.7 Language Coverage

TMax explicitly tags language: Python (35%), Bash (15%), C (15%), C++ (10%), Go (7%), Rust (7%), multi (6%), any (5%).

We don't track this, but our categories suggest heavy Bash/Python bias with minimal compiled-language coverage. No C, C++, Go, or Rust tasks are visible in our category labels.

---

### 2.8 Skill Taxonomy

TMax has a two-level skill taxonomy:
- **`skill_type`** (29 types): Systems, Algorithmic, Mathematical, Data Processing, Testing, Web Security, Graph Processing, etc.
- **`primitive_skills`** (free list per task): e.g. "Delta debugging", "Dimensionality reduction", "Parallel computing setup (MPI, OpenMP)"

We have none of this. Our categories are flat and domain-oriented, not skill-oriented. This matters for curriculum learning and gap analysis.

---

### 2.9 Scenario / Persona Context

TMax has 73 named scenarios grounding tasks in real roles: "data analyst processing CSV files", "bioinformatics analyst processing sequences", "MLOps engineer tracking experiment artifacts". This enriches diversity and realism.

We have no scenario metadata and our descriptions don't embed persona context.

---

### 2.10 Container Complexity

| Dataset | Mean Dockerfile (chars) | Median |
|---|---|---|
| Endless Terminals | 2,756 | 2,306 |
| TMax-15K | 1,657 | 1,497 |

Our Dockerfiles are ~65% longer on average, likely because our generator produces more complex environment setup. This may partly explain the known heredoc syntax issue affecting ~97% of our tasks.

---

## Part 3 — Summary of Gaps

| Gap | Severity | Notes |
|---|---|---|
| No intricate/multi-stage tasks | **High** | 0% vs 26% in TMax; limits hard RL training signal |
| Data science / scientific computing under-represented | **High** | ~0% vs ~24% combined in TMax |
| No ground truth solutions | **High** | Blocks SFT use; TMax ships 100% |
| Task descriptions too terse | **Medium** | 3× shorter; less scenario context for the agent |
| No language diversity | **Medium** | No C/C++/Go/Rust tasks |
| No skill taxonomy | **Medium** | Limits curriculum analysis and targeted generation |
| No persona/scenario metadata | **Low** | Nice-to-have for diversity analysis |
| Domain imbalance (sysadmin heavy) | **Medium** | ~50% sysadmin+file_ops vs ~20% in TMax |

**Strengths to preserve:**
- Verifier depth (3× more assertions than TMax — don't dilute)
- Fine-grained category labels (61 vs 9 — more useful for analysis)
- Dockerfile complexity (richer environments)

---

## Part 4 — Improvement Plan

### P1 — Add intricate/multi-stage tasks

**What:** Generate a new difficulty tier: tasks requiring 3–5 chained sub-goals, multiple files/languages, and a quantitative verifier (e.g. "output must match within 1e-6", "benchmark must improve by >20%").

**How:**
- Add an `intricate` difficulty level to `generator/task_template_gen.py`
- Update the task generation prompt to require: (a) explicit sub-goal decomposition, (b) iterative refinement steps, (c) quantitative success criterion
- Target: ~1,200 intricate tasks (25% of current dataset size) to reach parity with TMax's tier distribution

---

### P2 — Fill domain gaps: data science & scientific computing

**What:** Generate tasks in currently missing domains — pandas/numpy workflows, sklearn pipelines, scipy/numerical computing, matplotlib output validation, bioinformatics tools (samtools, bedtools), simulation (Monte Carlo, FEM).

**How:**
- Add new category seeds to the task template generator covering:
  - Data science: `pandas data cleaning`, `sklearn model training and evaluation`, `matplotlib figure generation`, `jupyter notebook execution`
  - Scientific computing: `numpy/scipy numerical solver`, `Monte Carlo simulation`, `HDF5/netCDF data processing`, `parallel computation with multiprocessing`
- Target: ~800 new tasks split across these domains to reach ~10% each

---

### P3 — Generate ground truth solutions

**What:** Run Harbor solution generation on all 4,929 deduped tasks to populate `solution/` directories.

**How:**
- Use `generate_harbor_solutions.py` with existing pipeline
- Filter to tasks where at least one attempt passes (pass@k > 0) — store best passing solution as ground truth
- Enables SFT data export and richer comparison with TMax-SFT-16.5K

---

### P4 — Enrich task descriptions with scenario context

**What:** Update the task generator prompt to embed a persona/scenario framing in the instruction (e.g. "You are a DevOps engineer..."), add quantitative success criteria inline, and target ~250–350 words (vs current ~94).

**How:**
- Modify the description generation prompt in `generator/task_template_gen.py` to:
  - Prepend a one-sentence scenario/role context
  - State the expected output or measurable success criterion explicitly
  - Expand background/motivation to 2–3 sentences
- Re-generate descriptions for existing tasks OR apply only to new generation runs

---

### P5 — Add language diversity (C, Go, Rust)

**What:** Generate tasks that require writing/debugging C, Go, or Rust code in the terminal environment.

**How:**
- Add language-tagged category seeds: `C memory debugging`, `Go CLI tool`, `Rust build and test`, `C++ performance optimization`
- Dockerfile generator needs corresponding base images (gcc, golang, rust toolchain)
- Target: ~300 tasks per language (~900 total), reaching ~6% language diversity

---

### P6 — Add skill taxonomy metadata

**What:** Tag each task with a `skill_type` and `primitive_skills` list, matching TMax's schema.

**How:**
- Option A (generative): Add a post-generation step that calls an LLM to classify each existing task against TMax's 29 skill_type values and generate a `primitive_skills` list — cheap, parallelizable
- Option B (rule-based): Write a mapping from our 61 categories to TMax's skill_type taxonomy
- Store in `task.toml` under `[metadata]`
- Enables direct apples-to-apples comparison and curriculum-aware sampling

---

### Execution order

| Priority | Task | Effort | Impact |
|---|---|---|---|
| 1 | P3 — Generate solutions (run Harbor) | Low (existing pipeline) | High (unlocks SFT) |
| 2 | P6 — Add skill taxonomy (LLM classify existing) | Low (post-hoc LLM call) | Medium (analysis) |
| 3 | P2 — Fill data science / sci-comp gaps | Medium (new category seeds) | High (domain balance) |
| 4 | P4 — Richer descriptions | Medium (prompt update) | Medium (agent context) |
| 5 | P1 — Intricate tasks | High (new difficulty tier) | High (hard RL signal) |
| 6 | P5 — Language diversity | High (new envs) | Medium (breadth) |
