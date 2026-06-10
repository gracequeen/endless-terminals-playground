# Harbor Task Boilerplate Generation Workflow

## Source Inputs

- `app-generation-gateway-main/` — repo snapshot at `main` (code, tests, schema, docs)
- `without_cds_q/all_prs.json` — 27 PRs in SWE-bench format, each with `problem_statement`, `patch`, `test_patch`, `non_test_patch`, `base_commit`, `has_js_test`, size metrics

## Step 1 — Understand the repo

Read the codebase: CDS schema, service definitions, key library modules (`event-proxy.js`, `preview-proxy.js`, `partner-url.ts`, `service-token.js`, `audit.js`), `package.json` test scripts, and architecture docs. This gave a working understanding of the domain, module responsibilities, and what a "fix" in this repo looks like.

## Step 2 — Select candidates

From the 27 PRs, filtered to those with `has_js_test=True` (16 PRs) — these have an existing `test_patch` that can eventually drive `FAIL_TO_PASS` without needing LLM-generated checks. From those, picked 5 PRs spanning a difficulty range based on `num_files_changed` and `num_additions`:

| Task | PR | Files changed | Difficulty |
|---|---|---|---|
| `task_cap_e1_trust_proxy` | #24 | 2 | easy |
| `task_cap_e2_remove_dead_code` | #17 | 8 | easy |
| `task_cap_m1_event_proxy_fallback` | #33 | 4 | medium |
| `task_cap_m2_event_proxy_destination` | #29 | 5 | medium |
| `task_cap_h1_preview_proxy` | #20 | 17 | hard |

## Step 3 — Craft instructions

For each PR, the `problem_statement` was the raw PR body. Cleaned it by: stripping implementation-describing sections ("Architecture Changes", "New REST API Endpoints", etc.), removing the solution framing, keeping only the "what is broken / what is needed" part. Cross-referenced with the actual source files to verify the described behavior existed and the fix location was accurate.

## Step 4 — Write boilerplates

Each task directory was created with 7 files:

- `task.toml` — difficulty, tags, `instance_id`, `base_commit`, `check_origin`, resource limits
- `instruction.md` — cleaned problem statement + verify command (`npm run test:unit`)
- `environment/Dockerfile` — stub based on `node:20-slim`; notes that `test_patch` must be applied and `non_test_patch` must not be
- `environment/task.json` — description + empty `fail_to_pass`/`pass_to_pass` arrays
- `environment/test_initial_state.py` — checks repo exists, `node_modules` installed, and unit tests fail (pre-fix state)
- `tests/test.sh` — generic: installs uv, runs pytest on `test_final_state.py`, writes `reward.txt`
- `tests/test_final_state.py` — task-specific structural assertions (e.g. `grep` for `trust proxy`, check dead files removed, check `executeHttpRequest` present) plus a generic `npm run test:unit` pass check

## What Remains Stubbed

`FAIL_TO_PASS`/`PASS_TO_PASS` in `task.json` are empty — they require git history to check out `base_commit`, apply `test_patch`, run tests to collect failing IDs, then repeat on the merge commit for passing IDs. The `augment_cap_fail_to_pass.py` script handles this once history is scraped. The Dockerfiles also reference a `TODO` for the actual repo snapshot at `base_commit` rather than `main`.
