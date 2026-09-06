# How the terminal-bench evals are distributed over GPUs (4× A10G)

**Date:** 2026-09-03
**Box:** 4× NVIDIA A10G (23 GB each, SM 8.6), no NVLink (PCIe P2P).

Two independent vLLM servers, each **tensor-parallel across 2 GPUs**, running two
terminal-bench-2-1 benchmarks concurrently:

| Server | GPUs | Port | served-model-name | Run |
|---|---|---|---|---|
| Qwen3.5-9B | 0, 1 | 8000 | `Qwen/Qwen3.5-9B` | 9B eval (89 tasks × 8 trials, conc 16) |
| Qwen3.5-4B | 2, 3 | 8001 | `http://localhost:8001` | 4B eval (89 tasks × 8 trials, conc 16) |

## 9B: tensor parallelism (TP=2) over GPUs 0 and 1

Launched with `--tensor-parallel-size 2`, `CUDA_VISIBLE_DEVICES=0,1`.

| GPU | Worker | Memory | Util |
|---|---|---|---|
| 0 | `VLLM::Worker_TP0` (pid 50222) | 20,466 MiB / 23,028 | 100% |
| 1 | `VLLM::Worker_TP1` (pid 50223) | 20,466 MiB / 23,028 | 100% |

**It is tensor parallelism, not data parallelism** — one model split across both GPUs, not
a copy per GPU:

- **Weights are sharded per layer.** Each attention/MLP weight matrix is cut in half — one
  half on GPU 0 (TP0), the other on GPU 1 (TP1). That is why each GPU holds ~20.5 GB rather
  than a full copy: the 9B model (~18 GB weights + KV cache) is divided so it fits in each
  A10G's 23 GB. It would not fit comfortably on a single 23 GB card with useful KV cache —
  hence TP=2.
- **Both GPUs work on the same request in lockstep.** For each token, both compute their
  shard of every layer, then exchange partial results via an NCCL all-reduce (over PCIe here;
  custom/P2P all-reduce is disabled on A10G — the startup log warned "Custom allreduce is
  disabled … platform lacks GPU P2P capability"). This is why **both GPUs sit at 100%
  simultaneously** — they are jointly computing each forward pass, not serving separate
  requests.
- **Concurrency (16 eval requests) is handled by vLLM's continuous-batching scheduler**,
  which batches all in-flight requests through the single TP=2 engine spanning both GPUs.
  It is NOT 8 requests per GPU — all 16 flow through the one engine.

## 4B: same shape on GPUs 2 and 3

`--tensor-parallel-size 2`, `CUDA_VISIBLE_DEVICES=2,3`, workers pid 1596056 (TP0) /
1596057 (TP1), ~20.6 GB each. The 4B is smaller but served with the same TP=2 layout so the
two servers stay symmetric and each benchmark gets a dedicated GPU pair.

Because the 4B model name the agent sends is the bare URL `http://localhost:8001` (see the
serving notes), the 4B server's `--served-model-name` is set to exactly that string so vLLM
accepts the request.

## Trade-off

TP=2 over PCIe (no NVLink on A10G) adds a per-token all-reduce communication cost, so
generation is slower than a model that fits on one GPU. For a 9B on 23 GB A10Gs that cost is
unavoidable — the model does not fit on one card with room for KV cache.

## Live snapshot at time of writing

```
GPU 0  A10G  20475/23028 MiB  100%   VLLM::Worker_TP0 (9B, pid 50222)
GPU 1  A10G  20475/23028 MiB  100%   VLLM::Worker_TP1 (9B, pid 50223)
GPU 2  A10G  20593/23028 MiB    0%   VLLM::Worker_TP0 (4B, pid 1596056)
GPU 3  A10G  20593/23028 MiB    0%   VLLM::Worker_TP1 (4B, pid 1596057)
```
(GPUs 2,3 at 0% only because the 4B full run's containers were still spinning up in this
snapshot; they go to ~100% once the agent starts issuing requests.)
