# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the audit log processing task.
"""

import os
import json
import hashlib
import re
from datetime import datetime
import pytest


class TestFinalState:
    """Test suite to validate the final state after processing."""

    AUDIT_DIR = "/home/user/audit"
    INPUT_FILE = "/home/user/audit/raw_transactions.jsonl"
    CLEAN_AUDIT_FILE = "/home/user/audit/clean_audit.jsonl"
    ERROR_LOG_FILE = "/home/user/audit/error_log.jsonl"
    SUMMARY_FILE = "/home/user/audit/processing_summary.txt"

    # Expected valid transaction IDs in timestamp-sorted order
    EXPECTED_VALID_TXN_IDS = [
        "TXN-00000025",  # 07:00:00Z
        "TXN-00000003",  # 08:30:00Z
        "TXN-00000001",  # 09:00:00Z
        "TXN-00000002",  # 09:05:30Z
        "TXN-00000009",  # 11:00:00Z
        "TXN-00000011",  # 11:30:00Z
        "TXN-00000014",  # 12:00:00Z
        "TXN-00000016",  # 12:30:00Z
        "TXN-00000017",  # 12:45:00Z
        "TXN-00000019",  # 13:15:00Z
        "TXN-00000021",  # 13:45:00Z
        "TXN-00000023",  # 14:15:00Z
        "TXN-00000024",  # 14:30:00Z
    ]

    # Expected valid transactions data (from input lines)
    EXPECTED_VALID_TRANSACTIONS = {
        "TXN-00000001": {"timestamp": "2024-03-15T09:00:00Z", "account_id": "ACC-001", "amount": 150.00, "currency": "USD", "status": "completed"},
        "TXN-00000002": {"timestamp": "2024-03-15T09:05:30Z", "account_id": "ACC-002", "amount": -75.50, "currency": "EUR", "status": "completed"},
        "TXN-00000003": {"timestamp": "2024-03-15T08:30:00Z", "account_id": "ACC-001", "amount": 200.00, "currency": "GBP", "status": "pending"},
        "TXN-00000009": {"timestamp": "2024-03-15T11:00:00Z", "account_id": "ACC-006", "amount": 500.00, "currency": "JPY", "status": "completed"},
        "TXN-00000011": {"timestamp": "2024-03-15T11:30:00Z", "account_id": "ACC-008", "amount": -1000.00, "currency": "USD", "status": "reversed"},
        "TXN-00000014": {"timestamp": "2024-03-15T12:00:00Z", "account_id": "ACC-010", "amount": 999.99, "currency": "CHF", "status": "failed"},
        "TXN-00000016": {"timestamp": "2024-03-15T12:30:00Z", "account_id": "ACC-012", "amount": 175.00, "currency": "USD", "status": "pending"},
        "TXN-00000017": {"timestamp": "2024-03-15T12:45:00Z", "account_id": "ACC-013", "amount": 0.01, "currency": "USD", "status": "completed"},
        "TXN-00000019": {"timestamp": "2024-03-15T13:15:00Z", "account_id": "ACC-015", "amount": -25.00, "currency": "AUD", "status": "completed"},
        "TXN-00000021": {"timestamp": "2024-03-15T13:45:00Z", "account_id": "ACC-017", "amount": 600.00, "currency": "NZD", "status": "completed"},
        "TXN-00000023": {"timestamp": "2024-03-15T14:15:00Z", "account_id": "ACC-018", "amount": 85.50, "currency": "USD", "status": "completed"},
        "TXN-00000024": {"timestamp": "2024-03-15T14:30:00Z", "account_id": "ACC-019", "amount": 320.00, "currency": "EUR", "status": "pending"},
        "TXN-00000025": {"timestamp": "2024-03-15T07:00:00Z", "account_id": "ACC-020", "amount": 1500.00, "currency": "USD", "status": "completed"},
    }

    # Expected errors (line_number, error_type)
    EXPECTED_ERRORS = [
        (4, "malformed_json"),
        (5, "invalid_value"),
        (6, "invalid_format"),
        (7, "invalid_format"),
        (8, "invalid_format"),
        (10, "invalid_format"),
        (12, "invalid_value"),
        (13, "malformed_json"),
        (15, "missing_field"),
        (18, "missing_field"),
        (20, "invalid_format"),
        (22, "malformed_json"),
    ]

    def compute_integrity_hash(self, txn_id, timestamp, account_id, amount, currency, status):
        """Compute the expected SHA-256 integrity hash for a transaction."""
        amount_str = f"{amount:.2f}"
        canonical = f"{txn_id}|{timestamp}|{account_id}|{amount_str}|{currency}|{status}"
        return hashlib.sha256(canonical.encode()).hexdigest()

    # ==================== Output File Existence Tests ====================

    def test_clean_audit_file_exists(self):
        """Test that clean_audit.jsonl was created."""
        assert os.path.exists(self.CLEAN_AUDIT_FILE), (
            f"Output file {self.CLEAN_AUDIT_FILE} does not exist. "
            "The clean audit file must be created after processing."
        )

    def test_clean_audit_file_is_file(self):
        """Test that clean_audit.jsonl is a regular file."""
        assert os.path.isfile(self.CLEAN_AUDIT_FILE), (
            f"{self.CLEAN_AUDIT_FILE} exists but is not a regular file."
        )

    def test_error_log_file_exists(self):
        """Test that error_log.jsonl was created."""
        assert os.path.exists(self.ERROR_LOG_FILE), (
            f"Output file {self.ERROR_LOG_FILE} does not exist. "
            "The error log file must be created after processing."
        )

    def test_error_log_file_is_file(self):
        """Test that error_log.jsonl is a regular file."""
        assert os.path.isfile(self.ERROR_LOG_FILE), (
            f"{self.ERROR_LOG_FILE} exists but is not a regular file."
        )

    def test_summary_file_exists(self):
        """Test that processing_summary.txt was created."""
        assert os.path.exists(self.SUMMARY_FILE), (
            f"Output file {self.SUMMARY_FILE} does not exist. "
            "The processing summary file must be created after processing."
        )

    def test_summary_file_is_file(self):
        """Test that processing_summary.txt is a regular file."""
        assert os.path.isfile(self.SUMMARY_FILE), (
            f"{self.SUMMARY_FILE} exists but is not a regular file."
        )

    # ==================== Clean Audit File Tests ====================

    def test_clean_audit_has_exactly_13_records(self):
        """Test that clean_audit.jsonl has exactly 13 valid transaction records."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        assert len(lines) == 13, (
            f"clean_audit.jsonl has {len(lines)} records, expected exactly 13 valid transactions."
        )

    def test_clean_audit_records_are_valid_json(self):
        """Test that all records in clean_audit.jsonl are valid JSON."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as e:
                        pytest.fail(
                            f"Line {i} in clean_audit.jsonl is not valid JSON: {e}\n"
                            f"Content: {line!r}"
                        )

    def test_clean_audit_records_have_required_fields(self):
        """Test that all records have the required fields including integrity_hash and processed_at."""
        required_fields = ["transaction_id", "timestamp", "account_id", "amount", "currency", "status", "integrity_hash", "processed_at"]

        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    record = json.loads(line)
                    for field in required_fields:
                        assert field in record, (
                            f"Record {i} in clean_audit.jsonl is missing required field '{field}'.\n"
                            f"Record: {record}"
                        )

    def test_clean_audit_sorted_by_timestamp_ascending(self):
        """Test that records in clean_audit.jsonl are sorted by timestamp ascending."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        timestamps = [r["timestamp"] for r in records]
        sorted_timestamps = sorted(timestamps)

        assert timestamps == sorted_timestamps, (
            f"Records in clean_audit.jsonl are not sorted by timestamp ascending.\n"
            f"Actual order: {timestamps}\n"
            f"Expected order: {sorted_timestamps}"
        )

    def test_clean_audit_transaction_ids_match_expected(self):
        """Test that the transaction IDs in clean_audit.jsonl match expected valid transactions."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        actual_txn_ids = [r["transaction_id"] for r in records]

        assert actual_txn_ids == self.EXPECTED_VALID_TXN_IDS, (
            f"Transaction IDs in clean_audit.jsonl do not match expected.\n"
            f"Actual: {actual_txn_ids}\n"
            f"Expected: {self.EXPECTED_VALID_TXN_IDS}"
        )

    def test_clean_audit_integrity_hashes_are_correct(self):
        """Test that integrity hashes are correctly computed for each record."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        for record in records:
            txn_id = record["transaction_id"]
            expected_hash = self.compute_integrity_hash(
                record["transaction_id"],
                record["timestamp"],
                record["account_id"],
                record["amount"],
                record["currency"],
                record["status"]
            )
            actual_hash = record["integrity_hash"]

            assert actual_hash == expected_hash, (
                f"Integrity hash mismatch for {txn_id}.\n"
                f"Expected: {expected_hash}\n"
                f"Actual: {actual_hash}\n"
                f"Record: {record}"
            )

    def test_clean_audit_processed_at_is_valid_iso8601(self):
        """Test that processed_at fields are valid ISO 8601 timestamps."""
        iso8601_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$')

        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        for record in records:
            processed_at = record["processed_at"]
            # Allow for slight variations in ISO 8601 format
            assert iso8601_pattern.match(processed_at) or 'T' in processed_at, (
                f"processed_at field is not valid ISO 8601 format for {record['transaction_id']}.\n"
                f"Value: {processed_at}"
            )

    def test_clean_audit_transaction_data_matches_expected(self):
        """Test that transaction data in clean_audit.jsonl matches expected values."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        for record in records:
            txn_id = record["transaction_id"]
            expected = self.EXPECTED_VALID_TRANSACTIONS[txn_id]

            assert record["timestamp"] == expected["timestamp"], (
                f"Timestamp mismatch for {txn_id}. Expected: {expected['timestamp']}, Actual: {record['timestamp']}"
            )
            assert record["account_id"] == expected["account_id"], (
                f"Account ID mismatch for {txn_id}. Expected: {expected['account_id']}, Actual: {record['account_id']}"
            )
            assert abs(record["amount"] - expected["amount"]) < 0.001, (
                f"Amount mismatch for {txn_id}. Expected: {expected['amount']}, Actual: {record['amount']}"
            )
            assert record["currency"] == expected["currency"], (
                f"Currency mismatch for {txn_id}. Expected: {expected['currency']}, Actual: {record['currency']}"
            )
            assert record["status"] == expected["status"], (
                f"Status mismatch for {txn_id}. Expected: {expected['status']}, Actual: {record['status']}"
            )

    # ==================== Error Log File Tests ====================

    def test_error_log_has_exactly_12_records(self):
        """Test that error_log.jsonl has exactly 12 error records."""
        with open(self.ERROR_LOG_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        assert len(lines) == 12, (
            f"error_log.jsonl has {len(lines)} records, expected exactly 12 error records."
        )

    def test_error_log_records_are_valid_json(self):
        """Test that all records in error_log.jsonl are valid JSON."""
        with open(self.ERROR_LOG_FILE, 'r') as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as e:
                        pytest.fail(
                            f"Line {i} in error_log.jsonl is not valid JSON: {e}\n"
                            f"Content: {line!r}"
                        )

    def test_error_log_records_have_required_fields(self):
        """Test that all error records have the required fields."""
        required_fields = ["line_number", "error_type", "error_detail", "raw_content"]

        with open(self.ERROR_LOG_FILE, 'r') as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    record = json.loads(line)
                    for field in required_fields:
                        assert field in record, (
                            f"Error record {i} in error_log.jsonl is missing required field '{field}'.\n"
                            f"Record: {record}"
                        )

    def test_error_log_line_numbers_match_expected(self):
        """Test that error line numbers match expected error lines."""
        with open(self.ERROR_LOG_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        actual_line_numbers = [r["line_number"] for r in records]
        expected_line_numbers = [e[0] for e in self.EXPECTED_ERRORS]

        assert actual_line_numbers == expected_line_numbers, (
            f"Error line numbers do not match expected.\n"
            f"Actual: {actual_line_numbers}\n"
            f"Expected: {expected_line_numbers}"
        )

    def test_error_log_error_types_match_expected(self):
        """Test that error types match expected error types."""
        with open(self.ERROR_LOG_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        for i, record in enumerate(records):
            expected_line, expected_type = self.EXPECTED_ERRORS[i]
            actual_type = record["error_type"]

            assert actual_type == expected_type, (
                f"Error type mismatch for line {expected_line}.\n"
                f"Expected: {expected_type}\n"
                f"Actual: {actual_type}"
            )

    def test_error_log_error_types_are_valid(self):
        """Test that all error types are one of the valid types."""
        valid_error_types = ["malformed_json", "missing_field", "invalid_format", "invalid_value"]

        with open(self.ERROR_LOG_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        for record in records:
            error_type = record["error_type"]
            assert error_type in valid_error_types, (
                f"Invalid error_type '{error_type}' for line {record['line_number']}.\n"
                f"Must be one of: {valid_error_types}"
            )

    def test_error_log_raw_content_truncated_to_200_chars(self):
        """Test that raw_content is truncated to 200 characters max."""
        with open(self.ERROR_LOG_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        for record in records:
            raw_content = record["raw_content"]
            assert len(raw_content) <= 200, (
                f"raw_content for line {record['line_number']} exceeds 200 characters.\n"
                f"Length: {len(raw_content)}"
            )

    def test_error_log_in_order_encountered(self):
        """Test that errors are in the order they were encountered (by line number)."""
        with open(self.ERROR_LOG_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        line_numbers = [r["line_number"] for r in records]
        assert line_numbers == sorted(line_numbers), (
            f"Error records are not in order encountered.\n"
            f"Line numbers: {line_numbers}"
        )

    # ==================== Processing Summary Tests ====================

    def test_summary_contains_header(self):
        """Test that summary file contains the correct header."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "AUDIT PROCESSING SUMMARY" in content, (
            "Summary file is missing 'AUDIT PROCESSING SUMMARY' header."
        )
        assert "========================" in content, (
            "Summary file is missing header underline."
        )

    def test_summary_contains_input_file_path(self):
        """Test that summary file contains the correct input file path."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "Input file: /home/user/audit/raw_transactions.jsonl" in content, (
            "Summary file is missing or has incorrect input file path."
        )

    def test_summary_total_lines_processed(self):
        """Test that summary shows 25 total lines processed."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "Total lines processed: 25" in content, (
            f"Summary file should show 'Total lines processed: 25'.\n"
            f"Content: {content}"
        )

    def test_summary_valid_transactions(self):
        """Test that summary shows 13 valid transactions."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "Valid transactions: 13" in content, (
            f"Summary file should show 'Valid transactions: 13'.\n"
            f"Content: {content}"
        )

    def test_summary_failed_records(self):
        """Test that summary shows 12 failed records."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "Failed records: 12" in content, (
            f"Summary file should show 'Failed records: 12'.\n"
            f"Content: {content}"
        )

    def test_summary_success_rate(self):
        """Test that summary shows 52.00% success rate."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "Success rate: 52.00%" in content, (
            f"Summary file should show 'Success rate: 52.00%'.\n"
            f"Content: {content}"
        )

    def test_summary_errors_by_type_section(self):
        """Test that summary contains 'Errors by type:' section."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "Errors by type:" in content, (
            "Summary file is missing 'Errors by type:' section."
        )

    def test_summary_malformed_json_count(self):
        """Test that summary shows malformed_json: 3."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "malformed_json: 3" in content, (
            f"Summary file should show 'malformed_json: 3'.\n"
            f"Content: {content}"
        )

    def test_summary_missing_field_count(self):
        """Test that summary shows missing_field: 2."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "missing_field: 2" in content, (
            f"Summary file should show 'missing_field: 2'.\n"
            f"Content: {content}"
        )

    def test_summary_invalid_format_count(self):
        """Test that summary shows invalid_format: 5."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "invalid_format: 5" in content, (
            f"Summary file should show 'invalid_format: 5'.\n"
            f"Content: {content}"
        )

    def test_summary_invalid_value_count(self):
        """Test that summary shows invalid_value: 2."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "invalid_value: 2" in content, (
            f"Summary file should show 'invalid_value: 2'.\n"
            f"Content: {content}"
        )

    def test_summary_processing_completed_timestamp(self):
        """Test that summary contains 'Processing completed at:' with a timestamp."""
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        assert "Processing completed at:" in content, (
            "Summary file is missing 'Processing completed at:' line."
        )

    def test_summary_error_counts_match_error_log(self):
        """Test that error counts in summary match the actual error_log.jsonl contents."""
        # Count errors by type from error_log.jsonl
        with open(self.ERROR_LOG_FILE, 'r') as f:
            error_records = [json.loads(line.strip()) for line in f if line.strip()]

        error_counts = {
            "malformed_json": 0,
            "missing_field": 0,
            "invalid_format": 0,
            "invalid_value": 0
        }
        for record in error_records:
            error_type = record["error_type"]
            if error_type in error_counts:
                error_counts[error_type] += 1

        # Read summary and verify counts
        with open(self.SUMMARY_FILE, 'r') as f:
            content = f.read()

        for error_type, count in error_counts.items():
            expected_str = f"{error_type}: {count}"
            assert expected_str in content, (
                f"Summary error count mismatch for {error_type}.\n"
                f"Expected '{expected_str}' in summary.\n"
                f"Actual error_log counts: {error_counts}"
            )

    # ==================== Consistency Tests ====================

    def test_valid_plus_failed_equals_total(self):
        """Test that valid transactions + failed records = total lines."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            valid_count = len([line for line in f if line.strip()])

        with open(self.ERROR_LOG_FILE, 'r') as f:
            failed_count = len([line for line in f if line.strip()])

        total = valid_count + failed_count
        assert total == 25, (
            f"Valid ({valid_count}) + Failed ({failed_count}) = {total}, expected 25 total lines."
        )

    def test_no_duplicate_transaction_ids_in_clean_audit(self):
        """Test that there are no duplicate transaction IDs in clean_audit.jsonl."""
        with open(self.CLEAN_AUDIT_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        txn_ids = [r["transaction_id"] for r in records]
        unique_txn_ids = set(txn_ids)

        assert len(txn_ids) == len(unique_txn_ids), (
            f"Duplicate transaction IDs found in clean_audit.jsonl.\n"
            f"Total: {len(txn_ids)}, Unique: {len(unique_txn_ids)}"
        )

    def test_no_duplicate_line_numbers_in_error_log(self):
        """Test that there are no duplicate line numbers in error_log.jsonl."""
        with open(self.ERROR_LOG_FILE, 'r') as f:
            records = [json.loads(line.strip()) for line in f if line.strip()]

        line_numbers = [r["line_number"] for r in records]
        unique_line_numbers = set(line_numbers)

        assert len(line_numbers) == len(unique_line_numbers), (
            f"Duplicate line numbers found in error_log.jsonl.\n"
            f"Total: {len(line_numbers)}, Unique: {len(unique_line_numbers)}"
        )
