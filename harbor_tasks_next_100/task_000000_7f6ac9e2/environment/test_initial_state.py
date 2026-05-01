# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of extracting critical service names from incidents.json.
"""

import json
import os
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state before the student performs the task."""

    def test_alerts_directory_exists(self):
        """Verify /home/user/alerts/ directory exists."""
        alerts_dir = "/home/user/alerts"
        assert os.path.isdir(alerts_dir), (
            f"Directory {alerts_dir} does not exist. "
            "The alerts directory must exist before performing the task."
        )

    def test_alerts_directory_is_writable(self):
        """Verify /home/user/alerts/ directory is writable."""
        alerts_dir = "/home/user/alerts"
        assert os.access(alerts_dir, os.W_OK), (
            f"Directory {alerts_dir} is not writable. "
            "The alerts directory must be writable to create the output file."
        )

    def test_incidents_json_exists(self):
        """Verify /home/user/alerts/incidents.json exists."""
        incidents_file = "/home/user/alerts/incidents.json"
        assert os.path.isfile(incidents_file), (
            f"File {incidents_file} does not exist. "
            "The incidents.json file must exist as the input for the task."
        )

    def test_incidents_json_is_readable(self):
        """Verify /home/user/alerts/incidents.json is readable."""
        incidents_file = "/home/user/alerts/incidents.json"
        assert os.access(incidents_file, os.R_OK), (
            f"File {incidents_file} is not readable. "
            "The incidents.json file must be readable to extract data from it."
        )

    def test_incidents_json_contains_valid_json(self):
        """Verify /home/user/alerts/incidents.json contains valid JSON."""
        incidents_file = "/home/user/alerts/incidents.json"
        try:
            with open(incidents_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {incidents_file} does not contain valid JSON: {e}"
            )
        except Exception as e:
            pytest.fail(
                f"Failed to read {incidents_file}: {e}"
            )

    def test_incidents_json_has_incidents_array(self):
        """Verify incidents.json has an 'incidents' array at the top level."""
        incidents_file = "/home/user/alerts/incidents.json"
        with open(incidents_file, 'r') as f:
            data = json.load(f)

        assert "incidents" in data, (
            f"File {incidents_file} does not have an 'incidents' key at the top level. "
            "The JSON structure must contain an 'incidents' array."
        )
        assert isinstance(data["incidents"], list), (
            f"The 'incidents' key in {incidents_file} is not an array. "
            "The 'incidents' value must be a list of incident objects."
        )

    def test_incidents_json_has_expected_structure(self):
        """Verify each incident has 'service' and 'status' fields."""
        incidents_file = "/home/user/alerts/incidents.json"
        with open(incidents_file, 'r') as f:
            data = json.load(f)

        for i, incident in enumerate(data["incidents"]):
            assert "service" in incident, (
                f"Incident at index {i} in {incidents_file} is missing 'service' field."
            )
            assert "status" in incident, (
                f"Incident at index {i} in {incidents_file} is missing 'status' field."
            )

    def test_incidents_json_has_critical_services(self):
        """Verify there are incidents with 'critical' status to extract."""
        incidents_file = "/home/user/alerts/incidents.json"
        with open(incidents_file, 'r') as f:
            data = json.load(f)

        critical_services = [
            inc["service"] for inc in data["incidents"] 
            if inc.get("status") == "critical"
        ]

        assert len(critical_services) > 0, (
            f"No incidents with 'critical' status found in {incidents_file}. "
            "There must be critical incidents to extract."
        )

    def test_critical_services_txt_does_not_exist(self):
        """Verify /home/user/alerts/critical_services.txt does not exist initially."""
        output_file = "/home/user/alerts/critical_services.txt"
        assert not os.path.exists(output_file), (
            f"File {output_file} already exists. "
            "The output file should not exist before the student performs the task."
        )

    def test_jq_is_installed(self):
        """Verify jq is installed and available in PATH."""
        result = subprocess.run(
            ["which", "jq"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "jq is not installed or not in PATH. "
            "jq must be installed to perform JSON processing."
        )

    def test_jq_is_functional(self):
        """Verify jq can execute basic commands."""
        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq is not functional. Exit code: {result.returncode}, "
            f"stderr: {result.stderr}"
        )

    def test_jq_can_parse_incidents_file(self):
        """Verify jq can successfully parse the incidents.json file."""
        incidents_file = "/home/user/alerts/incidents.json"
        result = subprocess.run(
            ["jq", ".", incidents_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq failed to parse {incidents_file}. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
