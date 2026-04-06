# test_final_state.py
"""
Tests to validate the final state of the filesystem after the student has
completed the task of filtering timeout errors from the payment API log file.
"""

import os
import pytest


class TestFinalState:
    """Test the final state of the filesystem after the task is performed."""

    def test_output_file_exists(self):
        """Verify that the timeout_errors.txt output file exists."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        assert os.path.isfile(output_path), (
            f"Output file '{output_path}' does not exist. "
            "The task requires creating this file with filtered timeout error entries."
        )

    def test_output_file_is_readable(self):
        """Verify that the timeout_errors.txt file is readable."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        assert os.access(output_path, os.R_OK), (
            f"Output file '{output_path}' is not readable. "
            "The output file must have read permissions."
        )

    def test_output_file_has_exactly_four_lines(self):
        """Verify that the output file contains exactly 4 lines."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        with open(output_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]

        # Filter out empty lines for counting actual content lines
        non_empty_lines = [line for line in lines if line.strip()]

        assert len(non_empty_lines) == 4, (
            f"Output file '{output_path}' should contain exactly 4 lines, "
            f"but has {len(non_empty_lines)} non-empty lines. "
            "The file should contain only the 4 ERROR entries with 'timeout'."
        )

    def test_all_output_lines_contain_error_level(self):
        """Verify that all lines in the output file contain [ERROR]."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        with open(output_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines() if line.strip()]

        for i, line in enumerate(lines, 1):
            assert "[ERROR]" in line, (
                f"Line {i} in output file does not contain '[ERROR]'.\n"
                f"Line content: '{line}'\n"
                "All output lines must be ERROR level log entries."
            )

    def test_all_output_lines_contain_timeout(self):
        """Verify that all lines in the output file contain 'timeout' (case-insensitive)."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        with open(output_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines() if line.strip()]

        for i, line in enumerate(lines, 1):
            assert "timeout" in line.lower(), (
                f"Line {i} in output file does not contain 'timeout' (case-insensitive).\n"
                f"Line content: '{line}'\n"
                "All output lines must contain the word 'timeout'."
            )

    def test_output_file_has_exact_expected_content(self):
        """Verify that the output file contains exactly the expected lines in order."""
        output_path = "/home/user/api_logs/timeout_errors.txt"

        expected_lines = [
            "[2024-01-15 10:23:46] [ERROR] [REQ-A1B2C3] - Connection timeout to payment gateway",
            "[2024-01-15 10:25:17] [ERROR] [REQ-G7H8I9] - Database connection TIMEOUT exceeded",
            "[2024-01-15 10:26:45] [ERROR] [REQ-J1K2L3] - Read Timeout while waiting for response",
            "[2024-01-15 10:29:00] [ERROR] [REQ-S1T2U3] - Socket timeout during SSL handshake",
        ]

        with open(output_path, 'r') as f:
            actual_lines = [line.rstrip('\n') for line in f.readlines() if line.strip()]

        assert len(actual_lines) == len(expected_lines), (
            f"Output file has {len(actual_lines)} lines, expected {len(expected_lines)} lines."
        )

        for i, (expected, actual) in enumerate(zip(expected_lines, actual_lines), 1):
            assert actual == expected, (
                f"Line {i} in output file does not match expected content.\n"
                f"Expected: '{expected}'\n"
                f"Actual:   '{actual}'\n"
                "Lines must be exact copies from the original file in the same order."
            )

    def test_output_lines_are_in_correct_order(self):
        """Verify that the output lines are in the same order as they appear in the source file."""
        output_path = "/home/user/api_logs/timeout_errors.txt"

        with open(output_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines() if line.strip()]

        # Extract timestamps to verify ordering
        timestamps = []
        for line in lines:
            # Extract timestamp from format [2024-01-15 10:23:46]
            if line.startswith('['):
                timestamp_end = line.find(']')
                if timestamp_end > 0:
                    timestamps.append(line[1:timestamp_end])

        # Verify timestamps are in ascending order
        for i in range(len(timestamps) - 1):
            assert timestamps[i] < timestamps[i + 1], (
                f"Lines are not in chronological order. "
                f"Timestamp '{timestamps[i]}' should come before '{timestamps[i + 1]}'."
            )

    def test_first_line_is_connection_timeout(self):
        """Verify the first line is the connection timeout error."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        expected_first = "[2024-01-15 10:23:46] [ERROR] [REQ-A1B2C3] - Connection timeout to payment gateway"

        with open(output_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines() if line.strip()]

        assert len(lines) > 0, "Output file is empty."
        assert lines[0] == expected_first, (
            f"First line does not match expected.\n"
            f"Expected: '{expected_first}'\n"
            f"Actual:   '{lines[0]}'"
        )

    def test_last_line_is_socket_timeout(self):
        """Verify the last line is the socket timeout error."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        expected_last = "[2024-01-15 10:29:00] [ERROR] [REQ-S1T2U3] - Socket timeout during SSL handshake"

        with open(output_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines() if line.strip()]

        assert len(lines) > 0, "Output file is empty."
        assert lines[-1] == expected_last, (
            f"Last line does not match expected.\n"
            f"Expected: '{expected_last}'\n"
            f"Actual:   '{lines[-1]}'"
        )

    def test_source_file_still_exists(self):
        """Verify that the original source file still exists (was not deleted or moved)."""
        source_path = "/home/user/api_logs/payment_api.log"
        assert os.path.isfile(source_path), (
            f"Source file '{source_path}' no longer exists. "
            "The original log file should not be deleted or moved."
        )

    def test_source_file_unchanged(self):
        """Verify that the source file has not been modified."""
        source_path = "/home/user/api_logs/payment_api.log"

        expected_lines = [
            "[2024-01-15 10:23:45] [INFO] [REQ-A1B2C3] - Payment request initiated for $150.00",
            "[2024-01-15 10:23:46] [ERROR] [REQ-A1B2C3] - Connection timeout to payment gateway",
            "[2024-01-15 10:24:01] [INFO] [REQ-D4E5F6] - Payment request initiated for $75.50",
            "[2024-01-15 10:24:02] [DEBUG] [REQ-D4E5F6] - Validating card number",
            "[2024-01-15 10:24:03] [ERROR] [REQ-D4E5F6] - Invalid card number format",
            "[2024-01-15 10:25:15] [INFO] [REQ-G7H8I9] - Payment request initiated for $200.00",
            "[2024-01-15 10:25:17] [ERROR] [REQ-G7H8I9] - Database connection TIMEOUT exceeded",
            "[2024-01-15 10:26:30] [WARN] [REQ-J1K2L3] - Retry attempt 1 for payment processing",
            "[2024-01-15 10:26:45] [ERROR] [REQ-J1K2L3] - Read Timeout while waiting for response",
            "[2024-01-15 10:27:00] [INFO] [REQ-M4N5O6] - Payment successful, transaction ID: TXN-98765",
            "[2024-01-15 10:28:10] [ERROR] [REQ-P7Q8R9] - Authentication failed for merchant",
            "[2024-01-15 10:29:00] [ERROR] [REQ-S1T2U3] - Socket timeout during SSL handshake",
            "[2024-01-15 10:30:00] [INFO] [REQ-V4W5X6] - Batch processing completed",
        ]

        with open(source_path, 'r') as f:
            actual_lines = [line.rstrip('\n') for line in f.readlines()]

        assert len(actual_lines) == len(expected_lines), (
            f"Source file has been modified. Expected {len(expected_lines)} lines, "
            f"but found {len(actual_lines)} lines."
        )

        for i, (expected, actual) in enumerate(zip(expected_lines, actual_lines), 1):
            assert actual == expected, (
                f"Source file has been modified at line {i}.\n"
                f"Expected: '{expected}'\n"
                f"Actual:   '{actual}'"
            )

    def test_no_non_error_lines_in_output(self):
        """Verify that no non-ERROR lines are in the output file."""
        output_path = "/home/user/api_logs/timeout_errors.txt"

        with open(output_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines() if line.strip()]

        non_error_levels = ["[INFO]", "[DEBUG]", "[WARN]", "[WARNING]"]

        for i, line in enumerate(lines, 1):
            for level in non_error_levels:
                assert level not in line, (
                    f"Line {i} contains non-ERROR level '{level}'.\n"
                    f"Line content: '{line}'\n"
                    "Only ERROR level entries should be in the output."
                )

    def test_no_non_timeout_errors_in_output(self):
        """Verify that ERROR entries without 'timeout' are not in the output."""
        output_path = "/home/user/api_logs/timeout_errors.txt"

        # These are ERROR entries that should NOT be in the output
        excluded_entries = [
            "Invalid card number format",
            "Authentication failed for merchant",
        ]

        with open(output_path, 'r') as f:
            content = f.read()

        for entry in excluded_entries:
            assert entry not in content, (
                f"Output file incorrectly contains '{entry}'.\n"
                "This ERROR entry does not contain 'timeout' and should be excluded."
            )