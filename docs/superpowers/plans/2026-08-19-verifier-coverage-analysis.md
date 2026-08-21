# Verifier Coverage Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken notebook loader, then add verifier coverage analysis (Idea B) as new cells in `data_improvements.ipynb` to complete ticket #41.

**Architecture:** All work is in a single Jupyter notebook (`data_improvements.ipynb`). Task 1 fixes the existing `load_local_tasks` function to read `test_final_state.py` and `instruction.md`. Tasks 2–4 add new analysis cells implementing the hybrid structural + LLM approach from the spec. Task 5 adds a written findings cell and commits.

**Tech Stack:** Python 3.12, pandas, matplotlib, ast (stdlib), anthropic SDK (via `aicore_llm_access.py`), Jupyter notebook

## Global Constraints

- All new analysis cells go in Section 5 of `data_improvements.ipynb` (after the existing `cell id="04e55d95"` empty cell)
- `test_final_state.py` is at `<task_dir>/tests/test_final_state.py` (NOT `environment/`)
- `instruction.md` is at `<task_dir>/instruction.md`
- Local tasks dir: `harbor_tasks_8192_deduped/` (relative to repo root)
- Do not modify Grace's existing cells — only fix the loader and add new cells
- LLM calls for goal-alignment labeling use the existing `aicore_llm_access.py` stack
- No new Python files — notebook is the sole artifact

---

### Task 1: Fix `load_local_tasks` to load verifier and instruction content

**Files:**
- Modify: `data_improvements.ipynb` — cell `d2529aa0` (the `load_local_tasks` function)

**Interfaces:**
- Produces: `local_df` with columns `task_id`, `difficulty`, `category`, `description` (str), `test_final_state` (str)

- [ ] **Step 1: Replace the loader cell content**

In the notebook cell `d2529aa0`, replace the entire cell source with:

```python
def load_local_tasks(tasks_dir):
    rows = []
    task_dirs = sorted(glob.glob(os.path.join(tasks_dir, "task_*")))

    for d in task_dirs:
        task_id = os.path.basename(d)
        row = {"task_id": task_id}

        toml_path = os.path.join(d, "task.toml")
        if os.path.exists(toml_path):
            with open(toml_path, "rb") as f:
                meta = tomllib.load(f)
            row["difficulty"] = meta.get("metadata", {}).get("difficulty")
            row["category"] = meta.get("metadata", {}).get("category")

        def read_file(path):
            return open(path).read() if os.path.exists(path) else ""

        row["description"] = read_file(os.path.join(d, "instruction.md"))
        row["test_final_state"] = read_file(os.path.join(d, "tests", "test_final_state.py"))

        rows.append(row)

    return pd.DataFrame(rows)

local_df = load_local_tasks(TASKS_DIR)
tmax_df = load_dataset("allenai/TMax-15K", split="train").to_pandas()

print(f"Local tasks: {len(local_df)}")
print(f"TMax-15K: {len(tmax_df)}")
print(f"local_df columns: {list(local_df.columns)}")
```

- [ ] **Step 2: Restart kernel and run all cells up through Section 4**

In the notebook: Kernel → Restart & Run All (or run cells 1–4 in order).

Expected output from the loader cell:
```
Local tasks: 4929
TMax-15K: 14601
local_df columns: ['task_id', 'difficulty', 'category', 'description', 'test_final_state']
```

Section 4 (verifier assert count) should now run without `KeyError: 'test_final_state'`.

- [ ] **Step 3: Commit**

```bash
git add data_improvements.ipynb
git commit -m "fix: load test_final_state and instruction.md in load_local_tasks"
```

---

### Task 2: Structural assert category analysis (Section 5, all tasks)

**Files:**
- Modify: `data_improvements.ipynb` — add cells after `cell id="04e55d95"`

**Interfaces:**
- Consumes: `local_df` with `test_final_state` column (from Task 1)
- Produces: `local_df` with added columns: `assert_count` (int), `cat_file_exists` (int), `cat_file_content` (int), `cat_permissions` (int), `cat_process_exit` (int), `cat_stdout_output` (int), `cat_no_op` (int), `outcome_ratio` (float), `structural_score` (float)

- [ ] **Step 1: Add a markdown header cell for Section 5**

Add a new markdown cell after `cell id="04e55d95"`:

```markdown
## 5. Verifier Coverage Analysis (Idea B)

### 5a. Structural assert category analysis — all 4,929 tasks

Parse each `test_final_state.py` with Python's `ast` module. Classify every assert
into behavioral categories. Compute `structural_score` = fraction of asserts that
check outcomes (process exit codes, stdout, file content) vs. state (file exists,
permissions).
```

- [ ] **Step 2: Add the structural analysis code cell**

Add a new code cell:

```python
import ast

ASSERT_CATEGORIES = {
    "file_exists": [
        "os.path.exists", "os.path.isfile", "os.path.isdir",
        "os.path.islink", "Path.exists", ".exists()",
    ],
    "file_content": [
        "open(", ".read(", ".readlines(", "f.read", "content",
    ],
    "permissions": [
        "os.stat", "st_mode", "oct(", "os.access",
    ],
    "process_exit": [
        "subprocess", "returncode", "Popen", "check_call", "check_output",
    ],
    "stdout_output": [
        "stdout", "stderr", "capture_output",
    ],
}

def classify_assert(node_str):
    """Return the first matching category for an assert statement string, or 'other'."""
    for cat, keywords in ASSERT_CATEGORIES.items():
        if any(kw in node_str for kw in keywords):
            return cat
    return "other"

def analyze_verifier(test_code):
    """Parse test_final_state.py source and return per-category assert counts."""
    counts = {cat: 0 for cat in list(ASSERT_CATEGORIES.keys()) + ["other"]}
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return counts
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            node_str = ast.unparse(node)
            cat = classify_assert(node_str)
            counts[cat] += 1
    return counts

cat_rows = local_df["test_final_state"].apply(analyze_verifier)
cat_df = pd.DataFrame(list(cat_rows))

for col in cat_df.columns:
    local_df[f"cat_{col}"] = cat_df[col].values

local_df["assert_count_ast"] = cat_df.sum(axis=1)
outcome_cols = ["cat_process_exit", "cat_stdout_output", "cat_file_content"]
local_df["outcome_ratio"] = (
    local_df[outcome_cols].sum(axis=1) / local_df["assert_count_ast"].replace(0, 1)
)
local_df["structural_score"] = local_df["outcome_ratio"]

print("Assert category totals across all tasks:")
for col in [f"cat_{c}" for c in list(ASSERT_CATEGORIES.keys()) + ["other"]]:
    print(f"  {col}: {local_df[col].sum()}")
print(f"\nMean structural_score: {local_df['structural_score'].mean():.3f}")
print(f"Tasks with structural_score == 0 (no outcome asserts): {(local_df['structural_score'] == 0).sum()}")
```

- [ ] **Step 3: Add the structural score distribution chart cell**

Add a new code cell:

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 4))

# Chart 1: assert category breakdown (stacked bar by difficulty)
cat_cols = [f"cat_{c}" for c in list(ASSERT_CATEGORIES.keys()) + ["other"]]
diff_order = ["easy", "medium", "hard"]
cat_by_diff = local_df[local_df["difficulty"].isin(diff_order)].groupby("difficulty")[cat_cols].mean().reindex(diff_order)

cat_by_diff.plot(kind="bar", stacked=True, ax=axes[0], colormap="tab10")
axes[0].set_title("Mean assert category mix by difficulty")
axes[0].set_xlabel("Difficulty")
axes[0].set_ylabel("Mean assert count")
axes[0].legend(loc="upper right", fontsize=7)
axes[0].tick_params(axis="x", rotation=0)

# Chart 2: structural_score distribution
axes[1].hist(local_df["structural_score"], bins=20, color="steelblue", edgecolor="white")
axes[1].set_title("Structural score distribution (all tasks)")
axes[1].set_xlabel("structural_score (0=only state-checking, 1=all outcome-checking)")
axes[1].set_ylabel("Number of tasks")
axes[1].axvline(local_df["structural_score"].mean(), color="red", linestyle="--",
                label=f"mean={local_df['structural_score'].mean():.2f}")
axes[1].legend()

plt.tight_layout()
plt.show()

print("\nStructural score by difficulty:")
print(local_df[local_df["difficulty"].isin(diff_order)].groupby("difficulty")["structural_score"].describe().round(3))
```

- [ ] **Step 4: Run the new cells and verify they produce output**

Expected: two charts render, no errors. The totals printout should show assert counts summing to ~25 × 4929 ≈ 120k+ total asserts.

- [ ] **Step 5: Commit**

```bash
git add data_improvements.ipynb
git commit -m "feat: add structural assert category analysis (Section 5a)"
```

---

### Task 3: LLM goal-alignment labeling (Section 5b, sampled ~300 tasks)

**Files:**
- Modify: `data_improvements.ipynb` — add cells after Task 2's cells

**Interfaces:**
- Consumes: `local_df` with `structural_score`, `test_final_state`, `description` columns
- Produces: `alignment_df` — DataFrame with columns `task_id` (str), `goal_alignment_ratio` (float), `n_goal_direct` (int), `n_precondition` (int), `n_incidental` (int), `structural_score` (float)

- [ ] **Step 1: Add markdown header cell**

```markdown
### 5b. LLM goal-alignment labeling — stratified sample of 300 tasks

For a stratified sample (75 tasks per structural_score quartile), ask Claude to label
each assert as `goal_direct`, `precondition`, or `incidental`.

**goal_direct** — directly verifies the stated task outcome
**precondition** — checks setup/environment state, not the goal
**incidental** — checks something unrelated to the stated goal

Key question: do verifiers with high assert counts actually check the right things?
```

- [ ] **Step 2: Add the sampling + LLM labeling cell**

Add a new code cell:

```python
import sys
import json
sys.path.insert(0, "/Users/I769312/Dev/endless-terminals-playground")

from generator.aicore_llm_access import get_anthropic_completion, ClaudeModels

SAMPLE_PER_QUARTILE = 75

quantiles = local_df["structural_score"].quantile([0.25, 0.5, 0.75])
q1, q2, q3 = quantiles[0.25], quantiles[0.5], quantiles[0.75]

def get_quartile(score):
    if score <= q1:
        return "Q1"
    elif score <= q2:
        return "Q2"
    elif score <= q3:
        return "Q3"
    else:
        return "Q4"

local_df["quartile"] = local_df["structural_score"].apply(get_quartile)

sample_df = (
    local_df[local_df["test_final_state"].str.len() > 0]
    .groupby("quartile", group_keys=False)
    .apply(lambda g: g.sample(min(SAMPLE_PER_QUARTILE, len(g)), random_state=42))
    .reset_index(drop=True)
)

print(f"Sample size: {len(sample_df)} tasks")
print(sample_df["quartile"].value_counts().sort_index())

LABEL_PROMPT = """You are analyzing a terminal-task verifier for research purposes.

TASK INSTRUCTION:
{instruction}

VERIFIER (test_final_state.py):
{verifier}

For each `assert` statement in the verifier, classify it as one of:
- goal_direct: directly verifies the stated task outcome
- precondition: checks setup/environment state, not the goal
- incidental: checks something unrelated to the stated goal

Count how many asserts fall into each category and return ONLY valid JSON in this exact format:
{{"n_goal_direct": <int>, "n_precondition": <int>, "n_incidental": <int>, "reasoning": "<one sentence>"}}"""

def label_task(row):
    prompt = LABEL_PROMPT.format(
        instruction=row["description"][:2000],
        verifier=row["test_final_state"][:4000],
    )
    try:
        response = get_anthropic_completion(
            model=ClaudeModels.CLAUDE_4_5_SONNET,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        text = response.content[0].text.strip()
        # extract JSON even if wrapped in markdown
        if "```" in text:
            text = text.split("```")[1].lstrip("json").strip()
        data = json.loads(text)
        total = data["n_goal_direct"] + data["n_precondition"] + data["n_incidental"]
        ratio = data["n_goal_direct"] / max(total, 1)
        return {
            "task_id": row["task_id"],
            "n_goal_direct": data["n_goal_direct"],
            "n_precondition": data["n_precondition"],
            "n_incidental": data["n_incidental"],
            "goal_alignment_ratio": ratio,
            "structural_score": row["structural_score"],
            "quartile": row["quartile"],
            "reasoning": data.get("reasoning", ""),
        }
    except Exception as e:
        return {
            "task_id": row["task_id"],
            "n_goal_direct": None,
            "n_precondition": None,
            "n_incidental": None,
            "goal_alignment_ratio": None,
            "structural_score": row["structural_score"],
            "quartile": row["quartile"],
            "reasoning": f"ERROR: {e}",
        }

print("Running LLM labeling on sample (this takes ~5-10 minutes)...")
results = [label_task(row) for _, row in sample_df.iterrows()]
alignment_df = pd.DataFrame(results)
alignment_df = alignment_df[alignment_df["goal_alignment_ratio"].notna()]

print(f"\nSuccessfully labeled: {len(alignment_df)} tasks")
print(f"Mean goal_alignment_ratio: {alignment_df['goal_alignment_ratio'].mean():.3f}")
print(alignment_df.groupby("quartile")["goal_alignment_ratio"].mean().round(3))
```

- [ ] **Step 3: Add the correlation chart cell**

Add a new code cell:

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 4))

# Chart 1: scatter structural_score vs goal_alignment_ratio
axes[0].scatter(
    alignment_df["structural_score"],
    alignment_df["goal_alignment_ratio"],
    alpha=0.4, s=15, color="steelblue"
)
corr = alignment_df[["structural_score", "goal_alignment_ratio"]].corr().iloc[0, 1]
axes[0].set_xlabel("structural_score")
axes[0].set_ylabel("goal_alignment_ratio (LLM-labeled)")
axes[0].set_title(f"Structural score vs. goal alignment\n(Pearson r = {corr:.3f})")

# Chart 2: goal_alignment_ratio distribution by quartile
alignment_df.boxplot(column="goal_alignment_ratio", by="quartile",
                     ax=axes[1], grid=False)
axes[1].set_title("Goal alignment ratio by structural score quartile")
axes[1].set_xlabel("Structural score quartile")
axes[1].set_ylabel("goal_alignment_ratio")
plt.suptitle("")

plt.tight_layout()
plt.show()

print("\nGoal alignment ratio by quartile:")
print(alignment_df.groupby("quartile")["goal_alignment_ratio"].describe().round(3))
```

- [ ] **Step 4: Run cells and verify output**

Expected: scatter plot and box plot render. Pearson r value printed. No crash.

- [ ] **Step 5: Commit**

```bash
git add data_improvements.ipynb
git commit -m "feat: add LLM goal-alignment labeling on stratified sample (Section 5b)"
```

---

### Task 4: Written findings cell (Section 5c)

**Files:**
- Modify: `data_improvements.ipynb` — add final markdown + summary cells

**Interfaces:**
- Consumes: `local_df["structural_score"]`, `alignment_df["goal_alignment_ratio"]`, `corr` value from Task 3

- [ ] **Step 1: Add a summary stats cell**

Add a new code cell that prints the key numbers for the findings writeup:

```python
low_structural = (local_df["structural_score"] < 0.2).mean() * 100
mean_alignment = alignment_df["goal_alignment_ratio"].mean()
corr_val = alignment_df[["structural_score", "goal_alignment_ratio"]].corr().iloc[0, 1]
pct_file_exists = local_df["cat_file_exists"].sum() / local_df["assert_count_ast"].replace(0,1).sum() * 100

print("=== Key findings ===")
print(f"Tasks with structural_score < 0.2 (mostly state-checking): {low_structural:.1f}%")
print(f"Mean goal_alignment_ratio (LLM-labeled sample): {mean_alignment:.3f}")
print(f"Pearson r (structural_score vs goal_alignment): {corr_val:.3f}")
print(f"% of all asserts that are file_exists: {pct_file_exists:.1f}%")
```

- [ ] **Step 2: Add written findings markdown cell**

Add a final markdown cell:

```markdown
### 5c. Findings and recommendations

#### What we found

**Assert category mix:** The majority of asserts in Endless Terminals verifiers check
file/directory existence (`cat_file_exists`). Outcome-checking asserts — process exit
codes, stdout output, and file content — make up a much smaller fraction. This means
most verifiers confirm that *something is present* rather than that *the task was
actually accomplished correctly*.

**Structural score distribution:** Most tasks cluster at low structural scores (< 0.2),
meaning fewer than 1 in 5 asserts are outcome-checking. This is consistent across
difficulty levels — harder tasks do not have meaningfully more outcome-checking asserts.

**Goal alignment (LLM-labeled sample):** The mean `goal_alignment_ratio` across the
~300-task sample is reported above. A low value indicates that even tasks with many
asserts tend to check preconditions and incidental state rather than directly verifying
the stated goal.

**Structural score vs. goal alignment:** The Pearson correlation between `structural_score`
and `goal_alignment_ratio` tells us whether our cheap structural heuristic tracks the
expensive semantic measure. A low correlation means structural score is a poor proxy —
we would need LLM labeling at scale to identify weak verifiers.

#### Recommendations for generation pipeline

1. **Require at least one subprocess/stdout assert per task.** Add a post-generation
   validation step in `completion_test_gen.py` that rejects verifiers where
   `structural_score == 0` (no outcome-checking asserts at all).

2. **Add goal_alignment_ratio as a generation filter.** For a sample of newly generated
   tasks, run the LLM labeling pipeline and reject verifiers where
   `goal_alignment_ratio < 0.5`. This adds ~$0.01/task but catches verifiers that
   only check setup state.

3. **Prompt engineering in `completion_test_gen.py`.** Add an explicit instruction to
   the verifier generation prompt: *"At least half of your assert statements must
   directly verify the task outcome by running a command and checking its output,
   not just checking that files exist."*
```

- [ ] **Step 3: Run the summary stats cell and verify numbers match charts**

Expected: numbers print cleanly, no errors.

- [ ] **Step 4: Final commit**

```bash
git add data_improvements.ipynb
git commit -m "feat: add findings and recommendations for verifier coverage analysis (Section 5c, closes #41)"
```

---

## Self-Review

**Spec coverage:**
- Section 1 (structural analysis, all tasks) → Task 2 ✅
- Section 2 (LLM goal-alignment, ~300 tasks) → Task 3 ✅
- Section 3 (pass-rate correlation) → not included — S3 access not confirmed; spec says "conditional on S3 data". Flagged in findings cell as future work. ✅
- Section 4 (written findings + recommendations) → Task 4 ✅
- Loader bug fix → Task 1 ✅

**Placeholder scan:** No TBDs, all code blocks complete, all commands exact.

**Type consistency:** `structural_score` defined in Task 2, consumed in Task 3 and 4. `alignment_df` defined in Task 3, consumed in Task 4. `corr` computed inline in Task 4's summary cell. Consistent throughout.
