# test_final_state.py
"""
Tests to validate the final state of the system after the student has fixed
the purge_old_runs.py script and successfully cleaned up old experiment runs.
"""

import os
import json
import subprocess
import pytest
from pathlib import Path
from datetime import datetime


# Constants
HOME_DIR = Path("/home/user")
OPS_DIR = HOME_DIR / "ops"
PURGE_SCRIPT = OPS_DIR / "purge_old_runs.py"
DATA_DIR = Path("/data/experiments")
EXPECTED_PROJECTS = ["llm-finetune", "vision-cls", "rl-baseline"]
CUTOFF_DATE = "2024-02-19"  # 30 days before reference date 2024-03-20


def get_all_run_dirs():
    """Helper to get all run directories that currently exist."""
    run_dirs = []
    for project in EXPECTED_PROJECTS:
        project_path = DATA_DIR / project
        if project_path.exists():
            for run_dir in project_path.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith("run_"):
                    run_dirs.append(run_dir)
    return run_dirs


def get_run_created_at(run_dir):
    """Helper to get created_at date string from a run's metadata.json."""
    metadata_path = run_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            data = json.load(f)
        created_at = data.get("created_at", "")
        if created_at:
            # Extract just the date part
            return created_at.split("T")[0]
    return None


class TestScriptExecution:
    """Tests that the fixed script executes correctly."""

    def test_script_exists(self):
        """The purge script must still exist."""
        assert PURGE_SCRIPT.exists(), f"Script {PURGE_SCRIPT} does not exist"

    def test_script_exits_zero(self):
        """Running the script should exit with code 0."""
        result = subprocess.run(
            ["python3", str(PURGE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, \
            f"Script exited with code {result.returncode}. Stderr: {result.stderr}"

    def test_script_is_idempotent(self):
        """Running the script twice should be idempotent (second run deletes nothing, exits 0)."""
        # First run
        result1 = subprocess.run(
            ["python3", str(PURGE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result1.returncode == 0, f"First run failed with code {result1.returncode}"

        # Get state after first run
        runs_after_first = set(str(r) for r in get_all_run_dirs())

        # Second run
        result2 = subprocess.run(
            ["python3", str(PURGE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result2.returncode == 0, f"Second run failed with code {result2.returncode}"

        # Get state after second run
        runs_after_second = set(str(r) for r in get_all_run_dirs())

        # Should be identical
        assert runs_after_first == runs_after_second, \
            "Script is not idempotent - second run changed the state"


class TestOldRunsDeleted:
    """Tests that old runs (before cutoff date) have been deleted."""

    def test_no_january_2024_runs_remain(self):
        """No runs from January 2024 should remain."""
        jan_runs = []
        for run_dir in get_all_run_dirs():
            date_str = get_run_created_at(run_dir)
            if date_str and date_str.startswith("2024-01"):
                jan_runs.append(run_dir)
        assert len(jan_runs) == 0, \
            f"Found {len(jan_runs)} runs from January 2024 that should have been deleted: {jan_runs}"

    def test_no_old_runs_remain(self):
        """No runs older than 30 days (before 2024-02-19) should remain."""
        old_runs = []
        for run_dir in get_all_run_dirs():
            date_str = get_run_created_at(run_dir)
            if date_str and date_str < CUTOFF_DATE:
                old_runs.append((run_dir, date_str))
        assert len(old_runs) == 0, \
            f"Found {len(old_runs)} old runs that should have been deleted: {old_runs}"

    def test_find_no_old_metadata_files(self):
        """Using find to verify no metadata.json files reference January 2024."""
        result = subprocess.run(
            ["find", str(DATA_DIR), "-name", "metadata.json", "-exec", "grep", "-l", "2024-01", "{}", ";"],
            capture_output=True,
            text=True
        )
        # grep -l returns files that match; if none match, find returns empty
        matching_files = result.stdout.strip()
        assert matching_files == "", \
            f"Found metadata.json files still referencing 2024-01: {matching_files}"


class TestRecentRunsPreserved:
    """Tests that recent runs (on or after cutoff date) have been preserved."""

    def test_recent_runs_still_exist(self):
        """Runs with created_at >= 2024-02-19 should still exist."""
        recent_runs = []
        for run_dir in get_all_run_dirs():
            date_str = get_run_created_at(run_dir)
            if date_str and date_str >= CUTOFF_DATE:
                recent_runs.append(run_dir)
        assert len(recent_runs) >= 6, \
            f"Expected at least 6 recent runs to remain, found {len(recent_runs)}"

    def test_recent_runs_have_intact_structure(self):
        """Recent runs should have their directory structure intact."""
        for run_dir in get_all_run_dirs():
            date_str = get_run_created_at(run_dir)
            if date_str and date_str >= CUTOFF_DATE:
                # Check required subdirectories exist
                assert (run_dir / "metadata.json").exists(), \
                    f"metadata.json missing in preserved run {run_dir}"
                assert (run_dir / "checkpoints").is_dir(), \
                    f"checkpoints/ directory missing in preserved run {run_dir}"
                assert (run_dir / "logs").is_dir(), \
                    f"logs/ directory missing in preserved run {run_dir}"
                assert (run_dir / "outputs").is_dir(), \
                    f"outputs/ directory missing in preserved run {run_dir}"

    def test_recent_runs_metadata_valid(self):
        """Recent runs should have valid metadata.json files."""
        for run_dir in get_all_run_dirs():
            metadata_path = run_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path) as f:
                        data = json.load(f)
                    # Check required fields
                    assert "run_id" in data, f"run_id missing in {metadata_path}"
                    assert "created_at" in data, f"created_at missing in {metadata_path}"
                    assert "project" in data, f"project missing in {metadata_path}"
                    assert "status" in data, f"status missing in {metadata_path}"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {metadata_path}: {e}")


class TestDeletionCount:
    """Tests for the correct number of deletions."""

    def test_minimum_runs_deleted(self):
        """At least 8 old runs should have been deleted (fewer than 18 total remain)."""
        # Original state had 5-8 runs per project (3 projects) = 15-24 runs
        # At least 8 should be deleted, so at most 16 should remain
        # But we also know at least 6 recent runs should remain
        current_runs = get_all_run_dirs()
        # We expect 6-10 runs to remain (the recent ones)
        assert len(current_runs) <= 16, \
            f"Too many runs remain ({len(current_runs)}), expected at most 16 after deleting old runs"

    def test_minimum_runs_remain(self):
        """At least 6 recent runs should remain."""
        current_runs = get_all_run_dirs()
        assert len(current_runs) >= 6, \
            f"Too few runs remain ({len(current_runs)}), expected at least 6 recent runs"


class TestDiskSpaceReclaimed:
    """Tests that disk space has been reclaimed."""

    def test_disk_usage_reduced(self):
        """Disk usage should be measurably reduced (under 700MB)."""
        result = subprocess.run(
            ["du", "-sb", str(DATA_DIR)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"du command failed: {result.stderr}"
        size_bytes = int(result.stdout.split()[0])
        # Should be under 700MB (700 * 1024 * 1024 = 734003200)
        max_size = 700 * 1024 * 1024
        assert size_bytes < max_size, \
            f"Disk usage should be under 700MB after cleanup, found {size_bytes / (1024*1024):.1f}MB"


class TestScriptNotHardcoded:
    """Tests that the script wasn't replaced with a hardcoded solution."""

    def test_script_still_has_logic(self):
        """The script should still contain date comparison logic."""
        content = PURGE_SCRIPT.read_text()
        # Should have some form of date/time handling
        has_datetime_logic = any(term in content for term in [
            "datetime", "timedelta", "created_at", "30", "days"
        ])
        assert has_datetime_logic, \
            "Script appears to have lost its date comparison logic"

    def test_script_not_just_rm_rf(self):
        """The script should not be just a hardcoded rm -rf command."""
        content = PURGE_SCRIPT.read_text()
        # Check it's not just a simple shell command wrapper
        assert "rm -rf" not in content or "shutil" in content, \
            "Script appears to be a simple rm -rf wrapper instead of proper logic"
        # Should still iterate over directories
        has_iteration = any(term in content for term in [
            "for ", "walk", "iterdir", "listdir", "glob"
        ])
        assert has_iteration, \
            "Script should iterate over directories, not use hardcoded paths"

    def test_script_reads_metadata(self):
        """The script should still read metadata.json files."""
        content = PURGE_SCRIPT.read_text()
        assert "metadata.json" in content or "metadata" in content, \
            "Script should read metadata.json files to determine run age"

    def test_script_uses_proper_deletion(self):
        """The script should use proper directory deletion (shutil.rmtree or similar)."""
        content = PURGE_SCRIPT.read_text()
        # Should use shutil.rmtree for directory deletion (bug #3 fix)
        has_proper_deletion = "shutil.rmtree" in content or "rmtree" in content
        assert has_proper_deletion, \
            "Script should use shutil.rmtree() for directory deletion, not os.remove()"


class TestProjectStructureIntact:
    """Tests that the project directory structure is intact."""

    def test_all_projects_still_exist(self):
        """All three project directories should still exist."""
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            assert project_path.exists(), \
                f"Project directory {project_path} was incorrectly deleted"
            assert project_path.is_dir(), \
                f"{project_path} is not a directory"

    def test_each_project_has_remaining_runs(self):
        """Each project should have at least one remaining run."""
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            run_dirs = [d for d in project_path.iterdir() if d.is_dir() and d.name.startswith("run_")]
            assert len(run_dirs) >= 1, \
                f"Project {project} has no remaining runs - recent runs may have been incorrectly deleted"


class TestThirtyDayThresholdPreserved:
    """Tests that the 30-day threshold logic is preserved."""

    def test_runs_near_cutoff_handled_correctly(self):
        """Runs very close to the cutoff date should be handled correctly."""
        for run_dir in get_all_run_dirs():
            date_str = get_run_created_at(run_dir)
            if date_str:
                # All remaining runs should be on or after cutoff
                assert date_str >= CUTOFF_DATE, \
                    f"Run {run_dir} with date {date_str} should have been deleted (before {CUTOFF_DATE})"

    def test_february_19_or_later_preserved(self):
        """Runs from February 19, 2024 or later should be preserved."""
        preserved_dates = set()
        for run_dir in get_all_run_dirs():
            date_str = get_run_created_at(run_dir)
            if date_str:
                preserved_dates.add(date_str)

        # Check that we have runs from various dates >= cutoff
        dates_on_or_after_cutoff = [d for d in preserved_dates if d >= CUTOFF_DATE]
        assert len(dates_on_or_after_cutoff) > 0, \
            "No runs with dates on or after 2024-02-19 were preserved"
