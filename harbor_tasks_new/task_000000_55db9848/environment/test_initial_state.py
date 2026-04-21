# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the disk inventory processing task.
"""

import os
import pytest


class TestInitialState:
    """Test suite to validate the initial filesystem state."""

    def test_home_directory_exists(self):
        """Verify that /home/user directory exists."""
        home_path = "/home/user"
        assert os.path.isdir(home_path), f"Home directory {home_path} does not exist"

    def test_home_directory_is_writable(self):
        """Verify that /home/user is writable."""
        home_path = "/home/user"
        assert os.access(home_path, os.W_OK), f"Home directory {home_path} is not writable"

    def test_disk_inventory_file_exists(self):
        """Verify that /home/user/disk_inventory.txt exists."""
        inventory_path = "/home/user/disk_inventory.txt"
        assert os.path.isfile(inventory_path), (
            f"Disk inventory file {inventory_path} does not exist. "
            "This file should contain the output of 'du -ab /var/data'."
        )

    def test_disk_inventory_file_is_readable(self):
        """Verify that /home/user/disk_inventory.txt is readable."""
        inventory_path = "/home/user/disk_inventory.txt"
        assert os.access(inventory_path, os.R_OK), (
            f"Disk inventory file {inventory_path} is not readable."
        )

    def test_disk_inventory_file_not_empty(self):
        """Verify that /home/user/disk_inventory.txt is not empty."""
        inventory_path = "/home/user/disk_inventory.txt"
        file_size = os.path.getsize(inventory_path)
        assert file_size > 0, (
            f"Disk inventory file {inventory_path} is empty. "
            "It should contain du -ab output data."
        )

    def test_disk_inventory_file_has_correct_format(self):
        """Verify that disk_inventory.txt has the correct du -ab format."""
        inventory_path = "/home/user/disk_inventory.txt"
        with open(inventory_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) > 0, "Disk inventory file has no lines."

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            assert len(parts) == 2, (
                f"Line {i+1} in disk_inventory.txt is not in correct format. "
                f"Expected '<bytes>\\t<path>', got: '{line}'"
            )
            bytes_str, path = parts
            assert bytes_str.isdigit(), (
                f"Line {i+1} in disk_inventory.txt has non-numeric bytes value: '{bytes_str}'"
            )
            assert path.startswith('/var/data'), (
                f"Line {i+1} in disk_inventory.txt has path not under /var/data: '{path}'"
            )

    def test_disk_inventory_contains_expected_entries(self):
        """Verify that disk_inventory.txt contains the expected data entries."""
        inventory_path = "/home/user/disk_inventory.txt"
        with open(inventory_path, 'r') as f:
            content = f.read()

        # Check for some expected paths that should be in the file
        expected_paths = [
            "/var/data/logs/app.log",
            "/var/data/backups/full_backup.tar.gz",
            "/var/data/cache/session_data.db",
            "/var/data/uploads/document.pdf",
            "/var/data/archives/2023_archive.tar.gz",
        ]

        for path in expected_paths:
            assert path in content, (
                f"Expected path '{path}' not found in disk_inventory.txt. "
                "The file may not contain the correct inventory data."
            )

    def test_reports_directory_does_not_exist(self):
        """Verify that /home/user/reports/ directory does NOT exist initially."""
        reports_path = "/home/user/reports"
        assert not os.path.exists(reports_path), (
            f"Reports directory {reports_path} already exists. "
            "It should NOT exist before the student performs the task. "
            "The student is expected to create this directory."
        )

    def test_python3_available(self):
        """Verify that Python 3 is available."""
        import subprocess
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python 3 is not available. "
            f"Error: {result.stderr}"
        )

    def test_awk_available(self):
        """Verify that awk is available."""
        import subprocess
        result = subprocess.run(
            ["which", "awk"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "awk is not available on this system."

    def test_sort_available(self):
        """Verify that sort is available."""
        import subprocess
        result = subprocess.run(
            ["which", "sort"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "sort is not available on this system."

    def test_grep_available(self):
        """Verify that grep is available."""
        import subprocess
        result = subprocess.run(
            ["which", "grep"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "grep is not available on this system."
