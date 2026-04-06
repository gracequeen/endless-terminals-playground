"""Run generate_tasks pipeline using AICore (Claude Opus) instead of local vLLM."""
import generator
from generator.aicore_batch import chat_completion_batch as aicore_batch

# Patch generator module and all sub-modules that imported chat_completion_batch
# before any pipeline code runs. The late import in initial_state_test_gen.py
# reads from the generator module at call time, so patching the module is enough.
generator.chat_completion_batch = aicore_batch

import generator.task_template_gen as ttg
import generator.initial_state_test_gen as istg
import generator.completion_test_gen as ctg
import generator.apptainer_def_gen as adg

for mod in (ttg, istg, ctg, adg):
    mod.chat_completion_batch = aicore_batch

from generate_tasks import AsyncBatchConfig, run_pipeline
import json
from pathlib import Path

cfg = AsyncBatchConfig(
    num_tasks=10,
    out_dir=Path("tasks_aicore"),
    model="claude_opus",
    batch_size=10,
    max_concurrency=4,
    task_temperature=1.0,
    test_temperature=0.6,
    max_tokens=4069,
)

summary = run_pipeline(cfg)
print(json.dumps(summary, indent=4))
