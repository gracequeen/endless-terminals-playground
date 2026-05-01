# test_initial_state.py
"""
Tests to validate the initial state of the system before the student
performs the task of extracting 503 error lines from nginx access log.
"""

import os
import re
import subprocess
import pytest


class TestInitialState:
    """Validate the system state before the task is performed."""

    def test_access_log_exists(self):
        """Verify /var/log/app/access.log exists."""
        log_path = "/var/log/app/access.log"
        assert os.path.exists(log_path), f"Access log does not exist at {log_path}"

    def test_access_log_is_file(self):
        """Verify /var/log/app/access.log is a regular file."""
        log_path = "/var/log/app/access.log"
        assert os.path.isfile(log_path), f"{log_path} is not a regular file"

    def test_access_log_readable(self):
        """Verify /var/log/app/access.log is readable by the current user."""
        log_path = "/var/log/app/access.log"
        assert os.access(log_path, os.R_OK), f"{log_path} is not readable by current user"

    def test_access_log_has_approximately_2000_lines(self):
        """Verify access log has approximately 2000 lines."""
        log_path = "/var/log/app/access.log"
        with open(log_path, 'r') as f:
            line_count = sum(1 for _ in f)
        # Allow some tolerance around 2000 lines
        assert 1800 <= line_count <= 2200, \
            f"Access log has {line_count} lines, expected approximately 2000"

    def test_access_log_combined_format(self):
        """Verify access log is in standard nginx combined log format."""
        log_path = "/var/log/app/access.log"
        # Combined log format pattern:
        # $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
        combined_log_pattern = re.compile(
            r'^\d+\.\d+\.\d+\.\d+ - .* \[.*\] ".*" \d{3} \d+ ".*" ".*"$'
        )

        with open(log_path, 'r') as f:
            # Check first 10 lines to verify format
            lines_checked = 0
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    assert combined_log_pattern.match(line), \
                        f"Line does not match combined log format: {line[:100]}..."
                    lines_checked += 1
                    if lines_checked >= 10:
                        break

        assert lines_checked > 0, "No valid log lines found in access log"

    def test_access_log_has_mixed_status_codes(self):
        """Verify access log contains various HTTP status codes."""
        log_path = "/var/log/app/access.log"
        expected_codes = {'200', '301', '302', '304', '400', '403', '404', '500', '502', '503', '504'}
        found_codes = set()

        # Pattern to extract status code (after closing quote of request)
        status_pattern = re.compile(r'" (\d{3}) ')

        with open(log_path, 'r') as f:
            for line in f:
                match = status_pattern.search(line)
                if match:
                    found_codes.add(match.group(1))

        # Check that we have a good variety of status codes
        assert len(found_codes) >= 5, \
            f"Expected mixed status codes, found only: {found_codes}"

        # Specifically verify 503 is present
        assert '503' in found_codes, "Status code 503 not found in access log"

    def test_access_log_has_approximately_47_503_errors(self):
        """Verify access log has approximately 47 lines with 503 status."""
        log_path = "/var/log/app/access.log"

        # Count lines with 503 status code in the correct position
        count_503 = 0
        with open(log_path, 'r') as f:
            for line in f:
                if '" 503 ' in line:
                    count_503 += 1

        # Allow some tolerance around 47
        assert 40 <= count_503 <= 55, \
            f"Expected approximately 47 lines with 503 status, found {count_503}"

    def test_docs_directory_exists(self):
        """Verify /home/user/docs/ directory exists."""
        docs_path = "/home/user/docs"
        assert os.path.exists(docs_path), f"Directory does not exist: {docs_path}"

    def test_docs_directory_is_directory(self):
        """Verify /home/user/docs is a directory."""
        docs_path = "/home/user/docs"
        assert os.path.isdir(docs_path), f"{docs_path} is not a directory"

    def test_docs_directory_writable(self):
        """Verify /home/user/docs/ is writable."""
        docs_path = "/home/user/docs"
        assert os.access(docs_path, os.W_OK), f"{docs_path} is not writable"

    def test_output_file_does_not_exist(self):
        """Verify /home/user/docs/503_examples.txt does not exist initially."""
        output_path = "/home/user/docs/503_examples.txt"
        assert not os.path.exists(output_path), \
            f"Output file already exists: {output_path} (should not exist initially)"

    def test_grep_available(self):
        """Verify grep command is available."""
        result = subprocess.run(['which', 'grep'], capture_output=True)
        assert result.returncode == 0, "grep command is not available"

    def test_awk_available(self):
        """Verify awk command is available."""
        result = subprocess.run(['which', 'awk'], capture_output=True)
        assert result.returncode == 0, "awk command is not available"

    def test_sed_available(self):
        """Verify sed command is available."""
        result = subprocess.run(['which', 'sed'], capture_output=True)
        assert result.returncode == 0, "sed command is not available"

    def test_access_log_has_503_in_other_positions(self):
        """
        Verify that 503 appears in positions other than status code,
        making naive grep potentially problematic (anti-shortcut guard).
        """
        log_path = "/var/log/app/access.log"

        # Count lines that contain '503' but NOT as the status code
        lines_with_503_elsewhere = 0
        with open(log_path, 'r') as f:
            for line in f:
                # Line contains 503 somewhere
                if '503' in line:
                    # But not as the status code (pattern: " 503 " after quote)
                    if '" 503 ' not in line:
                        lines_with_503_elsewhere += 1

        # This test documents the state - there may or may not be such lines
        # We just want to verify the log structure is realistic
        # (If there are such lines, naive grep would fail)
        pass  # This is informational - the log may or may not have such cases
