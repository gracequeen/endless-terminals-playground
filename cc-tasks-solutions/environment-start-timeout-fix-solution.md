# Solution: environment-start-timeout-fix

## Problem

Tasks with heavy Dockerfile setup (e.g. seeding 500k rows into SQLite) exceed Harbor's
default 600s environment build timeout. All 8 trials fail with `EnvironmentStartTimeoutError`,
and zombie containers exhaust the Docker bridge network pool, blocking other trials.

## Changes Made

### `evaluate_baseline.py`

Added two constants:
```python
HEAVY_TASK_ISOLATION_TIMEOUT_SEC = 3600       # trigger isolation if build > 1hr
HEAVY_TASK_BUILD_TIMEOUT_MULTIPLIER = 12.0    # 12 × 600s = 7200s (2hrs)
```

Added new functions:

**`detect_heavy_tasks(dataset_path, jobs_dir, job_name) -> set[str]`**
- Scans prior trial dirs for `exception.txt` containing `EnvironmentStartTimeoutError`
- Returns the set of affected task names

**`split_dataset(dataset_path, heavy_task_names) -> (normal_dir, heavy_dir)`**
- Symlinks tasks into two temp subdirs: `normal/` and `heavy/`
- Returns `(dataset_path, None)` if no heavy tasks

**`run_harbor()` — updated isolation logic:**

On re-run (when a prior job dir exists with timeouts):
1. Calls `detect_heavy_tasks()` to find affected tasks
2. Checks CPU headroom: `(os.cpu_count() - multiprocessing.active_children()) >= 2`
3. **If headroom available:**
   - Splits dataset into normal + heavy dirs
   - Launches heavy job in a separate `multiprocessing.Process` with `n_concurrent=1`
     and `HEAVY_TASK_BUILD_TIMEOUT_MULTIPLIER` (12×, 2hrs)
   - Runs normal batch concurrently in main process
   - Waits for heavy job, then merges results back into main job dir via `shutil.copytree`
   - Cleans up temp dirs
4. **If no headroom:**
   - Logs a warning to stderr
   - Runs everything sequentially with extended timeout (2hrs)

Added CLI flag:
```
--environment-build-timeout-multiplier FLOAT
    Multiply the default 600s environment build timeout.
    E.g. 5.0 = 50 min. Used for known heavy-setup datasets.
```

## Behavior Summary

| Scenario | Behavior |
|----------|----------|
| First run, no prior results | Normal run, heavy tasks may timeout |
| Re-run, heavy tasks detected, CPU headroom | Heavy tasks isolated to separate process, n_concurrent=1, 2hr timeout |
| Re-run, heavy tasks detected, no CPU headroom | Warning logged, all tasks run with 2hr timeout sequentially |
| Manual override | `--environment-build-timeout-multiplier` flag |

## Affected Tasks in harbor_tasks_v3_test

3 tasks confirmed heavy:
- `task_000054_487e083a` — SQLite 500k-row seed
- `task_000086_d35c9498` — Git repo + Grafana JSON history
- `task_000160_6e6faca5` — Large JSONL audit log export

## Files Changed

- `evaluate_baseline.py` — isolation logic, CLI flag, imports (`multiprocessing`, `os`, `shutil`, `tempfile`, `logging`)
