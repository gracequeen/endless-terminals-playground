# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the audit log processing task.
"""

import os
import json
import pytest


class TestInitialState:
    """Test suite to validate the initial state before processing."""

    AUDIT_DIR = "/home/user/audit"
    INPUT_FILE = "/home/user/audit/raw_transactions.jsonl"

    # Output files that should NOT exist initially
    OUTPUT_FILES = [
        "/home/user/audit/clean_audit.jsonl",
        "/home/user/audit/error_log.jsonl",
        "/home/user/audit/processing_summary.txt"
    ]

    # Expected content of each line in the input file
    EXPECTED_LINES = [
        '{"transaction_id": "TXN-00000001", "timestamp": "2024-03-15T09:00:00Z", "account_id": "ACC-001", "amount": 150.00, "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000002", "timestamp": "2024-03-15T09:05:30Z", "account_id": "ACC-002", "amount": -75.50, "currency": "EUR", "status": "completed"}',
        '{"transaction_id": "TXN-00000003", "timestamp": "2024-03-15T08:30:00Z", "account_id": "ACC-001", "amount": 200.00, "currency": "GBP", "status": "pending"}',
        'this is not valid json at all',
        '{"transaction_id": "TXN-00000005", "timestamp": "2024-03-15T10:00:00Z", "account_id": "", "amount": 50.00, "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000006", "timestamp": "2024-03-15T10:15:00Z", "account_id": "ACC-003", "amount": 300.00, "currency": "usd", "status": "completed"}',
        '{"transaction_id": "INVALID-ID", "timestamp": "2024-03-15T10:30:00Z", "account_id": "ACC-004", "amount": 125.75, "currency": "CAD", "status": "completed"}',
        '{"transaction_id": "TXN-00000008", "timestamp": "2024-03-15T10:45:00Z", "account_id": "ACC-005", "amount": "not_a_number", "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000009", "timestamp": "2024-03-15T11:00:00Z", "account_id": "ACC-006", "amount": 500.00, "currency": "JPY", "status": "completed"}',
        '{"transaction_id": "TXN-00000010", "timestamp": "invalid-timestamp", "account_id": "ACC-007", "amount": 250.00, "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000011", "timestamp": "2024-03-15T11:30:00Z", "account_id": "ACC-008", "amount": -1000.00, "currency": "USD", "status": "reversed"}',
        '{"transaction_id": "TXN-00000012", "timestamp": "2024-03-15T11:45:00Z", "account_id": "ACC-009", "amount": 75.25, "currency": "USD", "status": "unknown_status"}',
        '{malformed json with missing quotes: value}',
        '{"transaction_id": "TXN-00000014", "timestamp": "2024-03-15T12:00:00Z", "account_id": "ACC-010", "amount": 999.99, "currency": "CHF", "status": "failed"}',
        '{"timestamp": "2024-03-15T12:15:00Z", "account_id": "ACC-011", "amount": 50.00, "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000016", "timestamp": "2024-03-15T12:30:00Z", "account_id": "ACC-012", "amount": 175.00, "currency": "USD", "status": "pending"}',
        '{"transaction_id": "TXN-00000017", "timestamp": "2024-03-15T12:45:00Z", "account_id": "ACC-013", "amount": 0.01, "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000018", "account_id": "ACC-014", "amount": 100.00, "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000019", "timestamp": "2024-03-15T13:15:00Z", "account_id": "ACC-015", "amount": -25.00, "currency": "AUD", "status": "completed"}',
        '{"transaction_id": "TXN-00000020", "timestamp": "2024-03-15T13:30:00Z", "account_id": "ACC-016", "amount": 450.00, "currency": "TOOLONG", "status": "completed"}',
        '{"transaction_id": "TXN-00000021", "timestamp": "2024-03-15T13:45:00Z", "account_id": "ACC-017", "amount": 600.00, "currency": "NZD", "status": "completed"}',
        '',
        '{"transaction_id": "TXN-00000023", "timestamp": "2024-03-15T14:15:00Z", "account_id": "ACC-018", "amount": 85.50, "currency": "USD", "status": "completed"}',
        '{"transaction_id": "TXN-00000024", "timestamp": "2024-03-15T14:30:00Z", "account_id": "ACC-019", "amount": 320.00, "currency": "EUR", "status": "pending"}',
        '{"transaction_id": "TXN-00000025", "timestamp": "2024-03-15T07:00:00Z", "account_id": "ACC-020", "amount": 1500.00, "currency": "USD", "status": "completed"}',
    ]

    def test_audit_directory_exists(self):
        """Test that the /home/user/audit/ directory exists."""
        assert os.path.exists(self.AUDIT_DIR), (
            f"Directory {self.AUDIT_DIR} does not exist. "
            "The audit directory must be present before processing."
        )

    def test_audit_directory_is_directory(self):
        """Test that /home/user/audit/ is actually a directory."""
        assert os.path.isdir(self.AUDIT_DIR), (
            f"{self.AUDIT_DIR} exists but is not a directory. "
            "The audit path must be a directory."
        )

    def test_audit_directory_is_writable(self):
        """Test that the /home/user/audit/ directory is writable."""
        assert os.access(self.AUDIT_DIR, os.W_OK), (
            f"Directory {self.AUDIT_DIR} is not writable. "
            "The audit directory must be writable to create output files."
        )

    def test_input_file_exists(self):
        """Test that the input file raw_transactions.jsonl exists."""
        assert os.path.exists(self.INPUT_FILE), (
            f"Input file {self.INPUT_FILE} does not exist. "
            "The raw transaction log file must be present before processing."
        )

    def test_input_file_is_file(self):
        """Test that raw_transactions.jsonl is a regular file."""
        assert os.path.isfile(self.INPUT_FILE), (
            f"{self.INPUT_FILE} exists but is not a regular file. "
            "The input must be a regular file."
        )

    def test_input_file_is_readable(self):
        """Test that the input file is readable."""
        assert os.access(self.INPUT_FILE, os.R_OK), (
            f"Input file {self.INPUT_FILE} is not readable. "
            "The raw transaction log file must be readable."
        )

    def test_input_file_has_exactly_25_lines(self):
        """Test that the input file has exactly 25 lines."""
        with open(self.INPUT_FILE, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 25, (
            f"Input file {self.INPUT_FILE} has {len(lines)} lines, expected exactly 25 lines. "
            "The raw transaction log must contain exactly 25 transaction records/lines."
        )

    def test_input_file_line_content(self):
        """Test that each line in the input file matches expected content."""
        with open(self.INPUT_FILE, 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]

        for i, (actual, expected) in enumerate(zip(lines, self.EXPECTED_LINES), start=1):
            # For JSON lines, we need to compare the parsed content, not string equality
            # because JSON formatting might differ (e.g., spacing)
            if expected and not expected.startswith('{malformed') and expected != 'this is not valid json at all':
                try:
                    expected_parsed = json.loads(expected)
                    actual_parsed = json.loads(actual)
                    assert actual_parsed == expected_parsed, (
                        f"Line {i} content mismatch.\n"
                        f"Expected: {expected}\n"
                        f"Actual: {actual}"
                    )
                except json.JSONDecodeError:
                    # If expected is valid JSON but actual isn't, or vice versa
                    assert actual == expected, (
                        f"Line {i} content mismatch.\n"
                        f"Expected: {expected}\n"
                        f"Actual: {actual}"
                    )
            else:
                # For non-JSON lines, compare directly
                assert actual == expected, (
                    f"Line {i} content mismatch.\n"
                    f"Expected: {expected!r}\n"
                    f"Actual: {actual!r}"
                )

    def test_line_4_is_malformed_json(self):
        """Test that line 4 contains invalid JSON text."""
        with open(self.INPUT_FILE, 'r') as f:
            lines = f.readlines()

        line_4 = lines[3].strip()
        assert line_4 == "this is not valid json at all", (
            f"Line 4 should be 'this is not valid json at all', got: {line_4!r}"
        )

    def test_line_13_is_malformed_json(self):
        """Test that line 13 contains malformed JSON."""
        with open(self.INPUT_FILE, 'r') as f:
            lines = f.readlines()

        line_13 = lines[12].strip()
        assert line_13 == "{malformed json with missing quotes: value}", (
            f"Line 13 should be malformed JSON, got: {line_13!r}"
        )

    def test_line_22_is_empty(self):
        """Test that line 22 is empty."""
        with open(self.INPUT_FILE, 'r') as f:
            lines = f.readlines()

        line_22 = lines[21].strip()
        assert line_22 == "", (
            f"Line 22 should be empty, got: {line_22!r}"
        )

    def test_clean_audit_file_does_not_exist(self):
        """Test that the output file clean_audit.jsonl does not exist initially."""
        output_file = "/home/user/audit/clean_audit.jsonl"
        assert not os.path.exists(output_file), (
            f"Output file {output_file} already exists. "
            "Output files should not exist before processing."
        )

    def test_error_log_file_does_not_exist(self):
        """Test that the output file error_log.jsonl does not exist initially."""
        output_file = "/home/user/audit/error_log.jsonl"
        assert not os.path.exists(output_file), (
            f"Output file {output_file} already exists. "
            "Output files should not exist before processing."
        )

    def test_processing_summary_file_does_not_exist(self):
        """Test that the output file processing_summary.txt does not exist initially."""
        output_file = "/home/user/audit/processing_summary.txt"
        assert not os.path.exists(output_file), (
            f"Output file {output_file} already exists. "
            "Output files should not exist before processing."
        )

    def test_python3_available(self):
        """Test that Python 3 is available."""
        import sys
        assert sys.version_info.major == 3, (
            f"Python 3 is required, but Python {sys.version_info.major} is running."
        )

    def test_json_module_available(self):
        """Test that the json module is available."""
        try:
            import json
        except ImportError:
            pytest.fail("The json module is not available in the Python standard library.")

    def test_hashlib_module_available(self):
        """Test that the hashlib module is available."""
        try:
            import hashlib
        except ImportError:
            pytest.fail("The hashlib module is not available in the Python standard library.")

    def test_datetime_module_available(self):
        """Test that the datetime module is available."""
        try:
            import datetime
        except ImportError:
            pytest.fail("The datetime module is not available in the Python standard library.")

    def test_re_module_available(self):
        """Test that the re module is available."""
        try:
            import re
        except ImportError:
            pytest.fail("The re module is not available in the Python standard library.")

    def test_valid_json_lines_are_parseable(self):
        """Test that the expected valid JSON lines can be parsed."""
        valid_line_numbers = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25]

        with open(self.INPUT_FILE, 'r') as f:
            lines = f.readlines()

        for line_num in valid_line_numbers:
            line = lines[line_num - 1].strip()
            if line:  # Skip empty lines
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(
                        f"Line {line_num} should be valid JSON but failed to parse: {e}\n"
                        f"Content: {line!r}"
                    )
