# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student performs
the iOS build log processing task.
"""

import os
import pytest


class TestInitialState:
    """Tests to verify the required initial state exists."""

    def test_build_logs_directory_exists(self):
        """Verify that the build_logs directory exists."""
        build_logs_dir = "/home/user/build_logs"
        assert os.path.isdir(build_logs_dir), (
            f"Directory '{build_logs_dir}' does not exist. "
            "The build_logs directory must be created before running the task."
        )

    def test_ios_build_log_file_exists(self):
        """Verify that the iOS build log file exists."""
        log_file = "/home/user/build_logs/ios_build_20240115.log"
        assert os.path.isfile(log_file), (
            f"File '{log_file}' does not exist. "
            "The iOS build log file must be present before running the task."
        )

    def test_ios_build_log_is_readable(self):
        """Verify that the iOS build log file is readable."""
        log_file = "/home/user/build_logs/ios_build_20240115.log"
        assert os.path.isfile(log_file), (
            f"File '{log_file}' is not readable. "
            "The iOS build log file must be readable."
        )

    def test_ios_build_log_has_content(self):
        """Verify that the iOS build log file is not empty."""
        log_file = "/home/user/build_logs/ios_build_20240115.log"
        assert os.path.getsize(log_file) > 0, (
            f"File '{log_file}' is empty. "
            "The iOS build log file must contain build log content."
        )

    def test_ios_build_log_contains_expected_structure(self):
        """Verify that the iOS build log contains the expected log structure."""
        log_file = "/home/user/build_logs/ios_build_20240115.log"
        with open(log_file, 'r') as f:
            content = f.read()

        # Check for warning lines (case-insensitive)
        assert 'warning:' in content.lower(), (
            f"File '{log_file}' does not contain any 'warning:' lines. "
            "The build log must contain warning messages for the task."
        )

    def test_ios_build_log_contains_errors(self):
        """Verify that the iOS build log contains error messages."""
        log_file = "/home/user/build_logs/ios_build_20240115.log"
        with open(log_file, 'r') as f:
            content = f.read()

        # Check for error lines (case-insensitive)
        assert 'error:' in content.lower(), (
            f"File '{log_file}' does not contain any 'error:' lines. "
            "The build log must contain error messages for the task."
        )

    def test_ios_build_log_contains_build_phases(self):
        """Verify that the iOS build log contains build phase timing information."""
        log_file = "/home/user/build_logs/ios_build_20240115.log"
        with open(log_file, 'r') as f:
            content = f.read()

        # Check for build phase completion lines
        assert "Build phase" in content and "completed in" in content, (
            f"File '{log_file}' does not contain build phase timing information. "
            "The build log must contain lines like \"Build phase '<name>' completed in <N> seconds\"."
        )

    def test_ios_build_log_contains_swift_files_in_warnings(self):
        """Verify that the iOS build log contains .swift file references in warnings."""
        log_file = "/home/user/build_logs/ios_build_20240115.log"
        with open(log_file, 'r') as f:
            content = f.read()

        # Check for .swift file references
        assert '.swift' in content, (
            f"File '{log_file}' does not contain any .swift file references. "
            "The build log must contain Swift file paths in warning/error messages."
        )

    def test_build_reports_directory_does_not_exist(self):
        """Verify that the build_reports directory does NOT exist yet (agent should create it)."""
        build_reports_dir = "/home/user/build_reports"
        assert not os.path.exists(build_reports_dir), (
            f"Directory '{build_reports_dir}' already exists. "
            "The build_reports directory should NOT exist before the task - "
            "the agent is expected to create it."
        )

    def test_home_user_directory_exists(self):
        """Verify that the /home/user directory exists."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), (
            f"Directory '{home_dir}' does not exist. "
            "The home directory must exist for the task."
        )

    def test_home_user_is_writable(self):
        """Verify that the /home/user directory is writable."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), (
            f"Directory '{home_dir}' is not writable. "
            "The home directory must be writable to create the build_reports directory."
        )