# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the log filtering task.
"""

import os
import re
import subprocess
import pytest


class TestOutputFileExists:
    """Tests for the existence and properties of the output file."""

    def test_internal_hits_log_exists(self):
        """Verify /home/user/internal_hits.log exists."""
        assert os.path.exists("/home/user/internal_hits.log"), \
            "Output file /home/user/internal_hits.log does not exist - task not completed"

    def test_internal_hits_log_is_file(self):
        """Verify /home/user/internal_hits.log is a regular file."""
        assert os.path.isfile("/home/user/internal_hits.log"), \
            "/home/user/internal_hits.log exists but is not a regular file"

    def test_internal_hits_log_is_readable(self):
        """Verify /home/user/internal_hits.log is readable."""
        assert os.access("/home/user/internal_hits.log", os.R_OK), \
            "/home/user/internal_hits.log is not readable"

    def test_internal_hits_log_not_empty(self):
        """Verify /home/user/internal_hits.log is not empty."""
        assert os.path.getsize("/home/user/internal_hits.log") > 0, \
            "/home/user/internal_hits.log is empty"


class TestOutputLineCount:
    """Tests for the exact line count of the output file."""

    def test_output_has_exactly_4800_lines(self):
        """Verify /home/user/internal_hits.log has exactly 4800 lines."""
        result = subprocess.run(
            ["wc", "-l", "/home/user/internal_hits.log"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Failed to count lines in internal_hits.log: {result.stderr}"

        line_count = int(result.stdout.strip().split()[0])
        assert line_count == 4800, \
            f"Expected exactly 4800 lines, but found {line_count}. " \
            f"The filtering may have included/excluded wrong entries."


class TestNoExcludedIPsInOutput:
    """Tests to ensure 10.x.x.x IPs are excluded from output."""

    def test_no_lines_start_with_10_dot(self):
        """Verify no lines in output start with 10. (10.0.0.0/8 range)."""
        result = subprocess.run(
            ["grep", "-c", "^10\\."],
            stdin=open("/home/user/internal_hits.log", "r"),
            capture_output=True,
            text=True
        )
        # grep returns 1 if no matches (which is what we want)
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 0, \
            f"Found {count} lines starting with '10.' IP addresses. " \
            f"These should have been excluded as health check probes."

    def test_no_10x_ips_anywhere_at_line_start(self):
        """Double-check no 10.x.x.x IPs at line start using extended regex."""
        result = subprocess.run(
            ["grep", "-cE", r"^10\.[0-9]+\.[0-9]+\.[0-9]+"],
            stdin=open("/home/user/internal_hits.log", "r"),
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 0, \
            f"Found {count} lines with 10.x.x.x IP addresses at start. " \
            f"All requests from 10.0.0.0/8 range should be excluded."


class TestAllLinesMatchInternalAPIPattern:
    """Tests to ensure all lines contain the internal API pattern."""

    def test_all_lines_contain_internal_api_path(self):
        """Verify every line contains /api/v[0-9]+/internal/ pattern."""
        result = subprocess.run(
            ["grep", "-cvE", r"/api/v[0-9]+/internal/", "/home/user/internal_hits.log"],
            capture_output=True,
            text=True
        )
        # grep -c -v counts non-matching lines; should be 0
        non_matching_count = int(result.stdout.strip()) if result.returncode == 0 else 0
        # Note: grep returns 1 if all lines match (no non-matching lines)
        if result.returncode == 1:
            non_matching_count = 0
        assert non_matching_count == 0, \
            f"Found {non_matching_count} lines that do NOT match /api/v[0-9]+/internal/ pattern. " \
            f"All lines should be internal API requests."

    def test_positive_match_internal_api_count(self):
        """Verify all 4800 lines match the internal API pattern."""
        result = subprocess.run(
            ["grep", "-cE", r"/api/v[0-9]+/internal/", "/home/user/internal_hits.log"],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 4800, \
            f"Expected 4800 lines matching internal API pattern, found {count}"


class TestTimestampConversion:
    """Tests for proper timestamp conversion to ISO 8601 format."""

    def test_no_old_format_timestamps_remain(self):
        """Verify no Apache-style bracketed timestamps remain."""
        result = subprocess.run(
            ["grep", "-cE", r"\[[0-9]{2}/[A-Z][a-z]{2}/[0-9]{4}:"],
            stdin=open("/home/user/internal_hits.log", "r"),
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 0, \
            f"Found {count} lines with old Apache timestamp format [DD/Mon/YYYY:...]. " \
            f"All timestamps should be converted to ISO 8601 format."

    def test_all_lines_have_iso8601_timestamps(self):
        """Verify all lines have ISO 8601 formatted timestamps."""
        result = subprocess.run(
            ["grep", "-cE", r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"],
            stdin=open("/home/user/internal_hits.log", "r"),
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 4800, \
            f"Expected 4800 lines with ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SS), found {count}. " \
            f"Timestamps must be converted from Apache format to ISO 8601."

    def test_iso_timestamp_format_sample_check(self):
        """Verify ISO timestamps are properly formatted in sample lines."""
        with open("/home/user/internal_hits.log", "r") as f:
            sample_lines = [f.readline() for _ in range(min(100, 4800))]

        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        for i, line in enumerate(sample_lines):
            if line.strip():  # skip empty lines
                match = re.search(iso_pattern, line)
                assert match, \
                    f"Line {i+1} missing ISO 8601 timestamp: {line[:100]}..."


class TestLineContentPreservation:
    """Tests to verify the rest of the line content is preserved."""

    def test_lines_contain_ip_addresses(self):
        """Verify lines still contain IP addresses at the start."""
        with open("/home/user/internal_hits.log", "r") as f:
            sample_lines = [f.readline() for _ in range(100)]

        ip_pattern = r'^\d+\.\d+\.\d+\.\d+'
        for i, line in enumerate(sample_lines):
            if line.strip():
                assert re.match(ip_pattern, line), \
                    f"Line {i+1} does not start with an IP address: {line[:50]}..."

    def test_lines_contain_http_methods(self):
        """Verify lines contain HTTP methods (GET, POST, etc.)."""
        with open("/home/user/internal_hits.log", "r") as f:
            sample_lines = [f.readline() for _ in range(100)]

        method_pattern = r'"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)'
        for i, line in enumerate(sample_lines):
            if line.strip():
                assert re.search(method_pattern, line), \
                    f"Line {i+1} missing HTTP method: {line[:100]}..."

    def test_lines_contain_status_codes(self):
        """Verify lines contain HTTP status codes."""
        with open("/home/user/internal_hits.log", "r") as f:
            sample_lines = [f.readline() for _ in range(100)]

        # Status code should appear after the HTTP version
        status_pattern = r'HTTP/\d\.\d" \d{3}'
        for i, line in enumerate(sample_lines):
            if line.strip():
                assert re.search(status_pattern, line), \
                    f"Line {i+1} missing HTTP status code: {line[:100]}..."


class TestInputFileUnchanged:
    """Tests to verify the input file was not modified."""

    def test_access_log_still_exists(self):
        """Verify /var/log/app/access.log still exists."""
        assert os.path.exists("/var/log/app/access.log"), \
            "Original input file /var/log/app/access.log was deleted or moved"

    def test_access_log_still_has_original_format(self):
        """Verify /var/log/app/access.log still has Apache format timestamps."""
        result = subprocess.run(
            ["grep", "-cE", r"\[[0-9]{2}/[A-Z][a-z]{2}/[0-9]{4}:", "/var/log/app/access.log"],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        # Original file should still have many Apache-format timestamps
        assert count > 40000, \
            f"Original access.log appears to have been modified. " \
            f"Expected ~50k Apache timestamps, found {count}"

    def test_access_log_line_count_unchanged(self):
        """Verify /var/log/app/access.log line count is approximately unchanged."""
        result = subprocess.run(
            ["wc", "-l", "/var/log/app/access.log"],
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip().split()[0])
        assert 45000 <= line_count <= 55000, \
            f"Original access.log line count changed unexpectedly: {line_count}"


class TestNoExtraFilesInVarLog:
    """Tests to verify no extra files were created in /var/log/."""

    def test_no_new_files_in_var_log_app(self):
        """Verify no new files created in /var/log/app/ besides access.log."""
        files_in_app = os.listdir("/var/log/app")
        # Should only contain access.log (or possibly a few expected files)
        unexpected_files = [f for f in files_in_app if f not in ["access.log"]]
        # Allow for some flexibility but flag if internal_hits.log ended up there
        assert "internal_hits.log" not in files_in_app, \
            "Output file internal_hits.log was created in /var/log/app/ instead of /home/user/"


class TestComprehensiveValidation:
    """Comprehensive tests combining multiple validations."""

    def test_full_line_format_validation(self):
        """Validate complete line format for a sample of output lines."""
        with open("/home/user/internal_hits.log", "r") as f:
            lines = f.readlines()

        # Check every 50th line for comprehensive format
        for i in range(0, len(lines), 50):
            line = lines[i]
            # Should have: IP (not 10.x), ISO timestamp, internal API path
            assert not line.startswith("10."), \
                f"Line {i+1} starts with excluded 10.x IP: {line[:50]}..."
            assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", line), \
                f"Line {i+1} missing ISO timestamp: {line[:100]}..."
            assert re.search(r"/api/v\d+/internal/", line), \
                f"Line {i+1} missing internal API path: {line[:100]}..."
            assert not re.search(r"\[\d{2}/[A-Z][a-z]{2}/\d{4}:", line), \
                f"Line {i+1} still has old timestamp format: {line[:100]}..."
