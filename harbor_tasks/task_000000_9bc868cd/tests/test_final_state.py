# test_final_state.py
"""
Tests to validate the final state after the student has completed the task
of extracting degraded service names from services.json using jq.
"""

import json
import os
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the jq task is completed."""

    def test_services_json_unchanged(self):
        """Verify /home/user/infra/services.json remains unchanged."""
        services_file = "/home/user/infra/services.json"

        # Check file still exists
        assert os.path.isfile(services_file), (
            f"File {services_file} no longer exists. "
            "The services.json file should not be deleted or moved."
        )

        # Load and verify content matches expected
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

        assert "services" in data, (
            f"File {services_file} no longer has 'services' key. "
            "The file should remain unchanged."
        )

        actual_services = data.get("services", [])
        assert len(actual_services) == len(expected_services), (
            f"File {services_file} has been modified. "
            f"Expected {len(expected_services)} services, found {len(actual_services)}."
        )

        for i, expected in enumerate(expected_services):
            actual = actual_services[i]
            assert actual.get("name") == expected["name"], (
                f"Service at index {i} has name '{actual.get('name')}', "
                f"expected '{expected['name']}'. File should remain unchanged."
            )
            assert actual.get("status") == expected["status"], (
                f"Service '{expected['name']}' has status '{actual.get('status')}', "
                f"expected '{expected['status']}'. File should remain unchanged."
            )
            assert actual.get("port") == expected["port"], (
                f"Service '{expected['name']}' has port '{actual.get('port')}', "
                f"expected '{expected['port']}'. File should remain unchanged."
            )

    def test_jq_command_produces_correct_output(self):
        """
        Verify that the correct jq command produces the expected output.
        This tests that the task CAN be completed correctly with jq.
        """
        services_file = "/home/user/infra/services.json"

        # Run the jq command that should produce the correct output
        result = subprocess.run(
            ["jq", "-r", '.services[] | select(.status == "degraded") | .name', services_file],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"jq command failed with error: {result.stderr}"
        )

        # Parse the output
        output_lines = result.stdout.strip().split('\n')
        expected_names = ["payment-gateway", "cache-redis", "inventory-api"]

        assert output_lines == expected_names, (
            f"jq command output does not match expected. "
            f"Expected: {expected_names}, Got: {output_lines}"
        )

    def test_degraded_services_can_be_extracted_dynamically(self):
        """
        Verify that filtering by status='degraded' works correctly.
        This is an anti-shortcut guard - the solution must actually filter,
        not hardcode the names.
        """
        services_file = "/home/user/infra/services.json"

        # Load the JSON and get degraded services programmatically
        with open(services_file, 'r') as f:
            data = json.load(f)

        degraded_names = [
            s["name"] for s in data["services"] 
            if s.get("status") == "degraded"
        ]

        # Verify we have exactly 3 degraded services
        assert len(degraded_names) == 3, (
            f"Expected 3 degraded services, found {len(degraded_names)}. "
            "The services.json file may have been modified."
        )

        # Verify the names match expected
        expected_names = ["payment-gateway", "cache-redis", "inventory-api"]
        assert degraded_names == expected_names, (
            f"Degraded service names don't match expected. "
            f"Expected: {expected_names}, Got: {degraded_names}"
        )

    def test_output_format_is_correct(self):
        """
        Verify the output format: one service name per line, no quotes,
        no extra whitespace, in order they appear in the file.
        """
        services_file = "/home/user/infra/services.json"

        # Run jq to get the output
        result = subprocess.run(
            ["jq", "-r", '.services[] | select(.status == "degraded") | .name', services_file],
            capture_output=True,
            text=True
        )

        output = result.stdout

        # Check no JSON quotes in output (raw output)
        assert '"' not in output, (
            "Output contains quotes. Use jq -r for raw output without quotes."
        )

        # Check the lines
        lines = output.strip().split('\n')

        # Verify exactly 3 lines
        assert len(lines) == 3, (
            f"Expected exactly 3 lines of output, got {len(lines)}. "
            f"Output was: {repr(output)}"
        )

        # Verify no leading/trailing whitespace on each line
        for i, line in enumerate(lines):
            assert line == line.strip(), (
                f"Line {i+1} has extra whitespace: {repr(line)}"
            )

        # Verify correct order and values
        assert lines[0] == "payment-gateway", (
            f"First degraded service should be 'payment-gateway', got '{lines[0]}'"
        )
        assert lines[1] == "cache-redis", (
            f"Second degraded service should be 'cache-redis', got '{lines[1]}'"
        )
        assert lines[2] == "inventory-api", (
            f"Third degraded service should be 'inventory-api', got '{lines[2]}'"
        )

    def test_healthy_services_not_included(self):
        """
        Verify that healthy services are NOT included in the output.
        """
        services_file = "/home/user/infra/services.json"

        result = subprocess.run(
            ["jq", "-r", '.services[] | select(.status == "degraded") | .name', services_file],
            capture_output=True,
            text=True
        )

        output = result.stdout

        # These healthy services should NOT appear
        healthy_services = ["auth-api", "user-db", "notification-svc"]

        for service in healthy_services:
            assert service not in output, (
                f"Healthy service '{service}' should not be in the output. "
                "Only degraded services should be listed."
            )

    def test_jq_still_functional(self):
        """Verify jq is still installed and functional after task completion."""
        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq is no longer functional: {result.stderr}"
        )
