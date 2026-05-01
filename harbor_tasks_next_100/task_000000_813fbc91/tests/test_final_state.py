# test_final_state.py
"""
Pytest suite to validate the final OS/filesystem state after the student
has completed the task of extracting offline hostnames from a JSON file.
"""

import json
import os
import subprocess
import pytest


class TestFinalState:
    """Tests to verify the final state after the task is performed."""

    def test_offline_hosts_txt_exists(self):
        """Verify /home/user/inventory/offline_hosts.txt exists."""
        output_file = "/home/user/inventory/offline_hosts.txt"
        assert os.path.isfile(output_file), (
            f"File {output_file} does not exist. "
            "The output file must be created with offline hostnames."
        )

    def test_offline_hosts_txt_is_readable(self):
        """Verify /home/user/inventory/offline_hosts.txt is readable."""
        output_file = "/home/user/inventory/offline_hosts.txt"
        assert os.access(output_file, os.R_OK), (
            f"File {output_file} is not readable."
        )

    def test_offline_hosts_txt_contains_no_json_quotes(self):
        """Verify output file contains raw hostnames without JSON quotes."""
        output_file = "/home/user/inventory/offline_hosts.txt"
        result = subprocess.run(
            ["grep", '"', output_file],
            capture_output=True,
            text=True
        )
        # grep returns 0 if matches found, 1 if no matches
        assert result.returncode != 0, (
            f"File {output_file} contains JSON quotes. "
            "Hostnames should be raw strings without quotes. "
            f"Found lines with quotes: {result.stdout}"
        )

    def test_offline_hosts_txt_has_correct_hostnames(self):
        """Verify output file contains exactly the hostnames of offline devices."""
        switches_file = "/home/user/inventory/switches.json"
        output_file = "/home/user/inventory/offline_hosts.txt"

        # Get expected offline hostnames from the source JSON
        with open(switches_file, 'r') as f:
            data = json.load(f)

        expected_hostnames = set(
            item["hostname"] for item in data if item.get("status") == "offline"
        )

        # Get actual hostnames from the output file
        with open(output_file, 'r') as f:
            content = f.read()

        # Parse lines, stripping whitespace and filtering empty lines
        actual_hostnames = set(
            line.strip() for line in content.splitlines() if line.strip()
        )

        assert actual_hostnames == expected_hostnames, (
            f"Hostnames in {output_file} do not match expected offline devices.\n"
            f"Expected: {sorted(expected_hostnames)}\n"
            f"Actual: {sorted(actual_hostnames)}\n"
            f"Missing: {sorted(expected_hostnames - actual_hostnames)}\n"
            f"Extra: {sorted(actual_hostnames - expected_hostnames)}"
        )

    def test_offline_hosts_txt_line_count_matches(self):
        """Verify the number of lines matches the number of offline devices."""
        switches_file = "/home/user/inventory/switches.json"
        output_file = "/home/user/inventory/offline_hosts.txt"

        # Get expected count from the source JSON
        with open(switches_file, 'r') as f:
            data = json.load(f)

        expected_count = sum(1 for item in data if item.get("status") == "offline")

        # Count non-empty lines in output file
        with open(output_file, 'r') as f:
            actual_lines = [line.strip() for line in f if line.strip()]

        assert len(actual_lines) == expected_count, (
            f"Line count mismatch in {output_file}. "
            f"Expected {expected_count} offline hostnames, "
            f"but found {len(actual_lines)} non-empty lines."
        )

    def test_offline_hosts_txt_one_hostname_per_line(self):
        """Verify each line contains exactly one hostname (no commas, brackets, etc.)."""
        output_file = "/home/user/inventory/offline_hosts.txt"

        with open(output_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        for i, line in enumerate(lines):
            # Check for common JSON artifacts
            assert '[' not in line, (
                f"Line {i+1} in {output_file} contains '[': '{line}'. "
                "Each line should contain only a hostname."
            )
            assert ']' not in line, (
                f"Line {i+1} in {output_file} contains ']': '{line}'. "
                "Each line should contain only a hostname."
            )
            assert ',' not in line, (
                f"Line {i+1} in {output_file} contains ',': '{line}'. "
                "Each line should contain only a hostname."
            )
            assert '{' not in line, (
                f"Line {i+1} in {output_file} contains '{{': '{line}'. "
                "Each line should contain only a hostname."
            )
            assert '}' not in line, (
                f"Line {i+1} in {output_file} contains '}}': '{line}'. "
                "Each line should contain only a hostname."
            )

    def test_switches_json_unchanged(self):
        """Verify /home/user/inventory/switches.json is still valid and unchanged."""
        switches_file = "/home/user/inventory/switches.json"

        # Verify file still exists
        assert os.path.isfile(switches_file), (
            f"File {switches_file} no longer exists. "
            "The source file should not be deleted."
        )

        # Verify it's still valid JSON with the expected structure
        try:
            with open(switches_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {switches_file} is no longer valid JSON: {e}"
            )

        assert isinstance(data, list), (
            f"File {switches_file} no longer contains a JSON array."
        )

        # Verify structure is intact
        for i, item in enumerate(data):
            assert isinstance(item, dict), (
                f"Item at index {i} in {switches_file} is not an object."
            )
            assert "hostname" in item, (
                f"Item at index {i} in {switches_file} is missing 'hostname' field."
            )
            assert "status" in item, (
                f"Item at index {i} in {switches_file} is missing 'status' field."
            )

    def test_no_extra_whitespace_in_hostnames(self):
        """Verify hostnames don't have leading/trailing whitespace beyond line breaks."""
        output_file = "/home/user/inventory/offline_hosts.txt"

        with open(output_file, 'r') as f:
            for i, line in enumerate(f):
                # Remove only the newline, not other whitespace
                line_no_newline = line.rstrip('\n\r')
                if line_no_newline:  # Skip empty lines
                    stripped = line_no_newline.strip()
                    # Allow the line to have trailing newline, but not other whitespace
                    assert line_no_newline == stripped, (
                        f"Line {i+1} in {output_file} has extra whitespace: "
                        f"'{repr(line_no_newline)}' vs '{repr(stripped)}'"
                    )
