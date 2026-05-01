# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of extracting instance IDs from inventory.json.
"""

import json
import os
import subprocess
import pytest


class TestFinalState:
    """Test suite to verify the final state after task execution."""

    def test_instance_ids_txt_exists(self):
        """Verify /home/user/instance_ids.txt exists."""
        assert os.path.isfile("/home/user/instance_ids.txt"), \
            "/home/user/instance_ids.txt does not exist - task not completed"

    def test_instance_ids_txt_is_readable(self):
        """Verify /home/user/instance_ids.txt is readable."""
        assert os.access("/home/user/instance_ids.txt", os.R_OK), \
            "/home/user/instance_ids.txt is not readable"

    def test_instance_ids_txt_has_correct_line_count(self):
        """Verify /home/user/instance_ids.txt has exactly 3 lines."""
        result = subprocess.run(
            ["wc", "-l"],
            stdin=open("/home/user/instance_ids.txt", "r"),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip())
        assert line_count == 3, \
            f"/home/user/instance_ids.txt should have exactly 3 lines, got {line_count}"

    def test_instance_ids_txt_contains_expected_ids(self):
        """Verify /home/user/instance_ids.txt contains the expected instance IDs."""
        expected_ids = [
            "i-0a1b2c3d4e5f67890",
            "i-1b2c3d4e5f678901a",
            "i-2c3d4e5f678901a2b"
        ]
        with open("/home/user/instance_ids.txt", "r") as f:
            content = f.read()

        lines = content.strip().split('\n')
        assert lines == expected_ids, \
            f"Instance IDs do not match expected.\nGot: {lines}\nExpected: {expected_ids}"

    def test_instance_ids_txt_no_json_quotes(self):
        """Verify instance IDs do not contain JSON quotes."""
        with open("/home/user/instance_ids.txt", "r") as f:
            content = f.read()

        assert '"' not in content, \
            "Output contains JSON quotes - IDs should not be quoted"

    def test_instance_ids_txt_no_trailing_whitespace_on_lines(self):
        """Verify no trailing whitespace on individual lines."""
        with open("/home/user/instance_ids.txt", "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            # Remove the newline and check for trailing spaces/tabs
            line_content = line.rstrip('\n')
            assert line_content == line_content.rstrip(), \
                f"Line {i+1} has trailing whitespace: '{line_content}'"

    def test_instance_ids_txt_ends_with_single_newline(self):
        """Verify file ends with a single trailing newline."""
        with open("/home/user/instance_ids.txt", "r") as f:
            content = f.read()

        assert content.endswith('\n'), \
            "File should end with a newline"
        assert not content.endswith('\n\n'), \
            "File should have only a single trailing newline, not multiple"

    def test_instance_ids_txt_exact_content(self):
        """Verify the exact content of instance_ids.txt."""
        expected_content = """i-0a1b2c3d4e5f67890
i-1b2c3d4e5f678901a
i-2c3d4e5f678901a2b
"""
        with open("/home/user/instance_ids.txt", "r") as f:
            actual_content = f.read()

        assert actual_content == expected_content, \
            f"Content mismatch.\nExpected:\n{repr(expected_content)}\nGot:\n{repr(actual_content)}"

    def test_inventory_json_unchanged(self):
        """Verify /home/user/inventory.json is unchanged."""
        expected_data = [
            {"instance_id": "i-0a1b2c3d4e5f67890", "type": "t3.medium", "az": "us-east-1a"},
            {"instance_id": "i-1b2c3d4e5f678901a", "type": "t3.large", "az": "us-east-1b"},
            {"instance_id": "i-2c3d4e5f678901a2b", "type": "t3.small", "az": "us-east-1a"}
        ]

        assert os.path.isfile("/home/user/inventory.json"), \
            "/home/user/inventory.json no longer exists - it should be unchanged"

        with open("/home/user/inventory.json", "r") as f:
            actual_data = json.load(f)

        assert actual_data == expected_data, \
            f"inventory.json was modified.\nExpected: {expected_data}\nGot: {actual_data}"

    def test_instance_ids_one_per_line(self):
        """Verify each instance ID is on its own line."""
        with open("/home/user/instance_ids.txt", "r") as f:
            lines = [line.strip() for line in f.readlines()]

        # Check that each line contains exactly one instance ID (starts with i-)
        for i, line in enumerate(lines):
            assert line.startswith("i-"), \
                f"Line {i+1} does not start with 'i-': '{line}'"
            # Ensure no multiple IDs on same line
            assert line.count("i-") == 1, \
                f"Line {i+1} appears to have multiple instance IDs: '{line}'"
