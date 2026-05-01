# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the symlink creation task.
"""

import os
import json
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the task is performed."""

    def test_config_symlink_exists(self):
        """Verify /home/user/shortcuts/config exists."""
        config_link = "/home/user/shortcuts/config"
        assert os.path.lexists(config_link), (
            f"Symlink {config_link} does not exist. "
            "The symlink must be created at this path."
        )

    def test_config_is_symbolic_link(self):
        """Verify /home/user/shortcuts/config is a symbolic link."""
        config_link = "/home/user/shortcuts/config"
        assert os.path.islink(config_link), (
            f"{config_link} exists but is not a symbolic link. "
            "It must be a symlink, not a regular file or directory."
        )

    def test_symlink_is_relative_not_absolute(self):
        """Verify the symlink uses a relative path (does not start with /)."""
        config_link = "/home/user/shortcuts/config"
        link_target = os.readlink(config_link)
        assert not link_target.startswith('/'), (
            f"Symlink {config_link} uses an absolute path: '{link_target}'. "
            "The task requires a relative path so it survives if the tree is moved."
        )

    def test_symlink_target_is_correct_relative_path(self):
        """Verify the symlink points to ../app/settings.json."""
        config_link = "/home/user/shortcuts/config"
        link_target = os.readlink(config_link)
        expected_target = "../app/settings.json"
        assert link_target == expected_target, (
            f"Symlink {config_link} points to '{link_target}', "
            f"but expected '{expected_target}'."
        )

    def test_symlink_resolves_to_settings_json(self):
        """Verify the symlink resolves to /home/user/app/settings.json."""
        config_link = "/home/user/shortcuts/config"
        resolved_path = os.path.realpath(config_link)
        expected_resolved = "/home/user/app/settings.json"
        assert resolved_path == expected_resolved, (
            f"Symlink {config_link} resolves to '{resolved_path}', "
            f"but expected '{expected_resolved}'."
        )

    def test_symlink_is_readable(self):
        """Verify reading through the symlink returns the correct content."""
        config_link = "/home/user/shortcuts/config"
        expected_content = {"debug": False, "timeout": 30}

        with open(config_link, 'r') as f:
            content = f.read()

        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"Reading {config_link} does not return valid JSON. "
                f"Error: {e}"
            )

        assert parsed_content == expected_content, (
            f"Reading {config_link} returned {parsed_content}, "
            f"but expected {expected_content}."
        )

    def test_settings_json_unchanged(self):
        """Verify /home/user/app/settings.json is still a regular file with correct content."""
        settings_file = "/home/user/app/settings.json"
        expected_content = {"debug": False, "timeout": 30}

        assert os.path.exists(settings_file), (
            f"{settings_file} no longer exists. It should not be modified or deleted."
        )
        assert os.path.isfile(settings_file), (
            f"{settings_file} is not a regular file."
        )
        assert not os.path.islink(settings_file), (
            f"{settings_file} has become a symbolic link, but it should remain a regular file."
        )

        with open(settings_file, 'r') as f:
            content = f.read()

        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"{settings_file} does not contain valid JSON. Error: {e}"
            )

        assert parsed_content == expected_content, (
            f"{settings_file} content has changed. "
            f"Expected: {expected_content}, Got: {parsed_content}"
        )

    def test_no_extra_files_in_shortcuts(self):
        """Verify only 'config' exists in /home/user/shortcuts/."""
        shortcuts_dir = "/home/user/shortcuts"
        contents = os.listdir(shortcuts_dir)
        assert contents == ["config"], (
            f"Directory {shortcuts_dir} should only contain 'config'. "
            f"Found: {contents}"
        )

    def test_readlink_command_returns_relative_path(self):
        """Verify readlink command output is a relative path (anti-shortcut guard)."""
        result = subprocess.run(
            ["readlink", "/home/user/shortcuts/config"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"readlink command failed with return code {result.returncode}. "
            f"stderr: {result.stderr}"
        )
        link_target = result.stdout.strip()
        assert not link_target.startswith('/'), (
            f"readlink returned an absolute path: '{link_target}'. "
            "The symlink must use a relative path."
        )

    def test_grep_absolute_path_fails(self):
        """Anti-shortcut guard: grep for absolute path must fail (exit code 1)."""
        # Run: readlink /home/user/shortcuts/config | grep -q '^/'
        # This should return exit code 1 (not found) if the link is relative
        result = subprocess.run(
            "readlink /home/user/shortcuts/config | grep -q '^/'",
            shell=True
        )
        assert result.returncode == 1, (
            f"Expected 'readlink ... | grep -q \"^/\"' to return exit code 1 "
            f"(indicating relative path), but got exit code {result.returncode}. "
            "The symlink appears to be using an absolute path."
        )
