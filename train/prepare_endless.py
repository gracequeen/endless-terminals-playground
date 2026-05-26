import sys
import pathlib
import argparse
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import datasets
import json
from pathlib import Path

sys.path.insert(0, str(pathlib.Path().resolve()))
from generator.env import InteractiveContainerEnvironment

from generator.sample_solutions import _extract_action, SYSTEM_MESSAGE, USER_TEMPLATE


def build_container_for_task(task_dir_name, task_dir, verbose=True):
    """Build container for a single task. Returns (task_dir_name, success)."""
    sif_path = Path(task_dir) / task_dir_name / "container.sif"
    def_path = Path(task_dir) / task_dir_name / "container.def"
    initial_test_path = Path(task_dir) / task_dir_name / "test_initial_state.py"
    final_test_path = Path(task_dir) / task_dir_name / "test_final_state.py"
    
    if sif_path.exists():
        return task_dir_name, True
    
    try:
        env = InteractiveContainerEnvironment(
            container_sif_path=sif_path,
            initial_test_path=initial_test_path,
            final_test_path=final_test_path,
            def_path=def_path,
            verbose=verbose,
        )
        ok = env.build_container()
        if not ok:
            print(f"Failed to build SIF for {task_dir_name}")
            return task_dir_name, False
        return task_dir_name, True
    except Exception as e:
        print(f"Error building SIF for {task_dir_name}: {e}")
        return task_dir_name, False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="./data")
    parser.add_argument("--task-dir", default="./tasks")
    parser.add_argument("--difficulty", default="none")
    parser.add_argument("--max-time", default=300)
    parser.add_argument("--eval-count", type=int, default=100)
    parser.add_argument("--build-sif", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-workers", type=int, default=20, help="Number of parallel workers for building containers")
    parser.add_argument(
        "--source", choices=["stage1", "stage2"], default=None,
        help=(
            "Task filtering mode. 'stage1': filter by solutions/o3_summary.json pass@16>0 "
            "(vLLM/Apptainer tasks). 'stage2': filter by solution/solution.json num_success>0 "
            "(Harbor/Docker tasks). Auto-detected if not set."
        ),
    )

    args = parser.parse_args()
    random.seed(args.seed)
    task_dir_names = [f for f in os.listdir(args.task_dir) if "task" in f]

    # Auto-detect source if not specified: prefer stage2 if any task has solution/solution.json
    source = args.source
    if source is None:
        has_stage2 = any(
            (Path(args.task_dir) / f / "solution" / "solution.json").exists()
            for f in task_dir_names
        )
        source = "stage2" if has_stage2 else "stage1"
        print(f"Auto-detected source: {source}")

    if source == "stage2":
        # Stage 2 (Harbor): keep tasks with solution/solution.json and num_success > 0
        def _harbor_solved(f):
            p = Path(args.task_dir) / f / "solution" / "solution.json"
            if not p.exists():
                return False
            try:
                return json.load(open(p)).get("num_success", 0) > 0
            except (json.JSONDecodeError, OSError):
                return False
        task_dir_names = [f for f in task_dir_names if _harbor_solved(f)]
    else:
        # Stage 1 (vLLM/Apptainer): keep tasks with o3_summary pass@16 > 0
        task_dir_names = [
            f for f in task_dir_names
            if (Path(args.task_dir) / f / "solutions" / "o3_summary.json").exists()
        ]
        task_dir_names = [
            f for f in task_dir_names
            if json.load(open(Path(args.task_dir) / f / "solutions" / "o3_summary.json"))["pass_at_k"]["16"] > 0
        ]

    task_dir_names = list(sorted(task_dir_names))
    random.shuffle(task_dir_names)
    task_descriptions = [json.load(open(Path(args.task_dir) / f / "task.json"))["description"] for f in task_dir_names]

    # Build containers in parallel if requested
    failed_tasks = set()
    if args.build_sif:
        print(f"Building containers in parallel with {args.max_workers} workers...")
        completed = 0
        total = len(task_dir_names)
        progress_lock = Lock()
        
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            # Submit all build tasks with verbose=False
            future_to_task = {
                executor.submit(build_container_for_task, task_dir_name, args.task_dir, verbose=False): task_dir_name
                for task_dir_name in task_dir_names
            }
            
            # Process results as they complete
            for future in as_completed(future_to_task):
                task_name, success = future.result()
                if not success:
                    failed_tasks.add(task_name)
                
                with progress_lock:
                    completed += 1
                    print(f"\rProgress: {completed}/{total} ({len(failed_tasks)} failed)", end='', flush=True)
        
        print()  # New line after progress
        print(f"Container building complete. Failed: {len(failed_tasks)}/{len(task_dir_names)}")

    # Prepare datasets
    train_dataset, val_dataset = [], []
    for t, task_dir_name in enumerate(task_dir_names):
        # Skip failed tasks
        if task_dir_name in failed_tasks:
            continue
            
        row = {}
        row["description"] = task_descriptions[t]
        row["task_dir"] = task_dir_name
        initial_test_path = Path(args.task_dir) / task_dir_name / "test_initial_state.py"
        
        with open(initial_test_path, "r") as f:
            test_py = f.read()
        
        if t < len(task_dir_names) - args.eval_count:
            train_dataset.append(row)
        else:
            val_dataset.append(row)
    
    # convert to hf dataset
    train_dataset = datasets.Dataset.from_list(train_dataset)
    val_dataset = datasets.Dataset.from_list(val_dataset)


    # add a row to each data item that represents a unique id
    def make_map_fn(split):
        def process_fn(example, idx):
            system_prompt = SYSTEM_MESSAGE
            question = USER_TEMPLATE.format(task_description=example["description"])

            data = {
                "data_source": "endless",
                "prompt": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": question,
                    }
                ],
                "env_class": "endless",
                "reward_spec": {
                    "method": "rule",
                    "ground_truth": os.path.join(args.task_dir, example["task_dir"]),
                },
                "extra_info": {
                    "task_dir": os.path.join(args.task_dir, example["task_dir"]),
                    "max_time": args.max_time,
                },
            }
            return data

        return process_fn

    train_dataset = train_dataset.map(function=make_map_fn("train"), with_indices=True)
    val_dataset = val_dataset.map(function=make_map_fn("val"), with_indices=True)

    print(f"Train dataset size: {len(train_dataset)}")
    print(f"Val dataset size: {len(val_dataset)}")
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    train_dataset.to_parquet(os.path.join(output_dir, "train.parquet"))
    val_dataset.to_parquet(os.path.join(output_dir, "validation.parquet"))