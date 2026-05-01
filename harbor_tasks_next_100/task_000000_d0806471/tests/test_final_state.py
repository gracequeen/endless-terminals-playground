# test_final_state.py
"""
Tests to validate the final state after the student has completed the JSON to CSV conversion task.
"""

import csv
import json
import os
import subprocess
import pytest


class TestFinalState:
    """Test suite to validate the final state after task completion."""

    EXPORTS_DIR = "/home/user/exports"
    JSON_FILE = "/home/user/exports/customers.json"
    CSV_FILE = "/home/user/exports/customers.csv"

    def test_csv_file_exists(self):
        """Verify that customers.csv exists."""
        assert os.path.isfile(self.CSV_FILE), (
            f"File {self.CSV_FILE} does not exist. "
            "The CSV file must be created as part of the task."
        )

    def test_csv_file_is_readable(self):
        """Verify that customers.csv is readable."""
        assert os.access(self.CSV_FILE, os.R_OK), (
            f"File {self.CSV_FILE} is not readable."
        )

    def test_csv_header_is_correct(self):
        """Verify that the first line of the CSV is the correct header: id,name,email"""
        with open(self.CSV_FILE, 'r', newline='') as f:
            first_line = f.readline().strip()

        assert first_line == "id,name,email", (
            f"Expected header line to be 'id,name,email', but got: '{first_line}'"
        )

    def test_csv_has_501_lines(self):
        """Verify that the CSV has exactly 501 lines (1 header + 500 data rows)."""
        with open(self.CSV_FILE, 'r') as f:
            line_count = sum(1 for _ in f)

        assert line_count == 501, (
            f"Expected exactly 501 lines (1 header + 500 data rows), "
            f"but found {line_count} lines."
        )

    def test_csv_has_500_data_rows(self):
        """Verify that the CSV has exactly 500 data rows after the header."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            data_rows = list(reader)

        assert len(data_rows) == 500, (
            f"Expected exactly 500 data rows, but found {len(data_rows)} rows."
        )

    def test_csv_is_valid_csv_format(self):
        """Verify that the CSV file can be parsed as valid CSV."""
        try:
            with open(self.CSV_FILE, 'r', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
        except csv.Error as e:
            pytest.fail(f"CSV file is not valid CSV format: {e}")

        assert len(rows) > 0, "CSV file is empty."

    def test_csv_rows_have_three_fields(self):
        """Verify that each row in the CSV has exactly 3 fields."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                assert len(row) == 3, (
                    f"Row {i} has {len(row)} fields instead of 3. Row content: {row}"
                )

    def test_csv_header_field_order(self):
        """Verify that the header fields are in the correct order: id, name, email."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)

        assert header == ["id", "name", "email"], (
            f"Expected header ['id', 'name', 'email'], but got: {header}"
        )

    def test_csv_contains_alice_chen(self):
        """Verify that 'Alice Chen' is present in the CSV (anti-shortcut check)."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            content = f.read()

        assert "Alice Chen" in content, (
            "Expected 'Alice Chen' to be present in the CSV file, but it was not found. "
            "The CSV must contain actual data from the JSON source."
        )

    def test_csv_data_matches_json_source(self):
        """Verify that the CSV data matches the JSON source data."""
        # Load JSON data
        with open(self.JSON_FILE, 'r') as f:
            json_data = json.load(f)

        json_customers = json_data["data"]

        # Load CSV data
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)

        assert len(csv_rows) == len(json_customers), (
            f"CSV has {len(csv_rows)} data rows but JSON has {len(json_customers)} customers."
        )

        # Create a lookup from JSON data
        json_lookup = {
            (str(c["id"]), c["name"], c["email"]) for c in json_customers
        }

        # Check each CSV row exists in JSON
        for i, row in enumerate(csv_rows):
            csv_tuple = (row["id"], row["name"], row["email"])
            assert csv_tuple in json_lookup, (
                f"CSV row {i+1} with data {csv_tuple} does not match any JSON record."
            )

    def test_csv_ids_are_numeric(self):
        """Verify that all id values in the CSV are numeric."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                try:
                    int(row["id"])
                except ValueError:
                    pytest.fail(
                        f"Row {i+1} has non-numeric id: '{row['id']}'"
                    )

    def test_csv_spot_check_first_few_records(self):
        """Spot check that the first few CSV records match JSON records."""
        with open(self.JSON_FILE, 'r') as f:
            json_data = json.load(f)

        json_customers = json_data["data"]

        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)

        # Check at least the first 5 records can be found
        for json_customer in json_customers[:5]:
            expected_id = str(json_customer["id"])
            expected_name = json_customer["name"]
            expected_email = json_customer["email"]

            found = False
            for csv_row in csv_rows:
                if (csv_row["id"] == expected_id and 
                    csv_row["name"] == expected_name and 
                    csv_row["email"] == expected_email):
                    found = True
                    break

            assert found, (
                f"JSON customer (id={expected_id}, name='{expected_name}', "
                f"email='{expected_email}') not found in CSV."
            )

    def test_json_file_unchanged(self):
        """Verify that the original JSON file still exists and is valid."""
        assert os.path.isfile(self.JSON_FILE), (
            f"Original JSON file {self.JSON_FILE} no longer exists. "
            "The source file should not be deleted."
        )

        try:
            with open(self.JSON_FILE, 'r') as f:
                data = json.load(f)

            assert "data" in data, "JSON file missing 'data' key."
            assert len(data["data"]) == 500, (
                f"JSON file should still have 500 customers, but has {len(data['data'])}."
            )
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON file is no longer valid JSON: {e}")

    def test_head_command_output(self):
        """Verify that head -1 outputs the expected header."""
        result = subprocess.run(
            ["head", "-1", self.CSV_FILE],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0, (
            f"head command failed with return code {result.returncode}"
        )

        header_line = result.stdout.strip()
        assert header_line == "id,name,email", (
            f"Expected 'head -1' to output 'id,name,email', but got: '{header_line}'"
        )

    def test_wc_command_output(self):
        """Verify that wc -l outputs 501."""
        result = subprocess.run(
            ["wc", "-l"],
            stdin=open(self.CSV_FILE, 'r'),
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0, (
            f"wc command failed with return code {result.returncode}"
        )

        line_count = int(result.stdout.strip())
        assert line_count == 501, (
            f"Expected 'wc -l' to output 501, but got: {line_count}"
        )

    def test_grep_alice_chen(self):
        """Verify that grep finds 'Alice Chen' in the CSV (anti-shortcut guard)."""
        result = subprocess.run(
            ["grep", "Alice Chen", self.CSV_FILE],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0, (
            "grep 'Alice Chen' did not find a match in the CSV file. "
            "The CSV must contain actual data from the JSON source."
        )

        assert "Alice Chen" in result.stdout, (
            "grep output does not contain 'Alice Chen'."
        )

    def test_csv_emails_look_valid(self):
        """Verify that email fields contain @ symbol (basic validation)."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                email = row["email"]
                assert "@" in email, (
                    f"Row {i+1} has invalid email (missing @): '{email}'"
                )

    def test_csv_no_extra_fields_from_json(self):
        """Verify that the CSV only contains id, name, email - no nested data."""
        with open(self.CSV_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                # Check that values don't look like JSON objects
                for field, value in row.items():
                    assert not value.startswith("{"), (
                        f"Row {i+1}, field '{field}' appears to contain JSON object: '{value[:50]}...'"
                    )
                    assert not value.startswith("["), (
                        f"Row {i+1}, field '{field}' appears to contain JSON array: '{value[:50]}...'"
                    )
