# User-Defined Category Generation — Design

## Context

The existing pipeline (`generate_tasks.py`) accepts `--num-tasks`, `--model`, and difficulty flags. 
Task categories come from a hardcoded list (`TASK_CATEGORIES` in `generator/task_template_gen.py`) 
and are sampled randomly at generation time. `generate_templates_batch()` already accepts optional 
`categories` and `difficulties` lists — the infrastructure is there; what's missing is the input 
layer that builds those lists from a user request.

---

## System Overview

```
User natural-language query & a set of instructions for testing
        │
        ▼
┌─────────────────────┐
│  Query → Config     │  (LLM call, structured output)
│  query_to_config.py │
└────────┬────────────┘
         │  generation_config.json
         ▼
┌─────────────────────┐
│  Config Validator   │  (schema check, coverage warnings)
│                     │
└────────┬────────────┘
         │  validated config
         ▼
┌─────────────────────┐
│  Pipeline           │  generate_tasks.py (existing)
│  generate_tasks.py  │  now reads config instead of CLI flags
└────────┬────────────┘
         │  task output dirs
         ▼
┌─────────────────────┐
│  Stats + Report     │  distribution_report.py
│                     │  – actual vs. requested breakdown
│                     │  – zero-hit categories flagged
└────────┬────────────┘
         │
         ▼
   Satisfaction check
   (user reviews report,
    confirms or re-queries)
```

---

## Config Schema (`generation_config.json`)

**More freestyle, suggesting but not inforcing templates**

```json
{
  "categories": [
    {
      "name": "git repository operations",
      "weight": 0.4
    },
    {
      "name": "container management",
      "weight": 0.4
    },
    {
      "name": "shell scripting automation",
      "weight": 0.2
    }
  ],
  "difficulty_distribution": {
    "easy":   0.2,
    "medium": 0.5,
    "hard":   0.3
  },
  "num_tasks": 100,
  "model": "gpt-4o"
}
```

**Rules:**
- `categories[*].name` must match an entry in `TASK_CATEGORIES`, OR be a free-form string 
  (treated as a new domain hint injected into `random_user_msg`).
- `categories[*].weight` is relative — normalized to sum to 1.0 at runtime.
- `difficulty_distribution` keys: `easy`, `medium`, `hard`. Missing keys default to 0.
- If `categories` is omitted, behavior falls back to the existing random sampling.

---

## Component 1: Query → Config (`query_to_config.py`)

**Input:** natural-language string, more freestyle request query. 

**Output:** `generation_config.json` written to disk (path configurable).

**Approach:**
- Single LLM call with a system prompt that instructs the model to produce JSON matching the schema above.
- The system prompt includes the full `TASK_CATEGORIES` list so the model can match user intent to known categories.
- Use structured output / JSON mode if available on the chosen model.
- If the model proposes categories not in `TASK_CATEGORIES`, keep them as free-form hints — the validator flags them as unrecognized but doesn't reject them.


---

## Component 2: Config Validator

Runs immediately after `query_to_config.py` before any generation starts.
**User have the full control to edit config and validating results.**

**Checks:**
1. All category names are recognized (warn if not, don't block).
2. Weights sum > 0.
3. `num_tasks` > 0.
4. Difficulty distribution sums to ≤ 1.0.

**Output:** prints warnings inline; returns `(valid: bool, warnings: list[str])`.

This is a pre-flight check — cheap, catches bad configs before any LLM generation budget is spent.

---

## Component 3: Pipeline Integration

`generate_tasks.py` gains a `--config` flag:

```
python generate_tasks.py --config generation_config.json
```

When `--config` is provided:
- `num_tasks`, `model`, difficulty are read from the config (CLI flags can still override).
- `categories` list passed to `generate_templates_batch()` is built by sampling from `config.categories` 
  according to their normalized weights.
- `difficulties` list built from `config.difficulty_distribution` using the existing `pick_difficulties()`.

No other changes to the existing pipeline. The config is purely an input-shaping layer.

---

## Component 4: Stats & Distribution Report (`distribution_report.py`)

Runs once after a generation round completes. Reads the output task directories.

**Computes:**
- Requested distribution (from config): `{category: expected_count}`
- Actual distribution (from generated `task.json` files): `{category: actual_count}`
- Delta per category: actual − expected
- Zero-hit categories: requested > 0, actual = 0
- Overall success rate: tasks generated / tasks requested

**Output:** a plain-text + JSON report, e.g.:

```
Generation Report
=================
Requested: 100 tasks
Generated: 87 tasks  (87% success rate)

Category Distribution:
  container management     requested 40  actual 34  delta -6
  git repository ops       requested 40  actual 35  delta -5
  shell scripting          requested 20  actual 18  delta -2

Difficulty Distribution:
  easy    requested 20  actual 17
  medium  requested 50  actual 44
  hard    requested 30  actual 26

Zero-hit categories: none

Tests: PASS  (all categories within 15% of target)
```

**Coverage tests** (referenced in the design goal):
- Assert each requested category has `actual >= expected * 0.7` (configurable threshold).
- Assert overall success rate >= 0.8.
- Tests written as standard pytest assertions in `tests/test_distribution.py`, 
  parameterized from the report JSON.

---

## Iteration Flow

```
user query
    │
    ▼
query_to_config → config.json
    │
    ▼
validator  ──── warnings? ──── shown to user, proceed or edit
    │
    ▼
generate_tasks (pipeline)
    │
    ▼
distribution_report
    │
    ├── tests PASS + user satisfied → done
    │
    └── tests FAIL or user unsatisfied
            │
            ▼
        user provides updated query  (or edits config.json directly)
            │
            ▼
        query_to_config → new config.json  →  repeat
```

The iteration loop is explicit and user-driven. There is no automatic re-run — the report 
gives the user enough information to decide whether to re-query, adjust weights manually, 
or accept partial results.

---

## What's Not in Scope

- **UI integration for config input** — the query is submitted via CLI. The existing Flask UI 
  (`app/server.py`) already filters by `category` and `difficulty`; the stats view can be 
  a separate endpoint added later.
- **Automatic config suggestion** — no "here's what you'll get before running" preview. 
  The validator warnings serve this role cheaply.


## Targeted Areas

- Enterprise databse operations (SAP CAP tasks) (20-50 eval, start with 5-10)
