# test_initial_state.py
"""
Pre-validation tests for the nginx 5xx log extraction task.
Validates the initial state before the student performs the action.
"""

import os
import pytest
import subprocess


class TestInitialState:
    """Tests to verify the initial state before task execution."""

    def test_access_log_exists(self):
        """Verify that /var/log/app/access.log exists."""
        log_path = "/var/log/app/access.log"
        assert os.path.exists(log_path), f"Access log not found at {log_path}"
        assert os.path.isfile(log_path), f"{log_path} exists but is not a regular file"

    def test_access_log_readable(self):
        """Verify that /var/log/app/access.log is readable."""
        log_path = "/var/log/app/access.log"
        assert os.access(log_path, os.R_OK), f"{log_path} is not readable by current user"

    def test_access_log_line_count(self):
        """Verify that access.log contains approximately 200,000 lines."""
        log_path = "/var/log/app/access.log"
        result = subprocess.run(
            ["wc", "-l", log_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to count lines in {log_path}"
        line_count = int(result.stdout.split()[0])
        # Allow some tolerance around 200,000 lines
        assert 190000 <= line_count <= 210000, (
            f"Expected approximately 200,000 lines in {log_path}, got {line_count}"
        )

    def test_access_log_format_combined(self):
        """Verify that access.log uses standard combined log format with status in field 9."""
        log_path = "/var/log/app/access.log"
        with open(log_path, 'r') as f:
            # Check first 10 lines for proper format
            for i, line in enumerate(f):
                if i >= 10:
                    break
                fields = line.split()
                assert len(fields) >= 9, (
                    f"Line {i+1} has fewer than 9 fields: {line[:100]}..."
                )
                status_code = fields[8]  # 0-indexed, so field 9 is index 8
                assert status_code.isdigit() and len(status_code) == 3, (
                    f"Field 9 on line {i+1} is not a valid HTTP status code: '{status_code}'"
                )
                status_int = int(status_code)
                assert 100 <= status_int <= 599, (
                    f"Field 9 on line {i+1} is not a valid HTTP status code: {status_int}"
                )

    def test_access_log_contains_5xx_errors(self):
        """Verify that access.log contains 5xx error lines."""
        log_path = "/var/log/app/access.log"
        # Use awk to count 5xx status codes in field 9
        result = subprocess.run(
            ["awk", '$9 ~ /^5[0-9][0-9]$/ {count++} END {print count}', log_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to count 5xx errors"
        count_str = result.stdout.strip()
        assert count_str and count_str.isdigit(), (
            f"Unexpected output from awk: '{count_str}'"
        )
        count = int(count_str)
        # Should be approximately 847 lines
        assert 800 <= count <= 900, (
            f"Expected approximately 847 lines with 5xx status codes, found {count}"
        )

    def test_access_log_contains_various_status_codes(self):
        """Verify that access.log contains 2xx, 3xx, 4xx codes (not just 5xx)."""
        log_path = "/var/log/app/access.log"

        # Check for 2xx codes
        result_2xx = subprocess.run(
            ["awk", '$9 ~ /^2[0-9][0-9]$/ {count++} END {print count+0}', log_path],
            capture_output=True,
            text=True
        )
        count_2xx = int(result_2xx.stdout.strip())

        # Check for 3xx codes
        result_3xx = subprocess.run(
            ["awk", '$9 ~ /^3[0-9][0-9]$/ {count++} END {print count+0}', log_path],
            capture_output=True,
            text=True
        )
        count_3xx = int(result_3xx.stdout.strip())

        # Check for 4xx codes
        result_4xx = subprocess.run(
            ["awk", '$9 ~ /^4[0-9][0-9]$/ {count++} END {print count+0}', log_path],
            capture_output=True,
            text=True
        )
        count_4xx = int(result_4xx.stdout.strip())

        assert count_2xx > 0, "No 2xx status codes found in access.log"
        assert count_3xx > 0 or count_4xx > 0, (
            "No 3xx or 4xx status codes found in access.log"
        )

    def test_home_user_exists(self):
        """Verify that /home/user directory exists."""
        home_path = "/home/user"
        assert os.path.exists(home_path), f"Home directory not found at {home_path}"
        assert os.path.isdir(home_path), f"{home_path} exists but is not a directory"

    def test_home_user_writable(self):
        """Verify that /home/user is writable."""
        home_path = "/home/user"
        assert os.access(home_path, os.W_OK), f"{home_path} is not writable"

    def test_output_file_does_not_exist(self):
        """Verify that /home/user/5xx.log does not exist initially."""
        output_path = "/home/user/5xx.log"
        assert not os.path.exists(output_path), (
            f"Output file {output_path} already exists - it should not exist initially"
        )

    def test_required_tools_available(self):
        """Verify that standard text processing tools are available."""
        tools = ["awk", "grep", "sed", "cut"]
        for tool in tools:
            result = subprocess.run(
                ["which", tool],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Required tool '{tool}' is not available"

    def test_access_log_not_empty(self):
        """Verify that access.log is not empty."""
        log_path = "/var/log/app/access.log"
        file_size = os.path.getsize(log_path)
        assert file_size > 0, f"{log_path} is empty"
        # With ~200k lines of combined log format, expect at least several MB
        assert file_size > 1000000, (
            f"{log_path} is unexpectedly small ({file_size} bytes) for ~200k log lines"
        )
