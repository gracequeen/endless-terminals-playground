# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of extracting critical service names from incidents.json.
"""

import json
import os
import pytest


class TestFinalState:
    """Validate the final state after the student performs the task."""

    def test_output_file_exists(self):
        """Verify /home/user/alerts/critical_services.txt exists."""
        output_file = "/home/user/alerts/critical_services.txt"
        assert os.path.isfile(output_file), (
            f"File {output_file} does not exist. "
            "The output file must be created with the critical service names."
        )

    def test_output_file_is_readable(self):
        """Verify /home/user/alerts/critical_services.txt is readable."""
        output_file = "/home/user/alerts/critical_services.txt"
        assert os.access(output_file, os.R_OK), (
            f"File {output_file} is not readable."
        )

    def test_output_file_contains_correct_services(self):
        """Verify the output file contains exactly the expected critical services."""
        output_file = "/home/user/alerts/critical_services.txt"

        with open(output_file, 'r') as f:
            content = f.read()

        # Parse lines, stripping whitespace
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

        expected_services = ["api-gateway", "cdn-edge-03", "payment-gateway"]

        assert lines == expected_services, (
            f"Output file content does not match expected. "
            f"Expected: {expected_services}, Got: {lines}. "
            "The file should contain exactly the three critical services sorted alphabetically."
        )

    def test_output_file_has_correct_line_count(self):
        """Verify the output file has exactly 3 lines (no extra blank lines)."""
        output_file = "/home/user/alerts/critical_services.txt"

        with open(output_file, 'r') as f:
            content = f.read()

        # Check for trailing newline handling - content should have 3 service names
        lines = content.strip().split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        assert len(non_empty_lines) == 3, (
            f"Output file should have exactly 3 lines with service names. "
            f"Found {len(non_empty_lines)} non-empty lines."
        )

    def test_output_is_sorted_alphabetically(self):
        """Verify the services in the output file are sorted alphabetically."""
        output_file = "/home/user/alerts/critical_services.txt"

        with open(output_file, 'r') as f:
            content = f.read()

        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        sorted_lines = sorted(lines)

        assert lines == sorted_lines, (
            f"Services are not sorted alphabetically. "
            f"Got: {lines}, Expected sorted: {sorted_lines}"
        )

    def test_output_matches_critical_services_from_json(self):
        """Verify output file matches critical services derived from incidents.json."""
        incidents_file = "/home/user/alerts/incidents.json"
        output_file = "/home/user/alerts/critical_services.txt"

        # Read the source JSON and extract critical services
        with open(incidents_file, 'r') as f:
            data = json.load(f)

        expected_critical = sorted([
            inc["service"] for inc in data["incidents"]
            if inc.get("status") == "critical"
        ])

        # Read the output file
        with open(output_file, 'r') as f:
            content = f.read()

        actual_services = [line.strip() for line in content.strip().split('\n') if line.strip()]

        assert actual_services == expected_critical, (
            f"Output file does not match critical services from JSON. "
            f"Expected (from JSON): {expected_critical}, "
            f"Got (from output file): {actual_services}"
        )

    def test_incidents_json_unchanged(self):
        """Verify /home/user/alerts/incidents.json has not been modified."""
        incidents_file = "/home/user/alerts/incidents.json"

        with open(incidents_file, 'r') as f:
            data = json.load(f)

        # Verify the structure and content matches the original
        assert "incidents" in data, (
            f"File {incidents_file} no longer has 'incidents' key - file may have been corrupted."
        )

        expected_incidents = [
            {"service": "payment-gateway", "status": "critical", "since": "2024-01-15T08:30:00Z"},
            {"service": "auth-service", "status": "warning", "since": "2024-01-15T09:00:00Z"},
            {"service": "cdn-edge-03", "status": "critical", "since": "2024-01-15T07:45:00Z"},
            {"service": "metrics-collector", "status": "ok", "since": "2024-01-15T06:00:00Z"},
            {"service": "api-gateway", "status": "critical", "since": "2024-01-15T08:00:00Z"},
            {"service": "search-indexer", "status": "warning", "since": "2024-01-15T10:00:00Z"}
        ]

        assert len(data["incidents"]) == len(expected_incidents), (
            f"incidents.json has been modified - wrong number of incidents. "
            f"Expected {len(expected_incidents)}, got {len(data['incidents'])}."
        )

        # Check each incident exists (order may vary but content should match)
        for expected in expected_incidents:
            found = any(
                inc.get("service") == expected["service"] and
                inc.get("status") == expected["status"] and
                inc.get("since") == expected["since"]
                for inc in data["incidents"]
            )
            assert found, (
                f"incidents.json has been modified - missing or altered incident: {expected}"
            )

    def test_no_extra_content_in_output(self):
        """Verify output file contains only service names, no extra content."""
        output_file = "/home/user/alerts/critical_services.txt"

        with open(output_file, 'r') as f:
            content = f.read()

        lines = content.strip().split('\n')

        valid_services = {"api-gateway", "cdn-edge-03", "payment-gateway"}

        for line in lines:
            stripped = line.strip()
            if stripped:  # Skip empty lines for this check
                assert stripped in valid_services, (
                    f"Unexpected content in output file: '{stripped}'. "
                    f"Output should only contain: {valid_services}"
                )
