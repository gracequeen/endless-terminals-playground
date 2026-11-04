"""Task data quality auditor — shared data model."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Decision(StrEnum):
    """Audit decision for a single task."""

    PASS = "pass"
    FLAG = "flag"
    REJECT = "reject"


@dataclass
class TaskAuditResult:
    """Result of auditing a single task directory."""

    task_id: str
    task_dir: Path
    decision: Decision
    metrics: dict = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
