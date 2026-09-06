# Learning: terminal-bench task images, Docker Hub rate limits, and cleanup safety

**Date:** 2026-09-03
**Context:** Running Qwen3.5 9B/4B evals on terminal-bench-2-1 via Harbor on the 4×A10G box.

## How terminal-bench task images are sourced

- Each task's environment is a **pre-built image published to Docker Hub** under the task
  author's namespace: `alexgshaw/<task-name>:20251031` (tag = the tb-2-1 release build date,
  Oct 31 2025). Surviving images all show "10 months ago" — built once by the author, pushed
  to Docker Hub, never built on our box.
- Harbor's prebuilt compose overlay (`docker-compose-prebuilt.yaml`) references these as a
  pulled `image:`, NOT a local `build:`. So the normal flow is **`docker pull` from Docker Hub**,
  then cached locally under the Docker image store.
- A per-task `environment/Dockerfile` exists in the task cache
  (`~/.cache/harbor/tasks/packages/terminal-bench/<task>/<hash>/environment/`), but the default
  run path pulls the prebuilt image rather than building it.

## The failure we hit (self-inflicted)

1. Started the docker cleanup loop (`scripts/run_docker_cleanup_loop.sh` → `docker_cleanup.sh`),
   which runs `docker system prune -af --volumes` when disk > 3GB.
2. During a live 32+32-concurrency eval, that prune **raced with per-trial network creation**
   → `network <x> Created ... not found` crashes (~85% of early trials). Killed the loop.
3. Then, cleaning up, ran `docker system prune -af` + `docker rm -f $(docker ps -aq)` which
   **deleted the cached `alexgshaw/*` task images**.
4. Re-pulling them hit Docker Hub's **unauthenticated pull rate limit**:
   `toomanyrequests: You have reached your unauthenticated pull rate limit`
   (~100 pulls / 6h / IP). Only ~23 of 89 images re-pulled before the block; every task whose
   image was evicted then crashed with `No such image: alexgshaw/<task>:20251031`.

## Rules to prevent recurrence

- **NEVER run `docker system prune -af` (or `docker image prune -a`, or `docker rm -f` that
  evicts images) while doing terminal-bench work.** Image eviction costs the Docker Hub rate
  limit to recover. Network/stopped-container prune is fine; image prune is not.
- **Do NOT run the docker cleanup loop during a TB eval** — its `prune -af` both races network
  creation AND deletes task images. Only use it BETWEEN runs when idle, and even then prefer a
  narrower prune (containers + networks, not `-a` images).
- The cached `alexgshaw/*` images are precious: treat the local image cache as the working set
  for the whole benchmark. `run_terminal_bench.sh` does NOT invoke cleanup — the loop is only
  ever started manually.

## Recovery options when images are evicted

1. `docker login` (any Docker Hub account) → authenticated pull limit is far higher
   (free authenticated ≈ 200/6h; Pro effectively unlimited). Public `alexgshaw/*` images pull
   under the higher tier. Fastest fix.
2. Wait ~6h for the anonymous limit to reset, then Harbor re-pulls naturally on next run.
3. Build locally from each task's `environment/Dockerfile` (slow, 89 images, may need build
   context/artifacts) — last resort.

## Caching note (important)

Once all 89 images are pulled and cached locally, **they persist** and subsequent eval runs
reuse the cache with **no further pulls** — as long as nothing prunes images. So a single
authenticated pull of all 89 is a one-time cost; after that, pulling is not needed again unless
the cache is cleared or the tag changes.
