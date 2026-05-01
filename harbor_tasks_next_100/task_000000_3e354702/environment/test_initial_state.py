# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the backup verification task.
"""

import pytest
import os
import json
import subprocess


class TestInitialState:
    """Test suite to validate initial state before the task is performed."""

    def test_backups_directory_exists(self):
        """Verify /home/user/backups directory exists."""
        assert os.path.isdir("/home/user/backups"), \
            "Directory /home/user/backups does not exist"

    def test_customers_json_exists(self):
        """Verify /home/user/backups/customers.json file exists."""
        assert os.path.isfile("/home/user/backups/customers.json"), \
            "File /home/user/backups/customers.json does not exist"

    def test_customers_json_is_valid_json(self):
        """Verify customers.json contains valid JSON."""
        json_path = "/home/user/backups/customers.json"
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"File {json_path} is not valid JSON: {e}")
        except FileNotFoundError:
            pytest.fail(f"File {json_path} does not exist")

    def test_customers_json_is_array(self):
        """Verify customers.json contains a JSON array."""
        json_path = "/home/user/backups/customers.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list), \
            f"customers.json should contain a JSON array, got {type(data).__name__}"

    def test_customers_json_has_50_records(self):
        """Verify customers.json contains exactly 50 records."""
        json_path = "/home/user/backups/customers.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 50, \
            f"customers.json should have 50 records, got {len(data)}"

    def test_customers_json_records_have_id_field(self):
        """Verify each record in customers.json has an 'id' field."""
        json_path = "/home/user/backups/customers.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        for i, record in enumerate(data):
            assert isinstance(record, dict), \
                f"Record {i} is not an object, got {type(record).__name__}"
            assert 'id' in record, \
                f"Record {i} is missing 'id' field"

    def test_customers_json_ids_are_integers(self):
        """Verify all IDs in customers.json are integers."""
        json_path = "/home/user/backups/customers.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        for i, record in enumerate(data):
            assert isinstance(record.get('id'), int), \
                f"Record {i} has non-integer id: {record.get('id')}"

    def test_data_directory_exists(self):
        """Verify /home/user/data directory exists."""
        assert os.path.isdir("/home/user/data"), \
            "Directory /home/user/data does not exist"

    def test_customers_csv_exists(self):
        """Verify /home/user/data/customers.csv file exists."""
        assert os.path.isfile("/home/user/data/customers.csv"), \
            "File /home/user/data/customers.csv does not exist"

    def test_customers_csv_has_header(self):
        """Verify customers.csv has the expected header row."""
        csv_path = "/home/user/data/customers.csv"
        with open(csv_path, 'r') as f:
            header = f.readline().strip()
        expected_columns = ['id', 'name', 'email', 'created_at']
        actual_columns = [col.strip() for col in header.split(',')]
        assert actual_columns == expected_columns, \
            f"CSV header should be {expected_columns}, got {actual_columns}"

    def test_customers_csv_has_50_data_rows(self):
        """Verify customers.csv has exactly 50 data rows (excluding header)."""
        csv_path = "/home/user/data/customers.csv"
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        # Subtract 1 for header
        data_rows = len(lines) - 1
        assert data_rows == 50, \
            f"customers.csv should have 50 data rows, got {data_rows}"

    def test_customers_csv_id_is_first_column(self):
        """Verify 'id' is the first column in customers.csv."""
        csv_path = "/home/user/data/customers.csv"
        with open(csv_path, 'r') as f:
            header = f.readline().strip()
        first_column = header.split(',')[0].strip()
        assert first_column == 'id', \
            f"First column should be 'id', got '{first_column}'"

    def test_verify_directory_exists(self):
        """Verify /home/user/verify directory exists."""
        assert os.path.isdir("/home/user/verify"), \
            "Directory /home/user/verify does not exist"

    def test_verify_directory_is_empty(self):
        """Verify /home/user/verify directory is empty."""
        verify_path = "/home/user/verify"
        contents = os.listdir(verify_path)
        assert len(contents) == 0, \
            f"Directory /home/user/verify should be empty, contains: {contents}"

    def test_home_user_is_writable(self):
        """Verify /home/user is writable."""
        assert os.access("/home/user", os.W_OK), \
            "/home/user is not writable"

    def test_jq_is_available(self):
        """Verify jq command is available."""
        result = subprocess.run(['which', 'jq'], capture_output=True)
        assert result.returncode == 0, \
            "jq is not available in PATH"

    def test_python3_is_available(self):
        """Verify python3 command is available."""
        result = subprocess.run(['which', 'python3'], capture_output=True)
        assert result.returncode == 0, \
            "python3 is not available in PATH"

    def test_awk_is_available(self):
        """Verify awk command is available."""
        result = subprocess.run(['which', 'awk'], capture_output=True)
        assert result.returncode == 0, \
            "awk is not available in PATH"

    def test_sed_is_available(self):
        """Verify sed command is available."""
        result = subprocess.run(['which', 'sed'], capture_output=True)
        assert result.returncode == 0, \
            "sed is not available in PATH"

    def test_sort_is_available(self):
        """Verify sort command is available."""
        result = subprocess.run(['which', 'sort'], capture_output=True)
        assert result.returncode == 0, \
            "sort is not available in PATH"

    def test_cut_is_available(self):
        """Verify cut command is available."""
        result = subprocess.run(['which', 'cut'], capture_output=True)
        assert result.returncode == 0, \
            "cut is not available in PATH"

    def test_json_and_csv_have_same_ids(self):
        """Verify JSON and CSV files contain the same customer IDs (restore was successful)."""
        # Extract IDs from JSON
        json_path = "/home/user/backups/customers.json"
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        json_ids = set(record['id'] for record in json_data)

        # Extract IDs from CSV
        csv_path = "/home/user/data/customers.csv"
        csv_ids = set()
        with open(csv_path, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                if line.strip():
                    id_value = line.split(',')[0].strip()
                    csv_ids.add(int(id_value))

        assert json_ids == csv_ids, \
            f"JSON and CSV IDs do not match. JSON-only: {json_ids - csv_ids}, CSV-only: {csv_ids - json_ids}"
