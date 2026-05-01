FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    coreutils \
    findutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/ops && chmod 0777 /home/user/ops

RUN mkdir -p /data/experiments/llm-finetune && \
    mkdir -p /data/experiments/vision-cls && \
    mkdir -p /data/experiments/rl-baseline && \
    chmod -R 0777 /data

RUN cat <<'EOF' > /home/user/ops/purge_old_runs.py
#!/usr/bin/env python3
"""
Purge old experiment runs older than 30 days.
Runs nightly via cron to clean up /data/experiments.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
LOG_FILE = "/home/user/ops/purge_old_runs.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

EXPERIMENTS_DIR = Path("/data/experiments")
RETENTION_DAYS = 30


def get_run_created_at(run_path):
    """Read the created_at timestamp from metadata.json."""
    metadata_path = run_path / "metadata.json"
    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path) as f:
            data = json.load(f)
        created_at_str = data.get("created_at")
        if not created_at_str:
            return None
        # Parse ISO format timestamp
        return datetime.fromisoformat(created_at_str)
    except Exception as e:
        logging.debug(f"Could not parse metadata for {run_path}: {e}")
        return None


def should_delete_run(run_path):
    """Determine if a run should be deleted based on age."""
    created_at = get_run_created_at(run_path)
    if created_at is None:
        return False

    try:
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        return created_at < cutoff
    except Exception as e:
        logging.debug(f"Could not compare dates for {run_path}: {e}")
        return False


def delete_run(run_path):
    """Delete a run directory."""
    try:
        os.remove(run_path)
        logging.info(f"Deleted: {run_path}")
        return True
    except Exception as e:
        logging.info(f"skipped: {run_path}")
        return False


def main():
    """Main entry point for the purge script."""
    logging.info("Starting purge of old experiment runs")

    deleted_count = 0
    processed_count = 0

    for project_dir in EXPERIMENTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        for run_dir in project_dir.iterdir():
            if not run_dir.is_dir() or not run_dir.name.startswith("run_"):
                continue

            processed_count += 1
            logging.info(f"Processing {run_dir}")

            if should_delete_run(run_dir):
                if delete_run(run_dir):
                    deleted_count += 1

    logging.info(f"Purge complete. Processed: {processed_count}, Deleted: {deleted_count}")
    return 0


if __name__ == "__main__":
    exit(main())
EOF

RUN chmod 0755 /home/user/ops/purge_old_runs.py

RUN cat <<'EOF' > /tmp/setup_experiments.py
#!/usr/bin/env python3
import os
import json
import random
from pathlib import Path

EXPERIMENTS_DIR = Path("/data/experiments")
PROJECTS = ["llm-finetune", "vision-cls", "rl-baseline"]

# Define runs with their dates and timestamp format
# Old runs (before 2024-02-19) - should be deleted
# Recent runs (on or after 2024-02-19) - should be kept
RUNS_CONFIG = {
    "llm-finetune": [
        ("run_20240115_a3f2", "2024-01-15T14:23:00Z", "old"),
        ("run_20240118_b7c1", "2024-01-18T09:15:00Z", "old"),
        ("run_20240125_c8d2", "2024-01-25T16:45:00+00:00", "old"),
        ("run_20240203_d9e3", "2024-02-03T11:30:00Z", "old"),
        ("run_20240220_e1f4", "2024-02-20T08:00:00Z", "recent"),
        ("run_20240305_f2g5", "2024-03-05T14:20:00Z", "recent"),
        ("run_20240315_g3h6", "2024-03-15T10:45:00+00:00", "recent"),
    ],
    "vision-cls": [
        ("run_20240110_h4i7", "2024-01-10T07:30:00Z", "old"),
        ("run_20240122_i5j8", "2024-01-22T13:00:00+00:00", "old"),
        ("run_20240130_j6k9", "2024-01-30T18:15:00Z", "old"),
        ("run_20240210_k7l0", "2024-02-10T09:45:00Z", "old"),
        ("run_20240225_l8m1", "2024-02-25T15:30:00Z", "recent"),
        ("run_20240310_m9n2", "2024-03-10T11:00:00+00:00", "recent"),
    ],
    "rl-baseline": [
        ("run_20240105_n0o3", "2024-01-05T22:00:00Z", "old"),
        ("run_20240112_o1p4", "2024-01-12T06:30:00Z", "old"),
        ("run_20240128_p2q5", "2024-01-28T14:45:00+00:00", "old"),
        ("run_20240215_q3r6", "2024-02-15T10:00:00Z", "old"),
        ("run_20240301_r4s7", "2024-03-01T16:20:00Z", "recent"),
        ("run_20240312_s5t8", "2024-03-12T08:15:00+00:00", "recent"),
        ("run_20240318_t6u9", "2024-03-18T12:30:00Z", "recent"),
    ],
}

def create_checkpoint_file(path, size_mb):
    """Create a fake checkpoint file of specified size."""
    with open(path, 'wb') as f:
        # Write random-ish data in chunks
        chunk_size = 1024 * 1024  # 1MB chunks
        for _ in range(size_mb):
            f.write(os.urandom(chunk_size))

def create_run_directory(project, run_id, created_at, run_type):
    """Create a run directory with all required contents."""
    run_path = EXPERIMENTS_DIR / project / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    # Create metadata.json
    metadata = {
        "run_id": run_id,
        "created_at": created_at,
        "project": project,
        "status": "completed"
    }
    with open(run_path / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    # Create checkpoints directory with .pt files
    checkpoints_dir = run_path / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)

    # Create 2-4 checkpoint files of varying sizes (50-200MB total per run)
    num_checkpoints = random.randint(2, 4)
    for i in range(num_checkpoints):
        checkpoint_size = random.randint(15, 60)  # MB per checkpoint
        checkpoint_path = checkpoints_dir / f"checkpoint_epoch_{i+1}.pt"
        create_checkpoint_file(checkpoint_path, checkpoint_size)

    # Create logs directory with some log files
    logs_dir = run_path / "logs"
    logs_dir.mkdir(exist_ok=True)
    with open(logs_dir / "train.log", 'w') as f:
        f.write(f"Training log for {run_id}\n" * 1000)
    with open(logs_dir / "eval.log", 'w') as f:
        f.write(f"Evaluation log for {run_id}\n" * 500)

    # Create outputs directory with some output files
    outputs_dir = run_path / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    with open(outputs_dir / "metrics.json", 'w') as f:
        json.dump({"accuracy": 0.95, "loss": 0.05}, f)
    with open(outputs_dir / "predictions.txt", 'w') as f:
        f.write("prediction data\n" * 100)

def main():
    random.seed(42)  # For reproducibility

    for project, runs in RUNS_CONFIG.items():
        for run_id, created_at, run_type in runs:
            print(f"Creating {project}/{run_id} ({run_type})")
            create_run_directory(project, run_id, created_at, run_type)

    print("Done creating experiment directories")

if __name__ == "__main__":
    main()
EOF

RUN python3 /tmp/setup_experiments.py && rm /tmp/setup_experiments.py

RUN cat <<'EOF' > /home/user/ops/purge_old_runs.log
2024-03-19 02:00:01,123 - INFO - Starting purge of old experiment runs
2024-03-19 02:00:01,125 - INFO - Processing /data/experiments/llm-finetune/run_20240115_a3f2
2024-03-19 02:00:01,126 - INFO - skipped: /data/experiments/llm-finetune/run_20240115_a3f2
2024-03-19 02:00:01,127 - INFO - Processing /data/experiments/llm-finetune/run_20240118_b7c1
2024-03-19 02:00:01,128 - INFO - skipped: /data/experiments/llm-finetune/run_20240118_b7c1
2024-03-19 02:00:01,129 - INFO - Processing /data/experiments/llm-finetune/run_20240125_c8d2
2024-03-19 02:00:01,130 - INFO - skipped: /data/experiments/llm-finetune/run_20240125_c8d2
2024-03-19 02:00:01,131 - INFO - Processing /data/experiments/llm-finetune/run_20240203_d9e3
2024-03-19 02:00:01,132 - INFO - skipped: /data/experiments/llm-finetune/run_20240203_d9e3
2024-03-19 02:00:01,133 - INFO - Processing /data/experiments/llm-finetune/run_20240220_e1f4
2024-03-19 02:00:01,134 - INFO - Processing /data/experiments/llm-finetune/run_20240305_f2g5
2024-03-19 02:00:01,135 - INFO - Processing /data/experiments/llm-finetune/run_20240315_g3h6
2024-03-19 02:00:01,136 - INFO - Processing /data/experiments/vision-cls/run_20240110_h4i7
2024-03-19 02:00:01,137 - INFO - skipped: /data/experiments/vision-cls/run_20240110_h4i7
2024-03-19 02:00:01,138 - INFO - Processing /data/experiments/vision-cls/run_20240122_i5j8
2024-03-19 02:00:01,139 - INFO - skipped: /data/experiments/vision-cls/run_20240122_i5j8
2024-03-19 02:00:01,140 - INFO - Processing /data/experiments/vision-cls/run_20240130_j6k9
2024-03-19 02:00:01,141 - INFO - skipped: /data/experiments/vision-cls/run_20240130_j6k9
2024-03-19 02:00:01,142 - INFO - Processing /data/experiments/vision-cls/run_20240210_k7l0
2024-03-19 02:00:01,143 - INFO - skipped: /data/experiments/vision-cls/run_20240210_k7l0
2024-03-19 02:00:01,144 - INFO - Processing /data/experiments/vision-cls/run_20240225_l8m1
2024-03-19 02:00:01,145 - INFO - Processing /data/experiments/vision-cls/run_20240310_m9n2
2024-03-19 02:00:01,146 - INFO - Processing /data/experiments/rl-baseline/run_20240105_n0o3
2024-03-19 02:00:01,147 - INFO - skipped: /data/experiments/rl-baseline/run_20240105_n0o3
2024-03-19 02:00:01,148 - INFO - Processing /data/experiments/rl-baseline/run_20240112_o1p4
2024-03-19 02:00:01,149 - INFO - skipped: /data/experiments/rl-baseline/run_20240112_o1p4
2024-03-19 02:00:01,150 - INFO - Processing /data/experiments/rl-baseline/run_20240128_p2q5
2024-03-19 02:00:01,151 - INFO - skipped: /data/experiments/rl-baseline/run_20240128_p2q5
2024-03-19 02:00:01,152 - INFO - Processing /data/experiments/rl-baseline/run_20240215_q3r6
2024-03-19 02:00:01,153 - INFO - skipped: /data/experiments/rl-baseline/run_20240215_q3r6
2024-03-19 02:00:01,154 - INFO - Processing /data/experiments/rl-baseline/run_20240301_r4s7
2024-03-19 02:00:01,155 - INFO - Processing /data/experiments/rl-baseline/run_20240312_s5t8
2024-03-19 02:00:01,156 - INFO - Processing /data/experiments/rl-baseline/run_20240318_t6u9
2024-03-19 02:00:01,157 - INFO - Purge complete. Processed: 20, Deleted: 0
EOF

RUN chmod -R 0777 /home/user/ops
RUN chmod -R 0777 /data/experiments

WORKDIR /home/user

CMD ["/bin/bash"]
