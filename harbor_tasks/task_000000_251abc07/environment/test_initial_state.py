# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the log filtering task.
"""

import os
import re
import subprocess
import pytest


class TestInputLogFileExists:
    """Tests for the existence and properties of the input log file."""

    def test_access_log_exists(self):
        """Verify /var/log/app/access.log exists."""
        assert os.path.exists("/var/log/app/access.log"), \
            "Input log file /var/log/app/access.log does not exist"

    def test_access_log_is_file(self):
        """Verify /var/log/app/access.log is a regular file."""
        assert os.path.isfile("/var/log/app/access.log"), \
            "/var/log/app/access.log exists but is not a regular file"

    def test_access_log_is_readable(self):
        """Verify /var/log/app/access.log is readable."""
        assert os.access("/var/log/app/access.log", os.R_OK), \
            "/var/log/app/access.log is not readable by current user"

    def test_access_log_has_content(self):
        """Verify /var/log/app/access.log is not empty."""
        assert os.path.getsize("/var/log/app/access.log") > 0, \
            "/var/log/app/access.log is empty"


class TestInputLogLineCount:
    """Tests for the line count of the input log file."""

    def test_access_log_has_approximately_50k_lines(self):
        """Verify /var/log/app/access.log has approximately 50,000 lines."""
        result = subprocess.run(
            ["wc", "-l", "/var/log/app/access.log"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Failed to count lines in access.log: {result.stderr}"

        line_count = int(result.stdout.strip().split()[0])
        # Allow some tolerance around 50k lines
        assert 45000 <= line_count <= 55000, \
            f"Expected approximately 50,000 lines, but found {line_count}"


class TestInputLogFormat:
    """Tests for the format of the input log file (Apache combined format)."""

    def test_access_log_has_apache_combined_format(self):
        """Verify log entries are in Apache combined log format."""
        with open("/var/log/app/access.log", "r") as f:
            # Check first 100 lines for format
            for i, line in enumerate(f):
                if i >= 100:
                    break
                # Apache combined format pattern with bracketed timestamp
                # IP - - [DD/Mon/YYYY:HH:MM:SS +0000] "METHOD /path HTTP/x.x" STATUS SIZE "referer" "user-agent"
                pattern = r'^\d+\.\d+\.\d+\.\d+ - - \[\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4}\] ".*" \d+ \d+ ".*" ".*"'
                assert re.match(pattern, line), \
                    f"Line {i+1} does not match Apache combined log format: {line[:100]}..."

    def test_access_log_has_bracketed_timestamps(self):
        """Verify timestamps are in the bracketed Apache format."""
        with open("/var/log/app/access.log", "r") as f:
            sample_lines = [next(f) for _ in range(50)]

        timestamp_pattern = r'\[\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4}\]'
        for i, line in enumerate(sample_lines):
            assert re.search(timestamp_pattern, line), \
                f"Line {i+1} missing bracketed timestamp format: {line[:100]}..."


class TestInputLogContent:
    """Tests for the expected content patterns in the input log."""

    def test_access_log_contains_internal_api_calls(self):
        """Verify log contains lines matching /api/v[0-9]+/internal/ pattern."""
        result = subprocess.run(
            ["grep", "-c", "-E", r"/api/v[0-9]+/internal/", "/var/log/app/access.log"],
            capture_output=True,
            text=True
        )
        # grep returns 0 if matches found, 1 if no matches
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count > 0, \
            "No lines matching /api/v[0-9]+/internal/ pattern found in access.log"
        # Expect approximately 5000 internal API calls
        assert 4500 <= count <= 5500, \
            f"Expected approximately 5,000 internal API lines, found {count}"

    def test_access_log_contains_health_checks(self):
        """Verify log contains health check lines from 10.x.x.x range."""
        result = subprocess.run(
            ["grep", "-c", "-E", r"^10\.[0-9]+\.[0-9]+\.[0-9]+.*(/health|/ready)", "/var/log/app/access.log"],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count > 0, \
            "No health check lines from 10.x.x.x range found in access.log"
        # Expect approximately 15000 health check lines
        assert 13000 <= count <= 17000, \
            f"Expected approximately 15,000 health check lines, found {count}"

    def test_access_log_contains_10x_internal_api_calls(self):
        """Verify log contains internal API calls from 10.x.x.x (to be excluded)."""
        result = subprocess.run(
            ["grep", "-c", "-E", r"^10\.[0-9]+\.[0-9]+\.[0-9]+.*/api/v[0-9]+/internal/", "/var/log/app/access.log"],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count > 0, \
            "No internal API calls from 10.x.x.x range found (these should exist to test exclusion)"
        # Expect approximately 200 such lines
        assert 150 <= count <= 250, \
            f"Expected approximately 200 internal API calls from 10.x.x.x, found {count}"


class TestOutputDirectoryState:
    """Tests for the output directory initial state."""

    def test_home_user_directory_exists(self):
        """Verify /home/user/ directory exists."""
        assert os.path.exists("/home/user"), \
            "Output directory /home/user does not exist"

    def test_home_user_directory_is_writable(self):
        """Verify /home/user/ directory is writable."""
        assert os.access("/home/user", os.W_OK), \
            "/home/user directory is not writable by current user"

    def test_output_file_does_not_exist(self):
        """Verify /home/user/internal_hits.log does not exist initially."""
        assert not os.path.exists("/home/user/internal_hits.log"), \
            "Output file /home/user/internal_hits.log already exists - should not exist initially"


class TestRequiredToolsAvailable:
    """Tests for the availability of required tools."""

    @pytest.mark.parametrize("tool", ["grep", "awk", "sed", "perl", "python3", "wc", "cat"])
    def test_tool_available(self, tool):
        """Verify required tools are available in PATH."""
        result = subprocess.run(
            ["which", tool],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Required tool '{tool}' is not available in PATH"


class TestAppDirectoryStructure:
    """Tests for the /var/log/app directory structure."""

    def test_var_log_app_directory_exists(self):
        """Verify /var/log/app/ directory exists."""
        assert os.path.exists("/var/log/app"), \
            "Directory /var/log/app does not exist"

    def test_var_log_app_is_directory(self):
        """Verify /var/log/app is a directory."""
        assert os.path.isdir("/var/log/app"), \
            "/var/log/app exists but is not a directory"
