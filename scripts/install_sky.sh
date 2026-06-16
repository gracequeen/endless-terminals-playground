#!/bin/bash
set -e

if [ ! -d "SkyRL" ]; then
  git clone https://github.com/novasky-ai/SkyRL.git
fi

python3.12 -m venv /tmp/sky
source /tmp/sky/bin/activate

pip install torch --index-url https://download.pytorch.org/whl/cu126
pip install packaging wheel
sed -i 's/vllm==0.20.2/vllm==0.21.0/g' SkyRL/pyproject.toml
sed -i '/flashinfer-jit-cache/d' SkyRL/pyproject.toml
sed -i '/causal.conv1d/d' SkyRL/pyproject.toml

pip install -e "SkyRL[fsdp]" --no-build-isolation
pip install "ray[default]==2.51.1"
pip install -e .

cd SkyRL
git apply ../scripts/skyrl_patches.patch || echo "Patch already applied or not needed, skipping."
cd ..

echo "Done. Activate with: source /tmp/sky/bin/activate"
