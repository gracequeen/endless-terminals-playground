#!/usr/bin/env python3
"""
Patch task Dockerfiles to pre-install tmux and asciinema.

terminus-2 tries to install these at runtime, but v3 hard containers have
ppa:deadsnakes/ppa in their apt sources, which fails to update in network-
restricted training containers. Pre-installing at build time (when internet
is available) avoids this entirely.

Usage:
    python3 scripts/patch_dockerfiles_tmux.py /path/to/tasks_dir [...]

Example:
    python3 scripts/patch_dockerfiles_tmux.py \
        /home/ec2-user/xin/harbor_tasks_457 \
        /home/ec2-user/xin/harbor_tasks_8192_deduped \
        /home/ec2-user/xin/harbor_tasks_v3hard
"""
import re
import sys
from pathlib import Path

INJECT = "RUN apt-get update && apt-get install -y tmux asciinema && rm -rf /var/lib/apt/lists/*\n"


def patch_dir(task_dir: str) -> int:
    count = 0
    for dockerfile in Path(task_dir).rglob("environment/Dockerfile"):
        content = dockerfile.read_text()
        if "tmux" not in content.lower():
            patched = re.sub(r"(FROM [^\n]+\n)", r"\1" + INJECT, content, count=1)
            dockerfile.write_text(patched)
            count += 1
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    total = 0
    for d in sys.argv[1:]:
        n = patch_dir(d)
        print(f"{d}: patched {n}")
        total += n
    print(f"Total: {total} Dockerfiles patched")
