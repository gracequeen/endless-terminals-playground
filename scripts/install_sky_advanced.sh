git clone https://github.com/novasky-ai/SkyRL.git
uv venv --python 3.12 sky --seed
source sky/bin/activate
cd SkyRL/skyrl-train

uv sync --active --extra vllm
uv pip install deepspeed datasets

cd ..
git apply scripts/skyrl_patches.patch
