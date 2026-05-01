# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of extracting transaction IDs and amounts from a JSON file
to a CSV file.
"""

import csv
import json
import os
import subprocess
import pytest


class TestFinalState:
    """Tests for validating the final state after the task is performed."""

    def test_march_extract_csv_exists(self):
        """Verify /home/user/audit/march_extract.csv exists."""
        csv_file = "/home/user/audit/march_extract.csv"
        assert os.path.isfile(csv_file), (
            f"File {csv_file} does not exist. "
            "The output CSV file must be created by the task."
        )

    def test_march_extract_csv_is_readable(self):
        """Verify /home/user/audit/march_extract.csv is readable."""
        csv_file = "/home/user/audit/march_extract.csv"
        assert os.access(csv_file, os.R_OK), (
            f"File {csv_file} is not readable. "
            "The output CSV file must be readable."
        )

    def test_csv_has_exactly_48_lines(self):
        """Verify CSV has exactly 48 lines (1 header + 47 data rows)."""
        csv_file = "/home/user/audit/march_extract.csv"
        result = subprocess.run(
            ["wc", "-l"],
            stdin=open(csv_file, 'r'),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip())
        assert line_count == 48, (
            f"CSV file should have exactly 48 lines (1 header + 47 data rows), "
            f"but has {line_count} lines."
        )

    def test_csv_header_is_correct(self):
        """Verify first line is exactly 'txn_id,amount'."""
        csv_file = "/home/user/audit/march_extract.csv"
        result = subprocess.run(
            ["head", "-1", csv_file],
            capture_output=True,
            text=True
        )
        header = result.stdout.strip()
        assert header == "txn_id,amount", (
            f"CSV header must be exactly 'txn_id,amount', "
            f"but got '{header}'."
        )

    def test_csv_ends_with_newline(self):
        """Verify file ends with a newline."""
        csv_file = "/home/user/audit/march_extract.csv"
        with open(csv_file, 'rb') as f:
            f.seek(-1, 2)  # Go to last byte
            last_char = f.read(1)
        assert last_char == b'\n', (
            "CSV file must end with a newline character."
        )

    def test_csv_is_valid_csv_format(self):
        """Verify the file is valid CSV format."""
        csv_file = "/home/user/audit/march_extract.csv"
        try:
            with open(csv_file, 'r', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
        except csv.Error as e:
            pytest.fail(f"File {csv_file} is not valid CSV: {e}")

        assert len(rows) == 48, (
            f"CSV should have 48 rows (1 header + 47 data), got {len(rows)}."
        )

    def test_csv_has_two_columns(self):
        """Verify each row has exactly two columns."""
        csv_file = "/home/user/audit/march_extract.csv"
        with open(csv_file, 'r', newline='') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                assert len(row) == 2, (
                    f"Row {i} should have exactly 2 columns, "
                    f"but has {len(row)}: {row}"
                )

    def test_all_txn_ids_from_source_present(self):
        """Verify all 47 transaction IDs from source JSON are in the CSV."""
        json_file = "/home/user/audit/march_payments.json"
        csv_file = "/home/user/audit/march_extract.csv"

        # Load source transaction IDs
        with open(json_file, 'r') as f:
            source_data = json.load(f)
        source_txn_ids = {obj["txn_id"] for obj in source_data}

        # Load CSV transaction IDs
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            csv_txn_ids = {row["txn_id"] for row in reader}

        missing_txn_ids = source_txn_ids - csv_txn_ids
        extra_txn_ids = csv_txn_ids - source_txn_ids

        assert not missing_txn_ids, (
            f"CSV is missing transaction IDs from source: {missing_txn_ids}"
        )
        assert not extra_txn_ids, (
            f"CSV contains transaction IDs not in source: {extra_txn_ids}"
        )

    def test_amounts_match_source(self):
        """Verify amounts in CSV match the source JSON values."""
        json_file = "/home/user/audit/march_payments.json"
        csv_file = "/home/user/audit/march_extract.csv"

        # Load source data as dict of txn_id -> amount
        with open(json_file, 'r') as f:
            source_data = json.load(f)
        source_amounts = {obj["txn_id"]: obj["amount"] for obj in source_data}

        # Load CSV data
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                txn_id = row["txn_id"]
                csv_amount = float(row["amount"])
                source_amount = source_amounts.get(txn_id)

                assert source_amount is not None, (
                    f"Transaction ID {txn_id} not found in source."
                )

                # Allow small floating point tolerance
                assert abs(csv_amount - source_amount) < 0.001, (
                    f"Amount mismatch for {txn_id}: "
                    f"CSV has {csv_amount}, source has {source_amount}"
                )

    def test_source_json_unchanged(self):
        """Verify source JSON file still exists and has 47 records."""
        json_file = "/home/user/audit/march_payments.json"

        assert os.path.isfile(json_file), (
            f"Source file {json_file} no longer exists. "
            "The source file must not be deleted."
        )

        with open(json_file, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), (
            f"Source file {json_file} no longer contains a JSON array."
        )

        assert len(data) == 47, (
            f"Source file {json_file} should still have 47 records, "
            f"but has {len(data)}."
        )

        # Verify structure is intact
        required_keys = {"txn_id", "amount", "merchant", "timestamp", "status"}
        for i, obj in enumerate(data):
            assert isinstance(obj, dict), (
                f"Item at index {i} in source is no longer a dict."
            )
            missing_keys = required_keys - set(obj.keys())
            assert not missing_keys, (
                f"Source object at index {i} is missing keys: {missing_keys}. "
                "Source file may have been corrupted."
            )

    def test_csv_data_rows_have_valid_txn_id_format(self):
        """Verify transaction IDs in CSV are non-empty strings."""
        csv_file = "/home/user/audit/march_extract.csv"

        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                txn_id = row.get("txn_id", "")
                assert txn_id and isinstance(txn_id, str) and len(txn_id.strip()) > 0, (
                    f"Data row {i+1} has invalid or empty txn_id: '{txn_id}'"
                )

    def test_csv_data_rows_have_valid_amount_format(self):
        """Verify amounts in CSV are valid numeric values."""
        csv_file = "/home/user/audit/march_extract.csv"

        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                amount_str = row.get("amount", "")
                try:
                    amount = float(amount_str)
                except (ValueError, TypeError):
                    pytest.fail(
                        f"Data row {i+1} has invalid amount: '{amount_str}'. "
                        "Amount must be a valid numeric value."
                    )
