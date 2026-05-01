# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the JSON to CSV conversion task.
"""

import json
import os
import subprocess
import pytest


class TestInitialState:
    """Tests to verify the initial state before task execution."""

    def test_experiments_directory_exists(self):
        """Verify /home/user/experiments/ directory exists."""
        experiments_dir = "/home/user/experiments"
        assert os.path.isdir(experiments_dir), (
            f"Directory {experiments_dir} does not exist. "
            "The experiments directory must exist before the task can be performed."
        )

    def test_experiments_directory_writable(self):
        """Verify /home/user/experiments/ is writable."""
        experiments_dir = "/home/user/experiments"
        assert os.access(experiments_dir, os.W_OK), (
            f"Directory {experiments_dir} is not writable. "
            "The agent needs write access to create the output CSV file."
        )

    def test_source_json_file_exists(self):
        """Verify /home/user/experiments/run_047.json exists."""
        json_file = "/home/user/experiments/run_047.json"
        assert os.path.isfile(json_file), (
            f"Source file {json_file} does not exist. "
            "The JSON file with hyperparameters must exist before conversion."
        )

    def test_source_json_file_readable(self):
        """Verify /home/user/experiments/run_047.json is readable."""
        json_file = "/home/user/experiments/run_047.json"
        assert os.access(json_file, os.R_OK), (
            f"Source file {json_file} is not readable. "
            "The agent needs read access to the JSON file."
        )

    def test_source_json_valid_json(self):
        """Verify /home/user/experiments/run_047.json contains valid JSON."""
        json_file = "/home/user/experiments/run_047.json"
        try:
            with open(json_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"Source file {json_file} does not contain valid JSON: {e}"
            )

    def test_source_json_contains_expected_content(self):
        """Verify the JSON file contains the expected hyperparameters."""
        json_file = "/home/user/experiments/run_047.json"
        expected_data = {
            "run_id": "047",
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 50,
            "dropout": 0.2,
            "optimizer": "adam"
        }

        with open(json_file, 'r') as f:
            actual_data = json.load(f)

        assert actual_data == expected_data, (
            f"Source JSON content does not match expected. "
            f"Expected: {expected_data}, Got: {actual_data}"
        )

    def test_source_json_is_flat_object(self):
        """Verify the JSON is a flat object with no nesting."""
        json_file = "/home/user/experiments/run_047.json"

        with open(json_file, 'r') as f:
            data = json.load(f)

        assert isinstance(data, dict), (
            f"JSON content is not a dictionary/object. Got type: {type(data)}"
        )

        for key, value in data.items():
            assert not isinstance(value, (dict, list)), (
                f"JSON is not flat - key '{key}' contains nested structure: {type(value)}"
            )

    def test_output_csv_does_not_exist(self):
        """Verify /home/user/experiments/run_047.csv does not exist yet."""
        csv_file = "/home/user/experiments/run_047.csv"
        assert not os.path.exists(csv_file), (
            f"Output file {csv_file} already exists. "
            "The CSV file should not exist before the task is performed."
        )

    def test_python3_available(self):
        """Verify Python 3.x is available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python 3 is not available. "
            f"Error: {result.stderr}"
        )
        assert "Python 3" in result.stdout, (
            f"Expected Python 3.x but got: {result.stdout}"
        )

    def test_python_json_module_available(self):
        """Verify Python's json module is available."""
        result = subprocess.run(
            ["python3", "-c", "import json; print('json module OK')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python's json module is not available. "
            f"Error: {result.stderr}"
        )

    def test_python_csv_module_available(self):
        """Verify Python's csv module is available."""
        result = subprocess.run(
            ["python3", "-c", "import csv; print('csv module OK')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python's csv module is not available. "
            f"Error: {result.stderr}"
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
            "jq should be available as an alternative tool for JSON processing."
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
