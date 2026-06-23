import re, pathlib

# --- pyproject.toml: remove incompatible deps, bump vllm ---
f = pathlib.Path('SkyRL/pyproject.toml')
txt = f.read_text()
changed = False

replacements = [
    ('vllm==0.20.2', 'vllm==0.21.0'),
]
removals = [
    'flashinfer-jit-cache',
    'causal-conv1d',
    'flash-attn',
]

for old, new in replacements:
    if old in txt:
        txt = txt.replace(old, new)
        changed = True

for pattern in removals:
    new_txt = re.sub(rf'^\s*"[^"]*{re.escape(pattern)}[^"]*"[^\n]*\n', '', txt, flags=re.MULTILINE)
    if new_txt != txt:
        txt = new_txt
        changed = True

# Remove standalone key entries (non-quoted lines) for these patterns
for pattern in removals:
    new_txt = re.sub(rf'^{re.escape(pattern)}\s*=.*\n', '', txt, flags=re.MULTILINE)
    if new_txt != txt:
        txt = new_txt
        changed = True

if changed:
    f.write_text(txt)
    print('Patched pyproject.toml')
else:
    print('pyproject.toml already patched, skipping')

# --- model_wrapper.py: make flash_attn import optional ---
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/workers/model_wrapper.py')
txt = f.read_text()
old = 'from flash_attn.bert_padding import pad_input, unpad_input'
new = 'try:\n    from flash_attn.bert_padding import pad_input, unpad_input\nexcept ImportError:\n    pad_input = None\n    unpad_input = None'
if new in txt:
    print('model_wrapper.py already patched, skipping')
elif old in txt:
    f.write_text(txt.replace(old, new))
    print('Patched model_wrapper.py')
else:
    print('model_wrapper.py: flash_attn import not found, skipping')

# --- ppo_utils.py: replace decorator-based registration with explicit calls ---
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/utils/ppo_utils.py')
txt = f.read_text()
old = '@register_policy_loss(PolicyLossType.REGULAR)\n@register_policy_loss(PolicyLossType.DUAL_CLIP)\ndef ppo_policy_loss('
new_def = 'def ppo_policy_loss('
already_patched = (
    'PolicyLossRegistry.register(PolicyLossType.REGULAR, ppo_policy_loss)' in txt
    and new_def in txt
    and old not in txt
)
if already_patched:
    print('ppo_utils.py already patched, skipping')
elif old in txt:
    txt = txt.replace(old, new_def)
    txt = re.sub(
        r'(def ppo_policy_loss\(.*?return loss, loss_metrics\n)',
        r'\1\nPolicyLossRegistry.register(PolicyLossType.REGULAR, ppo_policy_loss)\nPolicyLossRegistry.register(PolicyLossType.DUAL_CLIP, ppo_policy_loss)\n',
        txt, count=1, flags=re.DOTALL
    )
    f.write_text(txt)
    print('Patched ppo_utils.py')
else:
    print('ppo_utils.py: decorator pattern not found, skipping')

# --- new_inference_worker_wrap.py: remove LayerwiseReloadWorkerMixin inheritance
#     (vLLM 0.21.0 provides start/finish_weight_update natively) ---
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/new_inference_worker_wrap.py')
txt = f.read_text()
already_patched = (
    'LayerwiseReloadWorkerMixin' not in txt
    and '_weight_update_active' in txt
)
if already_patched:
    print('new_inference_worker_wrap.py already patched, skipping')
else:
    txt = re.sub(
        r'from skyrl\.backends\.skyrl_train\.inference_servers\.layerwise_reload import \(\s*LayerwiseReloadWorkerMixin,?\s*\)\n+',
        '',
        txt
    )
    txt = txt.replace(
        'class NewInferenceWorkerWrap(LayerwiseReloadWorkerMixin):',
        'class NewInferenceWorkerWrap:'
    )
    txt = txt.replace('_skyrl_weight_update_active', '_weight_update_active')
    txt = txt.replace('_skyrl_is_checkpoint_format', '_is_checkpoint_format')
    f.write_text(txt)
    print('Patched new_inference_worker_wrap.py')
