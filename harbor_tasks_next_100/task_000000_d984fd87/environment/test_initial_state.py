# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the cleanup task.
Verifies the presence of the buggy purge script, the experiment directory structure,
and the expected metadata files with various timestamp formats.
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
PURGE_LOG = OPS_DIR / "purge_old_runs.log"
DATA_DIR = Path("/data/experiments")
EXPECTED_PROJECTS = ["llm-finetune", "vision-cls", "rl-baseline"]


class TestPurgeScriptExists:
    """Tests for the purge script existence and properties."""

    def test_ops_directory_exists(self):
        """The /home/user/ops directory must exist."""
        assert OPS_DIR.exists(), f"Directory {OPS_DIR} does not exist"
        assert OPS_DIR.is_dir(), f"{OPS_DIR} is not a directory"

    def test_purge_script_exists(self):
        """The purge_old_runs.py script must exist."""
        assert PURGE_SCRIPT.exists(), f"Script {PURGE_SCRIPT} does not exist"
        assert PURGE_SCRIPT.is_file(), f"{PURGE_SCRIPT} is not a file"

    def test_purge_script_is_readable(self):
        """The purge script must be readable."""
        assert os.access(PURGE_SCRIPT, os.R_OK), f"Script {PURGE_SCRIPT} is not readable"

    def test_purge_script_is_python(self):
        """The purge script should be a Python file."""
        content = PURGE_SCRIPT.read_text()
        # Should contain Python-like syntax
        assert "import" in content or "def " in content or "class " in content, \
            f"Script {PURGE_SCRIPT} does not appear to be a Python file"

    def test_purge_log_exists(self):
        """The purge log file should exist with recent entries."""
        assert PURGE_LOG.exists(), f"Log file {PURGE_LOG} does not exist"
        content = PURGE_LOG.read_text()
        assert len(content) > 0, f"Log file {PURGE_LOG} is empty"
        # Should have processing entries
        assert "Processing" in content or "processing" in content or "skipped" in content, \
            f"Log file {PURGE_LOG} does not contain expected processing entries"


class TestPythonEnvironment:
    """Tests for Python environment."""

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "python3 is not available"
        version_str = result.stdout.strip()
        assert "Python 3" in version_str, f"Expected Python 3, got: {version_str}"

    def test_python_version_3_10_plus(self):
        """Python version should be 3.10 or higher."""
        result = subprocess.run(
            ["python3", "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, "Failed to get Python version"
        version = result.stdout.strip()
        major, minor = map(int, version.split('.'))
        assert major >= 3 and minor >= 10, f"Python version should be 3.10+, got {version}"


class TestExperimentsDirectoryStructure:
    """Tests for the /data/experiments directory structure."""

    def test_data_experiments_exists(self):
        """The /data/experiments directory must exist."""
        assert DATA_DIR.exists(), f"Directory {DATA_DIR} does not exist"
        assert DATA_DIR.is_dir(), f"{DATA_DIR} is not a directory"

    def test_expected_projects_exist(self):
        """All expected project directories must exist."""
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            assert project_path.exists(), f"Project directory {project_path} does not exist"
            assert project_path.is_dir(), f"{project_path} is not a directory"

    def test_each_project_has_run_directories(self):
        """Each project should have 5-8 run directories."""
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            run_dirs = [d for d in project_path.iterdir() if d.is_dir() and d.name.startswith("run_")]
            assert 5 <= len(run_dirs) <= 8, \
                f"Project {project} should have 5-8 run directories, found {len(run_dirs)}"

    def test_run_directory_naming_convention(self):
        """Run directories should follow the naming pattern run_YYYYMMDD_xxxx."""
        import re
        pattern = re.compile(r"run_\d{8}_[a-z0-9]+")
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            for run_dir in project_path.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith("run_"):
                    assert pattern.match(run_dir.name), \
                        f"Run directory {run_dir.name} does not match expected pattern run_YYYYMMDD_xxxx"


class TestRunDirectoryContents:
    """Tests for the contents of run directories."""

    def get_all_run_dirs(self):
        """Helper to get all run directories."""
        run_dirs = []
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            for run_dir in project_path.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith("run_"):
                    run_dirs.append(run_dir)
        return run_dirs

    def test_each_run_has_metadata_json(self):
        """Each run directory must have a metadata.json file."""
        for run_dir in self.get_all_run_dirs():
            metadata_path = run_dir / "metadata.json"
            assert metadata_path.exists(), f"metadata.json missing in {run_dir}"
            assert metadata_path.is_file(), f"{metadata_path} is not a file"

    def test_each_run_has_checkpoints_directory(self):
        """Each run directory should have a checkpoints/ directory."""
        for run_dir in self.get_all_run_dirs():
            checkpoints_path = run_dir / "checkpoints"
            assert checkpoints_path.exists(), f"checkpoints/ directory missing in {run_dir}"
            assert checkpoints_path.is_dir(), f"{checkpoints_path} is not a directory"

    def test_each_run_has_logs_directory(self):
        """Each run directory should have a logs/ directory."""
        for run_dir in self.get_all_run_dirs():
            logs_path = run_dir / "logs"
            assert logs_path.exists(), f"logs/ directory missing in {run_dir}"
            assert logs_path.is_dir(), f"{logs_path} is not a directory"

    def test_each_run_has_outputs_directory(self):
        """Each run directory should have an outputs/ directory."""
        for run_dir in self.get_all_run_dirs():
            outputs_path = run_dir / "outputs"
            assert outputs_path.exists(), f"outputs/ directory missing in {run_dir}"
            assert outputs_path.is_dir(), f"{outputs_path} is not a directory"

    def test_checkpoints_contain_pt_files(self):
        """Checkpoints directories should contain .pt files."""
        has_pt_files = False
        for run_dir in self.get_all_run_dirs():
            checkpoints_path = run_dir / "checkpoints"
            pt_files = list(checkpoints_path.glob("*.pt"))
            if pt_files:
                has_pt_files = True
                break
        assert has_pt_files, "No .pt checkpoint files found in any run directory"


class TestMetadataJsonStructure:
    """Tests for the metadata.json file structure and content."""

    def get_all_metadata_files(self):
        """Helper to get all metadata.json files."""
        metadata_files = []
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            for run_dir in project_path.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith("run_"):
                    metadata_path = run_dir / "metadata.json"
                    if metadata_path.exists():
                        metadata_files.append(metadata_path)
        return metadata_files

    def test_metadata_is_valid_json(self):
        """All metadata.json files must be valid JSON."""
        for metadata_path in self.get_all_metadata_files():
            try:
                with open(metadata_path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {metadata_path}: {e}")

    def test_metadata_has_required_fields(self):
        """All metadata.json files must have required fields."""
        required_fields = ["run_id", "created_at", "project", "status"]
        for metadata_path in self.get_all_metadata_files():
            with open(metadata_path) as f:
                data = json.load(f)
            for field in required_fields:
                assert field in data, f"Missing field '{field}' in {metadata_path}"

    def test_metadata_created_at_format(self):
        """created_at should be in ISO format (with Z or +00:00 suffix)."""
        import re
        # Pattern for ISO format with Z or timezone offset
        pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})")
        for metadata_path in self.get_all_metadata_files():
            with open(metadata_path) as f:
                data = json.load(f)
            created_at = data.get("created_at", "")
            assert pattern.match(created_at), \
                f"created_at '{created_at}' in {metadata_path} does not match expected ISO format"

    def test_has_old_runs_with_z_suffix(self):
        """There should be runs with 'Z' suffix timestamps (to trigger bug #1)."""
        z_suffix_count = 0
        for metadata_path in self.get_all_metadata_files():
            with open(metadata_path) as f:
                data = json.load(f)
            if data.get("created_at", "").endswith("Z"):
                z_suffix_count += 1
        assert z_suffix_count > 0, "No metadata files found with 'Z' suffix timestamps"

    def test_has_runs_with_timezone_offset(self):
        """There should be some runs with '+00:00' timezone offset (to trigger bug #2)."""
        offset_count = 0
        for metadata_path in self.get_all_metadata_files():
            with open(metadata_path) as f:
                data = json.load(f)
            if "+00:00" in data.get("created_at", ""):
                offset_count += 1
        assert offset_count > 0, "No metadata files found with '+00:00' timezone offset"


class TestRunAgeDistribution:
    """Tests for the distribution of run ages."""

    def get_all_created_at_dates(self):
        """Helper to get all created_at dates from metadata files."""
        dates = []
        for project in EXPECTED_PROJECTS:
            project_path = DATA_DIR / project
            for run_dir in project_path.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith("run_"):
                    metadata_path = run_dir / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path) as f:
                            data = json.load(f)
                        created_at = data.get("created_at", "")
                        # Parse the date part only
                        if created_at:
                            date_str = created_at.split("T")[0]
                            dates.append((run_dir, date_str))
        return dates

    def test_has_runs_older_than_30_days(self):
        """There should be runs with created_at older than 30 days from 2024-03-20."""
        # Reference date is 2024-03-20, so 30 days before is 2024-02-19
        cutoff = "2024-02-19"
        old_runs = []
        for run_dir, date_str in self.get_all_created_at_dates():
            if date_str < cutoff:
                old_runs.append(run_dir)
        assert len(old_runs) >= 8, \
            f"Expected at least 8 runs older than 30 days (before {cutoff}), found {len(old_runs)}"

    def test_has_recent_runs(self):
        """There should be runs with created_at within 30 days of 2024-03-20."""
        cutoff = "2024-02-19"
        recent_runs = []
        for run_dir, date_str in self.get_all_created_at_dates():
            if date_str >= cutoff:
                recent_runs.append(run_dir)
        assert len(recent_runs) >= 6, \
            f"Expected at least 6 recent runs (on or after {cutoff}), found {len(recent_runs)}"

    def test_has_january_2024_runs(self):
        """There should be runs from January 2024 (definitely old)."""
        jan_runs = []
        for run_dir, date_str in self.get_all_created_at_dates():
            if date_str.startswith("2024-01"):
                jan_runs.append(run_dir)
        assert len(jan_runs) > 0, "No runs found from January 2024"

    def test_has_february_2024_runs(self):
        """There should be runs from February 2024."""
        feb_runs = []
        for run_dir, date_str in self.get_all_created_at_dates():
            if date_str.startswith("2024-02"):
                feb_runs.append(run_dir)
        assert len(feb_runs) > 0, "No runs found from February 2024"


class TestScriptBugs:
    """Tests to verify the script has the expected bugs."""

    def test_script_uses_fromisoformat(self):
        """The script should use datetime.fromisoformat() (bug #1 setup)."""
        content = PURGE_SCRIPT.read_text()
        assert "fromisoformat" in content, \
            "Script does not use fromisoformat() - expected for bug #1"

    def test_script_uses_datetime_now(self):
        """The script should use datetime.now() without timezone (bug #2 setup)."""
        content = PURGE_SCRIPT.read_text()
        assert "datetime.now()" in content or "now()" in content, \
            "Script does not appear to use datetime.now()"

    def test_script_uses_os_remove(self):
        """The script should use os.remove() on directories (bug #3 setup)."""
        content = PURGE_SCRIPT.read_text()
        assert "os.remove" in content, \
            "Script does not use os.remove() - expected for bug #3"

    def test_script_has_broad_exception_handling(self):
        """The script should have broad exception handling that hides errors."""
        content = PURGE_SCRIPT.read_text()
        assert "except" in content, "Script does not have exception handling"
        # Check for broad exception patterns
        has_broad_except = (
            "except Exception" in content or
            "except:" in content
        )
        assert has_broad_except, \
            "Script does not have broad exception handling (except Exception or bare except)"


class TestDiskUsage:
    """Tests for disk usage and data size."""

    def test_experiments_has_significant_data(self):
        """The experiments directory should have significant data (around 1.5GB)."""
        result = subprocess.run(
            ["du", "-sb", str(DATA_DIR)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"du command failed: {result.stderr}"
        size_bytes = int(result.stdout.split()[0])
        # Should be at least 500MB (500 * 1024 * 1024)
        min_size = 500 * 1024 * 1024
        assert size_bytes >= min_size, \
            f"Experiments directory should have at least 500MB of data, found {size_bytes / (1024*1024):.1f}MB"

    def test_required_tools_available(self):
        """Required tools (du, find) should be available."""
        for tool in ["du", "find"]:
            result = subprocess.run(["which", tool], capture_output=True)
            assert result.returncode == 0, f"Required tool '{tool}' is not available"


class TestWritePermissions:
    """Tests for write permissions."""

    def test_data_experiments_writable(self):
        """The /data/experiments directory should be writable."""
        assert os.access(DATA_DIR, os.W_OK), f"{DATA_DIR} is not writable"

    def test_ops_directory_writable(self):
        """The /home/user/ops directory should be writable."""
        assert os.access(OPS_DIR, os.W_OK), f"{OPS_DIR} is not writable"

    def test_purge_script_writable(self):
        """The purge script should be writable (for fixing)."""
        assert os.access(PURGE_SCRIPT, os.W_OK), f"{PURGE_SCRIPT} is not writable"
