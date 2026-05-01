# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the rsync task to sync CSV files from /home/user/reports/ to /home/user/backup/reports/.
"""

import os
import subprocess
import pytest


class TestInitialDirectoryStructure:
    """Test that the required directory structure exists."""

    def test_reports_directory_exists(self):
        """Verify /home/user/reports/ directory exists."""
        path = "/home/user/reports"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_backup_directory_exists(self):
        """Verify /home/user/backup/ directory exists."""
        path = "/home/user/backup"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_backup_reports_does_not_exist(self):
        """Verify /home/user/backup/reports/ does NOT exist yet."""
        path = "/home/user/backup/reports"
        assert not os.path.exists(path), f"Directory {path} should not exist yet (it's the target to be created)"

    def test_q1_subdirectory_exists(self):
        """Verify /home/user/reports/q1/ subdirectory exists."""
        path = "/home/user/reports/q1"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_q2_subdirectory_exists(self):
        """Verify /home/user/reports/q2/ subdirectory exists."""
        path = "/home/user/reports/q2"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestSourceCSVFiles:
    """Test that all required CSV files exist in the source directory."""

    def test_summary_csv_exists(self):
        """Verify /home/user/reports/summary.csv exists."""
        path = "/home/user/reports/summary.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_q1_sales_csv_exists(self):
        """Verify /home/user/reports/q1/sales.csv exists."""
        path = "/home/user/reports/q1/sales.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_q1_inventory_csv_exists(self):
        """Verify /home/user/reports/q1/inventory.csv exists."""
        path = "/home/user/reports/q1/inventory.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_q2_sales_csv_exists(self):
        """Verify /home/user/reports/q2/sales.csv exists."""
        path = "/home/user/reports/q2/sales.csv"
        assert os.path.isfile(path), f"File {path} does not exist"


class TestSourceXLSXFiles:
    """Test that the xlsx files (temp junk) exist in the source directory."""

    def test_scratch_xlsx_exists(self):
        """Verify /home/user/reports/scratch.xlsx exists."""
        path = "/home/user/reports/scratch.xlsx"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_q1_sales_draft_xlsx_exists(self):
        """Verify /home/user/reports/q1/sales_draft.xlsx exists."""
        path = "/home/user/reports/q1/sales_draft.xlsx"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_q2_notes_xlsx_exists(self):
        """Verify /home/user/reports/q2/notes.xlsx exists."""
        path = "/home/user/reports/q2/notes.xlsx"
        assert os.path.isfile(path), f"File {path} does not exist"


class TestRsyncInstalled:
    """Test that rsync is installed and available."""

    def test_rsync_is_installed(self):
        """Verify rsync command is available."""
        result = subprocess.run(
            ["which", "rsync"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "rsync is not installed or not in PATH"

    def test_rsync_is_executable(self):
        """Verify rsync can be executed."""
        result = subprocess.run(
            ["rsync", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "rsync cannot be executed (version check failed)"


class TestDirectoryPermissions:
    """Test that directories are writable."""

    def test_reports_directory_is_readable(self):
        """Verify /home/user/reports/ is readable."""
        path = "/home/user/reports"
        assert os.access(path, os.R_OK), f"Directory {path} is not readable"

    def test_backup_directory_is_writable(self):
        """Verify /home/user/backup/ is writable."""
        path = "/home/user/backup"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"


class TestSourceFileCount:
    """Test that the source has the expected number of files."""

    def test_source_has_four_csv_files(self):
        """Verify there are exactly 4 CSV files in /home/user/reports/."""
        result = subprocess.run(
            ["find", "/home/user/reports", "-name", "*.csv"],
            capture_output=True,
            text=True
        )
        csv_files = [f for f in result.stdout.strip().split('\n') if f]
        assert len(csv_files) == 4, f"Expected 4 CSV files in source, found {len(csv_files)}: {csv_files}"

    def test_source_has_three_xlsx_files(self):
        """Verify there are exactly 3 XLSX files in /home/user/reports/."""
        result = subprocess.run(
            ["find", "/home/user/reports", "-name", "*.xlsx"],
            capture_output=True,
            text=True
        )
        xlsx_files = [f for f in result.stdout.strip().split('\n') if f]
        assert len(xlsx_files) == 3, f"Expected 3 XLSX files in source, found {len(xlsx_files)}: {xlsx_files}"
