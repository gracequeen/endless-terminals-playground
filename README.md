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

## Citation

```bibtex
@article{gandhi2025endless,
    title={Endless Terminals: Scaling RL Environments for Terminal Agents},
    author={Gandhi, Kanishk and Garg, Shivam and Goodman, Noah D. and Papailiopoulos, Dimitris},
    journal={arXiv preprint arXiv:2601.16443},
    year={2025}
}
```

## License

Apache License 2.0 - see [LICENSE](LICENSE).
