# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of extracting transaction IDs and amounts from a JSON file
to a CSV file.
"""

import json
import os
import subprocess
import pytest


class TestInitialState:
    """Tests for validating the initial state before the task is performed."""

    def test_audit_directory_exists(self):
        """Verify /home/user/audit directory exists."""
        audit_dir = "/home/user/audit"
        assert os.path.isdir(audit_dir), (
            f"Directory {audit_dir} does not exist. "
            "The audit directory must exist before performing the task."
        )

    def test_audit_directory_is_writable(self):
        """Verify /home/user/audit directory is writable."""
        audit_dir = "/home/user/audit"
        assert os.access(audit_dir, os.W_OK), (
            f"Directory {audit_dir} is not writable. "
            "The audit directory must be writable to create the output CSV."
        )

    def test_march_payments_json_exists(self):
        """Verify /home/user/audit/march_payments.json exists."""
        json_file = "/home/user/audit/march_payments.json"
        assert os.path.isfile(json_file), (
            f"File {json_file} does not exist. "
            "The source JSON file must exist before performing the task."
        )

    def test_march_payments_json_is_readable(self):
        """Verify /home/user/audit/march_payments.json is readable."""
        json_file = "/home/user/audit/march_payments.json"
        assert os.access(json_file, os.R_OK), (
            f"File {json_file} is not readable. "
            "The source JSON file must be readable to extract data."
        )

    def test_march_payments_json_is_valid_json(self):
        """Verify /home/user/audit/march_payments.json contains valid JSON."""
        json_file = "/home/user/audit/march_payments.json"
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {json_file} contains invalid JSON: {e}. "
                "The source file must contain valid JSON."
            )

    def test_march_payments_json_is_array(self):
        """Verify /home/user/audit/march_payments.json contains a JSON array."""
        json_file = "/home/user/audit/march_payments.json"
        with open(json_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list), (
            f"File {json_file} does not contain a JSON array. "
            f"Expected a list, got {type(data).__name__}."
        )

    def test_march_payments_json_has_47_records(self):
        """Verify /home/user/audit/march_payments.json contains exactly 47 payment objects."""
        json_file = "/home/user/audit/march_payments.json"
        with open(json_file, 'r') as f:
            data = json.load(f)
        assert len(data) == 47, (
            f"File {json_file} should contain exactly 47 payment objects, "
            f"but found {len(data)}."
        )

    def test_march_payments_json_objects_have_required_keys(self):
        """Verify each payment object has the required keys: txn_id, amount, merchant, timestamp, status."""
        json_file = "/home/user/audit/march_payments.json"
        required_keys = {"txn_id", "amount", "merchant", "timestamp", "status"}

        with open(json_file, 'r') as f:
            data = json.load(f)

        for i, obj in enumerate(data):
            assert isinstance(obj, dict), (
                f"Item at index {i} in {json_file} is not an object/dict, "
                f"got {type(obj).__name__}."
            )
            missing_keys = required_keys - set(obj.keys())
            assert not missing_keys, (
                f"Payment object at index {i} is missing required keys: {missing_keys}. "
                f"Each object must have: {required_keys}."
            )

    def test_march_payments_json_txn_id_is_string(self):
        """Verify txn_id values are strings."""
        json_file = "/home/user/audit/march_payments.json"
        with open(json_file, 'r') as f:
            data = json.load(f)

        for i, obj in enumerate(data):
            assert isinstance(obj.get("txn_id"), str), (
                f"Payment object at index {i} has non-string txn_id: {obj.get('txn_id')}. "
                "txn_id must be a string."
            )

    def test_march_payments_json_amount_is_numeric(self):
        """Verify amount values are numeric (int or float)."""
        json_file = "/home/user/audit/march_payments.json"
        with open(json_file, 'r') as f:
            data = json.load(f)

        for i, obj in enumerate(data):
            amount = obj.get("amount")
            assert isinstance(amount, (int, float)), (
                f"Payment object at index {i} has non-numeric amount: {amount} "
                f"(type: {type(amount).__name__}). amount must be numeric."
            )

    def test_march_extract_csv_does_not_exist(self):
        """Verify /home/user/audit/march_extract.csv does NOT exist yet."""
        csv_file = "/home/user/audit/march_extract.csv"
        assert not os.path.exists(csv_file), (
            f"File {csv_file} already exists. "
            "The output CSV file should not exist before performing the task."
        )

    def test_python3_available(self):
        """Verify Python 3.11+ is available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python 3 is not available. "
            "Python 3.11+ must be installed to perform this task."
        )

        version_output = result.stdout.strip()
        # Parse version like "Python 3.11.2"
        version_parts = version_output.replace("Python ", "").split(".")
        major = int(version_parts[0])
        minor = int(version_parts[1])

        assert major >= 3 and minor >= 11, (
            f"Python version is {version_output}, but Python 3.11+ is required."
        )

    def test_jq_installed(self):
        """Verify jq is installed and available."""
        result = subprocess.run(
            ["which", "jq"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "jq is not installed or not in PATH. "
            "jq must be available for this task."
        )

    def test_jq_functional(self):
        """Verify jq is functional."""
        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "jq is installed but not functional. "
            f"Error: {result.stderr}"
        )
