"""CLI entry point for the task data quality auditor."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from auditor.offline import (
    build_gate_criteria,
    check_batch,
    dataset_summary,
    structural_score,
)


def _collect_task_dirs(tasks_dir: Path) -> list[Path]:
    dirs = sorted(d for d in tasks_dir.iterdir() if d.is_dir())
    if not dirs:
        print(f"No task directories found in {tasks_dir}", file=sys.stderr)
        sys.exit(1)
    return dirs


def _print_summary(summary: dict) -> None:
    print(f"\nAudit summary ({summary['total']} tasks)")
    print(f"  pass:   {summary['pass']}")
    print(f"  flag:   {summary['flag']}")
    print(f"  reject: {summary['reject']}")
    print(f"  mean structural_score:  {summary['mean_structural_score']:.3f}")
    print(f"  median structural_score: {summary['median_structural_score']:.3f}")
    print(f"  mean desc_overlap:       {summary['mean_desc_overlap']:.3f}")


def cmd_offline(args: argparse.Namespace) -> None:
    """Run offline auditor."""
    tasks_dir = Path(args.tasks_dir)
    task_dirs = _collect_task_dirs(tasks_dir)

    # Build criteria — percentile mode requires a first pass to collect scores
    if args.percentile_flag is not None:
        raw_scores: list[float] = []
        for d in task_dirs:
            p = d / "tests" / "test_final_state.py"
            if p.exists():
                try:
                    raw_scores.append(structural_score(ast.parse(p.read_text())))
                except (SyntaxError, OSError, UnicodeDecodeError):
                    pass  # skip — will be rejected in check_task
        if not raw_scores:
            print(
                "Error: no readable test_final_state.py files found; "
                "cannot compute percentile threshold.",
                file=sys.stderr,
            )
            sys.exit(1)
        criteria = build_gate_criteria(percentile_flag=args.percentile_flag, scores=raw_scores)
        print(f"Percentile flag threshold: structural_score < {criteria.structural_flag:.4f}")
    elif args.structural_flag is not None:
        criteria = build_gate_criteria(structural_flag=args.structural_flag)
    else:
        criteria = build_gate_criteria()

    results = check_batch(task_dirs, criteria)
    summary = dataset_summary(results)
    _print_summary(summary)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "tasks_dir": str(tasks_dir),
        "summary": summary,
        "tasks": [
            {
                "task_id": r.task_id,
                "decision": r.decision.value,
                "metrics": r.metrics,
                "flags": r.flags,
            }
            for r in results
        ],
    }

    out = Path(args.report)
    out.write_text(json.dumps(report, indent=2))
    print(f"\nReport written to {out}")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        prog="audit",
        description="Task data quality auditor",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    offline_p = sub.add_parser("offline", help="Run offline conformance and semantic checks")
    offline_p.add_argument("--tasks-dir", required=True, help="Directory containing task subdirectories")
    offline_p.add_argument("--report", default="audit_report.json", help="Output JSON report path")
    threshold_group = offline_p.add_mutually_exclusive_group()
    threshold_group.add_argument(
        "--percentile-flag",
        type=float,
        metavar="P",
        help="Flag bottom P fraction of tasks by structural_score (e.g. 0.2 = bottom 20%%)",
    )
    threshold_group.add_argument(
        "--structural-flag",
        type=float,
        metavar="T",
        help="Fixed structural_score threshold for flagging (default: 0.2)",
    )

    args = parser.parse_args()
    if args.command == "offline":
        cmd_offline(args)


if __name__ == "__main__":
    main()
