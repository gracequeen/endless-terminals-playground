# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of extracting ip and status columns from access.log.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Tests for validating the initial state before the task is performed."""

    LOG_DIR = "/home/user/logs"
    ACCESS_LOG = "/home/user/logs/access.log"
    OUTPUT_FILE = "/home/user/logs/ip_status.tsv"

    def test_logs_directory_exists(self):
        """Verify that /home/user/logs/ directory exists."""
        assert os.path.isdir(self.LOG_DIR), (
            f"Directory {self.LOG_DIR} does not exist. "
            "The logs directory must be present before starting the task."
        )

    def test_logs_directory_is_writable(self):
        """Verify that /home/user/logs/ directory is writable."""
        assert os.access(self.LOG_DIR, os.W_OK), (
            f"Directory {self.LOG_DIR} is not writable. "
            "The logs directory must be writable to create the output file."
        )

    def test_access_log_exists(self):
        """Verify that /home/user/logs/access.log exists."""
        assert os.path.isfile(self.ACCESS_LOG), (
            f"File {self.ACCESS_LOG} does not exist. "
            "The access log file must be present before starting the task."
        )

    def test_access_log_is_readable(self):
        """Verify that /home/user/logs/access.log is readable."""
        assert os.access(self.ACCESS_LOG, os.R_OK), (
            f"File {self.ACCESS_LOG} is not readable. "
            "The access log file must be readable to extract data from it."
        )

    def test_access_log_has_847_lines(self):
        """Verify that access.log contains exactly 847 lines."""
        result = subprocess.run(
            ["wc", "-l"],
            stdin=open(self.ACCESS_LOG, "r"),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip())
        assert line_count == 847, (
            f"File {self.ACCESS_LOG} has {line_count} lines, expected 847. "
            "The access log must contain exactly 847 lines."
        )

    def test_access_log_is_tab_separated_with_6_columns(self):
        """Verify that access.log is tab-separated with 6 columns per line."""
        # Use awk to check that every line has exactly 6 tab-separated fields
        result = subprocess.run(
            ["awk", "-F\t", "NF != 6 { exit 1 }"],
            stdin=open(self.ACCESS_LOG, "r"),
            capture_output=True
        )
        assert result.returncode == 0, (
            f"File {self.ACCESS_LOG} does not have exactly 6 tab-separated columns on every line. "
            "Each line must have 6 fields: timestamp, ip, method, path, status, bytes."
        )

    def test_access_log_sample_line_format(self):
        """Verify the format of a sample line from access.log."""
        with open(self.ACCESS_LOG, "r") as f:
            first_line = f.readline().rstrip("\n")

        fields = first_line.split("\t")
        assert len(fields) == 6, (
            f"First line of {self.ACCESS_LOG} has {len(fields)} fields, expected 6. "
            f"Line content: {first_line!r}"
        )

        # Basic format checks
        timestamp, ip, method, path, status, bytes_field = fields

        # Timestamp should look like ISO format
        assert "T" in timestamp and "Z" in timestamp, (
            f"Timestamp field '{timestamp}' does not appear to be in ISO format (expected format like '2024-01-15T09:23:41Z')."
        )

        # IP should contain dots (IPv4)
        assert "." in ip, (
            f"IP field '{ip}' does not appear to be a valid IPv4 address."
        )

        # Method should be a valid HTTP method
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        assert method in valid_methods, (
            f"Method field '{method}' is not a recognized HTTP method."
        )

        # Path should start with /
        assert path.startswith("/"), (
            f"Path field '{path}' does not start with '/'."
        )

        # Status should be a 3-digit number
        assert status.isdigit() and len(status) == 3, (
            f"Status field '{status}' is not a valid 3-digit HTTP status code."
        )

        # Bytes should be a number
        assert bytes_field.isdigit(), (
            f"Bytes field '{bytes_field}' is not a valid number."
        )

    def test_output_file_does_not_exist(self):
        """Verify that ip_status.tsv does not exist initially."""
        assert not os.path.exists(self.OUTPUT_FILE), (
            f"File {self.OUTPUT_FILE} already exists. "
            "The output file should not exist before the task is performed."
        )

    def test_cut_command_available(self):
        """Verify that cut command is available."""
        result = subprocess.run(["which", "cut"], capture_output=True)
        assert result.returncode == 0, (
            "The 'cut' command is not available. "
            "This tool should be available for the task."
        )

    def test_awk_command_available(self):
        """Verify that awk command is available."""
        result = subprocess.run(["which", "awk"], capture_output=True)
        assert result.returncode == 0, (
            "The 'awk' command is not available. "
            "This tool should be available for the task."
        )

    def test_sed_command_available(self):
        """Verify that sed command is available."""
        result = subprocess.run(["which", "sed"], capture_output=True)
        assert result.returncode == 0, (
            "The 'sed' command is not available. "
            "This tool should be available for the task."
        )

    def test_perl_command_available(self):
        """Verify that perl command is available."""
        result = subprocess.run(["which", "perl"], capture_output=True)
        assert result.returncode == 0, (
            "The 'perl' command is not available. "
            "This tool should be available for the task."
        )
