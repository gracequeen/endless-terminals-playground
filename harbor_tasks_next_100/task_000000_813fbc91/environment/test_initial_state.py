# test_initial_state.py
"""
Pytest suite to validate the initial OS/filesystem state before the student
performs the task of extracting offline hostnames from a JSON file.
"""

import json
import os
import subprocess
import pytest


class TestInitialState:
    """Tests to verify the initial state before the task is performed."""

    def test_inventory_directory_exists(self):
        """Verify /home/user/inventory/ directory exists."""
        inventory_dir = "/home/user/inventory"
        assert os.path.isdir(inventory_dir), (
            f"Directory {inventory_dir} does not exist. "
            "The inventory directory must be present."
        )

    def test_inventory_directory_is_writable(self):
        """Verify /home/user/inventory/ directory is writable."""
        inventory_dir = "/home/user/inventory"
        assert os.access(inventory_dir, os.W_OK), (
            f"Directory {inventory_dir} is not writable. "
            "The inventory directory must be writable to create output files."
        )

    def test_switches_json_exists(self):
        """Verify /home/user/inventory/switches.json exists."""
        switches_file = "/home/user/inventory/switches.json"
        assert os.path.isfile(switches_file), (
            f"File {switches_file} does not exist. "
            "The switches.json file must be present as input."
        )

    def test_switches_json_is_readable(self):
        """Verify /home/user/inventory/switches.json is readable."""
        switches_file = "/home/user/inventory/switches.json"
        assert os.access(switches_file, os.R_OK), (
            f"File {switches_file} is not readable. "
            "The switches.json file must be readable."
        )

    def test_switches_json_contains_valid_json(self):
        """Verify /home/user/inventory/switches.json contains valid JSON."""
        switches_file = "/home/user/inventory/switches.json"
        try:
            with open(switches_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {switches_file} does not contain valid JSON: {e}"
            )
        except Exception as e:
            pytest.fail(
                f"Error reading {switches_file}: {e}"
            )

    def test_switches_json_is_array(self):
        """Verify switches.json contains a JSON array."""
        switches_file = "/home/user/inventory/switches.json"
        with open(switches_file, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), (
            f"File {switches_file} must contain a JSON array at the top level, "
            f"but found {type(data).__name__}."
        )

    def test_switches_json_has_objects_with_required_fields(self):
        """Verify each object in switches.json has 'hostname' and 'status' fields."""
        switches_file = "/home/user/inventory/switches.json"
        with open(switches_file, 'r') as f:
            data = json.load(f)

        assert len(data) > 0, (
            f"File {switches_file} contains an empty array. "
            "There must be at least one device entry."
        )

        for i, item in enumerate(data):
            assert isinstance(item, dict), (
                f"Item at index {i} in {switches_file} is not an object, "
                f"found {type(item).__name__}."
            )
            assert "hostname" in item, (
                f"Item at index {i} in {switches_file} is missing 'hostname' field. "
                f"Item: {item}"
            )
            assert "status" in item, (
                f"Item at index {i} in {switches_file} is missing 'status' field. "
                f"Item: {item}"
            )
            assert isinstance(item["hostname"], str), (
                f"Item at index {i} in {switches_file} has non-string 'hostname'. "
                f"Found: {type(item['hostname']).__name__}"
            )
            assert isinstance(item["status"], str), (
                f"Item at index {i} in {switches_file} has non-string 'status'. "
                f"Found: {type(item['status']).__name__}"
            )

    def test_switches_json_has_offline_devices(self):
        """Verify there is at least one device with status 'offline'."""
        switches_file = "/home/user/inventory/switches.json"
        with open(switches_file, 'r') as f:
            data = json.load(f)

        offline_count = sum(1 for item in data if item.get("status") == "offline")
        assert offline_count > 0, (
            f"File {switches_file} has no devices with status 'offline'. "
            "There must be at least one offline device for this task."
        )

    def test_offline_hosts_txt_does_not_exist(self):
        """Verify /home/user/inventory/offline_hosts.txt does not exist initially."""
        output_file = "/home/user/inventory/offline_hosts.txt"
        assert not os.path.exists(output_file), (
            f"File {output_file} already exists. "
            "The output file should not exist before the task is performed."
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
            "jq must be installed for this task."
        )

    def test_jq_is_functional(self):
        """Verify jq can execute basic commands."""
        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq is not functional. "
            f"'jq --version' failed with: {result.stderr}"
        )

    def test_jq_can_parse_switches_file(self):
        """Verify jq can successfully parse the switches.json file."""
        switches_file = "/home/user/inventory/switches.json"
        result = subprocess.run(
            ["jq", ".", switches_file],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq cannot parse {switches_file}. "
            f"Error: {result.stderr}"
        )
