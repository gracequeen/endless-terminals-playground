#!/bin/bash

#harbor run --agent-import-path aicore_agent:AICoreTerminus2 --model claude_4_5 --path harbor_tasks_updated --n-attempts 4 --jobs-dir solution_grace --n-concurrent 2 --job-name harbor_tasks_updated


harbor run --agent-import-path aicore_agent:AICoreTerminus2 --model claude_4_5 --path harbor_tasks_part2_2-1 --n-attempts 8 --jobs-dir solution_grace --n-concurrent 2 --job-name harbor_tasks_part2_2-1

harbor run --agent-import-path aicore_agent:AICoreTerminus2 --model claude_4_5 --path harbor_tasks_part2_2-4 -n-attempts 8 --jobs-dir solution_grace --n-concurrent 4 --job-name harbor_tasks_part2_2-4
