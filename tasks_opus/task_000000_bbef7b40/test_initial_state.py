# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student performs
the task of filtering timeout errors from the payment API log file.
"""

import os
import pytest


class TestInitialState:
    """Test the initial state of the filesystem before the task is performed."""

    def test_api_logs_directory_exists(self):
        """Verify that the api_logs directory exists."""
        dir_path = "/home/user/api_logs"
        assert os.path.isdir(dir_path), (
            f"Directory '{dir_path}' does not exist. "
            "The api_logs directory must be created before starting the task."
        )

    def test_payment_api_log_file_exists(self):
        """Verify that the payment_api.log file exists."""
        file_path = "/home/user/api_logs/payment_api.log"
        assert os.path.isfile(file_path), (
            f"File '{file_path}' does not exist. "
            "The payment_api.log file must be present before starting the task."
        )

    def test_payment_api_log_is_readable(self):
        """Verify that the payment_api.log file is readable."""
        file_path = "/home/user/api_logs/payment_api.log"
        assert os.access(file_path, os.R_OK), (
            f"File '{file_path}' is not readable. "
            "The payment_api.log file must have read permissions."
        )

    def test_payment_api_log_has_correct_line_count(self):
        """Verify that the payment_api.log file has exactly 13 lines."""
        file_path = "/home/user/api_logs/payment_api.log"
        with open(file_path, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 13, (
            f"File '{file_path}' should have exactly 13 lines, but has {len(lines)} lines. "
            "The payment_api.log file must contain the correct log entries."
        )

    def test_payment_api_log_contains_error_entries(self):
        """Verify that the log file contains ERROR level entries."""
        file_path = "/home/user/api_logs/payment_api.log"
        with open(file_path, 'r') as f:
            content = f.read()
        error_count = content.count("[ERROR]")
        assert error_count == 6, (
            f"File '{file_path}' should contain exactly 6 ERROR entries, but found {error_count}. "
            "The payment_api.log file must contain the correct log entries."
        )

    def test_payment_api_log_contains_timeout_entries(self):
        """Verify that the log file contains entries with 'timeout' (case-insensitive)."""
        file_path = "/home/user/api_logs/payment_api.log"
        with open(file_path, 'r') as f:
            content = f.read().lower()
        timeout_count = content.count("timeout")
        assert timeout_count >= 4, (
            f"File '{file_path}' should contain at least 4 occurrences of 'timeout', "
            f"but found {timeout_count}. "
            "The payment_api.log file must contain the correct log entries."
        )

    def test_payment_api_log_has_expected_content(self):
        """Verify that the log file contains the expected log entries."""
        file_path = "/home/user/api_logs/payment_api.log"

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

        with open(file_path, 'r') as f:
            actual_lines = [line.rstrip('\n') for line in f.readlines()]

        for i, expected_line in enumerate(expected_lines):
            assert i < len(actual_lines), (
                f"File '{file_path}' is missing line {i + 1}. "
                f"Expected: '{expected_line}'"
            )
            assert actual_lines[i] == expected_line, (
                f"Line {i + 1} in '{file_path}' does not match expected content.\n"
                f"Expected: '{expected_line}'\n"
                f"Actual:   '{actual_lines[i]}'"
            )

    def test_output_file_does_not_exist(self):
        """Verify that the output file does not exist yet (task not performed)."""
        output_path = "/home/user/api_logs/timeout_errors.txt"
        assert not os.path.exists(output_path), (
            f"Output file '{output_path}' already exists. "
            "The output file should not exist before the task is performed."
        )

    def test_api_logs_directory_is_writable(self):
        """Verify that the api_logs directory is writable (for creating output file)."""
        dir_path = "/home/user/api_logs"
        assert os.access(dir_path, os.W_OK), (
            f"Directory '{dir_path}' is not writable. "
            "The api_logs directory must have write permissions to create the output file."
        )