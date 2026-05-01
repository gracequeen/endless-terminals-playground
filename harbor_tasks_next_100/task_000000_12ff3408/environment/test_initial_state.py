# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the disk usage audit task.
"""

import os
import pytest
import stat


class TestVarDataDirectory:
    """Tests for /var/data directory structure and contents."""

    def test_var_data_exists(self):
        """Verify /var/data directory exists."""
        assert os.path.exists("/var/data"), "/var/data directory does not exist"

    def test_var_data_is_directory(self):
        """Verify /var/data is a directory."""
        assert os.path.isdir("/var/data"), "/var/data exists but is not a directory"

    def test_var_data_is_readable(self):
        """Verify /var/data is readable by current user."""
        assert os.access("/var/data", os.R_OK), "/var/data is not readable by current user"

    def test_var_data_is_executable(self):
        """Verify /var/data is traversable (executable) by current user."""
        assert os.access("/var/data", os.X_OK), "/var/data is not traversable (no execute permission)"


class TestExpectedLargeFiles:
    """Tests for the five largest files that should exist."""

    EXPECTED_FILES = {
        "/var/data/archives/backup_2024_q1.tar.gz": 512000000,
        "/var/data/logs/access_full.log": 268435456,
        "/var/data/dumps/postgres_main.sql": 134217728,
        "/var/data/media/training_video.mp4": 104857600,
        "/var/data/exports/customer_data.csv": 52428800,
    }

    @pytest.mark.parametrize("filepath,expected_size", EXPECTED_FILES.items())
    def test_large_file_exists(self, filepath, expected_size):
        """Verify each expected large file exists."""
        assert os.path.exists(filepath), f"Expected file does not exist: {filepath}"

    @pytest.mark.parametrize("filepath,expected_size", EXPECTED_FILES.items())
    def test_large_file_is_regular_file(self, filepath, expected_size):
        """Verify each expected large file is a regular file."""
        assert os.path.isfile(filepath), f"Path exists but is not a regular file: {filepath}"

    @pytest.mark.parametrize("filepath,expected_size", EXPECTED_FILES.items())
    def test_large_file_is_readable(self, filepath, expected_size):
        """Verify each expected large file is readable."""
        assert os.access(filepath, os.R_OK), f"File is not readable: {filepath}"

    @pytest.mark.parametrize("filepath,expected_size", EXPECTED_FILES.items())
    def test_large_file_has_expected_size(self, filepath, expected_size):
        """Verify each expected large file has the correct size."""
        actual_size = os.path.getsize(filepath)
        assert actual_size == expected_size, (
            f"File {filepath} has unexpected size. "
            f"Expected: {expected_size} bytes, Actual: {actual_size} bytes"
        )


class TestDirectoryStructure:
    """Tests for required subdirectories under /var/data."""

    REQUIRED_DIRS = [
        "/var/data/archives",
        "/var/data/logs",
        "/var/data/dumps",
        "/var/data/media",
        "/var/data/exports",
    ]

    @pytest.mark.parametrize("dirpath", REQUIRED_DIRS)
    def test_subdirectory_exists(self, dirpath):
        """Verify required subdirectories exist."""
        assert os.path.exists(dirpath), f"Required directory does not exist: {dirpath}"

    @pytest.mark.parametrize("dirpath", REQUIRED_DIRS)
    def test_subdirectory_is_directory(self, dirpath):
        """Verify required paths are directories."""
        assert os.path.isdir(dirpath), f"Path exists but is not a directory: {dirpath}"


class TestAuditDirectory:
    """Tests for /home/user/audit directory."""

    def test_audit_directory_exists(self):
        """Verify /home/user/audit directory exists."""
        assert os.path.exists("/home/user/audit"), "/home/user/audit directory does not exist"

    def test_audit_directory_is_directory(self):
        """Verify /home/user/audit is a directory."""
        assert os.path.isdir("/home/user/audit"), "/home/user/audit exists but is not a directory"

    def test_audit_directory_is_writable(self):
        """Verify /home/user/audit is writable by current user."""
        assert os.access("/home/user/audit", os.W_OK), "/home/user/audit is not writable by current user"

    def test_top5_file_does_not_exist(self):
        """Verify /home/user/audit/top5.txt does not exist initially."""
        assert not os.path.exists("/home/user/audit/top5.txt"), (
            "/home/user/audit/top5.txt already exists - it should not exist before the task"
        )


class TestFileCount:
    """Tests to verify /var/data has sufficient files for the task."""

    def test_var_data_has_multiple_files(self):
        """Verify /var/data contains approximately 50 files."""
        file_count = 0
        for root, dirs, files in os.walk("/var/data"):
            file_count += len(files)

        # Allow some tolerance - task says ~50 files
        assert file_count >= 10, (
            f"/var/data should contain multiple files for the audit task. "
            f"Found only {file_count} files."
        )


class TestCoreutilsAvailable:
    """Tests to verify required coreutils are available."""

    REQUIRED_COMMANDS = ["find", "du", "sort", "head"]

    @pytest.mark.parametrize("command", REQUIRED_COMMANDS)
    def test_command_available(self, command):
        """Verify required coreutils commands are available in PATH."""
        import shutil
        cmd_path = shutil.which(command)
        assert cmd_path is not None, f"Required command '{command}' is not available in PATH"
