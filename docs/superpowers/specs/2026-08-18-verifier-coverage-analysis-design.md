# Verifier Coverage Analysis — Design Spec

**Date:** 2026-08-18  
**Author:** Elin Park  
**Ticket:** #41 — Data understanding and exploration for enhancement  
**Goal:** Research insight into verifier quality in the Endless Terminals dataset.

---

## Problem

Endless Terminals verifiers (`test_final_state.py`) average 3× more assert statements than TMax-15K (25.7 vs 8.6). High assert count is assumed to mean high quality, but we don't know whether those asserts actually test the stated task goal or merely check incidental file structure. This limits our ability to evaluate dataset quality and improve generation.

**Core research questions:**
1. What behavioral categories do our verifier asserts fall into (file existence, content, process output, permissions)?
2. Do verifier asserts align with the stated task goal, or do they check unrelated/precondition state?
3. Does structural complexity (assert category mix) correlate with semantic goal-alignment?
4. Does verifier quality correlate with informative reward signal (pass@k not too easy, not always 0)?

---

## Approach: Hybrid structural + LLM analysis

### Section 1 — Structural analysis (all 4,929 tasks)

**Input:** `test_final_state.py` for every task in `harbor_tasks_8192_deduped/`  
**Method:** AST parsing of each assert statement, classify into behavioral categories.

**Assert categories:**
- `file_exists` — `os.path.exists(...)`, `Path(...).exists()`
- `file_content` — file read + content assertion
- `permissions` — `os.stat(...)`, `.st_mode`, `oct(...)`
- `process_exit` — `subprocess.run(...)` checking return code
- `stdout_output` — capturing and asserting on command stdout/stderr
- `no_op` — trivially true asserts (`assert True`, always-passing fixtures)

**Per-task metrics:**
- Assert count per category
- `outcome_ratio` = (process_exit + stdout_output + file_content) / total_asserts
- `structural_score` = `outcome_ratio` (0–1, higher = more outcome-checking)

**Output:** Distribution charts of structural score overall and by difficulty. This establishes whether our verifiers skew toward checking state (file exists) vs. outcome (did the task actually work).

---

### Section 2 — Goal-alignment via LLM labeling (sampled ~300 tasks)

**Input:** Stratified sample — 75 tasks per structural score quartile (bottom 25%, 25–50%, 50–75%, top 25%)  
**Method:** For each sampled task, send `instruction.md` + `test_final_state.py` to Claude. Ask it to label each assert as:
- `goal_direct` — directly verifies the stated task outcome
- `precondition` — checks setup/environment state, not the goal
- `incidental` — checks something unrelated to the stated goal

**Per-task metric:** `goal_alignment_ratio` = goal_direct / total_asserts

**Analysis:** Correlate `goal_alignment_ratio` with `structural_score`. This validates whether structural heuristics are a good proxy for semantic quality — a key research finding either way.

**Key hypothesis to test:** LLM-generated verifiers may have high assert counts but systematically poor goal alignment, even for tasks labeled "hard".

---

### Section 3 — Pass-rate correlation (conditional on S3 data)

**Input:** Solution trial results from `s3://endless-terminals-training/data/`  
**First step:** Inspect S3 structure to understand what solution data is available.  
**Method:** For tasks with Harbor trial results, compute pass@k. Correlate with `structural_score` and `goal_alignment_ratio`.

**Research question:** Do tasks with better-aligned verifiers produce more informative reward signal — i.e., is pass@k in the 10–90% range rather than 0% or 100%?

**If S3 data is insufficient:** Document what's missing and note this as a future analysis.

---

### Section 4 — Written findings and generation recommendations

A markdown summary cell covering:
- Distribution of assert categories across the dataset
- Structural score distribution by difficulty
- LLM label findings: what fraction of asserts are goal-direct vs. precondition vs. incidental
- Whether structural score predicts goal alignment (and how well)
- Pass-rate correlation findings (if available)
- 2–3 concrete recommendations for improving the generation pipeline

**Example recommendation shape:** "Reject verifiers where `goal_alignment_ratio < 0.5`", or "require at least one `stdout_output` assert per task."

---

## Implementation notes

- All analysis added as new cells in `data_improvements.ipynb`, after Grace's existing sections
- LLM calls use the existing AICore stack (`aicore_llm_access.py`) or direct Anthropic API — whichever is simpler for notebook use
- S3 access via `boto3`/`awscli` using existing AWS credentials
- No new scripts — notebook is the primary artifact
- Sample size of 300 keeps LLM cost under ~$5 at Sonnet pricing

---

## Success criteria

1. Structural analysis covers all 4,929 tasks with charts by category and difficulty
2. LLM labels on ~300 sampled tasks with goal_alignment_ratio computed
3. Correlation between structural score and LLM alignment score is measured and reported
4. Written findings cell with at least 2 concrete generation recommendations
5. Section 3 either produces pass-rate correlation findings or documents why data was insufficient
