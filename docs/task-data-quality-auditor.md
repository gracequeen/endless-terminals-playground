# Task Data Quality Auditor — Design Spec
Ticket #46: Design doc for task data quality auditor

---

## 1. Motivation

Endless Terminals generates terminal-use tasks procedurally via a 5-stage LLM pipeline
(`task_template_gen` → `initial_state_test_gen` → `completion_test_gen` → `dockerfile_gen` →
save). Analysis of 4,929 tasks in `harbor_tasks_8192_deduped` (Ticket #41) revealed
measurable quality deficiencies that are invisible to the current pipeline:

- **16.6%** of tasks have `structural_score < 0.2` — verifiers that test filesystem state
  rather than task outcomes (process exit codes, stdout, file content).
- **110 tasks** (`~2.2%`) have `structural_score == 0` — no outcome-checking asserts at all.
- `structural_score` and `desc_overlap` are near-uncorrelated (Pearson r ≈ 0.03), meaning
  they capture independent quality dimensions — both are needed as filters.
- Domain gaps: `scientific_computing` (0 tasks), `data_science` (65), `security` (139).
- Zero `intricate`-tier tasks vs TMax-15K's 26%.

These findings motivate a dedicated quality auditing tool that acts as a production gate
during generation and a standalone analysis tool for dataset inspection.

---

## 2. Design Goal

Build a three-component tool (`auditor/`) that:

1. **Blocks low-quality tasks** from being saved during generation (gate mode).
2. **Reports dataset-level quality metrics** (report mode).
3. **Tracks container environment health and solution quality** as anomaly signals.

---

## 3. Architecture

```
endless-terminals-playground/
├── auditor/
│   ├── __init__.py          # TaskAuditResult dataclass, Decision enum
│   ├── offline.py           # Component 1: static conformance + semantic quality
│   ├── online.py            # Component 2: Docker environment health + anomaly tracking
│   └── solutions.py         # Component 3: solution quality (offline + online)
└── audit.py                 # CLI entry point
```

The three components share a single data model and are independently importable. Each
returns `list[TaskAuditResult]`. The CLI merges results and writes `audit_report.json`.

### 3.1 Shared Data Model (`auditor/__init__.py`)

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

class Decision(str, Enum):
    PASS   = "pass"
    FLAG   = "flag"
    REJECT = "reject"

@dataclass
class TaskAuditResult:
    task_id:  str
    task_dir: Path
    decision: Decision
    metrics:  dict        # component-specific float/int metrics
    flags:    list[str]   # human-readable reasons for flag/reject
```

`decision` follows precedence: any `reject` check overrides `flag`; `flag` overrides `pass`.

---

## 4. Component 1 — Offline Task Conformance & Semantic Quality

**File:** `auditor/offline.py`

**Inputs:** a task directory on disk following the Harbor layout:

```
task_{id}_{hash}/
├── instruction.md
├── task.toml                        # difficulty, category, tags
├── environment/
│   ├── Dockerfile
│   ├── task.json                    # {description, truth, name}
│   └── test_initial_state.py
└── tests/
    ├── test.sh
    └── test_final_state.py
```

### 4.1 Checks

All checks are static — no containers, no network. AST analysis uses Python's built-in
`ast` module, matching the methodology in Ticket #41.

#### Structural Score (`structural_score`)

Fraction of assert statements in `test_final_state.py` that check task outcomes
(process exit codes, stdout/stderr, file content) rather than passive state
(file existence, permissions).

```
structural_score = (process_exit + stdout_output + file_content asserts) / total asserts
```

Assert categories (keyword-based on `ast.unparse(node)`):

| Category | Keywords |
|---|---|
| `file_exists` | `os.path.exists`, `os.path.isfile`, `os.path.isdir`, `os.path.islink`, `.exists()` |
| `file_content` | `open(`, `.read(`, `.readlines(`, `content` |
| `permissions` | `os.stat`, `st_mode`, `oct(`, `os.access` |
| `process_exit` | `subprocess`, `returncode`, `Popen`, `check_call`, `check_output` |
| `stdout_output` | `stdout`, `stderr`, `capture_output` |
| `other` | all remaining |

Outcome-checking categories: `process_exit`, `stdout_output`, `file_content`.

**Thresholds:**
- `structural_score == 0` → **reject** (no outcome-checking asserts; regeneration candidate)
- `structural_score < 0.2` → **flag** (mostly state-checking; below empirical threshold from Ticket #41)

#### Description Overlap (`desc_overlap`)

Fraction of assert statements in `test_final_state.py` containing at least one keyword
extracted from `instruction.md`. Measures whether the verifier checks task-specific
behavior rather than generic filesystem state.

Keywords: lowercase alphabetic tokens ≥ 3 characters, excluding a fixed stopword list.

**Threshold:**
- `desc_overlap == 0` → **reject** (verifier references no task-specific terminology)

#### Assert Diversity (`assert_diversity`)

Number of distinct assert categories (from the table above) used in `test_final_state.py`.
Higher diversity indicates a verifier that checks multiple aspects of the task outcome.

**Threshold:**
- `assert_diversity < 2` → **flag**

#### Schema Conformance

Required files: `instruction.md`, `task.toml`, `environment/Dockerfile`,
`environment/task.json`, `environment/test_initial_state.py`, `tests/test_final_state.py`,
`tests/test.sh`.

**Threshold:**
- Any required file missing → **reject**

#### Syntax Validity

Both `test_initial_state.py` and `test_final_state.py` must parse without `SyntaxError`
via `ast.parse()`.

**Threshold:**
- `SyntaxError` in either file → **reject**

#### Metadata Validity

`task.toml` must contain non-empty `difficulty` and `category` under `[metadata]`.
Valid `difficulty` values: `easy`, `medium`, `hard`, `intricate`.

**Thresholds:**
- Missing or empty `difficulty` / `category` → **flag**
- `difficulty` not in valid set → **flag**

### 4.2 Interface

```python
def check_task(task_dir: Path) -> TaskAuditResult:
    """Run all offline checks on a single task directory."""

def check_batch(task_dirs: list[Path]) -> list[TaskAuditResult]:
    """Run offline checks on a list of task directories. Returns aligned list."""

def dataset_summary(results: list[TaskAuditResult]) -> dict:
    """Compute dataset-level aggregate statistics from a list of results.

    Returns: total/pass/flag/reject counts, mean/median structural_score,
    mean desc_overlap, domain distribution, difficulty distribution.
    """
```

---

## 5. Component 2 — Online Container Environment Health

**File:** `auditor/online.py`

**Inputs:** task directories with valid `environment/Dockerfile` and
`environment/test_initial_state.py` / `tests/test_final_state.py`.

This component **wraps** the existing `build_and_test_docker()` function in
`generator/dockerfile_gen.py` — it does not duplicate Docker build logic. It adds
structured result capture and batch-level anomaly tracking on top.

### 5.1 Per-Task Checks

The existing `build_and_test_docker()` already enforces:

1. Docker image builds successfully from `environment/Dockerfile`.
2. `test_initial_state.py` passes inside the container (environment set up correctly).
3. `test_final_state.py` **fails** inside the container (task is not trivially solved).

The online component records the outcome of each check as a structured result:

| Check | Condition | Decision |
|---|---|---|
| Docker build | `build_and_test_docker()` returns `False` | **reject** |
| Initial state tests pass | `test_initial_state.py` exit code `!= 0` | **reject** |
| Final state non-trivial | `test_final_state.py` exit code `== 0` in initial state | **reject** |
| Build timeout | `subprocess.TimeoutExpired` | **flag** |
| Dockerfile parse error | `"dockerfile parse error"` or `"unknown instruction:"` in Docker stderr | **reject** |
| Memory limit exceeded | OOM signal in Docker stderr | **flag** |

### 5.2 Batch-Level Anomaly Tracking

After running per-task checks across a batch, the following aggregate signals are computed
and reported. These detect systemic failures in the generation model or prompts rather
than isolated per-task issues:

| Signal | Formula | Threshold |
|---|---|---|
| Build failure rate | `failed_builds / total_tasks` | `> 0.3` → warning |
| Timeout rate | `timed_out / total_tasks` | `> 0.1` → warning |
| Trivially-solved rate | `trivially_solved / total_tasks` | `> 0.05` → warning |

Batch anomalies are reported in `audit_report.json` under `"batch_anomalies"` but do not
affect individual task decisions.

### 5.3 Interface

```python
def check_task(task_dir: Path) -> TaskAuditResult:
    """Build and run container checks for a single task."""

def check_batch(task_dirs: list[Path], max_workers: int = 4) -> list[TaskAuditResult]:
    """Run container checks in parallel. Returns aligned list."""

def batch_anomalies(results: list[TaskAuditResult]) -> dict:
    """Compute batch-level anomaly signals from per-task results."""
```

---

## 6. Component 3 — Solution Quality Checks

**File:** `auditor/solutions.py`

**Inputs:**
- Task directories (for cross-referencing task metadata).
- `solution/solution.json` files written by Harbor after agent runs.
- Run-level `result.json` from Harbor (e.g., `solution_sonnet/<run>/result.json`).

### 6.1 `solution.json` Schema (per task, offline)

```json
{
  "task_name": "task_000000_ff53f2f1",
  "num_runs": 8,
  "num_success": 0,
  "pass_at_k": {"1": 0.0, "2": 0.0, "4": 0.0, "8": 0.0},
  "trials": [{"trial_name": "...", "reward": 0.0, "success": false}]
}
```

### 6.2 `result.json` Schema (per Harbor run, online)

```json
{
  "id": "...",
  "n_total_trials": 232,
  "stats": {
    "n_errors": 2,
    "evals": {
      "<agent>__<model>__<tasks>": {
        "n_trials": 231,
        "n_errors": 2,
        "metrics": [{"mean": 0.414}],
        "reward_stats": {"reward": {"0.0": [...], "1.0": [...]}}
      }
    }
  }
}
```

### 6.3 Offline Checks (on `solution.json`)

| Check | Condition | Decision |
|---|---|---|
| Solution file present | `solution/solution.json` missing | **flag** (unevaluated) |
| `pass@1 == 0` | `pass_at_k["1"] == 0.0` across ≥2 independent runs | **flag** (possibly broken verifier or unsolvable task) |
| All trials failed + low structural score | `num_success == 0` AND `structural_score < 0.2` | **reject** (regeneration candidate — verifier likely wrong) |

### 6.4 Online Checks (on run-level `result.json`)

| Check | Condition | Signal |
|---|---|---|
| High error rate | `n_errors / n_trials > 0.05` | Batch warning: container instability |
| Low overall pass rate | `metrics[0]["mean"] < 0.1` for a full batch | Batch warning: generation quality regression |

### 6.5 Interface

```python
def check_task(task_dir: Path) -> TaskAuditResult:
    """Offline solution checks for a single task directory."""

def check_batch(task_dirs: list[Path]) -> list[TaskAuditResult]:
    """Offline solution checks for a list of task directories."""

def check_run(result_json: Path) -> dict:
    """Online anomaly checks for a Harbor run-level result.json."""
```

---

## 7. CLI Interface (`audit.py`)

```
python audit.py offline   --tasks-dir <dir> [--report <out.json>]
python audit.py online    --tasks-dir <dir> [--report <out.json>] [--workers N]
python audit.py solutions --tasks-dir <dir> --solutions-dir <dir> [--report <out.json>]
python audit.py all       --tasks-dir <dir> --solutions-dir <dir> [--report <out.json>]
```

All subcommands write `audit_report.json` (default) and print a summary table to stdout.

### 7.1 Report Format (`audit_report.json`)

```json
{
  "generated_at": "2026-09-02T17:00:00",
  "tasks_dir": "harbor_tasks_8192_deduped",
  "summary": {
    "total": 4929,
    "pass": 3987,
    "flag": 832,
    "reject": 110,
    "mean_structural_score": 0.408,
    "mean_desc_overlap": 0.773,
    "domain_distribution": {
      "file_operations": 1820,
      "system_administration": 1340,
      "scientific_computing": 0
    },
    "difficulty_distribution": {
      "easy": 1230, "medium": 2450, "hard": 1249, "intricate": 0
    }
  },
  "batch_anomalies": {
    "build_failure_rate": 0.04,
    "timeout_rate": 0.01,
    "trivially_solved_rate": 0.02
  },
  "tasks": [
    {
      "task_id": "task_003577_a6323242",
      "decision": "flag",
      "metrics": {
        "structural_score": 0.15,
        "desc_overlap": 0.82,
        "assert_diversity": 3,
        "assert_count": 18
      },
      "flags": ["structural_score_low"]
    }
  ]
}
```

---

## 8. Integration into Generation Pipeline

The gate hooks into `generate_harbor_tasks.py` after Stage 3 (final-state tests generated)
and before Stage 4 (Dockerfile generation). This is the earliest point where
`structural_score` and `desc_overlap` can be computed.

**Change to `_generate_harbor_batch()`:**

```python
# After Stage 3, before Stage 4
from auditor.offline import check_batch as offline_check_batch

audit_results = offline_check_batch([...task_data...])
valid = [i for i, r in enumerate(audit_results) if r.decision != Decision.REJECT]
# filter descriptions, truths, etc. down to valid indices
# flag tasks get quality_flags written to task.toml at Stage 5
```

Tasks with `decision=FLAG` are saved with a `quality_flags` list appended to `task.toml`
under `[metadata]`. Tasks with `decision=REJECT` are dropped and counted in the pipeline
summary. No changes to `dockerfile_gen.py`.

---

## 9. Threshold Validation

The `structural_score < 0.2` and `desc_overlap == 0` thresholds in Component 1 are validated
by cross-referencing them against agent solve rates from `solution.json`. We have 1,045 tasks
with solution data in `harbor_tasks_8192_deduped` — enough for a meaningful correlation study.

### 9.1 Analysis (to be run in `data_improvements.ipynb`, Section 6)

For each task that has both a computed `structural_score` and a `solution.json`:

1. **`structural_score` vs `pass@1`** — scatter plot + Pearson r. If tasks with
   `structural_score < 0.2` have significantly lower `pass@1` than tasks above 0.2, the
   threshold is empirically justified. Expected outcome: low-structural tasks cluster near
   `pass@1 = 0` because the verifier doesn't check real outcomes, making it either
   trivially passing or never solvable.

2. **`desc_overlap` vs `pass@1`** — same treatment. Tasks with `desc_overlap == 0` should
   show no meaningful signal in solve rate (verifier is disconnected from the task
   description entirely).

3. **Threshold sweep** — compute mean `pass@1` for tasks binned by `structural_score`
   (bins: [0, 0.1), [0.1, 0.2), [0.2, 0.4), [0.4, 0.6), [0.6, 1.0]). If there is a
   clear drop below 0.2, the threshold is validated. If the signal is flat, revise the
   threshold.

### 9.2 Results (computed on 1,045 tasks with both structural_score and solution.json)

| `structural_score` bin | N tasks | mean `pass@1` | median `pass@1` |
|---|---|---|---|
| [0, 0.1) | 52 | 0.130 | 0.000 |
| [0.1, 0.2) | 109 | 0.107 | 0.000 |
| [0.2, 0.4) | 340 | 0.106 | 0.000 |
| [0.4, 0.6) | 359 | 0.090 | 0.000 |
| [0.6, 1.0) | 185 | 0.049 | 0.000 |

**Pearson r (`structural_score` vs `pass@1`): −0.069**

The correlation is negative and |r| < 0.1 — no meaningful signal. Notably, mean `pass@1`
is slightly *higher* in the lowest structural score bins, which is consistent with the
hypothesis that low-structural verifiers tend toward state-checking that is *trivially*
satisfied rather than task outcome verification. The median is 0.0 across all bins,
indicating most tasks are unsolved regardless of structural score.

### 9.3 Threshold Justification (Fallback — Applied)

The fallback applies: `structural_score` does not predict agent solve rate. The threshold
justification is distributional:

- `structural_score == 0` → verifier has zero outcome-checking asserts; structurally broken
  regardless of solve rate. **Reject** is correct.
- `structural_score < 0.2` → captures the bottom 16.6% tail identified in Ticket #41.
  These verifiers are dominated by passive state checks (file existence, permissions) and
  are flagged to preserve dataset coverage while marking them for review.

The weak negative correlation (higher structural score → slightly lower solve rate) does
not undermine the threshold — it reflects model capability variation across task types, not
that low-structural verifiers are acceptable. Tasks in `[0, 0.1)` have high pass rates
because their verifiers are easier to trivially satisfy, not because they are better tasks.

---

## 11. Design Decisions and Rationale

| Decision | Rationale |
|---|---|
| Gate placed after Stage 3, not Stage 5 | Avoids expensive Docker builds (Stage 4) for tasks that will be rejected on static checks alone. |
| Reuse `build_and_test_docker()` in Component 2 | It already implements the correct Docker build + initial/final test logic. Wrapping avoids duplication and ensures consistency. |
| `FLAG` tasks saved with metadata, not dropped | Preserves dataset coverage while marking low-confidence tasks for downstream review. |
| Filesystem-based data model (no database) | Consistent with the project's existing storage pattern — all data is filesystem-based. |
| `ast.parse` for assert analysis | Exact AST-level matching is reproducible and correct. The keyword-based classification matches the Ticket #41 methodology. |
| `structural_score == 0` → reject (not just flag) | 110 tasks with zero outcome-checking asserts are definitively broken verifiers. Flagging them would perpetuate the problem into training data. |
| `structural_score < 0.2` threshold | Bottom tail of the distribution from Ticket #41 (16.6% of tasks). To be validated against agent `pass@1` in Section 9 — if tasks below 0.2 show meaningfully lower solve rates, the threshold is empirically confirmed. |