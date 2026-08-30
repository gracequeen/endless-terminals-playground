# Endless Terminals

**Scaling RL Environments for Terminal Agents**

[![Paper](https://img.shields.io/badge/Paper-arXiv-red)](https://arxiv.org/abs/2601.16443)
[![Dataset](https://img.shields.io/badge/Dataset-HuggingFace-yellow)](https://huggingface.co/collections/obiwan96/endless-terminals)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Endless Terminals is a fully autonomous pipeline that procedurally generates terminal-use tasks without human annotation for training terminal agents with reinforcement learning.

## Installation

**Prerequisites:** Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
# Install Apptainer
./scripts/install_apptainer.sh

# Install dependencies
uv sync

# Download base container
./scripts/get_ubuntu_sif.sh
```

## Task Generation

Start a vLLM server locally before running task generation:

```bash
./scripts/launch_vllm_server.sh
```

Then generate tasks:

```bash
python generate_tasks.py --num-tasks 100 --out-dir ./tasks --model Qwen/Qwen3-32B --jobs 8
```

Each task generates: `task.json`, `test_initial_state.py`, `test_final_state.py`, `container.def`, and `container.sif`.

## Running Solutions

```bash
python generate_solutions.py --tasks-dir ./tasks --num-solutions 16 --model Qwen/Qwen3-32B
```

## Training

```bash
# Prepare dataset
python train/prepare_endless.py --task-dir ./tasks --output-dir ./data --build-sif

# Install SkyRL
./scripts/install_sky.sh

# Run training
ray start --head
python train/main_endless.py --config-dir train/confs --config-name base
```

Configs: `base.yaml` (Llama-3.2-3B), `base_qwen.yaml` (Qwen2.5-7B), `base_qwen3_otak8.yaml` (Qwen3-8B)

## Evaluation with Harbor

```bash
# Install Harbor
./scripts/setup.sh

# Run evaluation
./scripts/parallel_harbor.sh --model path/to/model --parallel 8
```

### Baseline Evaluation (local vLLM models)

`evaluate_baseline.py` measures how well a locally vLLM-served model (e.g. a Qwen
checkpoint) solves a set of Harbor tasks *before* any RL training — the baseline.
It runs the `EndlessAgent` against each task `--n-attempts` times via `harbor run`,
reads each trial's reward, and reports **pass@k** per task and in aggregate.

**Prerequisites:** a running vLLM server for the model, and Docker.

```bash
# 1. Serve the model with vLLM (one GPU shown; note the port):
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3.5-9B --port 8006 &

# 2. Run the baseline eval (n=8 attempts → pass@1,2,3,4,8):
.venv/bin/python evaluate_baseline.py \
    --dataset-path harbor_tasks_top200 \
    --model Qwen/Qwen3.5-9B \
    --n-attempts 8 \
    --n-concurrent 3 \
    --jobs-dir baseline_results \
    --job-name passk_eval_top200_9b \
    --vllm-base-url http://localhost:8006/v1
```

Results are written to `output/<job-name>.{json,md}` (aggregate + per-task pass@k)
and raw trials to `baseline_results/<job-name>/`. Use `--dry-run` to print the
`harbor run` command without executing.

**pass@k.** With `--n-attempts N`, pass@k is defined only for `k ≤ N` (unbiased
estimator, Chen et al. 2021). The default reported set is `k = 1, 2, 3, 4, 8`, so
use `--n-attempts 8` to make all five valid — pass@8 needs `N ≥ 8`. Override with
`--pass-at-k K` (repeatable).

**Why `--n-concurrent 3`.** Each Harbor trial creates its own Docker bridge
network and holds it for the trial's entire lifetime (image build → agent episodes
→ verification). A stock Docker daemon (no `default-address-pools` in
`/etc/docker/daemon.json`) can allocate only **~31 networks at once**. Networks are
freed when a trial finishes, so the constraint is on *simultaneously live* trials,
not the total. At `--n-concurrent 3` the live-network count peaks around 3–9 — a
wide margin under the ceiling. Pushing concurrency higher (peak ~18 was where
address-pool exhaustion first appeared in practice) starves new trials of networks
and they fail environment setup. Note that `docker network prune` does **not** help
here: during a run the networks are all in-use, so there is nothing idle to reclaim
— keeping concurrency low is the fix. For a large run (e.g. 200 tasks × 8 = 1600
trials) prefer 3; raise it only after adding a wider `default-address-pools` and
restarting the daemon.

> **Running several evals at once?** The ~31-network ceiling is a single
> *host-wide* Docker daemon limit — it is **not** per-GPU or per-process. Two
> baseline evals on different GPUs still draw bridge networks from the same pool,
> so their `--n-concurrent` values **add up** against the same ceiling. Budget
> accordingly (e.g. 3 + 3).

## Citation

```bibtex
@article{gandhi2025endless,
    title={Endless Terminals: Scaling RL Environments for Terminal Agents},
    author={Gandhi, Kanishk and Garg, Shivam and Goodman, Noah D. and Papailiopoulos, Dimitris},
    journal={arXiv preprint arXiv:2601.16443},
    year={2025}
}
```

## Harbor Task Generation

The pipeline can generate tasks in [Harbor](https://www.harborframework.com/) format, using Claude Opus 4.5 as the LLM backend instead of a local vLLM server.

**Prerequisites:** Docker, access to AICore Claude API (configured via `aicore_llm_access.py`)

The AICore integration is split across three modules:

- **`aicore_llm_access.py`** — Model registry and low-level completion function. Defines a `get_anthropic_completion()` helper used by the task and solution generators.
- **`aicore_llm.py`** — Harbor-compatible LLM backend. Implements Harbor's `BaseLLM` interface (`AICoreAnthropicLLM`) so that Harbor agents can call Claude through AICore's Bedrock-compatible API instead of LiteLLM.
- **`aicore_agent.py`** — Custom Harbor agent. Subclasses Harbor's `Terminus2` agent and swaps in `AICoreAnthropicLLM` as the LLM backend, for use with `harbor run --agent-import-path aicore_agent:AICoreTerminus2`.

### I. Generating Tasks

Modify choices of arguments:
- num-tasks: total number of tasks to be generated
- out-dir: for tasks storage
- model: choice of generation model

```bash
python generate_harbor_tasks.py --num-tasks 10 --out-dir harbor_tasks --model claude_opus
```

For larger production runs (v3 spec):
```bash
# extra small test (64 tasks)
python generate_harbor_tasks.py \
  --num-tasks 64 --out-dir harbor_tasks_v3_small-test \
  --model claude_opus_4_8 --max-tokens 8192 \
  --difficulty mixed --difficulty-distribution easy:0.1,medium:0.4,hard:0.5 \
  --batch-size 64 --max-concurrency 32 --pipeline-depth 32 \
  --skip-build

# normal batch (5120 tasks)
python generate_harbor_tasks.py \
  --num-tasks 5120 --out-dir harbor_tasks_v3_normal \
  --model claude_opus_4_8 --max-tokens 8192 \
  --difficulty mixed --difficulty-distribution easy:0.1,medium:0.4,hard:0.5 \
  --batch-size 64 --max-concurrency 32 --pipeline-depth 32 \
  --skip-build
```

This runs a 5-stage pipeline:
1. **Task templates** — generates task descriptions and ground-truth solutions
2. **Initial-state tests** — generates pytest tests that verify the container starts in the correct state
3. **Final-state tests** — generates pytest tests that verify the task was completed correctly
4. **Dockerfiles** — generates Dockerfiles and optionally builds/tests them
5. **Save** — writes each task as a Harbor-compatible directory

Each task produces:

```
task_{id}_{hash}/
├── instruction.md              # Task prompt shown to the agent
├── task.toml                   # Harbor metadata (difficulty, timeouts, resources)
├── environment/
│   ├── Dockerfile              # Container environment definition
│   ├── task.json               # Task description + ground truth
│   └── test_initial_state.py   # Validates the initial container state
├── solution/
│   ├── solve.sh                # Reference solution script (if available)
│   └── solution.json           # Full solution attempt data
└── tests/
    ├── test.sh                 # Harbor verifier — runs pytest and writes reward
    └── test_final_state.py     # Validates task completion
```

`--skip-build` to skip Docker image building during generation, `--batch-size` to control how many are processed per LLM call.

### II. Generating Solutions

Modify choices of arguments:
- model: choice of generation model
- path: tasks folder path
- n-attempts: number of rollouts per task
- jobs-dir: folder path to store all solutions 
- n-concurrent: parallel processing in the number of CPU cores
- job-name: output subfolder for current job; MUST DELETE folder if already existing

```bash
harbor run --agent-import-path generator.aicore_agent:AICoreTerminus2 --model claude_4_6 --path harbor_tasks_v3_small-test --n-attempts 8 --jobs-dir solution_grace --n-concurrent 4 --job-name v3_small_test
```

For each task, this:
1. Builds the task's Docker image
2. Starts N containers (one per solution attempt)
3. Runs an agentic loop — the LLM reads the instruction, issues shell commands, and observes outputs
4. Runs the final-state tests inside each container
5. Saves `solution.json` (all attempts with message histories) and `solve.sh` (commands from the first passing attempt) to `solution/`

Tasks that already have a `solution/solution.json` are skipped automatically. Use `--workers` to process multiple tasks in parallel and `--max-actions` to cap the number of commands per attempt.

## Explorer UI

A small Flask app for browsing tasks, agent trajectories, and per-model
performance lives in `app/`:

```bash
uv run python -m app.server --port 5050
# then open http://127.0.0.1:5050
```

It reads `harbor_tasks/` and `solution_sonnet/` directly from disk and exposes:

- **Dashboard** — leaderboard across models, hardest/easiest tasks, recent runs
- **Runs** — per-task pass/fail heatmap, exception breakdown, token totals
- **Tasks** — searchable catalog with filters (difficulty / category / tag) and
  per-task detail (instruction, ground truth, Dockerfile, final-state test, and
  every trial across runs)
- **Trial viewer** — full agent trajectory (messages + tool calls + terminal
  observations), reward, tokens, durations, and an embedded asciinema player
  for the recorded session

## License

Apache License 2.0 - see [LICENSE](LICENSE).
