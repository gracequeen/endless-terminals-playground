"""Offline task conformance and semantic quality checks."""

from __future__ import annotations

import ast
import re
import statistics
import tomllib  # Python 3.11+
from dataclasses import dataclass
from pathlib import Path

from auditor import Decision, TaskAuditResult

# ---------------------------------------------------------------------------
# Gate criteria
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateCriteria:
    """Configurable thresholds for the offline gate."""

    structural_reject: float = 0.0
    structural_flag: float = 0.2
    desc_overlap_reject: float = 0.0
    assert_diversity_flag: int = 2


def build_gate_criteria(
    *,
    structural_reject: float = 0.0,
    structural_flag: float | None = None,
    percentile_flag: float | None = None,
    scores: list[float] | None = None,
    desc_overlap_reject: float = 0.0,
    assert_diversity_flag: int = 2,
) -> GateCriteria:
    """Build GateCriteria with either a fixed or percentile-based flag threshold.

    Args:
        structural_reject: Tasks at or below this score are rejected. Default 0.0.
        structural_flag: Fixed flag threshold. Mutually exclusive with percentile_flag.
        percentile_flag: Bottom-N fraction of dataset to flag (e.g. 0.2 = bottom 20%).
            Requires ``scores`` to compute the threshold.
        scores: List of structural scores from the dataset. Required when
            percentile_flag is given.
        desc_overlap_reject: Tasks at or below this desc_overlap are rejected.
        assert_diversity_flag: Tasks with fewer distinct categories are flagged.

    Returns:
        GateCriteria with resolved thresholds.
    """
    if structural_flag is not None and percentile_flag is not None:
        raise ValueError("structural_flag and percentile_flag are mutually exclusive")

    if percentile_flag is not None:
        if scores is None or len(scores) == 0:
            raise ValueError("scores must be provided when using percentile_flag")
        sorted_scores = sorted(scores)
        if percentile_flag == 0.0:
            resolved_flag = 0.0
        else:
            idx = max(0, int(len(sorted_scores) * percentile_flag) - 1)
            resolved_flag = sorted_scores[idx]
    elif structural_flag is not None:
        resolved_flag = structural_flag
    else:
        resolved_flag = 0.2

    return GateCriteria(
        structural_reject=structural_reject,
        structural_flag=resolved_flag,
        desc_overlap_reject=desc_overlap_reject,
        assert_diversity_flag=assert_diversity_flag,
    )


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

_KEYWORDS: dict[str, list[str]] = {
    "file_exists": [
        "os.path.exists", "os.path.isfile", "os.path.isdir",
        "os.path.islink", ".exists()",
    ],
    "file_content": ["open(", ".read(", ".readlines(", ".read_text(", "file_content"],
    "permissions": ["os.stat", "st_mode", "oct(", "os.access"],
    "process_exit": ["subprocess", "returncode", "Popen", "check_call", "check_output"],
    "stdout_output": ["stdout", "stderr", "capture_output"],
}

_OUTCOME_CATEGORIES = {"process_exit", "stdout_output", "file_content"}


def _assert_nodes(tree: ast.AST) -> list[ast.Assert]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]


def _category(node: ast.Assert) -> str:
    unparsed = ast.unparse(node)
    for category, keywords in _KEYWORDS.items():
        if any(kw in unparsed for kw in keywords):
            return category
    return "other"


def classify_asserts(tree: ast.AST) -> dict[str, int]:
    """Count assert statements by category.

    Args:
        tree: Parsed AST of a test file.

    Returns:
        Dict mapping category name to count.
    """
    counts: dict[str, int] = dict.fromkeys(list(_KEYWORDS) + ["other"], 0)
    for node in _assert_nodes(tree):
        counts[_category(node)] += 1
    return counts


def structural_score(tree: ast.AST) -> float:
    """Fraction of asserts that check task outcomes (not passive state).

    Args:
        tree: Parsed AST of test_final_state.py.

    Returns:
        Float in [0, 1]; 0.0 if there are no assert statements.
    """
    nodes = _assert_nodes(tree)
    if not nodes:
        return 0.0
    outcome = sum(1 for n in nodes if _category(n) in _OUTCOME_CATEGORIES)
    return outcome / len(nodes)


def assert_diversity(tree: ast.AST) -> int:
    """Number of distinct assert categories used.

    Args:
        tree: Parsed AST of test_final_state.py.

    Returns:
        Count of distinct categories (including "other").
    """
    categories = {_category(n) for n in _assert_nodes(tree)}
    return len(categories)


# ---------------------------------------------------------------------------
# Description overlap
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "are", "has", "have",
    "not", "its", "from", "will", "can", "into", "you", "your", "all",
    "task", "test", "check", "verify", "file", "assert", "should", "must",
}


def _extract_keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


def desc_overlap(test_tree: ast.AST, instruction_text: str) -> float:
    """Fraction of asserts referencing at least one keyword from the instruction.

    Args:
        test_tree: Parsed AST of test_final_state.py.
        instruction_text: Raw text of instruction.md.

    Returns:
        Float in [0, 1]; 0.0 if there are no assert statements.
    """
    nodes = _assert_nodes(test_tree)
    if not nodes:
        return 0.0
    keywords = _extract_keywords(instruction_text)
    if not keywords:
        return 0.0
    hits = sum(
        1 for n in nodes
        if any(kw in ast.unparse(n).lower() for kw in keywords)
    )
    return hits / len(nodes)


# ---------------------------------------------------------------------------
# Required files / metadata
# ---------------------------------------------------------------------------

_REQUIRED_FILES = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "environment/task.json",
    "environment/test_initial_state.py",
    "tests/test_final_state.py",
    "tests/test.sh",
]

_VALID_DIFFICULTIES = {"easy", "medium", "hard", "intricate"}


# ---------------------------------------------------------------------------
# check_task
# ---------------------------------------------------------------------------

_DEFAULT_CRITERIA = GateCriteria()


def check_task(
    task_dir: Path,
    criteria: GateCriteria | None = None,
) -> TaskAuditResult:
    """Run all offline checks on a single task directory.

    Args:
        task_dir: Path to a task directory following the Harbor layout.
        criteria: Gate thresholds. Uses spec defaults if None.

    Returns:
        TaskAuditResult with decision, metrics, and flags.
    """
    if criteria is None:
        criteria = _DEFAULT_CRITERIA

    task_id = task_dir.name
    decision = Decision.PASS
    flags: list[str] = []
    metrics: dict = {}

    def _reject(flag: str) -> None:
        nonlocal decision
        flags.append(flag)
        decision = Decision.REJECT

    def _flag(flag: str) -> None:
        nonlocal decision
        flags.append(flag)
        if decision != Decision.REJECT:
            decision = Decision.FLAG

    # 1. Schema conformance
    for rel in _REQUIRED_FILES:
        if not (task_dir / rel).exists():
            _reject(f"missing_file:{rel}")

    if decision == Decision.REJECT:
        return TaskAuditResult(task_id=task_id, task_dir=task_dir,
                               decision=decision, metrics=metrics, flags=flags)

    # 2. Syntax validity — cache parsed trees for reuse in step 4
    parsed: dict[str, ast.AST] = {}
    for rel in ("environment/test_initial_state.py", "tests/test_final_state.py"):
        path = task_dir / rel
        try:
            parsed[rel] = ast.parse(path.read_text())
        except SyntaxError:
            _reject(f"syntax_error:{rel}")
        except (OSError, UnicodeDecodeError):
            _reject(f"unreadable_file:{rel}")

    if decision == Decision.REJECT:
        return TaskAuditResult(task_id=task_id, task_dir=task_dir,
                               decision=decision, metrics=metrics, flags=flags)

    # 3. Metadata validity
    try:
        toml_data = tomllib.loads((task_dir / "task.toml").read_text())
        meta = toml_data.get("metadata", {})
        difficulty = meta.get("difficulty", "")
        category = meta.get("category", "")
        if not difficulty or not category:
            _flag("missing_metadata")
        elif difficulty not in _VALID_DIFFICULTIES:
            _flag(f"invalid_difficulty:{difficulty}")
        metrics["difficulty"] = difficulty
        metrics["category"] = category
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError):
        _flag("toml_parse_error")
        metrics["difficulty"] = ""
        metrics["category"] = ""

    # 4. AST metrics on test_final_state.py — reuse tree cached in step 2
    final_tree = parsed["tests/test_final_state.py"]

    s_score = structural_score(final_tree)
    d_score = desc_overlap(
        final_tree,
        (task_dir / "instruction.md").read_text(),
    )
    a_diversity = assert_diversity(final_tree)
    assert_counts = classify_asserts(final_tree)
    total_asserts = sum(assert_counts.values())

    metrics.update({
        "structural_score": s_score,
        "desc_overlap": d_score,
        "assert_diversity": a_diversity,
        "assert_count": total_asserts,
        **{f"assert_{k}": v for k, v in assert_counts.items()},
    })

    # structural_score checks
    if s_score <= criteria.structural_reject:
        _reject("structural_score_zero")
    elif s_score < criteria.structural_flag:
        _flag("structural_score_low")

    # desc_overlap check
    if d_score <= criteria.desc_overlap_reject:
        _reject("desc_overlap_zero")

    # assert_diversity check
    if a_diversity < criteria.assert_diversity_flag:
        _flag("assert_diversity_low")

    return TaskAuditResult(
        task_id=task_id,
        task_dir=task_dir,
        decision=decision,
        metrics=metrics,
        flags=flags,
    )


# ---------------------------------------------------------------------------
# check_batch + dataset_summary
# ---------------------------------------------------------------------------

def check_batch(
    task_dirs: list[Path],
    criteria: GateCriteria | None = None,
) -> list[TaskAuditResult]:
    """Run offline checks on a list of task directories.

    Args:
        task_dirs: Task directories to audit.
        criteria: Gate thresholds. Uses spec defaults if None.

    Returns:
        Aligned list of TaskAuditResult.
    """
    return [check_task(d, criteria) for d in task_dirs]


def dataset_summary(results: list[TaskAuditResult]) -> dict:
    """Compute dataset-level aggregate statistics.

    Args:
        results: List of TaskAuditResult from check_batch.

    Returns:
        Dict with total/pass/flag/reject counts, score statistics,
        domain_distribution, and difficulty_distribution.
    """
    total = len(results)
    counts = dict.fromkeys(Decision, 0)
    for r in results:
        counts[r.decision] += 1

    s_scores = [
        r.metrics["structural_score"] for r in results if "structural_score" in r.metrics
    ]
    d_scores = [
        r.metrics["desc_overlap"] for r in results if "desc_overlap" in r.metrics
    ]

    domain_dist: dict[str, int] = {}
    diff_dist: dict[str, int] = {}
    for r in results:
        cat = r.metrics.get("category", "unknown") or "unknown"
        diff = r.metrics.get("difficulty", "unknown") or "unknown"
        domain_dist[cat] = domain_dist.get(cat, 0) + 1
        diff_dist[diff] = diff_dist.get(diff, 0) + 1

    return {
        "total": total,
        "pass": counts[Decision.PASS],
        "flag": counts[Decision.FLAG],
        "reject": counts[Decision.REJECT],
        "mean_structural_score": statistics.mean(s_scores) if s_scores else 0.0,
        "median_structural_score": statistics.median(s_scores) if s_scores else 0.0,
        "mean_desc_overlap": statistics.mean(d_scores) if d_scores else 0.0,
        "domain_distribution": domain_dist,
        "difficulty_distribution": diff_dist,
    }
