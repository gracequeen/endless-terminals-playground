# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of extracting degraded service names from services.json.
"""

import json
import os
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state required for the jq task."""

    def test_infra_directory_exists(self):
        """Verify /home/user/infra directory exists."""
        infra_path = "/home/user/infra"
        assert os.path.isdir(infra_path), (
            f"Directory {infra_path} does not exist. "
            "The infra directory must be present for this task."
        )

    def test_infra_directory_is_readable(self):
        """Verify /home/user/infra directory is readable."""
        infra_path = "/home/user/infra"
        assert os.access(infra_path, os.R_OK), (
            f"Directory {infra_path} is not readable. "
            "The agent user must have read access to the infra directory."
        )

    def test_services_json_exists(self):
        """Verify /home/user/infra/services.json file exists."""
        services_file = "/home/user/infra/services.json"
        assert os.path.isfile(services_file), (
            f"File {services_file} does not exist. "
            "The services.json file must be present for this task."
        )

    def test_services_json_is_readable(self):
        """Verify /home/user/infra/services.json is readable."""
        services_file = "/home/user/infra/services.json"
        assert os.access(services_file, os.R_OK), (
            f"File {services_file} is not readable. "
            "The agent user must have read access to services.json."
        )

    def test_services_json_contains_valid_json(self):
        """Verify services.json contains valid JSON."""
        services_file = "/home/user/infra/services.json"
        try:
            with open(services_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {services_file} does not contain valid JSON: {e}"
            )
        except Exception as e:
            pytest.fail(
                f"Failed to read {services_file}: {e}"
            )

    def test_services_json_has_services_array(self):
        """Verify services.json has a 'services' key with an array."""
        services_file = "/home/user/infra/services.json"
        with open(services_file, 'r') as f:
            data = json.load(f)

        assert "services" in data, (
            f"File {services_file} does not have a 'services' key at the top level. "
            "Expected JSON structure with 'services' array."
        )
        assert isinstance(data["services"], list), (
            f"The 'services' key in {services_file} is not an array. "
            "Expected 'services' to be a JSON array."
        )

    def test_services_json_has_expected_structure(self):
        """Verify each service in services.json has required fields."""
        services_file = "/home/user/infra/services.json"
        with open(services_file, 'r') as f:
            data = json.load(f)

        services = data.get("services", [])
        assert len(services) > 0, (
            f"The 'services' array in {services_file} is empty. "
            "Expected at least one service entry."
        )

        for i, service in enumerate(services):
            assert "name" in service, (
                f"Service at index {i} in {services_file} is missing 'name' field."
            )
            assert "status" in service, (
                f"Service at index {i} in {services_file} is missing 'status' field."
            )

    def test_services_json_has_degraded_services(self):
        """Verify there are services with status 'degraded' to filter."""
        services_file = "/home/user/infra/services.json"
        with open(services_file, 'r') as f:
            data = json.load(f)

        services = data.get("services", [])
        degraded_services = [s for s in services if s.get("status") == "degraded"]

        assert len(degraded_services) > 0, (
            f"No services with status 'degraded' found in {services_file}. "
            "The task requires filtering degraded services."
        )

    def test_services_json_matches_expected_content(self):
        """Verify services.json contains the expected services."""
        services_file = "/home/user/infra/services.json"
        with open(services_file, 'r') as f:
            data = json.load(f)

        expected_services = [
            {"name": "auth-api", "status": "healthy", "port": 8080},
            {"name": "payment-gateway", "status": "degraded", "port": 8081},
            {"name": "user-db", "status": "healthy", "port": 5432},
            {"name": "cache-redis", "status": "degraded", "port": 6379},
            {"name": "notification-svc", "status": "healthy", "port": 8082},
            {"name": "inventory-api", "status": "degraded", "port": 8083}
        ]

        actual_services = data.get("services", [])
        assert len(actual_services) == len(expected_services), (
            f"Expected {len(expected_services)} services in {services_file}, "
            f"but found {len(actual_services)}."
        )

        for expected in expected_services:
            matching = [s for s in actual_services if s.get("name") == expected["name"]]
            assert len(matching) == 1, (
                f"Service '{expected['name']}' not found in {services_file}."
            )
            actual = matching[0]
            assert actual.get("status") == expected["status"], (
                f"Service '{expected['name']}' has status '{actual.get('status')}', "
                f"expected '{expected['status']}'."
            )

    def test_jq_is_installed(self):
        """Verify jq is installed and available in PATH."""
        result = subprocess.run(
            ["which", "jq"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "jq is not installed or not available in PATH. "
            "The task requires jq to be installed."
        )

    def test_jq_is_functional(self):
        """Verify jq can execute basic commands."""
        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq is not functional. Running 'jq --version' failed: {result.stderr}"
        )

    def test_jq_can_parse_services_json(self):
        """Verify jq can successfully parse the services.json file."""
        services_file = "/home/user/infra/services.json"
        result = subprocess.run(
            ["jq", ".", services_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq failed to parse {services_file}: {result.stderr}"
        )
