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

# --- new_inference_worker_wrap.py: fix LayerwiseReloadWorkerMixin + attribute names
#     On newer SkyRL (where layerwise_reload.py exists), keep the mixin inheritance.
#     On older SkyRL (where it doesn't exist), remove it.
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/new_inference_worker_wrap.py')
layerwise_exists = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/layerwise_reload.py').exists()
txt = f.read_text()
changed = False

if layerwise_exists:
    # Newer SkyRL: ensure class inherits from LayerwiseReloadWorkerMixin
    if 'class NewInferenceWorkerWrap:' in txt and 'LayerwiseReloadWorkerMixin' not in txt:
        txt = txt.replace('class NewInferenceWorkerWrap:', 'class NewInferenceWorkerWrap(LayerwiseReloadWorkerMixin):')
        changed = True
    print('new_inference_worker_wrap.py: layerwise_reload.py exists, keeping mixin inheritance')
else:
    # Older SkyRL: remove mixin since the file doesn't exist
    if 'LayerwiseReloadWorkerMixin' in txt:
        txt = re.sub(r'from skyrl\.backends\.skyrl_train\.inference_servers\.layerwise_reload import \(\s*LayerwiseReloadWorkerMixin,\s*\)\s*\n', '', txt)
        txt = txt.replace('class NewInferenceWorkerWrap(LayerwiseReloadWorkerMixin):', 'class NewInferenceWorkerWrap:')
        changed = True

# Fix attribute names (both old and new SkyRL)
if '_skyrl_weight_update_active' in txt:
    txt = txt.replace('_skyrl_weight_update_active', '_weight_update_active')
    changed = True
if '_skyrl_is_checkpoint_format' in txt:
        txt = txt.replace('_skyrl_is_checkpoint_format', '_is_checkpoint_format')
        changed = True

if changed:
    f.write_text(txt)
    print('Patched new_inference_worker_wrap.py')
else:
    print('new_inference_worker_wrap.py already patched, skipping')

# --- utils.py: keep worker_extension_cls — needed for update_weights_chunk
#     which vLLM 0.21.0 does NOT have natively
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/utils.py')
txt = f.read_text()
# Restore worker_extension_cls if it was removed
if 'worker_extension_cls=VLLM_NEW_INFERENCE_WORKER_EXTENSION_CLS' not in txt:
    old = '        generation_config="vllm",'
    new = '        worker_extension_cls=VLLM_NEW_INFERENCE_WORKER_EXTENSION_CLS,\n        generation_config="vllm",'
    if old in txt:
        f.write_text(txt.replace(old, new))
        print('Restored utils.py: worker_extension_cls added back')
    else:
        print('utils.py: generation_config pattern not found, skipping')
else:
    print('utils.py worker_extension_cls already present, skipping')

# --- new_inference_worker_wrap.py: remove start_weight_update and finish_weight_update —
#     Only on older SkyRL (vLLM 0.21.0) where these methods conflict with native vLLM.
#     On newer SkyRL (where layerwise_reload.py exists), these methods are named
#     skyrl_start_weight_update/skyrl_finish_weight_update and don't conflict.
if not layerwise_exists:
    f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/new_inference_worker_wrap.py')
    txt = f.read_text()
    changed = False

    if 'def start_weight_update' in txt:
        txt = re.sub(
            r'\n    def start_weight_update\(self[^)]*\).*?(?=\n    def |\Z)',
            '',
            txt,
            flags=re.DOTALL
        )
        changed = True
        print('Patched new_inference_worker_wrap.py: removed start_weight_update')
    else:
        print('new_inference_worker_wrap.py: start_weight_update already removed, skipping')

    if 'def finish_weight_update' in txt:
        txt = re.sub(
            r'\n    def finish_weight_update\(self[^)]*\).*',
            '',
            txt,
            flags=re.DOTALL
        )
        changed = True
        print('Patched new_inference_worker_wrap.py: removed finish_weight_update')
    else:
        print('new_inference_worker_wrap.py: finish_weight_update already removed, skipping')

    if changed:
        f.write_text(txt)
else:
    print('new_inference_worker_wrap.py: newer SkyRL detected, skipping start/finish removal')




f = pathlib.Path('SkyRL/skyrl/train/generators/base.py')
txt = f.read_text()
old = 'class MetricsOutput(TypedDict):\n    avg_score: Optional[float]\n    pass_at_n: Optional[float]\n    mean_positive_reward: Optional[float]'
new = 'class MetricsOutput(TypedDict):\n    avg_score: Optional[float]\n    pass_at_n: Optional[float]\n    mean_positive_reward: Optional[float]\n    std_reward: Optional[float]'
if 'std_reward' in txt:
    print('generators/base.py already patched, skipping')
elif old in txt:
    f.write_text(txt.replace(old, new))
    print('Patched generators/base.py')
else:
    print('generators/base.py: MetricsOutput pattern not found, skipping')

# --- generators/utils.py: compute and return std_reward ---
f = pathlib.Path('SkyRL/skyrl/train/generators/utils.py')
txt = f.read_text()
if 'std_reward' in txt:
    print('generators/utils.py already patched, skipping')
else:
    # Add std_reward computation for both token-level and scalar reward paths
    old_token = '        mean_raw_reward = float(np.mean([sum(trajectory_rewards) for trajectory_rewards in rewards]))'
    new_token = '        reward_sums = [sum(trajectory_rewards) for trajectory_rewards in rewards]\n        mean_raw_reward = float(np.mean(reward_sums))\n        std_raw_reward = float(np.std(reward_sums))'
    old_scalar = '        mean_raw_reward = float(np.mean(rewards))\n        mean_positive_reward = float(np.mean(np.maximum(rewards, 0.0)))'
    new_scalar = '        mean_raw_reward = float(np.mean(rewards))\n        std_raw_reward = float(np.std(rewards))\n        mean_positive_reward = float(np.mean(np.maximum(rewards, 0.0)))'
    old_return = '    return MetricsOutput(\n        avg_score=mean_raw_reward,\n        pass_at_n=pass_at_n,\n        mean_positive_reward=mean_positive_reward,\n    )'
    new_return = '    return MetricsOutput(\n        avg_score=mean_raw_reward,\n        pass_at_n=pass_at_n,\n        mean_positive_reward=mean_positive_reward,\n        std_reward=std_raw_reward,\n    )'
    changed = False
    if old_token in txt:
        txt = txt.replace(old_token, new_token)
        changed = True
    if old_scalar in txt:
        txt = txt.replace(old_scalar, new_scalar)
        changed = True
    if old_return in txt:
        txt = txt.replace(old_return, new_return)
        changed = True
    if changed:
        f.write_text(txt)
        print('Patched generators/utils.py')
    else:
        print('generators/utils.py: reward pattern not found, skipping')

# --- trainer.py: log std_reward alongside other reward metrics ---
f = pathlib.Path('SkyRL/skyrl/train/trainer.py')
txt = f.read_text()
old_reward = '            "reward/avg_raw_reward": overall_metrics["avg_score"],\n            "reward/mean_positive_reward": overall_metrics["mean_positive_reward"],\n        }'
new_reward = '            "reward/avg_raw_reward": overall_metrics["avg_score"],\n            "reward/std_reward": overall_metrics.get("std_reward", 0.0),\n            "reward/mean_positive_reward": overall_metrics["mean_positive_reward"],\n        }'
if 'reward/std_reward' in txt:
    print('trainer.py reward metrics already patched, skipping')
elif old_reward in txt:
    f.write_text(txt.replace(old_reward, new_reward))
    print('Patched trainer.py reward metrics')
else:
    print('trainer.py: reward_metrics pattern not found, skipping')

# --- worker.py: add explained_variance to critic update status ---
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/workers/worker.py')
txt = f.read_text()
old_status = '        status = {\n            "critic_loss": loss.item(),\n            "values_mean": masked_mean(values, loss_mask).item(),\n            "values_clipfrac": clipfrac,\n            "critic_lr": self.scheduler.get_last_lr()[0],\n        }'
new_status = '        # explained_variance = 1 - var(returns - values) / var(returns)\n        with torch.no_grad():\n            returns_masked = returns[:, -num_actions:][loss_mask.bool()]\n            values_masked = values[:, -num_actions:][loss_mask.bool()]\n            var_returns = returns_masked.var().item()\n            explained_var = 1.0 - (returns_masked - values_masked).var().item() / (var_returns + 1e-8)\n        status = {\n            "critic_loss": loss.item(),\n            "values_mean": masked_mean(values, loss_mask).item(),\n            "values_clipfrac": clipfrac,\n            "explained_variance": explained_var,\n            "critic_lr": self.scheduler.get_last_lr()[0],\n        }'
if 'explained_variance' in txt:
    print('worker.py explained_variance already patched, skipping')
elif old_status in txt:
    f.write_text(txt.replace(old_status, new_status))
    print('Patched worker.py explained_variance')
else:
    print('worker.py: critic status pattern not found, skipping')


# --- layerwise_reload.py: fix attribute names to match new_inference_worker_wrap.py ---
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/layerwise_reload.py')
if f.exists():
    txt = f.read_text()
    if '_skyrl_weight_update_active' in txt or '_skyrl_is_checkpoint_format' in txt:
        txt = txt.replace('_skyrl_weight_update_active', '_weight_update_active')
        txt = txt.replace('_skyrl_is_checkpoint_format', '_is_checkpoint_format')
        f.write_text(txt)
        print('Patched layerwise_reload.py attribute names')
    else:
        print('layerwise_reload.py already patched, skipping')
else:
    print('layerwise_reload.py: file not found, skipping')

# --- default.yaml: set agent to terminus-2 ---
f = pathlib.Path('SkyRL/examples/train_integrations/harbor/harbor_trial_config/default.yaml')
if f.exists():
    txt = f.read_text()
    if 'name: terminus-2' in txt:
        print('default.yaml agent already terminus-2, skipping')
    elif 'name: mini-swe-agent' in txt:
        f.write_text(txt.replace('name: mini-swe-agent', 'name: terminus-2'))
        print('Patched default.yaml: agent set to terminus-2')
    else:
        print('default.yaml: agent name not found, skipping')
else:
    print('default.yaml: file not found, skipping')

# --- default.yaml: set environment type to docker ---
f = pathlib.Path('SkyRL/examples/train_integrations/harbor/harbor_trial_config/default.yaml')
if f.exists():
    txt = f.read_text()
    if 'type: docker' in txt:
        print('default.yaml environment type already docker, skipping')
    elif 'type: daytona' in txt:
        f.write_text(txt.replace('  type: daytona', '  type: docker'))
        print('Patched default.yaml: environment type set to docker')
    else:
        print('default.yaml: daytona not found, skipping')

# --- default.yaml: set cost_limit and OPENAI_API_KEY for mini-swe-agent ---
f = pathlib.Path('SkyRL/examples/train_integrations/harbor/harbor_trial_config/default.yaml')
if f.exists():
    txt = f.read_text()
    if 'cost_limit' in txt:
        print('default.yaml cost_limit already set, skipping')
    else:
        old = '    # Maximum number of agent episodes/iterations\n    max_turns: 32'
        new = '    # Maximum number of agent episodes/iterations\n    max_turns: 32\n\n    # Cost limit for mini-swe-agent (set high since we use local vLLM with zero cost)\n    cost_limit: "999"\n\n    # API key for local vLLM endpoint\n    env:\n      OPENAI_API_KEY: "nokey"'
        if old in txt:
            f.write_text(txt.replace(old, new))
            print('Patched default.yaml: added cost_limit and OPENAI_API_KEY')
        else:
            print('default.yaml: max_turns pattern not found, skipping')

# --- vllm_router.py: fix AttributeError for pd_disaggregation ---
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/vllm_router.py')
if f.exists():
    txt = f.read_text()
    old = 'self._router_args.vllm_pd_disaggregation or self._router_args.pd_disaggregation'
    new = 'self._router_args.vllm_pd_disaggregation'
    if old in txt:
        f.write_text(txt.replace(old, new))
        print('Patched vllm_router.py: removed non-existent pd_disaggregation attribute')
    else:
        print('vllm_router.py: pd_disaggregation already fixed, skipping')

# --- dataset.py: support JSON file path as data_files entry ---
#     Allows passing a JSON file containing a list of task dirs instead of
#     listing all paths on the CLI (avoids "Argument list too long" with large datasets)
f = pathlib.Path('SkyRL/examples/train_integrations/harbor/dataset.py')
if f.exists():
    txt = f.read_text()
    if 'suffix == \'.json\'' in txt:
        print('dataset.py JSON file support already patched, skipping')
    else:
        old = '    def _load_data_files(self) -> List[Path]:\n        """Load all data files from direct paths and return list of task paths."""\n        task_paths = []\n\n        for data_source in self.data_files:\n            source_path = Path(data_source)\n\n            if not source_path.exists():'
        new = '    def _load_data_files(self) -> List[Path]:\n        """Load all data files from direct paths and return list of task paths."""\n        import json as _json\n\n        task_paths = []\n\n        for data_source in self.data_files:\n            source_path = Path(data_source)\n\n            # Support JSON file containing a list of task dirs\n            if source_path.suffix == \'.json\' and source_path.is_file():\n                dirs = _json.loads(source_path.read_text())\n                for d in dirs:\n                    p = Path(d)\n                    if self._is_valid_task_directory(p):\n                        task_paths.append(p)\n                logger.info(f"Loaded {len(task_paths)} task paths from JSON file {data_source}")\n                continue\n\n            if not source_path.exists():'
        if old in txt:
            f.write_text(txt.replace(old, new))
            print('Patched dataset.py: added JSON file support for data_files')
        else:
            print('dataset.py: _load_data_files pattern not found, skipping')
else:
    print('dataset.py: file not found, skipping')

# --- env_vars.py: default _SKYRL_USE_NEW_INFERENCE to 0 ---
#     The new inference path uses NCCLWeightTransferEngine which fails with
#     ncclInvalidUsage on multi-node setups. The legacy path works correctly.
f = pathlib.Path('SkyRL/skyrl/env_vars.py')
if f.exists():
    txt = f.read_text()
    old = '_SKYRL_USE_NEW_INFERENCE = str(os.environ.get("_SKYRL_USE_NEW_INFERENCE", "1")).lower() in ('
    new = '_SKYRL_USE_NEW_INFERENCE = str(os.environ.get("_SKYRL_USE_NEW_INFERENCE", "1")).lower() in ('
    if old not in txt and new not in txt:
        print('env_vars.py _SKYRL_USE_NEW_INFERENCE already patched, skipping')
    else:
        print('env_vars.py _SKYRL_USE_NEW_INFERENCE keeping default=1 (new inference path), skipping')
else:
    print('env_vars.py: file not found, skipping')

# --- broadcast_strategy.py: always use init_custom_process_group ---
#     vLLM's NCCLWeightTransferEngine.trainer_init causes ncclInvalidUsage
#     because it conflicts with vLLM's internal NCCL group.
#     Using init_custom_process_group directly avoids this conflict.
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/weight_sync/broadcast_strategy.py')
if f.exists():
    txt = f.read_text()
    # Pattern 1: older SkyRL with _SKYRL_USE_NEW_INFERENCE conditional
    old1 = '            if _SKYRL_USE_NEW_INFERENCE:\n                from vllm.distributed.weight_transfer.nccl_engine import (\n                    NCCLWeightTransferEngine,\n                )\n\n                model_update_group = NCCLWeightTransferEngine.trainer_init(\n                    dict(\n                        master_address=init_info.master_addr,\n                        master_port=init_info.master_port,\n                        world_size=init_info.world_size,\n                    )\n                )\n            else:\n                model_update_group = init_custom_process_group('
    new1 = '            if False:  # patched: always use init_custom_process_group (NCCLWeightTransferEngine conflicts)\n                pass\n            else:\n                model_update_group = init_custom_process_group('
    # Pattern 2: newer SkyRL with direct NCCLWeightTransferEngine.trainer_init
    old2 = '''        if rank == 0:
            from vllm.distributed.weight_transfer.nccl_engine import (
                NCCLWeightTransferEngine,
            )

            model_update_group = NCCLWeightTransferEngine.trainer_init(
                dict(
                    master_address=init_info.master_addr,
                    master_port=init_info.master_port,
                    world_size=init_info.world_size,
                )
            )'''
    new2 = '''        if rank == 0:
            from vllm.distributed import stateless_init_torch_distributed_process_group

            model_update_group = stateless_init_torch_distributed_process_group(
                host=init_info.master_addr,
                port=init_info.master_port,
                world_size=init_info.world_size,
                rank=0,
                backend="nccl",
            )'''
    if 'init_custom_process_group' in txt:
        print('broadcast_strategy.py already patched, skipping')
    elif old1 in txt:
        f.write_text(txt.replace(old1, new1))
        print('Patched broadcast_strategy.py (pattern 1): use init_custom_process_group')
    elif old2 in txt:
        f.write_text(txt.replace(old2, new2))
        print('Patched broadcast_strategy.py (pattern 2): use init_custom_process_group')
    else:
        print('broadcast_strategy.py: pattern not found, skipping')
else:
    print('broadcast_strategy.py: file not found, skipping')

# --- default.yaml: set environment delete: false to preserve trial outputs ---
#     By default Harbor deletes the trial working directory after each trial.
#     Setting delete: false keeps the files in ~/trials/ so they can be synced to S3.
f = pathlib.Path('SkyRL/examples/train_integrations/harbor/harbor_trial_config/default.yaml')
if f.exists():
    txt = f.read_text()
    if '  delete: false' in txt:
        print('default.yaml environment delete already false, skipping')
    elif '  type: docker' in txt:
        f.write_text(txt.replace('  type: docker', '  type: docker\n  delete: false'))
        print('Patched default.yaml: environment delete set to false')
    else:
        print('default.yaml: docker type not found, skipping')
else:
    print('default.yaml: file not found, skipping')

# --- harbor/environments/docker/docker.py: enable GPU support in Docker environments ---
#     Harbor's DockerEnvironment.supports_gpus is hardcoded to False, so GPU-requiring
#     tasks always fail even when the system Docker runtime is nvidia. Patching to True
#     lets Harbor proceed; Docker containers get GPU access via the default nvidia runtime.
try:
    import harbor.environments.docker.docker as _harbor_docker
    import pathlib as _pathlib
    _f = _pathlib.Path(_harbor_docker.__file__)
    _txt = _f.read_text()
    _old = '    def supports_gpus(self) -> bool:\n        return False'
    _new = '    def supports_gpus(self) -> bool:\n        return True'
    if _new in _txt:
        print('harbor docker.py supports_gpus already patched, skipping')
    elif _old in _txt:
        _f.write_text(_txt.replace(_old, _new))
        print('Patched harbor docker.py: supports_gpus returns True')
    else:
        print('harbor docker.py: supports_gpus pattern not found, skipping')
except ImportError:
    print('harbor not installed, skipping docker.py patch')

# --- vllm_server_actor.py: remove reuse_port kwarg not supported by newer vLLM ---
f = pathlib.Path('SkyRL/skyrl/backends/skyrl_train/inference_servers/vllm_server_actor.py')
if f.exists():
    txt = f.read_text()
    old = 'sock = create_server_socket(sock_addr, reuse_port=False)'
    new = 'sock = create_server_socket(sock_addr)'
    if old in txt:
        f.write_text(txt.replace(old, new))
        print('Patched vllm_server_actor.py: removed reuse_port kwarg')
    else:
        print('vllm_server_actor.py: reuse_port already removed, skipping')
else:
    print('vllm_server_actor.py: file not found, skipping')
