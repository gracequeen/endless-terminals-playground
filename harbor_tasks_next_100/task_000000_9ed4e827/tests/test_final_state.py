# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the JSON to CSV conversion task.
"""

import csv
import json
import os
import pytest


class TestFinalState:
    """Tests to verify the final state after task execution."""

    JSON_FILE = "/home/user/experiments/run_047.json"
    CSV_FILE = "/home/user/experiments/run_047.csv"

    EXPECTED_JSON_DATA = {
        "run_id": "047",
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 50,
        "dropout": 0.2,
        "optimizer": "adam"
    }

    def test_csv_file_exists(self):
        """Verify /home/user/experiments/run_047.csv exists."""
        assert os.path.isfile(self.CSV_FILE), (
            f"Output CSV file {self.CSV_FILE} does not exist. "
            "The task requires creating this CSV file from the JSON source."
        )

    def test_csv_file_readable(self):
        """Verify /home/user/experiments/run_047.csv is readable."""
        assert os.access(self.CSV_FILE, os.R_OK), (
            f"Output CSV file {self.CSV_FILE} is not readable."
        )

    def test_csv_parseable_by_python_csv_module(self):
        """Verify the CSV file is valid and parseable by Python's csv module."""
        try:
            with open(self.CSV_FILE, 'r', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            pytest.fail(
                f"CSV file {self.CSV_FILE} is not parseable by Python's csv module: {e}"
            )

        assert len(rows) >= 1, (
            "CSV file appears to be empty or unparseable."
        )

    def test_csv_has_exactly_two_lines(self):
        """Verify the CSV file has exactly 2 lines (header + data row)."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 2, (
            f"CSV file must have exactly 2 lines (header + data row). "
            f"Found {len(rows)} line(s)."
        )

    def test_csv_header_contains_all_keys(self):
        """Verify the header row contains all six keys from the JSON."""
        expected_keys = set(self.EXPECTED_JSON_DATA.keys())

        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) >= 1, "CSV file is empty, no header row found."

        header = rows[0]
        header_set = set(header)

        missing_keys = expected_keys - header_set
        assert not missing_keys, (
            f"Header row is missing required keys: {missing_keys}. "
            f"Header contains: {header}"
        )

        assert len(header) == len(expected_keys), (
            f"Header should have exactly {len(expected_keys)} columns. "
            f"Found {len(header)} columns: {header}"
        )

    def test_csv_data_row_has_correct_number_of_values(self):
        """Verify the data row has the same number of values as the header."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) >= 2, "CSV file missing data row."

        header = rows[0]
        data_row = rows[1]

        assert len(data_row) == len(header), (
            f"Data row has {len(data_row)} values but header has {len(header)} columns. "
            f"Header: {header}, Data: {data_row}"
        )

    def test_csv_values_match_json_exactly(self):
        """Verify the CSV values match the JSON values exactly."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_row = rows[1]

        # Create a dict from the CSV data
        csv_data = dict(zip(header, data_row))

        # Check each expected value
        for key, expected_value in self.EXPECTED_JSON_DATA.items():
            assert key in csv_data, (
                f"Key '{key}' not found in CSV header."
            )

            csv_value = csv_data[key]

            # Handle type conversion for comparison
            if isinstance(expected_value, str):
                assert csv_value == expected_value, (
                    f"Value mismatch for '{key}': expected '{expected_value}', got '{csv_value}'"
                )
            elif isinstance(expected_value, int):
                try:
                    actual_int = int(csv_value)
                    assert actual_int == expected_value, (
                        f"Value mismatch for '{key}': expected {expected_value}, got {actual_int}"
                    )
                except ValueError:
                    # Maybe stored as float string
                    try:
                        actual_float = float(csv_value)
                        assert actual_float == expected_value, (
                            f"Value mismatch for '{key}': expected {expected_value}, got {actual_float}"
                        )
                    except ValueError:
                        pytest.fail(
                            f"Value for '{key}' is not a valid number: '{csv_value}'"
                        )
            elif isinstance(expected_value, float):
                try:
                    actual_float = float(csv_value)
                    assert abs(actual_float - expected_value) < 1e-9, (
                        f"Value mismatch for '{key}': expected {expected_value}, got {actual_float}"
                    )
                except ValueError:
                    pytest.fail(
                        f"Value for '{key}' is not a valid float: '{csv_value}'"
                    )

    def test_csv_run_id_value(self):
        """Verify run_id is '047' (string)."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_row = rows[1]
        csv_data = dict(zip(header, data_row))

        assert csv_data.get("run_id") == "047", (
            f"run_id should be '047', got '{csv_data.get('run_id')}'"
        )

    def test_csv_learning_rate_value(self):
        """Verify learning_rate is 0.001."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_row = rows[1]
        csv_data = dict(zip(header, data_row))

        lr_value = float(csv_data.get("learning_rate", "0"))
        assert abs(lr_value - 0.001) < 1e-9, (
            f"learning_rate should be 0.001, got {lr_value}"
        )

    def test_csv_batch_size_value(self):
        """Verify batch_size is 32."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_row = rows[1]
        csv_data = dict(zip(header, data_row))

        batch_value = csv_data.get("batch_size", "")
        # Could be "32" or "32.0"
        try:
            batch_int = int(float(batch_value))
            assert batch_int == 32, (
                f"batch_size should be 32, got {batch_int}"
            )
        except ValueError:
            pytest.fail(f"batch_size is not a valid number: '{batch_value}'")

    def test_csv_epochs_value(self):
        """Verify epochs is 50."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_row = rows[1]
        csv_data = dict(zip(header, data_row))

        epochs_value = csv_data.get("epochs", "")
        try:
            epochs_int = int(float(epochs_value))
            assert epochs_int == 50, (
                f"epochs should be 50, got {epochs_int}"
            )
        except ValueError:
            pytest.fail(f"epochs is not a valid number: '{epochs_value}'")

    def test_csv_dropout_value(self):
        """Verify dropout is 0.2."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_row = rows[1]
        csv_data = dict(zip(header, data_row))

        dropout_value = float(csv_data.get("dropout", "0"))
        assert abs(dropout_value - 0.2) < 1e-9, (
            f"dropout should be 0.2, got {dropout_value}"
        )

    def test_csv_optimizer_value(self):
        """Verify optimizer is 'adam'."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        data_row = rows[1]
        csv_data = dict(zip(header, data_row))

        assert csv_data.get("optimizer") == "adam", (
            f"optimizer should be 'adam', got '{csv_data.get('optimizer')}'"
        )

    def test_source_json_unchanged(self):
        """Verify /home/user/experiments/run_047.json is unchanged."""
        with open(self.JSON_FILE, 'r') as f:
            actual_data = json.load(f)

        assert actual_data == self.EXPECTED_JSON_DATA, (
            f"Source JSON file has been modified. "
            f"Expected: {self.EXPECTED_JSON_DATA}, Got: {actual_data}"
        )

    def test_source_json_still_exists(self):
        """Verify /home/user/experiments/run_047.json still exists."""
        assert os.path.isfile(self.JSON_FILE), (
            f"Source JSON file {self.JSON_FILE} no longer exists. "
            "The original file should not be deleted."
        )

    def test_all_six_fields_present_in_csv(self):
        """Anti-shortcut: Verify all six fields from JSON appear in CSV."""
        required_fields = {"run_id", "learning_rate", "batch_size", "epochs", "dropout", "optimizer"}

        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = set(rows[0])

        assert required_fields == header, (
            f"CSV must contain exactly these 6 fields: {required_fields}. "
            f"Found: {header}"
        )
