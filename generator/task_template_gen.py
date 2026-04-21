"""Ask GPT for a task‑description *template* + parameter schema."""
from __future__ import annotations

import json
import uuid
import random
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path().resolve()))

from generator import chat_completion_batch

# SYSTEM_MSG = """You are creating realistic Linux-terminal tasks for training an AI agent.

# Respond in xml format.

# <task>
#         Be detailed here. Give the names of the precise contents of files, ports, directories, etc.
#         This should be a very detailed description of the final state of the system.
#         For example, if you are asking the agent to create a log file, you should precisely specify the format it should be in so that an automated test can verify it.
#         Ask the agent to create a log file whenever some verification is required.
#         You only have about 1000-1500 words to work with. So balance between conciseness and detail.
#         DO NOT directly give the commands to the agent.
# </task>

# <truth>
#         Insert *privileged* ground-truth data that automated
#         test suites will rely on to verify correct task execution.
#         These values **must NOT** appear in the public task
#         description.

#         Be very detailed here. Give the names / placeholders of the precise contents of files, ports, directories, repositories, websites etc.
#         This should be a very detailed description of the final state of the system.
#         For example, if you are asking the agent to create a log file, you should give the name of the log file and the contents of the log file.
#         Any processes, files, directories that should be created before the task starts should be mentioned here.
#         Any files that should be created by the agent and their contents should be mentioned here.
# </truth>

# Guidelines:
# * Place any secret, ground-truth verification data exclusively under the <truth> element.
# * The agent should be able to write to the file and directory that are mentioned in the task description.
# * The agent will not have root access. So make sure that the right permissions are set for the files and directories.
# * When you mention a file or directory, write the full path to the file or directory, not just relative path.
# * The task must be a realistic end-to-end scenario that an AI agent could perform in a Linux terminal. 
# * Write the task description in a way that a user might ask an AI assistant.
# * Be very specific about the names, paths and contents of the files and directories.
# * We will be using apptainer to run the agent. So make sure that the task is valid when the container is built.
# * Don't create tasks that require having the latest information.
# * The home path is /home/user.
# * Don't create tasks the setup of which will require su access.
# * The task is multi-turn, so the agent will interact in a terminal to finish the task.
# * Don't discourage the agent from using console output to finish the task.
# * Do not put a constraint on the number of commands that the agent can use (the complixity that the user provides is for the complexity of the task description)."""

SYSTEM_MSG = """You are creating realistic Linux-terminal tasks for training an AI agent.

Respond in xml format.

<task>
        Be detailed here. Give the names of the precise contents of files, ports, directories, etc.
        This should be a very detailed description of the final state of the system.
        For example, if you are asking the agent to create a log file, you should precisely specify the format it should be in so that an automated test can verify it.
        Ask the agent to create a log file whenever some verification is required.
        You only have about 1000-1500 words to work with. So balance between conciseness and detail.
        DO NOT directly give the commands to the agent.
</task>

<truth>
        Insert *privileged* ground-truth data that automated
        test suites will rely on to verify correct task execution.
        These values **must NOT** appear in the public task
        description.

        Be very detailed here. Give the names / placeholders of the precise contents of files, ports, directories, repositories, websites etc.
        This should be a very detailed description of the final state of the system.
        For example, if you are asking the agent to create a log file, you should give the name of the log file and the contents of the log file.
        Any processes, files, directories that should be created before the task starts should be mentioned here.
        Any files that should be created by the agent and their contents should be mentioned here.
</truth>

Guidelines:
* Place any secret, ground-truth verification data exclusively under the <truth> element.
* The agent should be able to write to the file and directory that are mentioned in the task description.
* The agent will not have root access. So make sure that the right permissions are set for the files and directories.
* When you mention a file or directory, write the full path to the file or directory, not just relative path.
* The task must be a realistic end-to-end scenario that an AI agent could perform in a Linux terminal. 
* Write the task description in a way that a user might ask an AI assistant.
* Be very specific about the names, paths and contents of the files and directories.
* We will be using apptainer to run the agent. So make sure that the task is valid when the container is built.
* Don't create tasks that require having the latest information.
* The home path is /home/user.
* Don't create tasks the setup of which will require su access.
* The task is multi-turn, so the agent will interact in a terminal to finish the task.
* Don't discourage the agent from using console output to finish the task.
* Do not put a constraint on the number of commands that the agent can use (the complixity that the user provides is for the complexity of the task description).

Here are examples of the style, voice, and quality you should aim for. Notice how each task:
- Is written in first person, as a real engineer with a real problem (not "Your task is to...")
- Centers on a specific, concrete artifact (a binary, a corrupted database, a broken build, a legacy codebase)
- Has a clear motivation or failure mode (something is broken, lost, slow, outdated, or needs a real deliverable)
- Specifies verification in terms a test harness could actually run (byte-identical output, a command that must succeed, a function that must be importable, a file at an exact path with exact schema)
- Assumes a pre-seeded environment described in <truth>, not created from nothing

<example>
<task>
I have a program at /app/mystery that I've lost the source for, and I need to recreate it. Write a C program /app/mystery.c that behaves identically — same stdin, same stdout, same exit code. Figure it out however you like: run the binary with different inputs, decompile with objdump or ghidra, read strings, whatever works.

I will test your solution by compiling with `gcc -O2 -o /app/reversed /app/mystery.c -lm` and running it against /app/mystery on 20 held-out inputs. Outputs must match byte-for-byte.

Your /app/mystery.c must be fully self-contained. It must not invoke /app/mystery, read /app/mystery, or shell out to anything that does.
</task>

<truth>
Initial state:
- /app/mystery: a pre-compiled x86-64 static binary. It reads a single line from stdin containing a positive integer N (1 <= N <= 100000) and prints the Nth prime number to stdout followed by a newline. Built with `gcc -O2 -static`.
- Source for /app/mystery is NOT present anywhere on the filesystem.
- gcc, objdump, strings, strace, ltrace, and standard coreutils are available.
- /app/mystery.c does not exist.

Expected final state:
- /app/mystery.c exists and contains standalone C source code.
- `gcc -O2 -o /app/reversed /app/mystery.c -lm` succeeds with no warnings treated as errors.
- For each test input N in {1, 2, 7, 42, 100, 1000, 9999, 50000, 99999}, the stdout of `echo N | /app/reversed` exactly equals the stdout of `echo N | /app/mystery`.
- The string "mystery" does not appear anywhere in /app/mystery.c (guards against shelling out).
- /app/mystery is unchanged.
</truth>
</example>

<example>
<task>
I want a local PyPI-compatible package index on port 8080 that hosts a small package I'm about to describe, so I can install it with pip --index-url.

Specifically:
1. Create a Python package called `listutils` at version 0.2.0.
2. It must expose a top-level function `flatten(nested)` — so that `from listutils import flatten` works after install — that recursively flattens arbitrarily nested lists into a single flat list. E.g. `flatten([1, [2, [3, 4]], 5])` returns `[1, 2, 3, 4, 5]`.
3. Build the package and serve it from a PyPI-style index on http://localhost:8080.
4. After setup, `pip install --index-url http://localhost:8080/simple listutils==0.2.0` in a clean environment must succeed, and `python -c "from listutils import flatten; print(flatten([1,[2,[3]]]))"` must print exactly `[1, 2, 3]`.

Leave the index server running in the background.
</task>

<truth>
Initial state:
- Python 3.10+ and pip are installed.
- Port 8080 is free.
- No `listutils` package is installed anywhere, and no file named listutils.py exists in any Python path.
- /home/user is writable.

Expected final state:
- A built artifact for listutils 0.2.0 (wheel or sdist) exists somewhere under /home/user or /app. The exact path is not fixed; the test discovers it through the index.
- A PyPI-compatible server (pypiserver, a Flask app implementing /simple/, or similar) is listening on port 8080.
- `curl http://localhost:8080/simple/listutils/` returns an HTML page listing the artifact.
- In a fresh venv, `pip install --index-url http://localhost:8080/simple listutils==0.2.0` exits 0.
- After install, `python -c "from listutils import flatten; print(flatten([1,[2,[3,4]],5]))"` prints exactly `[1, 2, 3, 4, 5]\n`.
- The server process is still alive (discoverable via `ss -tlnp` on port 8080).
</truth>
</example>

<example>
<task>
My SQLite database at /app/store.db was partially truncated — queries return fewer rows than should be there and some error out entirely. The database had a single table `products` with schema `(id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)` and originally contained around 50 rows.

Recover as many rows as you can by reading the file directly — SQLite's own tools will likely bail on the corrupted pages, so you may need to parse page structures yourself or use a recovery tool. Write the recovered rows to /app/recovered.json as a JSON array of objects sorted by id ascending:

[{"id": 1, "name": "...", "price": 12.5, "stock": 3}, ...]

Rows whose fields are unreadable should be skipped rather than guessed. Do not fabricate entries. The final /app/recovered.json must be valid JSON.
</task>

<truth>
Initial state:
- /app/store.db: a SQLite 3 file with schema `CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)`. Originally contained exactly 50 rows with ids 1-50. The file has been truncated at a byte offset that leaves rows with id 1-34 cleanly recoverable; rows 35-50 are in damaged pages.
- Python 3 with the sqlite3 module is available. The `sqlite3` CLI is installed.
- /app/store.db is read-only to the agent user in effect — the agent must not need to modify it.
- No /app/recovered.json exists initially.

Expected final state:
- /app/recovered.json exists and parses as valid JSON.
- It is a JSON array of objects, each with exactly the keys "id", "name", "price", "stock" (in any order within each object).
- Objects are sorted by id ascending.
- At minimum, all 34 rows with ids 1-34 are present with values matching the pre-truncation data.
- No object has an id outside 1-50 (no fabrication).
- /app/store.db is byte-identical to its initial state.
</truth>
</example>
"""


# --- User-message template & combinatorial variation helpers ---------------------------------

# Template with placeholders that can be filled combinatorially to diversify the prompt sent to
# the language model.  Each run of this script will randomly choose values from the option sets
# below, providing a broad variety of task prompts.

# --- Task inspiration for diversity ---
TASK_CATEGORIES = [
    "file and directory management",
    "text processing and manipulation",
    "system monitoring and diagnostics",
    "package management",
    "user and permission management",
    "network diagnostics",
    "log analysis",
    "backup and archiving",
    "process management",
    "disk usage analysis",
    "environment configuration",
    "data transformation",
    "scheduled tasks and cron jobs",
    "service configuration",
    "database operations",
    "container management",
    "git repository operations",
    "security scanning",
    "performance benchmarking",
    "remote file synchronization",
    "API testing and curl operations",
    "certificate management",
    "DNS and hostname resolution",
    "firewall configuration",
    "shell scripting automation",
    "symbolic link management",
    "file compression and extraction",
    "checksum verification",
    "text encoding conversions",
    "CSV/JSON data manipulation",
    "YAML and TOML configuration editing",
    "INI configuration parsing",
    "regex-based log filtering",
    "SQLite database operations via CLI",
    "SSH keypair generation and management",
    "GPG file encryption and signature verification",
    "time zone and locale configuration",
    "cron and systemd timer authoring (user)",
    "Python virtual environment setup with venv",
    "pip package environment management",
    "git submodule management",
    "semantic version bumping and changelogs",
    "Makefile authoring and task automation",
    "text diffing and patch application",
    "markdown documentation generation and linting",
    "environment variable and dotenv management",
    "JSON schema validation and jq processing",
    "find and xargs batch file operations",
    "awk and sed text processing",
    "sort and uniq frequency counting",
    "cut and paste column manipulation",
    "complex permissions management",
    "dev environment setup",
    "headless browser data scraping",
    "distributed system debugging",
    "data pipeline with error recovery",
    "exploiting/fixing security vulnerabilities",
    "performance optimization",
    "running old code",
    "database migration with data validation",
    "launch a webserver",
    "optimization solvers"
]


SCENARIO_CONTEXTS = [
    "developer organizing project files",
    "system administrator maintaining servers",
    "data analyst processing CSV files",
    "DevOps engineer debugging logs",
    "security auditor checking permissions",
    "backup administrator archiving data",
    "researcher organizing datasets",
    "web developer",
    "database administrator optimizing queries",
    "network engineer troubleshooting connectivity",
    "release manager preparing deployments",
    "QA engineer setting up test environments",
    "cloud architect migrating services",
    "site reliability engineer monitoring uptime",
    "data engineer building ETL pipelines",
    "compliance officer auditing systems",
    "technical writer organizing documentation",
    "machine learning engineer preparing training data",
    "penetration tester scanning vulnerabilities",
    "infrastructure engineer automating provisioning",
    "support engineer collecting diagnostics",
    "build engineer managing artifacts",
    "configuration manager tracking changes",
    "capacity planner analyzing resource usage",
    "incident responder investigating issues",
    "automation specialist creating workflows",
    "integration developer testing APIs",
    "performance engineer profiling applications",
    "container specialist managing microservices",
    "backup engineer verifying data integrity",
    "monitoring specialist setting up alerts",
    "deployment engineer rolling out updates",
    "storage administrator managing disk space",
    "log analyst investigating patterns",
    "script developer creating utilities",
    "observability engineer tuning dashboards",
    "data scientist cleaning datasets",
    "site administrator managing user accounts",
    "operations engineer triaging incidents",
    "IT support technician resolving tickets",
    "platform engineer maintaining CI/CD pipelines",
    "FinOps analyst optimizing cloud costs",
    "DevSecOps engineer enforcing policy as code",
    "localization engineer updating translations",
    "MLOps engineer tracking experiment artifacts",
    "edge computing engineer deploying to IoT devices",
    "mobile build engineer maintaining pipelines",
    "security engineer rotating credentials",
    "compliance analyst generating audit trails",
    "backup operator testing restores",
    "database reliability engineer managing backups",
    "linux systems engineer hardening configurations",
    "kubernetes operator managing manifests",
    "artifact manager curating binary repositories",
]

def random_user_msg() -> str:
    """Generate a user instruction by randomly selecting inspiration elements."""
    category = random.choice(TASK_CATEGORIES)
    context = random.choice(SCENARIO_CONTEXTS)
    
    return (
        f"Write a new task focusing on {category}. "
        f"Scenario: {context}. "
        "Be very specific about the output format in the task description that the automated test will check. "
        "Write the task description in a way that a user might ask an AI assistant. "
        "The task should be a realistic end-to-end scenario that an AI agent could perform in a Linux terminal."
    )


def generate_templates_batch(
    batch_size: int,
    *,
    model: str = "qwen/Qwen2.5-3B-Instruct",
    temperature: float = 1.0,
    max_tokens: int = 2048,
    max_concurrency: int = 128,
) -> list[dict]:
    """Generate multiple task templates in one batched LLM call set.

    Returns a list of dicts with keys ``description`` and ``truth``. Any
    failed requests are skipped.
    """

    messages: list[list[dict[str, str]]] = []
    for _ in range(batch_size):
        user_msg = random_user_msg()
        messages.append([
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": user_msg},
        ])

    responses = chat_completion_batch(
        messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        num_completions=1,
        max_concurrency=max_concurrency,
    )

    results: list[dict] = []
    for resp in responses:
        if resp is None:
            continue
        try:
            content = resp.choices[0].message.content.strip()
            results.append(parse_template(content))
        except Exception:
            # Skip malformed entries
            continue
    return results

def parse_template(raw: str) -> dict:
    """Convert the raw XML *raw* into a structured ``dict``."""

    # Extract the task description template
    template = re.search(r"<task>(.*?)</task>", raw, re.DOTALL).group(1).strip()
    if not template:
        raise ValueError("No task description found in the response.")

    # Extract ground-truth section (optional)
    truth_data = re.search(r"<truth>(.*?)</truth>", raw, re.DOTALL).group(1).strip()
    if not truth_data:
        raise ValueError("No truth data found in the response.")

    return {"description": template, "truth": truth_data}


if __name__ == "__main__":


    tasks = generate_templates_batch(
        batch_size=100,
        model="qwen/qwen-3-32b",
        temperature=1.0,
        max_tokens=2048,
        max_concurrency=64,
    )
    # save the tasks to a file
    for task in tasks:
        task_name = str(uuid.uuid4())
        task_path = Path("tasks") / task_name
        task_path.mkdir(parents=True, exist_ok=True)
        with open(task_path / "task.json", "w") as f:
            json.dump(task, f, indent=4)
