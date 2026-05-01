# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the SSH log analysis task.
"""

import os
import pytest
import re
from collections import Counter


class TestInitialState:
    """Validate the initial state before the task is performed."""

    def test_auth_log_exists(self):
        """Verify /var/log/auth_attempts.log exists."""
        log_path = "/var/log/auth_attempts.log"
        assert os.path.exists(log_path), (
            f"Log file {log_path} does not exist. "
            "The auth_attempts.log file must be present for this task."
        )

    def test_auth_log_is_file(self):
        """Verify /var/log/auth_attempts.log is a regular file."""
        log_path = "/var/log/auth_attempts.log"
        assert os.path.isfile(log_path), (
            f"{log_path} exists but is not a regular file."
        )

    def test_auth_log_is_readable(self):
        """Verify /var/log/auth_attempts.log is readable."""
        log_path = "/var/log/auth_attempts.log"
        assert os.access(log_path, os.R_OK), (
            f"{log_path} exists but is not readable. "
            "The file must be readable to extract IP addresses."
        )

    def test_auth_log_has_content(self):
        """Verify /var/log/auth_attempts.log has approximately 200 lines."""
        log_path = "/var/log/auth_attempts.log"
        with open(log_path, 'r') as f:
            lines = f.readlines()
        line_count = len(lines)
        # Allow some tolerance around 200 lines
        assert 150 <= line_count <= 250, (
            f"{log_path} has {line_count} lines, expected approximately 200 lines."
        )

    def test_auth_log_contains_failed_password_entries(self):
        """Verify the log contains Failed password entries in expected format."""
        log_path = "/var/log/auth_attempts.log"
        pattern = re.compile(r'Failed password.*from\s+(\d+\.\d+\.\d+\.\d+)')

        with open(log_path, 'r') as f:
            content = f.read()

        matches = pattern.findall(content)
        assert len(matches) > 0, (
            f"{log_path} does not contain any 'Failed password' entries "
            "in the expected auth.log format."
        )

    def test_auth_log_has_expected_ip_distribution(self):
        """Verify the log contains the expected IP addresses with correct counts."""
        log_path = "/var/log/auth_attempts.log"
        pattern = re.compile(r'Failed password.*from\s+(\d+\.\d+\.\d+\.\d+)')

        with open(log_path, 'r') as f:
            content = f.read()

        ips = pattern.findall(content)
        ip_counts = Counter(ips)

        # Expected distribution
        expected_counts = {
            "203.0.113.42": 23,
            "198.51.100.17": 15,
            "192.0.2.88": 9,
            "10.0.0.55": 7,
            "172.16.0.12": 5,
            "192.168.1.105": 4,
            "10.1.1.1": 3,
            "192.168.0.1": 2,
            "172.31.0.5": 2,
            "8.8.8.8": 1,
            "1.2.3.4": 1,
            "192.168.100.50": 1,
        }

        # Verify we have 12 distinct IPs
        assert len(ip_counts) == 12, (
            f"Expected 12 distinct IPs in the log, found {len(ip_counts)}: {list(ip_counts.keys())}"
        )

        # Verify each IP has the expected count
        for ip, expected_count in expected_counts.items():
            actual_count = ip_counts.get(ip, 0)
            assert actual_count == expected_count, (
                f"IP {ip} has {actual_count} attempts, expected {expected_count}"
            )

    def test_home_user_directory_exists(self):
        """Verify /home/user directory exists."""
        home_path = "/home/user"
        assert os.path.exists(home_path), (
            f"Home directory {home_path} does not exist."
        )

    def test_home_user_is_directory(self):
        """Verify /home/user is a directory."""
        home_path = "/home/user"
        assert os.path.isdir(home_path), (
            f"{home_path} exists but is not a directory."
        )

    def test_home_user_is_writable(self):
        """Verify /home/user is writable."""
        home_path = "/home/user"
        assert os.access(home_path, os.W_OK), (
            f"{home_path} exists but is not writable. "
            "The output file needs to be created here."
        )

    def test_output_file_does_not_exist(self):
        """Verify /home/user/repeat_offenders.txt does not exist initially."""
        output_path = "/home/user/repeat_offenders.txt"
        assert not os.path.exists(output_path), (
            f"Output file {output_path} already exists. "
            "It should not exist before the task is performed."
        )

    def test_required_tools_available(self):
        """Verify standard text processing tools are available."""
        required_tools = ["grep", "awk", "sed", "sort", "uniq", "cut", "wc"]
        missing_tools = []

        for tool in required_tools:
            # Check if tool is in PATH
            found = False
            for path_dir in os.environ.get("PATH", "").split(os.pathsep):
                tool_path = os.path.join(path_dir, tool)
                if os.path.isfile(tool_path) and os.access(tool_path, os.X_OK):
                    found = True
                    break
            if not found:
                missing_tools.append(tool)

        assert len(missing_tools) == 0, (
            f"Required tools are missing: {missing_tools}. "
            "These tools are needed to complete the task."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
