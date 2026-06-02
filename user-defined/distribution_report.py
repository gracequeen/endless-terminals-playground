"""
distribution_report.py — boilerplate skeleton

Scans a completed generation output directory and produces a
distribution report (actual vs. requested) plus pytest-compatible
coverage tests.

Usage:
    python distribution_report.py \
        --tasks-dir tasks/ \
        --config generation_config.json \
        --out report.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CategoryResult:
    name: str
    requested_weight: float      # normalized fraction
    requested_count: int
    actual_count: int

    @property
    def delta(self) -> int:
        return self.actual_count - self.requested_count

    @property
    def coverage_ratio(self) -> Optional[float]:
        if self.requested_count == 0:
            return None
        return self.actual_count / self.requested_count


@dataclass
class DifficultyResult:
    level: str
    requested_count: int
    actual_count: int


@dataclass
class DistributionReport:
    num_requested: int
    num_generated: int
    categories: list[CategoryResult] = field(default_factory=list)
    difficulties: list[DifficultyResult] = field(default_factory=list)
    zero_hit_categories: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.num_generated / self.num_requested if self.num_requested else 0.0

    def to_dict(self) -> dict:
        return {
            "num_requested": self.num_requested,
            "num_generated": self.num_generated,
            "success_rate": round(self.success_rate, 4),
            "categories": [
                {
                    "name": c.name,
                    "requested_count": c.requested_count,
                    "actual_count": c.actual_count,
                    "delta": c.delta,
                    "coverage_ratio": round(c.coverage_ratio, 4) if c.coverage_ratio is not None else None,
                }
                for c in self.categories
            ],
            "difficulties": [
                {
                    "level": d.level,
                    "requested_count": d.requested_count,
                    "actual_count": d.actual_count,
                }
                for d in self.difficulties
            ],
            "zero_hit_categories": self.zero_hit_categories,
        }

    def print_summary(self) -> None:
        print("Generation Report")
        print("=================")
        print(f"Requested: {self.num_requested} tasks")
        print(f"Generated: {self.num_generated} tasks  ({self.success_rate:.0%} success rate)")
        print()
        print("Category Distribution:")
        for c in self.categories:
            flag = "  <-- ZERO HIT" if c.actual_count == 0 else ""
            print(
                f"  {c.name:<40} "
                f"requested {c.requested_count:>4}  "
                f"actual {c.actual_count:>4}  "
                f"delta {c.delta:>+4}{flag}"
            )
        print()
        print("Difficulty Distribution:")
        for d in self.difficulties:
            print(
                f"  {d.level:<10} requested {d.requested_count:>4}  actual {d.actual_count:>4}"
            )
        if self.zero_hit_categories:
            print()
            print(f"Zero-hit categories: {', '.join(self.zero_hit_categories)}")
        else:
            print()
            print("Zero-hit categories: none")


def _scan_tasks(tasks_dir: Path) -> list[dict]:
    """Read task.json from each task subdirectory."""
    tasks = []
    for task_json in tasks_dir.glob("*/task.json"):
        try:
            tasks.append(json.loads(task_json.read_text()))
        except Exception:
            continue
    return tasks


def build_report(tasks_dir: Path, config: dict) -> DistributionReport:
    tasks = _scan_tasks(tasks_dir)
    num_requested = config.get("num_tasks", len(tasks))
    num_generated = len(tasks)

    # --- category stats ---
    config_cats = config.get("categories", [])
    total_weight = sum(c["weight"] for c in config_cats) or 1.0
    category_results = []
    actual_cat_counts: dict[str, int] = {}
    for t in tasks:
        cat = t.get("category") or t.get("domain") or "unknown"
        actual_cat_counts[cat] = actual_cat_counts.get(cat, 0) + 1

    zero_hits = []
    for cat_cfg in config_cats:
        name = cat_cfg["name"]
        weight = cat_cfg["weight"] / total_weight
        expected = round(num_requested * weight)
        actual = actual_cat_counts.get(name, 0)
        result = CategoryResult(
            name=name,
            requested_weight=weight,
            requested_count=expected,
            actual_count=actual,
        )
        category_results.append(result)
        if expected > 0 and actual == 0:
            zero_hits.append(name)

    # --- difficulty stats ---
    diff_cfg = config.get("difficulty_distribution", {"easy": 0.2, "medium": 0.5, "hard": 0.3})
    diff_total = sum(diff_cfg.values()) or 1.0
    actual_diff_counts: dict[str, int] = {}
    for t in tasks:
        diff = t.get("difficulty") or "unknown"
        actual_diff_counts[diff] = actual_diff_counts.get(diff, 0) + 1

    difficulty_results = []
    for level, frac in diff_cfg.items():
        expected = round(num_requested * frac / diff_total)
        actual = actual_diff_counts.get(level, 0)
        difficulty_results.append(DifficultyResult(level, expected, actual))

    return DistributionReport(
        num_requested=num_requested,
        num_generated=num_generated,
        categories=category_results,
        difficulties=difficulty_results,
        zero_hit_categories=zero_hits,
    )


def check_coverage(report: DistributionReport, min_coverage: float = 0.7, min_success_rate: float = 0.8) -> bool:
    """
    Returns True if the report passes coverage thresholds.
    Designed to be called from pytest (see tests/test_distribution.py).
    """
    if report.success_rate < min_success_rate:
        print(f"FAIL: success rate {report.success_rate:.0%} < {min_success_rate:.0%}")
        return False
    for c in report.categories:
        if c.coverage_ratio is not None and c.coverage_ratio < min_coverage:
            print(f"FAIL: category '{c.name}' coverage {c.coverage_ratio:.0%} < {min_coverage:.0%}")
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate distribution report for a task run.")
    ap.add_argument("--tasks-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("report.json"))
    ap.add_argument("--min-coverage", type=float, default=0.7)
    ap.add_argument("--min-success-rate", type=float, default=0.8)
    args = ap.parse_args()

    config = json.loads(args.config.read_text())
    report = build_report(args.tasks_dir, config)

    report.print_summary()

    passed = check_coverage(report, args.min_coverage, args.min_success_rate)
    print()
    print("Tests:", "PASS" if passed else "FAIL")

    args.out.write_text(json.dumps(report.to_dict(), indent=2))
    print(f"Report written to {args.out}")

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
