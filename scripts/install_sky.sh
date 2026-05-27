#!/bin/bash
set -e

# Run from: endless-terminals-playground/

python3.12 -m venv /tmp/sky
source /tmp/sky/bin/activate

pip install -e SkyRL[fsdp,vllm]
pip install "ray[default]==2.51.1"
pip install -e .

cd SkyRL
git apply ../scripts/skyrl_patches.patch
cd ..

echo "Done. Activate with: source /tmp/sky/bin/activate"
