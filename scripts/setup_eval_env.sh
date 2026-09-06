#!/bin/bash
# One-shot eval environment setup: CUDA, ninja, Docker Compose v2, harbor, uv deps.
# Safe to re-run — all steps are idempotent.
set -e

cd "$(dirname "$0")/.."

# 1. CUDA symlink so vLLM/flashinfer JIT can find nvcc
if [ ! -e /usr/local/cuda ]; then
  if [ -d /opt/pytorch/cuda ] && [ -f /opt/pytorch/cuda/bin/nvcc ]; then
    sudo ln -sf /opt/pytorch/cuda /usr/local/cuda
    echo "Symlinked /usr/local/cuda -> /opt/pytorch/cuda"
  else
    echo "WARNING: /opt/pytorch/cuda not found — set CUDA_HOME manually"
  fi
else
  echo "CUDA symlink OK: $(readlink -f /usr/local/cuda)"
fi

# 2. ninja in PATH (required by flashinfer JIT)
if ! command -v ninja &>/dev/null; then
  if [ -f /opt/pytorch/bin/ninja ]; then
    mkdir -p "$HOME/.local/bin"
    ln -sf /opt/pytorch/bin/ninja "$HOME/.local/bin/ninja"
    echo "Symlinked ninja into ~/.local/bin"
  else
    echo "WARNING: ninja not found at /opt/pytorch/bin/ninja"
  fi
else
  echo "ninja OK: $(which ninja)"
fi

# 3. Docker Compose v2
if ! docker compose version &>/dev/null 2>&1; then
  echo "Installing Docker Compose v2..."
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -SL https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-linux-x86_64 \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  echo "Docker Compose installed: $(docker compose version)"
else
  echo "Docker Compose OK: $(docker compose version)"
fi

# 4. uv deps (harbor extra)
if command -v uv &>/dev/null; then
  echo "Running uv sync --extra harbor..."
  uv sync --extra harbor
else
  echo "WARNING: uv not found — skipping dependency sync"
fi

# 5. harbor CLI in PATH
if ! command -v harbor &>/dev/null; then
  if [ -f ".venv/bin/harbor" ]; then
    echo "harbor is in .venv/bin — activate venv or use .venv/bin/harbor directly"
  else
    echo "Installing harbor via uv tool..."
    uv tool install harbor
  fi
else
  echo "harbor OK: $(which harbor)"
fi

echo ""
echo "Setup complete. To use harbor:"
echo "  source .venv/bin/activate"
echo "  harbor run ..."
