# test_initial_state.py
"""
Tests to validate the initial state before the student performs the JSON to CSV conversion task.
"""

import json
import os
import subprocess
import pytest


class TestInitialState:
    """Test suite to validate the initial state of the system."""

    EXPORTS_DIR = "/home/user/exports"
    JSON_FILE = "/home/user/exports/customers.json"
    CSV_FILE = "/home/user/exports/customers.csv"

    def test_exports_directory_exists(self):
        """Verify that /home/user/exports/ directory exists."""
        assert os.path.isdir(self.EXPORTS_DIR), (
            f"Directory {self.EXPORTS_DIR} does not exist. "
            "The exports directory must exist before the task can be performed."
        )

    def test_exports_directory_is_writable(self):
        """Verify that /home/user/exports/ directory is writable."""
        assert os.access(self.EXPORTS_DIR, os.W_OK), (
            f"Directory {self.EXPORTS_DIR} is not writable. "
            "The exports directory must be writable to create the output CSV file."
        )

    def test_json_file_exists(self):
        """Verify that customers.json exists."""
        assert os.path.isfile(self.JSON_FILE), (
            f"File {self.JSON_FILE} does not exist. "
            "The source JSON file must exist before conversion."
        )

    def test_json_file_is_readable(self):
        """Verify that customers.json is readable."""
        assert os.access(self.JSON_FILE, os.R_OK), (
            f"File {self.JSON_FILE} is not readable. "
            "The source JSON file must be readable for conversion."
        )

    def test_json_file_contains_valid_json(self):
        """Verify that customers.json contains valid JSON."""
        try:
            with open(self.JSON_FILE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {self.JSON_FILE} does not contain valid JSON: {e}"
            )

    def test_json_has_data_key(self):
        """Verify that the JSON has a 'data' key at the top level."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        assert "data" in data, (
            f"JSON file {self.JSON_FILE} does not have a 'data' key at the top level. "
            "Expected structure: {\"data\": [...], ...}"
        )

    def test_data_is_array(self):
        """Verify that the 'data' value is an array."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        assert isinstance(data["data"], list), (
            f"The 'data' key in {self.JSON_FILE} is not an array. "
            f"Got type: {type(data['data']).__name__}"
        )

    def test_data_has_500_customers(self):
        """Verify that there are exactly 500 customer objects in the data array."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        customer_count = len(data["data"])
        assert customer_count == 500, (
            f"Expected exactly 500 customers in the 'data' array, "
            f"but found {customer_count}."
        )

    def test_customer_objects_have_required_fields(self):
        """Verify that each customer object has id, name, and email fields."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        required_fields = {"id", "name", "email"}

        for i, customer in enumerate(data["data"]):
            missing_fields = required_fields - set(customer.keys())
            assert not missing_fields, (
                f"Customer at index {i} is missing required fields: {missing_fields}. "
                f"Each customer must have 'id', 'name', and 'email' fields."
            )

    def test_customer_id_is_integer(self):
        """Verify that customer id fields are integers."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        for i, customer in enumerate(data["data"]):
            assert isinstance(customer["id"], int), (
                f"Customer at index {i} has non-integer 'id': {customer['id']} "
                f"(type: {type(customer['id']).__name__})"
            )

    def test_customer_name_is_string(self):
        """Verify that customer name fields are strings."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        for i, customer in enumerate(data["data"]):
            assert isinstance(customer["name"], str), (
                f"Customer at index {i} has non-string 'name': {customer['name']} "
                f"(type: {type(customer['name']).__name__})"
            )

    def test_customer_email_is_string(self):
        """Verify that customer email fields are strings."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        for i, customer in enumerate(data["data"]):
            assert isinstance(customer["email"], str), (
                f"Customer at index {i} has non-string 'email': {customer['email']} "
                f"(type: {type(customer['email']).__name__})"
            )

    def test_alice_chen_exists_in_data(self):
        """Verify that 'Alice Chen' is present in the customer data (for anti-shortcut verification)."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        names = [customer.get("name", "") for customer in data["data"]]
        assert "Alice Chen" in names, (
            "Expected 'Alice Chen' to be present in the customer data, "
            "but this name was not found. This is required for verification."
        )

    def test_csv_file_does_not_exist(self):
        """Verify that customers.csv does not exist initially."""
        assert not os.path.exists(self.CSV_FILE), (
            f"File {self.CSV_FILE} already exists. "
            "The output CSV file should not exist before the task is performed."
        )

    def test_jq_is_installed(self):
        """Verify that jq is installed and accessible."""
        try:
            result = subprocess.run(
                ["jq", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, (
                f"jq command failed with return code {result.returncode}. "
                f"stderr: {result.stderr}"
            )
        except FileNotFoundError:
            pytest.fail("jq is not installed or not in PATH. jq must be available.")
        except subprocess.TimeoutExpired:
            pytest.fail("jq --version command timed out.")

    def test_jq_version_is_1_6_or_higher(self):
        """Verify that jq version is 1.6 or higher."""
        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        version_output = result.stdout.strip() or result.stderr.strip()
        # jq version output is typically like "jq-1.6" or "jq-1.7"

        import re
        match = re.search(r'jq-(\d+)\.(\d+)', version_output)
        assert match, (
            f"Could not parse jq version from output: {version_output}"
        )

        major = int(match.group(1))
        minor = int(match.group(2))

        assert (major, minor) >= (1, 6), (
            f"jq version must be 1.6 or higher, but found {major}.{minor}"
        )

    def test_python3_is_available(self):
        """Verify that python3 is available."""
        try:
            result = subprocess.run(
                ["python3", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, (
                f"python3 command failed with return code {result.returncode}. "
                f"stderr: {result.stderr}"
            )
        except FileNotFoundError:
            pytest.fail("python3 is not installed or not in PATH.")
        except subprocess.TimeoutExpired:
            pytest.fail("python3 --version command timed out.")

    def test_python3_json_module_available(self):
        """Verify that Python3 json module is available."""
        result = subprocess.run(
            ["python3", "-c", "import json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, (
            f"Python3 json module is not available. "
            f"stderr: {result.stderr}"
        )

    def test_python3_csv_module_available(self):
        """Verify that Python3 csv module is available."""
        result = subprocess.run(
            ["python3", "-c", "import csv"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, (
            f"Python3 csv module is not available. "
            f"stderr: {result.stderr}"
        )

    def test_json_has_nested_structure(self):
        """Verify that customer objects have nested fields (address, metadata) as expected."""
        with open(self.JSON_FILE, 'r') as f:
            data = json.load(f)

        # Check at least the first customer has nested structure
        first_customer = data["data"][0]

        # Check for presence of nested fields (at least one of address or metadata)
        has_nested = (
            ("address" in first_customer and isinstance(first_customer["address"], dict)) or
            ("metadata" in first_customer and isinstance(first_customer["metadata"], dict))
        )

        assert has_nested, (
            "Customer objects should have nested fields like 'address' or 'metadata'. "
            f"First customer keys: {list(first_customer.keys())}"
        )
