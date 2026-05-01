# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of extracting instance IDs from inventory.json.
"""

import json
import os
import shutil
import subprocess
import pytest


class TestInitialState:
    """Test suite to verify the initial state before task execution."""

    def test_home_directory_exists(self):
        """Verify /home/user directory exists."""
        assert os.path.isdir("/home/user"), "/home/user directory does not exist"

    def test_home_directory_is_writable(self):
        """Verify /home/user is writable."""
        assert os.access("/home/user", os.W_OK), "/home/user is not writable"

    def test_inventory_json_exists(self):
        """Verify /home/user/inventory.json exists."""
        assert os.path.isfile("/home/user/inventory.json"), \
            "/home/user/inventory.json does not exist"

    def test_inventory_json_is_readable(self):
        """Verify /home/user/inventory.json is readable."""
        assert os.access("/home/user/inventory.json", os.R_OK), \
            "/home/user/inventory.json is not readable"

    def test_inventory_json_contains_valid_json(self):
        """Verify /home/user/inventory.json contains valid JSON."""
        try:
            with open("/home/user/inventory.json", "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"/home/user/inventory.json contains invalid JSON: {e}")
        except Exception as e:
            pytest.fail(f"Failed to read /home/user/inventory.json: {e}")

    def test_inventory_json_is_array(self):
        """Verify /home/user/inventory.json contains a JSON array."""
        with open("/home/user/inventory.json", "r") as f:
            data = json.load(f)
        assert isinstance(data, list), \
            f"/home/user/inventory.json should contain an array, got {type(data).__name__}"

    def test_inventory_json_has_three_objects(self):
        """Verify /home/user/inventory.json contains exactly 3 objects."""
        with open("/home/user/inventory.json", "r") as f:
            data = json.load(f)
        assert len(data) == 3, \
            f"/home/user/inventory.json should contain 3 objects, got {len(data)}"

    def test_inventory_json_objects_have_instance_id_field(self):
        """Verify each object in inventory.json has an 'instance_id' field."""
        with open("/home/user/inventory.json", "r") as f:
            data = json.load(f)
        for i, obj in enumerate(data):
            assert isinstance(obj, dict), \
                f"Item {i} in inventory.json is not an object"
            assert "instance_id" in obj, \
                f"Item {i} in inventory.json is missing 'instance_id' field"

    def test_inventory_json_contains_expected_instance_ids(self):
        """Verify inventory.json contains the expected instance IDs."""
        expected_ids = [
            "i-0a1b2c3d4e5f67890",
            "i-1b2c3d4e5f678901a",
            "i-2c3d4e5f678901a2b"
        ]
        with open("/home/user/inventory.json", "r") as f:
            data = json.load(f)
        actual_ids = [obj["instance_id"] for obj in data]
        assert actual_ids == expected_ids, \
            f"Instance IDs do not match expected. Got: {actual_ids}, Expected: {expected_ids}"

    def test_inventory_json_objects_have_expected_structure(self):
        """Verify each object has the expected fields (instance_id, type, az)."""
        with open("/home/user/inventory.json", "r") as f:
            data = json.load(f)
        expected_keys = {"instance_id", "type", "az"}
        for i, obj in enumerate(data):
            assert set(obj.keys()) == expected_keys, \
                f"Item {i} has unexpected keys. Got: {set(obj.keys())}, Expected: {expected_keys}"

    def test_jq_is_installed(self):
        """Verify jq is installed and available in PATH."""
        jq_path = shutil.which("jq")
        assert jq_path is not None, "jq is not installed or not available in PATH"

    def test_jq_is_executable(self):
        """Verify jq can be executed."""
        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"jq --version failed with return code {result.returncode}: {result.stderr}"

    def test_instance_ids_txt_does_not_exist(self):
        """Verify /home/user/instance_ids.txt does not exist initially."""
        assert not os.path.exists("/home/user/instance_ids.txt"), \
            "/home/user/instance_ids.txt already exists but should not exist initially"
