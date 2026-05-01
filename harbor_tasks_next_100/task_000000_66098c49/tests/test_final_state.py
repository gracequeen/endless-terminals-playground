# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the SSH log analysis task.
"""

import os
import pytest
import re
from collections import Counter


class TestFinalState:
    """Validate the final state after the task is completed."""

    def test_output_file_exists(self):
        """Verify /home/user/repeat_offenders.txt exists."""
        output_path = "/home/user/repeat_offenders.txt"
        assert os.path.exists(output_path), (
            f"Output file {output_path} does not exist. "
            "The task requires creating this file with IPs that failed 5+ times."
        )

    def test_output_file_is_regular_file(self):
        """Verify /home/user/repeat_offenders.txt is a regular file."""
        output_path = "/home/user/repeat_offenders.txt"
        assert os.path.isfile(output_path), (
            f"{output_path} exists but is not a regular file."
        )

    def test_output_file_is_readable(self):
        """Verify /home/user/repeat_offenders.txt is readable."""
        output_path = "/home/user/repeat_offenders.txt"
        assert os.access(output_path, os.R_OK), (
            f"{output_path} exists but is not readable."
        )

    def test_output_file_has_exactly_five_lines(self):
        """Verify the output file contains exactly 5 lines (IPs with 5+ attempts)."""
        output_path = "/home/user/repeat_offenders.txt"
        with open(output_path, 'r') as f:
            content = f.read()

        # Strip trailing whitespace/newlines and split
        lines = [line for line in content.strip().split('\n') if line.strip()]

        assert len(lines) == 5, (
            f"Output file should contain exactly 5 IPs (those with 5+ attempts), "
            f"but found {len(lines)} non-empty lines. Lines found: {lines}"
        )

    def test_output_file_contains_correct_ips(self):
        """Verify the output file contains exactly the 5 IPs with 5+ failed attempts."""
        output_path = "/home/user/repeat_offenders.txt"
        expected_ips = {
            "203.0.113.42",
            "198.51.100.17",
            "192.0.2.88",
            "10.0.0.55",
            "172.16.0.12",
        }

        with open(output_path, 'r') as f:
            content = f.read()

        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        actual_ips = set(lines)

        missing_ips = expected_ips - actual_ips
        extra_ips = actual_ips - expected_ips

        assert missing_ips == set(), (
            f"Output file is missing expected IPs: {missing_ips}. "
            f"These IPs had 5+ failed attempts and should be included."
        )

        assert extra_ips == set(), (
            f"Output file contains unexpected IPs: {extra_ips}. "
            f"Only IPs with 5+ failed attempts should be included."
        )

    def test_output_file_sorted_by_count_descending(self):
        """Verify IPs are sorted by attempt count in descending order."""
        output_path = "/home/user/repeat_offenders.txt"

        # Expected order based on counts: 23, 15, 9, 7, 5
        expected_order = [
            "203.0.113.42",   # 23 attempts
            "198.51.100.17",  # 15 attempts
            "192.0.2.88",     # 9 attempts
            "10.0.0.55",      # 7 attempts
            "172.16.0.12",    # 5 attempts
        ]

        with open(output_path, 'r') as f:
            content = f.read()

        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

        assert lines == expected_order, (
            f"IPs are not sorted by count in descending order.\n"
            f"Expected order: {expected_order}\n"
            f"Actual order:   {lines}\n"
            f"IPs should be sorted from most attempts (203.0.113.42 with 23) "
            f"to least (172.16.0.12 with 5)."
        )

    def test_output_file_contains_only_ips_no_counts(self):
        """Verify the output contains only IP addresses, no counts or other text."""
        output_path = "/home/user/repeat_offenders.txt"
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

        with open(output_path, 'r') as f:
            content = f.read()

        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

        for line in lines:
            assert ip_pattern.match(line), (
                f"Line '{line}' is not a valid bare IP address. "
                f"The output should contain only IPs, no counts or other text."
            )

    def test_output_file_no_trailing_blank_lines(self):
        """Verify there are no trailing blank lines in the output file."""
        output_path = "/home/user/repeat_offenders.txt"

        with open(output_path, 'r') as f:
            content = f.read()

        # Check that content ends with a newline after the last IP (or no newline)
        # but not multiple trailing newlines
        lines = content.split('\n')

        # Remove the last element if it's empty (single trailing newline is OK)
        if lines and lines[-1] == '':
            lines = lines[:-1]

        # Now check there are no empty lines at the end
        trailing_empty = 0
        for line in reversed(lines):
            if line.strip() == '':
                trailing_empty += 1
            else:
                break

        assert trailing_empty == 0, (
            f"Output file has {trailing_empty} trailing blank lines. "
            f"The file should end after the last IP without extra blank lines."
        )

    def test_auth_log_unchanged(self):
        """Verify /var/log/auth_attempts.log is unchanged (invariant)."""
        log_path = "/var/log/auth_attempts.log"
        pattern = re.compile(r'Failed password.*from\s+(\d+\.\d+\.\d+\.\d+)')

        assert os.path.exists(log_path), (
            f"Log file {log_path} no longer exists. It should not be modified or deleted."
        )

        with open(log_path, 'r') as f:
            content = f.read()

        ips = pattern.findall(content)
        ip_counts = Counter(ips)

        # Expected distribution should still be intact
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

        assert len(ip_counts) == 12, (
            f"Log file appears to have been modified. Expected 12 distinct IPs, "
            f"found {len(ip_counts)}. The log file should remain unchanged."
        )

        for ip, expected_count in expected_counts.items():
            actual_count = ip_counts.get(ip, 0)
            assert actual_count == expected_count, (
                f"Log file appears to have been modified. IP {ip} has {actual_count} "
                f"attempts, expected {expected_count}. The log file should remain unchanged."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
