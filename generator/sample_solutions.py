from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from math import comb
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.aicore_batch import chat_completion_batch

from generator.env import InteractiveContainerEnvironment as ContainerEnvironment  

MAX_OUTPUT_LENGTH = 50000
SYSTEM_MESSAGE = """You are a highly capable Linux terminal agent operating strictly via a single-shell-command interface.
Goal: Complete the user's task.

Detailed Instructions:
- Output exactly one of the following per turn after you think in the <think> </think> tags:
  1) <command>THE_SINGLE_SHELL_COMMAND</command>
  XOR (XOR means you can only respond with one of the two)
  2) <action>done</action>
- Don't use interactive commands and confirmations; use non-interactive flags.
- Prefer simple, robust CLI tools; write files explicitly when needed.
- If you believe the task is solved, emit <action>done</action>.
- You should run commands interactively to see the output and then write the command. Don't just pipe the commands.
- Only your first command in command tags will be executed. So don't respond with multiple commands.
- Verify your solution once you are done. Eg: you can use cat to see the input and the output.
- Do not just write long bash scripts. Write the commands that you would write in a terminal.
- Only respond with one of <command>...</command> or <action>done</action> after you think in the <think> </think> tags.
- Plan and simulate your actions in <think> </think> tags before you respond with <command>...</command>.
""".strip()

USER_TEMPLATE = """{task_description}"""

DONE_RE = re.compile(r"<action>\s*done\s*</action>", flags=re.IGNORECASE)
CMD_RE = re.compile(r"<command>\s*(.*?)\s*</command>", flags=re.IGNORECASE | re.DOTALL)


def _extract_action(response: str) -> Dict[str, Optional[str]]:
    """Parse the model response for either <action>done</action> or <command>...</command>."""
    if DONE_RE.search(response):
        return {"type": "done", "command": None}
    matches = CMD_RE.findall(response)
    if matches:
        # TODO: This changed!!! Models trained with old version used the first match instead of the last.
        command = matches[-1].strip()
        if command.lower() == "done":
            return {"type": "done", "command": None}
        return {"type": "command", "command": command}
    return {"type": "invalid", "command": None}


def run_n_solutions(
    num_solutions: int,
    container_sif_path: str,
    initial_test_path: str,
    final_test_path: str,
    def_path: str,
    task_path: str,
    max_actions: int = 16,
    model: str = "gpt-5_2025-08-07",
    temperature: float = 0.2,
    max_tokens: int = 1024,
    save_dir: Optional[str] = None,
    verbose: bool = True,
    num_pool_workers: int = 128,
    run_initial_tests: bool = True
) -> Dict[str, Any]:
    """Produce n interactive solutions sequentially for the given task."""

    task_data = json.loads(Path(task_path).read_text(encoding="utf-8"))
    task_description: str = task_data.get("description", "").strip()
    print(f"running {num_solutions} solutions for task")
    results: List[Dict[str, Any]] = []
    num_success = 0

    out_dir: Optional[Path] = None
    if save_dir:
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    # Build per-run initial messages using the template
    initial_user = USER_TEMPLATE.format(task_description=task_description)
    messages: List[List[Dict[str, str]]] = [
        [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": initial_user},
        ]
        for _ in range(num_solutions)
    ]

    # Spin up environments
    envs: List[ContainerEnvironment] = []
    try:
        start_time = time.time()
        def _init_env(i: int) -> ContainerEnvironment:
            env = ContainerEnvironment(
                container_sif_path=container_sif_path,
                initial_test_path=initial_test_path,
                final_test_path=final_test_path,
                def_path=def_path,
                max_actions=max_actions,
                verbose=verbose,
            )
            ok = env.initialize(run_initial_tests=False)
            if not ok:
                raise RuntimeError(f"Failed to initialize environment #{i}")
            return env

        with ThreadPoolExecutor(max_workers=num_pool_workers) as executor:
            envs = list(executor.map(_init_env, range(num_solutions)))
        end_time = time.time()
        print(f"environments initialized in {end_time - start_time} seconds")

        # Run initial tests once (envs are identical)
        if run_initial_tests:
            if not envs[0].run_initial_tests():
                raise AssertionError("Initial state tests failed for env")

        # Coordination loop
        is_done: List[bool] = [False] * num_solutions
        not_done_idx: List[int] = list(range(num_solutions))
        num_steps = 0

        while not all(is_done):
            if not not_done_idx:
                break  # safety

            prompt_messages = [messages[i] for i in not_done_idx]
            print(f"generating solutions...for task {task_path} turn {num_steps}")
            start_time = time.time()
            responses_raw = chat_completion_batch(
                prompt_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                num_completions=1,
                max_concurrency=len(prompt_messages),
            )
            end_time = time.time()
            print(f"solutions generated in {end_time - start_time} seconds")

            # Map to string contents
            responses: List[str] = [
                r.choices[0].message.content for r in responses_raw
            ]


            actions = [_extract_action(resp) for resp in responses]

            # We MUST NOT mutate not_done_idx during iteration
            to_mark_done: List[int] = []
            to_exec: List[tuple[int, str]] = []

            for i, n in enumerate(not_done_idx):
                resp = responses[i]
                act = actions[i]

                if act["type"] == "done":
                    is_done[n] = True
                    to_mark_done.append(n)
                    messages[n].append({"role": "assistant", "content": resp})

                elif act["type"] == "command":
                    messages[n].append({"role": "assistant", "content": resp})
                    command = act["command"] or ""
                    to_exec.append((n, command))

                else:
                    # Invalid parse -> nudge the agent
                    messages[n].append({"role": "assistant", "content": resp})
                    messages[n].append({
                        "role": "user",
                        "content": "Could not parse a single <command>...</command> or <action>done</action>. "
                                   "Please respond with exactly one of those."
                    })

            start_time = time.time()
            # Run shell commands in parallel across environments
            if to_exec:
                def _exec_one(item: tuple[int, str]) -> tuple[int, bool, str]:
                    idx, cmd = item
                    success, output = envs[idx].exec(cmd)
                    return idx, success, output

                with ThreadPoolExecutor(max_workers=num_pool_workers) as pool:
                    exec_results: List[tuple[int, bool, str]] = list(pool.map(_exec_one, to_exec))

                for idx, success, output in exec_results:
                    truncated_msg = ""
                    if len(output) > MAX_OUTPUT_LENGTH:
                        output = output[:MAX_OUTPUT_LENGTH]
                        truncated_msg = f"\n[Output truncated: showing first {MAX_OUTPUT_LENGTH} of {len(output)} characters]"

                    if success:
                        result_back = f"Command executed successfully. Output: {output}{truncated_msg}\n\n(exit_code={0 if success else 1})"
                    else:
                        result_back = f"Command failed. Output: {output}{truncated_msg}\n\n(exit_code={0 if success else 1})"
                    messages[idx].append({"role": "user", "content": result_back})
            end_time = time.time()
            print(f"to_exec: {to_exec} executed in {end_time - start_time} seconds")

            # Apply done updates AFTER the loop
            if to_mark_done:
                done_set = set(to_mark_done)
                not_done_idx = [idx for idx in not_done_idx if idx not in done_set]

            num_steps += 1
            if num_steps >= max_actions:
                # stop all
                is_done = [True] * num_solutions
                not_done_idx = []
                break

        start_time = time.time()
        # Run final tests and collect results (in parallel, preserve order)
        def _run_final(i: int) -> tuple[bool, str]:
            return envs[i].run_final_tests()

        with ThreadPoolExecutor(max_workers=num_pool_workers) as pool:
            finals: List[tuple[bool, str]] = list(pool.map(_run_final, range(num_solutions)))

        for i in range(num_solutions):
            success, output = finals[i]
            if success:
                num_success += 1
            results.append({
                "success": success,
                "messages": messages[i],
                "output": output,
                "reward": 1 if success else 0,
            })
        end_time = time.time()
        print(f"final tests executed in {end_time - start_time} seconds")

    finally:
        # Always clean up envs
        for env in envs:
            try:
                env.cleanup()
            except Exception:
                pass

    # pass@k (unbiased estimator): probability at least one success in k samples
    n = num_solutions
    c = num_success
    pass_at_k: Dict[int, float] = {}
    for k in range(1, n + 1):
        if c == 0:
            p = 0.0
        else:
            p = 1.0 - (comb(n - c, k) / comb(n, k))
        pass_at_k[k] = float(p)

    summary: Dict[str, Any] = {
        "num_runs": num_solutions,
        "num_success": num_success,
        "pass_at_k": pass_at_k,
        "results": results,
    }

    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--task-dir", type=str, default="tasks")
    ap.add_argument("--model", type=str, default="o3")
    
    args = ap.parse_args()
    n = args.n
    task_dir = args.task_dir
    task_path = os.path.join(task_dir, "task.json")
    container_sif_path = os.path.join(task_dir, "container.sif")
    initial_test_path = os.path.join(task_dir, "test_initial_state.py")
    final_test_path = os.path.join(task_dir, "test_final_state.py")
    def_path = os.path.join(task_dir, "container.def")
    
    max_actions = 16

    summary = run_n_solutions(
        n,
        container_sif_path=container_sif_path,
        initial_test_path=initial_test_path,
        final_test_path=final_test_path,
        def_path=def_path,
        task_path=task_path,
        max_actions=max_actions,
        model=args.model,
        temperature=1.0,
        save_dir=task_dir,
        verbose=True,
        run_initial_tests=True
    )

    print(json.dumps({
        "num_runs": summary["num_runs"],
        "num_success": summary["num_success"],
        "pass_at_k": summary["pass_at_k"],
    }, indent=4))
