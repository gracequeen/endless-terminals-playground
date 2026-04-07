# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the backup integrity verification task.
"""

import os
import gzip
import pytest
from pathlib import Path


class TestInitialState:
    """Test the initial state required for the backup integrity verification task."""

    def test_backups_directory_exists(self):
        """Verify that the backups directory exists."""
        backups_dir = Path("/home/user/backups")
        assert backups_dir.exists(), (
            f"Backups directory does not exist at {backups_dir}. "
            "Please create the directory: mkdir -p /home/user/backups"
        )
        assert backups_dir.is_dir(), (
            f"{backups_dir} exists but is not a directory."
        )

    def test_compressed_backup_file_exists(self):
        """Verify that the compressed backup file exists."""
        backup_file = Path("/home/user/backups/database_dump.sql.gz")
        assert backup_file.exists(), (
            f"Compressed backup file does not exist at {backup_file}. "
            "Please create the backup file before running the task."
        )
        assert backup_file.is_file(), (
            f"{backup_file} exists but is not a regular file."
        )

    def test_compressed_backup_file_is_readable(self):
        """Verify that the compressed backup file is readable."""
        backup_file = Path("/home/user/backups/database_dump.sql.gz")
        assert os.path.isfile(backup_file), (
            f"Compressed backup file at {backup_file} is not readable. "
            "Please check file permissions."
        )

    def test_compressed_backup_file_is_not_empty(self):
        """Verify that the compressed backup file is not empty."""
        backup_file = Path("/home/user/backups/database_dump.sql.gz")
        file_size = backup_file.stat().st_size
        assert file_size > 0, (
            f"Compressed backup file at {backup_file} is empty (0 bytes). "
            "Please ensure the backup file contains data."
        )

    def test_compressed_backup_file_is_valid_gzip(self):
        """Verify that the backup file is a valid gzip file."""
        backup_file = Path("/home/user/backups/database_dump.sql.gz")
        try:
            with gzip.open(backup_file, 'rb') as f:
                # Try to read a small portion to verify it's valid gzip
                f.read(1)
        except gzip.BadGzipFile:
            pytest.fail(
                f"File at {backup_file} is not a valid gzip file. "
                "Please ensure the file is properly compressed with gzip."
            )
        except Exception as e:
            pytest.fail(
                f"Error reading gzip file at {backup_file}: {e}"
            )

    def test_compressed_backup_file_can_be_fully_decompressed(self):
        """Verify that the backup file can be fully decompressed."""
        backup_file = Path("/home/user/backups/database_dump.sql.gz")
        try:
            with gzip.open(backup_file, 'rb') as f:
                content = f.read()
                assert len(content) > 0, (
                    f"Decompressed content of {backup_file} is empty. "
                    "Please ensure the backup contains actual data."
                )
        except Exception as e:
            pytest.fail(
                f"Failed to decompress {backup_file}: {e}"
            )

    def test_integrity_check_log_does_not_exist(self):
        """Verify that the integrity check log does not exist yet (student needs to create it)."""
        log_file = Path("/home/user/backups/integrity_check.log")
        assert not log_file.exists(), (
            f"Integrity check log already exists at {log_file}. "
            "This file should be created by the student as part of the task. "
            "Please remove it before running the task."
        )

    def test_backups_directory_is_writable(self):
        """Verify that the backups directory is writable (for creating the log file)."""
        backups_dir = Path("/home/user/backups")
        assert os.path.isdir(backups_dir), (
            f"Backups directory at {backups_dir} is not writable. "
            "Please check directory permissions to allow creating the integrity log."
        )

    def test_home_user_directory_exists(self):
        """Verify that the /home/user directory exists."""
        home_dir = Path("/home/user")
        assert home_dir.exists(), (
            f"Home directory does not exist at {home_dir}. "
            "Please ensure the user home directory is set up correctly."
        )
        assert home_dir.is_dir(), (
            f"{home_dir} exists but is not a directory."
        )