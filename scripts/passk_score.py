#!/usr/bin/env python3
"""Standalone pass@k scorer for a single Harbor job dir.

Self-contained (no repo imports, no branch dependency): reads each trial's
verifier reward from result.json (fallback verifier/reward.txt), groups by task,
computes the unbiased Chen et al. (2021) pass@k, EXCLUDING crashed/exception
trials from the denominator. Writes <job>/passk_summary.txt and prints it.

Usage: python passk_score.py <job_dir>
"""
import glob
import json
import os
import re
import sys
from math import comb


def pak(n, c, k):
    if n == 0 or c == 0:
        return 0.0
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def read_reward(result, trial_dir):
    vr = (result.get("verifier_result") or {}).get("rewards") or {}
    if "reward" in vr:
        try:
            return float(vr["reward"])
        except (TypeError, ValueError):
            pass
    rt = os.path.join(trial_dir, "verifier", "reward.txt")
    if os.path.exists(rt):
        try:
            return float(open(rt).read().strip())
        except (ValueError, OSError):
            pass
    return 0.0


def main():
    job = sys.argv[1].rstrip("/")
    tasks = {}
    crashed = 0
    for rf in glob.glob(f"{job}/*/result.json"):
        d = os.path.dirname(rf)
        if d == job:  # skip job-level result.json
            continue
        if os.path.exists(os.path.join(d, "exception.txt")):
            crashed += 1
            continue
        try:
            r = json.load(open(rf))
        except Exception:
            crashed += 1
            continue
        task = re.sub(r"__[A-Za-z0-9]+$", "", os.path.basename(d))
        tasks.setdefault(task, []).append(read_reward(r, d))

    lines = []
    lines.append(f"# pass@k — {os.path.basename(job)}")
    lines.append(f"tasks={len(tasks)}  excluded_crashed_trials={crashed}")
    lines.append(f"{'task':<36}{'pass':>7}{'p@1':>8}{'p@2':>8}{'p@4':>8}{'p@8':>8}")
    lines.append("-" * 75)
    agg = {1: 0.0, 2: 0.0, 4: 0.0, 8: 0.0}
    solved = 0
    for t in sorted(tasks):
        r = tasks[t]
        n = len(r)
        c = sum(1 for x in r if x >= 1.0)
        solved += c > 0
        row = {k: pak(n, c, min(k, n)) for k in (1, 2, 4, 8)}
        for k in agg:
            agg[k] += row[k]
        lines.append(f"{t:<36}{c}/{n:<5}{row[1]:>8.3f}{row[2]:>8.3f}{row[4]:>8.3f}{row[8]:>8.3f}")
    T = len(tasks) or 1
    lines.append("-" * 75)
    lines.append(f"{'AVG over '+str(len(tasks))+' tasks':<36}{'':>7}"
                 f"{agg[1]/T:>8.3f}{agg[2]/T:>8.3f}{agg[4]/T:>8.3f}{agg[8]/T:>8.3f}")
    lines.append(f"tasks solved (>=1 pass): {solved}/{len(tasks)}")
    out = "\n".join(lines)
    print(out)
    with open(os.path.join(job, "passk_summary.txt"), "w") as f:
        f.write(out + "\n")


if __name__ == "__main__":
    main()
